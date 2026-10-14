"""Summarize AnalyseHub capture CSVs (SH2Perf_*_frames.csv / *_threads.csv).

Usage: python -I tools/analyze_frames.py <..._frames.csv> [--from-marker N] [--to-marker M]

Frames are filtered by the `marker` column (F8 in game): --from-marker 1
keeps frames recorded after the first marker press. The matching
*_threads.csv (same prefix) is summarized if present.
Output is Markdown, ready to paste into docs/EXPERIMENTS.md.
"""
import csv
import os
import statistics
import sys
from collections import defaultdict


def pct(values, p):
    if not values:
        return float("nan")
    s = sorted(values)
    k = min(len(s) - 1, max(0, round(p / 100 * (len(s) - 1))))
    return s[k]


def arg(name, default):
    if name in sys.argv:
        return int(sys.argv[sys.argv.index(name) + 1])
    return default


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    lo, hi = arg("--from-marker", 0), arg("--to-marker", 1 << 30)
    rows = [r for r in csv.DictReader(open(path, newline="")) if lo <= int(r["marker"]) < hi]
    if not rows:
        sys.exit("no frames in selected marker range")

    ft = [float(r["frame_ms"]) for r in rows]
    duration = float(rows[-1]["t_s"]) - float(rows[0]["t_s"])
    mean = lambda k: statistics.fmean(float(r[k]) for r in rows)
    worst1 = sorted(ft)[-max(1, len(ft) // 100):]

    print(f"### {os.path.basename(path)}  markers [{lo},{hi})")
    print(f"| metric | value |\n|---|---|")
    print(f"| frames / duration | {len(ft)} / {duration:.1f} s |")
    print(f"| avg FPS (frames/time) | {len(ft) / duration:.1f} |" if duration > 0 else "| avg FPS | n/a |")
    print(f"| frame ms p50 / p95 / p99 / max | {pct(ft, 50):.1f} / {pct(ft, 95):.1f} / {pct(ft, 99):.1f} / {max(ft):.1f} |")
    print(f"| 1% low FPS | {1000 / statistics.fmean(worst1):.1f} |")
    for k in ("present_ms", "endscene_ms", "between_endscene_ms", "overlay_ms"):
        print(f"| mean {k} | {mean(k):.2f} |")
    print(f"| mean cpu-side ms (frame - present - endscene) | "
          f"{mean('frame_ms') - mean('present_ms') - mean('endscene_ms'):.2f} |")
    for k in ("dip", "dp", "dpup", "dipup", "prims", "settex", "vsconst_calls", "psconst_calls"):
        print(f"| mean {k}/frame | {mean(k):.0f} |")
    print(f"| VA used MB max | {max(float(r['va_used_mb']) for r in rows):.0f} |")

    threads = path.replace("_frames.csv", "_threads.csv")
    if os.path.exists(threads):
        t0, t1 = float(rows[0]["t_s"]), float(rows[-1]["t_s"])
        per_tid = defaultdict(list)
        render = set()
        for r in csv.DictReader(open(threads, newline="")):
            if t0 <= float(r["t_s"]) <= t1:
                per_tid[r["tid"]].append(float(r["cpu_pct"]))
                if r["is_render_thread"] == "1":
                    render.add(r["tid"])
        top = sorted(per_tid.items(), key=lambda kv: -statistics.fmean(kv[1]))[:6]
        print("\n| thread | mean CPU % of one core | max | render thread |\n|---|---|---|---|")
        for tid, v in top:
            print(f"| {tid} | {statistics.fmean(v):.0f} | {max(v):.0f} | {'yes' if tid in render else ''} |")


if __name__ == "__main__":
    main()
