# Acceptance evidence: H1-H3, protection fixes and the prepared build (2026-10-15)

> Kurzfassung: Belege der Abnahmeläufe zu D012/D013 und dem vorbereiteten Build: Commit-IDs, volle Binär-Hashes, Werkzeugversionen, ausgeführte Prüfungen mit Ergebnis, Rot-vor-Fix-Nachweis und Patches. Stand-in-Läufe belegen weder Spielkompatibilität noch Performance.

## Software state
| Item | Value |
|---|---|
| Hub repo, branch `perf-metrics` | `e822e7f Hub: thread shutdown that waits for real thread end, END deactivates instead of unloading (D013)`; `ce07db2 Hub: measurement path off the render thread (D011), per-recording manifest and session provenance (D012)`; clean tree when built |
| Hub build id baked into the DLL | `e822e7f19019` (no `-dirty`) |
| `Stronghold2AnalyseHub.dll` sha256 | `591e6375a531c1dbcc6fee582e90f32f873f83629a3f4b7b065d4527b35a89e5` |
| proxy `d3d9.dll` sha256 | `13c895196c175fd3cd963ba3b20ad84e92d4d9caf41cd2e1308eadfc84e24801` |
| `standin_d3d9.exe` sha256 | `4f88882015e3e0b57b6ef6a69bf303bbfea10faf62bec81ce8af2cb1f500b22b` |
| SH2-Perf | tools/docs tree sha256 `769f9ae5195b19ac20096a06cae16c63ba76c39bb962b02c56fbd25891d6d5d9` (49 files, `docs/evidence/` excluded); the pipeline commits are the two newest in `git log` of SH2-Perf (A: state before D013 = `55974f1`, B: D013 round = `4f86008`; corrected, see "Correction") |
| Tools | Python 3.14.3, cmake version 4.4.4, MSVC Win32 Release (static CRT), Windows-10-10.0.19045-SP0 |
| Silver / import tool | `sh2perf-silver 2.1.0` (schema 3) / `sh2perf-import 2.0.0` |
| Installed in TEST? | **No.** TEST, the original installation and `captures/` were not changed (bronze hashes compared before/after) |

## Checks run on this state
| Check | Result |
|---|---|
| CMake configure + Win32 Release build after the hub commit | exit 0, 0 warnings, 0 errors; DLL contains the build id, no `-dirty` |
| `capture_test.exe` / `lifecycle_test.exe` / `sampler_test.exe` | all exit 0 (`sampler_test`'s 5 % overhead check is noisy near its threshold, F-notes in STATE) |
| `test_hardening.py` (with `-W error::ResourceWarning`) | Ran 31 tests in 18.732s OK |
| `test_import_safety.py` / `test_ingest.py` / `test_variant.py` / `test_ab_compare.py` (same flag) | Ran 45 tests in 9.804s OK / Ran 9 tests in 1.321s OK / Ran 15 tests in 0.428s OK / Ran 10 tests in 0.161s OK |
| ResourceWarnings in `test_hardening` | reproduced before (2 x unclosed pipe of the lock-holder process), 0 after (`-X dev -W always`) |
| `lint_docs.py` | OK |
| `e2e_standin.py` on the committed build (proxy + hub DLL + stand-in, 3 sessions, DLL swapped, import, repeat import, END deactivation) | 24 checks ok, "E2E OK" |
| END deactivation repeated on the committed build | deactivation check: 4 of 4 runs clean |
| Normal exit / hard kill of the stand-in while recording | manifest stays `recording` in both cases (F117); no finalization at game exit |

## Red before the fix
See `RED_BEFORE_FIX.txt` (test names) and F114-F117 in FINDINGS. END crash: 1 of 4 clean before D013, 0 of 4 with only the thread fixes, 8 of 8 after the hook fix.

## Patches
- `hub_lifecycle.patch`: `git diff ce07db2 e822e7f` of the hub (D013 over D011/D012).
- `pipeline_protections.patch`: SH2-Perf tools/docs, commit A to the D013 round (excluding this evidence folder).

## Correction (2026-10-15, after commit)
The first version of this report said the D013 round would be `55974f1` once committed. Wrong: `55974f1` is the D011/D012 commit (commit A, state before D013); the D013 round is **`4f86008`** ("Tools and docs: reference profile, verified bronze, write lock, name rules, deactivation wording (D013)"), which also added this report. Checked: `git diff 55974f1 4f86008 -- . ':(exclude)docs/evidence'` is byte-identical to `pipeline_protections.patch` (18 files, 1,732 lines), and `git diff ce07db2 e822e7f` in the hub is byte-identical to `hub_lifecycle.patch`. Hub commit, build id and the three binary hashes above were re-checked against the build folder and are unchanged. Only the commit assignment changed; no test result or hash in this report changed.
