# STATE

> Kurzfassung: Aktueller Stand, offene Aufgaben, nächster Schritt. Immer zuerst lesen.

Updated: 2026-10-15 · Phase: 0 → 1 (tooling verified in game via EXP-000; first real measurement EXP-001 pending)

## Done
- [x] Tools installed + verified (SETUP.md); REA doctor: Ghidra `available`, registration `aligned`; MCP tools loaded
- [x] Checks 3a–3d → FINDINGS F030–F033, F041–F050, docs/FORMATS/*
- [x] Hub `perf-metrics` @ `a8c7ad779e03`, built and copied to TEST: counters, timings, histogram, CSV, thread CPU, module dump, output dir, `latest.json` with hub commit, `SH2HUB_AUTORECORD`, caller chain of `Direct3DCreate9` in `SH2Proxy.log`. Runs in game since EXP-000 (`7a9e511`); `a8c7ad779e03` load-checked with the TEST copies in the stand-in program, not yet in game
- [x] Ghidra: exe + dragonfly.dll analysed; vtables exported; `data/vtables.db` via `sym.py build` (31,865 slots / 6,218 functions)
- [x] Data architecture (D006): captures/ → data/index.jsonl → docs/; `ingest.py` (real capture EXP-000 OK)
- [x] `sym.py` (addr/class), `fbrief.py` + `FunctionBrief.java` (tested on 0x0076ADC0 → F070)
- [x] CLAUDE.md as routing table; tools/ and ghidra_scripts/ CLAUDE.md; Kurzfassung in all docs
- [x] Skills `messung-auswerten`, `funktion-analysieren` (.claude/skills/)
- [x] `lint_docs.py` in pre-push (ids, links, summary, size, user paths, STATE change)
- [x] D007 privacy rule; personal paths removed from tools and docs (`tools/paths.py`)
- [x] Design draft: docs/design/SAMPLING_PROFILER.md (no code, D005)
- [x] Version 1.5 Steam + full exe sha256 (F058); direct start works (F057)
- [x] Launcher crash analysed: hub logger self-deadlock → `abort()` (F080–F082), fixed in hub `7a9e511`
- [x] d3d9 proxy (D009): chains to system d3d9 or `d3d9_dxvk.dll`, `SH2Proxy.ini`, hub switch, exe-hash check in log; stand-in program (F083) and in game (EXP-000, system d3d9)
- [x] `variant.py` installs proxy + hub for every variant, DXVK as `d3d9_dxvk.dll`; `tools/test_variant.py` (9 tests OK); TEST = `baseline` (proxy + hub `a8c7ad779e03`, `target=system`, hub on)
- [x] EXP-000 SMOKE ingested (`20261015_EXP-000_baseline_SMOKE`): proxy + hub work in game; menu 45 FPS, render thread ~12 % CPU → verdict n/a
- [x] Module list → F032 verified, F084/F085 (Steam overlay loaded, F086 hypothesis); device flags 0x44, 2× `Direct3DCreate9` (F087/F088)
- [x] `va_used_mb` = reserved + committed, limit 2048/4096 MB (F089); menu 1,351 MB (F090 hypothesis)
- [x] Counter hooks verified (slot static_asserts + counter test, system d3d9 + DXVK) (F091); menu uses DrawPrimitive only (F092)
- [x] dxrenderer.dll classified: Dragonfly D3D9 render plugin, structure only (F093/F094)

## Open tasks (ordered)
1. USER: build KNIGHTS scenario (EXPERIMENTS.md, Scenario Editor; fallback Kingmaker) — note graphics settings
2. EXP-001 baseline KNIGHTS N=100, phases P0–P4 → skill `messung-auswerten`; judge with render-thread CPU %, not `cpu-side` alone. Check `SH2Proxy.log` caller chain (F088)
   - optional EXP-001-REAL: user's own save from a real lag situation, same protocol (EXPERIMENTS.md)
3. EXP-002 LAA, EXP-003 DXVK (`tools/variant.py`, proxy chains to `d3d9_dxvk.dll`); optional: Steam overlay off vs. on (F086)
4. If EXP-001 = sim-bound: implement sampling profiler per design; `ExportFunctions.java` for full symbol coverage
5. Import `dxrenderer.dll` into Ghidra (vtables, `fbrief`) if the render path matters (F094)
6. Hub idea: log largest free VA block next to `va_used_mb` (fragmentation, F090)
7. Low prio: GR2 → standard uncompressed GR2 via file-builder API

## Next step
USER builds the KNIGHTS scenario (optionally also EXP-001-REAL with a real lag save), then EXP-001 (baseline, N=100, P0–P4 with F8 markers) → `ingest.py --exp EXP-001 --scenario KNIGHTS --troops 100`.

## Risks / unknowns
- F082 (cause of launcher crash) unconfirmed: launcher not re-run with fixed hub (low priority, proxy is default)
- DXVK behind the proxy only tested in the stand-in program
- Steam overlay hooks D3D9 as well (F086): may distort `present_ms`
- Menu already at 1,351 / 2,048 MB VA (F090): watch `va_used_mb` in big battles
- Whether direct start needs the Steam client running: untested (F057)
- Scenario editor may not allow enemy units → fallback in EXPERIMENTS.md
- `sym.py addr` only knows virtual functions until ExportFunctions exists
