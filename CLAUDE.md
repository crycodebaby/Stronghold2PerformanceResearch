# SH2-Perf

Stronghold 2 (Steam, Win32/DX9): bounded reverse engineering, reproducible evidence and own testable parts.
Performance changes require separate measurements; no demonstrated speedup. Current scope is in STATE.

Public entry: [README.md](README.md). Tool-neutral agent rules: [AGENTS.md](AGENTS.md). Current order: "Current status" in docs/STATE.md.

## Routing (task → file)

| Task | Read / use |
|---|---|
| Start of any session | [docs/STATE.md](docs/STATE.md), then [short leadership guide](docs/PROJECT_LEAD_HANDOFF.md); only linked task/evidence next |
| Evaluate a new measurement | skill `messung-auswerten` → `tools/ingest.py` |
| Analyse a function / address | skill `funktion-analysieren` → `tools/sym.py`, `tools/fbrief.py` |
| Look up a fact | [docs/FINDINGS.md](docs/FINDINGS.md) |
| Why is X done this way | [docs/DECISIONS.md](docs/DECISIONS.md) |
| Test scenario, protocol, results | [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) |
| Named functions (mittel/hoch) | [docs/FUNCTIONS.md](docs/FUNCTIONS.md) |
| File formats | [docs/FORMATS/](docs/FORMATS/) |
| Rebuild tools/environment | [docs/SETUP.md](docs/SETUP.md) |
| Overview of the local workspace folders (`RE-Projects`) | [docs/WORKSPACE.md](docs/WORKSPACE.md) |
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

Standard layout only: see [WORKSPACE](docs/WORKSPACE.md). Actual local paths may be in ignored
`build/project-lead-handoff/LOCAL_ENVIRONMENT.json`; verify branch/HEAD and project-copy paths before use.

## Rules

- Original folder stays untouched; experiments run on the TEST copy.
- Repo holds own code + docs only: no game files, assets, Ghidra DBs or decompiled code.
- Context gets tool output of ≤ ~30 lines; raw logs and decompiled code stay in their files.
- Game-code hooks follow measurement data (D005); measurement tooling only reads.
- FINDINGS entries carry `[verifiziert | Hypothese | widerlegt]` + evidence; observation and inference stay separate.
- After each work step and before commit/push: update docs/STATE.md + affected docs.
- Push runs `tools/lint_docs.py` (hook: `git config core.hooksPath .githooks`).
- Raw logs leave the machine only after personal paths are removed (D007).
