"""Structural brief of one function from the saved Ghidra project (no decompiled code).

Usage: python -I tools/fbrief.py <address hex> [program]   (program default Stronghold2.exe)

Runs ghidra_scripts/FunctionBrief.java headless (read-only, no re-analysis, ~30 s),
writes captures/briefs/<program>_<addr>.txt and prints it (<= 30 lines).
Needs GHIDRA_INSTALL_DIR and JAVA_HOME (JDK 21); see docs/SETUP.md.
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

PROJECT_DIR = paths.ROOT / "ghidra-projects"
PROJECT = "SH2"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    addr = sys.argv[1].lower().removeprefix("0x")
    program = sys.argv[2] if len(sys.argv) > 2 else "Stronghold2.exe"
    ghidra = os.environ.get("GHIDRA_INSTALL_DIR")
    if not ghidra:
        sys.exit("GHIDRA_INSTALL_DIR not set (docs/SETUP.md)")
    out = paths.CAPTURES / "briefs" / f"{program}_{addr}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists():
        cmd = [str(Path(ghidra) / "support" / "analyzeHeadless.bat"), str(PROJECT_DIR), PROJECT,
               "-process", program, "-noanalysis", "-readOnly",
               "-scriptPath", str(paths.REPO / "ghidra_scripts"),
               "-postScript", "FunctionBrief.java", addr, str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if not out.exists():
            tail = "\n".join((r.stdout + r.stderr).splitlines()[-10:])
            sys.exit(f"FunctionBrief failed (exit {r.returncode}):\n{tail}")
    lines = out.read_text(encoding="utf-8").splitlines()
    print("\n".join(lines[:30]))
    if len(lines) > 30:
        print(f"... {len(lines) - 30} more lines in {out.relative_to(paths.REPO)}")


if __name__ == "__main__":
    main()
