# STATE

Updated: 2026-10-15 · Phase: 0 (measurement infrastructure ready, no measurements yet)

## Done
- [x] Tools installed + verified (SETUP.md): JDK 21, Ghidra 12.1.4, CMake, VS BuildTools (MSVC 14.44 x86), x64dbg, RenderDoc, ffmpeg, DXVK 3.1.1
- [x] REA doctor: Ghidra provider `available`, registration `aligned`, env stored in `~/.claude.json` → needs Claude Code restart
- [x] TEST copy `Stronghold 2 - TEST` (14,395 files, 1.5 GB), currently variant `baseline` + `steam_appid.txt`
- [x] Repo + docs + pre-push hook (tested: rejects push without STATE.md change)
- [x] Checks 3a–3d → FINDINGS F030–F033, F041–F049, docs/FORMATS/*
- [x] AnalyseHub branch `perf-metrics` @ `68de2e2`: counters, timings, histogram, CSV, thread CPU, module dump, CMake, SH2Launcher. Builds clean. **Not yet run in game.**
- [x] Tools: `pe_info.py`, `laa_patch.py` (guard tested), `variant.py` (baseline↔laa tested), `analyze_frames.py` (synthetic CSV tested), `granny_raw`
- [x] Ghidra headless: dragonfly.dll (82 vtables) + Stronghold2.exe (1,585 vtables / 31,865 slots); project `RE-Projects\ghidra-projects\SH2`
- [x] Hotspot candidate list (17 entries, class-level only) → FUNCTIONS.md

## In progress
- (none)

## Open tasks (ordered)
1. USER: restart Claude Code (REA MCP tools + new PATH)
2. USER: first smoke test: `SH2Launcher.exe` → overlay visible? log `Stronghold2AnalyseHub.log` OK? module list answers F032
3. USER: build KNIGHTS scenario (EXPERIMENTS.md) → EXP-001 baseline
4. EXP-002 LAA, EXP-003 DXVK (`tools/variant.py`)
5. Ghidra/REA: call graph from `Simulation::vf02` (0x0076ADC0) and `S2Actor::vf20` (0x004E92C0) — only after EXP-001 shows sim-bound
6. Low prio: GR2 → standard uncompressed GR2 via file-builder API

## Next step
Smoke test of SH2Launcher + overlay in the TEST copy (user runs game), then EXP-001.

## Risks / unknowns
- Remote-thread injection into a suspended process untested on this game (fallback: attach-after-start won't catch Direct3DCreate9 → would need d3d9 proxy, conflicts with DXVK)
- Steam: direct start relies on `steam_appid.txt`; untested
- Scenario editor may not allow enemy units → fallback in EXPERIMENTS.md
