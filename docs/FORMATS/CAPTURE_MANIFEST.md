# Capture manifest, provenance and import

> Kurzfassung: Vertrag pro Aufnahme (D012): `<stem>_manifest.json` (manifest_version 1) mit Aufnahme-ID, Plan, Spielgeschwindigkeit/Pause mit Herkunft, Softwareidentität (volle SHA-256, in der Sitzung gemessen), wirksamen Schaltern und Dateiliste mit Hashes; Abschlussstatus erst nach dem Schließen der Dateien. Dazu der sichere Import (prüfen → Staging → atomare Freigabe), Kompatibilitätsregeln und die Silber-Ableitung.

One recording = one manifest. `latest.json` is only a pointer to the newest one and never identifies a recording (D012). Written by the hub's capture thread (never the render thread); CSV columns are described in [HUB_CAPTURE.md](HUB_CAPTURE.md).

## Files of one recording (hub output dir)
`<stem>_frames.csv`, `<stem>_threads.csv` (`poll`), `<stem>_samples.csv` (sampler), `<stem>_prepared.json` (copy of `SH2Prepared.json` if present), `<stem>_manifest.json`. `<stem>` = `SH2Perf_<YYYYMMDD>_<HHMMSS>`, local start time. The hub log is shared by a whole session and has no integrity guarantee (`session_log`).

## Manifest (`schema: sh2perf.capture-manifest`, `manifest_version: 1`)
| Key | Content |
|---|---|
| `capture_id` | `rec-<UTC start>-<8 random hex>`, unique per recording, also the bronze folder name |
| `status` | `recording` (written before the first frame) → `finalized` (written after all files are closed and hashed). A manifest that stays at `recording` is an interrupted recording |
| `session` | `session_id` (`ses-…`, one per game process), `pid` |
| `recording` | `stem`, `start_utc`/`stop_utc`, `start_local`/`stop_local`, `stop_reason` (`user_toggle` \| `hub_shutdown`), `frames_written`, `markers`; stop fields are `null` until finalized |
| `plan` | `experiment`, `protocol`, `scenario` from `SH2Proxy.ini [plan]` (origin always `planned`), `source_ini_sha256`; `null` = unknown |
| `game.game_speed` | `{value, origin, meaning}`: `value` is a number or `null`; `origin` is `planned` \| `user_confirmed` \| `observed` \| `unknown`; `meaning` is always `unspecified` (no unit, no valid range assumed). A text that is not a finite number is not stored as a value (`rejected_text`) |
| `game.paused` | `{value: true/false/null, origin}`, independent of the speed |
| `software` | identity measured by the hub **when it was loaded into this game session** (`basis: hub_session_start`): `files[]` with `role`, `name` (no paths), `size`, full 64-digit `sha256` for `game_exe`, `hub_dll`, `d3d9_in_game_dir`, `d3d9_dxvk` (if present), `config_ini`; `hub.commit` + `hub.dirty` (uncommitted build); `pending: true` if hashing was not finished when the recording started (then `files` may be empty = unknown) |
| `switches` | effective `profile`, `frametime`, `counters`, `poll`, `overlay`, `beep` (`value`, `source` = `env` \| `ini` \| `profile` \| `default` \| `derived` \| `forced`) and `sample` (`off` \| `module` \| `function`) |
| `files[]` | `role` (`frames` \| `threads` \| `samples` \| `prepared`), `name`, `size`, `sha256` (`null` until finalized) |
| `technical_quality` | facts about the files: `capture_ok` (`null` while recording), `frames_dropped`, `frames_lost_write`, `write_errors`, `files_closed`, `hashes_complete` |
| `benchmark_suitability` | always `{verdict: unknown, assessed_by: null}` from the hub: the hub does not judge (see below) |

`SH2Prepared.json` (written by `variant.py` at every change of the TEST folder, `schema: sh2perf.prepared-start`) carries the *prepared* state: variant, LAA/DXVK, the same hash list taken when the folder was prepared, and the plan. The importer compares it with the session identity (`software_differs_from_prepared`).

## Who supplies what
| Information | Origin | Automatic? |
|---|---|---|
| Frame times, counters, thread CPU, VA | hub measurement (CSV) | yes |
| `capture_id`, `session_id`, times, `stop_reason`, effective switches + source, file sizes/hashes, capture health | hub, at recording | yes |
| Software hashes (exe, hub DLL, d3d9 files, ini), hub commit/dirty | hub, hashed at hub load of this session (background thread) | yes |
| Variant, LAA, DXVK, hashes at *prepared* start | `variant.py` → `SH2Prepared.json` | yes (tool), not from the game |
| experiment / protocol / scenario / game_speed / paused as `planned` | typed by the user via `variant.py plan …` before the run | **no – declared plan**, not a measurement |
| game_speed / paused as `user_confirmed` | user via `ingest.py annotate … --game-speed N --paused true\|false` after looking at the game | **only user-confirmed**, stored in `data/annotations/`, never in the raw manifest |
| game_speed / paused as `observed` | **not produced**: the hub reads no game memory (no verified address); the reader accepts the origin for a future hub | no |
| benchmark suitability | user via `annotate --suitability …` | **only user judgement** |
| Hashes of the game folder at import time, CPU/GPU names | importer, `import.json` → `observed_at_import` | yes, but an *import-time observation*, never provenance |

## Technical quality is not benchmark suitability
`technical status` (silver): `ok` (finalized, `capture_ok`, files closed, all hashes) \| `degraded` (finalized with drops/write errors/missing hashes) \| `incomplete` (interrupted) \| `unknown` (no health information, e.g. legacy). Suitability is a separate verdict (`unknown` default; `suitable`/`not_suitable` only by the user). `blockers` (technical status not ok, interrupted, legacy origin) make `usable_as_benchmark` false even if the user says `suitable`; `missing_info` (speed, pause, switches, software identity, variant unknown) is listed but does not block.

## Compatibility rules
1. `manifest_version` is an integer. A reader refuses a higher version than it knows; it reads lower or equal ones. Unknown keys inside a known version are ignored. A key never changes meaning inside a version; new meaning = new version + reader change in the same step.
2. Hub `capture_version 3` = manifest present; `latest.json` keeps its older keys and adds `capture_id`, `manifest`, `manifest_sha256` (`null` if the manifest could not be written). Frames/threads/samples CSV columns are unchanged.
3. **Legacy** (no manifest, `capture_version` ≤ 2): imported only with `--legacy`; id `legacy-<stem>`; hashes taken at import time (`sha256_basis: import`); technical status `unknown`; switches known only if a `latest.json` of version 2 names this recording (then `basis` says so), otherwise unknown – never "all on"; blocker `legacy_unverified_origin`. Existing folders `captures/<date>_<exp>_…/` are read as legacy and never changed or moved.
4. Missing keys are unknown: no manifest field is defaulted to a "good" value. A manifest with only the required keys imports and shows everything else as unknown.
5. A `status: recording` manifest imports only with `--allow-interrupted`; its hashes are then import-time hashes and the capture is `incomplete`.

## Import (`tools/ingest.py`, library `bronze.py`)
1. **verify** (read-only): manifest valid and `finalized`; every listed file present, size and SHA-256 equal. A cut-off file or a changed byte stops here (exit 4).
2. **stage**: copy to `captures/.staging/<capture_id>/`, re-hash the copies, write `manifest.json` (byte-identical copy) and `import.json` (tool version, file hashes, `observed_at_import`, flags). A stale staging folder of the same id (earlier crash) is discarded first: it holds copies only.
3. **commit**: one atomic rename to `captures/<capture_id>/`. The capture exists only after this. Then silver is derived (`data/silver/<id>/`, `data/index.jsonl`).
- Same recording again → `already imported`, bronze unchanged, silver re-derived (this also repairs a crash after the rename). Same id, different content → conflict (exit 3), nothing written. A foreign folder with the id is never touched.
- Sources are **never** deleted or moved (the old behaviour is gone). Existing bronze folders are never changed.
- Exit codes: 0 ok/already imported · 2 choose a recording (several found; nothing touched) · 3 conflict · 4 verification failed · 5 refused (interrupted, legacy without flag) · 6 write error (staging removed, source untouched).

## Silver and reproducibility
`silver.py` derives `summary.json`, `timeline.md` and the index line from bronze + `data/annotations/<id>.json` only (no clock, no TEST folder); the summary names its tool (`sh2perf-silver <version>`). `ingest.py rebuild` re-derives every capture; `rebuild --write` replaces the index lines and `data/silver/`. `ingest.py verify <id>` re-hashes bronze against `import.json`. Change `silver.TOOL["version"]` whenever the derivation changes.
Game speed in silver keeps `planned`, `user_confirmed`, `observed` apart (`by_origin`) and adds `resolved`: strongest origin wins (observed > user_confirmed > planned); observed vs. user-confirmed disagreement is a `conflict` (value `null`); a planned value overridden by a stronger one sets `planned_differs`. `ab_compare.py` shows the speed per capture and warns on differing or unknown speeds.

## Not covered / open
- Whether the hub's new files behave in Stronghold 2 itself (only stand-in and unit tests so far) → STATE.md.
- Reading speed/pause from the game would need a verified address (analysis task, D005); until then `observed` stays unused.
- A hard kill during `MoveFileEx` at the final manifest: the previous `recording` manifest stays (interrupted), never a half-written file (temp + rename).
