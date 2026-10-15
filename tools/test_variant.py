"""Tests for variant.py (proxy install, DXVK as d3d9_dxvk.dll, hub switch).

Usage: python -I tools/test_variant.py
Runs against a temporary folder with fake files; never touches the TEST copy.
"""
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import variant  # noqa: E402


def fake_exe(path):
    """Minimal PE header with LAA off: e_lfanew=0x80, Characteristics=0."""
    data = bytearray(512)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    path.write_bytes(bytes(data))


class VariantTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.test = root / "TEST"
        build = root / "build"
        self.test.mkdir()
        build.mkdir()
        fake_exe(self.test / "Stronghold2.exe")
        self.proxy_src = build / "d3d9.dll"
        self.hub_src = build / "Stronghold2AnalyseHub.dll"
        self.dxvk_src = root / "dxvk_d3d9.dll"
        self.proxy_src.write_bytes(b"MZ proxy " + variant.PROXY_MARKER + b" v1")
        self.hub_src.write_bytes(b"MZ hub v1")
        self.dxvk_src.write_bytes(b"MZ dxvk")
        self.saved = (variant.TEST_DIR, variant.DXVK_SRC, variant.PROXY_SRC, variant.HUB_SRC)
        variant.TEST_DIR, variant.DXVK_SRC = self.test, self.dxvk_src
        variant.PROXY_SRC, variant.HUB_SRC = self.proxy_src, self.hub_src

    def tearDown(self):
        variant.TEST_DIR, variant.DXVK_SRC, variant.PROXY_SRC, variant.HUB_SRC = self.saved
        self.tmp.cleanup()

    def test_baseline_installs_proxy_and_hub(self):
        variant.apply("baseline")
        self.assertTrue(variant.is_proxy(self.test / "d3d9.dll"))
        self.assertEqual((self.test / "Stronghold2AnalyseHub.dll").read_bytes(), b"MZ hub v1")
        self.assertEqual(variant.read_ini(), {"target": "system", "hub": "1"})
        self.assertFalse((self.test / variant.DXVK_NAME).exists())
        self.assertEqual((self.test / "steam_appid.txt").read_text(), "40960")
        self.assertEqual(variant.current_variant(), "baseline")

    def test_dxvk_goes_behind_the_proxy_and_back(self):
        variant.apply("dxvk")
        self.assertTrue(variant.is_proxy(self.test / "d3d9.dll"))
        self.assertEqual((self.test / variant.DXVK_NAME).read_bytes(), b"MZ dxvk")
        self.assertEqual(variant.read_ini()["target"], variant.DXVK_NAME)
        self.assertEqual(variant.current_variant(), "dxvk")
        variant.apply("baseline")
        self.assertFalse((self.test / variant.DXVK_NAME).exists())
        self.assertEqual(variant.read_ini()["target"], "system")
        self.assertEqual(variant.current_variant(), "baseline")

    def test_old_layout_dxvk_as_d3d9_is_replaced(self):
        (self.test / "d3d9.dll").write_bytes(b"MZ dxvk")
        self.assertEqual(variant.current_variant(), "dxvk")
        variant.apply("dxvk")
        self.assertTrue(variant.is_proxy(self.test / "d3d9.dll"))
        self.assertEqual((self.test / variant.DXVK_NAME).read_bytes(), b"MZ dxvk")

    def test_foreign_d3d9_is_left_alone(self):
        (self.test / "d3d9.dll").write_bytes(b"MZ someone else")
        with self.assertRaises(SystemExit):
            variant.apply("baseline")
        self.assertEqual((self.test / "d3d9.dll").read_bytes(), b"MZ someone else")

    def test_foreign_d3d9_dxvk_is_left_alone(self):
        (self.test / variant.DXVK_NAME).write_bytes(b"MZ other build")
        with self.assertRaises(SystemExit):
            variant.apply("baseline")
        self.assertEqual((self.test / variant.DXVK_NAME).read_bytes(), b"MZ other build")

    def test_hub_switch_keeps_target_and_manual_keys(self):
        variant.apply("dxvk")
        variant.write_ini(out="D:\\perf")
        variant.set_hub(False)
        self.assertEqual(variant.read_ini(),
                         {"target": variant.DXVK_NAME, "hub": "0", "out": "D:\\perf"})
        variant.apply("dxvk")                      # re-running a variant keeps the switch
        self.assertEqual(variant.read_ini()["hub"], "0")
        variant.set_hub(True)
        self.assertEqual(variant.read_ini()["hub"], "1")

    def test_sample_mode_is_kept_across_variants(self):
        variant.apply("baseline")
        variant.set_sample("module")
        variant.apply("dxvk")
        variant.set_hub(False)
        self.assertEqual(variant.read_ini()["sample"], "module")
        variant.set_sample("off")
        self.assertEqual(variant.read_ini()["sample"], "off")

    def test_granny_observer_switch_is_separate_from_profiles(self):
        variant.apply("baseline")
        variant.set_granny(True)
        self.assertEqual(variant.read_ini()["granny"], "1")
        variant.set_mode("min")                       # a profile change does not touch it
        variant.set_sample("off")
        self.assertEqual(variant.read_ini()["granny"], "1")
        variant.set_granny(False)
        self.assertEqual(variant.read_ini()["granny"], "0")   # off is explicit, not a removed key

    def test_hub_measurement_switches(self):
        variant.apply("baseline")
        variant.set_switch("overlay", "off")
        variant.set_switch("counters", "on")
        ini = variant.read_ini()
        self.assertEqual((ini["overlay"], ini["counters"]), ("0", "1"))
        variant.set_mode("min")                       # profile replaces single switches
        ini = variant.read_ini()
        self.assertEqual(ini["profile"], "min")
        self.assertFalse(any(k in ini for k in variant.SWITCHES))
        variant.set_switch("poll", "on")
        variant.set_switch("poll", "default")        # removes the key again
        self.assertNotIn("poll", variant.read_ini())
        variant.set_sample("module")
        variant.set_mode("full")
        self.assertEqual(variant.read_ini()["sample"], "module")   # unrelated keys survive
        self.assertEqual(variant.read_ini()["target"], "system")

    def test_hub_measurement_switches_need_proxy(self):
        with self.assertRaises(SystemExit):
            variant.set_mode("min")
        with self.assertRaises(SystemExit):
            variant.set_switch("overlay", "off")

    def test_hub_switch_needs_proxy(self):
        with self.assertRaises(SystemExit):
            variant.set_hub(False)

    def test_rebuilt_hub_is_refreshed(self):
        variant.apply("baseline")
        self.hub_src.write_bytes(b"MZ hub v2")
        variant.apply("baseline")
        self.assertEqual((self.test / "Stronghold2AnalyseHub.dll").read_bytes(), b"MZ hub v2")

    def test_missing_build_is_reported(self):
        self.proxy_src.unlink()
        with self.assertRaises(SystemExit):
            variant.apply("baseline")

    def test_plan_is_stored_as_written_and_kept_across_other_commands(self):
        variant.apply("baseline")
        variant.set_plan(["game_speed=90", "experiment=EXP-1", "protocol=Real save", "paused=true"])
        self.assertEqual(variant.read_plan(), {"game_speed": "90", "experiment": "EXP-1", "protocol": "Real save", "paused": "1"})
        variant.set_mode("min")
        variant.set_sample("module")
        variant.set_hub(True)
        self.assertEqual(variant.read_plan()["game_speed"], "90")            # not lost when the proxy keys are rewritten
        self.assertEqual(variant.read_ini()["profile"], "min")
        variant.set_plan(["game_speed=30", "paused="])
        self.assertEqual(variant.read_plan()["game_speed"], "30")
        self.assertNotIn("paused", variant.read_plan())                       # pause is independent of the speed
        variant.set_plan(["game_speed=1.5"])
        self.assertEqual(variant.read_plan()["game_speed"], "1.5")
        variant.set_plan(["clear"])
        self.assertEqual(variant.read_plan(), {})
        self.assertNotIn("[plan]", (self.test / "SH2Proxy.ini").read_text())

    def test_plan_rejects_what_is_not_a_number_but_not_any_range(self):
        variant.apply("baseline")
        for bad in ("game_speed=fast", "game_speed=nan", "game_speed=inf", "paused=maybe", "colour=red", "game_speed"):
            with self.assertRaises(SystemExit, msg=bad):
                variant.set_plan([bad])
        variant.set_plan(["game_speed=-3"])                                    # the valid range is not guessed
        variant.set_plan(["game_speed=100000"])
        self.assertEqual(variant.read_plan()["game_speed"], "100000")

    def test_prepared_record_names_the_software_at_prepare_time(self):
        import json
        import hashlib
        variant.apply("baseline")
        rec = json.loads((self.test / "SH2Prepared.json").read_text())
        self.assertEqual(rec["schema"], "sh2perf.prepared-start")
        by_role = {f["role"]: f for f in rec["files"]}
        hub = (self.test / "Stronghold2AnalyseHub.dll").read_bytes()
        self.assertEqual(by_role["hub_dll"]["sha256"], hashlib.sha256(hub).hexdigest())      # full 64-digit SHA-256
        self.assertEqual(len(by_role["game_exe"]["sha256"]), 64)
        self.assertEqual(rec["variant"], "baseline")
        self.hub_src.write_bytes(b"MZ hub v2")
        variant.apply("baseline")
        rec2 = json.loads((self.test / "SH2Prepared.json").read_text())
        self.assertNotEqual({f["role"]: f["sha256"] for f in rec2["files"]}["hub_dll"], by_role["hub_dll"]["sha256"])
        variant.set_plan(["game_speed=90"])
        self.assertEqual(json.loads((self.test / "SH2Prepared.json").read_text())["plan"], {"game_speed": "90"})


if __name__ == "__main__":
    unittest.main(verbosity=1)
