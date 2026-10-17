"""Build/run the own H-record range contract; no game files or memory access.

Usage: python -I tools/hpose_native.py
Requires local MSVC/CMake. Outputs/logs only under ignored build/hpose-native.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths
from granny_pose import cmake_path, sha


def main():
    source = paths.REPO / "tools" / "hpose_contract"
    out = paths.REPO / "build" / "hpose-native"
    out.mkdir(parents=True, exist_ok=True)
    report = out / "results.json"
    report.unlink(missing_ok=True)
    cmake = cmake_path()
    build = out / "native"
    commands = [
        [cmake, "-S", str(source), "-B", str(build), "-A", "Win32"],
        [cmake, "--build", str(build), "--config", "Release"],
        [str(build / "Release" / "hpose_range_test.exe")],
    ]
    for index, command in enumerate(commands):
        log = out / f"step-{index}.log"
        with log.open("w", encoding="utf-8") as output:
            result = subprocess.run(command, cwd=out, stdout=output, stderr=subprocess.STDOUT, timeout=180)
        if result.returncode:
            raise RuntimeError(f"Native step {index} failed; see {log.relative_to(paths.REPO)}")
    summary = (out / "step-2.log").read_text(encoding="utf-8").strip()
    result = {"scope": "own synthetic arithmetic model, not original execution", "result": summary,
              "sources": {str(p.relative_to(paths.REPO)).replace("\\", "/"): sha(p)
                          for p in [Path(__file__).resolve(), *sorted(source.iterdir())] if p.is_file()},
              "host_sha256": sha(build / "Release" / "hpose_range_test.exe")}
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(summary)
    print("Report: build/hpose-native/results.json; original fallback, lifetimes and game performance untested.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        sys.exit(str(error))
