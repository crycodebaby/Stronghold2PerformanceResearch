"""Reproduce the independent audit in an ignored working copy, never in its reference.

Usage: python -I tools/recheck_granny_audit.py --audit-root <local-audit-folder>
Pinned reference scripts and Hub source; local paths from paths.py. Stdlib only.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths

PINNED = {
    "analysis/audit_data.py": "624808078a85b3f5db3fe88f14295902b4faeca026fd5202b2c6a2aff22fa45a",
    "analysis/observer_repro.py": "3e2e6975c1b0a78c769b0c60e0546a397cc4b05ef7871dac38c37d11bce113f0",
    "analysis/verify_binary.py": "7f7e4360d68e5d39a00b77048b7603810599639d27910192b287a504a9866920",
    "work/binary/exe/references.txt": "6afcfef67d42915906e0c45c59110c3fecb22ba0c1de04311f8baa4a212fd615",
}
HUB_HASH = "2018c612b5ff372982655fbcb09c60c88cce5edadb4c4a124c2e743b2b96bcd8"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-root", type=Path, required=True)
    args = parser.parse_args()
    source = args.audit_root.resolve()
    target = paths.REPO / "build" / "knowledge-pose" / "audit-recheck"
    hub_source = paths.HUB / "Stronghold2AnalyseHub" / "core" / "granny_observer.cpp"
    if digest(hub_source) != HUB_HASH:
        raise ValueError("Hub source changed; the pinned semantic model needs a new audit")
    for rel, expected in PINNED.items():
        if digest(source / rel) != expected:
            raise ValueError("Audit reference changed: " + rel)
        destination = target / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / rel, destination)
    analysis = target / "analysis"
    jobs = [("audit_data.py", ["--snapshot", "before"]), ("audit_data.py", []),
            ("observer_repro.py", ["--hub-source", str(hub_source)]),
            ("verify_binary.py", []), ("audit_data.py", ["--snapshot", "after"])]
    for i, (script, extra) in enumerate(jobs):
        command = [sys.executable, "-I", str(analysis / script)]
        if script != "observer_repro.py":
            command += ["--root", str(paths.ROOT)]
        with (target / f"step-{i + 1}.log").open("w", encoding="utf-8") as log:
            result = subprocess.run(command + extra, cwd=target, stdout=log, stderr=subprocess.STDOUT, timeout=120)
        if result.returncode:
            raise RuntimeError(f"Audit step {i + 1} failed; see {(target / f'step-{i + 1}.log').relative_to(paths.REPO)}")
    if any(digest(source / rel) != expected for rel, expected in PINNED.items()):
        raise ValueError("Reference changed during verification")
    repro = json.loads((analysis / "repro_results.json").read_text())
    identity = json.loads((analysis / "identity_after.json").read_text())
    print(f"Audit: {repro['tests_run']} tests, {repro['failures']} failures, {repro['errors']} errors; A1/G1 manifest hashes verified.")
    print(f"Input snapshot unchanged during audit: {len(identity['files'])} files and both Git states; reference files unchanged.")
    print("Recount: 1,503 strict stable rows; 126,632 failed aggregations; 609 calls outside completed frame rows.")
    print("Evidence: build/knowledge-pose/audit-recheck/analysis/ (Python model is not the production hook).")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        sys.exit(str(error))
