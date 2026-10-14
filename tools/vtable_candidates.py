"""Hotspot candidate list from ghidra_scripts/ExportVtables.java output.

Usage: python -I tools/vtable_candidates.py <vtables.csv> [--md]

Selects classes whose names suggest per-unit / per-tick work (pathing, layers,
simulation, formations, actors, AI chores) and lists their virtual functions,
largest first. Size and caller count are static hints only, not measured cost.
"""
import csv
import re
import sys
from collections import defaultdict

PATTERN = re.compile(
    r"(Path|Navigat|Cluster|QuadTree|Layer|Simulation|Sync|Formation|Actor|Unit|"
    r"Teleport|Governor|Clan|Animation|LevelOfDetail|Chore|Combat|Attack|Target)")
# Factory/trait templates only register classes; they do no per-tick work.
SKIP = re.compile(r"ClassTraitsT<|Factory")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    rows = list(csv.DictReader(open(sys.argv[1], newline="", encoding="utf-8")))
    by_class = defaultdict(list)
    for r in rows:
        if PATTERN.search(r["class"]) and not SKIP.search(r["class"]):
            by_class[r["class"]].append(r)

    print(f"# classes matched: {len(by_class)} of {len({r['class'] for r in rows})}")
    md = "--md" in sys.argv
    if md:
        print("| class | slot | address | size B | callers |\n|---|---|---|---|---|")
    for cls in sorted(by_class, key=lambda c: -max(int(r["size_bytes"]) for r in by_class[c])):
        fns = sorted(by_class[cls], key=lambda r: -int(r["size_bytes"]))
        for r in fns[:5]:
            if md:
                print(f"| {cls} | {r['slot']} | {r['function']} | {r['size_bytes']} | {r['callers']} |")
            else:
                print(f"{cls:50} slot {r['slot']:>3} {r['function']}  size {r['size_bytes']:>6}  callers {r['callers']}")


if __name__ == "__main__":
    main()
