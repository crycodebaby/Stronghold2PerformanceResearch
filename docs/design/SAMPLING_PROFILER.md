# Design: sampling profiler in the hub (DRAFT — no code before EXP-001)

> Kurzfassung: Entwurf. Hub sampelt den Instruction Pointer des Spiel-Hauptthreads, Histogramm nach Adresse, Auflösung über sym.py. Wird nur gebaut, wenn EXP-001 CPU/Simulation als Engpass zeigt.

## Trigger
Build only if EXP-001 shows: render thread ≈ 100 % of one core AND paused/look-away phases point at simulation (EXPERIMENTS.md interpretation key). If EXP-001 says GPU/driver-bound, this design is shelved.

## Question it answers
Which functions burn the main thread's time during phase P2 (melee) vs P0 (idle), per troop count N — i.e. the hotspot list that justifies a game-code hook (D005).

## Mechanism (read-only, no game-code hooks)
| Part | Choice | Notes |
|---|---|---|
| Sampler thread | own thread in hub, `timeBeginPeriod(1)`, waits 1 ms (≈ 1 kHz) | jittery but unbiased enough for hotspots |
| Target | render/main thread (TID from `Present` hook, already tracked) | sim runs there if F011 holds |
| Sample | `SuspendThread` → `GetThreadContext(CONTEXT_CONTROL)` → `Eip` (+ optional `Ebp` chain, depth ≤ 8) → `ResumeThread` | WOW64: hub is 32-bit, so plain `GetThreadContext` |
| Cost guard | suspend window < 20 µs; skip sample if thread is in our own module | measure overhead: frame ms with sampler on/off (must be < 2 %) |
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
