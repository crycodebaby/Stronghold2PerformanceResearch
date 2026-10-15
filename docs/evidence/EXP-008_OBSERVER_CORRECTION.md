# EXP-008 observer correction and restart

> Kurzfassung: G1 showed incomplete instance aggregation. This records the diagnosed limits, bounded correction, tests and the new same-build control plan. No in-game success or performance improvement is claimed for the correction.

## Diagnosis from preserved G1
- Capture: `rec-20261015T111010Z-d6bf1a9b`, hub `e3ea53e5d9f7`, speed 90 user-confirmed.
- 498,935 failed instance aggregations; 4,096 retained distinct pointer keys by recording end. These are failures, not that many distinct models.
- First detail-drop frame: 1151 (first recorded frame: 1135). Only 3,176 retained keys have first_frame <= 1151. Thus failures began before the 4,096-slot table filled: bounded probing was already exhausted. At the end capacity was also exhausted. Retained keys cannot reveal the missing unique-key population.
- Old hash kept allocator-alignment patterns in low bucket bits. Synthetic address patterns reproduce early collisions; this does not identify the game's allocator or object creation policy.
- 228 retained pointer rows have observed frees (unique keys, not lifetimes); 1,178 free calls in total. No live-model population is inferred from these totals.

## Correction
- Mix high and low pointer bits; keep a finite probe bound of 128. Raise retained instance capacity to 8,192. Report used slots and separate probe/capacity/invalid-key failures for all four tables.
- Allocation: 8,929,560 bytes with a compile-time ceiling of 12 MiB. No allocation, file writes, locks or waits added to hook bookkeeping. Finite capacity remains a constraint; real-game sufficiency is untested.
- Observed free starts a fresh comparison history and invalidates old pose links. CSV rows still combine pointer lifetimes, so stable-instance analysis excludes free/reuse rows.
- Observer metadata v2; original v1 captures remain readable. Silver 2.2.0 distinguishes intact frame files from complete observer detail and blocks reference use on partial/unknown detail.
- Remove last-pointer historical ownership grouping and vertex-total estimates inferred from min/max.

## Verification without Stronghold 2
- Regression cases were introduced before the fix: the old implementation failed five assertions for capacity/collisions and free/reuse comparisons.
- Corrected `granny_observer_test`: 6,000 distinct aligned keys retained with zero loss (maximum probe 43); 128 formerly colliding keys retained losslessly; every original call forwarded; fresh comparisons after free; stale pose link rejected; deliberate overflow remains visible.
- Observer test, capture test (11 groups) and lifecycle test (5 groups): passed. Python suites: observer quality 4, import safety 46, ingest 9, variant 16, hardening 31, A/B 10: passed.
- Full Win32 Release build passed. Proxy → hub → stand-in → manifests → import → END passed with observer configuration off and on. The stand-in has no Granny imports: actual six-hook forwarding is covered by the dedicated fake-Granny test, not by that end-to-end test. Final clean build id: `32ebc38a05ea`.
- Silver 2.2.0 re-derived all 20 archived captures after integrity checks; zero damaged. G1 now has `quality.granny_observer.status=partial` and blocker `observer_detail_partial`; no raw files were changed.

## Installation and rollback
- No Stronghold2 process was running. Backed up prior hub DLL, proxy, ini and prepared record to `../Stronghold 2 - TEST/_backup_before_EXP-008R_20261015/`, verified each copy and wrote SHA256SUMS.txt. This contains the pre-restart observer-off configuration, not the earlier G1-on configuration.
- Installed via `variant.py baseline`; proxy byte-identical (`13c89519…`), game exe unchanged (`f3ccdf9b…`), genuine granny2.dll unchanged (`94d56fd7…`). Original installation untouched.
- Installed hub SHA-256 `4a56b62e5e9e2d4b8794860d95d74b898840c00c23144bc63e2bbc13c1724127`; matches Release build. At installation: baseline/system, hub on, granny off, sample off, full, plan EXP-008R-A1 / GRANNY_OBS_R1 / REAL_LAG_257 / 90, no planned pause value. Current state after A1 is below.
- Rollback while game closed: restore the four backed-up files, then inspect `variant.py status` (old hub will intentionally differ from the newer build). Observer-only off: `variant.py granny off`.

## Restart protocol
- Old A1 and partial G1 stay preserved as historical captures; do not mix the corrected build with their overhead control.
- New run ids: `EXP-008R-A1` off, `EXP-008R-G1` on, `EXP-008R-G2` on, `EXP-008R-A2` off. Protocol `GRANNY_OBS_R1`; sampler off; full mode; same installed build across all four runs.
- Save `LAG_217_Reiter`, scenario `REAL_LAG_257`, 257 troops, speed 90. Camera unchanged, mouse centred. Load fresh before each run; wait 10 s.
- Initial target: F9; wait ~5 s; F8; running 20 s; F8; pause game; wait ~3 s; F8; paused 20 s; F9; wait until recording ends; quit normally. **Timing amendment before G1**: A1 actually recorded ~29 s per measured phase; remaining G1/G2/A2 target **30 s running / 30 s paused** to match it. Other steps and acceptance thresholds unchanged; A1's deviation is retained in the record.
- After every run verify manifest/file integrity, phase duration/scene, actual speed confirmation. Observer runs additionally require zero detail losses, patched imports and documented thread coverage. A failed run is retained and labelled, never discarded or silently substituted.
- Agent changes switches only while the game is closed; user starts the next run after TEST is reported ready. G2 proceeds only if G1 is complete; otherwise diagnose again before more user recording.
- Overhead uses the existing EXP-006/008 A/B rule after A2. F136 stays a hypothesis; unchanged observed arguments do not establish unchanged results or removable work.

## A1 result and G1 preparation
- `rec-20261015T121438Z-7d436886` (`20261015_141438`): imported, all 3 files and manifest verified, finalized by user_toggle; 2,407 frames / 70.43 s; zero dropped frames, write losses or errors. Speed 90 user-confirmed and annotated. Sources retained unchanged.
- Recorded software: hub `32ebc38a05ea` clean, DLL `4a56b62e…`, exe `f3ccdf9b…`, proxy `13c89519…`; prepared and session identities agree. Full, sampler off, granny off as intended.
- Marker 1 (running): 847 frames / 29.002 s, mean 34.241 ms (29.2 FPS), 1% low 17.2 FPS, p50/p99 32.90/51.32 ms, cpu_side 33.98 ms, Present 0.26 ms, DIP 2,504. Primitive counts vary, including the final 20 frames.
- Marker 3 (pause consistent with counters): 1,139 frames / 28.983 s, mean 25.446 ms (39.3 FPS), 1% low 25.1 FPS, p50/p99 24.29/37.30 ms, cpu_side 25.21 ms, Present 0.23 ms, DIP 2,504. Exactly one primitive count (525,497) throughout. No automatic pause observation or user pause annotation is invented.
- Marker 0 warm-up 6.384 s and marker 2 transition 6.099 s are excluded. Pause transition occurs in marker 2; no apparent paused tail in marker 1. Log confirms END only after recording finished, with orderly deactivation.
- Phase verdicts: running and paused remain **unclear by subsystem**. Pause reduces mean frame time by 8.795 ms at nearly equal draw-call count; this alone does not separate simulation, animation, rendering preparation or driver costs. No model arguments recorded in A1, no test of F136, no performance-gain claim.
- No earlier observer-on capture exists for this corrected build; old A1/G1 are historical and not a same-build overhead pair. Full reference release is still unknown, pause per phase unconfirmed in annotations; no suitability release was added. This is a documented experiment control, not a released general benchmark.
- After confirming the game was closed: `variant.py granny on`, plan EXP-008R-G1 / GRANNY_OBS_R1 / REAL_LAG_257 / 90. Sampler off/full, installed binary still matches build; no DLL copied. TEST ready for G1. Require complete observer detail before preparing G2.
