---
name: messung-auswerten
description: Evaluate a new Stronghold 2 performance recording (hub CSVs, SH2Perf_out, latest.json, "neue Messung", EXP-###). Ingests it, compares it with earlier captures and records the result in docs.
---

# Messung auswerten

Raw CSVs and logs stay in their files: every number comes from tool output of ≤ 30 lines.

1. **Identify** the experiment: EXP id, scenario, troops per player, variant (auto-detected unless the user says otherwise). Take them from the user's message or `docs/EXPERIMENTS.md` (planned table); ask only if the EXP id or troop count is unknown.
   Done when: all four values are named.
2. **Ingest** (game must be closed):
   `python -I tools/ingest.py --exp <EXP> --scenario <S> --troops <N> [--note "..."]`
   Done when: the tool printed `ingested <capture_id>`. On "no latest.json": the user has to stop the recording with F9 first.
3. **Compare** with earlier captures of the same scenario/troops: read only the matching lines of `data/index.jsonl` (e.g. `grep '"scenario":"KNIGHTS"' data/index.jsonl | grep '"troops":100'`), comparing `total` and `phases` per variant.
   Done when: a delta table (FPS avg, 1% low, cpu-side ms, present ms) exists for every earlier capture with the same scenario and troops, or it is stated that none exist.
4. **Interpret** with the key in `docs/EXPERIMENTS.md` ("Interpretation key"). Separate observation (numbers) from inference (cause).
   Done when: every phase has a one-line verdict (sim-bound / render-bound / GPU-bound / unclear) citing the numbers it rests on.
5. **Record**:
   - `docs/EXPERIMENTS.md` → Results: ID, date, capture_id, variant, setup line, metrics table, verdict.
   - `docs/FINDINGS.md` → new or updated F### with status and the capture_id as evidence.
   - `docs/STATE.md` → done / next step.
   Done when: `python -I tools/lint_docs.py` prints OK.
