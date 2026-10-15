# tools/

Run every tool as `python -I tools/<name>.py` from the repo root; `--help`/no args prints usage.

| Tool | Purpose |
|---|---|
| `paths.py` | single source for all locations (relative to repo); import it, never hardcode paths |
| `ingest.py` | `list` / `import` / `annotate` / `verify` / `rebuild` (D012): verify against the manifest → stage → atomic commit to `captures/<capture_id>/`; sources are never deleted; same id + different content = conflict; silver in `data/silver/` + `data/index.jsonl`; user facts in `data/annotations/` |
| `bronze.py`, `silver.py`, `capture_manifest.py`, `filelock.py` | libraries behind `ingest.py`: import transaction + integrity check + safe cleanup, silver derivation (tool version in every result; reference profile), manifest contract + name/role validation, write lock |
| `testkit.py`, `test_import_safety.py`, `test_hardening.py` | fixtures and tests for provenance/import (manifests, interruption, conflicts, write errors, speed origins); `test_hardening` = reference release, bronze integrity, write lock with real processes, names/roles |
| `e2e_standin.py` | real proxy + hub DLL + stand-in → manifests → import → END-key deactivation, in a temp folder (needs the hub build; `--deactivate-only --repeat N`, `--hub-build`) |
| `analyze_frames.py` | metrics for one CSV / marker range (library: `summarize()`); `--timeline [--window 5]` = 5 s windows (FPS, DIP, triangles, render CPU) |
| `samples.py` | sampler output: module groups per marker, top functions (`SH2Perf_*_samples.csv`) |
| `funcsamples.py` | function-mode samples → Ghidra function bodies (`captures/functions/<module>_functions.csv` from `ExportFunctions.java`), est. ms/frame per marker; unresolved addresses stay unresolved; `--check <rva> --module exe\|granny2`; `--delta-counts --module exe` = counts behind running-only statements (F135) |
| `grannyobs.py` | Granny observer files of one recording (EXP-008): calls/objects per frame, same vs changed clock and inputs, link classes, losses; per marker (docs/FORMATS/GRANNY_OBSERVER.md) |
| `ab_compare.py` | frame-time distributions of several captures side by side (A/B/repeat), long frames per minute, 1 s clock share vs random control; compares only columns valid in every hub mode |
| `test_ab_compare.py` | unit tests for `ab_compare.py` (synthetic series) |
| `test_ingest.py` | unit tests for the recording choice of `ingest.py` and the module groups |
| `sym.py` | vtable symbol DB: `build`, `addr <hex>`, `class <name>` |
| `fbrief.py` | structural brief of one function via Ghidra headless (no decompiled code) |
| `variant.py` | TEST copy: baseline / laa / dxvk / laa+dxvk; installs d3d9 proxy + hub (D009); `hub on/off`, `sample off/module/function`, `mode full/min`, `switch <frametime\|counters\|poll\|overlay\|beep> on/off/default` (D011), `granny on\|off` (EXP-008 observer, separate switch), `plan key=value…` (planned experiment/protocol/scenario/game_speed/paused, D012); writes `SH2Prepared.json` |
| `test_variant.py` | unit tests for `variant.py` (temp folder) |
| `laa_patch.py` | LARGE_ADDRESS_AWARE flag; refuses the original folder |
| `pe_info.py` | PE header/imports/exports |
| `vtable_candidates.py` | keyword filter over the vtable CSV |
| `lint_docs.py` | docs checks, run by pre-push |
| `granny_raw/` | GR2 → Granny raw dump via the game's DLL (local only) |

Conventions:
- Output ≤ 30 lines; longer results go to a file under `captures/` and the tool prints the path.
- `python -I` drops the script dir from `sys.path`: start with `sys.path.insert(0, <tools dir>)` before local imports.
- Stdlib only (no pip installs).
- Data written to `data/` holds relative names only, never absolute user paths.
