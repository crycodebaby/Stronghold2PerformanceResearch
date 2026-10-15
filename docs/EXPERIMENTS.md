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
| EXP-006 | baseline, full profile | REAL_LAG_257, army view running vs paused, sampler off/module A1–B1–B2–A2 (protocol "EXP-006" below) | done 2026-10-15, 4 valid runs + pilot (results below) |
| EXP-007 | baseline, full profile | REAL_LAG_257, same protocol as EXP-006, sampler off/function A1–F1–F2–A2 (protocol "EXP-007" below) | done 2026-10-15, 4 valid runs + 2 excluded attempts (results below) |
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

### Protocol "EXP-006" (army view, running vs paused, sampler off/on) — fixed 2026-10-15 before any run
Supersedes "Profiler run" below for the module split. Goal: module distribution of the busy render thread with the army in view at speed 90, running vs paused, and the sampler's own effect from repeated off/on runs. Not a performance-gain test.
- **Fixed for all four runs**: save LAG_217_Reiter (REAL_LAG_257), loaded fresh after a game start; speed 90 (user checks it per run); camera as after loading, untouched, mouse in the screen centre; hub `e822e7f19019` (DLL `591e6375…`), profile `full` (frame time, counters, poll, ImGui overlay on; beep off), set explicitly in `SH2Proxy.ini`; graphics = `Documents\Stronghold 2\Stronghold2.GraphicsSettings.xml` sha256 `de0d6ea7…` (1920×1080 @ 144 Hz fullscreen, multiSamples 3, anisotropy 4, gfxLevel 4, shader 3.0, real-time + ground shadows, reflections, bloom, grass, particles, enhanced water, normal maps on; arrow trails, early culling off); V-Sync/limiter: no setting in that file, unknown (F100); Steam overlay: read per run from the module list in the hub log (loaded in EXP-INGAME). The settings file hash is re-checked after the runs.
- **Only change between runs**: `variant.py sample off` (A) / `sample module` (B, interval default 10 ms). Order **A1, B1, B2, A2**, game restarted per run (the mode is read at hub start). `variant.py plan experiment=EXP-006-<run>` per run, so the manifest names the run.
- **Per run (marker = value of the F8 counter, the session starts at 0)**: load, wait 10 s → **F9** → marker 0 *settle* ≈ 5 s (discarded) → **F8** → marker 1 *running* 20 s → **F8** → marker 2 *transition*: press the game's pause, wait ≈ 3 s (discarded) → **F8** → marker 3 *paused* 20 s → **F9**, wait until the overlay no longer shows recording, quit. F8 only sets markers; the pause is the game's own key. Transitions therefore sit in markers 0 and 2 and never in 1 or 3, because samples carry only a marker, no time.
- **Validity (per run, checked before the next run)**: manifest `finalized`, `capture_ok`, 0 dropped / lost / write errors; exactly 3 markers; plan id and sampler mode as planned; markers 1 and 3 ≥ 15 s each; user confirms speed 90 and the pause in marker 3 (`annotate --phase-paused 1=false 3=true`, marker 0/2 left unknown); scene check: DIP and primitives per frame of marker 1 and 3 within ±10 % of A1 (same view). B runs: `Sampler: … samples (… failed, … dropped)` line in the log; samples per marker ÷ marker duration within 85–105 /s (10 ms nominal, `Sleep` granularity), otherwise lost samples are reported.
- **Sampler effect rule** (as EXP-005 rule 6): per marker 1 and 3, mean and p50 `frame_ms` (`ab_compare.py A1= B1= B2= A2= --marker N`). An effect is claimed only if |mean(B) − mean(A)| > 2 × max(|A1 − A2|, |B1 − B2|) with the same sign in both pairs. With an effect, frame times of B runs are reported as "under sampling" only; without one, the bound "below ≈ X ms noise" is stated, not "no effect".
- **Meaning of a module share** (fixed in advance): samples of the render thread in module M ÷ all samples of that marker in that run (unknown `?` included in the denominator, failed suspensions reported separately and not included). A sample is the **user-mode instruction pointer** at a wall-clock instant ≈ every 10.5 ms, taken whether or not the thread was on a CPU: a thread waiting or in the kernel shows its ntdll/win32u/driver stub. It is a share of wall time, equal to a CPU-time share only as far as the thread is busy (render thread CPU % from `threads.csv` is quoted next to it). Game CRT (`msvcr*`/`msvcp*`) is shown on its own, not inside "system". Derived "ms per frame in M" = share × mean frame ms of the same run and marker, labelled as an estimate. Module names are not translated into "rendering", "simulation" or "animation".

### Protocol "EXP-007" (function hotspots, sampler off/function) — fixed 2026-10-15 before any run
Goal: turn F127/F128 into ≤ 5 function candidates: (A) granny2.dll work present running and paused, (B) Stronghold2.exe functions whose cost grows when running. No engine change.
- **Identical to protocol "EXP-006"** (save, speed 90, untouched camera, hub `e822e7f19019` profile `full`, graphics file `de0d6ea7…`, markers 0 settle / 1 running 20 s / 2 transition with the pause / 3 paused 20 s, validity rules, frozen-counter check). Only change: `variant.py sample off` (A) / `sample function` (F), order **A1, F1, F2, A2**, plan id `EXP-007-<run>`. The sampler effect of EXP-006 (F125) is not carried over: A vs F is tested again with the EXP-006 rule (mean and p50 `frame_ms`, markers 1 and 3).
- **Function mode as built** (`core/sampler.cpp`, F122): same suspend/read/resume per sample as module mode; the key additionally holds `rva = Eip − module base` (32 bit), so one table entry per distinct (marker, module, instruction address) instead of per module; `?` rows keep the absolute Eip. Losses counted as in module mode (`failed`, `dropped` at 500,000 keys); the larger table is filled on the sampler thread after the resume. Ghidra address = image base + rva (exe 0x400000 although it loads relocated, F006; granny2 0x50000000).
- **Function boundaries**: Ghidra function bodies (`ghidra_scripts/ExportFunctions.java`, all functions with entry, body range, name and name source) for `Stronghold2.exe` (existing project) and `granny2.dll` (sha256 `94d56fd7…`, imported into the Ghidra project for this order). Each sample address is counted for the function whose **body contains it**; addresses outside every body stay "unresolved <module>+rva", grouped per 4 KiB page for display only, never named. A preceding granny2 export is a search hint, not an identity.
- **Quantities per run and marker**: samples n, rate, failed/dropped, `?`; function share = samples in function ÷ n; estimated ms per frame = share × mean frame ms of the same run and marker (estimate under sampling). Flat samples: location of execution only, no call path, no inclusive time.
- **Candidate rules (fixed before the data)**: (A) granny2: functions ranked by mean estimated ms over F1/F2 and both states; candidate if ≥ 0.5 ms in each of the four (run, state) cells. (B) exe: Δ = running ms − paused ms per run; candidate if Δ > 0 in F1 and F2, mean Δ ≥ 0.3 ms, and the smaller Δ ≥ half the larger. At most 5 candidates in total, ordered by estimated ms (A) and Δ (B); 1–3 analysed in depth (callers/callees, loops, data access, strings/types/exports), identity, task description and runtime relevance rated separately.

### Protocol "Profiler run" (render thread by module)
Superseded by protocol "EXP-006" above (transition markers, A1–B1–B2–A2). Goal: decide whether the render thread's time sits in game code or in the graphics stack (F102) and where the +10.7 ms of the running game come from (F101).
1. `python -I tools/variant.py baseline` (refresh the hub copy), `python -I tools/variant.py sample module`. Same save as EXP-001-REAL-B (LAG_217_Reiter), same graphics settings, V-Sync noted.
2. Run A (sampler off, `variant.py sample off`): load, wait 10 s, F9, then phases with F8 at each start: army in view **paused** 20 s | **running** 30 s | empty corner 15 s. F9 off. Ingest as `EXP-002P-A`.
3. Run B (sampler `module`): identical, ingest as `EXP-002P-B`. B's FPS are only compared with A (overhead check); B's `render_modules` per marker is the result.
4. Read `render_modules` per marker: paused vs running difference in the `exe`/`dragonfly`/`granny2` share = simulation/animation on the render thread; `driver`/`d3d9` share = graphics stack; `system` = waiting.
5. Optional run C with `function` for the top functions of the dominant module.
6. Set one F8 marker per phase and keep markers exact; phases are checked with `analyze_frames.py --timeline`.

### Protocol "Hub overhead A/B" (EXP-005, D011)
Goal: how much of the periodic long frames (F104) and of the frame time is caused by the hub itself (F107)? Compares the hub profile `full` (frame time + counters + polls + overlay, now with the work off the render thread) against `min` (frame time only). This measures **the cost of measuring**, not a game speedup; do not report either as a performance gain.
1. Same save as EXP-001-REAL-B (lag save, game speed 90), same graphics settings, V-Sync/limiter state written down, same camera spots, Steam overlay state unchanged between runs. `python -I tools/variant.py baseline` (refresh the hub copy after the hub is committed and CMake re-run), `variant.py sample off`.
   **Checklist before every run, identical for all runs** (the tools do not verify any of this; write it into the result): (a) the same save game, loaded fresh, not a continued session; (b) the same camera position and zoom for each phase; (c) numeric game speed set in the game and stated: `variant.py plan game_speed=<N>` before, `ingest.py annotate <id> --game-speed <N>` after (what you saw); pause state per F8 phase, `annotate --phase-paused <marker>=true|false`; (d) graphics settings and V-Sync / frame limiter noted and unchanged; (e) Steam overlay on or off, unchanged; (f) nothing else heavy running. `usable as reference` in the ingest output does not cover any of (a)-(f).
2. Order **A1, B1, B2, A2** (A = `variant.py mode full`, B = `variant.py mode min`; the game reads the profile at start, so restart the game for every run; check `variant.py status`). The repeats give the run-to-run noise.
3. Each run: load the save, wait 10 s, **F9**, then phases with **F8 at the start of each**: army in view **paused** 20 s | **running** 30 s | **empty corner** 15 s, **F9** off, wait for `Recording stopped … manifest published` in the log, only then quit the game (quitting while recording leaves an interrupted manifest, F117). In `min` there is no overlay: F9 gives a high tone on start and a low tone on stop (`beep`), and the log says `Recording started/stopped`.
4. After each run read `Stronghold2AnalyseHub.log`: line `Config:` shows the mode, `Recording stopped: ... -> capture OK`. A run with `CAPTURE INCOMPLETE`, dropped frames or write errors is invalid and is repeated. Then `python -I tools/ingest.py import --exp EXP-005-A1 --scenario REAL_LAG_257 --troops 257 --recording <timestamp>` (and B1, B2, A2); the effective switches are read from each manifest, the game speed (90 for this save) set with `variant.py plan game_speed=90` before or `ingest.py annotate` after.
5. `python -I tools/ab_compare.py A1=<id> B1=<id> B2=<id> A2=<id> --marker <N>` per phase (and once without `--marker`). Only `frame_ms`/`present_ms` are compared: `min` has no EndScene timing, so `cpu-side` differs by definition.
6. Reading rules, fixed before the run: an effect of the mode is claimed only if |A − B| (mean of the pairs) exceeds twice the larger of |A1 − A2| and |B1 − B2| and has the same sign in both pairs. "long-frame gaps ~period %" is compared with the random control row: a value far above control in **both** modes means the clock is not (only) the hub; a value that falls to the control level in `min` points to the hub's overlay/counters/poll (then switch them on one by one: `variant.py switch overlay on` etc., one switch per run).
7. Lifecycle check in the same session (once, `min`): F9 on/off three times in a row, F9 within a second of the previous stop, F8 while stopped, END (deactivates the hub; the DLL stays loaded) with a recording open. Expected: each recording has its own files, the last one is closed and `latest.json` says `capture_ok: true`.
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

### EXP-INGAME · 2026-10-15 · first real-game acceptance of hub e822e7f
- User loaded LAG_217_Reiter and followed the acceptance instructions; speed **90**, explicitly confirmed after capture; no pause action was requested. Phase pause annotations are user-confirmed false. F8 markers in this check are labels only, not pause or movement phases.
- All three manifests finalized with user_toggle, full mode, sampler off, 0 dropped frames / write losses / errors; session exe and hub hashes match the prepared build. Imported and verified; source files retained. Logs confirm Device reset handled at 07:20:35 and complete END deactivation at 07:21:04; user confirms overlay returned and game continued.

| capture_id | frames | duration s | avg FPS | 1% low FPS | p50 / p99 ms | max ms | render CPU % |
|---|---|---|---|---|---|---|---|
| rec-20261015T051911Z-00d7566d | 873 | 29.33 | 29.8 | 15.3 | 32.58 / 48.79 | 142.50 | 99 |
| rec-20261015T051954Z-011b26f7 | 399 | 13.23 | 30.2 | 19.1 | 32.18 / 47.64 | 53.61 | 99 |
| rec-20261015T052024Z-f05fa15b (Alt-Tab) | 514 | 24.72 | 20.8 | 0.6 | 32.48 / 53.56 | 7561.07 | 89 |

- First two captures: Present mean 0.24 ms, DIP 2549 / 2521, primitives 524164 / 524890, SetTexture 4721 / 4768, VS constant calls 6607 / 6546 per frame. Capture writer TID 47876 averages 7% of one core; offloading does not mean zero overhead. No capture samples CSV exists.
- Alt-Tab: 7561.073 ms Present-to-Present interval at t=10.5816 s; Present itself 0.664 ms for that row. Desktop transition/device reset is present in this recording; aggregate FPS/low is unsuitable for normal gameplay comparison. No GPU execution time is measured.
- Long-frame periodicity (>1.5 x median, ab_compare): first run 9 long frames, 25% of consecutive gaps near 1 s; second run 4 long frames, 0%. Too few events and no paired old/new control to decide F107. One 142.504 ms frame in run 1, despite no user-noticed hitch.
- Verdict for all marker phases: **unclear cause**. First two captures strongly support one busy render thread (99%); no paused/look-away/march intervention or module/function sampling, so no split of rendering/simulation/animation. Low Present is not a GPU exclusion.
- Acceptance value: real-game recording, repeat recording, manifest integrity, Alt-Tab/reset and END-without-recording verified for this session. END during recording and exit during recording remain untested in the real game. Startup/stop overhead is not bounded by these CSVs (no post-stop frame stream).
- No benchmark suitability release: settings/camera are not standardized; same-session short captures are not independent benchmark repeats. REAL-B is historical context, not a controlled old/new comparison. Next: fixed-camera pause/run comparison plus sampler-off/on module profiling, with measurement overhead checked.

### EXP-006 · 2026-10-15 · baseline, full profile · REAL_LAG_257 army view running vs paused, sampler off/module
- **A0 pilot** `rec-20261015T062849Z-735e2089` (manifest plan id `EXP-006-A1`, relabelled `EXP-006-A0` by annotation): sampler off, capture OK, 2,047 frames, 60.8 s, 0 dropped/lost, render thread 98 %. **Not protocol-conform**: only 2 F8 markers (+16 s, +39 s); frozen counters (primitives exactly 526,421 per frame in 18–38 s) show marker 1 = paused, markers 0 and 2 = running, so the pause transitions fall inside measured markers. Usable only as time-windowed frame data, never for the A/B rule; A1 is repeated with the same settings.
- Pilot frame times (2 s windows, transitions cut, sampler off): running 0–16 s mean 32.1–33.1 ms; paused 18–38 s mean 25.1–26.0 ms; running again 40–60 s mean 32.0–34.5 ms; DIP ≈ 2,490–2,560 in all windows. Observation only (one run): paused vs running ≈ 7 ms per frame, smaller than the 10.7 ms of REAL-B (other hub build, different camera/timing).
- **Runs (all valid per the protocol rules)**, user confirms speed 90 for each (annotated), hub `e822e7f19019` full profile, Steam overlay loaded (`gameoverlayrenderer.dll` in every session), graphics settings file hash unchanged after the runs (`de0d6ea7…`). Pause = frozen counters (1 distinct primitive count) throughout marker 3 in every run; the pause key fell inside transition marker 2 every time (A1 ≈ 13 s after F8, others ≈ 1 s). Scene check: DIP of markers 1/3 within 2,492–2,608, i.e. ≤ 5 % from A1.

| Run | capture_id | sample | m1 running s / frames | m3 paused s / frames | samples (failed, dropped) | rate m1 / m3 | render CPU m1 / m3 |
|---|---|---|---|---|---|---|---|
| A1 | rec-20261015T063324Z-11f9f002 | off | 19.9 / 611 | 23.4 / 925 | – | – | 97.9 / 98.0 % |
| B1 | rec-20261015T063727Z-a0c4873e | module | 18.2 / 542 | 21.5 / 825 | 5,018 (0, 0) | 94.9 / 95.0 /s | 98.0 / 98.3 % |
| B2 | rec-20261015T064050Z-f3b36a54 | module | 20.1 / 597 | 21.2 / 802 | 5,060 (0, 0) | 94.9 / 94.9 /s | 98.2 / 97.3 % |
| A2 | rec-20261015T064341Z-dee7161d | off | 19.8 / 598 | 21.1 / 848 | – | – | 98.0 / 97.9 % |

- **Frame times and sampler effect** (rule fixed in advance; mean from the frames CSV, p50 from `ab_compare.py --marker`):

| State | metric | A1 / A2 | B1 / B2 | B − A (pair means) | 2 × max repeat deviation | verdict |
|---|---|---|---|---|---|---|
| running (m1) | mean ms | 32.63 / 33.04 | 33.64 / 33.73 | +0.85 | 0.82 | effect (at the threshold) |
| running (m1) | p50 ms | 31.57 / 31.89 | 32.20 / 32.52 | +0.63 | 0.66 | not claimed |
| paused (m3) | mean ms | 25.31 / 24.91 | 26.02 / 26.46 | +1.13 | 0.88 | effect |
| paused (m3) | p50 ms | 24.19 / 23.73 | 25.00 / 25.42 | +1.27 | 0.96 | effect |

  Sampling at 10 ms makes frames ≈ 0.6–1.3 ms (≈ 2–5 %) slower, same sign in both pairs. B frame times are therefore "under sampling" and not used as performance values; A runs are. Present stays 0.23–0.24 ms in all runs. Long-frame counts per marker (4–12) are too few for the period test.
- **Running vs paused without sampler (A1, A2)**: mean 32.8 vs 25.1 ms → running costs **+7.7 ms per frame** (p50 +7.8 ms), render thread ≈ 98 % in both states, same draw load (DIP ≈ 2,500, ≈ 525,000 primitives).
- **Module distribution of the render thread (B1, B2)**. Share = samples of the render thread in the module ÷ all samples of that run and marker (n = 1,731 / 1,910 running, 2,038 / 2,014 paused; `?` included, 0 failed). A sample is the user-mode instruction pointer at a wall-clock instant ≈ every 10.5 ms; because the thread is ≈ 98 % busy, wall share ≈ CPU share within ≈ 2 points. "ms" = share × mean frame time of the same run and marker (an estimate under sampling), mean of B1 and B2. Statistical spread of a 30 % share at n ≈ 1,800: ± 1.1 points (± 0.4 ms).

| Module | running % B1 / B2 | paused % B1 / B2 | running ms | paused ms | running − paused ms (B1, B2) |
|---|---|---|---|---|---|
| granny2.dll | 34.5 / 32.0 | 39.4 / 40.5 | 11.20 | 10.47 | +0.73 (+1.36, +0.10) |
| Stronghold2.exe | 29.3 / 28.9 | 17.0 / 15.9 | 9.80 | 4.32 | **+5.48 (+5.42, +5.54)** |
| d3dx9_27.dll | 10.7 / 10.6 | 15.0 / 13.9 | 3.60 | 3.79 | −0.19 |
| d3d9.dll | 9.2 / 9.5 | 12.0 / 12.9 | 3.14 | 3.26 | −0.12 |
| ntdll / win32u / kernel32 / KERNELBASE | 7.0 / 7.1 | 6.3 / 8.0 | 2.39 | 1.87 | +0.51 (+0.74, +0.29) |
| nvd3dum.dll (NVIDIA user-mode driver) | 3.0 / 3.5 | 3.5 / 3.8 | 1.09 | 0.97 | +0.12 |
| CRT msvcr100 + msvcrt | 3.2 / 3.5 | 1.2 / 1.3 | 1.12 | 0.33 | +0.79 (+0.75, +0.82) |
| Steam overlay + steamclient | 0.9 / 1.4 | 2.2 / 1.3 | 0.38 | 0.46 | −0.08 |
| dragonfly.dll | 1.0 / 1.5 | 1.2 / 0.9 | 0.42 | 0.28 | +0.14 |
| binkw32.dll | 0.5 / 1.0 | 0.9 / 0.8 | 0.26 | 0.23 | +0.03 |
| hub | 0.3 / 0.8 | 0.8 / 0.2 | 0.20 | 0.13 | +0.07 |
| unknown `?` + other | 0.3 / 0.3 | 0.4 / 0.4 | 0.09 | 0.13 | −0.04 |

- **Observation**: of the ≈ 7.4 ms running − paused difference in the sampled runs, ≈ 5.5 ms are samples in `Stronghold2.exe` (reproduced to ± 0.06 ms in B1/B2), ≈ 0.8 ms in the CRT and ≈ 0.5 ms in ntdll; `granny2.dll` is the largest block in **both** states (≈ 10.5–11.2 ms, 32–41 %) and its running − paused change is not reproducible (+1.36 vs +0.10 ms). Graphics stack (d3dx9_27 + d3d9 + nvd3dum) ≈ 7.8–8.0 ms in both states. `dragonfly.dll` and `dxrenderer.dll` ≈ 1 % or less.
- **Not claimed**: what the exe or granny2 code does (module names only; no "rendering/simulation/animation" mapping), GPU execution time (not measured; low Present is not a GPU exclusion), effect of other threads (only the render thread is sampled), and any performance gain.
- Limits: one save and camera view, one machine, 4 runs of ≈ 20 s per state; frame times under sampling are biased (+2–5 %); module shares come only from sampled runs; samples carry no time, so the result depends on the transitions staying in markers 0/2 (checked with frozen counters); V-Sync/limiter state unknown (no effect visible: frames 24–34 ms, far from a 60 FPS cap); `system` group of `samples.py` would mix CRT and waits (F124), so the table is per module.

### EXP-007 · 2026-10-15 · baseline, full profile · REAL_LAG_257 army view, sampler off/function
- **Runs** (protocol "EXP-007"; all valid ones have speed 90 user-confirmed + annotated, pause = frozen counters through all of marker 3, no pause in the last 20 frames of marker 1, scene DIP 2,445–2,625):

| Run | capture_id | sample | m1 running s | m3 paused s | samples (failed, dropped), rows | rate m1 / m3 |
|---|---|---|---|---|---|---|
| A1 | rec-20261015T073119Z-a7148666 | off | 19.8 | 18.8 | – | – |
| F1 | rec-20261015T073402Z-bf15a427 | function | 22.1 | 21.8 | 5,595 (0, 0), 3,187 rows | 94.9 / 95.0 /s |
| F2 | rec-20261015T073915Z-387fcc8e | function | 18.4 | 22.8 | 5,158 (0, 0), 2,886 rows | 95.1 / 95.0 /s |
| A2 | rec-20261015T074131Z-82c45e9a | off | 19.1 | 26.2 | – | – |

  Excluded (imported, labelled, never used): `rec-20261015T072526Z-f1d856a1` (A0: Alt-Tab, camera moved, marker 3 another view, DIP 2,799), `rec-20261015T073630Z-6e960aca` + `rec-20261015T073721Z-e6a4bc3e` (F2 attempt out of sequence). Unknown `?` samples: 0–3 per run and state.
- **Sampler effect, function mode** (EXP-006 rule): running mean A 34.98 / 33.37, F 33.83 / 34.31 → F − A −0.11 ms (threshold 3.22); p50 −0.23 (4.78); paused mean A 25.35 / 25.62, F 25.58 / 26.43 → +0.52 (1.70); p50 +0.42 (1.26). **No effect claimed**, but only because A1/A2 differ by 1.6 ms running: an effect below ≈ 1.3 ms (paused) / 3.2 ms (running) is not excluded, and EXP-006 measured ≈ 1 ms for module mode (F125). F frame times stay "under sampling". Without sampler, running − paused = 9.6 / 7.8 ms (A1 / A2).
- **Function boundaries**: Ghidra bodies via `ExportFunctions.java` (exe 40,216 functions, csv sha256 prefix `311DC66F`; granny2.dll sha256 `94d56fd7…` newly imported, 2,155 functions after 3 added, prefix `F124B38D`), `tools/funcsamples.py`. First pass left ≈ 1.2–1.5 ms per frame of granny2 samples outside every body; three code entries reached only through data pointers (`FUN_50015750` referenced from `FUN_500156F0`, `FUN_50044410` / `FUN_50044630` from a pointer table at 0x50066CA4/CC8) were created as functions (`CreateFunctionsAt.java`); remaining unresolved granny2 0.26–0.32 ms (one unreferenced block 0x5001C7C4–0x5001C9F3 and a switch case of `FUN_50003EF0`), exe 0.02–0.06 ms.
- **Module totals in function mode** (estimate = share × mean frame ms, same run/marker): granny2 running 11.34 / 12.18, paused 10.48 / 10.86 ms; exe running 10.52 / 10.67, paused 4.34 / 4.37 ms → exe Δ +6.18 / +6.30 ms (consistent with F127/F128).
- **Candidates by the fixed rules** (F1 / F2, est. ms per frame under sampling, samples in brackets):

| # | Module + address | Rule | running F1 / F2 | paused F1 / F2 | Identity | Analysis evidence |
|---|---|---|---|---|---|---|
| A1 | granny2 `FUN_50008810` | A | 3.61 (224) / 4.93 (252) | 4.39 (356) / 4.46 (366) | Ghidra body 0x50008810–0x50008A95 (646 B); only caller `SseDeformPWNT3432I` (0x500092E0, named from its own assert string) | 187 instructions, mostly SSE (`mulps` 32, `shufps` 31, `addps` 26), `movntps` stores, one loop; reached via the deformer table filled in `FUN_5000BFD0` ← `FUN_50021EB0` ("granny_deformers.cpp") ← `GrannyNewMeshDeformer`; executed via `GrannyDeformVertices` → `FUN_50033D40` indirect `call [ecx+8]/[ecx+4]`. The exe calls `GrannyDeformVertices` from `FUN_0076B210` and `FUN_0078C9E0` |
| A2 | granny2 `FUN_500166E0` | A | 1.18 (73) / 1.37 (70) | 1.16 (94) / 1.32 (108) | body 274 B; only static caller the export `GrannySampleBSpline2x4n` | one basic block, x87 only (`fld` 29, `fmul` 23); the export is not imported by the exe and has no internal static caller → reached indirectly, path not resolved |
| A3 | granny2 `FUN_50017600` | A | 0.87 (54) / 0.92 (47) | 0.67 (54) / 0.79 (65) | body 148 B; callers `GrannyFindKnot` export, `FUN_500176A0`, `FUN_500186A0`, switch case code of `FUN_50003EF0` | 2 loops with float compares (`fcomp`/`fnstsw`) |
| B1 | exe `FUN_004E3530` | B | Δ +0.21 (13) / +0.41 (21), 0 samples paused | – | body 160 B; callers `FUN_004E35D0`, `FUN_004E6570` (vf00 of 73 unit classes, `sym.py`) | x87 helper, no loop (`fabs`, `fdivp`, `fcom`) |

  Below the thresholds: `FUN_50015750` (0.45–0.72 ms), `FUN_5002FF60`, `FUN_50002640`.
- **Observation**: the largest single function is the SSE deform loop A1 (≈ 11–17 % of render-thread samples, ≈ 3.6–4.9 ms), equally present running and paused; A2/A3 (curve helpers) add ≈ 1.8–2.3 ms and are also present paused. The exe calls `GrannySetModelClock` and `GrannySampleModelAnimationsAccelerated` from `FUN_0078E4D0`, which was sampled running (30 / 30) and paused (33 / 33). The exe's running-only cost is **flat**: 146–169 functions with samples only when running, the top 10 cover 2.1–2.9 of 6.2–6.3 ms; by 64 KiB code region 0x770000–0x79FFFF holds +3.3–3.8 ms (the same region as the exe's Granny call sites), 0x4E0000–0x4FFFFF +0.9–1.5 ms (S2Actor/Soldier vfuncs, e.g. `S2Actor::vf19`, `Soldier::vf19`, `GlowWorm::Actor::vf08`). No exe function reaches 0.5 ms Δ; only B1 meets rule B.
- Repeat deviation: A1 running 3.61 vs 4.93 ms (Poisson spread of 224 samples ≈ ± 7 %) is larger than counting noise → the running scene differs between runs (units move); the paused values agree (4.39 / 4.46).
- **Not shown**: inclusive time or call paths (flat samples); that work in paused frames is redundant (needs inputs per frame, see next step); any name beyond FUNCTIONS.md; a GPU/driver statement.

