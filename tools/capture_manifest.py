"""Data contract of one hub recording: the per-recording manifest (docs/FORMATS/CAPTURE_MANIFEST.md, D012).

Library only (no CLI): load and check a manifest, interpret its status, compare software identities.
Stdlib only. Everything here is read-only; nothing guesses a missing value - absent information is None/"unknown".

Compatibility rules (also in the format doc):
  - `manifest_version` is an integer. This reader knows SUPPORTED_VERSION. A higher number is refused
    (a newer hub may mean something this reader does not know); a lower or equal number is read.
  - Within one version, readers must ignore unknown keys; the hub only adds keys without bumping the version.
  - A key's meaning never changes inside a version.
"""
import hashlib
import json
import re
import unicodedata

SCHEMA = "sh2perf.capture-manifest"
SUPPORTED_VERSION = 1
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ORIGINS = ("planned", "user_confirmed", "observed", "unknown")     # allowed `origin` of game_speed / paused
STATUSES = ("recording", "finalized")
KNOWN_ROLES = ("frames", "threads", "samples", "prepared",
               "granny_meta", "granny_frames", "granny_instances", "granny_deformers")   # granny_*: EXP-008 observer      # a regular recording has exactly one frames file, each role at most once
# Names the importer writes itself next to the raw files; a manifest must not claim them as data files.
RESERVED_ADMIN_NAMES = ("manifest.json", "import.json", "latest.json", "stronghold2analysehub.log")
_DEVICE_NAMES = {"con", "prn", "aux", "nul", "conin$", "conout$", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
_BAD_CHARS = set('<>:"/\\|?*')
MAX_NAME = 200


def _fold(name):
    """Key under which Windows treats two names as the same file: compatibility-normalised and case-folded."""
    return unicodedata.normalize("NFKC", name).casefold()


def name_problem(name, reserved_ok=False):
    """Why `name` is not an acceptable plain file name on Windows (None if it is). Covers absolute paths, drive letters,
    alternative data streams (all contain ':' or a separator), device names, trailing dots/spaces, control characters."""
    if not isinstance(name, str) or not name:
        return "empty or not text"
    if len(name) > MAX_NAME:
        return f"longer than {MAX_NAME} characters"
    if any(ord(ch) < 32 or ch in _BAD_CHARS for ch in name):
        return "contains a path separator, drive or stream marker, wildcard or control character"
    if name in (".", "..") or name.startswith(".") or name.endswith((" ", ".")):
        return "starts with a dot or ends with a dot or space"
    stem = _fold(name).split(".")[0].rstrip(" ")
    if stem in _DEVICE_NAMES:
        return "is a reserved Windows device name"
    if not reserved_ok and _fold(name) in RESERVED_ADMIN_NAMES:
        return "is reserved for the importer"
    return None


def id_problem(cid):
    if not isinstance(cid, str) or not re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]*$", cid):
        return "has characters that are not safe in a folder name"
    if len(cid) > 100 or cid.endswith((".", " ")):
        return "is too long or ends with a dot"
    if _fold(cid).split(".")[0] in _DEVICE_NAMES:
        return "is a reserved Windows device name"
    return None


class ManifestError(Exception):
    """The manifest cannot be trusted or read; `problems` lists why."""

    def __init__(self, problems):
        super().__init__("; ".join(problems))
        self.problems = problems


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def parse(raw):
    """Parse manifest bytes and check the structure; returns the dict. Raises ManifestError."""
    try:
        m = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        raise ManifestError([f"not valid JSON: {e}"])
    problems = []
    if not isinstance(m, dict) or m.get("schema") != SCHEMA:
        raise ManifestError([f"schema is not {SCHEMA!r}"])
    version = m.get("manifest_version")
    if not isinstance(version, int) or isinstance(version, bool):
        problems.append("manifest_version missing or not an integer")
    elif version > SUPPORTED_VERSION:
        problems.append(f"manifest_version {version} is newer than this reader ({SUPPORTED_VERSION})")
    if not isinstance(m.get("capture_id"), str) or not m.get("capture_id"):
        problems.append("capture_id missing")
    elif id_problem(m["capture_id"]):
        problems.append(f"capture_id {m['capture_id'][:40]!r} {id_problem(m['capture_id'])}")
    if m.get("status") not in STATUSES:
        problems.append(f"status {m.get('status')!r} is not one of {STATUSES}")
    files = m.get("files")
    if not isinstance(files, list) or not files:
        problems.append("files missing or empty")
    else:
        seen, roles = {}, {}
        for f in files:
            name = f.get("name") if isinstance(f, dict) else None
            why = name_problem(name)
            if why:
                problems.append(f"file name {str(name)[:40]!r} is not a valid file name: {why}")
                continue
            key = _fold(name)
            if key in seen:
                problems.append(f"duplicate file name {name!r} (the same file on Windows as {seen[key]!r})")
            seen[key] = name
            role = f.get("role")
            if role not in KNOWN_ROLES:
                problems.append(f"{name}: file role {role!r} is not one of {KNOWN_ROLES}")
            elif role in roles:
                problems.append(f"{name}: file role {role!r} used twice (also {roles[role]!r})")
            else:
                roles[role] = name
            if m.get("status") == "finalized":
                if not (isinstance(f.get("sha256"), str) and SHA256_RE.match(f["sha256"])):
                    problems.append(f"{name}: sha256 is not a full 64-digit lowercase hex value")
                if not isinstance(f.get("size"), int) or isinstance(f.get("size"), bool) or f["size"] < 0:
                    problems.append(f"{name}: size missing")
        if "frames" not in roles:
            problems.append("file role 'frames': exactly one frames file is required")
    game = m.get("game") if isinstance(m.get("game"), dict) else {}
    for key in ("game_speed", "paused"):
        item = game.get(key)
        if item is not None and (not isinstance(item, dict) or item.get("origin") not in ORIGINS):
            problems.append(f"game.{key}.origin is not one of {ORIGINS}")
        if isinstance(item, dict) and item.get("value") is not None:
            if key == "game_speed" and (isinstance(item["value"], bool) or not isinstance(item["value"], (int, float))):
                problems.append("game.game_speed.value is not a number")
            if key == "paused" and not isinstance(item["value"], bool):
                problems.append("game.paused.value is not true/false")
            if item.get("origin") == "unknown":
                problems.append(f"game.{key} has a value but origin 'unknown'")
    for role_file in (m.get("software") or {}).get("files", []) if isinstance(m.get("software"), dict) else []:
        sw_why = name_problem(role_file.get("name"), reserved_ok=True)
        if sw_why:
            problems.append(f"software file name {str(role_file.get('name'))[:40]!r} is not a valid file name: {sw_why}")
        sha = role_file.get("sha256")
        if sha is not None and not SHA256_RE.match(str(sha)):
            problems.append(f"software file {role_file.get('name')}: sha256 is not a full 64-digit value")
    if problems:
        raise ManifestError(problems)
    return m


def load(path):
    with open(path, "rb") as f:
        raw = f.read()
    return parse(raw), raw


def completion(m):
    """'finalized' (published after all files were closed) or 'interrupted' (stayed at 'recording')."""
    return "finalized" if m["status"] == "finalized" else "interrupted"


def technical_status(m):
    """Technical quality of the files, separate from any benchmark judgement: ok | degraded | incomplete | unknown."""
    if m["status"] != "finalized":
        return "incomplete"
    q = m.get("technical_quality") or {}
    if q.get("capture_ok") is True and q.get("files_closed") is True and q.get("hashes_complete") is True:
        return "ok"
    if q.get("capture_ok") is False or q.get("hashes_complete") is False:
        return "degraded"
    return "unknown"


def switches(m):
    """{'frametime': bool, ...} from the manifest's effective switches, or None if the manifest has none."""
    sw = m.get("switches")
    if not isinstance(sw, dict):
        return None
    out = {}
    for k in ("frametime", "counters", "poll", "overlay"):
        item = sw.get(k)
        out[k] = item.get("value") if isinstance(item, dict) and isinstance(item.get("value"), bool) else None
    sample = sw.get("sample")
    out["sample"] = sample.get("value") if isinstance(sample, dict) else None
    granny = sw.get("granny")      # hub builds before EXP-008 have no such switch: None (unknown), not False
    out["granny"] = granny.get("value") if isinstance(granny, dict) and isinstance(granny.get("value"), bool) else None
    return out


def software_by_name(m, comparable=False):
    """{file name: sha256} of the session identity (empty if the hub could not hash it).

    comparable=True leaves out the config file: it changes with every setting and is recorded as `switches`,
    so a later edit is not a software change.
    """
    sw = m.get("software") if isinstance(m.get("software"), dict) else {}
    return {f["name"]: f.get("sha256") for f in sw.get("files", [])
            if isinstance(f, dict) and f.get("name") and not (comparable and f.get("role") == "config_ini")}


def software_changes(recorded, current):
    """Compare recorded identity {name: sha256} with hashes taken now {name: sha256 or None for missing}.

    Returns {name: 'changed' | 'missing_now' | 'unverifiable'}. Hashes taken now are an observation made at
    import time and never become the provenance of the recording.
    """
    out = {}
    for name, sha in recorded.items():
        now = current.get(name)
        if not sha:
            out[name] = "unverifiable"
        elif now is None:
            out[name] = "missing_now"
        elif now != sha:
            out[name] = "changed"
    return out
