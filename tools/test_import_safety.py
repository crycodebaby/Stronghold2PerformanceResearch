"""Tests for provenance and safe import (D012): manifests, identity independent of latest.json, repeat/interrupted
import, conflicts, damaged sources, write errors, game speed origins, reproducible silver.

Run: python -I tools/test_import_safety.py   (temp folders only; never touches captures/, data/ or the TEST copy)
"""
import errno
import json
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bronze  # noqa: E402
import capture_manifest as cm  # noqa: E402
import silver  # noqa: E402
import testkit as tk  # noqa: E402


class Crash(BaseException):
    """Stands in for a killed process: not an Exception, so the importer's own cleanup does not run."""


class Base(unittest.TestCase):
    def setUp(self):
        self.L = tk.Layout()

    def tearDown(self):
        self.L.cleanup()

    def import_ok(self, *args):
        r = self.L.run("import", *args)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def capture_dirs(self):
        return sorted(p.name for p in self.L.captures.iterdir() if not p.name.startswith(".")) if self.L.captures.exists() else []


class MultipleRecordings(Base):
    def test_only_the_newest_is_in_latest_json_but_every_recording_keeps_its_own_identity(self):
        m1, _ = tk.make_recording(self.L.src, "20261015_100000", modes=tk.FULL, speed=30)
        m2, _ = tk.make_recording(self.L.src, "20261015_110000", modes=tk.MIN, speed=90)
        m3, _ = tk.make_recording(self.L.src, "20261015_120000", modes=tk.FULL, speed=None)
        (self.L.src / "latest.json").write_text(json.dumps(
            {"frames_csv": "SH2Perf_20261015_120000_frames.csv", "capture_version": 3, "capture_id": m3["capture_id"],
             "modes": {"frametime": True, "counters": True, "poll": True, "overlay": True, "sample": False}}))
        before = tk.tree_hashes(self.L.src)
        r = self.L.run("import")
        self.assertEqual(r.returncode, 2, "several recordings: choose one")
        self.assertIn("--recording", r.stdout)
        self.assertEqual(self.capture_dirs(), [])
        self.assertFalse(self.L.index.exists())
        for stamp in ("20261015_100000", "20261015_110000", "20261015_120000"):
            self.import_ok("--recording", stamp)
        self.assertEqual(self.capture_dirs(), sorted([m1["capture_id"], m2["capture_id"], m3["capture_id"]]))
        self.assertEqual(tk.tree_hashes(self.L.src), before, "sources must be left exactly as they were")
        by_id = {line["capture_id"]: line for line in self.L.index_lines()}
        self.assertEqual(by_id[m1["capture_id"]]["game_speed"], {"value": 30, "origin": "planned"})
        self.assertEqual(by_id[m2["capture_id"]]["game_speed"], {"value": 90, "origin": "planned"})
        self.assertEqual(by_id[m3["capture_id"]]["game_speed"], {"value": None, "origin": "unknown"})

    def test_older_recording_does_not_inherit_the_newest_recordings_modes(self):
        old, _ = tk.make_recording(self.L.src, "20261015_100000", modes=tk.MIN)
        new, _ = tk.make_recording(self.L.src, "20261015_110000", modes=tk.FULL)
        (self.L.src / "latest.json").write_text(json.dumps({"frames_csv": "SH2Perf_20261015_110000_frames.csv", "capture_version": 2,
                                                            "modes": {"frametime": True, "counters": True, "poll": True, "overlay": True}}))
        self.import_ok("--recording", "20261015_100000")
        line = {x["capture_id"]: x for x in self.L.index_lines()}[old["capture_id"]]
        self.assertEqual(line["modes"]["counters"], False)
        self.assertIsNone(line["total"]["dip"], "counters off in this recording: null, not 0")
        self.assertIsNone(line["total"]["cpu_side_ms"])

    def test_different_measurement_modes_per_recording(self):
        a, _ = tk.make_recording(self.L.src, "20261015_100000", modes=tk.FULL)
        b, _ = tk.make_recording(self.L.src, "20261015_110000", modes=tk.MIN)
        self.import_ok("--recording", "20261015_100000")
        self.import_ok("--recording", "20261015_110000")
        lines = {x["capture_id"]: x for x in self.L.index_lines()}
        self.assertEqual(lines[a["capture_id"]]["total"]["dip"], 100)
        self.assertIsNone(lines[b["capture_id"]]["total"]["dip"])
        self.assertIsNotNone(lines[b["capture_id"]]["total"]["present_ms"], "frame time exists in every mode")
        self.assertEqual(self.L.summary(b["capture_id"])["switches"]["basis"], "manifest")


class SoftwareIdentity(Base):
    def test_hub_dll_replaced_after_the_recording_is_flagged_but_the_recorded_identity_stays(self):
        m, _ = tk.make_recording(self.L.src, "20261015_100000")
        recorded = {f["name"]: f["sha256"] for f in m["software"]["files"]}
        # rebuilt hub copied into the game folder after the recording
        (self.L.game / "Stronghold2AnalyseHub.dll").write_bytes(b"MZ hub build B")
        self.import_ok()
        s = self.L.summary(m["capture_id"])
        self.assertEqual(s["software"]["files"]["Stronghold2AnalyseHub.dll"], recorded["Stronghold2AnalyseHub.dll"],
                         "provenance is the hash taken in the session, not the one at import")
        self.assertEqual(s["software"]["changed_after_capture"], {"Stronghold2AnalyseHub.dll": "changed"})
        self.assertIn("software_changed_after_capture", s["flags"])
        imp = json.loads((self.L.captures / m["capture_id"] / "import.json").read_text())
        self.assertNotEqual(imp["observed_at_import"]["game_dir_hashes"]["Stronghold2AnalyseHub.dll"], recorded["Stronghold2AnalyseHub.dll"])

    def test_edited_config_is_not_a_software_change(self):
        m, _ = tk.make_recording(self.L.src, "20261015_100000")
        (self.L.game / "SH2Proxy.ini").write_text("[proxy]\r\nprofile=min\r\n")
        self.import_ok()
        self.assertNotIn("changed_after_capture", self.L.summary(m["capture_id"])["software"])

    def test_prepared_record_that_differs_from_the_session_is_flagged(self):
        other = tk.software_files({"hub_dll": ("Stronghold2AnalyseHub.dll", b"MZ hub build PREPARED")})
        m, _ = tk.make_recording(self.L.src, "20261015_100000", prepared=tk.prepared_record("dxvk", other))
        self.import_ok()
        s = self.L.summary(m["capture_id"])
        self.assertEqual(s["software"]["prepared_vs_session"], ["Stronghold2AnalyseHub.dll"])
        self.assertEqual(s["labels"]["variant"], "dxvk", "variant comes from the prepared record, not from the folder state at import")
        self.assertEqual(s["software"]["prepared"]["files"]["Stronghold2AnalyseHub.dll"], other[1]["sha256"])

    def test_prepared_record_that_matches_is_not_flagged(self):
        m, _ = tk.make_recording(self.L.src, "20261015_100000", prepared=tk.prepared_record())
        self.import_ok()
        self.assertNotIn("prepared_vs_session", self.L.summary(m["capture_id"])["software"])

    def test_hashes_are_full_sha256(self):
        m, _ = tk.make_recording(self.L.src, "20261015_100000")
        self.import_ok()
        for sha in self.L.summary(m["capture_id"])["software"]["files"].values():
            self.assertRegex(sha, r"^[0-9a-f]{64}$")
        short = json.loads(json.dumps(m))
        short["software"]["files"][0]["sha256"] = short["software"]["files"][0]["sha256"][:16]
        with self.assertRaises(cm.ManifestError):
            cm.parse(json.dumps(short).encode())


class MissingMetadataAndLegacy(Base):
    def test_recording_without_manifest_is_refused_unless_accepted_as_legacy(self):
        tk.make_legacy_recording(self.L.src, "20261015_100000")
        r = self.L.run("import")
        self.assertEqual(r.returncode, 5)
        self.assertIn("--legacy", r.stderr)
        self.assertEqual(self.capture_dirs(), [])

    def test_legacy_capture_is_neither_fault_free_nor_fully_measured(self):
        tk.make_legacy_recording(self.L.src, "20261015_100000")
        self.import_ok("--legacy", "--exp", "EXP-9", "--scenario", "S", "--troops", "5")
        s = self.L.summary("legacy-SH2Perf_20261015_100000")
        self.assertEqual(s["provenance"], "legacy")
        self.assertEqual(s["quality"]["technical"]["status"], "unknown")
        self.assertIsNone(s["quality"]["technical"]["capture_ok"], "legacy: not 'ok', not 'failed' - unknown")
        self.assertIsNone(s["switches"]["modes"], "legacy: modes unknown, not 'all on'")
        self.assertFalse(s["switches"]["known"])
        self.assertIn("legacy_unverified_origin", s["quality"]["benchmark_suitability"]["blockers"])
        self.assertFalse(s["quality"]["benchmark_suitability"]["usable_as_benchmark"])
        line = self.L.index_lines()[0]
        self.assertIsNone(line["modes"])
        self.assertNotIn("capture_ok", line)
        self.assertEqual((line["exp"], line["scenario"], line["troops"]), ("EXP-9", "S", 5))
        imp = json.loads((self.L.captures / s["capture_id"] / "import.json").read_text())
        self.assertTrue(all(f["sha256_basis"] == "import" for f in imp["files"]), "legacy hashes are import-time hashes")
        self.assertFalse(imp["verification"]["against_manifest"])

    def test_legacy_with_v2_latest_json_uses_its_modes_but_stays_unverified(self):
        tk.make_legacy_recording(self.L.src, "20261015_100000")
        (self.L.src / "latest.json").write_text(json.dumps({
            "frames_csv": "SH2Perf_20261015_100000_frames.csv", "capture_version": 2, "capture_ok": True,
            "modes": {"frametime": True, "counters": False, "poll": True, "overlay": True, "sample": False}}))
        self.import_ok("--legacy")
        s = self.L.summary("legacy-SH2Perf_20261015_100000")
        self.assertEqual(s["switches"]["modes"]["counters"], False)
        self.assertIn("latest.json", s["switches"]["basis"])
        self.assertIsNone(self.L.index_lines()[0]["total"]["dip"])
        self.assertIn("legacy_unverified_origin", s["quality"]["benchmark_suitability"]["blockers"])

    def test_old_bronze_folder_is_read_as_legacy_without_touching_it(self):
        d = self.L.captures / "20261015_EXP-000_baseline_SMOKE"
        d.mkdir(parents=True)
        (d / "SH2Perf_20261015_024518_frames.csv").write_bytes(tk.frames_csv())
        (d / "meta.json").write_text(json.dumps({"capture_id": d.name, "exp": "EXP-000", "variant": "baseline", "scenario": "SMOKE",
                                                  "troops": 0, "start": "2026-10-15T02:45:18", "hub_commit": "7a9e511", "cpu": "X", "gpu": "Y"}))
        (d / "latest.json").write_text(json.dumps({"frames_csv": "SH2Perf_20261015_024518_frames.csv", "hub_commit": "7a9e511"}))
        before = tk.tree_hashes(d)
        s = silver.derive(d)
        self.assertEqual(s["provenance"], "legacy")
        self.assertEqual(s["labels"]["variant"], "baseline")
        self.assertEqual(s["quality"]["technical"]["status"], "unknown")
        self.assertEqual(tk.tree_hashes(d), before)

    def test_minimal_manifest_leaves_everything_else_unknown(self):
        m, _ = tk.make_recording(self.L.src, "20261015_100000", minimal=True)
        self.import_ok()
        s = self.L.summary(m["capture_id"])
        self.assertEqual(s["game"]["game_speed"]["resolved"]["origin"], "unknown")
        self.assertEqual(s["game"]["paused"]["resolved"]["origin"], "unknown")
        self.assertFalse(s["switches"]["known"])
        self.assertIsNone(s["switches"]["modes"])
        self.assertEqual(s["quality"]["technical"]["status"], "unknown", "no health information: unknown, not ok")
        missing = s["quality"]["benchmark_suitability"]["missing_info"]
        for key in ("game_speed_unknown", "paused_unknown", "switches_unknown", "software_identity_missing", "variant_unknown"):
            self.assertIn(key, missing)

    def test_invalid_manifests_are_refused(self):
        cases = {"not json": lambda p: p.write_text("{nope"),
                 "wrong schema": lambda p: p.write_text(json.dumps({"schema": "x", "manifest_version": 1})),
                 "newer version": lambda p: p.write_text(json.dumps({**json.loads(p.read_text()), "manifest_version": 99})),
                 "unsafe id": lambda p: p.write_text(json.dumps({**json.loads(p.read_text()), "capture_id": "../evil"})),
                 "path in file name": lambda p: p.write_text(json.dumps({**json.loads(p.read_text()), "files": [
                     {"role": "frames", "name": "../x.csv", "size": 1, "sha256": "0" * 64}]}))}
        for label, mutate in cases.items():
            with self.subTest(label):
                lay = tk.Layout()
                try:
                    tk.make_recording(lay.src, "20261015_100000")
                    mutate(lay.src / "SH2Perf_20261015_100000_manifest.json")
                    r = lay.run("import")
                    self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
                    self.assertFalse(lay.captures.exists() and any(lay.captures.iterdir()))
                finally:
                    lay.cleanup()


class RepeatAndInterrupt(Base):
    def test_repeated_import_creates_no_duplicate(self):
        m, _ = tk.make_recording(self.L.src, "20261015_100000", speed=90)
        self.import_ok("--exp", "E", "--scenario", "S", "--troops", "1")
        bronze_before = tk.tree_hashes(self.L.captures)
        index_before = self.L.index.read_text()
        r = self.import_ok("--exp", "E", "--scenario", "S", "--troops", "1")
        self.assertIn("already imported", r.stdout)
        self.assertEqual(tk.tree_hashes(self.L.captures), bronze_before)
        self.assertEqual(self.L.index.read_text(), index_before)
        self.assertEqual(len(self.L.index_lines()), 1)
        self.assertEqual(self.capture_dirs(), [m["capture_id"]])

    def test_new_labels_on_a_repeat_do_not_touch_bronze(self):
        m, _ = tk.make_recording(self.L.src, "20261015_100000")
        self.import_ok("--exp", "E1")
        bronze_before = tk.tree_hashes(self.L.captures)
        self.import_ok("--exp", "E2")
        self.assertEqual(tk.tree_hashes(self.L.captures), bronze_before)
        self.assertEqual(self.L.index_lines()[0]["exp"], "E2")
        ann = json.loads((self.L.root / "data" / "annotations" / f"{m['capture_id']}.json").read_text())
        self.assertEqual([h["new"] for h in ann["history"]], ["E1", "E2"])

    def test_import_killed_while_copying_leaves_only_staging_and_the_rerun_completes(self):
        m, stem = tk.make_recording(self.L.src, "20261015_100000")
        rec = bronze.Recording(self.L.src, stem)
        copied = []

        def crash(point, **ctx):
            if point == "copy":
                copied.append(ctx["name"])
                if len(copied) == 2:
                    raise Crash()

        with self.assertRaises(Crash):
            bronze.import_recording(rec, self.L.captures, inject=crash)
        self.assertEqual(self.capture_dirs(), [], "nothing is committed")
        self.assertTrue((self.L.captures / ".staging" / m["capture_id"]).exists(), "a crash leaves its staging copies behind")
        self.import_ok()
        self.assertEqual(self.capture_dirs(), [m["capture_id"]])
        self.assertFalse((self.L.captures / ".staging" / m["capture_id"]).exists())
        self.assertEqual(self.L.run("verify", m["capture_id"]).returncode, 0)
        self.assertEqual(len(self.L.index_lines()), 1)

    def test_import_killed_before_the_rename_leaves_no_capture(self):
        m, stem = tk.make_recording(self.L.src, "20261015_100000")
        rec = bronze.Recording(self.L.src, stem)

        def crash(point, **ctx):
            if point == "before_commit":
                raise Crash()

        with self.assertRaises(Crash):
            bronze.import_recording(rec, self.L.captures, inject=crash)
        self.assertEqual(self.capture_dirs(), [])
        self.import_ok()
        self.assertEqual(self.capture_dirs(), [m["capture_id"]])

    def test_import_killed_after_commit_before_silver_is_repaired_by_the_rerun(self):
        m, stem = tk.make_recording(self.L.src, "20261015_100000")
        rec = bronze.Recording(self.L.src, stem)

        def crash(point, **ctx):
            if point == "after_commit":
                raise Crash()

        with self.assertRaises(Crash):
            bronze.import_recording(rec, self.L.captures, inject=crash)
        self.assertEqual(self.capture_dirs(), [m["capture_id"]], "the commit is complete")
        self.assertFalse(self.L.index.exists(), "silver is still missing")
        r = self.import_ok()
        self.assertIn("already imported", r.stdout)
        self.assertEqual(len(self.L.index_lines()), 1)
        self.assertTrue((self.L.root / "data" / "silver" / m["capture_id"] / "summary.json").exists())


class DamagedOrConflictingSources(Base):
    def assert_nothing_written(self):
        self.assertEqual(self.capture_dirs(), [])
        self.assertFalse((self.L.captures / ".staging").exists() and any((self.L.captures / ".staging").iterdir()))
        self.assertFalse(self.L.index.exists())

    def test_incomplete_file_is_refused(self):
        m, stem = tk.make_recording(self.L.src, "20261015_100000")
        f = self.L.src / f"{stem}_frames.csv"
        f.write_bytes(f.read_bytes()[:-37])                       # copy cut short
        r = self.L.run("import")
        self.assertEqual(r.returncode, 4)
        self.assertIn("incomplete or truncated", r.stderr)
        self.assert_nothing_written()

    def test_hash_conflict_with_equal_size_is_refused(self):
        m, stem = tk.make_recording(self.L.src, "20261015_100000")
        f = self.L.src / f"{stem}_frames.csv"
        data = bytearray(f.read_bytes())
        data[-5] = ord("9") if data[-5] != ord("9") else ord("8")
        f.write_bytes(bytes(data))
        r = self.L.run("import")
        self.assertEqual(r.returncode, 4)
        self.assertIn("hash conflict", r.stderr)
        self.assert_nothing_written()

    def test_missing_listed_file_is_refused(self):
        m, stem = tk.make_recording(self.L.src, "20261015_100000")
        (self.L.src / f"{stem}_threads.csv").unlink()
        r = self.L.run("import")
        self.assertEqual(r.returncode, 4)
        self.assertIn("missing", r.stderr)
        self.assert_nothing_written()

    def test_same_capture_id_with_different_content_is_a_conflict(self):
        m, stem = tk.make_recording(self.L.src, "20261015_100000", capture_id="rec-fixed-id")
        self.import_ok()
        before = tk.tree_hashes(self.L.captures)
        index_before = self.L.index.read_text()
        # a different recording that claims the same capture id
        shutil.rmtree(self.L.src)
        self.L.src.mkdir()
        tk.make_recording(self.L.src, "20261015_130000", capture_id="rec-fixed-id", frames=30)
        r = self.L.run("import")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("different content", r.stderr)
        self.assertEqual(tk.tree_hashes(self.L.captures), before, "existing raw data stays")
        self.assertEqual(self.L.index.read_text(), index_before)

    def test_existing_foreign_folder_with_the_id_is_a_conflict_and_untouched(self):
        m, stem = tk.make_recording(self.L.src, "20261015_100000", capture_id="rec-taken")
        (self.L.captures / "rec-taken").mkdir(parents=True)
        (self.L.captures / "rec-taken" / "notes.txt").write_text("someone else's data")
        r = self.L.run("import")
        self.assertEqual(r.returncode, 3)
        self.assertEqual(tk.tree_hashes(self.L.captures / "rec-taken"), {"notes.txt": tk.sha(b"someone else's data")})

    def test_write_error_aborts_cleanly_and_the_retry_works(self):
        m, stem = tk.make_recording(self.L.src, "20261015_100000")
        rec = bronze.Recording(self.L.src, stem)
        sources = tk.tree_hashes(self.L.src)

        def disk_full(point, **ctx):
            if point == "copy" and ctx["name"].endswith("_threads.csv"):
                raise OSError(errno.ENOSPC, "No space left on device")

        with self.assertRaises(bronze.ImportFailure) as ctx:
            bronze.import_recording(rec, self.L.captures, inject=disk_full)
        self.assertEqual(ctx.exception.code, bronze.EXIT_WRITE)
        self.assertEqual(self.capture_dirs(), [])
        self.assertFalse((self.L.captures / ".staging" / m["capture_id"]).exists(), "partial copies are removed")
        self.assertEqual(tk.tree_hashes(self.L.src), sources, "the source is untouched")
        self.import_ok()
        self.assertEqual(self.capture_dirs(), [m["capture_id"]])

    def test_unwritable_target_reports_a_write_error_code(self):
        m, stem = tk.make_recording(self.L.src, "20261015_100000")
        (self.L.root / "captures").write_text("a file where the folder should be")
        r = self.L.run("import")
        self.assertIn(r.returncode, (bronze.EXIT_WRITE, 1))
        self.assertNotEqual(r.returncode, 0)

    def test_sources_are_never_deleted_not_even_after_success(self):
        m, stem = tk.make_recording(self.L.src, "20261015_100000", samples=True)
        before = tk.tree_hashes(self.L.src)
        self.import_ok()
        self.assertEqual(tk.tree_hashes(self.L.src), before)

    def test_existing_raw_captures_are_not_changed_by_import_or_rebuild(self):
        old = self.L.captures / "20261015_EXP-000_baseline_SMOKE"
        old.mkdir(parents=True)
        (old / "SH2Perf_20261015_024518_frames.csv").write_bytes(tk.frames_csv())
        (old / "meta.json").write_text(json.dumps({"capture_id": old.name, "exp": "EXP-000", "variant": "baseline",
                                                    "scenario": "SMOKE", "troops": 0, "start": "2026-10-15T02:45:18"}))
        before = tk.tree_hashes(old)
        tk.make_recording(self.L.src, "20261015_100000")
        self.import_ok()
        r = self.L.run("rebuild", "--write")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(tk.tree_hashes(old), before)


class InterruptedRecording(Base):
    def test_interrupted_recording_is_refused_by_default_and_kept_with_a_flag(self):
        m, stem = tk.make_recording(self.L.src, "20261015_100000", status="recording")
        r = self.L.run("import")
        self.assertEqual(r.returncode, 5)
        self.assertIn("not finalized", r.stderr)
        self.assertEqual(self.capture_dirs(), [])
        self.import_ok("--allow-interrupted")
        s = self.L.summary(m["capture_id"])
        self.assertEqual(s["quality"]["technical"]["status"], "incomplete")
        self.assertEqual(s["quality"]["technical"]["completion"], "interrupted")
        self.assertIn("interrupted", s["quality"]["benchmark_suitability"]["blockers"])
        self.assertIn("interrupted", s["flags"])
        imp = json.loads((self.L.captures / m["capture_id"] / "import.json").read_text())
        self.assertTrue(all(f["sha256_basis"] == "import" for f in imp["files"]), "no hub hash exists for an interrupted recording")

    def test_hub_reported_write_failure_is_degraded_not_ok(self):
        m, _ = tk.make_recording(self.L.src, "20261015_100000", quality={
            "capture_ok": False, "frames_dropped": 4, "frames_lost_write": 0, "write_errors": 0, "files_closed": True, "hashes_complete": True})
        self.import_ok()
        s = self.L.summary(m["capture_id"])
        self.assertEqual(s["quality"]["technical"]["status"], "degraded")
        self.assertEqual(self.L.index_lines()[0]["capture_loss"]["dropped"], 4)


class GameSpeedAndPause(Base):
    def test_missing_speed_stays_unknown_everywhere(self):
        m, _ = tk.make_recording(self.L.src, "20261015_100000", speed=None)
        self.import_ok()
        g = self.L.summary(m["capture_id"])["game"]["game_speed"]
        self.assertEqual(g["resolved"], {"value": None, "origin": "unknown", "conflict": False, "planned_differs": False})
        self.assertEqual(g["by_origin"], {"planned": None, "user_confirmed": None, "observed": None})
        self.assertEqual(self.L.index_lines()[0]["game_speed"], {"value": None, "origin": "unknown"})

    def test_speed_30_and_90_stay_distinguishable_and_numeric(self):
        a, _ = tk.make_recording(self.L.src, "20261015_100000", speed=30)
        b, _ = tk.make_recording(self.L.src, "20261015_110000", speed=90)
        self.import_ok("--recording", "20261015_100000")
        self.import_ok("--recording", "20261015_110000")
        speeds = {x["capture_id"]: x["game_speed"]["value"] for x in self.L.index_lines()}
        self.assertEqual(speeds, {a["capture_id"]: 30, b["capture_id"]: 90})
        self.assertIsInstance(speeds[a["capture_id"]], int)
        self.assertEqual(len(self.capture_dirs()), 2)

    def test_pause_is_independent_of_speed(self):
        m, _ = tk.make_recording(self.L.src, "20261015_100000", speed=90, paused=True)
        self.import_ok()
        g = self.L.summary(m["capture_id"])["game"]
        self.assertEqual((g["game_speed"]["resolved"]["value"], g["paused"]["resolved"]["value"]), (90, True))
        self.assertEqual(g["paused"]["resolved"]["origin"], "planned")

    def test_origins_planned_user_confirmed_and_observed_stay_apart(self):
        m, _ = tk.make_recording(self.L.src, "20261015_100000", speed=90)
        self.import_ok()
        r = self.L.run("annotate", m["capture_id"], "--game-speed", "60")
        self.assertEqual(r.returncode, 0, r.stderr)
        g = self.L.summary(m["capture_id"])["game"]["game_speed"]
        self.assertEqual(g["by_origin"], {"planned": 90, "user_confirmed": 60, "observed": None})
        self.assertEqual(g["resolved"], {"value": 60, "origin": "user_confirmed", "conflict": False, "planned_differs": True})
        manifest_after = json.loads((self.L.captures / m["capture_id"] / "manifest.json").read_text())
        self.assertEqual(manifest_after["game"]["game_speed"]["origin"], "planned", "the raw manifest keeps what the hub wrote")

    def test_observed_value_beats_the_plan_and_conflicts_with_a_different_user_value(self):
        # a future hub may observe the speed; the reader already keeps that origin apart
        m, _ = tk.make_recording(self.L.src, "20261015_100000", speed=45, speed_origin="observed")
        self.import_ok()
        self.assertEqual(self.L.summary(m["capture_id"])["game"]["game_speed"]["resolved"]["origin"], "observed")
        self.L.run("annotate", m["capture_id"], "--game-speed", "45")
        self.assertFalse(self.L.summary(m["capture_id"])["game"]["game_speed"]["resolved"]["conflict"])
        self.L.run("annotate", m["capture_id"], "--game-speed", "50")
        res = self.L.summary(m["capture_id"])["game"]["game_speed"]["resolved"]
        self.assertTrue(res["conflict"])
        self.assertIsNone(res["value"], "disagreeing origins are never resolved by guessing")

    def test_annotation_rejects_non_numbers_but_accepts_any_number(self):
        m, _ = tk.make_recording(self.L.src, "20261015_100000")
        self.import_ok()
        for bad in ("fast", "nan", "inf"):
            self.assertNotEqual(self.L.run("annotate", m["capture_id"], "--game-speed", bad).returncode, 0, bad)
        self.assertEqual(self.L.run("annotate", m["capture_id"], "--game-speed", "1.5").returncode, 0)
        self.assertEqual(self.L.summary(m["capture_id"])["game"]["game_speed"]["resolved"]["value"], 1.5)

    def test_hub_value_with_origin_unknown_or_non_number_is_refused(self):
        with self.assertRaises(cm.ManifestError):
            cm.parse(json.dumps({**json.loads(json.dumps(tk.make_recording(self.L.src, "20261015_100000", speed=90)[0])),
                                 "game": {"game_speed": {"value": 90, "origin": "unknown"}}}).encode())
        with self.assertRaises(cm.ManifestError):
            cm.parse(json.dumps({**json.loads(json.dumps(tk.make_recording(self.L.src, "20261015_110000", speed=90)[0])),
                                 "game": {"game_speed": {"value": "90", "origin": "planned"}}}).encode())


class QualityVersusSuitability(Base):
    def test_good_technical_quality_alone_is_not_a_benchmark(self):
        m, _ = tk.make_recording(self.L.src, "20261015_100000", speed=90)
        self.import_ok()
        q = self.L.summary(m["capture_id"])["quality"]
        self.assertEqual(q["technical"]["status"], "ok")
        self.assertEqual(q["benchmark_suitability"]["verdict"], "unknown")
        self.assertFalse(q["benchmark_suitability"]["usable_as_benchmark"])

    def test_user_verdict_counts_only_without_blockers(self):
        good, _ = tk.make_recording(self.L.src, "20261015_100000", speed=90)
        bad, _ = tk.make_recording(self.L.src, "20261015_110000", speed=90, quality={
            "capture_ok": False, "frames_dropped": 9, "frames_lost_write": 0, "write_errors": 0, "files_closed": True, "hashes_complete": True})
        self.import_ok("--recording", "20261015_100000")
        self.import_ok("--recording", "20261015_110000")
        for cid in (good["capture_id"], bad["capture_id"]):
            self.assertEqual(self.L.run("annotate", cid, "--suitability", "suitable", "--reason", "looks fine").returncode, 0)
        self.assertTrue(self.L.summary(good["capture_id"])["quality"]["benchmark_suitability"]["usable_as_benchmark"])
        sb = self.L.summary(bad["capture_id"])["quality"]["benchmark_suitability"]
        self.assertEqual(sb["verdict"], "suitable")
        self.assertFalse(sb["usable_as_benchmark"])
        self.assertIn("technical_quality_degraded", sb["blockers"])


class ReproducibleSilver(Base):
    def test_rebuild_reproduces_silver_byte_for_byte_from_bronze(self):
        m, _ = tk.make_recording(self.L.src, "20261015_100000", speed=90, samples=True, prepared=tk.prepared_record())
        self.import_ok("--exp", "E", "--scenario", "S", "--troops", "3")
        self.L.run("annotate", m["capture_id"], "--game-speed", "90", "--paused", "false")
        silver_dir = self.L.root / "data" / "silver"
        first = tk.tree_hashes(silver_dir)
        index_first = self.L.index.read_text()
        shutil.rmtree(silver_dir)
        self.L.index.unlink()
        r = self.L.run("rebuild", "--write")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(tk.tree_hashes(silver_dir), first)
        self.assertEqual(self.L.index.read_text(), index_first)
        s = self.L.summary(m["capture_id"])
        self.assertEqual(s["tool"], {"name": "sh2perf-silver", "version": silver.TOOL["version"]})
        self.assertIn(f"sh2perf-silver {silver.TOOL['version']}", self.L.index_lines()[0]["silver"])
        check = self.L.run("rebuild")
        self.assertIn("1 index lines identical", check.stdout)

    def test_verify_detects_changed_raw_data(self):
        m, stem = tk.make_recording(self.L.src, "20261015_100000")
        self.import_ok()
        self.assertEqual(self.L.run("verify", m["capture_id"]).returncode, 0)
        f = self.L.captures / m["capture_id"] / f"{stem}_frames.csv"
        f.write_bytes(f.read_bytes() + b"x")
        r = self.L.run("verify", m["capture_id"])
        self.assertEqual(r.returncode, 4)
        self.assertIn("raw data changed", r.stderr)


class ManifestContract(unittest.TestCase):
    def manifest(self):
        lay = tk.Layout()
        try:
            return tk.make_recording(lay.src, "20261015_100000", speed=30)[0]
        finally:
            lay.cleanup()

    def test_unknown_keys_are_ignored_within_a_version(self):
        m = self.manifest()
        m["something_new"] = {"x": 1}
        self.assertEqual(cm.parse(json.dumps(m).encode())["capture_id"], m["capture_id"])

    def test_newer_version_is_refused(self):
        m = self.manifest()
        m["manifest_version"] = cm.SUPPORTED_VERSION + 1
        with self.assertRaises(cm.ManifestError):
            cm.parse(json.dumps(m).encode())

    def test_finalized_needs_full_hashes_but_recording_does_not(self):
        m = self.manifest()
        m["files"][0]["sha256"] = None
        with self.assertRaises(cm.ManifestError):
            cm.parse(json.dumps(m).encode())
        m["status"] = "recording"
        self.assertEqual(cm.completion(cm.parse(json.dumps(m).encode())), "interrupted")

    def test_software_changes(self):
        rec = {"a.dll": "1" * 64, "b.dll": "2" * 64, "c.dll": "3" * 64, "d.dll": None}
        now = {"a.dll": "1" * 64, "b.dll": "9" * 64, "c.dll": None, "d.dll": "4" * 64}
        self.assertEqual(cm.software_changes(rec, now), {"b.dll": "changed", "c.dll": "missing_now", "d.dll": "unverifiable"})


if __name__ == "__main__":
    unittest.main(verbosity=1)
