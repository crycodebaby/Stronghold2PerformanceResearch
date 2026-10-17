# T2: global call-to-frame accounting

> Kurzfassung: Spielfreie Reader-Korrektur: Ganzzahlbilanz aller sechs Aufrufzaehler, explizite Luecken und inkonsistente/unbekannte Eingaenge. Keine neue Spielmessung oder native Aenderung.

Date: 2026-10-17. Research baseline `f2718cc`; companion Hub `026584a` (unchanged).

## Question and result

Recording totals include calls that need not have a saved frame row. The reader now reports that difference globally,
before marker filtering and without excluding the partial first row. Its frame-call status is separate from the existing
owner-detail quality API and Silver. This is a file-accounting result, not proof of complete observation or matching poses.

The six functions map to `clock_calls`, `sample_calls`, `deform_calls`, `composite_calls`, `free_instance_calls` and
`free_deformer_calls`, respectively, as defined in `grannyobs.CALL_COLUMNS` and the native frame CSV header. Counts are
nonnegative integers; bools, fractional values and missing fields cannot silently become zero. CSV counters do not
pass through float conversion. Tests exercise metadata/CSV values above `2**53`.

## Outputs and limits

```text
frame-call accounting: balanced (counts only, not complete observer coverage)
frame-call accounting: partial; unframed tail: 609 calls (no reported frame-row drops)
frame-call accounting: inconsistent; a frame-column sum exceeds its recording total; cause unknown
frame-call accounting: unknown; missing call totals
```

The 609 example is **synthetic**, with differences 372/187/25/25/0/0. No historical capture was read or re-counted.
Where frame-row drops are nonzero or unknown, the label is `unframed/unassigned calls`: the source of all missing calls
is not established. No last-frame timing, marker allocation or missing object record is reconstructed. Unknown or
inconsistent accounting suppresses phase statistics and exits nonzero. A positive, known balance remains reportable.

## Reproduce without the game

Run from the repository root:

```text
python -I tools/test_grannyobs.py
python -I tools/run_checks.py --audit --e2e
```

The latter requires the unchanged companion Hub next to the research repo, built Win32 Release in `build/Release`.
All new tests use temporary synthetic files. Existing quality/Silver tests remain in the suite.

Actual local acceptance: 18/18 reader tests pass; the selected old-reader CLI test fails as expected with one assertion
failure (missing accounting line), no test error. Full `run_checks.py --audit --e2e`: 11/11, audit model matches its
published reference, stand-in end-to-end succeeds. The unchanged Hub builds Win32 Release and passes 4/4 gating native
tests. The final extra rejection of duplicate counter headers was checked in the reader suite and normal game-free
checks; it does not change native or import code. No real-DLL, new Ghidra export or game test was run.

For the old-reader counterexample, extract `git show f2718cc:tools/grannyobs.py` to a temporary Python file. Import the
new `tools/test_grannyobs.py`, point its module-level `READER` to that old file, and run only
`FrameAccounting.test_cli_global_tail_ignores_phase_filters`. That test calls no new helper: it invokes the actual CLI
and expects the 609 accounting line and six literal function differences. Old output fails that assertion; new output
passes for marker 1 and marker 3, despite a partial first row and different phase selection. The fixture's unequal
nonzero frame counts cover all six mappings independently of the implementation's mapping constant.

## Agent contribution and responsibility

A Gemini 3.8 Flash High read-only patch attempt read the two source files but reached its 180-second CLI timeout with
no final patch. The CLI reported `SUCCESS` with an empty response; this is recorded as **incomplete**, not implemented.
The local orchestration helper was corrected to reject print timeouts/empty final responses; replaying that actual
recorded timeout now returns failure without another model call. No automatic retry or model substitution was used.
The lead implemented this change and owns its validation. A separate focused read-only Flash review returned no
defects for the accounting core and tests it inspected. The lead also added explicit missing-file/invalid-metadata and
duplicate-header CLI checks. An agent response is not an acceptance test or a claim that every possible CSV was validated.

The next research task remains the game-side H-pose ownership/lifetime chain. T1/T3, new captures, observer production
changes, engine patches, cache/skip logic and performance claims were outside this work.

## Independent Sol 6.1 review and small correction

A fresh native subagent selected as `gpt-6.1-sol` reviewed local commit `a1b43cc` read-only, with no Antigravity call.
It independently passed the then-current 18 reader tests and reproduced the expected old-reader CLI assertion failure.
It found no defect in the accounting core within that review, but reproduced an uncaught `csv.Error`: a synthetic CSV
counter containing 140,000 ASCII digits exceeded the CSV parser field limit. The CLI exited nonzero with a traceback
instead of its intended `unknown` report. Such a value is not a plausible native counter; this was a low-priority
input-handling defect, not a false balanced result or a new game finding.

The lead added `FrameAccounting.test_cli_oversized_csv_field_is_unknown`, observed its assertion fail against `a1b43cc`,
and caught `csv.Error` at the existing load boundary. All 19 reader tests then passed. The test requires nonzero exit,
an explicit unknown report, no traceback and no phase statistics. No parser size limit was relaxed. This supplements
the original acceptance above; the published main and companion Hub remain unchanged. A single review task does not
establish a fair model ranking: the earlier Flash implementation timeout and this review had different assignments.
After the correction, `python -B -I tools/run_checks.py --audit --e2e` passed 11/11 checks, including the 19 reader
tests, audit model/reference equality and the stand-in integration. No game or raw-data test was added.
