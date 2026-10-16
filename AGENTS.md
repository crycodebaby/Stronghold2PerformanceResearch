# AGENTS.md

Tool-neutral instructions for automated agents. Claude Code users also get [CLAUDE.md](CLAUDE.md) (routing table) and
`.claude/skills/`; the rules below apply to every agent.

## Reading order

1. [README.md](README.md) — purpose, what is known, limits.
2. [docs/STATE.md](docs/STATE.md) — "Current status" is the only current order.
3. [docs/PROJECT_LEAD_HANDOFF.md](docs/PROJECT_LEAD_HANDOFF.md) — current assignment and its boundaries (German).
4. For your task only: [docs/FINDINGS.md](docs/FINDINGS.md), [docs/DECISIONS.md](docs/DECISIONS.md),
   [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md), [docs/FORMATS/](docs/FORMATS/), [tools/CLAUDE.md](tools/CLAUDE.md).
5. [docs/HANDOFF.md](docs/HANDOFF.md) is **historical**: context only, never execute its game-run orders.

Earlier agent reports (including audits) are claims to verify, not authority.

## Boundaries

- Do not modify an original game installation, raw recordings (`captures/`, `SH2Perf_out/`), user annotations without
  a user statement, or a Ghidra database (analyse a copy).
- No game-behaviour patch, cache or skip; hooks only read. No new game recording unless the task asks for it and the
  native tests of the change pass.
- No game files, assets, Ghidra databases, decompiled code or personal absolute paths in the repository.
- Do not push, publish, open pull requests or install into a TEST copy unless explicitly asked.
- Do not commit someone else's uncommitted changes without checking them.
- Large raw output stays in files; bring only short summaries into the conversation.

## Done when

- The question asked is answered or the precise open boundary is stated; observation, inference and user statements are
  kept apart and each claim cites its evidence.
- `python -I tools/run_checks.py` passes (add `--audit`/`--e2e` when hub or observer code is involved); hub changes also
  pass `ctest -C Release -LE timing`.
- `docs/STATE.md` and affected docs are updated; new facts follow CONTRIBUTING.md "Requirements for a finding".
- The final report says which checks ran without the game and which would need the game or local raw data.
