# LifeStudio Head (facial animation middleware) — rough classification only

Scope: classify, do NOT decode (low perf relevance).

| Ext | Location | Magic | Guess | Status |
|---|---|---|---|---|
| `.gdp` | `meshes/heads/*_hi.gdp` (42) | `D0 CF 11 E0 A1 B1 1A E1` = OLE Compound File (MS Structured Storage) | head geometry/morph package; open with any CFB reader (e.g. Python `olefile`) | [verifiziert] magic |
| `.mms` | `meshes/heads/`, `speech/` (642) | `MMSF`, u32 3 | morph/speech sequence (lip-sync) | [verifiziert] magic, purpose Hypothese |
| `.mma` | `meshes/heads/` (16) | `MMLF`, u32 4 | morph library per character | [verifiziert] magic, purpose Hypothese |

Runtime DLLs: `LifeStudioHeadAPI.dll`, `GDPFile.dll`, `IMorphFile.dll`, `UVPupil.dll`. exe imports `IGDPFile::Create`, `ITransformer/IMMTree/IAnimator/IOptions/ISequencer::Create`. [verifiziert]
