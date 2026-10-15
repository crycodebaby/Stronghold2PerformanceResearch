"""Sampling-profiler output (SH2Perf_*_samples.csv): module shares per marker, top functions.

Usage:
  python -I tools/samples.py <..._samples.csv> [--marker N] [--top 12]   module groups (+ top functions in function mode)
  python -I tools/samples.py <..._samples.csv> --window <frames.csv> <t0> <t1>   not supported: samples are per marker

The hub samples the render thread's instruction pointer (docs/design/SAMPLING_PROFILER.md);
each sample is attributed to the module that contains it. A thread blocked in a system call is
reported in ntdll/win32u: group "system" means waiting or OS work, not game code.
Library use: groups(path) -> {marker: {group: samples}}, group_of(module_name).
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

EXE_BASE = 0x00400000          # Ghidra image base of Stronghold2.exe (no ASLR in Ghidra project)

# Order matters: first match wins. Names are compared lower case.
GROUP_RULES = [
    ("exe", re.compile(r"^stronghold2\.exe$")),
    ("dragonfly", re.compile(r"^dragonfly\.dll$")),
    ("dxrenderer", re.compile(r"^dxrenderer\.dll$")),
    ("granny2", re.compile(r"^granny2\.dll$")),
    ("d3d9", re.compile(r"^d3d9\.dll$")),
    ("d3dx9", re.compile(r"^d3dx9_\d+\.dll$")),
    ("driver", re.compile(r"^(nv|ati|amd|igd|ig9|igc|igxe|d3d9on12)")),
    ("overlay", re.compile(r"^(gameoverlayrenderer|overlay|rtss)")),
    ("hub", re.compile(r"^stronghold2analysehub\.dll$")),
    ("system", re.compile(r"^(ntdll|kernelbase|kernel32|win32u|user32|gdi32|gdi32full|ucrtbase|msvcr\w*|msvcp\w*|vcruntime\w*|"
                          r"dxgi|ole32|combase|rpcrt4|advapi32|sechost|shlwapi|ws2_32|winmm|wow64\w*|ntdll)\.dll$")),
]
GROUP_ORDER = ["exe", "dragonfly", "dxrenderer", "granny2", "d3d9", "d3dx9", "driver", "overlay", "hub", "system", "other"]


def group_of(module):
    m = module.lower()
    for name, rx in GROUP_RULES:
        if rx.match(m):
            return name
    return "unknown" if module == "?" else "other"


def read(path):
    with open(path, newline="") as f:
        return [(int(r["marker"]), r["module"], int(r["rva"], 16), int(r["count"])) for r in csv.DictReader(f)]


def groups(path):
    """{marker: {group: samples}} plus key -1 for all markers together."""
    out = defaultdict(lambda: defaultdict(int))
    for marker, module, _, count in read(path):
        g = group_of(module)
        out[marker][g] += count
        out[-1][g] += count
    return {m: dict(v) for m, v in out.items()}


def shares(counts):
    """Group -> percent of samples, ordered, zero entries dropped; plus the sample total."""
    total = sum(counts.values())
    if not total:
        return {}, 0
    ordered = [g for g in GROUP_ORDER + sorted(set(counts) - set(GROUP_ORDER)) if counts.get(g)]
    return {g: round(100.0 * counts[g] / total, 1) for g in ordered}, total


def top_functions(path, marker=None, top=12):
    """Top (module, rva) rows; with the exe, rva + image base = Ghidra address. Empty in module mode."""
    agg = defaultdict(int)
    for m, module, rva, count in read(path):
        if rva and (marker is None or m == marker):
            agg[(module, rva)] += count
    return sorted(agg.items(), key=lambda kv: -kv[1])[:top]


def resolve_exe(rva):
    """Name of the virtual function containing the exe address, or ''. Only vtable slots are known (F028)."""
    try:
        import sqlite3
        import paths
        if not paths.VTABLE_DB.exists():
            return ""
        a = EXE_BASE + rva
        hit = sqlite3.connect(paths.VTABLE_DB).execute(
            "SELECT addr, name FROM slots WHERE addr <= ? AND ? < addr + size ORDER BY addr DESC LIMIT 1", (a, a)).fetchone()
        return f"{hit[1]} (0x{hit[0]:08X})" if hit else ""
    except Exception:
        return ""


def format_shares(counts):
    sh, total = shares(counts)
    return f"{total} samples: " + ", ".join(f"{g} {p} %" for g, p in sh.items()) if total else "no samples"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    marker = int(sys.argv[sys.argv.index("--marker") + 1]) if "--marker" in sys.argv else None
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 12
    g = groups(path)
    print(f"all markers: {format_shares(g[-1])}" if g else "no samples")
    for m in sorted(k for k in g if k >= 0):
        if marker is None or m == marker:
            print(f"marker {m}: {format_shares(g[m])}")
    for (module, rva), count in top_functions(path, marker, top):
        name = resolve_exe(rva) if module.lower() == "stronghold2.exe" else ""
        print(f"  {count:>6}  {module} +0x{rva:08X}" + (f"  {name}" if name else ""))


if __name__ == "__main__":
    main()
