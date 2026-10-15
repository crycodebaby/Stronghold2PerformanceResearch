"""Silver layer: summaries derived from bronze (`captures/<id>/`) plus user annotations, D012. Library; CLI = `ingest.py`.

Everything here is a pure function of (bronze folder, annotations file, TOOL version): running it again gives the
same bytes, which is what makes silver results reproducible ("rebuild"). Bronze is only read.

Files:
  data/silver/<capture_id>/summary.json   full derived record (git-ignored, rebuilt)
  data/silver/<capture_id>/timeline.md    5 s windows
  data/index.jsonl                        one compact line per capture (tracked)
  data/annotations/<capture_id>.json      human input: labels, user-confirmed game speed / pause, suitability (tracked)

Reference profile `reference-v1` (the only rule set; see docs/FORMATS/CAPTURE_MANIFEST.md): a capture is usable as a
reference benchmark only if (1) its integrity is ok, (2) the experiment description is complete (experiment, scenario, variant,
game speed known and not contradicted, switches known, software identity present, pause known for every phase) and (3) the
user released it. The three are judged separately and every failure is listed with a code and a text.

Change SILVER_VERSION whenever the derivation changes; every summary and index line names the version that made it.
"""
import json
import os
from pathlib import Path

import analyze_frames
import capture_manifest as cm
import samples

TOOL = {"name": "sh2perf-silver", "version": "2.1.0"}
SILVER_SCHEMA = 3
REFERENCE_PROFILE = "reference-v1"
ANNOTATION_SCHEMA = "sh2perf.annotations"

# Metrics that exist only while a hub switch is on (D011); the CSV holds 0 for them otherwise.
UNMEASURED = {
    "counters": ("dip", "dp", "dpup", "dipup", "prims", "settex", "vsconst_calls", "psconst_calls"),
    "overlay": ("endscene_ms", "between_endscene_ms", "overlay_ms", "cpu_side_ms"),
    "poll": ("va_max_mb",),
}


def mask_unmeasured(metrics, modes):
    """Copy of a summary dict with the metrics of switched-off hub parts set to None.

    Only a switch that is known to be off masks; unknown (None) or absent modes mask nothing (and the caller records
    that the modes are unknown instead of assuming they were on).
    """
    out = dict(metrics)
    for switch, keys in UNMEASURED.items():
        if modes and modes.get(switch) is False:
            for k in keys:
                if k in out:
                    out[k] = None
    if modes and modes.get("poll") is False and "threads" in out:
        out["threads"] = []
    return out


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


# --- annotations (human input) ---------------------------------------------------------------------------

def annotation_path(root, capture_id):
    return Path(root) / f"{capture_id}.json"


def load_annotations(root, capture_id):
    a = _read_json(annotation_path(root, capture_id))
    return a if isinstance(a, dict) and a.get("schema") == ANNOTATION_SCHEMA else None


def write_atomic(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as f:
        f.write(text.encode("utf-8"))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def save_annotations(root, capture_id, ann):
    write_atomic(annotation_path(root, capture_id), json.dumps(ann, indent=2, ensure_ascii=False) + "\n")


def empty_annotations(capture_id):
    return {"schema": ANNOTATION_SCHEMA, "version": 1, "capture_id": capture_id, "labels": {}, "history": []}


# --- game speed / pause: keep the origins apart ----------------------------------------------------------

_STRENGTH = {"observed": 3, "user_confirmed": 2, "planned": 1}


def resolve_origins(by_origin):
    """{origin: value} -> {'value','origin','conflict','planned_differs'}; nothing known -> value None, origin 'unknown'.

    The strongest origin wins (observed > user_confirmed > planned). If an observed and a user-confirmed value
    disagree, nothing is chosen (conflict). A planned value that differs from a stronger one is reported.
    """
    known = {o: v for o, v in by_origin.items() if v is not None}
    if not known:
        return {"value": None, "origin": "unknown", "conflict": False, "planned_differs": False}
    if "observed" in known and "user_confirmed" in known and known["observed"] != known["user_confirmed"]:
        return {"value": None, "origin": "unknown", "conflict": True, "planned_differs": False}
    best = max(known, key=lambda o: _STRENGTH[o])
    return {"value": known[best], "origin": best, "conflict": False,
            "planned_differs": "planned" in known and known["planned"] != known[best]}


def phase_pause(recording_level, phase_ids, ann):
    """Pause state per phase. A global pause statement is evidence for a recording with ONE phase only; in a recording
    with several F8 phases it says nothing about the individual phases, so each of them stays unknown until the user
    confirms it (annotate --phase-paused M=true|false). Nothing is read from game memory."""
    mine = (ann or {}).get("phase_paused") or {}
    out = {}
    for pid in phase_ids:
        if len(phase_ids) == 1:
            out[pid] = {"value": recording_level["value"], "origin": recording_level["origin"]}
        elif isinstance(mine.get(pid), dict) and isinstance(mine[pid].get("value"), bool):
            out[pid] = {"value": mine[pid]["value"], "origin": "user_confirmed"}
        else:
            out[pid] = {"value": None, "origin": "unknown"}
    return out


def collect_origins(manifest, ann, key):
    """Values of game.<key> per origin: the hub's (planned / observed) and the user's confirmation."""
    by = {"planned": None, "user_confirmed": None, "observed": None}
    item = ((manifest or {}).get("game") or {}).get(key)
    if isinstance(item, dict) and item.get("value") is not None and item.get("origin") in by:
        by[item["origin"]] = item["value"]
    mine = (ann or {}).get(key)
    if isinstance(mine, dict) and mine.get("value") is not None:
        by["user_confirmed"] = mine["value"]
    return {"by_origin": by, "resolved": resolve_origins(by)}


# --- derivation ------------------------------------------------------------------------------------------

def _frames_path(cdir, imp, latest):
    if imp:
        for f in imp.get("files", []):
            if f.get("role") == "frames":
                return cdir / f["name"]
    if latest and latest.get("frames_csv"):
        return cdir / latest["frames_csv"]
    found = sorted(cdir.glob("SH2Perf_*_frames.csv"))
    return found[0] if found else None


def _role_file(cdir, imp, latest, role, legacy_key):
    if imp:
        for f in imp.get("files", []):
            if f.get("role") == role:
                return cdir / f["name"]
    if latest and latest.get(legacy_key):
        return cdir / latest[legacy_key]
    return None


_REJECTION_TEXTS = {
    "technical_quality_degraded": "the recording lost frames or had write errors",
    "technical_quality_incomplete": "the recording was interrupted and never finalized",
    "technical_quality_unknown": "no capture health information exists for this recording",
    "interrupted": "the recording was interrupted",
    "legacy_unverified_origin": "the recording has no manifest; its origin and software cannot be verified",
    "no_usable_frames": "fewer than two frames were recorded",
    "experiment_unknown": "the experiment is not named",
    "scenario_unknown": "the scenario is not named",
    "variant_unknown": "the variant of the game folder is unknown",
    "game_speed_unknown": "the game speed is unknown (neither planned, observed nor confirmed by the user)",
    "game_speed_conflict": "the game speed statements contradict each other (observed and user-confirmed differ)",
    "switches_unknown": "the hub measurement switches of this recording are unknown",
    "software_identity_missing": "the hash of the game exe or hub DLL taken in the session is missing",
    "pause_unknown": "it is not known whether the game was paused",
    "not_released": "nobody has released the recording as a reference benchmark",
    "released_unsuitable": "the user judged the recording not suitable",
}


def REJECTION_TEXT(code):
    if code.startswith("pause_unknown_phase_"):
        return f"it is not confirmed whether the game was paused in phase (marker) {code.rsplit('_', 1)[1]}"
    return _REJECTION_TEXTS.get(code, code)


def derive(cdir, ann=None):
    """Summary dict of one bronze capture folder. Pure: same inputs -> same output."""
    cdir = Path(cdir)
    imp = _read_json(cdir / "import.json")
    meta = _read_json(cdir / "meta.json") or {}
    latest = _read_json(cdir / "latest.json")
    latest = latest if isinstance(latest, dict) else None
    manifest = None
    if (cdir / "manifest.json").exists():
        manifest = cm.parse((cdir / "manifest.json").read_bytes())
    provenance = "manifest" if manifest else "legacy"
    ann = ann or {}
    labels = ann.get("labels", {})
    flags = list(imp.get("flags", [])) if imp else ["legacy_unverified"]
    observed = (imp or {}).get("observed_at_import", {})

    prepared = None
    if imp:
        pf = next((f for f in imp.get("files", []) if f.get("role") == "prepared"), None)
        if pf:
            prepared = _read_json(cdir / pf["name"])
            if not isinstance(prepared, dict):
                prepared, flags = None, flags + ["prepared_record_unreadable"]

    # switches: the manifest is authoritative; a v2 latest.json is the hub's own statement; otherwise unknown
    if manifest:
        modes, modes_basis = cm.switches(manifest), "manifest"
    elif latest and isinstance(latest.get("modes"), dict):
        modes, modes_basis = latest["modes"], "latest.json (capture_version 2, unverified link)"
    else:
        modes, modes_basis = None, "unknown"
    switches_known = bool(modes) and all(modes.get(k) is not None for k in ("frametime", "counters", "poll", "overlay"))

    # technical quality: facts about the files, kept apart from the benchmark judgement
    if manifest:
        q = manifest.get("technical_quality") or {}
        technical = {"status": cm.technical_status(manifest), "basis": "manifest", "completion": cm.completion(manifest),
                     "capture_ok": q.get("capture_ok"), "frames_dropped": q.get("frames_dropped"),
                     "frames_lost_write": q.get("frames_lost_write"), "write_errors": q.get("write_errors")}
    elif latest and "capture_ok" in latest:
        ok = latest.get("capture_ok")
        technical = {"status": "ok" if ok else "degraded", "basis": "latest.json (hub report, unverified link)",
                     "completion": "legacy", "capture_ok": ok, "frames_dropped": latest.get("frames_dropped"),
                     "frames_lost_write": latest.get("frames_lost_write"), "write_errors": latest.get("write_errors")}
    else:
        technical = {"status": "unknown", "basis": "legacy: the recording carries no health information",
                     "completion": "legacy", "capture_ok": None, "frames_dropped": None,
                     "frames_lost_write": None, "write_errors": None}

    # software identity
    by_name = cm.software_by_name(manifest) if manifest else {}
    soft = {"basis": "hub_session_start" if manifest else "legacy: only hashes taken at import time exist",
            "hub_commit": ((manifest or {}).get("software") or {}).get("hub", {}).get("commit")
            or (latest or {}).get("hub_commit") or meta.get("hub_commit"),
            "hub_dirty": ((manifest or {}).get("software") or {}).get("hub", {}).get("dirty"),
            "pending": bool(((manifest or {}).get("software") or {}).get("pending")),
            "files": by_name}
    if not manifest and meta.get("binaries_sha256_16"):
        soft["import_time_hashes_16"] = meta["binaries_sha256_16"]          # short, taken at ingest, not provenance
    if prepared:
        prep_files = {f["name"]: f.get("sha256") for f in prepared.get("files", []) if isinstance(f, dict) and f.get("name")}
        soft["prepared"] = {"prepared_utc": prepared.get("prepared_utc"), "variant": prepared.get("variant"), "files": prep_files}
        comparable = cm.software_by_name(manifest, comparable=True)
        diff = sorted(n for n, sha in prep_files.items() if n in comparable and sha and comparable[n] and sha != comparable[n]
                      and not n.endswith(".ini"))
        if diff:
            soft["prepared_vs_session"] = diff
            flags.append("software_differs_from_prepared")
    changed = (observed.get("software_changes") or {})
    if changed:
        soft["changed_after_capture"] = changed          # observation at import time; the session hashes above stay the identity
        flags.append("software_changed_after_capture")

    # game speed / pause
    game = {"game_speed": collect_origins(manifest, ann, "game_speed"), "paused": collect_origins(manifest, ann, "paused")}

    # labels (planned in the manifest, user-given in annotations, or the legacy meta.json)
    plan = (manifest or {}).get("plan") or {}
    lab = {
        "exp": labels.get("exp") or plan.get("experiment") or meta.get("exp"),
        "scenario": labels.get("scenario") or plan.get("scenario") or meta.get("scenario"),
        "protocol": labels.get("protocol") or plan.get("protocol"),
        "troops": labels["troops"] if "troops" in labels else meta.get("troops"),
        "variant": labels.get("variant") or (prepared or {}).get("variant") or meta.get("variant"),
        "note": labels.get("note") if "note" in labels else meta.get("note"),
    }

    # metrics from the frames CSV
    frames = _frames_path(cdir, imp, latest)
    total, phases, tl, render_modules = None, [], "", None
    if frames and frames.exists():
        total = analyze_frames.summarize(str(frames))
        if total:
            total = mask_unmeasured(total, modes)
            for m in analyze_frames.markers(str(frames)):
                s = analyze_frames.summarize(str(frames), m, m + 1)
                if s:
                    s = mask_unmeasured(s, modes)
                    phases.append({"marker": m, "frames": s["frames"], "avg_fps": s["avg_fps"], "p50_ms": s["p50_ms"],
                                   "p99_ms": s["p99_ms"], "cpu_side_ms": s["cpu_side_ms"],
                                   "present_ms": s["present_ms"], "dip": s["dip"]})
        tl = "\n".join(analyze_frames.format_timeline(analyze_frames.timeline(str(frames), 5.0), 5.0)) + "\n"
        sp = _role_file(cdir, imp, latest, "samples", "samples_csv")
        if sp and sp.exists():
            g = samples.groups(str(sp))
            render_modules = {"all": samples.shares(g[-1])[0], "n": samples.shares(g[-1])[1],
                              "by_marker": {str(m): samples.shares(c)[0] for m, c in g.items() if m >= 0}}

    # phases and pause per phase (the recording-level pause only counts for a single-phase recording)
    phase_ids = [str(ph["marker"]) for ph in phases]
    rec_pause = game["paused"]["resolved"]
    game["paused"]["recording_level"] = rec_pause
    game["paused"]["by_phase"] = phase_pause(rec_pause, phase_ids, ann)
    if len(phase_ids) > 1:
        game["paused"]["resolved"] = {"value": None, "origin": "unknown", "conflict": False, "planned_differs": False}

    # integrity (technical), completeness (experiment description, profile reference-v1) and release (user) are judged apart
    reasons = []
    if technical["status"] != "ok":
        reasons.append(f"technical_quality_{technical['status']}")
    if technical["completion"] == "interrupted":
        reasons.append("interrupted")
    if provenance == "legacy":
        reasons.append("legacy_unverified_origin")
    if total is None:
        reasons.append("no_usable_frames")
    integrity = {"status": technical["status"] if reasons else "ok", "reasons": reasons}

    missing = []
    for code, value in (("experiment_unknown", lab["exp"]), ("scenario_unknown", lab["scenario"]), ("variant_unknown", lab["variant"])):
        if not value:
            missing.append(code)
    gres = game["game_speed"]["resolved"]
    if gres["conflict"]:
        missing.append("game_speed_conflict")
    elif gres["value"] is None:
        missing.append("game_speed_unknown")
    if not switches_known:
        missing.append("switches_unknown")
    roles_hashed = {f.get("role") for f in ((manifest or {}).get("software") or {}).get("files", []) if f.get("sha256")}
    if provenance != "manifest" or soft["pending"] or not {"game_exe", "hub_dll"} <= roles_hashed:
        missing.append("software_identity_missing")
    if len(phase_ids) == 1:
        if game["paused"]["by_phase"][phase_ids[0]]["value"] is None:
            missing.append("pause_unknown")
    else:
        for pid in phase_ids:
            if game["paused"]["by_phase"][pid]["value"] is None:
                missing.append(f"pause_unknown_phase_{pid}")
    completeness = {"profile": REFERENCE_PROFILE, "complete": not missing, "missing": missing}

    verdict = (ann.get("suitability") or {}).get("verdict", "unknown")
    rejections = [{"code": r, "text": REJECTION_TEXT(r)} for r in reasons + missing]
    if verdict == "unknown":
        rejections.append({"code": "not_released", "text": REJECTION_TEXT("not_released")})
    elif verdict == "not_suitable":
        why = (ann.get("suitability") or {}).get("reason")
        rejections.append({"code": "released_unsuitable", "text": REJECTION_TEXT("released_unsuitable") + (f": {why}" if why else "")})
    suit = {"verdict": verdict, "reason": (ann.get("suitability") or {}).get("reason"),
            "assessed_by": "user" if "suitability" in ann else None,
            "integrity": integrity, "completeness": completeness, "rejections": rejections,
            "usable_as_benchmark": not rejections,
            "blockers": reasons, "missing_info": missing}

    hardware = observed.get("hardware") or {"cpu": meta.get("cpu"), "gpu": meta.get("gpu")}
    start = (manifest or {}).get("recording", {}).get("start_local") or (latest or {}).get("start") or meta.get("start")
    capture_id = (imp or {}).get("capture_id") or meta.get("capture_id") or cdir.name
    return {
        "silver_schema": SILVER_SCHEMA, "tool": TOOL, "capture_id": capture_id, "provenance": provenance,
        "bronze": {"manifest_sha256": ((imp or {}).get("manifest") or {}).get("sha256"),
                   "files": {f["name"]: f["sha256"] for f in (imp or {}).get("files", [])},
                   "imported_utc": (imp or {}).get("imported_utc")},
        "start": start, "labels": lab, "game": game, "software": soft,
        "switches": {"modes": modes, "basis": modes_basis, "known": switches_known},
        "quality": {"technical": technical, "benchmark_suitability": suit},
        "flags": sorted(set(flags)), "hardware": hardware,
        "total": total, "phases": phases, "render_modules": render_modules,
        "_timeline": tl,
    }


def index_line(s):
    """Compact index line. Keys of the earlier format stay (capture_id, exp, variant, scenario, troops, start, ...)."""
    line = {"capture_id": s["capture_id"], "exp": s["labels"]["exp"], "variant": s["labels"]["variant"],
            "scenario": s["labels"]["scenario"], "troops": s["labels"]["troops"], "start": s["start"],
            "hub_commit": s["software"]["hub_commit"], "cpu": s["hardware"].get("cpu"), "gpu": s["hardware"].get("gpu"),
            "provenance": s["provenance"],
            "game_speed": {k: s["game"]["game_speed"]["resolved"][k] for k in ("value", "origin")},
            "paused": {k: s["game"]["paused"]["resolved"][k] for k in ("value", "origin")},
            "technical": s["quality"]["technical"]["status"],
            "benchmark": s["quality"]["benchmark_suitability"]["verdict"],
            "integrity": s["quality"]["benchmark_suitability"]["integrity"]["status"],
            "complete": s["quality"]["benchmark_suitability"]["completeness"]["complete"],
            "usable_as_benchmark": s["quality"]["benchmark_suitability"]["usable_as_benchmark"],
            "total": s["total"], "phases": s["phases"]}
    if s["switches"]["modes"]:
        line["modes"] = s["switches"]["modes"]
    else:
        line["modes"] = None                                        # unknown, not "all on"
    if not s["switches"]["known"]:
        line["modes_basis"] = s["switches"]["basis"]
    tq = s["quality"]["technical"]
    if tq["status"] in ("degraded", "incomplete"):
        line["capture_ok"] = False
        line["capture_loss"] = {"dropped": tq["frames_dropped"], "lost_write": tq["frames_lost_write"],
                                "write_errors": tq["write_errors"]}
    if s["render_modules"]:
        line["render_modules"] = s["render_modules"]
    if s["flags"]:
        line["flags"] = s["flags"]
    line["silver"] = f"{s['tool']['name']} {s['tool']['version']}"
    return line


def write_silver(summary, silver_root):
    """Write summary.json and timeline.md for one capture (atomic per file)."""
    d = Path(silver_root) / summary["capture_id"]
    body = {k: v for k, v in summary.items() if not k.startswith("_")}
    write_atomic(d / "summary.json", json.dumps(body, indent=2, ensure_ascii=False) + "\n")
    write_atomic(d / "timeline.md", summary["_timeline"])
    (d / INVALID_MARKER).unlink(missing_ok=True)       # derived from an intact bronze again
    return d


INVALID_MARKER = "INVALID.json"


def mark_invalid(silver_root, index_path, capture_id, problems):
    """Bronze of this capture no longer matches its import record: keep the earlier results, but mark them as not valid
    (a marker next to the summary and silver_valid=false in the index line). Nothing new is derived."""
    d = Path(silver_root) / capture_id
    if d.exists():
        write_atomic(d / INVALID_MARKER, json.dumps({
            "capture_id": capture_id, "silver_valid": False,
            "reason": "raw data no longer matches the import record; results below are from before the change and are not valid",
            "problems": list(problems)}, indent=2) + "\n")
    lines = read_index(index_path)
    if capture_id in lines:
        line = json.loads(lines[capture_id])
        line["silver_valid"] = False
        line["silver_invalid_reason"] = list(problems)[:5]
        lines[capture_id] = json.dumps(line, separators=(",", ":"))
        write_atomic(index_path, "\n".join(lines.values()) + "\n")


def read_index(index_path):
    """{capture_id: raw line text} in file order; lines that do not parse are kept under a synthetic key."""
    out = {}
    p = Path(index_path)
    if not p.exists():
        return out
    for n, raw in enumerate(p.read_text(encoding="utf-8").splitlines()):
        if not raw.strip():
            continue
        try:
            key = json.loads(raw).get("capture_id") or f"?line{n}"
        except ValueError:
            key = f"?line{n}"
        out[key] = raw
    return out


def update_index(index_path, line):
    """Insert or replace the line of one capture (by capture_id); all other lines stay byte-identical."""
    lines = read_index(index_path)
    lines[line["capture_id"]] = json.dumps(line, separators=(",", ":"))
    write_atomic(index_path, "\n".join(lines.values()) + "\n")


def derive_all(captures_root, annotations_root):
    """Summaries of every bronze capture folder (skips hidden/staging folders and folders without frames)."""
    out = []
    for d in sorted(Path(captures_root).iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        if not (d / "import.json").exists() and not (d / "meta.json").exists():
            continue
        s = derive(d, load_annotations(annotations_root, (_read_json(d / "import.json") or _read_json(d / "meta.json") or {}).get("capture_id", d.name)))
        out.append(s)
    return out
