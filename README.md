# Stronghold 2 Performance Research

Measurement-first research into why **Stronghold 2** (Steam 1.5, 32-bit, Direct3D 9) slows down with large armies,
and what a safe, switchable improvement could look like. Locally this repository is called `SH2-Perf`.

> **Status (2026-10-16): no performance fix exists.** Nothing here makes the game faster yet. What this repository
> offers is verified measurements of one reference scene, a located set of expensive code paths, measurement and
> import tooling, and a precisely bounded next research question. Hypotheses are marked as such.

Companion repository: **[Stronghold2AnalyseHub](https://github.com/crycodebaby/Stronghold2AnalyseHub)** — the d3d9 proxy,
the measurement DLL (hub) and its native tests. This repository holds everything else: findings, decisions,
experiment protocols, data contracts, analysis tools, Ghidra scripts and audits.

## The problem

Users report that large battles become very slow; the historical extreme (1–2 FPS) was a human-vs-human multiplayer
game on a large, heavily built map with several hundred troops, with no recording (F060, hypothesis). The current
**reference scene** is a single-player save with 257 units (217 mounted archers, 20 crossbowmen, 20 archers) at game
speed 90 (`REAL_LAG_257` / `LAG_217_Reiter`). Long-term target: the original exe plus a switchable drop-in extension
reaching ≥ 45 FPS mean and ≥ 30 FPS 1 % low in that scene, without changing game rules, saves or multiplayer behaviour.
Not reached.

## How it works

```
your game copy (TEST) ── d3d9.dll proxy ──► Stronghold2AnalyseHub.dll (hooks only read and forward)
                                              render thread → lock-free ring → capture thread → SH2Perf_out/
SH2Perf_out/ ── tools/ingest.py (verify → stage → atomic import) ──► captures/  (bronze: raw files, local only)
                                                                   └► data/      (silver: one metrics line per recording)
                                                                   └► docs/      (gold: findings, decisions, experiments)
```

- **Bronze** `captures/`: raw CSVs, logs, manifests, Ghidra exports. Never in git, never edited.
- **Silver** `data/index.jsonl` (tracked) and `data/silver/` (rebuilt by `ingest.py rebuild`), plus user-confirmed
  context in `data/annotations/` (e.g. confirmed game speed or pause).
- **Gold** `docs/`: [FINDINGS.md](docs/FINDINGS.md) (facts F### with `[verifiziert]`/`[Hypothese]`/`[widerlegt]` and
  evidence), [DECISIONS.md](docs/DECISIONS.md) (D###), [EXPERIMENTS.md](docs/EXPERIMENTS.md) (protocols and results),
  [FUNCTIONS.md](docs/FUNCTIONS.md), [FORMATS/](docs/FORMATS/) (data contracts), [SETUP.md](docs/SETUP.md).
- Every recording carries a manifest with hashes of the exe, hub, d3d9 files and ini, the effective switches and the
  planned conditions (D012); the importer refuses damaged or ambiguous input.

The detailed documentation is partly German; entry documents are English. Facts keep their IDs across languages.

## What is known (verified, with evidence)

| Topic | Finding |
|---|---|
| Reference scene, no sampler | running ≈ 32.8 ms vs paused ≈ 25.1 ms per frame at nearly equal draw load; render thread ≈ 98 % busy in both (F126, F097) |
| Where the extra running cost sits | mostly in `Stronghold2.exe` (≈ +5.5 ms of ≈ 7.4 ms in module samples, F128); no single exe hotspot in flat samples (F135) |
| Granny animation runtime | `granny2.dll` is a large per-frame cost in both states (F127, estimate in F129 is a hypothesis); its SSE vertex-deform loop and B-spline/knot helpers are located (F132–F134) |
| Exe → Granny boundary | six imports, all `__stdcall`, argument roles verified (F137); the deform call carries no model instance (F138); clock sources per call site (F139) |
| Paused frames still animate | in the confirmed pause of EXP-008R-G1 each frame issues ≈ 2,842 sample and ≈ 2,185 deform calls ([evidence](docs/evidence/EXP-008R_G1_PARTIAL.md)) |
| Retained pointers | 1,503 retained pointer rows receive identical observed inputs throughout the pause; 135 others get changing clocks/offsets (F146, F147) |

**Not established:** that any work is redundant, that results (poses, vertices) are identical, that caching or skipping
is safe, how many milliseconds could be saved, or a mapping from model pointers to soldiers. F136 ("some paused-frame
Granny work recomputes unchanged poses") remains a **hypothesis**.

## Limits you should know before relying on anything

- **No performance gain** and no patch to game behaviour exist. All instrumentation is research tooling.
- **Granny observer (hub switch `granny`)**: even the corrected build lost 126,632 per-instance aggregations in the
  latest real-game run (F145); per-instance tables are incomplete, only frame-level call counts are complete. The
  [independent audit](audits/2026-10-16-independent/README.md) adds: `all_observed_same` is not a general
  sample-to-sample clock comparison; missing samples can hide ambiguous pose links; 609 final calls have no frame row
  although frame drops read 0; the native test uses a fake `granny2.dll`. These corrections are not yet fully merged
  into FINDINGS.
- **Sampling biases frame times** by ≈ 2–5 % in the game (F125); sampled runs are not benchmark runs.
- **One machine, one scene.** All recordings come from one PC (see `data/index.jsonl`) and mostly one save.
- **Raw data are not published** (absolute paths in logs, game-derived Ghidra exports). Numbers in the docs can be
  re-measured with your own game copy, but not re-counted from our files: [REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).
- User statements (confirmed game speed, pause, the multiplayer report) are recorded as such, not as measurements.

## Getting started

**1. Without the game** (Windows; Python ≥ 3.12, verified 3.14; for the hub VS 2022 Build Tools + CMake ≥ 3.21). Clone
both repositories side by side into a short path; the tools find the hub as the sibling folder `Stronghold2AnalyseHub`
(commands for `cmd.exe`):

```
mkdir C:\src\RE-Projects & cd C:\src\RE-Projects
git clone https://github.com/OWNER/Stronghold2PerformanceResearch SH2-Perf
git clone https://github.com/crycodebaby/Stronghold2AnalyseHub
cd Stronghold2AnalyseHub
cmake -S . -B build -A Win32 && cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure -LE timing
cd ..\SH2-Perf
python -I tools/run_checks.py --audit --e2e
```

`--audit` re-runs the audit's observer model against the hub source; `--e2e` drives the real proxy and hub DLL against
a D3D9 stand-in program and imports the result. Both need no game files.

**2. With your own game** (Steam 1.5; check the exe SHA-256 in [FINDINGS F058](docs/FINDINGS.md)): copy the
installation to `Stronghold 2 - TEST` next to the repositories, never modify the original, then follow
[SETUP.md](docs/SETUP.md) (`tools/variant.py baseline`, recording, `tools/ingest.py import`) and the protocols in
[EXPERIMENTS.md](docs/EXPERIMENTS.md). Folder layout: [WORKSPACE.md](docs/WORKSPACE.md).

**3. Pick a task**: [docs/STARTER_TASKS.md](docs/STARTER_TASKS.md) has three small, checkable tasks. The current research
assignment is in [docs/STATE.md](docs/STATE.md) ("Current status") and
[docs/PROJECT_LEAD_HANDOFF.md](docs/PROJECT_LEAD_HANDOFF.md). [docs/HANDOFF.md](docs/HANDOFF.md) is a historical log of
earlier game-run orders; do not execute it.

## Verified version pair

| Repository | Version | Meaning |
|---|---|---|
| Stronghold2PerformanceResearch | the commit that contains this table (branch `publish-prep`) | docs, tools and audit copy checked on 2026-10-16 |
| Stronghold2AnalyseHub | branch `publish-prep` `a643f97`; runtime sources identical to `perf-metrics` `32ebc38a05ea` | `32ebc38a05ea` is the hub build of the latest in-game recordings (EXP-008R-A1/G1) |

Checked together on 2026-10-16 from fresh clones: hub build and native tests, all game-free Python checks, the audit
model and the stand-in end-to-end run (results in [REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md)). Locally only; no
GitHub CI run yet.

## Repository layout

| Path | Content |
|---|---|
| `docs/` | state, findings, decisions, experiments, formats, setup, evidence, tasks |
| `tools/` | stdlib-only Python tools (`python -I tools/<name>.py`), tests, `run_checks.py`; see [tools/CLAUDE.md](tools/CLAUDE.md) |
| `ghidra_scripts/` | headless Ghidra scripts that export addresses, names and counts, never decompiled code |
| `audits/` | published copies of independent audits with provenance |
| `data/` | silver index and user annotations |
| `.claude/skills/`, `CLAUDE.md` | routing for Claude Code; [AGENTS.md](AGENTS.md) is the tool-neutral version |

## Contributing, legal

See [CONTRIBUTING.md](CONTRIBUTING.md); agents read [AGENTS.md](AGENTS.md) first. Our own code and documentation are
under the MIT license ([LICENSE](LICENSE)). Stronghold 2 is a game by Firefly Studios; Granny is a runtime by RAD Game
Tools. This project is not affiliated with either and contains none of their files, assets or decompiled code; you
need your own copy of the game for anything that runs against it.
