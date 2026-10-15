# EXP-008R-G1: verified observations, incomplete coverage

> Kurzfassung: G1 preserves all frames and demonstrates repeated animation calls during the user-confirmed pause, including stable observed inputs for retained pointers and changing inputs on others. Instance detail is again incomplete; no population percentage, redundant-work verdict, patch or overhead result follows.

## Recording and validity
- Capture `rec-20261015T122211Z-dff71642` (`20261015_142211`), imported and manifest-verified (7 files), finalized by user_toggle. 2,542 frames / 75.24 s; zero frame drops, write losses, write errors, observer frame-row drops or offset-read faults. Sources preserved.
- Hub `32ebc38a05ea`, clean; session/prepared DLL `4a56b62e…`, exe `f3ccdf9b…`, proxy `13c89519…`; full / sample off / granny on. All six import slots patched. Owner/render TID 49360; zero foreign-thread calls.
- User explicitly confirms speed 90 and the final section continuously paused. Annotated game_speed=90 and phase 3 paused=true only; no suitability release added.
- Marker 1 running: 864 frames / 30.265 s, mean 35.029 ms (28.55 FPS), 1% low 16.28 FPS, p50/p99 33.82/53.25 ms, cpu_side 34.78 ms, Present 0.25 ms, DIP 2,473.13, triangles 522,044.32. Primitive counts vary in the final 20 frames.
- Marker 3 confirmed pause: 1,352 frames / 35.158 s, mean 26.004 ms (38.46 FPS), 1% low 25.53 FPS, p50/p99 24.73/36.50 ms, cpu_side 25.78 ms, Present 0.23 ms, DIP 2,492.00, triangles 522,749 (constant throughout). Marker 0/2 are warm-up/transition, excluded.
- A1 means 34.241/25.446 ms; G1 differences +0.788/+0.558 ms are descriptive only. One off/on pair, no G2/A2, slightly differing scene counters/durations: no observer-overhead verdict. Neither running nor paused frame times alone identify a subsystem.

## Observer failure: correction insufficient in the game
- 126,632 failed instance aggregations, all classified as probe failures; zero actual-capacity failures. First at frame 911, about 5.847 s into capture, marker 1; 6,508 retained keys first seen by then.
- Final occupancy 8,134/8,192 keys; maximum probe 128. Marker 1: 26,281 failures across 804/864 frames; marker 3: 89,232 failures across every frame. Thus there is no complete paused window to reclassify as valid.
- Other tables: 88 deformers (max probe 1), 2,208 poses (12), 1,247 composite pointers (9), no failures. Allocated 8,929,560 bytes. Of the 8,134 retained keys, 5,919 have no recorded sample call anywhere in this recording (203,180 clock calls in those rows). This is retained-key evidence, not the size of the unobserved population or a memory-leak claim.
- 708 retained keys have observed frees; 1,569 free-instance calls overall. These counts do not establish live objects, lifetime count or temporary-object semantics.
- Silver marks observer detail partial and blocks benchmark use despite intact frames. G2/A2 are suspended; no new recording requested on this build.

## Positive observations that survive incomplete coverage
- Whole-boundary call counts precede table lookup; frame rows are complete. During confirmed pause each frame has 3,400 clock, 2,842 sample and 2,185 deform/composite calls. Totals: 3,842,384 sample and 2,954,120 deform calls in marker 3. These count calls, not visible soldiers, costs or unique objects.
- For subset analysis, retain marker_slot=3 instance rows with frees=0 and used_after_free=0. Existing table keys are never evicted and remain at their inserted probe position (code `Find`, hub `32ebc38`); failures concern keys not yet retained. Comparisons for these retained keys can support positive observations, while coverage of all model keys remains incomplete. Unobserved frees/reinitialisations remain a limit.
- 1,503 such pointer rows have sample_calls > 1,000 and all_observed_same == sample_calls. Example `0x4E42CEBC`: 1,351 sample calls in 1,351 frames, all_observed_same=1,351, ch_offset=0. This demonstrates repeated calls with identical observed clock/input values for these rows; it is not proof of identical pose contents or results.
- 135 such rows have clock_changed > 0 during pause. Example `0x34A93C3C`: sample_calls=35,142 over 1,352 frames; repeat_in_frame=33,790, clock_changed=70,284, ch_offset=35,142, all_observed_same=0. The same observed pointer is sampled about 26 times per paused frame with changing clock/offset. One pointer cannot simply be equated with one on-screen soldier or one fixed pose per frame.
- The recorded sample return site is RVA `0x0038E6DF`, VA `0x0078E6DF`, in exe `FUN_0078E4D0` (F139). This connects the dynamic observation to an analysed code location; no source-level function name is invented.
- Deform links during pause: 2,947,360 same-frame, 6,760 none, zero older/ambiguous. Full instance linkage is not claimed. Deformer rows do not establish historical per-model ownership or unchanged matrix contents.

## Interpretation and next scope
- Verified narrow statement: some retained model pointers repeatedly reach animation sampling with unchanged observed values during pause; others do not. F136 remains a hypothesis, pending complete independent repeat plus hidden-input/result checks. Not all pointer keys receive a constant clock argument during pause. This does not prove animation time advances: different frozen actor poses could be submitted through a shared pointer (hypothesis).
- Not established: redundant calculations, safe caching/skipping, attributable saved milliseconds, function-inclusive time, troop ownership, or improvements to gameplay/performance. Control clocks/weights and memory behind pose/matrix pointers are not observed.
- Next tooling scope: separate history/aggregation from bounded active comparison state; avoid letting unsampled clock-only history exhaust the state needed for sampled models. Preserve identity/lifetime uncertainty and explicit losses. Reproduce a >8,192-key mixed clock/sample workload in tests before another user run. No engine patch and no silent capacity increase as an acceptance substitute.
- TEST after analysis, game closed: granny off, sampler off, full; experiment/protocol cleared, scenario REAL_LAG_257 and planned speed 90 retained. DLL unchanged. Original and raw captures untouched.

## Reproduction
- `ingest.py verify rec-20261015T122211Z-dff71642`; `grannyobs.py captures/rec-20261015T122211Z-dff71642` shows partial and intentionally suppresses population ratios.
- Numbers above are direct CSV sums/filter counts, not a replacement global reader result. Filters and example keys are specified above; inspect frame rows for first drops, sum boundary counters by marker, and compare each retained instance row's sample_calls/all_observed_same/free flags. No extrapolation from retained rows.
