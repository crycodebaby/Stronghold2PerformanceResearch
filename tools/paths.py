"""Shared locations, derived from the repo position (no personal absolute paths).

Layout (siblings of the repo):
  <root>/Stronghold 2            original game, read-only
  <root>/Stronghold 2 - TEST     test copy, all experiments
  <root>/Stronghold2AnalyseHub   hub repo (build/Release/*)
  <root>/SH2-Perf                this repo
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROOT = REPO.parent
ORIGINAL = ROOT / "Stronghold 2"
TEST = ROOT / "Stronghold 2 - TEST"
HUB = ROOT / "Stronghold2AnalyseHub"
HUB_BUILD = HUB / "build" / "Release"
HUB_OUT = TEST / "SH2Perf_out"                 # SH2Launcher default --out
DXVK_D3D9 = Path.home() / "Tools" / "dxvk-3.1.1" / "x32" / "d3d9.dll"

CAPTURES = REPO / "captures"                   # bronze, gitignored
DATA = REPO / "data"                           # silver
DOCS = REPO / "docs"                           # gold
INDEX = DATA / "index.jsonl"
VTABLE_CSV = CAPTURES / "vtables_exe.csv"
VTABLE_DB = DATA / "vtables.db"


def is_inside(path, folder):
    """True if path is folder or below it (case-insensitive on Windows)."""
    p, f = Path(path).resolve(), Path(folder).resolve()
    return p == f or f in p.parents


def make_tools_importable():
    """`python -I` drops the script dir from sys.path; re-add tools/."""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
