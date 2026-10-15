"""Symbol lookup over the Ghidra vtable export (SQLite, silver layer).

Usage:
  python -I tools/sym.py build [vtables.csv]   CSV -> data/vtables.db (default captures/vtables_exe.csv)
  python -I tools/sym.py addr 0x004E92C0       function at/containing address + classes using it
  python -I tools/sym.py class S2Actor [N]     largest virtual functions of matching classes (default 20)

Output is capped at 30 lines. Addresses are Ghidra image-base addresses (0x00400000).
Containment uses start + size of the function body, which is approximate for
non-contiguous functions. Only virtual functions are known (FINDINGS F028).
"""
import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

MAX_LINES = 30


def build(csv_path):
    paths.DATA.mkdir(exist_ok=True)
    if paths.VTABLE_DB.exists():
        paths.VTABLE_DB.unlink()
    db = sqlite3.connect(paths.VTABLE_DB)
    db.execute("CREATE TABLE slots (class TEXT, vtable INTEGER, slot INTEGER, addr INTEGER,"
               " name TEXT, size INTEGER, callers INTEGER)")
    rows = [(r["class"], int(r["vtable"], 16), int(r["slot"]), int(r["function"], 16),
             r["function_name"], int(r["size_bytes"]), int(r["callers"]))
            for r in csv.DictReader(open(csv_path, newline="", encoding="utf-8"))]
    db.executemany("INSERT INTO slots VALUES (?,?,?,?,?,?,?)", rows)
    db.execute("CREATE INDEX i_addr ON slots(addr)")
    db.execute("CREATE INDEX i_class ON slots(class)")
    db.commit()
    n_fn = db.execute("SELECT COUNT(DISTINCT addr) FROM slots").fetchone()[0]
    print(f"{len(rows)} slots, {n_fn} distinct functions -> {paths.VTABLE_DB.relative_to(paths.REPO)}")


def connect():
    if not paths.VTABLE_DB.exists():
        sys.exit("data/vtables.db missing - run: python -I tools/sym.py build")
    return sqlite3.connect(paths.VTABLE_DB)


def addr(text):
    a = int(text, 16)
    db = connect()
    hit = db.execute("SELECT addr, size, name, callers FROM slots WHERE addr <= ? AND ? < addr + size"
                     " ORDER BY addr DESC LIMIT 1", (a, a)).fetchone()
    if not hit:
        print(f"0x{a:08X}: no known virtual function (only vtable slots are indexed)")
        return
    start, size, name, callers = hit
    uses = db.execute("SELECT class, slot FROM slots WHERE addr = ? ORDER BY class", (start,)).fetchall()
    print(f"0x{a:08X} -> 0x{start:08X} +0x{a - start:X}  size {size} B  refs {callers}  ghidra name {name}")
    print(f"used in {len(uses)} vtable slot(s):")
    for cls, slot in uses[:MAX_LINES - 3]:
        print(f"  {cls}::vf{slot:02d}")
    if len(uses) > MAX_LINES - 3:
        print(f"  ... {len(uses) - (MAX_LINES - 3)} more")


def klass(pattern, limit):
    db = connect()
    rows = db.execute("SELECT class, slot, addr, size, callers FROM slots WHERE class LIKE ?"
                      " ORDER BY size DESC", (f"%{pattern}%",)).fetchall()
    classes = sorted({r[0] for r in rows})
    print(f"{len(classes)} class(es) match '{pattern}': {', '.join(classes[:6])}{' ...' if len(classes) > 6 else ''}")
    for cls, slot, a, size, callers in rows[:min(limit, MAX_LINES - 2)]:
        print(f"  0x{a:08X}  {cls}::vf{slot:02d}  size {size} B  refs {callers}")
    if len(rows) > limit:
        print(f"  ... {len(rows) - limit} more slots")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "build":
        build(sys.argv[2] if len(sys.argv) > 2 else paths.VTABLE_CSV)
    elif cmd == "addr" and len(sys.argv) == 3:
        addr(sys.argv[2])
    elif cmd == "class" and len(sys.argv) >= 3:
        klass(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 20)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
