# Independent audit 2026-10-16 (published copy)

Independent re-check of the EXP-008R Granny-observer evidence and of the exe animation path around RVA `0x0038E4D0`.
The report ([INDEPENDENT_AUDIT_2026-10-16.md](INDEPENDENT_AUDIT_2026-10-16.md), German) and its start file
([HANDOFF.md](HANDOFF.md)) are kept as written. Its corrections were reproduced and integrated into
[docs/FINDINGS.md](../../docs/FINDINGS.md) as F148 (and F149 for the exe path), see
[docs/evidence/POSE_CONTRACT_2026-10-16.md](../../docs/evidence/POSE_CONTRACT_2026-10-16.md). The audit is evidence to
check, not an authority: it states its own limits.

## Origin

- Produced on 2026-10-16 by a separate, fresh AI-agent session working on the project owner's instruction, with the
  scope in [docs/tasks/INDEPENDENT_AUDIT_2026-10-16.md](../../docs/tasks/INDEPENDENT_AUDIT_2026-10-16.md). It read the
  project repositories, game files, recordings and a copy of the Ghidra project, and wrote only into its own local
  workspace (`<audit-workspace>`).
- Inputs at audit time: research repo `77af09e72f2e`, hub `32ebc38a05ea` (both clean); exe SHA-256
  `f3ccdf9b…f32d34b`, `granny2.dll` SHA-256 `94d56fd7…6050fd`; recordings A1 `rec-20261015T121438Z-7d436886`, G1
  `rec-20261015T122211Z-dff71642`. `identity_before.json` / `identity_after.json` list every input hash.
- Source of this copy: the workspace's canonical `analysis/` folder (identical to its delivery copy
  `outputs/analysis/`; delivery ZIP SHA-256 `0446064eb3ed63e8120203ff24005615ed9fe1ec64b3cd5b5b957755dec4b563`).
  Imported into this repository on 2026-10-16.

## What was copied, and what was changed

Only the audit's own report, scripts and derived result files. **Not** copied: the workspace's `work/` folder
(Ghidra project copy, instruction exports around the analysed functions, stand-in runs), because it holds game-derived
disassembly and local paths. Nothing in this folder contains game binaries, assets or decompiled code.

Seven files were published unchanged; seven are **edited derivatives** and are not byte-identical to the audit
originals. All files keep the originals' LF line endings, and `.gitattributes` marks `audits/**` as `-text` so every
checkout has exactly the hashed bytes. Each replacement was applied by an exact, counted string match.

| File | Original SHA-256 | Published copy | Changes |
|---|---|---|---|
| `AuditPath.java` | `44fc42f4689c83bd88ae1032f7da6cc7edb8ba340db31a58e814745300332b5b` | identical | — |
| `HANDOFF.md` | `1ac3fcb705f2a284c9b0fcca92285c7eeacd7dfcaf40d25ac56d5c6c0ee146e0` | `5c84dc067c06b61b5b19da6a8ce5b0711f630b61abeeb4e8395ce1893a9f02e8` | P1 (1×), P2 (2×), P3 (1×) |
| `INDEPENDENT_AUDIT_2026-10-16.md` | `2bdf89b91931e06fc1ce672eec07cf818c8e29cec47be0fac514fa65affc1c9b` | `9fe933312fb346d94fcbab34fad5337a02d50e3245c049d3e8c97d0cfb519f25` | P1, P2 (1× each) |
| `audit_data.py` | `624808078a85b3f5db3fe88f14295902b4faeca026fd5202b2c6a2aff22fa45a` | `160148d041aa364484409d2de83d5e08bea417e05d8d323f2aedaa03f9ec3c96` | S1 |
| `verify_binary.py` | `7f7e4360d68e5d39a00b77048b7603810599639d27910192b287a504a9866920` | `d938181c9f5205d9836094774053508dfc68e6170f9c7979a5ba92aed8face4c` | S1 |
| `observer_repro.py` | `3e2e6975c1b0a78c769b0c60e0546a397cc4b05ef7871dac38c37d11bce113f0` | `b0cc302d1a8e184fc49dfd54a0b6728c1fd38c8fd9f01efa9feca19927429b7f` | S1, S2 |
| `run_audit.ps1` | `b67c5b3ed016a8cb1071ad967578c6a11a42a3646f9a75ecf6fe221a2e9342d6` | `2c5d1e62ebfe4669f81cc485d9b130086c90a96ca2be15994e449125eba5c805` | S1, S3 |
| `native_test_result.json` | `d4c848855a1b94d457f73219cadb482333d4118158dc6f9bb2b43562cc8c5e8c` | `45ce9d04a17dc4381a0bc9238d9b7b7cc53496ee1ff21b9d5d590c6bcecd5892` | P2 (1×, in the `output` string) |
| `binary_results.json` | `b8c23dc03d7d4886f474800dfcc8d2967180737aab66aa30f9ca583b6022e9e6` | identical | — |
| `data_results.json` | `0b1a4e2ea50d985ea07b056a25240c20c881d5200f62a568913b793040d47f5f` | identical | — |
| `repro_results.json` | `0ac831d8c27b1d2f02609e9c25af1b5dca94e294a71b8c15ce16ee3be8798d29` | identical | — |
| `identity_before.json`, `identity_after.json` | `7d36630dbbe547a439632bf71b8629dd20afa4e40a152b5bc663be62a8a83f43` (both) | identical | — |
| `workload_distribution.json` | `82f6691700ffa69969686061d83fa0c00fd56ebf7c765e63804a6164d0968bd1` | identical | — |

- **P1** absolute path of the local project workspace → `<RE-Projects>` (the folder that holds this repository as
  `SH2-Perf`, the hub repository, the game copies and the Ghidra project).
- **P2** absolute path of the audit workspace → `<audit-workspace>`.
- **P3** absolute Ghidra install path → `%USERPROFILE%\Tools\ghidra_12.1.4_PUBLIC`.
- **S1** hard-coded workspace default in the script → derived from the script location (`HERE.parents[2]`, i.e.
  `<RE-Projects>` when this repository is checked out as `<RE-Projects>/SH2-Perf`); `run_audit.ps1` likewise uses
  `$PSScriptRoot` and `%USERPROFILE%`. `--root` / `-InputRoot` still override it.
- **S2** `observer_repro.py` hashes the hub source after normalising CRLF to LF. The audit hashed an LF working copy;
  a fresh Windows clone with `core.autocrlf=true` has CRLF and was rejected although the git content is the same.
- **S3** `run_audit.ps1` writes its work files (Ghidra project copy, exports) to `-Work`, default
  `%TEMP%\sh2-independent-audit-work`, instead of a `work/` folder beside the scripts, so nothing large or game-derived
  lands inside the repository.

Result files are the audit's outputs from its own run; they were not regenerated for this copy. Re-running a script
rewrites its result file beside it, so `git diff` shows whether a rerun reproduces it.

## What can be re-run where

| Command (from this folder) | Needs | Checked on 2026-10-16 for this copy |
|---|---|---|
| `python -I observer_repro.py --hub-source <hub>/Stronghold2AnalyseHub/core/granny_observer.cpp` | hub source equal to `32ebc38` (default: sibling `../Stronghold2AnalyseHub`); no game, no raw data | 9/9 tests OK from fresh clones; `results` equal to the published `repro_results.json` |
| `python -I audit_data.py [--root <RE-Projects>]` | the two raw recordings under `SH2-Perf/captures/` and the game files | not re-run (raw data are not published) |
| `python -I verify_binary.py [--root <RE-Projects>]` | your own `Stronghold2.exe` / `granny2.dll` (Steam 1.5 hashes above) and the instruction exports of `run_audit.ps1 -ExportBinary` | not re-run |
| `powershell -File run_audit.ps1 -ExportBinary` | all of the above, Ghidra 12.1.4 and the project's Ghidra database | not re-run |

`observer_repro.py` is a Python model fed with real aggregated distributions (`workload_distribution.json`,
`data_results.json`) and explicitly synthetic event orders. It is not an event replay, measures no hook latency and does
not prove engine identity or output equivalence.
