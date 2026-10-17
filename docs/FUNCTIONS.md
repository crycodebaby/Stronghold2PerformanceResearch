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
| 0x0078E4D0 | `exe_GrannySampleModel_call` (working name) | exe | mittel | F149: selects 20-byte H record (instance/world/local), passes clock/offset to Sample (return RVA 0x38E6DF), then FreeCompletedModelControls and recursive linked-context traversal. O/H/instance are distinct identities; game semantics beyond this bounded flow unresolved. [Audit integration](evidence/POSE_CONTRACT_2026-10-16.md) |
| 0x0078E0A0 | `exe_HRecord_create_path` (working name) | exe | mittel | F154/F155: one path resizes the O+0x18 container, stores Granny-created instance/world/local returns in 20-byte H records and sets initial O+0x4C. Original source type/name, full capacity/count source and lifetime unresolved. [Bounded creation evidence](evidence/HPOSE_CREATION_2026-10-17.md) |
| 0x0078D500 | `exe_HRecord_reserve_transfer` (working name) | exe | mittel | F156/F157: bounded capacity request, old-record field transfer, unsized old-array delete, capacity/end/begin stores; no full exception/lifetime proof. [Allocation evidence](evidence/HPOSE_ALLOCATION_2026-10-17.md) |
| 0x0078D6D0 | `exe_HRecord_grow_request` (working name) | exe | mittel | F157: valid-range target vs bounded 1.5x capacity choice before reserve; unsigned guards are not arbitrary-corrupt-input validation. [Allocation evidence](evidence/HPOSE_ALLOCATION_2026-10-17.md) |
| 0x0079A840 | `exe_HRecord_byte_request` (working name) | exe | mittel | F156: null/limit branches and exact 20*n argument to nominal CRT new; no measured heap extent. [Allocation evidence](evidence/HPOSE_ALLOCATION_2026-10-17.md) |
| 0x0078E3C0 | `exe_HRecord_cleanup_path` (working name) | exe | mittel | F158: H+0/+4/+8 reach the three Granny Free imports; normal path clears logical range and later selected H, leaving buffer/capacity. Indirect release effects and full generations unresolved. [Cleanup evidence](evidence/HPOSE_CLEANUP_2026-10-17.md) |
| 0x0078EC30 | `exe_HRecord_owner_teardown_path` (working name) | exe | mittel | F159: same-O call to cleanup, then conditional H-array delete and null begin/end/capacity. Only the relevant bounded portion is reconstructed. [Direct chain](evidence/HPOSE_CLEANUP_2026-10-17.md) |
| 0x0078EEF0 | `exe_owner_conditional_delete_wrapper` (working name) | exe | mittel | F159: same-O teardown, flag-bit-0 conditional delete(O); data reference is not full indirect-call coverage or an original source class name. [Boundary](evidence/HPOSE_CLEANUP_2026-10-17.md) |
| 0x00796470 | `exe_resource_candidate_delete_wrapper` (working name) | exe | mittel | F160/F161: slot-0 target of constructor-installed table, calls 0x3963A0 and conditionally deletes its object. Binding to dynamic H resources remains open. [Resource evidence](evidence/HPOSE_RESOURCE_RELEASE_2026-10-17.md) |
| 0x00796240 | `exe_resource_candidate_clear_mesh_file` (working name) | exe | mittel | F161: observed mesh-deformer/binding and file Free calls with additional unresolved virtual calls; not full resource destruction or type identity. [Arguments and boundaries](evidence/HPOSE_RESOURCE_RELEASE_2026-10-17.md) |
| 0x007BB400 | `exe_resource_pointer_lookup_or_create` (working name) | exe | mittel | F162: cache-hit pointer return or allocation/constructor/initialization/insertion path. Cache-writer coverage, original type and full failure semantics not reconstructed. [Provenance](evidence/HPOSE_RESOURCE_RELEASE_2026-10-17.md) |
| 0x00794350 | `exe_lightmap_reference_list_init` (working name) | exe | mittel | F163/F166: filename-based lightmap lookup and 4-byte pointer append to R+0x14 container; lookup implementation and original resource types unknown. [Effects](evidence/HPOSE_INITIALIZER_EFFECTS_2026-10-17.md) |
| 0x007949A0 | `exe_normalmap_reference_request` (working name) | exe | mittel | F164/F166: normalmap filename/extension search and lookup return store R+0x28, including failure null. [Effects](evidence/HPOSE_INITIALIZER_EFFECTS_2026-10-17.md) |
| 0x00794000 | `exe_lights_occlusion_reference_request` (working name) | exe | mittel | F164/F166: lights/occlusion filename search, conditional fallback and R+0x24 result store. [Effects](evidence/HPOSE_INITIALIZER_EFFECTS_2026-10-17.md) |
| 0x007D8A20 | `exe_pointer_array_reserve` (working name) | exe | mittel | F165: reserve/copy/delete of a 4-byte pointer buffer; distinct from H-record reserve and referent release. [Bridge](evidence/HPOSE_INITIALIZER_EFFECTS_2026-10-17.md) |
| 0x0065EF50 | `exe_pointer_array_byte_request` (working name) | exe | mittel | F165: incoming allocator context unused, standalone null/limit/4*count request paths. Not a heap implementation or live-allocation proof. [Bridge](evidence/HPOSE_INITIALIZER_EFFECTS_2026-10-17.md) |
| 0x50054420 | `GrannyGetResultingWorldPoseSize` | granny2.dll (sha256 `94d56fd7…`) | hoch | verified PE export, ret 4, worker RVA 0x467E0; 16+128*N for tested N=0..4096, not an overflow-domain claim (F150) |
| 0x50054400 | `GrannyNewWorldPose` | granny2.dll | hoch | export/ret 4, worker RVA 0x46790, allocator ownership; Free at VA 0x50054410. Constructor does not initialize matrix payload (F150/F151) |
| 0x50054430 | `GrannyNewWorldPoseInPlace` | granny2.dll | hoch | export/ret 8, worker RVA 0x46840; caller-owned aligned memory, header count and two array pointers, guard-tested layout (F150/F151) |
| 0x5004F9F0 | `GrannyGetWorldPoseBoneCount` (shared export address) | granny2.dll | hoch | export map + worker RVA 0x2E9E0 reading int32 at +0; other Ghidra/export labels share address (F150) |
| 0x50052B90 | `GrannyGetWorldPose4x4Array` (shared export address) | granny2.dll | hoch | export map + worker RVA 0x322D0 reading pointer at +4, borrowed N*64-byte array for valid live pose (F150) |
| 0x50052BB0 | `GrannyGetWorldPoseComposite4x4Array` (shared export address) | granny2.dll | hoch | export map + worker RVA 0x32300 reading pointer at +8; consumed by known Exe deform sites. Getter neither copies nor proves capacity/lifetime (F138/F150) |
| 0x500545E0 | `GrannyBuildCompositeFromWorldPose` | granny2.dll | hoch | export/ret 16 → worker RVA 0x477D0; selected composite matrices from inverse-bind and world inputs, own valid-data differential host; original also changes profiling state. [Contract and limits](evidence/POSE_CONTRACT_2026-10-16.md) (F151/F152) |
| 0x5002FF60 | `affine_composite_multiply` (working name) | granny2.dll | mittel | caller RVA 0x15600 under BuildCompositeFromWorldPose, affine 3x3 + translation, x87 arithmetic, canonical output column. Not arbitrary 4x4 multiply; differential evidence covers bounded finite inputs (F151/F152) |
| 0x500469C0 | `local_rest_world_composite_writer` (working name) | granny2.dll (sha256 `94d56fd7…`, base 0x50000000) | mittel | F168/F169: bounded Local/rest source loop with count guards and consecutive World/Composite 64-byte outputs through known dispatch candidates; source validity and selected Sample path remain conditional. [Sample extent](evidence/POSE_SAMPLE_EXTENT_2026-10-17.md) |
| 0x50047060 | `rest_world_composite_writer` (working name) | granny2.dll (same build) | mittel | F168/F169: consecutive bone-rest World/Composite outputs; no World-header capacity guard in this writer. Zero count has no matrix stores. No universal Sample-return guarantee. [Sample extent](evidence/POSE_SAMPLE_EXTENT_2026-10-17.md) |
| 0x500023B0 | `controlled_node_create_with_descriptor` (working name) | granny2.dll (sha256 `94d56fd7…`, base 0x50000000) | mittel | F171: descriptor argument stored at node+0x18, list linking and optional descriptor initializer; known producers only, no complete live-node provenance. [Callback evidence](evidence/POSE_SPECIAL_CALLBACK_2026-10-17.md) |
| 0x5001C780 | `controlled_animation_pose_callback` (working name) | granny2.dll (same build) | mittel | F172–F174: descriptor-bound candidate, count clamp, optional pre-loop fast call and conditional known-writer prefix; indirect track callback and actual live binding remain open. [Callback evidence](evidence/POSE_SPECIAL_CALLBACK_2026-10-17.md) |

Source: `ghidra_scripts/ExportVtables.java` → `captures/vtables_exe.csv` → `data/vtables.db`; granny2 and EXP-007 rows: `fbrief.py`, `AddressContext.java`, `InstructionStats.java` (captures/functions/). Working names are not set in Ghidra (plate comments only). Size/refs are static, not measured cost.
