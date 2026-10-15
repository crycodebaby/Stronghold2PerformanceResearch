# HANDOFF

> Kurzfassung: Übergabe an den nächsten Agenten: aktueller Auftrag (Abnahme der Messinstrumentierung in Stronghold 2), geprüfte Stände, Abnahmeschritte erledigt/offen, nächste Aktion. Projekthistorie steht in STATE.md, nicht hier.

Updated: 2026-10-15. Read [STATE.md](STATE.md) for history and open tasks; this file only covers the current order.

## Current order
In-game acceptance of the measurement instrumentation (hub D011/D012/D013) in Stronghold 2 Steam 1.5, steps of [SETUP.md](SETUP.md) "Check in Stronghold 2". **Nothing about performance** is shown or claimed yet; stand-in results are no game result.

Excluded: engine/game-code patches, new measurement functions, databases, Docker services, larger rebuilds, push or publishing, changes to the original installation or to raw recordings (`captures/`, `SH2Perf_out`), performance claims from stand-in runs.

## Verified state (checked 2026-10-15 against the real files)
| Item | Value | Check |
|---|---|---|
| SH2-Perf `main` | `4f86008` (D013), clean tree before this handoff | `git log`, `git status` |
| Hub `perf-metrics` | `e822e7f`, clean, `git describe --dirty --abbrev=12` = `e822e7f19019` | build id string in the DLL found once |
| Hub DLL / proxy / stand-in sha256 | `591e6375…35a89e5` / `13c89519…84e24801` / `4f888820…f500b22b` (full in [SETUP.md](SETUP.md), [evidence](evidence/ACCEPTANCE_2026-10-15.md)) | `sha256sum build/Release/*` = documented values |
| Acceptance report commit mix-up | fixed: D013 = `4f86008`, before D013 = `55974f1` | both evidence patches byte-identical to the commit diffs (report section "Correction") |

## TEST copy (`..\Stronghold 2 - TEST`)
| | Before (until 2026-10-15) | Now |
|---|---|---|
| hub DLL | build `a98bea10ad6e` (sampler, pre-D011), sha256 `4459368a…4695b563` | `e822e7f19019`, `591e6375…35a89e5` |
| proxy `d3d9.dll` | `13c89519…84e24801` | unchanged (same file) |
| `SH2Proxy.ini` | `target=system`, `hub=1`, no plan | same keys + `[plan] experiment=EXP-INGAME scenario=REAL_LAG_257` (**no game_speed**: the user names the real one, it goes in via `annotate`) |
| `SH2Prepared.json` | absent | written by `variant.py` |
| exe | sha256 `f3ccdf9b…0f32d34b`, LAA off | unchanged |

Installed with `variant.py baseline` (game was not running); `variant.py status` = `matches hub build: True`; installed DLL hash checked. Original folder: exe hash unchanged, no proxy/hub files.

**Way back**: `..\Stronghold 2 - TEST\_backup_before_e822e7f_20261015\` holds the old hub DLL, old `SH2Proxy.ini`, proxy and the previous `SH2Proxy.log` (+ `SHA256SUMS.txt`). Restore = game closed, copy `Stronghold2AnalyseHub.dll` and `SH2Proxy.ini` back, delete `SH2Prepared.json`. Hub off without restore: `variant.py hub off`. Fully vanilla: see SETUP "Import and provenance checks".

## Acceptance steps
| Step (SETUP "Check in Stronghold 2") | Prepared | Stand-in checked | In Stronghold 2 checked |
|---|---|---|---|
| 0 install + status + plan | done | – | – (no game start yet) |
| 1 first F9 recording, manifest `finalized` | yes | yes (e2e) | **open** |
| 2 second recording, new `capture_id` | yes | yes | **open** |
| 3 Alt-Tab during recording | yes | no | **open** |
| 4 END deactivation (with/without recording) | yes | yes (8/8, 4/4) | **open** |
| 5 game exit while recording (limit F117) | yes | yes | **open** |
| 6 import, re-import, annotate speed | yes | yes | **open** |

## Working trees
- SH2-Perf: this handoff, STATE pointer and the acceptance-report correction, committed locally (no push). Nothing else changed.
- Hub: clean at `e822e7f`, not touched.
- TEST: changed as in the table above (outside git). `SH2Perf_out` held only the old `SH2Proxy.log` (backed up); no recordings yet.

## Next action
Wait for the user's first game session. Then read yourself (do not ask the user to copy files): `..\Stronghold 2 - TEST\SH2Perf_out\Stronghold2AnalyseHub.log`, `SH2Proxy.log`, `*_manifest.json`, `*_prepared.json`, `latest.json`; check against SETUP steps 1–5 "Expected"; `python -I tools/ingest.py list`, then import per SETUP step 6 and `annotate --game-speed <N>` with the speed the **user** named. Record the result in EXPERIMENTS.md/FINDINGS (F113 stays stand-in-only until then) and update this file and STATE.

User actions needed: start the game from the TEST folder, load LAG_217_Reiter (REAL_LAG_257), say which game speed is set, do recordings 1+2 with F9, Alt-Tab, END in a suitable session, one session that quits while recording (last).
