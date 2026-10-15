"""Import hub recordings safely (bronze) and derive silver results (D012).

Usage (every command also prints this text with --help):
  python -I tools/ingest.py list      [--src <hub out dir>]
  python -I tools/ingest.py import    [--recording <timestamp>] [--exp E] [--scenario S] [--troops N] [--variant V]
                                      [--note "..."] [--legacy] [--allow-interrupted] [--src DIR] [--game-dir DIR]
  python -I tools/ingest.py annotate  <capture_id> [--game-speed N] [--paused true|false] [--suitability suitable|not_suitable|unknown
                                      --reason "..."] [--phase-paused M=true|false ...] [--exp E] [--scenario S] [--troops N]
                                      [--variant V] [--note "..."]
  python -I tools/ingest.py verify    <capture_id>
  python -I tools/ingest.py rebuild   [--write]
Every command that writes (import, annotate, rebuild --write) first takes one local write lock (data/.sh2perf.lock, an OS lock
that disappears with its process); a second writer waits --lock-timeout seconds (default 60), then stops with exit 7 and changes
nothing. list, verify and rebuild without --write only read.
`import` is the default command: `ingest.py --exp EXP-001 --scenario KNIGHTS --troops 100` still works.

import: verify (manifest finalized, every file present with the listed size and SHA-256) -> stage a copy in
  captures/.staging/<id>/ -> one atomic rename to captures/<capture_id>/ -> derive silver (data/silver/<id>/,
  data/index.jsonl). Source files are NEVER deleted or moved. Importing the same recording again changes nothing;
  the same capture id with different content is a conflict. Several recordings in the folder: nothing is touched
  until --recording is given. A recording without a manifest needs --legacy and stays marked unverified.
annotate: user-confirmed facts (game speed, pause, suitability, labels) go to data/annotations/<id>.json, never
  into the raw data; silver is re-derived.
verify: re-hash a committed capture against its import record (detects changed raw data). The same check runs before a repeated
  import is reported as "already imported" and before silver is derived; a damaged capture stops there (exit 4), earlier silver
  results are kept but marked INVALID, bronze is never repaired by the tools.
rebuild: re-derive silver for every capture from bronze + annotations with the current tool versions
  (without --write only compares and reports).
Exit codes: 0 ok / already imported, 2 choose a recording, 3 conflict, 4 verification failed or damaged capture, 5 refused,
6 write error, 7 write lock busy.
Run after the game has exited (the hub keeps its log open while running).
"""
import argparse
import datetime
import json
import math
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bronze  # noqa: E402
import capture_manifest as cm  # noqa: E402
import filelock  # noqa: E402
import paths  # noqa: E402
import silver  # noqa: E402

ANNOTATIONS = paths.DATA / "annotations"
SILVER = paths.DATA / "silver"


def hardware():
    """CPU and GPU names via CIM; empty strings if unavailable. Skipped with SH2PERF_NO_HARDWARE=1 (tests)."""
    if os.environ.get("SH2PERF_NO_HARDWARE") == "1":
        return {"cpu": None, "gpu": None}

    def cim(cls):
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"(Get-CimInstance {cls} | Select-Object -First 1 -ExpandProperty Name)"],
                capture_output=True, text=True, timeout=30)
            return out.stdout.strip() or None
        except (OSError, subprocess.TimeoutExpired):
            return None
    return {"cpu": cim("Win32_Processor"), "gpu": cim("Win32_VideoController")}


def observer(game_dir):
    """What is true at import time: hardware and the hashes of the game folder now. Observations, never provenance."""
    def observe(p):
        obs = {"observed_utc": bronze._utc_now(), "hardware": hardware(), "flags": []}
        if p["manifest"]:
            recorded = cm.software_by_name(p["manifest"], comparable=True)
            current = {n: (cm.sha256_file(game_dir / n) if (game_dir / n).is_file() else None) for n in recorded}
            changes = cm.software_changes(recorded, current)
            obs["game_dir_hashes"] = current
            obs["software_changes"] = changes
        return obs
    return observe


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_number(text):
    """Strict number for a game speed: any finite number is accepted; the range and the meaning are not judged."""
    try:
        v = float(text)
    except ValueError:
        sys.exit(f"game speed {text!r} is not a number")
    if not math.isfinite(v):
        sys.exit(f"game speed {text!r} is not a finite number")
    return int(v) if v == int(v) else v


def apply_annotation(capture_id, a):
    """Merge the given facts into data/annotations/<id>.json (with history); returns True if anything changed."""
    ann = silver.load_annotations(ANNOTATIONS, capture_id) or silver.empty_annotations(capture_id)
    at, changed = utc_now(), False

    def record(field, old, new):
        ann["history"].append({"at": at, "field": field, "old": old, "new": new})

    for key in ("exp", "scenario", "troops", "variant", "note"):
        val = getattr(a, key, None)
        if val is not None and ann["labels"].get(key) != val:
            record(f"labels.{key}", ann["labels"].get(key), val)
            ann["labels"][key] = val
            changed = True
    speed = getattr(a, "game_speed", None)
    if speed is not None:
        value = parse_number(speed)
        if (ann.get("game_speed") or {}).get("value") != value:
            record("game_speed", (ann.get("game_speed") or {}).get("value"), value)
            ann["game_speed"] = {"value": value, "origin": "user_confirmed", "at": at}
            changed = True
    paused = getattr(a, "paused", None)
    if paused is not None:
        value = {"true": True, "false": False}[paused]
        if (ann.get("paused") or {}).get("value") != value:
            record("paused", (ann.get("paused") or {}).get("value"), value)
            ann["paused"] = {"value": value, "origin": "user_confirmed", "at": at}
            changed = True
    for item in getattr(a, "phase_paused", None) or []:
        pid, _, val = item.partition("=")
        value = {"true": True, "false": False}[val]
        old = (ann.get("phase_paused") or {}).get(pid, {}).get("value")
        if old != value:
            record(f"phase_paused.{pid}", old, value)
            ann.setdefault("phase_paused", {})[pid] = {"value": value, "origin": "user_confirmed", "at": at}
            changed = True
    suit = getattr(a, "suitability", None)
    if suit is not None:
        new = {"verdict": suit, "reason": getattr(a, "reason", None), "at": at}
        old = ann.get("suitability") or {}
        if (old.get("verdict"), old.get("reason")) != (new["verdict"], new["reason"]):
            record("suitability", old.get("verdict"), suit)
            ann["suitability"] = new
            changed = True
    if changed:
        silver.save_annotations(ANNOTATIONS, capture_id, ann)
    return changed


def check_intact(capture_dir):
    """The one integrity check in front of every use of a committed capture. On damage: earlier silver results are kept
    but marked not valid, nothing new is derived, and ImportFailure(EXIT_VERIFY) is raised. Bronze is never touched."""
    cid = (bronze._read_json(capture_dir / "import.json") or {}).get("capture_id", capture_dir.name)
    problems, _ = bronze.verify_committed(capture_dir)
    if problems:
        silver.mark_invalid(SILVER, paths.INDEX, cid, problems)
        bronze.require_intact(capture_dir)


def refresh_silver(capture_dir):
    """Derive silver for one committed capture and update its index line. Safe to repeat."""
    check_intact(capture_dir)
    cid = (bronze._read_json(capture_dir / "import.json") or {}).get("capture_id", capture_dir.name)
    s = silver.derive(capture_dir, silver.load_annotations(ANNOTATIONS, cid))
    silver.write_silver(s, SILVER)
    silver.update_index(paths.INDEX, silver.index_line(s))
    return s


def na(v):
    return "n/a" if v is None else v


def print_summary(s, state, captures):
    t, q = s["total"], s["quality"]
    gs, ps = s["game"]["game_speed"]["resolved"], s["game"]["paused"]["resolved"]
    print(f"{state} {s['capture_id']}  ({s['provenance']}, captures/{s['capture_id']})")
    bs = q["benchmark_suitability"]
    print(f"integrity: {bs['integrity']['status']} ({q['technical']['basis']}) | description {bs['completeness']['profile']}: "
          f"{'complete' if bs['completeness']['complete'] else 'INCOMPLETE'} | release: {bs['verdict']} | "
          f"reference-v1 passed and released: {'yes' if bs['usable_as_benchmark'] else 'NO'} (does not show same save, graphics, V-Sync or hardware)")
    print(f"game speed: {na(gs['value'])} ({gs['origin']}{', CONFLICT' if gs['conflict'] else ''}) | "
          f"paused: {na(ps['value'])} ({ps['origin']}{', per phase only' if len(s['phases']) > 1 else ''})")
    for r in bs["rejections"][:6]:
        print(f"  - {r['code']}: {r['text']}")
    if len(bs["rejections"]) > 6:
        print(f"  ... {len(bs['rejections']) - 6} more in data/silver/{s['capture_id']}/summary.json")
    if not t:
        print("fewer than 2 frames recorded: no metrics")
        return
    print(f"total: {t['frames']} frames, {t['duration_s']} s, {t['avg_fps']} FPS avg, 1% low {t['low1_fps']}, p50/p99 {t['p50_ms']}/{t['p99_ms']} ms")
    print(f"       present {na(t['present_ms'])} ms, cpu-side {na(t['cpu_side_ms'])} ms, DIP {na(t['dip'])}/frame, VA max {na(t['va_max_mb'])} MB")
    for th in t["threads"][:2]:
        print(f"       thread {th['tid']}{' (render)' if th['render'] else ''}: {th['cpu_mean']}% mean, {th['cpu_max']}% max")
    print("marker | frames | FPS  | p50 ms | p99 ms | cpu-side ms | present ms | DIP")
    for p in s["phases"][:10]:
        print(f"{p['marker']:>6} | {p['frames']:>6} | {p['avg_fps']:>4} | {p['p50_ms']:>6} | {p['p99_ms']:>6} |"
              f" {na(p['cpu_side_ms']):>11} | {na(p['present_ms']):>10} | {na(p['dip'])}")
    if len(s["phases"]) > 10:
        print(f"... {len(s['phases']) - 10} more phases in data/silver/{s['capture_id']}/summary.json")
    if s["flags"]:
        print("flags: " + ", ".join(s["flags"]))


def fail(e):
    print(e.message, file=sys.stderr)
    for d in e.details[:12]:
        print(f"  - {d}", file=sys.stderr)
    if len(e.details) > 12:
        print(f"  ... {len(e.details) - 12} more", file=sys.stderr)
    sys.exit(e.code)


def test_pause_hook():
    """Tests only: SH2PERF_TEST_PAUSE_BEFORE_COMMIT=<file> keeps the importer inside its locked section, staging written,
    until <file> exists - how the tests hold a real second process at the critical moment."""
    flag = os.environ.get("SH2PERF_TEST_PAUSE_BEFORE_COMMIT")
    if not flag:
        return None

    def hook(point, **ctx):
        if point == "before_commit":
            import time
            deadline = time.time() + 120
            while not Path(flag).exists() and time.time() < deadline:
                time.sleep(0.05)
    return hook


def cmd_list(a):
    recs = bronze.find_recordings(Path(a.src))
    if not recs:
        print(f"no recording in {a.src}")
    for r in recs:
        print(bronze.describe(r))


def cmd_import(a):
    src, captures = Path(a.src), Path(a.captures)
    try:
        rec = bronze.select(src, a.recording)
        result = bronze.import_recording(rec, captures, legacy=a.legacy, allow_interrupted=a.allow_interrupted,
                                         observed=observer(Path(a.game_dir)), inject=test_pause_hook())
    except bronze.ImportFailure as e:
        if e.code == bronze.EXIT_SELECT:
            print(e.message)
            for d in e.details:
                print(f"  {d}")
            sys.exit(e.code)
        fail(e)
    cid = result["capture_id"]
    apply_annotation(cid, a)
    s = refresh_silver(result["dest"])
    if result["state"] == "already_imported":
        print("already imported: bronze unchanged, silver refreshed (no duplicate)")
    print_summary(s, "imported" if result["state"] == "imported" else "present", captures)
    print(f"source files left in place: {src.name}/{rec.stem}_* (delete them yourself when you no longer need them)")


def cmd_annotate(a):
    d = Path(a.captures) / a.capture_id
    if not (d / "import.json").exists() and not (d / "meta.json").exists():
        sys.exit(f"{a.capture_id}: not a committed capture in {a.captures}")
    check_intact(d)                               # no annotation on a damaged basis
    for item in a.phase_paused or []:
        pid, sep, val = item.partition("=")
        phases = {str(ph["marker"]) for ph in silver.derive(d, silver.load_annotations(ANNOTATIONS, a.capture_id))["phases"]}
        if not sep or val not in ("true", "false") or pid not in phases:
            sys.exit(f"--phase-paused {item!r}: use <marker>=true|false with a marker of this recording ({', '.join(sorted(phases)) or 'none'})")
    changed = apply_annotation(a.capture_id, a)
    s = refresh_silver(d)
    print(("annotations updated" if changed else "nothing to change") + f": data/annotations/{a.capture_id}.json")
    print_summary(s, "silver refreshed", Path(a.captures))


def cmd_verify(a):
    d = Path(a.captures) / a.capture_id
    problems, verifiable = bronze.verify_committed(d)
    if not verifiable and not problems:
        sys.exit(f"{a.capture_id}: no import record (folder from before D012 or not a capture): nothing to verify against")
    if problems:
        print(f"{a.capture_id} is damaged (raw data changed):", file=sys.stderr)
        print("\n".join("  - " + p for p in problems), file=sys.stderr)
        sys.exit(bronze.EXIT_VERIFY)
    imp = bronze._read_json(d / "import.json")
    print(f"{a.capture_id}: {len(imp['files'])} files and manifest match the import record")


def cmd_rebuild(a):
    captures = Path(a.captures)
    summaries, damaged = [], {}
    for d in sorted(captures.iterdir()) if captures.exists() else []:
        if not (d.is_dir() and not d.name.startswith(".") and ((d / "import.json").exists() or (d / "meta.json").exists())):
            continue
        imp = bronze._read_json(d / "import.json") or {}
        cid = imp.get("capture_id") or (bronze._read_json(d / "meta.json") or {}).get("capture_id", d.name)
        problems, _ = bronze.verify_committed(d)
        if problems:
            damaged[cid] = problems
            if a.write:
                silver.mark_invalid(SILVER, paths.INDEX, cid, problems)
            continue
        summaries.append(silver.derive(d, silver.load_annotations(ANNOTATIONS, cid)))
    existing = silver.read_index(paths.INDEX)
    same, differ, new = 0, [], []
    for s in summaries:
        text = json.dumps(silver.index_line(s), separators=(",", ":"))
        old = existing.get(s["capture_id"])
        if old is None:
            new.append(s["capture_id"])
        elif old == text:
            same += 1
        else:
            differ.append(s["capture_id"])
    print(f"{len(summaries)} captures derived with {silver.TOOL['name']} {silver.TOOL['version']}: "
          f"{same} index lines identical, {len(differ)} differ, {len(new)} missing, {len(damaged)} damaged (skipped)")
    for cid in differ[:8]:
        print(f"  differs: {cid}")
    if a.write:
        for s in summaries:
            silver.write_silver(s, SILVER)
            silver.update_index(paths.INDEX, silver.index_line(s))
        print(f"written: data/silver/ ({len(summaries)} captures) and {len(differ) + len(new)} index lines")
    else:
        print("nothing written (use --write to replace the index lines and write data/silver/)")
    if damaged:
        for cid, problems in damaged.items():
            print(f"DAMAGED {cid}: {'; '.join(problems[:3])}", file=sys.stderr)
        print(f"{len(damaged)} capture(s) damaged: earlier results kept{' and marked INVALID' if a.write else ''}, nothing new derived, bronze untouched",
              file=sys.stderr)
        sys.exit(bronze.EXIT_VERIFY)


def main():
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")      # file names in messages may not be ASCII
    argv = sys.argv[1:]
    commands = ("list", "import", "annotate", "verify", "rebuild")
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return
    if argv[0] not in commands:
        argv = ["import"] + argv
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--src", default=str(paths.HUB_OUT))
    common.add_argument("--captures", default=str(paths.CAPTURES), help=argparse.SUPPRESS)
    common.add_argument("--index", default=str(paths.INDEX), help=argparse.SUPPRESS)
    common.add_argument("--lock-timeout", type=float, default=60.0, help="seconds to wait for the write lock (default 60)")
    labels = argparse.ArgumentParser(add_help=False)
    labels.add_argument("--exp")
    labels.add_argument("--scenario")
    labels.add_argument("--troops", type=int)
    labels.add_argument("--variant")
    labels.add_argument("--note")
    ap = argparse.ArgumentParser(prog="ingest.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", parents=[common])
    p = sub.add_parser("import", parents=[common, labels])
    p.add_argument("--recording", default="", help="timestamp, e.g. 20261015_034411")
    p.add_argument("--legacy", action="store_true", help="accept a recording without manifest as unverified")
    p.add_argument("--allow-interrupted", action="store_true", help="keep a recording whose manifest never reached 'finalized'")
    p.add_argument("--game-dir", default=str(paths.TEST), help="folder whose files are compared with the recorded identity")
    p = sub.add_parser("annotate", parents=[common, labels])
    p.add_argument("capture_id")
    p.add_argument("--game-speed", help="number, as the user saw it in the game; recorded as user_confirmed")
    p.add_argument("--paused", choices=("true", "false"))
    p.add_argument("--suitability", choices=("suitable", "not_suitable", "unknown"))
    p.add_argument("--reason")
    p.add_argument("--phase-paused", action="append", metavar="MARKER=true|false",
                   help="user-confirmed pause state of one F8 phase (repeatable); a global pause is no proof for a mixed recording")
    p = sub.add_parser("verify", parents=[common])
    p.add_argument("capture_id")
    p = sub.add_parser("rebuild", parents=[common])
    p.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    global ANNOTATIONS, SILVER
    # test hooks: --index lives in data/, annotations and silver sit next to it
    paths.INDEX = Path(a.index)
    ANNOTATIONS = paths.INDEX.parent / "annotations"
    SILVER = paths.INDEX.parent / "silver"
    run = {"list": cmd_list, "import": cmd_import, "annotate": cmd_annotate, "verify": cmd_verify, "rebuild": cmd_rebuild}[a.cmd]
    if a.cmd in ("import", "annotate") or (a.cmd == "rebuild" and a.write):
        lock = paths.INDEX.parent / ".sh2perf.lock"
        try:
            with filelock.exclusive(lock, a.lock_timeout):
                run(a)
        except filelock.Busy as e:
            print(f"busy: {e.holder} holds the write lock {lock.name} (waited {e.waited:.0f} s). Nothing was changed; "
                  "run again when the other ingest.py has finished (a crashed one releases the lock by itself).", file=sys.stderr)
            sys.exit(bronze.EXIT_BUSY)
        except bronze.ImportFailure as e:
            fail(e)
    else:
        try:
            run(a)
        except bronze.ImportFailure as e:
            fail(e)


if __name__ == "__main__":
    main()
