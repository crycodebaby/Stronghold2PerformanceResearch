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
- Installed hub SHA-256 `4a56b62e5e9e2d4b8794860d95d74b898840c00c23144bc63e2bbc13c1724127`; matches Release build. Status: baseline/system, hub on, granny off, sample off, full, plan EXP-008R-A1 / GRANNY_OBS_R1 / REAL_LAG_257 / 90, no planned pause value. TEST is ready for the new A1; no corrected-build game capture yet.
- Rollback while game closed: restore the four backed-up files, then inspect `variant.py status` (old hub will intentionally differ from the newer build). Observer-only off: `variant.py granny off`.

## Restart protocol
- Old A1 and partial G1 stay preserved as historical captures; do not mix the corrected build with their overhead control.
- New run ids: `EXP-008R-A1` off, `EXP-008R-G1` on, `EXP-008R-G2` on, `EXP-008R-A2` off. Protocol `GRANNY_OBS_R1`; sampler off; full mode; same installed build across all four runs.
- Save `LAG_217_Reiter`, scenario `REAL_LAG_257`, 257 troops, speed 90. Camera unchanged, mouse centred. Load fresh before each run; wait 10 s.
- F9; wait ~5 s; F8; running 20 s; F8; pause game; wait ~3 s; F8; paused 20 s; F9; wait until recording ends; quit normally.
- After every run verify manifest/file integrity, phase duration/scene, actual speed confirmation. Observer runs additionally require zero detail losses, patched imports and documented thread coverage. A failed run is retained and labelled, never discarded or silently substituted.
- Agent changes switches only while the game is closed; user starts the next run after TEST is reported ready. G2 proceeds only if G1 is complete; otherwise diagnose again before more user recording.
- Overhead uses the existing EXP-006/008 A/B rule after A2. F136 stays a hypothesis; unchanged observed arguments do not establish unchanged results or removable work.
