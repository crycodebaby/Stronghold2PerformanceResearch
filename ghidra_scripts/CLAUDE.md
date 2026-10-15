# ghidra_scripts/

Java GhidraScripts, run headless against the project `../ghidra-projects/SH2`
(programs `Stronghold2.exe`, `dragonfly.dll`; already analysed — use `-process <prog> -noanalysis -readOnly`).

| Script | Args | Output |
|---|---|---|
| `ExportVtables.java` | `<out.csv>` | RTTI vtable slots: class, slot, address, size, callers → feed `tools/sym.py build` |
| `FunctionBrief.java` | `<addr hex> <out.txt>` | ≤ 30-line structural summary; wrapper `tools/fbrief.py` |

Rules:
- Scripts emit addresses, names, counts and strings — decompiled code stays inside Ghidra (D008).
- Write results to a file given as argument (headless stdout is noisy); keep files under `captures/`.
- Environment: `GHIDRA_INSTALL_DIR`, `JAVA_HOME` = JDK 21 (docs/SETUP.md).
