"""Tests for ingest.py (recording choice, legacy recordings, old command line) and samples.py (module groups).

Safety, provenance and manifest behaviour is covered by test_import_safety.py.
Run: python -I tools/test_ingest.py   (temp folders only)
"""
import json
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import samples  # noqa: E402
import testkit as tk  # noqa: E402


class IngestTest(unittest.TestCase):
    def setUp(self):
        self.L = tk.Layout()

    def tearDown(self):
        self.L.cleanup()

    def test_single_legacy_recording_keeps_its_sources(self):
        tk.make_legacy_recording(self.L.src, "20261015_100000")
        before = tk.tree_hashes(self.L.src)
        r = self.L.run("import", "--legacy")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(tk.tree_hashes(self.L.src), before, "no source is deleted any more")
        self.assertEqual(len(self.L.index.read_text().splitlines()), 1)

    def test_old_command_line_without_subcommand_still_works(self):
        tk.make_legacy_recording(self.L.src, "20261015_100000")
        r = self.L.run("--legacy", "--exp", "T", "--scenario", "S", "--troops", "1")
        self.assertEqual(r.returncode, 0, r.stderr)
        line = self.L.index_lines()[0]
        self.assertEqual((line["exp"], line["scenario"], line["troops"]), ("T", "S", 1))

    def test_two_recordings_are_not_touched_without_choice(self):
        tk.make_legacy_recording(self.L.src, "20261015_100000")
        tk.make_legacy_recording(self.L.src, "20261015_110000")
        (self.L.src / "latest.json").write_text(json.dumps({"frames_csv": "SH2Perf_20261015_110000_frames.csv"}))
        before = tk.tree_hashes(self.L.src)
        r = self.L.run("import", "--legacy")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--recording", r.stdout)
        self.assertEqual(tk.tree_hashes(self.L.src), before)
        self.assertFalse(self.L.captures.exists())
        self.assertFalse(self.L.index.exists())

    def test_chosen_recording_with_samples_and_its_own_latest_json_untouched(self):
        tk.make_legacy_recording(self.L.src, "20261015_100000", samples=True)
        tk.make_legacy_recording(self.L.src, "20261015_110000")
        (self.L.src / "latest.json").write_text(json.dumps({"frames_csv": "SH2Perf_20261015_110000_frames.csv"}))
        r = self.L.run("import", "--legacy", "--recording", "20261015_100000")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.L.src / "latest.json").exists())
        line = self.L.index_lines()[0]
        self.assertEqual(line["render_modules"]["all"], {"exe": 60.0, "driver": 30.0, "system": 10.0})
        self.assertTrue(list((self.L.captures / "legacy-SH2Perf_20261015_100000").glob("*_samples.csv")))

    def test_unknown_recording_is_refused(self):
        tk.make_legacy_recording(self.L.src, "20261015_100000")
        r = self.L.run("import", "--legacy", "--recording", "20200101_000000")
        self.assertEqual(r.returncode, 2)
        self.assertFalse(self.L.captures.exists())

    def test_empty_folder_is_reported(self):
        r = self.L.run("import")
        self.assertEqual(r.returncode, 2)
        self.assertIn("no recording", r.stdout)

    def test_list_shows_manifest_state_and_legacy(self):
        tk.make_recording(self.L.src, "20261015_100000")
        tk.make_recording(self.L.src, "20261015_110000", status="recording")
        tk.make_legacy_recording(self.L.src, "20261015_120000")
        out = self.L.run("list").stdout
        self.assertIn("manifest finalized", out)
        self.assertIn("manifest interrupted", out)
        self.assertIn("legacy (no manifest)", out)

    def test_hub_v2_modes_and_health_in_a_legacy_latest_json(self):
        tk.make_legacy_recording(self.L.src, "20261015_100000", counters=False, overlay=False, poll=False)
        (self.L.src / "latest.json").write_text(json.dumps({
            "frames_csv": "SH2Perf_20261015_100000_frames.csv", "start": "2026-10-15T10:00:00", "stop": "2026-10-15T10:00:01",
            "capture_version": 2, "capture_ok": False, "frames_dropped": 7, "frames_lost_write": 0, "write_errors": 0,
            "modes": {"frametime": True, "counters": False, "poll": False, "overlay": False, "sample": False}}))
        r = self.L.run("import", "--legacy")
        self.assertEqual(r.returncode, 0, r.stderr)
        line = self.L.index_lines()[0]
        self.assertIsNone(line["total"]["dip"])                 # counters off: null, not 0
        self.assertIsNone(line["total"]["cpu_side_ms"])         # no EndScene timing without overlay
        self.assertIsNone(line["total"]["va_max_mb"])
        self.assertEqual(line["total"]["threads"], [])
        self.assertIsNotNone(line["total"]["present_ms"])       # always measured
        self.assertFalse(line["capture_ok"])
        self.assertEqual(line["capture_loss"]["dropped"], 7)


class SamplesTest(unittest.TestCase):
    def test_groups(self):
        for name, grp in [("Stronghold2.exe", "exe"), ("dragonfly.dll", "dragonfly"), ("dxrenderer.dll", "dxrenderer"),
                          ("granny2.dll", "granny2"), ("d3d9.dll", "d3d9"), ("d3dx9_27.dll", "d3dx9"),
                          ("nvwgf2um.dll", "driver"), ("nvd3dum.dll", "driver"), ("ntdll.dll", "system"),
                          ("win32u.dll", "system"), ("gameoverlayrenderer.dll", "overlay"),
                          ("Stronghold2AnalyseHub.dll", "hub"), ("foo.dll", "other"), ("?", "unknown")]:
            self.assertEqual(samples.group_of(name), grp, name)


if __name__ == "__main__":
    unittest.main()
