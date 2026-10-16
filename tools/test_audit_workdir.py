"""Regression tests for the work-dir contract of the published audit copy (no game, no raw data, no Ghidra).

Usage: python -I tools/test_audit_workdir.py
A different --work / -Work must reach every audit script; new runs write only below <work>/results, read Ghidra
exports only from <work>/binary, never use the historical identity_before.json as their baseline, and leave the
reference files in audits/2026-10-16-independent/ byte-identical.
"""
import hashlib
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

AUDIT = paths.REPO / "audits" / "2026-10-16-independent"
HUB_SOURCE = paths.HUB / "Stronghold2AnalyseHub" / "core" / "granny_observer.cpp"


def snapshot():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(AUDIT.iterdir()) if p.is_file()}


def run(script, *args):
    proc = subprocess.run([sys.executable, "-I", str(AUDIT / script), *map(str, args)], cwd=paths.REPO,
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    return proc.returncode, proc.stdout + proc.stderr


class AuditWorkDir(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = snapshot()

    @classmethod
    def tearDownClass(cls):
        assert snapshot() == cls.before, "reference files in the audit folder changed"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="sh2_auditwork_")
        self.tmp = Path(self._tmp.name)
        self.work = self.tmp / "custom-work"
        self.root = self.tmp / "no-game-root"
        self.root.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def test_verify_binary_reads_exports_from_the_given_work_dir(self):
        code, out = run("verify_binary.py", "--root", self.root, "--work", self.work)
        self.assertNotEqual(code, 0)
        self.assertIn(str(self.work / "binary" / "exe" / "references.txt"), out)
        self.assertNotIn(str(AUDIT.parent / "work"), out)

    def test_verify_binary_passes_the_export_stage_with_exports_in_work(self):
        refs = self.work / "binary" / "exe" / "references.txt"
        refs.parent.mkdir(parents=True)
        refs.write_text("Program=placeholder\n", encoding="utf-8")
        code, out = run("verify_binary.py", "--root", self.root, "--work", self.work)
        self.assertNotEqual(code, 0)                        # no game files here
        self.assertNotIn("Missing Ghidra export", out)       # ... but the export was found in <work>
        self.assertIn("Stronghold2.exe", out)
        self.assertFalse((self.work / "results" / "binary_results.json").exists())

    def test_snapshot_after_requires_a_baseline_in_the_same_work_dir(self):
        code, out = run("audit_data.py", "--root", self.root, "--work", self.work, "--snapshot", "after")
        self.assertNotEqual(code, 0)
        self.assertIn("No baseline snapshot", out)
        self.assertIn(str(self.work / "results"), out)
        self.assertFalse((self.work / "results" / "identity_after.json").exists())

    @unittest.skipUnless(HUB_SOURCE.is_file(), "hub source not next to this repository")
    def test_observer_model_writes_only_into_work(self):
        code, out = run("observer_repro.py", "--hub-source", HUB_SOURCE, "--work", self.work)
        self.assertEqual(code, 0, out[-500:])
        self.assertTrue((self.work / "results" / "repro_results.json").is_file())

    def test_observer_model_rejects_a_changed_hub_source(self):
        changed = self.tmp / "granny_observer.cpp"
        changed.write_text("// not the audited source\n", encoding="utf-8")
        code, out = run("observer_repro.py", "--hub-source", changed, "--work", self.work)
        self.assertNotEqual(code, 0)
        self.assertIn("Source changed", out)
        self.assertFalse((self.work / "results" / "repro_results.json").exists())

    def test_run_audit_passes_the_same_work_dir_to_every_script(self):
        text = (AUDIT / "run_audit.ps1").read_text(encoding="utf-8")
        calls = re.findall(r"^\s*Invoke-PythonAudit '([^']+)' @\((.*)\)\s*$", text, re.M)
        self.assertEqual(len(calls), 6)
        for script, args in calls:
            self.assertIn("'--work',$Work", args, script)
        self.assertIn("$scratch = $Work", text)
        self.assertIn("Join-Path $scratch ('binary\\'+$job.Folder)", text)   # exports land where verify_binary reads
        self.assertIn("Join-Path $results 'identity_before.json'", text)    # own baseline per work dir
        self.assertNotIn("Join-Path $auditDir 'identity_before.json'", text)


if __name__ == "__main__":
    unittest.main(verbosity=1)
