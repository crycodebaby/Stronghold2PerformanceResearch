# Design: sampling profiler in the hub (step 1 built: module counting)

> Kurzfassung: Hub sampelt den Instruction Pointer des Render-Threads. Schritt 1 (Zählung pro Modul: exe, dragonfly, dxrenderer, d3d9, Treiber, granny2) ist gebaut und getestet; Schritt 2 (Funktionen, `function`-Modus) liefert Adressen, die Namensauflösung ist offen.

## Trigger
Original rule: build only if EXP-001 shows render thread ≈ 100 % of one core and the phases point at simulation. Changed by D010: EXP-001-REAL-B (real lag save) already shows the render thread at 98 % with the army in view, but the counters cannot tell game code from graphics driver (F102). So step 1 (module split) is built first; it decides between "driver/D3D9" and "game code" and so which of the two branches is worth a hook.

## Status
| Step | What | State |
|---|---|---|
| 1 | per (marker, module) counts, render thread only | **built** (hub `core/sampler.cpp`), validated without the game (F103); not yet run in the game |
| 2 | per (marker, module, rva) counts (`function` mode, same code, `rva` filled) | built, output in `samples.csv`; Ghidra names only for exe vtable slots (`tools/samples.py`), `ExportFunctions.java` still open |
| 3 | EBP call stacks | not built (design below) |

## Use
1. `python -I tools/variant.py sample module` (or `function`), then `variant.py baseline` if the hub was rebuilt.
2. In game as before: F9 on, F8 markers, F9 off. The hub writes `SH2Perf_<ts>_samples.csv` next to the frame CSV and names it in `latest.json` (`samples_csv`).
3. `python -I tools/ingest.py ...` copies it, adds `render_modules` (percent per module group, total and per marker) to the index line and prints it; `python -I tools/samples.py <csv>` shows it again (+ top functions in `function` mode).
4. Interval: `SH2HUB_SAMPLE_MS` (default 10 ms, ~100 samples/s, ≈ 9,000 samples per 90 s). Module groups: exe, dragonfly, dxrenderer, granny2, d3d9, d3dx9, driver (nv*/ati*/amd*/ig*), overlay, hub, system (ntdll, win32u, KERNELBASE …), other.
5. Reading: group `system` = the thread sat in a system call (waiting or OS work) because a blocked thread reports the user-mode stub (ntdll/win32u). `driver` and `d3d9` = time in the graphics stack, `exe`/`dragonfly`/`dxrenderer`/`granny2` = game code and its libraries. Hub samples (`hub` group) are our own overlay/recording work.
6. Always compare one run with the sampler off against one with it on (same save): the sampler is an intervention (below).

## Measured properties (tests/sampler_test.cpp, tests/standin_d3d9.cpp)
| Property | Result |
|---|---|
| attribution | busy loop in the test exe: 100 % in that module, in both markers; a thread blocked in a wait: 100 % `ntdll`/`KERNELBASE` (0 % in the exe) |
| suspend window | mean 30–36 µs, max 60–400 µs per sample (`SuspendThread` → `GetThreadContext` → `ResumeThread`) |
| overhead | synthetic worst case (busy loop on a free core, 12-core Ryzen): 2–4 % slowdown at 2–10 ms interval (noisy), ≈ 0 % at 20 ms. In the game unknown → measure (step 6) |
| integration | stand-in D3D9 program with proxy + hub: recording, `samples.csv` and `samples_csv` in `latest.json` correct, ingest picks it up |


## Question it answers
Which functions burn the main thread's time during phase P2 (melee) vs P0 (idle), per troop count N — i.e. the hotspot list that justifies a game-code hook (D005).

## Mechanism (read-only, no game-code hooks)
| Part | Choice | Notes |
|---|---|---|
| Sampler thread | own thread in hub, `timeBeginPeriod(1)`, `Sleep(SH2HUB_SAMPLE_MS)`, default 10 ms (~100 Hz; the draft said 1 kHz, but the overhead measurement above rules that out) | jittery but unbiased enough for module shares |
| Target | render/main thread (TID from `Present` hook, already tracked) | sim runs there if F011 holds; the other busy thread (tid 43136, 18–28 %) is not sampled yet |
| Sample | `SuspendThread` → `GetThreadContext(CONTEXT_CONTROL)` → `Eip` (+ optional `Ebp` chain, depth ≤ 8) → `ResumeThread` | WOW64: hub is 32-bit, so plain `GetThreadContext` |
| Cost guard | no heap/lock/logger between Suspend and Resume (the thread may hold them); the suspend window is measured and logged | measure overhead: frame ms with sampler on/off (target < 2 %, synthetic test shows 2–4 % at 10 ms, see above) |
| Address → module | snapshot module list once (base, size, name); store `module_id, rva` | exe has ASLR: rva = eip − base; Ghidra addr = 0x400000 + rva |
| Aggregation | fixed hash map `rva → count` per marker phase, in memory | no per-sample I/O |
| Output | on F9 stop: `SH2Perf_<ts>_samples.csv` (`marker, module, rva, count`), listed in `latest.json` | bronze |
| Call stacks | phase 2 only: EBP walk, compressed as `rva1;rva2;…` (folded stacks) | MSVC 2010 /O2 often omits frame pointers → stacks may be partial |

## Resolution / silver
- `tools/sym.py` gains `ExportFunctions.java` data: all functions (start, size, name), not only vtable slots (today only 6,218 virtual functions are known).
- `ingest.py` aggregates samples → top 20 functions per phase into the `data/index.jsonl` line (`hot`: `[{"addr","name","pct"}]`).
- Skill `funktion-analysieren` takes the top entries as input.

## Validation before trusting it
1. Synthetic: inject a busy loop in a test process → sampler must attribute > 90 % to it.
2. In game: P3 (paused) profile must differ from P2 (melee); P0 vs P2 delta must grow with N.
3. Cross-check one hotspot with x64dbg trace or Windows Performance Recorder (WPR, CPU sampling) on the same scenario.

## Alternatives considered
| Option | Why not first |
|---|---|
| WPR/WPA ETW sampling | no symbols for the exe → still needs our sym.py resolution; good cross-check (step 3) |
| Instrumenting candidate functions (MinHook timing) | hooks on guesses — contradicts D005 |
| Intel VTune / AMD uProf | heavy setup, same symbol problem; possible later |

## Open questions
- Is the simulation really on the render thread (F011)? EXP-001 thread CSV decides.
- Are there worker threads for pathfinding? Sample the top-2 CPU threads if so.
