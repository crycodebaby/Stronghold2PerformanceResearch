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


if __name__ == "__main__":
    unittest.main(verbosity=1)
