# DECISIONS

Format: ID · date · decision · rationale · rejected alternatives.

## D001 · 2026-10-15 · Patch/hook the original, not reimplement
- Decision: Improve performance via measurement, hooks and patches on `Stronghold2.exe`. Reimplementation = long-term vision.
- Rationale: ~1,300 game classes / 5 MB code; cause of slowdown unmeasured; proprietary middleware (Granny, LifeStudio); lockstep determinism makes bit-exact reimplementation very hard.
- Rejected: full open-source clone now (years, unclear payoff before knowing the hotspot).

## D002 · 2026-10-15 · Separate project repo, AnalyseHub stays its own repo
- Decision: `SH2-Perf` holds docs + small tools; `Stronghold2AnalyseHub` (upstream crycodebaby) gets changes on branch `perf-metrics`.
- Rationale: keeps upstream history clean, allows PR upstream; docs independent of DLL code.
- Rejected: vendoring AnalyseHub into SH2-Perf (loses upstream link); git submodule (extra friction now, can add later).

## D003 · 2026-10-15 · CMake build for AnalyseHub
- Decision: add `CMakeLists.txt` (Win32, Release, static CRT).
- Rationale: upstream `.sln` references no project (no `.vcxproj` in repo) → not buildable as-is. CMake is scriptable from CLI.
- Rejected: hand-written `.vcxproj` (verbose, hard to review).

## D004 · 2026-10-15 · Load AnalyseHub via launcher injection, not d3d9.dll proxy
- Decision: `SH2Launcher.exe` starts the game suspended, injects the DLL (`LoadLibraryW` via remote thread), waits for a ready event, resumes.
- Rationale: DXVK test (EXP-003) needs `d3d9.dll` in the game folder → a d3d9 proxy would collide. Hook must be installed before the game calls `Direct3DCreate9` → suspended start.
- Rejected: d3d9 proxy (DXVK conflict); attach-after-start injection (misses `Direct3DCreate9`).

## D005 · 2026-10-15 · Measurement first, game-code hooks later
- Decision: phase 1 instruments only D3D9 (counters, timings). No hooks into game functions until profiling data (EXP-001) points at a hotspot.
- Rationale: user requirement; avoids guesswork.
- Rejected: speculative hooks on pathfinder.
