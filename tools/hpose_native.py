"""Build/run the own Win32 range contract; no game or hub inputs.

Usage: python -I tools/hpose_native.py [--cmake PATH]
Outputs/logs only under ignored build/hpose-native.
"""
import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths


def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def parse_report(text):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate native report field: {key}")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError(f"Invalid JSON constant: {value}")

    def finite_float(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("Native report number exceeds finite floating-point range")
        return parsed

    report = json.loads(text, object_pairs_hook=unique_object, parse_constant=invalid_constant,
                        parse_float=finite_float)
    if not isinstance(report, dict):
        raise ValueError("Native report must be one JSON object")
    if report.get("schema") != "sh2perf.hpose-range-test":
        raise ValueError("Unknown native report schema")
    if type(report.get("version")) is not int or report["version"] != 1:
        raise ValueError("Unknown native report version")
    if report.get("completed") is not True:
        raise ValueError("Native run did not complete")
    for field, minimum in (("checks", 1), ("failures", 0)):
        if type(report.get(field)) is not int or report[field] < minimum:
            raise ValueError(f"Invalid native report counter: {field}")
    if report["failures"] > report["checks"]:
        raise ValueError("Native failures exceed checks")
    return report


def run_native(source, out, cmake=None, *, repo=paths.REPO, timeout=180, native_command=None):
    """Run the same gates with injectable own paths/commands for synthetic tests."""
    source, out, repo = Path(source).resolve(), Path(out).resolve(), Path(repo).resolve()
    report_path = out / "results.json"
    # Invalidate before tool discovery, configure, build, or process startup.
    report_path.unlink(missing_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    cmake = str(cmake) if cmake is not None else shutil.which("cmake")
    if not cmake:
        raise RuntimeError("CMake not found on PATH; pass --cmake PATH")
    build = out / "native"
    host = build / "Release" / "hpose_range_test.exe"
    commands = [
        [cmake, "-S", str(source), "-B", str(build), "-A", "Win32"],
        [cmake, "--build", str(build), "--config", "Release"],
        native_command if native_command is not None else [str(host)],
    ]
    for index, command in enumerate(commands):
        log = out / f"step-{index}.log"
        try:
            with log.open("w", encoding="utf-8") as output, (out / f"step-{index}-stderr.log").open(
                    "w", encoding="utf-8") as errors:
                process = subprocess.run(command, cwd=out, stdout=output, stderr=errors, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RuntimeError(f"Native step {index} could not complete; see {log.name}: {error}") from error
        if process.returncode:
            raise RuntimeError(f"Native step {index} exited {process.returncode}; see {log.name}")
    native_report = parse_report((out / "step-2.log").read_text(encoding="utf-8"))
    if native_report["failures"]:
        raise RuntimeError(f"Native contract reported {native_report['failures']} failures")
    result = {"scope": "own synthetic arithmetic model, not original execution", "result": native_report,
              "sources": {p.relative_to(repo).as_posix(): sha(p)
                          for p in [Path(__file__).resolve(), *sorted(source.iterdir())] if p.is_file()},
              "host_sha256": sha(host)}
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=out,
                                         prefix=".results-", suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            json.dump(result, output, indent=2, allow_nan=False)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, report_path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cmake", type=Path, help="CMake executable (default: PATH)")
    args = parser.parse_args()
    result = run_native(paths.REPO / "tools" / "hpose_contract", paths.REPO / "build" / "hpose-native", args.cmake)
    print(json.dumps(result["result"]))
    print("Report: build/hpose-native/results.json; original fallback, lifetimes and game performance untested.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        sys.exit(str(error))
