# FINDINGS

> Kurzfassung: Fakten (F###) mit Status [verifiziert | Hypothese | widerlegt] und Beleg. Engine, Binary, Formate, Performance.

Status: `[verifiziert]` = directly observed with evidence · `[Hypothese]` = inference, unproven · `[widerlegt]` = disproven.
IDs are stable; never renumber. Append, don't rewrite history (mark old entries `[widerlegt]` instead).

## Binary / build

| ID | Status | Fact | Evidence |
|---|---|---|---|
| F001 | [verifiziert] | `Stronghold2.exe` is PE32 i386 (machine 0x014c), 14,208,000 B, sha256 prefix `f3ccdf9bb4115820` | `tools/pe_info.py Stronghold2.exe` |
| F002 | [verifiziert] | Link timestamp 2020-04-24 16:20:16 UTC, linker 10.0 (MSVC 2010), Rich header present | PE header parse (FileHeader.TimeDateStamp, OptionalHeader.MajorLinkerVersion) |
| F003 | [verifiziert] | No PDB / no RSDS debug record | no `RSDS` signature in file |
| F004 | [verifiziert] | Sections: .text 5.24 MB, .rdata 1.49 MB, .data VSize 33.97 MB (raw 6.38 MB), .rsrc, .reloc | section table |
| F005 | [verifiziert] | No SteamStub wrapper (no `.bind` section) → exe can be patched/analysed directly | section table |
| F006 | [verifiziert] | `LARGE_ADDRESS_AWARE` NOT set → 2 GB user VA limit; ASLR (DYNAMIC_BASE) and NX set | FileHeader.Characteristics & 0x20 == 0; DllCharacteristics 0x40, 0x100 |
| F007 | [verifiziert] | 1,634 RTTI type names: `Stronghold2::` 1331, `GlowWorm::` 185, `Dragonfly::` 55, `std` 22, `boost` 10, `GameSpy` 7 | regex `\.\?A[VU](\w+)@@` over exe |
| F008 | [verifiziert] | Imports: d3d9 (`Direct3DCreate9` only), d3dx9_27 (34 fns), dragonfly.dll (274), granny2.dll (49), binkw32 (7), LifeStudioHeadAPI (5), GDPFile (1), ffonlinelib (48), WS2_32, MSVCR100/MSVCP100 | import table parse |
| F009 | [verifiziert] | `dragonfly.dll` exports C++-mangled symbols (Vector3D, XMLReader, PackFile, ClassRegistry, Timer, ObjectStream…) → free type signatures | export table parse |
| F010 | [verifiziert] | exe imports `CreateThread`, critical sections, mutex | string/import scan |
| F011 | [Hypothese] | Simulation is single-threaded (threads only for loading/network/audio) | none yet — F010 only proves threads exist; needs runtime thread CPU profile |

## Engine architecture (from RTTI names only — names ≠ behavior)

| ID | Status | Fact | Evidence |
|---|---|---|---|
| F020 | [verifiziert] | RTTI names exist: `GlowWorm::Simulation`, `SyncCheck`, `SyncLayer`, `SyncListener`, `SyncUI` | RTTI scan |
| F021 | [Hypothese] | Deterministic lockstep multiplayer simulation | inferred from F020 |
| F022 | [verifiziert] | Grid layer classes: `Layer`, `HeightLayer`, `DangerLayer`, `DesirabilityLayer`, `ClaimLayer`, `ProximityLayer`, `SearchLayer`, `SpreadLayer`, `LogicLayer`, `ConnectionLayer`, `LinkageLayer`, `EstateLayer`, `TempLayer`, `ChannelLayer`, `ContextLayer`, `BuildingLayer` | RTTI scan |
| F023 | [verifiziert] | Pathing classes: `Pathfinder`, `BiDiPathfinder`, `Cluster`, `ClusterNavigator` (global ns), `Navigator`, `HarassNavigator`, `DummyNavigator`, `QuadTree` | RTTI scan |
| F024 | [Hypothese] | Hierarchical (cluster) + bidirectional pathfinding | inferred from F023 names |
| F025 | [verifiziert] | AI implemented as `*Chore` classes (e.g. `AIAttackActorChore`, `AIMoveTroopsChore`); `Dragonfly::Chore` base | RTTI scan |
| F026 | [verifiziert] | Formation classes: `BoxFormation`, `ColumnFormation`, `GridFormation`, `KnotFormation`, `LineFormation` | RTTI scan |
| F027 | [verifiziert] | Render-side classes: `LevelOfDetailManager`, `GroundShadows`, `PostEffects`, `MaterialManager`, `VertexDeclarationPool`, `D3DResourceManager` | RTTI scan |

| F028 | [verifiziert] | Ghidra 12.1.4 RTTI analysis: 1,585 vftables / 31,865 virtual slots in exe; 82 / 539 in dragonfly.dll | `ExportVtables.java` → `captures/vtables_*.csv` |
| F029 | [verifiziert] | Largest S2Actor virtual function: slot 20 @ 0x004E92C0, 12,783 B | vtables_exe.csv (see FUNCTIONS.md) |
| F070 | [verifiziert] | `Simulation::vf02` (0x0076ADC0) has 3 blocks, no loop, 1 direct callee (0x0076AC40) and 13 indirect calls | `tools/fbrief.py 0x0076ADC0` |
| F071 | [Hypothese] | `Simulation::vf02` is the sim tick, dispatching to subsystems via virtual calls | F070 shape only; confirm with profiler samples (design/SAMPLING_PROFILER.md) |
| F072 | [Hypothese] | `S2Actor::vf20` is the per-actor update/think function | size only (F029) |
| F073 | [Hypothese] | `BiDiPathfinder::vf05` is the path search step | largest pathfinder vfunc |
| F074 | [Hypothese] | `ProximityLayer` serves target search (nearest enemy) | class name only |

## Runtime DLLs

| ID | Status | Fact | Evidence |
|---|---|---|---|
| F030 | [verifiziert] | `msvcr100.dll`, `msvcp100.dll`, `msvcrt.dll` in game folder are **x86-64** (machine 0x8664, optmagic 0x20b) next to a 32-bit exe | PE header: msvcr100 sha256 `ae3cb6c6afba9a4a`, msvcp100 `934d882efd3c0f3f`, msvcrt `1cb0dab84545d9fd` |
| F031 | [verifiziert] | 32-bit VC2010 runtime present in `C:\Windows\SysWOW64\msvcr100.dll` / `msvcp100.dll` | `ls` |
| F032 | [Hypothese] | Loader skips the wrong-arch local DLLs and loads SysWOW64 versions | game reportedly runs; verify by listing loaded modules at runtime (x64dbg / AnalyseHub module dump) |
| F033 | [verifiziert] | `msvcr71.dll`, `msvcp71.dll` in game folder are i386 | PE header |

## Assets / formats → details in `docs/FORMATS/`

| ID | Status | Fact | Evidence |
|---|---|---|---|
| F040 | [verifiziert] | All assets are loose files; no archive container | directory inventory |
| F041 | [verifiziert] | 3,326 GR2 files, all Granny file format version 6, 32-bit LE magic; `granny2.dll` = 2.6.0.14 | header parse; DLL version string |
| F042 | [verifiziert] | GR2 sections use compression types 0 (none), 1 (Oodle0), 2 (Oodle1) | section header compression field |
| F043 | [verifiziert] | `granny2.dll` exports `GrannyConvertFileToRaw`, `GrannyDecompressData` → own DLL can decompress for export | `tools/pe_info.py granny2.dll --exports` |
| F044 | [verifiziert] | DDS: DXT1 937, DXT3 806, uncompressed 32bpp 143, DXT5 5, 8bpp 1 | DDS header FourCC scan |
| F045 | [verifiziert] | TGA: RLE 32bpp 135, raw 32bpp 84, RLE 24bpp 6, raw 24bpp 2 | TGA header scan |
| F046 | [verifiziert] | S2M/S2C/SH2 map files: key/value header (`author`, `type`, `balanced`, `mapsize`, `maxplayers`, `version`) + 3 chained zlib streams (`MapHeader` 1.6 KB, `RadarMap` 328 KB, body 9.7 MB for Arena of Kings) | zlib walk |
| F047 | [verifiziert] | `gameRules.dat` is a zlib stream (starts `78 9C`) | hexdump |
| F048 | [verifiziert] | LifeStudio: `.gdp` = OLE Compound File (`D0 CF 11 E0`), `.mms` magic `MMSF` v3, `.mma` magic `MMLF` v4 | magic bytes |
| F049 | [verifiziert] | Shaders are HLSL source (`.fx`) loaded at runtime | file content `#include "...` |
| F050 | [verifiziert] | `GrannyConvertFileToRaw` output is a flattened in-memory dump, not a GR2 container | `tools/granny_raw` on knight.gr2 → no magic, 87,672 B (docs/FORMATS/GR2.md) |

## Steam / launch

| ID | Status | Fact | Evidence |
|---|---|---|---|
| F055 | [verifiziert] | Steam AppID 40960 | `installscript.vdf` HasRunKey `…\Steam\Apps\40960` |
| F056 | [verifiziert] | `SteamLib.dll` imports `SteamAPI_Init` etc. but NOT `SteamAPI_RestartAppIfNecessary` | `pe_info.py SteamLib.dll --imports` |
| F057 | [Hypothese] | Direct start (outside Steam) works with `steam_appid.txt`=40960 while Steam runs | untested |

## Performance (unmeasured)

| ID | Status | Fact | Evidence |
|---|---|---|---|
| F060 | [Hypothese] | User report: 2×~100 knights → ~20 FPS; more troops/melee → 1–2 FPS on strong PCs | user statement, not yet measured |
| F061 | [Hypothese] | Cause is CPU-side simulation (pathing/targeting/melee) rather than GPU | none — FPS collapse correlating with melee suggests sim; must measure (EXP-001) |
| F062 | [Hypothese] | 2 GB VA limit (F006) contributes to stutter/crash on large maps | none — test EXP-002 |
