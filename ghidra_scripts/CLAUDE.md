# ghidra_scripts/

Java GhidraScripts, run headless against the project `../ghidra-projects/SH2`
(programs `Stronghold2.exe`, `dragonfly.dll`, `granny2.dll` (imported 2026-10-15 for EXP-007); already analysed — use `-process <prog> -noanalysis -readOnly`).

| Script | Args | Output |
|---|---|---|
| `ExportVtables.java` | `<out.csv>` | RTTI vtable slots: class, slot, address, size, callers → feed `tools/sym.py build` |
| `ExportFunctions.java` | `<out.csv>` | every function: entry, body min/max, all body ranges, name, name source, thunk → `captures/functions/<module>_functions.csv` for `tools/funcsamples.py` |
| `AddressContext.java` | `<out.txt> <addr>...` | read-only: containing / previous / next function, instruction or data, references to the address or its function |
| `InstructionStats.java` | `<out.txt> <addr>...` | read-only: instruction count, mnemonic histogram, loop back edges, indirect calls per function |
| `InstructionWindow.java` | `<out.txt> <before> <after> <addr>\|ret:<addr>...` | read-only: instructions around an address (call-site argument setup) or every RET of a function with Ghidra's convention/purge guess (stdcall pop count); assembly stays under `captures/` |
| `CreateFunctionsAt.java` | `<out.txt> <addr>...` | **writes**: creates a function where code starts and none exists (entries only reached via data pointers) |
| `AnnotateFunctions.java` | `<out.txt> addr#name#comment...` | **writes**: name and/or plate comment for FUNCTIONS.md knowledge; no spaces, commas or `\|` in arguments (the .bat goes through cmd) |
| `FunctionBrief.java` | `<addr hex> <out.txt>` | ≤ 30-line structural summary; wrapper `tools/fbrief.py` |
| `PoseContract.java` | `<output-dir> <depth> <VA>...` | bounded read-only function/callee byte export, no decompilation; use separate project copy; local evidence in ignored build/knowledge-pose |
| `hpose_creation.java` | `<output-dir> <VA>...` | pinned Exe identity, bounded IAT references/function evidence on a separate read-only copy; raw listings stay local under build/hpose-creation |
| `hpose_resource.java` | `<output-dir> <VA>...` | pinned Exe, bounded function/reference export for resource provenance; `x:<VA>` omits direct function export, local ignored output only |

Rules:
- Scripts emit addresses, names, counts and strings — decompiled code stays inside Ghidra (D008).
- Write results to a file given as argument (headless stdout is noisy); keep files under `captures/`.
- Environment: `GHIDRA_INSTALL_DIR`, `JAVA_HOME` = JDK 21 (docs/SETUP.md).
