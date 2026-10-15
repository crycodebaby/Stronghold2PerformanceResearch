"""Tests for ingest.py (recording choice) and samples.py (module groups), in a temp folder.

Run: python -I tools/test_ingest.py
"""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import samples  # noqa: E402

HEADER = ("frame,t_s,frame_ms,present_ms,endscene_ms,between_endscene_ms,overlay_ms,scenes,dip,dp,dpup,dipup,"
          "prims,settex,vsconst_calls,vsconst_vec4,psconst_calls,psconst_vec4,va_used_mb,marker\n")


def make_recording(folder, stamp, frames=20, samples_csv=False):
    rows = "".join(f"{i},{i * 0.02:.4f},20.0,0.5,0.0,19.0,0.1,2,100,10,0,0,5000,50,60,200,5,20,1500,0\n"
                   for i in range(frames))
    (folder / f"SH2Perf_{stamp}_frames.csv").write_text(HEADER + rows)
    (folder / f"SH2Perf_{stamp}_threads.csv").write_text("t_s,tid,cpu_pct,is_render_thread\n0.5,1,90.0,1\n")
    if samples_csv:
        (folder / f"SH2Perf_{stamp}_samples.csv").write_text(
            "marker,module,rva,count\n0,Stronghold2.exe,0x00000000,60\n0,nvwgf2um.dll,0x00000000,30\n"
            "0,ntdll.dll,0x00000000,10\n")


class IngestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.src, self.cap, self.index = root / "out", root / "cap", root / "index.jsonl"
        self.src.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def ingest(self, *extra):
        return subprocess.run(
            [sys.executable, "-I", str(TOOLS / "ingest.py"), "--exp", "T", "--scenario", "S", "--troops", "1",
             "--variant", "baseline", "--src", str(self.src), "--captures", str(self.cap), "--index", str(self.index),
             *extra], capture_output=True, text=True)

    def test_single_recording_without_latest_json(self):
        make_recording(self.src, "20261015_100000")
        r = self.ingest()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(list(self.src.glob("*_frames.csv")), [])
        self.assertEqual(len(self.index.read_text().splitlines()), 1)

    def test_two_recordings_are_not_touched_without_choice(self):
        make_recording(self.src, "20261015_100000")
        make_recording(self.src, "20261015_110000")
        (self.src / "latest.json").write_text(json.dumps({"frames_csv": "SH2Perf_20261015_110000_frames.csv"}))
        before = sorted(p.name for p in self.src.iterdir())
        r = self.ingest()
        self.assertEqual(r.returncode, 2)
        self.assertIn("--recording", r.stdout)
        self.assertEqual(sorted(p.name for p in self.src.iterdir()), before)
        self.assertFalse(self.cap.exists())
        self.assertFalse(self.index.exists())

    def test_chosen_recording_moves_only_its_own_files(self):
        make_recording(self.src, "20261015_100000", samples_csv=True)
        make_recording(self.src, "20261015_110000")
        (self.src / "latest.json").write_text(json.dumps(
            {"frames_csv": "SH2Perf_20261015_110000_frames.csv", "threads_csv": "SH2Perf_20261015_110000_threads.csv"}))
        r = self.ingest("--recording", "20261015_100000")
        self.assertEqual(r.returncode, 0, r.stderr)
        left = sorted(p.name for p in self.src.iterdir())
        self.assertIn("SH2Perf_20261015_110000_frames.csv", left)
        self.assertIn("latest.json", left)                 # belongs to the other recording
        self.assertNotIn("SH2Perf_20261015_100000_frames.csv", left)
        line = json.loads(self.index.read_text().splitlines()[0])
        self.assertEqual(line["render_modules"]["all"], {"exe": 60.0, "driver": 30.0, "system": 10.0})

    def test_unknown_recording_is_refused(self):
        make_recording(self.src, "20261015_100000")
        r = self.ingest("--recording", "20200101_000000")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(len(list(self.src.glob("*_frames.csv"))), 1)


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
