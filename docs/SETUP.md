# SETUP — rebuild the environment

> Kurzfassung: Werkzeuge, Versionen, Umgebungsvariablen, Builds — Umgebung neu aufbauen.

Host: Windows 10/11 x64. Install via winget (as done 2026-10-15):

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
# -> build\Release\Stronghold2AnalyseHub.dll, build\Release\SH2Launcher.exe
```

## Test copy
```
robocopy "Stronghold 2" "Stronghold 2 - TEST" /E      # robocopy exit 1 = copied OK
python -I tools/variant.py baseline                   # also writes steam_appid.txt (40960)
```

## Ghidra headless (project outside repo)
```
set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot
%GHIDRA_INSTALL_DIR%\support\analyzeHeadless.bat RE-Projects\ghidra-projects SH2 ^
  -import "Stronghold 2\Stronghold2.exe" -scriptPath SH2-Perf\ghidra_scripts ^
  -postScript ExportVtables.java SH2-Perf\captures\vtables_exe.csv
```
