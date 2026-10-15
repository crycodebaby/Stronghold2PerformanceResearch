# GR2 — Granny 3D (RAD Game Tools, proprietary)

> Kurzfassung: Granny-3D-Modelle (proprietär, v6, Oodle-komprimiert). Für Performance unwichtig.

| Field | Value | Status |
|---|---|---|
| Count | 3,326 (`meshes/**`) | [verifiziert] |
| Magic | `B8 67 B0 CA F8 6D B1 0F 84 72 8C 7E 5E 19 00 1E` (32-bit LE) | [verifiziert] |
| Header @0x10 | u32 header_size (e.g. 0x1B8), u32 format 0, 8 B reserved | [verifiziert] knight.gr2 |
| Header @0x20 | u32 version=6, u32 total_size, u32 crc, u32 section_array_offset (rel. 0x20), u32 section_count | [verifiziert] knight.gr2: 6, 0xBAB7, …, 0x38, 8 |
| Section header | 44 B; first u32 = compression | [verifiziert] |
| Compression | 0 none, 1 Oodle0, 2 Oodle1 | [verifiziert] counts: type 2 dominates |
| Runtime | `granny2.dll` 2.6.0.14 (`GrannyGetVersionString`) | [verifiziert] |
| Referenced by | `.bdg`, `.uni`, `.aml` descriptors (`*.GR2` names) | [verifiziert] |

## Decompression tests
| Test | Result | Status |
|---|---|---|
| `tools/granny_raw` → `_GrannyConvertFileToRaw@8(knight.gr2)` | returns 1; output 87,672 B (input 47,799 B) | [verifiziert] |
| Output format | NOT a GR2 container (no magic; starts with offset table `5c 00 00 00 9c 00 …`) = flattened in-memory struct dump | [verifiziert] header dump |
| Uncompressed standard GR2 | needs `GrannyReadEntireFile` + file-builder/write API (`GrannyBeginFile…`) | open task, low priority |

## Public tools
| Tool | Status |
|---|---|
| opengr2, Norbyte lslib (Divinity) | [Hypothese] target GR2 v7 + Oodle1; v6 / Oodle0 support unverified |
| Blender GR2 importers | [Hypothese] expect uncompressed GR2 |

Priority: low for the performance goal (D001). Revisit for the reimplementation vision.
