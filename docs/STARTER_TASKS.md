# STARTER_TASKS — three small, checkable entry tasks

> Kurzfassung: Drei kleine Einstiegsaufgaben mit festem Abnahmekriterium: Auditkorrekturen in FINDINGS übernehmen (ohne Spiel), Schlussrest-Prüfung in grannyobs.py (ohne Spiel), Grenz-ABI auf eigener Spielkopie unabhängig bestätigen (eigenes Spiel). Stand 2026-10-16.

Each task is useful on its own, fits in a small pull request and has an acceptance check that someone else can
repeat. Read [README.md](../README.md), [CONTRIBUTING.md](../CONTRIBUTING.md) and the "Current status" in
[STATE.md](STATE.md) first. Claim a task by opening an issue before starting.

## T1 — Integrate two audit corrections into FINDINGS (no game)

**Why**: the [independent audit](../audits/2026-10-16-independent/README.md) found limits that FINDINGS does not yet
state; later work must not build on the older, broader reading (STATE "Done", audit entry).

**Do**:
1. Read audit report sections 2 ("Prüfung der tragenden Behauptungen", "Neu: unzugeordneter Schlussrest und
   Phasengrenzen", "Vier unterschiedliche Gleichheiten") and `data_results.json` → `captures.G1.unframed_boundary_tail`.
2. Add two new rows to [FINDINGS.md](FINDINGS.md) (next free F numbers): (a) the meaning and limit of
   `all_observed_same` (not a general sample-to-sample clock comparison; which group nevertheless survives stricter
   checks); (b) the 609 boundary calls (clock 372, sample 187, deform 25, composite 25) counted in the totals without a
   frame row although frame drops are 0.
3. Add a cross-reference "(limit: F###)" to F146 without changing its existing text.

**Done when**: each new row has a status, a precise statement, and evidence pointing to the audit file, section and
JSON key; you re-checked the 609 figure from `data_results.json`; `python -I tools/run_checks.py` passes; STATE.md
mentions the integration.

## T2 — Report the unframed tail in `grannyobs.py` (no game)

**Why**: an observer recording can count calls in its totals (`<stem>_granny.json`) that never reach a frame row, and
today's reader does not show it ([GRANNY_OBSERVER.md](FORMATS/GRANNY_OBSERVER.md); audit finding above).

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
