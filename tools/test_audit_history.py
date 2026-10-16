"""Regression tests: historical commit ids in the published audit copy (no game, no raw data, small temporary repos).

Usage: python -I tools/test_audit_history.py
audit_data.py records the diff since the audit assignment commits (02bce97 / 32ebc38). In the original history the
ids resolve directly; in a clean export they resolve only through docs/export/EXPORT_MAP.tsv; a missing or ambiguous
mapping is reported as such and never shown as an unchanged or passed historical comparison.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

SCRIPT = paths.REPO / "audits" / "2026-10-16-independent" / "audit_data.py"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
       "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.invalid", "GIT_CONFIG_NOSYSTEM": "1"}


def load_audit_data():
    sys.dont_write_bytecode = True        # no __pycache__ inside the audit reference folder
    spec = importlib.util.spec_from_file_location("audit_data_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True,
                          env=ENV).stdout.strip()


def make_repo(path, files, label=""):
    """files: list of (name, content) committed one per commit; returns the full commit ids."""
    path.mkdir(parents=True)
    git(path, "init", "-q")
    git(path, "config", "core.autocrlf", "false")
    ids = []
    for name, content in files:
        (path / name).parent.mkdir(parents=True, exist_ok=True)
        (path / name).write_text(content, encoding="utf-8")
        git(path, "add", name)
        git(path, "commit", "-q", "-m", f"add {name}{label}")
        ids.append(git(path, "rev-parse", "HEAD"))
    return ids


def add_map(repo, rows):
    text = "# test mapping\noriginal\texported\n" + "".join(f"{o}\t{e}\n" for o, e in rows)
    (repo / "docs" / "export").mkdir(parents=True, exist_ok=True)
    (repo / "docs" / "export" / "EXPORT_MAP.tsv").write_text(text, encoding="utf-8")
    git(repo, "add", "docs/export/EXPORT_MAP.tsv")
    git(repo, "commit", "-q", "-m", "add map")


class HistoricalIds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ad = load_audit_data()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="sh2_audithist_")
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_original_history_resolves_directly(self):
        a, _ = make_repo(self.tmp / "orig", [("a.txt", "1"), ("b.txt", "2")])
        r = self.ad.resolve_commit(self.tmp / "orig", a[:7])
        self.assertEqual((r["status"], r["commit"], r["via"]), ("original", a, None))

    def test_rewritten_history_resolves_through_the_map(self):
        orig, _ = make_repo(self.tmp / "orig", [("a.txt", "1"), ("b.txt", "2")])
        exported, _ = make_repo(self.tmp / "export", [("a.txt", "1"), ("b.txt", "2")], label=" (rewritten)")
        self.assertNotEqual(orig, exported)                      # different identity -> different ids
        add_map(self.tmp / "export", [(orig, exported)])
        r = self.ad.resolve_commit(self.tmp / "export", orig[:7])
        self.assertEqual((r["status"], r["commit"], r["original"]), ("mapped", exported, orig))
        self.assertEqual(r["via"], "docs/export/EXPORT_MAP.tsv")

    def test_missing_mapping_is_reported_not_passed(self):
        make_repo(self.tmp / "export", [("a.txt", "1")])
        add_map(self.tmp / "export", [("1" * 40, "2" * 40)])
        r = self.ad.resolve_commit(self.tmp / "export", "abcdef1")
        self.assertEqual((r["status"], r["commit"]), ("missing", None))
        text = self.ad.describe_history("X", {"assignment": r})
        self.assertIn("UNAVAILABLE", text)
        self.assertIn("not checked", text)

    def test_no_map_at_all_is_missing(self):
        make_repo(self.tmp / "plain", [("a.txt", "1")])
        r = self.ad.resolve_commit(self.tmp / "plain", "abcdef1")
        self.assertEqual(r["status"], "missing")
        self.assertIn("no docs/export/EXPORT_MAP.tsv", r["reason"])

    def test_mapped_commit_absent_from_the_export_is_missing(self):
        make_repo(self.tmp / "export", [("a.txt", "1")])
        add_map(self.tmp / "export", [("abcdef1" + "0" * 33, "f" * 40)])
        r = self.ad.resolve_commit(self.tmp / "export", "abcdef1")
        self.assertEqual(r["status"], "missing")
        self.assertIn("not in this history", r["reason"])

    def test_ambiguous_mapping_is_reported(self):
        head, = make_repo(self.tmp / "export", [("a.txt", "1")])
        add_map(self.tmp / "export", [("abcdef1" + "1" * 33, head), ("abcdef1" + "2" * 33, head)])
        r = self.ad.resolve_commit(self.tmp / "export", "abcdef1")
        self.assertEqual(r["status"], "ambiguous")
        self.assertEqual(len(r["candidates"]), 2)

    def test_snapshot_in_a_clean_export_layout(self):
        """Script level: mapped research id, missing hub id, absent raw recordings, then present (empty) ones."""
        root, work = self.tmp / "root", self.tmp / "work"
        old, _ = make_repo(self.tmp / "orig", [("a.txt", "1"), ("b.txt", "2")])
        new, _ = make_repo(root / "SH2-Perf", [("a.txt", "1"), ("b.txt", "2")], label=" (rewritten)")
        add_map(root / "SH2-Perf", [("02bce97" + old[7:], new)])
        make_repo(root / "Stronghold2AnalyseHub", [("hub.txt", "h")])
        cmd = [sys.executable, "-I", str(SCRIPT), "--root", str(root), "--work", str(work), "--snapshot", "before"]

        first = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotEqual(first.returncode, 0)
        self.assertIn("Missing local input (raw recording, not published)", first.stdout + first.stderr)
        self.assertNotIn("fatal:", first.stdout + first.stderr)          # the git stage itself works

        for cap in self.ad.IDS.values():
            (root / "SH2-Perf" / "captures" / cap).mkdir(parents=True)
        before = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(before.returncode, 0, before.stdout + before.stderr)
        self.assertIn("SH2-Perf: diff since 02bce97 recorded via docs/export/EXPORT_MAP.tsv", before.stdout)
        self.assertIn("Stronghold2AnalyseHub: historical diff since 32ebc38 UNAVAILABLE", before.stdout)
        snap = json.loads((work / "results" / "identity_before.json").read_text(encoding="utf-8"))
        self.assertEqual(snap["repos"]["SH2-Perf"]["assignment"]["commit"], new)
        self.assertIsNone(snap["repos"]["Stronghold2AnalyseHub"]["diff_from_assignment"])

        after = subprocess.run(cmd[:-1] + ["after"], capture_output=True, text=True)
        self.assertEqual(after.returncode, 0, after.stdout + after.stderr)
        self.assertIn("file identity unchanged", after.stdout)
        self.assertIn("UNAVAILABLE", after.stdout)
        self.assertIn("not checked", after.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
