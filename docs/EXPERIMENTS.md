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
1. `python -I tools/variant.py <variant>`; start Steam; run `SH2Launcher.exe "…\Stronghold 2 - TEST\Stronghold2.exe"`.
2. Fixed settings: same resolution/graphics preset each run (note them), V-Sync OFF, window mode noted.
3. Load save → wait 10 s → **F9** (record on).
4. At each phase start press **F8** (marker). ~30 s per phase.
5. **F9** (record off). Hub writes CSVs + `latest.json` to `TEST\SH2Perf_out\` (launcher `--out` overrides).
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
| VA used near 2,000 MB / crash | address space (LAA helps) |

## Planned
| ID | Variant | Scenario | Status |
|---|---|---|---|
| EXP-001 | baseline | KNIGHTS N=100, P0–P4 | waiting for user run |
| EXP-001b | baseline | KNIGHTS N=25/50/200, P2 | waiting |
| EXP-002 | laa | KNIGHTS N=100 + N=200 | after EXP-001 |
| EXP-003 | dxvk | KNIGHTS N=100 | after EXP-001 |
| EXP-004 | laa+dxvk | KNIGHTS N=100 | if 002/003 help |

## Results
(none yet)
