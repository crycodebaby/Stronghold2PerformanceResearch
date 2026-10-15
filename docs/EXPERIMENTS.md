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
6. Close the game, then `python -I tools/ingest.py import --recording <timestamp> --exp <EXP> --scenario KNIGHTS --troops <N>` (skill `messung-auswerten`): verifies the recording against its manifest, copies it to `captures/<capture_id>/` (sources stay; delete them yourself), writes silver + `data/index.jsonl`, prints per-marker phases. Before the run `python -I tools/variant.py plan game_speed=<N> experiment=<EXP> scenario=KNIGHTS` (planned values go into the manifest as `planned`); after looking at the game: `ingest.py annotate <capture_id> --game-speed <N>` (user-confirmed).

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
| EXP-001-REAL-B | baseline | REAL_LAG_257: lag save, 217 mounted archers + 20 crossbow + 20 bow, game speed 90 | ingested, first real lag measurement |
| EXP-001-REAL | baseline | further lag saves, protocol "Real save" below | optional |
| EXP-005 | baseline | REAL_LAG_257, hub overhead A/B: `full` vs `min` (protocol "Hub overhead A/B") | prepared, waiting for user run |
| EXP-002 | laa | KNIGHTS N=100 + N=200 | after EXP-001 |
| EXP-003 | dxvk | KNIGHTS N=100 | after EXP-001 |
| EXP-004 | laa+dxvk | KNIGHTS N=100 | if 002/003 help |

### EXP-001-REAL (optional): real lag save
Goal: confirm that KNIGHTS reproduces the lag the user actually sees, not just a synthetic load.
- Input: a save game from a real situation with heavy lag (user, any map). Copy the save into the TEST copy's save folder; note map, troop counts per side (estimate), what happens on screen.
- Protocol: identical to KNIGHTS (variant `baseline`, same graphics settings, V-Sync off, load → wait 10 s → F9, F8 at each phase change, ~30 s per phase, F9). Phases as far as they apply: P0 as loaded (paused if the save starts paused, then unpause), P2 the laggy action, P3 pause during the lag, P4 camera on an empty area during the lag.
- Ingest: `python -I tools/ingest.py import --recording <timestamp> --exp EXP-001-REAL --scenario REAL --troops <estimate per player> --note "<map, situation>"`; set the game speed first (`variant.py plan game_speed=<N>`) or confirm it afterwards (`ingest.py annotate`), otherwise it stays unknown.
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
6. Several recordings in one out folder are fine since D012: each has its own manifest, `latest.json` is only a pointer. `ingest.py import` without `--recording` lists them and touches nothing. (Before D012 `latest.json` described only the newest recording; the extra one of 2026-10-15 was set aside by hand.)

### Protocol "Profiler run" (render thread by module)
Goal: decide whether the render thread's time sits in game code or in the graphics stack (F102) and where the +10.7 ms of the running game come from (F101).
1. `python -I tools/variant.py baseline` (refresh the hub copy), `python -I tools/variant.py sample module`. Same save as EXP-001-REAL-B (LAG_217_Reiter), same graphics settings, V-Sync noted.
2. Run A (sampler off, `variant.py sample off`): load, wait 10 s, F9, then phases with F8 at each start: army in view **paused** 20 s | **running** 30 s | empty corner 15 s. F9 off. Ingest as `EXP-002P-A`.
3. Run B (sampler `module`): identical, ingest as `EXP-002P-B`. B's FPS are only compared with A (overhead check); B's `render_modules` per marker is the result.
4. Read `render_modules` per marker: paused vs running difference in the `exe`/`dragonfly`/`granny2` share = simulation/animation on the render thread; `driver`/`d3d9` share = graphics stack; `system` = waiting.
5. Optional run C with `function` for the top functions of the dominant module.
6. Set one F8 marker per phase and keep markers exact; phases are checked with `analyze_frames.py --timeline`.

### Protocol "Hub overhead A/B" (EXP-005, D011)
Goal: how much of the periodic long frames (F104) and of the frame time is caused by the hub itself (F107)? Compares the hub profile `full` (frame time + counters + polls + overlay, now with the work off the render thread) against `min` (frame time only). This measures **the cost of measuring**, not a game speedup; do not report either as a performance gain.
1. Same save as EXP-001-REAL-B (lag save, game speed 90), same graphics settings, V-Sync/limiter state written down, same camera spots, Steam overlay state unchanged between runs. `python -I tools/variant.py baseline` (refresh the hub copy after the hub is committed and CMake re-run), `variant.py sample off`.
2. Order **A1, B1, B2, A2** (A = `variant.py mode full`, B = `variant.py mode min`; the game reads the profile at start, so restart the game for every run; check `variant.py status`). The repeats give the run-to-run noise.
3. Each run: load the save, wait 10 s, **F9**, then phases with **F8 at the start of each**: army in view **paused** 20 s | **running** 30 s | **empty corner** 15 s, **F9** off, quit the game. In `min` there is no overlay: F9 gives a high tone on start and a low tone on stop (`beep`), and the log says `Recording started/stopped`.
4. After each run read `Stronghold2AnalyseHub.log`: line `Config:` shows the mode, `Recording stopped: ... -> capture OK`. A run with `CAPTURE INCOMPLETE`, dropped frames or write errors is invalid and is repeated. Then `python -I tools/ingest.py import --exp EXP-005-A1 --scenario REAL_LAG_257 --troops 257 --recording <timestamp>` (and B1, B2, A2); the effective switches are read from each manifest, the game speed (90 for this save) set with `variant.py plan game_speed=90` before or `ingest.py annotate` after.
5. `python -I tools/ab_compare.py A1=<id> B1=<id> B2=<id> A2=<id> --marker <N>` per phase (and once without `--marker`). Only `frame_ms`/`present_ms` are compared: `min` has no EndScene timing, so `cpu-side` differs by definition.
6. Reading rules, fixed before the run: an effect of the mode is claimed only if |A − B| (mean of the pairs) exceeds twice the larger of |A1 − A2| and |B1 − B2| and has the same sign in both pairs. "long-frame gaps ~period %" is compared with the random control row: a value far above control in **both** modes means the clock is not (only) the hub; a value that falls to the control level in `min` points to the hub's overlay/counters/poll (then switch them on one by one: `variant.py switch overlay on` etc., one switch per run).
7. Lifecycle check in the same session (once, `min`): F9 on/off three times in a row, F9 within a second of the previous stop, F8 while stopped, END to unload with a recording open. Expected: each recording has its own files, the last one is closed and `latest.json` says `capture_ok: true`.
8. Record the result in the Results section with: runs and order, graphics settings, the `ab_compare` table, the noise estimate, and the verdict per rule 6. Update F107 (`verifiziert`/`widerlegt`) only from this table.

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

### EXP-001-REAL-B · 2026-10-15 · baseline · REAL_LAG_257 (lag save, 257 units, game speed 90)
- capture `20261015_EXP-001-REAL-B_baseline_REAL_LAG_257`, hub `a8c7ad779e03`, 3,734 frames, 88 s. Save: 217 mounted archers + 20 crossbow + 20 bow, medium number of buildings. Graphics settings and V-Sync not noted.
- Actual sequence (from the time line, not from the markers): marker 1 set at once and the game paused → **paused ~25 s** (5–25 s) | unpaused, camera on an empty minimap corner (marker 2, ~25–60 s) | back to the army (marker 3, ~60–70 s) | army marching (marker 4, ~70–88 s). The markers are hand-set and do not sit on the phase borders; `ingest.py` therefore writes `timeline.md` (5 s windows). Phase 0 "running, army in view" is only the first ~3 s.

| Situation (window) | FPS | frame ms (p50) | present ms | DIP | triangles | SetTexture | render thread CPU |
|---|---|---|---|---|---|---|---|
| army, paused (8–24 s) | 37.1 | 24.5 (mean 26.9) | 0.24 | 2,467 | 517,000 | 4,410 | 98 % |
| empty corner, running (33–57 s) | 57.7 | 16.67 (pinned) | 6.46 | 567 | 53,000 | 1,980 | 67 % |
| army, running/marching (66–88 s) | 26.6 | 34.6 (mean 37.6) | 0.26 | 2,690 | 520,000 | 5,020 | 98 % |

Whole recording: 42.4 FPS avg, 1 % low 12.8, p99 68.5 ms; VA 1,568–1,573 MB. Findings F096–F102.

- **Observation:** with the army in view the render thread is at 98 % in both the paused and the running state; running costs ≈ +10.7 ms per frame (26.9 → 37.6 ms) at nearly the same draw load; GPU wait (`present`) stays at 0.25 ms. In the empty corner the frame is pinned at 16.67 ms with `present` 6.5 ms.
- Verdict per phase (Interpretation key; inference = **Hypothese**):
  - paused, army: **render-side CPU-bound** (render thread 98 %, `present` low); module split open (F102).
  - empty corner: **unclear / capped** (V-Sync or 60 FPS limiter, F100): no cost information.
  - running, army: **CPU-bound on the render thread**; the extra ≈ 10.7 ms vs pause are probably simulation on that thread (F101, Hypothese). Neither GPU-bound nor a pure draw-call limit explains the difference.
- Not yet answered: how much of the paused 26.9 ms is game code vs graphics driver → sampling profiler (design/SAMPLING_PROFILER.md).
- Limits: one run, hand-set markers, unknown V-Sync/graphics settings, camera position differs between phases, "paused" identified from constant counters.
