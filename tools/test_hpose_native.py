"""Game/compiler-free native runner regression tests; own temporary processes only."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hpose_native as native

VALID = {"schema": "sh2perf.hpose-range-test", "version": 1, "completed": True, "checks": 7, "failures": 0}


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(prefix="hpose_test_")
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "own.txt").write_text("own synthetic fixture")
        self.runner_source = self.root / "hpose_native.py"
        self.runner_source.write_bytes(Path(native.__file__).read_bytes())
        self.out = self.root / "out"
        self.out.mkdir()
        self.report = self.out / "results.json"
        self.script = self.root / "fake.py"
        self.script.write_text("import sys\nprint('fake cmake')\n", encoding="utf-8")
        self.command = [sys.executable, "-I", str(self.script)]
        self.host = self.out / "native" / "Release" / "hpose_range_test.exe"
        self.host.parent.mkdir(parents=True)
        self.host.write_bytes(b"own fake host hash input")

    def run_case(self, report=None, *, exit_code=0, fail_step=None, start_error=False, timeout=False):
        self.report.write_text("stale success")
        runner = subprocess.run
        calls = []
        text = json.dumps(VALID) if report is None else report
        native_script = self.root / "native.py"
        native_script.write_text(f"import sys\nsys.stdout.write({text!r})\nsys.exit({exit_code})\n", encoding="utf-8")

        def execute(command, **kwargs):
            step = len(calls)
            calls.append(command)
            if start_error is not False and step == start_error:
                raise OSError("synthetic spawn failure")
            if timeout is not False and step == timeout:
                return runner([sys.executable, "-I", "-c", "import time; time.sleep(10)"],
                              **dict(kwargs, timeout=0.05))
            # Real isolated Python child processes, replacing only the CMake executable.
            actual = [sys.executable, "-I", str(native_script)] if step == 2 else self.command
            if step == fail_step:
                actual = [sys.executable, "-I", "-c", "raise SystemExit(9)"]
            return runner(actual, **kwargs)

        # All provenance files belong to this synthetic repo, even when the real
        # checkout and the OS temporary directory are on different drives.
        with patch.object(native, "__file__", str(self.runner_source)), \
                patch.object(native.subprocess, "run", side_effect=execute):
            return native.run_native(self.source, self.out, "synthetic-cmake", repo=self.root)

    def assert_failed(self, **kwargs):
        with self.assertRaises((RuntimeError, ValueError, OSError)):
            self.run_case(**kwargs)
        self.assertFalse(self.report.exists())
        self.assertEqual(list(self.out.glob(".results-*.tmp")), [])

    def test_success_real_process_and_hashes(self):
        result = self.run_case()
        self.assertEqual(result["result"], VALID)
        self.assertEqual(result["host_sha256"], native.sha(self.host))
        self.assertEqual(json.loads(self.report.read_text()), result)
        self.assertTrue(result["sources"])
        self.assertEqual(set(result["sources"]), {"hpose_native.py", "source/own.txt"})
        self.assertEqual(list(self.out.glob(".results-*.tmp")), [])

    def test_failed_process_steps(self):
        for step in range(3):
            with self.subTest(step=step):
                self.assert_failed(fail_step=step)
        self.assert_failed(report=json.dumps(dict(VALID, failures=2)), exit_code=1)
        self.assert_failed(report=json.dumps(VALID), exit_code=1)
        self.assert_failed(report=json.dumps(dict(VALID, failures=1)))

    def test_spawn_and_timeout(self):
        for step in range(3):
            with self.subTest(step=step):
                self.assert_failed(start_error=step)
                self.assert_failed(timeout=step)

    def test_invalid_json_process_output(self):
        for report in ("", "garbage", "{}", "[]", json.dumps(VALID) * 2,
                       json.dumps(VALID) + "\nextra",
                       json.dumps(VALID)[:-1] + ',"extra":NaN}',
                       json.dumps(VALID)[:-1] + ',"extra":Infinity}', '{"schema":"a","schema":"b"}'):
            with self.subTest(report=report):
                self.assert_failed(report=report)

    def test_strict_fields(self):
        for field, values in {"schema": [None, "unknown"], "version": [True, 1.0, -1, 2],
                              "completed": [False, 1, "true"], "checks": [True, 1.0, 0, -1],
                              "failures": [False, 0.0, -1, 8]}.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        native.parse_report(json.dumps(dict(VALID, **{field: value})))
            missing = dict(VALID)
            del missing[field]
            with self.assertRaises(ValueError):
                native.parse_report(json.dumps(missing))
        self.assertEqual(native.parse_report(json.dumps(dict(VALID, checks=9000)))["checks"], 9000)

    def test_exponent_overflow_cannot_be_persisted(self):
        for number in ("1e999", "-1e999"):
            with self.subTest(number=number):
                self.assert_failed(report=json.dumps(VALID)[:-1] + ',"extra":' + number + '}')

    def test_atomic_write_failure(self):
        for operation in ("replace", "fsync"):
            with self.subTest(operation=operation):
                with patch.object(native.os, operation, side_effect=OSError("synthetic write failure")) as fault:
                    self.assert_failed()
                fault.assert_called_once()

    def test_serialization_failure(self):
        with patch.object(native.json, "dump", side_effect=OSError("synthetic write failure")) as fault:
            self.assert_failed()
        fault.assert_called_once()

    def test_discovery_failure_invalidates_stale(self):
        self.report.write_text("stale success")
        with patch.object(native.shutil, "which", return_value=None):
            with self.assertRaises(RuntimeError):
                native.run_native(self.source, self.out)
        self.assertFalse(self.report.exists())

    def test_cli_and_optimized_gates(self):
        # CLI help must work isolated, even when no sibling hub/game exists.
        tool = str(Path(native.__file__).resolve())
        help_result = subprocess.run([sys.executable, "-I", tool, "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn("--cmake", help_result.stdout)
        code = ("import sys; sys.path.insert(0, " + repr(str(Path(tool).parent)) + "); "
                "import hpose_native; hpose_native.parse_report(" + repr(json.dumps(dict(VALID, checks=True))) + ")")
        result = subprocess.run([sys.executable, "-O", "-I", "-c", code], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid native report counter", result.stderr)


if __name__ == "__main__":
    unittest.main()
