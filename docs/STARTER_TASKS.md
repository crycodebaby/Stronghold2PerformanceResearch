# STARTER_TASKS — three small, checkable entry tasks

> Kurzfassung: Drei kleine Einstiegsaufgaben mit festem Abnahmekriterium: Prüfung verwaister F-/D-Verweise im Doku-Linter (ohne Spiel), Schlussrest-Prüfung in grannyobs.py (ohne Spiel), Grenz-ABI auf eigener Spielkopie unabhängig bestätigen (eigenes Spiel). Stand 2026-10-16.

Each task is useful on its own, fits in a small pull request and has an acceptance check that someone else can
repeat. Read [README.md](../README.md), [CONTRIBUTING.md](../CONTRIBUTING.md) and the "Current status" in
[STATE.md](STATE.md) first. Claim a task by opening an issue before starting.

## T1 — Guard against dangling fact references in the docs linter (no game)

**Why**: findings (F###) and decisions (D###) are cited across the docs, the README and audits. Today
`tools/lint_docs.py` checks that an id is defined at most once, but not that every cited id exists, so a renumbered or
mistyped id would go unnoticed (two `D015` drafts met in one merge on 2026-10-16).

**Do**: add a `refs` check to `tools/lint_docs.py`: every `F\d{3}` / `D\d{3}` mentioned in a tracked `*.md` file must be
defined in [FINDINGS.md](FINDINGS.md) / [DECISIONS.md](DECISIONS.md). Report file and id. Add `tools/test_lint_docs.py`
that builds a tiny temporary docs tree with one defined and one dangling id and asserts that only the dangling one is
reported. Add the new suite to `SUITES` in `tools/run_checks.py`.

**Done when**: the new test passes, the current repository lints clean (it did on 2026-10-16: 0 dangling ids), and
`python -I tools/run_checks.py` passes. The linter stays stdlib-only and prints at most one line per error.

## T2 — Report the unframed tail in `grannyobs.py` (no game)

**Completed locally 2026-10-17:** global six-function reconciliation, integer counters, explicit partial/unknown/
inconsistent states, and synthetic tests including a CLI regression against the old reader. No new capture or Hub
change. [Evidence and reproduction](evidence/T2_FRAME_ACCOUNTING_2026-10-17.md). When frame rows were dropped or drop
information is unknown, the difference is reported as unassigned calls, not exclusively a tail. The original task
description below records its motivation; its implementation does not change the current H-pose research priority.

**Why**: an observer recording can count calls in its totals (`<stem>_granny.json`) that never reach a frame row, and
today's reader does not show it. In EXP-008R-G1 these were 609 calls (clock 372, sample 187, deform 25, composite 25;
F148, audit `data_results.json` → `captures.G1.unframed_boundary_tail`) while frame drops read 0
([GRANNY_OBSERVER.md](FORMATS/GRANNY_OBSERVER.md)).

**Do**: in `tools/grannyobs.py`, compute per function `calls in granny_meta − sum over frame rows` and print it as an
explicit "unframed tail" line (marked partial when non-zero). Add a synthetic case to `tools/test_grannyobs.py` (no
real recording) whose totals exceed the frame rows by a known amount.

**Done when**: the new test fails on the old reader and passes on the new one; existing tests still pass;
`python -I tools/run_checks.py` passes; [GRANNY_OBSERVER.md](FORMATS/GRANNY_OBSERVER.md) documents the line. Nothing
in `captures/` is read by the test.

## T3 — Confirm the exe→Granny boundary on your own game copy (your own Steam 1.5 installation)

**Why**: the six import/export/pop-count facts (F137) and the sample return site RVA `0x0038E6DF` (F139) were verified
on one machine only. An independent byte-level confirmation needs no Ghidra.

**Do**: write `tools/check_boundary.py` (stdlib, read-only) that takes the path of a game folder, checks the SHA-256 of
`Stronghold2.exe` and `granny2.dll` against the full hashes in [REPRODUCIBILITY.md](REPRODUCIBILITY.md) (class B), and re-checks from the PE bytes the six IAT RVAs, export RVAs and
`ret N` pop counts plus the indirect call before RVA `0x0038E6DF`, exactly as listed in
`audits/2026-10-16-independent/binary_results.json`. Add a test that runs it against a small synthetic PE built in the
test (no game file in the repository). Run it on your own copy.

**Done when**: the test passes without game files; your run on a Steam 1.5 copy prints all checks OK (report the two
hashes you saw); on a different game version it stops with a clear "unknown build" message instead of wrong results;
the tool never writes into the game folder. Report your result in an issue or PR, labelled "own game copy".
