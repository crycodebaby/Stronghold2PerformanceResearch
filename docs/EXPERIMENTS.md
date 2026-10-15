# EXPERIMENTS

> Kurzfassung: Testszenario KNIGHTS, Messprotokoll, geplante und ausgewertete Messungen (EXP-###). Rohdaten: captures/, Kennzahlen: data/index.jsonl.

Each entry: ID · date · variant · setup · scenario · result · conclusion. Raw CSVs stay in `captures/` (gitignored); paste `tools/analyze_frames.py` output here.

## Standard test scenario "KNIGHTS" (proposal, not yet built)

Goal: reproducible, separates **simulation cost** from **render cost**, gives a **scaling curve**.

### Build once (in TEST copy, via Scenario Editor)
1. Main menu → Scenario Editor → new map, flat terrain, smallest size that fits 2 armies. [Hypothese: editor can place units for 2 players — verify; fallback below]
2. Place Player 1: N knights in a block on the west side; Player 2: N knights on the east side, ~60 tiles apart. No buildings except required keeps.
3. Save as scenario `PERF_KNIGHTS_N` for N = 25, 50, 100, 200 (4 files).
4. Fallback if editor can't assign enemy units: Kingmaker on a small map vs 1 AI, max starting gold/troops, buy N knights, save game before attacking.

### Phases per run (one save per phase start)
| Phase | Action | What it isolates |
|---|---|---|
| P0 idle | troops standing still | baseline per-unit cost (animation, idle AI) |
| P1 march | both armies ordered toward each other (no contact yet) | pathfinding + formation movement |
| P2 melee | armies in contact | target search, combat, collision |
| P3 melee paused | press pause during P2 for 15 s | render-only cost (sim stopped) |
| P4 melee look-away | camera pointed at empty corner during P2 | sim-only cost (few draws) |

### Measurement protocol
1. `python -I tools/variant.py <variant>` (installs d3d9 proxy + hub, D009); start Steam; start `Stronghold 2 - TEST\Stronghold2.exe` normally (double-click).
2. Fixed settings: same resolution/graphics preset each run (note them), V-Sync OFF, window mode noted.
3. Load save → wait 10 s → **F9** (record on).
4. At each phase start press **F8** (marker). ~30 s per phase.
5. **F9** (record off). Hub writes CSVs + `latest.json` to `TEST\SH2Perf_out\` (`out=` in `SH2Proxy.ini` or env `SH2HUB_OUT` overrides).
6. Close the game, then `python -I tools/ingest.py --exp <EXP> --scenario KNIGHTS --troops <N>` (skill `messung-auswerten`): moves files to `captures/<date>_<EXP>_<variant>_KNIGHTS/`, appends `data/index.jsonl`, prints per-marker phases.

### Interpretation key
| Observation | Points to |
|---|---|
| P3 (paused) FPS ≫ P2 | simulation is the bottleneck |
| P4 (look-away) FPS ≈ P2 | simulation is the bottleneck |
| P4 FPS ≫ P2, P3 ≈ P2 | rendering/draw-call bottleneck |
| render thread ≈ 100 % of one core, others idle | single-threaded CPU limit |
| high `present_ms` | GPU-bound or driver wait |
| frame ms grows ~N² across N=25…200 | O(n²) algorithm (e.g. target search) |
| VA used near 2,048 MB / crash | address space (LAA helps); `va_used_mb` = reserved + committed (F089) |
| high `cpu-side ms` but render thread CPU % low | waiting/sleeping outside Present (frame limiter, sync), not CPU work: `cpu-side` = frame − Present − EndScene wall time |

## Planned
| ID | Variant | Scenario | Status |
|---|---|---|---|
| EXP-001 | baseline | KNIGHTS N=100, P0–P4 | waiting for user run |
| EXP-001b | baseline | KNIGHTS N=25/50/200, P2 | waiting |
| EXP-001-REAL-A | baseline | REAL8P_EARLY: 8 players (7 AI), early, ~10 s, no lag | ingested, reference only (no comparison baseline) |
| EXP-001-REAL | baseline | user save from a real lag situation, protocol "Real save" below | waiting for user save |
| EXP-002 | laa | KNIGHTS N=100 + N=200 | after EXP-001 |
| EXP-003 | dxvk | KNIGHTS N=100 | after EXP-001 |
| EXP-004 | laa+dxvk | KNIGHTS N=100 | if 002/003 help |

### EXP-001-REAL (optional): real lag save
Goal: confirm that KNIGHTS reproduces the lag the user actually sees, not just a synthetic load.
- Input: a save game from a real situation with heavy lag (user, any map). Copy the save into the TEST copy's save folder; note map, troop counts per side (estimate), what happens on screen.
- Protocol: identical to KNIGHTS (variant `baseline`, same graphics settings, V-Sync off, load → wait 10 s → F9, F8 at each phase change, ~30 s per phase, F9). Phases as far as they apply: P0 as loaded (paused if the save starts paused, then unpause), P2 the laggy action, P3 pause during the lag, P4 camera on an empty area during the lag.
- Ingest: `python -I tools/ingest.py --exp EXP-001-REAL --scenario REAL --troops <estimate per player> --note "<map, situation>"`.
- Compare with EXP-001 per phase (FPS, render-thread CPU %, present ms, DIP, VA). Same verdict pattern → KNIGHTS is representative; different → use the real save as the main scenario.
- Saves are user data: keep them out of the repo (local only, like captures/).

### Protocol "Real save" (real game states, from EXP-001-REAL on)
Replaces the KNIGHTS phases for the user's own saves; keeps the camera fixed so runs are comparable.
1. Variant `baseline`, same graphics settings and V-Sync off as before (note them). Load the save, wait 10 s.
2. Fix the camera (same position and zoom for the whole run) and keep the mouse in the screen centre (no edge scrolling).
3. **F9** on, then phases with **F8** at each start:

| Phase | Duration | Action |
|---|---|---|
| R0 rest | 20–30 s | game running, camera fixed, no input |
| R1 pause | 15 s | pause the game |
| R2 look-away | 15 s | unpause, point the camera at an empty corner (same zoom) |

4. **F9** off, close the game, then `ingest.py` (skill `messung-auswerten`). Read: R1 vs R0 → sim vs render (Interpretation key); R2 vs R0 → sim-only cost.
5. **Save the game state whenever the FPS in the overlay have dropped clearly** (before you load/leave it): lag situations are hard to recreate, and such a save is the preferred input for EXP-001-REAL.
6. Do not start a second recording while the game runs if a capture is still to be ingested: `latest.json` is overwritten by the newest recording (happened 2026-10-15; the extra recording was set aside in `captures/_unassigned_20261015_034411/`).

## Results

### EXP-000 · 2026-10-15 · baseline · SMOKE (main menu, 0 troops)
- capture `20261015_EXP-000_baseline_SMOKE`, hub `7a9e511da4a6`, exe known build (F058), loader: d3d9 proxy → system d3d9 (D009)
- Setup: main menu only, ~38 s, 1 marker (F8) at ~31 s; Steam overlay loaded (F085). Graphics settings not noted.

| Range | Frames | FPS avg | 1% low | p50 / p99 ms | cpu-side ms | present ms | DP / DIP per frame | render thread CPU |
|---|---|---|---|---|---|---|---|---|
| total | 1712 | 45.1 | 18.8 | 21.85 / 39.12 | 21.48 | 0.70 | 24 / 0 | 12 % mean, 22 % max |
| marker 0 | 1413 | 45.1 | – | 21.87 / 39.17 | 21.5 | 0.71 | – / 0 | |
| marker 1 | 299 | 45.6 | – | 21.74 / 37.3 | 21.38 | 0.63 | – / 0 | |

VA used 1,348–1,355 MB (F090); frame ms min 16.66, max 118; 2 scenes/frame; DIP, DPUP, DIPUP, shader constants 0 (F092; hooks verified F091).

- Verdict: **smoke test passed** (proxy start, hub ready before `Direct3DCreate9`, overlay, F9 recording, ingest). Confirms F083 in game (system d3d9). F082 stays a hypothesis: the launcher was not re-run with the fixed hub.
- Performance verdict: **unclear / not applicable**. Menu frames are ~22 ms while the render thread uses only ~12 % CPU → the time outside Present is mostly waiting, not work [Hypothese: menu frame pacing]. No conclusion for battles.
- Follow-ups: F032 verified via module list (F084); `Direct3DCreate9` twice (F087/F088, caller logged from next hub build).

### EXP-001-REAL-A · 2026-10-15 · baseline · REAL8P_EARLY (Skirmish, 8 players with 7 AI, early, no lag)
- capture `20261015_EXP-001-REAL-A_baseline_REAL8P_EARLY`, hub `a8c7ad779e03` (first in-game run of this hub build), troops 0 (field unused), F9 on, F8 after ~1 s, F9 off, 376 frames, 9.5 s. Graphics settings and camera not noted.

| Range | Frames | FPS avg | 1% low | p50 / p99 ms | cpu-side ms | present ms | DIP per frame | render thread CPU |
|---|---|---|---|---|---|---|---|---|
| total | 376 | 39.5 | 17.7 | 24.98 / 52.71 | 25.12 | 0.34 | 1,740 | 57 % mean, 70 % max |
| marker 0 | 22 | 42.5 | – | 24.7 / 57.88 | 25.88 | 0.25 | 1,638 | |
| marker 1 | 354 | 39.4 | – | 24.98 / 52.38 | 25.07 | 0.35 | 1,746 | |

Draw load (F095): triangles ≈ 155,000, SetTexture ≈ 3,540, VS constant calls ≈ 5,250 per frame. VA 1,497 MB constant (F090).

- Verdict: **n/a**. Not a baseline for comparisons: too short (9.5 s), a single F8 marker (marker 0 is only 22 frames), no lag, camera/settings not fixed. Use only as reference for the draw load of a real game state.
- Observation (no inference): even without lag the frame time is ~25 ms with the render thread at 57 % CPU and present 0.3 ms; the menu (EXP-000) showed the same pattern (cpu-side ≫ render CPU %). Cause open.
