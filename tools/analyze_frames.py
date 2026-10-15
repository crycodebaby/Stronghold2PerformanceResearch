"""Summarize AnalyseHub capture CSVs (SH2Perf_*_frames.csv / *_threads.csv).

Usage: python -I tools/analyze_frames.py <..._frames.csv> [--from-marker N] [--to-marker M]
       python -I tools/analyze_frames.py <..._frames.csv> --timeline [--window 5]

Frames are filtered by the `marker` column (F8 in game): --from-marker 1
keeps frames recorded after the first marker press. The matching
*_threads.csv (same prefix) is summarized if present.
Output is Markdown (<= 30 lines), ready to paste into docs/EXPERIMENTS.md.
--timeline: fixed time windows (default 5 s) with FPS, DIP, triangles, render-thread CPU and the
markers seen in the window; for hand-set markers whose phases blur.
Library use: summarize(path, lo, hi) -> dict, timeline(path, width) -> list (used by tools/ingest.py).
"""
import csv
import os
import statistics
import sys
from collections import defaultdict

COUNTERS = ("dip", "dp", "dpup", "dipup", "prims", "settex", "vsconst_calls", "psconst_calls")


def pct(values, p):
    s = sorted(values)
    return s[min(len(s) - 1, max(0, round(p / 100 * (len(s) - 1))))]


def summarize(path, lo=0, hi=1 << 30):
    """Metrics for frames with lo <= marker < hi; None if no frames."""
    with open(path, newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if lo <= int(r["marker"]) < hi]
    if len(rows) < 2:
        return None
    ft = [float(r["frame_ms"]) for r in rows]
    mean = lambda k: statistics.fmean(float(r[k]) for r in rows)
    duration = float(rows[-1]["t_s"]) - float(rows[0]["t_s"])
    worst1 = sorted(ft)[-max(1, len(ft) // 100):]
    m = {
        "frames": len(ft),
        "duration_s": round(duration, 2),
        "avg_fps": round(len(ft) / duration, 1) if duration > 0 else None,
        "p50_ms": round(pct(ft, 50), 2), "p95_ms": round(pct(ft, 95), 2),
        "p99_ms": round(pct(ft, 99), 2), "max_ms": round(max(ft), 2),
        "low1_fps": round(1000 / statistics.fmean(worst1), 1),
        "present_ms": round(mean("present_ms"), 2),
        "endscene_ms": round(mean("endscene_ms"), 2),
        "between_endscene_ms": round(mean("between_endscene_ms"), 2),
        "overlay_ms": round(mean("overlay_ms"), 2),
        "cpu_side_ms": round(mean("frame_ms") - mean("present_ms") - mean("endscene_ms"), 2),
        "va_max_mb": round(max(float(r["va_used_mb"]) for r in rows)),
    }
    for k in COUNTERS:
        m[k] = round(mean(k))
    m["threads"] = thread_summary(path, float(rows[0]["t_s"]), float(rows[-1]["t_s"]))
    return m


def thread_summary(frames_path, t0, t1, top=4):
    """Top threads by mean CPU% (of one core) within [t0, t1]."""
    threads = frames_path.replace("_frames.csv", "_threads.csv")
    if not os.path.exists(threads):
        return []
    per_tid, render = defaultdict(list), set()
    with open(threads, newline="") as fh:
        for r in csv.DictReader(fh):
            if t0 <= float(r["t_s"]) <= t1:
                per_tid[r["tid"]].append(float(r["cpu_pct"]))
                if r["is_render_thread"] == "1":
                    render.add(r["tid"])
    ranked = sorted(per_tid.items(), key=lambda kv: -statistics.fmean(kv[1]))[:top]
    return [{"tid": int(t), "cpu_mean": round(statistics.fmean(v)), "cpu_max": round(max(v)),
             "render": t in render} for t, v in ranked]


def timeline(path, width=5.0):
    """Per fixed window of `width` s: frames, FPS, mean DIP/prims per frame, render-thread CPU %, markers."""
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return []
    t0 = float(rows[0]["t_s"])
    win = defaultdict(list)
    for r in rows:
        win[int((float(r["t_s"]) - t0) // width)].append(r)
    cpu = defaultdict(list)
    threads = path.replace("_frames.csv", "_threads.csv")
    if os.path.exists(threads):
        with open(threads, newline="") as fh:
            for r in csv.DictReader(fh):
                if r["is_render_thread"] == "1":
                    cpu[int((float(r["t_s"]) - t0) // width)].append(float(r["cpu_pct"]))
    out = []
    for i in sorted(win):
        w = win[i]
        mean = lambda k: statistics.fmean(float(r[k]) for r in w)
        span = float(w[-1]["t_s"]) - float(w[0]["t_s"])
        out.append({
            "t_start": round(i * width), "frames": len(w),
            "fps": round((len(w) - 1) / span, 1) if span > 0 else None,
            "dip": round(mean("dip")), "prims": round(mean("prims")),
            "render_cpu": round(statistics.fmean(cpu[i])) if cpu[i] else None,
            "markers": sorted({int(r["marker"]) for r in w}),
        })
    return out


def format_timeline(tl, width):
    lines = [f"| t (s) | frames | FPS | DIP | triangles | render CPU % | marker |", "|---|---|---|---|---|---|---|"]
    for w in tl:
        lines.append(f"| {w['t_start']}-{w['t_start'] + width:g} | {w['frames']} | {w['fps']} | {w['dip']} | {w['prims']}"
                     f" | {w['render_cpu']} | {','.join(map(str, w['markers']))} |")
    return lines


def markers(path):
    with open(path, newline="") as fh:
        return sorted({int(r["marker"]) for r in csv.DictReader(fh)})


def arg(name, default):
    return int(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    if "--timeline" in sys.argv:
        width = float(sys.argv[sys.argv.index("--window") + 1]) if "--window" in sys.argv else 5.0
        print(chr(10).join(format_timeline(timeline(path, width), width)))
        return
    lo, hi = arg("--from-marker", 0), arg("--to-marker", 1 << 30)
    m = summarize(path, lo, hi)
    if not m:
        sys.exit("no frames in selected marker range")
    print(f"### {os.path.basename(path)}  markers [{lo},{hi})")
    print("| metric | value |\n|---|---|")
    print(f"| frames / duration | {m['frames']} / {m['duration_s']} s |")
    print(f"| avg FPS / 1% low | {m['avg_fps']} / {m['low1_fps']} |")
    print(f"| frame ms p50 / p95 / p99 / max | {m['p50_ms']} / {m['p95_ms']} / {m['p99_ms']} / {m['max_ms']} |")
    print(f"| ms present / endscene / cpu-side | {m['present_ms']} / {m['endscene_ms']} / {m['cpu_side_ms']} |")
    print(f"| draws/frame DIP / DP / DPUP / DIPUP | {m['dip']} / {m['dp']} / {m['dpup']} / {m['dipup']} |")
    print(f"| prims / settex / vsconst / psconst | {m['prims']} / {m['settex']} / {m['vsconst_calls']} / {m['psconst_calls']} |")
    print(f"| VA used MB max | {m['va_max_mb']} |")
    for t in m["threads"]:
        print(f"| thread {t['tid']}{' (render)' if t['render'] else ''} CPU% mean/max | {t['cpu_mean']} / {t['cpu_max']} |")


if __name__ == "__main__":
    main()
