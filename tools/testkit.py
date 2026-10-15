"""Fixtures shared by the ingest/import tests (synthetic hub recordings, manifests and a fake game folder).

Not a tool. A manifest built here follows docs/FORMATS/CAPTURE_MANIFEST.md; the C++ side is checked by the hub's
capture_test.exe, and the real DLL end to end by the stand-in run described in docs/SETUP.md.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent

HEADER = ("frame,t_s,frame_ms,present_ms,endscene_ms,between_endscene_ms,overlay_ms,scenes,dip,dp,dpup,dipup,"
          "prims,settex,vsconst_calls,vsconst_vec4,psconst_calls,psconst_vec4,va_used_mb,marker\n")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def frames_csv(frames=20, counters=True, overlay=True, poll=True, base_ms=20.0, single_phase=False):
    rows = ""
    for i in range(frames):
        dip = 100 if counters else 0
        endscene = 0.2 if overlay else 0.0
        between = base_ms - 1 if overlay else 0.0
        va = 1500 if poll else 0
        rows += f"{i},{i * base_ms / 1000:.4f},{base_ms},0.5,{endscene},{between},{0.1 if overlay else 0.0},2,{dip},10,0,0,5000,50,60,200,5,20,{va},{0 if single_phase else i // 10}\n"
    return (HEADER + rows).encode()


FULL = {"frametime": True, "counters": True, "poll": True, "overlay": True}
MIN = {"frametime": True, "counters": False, "poll": False, "overlay": False}

DEFAULT_SOFTWARE = {
    "game_exe": ("Stronghold2.exe", b"MZ original game exe"),
    "hub_dll": ("Stronghold2AnalyseHub.dll", b"MZ hub build A"),
    "d3d9_in_game_dir": ("d3d9.dll", b"MZ proxy"),
    "config_ini": ("SH2Proxy.ini", b"[proxy]\r\n"),
}


def software_files(overrides=None):
    sw = dict(DEFAULT_SOFTWARE)
    sw.update(overrides or {})
    return [{"role": role, "name": name, "size": len(data), "sha256": sha(data)} for role, (name, data) in sw.items()]


def make_game_dir(folder, overrides=None):
    """A fake game folder holding the software the manifest describes (or, with overrides, something else)."""
    folder.mkdir(parents=True, exist_ok=True)
    sw = dict(DEFAULT_SOFTWARE)
    sw.update(overrides or {})
    for _, (name, data) in sw.items():
        (folder / name).write_bytes(data)
    return folder


def make_legacy_recording(folder, stamp, frames=20, samples=False, **kw):
    (folder / f"SH2Perf_{stamp}_frames.csv").write_bytes(frames_csv(frames, **kw))
    (folder / f"SH2Perf_{stamp}_threads.csv").write_text("t_s,tid,cpu_pct,is_render_thread\n0.5,1,90.0,1\n")
    if samples:
        (folder / f"SH2Perf_{stamp}_samples.csv").write_text(
            "marker,module,rva,count\n0,Stronghold2.exe,0x00000000,60\n0,nvwgf2um.dll,0x00000000,30\n0,ntdll.dll,0x00000000,10\n")


def make_recording(folder, stamp, capture_id=None, modes=None, speed=None, speed_origin="planned", paused=None,
                   status="finalized", frames=20, software=None, quality=None, prepared=None, plan=None,
                   minimal=False, manifest_extra=None, csv_bytes=None, samples=False, single_phase=False, granny=False):
    """Write a hub recording with a manifest the way the hub does. Returns (manifest dict, stem)."""
    modes = modes or FULL
    stem = f"SH2Perf_{stamp}"
    capture_id = capture_id or f"rec-{stamp.replace('_', 'T')}Z-{sha(stamp.encode())[:8]}"
    csv = csv_bytes if csv_bytes is not None else frames_csv(frames, counters=modes["counters"], overlay=modes["overlay"], poll=modes["poll"], single_phase=single_phase)
    files = [("frames", f"{stem}_frames.csv", csv)]
    if modes["poll"]:
        files.append(("threads", f"{stem}_threads.csv", b"t_s,tid,cpu_pct,is_render_thread\n0.5,1,90.0,1\n"))
    if samples:
        files.append(("samples", f"{stem}_samples.csv", b"marker,module,rva,count\n0,Stronghold2.exe,0x00000000,60\n0,nvwgf2um.dll,0x00000000,30\n"))
    if granny:      # EXP-008 observer files (content shape only)
        files.append(("granny_meta", f"{stem}_granny.json", b'{"schema": "sh2perf.granny-observer", "version": 1}\n'))
        files.append(("granny_frames", f"{stem}_granny_frames.csv", b"frame,marker,partial\n0,0,1\n"))
        files.append(("granny_instances", f"{stem}_granny_instances.csv", b"instance,marker_slot\n0x00001000,0\n"))
        files.append(("granny_deformers", f"{stem}_granny_deformers.csv", b"deformer,marker_slot\n0x00002000,0\n"))
    if prepared is not None:
        files.append(("prepared", f"{stem}_prepared.json", json.dumps(prepared).encode()))
    for _, name, data in files:
        (folder / name).write_bytes(data)
    done = status == "finalized"
    m = {
        "schema": "sh2perf.capture-manifest", "manifest_version": 1, "capture_id": capture_id, "status": status,
        "recording": {"stem": stem, "start_utc": f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}T{stamp[9:11]}:{stamp[11:13]}:{stamp[13:15]}Z",
                      "start_local": f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}T{stamp[9:11]}:{stamp[11:13]}:{stamp[13:15]}",
                      "stop_utc": "2026-10-15T10:00:30Z" if done else None, "stop_reason": "user_toggle" if done else None,
                      "frames_written": frames, "markers": 0},
        "files": [{"role": r, "name": n, "size": len(d) if done else None, "sha256": sha(d) if done else None} for r, n, d in files],
    }
    if not minimal:
        m["plan"] = {"origin": "planned", **(plan or {})}
        m["game"] = {
            "game_speed": {"value": speed, "origin": speed_origin if speed is not None else "unknown", "meaning": "unspecified"},
            "paused": {"value": paused, "origin": "planned" if paused is not None else "unknown"},
            "observation": "none: the hub reads no game memory for speed or pause"}
        m["software"] = {"basis": "hub_session_start", "hash_algorithm": "sha256", "pending": False,
                         "hub": {"commit": "abc123def456", "dirty": False}, "files": software or software_files()}
        m["switches"] = {k: {"value": v, "source": "ini"} for k, v in modes.items()}
        m["switches"]["sample"] = {"value": "off", "source": "default"}
        m["technical_quality"] = quality or ({"capture_ok": True, "frames_dropped": 0, "frames_lost_write": 0, "write_errors": 0,
                                              "files_closed": True, "hashes_complete": True} if done else
                                             {"capture_ok": None, "frames_dropped": 0, "frames_lost_write": 0, "write_errors": 0,
                                              "files_closed": False, "hashes_complete": False})
        m["benchmark_suitability"] = {"verdict": "unknown", "assessed_by": None}
    m.update(manifest_extra or {})
    (folder / f"{stem}_manifest.json").write_text(json.dumps(m, indent=1))
    return m, stem


def reference_recording(folder, stamp, **kw):
    """A recording that satisfies the reference profile (docs/FORMATS/CAPTURE_MANIFEST.md): one phase, speed, pause,
    labels, variant, switches and software identity all stated."""
    args = dict(speed=90, paused=False, single_phase=True, plan={"experiment": "EXP-REF", "scenario": "REF"},
                prepared=prepared_record())
    args.update(kw)
    return make_recording(folder, stamp, **args)


def prepared_record(variant="baseline", software=None):
    return {"schema": "sh2perf.prepared-start", "version": 1, "prepared_utc": "2026-10-15T09:00:00Z", "variant": variant,
            "files": software or software_files(), "plan": {}}


def run_ingest(args, src, root, game_dir=None):
    """Run ingest.py as a subprocess against a temp layout; returns CompletedProcess."""
    env = dict(os.environ, SH2PERF_NO_HARDWARE="1")
    cmd = [sys.executable, "-I", str(TOOLS / "ingest.py"), *args, "--src", str(src), "--captures", str(root / "captures"),
           "--index", str(root / "data" / "index.jsonl")]
    if args and args[0] in ("import",) or (args and args[0].startswith("-")):
        cmd += ["--game-dir", str(game_dir or root / "game")]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)


def tree_hashes(folder):
    """{relative path: sha256} of every file below a folder (to prove nothing changed)."""
    folder = Path(folder)
    return {str(p.relative_to(folder)): sha(p.read_bytes()) for p in sorted(folder.rglob("*")) if p.is_file()}


class Layout:
    """src (hub out), captures, data, game folders inside one temp dir."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.src = self.root / "out"
        self.src.mkdir()
        self.game = make_game_dir(self.root / "game")
        self.captures = self.root / "captures"
        self.index = self.root / "data" / "index.jsonl"

    def cleanup(self):
        self.tmp.cleanup()

    def index_lines(self):
        return [json.loads(line) for line in self.index.read_text().splitlines()] if self.index.exists() else []

    def summary(self, capture_id):
        return json.loads((self.root / "data" / "silver" / capture_id / "summary.json").read_text())

    def run(self, *args):
        return run_ingest(list(args), self.src, self.root, self.game)
