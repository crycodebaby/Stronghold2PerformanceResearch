"""Compare frame-time distributions of several captures side by side (A/B runs, D011).

Usage: python -I tools/ab_compare.py <label>=<capture id | frames csv> [<label>=...] [--marker N] [--period 1.0]

Only columns that exist in every hub mode are used: frame_ms and t_s (present_ms is shown too).
Columns that a switched-off hub part leaves at 0 (counters, EndScene timing) are never compared.
The first capture is the reference; deltas are relative to it. Always include a REPEAT of one
mode (A1, A2): the difference between A1 and A2 is the run-to-run noise that any A-vs-B difference
must clearly exceed before it is called an effect.

Rows:
  frames / FPS / p50 / p95 / p99 / max  frame_ms statistics (--marker N: only frames with that marker)
  long frames       frames above 1.5 x the median of the same capture, per minute
  long ~period      share of intervals between consecutive long frames within +-10 % of --period
                    seconds (default 1.0). Near 100 % = long frames come on a clock (hypothesis H1: the
                    hub's old 1 s thread poll / file flush; or the game's own 1 s tick - compare modes).
  long at period*k  share of ALL long-frame intervals that are a multiple k*period (+-10 %)
  random control    expected "~period" share if the same number of long frames were placed at random in
                    the same duration (500 trials, fixed seed). A real clock is far above this value.
Output is Markdown, <= 30 lines. Library use: stats(rows, period) -> dict.
"""
import argparse
import csv
import json
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402


def load(spec, marker=None):
    """Rows (t_s, frame_ms, present_ms) of one capture given by id or csv path."""
    p = Path(spec)
    if not p.suffix:
        found = sorted((paths.CAPTURES / spec).glob("SH2Perf_*_frames.csv"))
        if len(found) != 1:
            sys.exit(f"{spec}: expected exactly one frames CSV in captures/{spec}, found {len(found)}")
        p = found[0]
    rows = []
    with open(p, newline="") as f:
        for r in csv.DictReader(f):
            if marker is None or int(r["marker"]) == marker:
                rows.append((float(r["t_s"]), float(r["frame_ms"]), float(r["present_ms"])))
    return rows


def speed_of(spec):
    """(value, origin) of the game speed of a capture id from data/index.jsonl; (None, 'unknown') if unknown or not an id."""
    if Path(spec).suffix or not paths.INDEX.exists():
        return None, "unknown"
    for raw in paths.INDEX.read_text(encoding="utf-8").splitlines():
        try:
            line = json.loads(raw)
        except ValueError:
            continue
        if line.get("capture_id") == spec:
            gs = line.get("game_speed") or {}
            return gs.get("value"), gs.get("origin", "unknown")
    return None, "unknown"


def speed_notes(labels, speeds):
    """Table cells and warnings: runs at different or unknown game speeds are not comparable by their frame times."""
    cells = ["unknown" if v is None else f"{v:g} ({o})" for v, o in speeds]
    notes = []
    known = {v for v, _ in speeds if v is not None}
    unknown = [lab for lab, (v, _) in zip(labels, speeds) if v is None]
    if len(known) > 1:
        notes.append(f"WARNING game speeds differ ({', '.join(f'{v:g}' for v in sorted(known))}): frame times of these runs are not comparable")
    if unknown:
        notes.append(f"NOTE game speed unknown for {', '.join(unknown)}: sameness of the runs is not verified")
    return cells, notes


def pct(values, q):
    s = sorted(values)
    return s[min(len(s) - 1, max(0, round(q / 100 * (len(s) - 1))))]


def stats(rows, period=1.0, factor=1.5):
    """Metrics of one capture; None if fewer than 10 frames."""
    if len(rows) < 10:
        return None
    ft = [r[1] for r in rows]
    med = statistics.median(ft)
    dur = rows[-1][0] - rows[0][0]
    long_t = [r[0] for r in rows if r[1] > factor * med]
    gaps = [b - a for a, b in zip(long_t, long_t[1:])]
    near = sum(1 for g in gaps if abs(g - period) <= 0.1 * period)
    mult = sum(1 for g in gaps if any(abs(g - k * period) <= 0.1 * period for k in range(1, 6)))
    control = None
    if len(long_t) >= 3 and dur > 0:
        rnd, shares = random.Random(1), []
        for _ in range(500):
            t = sorted(rnd.uniform(0, dur) for _ in long_t)
            g = [b - a for a, b in zip(t, t[1:])]
            shares.append(100 * sum(1 for x in g if abs(x - period) <= 0.1 * period) / len(g))
        control = statistics.fmean(shares)
    return {
        "frames": len(rows), "fps": len(rows) / dur if dur > 0 else float("nan"),
        "p50": pct(ft, 50), "p95": pct(ft, 95), "p99": pct(ft, 99), "max": max(ft),
        "present": statistics.fmean(r[2] for r in rows),
        "long_per_min": 60 * len(long_t) / dur if dur > 0 else float("nan"),
        "long_n": len(long_t),
        "period_share": 100 * near / len(gaps) if gaps else None,
        "multiple_share": 100 * mult / len(gaps) if gaps else None,
        "control_share": control,
    }


def fmt(v, digits=1):
    return "n/a" if v is None else f"{v:.{digits}f}"


def render(labels, results, speeds=None):
    ref = results[0]
    lines = ["| metric | " + " | ".join(labels) + " |", "|---|" + "---|" * len(labels)]
    notes = []
    if speeds:
        cells, notes = speed_notes(labels, speeds)
        lines.append("| game speed (origin) | " + " | ".join(cells) + " |")

    def row(name, key, digits=1, delta=False):
        cells = []
        for i, r in enumerate(results):
            if r is None or r[key] is None:
                cells.append("n/a")
                continue
            cell = fmt(r[key], digits)
            if delta and i > 0 and ref and ref[key]:
                cell += f" ({100 * (r[key] / ref[key] - 1):+.1f} %)"
            cells.append(cell)
        lines.append(f"| {name} | " + " | ".join(cells) + " |")

    row("frames", "frames", 0)
    row("avg FPS", "fps", 1, True)
    row("p50 ms", "p50", 2, True)
    row("p95 ms", "p95", 2, True)
    row("p99 ms", "p99", 2, True)
    row("max ms", "max", 1)
    row("present ms (mean)", "present", 2)
    row("long frames /min (>1.5x median)", "long_per_min", 1, True)
    row("long frames n", "long_n", 0)
    row("long-frame gaps ~period %", "period_share", 0)
    row("long-frame gaps k*period %", "multiple_share", 0)
    row("random control ~period %", "control_share", 0)
    return lines + notes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("captures", nargs="+", help="label=<capture id or frames csv>, first = reference")
    ap.add_argument("--marker", type=int, default=None, help="only frames with this marker")
    ap.add_argument("--period", type=float, default=1.0, help="clock period to test, seconds")
    a = ap.parse_args()
    labels, results, speeds = [], [], []
    for spec in a.captures:
        if "=" not in spec:
            sys.exit(f"{spec!r}: use label=<capture id or csv>")
        label, target = spec.split("=", 1)
        labels.append(label)
        results.append(stats(load(target, a.marker), a.period))
        speeds.append(speed_of(target))
    if results[0] is None:
        sys.exit("reference capture has fewer than 10 frames in the chosen range")
    print("\n".join(render(labels, results, speeds)))


if __name__ == "__main__":
    main()
