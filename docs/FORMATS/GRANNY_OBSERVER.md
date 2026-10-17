# Granny observer (EXP-008) — data contract

> Kurzfassung: Datenvertrag des abschaltbaren Granny-Beobachters im Hub (Schalter `granny`, Standard aus): welche sechs Exe-Importe er umleitet, welche geprüften Argumente er sieht, was pro Bild und pro Objekt gezählt wird, die vier Ausgabedateien pro Aufnahme, wie Deformationsaufrufe Modellinstanzen zugeordnet werden (mit Sicherheitsklasse), Grenzen, Verluste und Abdeckung. „Gleich“ heißt immer: gleich wie beim vorigen beobachteten Aufruf auf demselben Zeiger.

Hub source: `Stronghold2AnalyseHub/core/granny_observer.{h,cpp}`; reader: `tools/grannyobs.py`; test without the game: `build/Release/granny_observer_test.exe`. Evidence for the signatures: F137; for the missing model argument of the deform call and the link path: F138.

## Switch and hook path
- `granny=1|0` in `SH2Proxy.ini` (`variant.py granny on|off`) or env `SH2HUB_GRANNY`; not part of `full`/`min`. Off (default): no import slot is touched. In the manifest: `switches.granny {value, source}`; hub builds before EXP-008 have no such key (= unknown).
- On: at hub start six slots of the **exe's import address table for granny2.dll** are pointed at stdcall thunks. All-or-nothing: if a slot is missing or does not hold the granny2 export address (someone else redirected it), nothing is patched and the log says so. END restores every slot that still holds our thunk.
- A thunk calls the original exactly once with the arguments it received (the clock as its raw 32 bits) and returns the original's return value. Bookkeeping only while a recording runs and only on the render thread (`owner_tid`, the thread that calls Present); no file, heap, lock or wait. Calls on other threads are counted (`foreign_thread_calls`) and not aggregated.
- Only memory read of game data: the 64-byte offset matrix argument of the sample call, which the exe fills immediately before the call (F137), copied as raw bits under SEH; a fault is counted (`offset_read_faults`), never hidden.
- Tables are allocated at recording start (`VirtualAlloc`, freed at stop). Version 2 reserves 8,929,560 bytes (8.52 MiB; compile-time ceiling 12 MiB): 8,192 instance keys, 8,192 deformers, 4,096 world poses / composite pointers, 8,192 frame rows. Version 1 had 4,096 instance keys. Keys retain history until recording stop; freed keys are not silently evicted. A longer recording can still exhaust this finite budget.
- Version 2 mixes all pointer bits and probes at most 128 slots (v1: 32). `table_usage` separately reports occupancy, maximum probe length, probe exhaustion before full capacity, capacity exhaustion and invalid null keys. The legacy `losses.*_table_full` fields count all failed aggregations, not necessarily a physically full table. Original calls are still forwarded.

## Observed functions (exe import → arguments used)
| Fn | Import (decorated) | Arguments as verified (F137) | Recorded |
|---|---|---|---|
| clock | `_GrannySetModelClock@8` | (model instance, float32 clock) | instance, clock bits, call site |
| sample | `_GrannySampleModelAnimationsAccelerated@20` | (model instance, bone count, offset 4x4*, local pose*, world pose*) | instance, bone count, offset matrix bits, both pose pointers, call site |
| deform | `_GrannyDeformVertices@24` | (mesh deformer, matrix indices*, matrix buffer 4x4*, vertex count, source vertices*, dest vertices*) | all six; **no model instance is passed** (F138) |
| composite | `_GrannyGetWorldPoseComposite4x4Array@4` | (world pose) → composite matrix array pointer (= field +8 of the world pose) | world pose, returned pointer |
| free instance | `_GrannyFreeModelInstance@4` | (model instance) | marks the pointer freed |
| free deformer | `_GrannyFreeMeshDeformer@4` | (mesh deformer) | marks the pointer freed |

Not observed (examples, all imported by the exe as well): `GrannySetControlClock`, `GrannySetControlRawLocalClock`, `GrannySetControlSpeed`, `GrannySetControlWeight`, `GrannyPlayControlledAnimation`, `GrannyFreeCompletedModelControls`, `GrannyBuildCompositeTransform4x4` — the control clocks/speeds/weights are further inputs of the sampling that this contract does **not** see. Internal granny2 calls (e.g. the B-spline helpers of F134) are not seen at all.

## Identity, "same", and what it does not mean
- Object key = pointer value within a recording, not proof of one object lifetime. Reuse after an observed free is flagged (`frees`, `used_after_free`). Version 2 resets prior-input comparisons at free and invalidates old pose links using an internal generation. CSV rows still aggregate lifetimes at that address; the reader excludes rows with any observed free/reuse from stable-instance statistics. Reuse without an observed free cannot be excluded.
- clock *same*: the 32 bits equal those of the previous clock call on that instance (any earlier frame). *changed* / *noprev* (first call seen in this recording) accordingly.
- sample inputs *same*: bone count, offset matrix bits, local-pose and world-pose pointers all equal to the previous sample call on that instance. Pointers equal ≠ pointed-to data equal.
- `all_observed_same` (per sample call): this frame's latest clock call on the instance was *same* **and** the sample inputs are *same*. It says "repeated with unchanged observed values" — not "identical results", not "all inputs unchanged" (control clocks etc. are not observed), not "computation unnecessary".
- Audit correction (F148): the last clock-call comparison is **not a comparison of clock bits at two samples**. `clock(10), sample; clock(20), clock(20), sample` can report same despite a sample-clock change; the reverse counterexample also exists. Only the strict F146 subset survives the added `clock_changed=clock_noprev=0`, min=max and clock_calls=sample_calls checks. A read-fault offset and null share an invalid representation in this observer; do not treat a fault followed by null as proven equality.
- deform inputs *same*: all five pointer/count arguments equal to the previous call on that deformer. The matrix contents are not compared.

## Link deform → model instance (per deform call)
Chain: deform `matrix buffer` == pointer **returned** by the composite getter for world pose W (observed), and W was the `world pose` argument of a sample call of instance I (observed).
| Class | Meaning |
|---|---|
| `link_frame` | both observations happened in the same frame as the deform call, W sampled by exactly one instance in that frame |
| `link_older` | chain exists but at least one observation is from an earlier frame |
| `link_none` | chain absent, instance detail unavailable, or observed free/generation mismatch invalidated it |
| `link_ambiguous` | W was sampled by two different instances in its last sample frame |
Static support: both exe deform call sites pass `GrannyGetWorldPoseComposite4x4Array([[obj+0x4c]+4])` as the matrix buffer, the same `+0x4c` holder whose `[+0]` is passed to clock/sample and `[+4]` as world pose (F138). The link is pointer equality within a session, not a proof that the deformed mesh belongs to that instance.

Audit correction (F148): a failed instance lookup returns before updating the pose link. A missed second sampler of the same pose can therefore leave an apparently unique `link_frame`. Zero `link_ambiguous` under losses is not proof of actual uniqueness; the counterexample is a test-model boundary, not a proven G1 occurrence.

## Files per recording (roles in the manifest)
| File | Role | Content |
|---|---|---|
| `<stem>_granny.json` | `granny_meta` | schema `sh2perf.granny-observer` v2 (reader also accepts v1), hub, owner tid, the six slots, calls and foreign-thread calls per fn, capacities, allocated_bytes, table_usage, owner_detail_complete, losses, composite pointer conflicts, frame rows written, coverage text |
| `<stem>_granny_frames.csv` | `granny_frames` | one row per frame: `frame` (= `frames.csv` frame), `marker`, `partial` (1 = first frame after start), calls per fn, distinct instances clocked/sampled, clock same/changed/noprev, sample same/changed/noprev, `all_observed_same`, distinct deformers, deform same/changed/noprev, link classes, `drops` |
| `<stem>_granny_instances.csv` | `granny_instances` | one row per (instance, marker slot 0–3, 4 = ≥ 4): first/last frame, clock frames/calls/same/changed/noprev/repeat_in_frame/change_in_frame/min/max, sample frames/calls/same/changed/noprev/repeat, per-input change counts (`ch_bone_count`, `ch_offset`, `ch_local_pose`, `ch_world_pose`), `all_observed_same`, `offset_faults`, last bone count + world pose, frees, used_after_free, exe call sites (rva, `0xFFFFFFFF` = not from the exe), multi_site |
| `<stem>_granny_deformers.csv` | `granny_deformers` | one row per (deformer, marker slot): first/last frame, frames, calls, same/changed/noprev/repeat_in_frame, per-argument change counts, vertex count min/max, link classes, link instance changes, last linked instance, frees, used_after_free, call site, multi_site |

A recording with the observer active but without its files is `capture_ok = false`. Per-object rows use the marker at call time; frame rows the marker at frame end. They can disagree across the marker-transition interval; no exact reallocation is possible from aggregates. Object first/last frame, last pose/count, free/reuse and callsite fields are whole-pointer values repeated in marker rows, not phase-local lifetime histories.

## Completeness is separate from frame integrity
- `owner_detail_complete` requires zero table failures, frame-row losses and matrix-read faults; it covers observed imports on the owner thread only. Other-thread counts and unobserved calls remain separate limits. Zero losses in v1 can establish aggregation completeness but do not repair its earlier lifetime semantics.
- Silver 2.2.0 records `quality.granny_observer` as complete / partial / unknown. Partial or unknown blocks benchmark release even when all file hashes and frame records are intact; it does not rewrite raw `capture_ok` or frame integrity.
- `grannyobs.py` suppresses per-instance conclusions for incomplete detail. Boundary call counters are incremented before table lookups; object counts can be partial. Missing frame rows also limit phase call totals.
- Audit correction (F148): `End` does not emit the pending last `t.cur`. `owner_detail_complete`/zero frame drops do **not** prove all observed calls have a frame row. G1 metadata minus rows = 372 clock + 187 sample + 25 deform + 25 composite = 609 unassigned final calls. Completed-frame sums, recording totals and object-marker sums have distinct scopes. See [reproduced audit and pose contract](../evidence/POSE_CONTRACT_2026-10-16.md).
- The last linked-instance pointer in a deformer row is not a historical model assignment. No per-model deformer count is derived from it. Vertex min/max do not establish the total number of processed vertices.

## Reader call accounting (T2, 2026-10-17)

`python -I tools/grannyobs.py <stem> [--markers 1,3]` first reconciles all six recording call totals against **all**
saved frame rows, including the first partial row and every marker. The marker filter changes only phase statistics.
Frame call counters are read as integers, avoiding float rounding in this accounting. Versions 1 and 2 are supported.
These recording totals cover the owner thread; foreign-thread counts remain separate.

Example with synthetic data (the 609 distribution mirrors F148; this is not a new raw-data recount):

```text
frame-call accounting: partial; unframed tail: 609 calls (no reported frame-row drops)
  per-function difference: clock=372, sample=187, deform=25, composite=25, free_instance=0, free_deformer=0
```

- `balanced`: all six differences are zero. This is call-count agreement, not complete observer coverage or file integrity.
- `partial`: positive differences are printed. With a known zero `frame_rows_dropped`, the label is `unframed tail`
  (no **reported** frame-row drops). With nonzero, missing or invalid drop information it is `unframed/unassigned calls`:
  missing rows may contribute, so the difference is not exclusively an end-of-recording tail. No marker is inferred.
- `unknown`: schema/version, totals or required counters are absent or invalid. Missing columns are not interpreted as
  zero. `inconsistent`: at least one frame sum exceeds its recording total, even if other differences are positive.
  These two statuses suppress phase statistics and exit nonzero; neither establishes the cause of the bad input.

This accounting is separate from `quality(meta)`, `owner_detail_complete` and Silver's existing suitability checks,
which are unchanged. A partial call-to-frame balance does not rewrite an owner-aggregation flag. The report does not
restore lost details, repair the native observer, compare pose outputs or permit caching/skipping. Tests and baseline
CLI counterexample: [T2 evidence](../evidence/T2_FRAME_ACCOUNTING_2026-10-17.md).
