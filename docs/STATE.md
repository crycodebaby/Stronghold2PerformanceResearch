# STATE

> Kurzfassung: Aktueller Stand, offene Aufgaben, nächster Schritt. Immer zuerst lesen.

Updated: 2026-10-15 · Phase: 0 (infrastructure + data architecture ready, no game measurements yet)

## Done
- [x] Tools installed + verified (SETUP.md); REA doctor: Ghidra `available`, registration `aligned` (needs Claude Code restart)
- [x] TEST copy, variant `baseline` + `steam_appid.txt`
- [x] Checks 3a–3d → FINDINGS F030–F033, F041–F050, docs/FORMATS/*
- [x] Hub `perf-metrics` @ `d29d935`: counters, timings, histogram, CSV, thread CPU, module dump, `--out` dir, `latest.json` with hub commit. Builds clean. **Not yet run in game.**
- [x] Ghidra: exe + dragonfly.dll analysed; vtables exported; `data/vtables.db` via `sym.py build` (31,865 slots / 6,218 functions)
- [x] Data architecture (D006): captures/ → data/index.jsonl → docs/; `ingest.py` (synthetic end-to-end test OK, 8-line summary)
- [x] `sym.py` (addr/class), `fbrief.py` + `FunctionBrief.java` (tested on 0x0076ADC0 → F070)
- [x] CLAUDE.md as routing table; tools/ and ghidra_scripts/ CLAUDE.md; Kurzfassung in all docs
- [x] Skills `messung-auswerten`, `funktion-analysieren` (.claude/skills/)
- [x] `lint_docs.py` in pre-push (ids, links, summary, size, user paths, STATE change)
- [x] D007 privacy rule; personal paths removed from tools and docs (`tools/paths.py`)
- [x] Design draft: docs/design/SAMPLING_PROFILER.md (no code, D005)

## Open tasks (ordered)
1. USER: restart Claude Code (REA MCP tools, skills, new PATH)
2. USER: smoke test `SH2Launcher.exe "<TEST>\Stronghold2.exe"` → overlay? F9 twice → `SH2Perf_out\latest.json`? log module list (F032)
3. USER: build KNIGHTS scenario (EXPERIMENTS.md) → EXP-001 baseline → skill `messung-auswerten`
4. EXP-002 LAA, EXP-003 DXVK (`tools/variant.py`)
5. If EXP-001 = sim-bound: implement sampling profiler per design; `ExportFunctions.java` for full symbol coverage
6. Low prio: GR2 → standard uncompressed GR2 via file-builder API

## Next step
Smoke test of SH2Launcher + overlay + one short F9 recording, then `ingest.py --exp EXP-000 --scenario SMOKE --troops 0`.

## Risks / unknowns
- Remote-thread injection into the suspended game untested (fallback needs a d3d9 proxy, conflicts with DXVK)
- Direct start relies on `steam_appid.txt`; untested
- Scenario editor may not allow enemy units → fallback in EXPERIMENTS.md
- `sym.py addr` only knows virtual functions until ExportFunctions exists
