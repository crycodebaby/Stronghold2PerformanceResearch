# SH2-Perf

Stronghold 2 (Steam, Win32/DX9) faster through **measurement → hooks → patches on the original**.
Problem: 2×~100 knights ≈ 20 FPS, more troops/melee → 1–2 FPS. Cause unmeasured. Reimplementation = later vision.

## Routing (task → file)

| Task | Read / use |
|---|---|
| Start of any session | [docs/STATE.md](docs/STATE.md) |
| Evaluate a new measurement | skill `messung-auswerten` → `tools/ingest.py` |
| Analyse a function / address | skill `funktion-analysieren` → `tools/sym.py`, `tools/fbrief.py` |
| Look up a fact | [docs/FINDINGS.md](docs/FINDINGS.md) |
| Why is X done this way | [docs/DECISIONS.md](docs/DECISIONS.md) |
| Test scenario, protocol, results | [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) |
| Named functions (mittel/hoch) | [docs/FUNCTIONS.md](docs/FUNCTIONS.md) |
| File formats | [docs/FORMATS/](docs/FORMATS/) |
| Rebuild tools/environment | [docs/SETUP.md](docs/SETUP.md) |
| Overview of all folders in `RE-Projects` | [../README.md](../README.md) |
| Hub capture files, switches, `latest.json` | [docs/FORMATS/HUB_CAPTURE.md](docs/FORMATS/HUB_CAPTURE.md) |
| Granny observer (EXP-008) data contract | [docs/FORMATS/GRANNY_OBSERVER.md](docs/FORMATS/GRANNY_OBSERVER.md) → `tools/grannyobs.py` |
| Per-recording manifest, provenance, safe import | [docs/FORMATS/CAPTURE_MANIFEST.md](docs/FORMATS/CAPTURE_MANIFEST.md) |
| Sampling profiler design | [docs/design/SAMPLING_PROFILER.md](docs/design/SAMPLING_PROFILER.md) |
| Write or change a tool | [tools/CLAUDE.md](tools/CLAUDE.md) |
| Ghidra scripts | [ghidra_scripts/CLAUDE.md](ghidra_scripts/CLAUDE.md) |

## Data layers

| Layer | Where | Git | Content |
|---|---|---|---|
| Bronze | `captures/` | ignored | raw CSV/logs, Ghidra exports, briefs — read only through tools |
| Silver | `data/` | `index.jsonl` + `annotations/` tracked, `silver/` + `*.db` rebuilt | one metrics line per capture, derived from bronze + annotations by `ingest.py` (tool version recorded; `rebuild`); `vtables.db` (`sym.py build`) |
| Gold | `docs/` | tracked | curated facts, decisions, experiments |

## Sibling folders (relative to repo)

`../Stronghold 2` original, read-only · `../Stronghold 2 - TEST` all experiments · `../Stronghold2AnalyseHub` hub (branch `perf-metrics`) · `../ghidra-projects/SH2` Ghidra DB.

## Rules

- Original folder stays untouched; experiments run on the TEST copy.
- Repo holds own code + docs only: no game files, assets, Ghidra DBs or decompiled code.
- Context gets tool output of ≤ ~30 lines; raw logs and decompiled code stay in their files.
- Game-code hooks follow measurement data (D005); measurement tooling only reads.
- FINDINGS entries carry `[verifiziert | Hypothese | widerlegt]` + evidence; observation and inference stay separate.
- After each work step and before commit/push: update docs/STATE.md + affected docs.
- Push runs `tools/lint_docs.py` (hook: `git config core.hooksPath .githooks`).
- Raw logs leave the machine only after personal paths are removed (D007).
