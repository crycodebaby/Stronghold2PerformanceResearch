"""Regression tests for the protection rules of D012 (work order "Schutzluecken schliessen").

1. reference release   2. bronze verified before use   3. write lock (real processes)   4. names and file roles

Run: python -I tools/test_hardening.py   (temp folders only)
"""
import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import bronze  # noqa: E402
import capture_manifest as cm  # noqa: E402
import testkit as tk  # noqa: E402


def codes(summary):
    return [r["code"] for r in summary["quality"]["benchmark_suitability"]["rejections"]]


class Base(unittest.TestCase):
    def setUp(self):
        self.L = tk.Layout()

    def tearDown(self):
        self.L.cleanup()

    def imp(self, *args):
        r = self.L.run("import", *args)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def suit(self, cid):
        return self.L.summary(cid)["quality"]["benchmark_suitability"]


# --- 1. reference release ---------------------------------------------------------------------------------

class ReferenceRelease(Base):
    def release(self, cid):
        r = self.L.run("annotate", cid, "--suitability", "suitable", "--reason", "looks right")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_unknown_speed_cannot_be_overruled_by_the_user(self):
        m, _ = tk.reference_recording(self.L.src, "20261015_100000", speed=None)
        self.imp()
        self.release(m["capture_id"])
        s = self.L.summary(m["capture_id"])
        self.assertEqual(s["quality"]["benchmark_suitability"]["verdict"], "suitable", "the user's release is recorded as given")
        self.assertFalse(self.suit(m["capture_id"])["usable_as_benchmark"])
        self.assertIn("game_speed_unknown", codes(s))

    def test_conflicting_speed_cannot_be_overruled_by_the_user(self):
        m, _ = tk.reference_recording(self.L.src, "20261015_100000", speed=45, speed_origin="observed")
        self.imp()
        self.assertEqual(self.L.run("annotate", m["capture_id"], "--game-speed", "50").returncode, 0)
        self.release(m["capture_id"])
        s = self.L.summary(m["capture_id"])
        self.assertFalse(self.suit(m["capture_id"])["usable_as_benchmark"])
        self.assertIn("game_speed_conflict", codes(s))
        self.assertNotIn("game_speed_unknown", codes(s), "a conflict is named as a conflict")

    def test_complete_intact_recording_needs_the_release_and_can_get_it(self):
        m, _ = tk.reference_recording(self.L.src, "20261015_100000")
        self.imp()
        before = self.suit(m["capture_id"])
        self.assertEqual(before["integrity"]["status"], "ok")
        self.assertTrue(before["completeness"]["complete"], before["completeness"])
        self.assertFalse(before["usable_as_benchmark"], "no release yet")
        self.assertEqual([r["code"] for r in before["rejections"]], ["not_released"])
        self.release(m["capture_id"])
        after = self.suit(m["capture_id"])
        self.assertTrue(after["usable_as_benchmark"])
        self.assertEqual(after["rejections"], [])
        self.assertTrue(self.L.index_lines()[0]["usable_as_benchmark"])

    def test_missing_required_description_is_listed_with_reasons(self):
        m, _ = tk.make_recording(self.L.src, "20261015_100000", speed=90, single_phase=True)   # no labels, no prepared record
        self.imp()
        self.release(m["capture_id"])
        c = codes(self.L.summary(m["capture_id"]))
        for code in ("experiment_unknown", "scenario_unknown", "variant_unknown", "pause_unknown"):
            self.assertIn(code, c)
        self.assertTrue(all(r["text"] for r in self.suit(m["capture_id"])["rejections"]), "every rejection has a readable text")

    def test_unknown_switches_and_software_identity_reject(self):
        m, _ = tk.reference_recording(self.L.src, "20261015_100000", minimal=True)
        self.imp()
        self.release(m["capture_id"])
        c = codes(self.L.summary(m["capture_id"]))
        for code in ("switches_unknown", "software_identity_missing", "game_speed_unknown"):
            self.assertIn(code, c)

    def test_technical_damage_rejects_even_with_complete_description(self):
        m, _ = tk.reference_recording(self.L.src, "20261015_100000", quality={
            "capture_ok": False, "frames_dropped": 9, "frames_lost_write": 0, "write_errors": 0,
            "files_closed": True, "hashes_complete": True})
        self.imp()
        self.release(m["capture_id"])
        s = self.L.summary(m["capture_id"])
        self.assertEqual(self.suit(m["capture_id"])["integrity"]["status"], "degraded")
        self.assertTrue(self.suit(m["capture_id"])["completeness"]["complete"], "completeness is judged apart from integrity")
        self.assertIn("technical_quality_degraded", codes(s))
        self.assertFalse(self.suit(m["capture_id"])["usable_as_benchmark"])

    def test_global_pause_is_no_proof_for_a_mixed_recording(self):
        m, _ = tk.reference_recording(self.L.src, "20261015_100000", single_phase=False, paused=True)   # markers 0 and 1
        self.imp()
        s = self.L.summary(m["capture_id"])
        self.assertEqual(len(s["phases"]), 2)
        self.release(m["capture_id"])
        c = codes(self.L.summary(m["capture_id"]))
        self.assertIn("pause_unknown_phase_0", c)
        self.assertIn("pause_unknown_phase_1", c)
        self.assertFalse(self.suit(m["capture_id"])["usable_as_benchmark"])
        pp = self.L.summary(m["capture_id"])["game"]["paused"]
        self.assertEqual(pp["by_phase"], {"0": {"value": None, "origin": "unknown"}, "1": {"value": None, "origin": "unknown"}})
        self.assertEqual(pp["recording_level"]["value"], True, "the planned global value stays visible, as a recording-level statement")

    def test_phase_confirmation_by_the_user_completes_a_mixed_recording(self):
        m, _ = tk.reference_recording(self.L.src, "20261015_100000", single_phase=False, paused=None)
        self.imp()
        r = self.L.run("annotate", m["capture_id"], "--phase-paused", "0=true", "--phase-paused", "1=false")
        self.assertEqual(r.returncode, 0, r.stderr)
        pp = self.L.summary(m["capture_id"])["game"]["paused"]["by_phase"]
        self.assertEqual(pp["0"], {"value": True, "origin": "user_confirmed"})
        self.assertEqual(pp["1"], {"value": False, "origin": "user_confirmed"})
        self.release(m["capture_id"])
        self.assertTrue(self.suit(m["capture_id"])["usable_as_benchmark"])

    def test_phase_pause_for_a_phase_that_does_not_exist_is_refused(self):
        m, _ = tk.reference_recording(self.L.src, "20261015_100000")
        self.imp()
        self.assertNotEqual(self.L.run("annotate", m["capture_id"], "--phase-paused", "7=true").returncode, 0)

    def test_single_phase_recording_takes_the_recording_level_pause(self):
        m, _ = tk.reference_recording(self.L.src, "20261015_100000", paused=True)
        self.imp()
        self.assertEqual(self.L.summary(m["capture_id"])["game"]["paused"]["by_phase"]["0"], {"value": True, "origin": "planned"})
        self.assertTrue(self.suit(m["capture_id"])["completeness"]["complete"])


# --- 2. bronze verified before use ------------------------------------------------------------------------

def damage_append(p):
    p.write_bytes(p.read_bytes() + b"x")


def damage_truncate(p):
    p.write_bytes(p.read_bytes()[:-20])


def damage_remove(p):
    p.unlink()


class BronzeIntegrity(Base):
    def setUp(self):
        super().setUp()
        self.m, self.stem = tk.reference_recording(self.L.src, "20261015_100000")
        self.cid = self.m["capture_id"]
        self.imp()
        self.cap = self.L.captures / self.cid

    def damaged_run(self, target, damage):
        path = self.cap / target
        damage(path)
        after = tk.tree_hashes(self.cap)
        summary_before = (self.L.root / "data" / "silver" / self.cid / "summary.json").read_bytes()
        index_before = self.L.index.read_text()
        r = self.L.run("import")
        self.assertEqual(r.returncode, 4, "re-import of a damaged capture: " + r.stdout + r.stderr)
        self.assertNotIn("already imported", r.stdout)
        self.assertIn("damaged", r.stderr)
        r = self.L.run("annotate", self.cid, "--game-speed", "60")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        self.assertFalse((self.L.root / "data" / "annotations" / f"{self.cid}.json").exists(), "no annotation on a damaged basis")
        self.assertEqual(self.L.run("verify", self.cid).returncode, 4)
        r = self.L.run("rebuild", "--write")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        self.assertEqual((self.L.root / "data" / "silver" / self.cid / "summary.json").read_bytes(), summary_before,
                         "earlier results are kept")
        self.assertTrue((self.L.root / "data" / "silver" / self.cid / "INVALID.json").exists(), "and marked as not valid")
        line = self.L.index_lines()[0]
        self.assertIs(line["silver_valid"], False)
        self.assertEqual(line["capture_id"], self.cid)
        self.assertEqual(tk.tree_hashes(self.cap), after, "bronze is never repaired or changed by the tools")
        self.assertNotEqual(self.L.index.read_text(), index_before)

    def test_changed_raw_file(self):
        self.damaged_run(f"{self.stem}_frames.csv", damage_append)

    def test_truncated_raw_file(self):
        self.damaged_run(f"{self.stem}_frames.csv", damage_truncate)

    def test_removed_raw_file(self):
        self.damaged_run(f"{self.stem}_threads.csv", damage_remove)

    def test_removed_manifest_copy(self):
        self.damaged_run("manifest.json", damage_remove)

    def test_changed_manifest_copy(self):
        self.damaged_run("manifest.json", damage_append)

    def test_restored_data_makes_the_capture_valid_again(self):
        path = self.cap / f"{self.stem}_frames.csv"
        original = path.read_bytes()
        damage_append(path)
        self.assertEqual(self.L.run("rebuild", "--write").returncode, 4)
        path.write_bytes(original)
        r = self.L.run("rebuild", "--write")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse((self.L.root / "data" / "silver" / self.cid / "INVALID.json").exists())
        self.assertNotIn("silver_valid", self.L.index_lines()[0])
        self.assertIn("already imported", self.imp().stdout)

    def test_unchanged_data_stays_idempotent(self):
        before = tk.tree_hashes(self.L.root)
        r = self.imp()
        self.assertIn("already imported", r.stdout)
        self.assertEqual(self.L.run("rebuild", "--write").returncode, 0)
        after = tk.tree_hashes(self.L.root)
        self.assertEqual({k: v for k, v in after.items() if not k.endswith(".lock")},
                         {k: v for k, v in before.items() if not k.endswith(".lock")})

    def test_one_damaged_capture_does_not_hide_the_good_ones(self):
        m2, _ = tk.reference_recording(self.L.src, "20261015_110000")
        self.imp("--recording", "20261015_110000")
        damage_append(self.cap / f"{self.stem}_frames.csv")
        r = self.L.run("rebuild", "--write")
        self.assertEqual(r.returncode, 4)
        lines = {x["capture_id"]: x for x in self.L.index_lines()}
        self.assertIs(lines[self.cid]["silver_valid"], False)
        self.assertNotIn("silver_valid", lines[m2["capture_id"]])
        self.assertIn(self.cid, r.stderr)


# --- 3. write lock with real processes --------------------------------------------------------------------

HOLDER = (
    "import sys; sys.path.insert(0, sys.argv[1]); import filelock\n"
    "with filelock.exclusive(sys.argv[2], 30):\n"
    "    print('locked', flush=True); sys.stdin.read()\n"
)


class WriteLock(Base):
    def spawn_import(self, *extra, pause=None):
        env = dict(os.environ, SH2PERF_NO_HARDWARE="1")
        if pause:
            env["SH2PERF_TEST_PAUSE_BEFORE_COMMIT"] = str(pause)
        cmd = [sys.executable, "-I", str(TOOLS / "ingest.py"), "import", *extra, "--src", str(self.L.src),
               "--captures", str(self.L.captures), "--index", str(self.L.index), "--game-dir", str(self.L.game)]
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", env=env)

    def wait_for(self, cond, what, timeout=20):
        t0 = time.time()
        while not cond():
            if time.time() - t0 > timeout:
                self.fail("timeout waiting for " + what)
            time.sleep(0.05)

    def lock_path(self):
        return self.L.index.parent / ".sh2perf.lock"

    def test_busy_lock_is_reported_and_leaves_everything_alone_then_a_killed_holder_frees_it(self):
        tk.make_recording(self.L.src, "20261015_100000")
        self.L.index.parent.mkdir(parents=True)
        with subprocess.Popen([sys.executable, "-I", "-c", HOLDER, str(TOOLS), str(self.lock_path())],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True) as holder:     # the with-block closes both pipes
            try:
                self.assertEqual(holder.stdout.readline().strip(), "locked")
                t0 = time.time()
                r = self.L.run("import", "--lock-timeout", "1")
                self.assertEqual(r.returncode, 7, r.stdout + r.stderr)
                self.assertIn("busy", r.stderr)
                self.assertLess(time.time() - t0, 10)
                self.assertFalse(self.L.captures.exists() and any(self.L.captures.iterdir()), "nothing written while the lock is held")
                holder.kill()                            # the holder dies without releasing anything
                holder.wait()
                self.assertEqual(self.L.run("import", "--lock-timeout", "5").returncode, 0)
            finally:
                holder.kill()

    def test_active_staging_is_never_taken_for_an_orphan(self):
        m, stem = tk.make_recording(self.L.src, "20261015_100000")
        flag = self.L.root / "release.flag"
        a = self.spawn_import(pause=flag)
        try:
            staging = self.L.captures / ".staging" / m["capture_id"]
            self.wait_for(lambda: staging.exists() and (staging / "import.json").exists(), "A to stage its copy")
            snapshot = tk.tree_hashes(staging)
            b = self.spawn_import("--lock-timeout", "1")
            out, err = b.communicate(timeout=30)
            self.assertEqual(b.returncode, 7, out + err)
            self.assertEqual(tk.tree_hashes(staging), snapshot, "the active staging folder is untouched")
            flag.write_text("go")
            out, err = a.communicate(timeout=30)
            self.assertEqual(a.returncode, 0, out + err)
        finally:
            a.kill()
            a.communicate()
        self.assertEqual(sorted(p.name for p in self.L.captures.iterdir() if not p.name.startswith(".")), [m["capture_id"]])
        self.assertEqual(self.L.run("verify", m["capture_id"]).returncode, 0)

    def test_killed_importer_leaves_a_staging_that_the_next_importer_may_remove(self):
        m, stem = tk.make_recording(self.L.src, "20261015_100000")
        flag = self.L.root / "never.flag"
        a = self.spawn_import(pause=flag)
        staging = self.L.captures / ".staging" / m["capture_id"]
        self.wait_for(lambda: staging.exists() and (staging / "import.json").exists(), "A to stage its copy")
        a.kill()
        a.communicate()
        r = self.L.run("import", "--lock-timeout", "5")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(staging.exists())
        self.assertEqual(self.L.run("verify", m["capture_id"]).returncode, 0)

    def test_parallel_imports_of_different_recordings_lose_nothing(self):
        stamps = [f"20261015_1{n}0000" for n in range(5)]
        ms = [tk.make_recording(self.L.src, s)[0] for s in stamps]
        procs = [self.spawn_import("--recording", s) for s in stamps]
        results = [p.communicate(timeout=120) + (p.returncode,) for p in procs]
        for out, err, rc in results:
            self.assertEqual(rc, 0, out + err)
        self.assertEqual({x["capture_id"] for x in self.L.index_lines()}, {m["capture_id"] for m in ms}, "no index entry lost")
        self.assertEqual(len(self.L.index.read_text().splitlines()), 5)
        for m in ms:
            self.assertEqual(self.L.run("verify", m["capture_id"]).returncode, 0)
            self.assertTrue((self.L.root / "data" / "silver" / m["capture_id"] / "summary.json").exists())

    def test_parallel_imports_of_the_same_recording_end_with_one_capture(self):
        m, _ = tk.make_recording(self.L.src, "20261015_100000")
        procs = [self.spawn_import() for _ in range(4)]
        results = [p.communicate(timeout=120) + (p.returncode,) for p in procs]
        for out, err, rc in results:
            self.assertEqual(rc, 0, out + err)
        self.assertEqual(sum("imported " in o and "already" not in o.split("\n")[0] for o, _, _ in results) >= 1, True)
        self.assertEqual(len(self.L.index.read_text().splitlines()), 1)
        self.assertEqual(self.L.run("verify", m["capture_id"]).returncode, 0)

    def test_parallel_annotations_keep_every_change_and_valid_json(self):
        m, _ = tk.make_recording(self.L.src, "20261015_100000")
        self.imp()
        jobs = [("--exp", "E7"), ("--scenario", "S7"), ("--game-speed", "77"), ("--troops", "7"), ("--note", "n7"), ("--variant", "v7")]
        env = dict(os.environ, SH2PERF_NO_HARDWARE="1")
        procs = [subprocess.Popen([sys.executable, "-I", str(TOOLS / "ingest.py"), "annotate", m["capture_id"], *j, "--src", str(self.L.src),
                                   "--captures", str(self.L.captures), "--index", str(self.L.index)],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", env=env) for j in jobs]
        for p in procs:
            out, err = p.communicate(timeout=120)
            self.assertEqual(p.returncode, 0, out + err)
        ann = json.loads((self.L.root / "data" / "annotations" / f"{m['capture_id']}.json").read_text())
        self.assertEqual(ann["labels"], {"exp": "E7", "scenario": "S7", "troops": 7, "note": "n7", "variant": "v7"})
        self.assertEqual(ann["game_speed"]["value"], 77)
        self.assertEqual(len(ann["history"]), 6, "no lost update")
        self.assertEqual(len(self.L.index.read_text().splitlines()), 1)


# --- 4. names and file roles ------------------------------------------------------------------------------

BAD_NAMES = ["manifest.json", "MANIFEST.JSON", "Import.Json", "import.json", "latest.json", "Stronghold2AnalyseHub.log",
             "C:evil.csv", "C:\\evil.csv", "\\\\server\\share\\x.csv", "/abs.csv", "a/b.csv", "..\\x.csv", "x.csv:stream",
             "x.csv::$DATA", "CON", "con.csv", "NUL.txt", "COM1.csv", "lpt9", "Aux.json", "COM\u00b9.csv", "bad.", "bad ",
             "a<b.csv", "a|b.csv", "q?.csv", "a*.csv", 'a"b.csv', "", ".hidden", "..", ".", "x" * 300 + ".csv", "a\x01b.csv", "tab\t.csv"]


def with_files(m, mutate):
    m = json.loads(json.dumps(m))
    mutate(m)
    return m


class NamesAndRoles(Base):
    def make(self):
        m, stem = tk.make_recording(self.L.src, "20261015_100000")
        self.mpath = self.L.src / f"{stem}_manifest.json"
        return m, stem

    def rewrite(self, m):
        self.mpath.write_text(json.dumps(m))

    def assert_rejected_without_writes(self, expect_text=None):
        before = tk.tree_hashes(self.L.src)
        r = self.L.run("import")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        if expect_text:
            self.assertIn(expect_text, r.stderr)
        self.assertEqual(tk.tree_hashes(self.L.src), before, "the source is unchanged")
        self.assertFalse(self.L.captures.exists(), "nothing was created before the manifest was rejected")
        self.assertFalse(self.L.index.exists())

    def test_invalid_or_reserved_file_names_are_rejected_before_any_write(self):
        m, stem = self.make()
        for bad in BAD_NAMES:
            with self.subTest(name=bad[:40]):
                self.rewrite(with_files(m, lambda x: x["files"].append({"role": "threads", "name": bad, "size": 1, "sha256": "0" * 64})))
                self.assert_rejected_without_writes("file name")

    def test_reserved_administration_names_cannot_replace_the_manifest_copy(self):
        m, stem = self.make()
        # the old rule accepted this and the staged copy would have overwritten the importer's own manifest.json
        self.rewrite(with_files(m, lambda x: x["files"][0].update(name="manifest.json")))
        self.assert_rejected_without_writes("reserved")

    def test_windows_equivalent_duplicates_are_rejected(self):
        m, stem = self.make()
        for a, b in [("A_x.csv", "a_x.csv"), ("caf\u00e9.csv", "cafe\u0301.csv"), ("same.csv", "same.csv")]:
            with self.subTest(pair=(a, b)):
                self.rewrite(with_files(m, lambda x: x["files"].extend([
                    {"role": "threads", "name": a, "size": 1, "sha256": "0" * 64},
                    {"role": "samples", "name": b, "size": 1, "sha256": "0" * 64}])))
                self.assert_rejected_without_writes("duplicate")

    def test_exactly_one_frames_file_and_known_unique_roles(self):
        m, stem = self.make()
        frames = next(f for f in m["files"] if f["role"] == "frames")
        cases = {
            "no frames": lambda x: x.update(files=[f for f in x["files"] if f["role"] != "frames"]),
            "two frames": lambda x: x["files"].append({**frames, "name": "second_frames.csv"}),
            "unknown role": lambda x: x["files"].append({"role": "evil", "name": "evil.bin", "size": 1, "sha256": "0" * 64}),
            "role missing": lambda x: x["files"][1].pop("role"),
            "duplicate threads": lambda x: x["files"].append({**next(f for f in x["files"] if f["role"] == "threads"), "name": "other_threads.csv"}),
        }
        for label, mutate in cases.items():
            with self.subTest(label):
                self.rewrite(with_files(m, mutate))
                self.assert_rejected_without_writes("role")

    def test_unsafe_capture_ids_are_rejected(self):
        m, stem = self.make()
        for bad in ("CON", "nul", "rec.", "rec ", "a:b", "x" * 200, "aux.v1", ".staging", "a\\b", "COM3"):
            with self.subTest(cid=bad):
                self.rewrite(with_files(m, lambda x: x.update(capture_id=bad)))
                self.assert_rejected_without_writes("capture_id")

    def test_existing_target_is_untouched_by_a_rejected_manifest(self):
        m, stem = self.make()
        self.imp()
        before = tk.tree_hashes(self.L.captures)
        index_before = self.L.index.read_text()
        self.rewrite(with_files(m, lambda x: x["files"][0].update(name="import.json")))
        r = self.L.run("import")
        self.assertEqual(r.returncode, 4)
        self.assertEqual(tk.tree_hashes(self.L.captures), before)
        self.assertEqual(self.L.index.read_text(), index_before)

    def test_cleanup_refuses_targets_outside_the_staging_area(self):
        root = self.L.root / "stage_root"
        root.mkdir()
        outside = self.L.root / "precious"
        outside.mkdir()
        (outside / "keep.txt").write_text("keep")
        inside = root / "id1"
        inside.mkdir()
        (inside / "f").write_text("x")
        for bad in (outside, root, root / ".." / "precious", self.L.root):
            with self.assertRaises(bronze.UnsafePath, msg=str(bad)):
                bronze.safe_rmtree(bad, root)
        self.assertTrue((outside / "keep.txt").exists())
        link = root / "link"
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True, text=True)
        if r.returncode == 0:
            with self.assertRaises(bronze.UnsafePath):
                bronze.safe_rmtree(link, root)
            self.assertTrue((outside / "keep.txt").exists(), "a junction is never followed")
            os.rmdir(link)
        bronze.safe_rmtree(inside, root)
        self.assertFalse(inside.exists())

    def imp(self, *a):
        r = self.L.run("import", *a)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
