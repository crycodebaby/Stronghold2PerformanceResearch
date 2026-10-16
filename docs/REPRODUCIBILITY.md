# REPRODUCIBILITY — what an outside developer can re-check

> Kurzfassung: Which checks run without the game, which need your own Stronghold 2 installation, and which results depend on unpublished local raw data or the Ghidra database. Status as checked from fresh clones on 2026-10-16 (local runs only, no GitHub CI run yet).

## Three classes of checks

| Class | Needs | Published? |
|---|---|---|
| **A — no game** | Windows, Python ≥ 3.12, for the hub VS 2022 Build Tools + CMake | everything needed is in the two repositories |
| **B — own game** | your own Stronghold 2 **Steam 1.5** installation (exe SHA-256 `f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b`, `granny2.dll` `94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd`), a TEST copy of it, optionally Ghidra 12.1.4 | game files are never published; you bring them |
| **C — local raw data** | the original recordings in `captures/`, the project's Ghidra database, the audit's `work/` exports | not published (personal paths in logs, game-derived disassembly, size) |

## Checks and their last result

All class A rows were run on 2026-10-16 from fresh clones without build folders or databases (Windows 10, Python
3.14.3, CMake 4.4.4, MSVC 19.44, hub `publish-prep` whose runtime sources equal `32ebc38`).

| Check | Command | Class | Result 2026-10-16 |
|---|---|---|---|
| Hub Win32 build | `cmake -S . -B build -A Win32` + `cmake --build build --config Release` | A | OK, 0 compiler warnings |
| Hub native tests | `ctest --test-dir build -C Release -LE timing` (capture, lifecycle, Granny observer with fake DLL) | A | 3/3 OK |
| Hub sampler overhead | `ctest ... -L timing` (`sampler_test`) | A, load-dependent | **FAIL** 4/4 runs: slowdown 5.3–6.1 % > 5 % threshold on a busy machine; attribution checks passed. Earlier result 2–4 % (F103) |
| Python suites + docs lint | `python -I tools/run_checks.py` | A | 7/7 OK (with this commit's docs) |
| Audit observer model | `python -I tools/run_checks.py --audit` | A (needs hub source at `32ebc38`) | 9/9 OK, `repro_results.json` reproduced byte-identically |
| End-to-end stand-in | `python -I tools/run_checks.py --e2e` | A (needs hub build + interactive desktop) | E2E OK |
| Python 3.11 | same suites | A | `test_import_safety`, `test_hardening` fail (`os.path.isjunction` is 3.12+) |
| Install hub into a TEST copy | `python -I tools/variant.py baseline`, `status` | B | not re-run for publication |
| In-game recording, import, evaluation | EXPERIMENTS.md protocols, `ingest.py`, `grannyobs.py`, `ab_compare.py` | B | not re-run; last real runs 2026-10-15 |
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
- **The independent audit**: its observer model runs anywhere (class A); its recounts need our raw data (C); its binary
  checks need your own game files plus fresh exports (B). Details in
  [audits/2026-10-16-independent/README.md](../audits/2026-10-16-independent/README.md).
- **User-confirmed context** (game speed 90, paused phases, the historical multiplayer report F060) cannot be
  re-checked at all; it is recorded as user statement, separate from measured values.

## Environment pitfalls found while checking

- Clone to a short path: MSBuild stops with "path exceeds 260 characters" when the hub build folder is deep inside
  `%TEMP%`.
- Python 3.12 or newer is required; 3.14.3 is the verified version.
- `core.autocrlf=true` checks out CRLF files; anything that hashes source files must normalise line endings (the
  audit copy does, see its README).
- `sampler_test`'s overhead threshold is sensitive to machine load; CI reports it without gating.
