# S2M / S2C / SH2 — maps, castles, cutscene maps

Extensions share one layout (S2M skirmish/sandbox maps, S2C campaign castles, SH2 cutscene maps). [verifiziert: same header start]

## Layout (sample: `maps/Arena of Kings.s2m`, 843,825 B)
| Offset | Type | Meaning | Status |
|---|---|---|---|
| 0 | u32 | `2` = number? / version of header block | [Hypothese] |
| 4 | repeated | key/value entries: `u32 keyLen, char key[keyLen], u32 valLen, u16 val[valLen]` (UTF-16 values) or `u32` values | [verifiziert] for `author`=`Firefly`, `type`=`kingmaker` |
| … | keys | `author`, `type`, `balanced`, `mapsize`, `maxplayers`, `version` | [verifiziert] |
| 146 | zlib | stream 1 → 1,661 B, starts with class tag `MapHeader` | [verifiziert] |
| next | zlib | stream 2 → 327,820 B, `RadarMap` (minimap) | [verifiziert] |
| next | zlib | stream 3 → 9,689,710 B, map body (terrain/objects; contents TBD) | [verifiziert] size; contents unknown |

Decompressed streams contain class-name tags + 32-bit ids (e.g. `1e ab a1 5c`) → likely `Dragonfly::ObjectStream` / `Serializable` serialization. [Hypothese]

## Related
- `gameRules.dat`: single zlib stream. [verifiziert]
- `.aic` (AI castle), `.csc` (cutscene script): u32 version header, not decoded.
