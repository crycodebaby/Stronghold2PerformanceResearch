# Analysis state after EXP-007

> Kurzfassung: Reproduzierbarer Analysezustand nach EXP-007 (2026-10-15): vollständige Binär-Hashes, Ghidra-Version, Bildbasen, Hashes der Funktionskarten, Sicherung des geschlossenen Ghidra-Projekts und alle manuellen Änderungen in der Ghidra-Datenbank. Keine Datenbank, keine Binärdatei und kein dekompilierter Code im Repo.

Checked 2026-10-15 against the files, not copied from earlier notes.

## Binaries (original = TEST copy, byte-identical)
| File | sha256 | PE image base | SizeOfImage | PE timestamp | Ghidra import source |
|---|---|---|---|---|---|
| `Stronghold2.exe` | `f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b` | 0x00400000 (ASLR on; loads relocated, F006) | 0x027E0000 | 2020-04-24 16:20:16 | `Stronghold 2/` (01:50) |
| `dragonfly.dll` | `cdfbaae5a7eaf3a8c4bacef6435d8c05c626d74d1678280625a7e56267da0186` | 0x10000000 | 0x0005E000 | 2020-04-20 21:52:32 | `Stronghold 2/` (01:49) |
| `granny2.dll` | `94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd` | 0x50000000 (no ASLR) | 0x00092000 | 2006-02-17 19:37:01 | `Stronghold 2 - TEST/` (09:25, same hash as original) |

## Tools
- Ghidra 12.1.4 PUBLIC, build date 2026-09-21 (`application.properties` of `%USERPROFILE%\Tools\ghidra_12.1.4_PUBLIC`); JDK as in [SETUP.md](../SETUP.md).
- Function maps from `ghidra_scripts/ExportFunctions.java` (bronze, `captures/functions/`, not in git):

| Map | sha256 | Functions | Exported | Contains |
|---|---|---|---|---|
| `exe_functions.csv` | `311dc66fc1fa180735c61416d81c2429a48d98e359760a9140595c0916c8c245` | 40,216 | 09:25 | auto-analysis state; the later exe change is a plate comment only (bodies unchanged) |
| `granny2_functions.csv` | `f124b38d938e6705bd89bd1c4b4ece78de11b347031fecf94b7efdba84ea0cce` | 2,155 | 09:51:55 | after the 3 created functions and the `SseDeformPWNT3432I` name |

## Manual changes in the Ghidra database (all logged in `captures/functions/`)
| Time | Script | Program | Change | Log |
|---|---|---|---|---|
| 09:25 | headless import + auto-analysis | granny2.dll | imported, 2,152 functions | `ghidra_granny2.log` |
| 09:46 | `CreateFunctionsAt.java` | granny2.dll | created `FUN_50015750` (0x50015750–0x50015962, 531 B), `FUN_50044410` (0x50044410–0x50044540, 305 B), `FUN_50044630` (0x50044630–0x500447BC, 397 B); entries reached only via data pointers (F131) | `created_granny2.txt`, `ghidra_create.log` |
| 09:51 | `AnnotateFunctions.java` | granny2.dll | name `SseDeformPWNT3432I` at 0x500092E0 (USER_DEFINED; from its own assert string); plate comments `SH2Perf_…` on 0x500092E0, 0x50008810, 0x500166E0, 0x50017600 | `annotate_granny2.txt`, `ghidra_annotate.log` |
| 09:51 | `AnnotateFunctions.java` | Stronghold2.exe | plate comment `SH2Perf_EXP-007_candidate_B1…` on 0x004E3530; no rename | `annotate_exe.txt`, `ghidra_annotate_exe.log` |

Working names in [FUNCTIONS.md](../FUNCTIONS.md) (`…_loop`, `BSpline2x4n_eval`, `FindKnot_search`, `exe_GrannySampleModel_call`) are **not** set in Ghidra. All other scripts of the session ran `-readOnly`.

## Ghidra project backup
- Project closed when copied: no Ghidra/pyghidra process running, no `SH2.lock` in `ghidra-projects/` (the three `java.exe` processes on the machine belong to an unrelated program).
- `ghidra-projects/_backup/SH2_after_EXP-007_20261015.zip` (outside every git repo): `SH2.gpr` + `SH2.rep/`, 15 files, 384,043,272 bytes uncompressed (= source, checked entry by entry count and sum), zip 100,415,623 bytes, sha256 `48d50246a17941559cbcbaa96fee7b41a4e2f2aa3ad48ae695c591441a413c53` (also in `_backup/SHA256SUMS.txt`).
- Restore: Ghidra closed, move the current `SH2.gpr`/`SH2.rep` aside, unzip into `ghidra-projects/`. Opening the backup in Ghidra was not tested.

## Reproduce the EXP-007 counts
```
python -I tools/funcsamples.py captures/rec-20261015T073402Z-bf15a427/SH2Perf_20261015_093402_samples.csv captures/rec-20261015T073402Z-bf15a427/SH2Perf_20261015_093402_frames.csv --delta-counts --module exe
python -I tools/funcsamples.py captures/rec-20261015T073915Z-387fcc8e/SH2Perf_20261015_093915_samples.csv captures/rec-20261015T073915Z-387fcc8e/SH2Perf_20261015_093915_frames.csv --delta-counts --module exe
```
F1 / F2: 134 / 120 known exe functions with samples in marker 1 and none in marker 3 (138 / 121 with unresolved 4 KiB pages); 165 / 145 known with Δ > 0 (169 / 146 with pages = the figure first reported); Δ total 6.17 / 6.30 ms; top 10 positive 2.13 / 2.90 ms; max 0.24 / 0.41 ms. Requires the two maps with the hashes above.
