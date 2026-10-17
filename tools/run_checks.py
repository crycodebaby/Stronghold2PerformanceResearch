"""Run every check that needs neither the game nor local raw data (also used by CI).

Usage: python -I tools/run_checks.py [--audit] [--e2e] [--hub <hub repo>]

Default: the Python test suites (temp folders only) and lint_docs.py.
  --audit  also the independent audit's observer model (audits/2026-10-16-independent/observer_repro.py); needs the
           hub source equal to commit 32ebc38 (default hub: sibling Stronghold2AnalyseHub). Runs in a new temporary
           work dir and compares its results with the published reference repro_results.json (left unchanged).
  --e2e    also e2e_standin.py (real proxy + hub DLL + D3D9 stand-in); needs a Release build of the hub and an
           interactive Windows desktop.
Exit code 0 = all selected checks passed. Requires Python >= 3.12 (os.path.isjunction); verified with 3.14.
"""
import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

SUITES = ["test_variant", "test_ingest", "test_ab_compare", "test_import_safety", "test_hardening", "test_grannyobs",
          "test_audit_workdir", "test_audit_history", "test_hpose_creation", "test_hpose_native"]
AUDIT = paths.REPO / "audits" / "2026-10-16-independent"


def run(name, args, cwd):
    start = time.monotonic()
    proc = subprocess.run([sys.executable, "-I", *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-1:] or [""]
    print(f"{'ok  ' if proc.returncode == 0 else 'FAIL'}  {name:<22} {time.monotonic() - start:6.1f} s  {tail[0][:70]}")
    return proc.returncode == 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--e2e", action="store_true")
    ap.add_argument("--hub", type=Path, default=paths.HUB)
    a = ap.parse_args()
    if sys.version_info < (3, 12):
        print(f"Python {sys.version.split()[0]} is too old: the suites need 3.12 or newer.")
        return 2
    results = [run(s, [f"tools/{s}.py"], paths.REPO) for s in SUITES]
    results.append(run("lint_docs", ["tools/lint_docs.py"], paths.REPO))
    if a.audit:
        source = a.hub / "Stronghold2AnalyseHub" / "core" / "granny_observer.cpp"
        if source.is_file():
            with tempfile.TemporaryDirectory(prefix="sh2_audit_") as work:
                ok = run("audit observer_repro", ["observer_repro.py", "--hub-source", str(source), "--work", work], AUDIT)
                if ok:
                    new = json.loads((Path(work) / "results" / "repro_results.json").read_text(encoding="utf-8"))
                    ref = json.loads((AUDIT / "repro_results.json").read_text(encoding="utf-8"))
                    ok = new["results"] == ref["results"] and new["source_sha256"] == ref["source_sha256"]
                    print(f"{'ok  ' if ok else 'FAIL'}  audit vs reference          results {'equal' if ok else 'DIFFER'}")
            results.append(ok)
        else:
            print(f"FAIL  audit observer_repro   hub source not found: {source} (clone the hub next to this repo or pass --hub)")
            results.append(False)
    if a.e2e:
        build = a.hub / "build" / "Release"
        if (build / "Stronghold2AnalyseHub.dll").is_file():
            results.append(run("e2e_standin", ["tools/e2e_standin.py", "--hub-build", str(build)], paths.REPO))
        else:
            print(f"FAIL  e2e_standin            no hub build in {build} (build the hub first, see its README)")
            results.append(False)
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
