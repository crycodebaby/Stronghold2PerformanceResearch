# REPRODUCIBILITY — what an outside developer can re-check

> Kurzfassung: Which checks run without the game, which need your own Stronghold 2 installation, and which results depend on unpublished local raw data or the Ghidra database. Local results from fresh clones on 2026-10-16/17; GitHub CI runs of the first published state (2026-10-17) in their own section.

## Three classes of checks

| Class | Needs | Published? |
|---|---|---|
| **A — no game** | Windows, Python ≥ 3.12; native hosts/hub also VS 2022 Build Tools + CMake | own H-record host needs this research repo only; hub checks need its separate repo |
| **B — own game** | your own Stronghold 2 **Steam 1.5** installation (exe SHA-256 `f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b`, `granny2.dll` `94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd`), a TEST copy of it, optionally Ghidra 12.1.4 | game files are never published; you bring them |
| **C — local raw data** | the original recordings in `captures/`, the project's Ghidra database, the audit's `work/` exports | not published (personal paths in logs, game-derived disassembly, size) |

## First published state (2026-10-17): what ran where

Research `main` `46b14eb2cefa`, hub `main` `d3a763a33777` (runtime sources equal to `32ebc38`).

| Kind | What | Result |
|---|---|---|
| GitHub CI, game-free | research `checks` = `tools/run_checks.py` without `--audit`/`--e2e`: [run 38983278177](https://github.com/crycodebaby/Stronghold2PerformanceResearch/actions/runs/38983278177) | 9/9 check groups OK. Inside `test_audit_workdir` 1 case skipped: `test_observer_model_writes_only_into_work` needs the hub source `../Stronghold2AnalyseHub/Stronghold2AnalyseHub/core/granny_observer.cpp`, and the workflow checks out this repository only |
| GitHub CI, game-free | hub `build-test` (Win32 build, `ctest -LE timing`): [push 621a9d6](https://github.com/crycodebaby/Stronghold2AnalyseHub/actions/runs/38983295967), [PR #1](https://github.com/crycodebaby/Stronghold2AnalyseHub/actions/runs/38983296023), [`main` d3a763a](https://github.com/crycodebaby/Stronghold2AnalyseHub/actions/runs/38983478344) | build OK; 4/4 gating tests OK in each run |
| Local, extra inputs (hub sibling, desktop) | fresh clones of both published states side by side: `run_checks.py --audit --e2e` | 11/11 OK, including the case skipped in CI (6/6 in `test_audit_workdir`), audit model equal to the reference, stand-in end-to-end run OK |
| Not run (inputs not published) | `audit_data.py --snapshot before` · `recheck_granny_audit.py` · `test_granny_pose.py` | stop with "Missing local input" · "Original history required" · "Run tools/granny_pose.py first" (needs your own `granny2.dll`); these are not passes |
| Non-gating overhead test | hub `sampler_overhead` (label `timing`) | CI step green in all three runs, no number in the log (`ctest --output-on-failure` prints output only on failure); local fresh clones 2026-10-17: **5.5 % and 5.2 %, above the 5 % threshold, failed**. Not a performance acceptance |

None of these runs touches the game. They show neither a performance change nor behaviour inside Stronghold 2.

## Checks and their last result

Local allocation follow-up: [H-container byte request/transfer](evidence/HPOSE_ALLOCATION_2026-10-17.md) adds seven
compiler-free tests to normal checks, nine function/five import checks against matching own game files (read-only),
and ten own native byte-arithmetic witnesses. Native total is now6393; earlier6383 results below retain their dated
acceptance meaning. No original function execution or additional game capture.

Local native-acceptance follow-up: [result contract and failure tests](evidence/HPOSE_NATIVE_ACCEPTANCE_2026-10-17.md).
`test_hpose_native.py` is part of normal Python checks (ten tests, no compiler). `hpose_native.py` is an additional
mandatory Win32 workflow step; standalone source-copy run passed locally. This workflow change is not yet pushed or
verified on GitHub. The original published-state CI results below remain historical.

Local follow-up 2026-10-17, not published: the [H-record creation block](evidence/HPOSE_CREATION_2026-10-17.md)
adds `tools/test_hpose_creation.py` (class A: six synthetic verifier tests), `tools/hpose_native.py` (class A:
MSVC Win32 own range/layout host, no game inputs), and `tools/hpose_creation_verify.py --exe <exe> --dll <dll>`
(class B: read-only matching original files). New static Ghidra checks use a separate project copy; no game run.
The result counts in the dated tables below describe their earlier revisions, not these new local checks.

All class A rows were run on 2026-10-16 from fresh clones without build folders or databases (Windows 10, Python
3.14.3, CMake 4.4.4, MSVC 19.44, hub `publish-prep` whose runtime sources equal `32ebc38`).

| Check | Command | Class | Result 2026-10-16 |
|---|---|---|---|
| Hub Win32 build | `cmake -S . -B build -A Win32` + `cmake --build build --config Release` | A | OK, 0 compiler warnings |
| Hub native tests | `ctest --test-dir build -C Release -LE timing` (capture, lifecycle, Granny observer with fake DLL, sampler functional checks) | A | 4/4 OK; a forced functional failure (`SH2HUB_SAMPLE_MS=1000`) makes `sampler_functional` fail as intended |
| Hub sampler overhead | `ctest ... -L timing` (`sampler_overhead` = `sampler_test --checks overhead`) | A, hardware- and load-dependent, reported, not gating | Varies: repeated runs on 2026-10-16 measured 3.8–6.3 % (one pass, most above the 5 % threshold) while other work ran on the machine (load is a possible, unproven cause); all functional checks passed in every run. Earlier results 2–4 % (F103) and 4.6–5.1 % (F123). Threshold unchanged |
| Python suites + docs lint | `python -I tools/run_checks.py` (incl. `test_audit_workdir`, `test_audit_history`) | A | 9/9 OK; with `--audit --e2e` 11/11 OK; in the clean export 9/9 and with `--audit` 10/10 |
| Audit observer model | `python -I tools/run_checks.py --audit` | A (needs hub source equal to `32ebc38`) | 9/9 OK in a temporary work dir, results equal to the reference `repro_results.json`; a changed hub source is rejected (this check was ineffective in the first published copy, see the audit README) |
| Audit work-dir contract | `python -I tools/test_audit_workdir.py` | A | 6/6 OK (6/6 fail against the previous scripts) |
| Historical commit ids in the audit copy | `python -I tools/test_audit_history.py` (temporary git repos: original, rewritten, missing, ambiguous mapping) | A | 7/7 OK (7/7 fail against the previous script) |
| End-to-end stand-in | `python -I tools/run_checks.py --e2e` | A (needs hub build + interactive desktop) | E2E OK |
| Python 3.11 | same suites | A | `test_import_safety`, `test_hardening` fail (`os.path.isjunction` is 3.12+) |
| Install hub into a TEST copy | `python -I tools/variant.py baseline`, `status` | B | not re-run for publication |
| In-game recording, import, evaluation | EXPERIMENTS.md protocols, `ingest.py`, `grannyobs.py`, `ab_compare.py` | B | not re-run; last real runs 2026-10-15 |
| Granny pose contract host (F150–F152) | `python -I tools/granny_pose.py [--dll <your granny2.dll>]`, then `tools/test_granny_pose.py` | B (real `granny2.dll` of your install, MSVC/CMake; own generated data only, no game start) | `granny_pose.py --dll <copy of the local Steam 1.5 granny2.dll>` from a fresh clone: 10 export/pop checks, 30 fingerprints, 142 layout + 1,620 differential cases, 0 failures, 443 rounding cases, max abs 1.53e-5 (= F150–F152). `test_granny_pose.py` not run: it reads `granny2.dll` from the sibling `Stronghold 2` folder, absent in the clean clone |
| Full audit with new exports | `powershell -File audits/2026-10-16-independent/run_audit.ps1 -ExportBinary -Work <dir>` | B + C (game files, raw recordings, Ghidra 12.1.4 and the project database) | not re-run; the work-dir handover is covered by the class A test above |
| Audit recount in an isolated copy (F148) | `python -I tools/recheck_granny_audit.py --audit-root <audit workspace>` | C (needs the audit's local `work/` exports and our raw recordings) and the **original** local history (its pinned scripts diff against `02bce97`); in a clean export it stops with "Original history required" | not re-run for publication |
| Static binary facts (RVAs, signatures, call sites) | `ghidra_scripts/*.java` headless on your own exe/DLLs, `audits/.../verify_binary.py` | B | not re-run for publication |
| Recount of A1/G1 numbers | `audits/.../audit_data.py`, `ingest.py verify` | C | not possible without the raw recordings |

## Which results are only partly reproducible without our raw data

- **All in-game numbers** (F096–F147, EXPERIMENTS.md results: frame times, module shares, call counts, the 126,632
  observer losses, the 1,503 pointer rows) come from recordings in `captures/`, which stay local. Published are only
  derived values: `data/index.jsonl` (one metrics line per recording), user annotations in `data/annotations/`, and the
  numbers quoted in the docs. `data/silver/` is not in git and can only be rebuilt from the raw files. An outside
  developer can repeat the **protocols** with their own game copy and compare distributions, but cannot re-hash or
  recount our recordings. Expect different absolute values on other hardware (our recordings: Ryzen 9 5900X,
  RTX 5070 Ti, see `data/index.jsonl`).
- **Static analysis facts** (function addresses, sizes, call sites, signatures) are reproducible with your own Steam
  1.5 files and the published Ghidra scripts, but the Ghidra database is not published. Function boundaries depend on
  Ghidra version (12.1.4), auto-analysis options and the manual edits listed in
  [evidence/ANALYSIS_STATE_EXP-007.md](evidence/ANALYSIS_STATE_EXP-007.md).
- **The independent audit**: its observer model runs anywhere (class A); in a clean export of this repository the
  historical assignment ids resolve through `docs/export/EXPORT_MAP.tsv`, but a snapshot still needs our raw recordings
  and stops with "Missing local input" without them; its recounts need our raw data (C); its binary
  checks need your own game files plus fresh exports (B). Details in
  [audits/2026-10-16-independent/README.md](../audits/2026-10-16-independent/README.md).
- **The pose block** (F149–F153) needs your own `granny2.dll` (SHA-256 above) and, for F149, the exe and Ghidra
  exports; the host never uses game assets or recorded pointers, so it is class B, not C.
- **User-confirmed context** (game speed 90, paused phases, the historical multiplayer report F060) cannot be
  re-checked at all; it is recorded as user statement, separate from measured values.

## Environment pitfalls found while checking

- Clone to a short path: MSBuild stops with "path exceeds 260 characters" when the hub build folder is deep inside
  `%TEMP%`.
- Python 3.12 or newer is required; 3.14.3 is the verified version.
- `core.autocrlf=true` checks out CRLF files; anything that hashes source files must normalise line endings (the
  audit copy does, see its README).
- The sampler's overhead threshold depends on hardware and load; only that entry (`sampler_overhead`) is non-gating.
