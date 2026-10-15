"""Ingest one hub recording: bronze capture folder + silver index line.

Usage:
  python -I tools/ingest.py --exp EXP-001 --scenario KNIGHTS --troops 100 [--note "..."]
         [--variant auto] [--src <hub out dir>] [--recording <timestamp, e.g. 20261015_034411>]

Steps:
  1. Find the recordings in <src> (default TEST/SH2Perf_out) by their *_frames.csv files. Exactly one
     recording -> take it. Several -> NOTHING is touched: the tool lists them (start, frames, size)
     and exits; rerun with --recording <timestamp>. latest.json is only used when it names the chosen
     recording (otherwise it is left alone and a replacement is written from the CSV name).
  2. Copy the recording's CSVs, the log and latest.json to
     captures/<YYYYMMDD>_<EXP>_<variant>_<scenario>/ (bronze, gitignored); the sources are deleted only
     after meta.json and the index line are written. Other recordings are never moved.
  3. Write meta.json there (hashes of exe/DLLs, variant, scenario, troops, CPU/GPU, hub commit).
  4. Append one metrics line to data/index.jsonl (silver; no absolute paths), write timeline.md
     (5 s windows) into the capture folder.
  5. Print a summary of at most 30 lines.
  Sampler output (*_samples.csv, listed as samples_csv in latest.json) is copied too and summarized
  per module group into the index line (render_modules).
Run after the game has exited (the hub keeps its log open while running).
"""
import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_frames  # noqa: E402
import paths  # noqa: E402
import samples  # noqa: E402
import variant as variant_tool  # noqa: E402


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hardware():
    """CPU and GPU names via CIM; empty strings if unavailable."""
    def cim(cls):
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"(Get-CimInstance {cls} | Select-Object -First 1 -ExpandProperty Name)"],
                capture_output=True, text=True, timeout=30)
            return out.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            return ""
    return {"cpu": cim("Win32_Processor"), "gpu": cim("Win32_VideoController")}


def binaries_meta():
    """Hashes identify the exact build measured (exe, d3d9 proxy, optional DXVK, hub).

    The proxy loads the hub copy in the TEST folder (D009), so that one is hashed.
    """
    files = {
        "Stronghold2.exe": paths.TEST / "Stronghold2.exe",
        "d3d9.dll (TEST folder)": paths.TEST / "d3d9.dll",
        "d3d9_dxvk.dll (TEST folder)": paths.TEST / "d3d9_dxvk.dll",
        "Stronghold2AnalyseHub.dll (TEST folder)": paths.TEST / "Stronghold2AnalyseHub.dll",
    }
    return {name: sha256(p)[:16] for name, p in files.items() if p.exists()}


def recording_info(frames_csv):
    """Start timestamp (from the file name), frame count and size of one recording."""
    stamp = frames_csv.name[len("SH2Perf_"):-len("_frames.csv")]
    with open(frames_csv, "rb") as f:
        n = max(0, sum(1 for _ in f) - 1)
    return stamp, n, frames_csv.stat().st_size


def choose_recording(src, wanted):
    """Return the latest.json-like dict of exactly one unambiguous recording, or exit without touching anything."""
    csvs = sorted(src.glob("SH2Perf_*_frames.csv"))
    if not csvs:
        sys.exit(f"no *_frames.csv in {src} - record with F9 (start) and F9 (stop) first")
    stamps = {recording_info(c)[0]: c for c in csvs}
    if wanted:
        if wanted not in stamps:
            sys.exit(f"recording {wanted} not in {src}; found: {', '.join(stamps)}")
        stamp = wanted
    elif len(stamps) == 1:
        stamp = next(iter(stamps))
    else:
        print(f"{len(stamps)} recordings in {src}; nothing was touched. Rerun with --recording <timestamp>:")
        for s, c in stamps.items():
            _, n, size = recording_info(c)
            print(f"  {s}  {n} frames  {size // 1024} KiB")
        sys.exit(2)
    frames = stamps[stamp]
    latest = {}
    lp = src / "latest.json"
    if lp.exists():
        try:
            latest = json.loads(lp.read_text())
        except ValueError:
            latest = {}
    if latest.get("frames_csv") == frames.name:
        latest["_from_latest_json"] = True
        return latest
    d, tm = stamp.split("_")
    start = f"{d[:4]}-{d[4:6]}-{d[6:]}T{tm[:2]}:{tm[2:4]}:{tm[4:]}"
    stop = datetime.datetime.fromtimestamp(frames.stat().st_mtime).isoformat(timespec="seconds")
    threads = frames.name.replace("_frames.csv", "_threads.csv")
    rec = {"frames_csv": frames.name, "threads_csv": threads, "log": "Stronghold2AnalyseHub.log",
           "start": start, "stop": stop, "frames": recording_info(frames)[1],
           "hub_commit": "unknown",                      # latest.json belongs to another recording
           "reconstructed": "latest.json missing or names another recording"}
    samples_csv = frames.name.replace("_frames.csv", "_samples.csv")
    if (src / samples_csv).exists():
        rec["samples_csv"] = samples_csv
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exp", required=True, help="experiment id, e.g. EXP-001")
    ap.add_argument("--scenario", required=True, help="e.g. KNIGHTS")
    ap.add_argument("--troops", type=int, required=True, help="troops per player")
    ap.add_argument("--variant", default="auto", help="auto = detect from TEST folder")
    ap.add_argument("--note", default="")
    ap.add_argument("--src", default=str(paths.HUB_OUT))
    ap.add_argument("--recording", default="", help="timestamp of the recording, e.g. 20261015_034411")
    ap.add_argument("--captures", default=str(paths.CAPTURES), help=argparse.SUPPRESS)
    ap.add_argument("--index", default=str(paths.INDEX), help=argparse.SUPPRESS)
    a = ap.parse_args()

    src = Path(a.src)
    latest_path = src / "latest.json"
    latest = choose_recording(src, a.recording)

    var = variant_tool.current_variant() if a.variant == "auto" else a.variant
    day = latest["start"][:10].replace("-", "")
    capture_id = f"{day}_{a.exp}_{var}_{a.scenario}"
    dest = Path(a.captures) / capture_id
    n = 2
    while dest.exists():                       # same exp/variant/scenario twice a day
        dest = Path(a.captures) / f"{capture_id}_{n}"
        n += 1
    capture_id = dest.name
    dest.mkdir(parents=True)

    to_remove = []                              # sources are deleted only at the very end
    for key in ("frames_csv", "threads_csv", "samples_csv", "log"):
        f = src / latest[key] if key in latest else None
        if f and f.exists():
            shutil.copy2(f, dest / f.name)
            if key != "log":
                to_remove.append(f)
    meta_latest = {k: v for k, v in latest.items() if k != "_from_latest_json"}
    (dest / "latest.json").write_text(json.dumps(meta_latest, indent=2))
    if latest.get("_from_latest_json"):
        to_remove.append(latest_path)

    meta = {
        "capture_id": capture_id, "exp": a.exp, "variant": var, "scenario": a.scenario,
        "troops": a.troops, "note": a.note, "start": latest["start"], "stop": latest["stop"],
        "hub_commit": latest.get("hub_commit", "unknown"), "binaries_sha256_16": binaries_meta(),
        **hardware(),
        "ingested": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    (dest / "meta.json").write_text(json.dumps(meta, indent=2))

    frames = dest / latest["frames_csv"]
    (dest / "timeline.md").write_text(
        "\n".join(analyze_frames.format_timeline(analyze_frames.timeline(str(frames), 5.0), 5.0)) + "\n")
    total = analyze_frames.summarize(str(frames))
    if not total:
        sys.exit(f"{capture_id}: fewer than 2 frames recorded; meta.json written, no index line")
    phases = []
    for m in analyze_frames.markers(str(frames)):
        s = analyze_frames.summarize(str(frames), m, m + 1)
        if s:
            phases.append({"marker": m, "frames": s["frames"], "avg_fps": s["avg_fps"],
                           "p50_ms": s["p50_ms"], "p99_ms": s["p99_ms"], "cpu_side_ms": s["cpu_side_ms"],
                           "present_ms": s["present_ms"], "dip": s["dip"]})
    line = {k: meta[k] for k in ("capture_id", "exp", "variant", "scenario", "troops", "start",
                                 "hub_commit", "cpu", "gpu")}
    line.update({"total": total, "phases": phases})
    sample_groups = None
    if latest.get("samples_csv") and (dest / latest["samples_csv"]).exists():
        g = samples.groups(str(dest / latest["samples_csv"]))
        sample_groups = {"all": samples.shares(g[-1])[0], "n": samples.shares(g[-1])[1],
                         "by_marker": {str(m): samples.shares(c)[0] for m, c in g.items() if m >= 0}}
        line["render_modules"] = sample_groups
    index = Path(a.index)
    index.parent.mkdir(parents=True, exist_ok=True)
    with open(index, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, separators=(",", ":")) + "\n")

    for f in to_remove:
        f.unlink()
    log = src / latest["log"]                   # the hub log is shared by all recordings of a session
    if log.exists() and not list(src.glob("*_frames.csv")):
        try:
            log.unlink()
        except OSError:
            pass                                # still open by a running game

    # Summary (<= 30 lines).
    t = total
    print(f"ingested {capture_id}  ({t['frames']} frames, {t['duration_s']} s, hub {meta['hub_commit']})")
    print(f"total: {t['avg_fps']} FPS avg, 1% low {t['low1_fps']}, p50/p99 {t['p50_ms']}/{t['p99_ms']} ms")
    print(f"       present {t['present_ms']} ms, cpu-side {t['cpu_side_ms']} ms, DIP {t['dip']}/frame, VA max {t['va_max_mb']} MB")
    for th in t["threads"][:3]:
        print(f"       thread {th['tid']}{' (render)' if th['render'] else ''}: {th['cpu_mean']}% mean, {th['cpu_max']}% max")
    print("marker | frames | FPS  | p50 ms | p99 ms | cpu-side ms | present ms | DIP")
    for p in phases[:18]:
        print(f"{p['marker']:>6} | {p['frames']:>6} | {p['avg_fps']:>4} | {p['p50_ms']:>6} | {p['p99_ms']:>6} |"
              f" {p['cpu_side_ms']:>11} | {p['present_ms']:>10} | {p['dip']}")
    if len(phases) > 18:
        print(f"... {len(phases) - 18} more phases in data/index.jsonl")
    if sample_groups:
        print(f"render thread by module (samples.py): {samples.format_shares(g[-1])}")
        for m in sorted(k for k in g if k >= 0)[:6]:
            print(f"  marker {m}: {samples.format_shares(g[m])}")
    print(f"timeline (5 s windows): captures/{capture_id}/timeline.md")


if __name__ == "__main__":
    main()
