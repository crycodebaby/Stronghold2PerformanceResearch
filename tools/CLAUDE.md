# tools/

Run every tool as `python -I tools/<name>.py` from the repo root; `--help`/no args prints usage.

| Tool | Purpose |
|---|---|
| `paths.py` | single source for all locations (relative to repo); import it, never hardcode paths |
| `ingest.py` | hub recording → `captures/<id>/` + `meta.json` + line in `data/index.jsonl` |
| `analyze_frames.py` | metrics for one CSV / marker range (library: `summarize()`) |
| `sym.py` | vtable symbol DB: `build`, `addr <hex>`, `class <name>` |
| `fbrief.py` | structural brief of one function via Ghidra headless (no decompiled code) |
| `variant.py` | TEST copy: baseline / laa / dxvk / laa+dxvk |
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
