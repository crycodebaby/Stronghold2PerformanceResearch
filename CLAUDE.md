# SH2-Perf — Stronghold 2 performance RE

## Goal
Improve Stronghold 2 (Steam, Win32/DX9) performance through **measurement → hooks → patches on the original binary**.
Open-source reimplementation = long-term vision, NOT current scope.

Target problem: many troops (2 players × ~100 knights) → ~20 FPS; more troops / melee → 1–2 FPS, even on strong PCs. Cause: unmeasured.

## Read first
1. `docs/STATE.md` — current state, open tasks, next step. ALWAYS read first.
2. `docs/FINDINGS.md` — facts with status + evidence.
3. Others as needed: `docs/DECISIONS.md`, `docs/EXPERIMENTS.md`, `docs/FUNCTIONS.md`, `docs/FORMATS/`, `docs/SETUP.md`.

## Paths
| What | Path |
|---|---|
| Original game (READ-ONLY, never modify) | `<RE-Projects>\Stronghold 2` |
| Test copy (all experiments here) | `<RE-Projects>\Stronghold 2 - TEST` |
| Overlay/measurement DLL (separate repo) | `<RE-Projects>\Stronghold2AnalyseHub` |
| Ghidra | `%GHIDRA_INSTALL_DIR%` = `%USERPROFILE%\Tools\ghidra_12.1.4_PUBLIC` |
| Local raw data (gitignored) | `captures/` |

## Hard rules
- NEVER modify the original game folder. Experiments only in `Stronghold 2 - TEST`.
- NEVER commit game files, exe/dll, assets, Ghidra DBs or decompiled code. Own code + docs only. (Legal: §69e UrhG; OpenMW model.)
- No hooks on game code without measurement data justifying them.
- Measurement tooling only reads/logs; it must not change game behavior.
- Every fact in FINDINGS.md carries a status `[verifiziert | Hypothese | widerlegt]` and evidence (command, address, measurement).
- Strictly separate observation from inference.

## Workflow (mandatory)
- After each work step and before each commit/push: update `docs/STATE.md` + affected docs.
- `pre-push` hook rejects pushes whose commits don't touch `docs/STATE.md` (install: `git config core.hooksPath .githooks`).
- Write terse, machine-readable docs (tables, bullets). No prose novels.
- New function name in Ghidra → row in `docs/FUNCTIONS.md` (address | name | confidence | evidence).
- New measurement → entry in `docs/EXPERIMENTS.md` (setup, scenario, result, date).
- New decision → `docs/DECISIONS.md` with rationale + rejected alternatives.

## Tools
- `tools/pe_info.py <file>` — PE machine/flags/imports/exports summary.
- `tools/laa_patch.py <exe>` — set LARGE_ADDRESS_AWARE on a COPY (refuses original path).
- `tools/analyze_frames.py <csv>` — FPS percentiles/counters from AnalyseHub frame CSV.
- REA MCP (`reverse-engineer-anything` skill) with Ghidra provider for native analysis.
