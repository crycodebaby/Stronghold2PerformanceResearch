# STATE

> Kurzfassung: Aktueller Stand, offene Aufgaben, nächster Schritt. Immer zuerst lesen.

Updated: 2026-10-15 · Phase: 1 (first real lag measurement EXP-001-REAL-B done; sampling profiler step 1 built; measurement path moved off the render thread (D011), per-recording manifest + safe import (D012) — built and tested without the game (stand-in end to end OK), **not yet run in Stronghold 2, hub changes uncommitted**)

## Done
- [x] Tools installed + verified (SETUP.md); REA doctor: Ghidra `available`, registration `aligned`; MCP tools loaded
- [x] Checks 3a–3d → FINDINGS F030–F033, F041–F050, docs/FORMATS/*
- [x] Hub `perf-metrics` @ `a8c7ad779e03`, built and copied to TEST: counters, timings, histogram, CSV, thread CPU, module dump, output dir, `latest.json` with hub commit, `SH2HUB_AUTORECORD`, caller chain of `Direct3DCreate9` in `SH2Proxy.log`. Runs in game (EXP-000 with `7a9e511`, EXP-001-REAL-A with `a8c7ad779e03`)
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
- [x] EXP-001-REAL-A ingested (`20261015_EXP-001-REAL-A_baseline_REAL8P_EARLY`, 8 players, no lag, 9.5 s): reference only, verdict n/a; draw load per frame in a real game F095, hub counters work in real game (F091), `Direct3DCreate9` callers F088 partly verified, VA 1,497 MB F090; hub `a8c7ad779e03` now also run in game
- [x] EXPERIMENTS.md: protocol "Real save" (fixed camera, R0 rest / R1 pause / R2 look-away) + hint to save the game on a clear FPS drop
- [x] EXP-001-REAL-B ingested (`20261015_EXP-001-REAL-B_baseline_REAL_LAG_257`, lag save 257 units, speed 90, 88 s): army in view → render thread 98 %, paused 26.9 ms vs running 37.6 ms (+10.7 ms), empty corner pinned at 16.67 ms (F096–F102). Interpretations are hypotheses (F100–F102)
- [x] `ingest.py` robust: several recordings in `SH2Perf_out` → lists them, needs `--recording <timestamp>`, copies first and deletes sources last, never moves foreign files (`test_ingest.py`); writes `timeline.md`; `analyze_frames.py --timeline` (5 s windows)
- [x] Sampling profiler step 1 (D010): hub `core/sampler.cpp` counts the render thread per module (`function` mode adds rva), off by default; `variant.py sample`, `tools/samples.py`, `render_modules` in the index line; tests `sampler_test.exe` + `standin_d3d9.exe` OK (F103). Hub rebuilt and copied to TEST (`sample=off`); not yet run in Stronghold 2
- [x] dxrenderer.dll classified: Dragonfly D3D9 render plugin, structure only (F093/F094)

- [x] Measurement foundation (D011), hub branch `perf-metrics`, working tree (uncommitted, builds as `<commit>-dirty`): `core/config` (4 independent switches + `beep`, `full`/`min` profile), `core/capture` (wait-free ring of 8,192 frames, capture thread does CSV/files/polls/start-stop, drops + open/write errors reported), `metrics.cpp` no longer touches files or system queries on the render thread, hooks installed per switch (all off = no hook). CSV unchanged, `latest.json` `capture_version: 2` + `modes` + health (docs/FORMATS/HUB_CAPTURE.md). Tests OK: `capture_test.exe` (F108), stand-in per mode (F109), `test_ingest` (7), `test_variant` (12), `test_ab_compare` (6), lint. `variant.py mode|switch`, `ingest.py` stores unmeasured metrics as null and flags incomplete captures, `tools/ab_compare.py`, protocol "Hub overhead A/B" (EXP-005). README for all folders: `../README.md`
- [x] Long-frame clock: observed in EXP-001-REAL-B (F104), reproduced with the old hub in a stand-in and absent with the new build (F106); cause in the game stays a hypothesis (F107)

- [x] Provenance + safe import (D012, work order H1–H3): hub writes `<stem>_manifest.json` per recording (id, plan, speed/pause with origin, session software SHA-256, effective switches with source, file hashes, status `recording` → `finalized` after the files are closed), `latest.json` = pointer (`capture_version 3`); `core/provenance` (background hashing), `core/manifest`; `variant.py plan` + `SH2Prepared.json`; `ingest.py list|import|annotate|verify|rebuild` (verify → stage → atomic commit, sources never deleted, conflict on same id + other content, legacy = unverified/unknown); silver derived from bronze + `data/annotations/` with tool version; `ab_compare.py` warns on differing/unknown speed. Tests: `capture_test.exe` (11 groups), `test_import_safety` (45), `test_ingest` (9), `test_variant` (15), `test_ab_compare` (10), `e2e_standin.py`, lint (F110–F113, FORMATS/CAPTURE_MANIFEST.md). The 3 existing captures were re-derived (`rebuild --write`): bronze byte-identical, silver now `legacy`/`unknown`

## Open tasks (ordered)
00. USER/next session: review the hub diff (D011 + D012), **commit** on `perf-metrics`, re-run `cmake -S . -B build -A Win32` (commit id is baked in at configure time; until then recordings say `-dirty`), rebuild, `variant.py baseline` (writes `SH2Prepared.json`); `variant.py plan game_speed=<N> experiment=<EXP>` before each run; then in game: lifecycle check (**also D012**: after F9 on/off `SH2Perf_out` holds `*_manifest.json` with `status: finalized`, `ingest.py list` shows it, `ingest.py import --recording <ts>` runs through, a killed game leaves a manifest at `recording`, hashing at hub load/stop does not show as a long frame) + EXP-005 A/B (EXPERIMENTS.md "Hub overhead A/B"), order A1 B1 B2 A2 on the lag save. Until then no performance statement about the new build is allowed
0. USER: profiler runs on the lag save LAG_217_Reiter (EXPERIMENTS.md "Profiler run"): run A `sample off`, run B `sample module`, same phases with exact F8 markers (paused 20 s | running 30 s | empty corner 15 s), V-Sync/graphics settings noted. Then `ingest.py ... --recording <timestamp>` for each and read `render_modules` per marker (module split of the render thread decides F101/F102)
1. USER: build KNIGHTS scenario (EXPERIMENTS.md, Scenario Editor; fallback Kingmaker) — note graphics settings
2. EXP-001 baseline KNIGHTS N=100, phases P0–P4 → skill `messung-auswerten`; judge with render-thread CPU %, not `cpu-side` alone. Check `SH2Proxy.log` caller chain (F088)
   - optional EXP-001-REAL: user's own save from a real lag situation, protocol "Real save" (EXPERIMENTS.md); save the game as soon as the FPS overlay drops clearly
3. EXP-002 LAA, EXP-003 DXVK (`tools/variant.py`, proxy chains to `d3d9_dxvk.dll`); optional: Steam overlay off vs. on (F086)
4. After the module split: if game code dominates → `function` mode run + `ExportFunctions.java` for full symbol coverage (names for exe/dragonfly addresses), EBP stacks (design step 3); if driver/d3d9 dominates → look at draw-call/state-change reduction instead (hook candidates)
5. Import `dxrenderer.dll` into Ghidra (vtables, `fbrief`) if the render path matters (F094)
6. Hub idea: log largest free VA block next to `va_used_mb` (fragmentation, F090)
7. Low prio: GR2 → standard uncompressed GR2 via file-builder API

## Next step
Commit + rebuild + deploy the hub (open task 00; checks of D012 included), run the hub overhead A/B (EXP-005) and the in-game lifecycle check; read F107 from its table. Then the profiler runs on the lag save (open task 0) with the `min` profile, so that the sampled run is not disturbed by hub work. In parallel (optional): V-Sync/limiter check in the empty corner (F100) by noting the in-game option.

Previous next step, still open: USER builds the KNIGHTS scenario (optionally also EXP-001-REAL with a real lag save), then EXP-001 (baseline, N=100, P0–P4 with F8 markers) → `ingest.py --exp EXP-001 --scenario KNIGHTS --troops 100`.

## Risks / unknowns
- D012 code has run only in the stand-in and unit tests, never in Stronghold 2 (F113): hashing of the 5 MB+ exe at hub load (background thread) and of the CSVs at recording stop (capture thread) is untimed in the game. The hub reads no game memory: **no automatic game speed/pause** exists — `planned` (typed via `variant.py plan`) and `user_confirmed` (`ingest.py annotate`) only; an `observed` value needs a verified address (D005, separate analysis task). The speed of EXP-001-REAL-B ("90" appears only in its note) is still `unknown` in silver until the user confirms it with `annotate`
- Old recordings (no manifest) stay `legacy`/unverified: modes and capture health are unknown for them, not "all on / OK"; the 3 existing captures cannot become benchmark-usable without new runs
- `ingest.py` no longer deletes sources: `SH2Perf_out` grows until the user cleans it; a stale `captures/.staging/<id>/` after a crash is discarded by the next import of that id
- D011 code has run only in the stand-in and unit tests, never in Stronghold 2: possible differences are the real thread count, WndProc/overlay interplay with the Steam overlay, and `Reset` handling with the overlay off (not hooked, untested in the game). Fallback: `variant.py mode full`, or hub off
- `min`/overlay off: no EndScene timing, so `cpu-side` is not comparable between modes; the game gives no on-screen recording state without the overlay (tones + log only; `beep` can be switched off)
- Ring 8,192 frames (~0.9 MB of the 2 GB address space, F090 headroom is small but far above this); a capture thread starved for > 2 minutes at 60 FPS would drop frames — reported, but the run is then invalid
- Which part of the old hub work caused the 1 s hitch in the stand-in (thread poll vs file flush vs VA query) was not isolated (F106)
- Sampler never ran in Stronghold 2: suspending the render thread ~100×/s could interact with the Steam overlay/driver; synthetic overhead 2–4 % (F103) → run A (off) vs B (module) before trusting FPS of sampled runs
- `latest.json` is only a pointer (D012); recordings are identified by their manifest. The hub log is shared by all recordings of a session and has no integrity guarantee
- F082 (cause of launcher crash) unconfirmed: launcher not re-run with fixed hub (low priority, proxy is default)
- DXVK behind the proxy only tested in the stand-in program
- Steam overlay hooks D3D9 as well (F086): may distort `present_ms`
- Menu 1,351 MB, early 8-player game 1,497 MB of 2,048 MB VA (F090): watch `va_used_mb` in big battles
- Whether direct start needs the Steam client running: untested (F057)
- Scenario editor may not allow enemy units → fallback in EXPERIMENTS.md
- `sym.py addr` only knows virtual functions until ExportFunctions exists
