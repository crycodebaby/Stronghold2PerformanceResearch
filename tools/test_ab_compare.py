"""Tests for ab_compare.py on synthetic frame series.

Run: python -I tools/test_ab_compare.py
"""
import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import ab_compare  # noqa: E402

HEADER = ("frame,t_s,frame_ms,present_ms,endscene_ms,between_endscene_ms,overlay_ms,scenes,dip,dp,dpup,dipup,"
          "prims,settex,vsconst_calls,vsconst_vec4,psconst_calls,psconst_vec4,va_used_mb,marker\n")


def series(seconds=30, base=16.67, spike_every=None, spike_ms=60.0, marker=0):
    """Rows (t_s, frame_ms, present_ms); one spike every `spike_every` seconds if given."""
    rows, t, next_spike = [], 0.0, spike_every
    while t < seconds:
        ms = base
        if next_spike is not None and t >= next_spike:
            ms = spike_ms
            next_spike += spike_every
        t += ms / 1000
        rows.append((t, ms, 0.3))
    return rows


def write_csv(path, rows, marker=0):
    with open(path, "w", newline="") as f:
        f.write(HEADER)
        for i, (t, ms, pr) in enumerate(rows):
            f.write(f"{i},{t:.4f},{ms:.3f},{pr:.3f},0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,{marker}\n")


class StatsTest(unittest.TestCase):
    def test_clocked_spikes_are_detected(self):
        s = ab_compare.stats(series(spike_every=1.0))
        self.assertGreaterEqual(s["long_n"], 25)
        self.assertGreater(s["period_share"], 90)
        self.assertLess(s["control_share"], 25)                # a clock is far above random placement

    def test_no_spikes(self):
        s = ab_compare.stats(series())
        self.assertEqual(s["long_n"], 0)
        self.assertIsNone(s["period_share"])
        self.assertAlmostEqual(s["p50"], 16.67, places=2)

    def test_irregular_spikes_are_not_clocked(self):
        rows = series()
        for i in (40, 130, 300, 310, 700, 1100, 1105, 1500):
            rows[i] = (rows[i][0], 60.0, 0.3)
        s = ab_compare.stats(rows)
        self.assertLess(s["period_share"], 40)

    def test_too_short(self):
        self.assertIsNone(ab_compare.stats(series(seconds=0.05)))


class CliTest(unittest.TestCase):
    def test_columns_and_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a_frames.csv", Path(tmp) / "b_frames.csv"
            write_csv(a, series(spike_every=1.0))
            write_csv(b, series(base=15.0))
            r = subprocess.run([sys.executable, "-I", str(TOOLS / "ab_compare.py"), f"A={a}", f"B={b}"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("| metric | A | B |", r.stdout)
            self.assertIn("long-frame gaps ~period %", r.stdout)
            self.assertIn("%)", r.stdout)                      # delta against the reference column

    def test_marker_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a_frames.csv"
            write_csv(a, series(), marker=2)
            self.assertEqual(len(ab_compare.load(str(a), marker=1)), 0)
            self.assertGreater(len(ab_compare.load(str(a), marker=2)), 100)


class SpeedNotesTest(unittest.TestCase):
    def test_different_speeds_warn_and_are_shown(self):
        cells, notes = ab_compare.speed_notes(["a", "b"], [(30, "planned"), (90, "user_confirmed")])
        self.assertEqual(cells, ["30 (planned)", "90 (user_confirmed)"])
        self.assertTrue(any("30, 90" in n and "not comparable" in n for n in notes))

    def test_unknown_speed_is_noted_not_assumed_equal(self):
        cells, notes = ab_compare.speed_notes(["a", "b"], [(90, "planned"), (None, "unknown")])
        self.assertEqual(cells[1], "unknown")
        self.assertEqual(len(notes), 1)
        self.assertIn("b", notes[0])

    def test_same_known_speed_has_no_note(self):
        self.assertEqual(ab_compare.speed_notes(["a", "b"], [(90, "planned"), (90, "observed")])[1], [])

    def test_csv_path_has_unknown_speed(self):
        self.assertEqual(ab_compare.speed_of("some/file_frames.csv"), (None, "unknown"))


if __name__ == "__main__":
    unittest.main()
