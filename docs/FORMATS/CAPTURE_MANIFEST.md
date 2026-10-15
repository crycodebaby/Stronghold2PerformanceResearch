# Capture manifest, provenance and import

> Kurzfassung: Vertrag pro Aufnahme (D012): `<stem>_manifest.json` (manifest_version 1) mit Aufnahme-ID, Plan, Spielgeschwindigkeit/Pause mit Herkunft, Softwareidentität (volle SHA-256, in der Sitzung gemessen), wirksamen Schaltern und Dateiliste mit Hashes; Abschlussstatus erst nach dem Schließen der Dateien. Dazu der sichere Import (prüfen → Staging → atomare Freigabe), Kompatibilitätsregeln und die Silber-Ableitung.

One recording = one manifest. `latest.json` is only a pointer to the newest one and never identifies a recording (D012). Written by the hub's capture thread (never the render thread); CSV columns are described in [HUB_CAPTURE.md](HUB_CAPTURE.md).

## Files of one recording (hub output dir)
`<stem>_frames.csv`, `<stem>_threads.csv` (`poll`), `<stem>_samples.csv` (sampler), `<stem>_prepared.json` (copy of `SH2Prepared.json` if present), `<stem>_granny.json` + `_granny_frames.csv` + `_granny_instances.csv` + `_granny_deformers.csv` (Granny observer, switch `granny`), `<stem>_manifest.json`. Importers match a recording only by the exact stem (`tools/bronze.py` `STEM_RE`). `<stem>` = `SH2Perf_<YYYYMMDD>_<HHMMSS>`, local start time. The hub log is shared by a whole session and has no integrity guarantee (`session_log`).

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
| `files[]` | `role` (`frames` \| `threads` \| `samples` \| `prepared` \| since EXP-008 `granny_meta` \| `granny_frames` \| `granny_instances` \| `granny_deformers`, [GRANNY_OBSERVER.md](GRANNY_OBSERVER.md)), `name`, `size`, `sha256` (`null` until finalized) |
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

## Integrity, description and release are judged apart (silver `quality.benchmark_suitability`)
- **integrity** (`status`): `ok` \| `degraded` (finalized with drops/write errors/missing hashes) \| `incomplete` (interrupted) \| `unknown` (no health information, e.g. legacy). Reasons: `technical_quality_<status>`, `interrupted`, `legacy_unverified_origin`, `no_usable_frames`.
- **description** (`completeness`, profile **`reference-v1`**, the only rule set): experiment, scenario and variant named; game speed known **and not contradicted** (`game_speed_unknown` / `game_speed_conflict`); all four hub switches known; hash of game exe and hub DLL from the session present; pause known **for every phase**. Nothing else is required; troops, note, protocol are optional.
- **release** (`verdict`): `unknown` (default) \| `suitable` \| `not_suitable`, set only by the user (`annotate --suitability`). A release is recorded as given and never overrules the other two.
- `usable_as_benchmark` is true only if integrity is ok, the description is complete and the user released it - i.e. "reference-v1 passed and released". Otherwise `rejections` lists every reason as `{code, text}` (also `not_released`, `released_unsuitable`). `blockers` = integrity reasons, `missing_info` = description gaps (kept for older readers).
- **Pause per phase**: a phase is an F8 marker range. A recording-level pause statement (planned or `annotate --paused`) counts as evidence only for a recording with **one** phase. With several phases it is shown as `recording_level` but each phase stays `unknown` until the user confirms it (`annotate --phase-paused <marker>=true|false`, repeatable); the hub never reads the pause from game memory. `game.paused.resolved` is `unknown` for a mixed recording.

### What `reference-v1` checks - and what it does not
Checks: integrity of the recording (finalized, no drops or write errors, hashes complete, raw data still matching the import record); that experiment, scenario, variant, a numeric game speed (not contradicted), the four hub switches, the session hashes of game exe and hub DLL and the pause state of every phase are **stated**; and that the user released it.
It does **not** check, and `usable as reference: yes` is **no evidence** of: the same save game or map, the same camera or scene, the same graphics settings, V-Sync or frame limiter, the same Steam-overlay state, the same hardware or driver, that a stated value is true (planned and user-confirmed values are statements), that two captures are comparable with each other, or that the run is representative. Those are the user's checklist before a comparison (EXPERIMENTS.md "Hub overhead A/B", step 2); no comparison rule engine exists.

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
- **Manifest names are validated before the first write** (`capture_manifest.parse`): file and capture-id names must be plain Windows file names (no path, drive, `:`/alternate data stream, wildcard, control character, trailing dot or space, device name such as `CON`/`NUL`/`COM1`, no leading dot, at most 200 characters); the importer's own names (`manifest.json`, `import.json`, `latest.json`, `Stronghold2AnalyseHub.log`) are reserved; names equal on Windows (case, Unicode normalisation) are duplicates; roles are `frames`/`threads`/`samples`/`prepared`/`granny_*` (four, EXP-008), each at most once, **exactly one `frames`**. A failing manifest exits 4 with nothing written; every cleanup goes through `safe_rmtree`, which only deletes a direct, non-link child of `captures/.staging/`.
- **Bronze is verified before it is used**: `verify`, a repeated import ("already imported" is only said for an intact capture), `annotate`, and every derivation of silver run the same check against `import.json` (all files, sizes, hashes, `manifest.json`). A damaged capture ends with exit 4 and a readable list; nothing new is derived, earlier silver results stay but get `data/silver/<id>/INVALID.json` and `silver_valid: false` in the index line (removed again when the capture verifies); bronze is never repaired. Folders from before D012 have no import record and cannot be checked.
- **One write lock**: `import`, `annotate` and `rebuild --write` hold `data/.sh2perf.lock` (an OS byte-range lock, `filelock.py`) for their whole run, so index lines, annotations and staging folders are never changed by two processes at once; a staging folder found under the lock is a leftover of a dead process by definition. `list`, `verify` and `rebuild` without `--write` do not lock. A busy lock is waited for `--lock-timeout` seconds (default 60), then exit 7, nothing changed. The lock is released by the OS when its process ends in any way, so a killed importer never blocks the tools.
- Exit codes: 0 ok/already imported · 2 choose a recording (several found; nothing touched) · 3 conflict · 4 verification failed / damaged capture / invalid manifest · 5 refused (interrupted, legacy without flag) · 6 write error (staging removed, source untouched) · 7 write lock busy.

## Silver and reproducibility
`silver.py` (silver schema 3, tool 2.1.0) derives `summary.json`, `timeline.md` and the index line from bronze + `data/annotations/<id>.json` only (no clock, no TEST folder); the summary names its tool (`sh2perf-silver <version>`). `ingest.py rebuild` re-derives every capture; `rebuild --write` replaces the index lines and `data/silver/`. `ingest.py verify <id>` re-hashes bronze against `import.json`. Change `silver.TOOL["version"]` whenever the derivation changes.
Game speed in silver keeps `planned`, `user_confirmed`, `observed` apart (`by_origin`) and adds `resolved`: strongest origin wins (observed > user_confirmed > planned); observed vs. user-confirmed disagreement is a `conflict` (value `null`); a planned value overridden by a stronger one sets `planned_differs`. `ab_compare.py` shows the speed per capture and warns on differing or unknown speeds.

## Not covered / open
- A normal exit of the game does not finalize an open recording (F117): the manifest stays `recording` and imports only with `--allow-interrupted`. Stop with F9 first.
- Whether the hub's new files behave in Stronghold 2 itself (only stand-in and unit tests so far) → STATE.md.
- Reading speed/pause from the game would need a verified address (analysis task, D005); until then `observed` stays unused.
- A hard kill during `MoveFileEx` at the final manifest: the previous `recording` manifest stays (interrupted), never a half-written file (temp + rename).
