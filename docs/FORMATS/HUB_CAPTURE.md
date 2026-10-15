# Hub capture files

> Kurzfassung: Dateien, die der AnalyseHub pro Aufnahme schreibt (frames/threads/samples CSV, latest.json, Log): Spalten, Einheiten, wann ein Wert 0 bzw. n/a ist, Versionierung (`capture_version`); Identität einer Aufnahme steht im Manifest ([CAPTURE_MANIFEST.md](CAPTURE_MANIFEST.md)), `latest.json` ist nur ein Verweis.

Written to `SH2Perf_out` next to the TEST exe (`SH2HUB_OUT` / `out=`). One recording = F9 on … F9 off. Stem = local start time `SH2Perf_<YYYYMMDD>_<HHMMSS>` (a second recording in the same second moves to the next free second). Everything is written by the hub's capture thread, never by the render thread (D011).

## `<stem>_frames.csv` — one row per frame (Present to Present)
Header, unchanged since the first hub build (readers: `analyze_frames.py`, `ingest.py`, `ab_compare.py`):

`frame,t_s,frame_ms,present_ms,endscene_ms,between_endscene_ms,overlay_ms,scenes,dip,dp,dpup,dipup,prims,settex,vsconst_calls,vsconst_vec4,psconst_calls,psconst_vec4,va_used_mb,marker`

| Column | Unit | Source / switch |
|---|---|---|
| `frame` | frame index since hub start (gaps = dropped frames) | `frametime` |
| `t_s` | s since recording start | `frametime` |
| `frame_ms`, `present_ms` | ms; frame = Present to previous Present, present = time inside the original `Present` | `frametime` |
| `endscene_ms`, `between_endscene_ms`, `overlay_ms` | ms per frame; EndScene wall time, time from the previous EndScene exit, own ImGui drawing | `overlay` (EndScene hook); **0 otherwise** |
| `scenes … psconst_vec4` | counts per frame (BeginScene, DrawIndexedPrimitive `dip`, DrawPrimitive `dp`, the two `UP` variants, triangles `prims`, SetTexture, shader constant calls and vec4) | `counters`; **0 otherwise** |
| `va_used_mb` | MB, reserved + committed (F089), last value polled (about 1 s old) | `poll`; **0 otherwise** |
| `marker` | number of F8 presses so far | always |

A 0 can therefore mean "measured 0" (menu: no DIP) or "switch off". the recording's manifest (`switches`) tells which (older: `latest.json` → `modes`); `ingest.py` stores the unmeasured metrics as `null`.

## `<stem>_threads.csv` — only with `poll`
`t_s,tid,cpu_pct,is_render_thread`: one row per thread above 0.5 % CPU about once per second (100 ns CPU time vs wall clock, 100 % = one core). Polled on the capture thread, only while recording.

## `<stem>_samples.csv` — only with the sampler (`SH2HUB_SAMPLE`)
`marker,module,rva,count`, see [SAMPLING_PROFILER.md](../design/SAMPLING_PROFILER.md).

## `latest.json` — pointer to the newest finished recording (not an identity)
Since `capture_version: 3` (D012) it only points to the newest recording's manifest; every recording has its own `<stem>_manifest.json` ([CAPTURE_MANIFEST.md](CAPTURE_MANIFEST.md)), and an importer must not use `latest.json` to identify, describe or select a recording. Keys (file names only, no absolute paths): `frames_csv`, `threads_csv` (if `poll`), `samples_csv` (if sampled), `log`, `start`, `stop`, `frames` (rows written), `markers`, `hub_commit`, since **`capture_version: 2`** (D011) the health and mode keys below, since **`capture_version: 3`** (D012) also `capture_id`, `manifest`, `manifest_sha256` (`null` if the manifest could not be written):

| Key | Meaning |
|---|---|
| `capture_ok` | `false` if frames were dropped, a write failed or a flush failed — such a recording is not a baseline |
| `frames_dropped` | records lost because the ring (8,192) was full; the render thread did not wait |
| `frames_lost_write` | records lost after a write error |
| `write_errors` | failed writes/flushes/closes |
| `modes` | `{frametime, counters, poll, overlay, sample}` in effect |

Captures written before version 2 have none of these keys: switches and capture health are **unknown** (an earlier version of this page said "all on, OK"; that is not proven for any single recording). The hub log (`Stronghold2AnalyseHub.log`, shared by all recordings of a session) has the matching lines: `Config: …`, `Recording started/stopped …`, `Capture: … dropped …`, `Capture: write … failed …`.

## Compatibility rule
Columns of the frames/threads/samples CSVs are not changed or reordered. A new column or a changed meaning needs a new `capture_version`, a reader change in `ingest.py` in the same step and a line here. Version 3 adds files (`*_manifest.json`, `*_prepared.json`) and `latest.json` keys only.
