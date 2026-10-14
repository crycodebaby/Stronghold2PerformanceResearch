# FUNCTIONS

Ghidra renames. One row per function. Addresses = image base 0x00400000 (ASLR on → rebase at runtime: `runtime = base + (addr - 0x400000)`).
Confidence: `hoch` (RTTI/vtable/exported symbol or string proof) · `mittel` (behavior matches) · `niedrig` (guess).
Naming: `Class::vfNN` = virtual slot NN. Class membership is `hoch` (RTTI vftable); **purpose is unknown** unless stated.
Source: `ghidra_scripts/ExportVtables.java` → `captures/vtables_exe.csv` (1,585 vtables, 31,865 slots), filter `tools/vtable_candidates.py`.
Size/callers = static hints only, NOT measured cost. No hooks until EXP-001 data (D005).

## Hotspot candidates (Stronghold2.exe)

| Address | Name | Module | Confidence | Evidence |
|---|---|---|---|---|
| 0x004E92C0 | `S2Actor::vf20` | exe | class hoch / purpose niedrig | S2Actor vftable slot 20; 12,783 B (largest S2Actor vfunc), 21 refs. Candidate per-actor update/think. |
| 0x004EC740 | `S2Actor::vf19` | exe | class hoch / purpose niedrig | slot 19; 3,968 B; 33 refs |
| 0x004E7860 | `S2Actor::vf118` | exe | class hoch | slot 118; 1,843 B; 116 refs (shared by S2Actor-derived classes) |
| 0x004E70D0 | `S2Actor::vf117` | exe | class hoch | slot 117; 1,727 B; 117 refs |
| 0x00789600 | `Actor::vf02` | exe (GlowWorm) | class hoch | GlowWorm::Actor slot 2; 1,871 B |
| 0x0078AAF0 | `Actor::vf09` | exe (GlowWorm) | class hoch | slot 9; 600 B; 117 refs (inherited by all actor types) |
| 0x007CD8C0 | `BiDiPathfinder::vf05` | exe (GlowWorm) | class hoch / purpose mittel | slot 5; 1,847 B — largest pathfinder vfunc, likely search step |
| 0x007D64A0 | `Pathfinder::vf02` | exe (GlowWorm) | class hoch | slot 2; 133 B (base impl) |
| 0x0079DDF0 | `Cluster::vf02` | exe (GlowWorm) | class hoch | slot 2; 1,138 B |
| 0x0079BA90 | `ClusterNavigator::vf00` | exe | class hoch | only slot; 524 B |
| 0x0076ADC0 | `Simulation::vf02` | exe (GlowWorm) | class hoch | slot 2; 220 B — candidate sim tick entry (follow callees) |
| 0x00769F60 | `ActorMgr::vf00` | exe (GlowWorm) | class hoch | slot 0; 137 B |
| 0x007B5F20 | `Layer::vf08` (shared) | exe (GlowWorm) | class hoch | slot 8 shared by 16 *Layer classes; 433 B |
| 0x00723780 | `DangerLayer::vf09` | exe (GlowWorm) | class hoch | slot 9; 143 B |
| 0x00723920 | `ProximityLayer::vf02` | exe (GlowWorm) | class hoch | slot 2; 133 B — proximity = candidate for target search |
| 0x007CED60 | `LevelOfDetailManager::vf04` | exe (GlowWorm) | class hoch | slot 4; 492 B (render side) |
| 0x007CD700 | `SyncCheck::vf01` | exe (GlowWorm) | class hoch | slot 1; 145 B (lockstep check) |

## Notes
- `GlowWorm::Formation` has an RTTI name but no exported vftable slots (abstract or no vftable symbol) — formations need another route (xrefs to `BoxFormation` etc.).
- Many vfuncs are small dispatchers; real work sits in non-virtual callees → next: call graph from `Simulation::vf02` and `S2Actor::vf20` (REA `analyze_function` after restart).
