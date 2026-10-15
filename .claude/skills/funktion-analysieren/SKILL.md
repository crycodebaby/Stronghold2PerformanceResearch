---
name: funktion-analysieren
description: Analyse a function or address in Stronghold2.exe / dragonfly.dll (hex address, Class::vfNN, hotspot candidate, profiler sample). Resolves it, summarizes its structure and records the result in docs/FUNCTIONS.md.
---

# Funktion analysieren

Decompiled code stays inside Ghidra (D008): the context receives addresses, names, counts and strings only, via tools capped at ~30 lines. Addresses are image-base 0x00400000.

1. **Resolve**: `python -I tools/sym.py addr <hex>` (or `sym.py class <name>` to find candidates).
   If `data/vtables.db` is missing: `python -I tools/sym.py build` first.
   Done when: entry address, size and the vtable slot(s) using it are known, or the tool says "no known virtual function".
2. **Check existing knowledge**: search `docs/FUNCTIONS.md` and `docs/FINDINGS.md` for the entry address.
   Done when: existing entries are listed or confirmed absent.
3. **Brief**: `python -I tools/fbrief.py <entry hex>` → size, blocks, loops, callers, callees, strings.
   Repeat for the 1–3 callees that dominate (most call sites, or loops) when the question needs depth.
   Done when: the brief(s) answer the question asked, or the open question is stated precisely.
4. **REA (optional, after a Claude Code restart)**: REA tools on `Stronghold2.exe` with provider `ghidra` give xrefs and call graphs; request summary/graph views and skip pseudocode output.
5. **Record**:
   - Name in `docs/FUNCTIONS.md` only at confidence `mittel` (behaviour matches evidence) or `hoch` (RTTI/string/export proof); cite the evidence (brief facts, capture_id).
   - Guesses (`niedrig`) go to `docs/FINDINGS.md` as `[Hypothese]`.
   - `docs/STATE.md` updated.
   Done when: `python -I tools/lint_docs.py` prints OK.
