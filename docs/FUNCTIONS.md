# FUNCTIONS

Ghidra renames. One row per function. Addresses = image base 0x00400000 (ASLR on → rebase at runtime: `runtime = base + (addr - 0x400000)`).
Confidence: `hoch` (RTTI/vtable/exported symbol or string proof) · `mittel` (behavior matches) · `niedrig` (guess).

| Address | Name | Module | Confidence | Evidence |
|---|---|---|---|---|
| — | — | — | — | (empty — Ghidra analysis not started, see STATE.md) |
