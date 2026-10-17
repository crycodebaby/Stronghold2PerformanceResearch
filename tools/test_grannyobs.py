"""Regression tests for G1 detail loss and reference gating; synthetic temporary files only."""
import copy
import csv
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grannyobs
import silver
import testkit

READER = Path(grannyobs.__file__)


class ObserverQuality(unittest.TestCase):
    def meta(self, version=2):
        return {"schema": "sh2perf.granny-observer", "version": version,
                "losses": {k: 0 for k in grannyobs.LOSS_KEYS}, "owner_detail_complete": True}

    def test_v1_and_v2_complete(self):
        for version in (1, 2):
            self.assertEqual(grannyobs.quality(self.meta(version))["status"], "complete")

    def test_losses_override_optimistic_flag(self):
        m = self.meta(); m["losses"]["instance_table_full"] = 498935
        self.assertEqual(grannyobs.quality(m)["status"], "partial")

    def test_unknown_is_not_complete(self):
        for m in ([], {}, {"version": 99}, {"schema": "sh2perf.granny-observer", "version": 2, "losses": {}},
                  dict(self.meta(), version=True), dict(self.meta(), owner_detail_complete=None)):
            self.assertEqual(grannyobs.quality(m)["status"], "unknown")

    def test_observer_loss_blocks_reference_but_not_frame_integrity(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            m, stem = testkit.reference_recording(d, "20261015_100000")
            obs = self.meta(); obs["losses"]["instance_table_full"] = 1
            name = stem + "_granny.json"; raw = json.dumps(obs).encode(); (d / name).write_bytes(raw)
            m["files"].append({"role": "granny_meta", "name": name, "size": len(raw), "sha256": testkit.sha(raw)})
            (d / "manifest.json").write_text(json.dumps(m))
            (d / "import.json").write_text(json.dumps({"capture_id": m["capture_id"], "files": m["files"]}))
            s = silver.derive(d, {"suitability": {"verdict": "suitable"}})
            self.assertEqual(s["quality"]["technical"]["status"], "ok")
            self.assertFalse(s["quality"]["benchmark_suitability"]["usable_as_benchmark"])
            self.assertIn("observer_detail_partial", s["quality"]["benchmark_suitability"]["missing_info"])


class FrameAccounting(unittest.TestCase):
    def meta(self, version=2):
        return dict(ObserverQuality().meta(version), calls=dict.fromkeys(grannyobs.CALL_COLUMNS, 0))

    def frame(self, **values):
        return dict(dict.fromkeys(grannyobs.CALL_COLUMNS.values(), 0), **values)

    def test_balanced_versions_and_unchanged_owner_quality(self):
        for version in (1, 2):
            meta = self.meta(version)
            before = copy.deepcopy(meta)
            self.assertEqual(grannyobs.frame_accounting(meta, [self.frame()])["status"], "balanced")
            self.assertEqual(grannyobs.quality(meta)["status"], "complete")
            self.assertEqual(meta, before)

    def test_known_residual_and_separate_quality(self):
        meta = self.meta()
        for fn, number in zip(grannyobs.CALL_COLUMNS, (372, 187, 25, 25, 0, 0)):
            meta["calls"][fn] = number
        result = grannyobs.frame_accounting(meta, [self.frame()])
        self.assertEqual((result["status"], result["total"], result["label"]),
                         ("partial", 609, "unframed tail"))
        self.assertEqual(grannyobs.quality(meta)["status"], "complete")

    def test_every_function_mapping(self):
        meta = self.meta()
        row = self.frame()
        for number, (fn, column) in enumerate(grannyobs.CALL_COLUMNS.items(), 1):
            meta["calls"][fn], row[column] = number * 3, number
        result = grannyobs.frame_accounting(meta, [row])
        self.assertEqual(list(result["differences"].values()), [2, 4, 6, 8, 10, 12])

    def test_dropped_or_unknown_rows_are_not_definitely_tail(self):
        for drops in (1, None, True, -1, "0"):
            meta = self.meta()
            meta["losses"]["frame_rows_dropped"] = drops
            meta["calls"]["GrannySetModelClock"] = 1
            result = grannyobs.frame_accounting(meta, [])
            self.assertEqual(result["label"], "unframed/unassigned calls")
            self.assertIn("not exclusively", result["note"])

    def test_negative_delta_not_cancelled_by_positive_delta(self):
        meta = self.meta()
        meta["calls"]["GrannyDeformVertices"] = 99
        result = grannyobs.frame_accounting(meta, [self.frame(clock_calls=1)])
        self.assertEqual(result["status"], "inconsistent")
        self.assertEqual(result["differences"]["GrannySetModelClock"], -1)

    def test_missing_and_invalid_totals(self):
        for value in (None, True, -1, 1.0, "1"):
            meta = self.meta()
            meta["calls"]["GrannySetModelClock"] = value
            self.assertEqual(grannyobs.frame_accounting(meta, [self.frame()])["status"], "unknown")
        self.assertEqual(grannyobs.frame_accounting(ObserverQuality().meta(), [])["status"], "unknown")
        meta = self.meta()
        del meta["calls"]["GrannyFreeMeshDeformer"]
        self.assertEqual(grannyobs.frame_accounting(meta, [])["status"], "unknown")

    def test_invalid_frame_counters_and_schema(self):
        for value in (None, True, -1, 1.0, "1.5", "nan", ""):
            self.assertEqual(grannyobs.frame_accounting(self.meta(), [self.frame(clock_calls=value)])["status"],
                             "unknown")
        row = self.frame()
        del row["free_deformer_calls"]
        self.assertEqual(grannyobs.frame_accounting(self.meta(), [row])["status"], "unknown")
        for meta in ([], {}, dict(self.meta(), version=True), dict(self.meta(), version=99)):
            self.assertEqual(grannyobs.frame_accounting(meta, [])["status"], "unknown")

    def test_empty_frames_and_integer_precision(self):
        meta = self.meta()
        self.assertEqual(grannyobs.frame_accounting(meta, [])["status"], "balanced")
        meta["calls"]["GrannySetModelClock"] = 2**53 + 7
        result = grannyobs.frame_accounting(meta, [self.frame(clock_calls=3)])
        self.assertEqual(result["total"], 2**53 + 4)
        self.assertIs(type(result["total"]), int)

    def test_cli_global_tail_ignores_phase_filters(self):
        # No new helper is called here: this same CLI test is run against the old reader.
        with tempfile.TemporaryDirectory() as td:
            stem = self.write_recording(Path(td))
            prefixes = []
            for marker in (1, 3):
                run = subprocess.run([sys.executable, "-I", str(READER), str(stem), "--markers", str(marker)],
                                     capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                prefix = run.stdout.split("observer detail:")[0]
                self.assertIn("frame-call accounting: partial; unframed tail: 609 calls", prefix)
                self.assertIn("clock=372, sample=187, deform=25, composite=25, free_instance=0, free_deformer=0", prefix)
                prefixes.append(prefix)
            self.assertEqual(prefixes[0], prefixes[1])

    def write_recording(self, directory):
        # Literal column names/values provide a fixture independent of implementation mappings.
        columns = ["clock_calls", "sample_calls", "deform_calls", "composite_calls",
                   "free_instance_calls", "free_deformer_calls"]
        names = ["GrannySetModelClock", "GrannySampleModelAnimationsAccelerated", "GrannyDeformVertices",
                 "GrannyGetWorldPoseComposite4x4Array", "GrannyFreeModelInstance", "GrannyFreeMeshDeformer"]
        stem = directory / "SH2Perf_synthetic"
        meta = dict(ObserverQuality().meta(), calls=dict(zip(names, (387, 207, 35, 55, 2, 3))))
        Path(f"{stem}_granny.json").write_text(json.dumps(meta), encoding="utf-8")
        fields = ["frame", "marker", "partial", *columns, "inst_clocked", "inst_sampled", "deformers"]
        with Path(f"{stem}_granny_frames.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for frame, marker, partial, count in ((0, 0, 1, 7), (1, 1, 0, 3), (2, 3, 0, 5)):
                row = dict.fromkeys(fields, 0)
                row.update(frame=frame, marker=marker, partial=partial, clock_calls=count)
                if frame == 2:
                    row.update(sample_calls=20, deform_calls=10, composite_calls=30,
                               free_instance_calls=2, free_deformer_calls=3)
                writer.writerow(row)
        Path(f"{stem}_granny_instances.csv").write_text("instance\n", encoding="utf-8")
        Path(f"{stem}_granny_deformers.csv").write_text("deformer\n", encoding="utf-8")
        return stem

    def test_csv_precision_and_bad_counter_cli(self):
        with tempfile.TemporaryDirectory() as td:
            stem = self.write_recording(Path(td))
            path = Path(f"{stem}_granny_frames.csv")
            text = path.read_text(encoding="utf-8").replace("0,0,1,7,", f"0,0,1,{2**53 + 1},")
            path.write_text(text, encoding="utf-8")
            rows = grannyobs._rows(path, frame_calls=True)
            self.assertEqual(rows[0]["clock_calls"], 2**53 + 1)
            path.write_text(text.replace(str(2**53 + 1), "1.5"), encoding="utf-8")
            run = subprocess.run([sys.executable, "-I", str(READER), str(stem)], capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("frame-call accounting: unknown", run.stdout)
            self.assertNotIn("--- marker", run.stdout)

    def test_missing_frame_columns_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            stem = self.write_recording(Path(td))
            Path(f"{stem}_granny_frames.csv").write_text("frame,marker,partial\n", encoding="utf-8")
            run = subprocess.run([sys.executable, "-I", str(READER), str(stem)], capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("frame-call accounting: unknown; missing frame call-counter columns", run.stdout)
            stem = self.write_recording(Path(td))
            path = Path(f"{stem}_granny_frames.csv")
            text = path.read_text().splitlines()
            text[0] += ",clock_calls"
            path.write_text("\n".join(text) + "\n", encoding="utf-8")
            run = subprocess.run([sys.executable, "-I", str(READER), str(stem)], capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("frame-call accounting: unknown; duplicate frame call-counter columns", run.stdout)

    def test_cli_empty_frames_in_both_versions(self):
        for version in (1, 2):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as td:
                stem = self.write_recording(Path(td))
                meta_path, frames_path = Path(f"{stem}_granny.json"), Path(f"{stem}_granny_frames.csv")
                meta = json.loads(meta_path.read_text())
                meta["version"] = version
                meta["calls"] = dict.fromkeys(meta["calls"], 0)
                meta_path.write_text(json.dumps(meta), encoding="utf-8")
                frames_path.write_text(frames_path.read_text().splitlines()[0] + "\n", encoding="utf-8")
                run = subprocess.run([sys.executable, "-I", str(READER), str(stem)], capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertIn("frame-call accounting: balanced (counts only", run.stdout)
                self.assertIn("marker 1: no frames", run.stdout)

    def test_cli_missing_drops_are_not_zero_and_bad_totals_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            stem = self.write_recording(Path(td))
            path = Path(f"{stem}_granny.json")
            meta = json.loads(path.read_text())
            del meta["losses"]["frame_rows_dropped"]
            path.write_text(json.dumps(meta), encoding="utf-8")
            run = subprocess.run([sys.executable, "-I", str(READER), str(stem)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("unframed/unassigned calls: 609 calls", run.stdout)
            self.assertIn("observer detail: unknown", run.stdout)
            for value, status in ((0, "inconsistent"), (None, "unknown")):
                meta["calls"]["GrannySetModelClock"] = value
                path.write_text(json.dumps(meta), encoding="utf-8")
                run = subprocess.run([sys.executable, "-I", str(READER), str(stem)], capture_output=True, text=True)
                self.assertNotEqual(run.returncode, 0)
                self.assertIn(f"frame-call accounting: {status}", run.stdout)
                self.assertNotIn("--- marker", run.stdout)

    def test_cli_oversized_csv_field_is_unknown(self):
        with tempfile.TemporaryDirectory() as td:
            stem = self.write_recording(Path(td))
            path = Path(f"{stem}_granny_frames.csv")
            text = path.read_text(encoding="utf-8").replace("0,0,1,7,", "0,0,1," + "7" * 140000 + ",")
            path.write_text(text, encoding="utf-8")
            run = subprocess.run([sys.executable, "-I", str(READER), str(stem)], capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("frame-call accounting: unknown", run.stdout)
            self.assertNotIn("Traceback", run.stderr)
            self.assertNotIn("--- marker", run.stdout)

    def test_cli_missing_file_or_invalid_metadata_is_unknown(self):
        for value in ([], None, {"version": True}, {"version": 99}):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as td:
                stem = self.write_recording(Path(td))
                Path(f"{stem}_granny.json").write_text(json.dumps(value), encoding="utf-8")
                run = subprocess.run([sys.executable, "-I", str(READER), str(stem)], capture_output=True, text=True)
                self.assertNotEqual(run.returncode, 0)
                self.assertIn("frame-call accounting: unknown", run.stdout)
                self.assertNotIn("Traceback", run.stderr)
        with tempfile.TemporaryDirectory() as td:
            stem = self.write_recording(Path(td))
            Path(f"{stem}_granny_frames.csv").unlink()
            run = subprocess.run([sys.executable, "-I", str(READER), str(stem)], capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("frame-call accounting: unknown", run.stdout)
            self.assertNotIn("Traceback", run.stderr)


if __name__ == "__main__":
    unittest.main()
