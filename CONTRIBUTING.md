# Contributing

Thanks for helping. This project values a correct "we do not know yet" over an attractive claim. Read
[README.md](README.md) and [docs/STATE.md](docs/STATE.md) first; agents also read [AGENTS.md](AGENTS.md).

## Set up

- Windows 10/11, Git, Python ≥ 3.12 (verified 3.14.3; stdlib only, no `pip install`).
- For the hub: Visual Studio 2022 Build Tools (C++ workload), CMake ≥ 3.21. Clone both repositories side by side into a
  short path (see README "Getting started"); this repository may keep the local folder name `SH2-Perf`.
- With your own game: a copy of the Steam 1.5 installation as `Stronghold 2 - TEST` next to the repositories.
  Optional analysis tools and versions: [docs/SETUP.md](docs/SETUP.md).
- `git config core.hooksPath .githooks` enables the pre-push hook (docs lint, requires a `docs/STATE.md` change in the
  pushed commits).

## Tests

```
python -I tools/run_checks.py            # all game-free Python suites + docs lint (what CI runs)
python -I tools/run_checks.py --audit    # + audit observer model (needs the hub source at 32ebc38)
python -I tools/run_checks.py --e2e      # + real proxy/hub against the D3D9 stand-in (needs a hub build, a desktop)
python -I tools/hpose_native.py         # own Win32 H-record contract, validated JSON; MSVC/CMake, no game or hub
```

The research workflow also runs the native H-record command as a mandatory step. Its runner failure tests are part
of the compiler-free Python suite. Use `--cmake <executable>` if CMake is not on PATH.

Hub tests: see the hub's CONTRIBUTING.md (`ctest -C Release -LE timing`). Tests use temporary folders only; they must
never touch `Stronghold 2`, `Stronghold 2 - TEST`, `captures/` or `data/`. A new tool comes with a test in
`tools/test_*.py` and a row in [tools/CLAUDE.md](tools/CLAUDE.md). Tool conventions there: `python -I`, stdlib only,
relative paths via `tools/paths.py`, at most ~30 lines of output.

## Contributing measurements

1. Use a fixed protocol from [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) or propose a new one **before** recording:
   question, phases with F8 markers, switches, what counts as valid, what each outcome would mean.
2. Record with a clean, committed hub build (`git describe` without `-dirty`); set the plan with
   `tools/variant.py plan ...` so the manifest carries it.
3. Import with `tools/ingest.py import --recording <timestamp>`; confirm game speed and pauses with
   `ingest.py annotate` only if you actually saw them.
4. Share derived numbers (the `data/index.jsonl` line, `ab_compare.py` output) and the manifest. Raw logs and CSVs may
   contain absolute paths with your user name: share them only after replacing those paths (D007), and say that the
   shared file is an edited copy, not the original. Never commit raw recordings.
5. Report hardware, graphics settings, V-Sync, game version (exe SHA-256) and anything unusual (Alt-Tab, camera moved).

## Requirements for a finding

- One fact per `docs/FINDINGS.md` row: `| F### | [verifiziert] / [Hypothese] / [widerlegt] | statement | evidence |`.
- Evidence names the source precisely: capture id and marker, tool and command, module SHA-256 + RVA, or a document
  section. "An agent said so" is not evidence.
- Keep observation and inference apart: what was counted vs. what it might mean. State the limit (what the data cannot
  show).
- Never delete or silently reword an existing finding; mark it `[widerlegt]` or add a correcting row that references it.
- Performance claims need comparison runs with matching controls (same save, camera, switches, repeat), not a single run.
- Name functions in [docs/FUNCTIONS.md](docs/FUNCTIONS.md) only at confidence `mittel`/`hoch`; guesses go to FINDINGS
  as hypotheses. Use module hash + RVA; do not invent original source names.
- Update [docs/STATE.md](docs/STATE.md) and run `python -I tools/run_checks.py` before a pull request.

## Never commit

Game files or assets (`*.exe`, `*.dll`, `*.gr2`, …, see `.gitignore`), Ghidra databases, decompiled game code or
disassembly listings, raw recordings, personal absolute paths. Ghidra scripts emit addresses, names, counts and strings
only (D008).

## Pull requests

Small and focused: one finding, one tool change or one document per PR. Explain the question it answers. Do not mix
documentation with runtime changes in the hub. Results that need the game are labelled as such, with the exact build
and capture ids.
