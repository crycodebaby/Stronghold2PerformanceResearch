"""Function-mode samples -> Ghidra functions (EXP-007).

Usage:
  python -I tools/funcsamples.py <..._samples.csv> <..._frames.csv> [--markers 1,3] [--top 15] [--module exe|granny2]
  python -I tools/funcsamples.py --check <hex rva> --module exe|granny2      which function body contains rva
  python -I tools/funcsamples.py <samples.csv> <frames.csv> --delta-counts --module exe [--markers 1,3]
      counts for "first marker vs second marker" (running vs paused): known functions with samples only in the
      first marker, the same incl. unresolved 4 KiB pages, keys with est. ms delta > 0, delta total, top 10, max

Each sample address (module, rva) is counted for the Ghidra function whose body (all address ranges,
from ghidra_scripts/ExportFunctions.java -> captures/functions/<module>_functions.csv) contains
image base + rva. Addresses outside every body stay "unresolved", grouped per 4 KiB page only for display.
Quantities per marker: samples, share of all samples of that marker, estimated ms per frame =
share x mean frame ms of the same marker (estimate under sampling). Flat samples: where the thread
executed, not call paths or inclusive time.
Library: load_functions(module), resolve(funcs, addr), per_function(samples_csv, frames_csv).
"""
import bisect
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402
import samples  # noqa: E402

FUNC_DIR = paths.REPO / "captures" / "functions"
MODULES = {  # sampler module name (lower) -> (short name, Ghidra image base)
    "stronghold2.exe": ("exe", 0x00400000),
    "granny2.dll": ("granny2", 0x50000000),
}
_cache = {}


def load_functions(short):
    """Sorted list of (start, end_inclusive, entry, name, source) over all body ranges."""
    if short in _cache:
        return _cache[short]
    rows = []
    with open(FUNC_DIR / f"{short}_functions.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            entry = int(r["entry"], 16)
            for rg in r["ranges"].split(";"):
                a, b = rg.split("-")
                rows.append((int(a, 16), int(b, 16), entry, r["name"], r["source"]))
    rows.sort()
    _cache[short] = (rows, [r[0] for r in rows])
    return _cache[short]


def resolve(funcs, addr):
    rows, starts = funcs
    i = bisect.bisect_right(starts, addr) - 1
    if i >= 0 and rows[i][0] <= addr <= rows[i][1]:
        return rows[i][2], rows[i][3], rows[i][4]
    return None


def mean_frame_ms(frames_csv):
    acc = defaultdict(list)
    with open(frames_csv, newline="") as f:
        for r in csv.DictReader(f):
            acc[int(r["marker"])].append(float(r["frame_ms"]))
    return {m: sum(v) / len(v) for m, v in acc.items()}


def per_function(samples_csv, frames_csv):
    """{marker: {"n": total, "unknown": n_?, "funcs": {key: count}}}; key = (short, entry, name, source) or
    (short|module, 'unresolved', page) for addresses outside every known body / unmapped modules (module level)."""
    out = defaultdict(lambda: {"n": 0, "unknown": 0, "funcs": defaultdict(int)})
    for marker, module, rva, count in samples.read(samples_csv):
        o = out[marker]
        o["n"] += count
        if module == "?":
            o["unknown"] += count
            o["funcs"][("?", "unresolved", 0)] += count
            continue
        m = MODULES.get(module.lower())
        if not m:
            o["funcs"][(module, "module", 0)] += count
            continue
        short, base = m
        hit = resolve(load_functions(short), base + rva)
        key = (short,) + hit if hit else (short, "unresolved", (base + rva) & ~0xFFF)
        o["funcs"][key] += count
    return out, mean_frame_ms(frames_csv)


def label(key):
    if key[1] == "unresolved":
        return f"{key[0]} unresolved page 0x{key[2]:08X}" if key[2] else f"{key[0]} unresolved"
    if key[1] == "module":
        return f"{key[0]} (module, no function map)"
    return f"{key[0]} 0x{key[1]:08X} {key[2]} [{key[3]}]"


def delta_counts(data, fms, m_run, m_pause, short):
    """Counts behind 'running-only' statements (EXP-007 F135). Zero samples in a marker is no proof of zero calls."""
    run, pause = data[m_run], data[m_pause]

    def ms(d, m, k):
        return d["funcs"].get(k, 0) / d["n"] * fms[m]

    keys = [k for k in set(run["funcs"]) | set(pause["funcs"]) if k[0] == short]
    known = [k for k in keys if k[1] not in ("unresolved", "module")]
    only_run = lambda ks: [k for k in ks if run["funcs"].get(k, 0) > 0 and pause["funcs"].get(k, 0) == 0]  # noqa: E731
    delta = {k: ms(run, m_run, k) - ms(pause, m_pause, k) for k in keys}
    pos = sorted((v for v in delta.values() if v > 0), reverse=True)
    print(f"{short}: m{m_run} vs m{m_pause}, est. ms per frame under sampling")
    print(f"known functions with samples in m{m_run} only:            {len(only_run(known))}")
    print(f"  incl. unresolved 4 KiB pages:                       {len(only_run(keys))}")
    print(f"known functions with delta > 0:                      {sum(1 for k in known if delta[k] > 0)}")
    print(f"  incl. unresolved 4 KiB pages:                       {len(pos)}")
    print(f"delta total {sum(delta.values()):.2f} ms; top 10 positive {sum(pos[:10]):.2f} ms; max {pos[0] if pos else 0:.2f} ms")


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "--check":
        short = a[a.index("--module") + 1]
        base = {v[0]: v[1] for v in MODULES.values()}[short]
        hit = resolve(load_functions(short), base + int(a[1], 16))
        print(label((short,) + hit) if hit else f"{short} 0x{base + int(a[1], 16):08X}: outside every function body")
        return
    markers = [int(x) for x in a[a.index("--markers") + 1].split(",")] if "--markers" in a else [1, 3]
    top = int(a[a.index("--top") + 1]) if "--top" in a else 15
    only = a[a.index("--module") + 1] if "--module" in a else None
    data, fms = per_function(a[0], a[1])
    if "--delta-counts" in a:
        delta_counts(data, fms, markers[0], markers[1], only or "exe")
        return
    keys = defaultdict(float)
    for m in markers:
        d = data.get(m)
        if not d:
            continue
        print(f"marker {m}: n={d['n']} unknown(?)={d['unknown']} mean frame {fms[m]:.2f} ms")
        for k, c in d["funcs"].items():
            keys[k] += c / d["n"] * fms[m]
    ranked = [k for k in sorted(keys, key=lambda k: -keys[k]) if not only or k[0] == only][:top]
    print("est ms/frame per marker (samples) | function")
    for k in ranked:
        cells = []
        for m in markers:
            d = data.get(m)
            c = d["funcs"].get(k, 0) if d else 0
            cells.append(f"m{m} {c / d['n'] * fms[m]:5.2f} ({c})" if d else f"m{m} -")
        print(" | ".join(cells) + " | " + label(k))


if __name__ == "__main__":
    main()
