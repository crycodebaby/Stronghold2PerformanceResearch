# DECISIONS

> Kurzfassung: Warum wir etwas so machen (D###): Entscheidung, Begründung, verworfene Alternativen.

Format: ID · date · decision · rationale · rejected alternatives.

## D001 · 2026-10-15 · Patch/hook the original, not reimplement
- Decision: Improve performance via measurement, hooks and patches on `Stronghold2.exe`. Reimplementation = long-term vision.
- Rationale: ~1,300 game classes / 5 MB code; cause of slowdown unmeasured; proprietary middleware (Granny, LifeStudio); lockstep determinism makes bit-exact reimplementation very hard.
- Rejected: full open-source clone now (years, unclear payoff before knowing the hotspot).

## D002 · 2026-10-15 · Separate project repo, AnalyseHub stays its own repo
- Decision: `SH2-Perf` holds docs + small tools; `Stronghold2AnalyseHub` (upstream crycodebaby) gets changes on branch `perf-metrics`.
- Rationale: keeps upstream history clean, allows PR upstream; docs independent of DLL code.
- Rejected: vendoring AnalyseHub into SH2-Perf (loses upstream link); git submodule (extra friction now, can add later).

## D003 · 2026-10-15 · CMake build for AnalyseHub
- Decision: add `CMakeLists.txt` (Win32, Release, static CRT).
- Rationale: upstream `.sln` references no project (no `.vcxproj` in repo) → not buildable as-is. CMake is scriptable from CLI.
- Rejected: hand-written `.vcxproj` (verbose, hard to review).

## D004 · 2026-10-15 · Load AnalyseHub via launcher injection, not d3d9.dll proxy
- Status: **superseded by D009** (2026-10-15). Launcher kept as fallback.
- Decision: `SH2Launcher.exe` starts the game suspended, injects the DLL (`LoadLibraryW` via remote thread), waits for a ready event, resumes.
- Rationale: DXVK test (EXP-003) needs `d3d9.dll` in the game folder → a d3d9 proxy would collide. Hook must be installed before the game calls `Direct3DCreate9` → suspended start.
- Rejected: d3d9 proxy (DXVK conflict); attach-after-start injection (misses `Direct3DCreate9`).

## D005 · 2026-10-15 · Measurement first, game-code hooks later
- Decision: phase 1 instruments only D3D9 (counters, timings). No hooks into game functions until profiling data (EXP-001) points at a hotspot.
- Rationale: user requirement; avoids guesswork.
- Rejected: speculative hooks on pathfinder.

## D006 · 2026-10-15 · Bronze / silver / gold data layers
- Decision: `captures/` (bronze: raw CSV, logs, Ghidra exports; gitignored) → `data/` (silver: `index.jsonl` one metrics line per capture, tracked; `vtables.db` rebuilt by `sym.py build`) → `docs/` (gold: curated). Tools move data between layers (`ingest.py`, `sym.py`); the hub writes into a configurable dir (`SH2Launcher --out`, default `TEST\SH2Perf_out`) plus `latest.json`.
- Rationale: raw data never enters agent context; comparisons run on small structured lines; captures are reproducible via `meta.json` (hashes, variant, hub commit, CPU/GPU).
- Rejected: CSVs in git (size, personal data); a database server (overkill); hub writing next to the exe (mixes game and data files).

## D007 · 2026-10-15 · Remove personal paths before publishing raw data
- Decision: raw logs/CSVs (`captures/`) may contain absolute paths (the hub log lists every loaded module path incl. user name). Before any upload, issue attachment or release they are scrubbed (replace `<drive>:\Users\<name>` with `%USERPROFILE%`). `data/` and all `*.md` must never contain absolute user paths — enforced by `lint_docs.py`.
- Rationale: privacy; repo may become public.
- Rejected: stripping paths in the hub (module paths are the evidence for F032 locally).

## D008 · 2026-10-15 · Function analysis through structural briefs
- Decision: agents analyse functions via `tools/sym.py` + `tools/fbrief.py` (addresses, sizes, callers/callees, loops, strings). Decompiled code stays inside Ghidra — not in the repo, not in agent context.
- Rationale: legal (no decompiled code in repo/releases), context budget, briefs are diffable facts.
- Rejected: pasting pseudocode into docs/context.

## D009 · 2026-10-15 · Load AnalyseHub via d3d9.dll proxy (chains to system d3d9 or DXVK)
- Decision: default loader is a `d3d9.dll` proxy in the TEST folder (hub repo `proxy/`). It loads the real d3d9 (`target=system` → system dir, or `target=d3d9_dxvk.dll` = renamed DXVK) and then `Stronghold2AnalyseHub.dll`; its `Direct3DCreate9` waits (≤ 15 s) until the hub reports its hook. Config `SH2Proxy.ini` (`target`, `hub`, `hubdll`, `out`), env overrides `SH2HUB_DISABLE=1`, `SH2HUB_OUT`. `hub=0` = pass-through without recompiling. `tools/variant.py` installs proxy + hub copy + ini for every variant and places DXVK as `d3d9_dxvk.dll`. The hub logs the exe sha256 and `known build: yes/no` (F058), log only.
- Rationale: game starts normally (double-click), no suspended process, no remote thread; D004's objections are resolved: DXVK conflict → chaining via `target`; hook timing → the proxy owns the export the game calls. The observed launcher failure (F080) is **not** the reason: it was a hub bug (F081), fixed in the hub; cause in game still to confirm (F082).
- Details: real exports resolved at runtime (17 named exports of system d3d9 = DXVK 3.1.1), naked jump stubs; nothing loaded under loader lock (starter thread); the hub finds the real module through the proxy export `SH2Proxy_RealModule` (two modules named d3d9.dll are loaded); `target` pointing at the proxy itself is refused.
- Rejected: launcher only (extra start step, suspended start fragile); static `.def` forwarders (fixed target, no DXVK switch without rebuild); loading the hub inside `DllMain` (loader lock); DXVK's own `d3d9.dll` slot with hub injection (needs the launcher again).
