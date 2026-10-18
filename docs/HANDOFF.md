# HANDOFF

> Kurzfassung: Generationen sind spielfrei modelliert; interne New-/Free-Aufrufe umgehen Exporte. Konkrete Ereignisabdeckung und sicheres Leseintervall bleiben offen. Naechster Schritt: Allocatorslot-Veraenderung und Weiterleitung fuer ausgewaehlte Posen. Kein Observer oder Messlauf.

Updated: 2026-10-18 (generation model and allocator boundary).
Read [STATE.md](STATE.md) and [PROJECT_LEAD_HANDOFF.md](PROJECT_LEAD_HANDOFF.md).
Use the [animation knowledge map](ANIMATION_KNOWLEDGE_MAP.md) for the connected path and evidence links.

Only the first section below is a current order. Every later section is a historical operations log (game-run sequences, user guides, way-back instructions) kept as evidence; do not execute it.

## Current order — Exe H-pose ownership/lifetime

- F178/F179: [generation, lifecycle boundaries and read window](evidence/POSE_GENERATION_READ_WINDOW_2026-10-18.md).
  New/Free workers delegate to configurable slots 0x64B48/0x64B4C. Concrete DLL calls bypass exports;
  whether selected H poses use these paths is separate. Own 17-test model handles delivered ABA/gaps/overlap
  with bounded quarantine, but cannot detect silent missing events or authorize memory reads. Independent
  review found and verified correction of one model-history bug. Current verifier: 70 entries/83 ranges,
  seven imports/ten exports, 15 tests normal/-O. Earlier counts below describe their earlier revisions.

- F175–F177: [first-bone fast](evidence/POSE_FIRST_BONE_FAST_2026-10-18.md). All three source branches pass
  World0/Composite0 to known full-store slots; 64 bytes each, conditional on normal calls/live memory/dispatch.
  Route B copies Parent and builds Composite with the previous value contract. A/C U.flags=4 and producer out
  U+0x20 do not establish translation/quaternion initialization; those consumer reads are not disabled by flag 4.
  No engine defect is proved. C>=1 fast plus known rest-loop helpers covers both array prefixes; C=0 is not a
  demonstrated valid Sample counterexample. Verifier remains schema 2, 58 entries/71 ranges, 13 tests normal/-O.

- F171–F174: [special-callback provenance and prefix](evidence/POSE_SPECIAL_CALLBACK_2026-10-17.md).
  Node factory 0x23B0 stores D; animation producer passes 0x61D58, whose file slot +0x10 points to 0x1C780.
  This is a conditional construction binding, not all live-node provenance. Callback C=min(B,BindingCount);
  bypass firstfast and choose known direct helpers on every iteration to obtain complete World/Composite [0,C).
  The exact prelude comparison is node+0x20==2, not a mask test; a general C=0 no-write result is not established.
  Firstfast and Track+8 at 0x1C9C1 remain outside the positive span. Verifier expanded, no clone: schema 2,
  54 entries/67 ranges, six imports/six exports, 12 tests normal/-O. Original-file gates and independent review pass.

- F167–F170: [sample write extent](evidence/POSE_SAMPLE_EXTENT_2026-10-17.md). Exe sample arguments and DLL
  branching connect to two direct writers. For the known first-index-zero subpaths, each writes complete World
  and Composite matrices in `[0,B)` under explicit source/capacity/hierarchy/dispatch conditions. All eight known
  candidate target bindings and 64-byte stores independently checked. Local source starts at 80*f, not 80*a;
  a is only a guard addend here. The special callback and valid LocalPose production remain open. Neither normal
  Sample return nor HeaderN authorizes a full live read. Nine tests and original-file gates normal/-O pass;
  33 pinned entries/46 ranges, five imports/three exports. Reproduce:
  `python -I tools/pose_sample_verify.py --exe <exe> --dll <dll>` and `python -I tools/test_pose_sample.py`.

- F163–F166: [initializer effects](evidence/HPOSE_INITIALIZER_EFFECTS_2026-10-17.md). Optional filename-driven
  lightmap reference list R+0x14, normalmap R+0x28, lights/occlusion R+0x24. Pointer-list stride 4 differs from H20.
  The small allocator discards incoming ECX=R+0x20 before use; that one apparent escape is closed. Lookup/global
  alias effects and dynamic release 0x38E428 remain open. Do not promote direct no-store to global unchangedness.
  Existing resource verifier/manifest now schema 2; 20 functions/24 ranges, 16 bindings and 15 tests normal/-O.
  [Readiness decision](design/POSE_COMPARISON_READINESS_2026-10-17.md) selects the next proof independently of a
  complete cache/type reconstruction. No observer implementation or live comparison is ready.

- F160–F162: [resource provenance and candidate cleanup](evidence/HPOSE_RESOURCE_RELEASE_2026-10-17.md).
  Constructor table slot 0 points to 0x396470 -> 0x3963A0 -> 0x396240 (mesh/file releases), but post-construction
  initialization passes R into unexamined helpers and cache hits have separate provenance. Dynamic target at
  0x38E428 remains unresolved. Do not turn the constructor table into a claim about all live H resources.
  Reproduce: `python -I tools/hpose_resource_verify.py --exe <exe> --dll <dll>` and
  `python -I tools/test_hpose_resource.py`; normal/-O gates, ten tests, independent review. No original execution.

- Completed F158/F159: [cleanup and outer teardown](evidence/HPOSE_CLEANUP_2026-10-17.md).
  Three Free arguments are H+0/+4/+8; logical emptying, selected-H nulling and later array delete are separate.
  O+0x4C becomes null only after additional indirect calls. Normal-return result; no general generation/reentrancy
  or output-initialization proof. Six function/six import gates, eight tests normal/-O and independent review.
  Reproduce: `python -I tools/hpose_cleanup_verify.py --exe <exe> --dll <dll>` and
  `python -I tools/test_hpose_cleanup.py`. No native source/observer/runtime change.

- Completed F156/F157: [capacity, allocator argument and transfer](evidence/HPOSE_ALLOCATION_2026-10-17.md).
  `0x38D500` -> `0x39A840` -> nominal CRT new requests 20*n, not measured heap reserve. Five-word H transfer,
  old-array delete and capacity/end/begin stores are distinct from Granny pose construction/destruction.
  Reproduce: `python -I tools/hpose_allocation_verify.py --exe <exe> --dll <dll>`; synthetic verifier:
  `python -I tools/test_hpose_allocation.py`. Own native byte model adds ten literal cases; now 6393 checks total.

- Tooling acceptance follow-up: [native JSON/process/report gates](evidence/HPOSE_NATIVE_ACCEPTANCE_2026-10-17.md)
  completed locally, ten runner tests normal/-O plus standalone Win32 run. Workflow now includes the native step;
  no new online CI or push. `record_range.h` and research findings unchanged. Do not repeat general tooling hardening
  before the next bounded cleanup/lifetime investigation.

- New bounded result F154/F155: [creation and handover](evidence/HPOSE_CREATION_2026-10-17.md), entry `0x38E0A0`,
  Granny returns at H+0/+4/+8; same O+0x18/+0x1C range and O+0x4C selection at `0x38E4D0`. Record count C and
  requested bone count N are different. Own C++ range/layout preparation has no live-pointer access or ownership.
- Reproduce: `python -I tools/hpose_creation_verify.py --exe <exe> --dll <dll>`; game-free verifier tests:
  `python -I tools/test_hpose_creation.py`; native own model: `python -I tools/hpose_native.py` (MSVC Win32/CMake).
  Fingerprints prove byte locations, not semantics. See evidence for exact RVAs, input identities and limits.

- Tooling follow-up 2026-10-17: T2 now reports global call-to-frame accounting with synthetic tests and an old-CLI
  counterexample ([evidence](evidence/T2_FRAME_ACCOUNTING_2026-10-17.md)). Owner-detail/Silver quality and native
  observer unchanged. This closes a reporting gap, not the losses or pose lifetime question. No new capture or push.
  A fresh Sol 6.1 review found a CSV parser-error reporting gap; corrected with a failing-then-passing regression
  (19 reader tests total). See the same evidence for review scope and limits.

- Completed block: [contract, audit corrections, exact limits and reproduction](evidence/POSE_CONTRACT_2026-10-16.md), F148–F153. Real-DLL host: 142 layout cases, 1,620 differential cases, 238,768 components; 0 criterion failures. Own affine helper is numerically close but differs in 443 cases; no universal bit identity or replacement permission. Nine audit model tests + two integration tests pass.
- Reproduce from repo root: `python -I tools/granny_pose.py`, then `python -I tools/test_granny_pose.py`; audit: `python -I tools/recheck_granny_audit.py --audit-root <local-audit-root>`; docs: `python -I tools/lint_docs.py`. MSVC/CMake/Win32 required; writes only isolated ignored build outputs. Reports include identities/source hashes and a float counterexample.
- **Exactly one next proof:** delimit change/forwarding paths of DLL allocator slots 0x64B48/0x64B4C for
  selected NewWorldPose provenance. Which concrete unhandled free/reuse path could end that generation and
  which event boundary would detect it? No complete heap reconstruction. Safe writer/read interval remains a
  separate obligation; consistent ledger metadata or an active original call is no synchronization proof.
  No observer/hooks, original execution, recording, cache/skip or automatic curve-family reconstruction.
- Acceptance/result decisions are in the evidence's final section. Library ownership is established in own valid hosts; the particular game-side owner/lifetime is not yet fully proven. Unresolved indirect transfers remain an explicit boundary. No output observer implementation is claimed.
- Do not resume G2, install a build or request a recording. Original/TEST, Hub source/builds, captures, audit reference and original Ghidra DB stay unchanged. SH2-Perf own code/docs only. New agents update STATE and this section after the next result.
- Publication (2026-10-17): both repositories are public ([STATE.md](STATE.md) "Published state"). Work in a clone of the published research history with normal commits and pull requests; no re-export, no rewrite of published or hub ids. Push or open a PR only when the task asks for it. Publication changes nothing in this order.

## Historical checkpoint — EXP-008R, corrected observer (superseded)

The sequence below records the previous checkpoint; it is not an active work order.

- Evidence and exact restart protocol: [evidence/EXP-008_OBSERVER_CORRECTION.md](evidence/EXP-008_OBSERVER_CORRECTION.md). Hub `32ebc38a05ea`, metadata v2; Silver 2.2.0. All changes local; no push, no optimisation or gameplay change.
- Old A1 `rec-20261015T110452Z-e10a0594` remains historical control. Old G1 `rec-20261015T111010Z-d6bf1a9b` is manifest-verified but has 498,935 instance aggregation failures. No complete per-instance conclusions; F136 stays hypothesis. Fresh controls after observer code change.
- Next sequence: EXP-008R-A1 **off** → EXP-008R-G1 **on** → EXP-008R-G2 **on** → EXP-008R-A2 **off**. Sampler off, full, speed 90, same save/camera. Agent verifies/imports each run before switching for the next; stop for diagnosis if G1 detail is incomplete.
- **G1 partial; do not run G2**: `rec-20261015T122211Z-dff71642`, verified 7 files/2,542 frames, speed 90 and final pause user-confirmed. Observer still loses 126,632 instance aggregations (probe failures, not physical capacity full); first losses at +5.847 s, all paused frames affected. Narrow retained-pointer observations are useful, not complete population evidence. [G1 analysis and next tooling scope](evidence/EXP-008R_G1_PARTIAL.md). TEST now granny off, sample off, full, experiment/protocol cleared; scenario/speed retained. Same installed DLL, no engine patch. No next game run prepared; next correct state/history design and stress tests. Backup unchanged, original untouched.
- Preparatory scope after the completed independent audit: validate this Granny build's pose-buffer lengths/layouts and lifetimes, then prepare a bounded actual-output observer (at most 16 selected generations, per-sample clock comparison, explicit gaps/tail). Original calls still run, no skip/cache and no new game capture before native tests pass. Historical multiplayer collapse is a separate unrecorded case (F060); do not wait for AI recruitment/attacks or treat current SP results as its explanation. User clarification 2026-10-16 is recorded in EXPERIMENTS/STATE.
- Suspended protocol (resume only after correction and explicit readiness): load LAG_217_Reiter, speed 90, unchanged camera, centred mouse, wait 10 s; F9 → ~5 s → F8 → running **30 s** → F8 → game pause → ~3 s → F8 → paused **30 s** → F9 → wait for recording completion → quit normally. F8 only marks phases. Timing amendment documented before G1; no threshold changed. G1 actual running/paused durations 30.265/35.158 s.
- User has confirmed speed 90 for old G1. Pause inferred from frozen counters is not automatically a user-confirmed pause annotation. No reference release has been added on the user's behalf.

## Historical order (2026-10-15): close EXP-007, prepare EXP-008
Order: A) correct and secure EXP-007; B) read-only Granny boundary observer, then four game runs. No optimisation, cache, skipping, clock or simulation change, publishing.

| Step | State |
|---|---|
| A1 wording (deform loop "large in both states", "no exe hotspot" only for flat sampling, 0 samples ≠ 0 calls) | done (EXPERIMENTS, F135/F136, STATE) |
| A2 recount | done: **134 / 120** known exe functions sampled only running (138 / 121 with unresolved pages); 169 / 146 were keys incl. pages with Δ > 0. Query: `funcsamples.py … --delta-counts --module exe` |
| A3 analysis state | done: [evidence/ANALYSIS_STATE_EXP-007.md](evidence/ANALYSIS_STATE_EXP-007.md) (binary hashes, Ghidra 12.1.4, image bases, map hashes, manual Ghidra edits); closed project zipped to `ghidra-projects/_backup/SH2_after_EXP-007_20261015.zip` (sha256 `48d50246…`) |
| A4 commits | SH2-Perf `68b8868` (prior sessions' EXP-INGAME/006/007 tree as found), `a31a5c7` (corrections); this preparation in the next commit. No push |
| B4 signatures | done: F137 (all stdcall, pop counts, argument roles), F138 (deform call has **no** model instance; link only through world pose → composite pointer), F139 (clock values per call site) |
| B5 data contract | done: [FORMATS/GRANNY_OBSERVER.md](FORMATS/GRANNY_OBSERVER.md), D014 |
| B6 implementation | done: hub `perf-metrics` `e3ea53e` (`core/granny_observer.*`, switch `granny`, default off); `tools/grannyobs.py`; `variant.py granny on\|off`; ingest stem fix (F140) |
| B7 checks without the game | done: F140 (`granny_observer_test` 3/3 + mutation check, `capture_test`, `lifecycle_test`, `sampler_test`, `e2e_standin` off and on, Python suites, lint) |
| B7 install in TEST | done, game closed: DLL `54de688f…` (build `e3ea53e5d9f7`), proxy unchanged `13c89519…`, exe unchanged `f3ccdf9b…`; `granny=0`, `sample=off`, profile full, plan `EXP-008-A1` / `GRANNY_OBS` / REAL_LAG_257 / 90. Original folder untouched |
| B8 protocol | fixed before any run: [EXPERIMENTS.md](EXPERIMENTS.md) "Protocol EXP-008" (A1 off, G1 on, G2 on, A2 off; sampler off) |
| Game runs | A1 imported/verified; G1 partial (F141/F142); G2/A2 deferred until observer correction |

| Run | `granny` | plan id | State |
|---|---|---|---|
| A1 | off | EXP-008-A1 | done: rec-20261015T110452Z-e10a0594, imported/verified, no losses; marker 1/3 33.113/25.673 ms; pause consistent with frozen counters; speed 90 remains planned in metadata |
| G1 | on | EXP-008-G1 | recorded rec-20261015T111010Z-d6bf1a9b; imported/verified; 498,935 instance-table failures, partial detail evidence only |
| G2 | on | EXP-008-G2 | open |
| A2 | off | EXP-008-A2 | open |

**Way back** (game closed): copy `Stronghold2AnalyseHub.dll`, `SH2Proxy.ini`, `SH2Prepared.json` from `..\Stronghold 2 - TEST\_backup_before_EXP-008_20261015\` (+ `SHA256SUMS.txt`; hub `e822e7f19019`, DLL `591e6375…`), then `variant.py status`. Observer only off: `variant.py granny off`.

**User guide (per run, game started from the TEST folder):**
1. Load the save LAG_217_Reiter, set/check speed 90, do not touch the camera, mouse to the screen centre. Wait 10 s.
2. **F9** (recording starts) → wait ≈ 5 s → **F8** → let it run 20 s → **F8** → press the game's **pause**, wait ≈ 3 s → **F8** → wait 20 s paused → **F9** (recording stops; wait until the overlay no longer shows recording) → quit the game.
3. Tell me: run done, speed was 90, paused in the last part, anything unusual (Alt-Tab, camera moved, stutter). I import and check it, then switch the observer for the next run (A1 off → G1 on → G2 on → A2 off); only start the next run after I say TEST is ready.

**Between runs (agent, game closed):** `ingest.py list` → `import --recording <ts> --exp EXP-008-<run> --scenario REAL_LAG_257 --troops 257` → validity per protocol (G runs: `grannyobs.py captures/<id>` + log line `Granny observer: installed`) → `annotate <id> --game-speed 90 --phase-paused 1=false 3=true` after the user's confirmation → `variant.py granny on|off` + `variant.py plan experiment=EXP-008-<next>` → `variant.py status`. After A2: `ab_compare.py` per marker, evaluation questions of the protocol, results into EXPERIMENTS/FINDINGS (F136 stays a hypothesis unless G1 and G2 agree; allowed wording only), graphics settings hash re-check, then set `granny=0` and remove the plan id.

## Previous order (2026-10-15): EXP-007 function hotspots — done; supersedes EXP-006 below
Protocol and candidate rules fixed in advance: [EXPERIMENTS.md](EXPERIMENTS.md) "Protocol EXP-007". Prerequisite added: `ghidra_scripts/ExportFunctions.java` (all function bodies) and `granny2.dll` imported into the Ghidra project.

| Run | `sample` | plan id | State |
|---|---|---|---|
| A0 | off | (plan id EXP-007-A1) | 09:25, `rec-20261015T072526Z-f1d856a1`, **excluded**: Alt-Tab in marker 2 (4,007 ms frame, device reset), camera moved, marker 3 another view (DIP 2,799, > 10 % off); marker 1 clean (34.4 ms mean) |
| A1 | off | EXP-007-A1 | done 09:31, `rec-20261015T073119Z-a7148666`, valid: m1 running 19.8 s (mean 34.98 ms), m3 paused 18.8 s (25.35 ms), DIP 2,445–2,495; speed 90 user-confirmed + annotated |
| F1 | function | EXP-007-F1 | done 09:34, `rec-20261015T073402Z-bf15a427`, valid: m1 running 22.1 s, m3 paused 21.8 s; 5,595 samples (0 failed/dropped), 3,187 rows, ≈ 95/s; speed 90 user-confirmed + annotated |
| X | function | (plan id EXP-007-F2) | 09:36/09:37, `rec-20261015T073630Z-6e960aca` + `rec-20261015T073721Z-e6a4bc3e`, **excluded**: out of sequence (marker 1 at +19 s, F9 before marker 3, second 14 s recording); 3× F10 before (histogram only) |
| F2 | function | EXP-007-F2 | done 09:39, `rec-20261015T073915Z-387fcc8e`, valid: m1 running 18.4 s, m3 paused 22.8 s, DIP 2,544–2,625; 5,158 samples (0 failed/dropped), 2,886 rows, ≈ 95/s; speed 90 user-confirmed + annotated |
| A2 | off | EXP-007-A2 | **TEST prepared** (`sample=off`), waiting for the user |

- **Result (EXPERIMENTS.md EXP-007, F130–F136, FUNCTIONS.md)**: 4 candidates by the fixed rules — granny2 `FUN_50008810` (SSE deform loop under `SseDeformPWNT3432I`, large cost in both states: paused 4.39/4.46 ms well repeated, running 3.61/4.93 ms differing more), `FUN_500166E0` (B-spline eval helper, 1.2–1.4 ms), `FUN_50017600` (knot search, 0.7–0.9 ms), exe `FUN_004E3530` (x87 helper, +0.2/+0.4 ms running-only). In flat samples the exe's running-only +6.2 ms is spread over 134/120 known functions sampled only running (F135, corrected count); no single exe hotspot in flat sampling, a shared expensive call path is not excluded; 0 paused samples ≠ 0 paused calls. Function-mode frame effect not claimed, bounded only to ≈ 1.3/3.2 ms (F130). Ghidra: granny2 imported, 3 functions created, `SseDeformPWNT3432I` named, plate comments on the candidates.
- **TEST now**: `sample=off`, plan id removed (see below). `SH2Perf_out` keeps all sources.
- **Next order (smallest, F136)** — superseded by the newest order above (EXP-008 as prepared differs: six import slots, aggregated per object, sampler off, A1/G1/G2/A2): EXP-008 read-only call counter at the exe → granny2 import boundary (hub: IAT hooks for `GrannySetModelClock`, `GrannySampleModelAnimationsAccelerated`, `GrannyDeformVertices`; per frame call count, clock argument min/max, vertex count argument if present), same save/protocol, 1 off + 2 on runs. Decides whether paused frames recompute identical poses/skinning (redundant work, then a hook target) and how calls scale per visible unit. Exe side: attributing the flat running-only cost needs call stacks (design step 3, EBP walk) or a static common-caller search over the 134/120 known functions sampled only running — after EXP-008.

## Previous order (2026-10-15, later): EXP-006 army-view profiling — supersedes the acceptance order below
Protocol and evaluation rules fixed in advance: [EXPERIMENTS.md](EXPERIMENTS.md) "Protocol EXP-006". Sampler check: F122–F124 (no blocking defect; synthetic overhead now 4.6–5.1 %, `system` group contains game CRT).

| Run | `sample` | plan id | State |
|---|---|---|---|
| A0 | off | (plan id EXP-006-A1) | pilot done 08:28, imported `rec-20261015T062849Z-735e2089`, relabelled A0: only 2 markers, pause in marker 1 → not protocol-conform |
| A1 | off | EXP-006-A1 | done 08:33, `rec-20261015T063324Z-11f9f002`, valid: 3 markers, m1 running 20 s, m3 paused 24 s (frozen counters from 40 s), pause at ≈ 39 s inside transition marker 2 (20 s long instead of 3 s). speed 90 user-confirmed + annotated; pause from counters |
| B1 | module | EXP-006-B1 | done 08:37, `rec-20261015T063727Z-a0c4873e`, valid: m1 running 18.2 s, m3 paused 21.5 s, pause ≈ 26 s in marker 2; 5,018 samples, 0 failed/dropped, ≈ 95/s per marker; speed 90 user-confirmed + annotated |
| B2 | module | EXP-006-B2 | done 08:40, `rec-20261015T064050Z-f3b36a54`, valid: m1 running 20.1 s, m3 paused 21.2 s; 5,060 samples, 0 failed/dropped, ≈ 95/s; speed 90 user-confirmed + annotated |
| A2 | off | EXP-006-A2 | done 08:43, `rec-20261015T064341Z-dee7161d`, valid: m1 running 19.8 s, m3 paused 21.1 s; speed 90 user-confirmed + annotated |

- TEST change (game closed, 2026-10-15): before = `SH2Proxy.ini` sha256 `57946eae…`, `[proxy] target=system hub=1`, `[plan] experiment=EXP-INGAME scenario=REAL_LAG_257`, no explicit profile/sample (defaults full/off); `SH2Prepared.json` `6e635c7b…`. Both copied to `..\Stronghold 2 - TEST\_backup_before_EXP-006_20261015\` (+ `SHA256SUMS.txt`). Now: `profile=full`, `sample=off` explicit, plan `experiment=EXP-006-A1 scenario=REAL_LAG_257 game_speed=90 protocol=ARMY_RUN_PAUSE`. Hub DLL/proxy unchanged (`matches hub build: True`). Original untouched.
- **Result (EXPERIMENTS.md EXP-006, F125–F129)**: sampler adds ≈ 0.6–1.3 ms per frame (2–5 %, F125), so only A runs give frame times: running 32.8 vs paused 25.1 ms (+7.7 ms, F126). Module split from B1/B2 (F127): granny2 ≈ 11 ms in both states, exe 9.8 running vs 4.3 paused, graphics stack (d3dx9_27 + d3d9 + nvd3dum) ≈ 8 ms in both; the running − paused difference is ≈ 5.5 ms exe + 0.8 ms CRT + 0.5 ms ntdll (F128). Graphics settings hash unchanged after the runs.
- **TEST now**: `sample=off`, `profile=full`, plan `scenario=REAL_LAG_257 game_speed=90` (experiment/protocol removed after A2). Way back to the pre-EXP-006 state: copy `SH2Proxy.ini` from `_backup_before_EXP-006_20261015\` (game closed), then `variant.py status`. `SH2Perf_out` still holds all sources (imported; delete only on the user's word).
- **Next order (smallest)**: EXP-007, function mode, same save/protocol/profile, 2 runs (C1, C2) with `variant.py sample function` — no new off runs needed (sampler bias known, F125; frame times of C runs are not used). Evaluate: top `Stronghold2.exe` rva per marker and the rva whose samples grow running vs paused (reproduced in C1 and C2); top `granny2.dll` rva mapped to the nearest preceding export (`pe_info.py granny2.dll --exports`). Only then skill `funktion-analysieren` (fbrief/Ghidra) on the ≤ 5 reproduced exe candidates. Module sampling cannot name functions, hence the function-mode run.
- Between runs (game closed): import + validity check of the last run, then `variant.py sample <mode>` and `variant.py plan experiment=EXP-006-<next>`; `variant.py status`.
- Import: `ingest.py import --recording <ts> --exp EXP-006-<run> --scenario REAL_LAG_257 --troops 257`, then `annotate <id> --game-speed 90 --phase-paused 1=false 3=true` only after the user confirms.
- Save file: no file named LAG_217_Reiter exists in `Documents\Stronghold 2\Saves` or the Steam cloud list; the user loads it by its in-game name. Its file identity is not recorded.
- Old `SH2Perf_out` recordings of EXP-INGAME are still there (already imported); `ingest.py import` needs `--recording`.

## Order (2026-10-15, superseded): in-game acceptance
In-game acceptance of the measurement instrumentation (hub D011/D012/D013) in Stronghold 2 Steam 1.5, steps of [SETUP.md](SETUP.md) "Check in Stronghold 2". **Nothing about performance** is shown or claimed yet; stand-in results are no game result.

Excluded: engine/game-code patches, new measurement functions, databases, Docker services, larger rebuilds, push or publishing, changes to the original installation or to raw recordings (`captures/`, `SH2Perf_out`), performance claims from stand-in runs.

## Verified state (checked 2026-10-15 against the real files)
| Item | Value | Check |
|---|---|---|
| SH2-Perf `main` | `4f86008` (D013), clean tree before this handoff | `git log`, `git status` |
| Hub `perf-metrics` | `e822e7f`, clean, `git describe --dirty --abbrev=12` = `e822e7f19019` | build id string in the DLL found once |
| Hub DLL / proxy / stand-in sha256 | `591e6375…35a89e5` / `13c89519…84e24801` / `4f888820…f500b22b` (full in [SETUP.md](SETUP.md), [evidence](evidence/ACCEPTANCE_2026-10-15.md)) | `sha256sum build/Release/*` = documented values |
| Acceptance report commit mix-up | fixed: D013 = `4f86008`, before D013 = `55974f1` | both evidence patches byte-identical to the commit diffs (report section "Correction") |

## TEST copy (`..\Stronghold 2 - TEST`)
| | Before (until 2026-10-15) | Now |
|---|---|---|
| hub DLL | build `a98bea10ad6e` (sampler, pre-D011), sha256 `4459368a…4695b563` | `e822e7f19019`, `591e6375…35a89e5` |
| proxy `d3d9.dll` | `13c89519…84e24801` | unchanged (same file) |
| `SH2Proxy.ini` | `target=system`, `hub=1`, no plan | same keys + `[plan] experiment=EXP-INGAME scenario=REAL_LAG_257` (**no game_speed**: the user names the real one, it goes in via `annotate`) |
| `SH2Prepared.json` | absent | written by `variant.py` |
| exe | sha256 `f3ccdf9b…0f32d34b`, LAA off | unchanged |

Installed with `variant.py baseline` (game was not running); `variant.py status` = `matches hub build: True`; installed DLL hash checked. Original folder: exe hash unchanged, no proxy/hub files.

**Way back**: `..\Stronghold 2 - TEST\_backup_before_e822e7f_20261015\` holds the old hub DLL, old `SH2Proxy.ini`, proxy and the previous `SH2Proxy.log` (+ `SHA256SUMS.txt`). Restore = game closed, copy `Stronghold2AnalyseHub.dll` and `SH2Proxy.ini` back, delete `SH2Prepared.json`. Hub off without restore: `variant.py hub off`. Fully vanilla: see SETUP "Import and provenance checks".

## Acceptance steps
| Step (SETUP "Check in Stronghold 2") | Prepared | Stand-in checked | In Stronghold 2 checked |
|---|---|---|---|
| 0 install + status + plan | done | – | – (no game start yet) |
| 1 first F9 recording, manifest `finalized` | yes | yes (e2e) | **open** |
| 2 second recording, new `capture_id` | yes | yes | **open** |
| 3 Alt-Tab during recording | yes | no | **open** |
| 4 END deactivation (with/without recording) | yes | yes (8/8, 4/4) | **open** |
| 5 game exit while recording (limit F117) | yes | yes | **open** |
| 6 import, re-import, annotate speed | yes | yes | **open** |

## Working trees
- SH2-Perf: this handoff, STATE pointer and the acceptance-report correction, committed locally (no push). Nothing else changed.
- Hub: clean at `e822e7f`, not touched.
- TEST: changed as in the table above (outside git). `SH2Perf_out` held only the old `SH2Proxy.log` (backed up); no recordings yet.

## Next action
Wait for the user's first game session. Then read yourself (do not ask the user to copy files): `..\Stronghold 2 - TEST\SH2Perf_out\Stronghold2AnalyseHub.log`, `SH2Proxy.log`, `*_manifest.json`, `*_prepared.json`, `latest.json`; check against SETUP steps 1–5 "Expected"; `python -I tools/ingest.py list`, then import per SETUP step 6 and `annotate --game-speed <N>` with the speed the **user** named. Record the result in EXPERIMENTS.md/FINDINGS (F113 stays stand-in-only until then) and update this file and STATE.

User actions needed: start the game from the TEST folder, load LAG_217_Reiter (REAL_LAG_257), say which game speed is set, do recordings 1+2 with F9, Alt-Tab, END in a suitable session, one session that quits while recording (last).

## Acceptance result — supersedes the open rows above
User completed the simplified check and confirms speed 90 throughout. Three captures imported/verified and annotated; see EXPERIMENTS.md EXP-INGAME and F118–F121. Sources retained. Pause annotations false follow the user-confirmed instructions; F8 was only a marker. No benchmark release.
Passed in this session: F9, second recording, Alt-Tab with logged reset, END without active recording. Not performed: END during recording or process exit during recording. No sampler capture and no controlled performance gain. Next prepare a fixed-camera pause/run and sampler-off/on protocol; do not repeat generic hardening. Old acceptance rows and Next action above describe the pre-session state.

## Operational handoff (2026-10-15, superseded) — A1 checked, G1 ready
A1 rec-20261015T110452Z-e10a0594 is archived and verified; see EXPERIMENTS.md. TEST configuration is now EXP-008-G1 / granny on / sampler off / full / planned speed 90. User should restart TEST, reload the same save and repeat the protocol. Do not run variant.py again before this G1 unless a mismatch is found. No game process was running during configuration. Do not report the final-linked-instance grouping as historical per-model deform counts (see EXPERIMENTS caveat); this derived statistic is excluded from the experiment interpretation. No observer game data exists yet. Sources retained, original untouched.

## Operational checkpoint (2026-10-15, superseded) — G1 partial, do not run G2 yet
G1 rec-20261015T111010Z-d6bf1a9b is imported/verified, user confirms speed 90. Raw frame integrity is good, but 498,935 instance-table failures make complete per-instance conclusions invalid. Details in EXPERIMENTS and F141/F142. Diagnose bounded instance table/lifetimes/probe saturation before repeating observation. Counters before lookup are useful; tracked subset is not representative by default. TEST now granny off / sample off / full, experiment and protocol cleared, planned speed 90 retained; no game process running. No G2 prepared, no binary changed. All source files retained. After changing observer code, use fresh matching controls rather than silently reusing old A1.
