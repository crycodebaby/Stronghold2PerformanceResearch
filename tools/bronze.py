"""Safe import of hub recordings into bronze (`captures/`), D012. Library; the CLI is `ingest.py`.

Three phases, in this order:
  1. verify   read-only on the source: manifest valid and finalized, every listed file present with the
              listed size and full SHA-256. Nothing is written.
  2. stage    copy the files into `captures/.staging/<capture_id>/`, hash the copies again, write
              `manifest.json` (byte-identical copy of the hub manifest) and `import.json`.
  3. commit   one atomic directory rename `.staging/<id>` -> `<id>`. Only then does the capture exist.

Guarantees:
  - Source files are never deleted, moved or changed. Existing bronze folders are never changed.
  - Importing the same recording again changes nothing ("already imported"); a repair of missing
    derived data is the caller's job (ingest.py does it after this returns).
  - The same capture id with different content is a CONFLICT: nothing is written.
  - A crash before the rename leaves only a `.staging` folder (copies only). The next import of the same id
    deletes it and starts over. A crash after the rename leaves a complete bronze folder.
  - Write errors (disk full, access denied) abort the import, remove the staging folder and leave the
    source untouched.
  - Every cleanup goes through `safe_rmtree`, which refuses anything that is not a direct, non-link child of the staging
    area. Names and roles in the manifest are validated (capture_manifest.parse) before the first write.
  - A committed capture is verified against its import record (`verify_committed`) before it is reported as "already
    imported" or used for silver; a damaged one is reported and never repaired.
  - Callers serialise writers with `filelock.exclusive` (ingest.py); under that lock a staging folder found for the
    own id is by definition left behind by a dead process.
A recording without a manifest (legacy) is imported only with `legacy=True`; its capture id is `legacy-<stem>`,
its hashes are taken at import time (basis "import") and it is never treated as verified.
"""
import datetime
import json
import os
import re
import shutil
from pathlib import Path

import capture_manifest as cm

TOOL = {"name": "sh2perf-import", "version": "2.0.0"}
IMPORT_SCHEMA = "sh2perf.import-record"
STAGING = ".staging"
MANIFEST_COPY = "manifest.json"
IMPORT_RECORD = "import.json"

# Exit codes of ingest.py (also used by tests).
EXIT_OK, EXIT_SELECT, EXIT_CONFLICT, EXIT_VERIFY, EXIT_REFUSED, EXIT_WRITE, EXIT_BUSY = 0, 2, 3, 4, 5, 6, 7


class ImportFailure(Exception):
    def __init__(self, code, message, details=()):
        super().__init__(message)
        self.code, self.message, self.details = code, message, list(details)


class UnsafePath(Exception):
    """A cleanup target outside the area it may touch."""


def safe_rmtree(path, root):
    """Delete `path` only if it is a direct child of `root` and neither a symlink nor a junction (never followed)."""
    p, r = os.path.abspath(path), os.path.abspath(root)
    if os.path.normcase(os.path.dirname(p)) != os.path.normcase(r) or os.path.normcase(p) == os.path.normcase(r):
        raise UnsafePath(f"{p} is not a direct child of {r}")
    if os.path.islink(p) or os.path.isjunction(p):
        raise UnsafePath(f"{p} is a link; links are not followed")
    if os.path.islink(r) or os.path.isjunction(r):
        raise UnsafePath(f"{r} is a link")
    if os.path.normcase(os.path.realpath(os.path.dirname(p))) != os.path.normcase(os.path.realpath(r)):
        raise UnsafePath(f"{p} resolves outside {r}")
    shutil.rmtree(p, ignore_errors=False)


class Recording:
    """One recording in the hub output folder, identified by its stem (SH2Perf_<date>_<time>)."""

    def __init__(self, src, stem):
        self.src, self.stem = Path(src), stem

    @property
    def manifest_path(self):
        return self.src / f"{self.stem}_manifest.json"

    @property
    def frames_path(self):
        return self.src / f"{self.stem}_frames.csv"

    @property
    def timestamp(self):
        return self.stem[len("SH2Perf_"):]


# A hub stem is SH2Perf_<YYYYMMDD>_<HHMMSS>; other files of a recording only add a suffix to it
# (e.g. SH2Perf_<ts>_granny_frames.csv must not look like a recording "<ts>_granny").
STEM_RE = re.compile(r"^SH2Perf_\d{8}_\d{6}$")


def find_recordings(src):
    stems = set()
    for pattern, tail in (("SH2Perf_*_frames.csv", "_frames.csv"), ("SH2Perf_*_manifest.json", "_manifest.json")):
        for p in Path(src).glob(pattern):
            stem = p.name[:-len(tail)]
            if STEM_RE.match(stem):
                stems.add(stem)
    return [Recording(src, s) for s in sorted(stems)]


def describe(rec):
    """One line per recording for the selection list: kind, frames, size."""
    kind, n = "legacy (no manifest)", 0
    if rec.manifest_path.exists():
        try:
            m, _ = cm.load(rec.manifest_path)
            kind = f"manifest {cm.completion(m)}  {m['capture_id']}"
        except cm.ManifestError:
            kind = "manifest INVALID"
    size = 0
    if rec.frames_path.exists():
        with open(rec.frames_path, "rb") as f:
            n = max(0, sum(1 for _ in f) - 1)
        size = rec.frames_path.stat().st_size
    return f"{rec.timestamp}  {n} frames  {size // 1024} KiB  {kind}"


def select(src, wanted):
    """The single recording to import, or ImportFailure(EXIT_SELECT) listing the choices. Touches nothing."""
    recs = find_recordings(src)
    if not recs:
        raise ImportFailure(EXIT_SELECT, f"no recording in {src} - record with F9 (start) and F9 (stop) first")
    if wanted:
        for r in recs:
            if wanted in (r.stem, r.timestamp):
                return r
        raise ImportFailure(EXIT_SELECT, f"recording {wanted} not found", [describe(r) for r in recs])
    if len(recs) == 1:
        return recs[0]
    raise ImportFailure(EXIT_SELECT, f"{len(recs)} recordings; nothing was touched. Rerun with --recording <timestamp>:",
                        [describe(r) for r in recs])


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


# --- phase 1: verify (read-only) -------------------------------------------------------------------------

def plan(rec, legacy=False, allow_interrupted=False):
    """Describe what would be imported and verify the source. Raises ImportFailure; never writes."""
    if rec.manifest_path.exists():
        try:
            manifest, raw = cm.load(rec.manifest_path)
        except cm.ManifestError as e:
            raise ImportFailure(EXIT_VERIFY, f"manifest of {rec.stem} cannot be used", e.problems)
        completion = cm.completion(manifest)
        if completion == "interrupted" and not allow_interrupted:
            raise ImportFailure(
                EXIT_REFUSED,
                f"{rec.stem} is not finalized: the manifest still says 'recording' (the game may still be running, "
                "or the recording was interrupted). Close the game first; to keep an interrupted recording as it is, "
                "rerun with --allow-interrupted.")
        files = []
        for f in manifest["files"]:
            files.append({"name": f["name"], "role": f.get("role"), "size": f.get("size"),
                          "expected_sha256": f.get("sha256") if completion == "finalized" else None})
        return {"kind": "manifest", "capture_id": manifest["capture_id"], "completion": completion,
                "manifest": manifest, "manifest_raw": raw, "files": files}
    if not legacy:
        raise ImportFailure(
            EXIT_REFUSED,
            f"{rec.stem} has no manifest (recorded by a hub before D012, or incomplete). Its origin cannot be verified. "
            "To keep it as an unverified legacy capture, rerun with --legacy.")
    files = [{"name": rec.frames_path.name, "role": "frames", "size": None, "expected_sha256": None}]
    for role, suffix in (("threads", "_threads.csv"), ("samples", "_samples.csv")):
        p = rec.src / f"{rec.stem}{suffix}"
        if p.exists():
            files.append({"name": p.name, "role": role, "size": None, "expected_sha256": None})
    return {"kind": "legacy", "capture_id": f"legacy-{rec.stem}", "completion": "legacy",
            "manifest": None, "manifest_raw": None, "files": files}


def verify_source(rec, p):
    """Hash the source files and compare with the manifest. Returns {name: (size, sha256)}; raises on any difference."""
    problems, actual = [], {}
    for f in p["files"]:
        path = rec.src / f["name"]
        if not path.is_file():
            problems.append(f"{f['name']}: missing")
            continue
        size = path.stat().st_size
        sha = cm.sha256_file(path)
        actual[f["name"]] = (size, sha)
        if f["size"] is not None and p["completion"] == "finalized" and size != f["size"]:
            problems.append(f"{f['name']}: size {size} != manifest {f['size']} (incomplete or truncated file)")
        elif f["expected_sha256"] and sha != f["expected_sha256"]:
            problems.append(f"{f['name']}: sha256 {sha[:16]}... != manifest {f['expected_sha256'][:16]}... (hash conflict)")
    if problems:
        raise ImportFailure(EXIT_VERIFY, f"{rec.stem}: source does not match its manifest; nothing was imported", problems)
    return actual


# --- identity of an existing bronze folder ---------------------------------------------------------------

def identity_of(import_record):
    """What makes two imports 'the same recording': manifest hash and the raw file hashes."""
    return {"manifest_sha256": (import_record.get("manifest") or {}).get("sha256"),
            "files": {f["name"]: f["sha256"] for f in import_record.get("files", [])}}


def committed_record(dest):
    return _read_json(Path(dest) / IMPORT_RECORD)


def verify_committed(dest):
    """Check a committed capture folder against its import record. Returns (problems, verifiable).

    One check for `verify`, a repeated import and every (re)derivation of silver. Folders from before D012 have no
    import record: nothing to compare with (verifiable False). Never changes anything.
    """
    dest = Path(dest)
    imp = committed_record(dest)
    if imp is None:
        return ([] if not (dest / IMPORT_RECORD).exists() else [f"{IMPORT_RECORD} unreadable"]), False
    problems = []
    for f in imp.get("files", []):
        path = dest / f["name"]
        if not path.is_file():
            problems.append(f"{f['name']}: missing")
        elif path.stat().st_size != f["size"]:
            problems.append(f"{f['name']}: size {path.stat().st_size} != recorded {f['size']} (raw data changed)")
        elif cm.sha256_file(path) != f["sha256"]:
            problems.append(f"{f['name']}: sha256 differs from the import record (raw data changed)")
    m = imp.get("manifest")
    if m:
        path = dest / m["name"]
        if not path.is_file():
            problems.append(f"{m['name']}: missing")
        elif cm.sha256_file(path) != m["sha256"]:
            problems.append(f"{m['name']}: sha256 differs from the import record (raw data changed)")
    return problems, True


def require_intact(dest):
    """Raise ImportFailure(EXIT_VERIFY) naming the damage if a committed capture no longer matches its import record."""
    problems, _ = verify_committed(dest)
    if problems:
        raise ImportFailure(
            EXIT_VERIFY,
            f"capture {Path(dest).name} is damaged: its raw data no longer matches the import record. Nothing was derived and "
            "bronze is not repaired automatically; restore the files (the sources in the hub output folder are still there) "
            "or import under a new id.", problems)


# --- phases 2 and 3 --------------------------------------------------------------------------------------

def _copy_synced(src, dst):
    shutil.copyfile(src, dst)
    with open(dst, "rb+") as f:
        os.fsync(f.fileno())


def _write_synced(path, data):
    with open(path, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def import_recording(rec, bronze_root, legacy=False, allow_interrupted=False, observed=None, inject=None):
    """Import one recording. Returns {'state': 'imported'|'already_imported', 'capture_id', 'dest'}.

    `observed` is a callable(plan) -> dict stored as `observed_at_import` (hardware, hashes of the game folder now).
    These are observations made at import time and never provenance. `inject(point, **ctx)` is a test hook that
    may raise to simulate crashes and write errors at named points ("copy", "before_commit", "after_commit").
    """
    inject = inject or (lambda point, **ctx: None)
    p = plan(rec, legacy, allow_interrupted)
    actual = verify_source(rec, p)
    capture_id = p["capture_id"]
    bronze_root = Path(bronze_root)
    dest = bronze_root / capture_id

    new_identity = {"manifest_sha256": cm.sha256_bytes(p["manifest_raw"]) if p["manifest_raw"] else None,
                    "files": {n: sha for n, (_, sha) in actual.items()}}
    if dest.exists():
        return _existing(dest, new_identity, capture_id)

    stage_root = bronze_root / STAGING
    stage = stage_root / capture_id
    try:
        if stage.exists():                         # leftover of a dead import (callers hold the write lock): copies only
            safe_rmtree(stage, stage_root)
        stage.mkdir(parents=True)
        for f in p["files"]:
            inject("copy", name=f["name"])
            _copy_synced(rec.src / f["name"], stage / f["name"])
            size, sha = actual[f["name"]]
            if cm.sha256_file(stage / f["name"]) != sha or (stage / f["name"]).stat().st_size != size:
                raise ImportFailure(EXIT_VERIFY, f"{f['name']}: copy differs from the source (source changed during the import?)")
        aux = []
        log = rec.src / "Stronghold2AnalyseHub.log"
        if log.is_file():                          # shared by all recordings of a session, still growing: not part of the identity
            try:
                _copy_synced(log, stage / log.name)
                aux.append({"name": log.name, "sha256_at_import": cm.sha256_file(stage / log.name)})
            except OSError:
                pass
        if p["kind"] == "legacy":
            latest = _read_json(rec.src / "latest.json")
            if isinstance(latest, dict) and latest.get("frames_csv") == rec.frames_path.name:
                _write_synced(stage / "latest.json", (rec.src / "latest.json").read_bytes())
                aux.append({"name": "latest.json", "sha256_at_import": cm.sha256_file(stage / "latest.json"),
                            "note": "pointer written by an older hub; metadata only, not identity"})
        manifest_info = None
        if p["manifest_raw"] is not None:
            _write_synced(stage / MANIFEST_COPY, p["manifest_raw"])
            manifest_info = {"name": MANIFEST_COPY, "source_name": rec.manifest_path.name,
                             "sha256": new_identity["manifest_sha256"], "manifest_version": p["manifest"]["manifest_version"]}
        flags = []
        if p["kind"] == "legacy":
            flags.append("legacy_unverified")
        if p["completion"] == "interrupted":
            flags.append("interrupted")
        record = {
            "schema": IMPORT_SCHEMA, "version": 1, "state": "committed", "tool": TOOL,
            "capture_id": capture_id, "kind": p["kind"], "completion": p["completion"],
            "imported_utc": _utc_now(), "source_stem": rec.stem,
            "manifest": manifest_info,
            "files": [{"name": f["name"], "role": f["role"], "size": actual[f["name"]][0], "sha256": actual[f["name"]][1],
                       "sha256_basis": "manifest" if f["expected_sha256"] else "import"} for f in p["files"]],
            "aux": aux,
            "verification": {"against_manifest": p["kind"] == "manifest" and p["completion"] == "finalized",
                             "copies_rehashed": True},
            "observed_at_import": observed(p) if observed else {},
            "flags": flags,
        }
        record["flags"] += record["observed_at_import"].get("flags", [])
        _write_synced(stage / IMPORT_RECORD, (json.dumps(record, indent=2) + "\n").encode("utf-8"))
        inject("before_commit")
        try:
            os.rename(stage, dest)                 # the commit: atomic, fails if the id appeared meanwhile
        except FileExistsError:
            _cleanup(stage, stage_root)
            return _existing(dest, new_identity, capture_id)
        inject("after_commit")
    except ImportFailure:
        _cleanup(stage, stage_root)
        raise
    except OSError as e:
        _cleanup(stage, stage_root)
        raise ImportFailure(EXIT_WRITE, f"write error while importing {capture_id}: {e}; the source is untouched and "
                                        "nothing was committed")
    return {"state": "imported", "capture_id": capture_id, "dest": dest}


def _cleanup(stage, stage_root):
    try:
        if os.path.lexists(stage):
            safe_rmtree(stage, stage_root)
    except (UnsafePath, OSError):
        pass                                       # never escalate a failed cleanup; a stale staging folder is harmless


def _existing(dest, new_identity, capture_id):
    require_intact(dest)                           # "already imported" is only true for an intact capture
    old = committed_record(dest)
    if old is None:
        raise ImportFailure(EXIT_CONFLICT, f"{dest.name} exists but has no import record; it is not touched")
    if identity_of(old) == new_identity:
        return {"state": "already_imported", "capture_id": capture_id, "dest": dest}
    diff = []
    if identity_of(old)["manifest_sha256"] != new_identity["manifest_sha256"]:
        diff.append("manifest differs")
    for name in sorted(set(identity_of(old)["files"]) | set(new_identity["files"])):
        if identity_of(old)["files"].get(name) != new_identity["files"].get(name):
            diff.append(f"{name} differs")
    raise ImportFailure(EXIT_CONFLICT, f"capture id {capture_id} already exists with different content; nothing was changed", diff)
