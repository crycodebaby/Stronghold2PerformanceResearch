# STATE

> Kurzfassung: Aktueller Stand, offene Aufgaben, nächster Schritt. Immer zuerst lesen.

Updated: 2026-10-18 · Phase: 1 (measurement and bounded analysis) · **No performance gain has been shown; no change to game behaviour exists.**

## Current status (the only current order)
| Item | State |
|---|---|
| Goal | Original exe Steam 1.5 + switchable drop-in extension; reference scene REAL_LAG_257 (257 units, speed 90) ≥ 45 FPS mean / ≥ 30 FPS 1 % low. Not reached. |
| Published state (2026-10-17) | Public on GitHub: this repository, first `main` `46b14eb2cefa` (cleaned history; local ids cited in docs map via [export/EXPORT_MAP.tsv](export/EXPORT_MAP.tsv)) · [hub](https://github.com/crycodebaby/Stronghold2AnalyseHub) `main` merge commit `d3a763a33777`, runtime sources equal to `32ebc38a05ea` (build of the latest in-game recordings), original hub ids kept. Continue with normal commits/PRs on these histories; no re-export. CI and local checks: [REPRODUCIBILITY.md](REPRODUCIBILITY.md) |
| Latest in-game data (2026-10-15) | EXP-008R-A1 `rec-20261015T121438Z-7d436886` (observer off, F144); EXP-008R-G1 `rec-20261015T122211Z-dff71642` (observer on; frames intact, 126,632 instance aggregation losses, F145–F147, [evidence](evidence/EXP-008R_G1_PARTIAL.md)) |
| Latest knowledge block (2026-10-18, local, no game run) | F180–F182: default allocator bindings, separate setter/getter stores/reads and process-heap forwarding established. Saved exact references and raw literals agree at 88/128; no alias completeness. Getter output aliases and intervening callback switches are explicit synthetic counterexamples, not measured game bugs. [Evidence](evidence/POSE_ALLOCATOR_BINDING_2026-10-18.md) |
| Earlier generation block (2026-10-18) | F178/F179: New/Free worker arguments, configurable slots and concrete internal export bypasses. Own model detects delivered ABA/gaps/contradictions; no live-read permission. [Evidence](evidence/POSE_GENERATION_READ_WINDOW_2026-10-18.md) |
| Earlier first-bone block (2026-10-18) | F175–F177: conditional complete World0/Composite0 byte coverage in three fast routes; Route B value contract, A/C source initialization open. [Evidence](evidence/POSE_FIRST_BONE_FAST_2026-10-18.md) |
| Earlier special-callback block (2026-10-17) | F171–F174: constructor-bound descriptor/callback candidate 0x1C780 and conditional prefix. Actual live provenance and indirect Track+8 remain open. [Evidence](evidence/POSE_SPECIAL_CALLBACK_2026-10-17.md) |
| Earlier sample block (2026-10-17) | F167–F170: Sample argument/branch bridge and conditional complete 64-byte stores through eight known direct writer candidates. No unconditional initialized Sample-output span. [Evidence](evidence/POSE_SAMPLE_EXTENT_2026-10-17.md) |
| Earlier initializer block (2026-10-17) | F163–F166: optional lightmap/normalmap/lights-occlusion references and discarded allocator context. Direct R effects bounded; lookup/global aliases and dynamic release target remain open. [Evidence](evidence/HPOSE_INITIALIZER_EFFECTS_2026-10-17.md) |
| Earlier resource block (2026-10-17) | F160–F162: producer/list/H transfer and constructor-bound release candidate; no universally resolved dynamic target. [Evidence](evidence/HPOSE_RESOURCE_RELEASE_2026-10-17.md) |
| Earlier cleanup block (2026-10-17) | F158/F159: three H-field Free arguments, reloaded cleanup range, late selected-H reset and direct outer teardown chain; normal-return path only. [Evidence](evidence/HPOSE_CLEANUP_2026-10-17.md) |
| Earlier allocation block (2026-10-17) | F156/F157: exact 20*n requested bytes, growth/copy/delete/container-store path; requested bytes are not actual heap reserve. [Evidence](evidence/HPOSE_ALLOCATION_2026-10-17.md) |
| Earlier creation block (2026-10-17) | F154/F155: one creation path 0x38E0A0 stores Granny returns in H+0/+4/+8; same O+0x18/+0x1C range and O+0x4C selection connect to 0x38E4D0. [Evidence](evidence/HPOSE_CREATION_2026-10-17.md) |
| Earlier knowledge block (2026-10-16) | F148 audit corrections reproduced; F149 H-record sample path; F150–F153 real-DLL World-Pose contract and own affine helper: within predeclared tolerance, not bit-identical (443 cases). [Evidence](evidence/POSE_CONTRACT_2026-10-16.md) |
| Latest tool change (2026-10-18, local) | Existing sample verifier schema 2: 80 entries/93 ranges, seven Exe imports/twelve exports, three DLL heap imports, eight direct/two allocator-slot/four heap calls and full literal census; 18 tests normal/-O. Own generation model: 19 tests normal/-O. New read-only exact-reference script; no native/Hub change. [Evidence](evidence/POSE_ALLOCATOR_BINDING_2026-10-18.md) |
| Open hypothesis | F136: some paused-frame Granny work recomputes unchanged poses. Not proven; no cache/skip may be built on it. |
| Current assignment | Next bounded proof: internal context DLL 0xE080, WorldPose New/Free calls 0xE165/0xE54D. Trace only the pose identity: does Free use its own New result or an incoming pose that might alias selected H storage? Delimit concrete open aliases; no whole-heap reconstruction. Protected writer/read interval remains separate. No observer, hooks, original execution, recording or cache/skip. [Evidence and next proof](evidence/POSE_ALLOCATOR_BINDING_2026-10-18.md) |
| Suspended / historical | EXP-008R-G2/A2; all game-run orders in [HANDOFF.md](HANDOFF.md); backlog items under "Open tasks" that predate EXP-006 (KNIGHTS, EXP-001…005). The historical 1–2 FPS multiplayer case (F060) is separate and unrecorded. |
| Entry for newcomers | [README](../README.md), [animation knowledge map](ANIMATION_KNOWLEDGE_MAP.md), [STARTER_TASKS.md](STARTER_TASKS.md), [AGENTS.md](../AGENTS.md) |

### Navigation update (2026-10-18)
[Animation knowledge map](ANIMATION_KNOWLEDGE_MAP.md) connects the existing F148–F174 evidence by subsystem
rather than report date. It separates known paths, validity conditions and open edges, with a lifecycle diagram
and maintenance rules. No new binary finding or change to the current fast-route research assignment.
Independent semantic documentation review found no blocking issue; integrated game-free checks pass 15/15 groups.

### Checkpoint notes (2026-10-18)
Allocator F180–F182 establishes defaults, sequential setter/getter binding and default process-heap bridges.
The 216 exact saved refs agree with a separate raw-section literal scan, not a complete alias/writer inventory.
An output alias in the Getter is a concrete synthetic counterexample; configuration change is not a measured
Free or automatic incompatibility. Original-file gates and 18 verifier/19 model tests pass normal/-O.
Next: selected relevance of the internal New/Free bypass in 0xE080. [Evidence](evidence/POSE_ALLOCATOR_BINDING_2026-10-18.md).
Final game-free integrated checks: 16/16 groups; independent final-document review without a substantive blocker.

Generation F178/F179 connects New/Free to configurable allocator callbacks and concrete internal export bypasses.
Own numerical lifecycle reconciliation distinguishes delivered ABA/gaps/overlap, not silent event loss or a safe
read interval. Restarted independent review found a forgotten ambiguous birth; a red regression preceded bounded
quarantine, then 17 tests normal/-O passed. Existing sample verifier: 15 tests normal/-O and original-file gates.
Next: selected-provenance allocator-slot change/forwarding, not a live observer. [Evidence](evidence/POSE_GENERATION_READ_WINDOW_2026-10-18.md).
Final integrated game-free checks: 16/16 groups; independent final-document review reports no substantive blocker.

First-bone F175–F177 closes conditional 64-byte destination coverage in all three fast branches. A fixed-entry-SP
review confirms A/C partial wrapper initialization and unguarded consumer reads; further producer writes remain
unknown, so no engine defect is asserted. Route B has its own source-valid value contract. The next proof is a
bounded byte-observation validity contract, not an automatic reconstruction of all curve formats.
Integrated game-free checks pass 15/15 groups; no new native host or original-code execution.
[Evidence](evidence/POSE_FIRST_BONE_FAST_2026-10-18.md). Earlier checkpoints keep their original scope.

### Checkpoint notes (2026-10-17)
Special-callback F171–F174 separates factory/descriptor provenance from actual live binding. Under the exact
documented bypass and direct-helper conditions, callback 0x1C780 fully writes both arrays through matrix C-1.
The first-bone fast route precedes the count guard; count zero alone is no general no-write proof. Review corrected
an enum comparison misread as a mask test before acceptance. Next: the small known fast target 0x44F40, rather
than recursively reconstructing every track callback. Integrated game-free checks pass 15/15 groups.
[Evidence](evidence/POSE_SPECIAL_CALLBACK_2026-10-17.md).

Sample F167–F170 has conditional direct-writer spans: World and Composite each `[0,64*B)` for the known
first-index-zero Sample subpaths, provided the documented sources, capacity, dispatch and hierarchy are valid.
All eight known candidate target bindings and full matrix stores were independently checked; a Local-source index
misinterpretation was corrected before acceptance. All 15/15 integrated game-free check groups pass.
The special callback and LocalPose production remain open;
normal Sample return alone is insufficient. Next: one descriptor/callback binding, not all animation mathematics.
[Evidence](evidence/POSE_SAMPLE_EXTENT_2026-10-17.md). Earlier checkpoints retain their own scope/context.

Initializer F163–F166 passed all 14/14 integrated game-free check groups and now has bounded functional roles
and explicit write/escape limits. A small reserve/allocator
bridge closed an apparent R-derived ECX escape: the incoming context is overwritten before use. No global Vptr
or lifetime invariant follows. [Evidence](evidence/HPOSE_INITIALIZER_EFFECTS_2026-10-17.md).
Project decision: pivot to initialized pose-output extent rather than automatically descending every resource
lookup. Concrete generation and safe read-window obligations remain open; a complete cache/type reconstruction
is not a universal prerequisite. [Readiness decision](design/POSE_COMPARISON_READINESS_2026-10-17.md).
Earlier checkpoints below retain their original scope/next-step context.

Resource F160–F162 passed 14/14 integrated game-free check groups. It is a constructor-bound candidate result,
not a resolved dynamic call. A fresh review caught
the intervening initializer; its narrow inventory now exposes three exact R escapes instead of assuming Vptr
persistence. The producer-to-list-to-H pointer transfer and candidate mesh/file releases are independently checked.
Next: first escape `0x395E4F -> 0x394350`. [Scope and agent prompt](tasks/HPOSE_RESOURCE_RELEASE_2026-10-17.md),
[evidence](evidence/HPOSE_RESOURCE_RELEASE_2026-10-17.md). Earlier checkpoints below retain their own next steps.

Cleanup F158/F159 passed the final integrated 13/13 game-free check groups. It is a bounded normal-return result,
not full lifetime closure. A future observer must not infer
live poses from O+0x4C alone; it must invalidate its own observed generation at release entry and treat lifecycle
gaps as unknown. No such hook is implemented. Next target: indirect resource release at `0x38E428`.
[Cleanup evidence](evidence/HPOSE_CLEANUP_2026-10-17.md). The allocation checkpoint below predates this result.

Public `origin/main` at `898a394` was merged normally into the local research branch after checkpoint `af14eea`;
the incoming Discord workflow is unchanged. The integrated tree passed 12/12 regular check groups and the own
native host passed 6393 conditions with zero failures. Research remains local; no push or new GitHub CI run.

Creation-to-selection (F154/F155) and allocator-argument/transfer path (F156/F157) are now bounded static results.
Native C++ preparation implements checked address/byte arithmetic only; no original allocator or game computation
is replaced. Next: cleanup candidate `0x38E3C0`, not heap-rounding measurement.
[Allocation evidence](evidence/HPOSE_ALLOCATION_2026-10-17.md),
[native requirements](design/HPOSE_CPP_CONTRACT.md). Earlier checkpoints below retain their own date/context.

### Checkpoint notes (2026-10-16)
First bounded knowledge block completed: audit corrections reproduced/integrated, native World-Pose contract and independent affine Composite helper tested against the real DLL. General bit identity is disproved for the own helper. Next: static Exe H-pose ownership/lifetime trace. No new capture, installation or performance gain. [Evidence and reproduction](evidence/POSE_CONTRACT_2026-10-16.md).

EXP-008/008R captures archived; both observer G1 runs have intact frame files but incomplete instance detail. Independent audit completed in a separate analysis session; no new game run prepared. [Correction and restart evidence](evidence/EXP-008_OBSERVER_CORRECTION.md). Operational protocol history: [HANDOFF.md](HANDOFF.md).

New technical project lead: start with [PROJECT_LEAD_HANDOFF.md](PROJECT_LEAD_HANDOFF.md) (2026-10-16): verified subsystem knowledge, bounded own implementations/differential tests and precise read/write scope. This is the current leadership handover; old G2 sequences remain suspended.

- Current operational checkpoint: **EXP-008R-G1 again partial; G2 suspended**. `rec-20261015T122211Z-dff71642`, speed 90/final pause user-confirmed; 126,632 instance probe failures, intact frame records. Narrow positive evidence: some retained pointers have unchanged observed inputs, others change clocks/offset even paused. F136 remains hypothesis. [G1 evidence and next scope](evidence/EXP-008R_G1_PARTIAL.md). TEST granny off/sample off/full, run id/protocol cleared; no next user recording prepared. Original untouched.
## Done
- Allocator binding 2026-10-18, local: F180–F182; default/API/heap forwarding, 80 entries/93 ranges and exact-reference/literal census. Independent byte/argument/code review and own synthetic switch/alias witnesses; no live read, original execution, native/Hub change or push. [Evidence](evidence/POSE_ALLOCATOR_BINDING_2026-10-18.md).
- Generation/read-window block 2026-10-18, local: F178/F179; 70 pinned entries/83 ranges, seven imports/ten exports, direct/allocator-slot gates. Own 17-test synthetic ledger with bounded quarantine; independent review found and confirmed correction of an overlap-history bug. No live read, original execution, native/Hub change or push. [Evidence](evidence/POSE_GENERATION_READ_WINDOW_2026-10-18.md).
- First-bone fast 2026-10-18, local: F175–F177; three target bindings, route B value contract, A/C explicit source boundary and C>=1 composition. Existing verifier 58 entries/71 ranges, six import/six export gates; 13 tests normal/-O, independent byte/semantic review and parent audit-reader check. No original execution, new native/Hub code or push. [Evidence](evidence/POSE_FIRST_BONE_FAST_2026-10-18.md).
- Special callback 2026-10-17, local: F171–F174; existing sample verifier schema 2, 54 entries/67 ranges, six import/six export gates; 12 tests normal/-O. Independent review plus parent audit-reader checks. Conditional known-writer prefix only; fast route, Track+8 and live-generation obligations remain open. No original execution, native/Hub change or push. [Evidence](evidence/POSE_SPECIAL_CALLBACK_2026-10-17.md).
- Sample output extent 2026-10-17, local: F167–F170; 33 entries/46 ranges, five imports/three exports; nine tests and original-file gates normal/-O. Independent semantic/byte review plus parent audit-reader recheck. Conditional full matrix coverage, no universal initialized Sample span. No original execution, observer/native/Hub change or push. [Evidence](evidence/POSE_SAMPLE_EXTENT_2026-10-17.md).
- H-resource initializer 2026-10-17, local: F163–F166; 20 function fingerprints/24 ranges, nine imports/one table/16 bindings; 15 synthetic tests normal/-O and original verifier pass. Independent review plus parent recheck cover 2907 exported instructions. Four VA/RVA helper labels corrected before acceptance. No original execution, native/Hub change, cache observer or push. [Evidence](evidence/HPOSE_INITIALIZER_EFFECTS_2026-10-17.md).
- H-resource candidate 2026-10-17, local: F160–F162; 15 functions/18 ranges, six imports and one table slot; ten new synthetic tests normal/-O. Independent PE/semantic review and parent byte check cover 1925 instructions. Actual call target, initializer escapes, cache generations and reentrancy remain open. No original execution, native/Hub change or push. [Evidence](evidence/HPOSE_RESOURCE_RELEASE_2026-10-17.md).
- H cleanup 2026-10-17, local: F158/F159, six function/six import checks and eight new synthetic tests normal/-O; independent review confirms 403 exported instruction bytes and the bounded interpretation. Ordinary checks include the new suite. Own native code, Hub, game files/raw data unchanged; no original execution, push or new GitHub CI. [Evidence](evidence/HPOSE_CLEANUP_2026-10-17.md).
- H-container allocation 2026-10-17, local: F156/F157, nine function/five import checks, seven new compiler-free tests normal/-O; standalone byte-request model adds ten literal boundaries (native total6393). Independent semantic review and final Ghidra reproduction agree. Actual heap reserve and pose lifetime remain unproved. [Evidence](evidence/HPOSE_ALLOCATION_2026-10-17.md).
- Native H-pose acceptance 2026-10-17, local: runner independent of Hub/Granny, strict completed JSON and atomic success report, ten negative/positive tests normal and -O, Win32 host in isolated minimal source copy. Review found and closed cross-drive fixture and JSON exponent-overflow gaps. CI step prepared, no push/online CI; allocation research remains next. [Evidence](evidence/HPOSE_NATIVE_ACCEPTANCE_2026-10-17.md).
- H-record creation path 2026-10-17, local: F154/F155, read-only binary verifier with seven function/eight edge fingerprints, game-free rejection tests and a separate MSVC Win32 C++17 range model. No live memory access, original execution, new recording, ownership closure or speedup. [Evidence](evidence/HPOSE_CREATION_2026-10-17.md).
- T2 reader accounting completed locally 2026-10-17: old CLI fails the new output regression, new reader passes. A positive difference with dropped/unknown frame rows is not exclusively a tail; missing/invalid counters fail closed. Existing `quality(meta)`/Silver semantics unchanged. No recording, installation, runtime change or push. The H-pose lifetime assignment remains next.
- T2 independent Sol 6.1 review: 18 reader tests and old-CLI counterexample independently checked; oversized CSV field exposed an uncaught parser error. Lead regression failed before the fix and passes afterward, with 19 reader tests total. See the T2 evidence; no new game finding or publication.
- Discord notices 2026-10-17: `.github/workflows/discord-notify.yml` (same file in the hub repository) posts new and merged pull requests to #changelog and published releases to #announcements through two webhook secrets (`DISCORD_WEBHOOK_CHANGELOG`, `DISCORD_WEBHOOK_ANNOUNCEMENTS`); without the secrets it skips. Message logic tested locally against a stand-in endpoint (new, merged, closed unmerged, draft, release, hostile title, missing secret); not yet run on GitHub, needs the two secrets. No game run, no research content changed.
- Publication 2026-10-17: both repositories public (research `46b14eb2cefa`, hub PR #1 → `d3a763a33777`). GitHub CI green: research `checks` 9/9 (1 case in `test_audit_workdir` skipped, no hub sibling in CI), hub `build-test` 4/4 gating. Locally with hub sibling `--audit --e2e` 11/11. Not run for lack of inputs: raw-data snapshot, audit recount, real-DLL pose test. `sampler_overhead` non-gating and failed locally (5.5 %, 5.2 %). Follow-up: license files reduced to the plain MIT text (scope note → [NOTICE.md](../NOTICE.md)), public entry texts updated. No runtime, observer, algorithm or test change; no game run. Earlier "nothing pushed / no CI run" entries below describe their own date.
- Publication follow-up 2026-10-16: historical commit ids in the audit copy resolve directly (original history) or via `docs/export/EXPORT_MAP.tsv` (clean export) and are otherwise reported as unavailable, never as unchanged; missing raw recordings are named as missing local input (`tools/test_audit_history.py`). `recheck_granny_audit.py` states that it needs the original history. Hub unchanged at `621a9d6`. Local checks only; nothing pushed.
- Publication preparation completed 2026-10-16 (D016): audit copy with one `--work` contract (exports from `<work>/binary`, results and own snapshot baseline in `<work>/results`, reference files untouched; `tools/test_audit_workdir.py`), the disabled hub-source hash check in the audit copy fixed, research repository named `github.com/crycodebaby/Stronghold2PerformanceResearch`; hub `621a9d6` gates the sampler's functional checks and reports only its overhead (`sampler_overhead`, label `timing`). Local checks only, no GitHub CI run; nothing pushed. Open before publishing: the personal author e-mail and the historical user paths in four early commits (clean export prepared locally, not part of the repository).
- Publication preparation 2026-10-16 (D016): English README/CONTRIBUTING/AGENTS, STARTER_TASKS, REPRODUCIBILITY, WORKSPACE, MIT LICENSE, `tools/run_checks.py` + CI workflow (not yet run on GitHub), audit copy under `audits/`; merged with `main` `160f141` (pose block) and re-checked; hub branch `publish-prep` adds licence notices, CTest registration, CI and docs on top of `32ebc38` without runtime change. Nothing pushed.
- [x] Technical-lead first knowledge block (2026-10-16): F148–F153, [pose evidence](evidence/POSE_CONTRACT_2026-10-16.md), `tools/granny_pose.py`, own affine implementation and x86 host. 10 export/ABI checks, 30 function fingerprints, 142 layout cases, 1,620 differential cases / 238,768 components plus a noncommuting oracle, 0 failures under predeclared criteria. 443 cases differ in float rounding; counterexample checked with exact rational arithmetic. Two integration tests pass. Nine audit model tests and real A1/G1 recount repeated in an ignored copy, reference unchanged. No Hub/installation/raw-data changes; no cache/skip permission.
- Independent fresh-agent assignment completed on 2026-10-16: [scope](tasks/INDEPENDENT_AUDIT_2026-10-16.md), published copy with provenance in [audits/2026-10-16-independent/](../audits/2026-10-16-independent/README.md). Historical audit checkpoint: strict 1,503-row result retained; equality/pose-link/tail corrections then pending. **Now integrated and reproduced as F148; pose-buffer block F150–F153.** Original repositories unchanged by that audit; later changes to this repository are explicitly documented here. Result observer still not implemented or ready for capture.
- User context clarified 2026-10-16: historical 1–2 FPS event was human multiplayer on a large/high-resource/heavily built map with several hundred troops (counts uncertain), not current REAL_LAG_257 single-player. Keep these cases separate (F060); no need to wait for AI attacks to investigate the current animation candidate.
- [x] EXP-008 **preparation only** (no in-game measurement yet): signatures F137, deform call without model instance F138, clock sources F139; data contract FORMATS/GRANNY_OBSERVER.md + D014; hub `e3ea53e` observer (switch `granny`, default off) + `grannyobs.py` + `variant.py granny`; checks without the game F140 (incl. ingest stem fix); installed in TEST with `granny=0`, plan EXP-008-A1, backup `_backup_before_EXP-008_20261015`; protocol fixed in EXPERIMENTS.md
- [x] EXP-007 closed: wording corrected, F135 recount 134/120 (was 169/146 = keys with Δ > 0 incl. pages), `funcsamples.py --delta-counts`; analysis state evidence/ANALYSIS_STATE_EXP-007.md; Ghidra project backup (zip, sha256 `48d50246…`); commits `68b8868`, `a31a5c7`
- [x] EXP-007 function hotspots A1–F1–F2–A2 (EXPERIMENTS.md): function sampler F130; granny2 in Ghidra + 3 functions created F131; candidates F132–F135 (deform loop under `SseDeformPWNT3432I`, B-spline/knot helpers, exe helper `FUN_004E3530`); hypothesis F136; tools `ExportFunctions.java`, `AddressContext.java`, `InstructionStats.java`, `CreateFunctionsAt.java`, `AnnotateFunctions.java`, `tools/funcsamples.py`
- [x] EXP-006 army view running vs paused, sampler off/module A1–B1–B2–A2 (EXPERIMENTS.md): sampler bias +0.6–1.3 ms/frame (F125); running 32.8 vs paused 25.1 ms without sampler (F126); render-thread module split (F127); difference mainly in Stronghold2.exe (F128); granny2 constant ≈ 11 ms (F129, Hypothese). Sampler checked first (F122–F124)
- [x] EXP-INGAME: 3 real-game captures imported and verified; user confirms speed 90. Full mode records cleanly, Alt-Tab/reset and END without recording passed. No performance gain or subsystem attribution established (F118–F121).
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
- [x] Protection fixes (work order "Schutzluecken", D013, F114–F116, evidence `docs/evidence/ACCEPTANCE_2026-10-15.md`): benchmark use = integrity + description (`reference-v1`) + user release, apart, with coded rejections; pause per phase; one integrity check before every use of bronze (damaged → exit 4, silver kept but `INVALID`); write lock `data/.sh2perf.lock` (real-process tests); manifest names/roles validated, cleanup contained; hub threads must really end before unload (`Lifecycle`), unload crash fixed (8/8 in the stand-in, was 1/4). Tests: `test_hardening` 31, `test_import_safety` 45, `lifecycle_test`, `capture_test`, `e2e_standin`; patches `pipeline_protections.patch` / `hub_lifecycle.patch` for separate review. Silver of the 3 old captures re-derived with 2.1.0 (bronze identical)

## Open tasks (ordered)
00000. **Current only priority: H-pose cleanup/lifetime boundary.** Follow the three Free-import references in `0x38E3C0` to the exact H fields, traversal and caller paths. Distinguish array relocation from pose destruction; no UAF or generation claim from pointer reuse alone. [Acceptance and result decisions](evidence/HPOSE_ALLOCATION_2026-10-17.md). No new game capture or observer production changes. Lower historical tasks do not override this order.
Backlog in the order it was written; items 00–7 predate EXP-006 and are not the current order (see "Current status").
0000. **EXP-008R: A1 archived; G1 partial; G2/A2 suspended.** Correct observer state/history design and add real-workload stress test before any new game run. [G1 evidence/next scope](evidence/EXP-008R_G1_PARTIAL.md). No cache/skip/engine patch; F136 remains hypothesis. A new observer build requires fresh matching controls.
000. **EXP-007 done** (F130–F136): granny2 SSE deform loop `FUN_50008810` large cost in both states (paused 4.39/4.46 ms well repeated, running 3.61/4.93 ms), curve helpers ≈ 2 ms; in flat samples the exe running-only cost is spread over 134/120 known functions (corrected from 169/146), a shared call path is not excluded. EXP-008 prepared (task 0000).
000b. **EXP-006 done (previous)** (4 valid runs + pilot, F125–F129): sampler bias 2–5 %; running +7.7 ms vs paused (A runs); running − paused ≈ 5.5 ms in Stronghold2.exe; granny2 ≈ 11 ms per frame in both states. **Next: EXP-007 function mode, 2 runs** (HANDOFF.md), then function analysis of reproduced exe/granny2 candidates only.
00. Basic in-game acceptance passed (EXP-INGAME, F118–F121). Still untested in game: END during recording, process exit while recording, startup/stop overhead. These are separate from the next engine measurement. See HANDOFF.md.
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
See "Current status" above and the current top of [HANDOFF.md](HANDOFF.md): static cleanup/lifetime boundary after the bounded allocation result. Old in-game/KNIGHTS/G2 instructions below are history, not current work orders. No user recording requested.

## Risks / unknowns
- Known limits of D013: the DLL stays mapped after hook installation (hub update = game restart); END deactivates, it does not unload (re-activation or a new hub build = game restart); a permanently blocked background thread defers the deactivation for the rest of the process; a normal game exit does not finalize an open recording (F117), only F9/END do; MinHook trampolines are never freed; the 2 s wait for the render thread to drop ImGui can end with ImGui left allocated (logged) if the game stops calling EndScene; hooks of the counter slots are not drained, they stay valid because the module stays loaded; the write lock is per machine (local file lock), not for a network share; legacy captures cannot be integrity-checked (no import record); name rules cover Windows names only; reference profile `reference-v1` is deliberately small (no hardware, graphics settings, V-Sync, hub-dirty or save-game identity); `sampler_test`'s 5 % overhead check is noisy near its threshold
- D012 basic manifest/hash/import operation is verified in 3 real-game captures (F118); startup/stop overhead is unmeasured. Speed 90 is user-confirmed, not read from memory. REAL-B remains legacy.
- Old recordings (no manifest) stay `legacy`/unverified: modes and capture health are unknown for them, not "all on / OK"; the 3 existing captures cannot become benchmark-usable without new runs
- `ingest.py` no longer deletes sources: `SH2Perf_out` grows until the user cleans it; a stale `captures/.staging/<id>/` after a crash is discarded by the next import of that id
- D011 full mode passed basic real-game recording and Alt-Tab/reset (F118/F120); min mode and comparative overhead remain untested in the game. No old/new speedup claim.
- `min`/overlay off: no EndScene timing, so `cpu-side` is not comparable between modes; the game gives no on-screen recording state without the overlay (tones + log only; `beep` can be switched off)
- Ring 8,192 frames (~0.9 MB of the 2 GB address space, F090 headroom is small but far above this); a capture thread starved for > 2 minutes at 60 FPS would drop frames — reported, but the run is then invalid
- Which part of the old hub work caused the 1 s hitch in the stand-in (thread poll vs file flush vs VA query) was not isolated (F106)
- Sampler did run in Stronghold 2 (EXP-006/007); measured module-sampler bias F125. Thread suspension/overlay/driver neutrality is not fully proven; use measured controls, not the older synthetic-only F103 checkpoint.
- `latest.json` is only a pointer (D012); recordings are identified by their manifest. The hub log is shared by all recordings of a session and has no integrity guarantee
- F082 (cause of launcher crash) unconfirmed: launcher not re-run with fixed hub (low priority, proxy is default)
- DXVK behind the proxy only tested in the stand-in program
- Steam overlay hooks D3D9 as well (F086): may distort `present_ms`
- Menu 1,351 MB, early 8-player game 1,497 MB of 2,048 MB VA (F090): watch `va_used_mb` in big battles
- Whether direct start needs the Steam client running: untested (F057)
- Scenario editor may not allow enemy units → fallback in EXPERIMENTS.md
- `sym.py addr` only knows virtual functions until ExportFunctions exists

## Operational checkpoint (2026-10-15, superseded) — EXP-008 correction
Historical checkpoint (before EXP-008R; superseded by the current top): G1 `rec-20261015T111010Z-d6bf1a9b` partial; corrected hub `32ebc38a05ea`, metadata v2, 8.52 MiB allocation; Silver 2.2.0 re-derived 20 captures. At that time no corrected-build game result existed. Later corrected-build G1 is also partial (F145), so this old preparation instruction must not be resumed.
