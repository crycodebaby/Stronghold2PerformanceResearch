# Other formats (inventory)

> Kurzfassung: Inventar der übrigen Formate (Bink, Audio, Deskriptoren, Skripte).

| Ext | Count | Magic / start | Meaning | Status |
|---|---|---|---|---|
| `.bik` | 89 | `BIKi` | Bink 1 video (ffmpeg decodes) | [verifiziert] magic |
| `.mp3` / `.wav` | 3,992 / 1,817 | — | speech/music/sfx via Miles (`Mss32.dll`, `mssmp3.asi`) | [verifiziert] count |
| `.bdg` | 122 | u32 13 … | building descriptor, references GR2 | [Hypothese] |
| `.uni` | 99 | u32 6, u32 2, `actor.GR2` | unit descriptor (model + anims) | [verifiziert] start bytes |
| `.aml` | 36 | u32 3, `bear.GR2` | animal descriptor | [verifiziert] start bytes |
| `.aic` | 47 | u32 1 | AI castle layout | [Hypothese] |
| `.csc` | 49 | u32 2, u32 0x18 | cutscene script | [Hypothese] |
| `.fx` | 76 | HLSL text | D3DX effect files | [verifiziert] |
| `.xml` | 34 | text | config, materials, LOD settings | [verifiziert] |
| `.cab` | 154 | `MSCF` | DirectX redist only (`resources/directx`) | [verifiziert] |
