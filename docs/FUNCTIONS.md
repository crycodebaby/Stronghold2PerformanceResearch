# FUNCTIONS

> Kurzfassung: Benannte Funktionen mit Vertrauen mittel/hoch. Alle übrigen vtable-Slots: tools/sym.py.

Only entries at confidence `mittel` (behaviour matches evidence) or `hoch` (RTTI/vtable, export or string proof).
Guesses about purpose live in FINDINGS as `[Hypothese]`. Everything else: `python -I tools/sym.py addr|class …`.
Addresses = image base 0x00400000 (ASLR → runtime = base + (addr − 0x400000)).
Name `Class::vfNN` = virtual slot NN of the RTTI vftable (structural, says nothing about purpose).

| Address | Name | Module | Confidence | Evidence |
|---|---|---|---|---|
| 0x004E92C0 | `S2Actor::vf20` | exe | hoch | RTTI vftable slot 20; 12,783 B, 21 refs (largest S2Actor vfunc) |
| 0x004EC740 | `S2Actor::vf19` | exe | hoch | slot 19; 3,968 B, 33 refs |
| 0x004E7860 | `S2Actor::vf118` | exe | hoch | slot 118; 1,843 B, 116 refs (shared by derived classes) |
| 0x004E70D0 | `S2Actor::vf117` | exe | hoch | slot 117; 1,727 B, 117 refs |
| 0x00789600 | `Actor::vf02` | exe (GlowWorm) | hoch | slot 2; 1,871 B |
| 0x0078AAF0 | `Actor::vf09` | exe (GlowWorm) | hoch | slot 9; 600 B, 117 refs |
| 0x007CD8C0 | `BiDiPathfinder::vf05` | exe (GlowWorm) | hoch | slot 5; 1,847 B (largest pathfinder vfunc) |
| 0x007D64A0 | `Pathfinder::vf02` | exe (GlowWorm) | hoch | slot 2; 133 B |
| 0x0079DDF0 | `Cluster::vf02` | exe (GlowWorm) | hoch | slot 2; 1,138 B |
| 0x0079BA90 | `ClusterNavigator::vf00` | exe | hoch | only slot; 524 B |
| 0x0076ADC0 | `Simulation::vf02` | exe (GlowWorm) | hoch | slot 2; 220 B; brief: 3 blocks, 0 loops, 1 direct callee (0x0076AC40), 13 indirect calls |
| 0x00769F60 | `ActorMgr::vf00` | exe (GlowWorm) | hoch | slot 0; 137 B |
| 0x007B5F20 | `Layer::vf08` | exe (GlowWorm) | hoch | slot 8 shared by 16 *Layer classes; 433 B |
| 0x00723780 | `DangerLayer::vf09` | exe (GlowWorm) | hoch | slot 9; 143 B |
| 0x00723920 | `ProximityLayer::vf02` | exe (GlowWorm) | hoch | slot 2; 133 B |
| 0x007CED60 | `LevelOfDetailManager::vf04` | exe (GlowWorm) | hoch | slot 4; 492 B |
| 0x007CD700 | `SyncCheck::vf01` | exe (GlowWorm) | hoch | slot 1; 145 B |
| 0x500092E0 | `SseDeformPWNT3432I` | granny2.dll (sha256 `94d56fd7…`, base 0x50000000) | hoch | its own assert string "SseDeformPWNT3432I" next to "x86_granny_accelerated_deformers.cpp", "MatrixBuffer4x4", "DestVertices"; pointer stored by `FUN_5000BFD0` (deformer table, F133); named in Ghidra |
| 0x50008810 | `SseDeformPWNT3432I_loop` (working name, Ghidra keeps FUN_) | granny2.dll | mittel | only caller `SseDeformPWNT3432I`; one SSE loop, `movntps` stores; EXP-007 F1/F2 3.6–4.9 ms/frame (F132) |
| 0x500166E0 | `BSpline2x4n_eval` (working name) | granny2.dll | mittel | only static caller export `GrannySampleBSpline2x4n`; x87 single block (F134) |
| 0x50017600 | `FindKnot_search` (working name) | granny2.dll | mittel | callers incl. export `GrannyFindKnot`; 2 loops with float compares (F134) |
| 0x0078E4D0 | `exe_GrannySampleModel_call` (working name) | exe | mittel | reads IAT slots of `GrannySetModelClock` (0x0078E6B1) and `GrannySampleModelAnimationsAccelerated` (0x0078E6D9); purpose beyond these calls not analysed (F134) |

Source: `ghidra_scripts/ExportVtables.java` → `captures/vtables_exe.csv` → `data/vtables.db`; granny2 and EXP-007 rows: `fbrief.py`, `AddressContext.java`, `InstructionStats.java` (captures/functions/). Working names are not set in Ghidra (plate comments only). Size/refs are static, not measured cost.
