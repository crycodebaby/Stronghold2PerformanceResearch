"""Ingest the latest hub recording: bronze capture folder + silver index line.

Usage:
  python -I tools/ingest.py --exp EXP-001 --scenario KNIGHTS --troops 100 [--note "..."]
         [--variant auto] [--src <hub out dir>]

Steps:
  1. Read <src>/latest.json (written by the hub on F9 stop; default src = TEST\\SH2Perf_out).
  2. Move the listed CSVs, the log and latest.json to
     captures/<YYYYMMDD>_<EXP>_<variant>_<scenario>/ (bronze, gitignored).
  3. Write meta.json there (hashes of exe/DLLs, variant, scenario, troops, CPU/GPU, hub commit).
  4. Append one metrics line to data/index.jsonl (silver; no absolute paths).
  5. Print a summary of at most 30 lines.
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
    """Hashes identify the exact build measured (exe, optional DXVK d3d9, hub)."""
    files = {
        "Stronghold2.exe": paths.TEST / "Stronghold2.exe",
        "d3d9.dll (TEST folder)": paths.TEST / "d3d9.dll",
        "Stronghold2AnalyseHub.dll": paths.HUB_BUILD / "Stronghold2AnalyseHub.dll",
    }
    return {name: sha256(p)[:16] for name, p in files.items() if p.exists()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exp", required=True, help="experiment id, e.g. EXP-001")
    ap.add_argument("--scenario", required=True, help="e.g. KNIGHTS")
    ap.add_argument("--troops", type=int, required=True, help="troops per player")
    ap.add_argument("--variant", default="auto", help="auto = detect from TEST folder")
    ap.add_argument("--note", default="")
    ap.add_argument("--src", default=str(paths.HUB_OUT))
    ap.add_argument("--captures", default=str(paths.CAPTURES), help=argparse.SUPPRESS)
    ap.add_argument("--index", default=str(paths.INDEX), help=argparse.SUPPRESS)
    a = ap.parse_args()

    src = Path(a.src)
    latest_path = src / "latest.json"
    if not latest_path.exists():
        sys.exit(f"no latest.json in {src} - record with F9 (start) and F9 (stop) first")
    latest = json.loads(latest_path.read_text())
    frames_csv = src / latest["frames_csv"]
    if not frames_csv.exists():
        sys.exit(f"{latest['frames_csv']} missing - already ingested?")

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

    for key in ("frames_csv", "threads_csv", "log"):
        f = src / latest[key]
        if f.exists():
            shutil.move(str(f), dest / f.name)
    shutil.move(str(latest_path), dest / "latest.json")

    meta = {
        "capture_id": capture_id, "exp": a.exp, "variant": var, "scenario": a.scenario,
        "troops": a.troops, "note": a.note, "start": latest["start"], "stop": latest["stop"],
        "hub_commit": latest.get("hub_commit", "unknown"), "binaries_sha256_16": binaries_meta(),
        **hardware(),
        "ingested": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    (dest / "meta.json").write_text(json.dumps(meta, indent=2))

    frames = dest / latest["frames_csv"]
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
    index = Path(a.index)
    index.parent.mkdir(parents=True, exist_ok=True)
    with open(index, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, separators=(",", ":")) + "\n")

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


if __name__ == "__main__":
    main()
