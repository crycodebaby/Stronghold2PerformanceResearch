# SETUP — rebuild the environment

> Kurzfassung: Werkzeuge, Versionen, Umgebungsvariablen, Builds — Umgebung neu aufbauen.

Host: Windows 10/11 x64. Install via winget (as done 2026-10-15):

Native pose knowledge host (2026-10-16): `python -I tools/granny_pose.py` builds an
isolated Win32 target with the tools below; `python -I tools/test_granny_pose.py`
checks rejection gates and the exact rounding witness. No installation, game start,
asset input or download. [Contract, results, limits and commands](evidence/POSE_CONTRACT_2026-10-16.md).

| Tool | winget id / source | Version | Path |
|---|---|---|---|
| JDK 21 | `EclipseAdoptium.Temurin.21.JDK` | 21.0.12.101 | `C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot` |
| Ghidra | GitHub release zip (not in winget), sha256 `ddac49f9…d4db` verified | 12.1.4 | `%USERPROFILE%\Tools\ghidra_12.1.4_PUBLIC` |
| CMake | `Kitware.CMake` | 4.4.4 | WinGet packages dir (on PATH) |
| VS Build Tools 2022 | `Microsoft.VisualStudio.2022.BuildTools` + `--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended` | 17.14 / MSVC 14.44 | `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools` |
| x64dbg | `x64dbg.x64dbg` | 2026.05.27 | winget default |
| RenderDoc | `BaldurKarlsson.RenderDoc` | 1.46.0 | `C:\Program Files\RenderDoc` — NOTE: no D3D9 capture; usable only with DXVK (Vulkan) |
| ffmpeg | `Gyan.FFmpeg` | 9.0.2 | WinGet packages dir (on PATH) |
| DXVK | GitHub release tar.gz, sha256 `40565b4a…e608` verified | 3.1.1 | `%USERPROFILE%\Tools\dxvk-3.1.1` |
| Git, Python 3.14, Node 24 | preinstalled | | |

## Environment
- User env: `GHIDRA_INSTALL_DIR=%USERPROFILE%\Tools\ghidra_12.1.4_PUBLIC`
- REA: `npx -y rea-agents@6.5.0 setup --client claude_code --yes` run with `GHIDRA_INSTALL_DIR` + `JAVA_HOME` set → stored in `~/.claude.json` `mcpServers.rea.env`. Check: `npx -y rea-agents@6.5.0 doctor --client claude_code --json`.
- Restart Claude Code after REA setup so the MCP tools load.

## Repos
| Repo | Path | Branch |
|---|---|---|
| SH2-Perf (this) | `RE-Projects\SH2-Perf` | main; `git config core.hooksPath .githooks` |
| Stronghold2AnalyseHub | `RE-Projects\Stronghold2AnalyseHub` (clone of github.com/crycodebaby/Stronghold2AnalyseHub) | `perf-metrics` |

## Build AnalyseHub
```
cd Stronghold2AnalyseHub
cmake -S . -B build -A Win32
cmake --build build --config Release
# -> build\Release\Stronghold2AnalyseHub.dll, d3d9.dll (proxy, D009), SH2Launcher.exe (fallback)
```
If `cmake` is not on PATH yet (new shell needed after winget), use the path from `build\CMakeCache.txt` (`CMAKE_COMMAND`).
Re-run the configure step after a hub commit: the commit id is baked into `latest.json` at configure time.
Hub tests (no game needed): `build\Release\capture_test.exe` (capture ring, overflow, open/write errors, lifecycle, Push cost, manifests/provenance D012; ~20 s, exit code 0 = OK), `build\Release\sampler_test.exe` (sampler attribution + overhead, ~15 s, exit code 0 = OK) and `build\Release\standin_d3d9.exe` (D3D9 stand-in: copy it with the proxy `d3d9.dll` and the hub DLL into one folder, set `SH2HUB_OUT`, `SH2HUB_AUTORECORD=250`, `SH2HUB_SAMPLE=module`).

## Test copy
```
robocopy "Stronghold 2" "Stronghold 2 - TEST" /E      # robocopy exit 1 = copied OK
python -I tools/variant.py baseline                   # proxy + hub copy + SH2Proxy.ini + steam_appid.txt (40960)
python -I tools/variant.py status
python -I tools/test_variant.py                       # unit tests (temp folder, never touches TEST)
python -I tools/variant.py plan game_speed=90 experiment=EXP-001   # planned conditions of the next recordings (SH2Proxy.ini [plan])
```
`variant.py` also writes `SH2Prepared.json` (prepared state: variant + SHA-256 of exe/hub/proxy/ini + plan); the hub copies it into every recording.

## Import and provenance checks (D012)
```
python -I tools/test_import_safety.py ; python -I tools/test_ingest.py ; python -I tools/test_hardening.py   # import, conflicts, interruption, speed origins, reference release, bronze integrity, write lock (real processes), names (temp folders)
build\Release\lifecycle_test.exe                      # hub: blocked writer / sampler / hashing at deactivation (exit 0 = OK)
python -I tools/e2e_standin.py                        # real proxy + hub DLL + stand-in: 3 sessions -> manifests -> import -> END-key deactivation (needs the hub build and an interactive desktop)
python -I tools/e2e_standin.py --deactivate-only --repeat 8   # only the END deactivation, N times
python -I tools/ingest.py list                        # recordings in SH2Perf_out with manifest state
python -I tools/ingest.py import --recording <timestamp>      # verify -> stage -> atomic commit; sources stay
python -I tools/ingest.py annotate <capture_id> --game-speed 90   # user-confirmed value (never written into the raw manifest)
python -I tools/ingest.py verify <capture_id> ; python -I tools/ingest.py rebuild   # re-hash bronze / compare silver (add --write to replace)
```
Format and rules: [FORMATS/CAPTURE_MANIFEST.md](FORMATS/CAPTURE_MANIFEST.md).
TEST folder after `variant.py` (D009): `d3d9.dll` (proxy), `Stronghold2AnalyseHub.dll`, `SH2Proxy.ini`, with DXVK also `d3d9_dxvk.dll`.
Re-run the variant after every hub rebuild (refreshes the copies; `status` shows `matches hub build`).
Hub off without rebuild: `variant.py hub off` (or `hub=0` in `SH2Proxy.ini`, or env `SH2HUB_DISABLE=1`).
Fully vanilla TEST folder: delete `d3d9.dll`, `Stronghold2AnalyseHub.dll`, `SH2Proxy.ini` (and `d3d9_dxvk.dll`).
Logs: `TEST\SH2Perf_out\SH2Proxy.log` (loader, rewritten per start) and `Stronghold2AnalyseHub.log` (appended).

## Ghidra headless (project outside repo)
```
set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot
%GHIDRA_INSTALL_DIR%\support\analyzeHeadless.bat RE-Projects\ghidra-projects SH2 ^
  -import "Stronghold 2\Stronghold2.exe" -scriptPath SH2-Perf\ghidra_scripts ^
  -postScript ExportVtables.java SH2-Perf\captures\vtables_exe.csv
```

## Prepared build for the first check in Stronghold 2
| Item | Value |
|---|---|
| Hub commit (branch `perf-metrics`, clean tree) | `e822e7f` (`git describe --always --dirty --abbrev=12` = `e822e7f19019`, no `-dirty`); parent `ce07db2` |
| `build\Release\Stronghold2AnalyseHub.dll` sha256 | `591e6375a531c1dbcc6fee582e90f32f873f83629a3f4b7b065d4527b35a89e5` |
| `build\Release\d3d9.dll` (proxy) sha256 | `13c895196c175fd3cd963ba3b20ad84e92d4d9caf41cd2e1308eadfc84e24801` |
The build is **not** installed in the TEST copy; the user installs it (below).

**EXP-008 build (installed in TEST 2026-10-15, game closed)**: hub `e3ea53e` (`e3ea53e5d9f7`, clean, parent `e822e7f`), `Stronghold2AnalyseHub.dll` sha256 `54de688fd37840b07aa6b543be6089fb60a953010ee418d83e2e35d78d9f714d`, proxy unchanged `13c89519…`. Tests: `build\Release\granny_observer_test.exe` (needs the stand-in `granny2.dll` next to it — a test DLL, never copy it into a game folder), `capture_test`, `lifecycle_test`, `sampler_test`, `e2e_standin.py` (also with `SH2HUB_GRANNY=1`: logs "granny2.dll is not loaded", runs unobserved). Rebuild: re-run `cmake -S . -B build -A Win32` after a commit so the commit id is baked in. The manifests of the recordings name these hashes (`software.files`), so the log of the check shows which build ran.

## Check in Stronghold 2 (user): install, record, record again, Alt-Tab, END, import
What each step shows is also what the hub does *not* promise: END **deactivates** the hub (the DLL stays loaded until the game exits; to activate it again or to change the hub build, restart the game), and a normal exit of the game does **not** finalize a running recording (F117) - stop with F9 first.
0. **Install** (game closed, Steam running later): in `Stronghold2AnalyseHub` check `git describe --always --dirty --abbrev=12` = `e822e7f19019` and `Get-FileHash build\Release\Stronghold2AnalyseHub.dll` = the hash above. In `SH2-Perf`: `python -I tools/variant.py baseline` (copies proxy + hub into the TEST copy, writes `SH2Proxy.ini` and `SH2Prepared.json` there; it also sets LAA off for `baseline`), then `python -I tools/variant.py status` must say `matches hub build: True`; `Get-FileHash` of the DLL in the TEST folder equals the hash above. Then `python -I tools/variant.py plan game_speed=<N> experiment=EXP-INGAME scenario=SMOKE` with the number you will set in the game. Start the game from the TEST folder.
1. **First recording**: load a game, **F9** (overlay shows recording, or high tone with `min`), **F8** twice, wait ~20 s, **F9**. Wait until `Stronghold2AnalyseHub.log` shows `Recording stopped (user_toggle) … manifest published -> capture OK`. In `SH2Perf_out`: `*_manifest.json` with `"status": "finalized"`, `"capture_ok": true`, 64-digit hashes equal to the table above for `hub_dll` and the proxy, `game_speed` as you planned it; plus `*_prepared.json`. Note any visible hitch at the stop.
2. **Second recording** in the same session: F9 on, ~10 s, F9 off, wait for `manifest published`. A second manifest with a new `capture_id` and stem; `latest.json` names only this one.
3. **Alt-Tab**: F9 on, Alt-Tab to the desktop and back (and once more with a window/resolution change if you use one), ~10 s, F9 off, wait for `manifest published`. Expected: recording continues, overlay returns, manifest `capture_ok` true. Report `Device reset` lines or a visible problem.
4. **END (deactivation)**, once with no recording and once with a recording open (separate sessions are fine): press END. Log: `VK_END pressed: deactivating the hub`, `ImGui shutdown`, `All hooks disabled`, `Hub deactivated: hooks disabled, background threads ended. The DLL and its trampolines stay loaded …`; **no** `DLL detaching`, no `Deactivation DEFERRED`. The overlay disappears, the game keeps running normally, F9/F8 do nothing any more; with a recording open its manifest becomes `finalized` with `"stop_reason": "hub_shutdown"`. Quit the game normally afterwards. `Deactivation DEFERRED … still running: <thread>` means a background thread did not end: leave the game running, note the thread, send the log.
5. **Game exit while recording (to see the limit)**, last session: F9 on, quit the game normally without F9. Expected (stand-in result, unproven in the game): no `Recording stopped` line, the manifest stays `"status": "recording"`; `ingest.py import` refuses it (exit 5) and accepts it only with `--allow-interrupted`, as `incomplete`.
6. **Import** (game closed): `python -I tools/ingest.py list`; then for each finalized recording `python -I tools/ingest.py import --recording <timestamp> --exp EXP-INGAME --scenario SMOKE`; import the first one again (`already imported`). Confirm what you saw: `ingest.py annotate <id> --game-speed <N>` and `--phase-paused <marker>=true|false` per F8 phase. `usable as reference` will stay NO for a smoke run without release; it never says anything about save game, camera, graphics, V-Sync, hardware (CAPTURE_MANIFEST.md "What reference-v1 checks").
Report back: the log lines around steps 1-5, one finalized manifest (personal paths removed, D007), the `ingest.py` output of step 6, and anything that did not match "Expected". Nothing here claims game compatibility until you have done it.
