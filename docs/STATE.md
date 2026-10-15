# STATE

> Kurzfassung: Aktueller Stand, offene Aufgaben, nächster Schritt. Immer zuerst lesen.

Updated: 2026-10-15 · Phase: 0 (infrastructure ready; hub loader switched to d3d9 proxy, first in-game run pending)

## Done
- [x] Tools installed + verified (SETUP.md); REA doctor: Ghidra `available`, registration `aligned` (needs Claude Code restart)
- [x] TEST copy, variant `baseline` + `steam_appid.txt`
- [x] Checks 3a–3d → FINDINGS F030–F033, F041–F050, docs/FORMATS/*
- [x] Hub `perf-metrics` @ `d29d935` (now `7a9e511`, built + copied to TEST): counters, timings, histogram, CSV, thread CPU, module dump, `--out` dir, `latest.json` with hub commit. Builds clean. **Not yet run in game.**
- [x] Ghidra: exe + dragonfly.dll analysed; vtables exported; `data/vtables.db` via `sym.py build` (31,865 slots / 6,218 functions)
- [x] Data architecture (D006): captures/ → data/index.jsonl → docs/; `ingest.py` (synthetic end-to-end test OK, 8-line summary)
- [x] `sym.py` (addr/class), `fbrief.py` + `FunctionBrief.java` (tested on 0x0076ADC0 → F070)
- [x] CLAUDE.md as routing table; tools/ and ghidra_scripts/ CLAUDE.md; Kurzfassung in all docs
- [x] Skills `messung-auswerten`, `funktion-analysieren` (.claude/skills/)
- [x] `lint_docs.py` in pre-push (ids, links, summary, size, user paths, STATE change)
- [x] D007 privacy rule; personal paths removed from tools and docs (`tools/paths.py`)
- [x] Design draft: docs/design/SAMPLING_PROFILER.md (no code, D005)
- [x] Version 1.5 Steam + full exe sha256 (F058); direct start works (F057)
- [x] Launcher crash analysed: hub logger self-deadlock → `abort()` (F080–F082), fixed in hub `7a9e511`
- [x] d3d9 proxy (D009): chains to system d3d9 or `d3d9_dxvk.dll`, `SH2Proxy.ini`, hub switch, exe-hash check in log; tested in a stand-in D3D9 program (F083), **not yet in game**
- [x] `variant.py` installs proxy + hub for every variant, DXVK as `d3d9_dxvk.dll`; `tools/test_variant.py` (9 tests OK); TEST set to `baseline`

## Open tasks (ordered)
1. USER: smoke test with proxy: start `TEST\Stronghold2.exe` normally → overlay? F9 twice → `SH2Perf_out\latest.json` → `ingest.py --exp EXP-000 --scenario SMOKE --troops 0`; confirms F082/F083 in game, module list answers F032
2. USER: build KNIGHTS scenario (EXPERIMENTS.md) → EXP-001 baseline → skill `messung-auswerten`
3. EXP-002 LAA, EXP-003 DXVK (`tools/variant.py`, proxy chains to `d3d9_dxvk.dll`)
4. If EXP-001 = sim-bound: implement sampling profiler per design; `ExportFunctions.java` for full symbol coverage
5. Low prio: GR2 → standard uncompressed GR2 via file-builder API

## Next step
In-game smoke test with the d3d9 proxy (task 1). If the game does not start: `variant.py hub off` → starts? (proxy vs. hub), then read `SH2Perf_out\SH2Proxy.log` + hub log.

## Risks / unknowns
- Proxy + hub never ran inside the game yet (F083 = stand-in program only); F082 (cause of launcher crash) unconfirmed in game
- DXVK behind the proxy only tested in the stand-in program
- Whether direct start needs the Steam client running: untested (F057)
- Scenario editor may not allow enemy units → fallback in EXPERIMENTS.md
- `sym.py addr` only knows virtual functions until ExportFunctions exists
