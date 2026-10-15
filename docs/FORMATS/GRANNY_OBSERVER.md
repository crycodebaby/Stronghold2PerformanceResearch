# Granny observer (EXP-008) — data contract

> Kurzfassung: Datenvertrag des abschaltbaren Granny-Beobachters im Hub (Schalter `granny`, Standard aus): welche sechs Exe-Importe er umleitet, welche geprüften Argumente er sieht, was pro Bild und pro Objekt gezählt wird, die vier Ausgabedateien pro Aufnahme, wie Deformationsaufrufe Modellinstanzen zugeordnet werden (mit Sicherheitsklasse), Grenzen, Verluste und Abdeckung. „Gleich“ heißt immer: gleich wie beim vorigen beobachteten Aufruf auf demselben Zeiger.

Hub source: `Stronghold2AnalyseHub/core/granny_observer.{h,cpp}`; reader: `tools/grannyobs.py`; test without the game: `build/Release/granny_observer_test.exe`. Evidence for the signatures: F137; for the missing model argument of the deform call and the link path: F138.

## Switch and hook path
- `granny=1|0` in `SH2Proxy.ini` (`variant.py granny on|off`) or env `SH2HUB_GRANNY`; not part of `full`/`min`. Off (default): no import slot is touched. In the manifest: `switches.granny {value, source}`; hub builds before EXP-008 have no such key (= unknown).
- On: at hub start six slots of the **exe's import address table for granny2.dll** are pointed at stdcall thunks. All-or-nothing: if a slot is missing or does not hold the granny2 export address (someone else redirected it), nothing is patched and the log says so. END restores every slot that still holds our thunk.
- A thunk calls the original exactly once with the arguments it received (the clock as its raw 32 bits) and returns the original's return value. Bookkeeping only while a recording runs and only on the render thread (`owner_tid`, the thread that calls Present); no file, heap, lock or wait. Calls on other threads are counted (`foreign_thread_calls`) and not aggregated.
- Only memory read of game data: the 64-byte offset matrix argument of the sample call, which the exe fills immediately before the call (F137), copied as raw bits under SEH; a fault is counted (`offset_read_faults`), never hidden.
- Tables are allocated at recording start (`VirtualAlloc`, ≈ 6.6 MB committed while observing, freed at stop): 4,096 instances, 8,192 deformers, 4,096 world poses / composite pointers, 8,192 frame rows. Full = counted in `losses`, the call itself is still forwarded.

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
- Object id = pointer value, valid within one session. Reuse after a free is flagged (`frees`, `used_after_free`); reuse without an observed free cannot be excluded.
- clock *same*: the 32 bits equal those of the previous clock call on that instance (any earlier frame). *changed* / *noprev* (first call seen in this recording) accordingly.
- sample inputs *same*: bone count, offset matrix bits, local-pose and world-pose pointers all equal to the previous sample call on that instance. Pointers equal ≠ pointed-to data equal.
- `all_observed_same` (per sample call): this frame's latest clock call on the instance was *same* **and** the sample inputs are *same*. It says "repeated with unchanged observed values" — not "identical results", not "all inputs unchanged" (control clocks etc. are not observed), not "computation unnecessary".
- deform inputs *same*: all five pointer/count arguments equal to the previous call on that deformer. The matrix contents are not compared.

## Link deform → model instance (per deform call)
Chain: deform `matrix buffer` == pointer **returned** by the composite getter for world pose W (observed), and W was the `world pose` argument of a sample call of instance I (observed).
| Class | Meaning |
|---|---|
| `link_frame` | both observations happened in the same frame as the deform call, W sampled by exactly one instance in that frame |
| `link_older` | chain exists but at least one observation is from an earlier frame |
| `link_none` | matrix pointer never returned by an observed getter, or W never sampled |
| `link_ambiguous` | W was sampled by two different instances in its last sample frame |
Static support: both exe deform call sites pass `GrannyGetWorldPoseComposite4x4Array([[obj+0x4c]+4])` as the matrix buffer, the same `+0x4c` holder whose `[+0]` is passed to clock/sample and `[+4]` as world pose (F138). The link is pointer equality within a session, not a proof that the deformed mesh belongs to that instance.

## Files per recording (roles in the manifest)
| File | Role | Content |
|---|---|---|
| `<stem>_granny.json` | `granny_meta` | schema `sh2perf.granny-observer` v1, hub, owner tid, the six slots (iat rva, target rva in granny2, patched), calls and foreign-thread calls per fn, capacities, `losses` (table full, frame rows dropped, offset faults), composite pointer conflicts, frame rows written, coverage text |
| `<stem>_granny_frames.csv` | `granny_frames` | one row per frame: `frame` (= `frames.csv` frame), `marker`, `partial` (1 = first frame after start), calls per fn, distinct instances clocked/sampled, clock same/changed/noprev, sample same/changed/noprev, `all_observed_same`, distinct deformers, deform same/changed/noprev, link classes, `drops` |
| `<stem>_granny_instances.csv` | `granny_instances` | one row per (instance, marker slot 0–3, 4 = ≥ 4): first/last frame, clock frames/calls/same/changed/noprev/repeat_in_frame/change_in_frame/min/max, sample frames/calls/same/changed/noprev/repeat, per-input change counts (`ch_bone_count`, `ch_offset`, `ch_local_pose`, `ch_world_pose`), `all_observed_same`, `offset_faults`, last bone count + world pose, frees, used_after_free, exe call sites (rva, `0xFFFFFFFF` = not from the exe), multi_site |
| `<stem>_granny_deformers.csv` | `granny_deformers` | one row per (deformer, marker slot): first/last frame, frames, calls, same/changed/noprev/repeat_in_frame, per-argument change counts, vertex count min/max, link classes, link instance changes, last linked instance, frees, used_after_free, call site, multi_site |

A recording with the observer active but without its files is `capture_ok = false`. Per-object rows use the marker at call time; frame rows the marker at frame end (they differ only on the F8 frame).
