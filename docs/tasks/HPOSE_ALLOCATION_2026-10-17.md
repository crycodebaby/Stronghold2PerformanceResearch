# H-record container allocation: bounded work order

> Kurzfassung: Genau einen statischen Kapazitaet-zu-Byte-Pfad hinter Exe RVA 0x38D500 untersuchen. Allokatorargumente, logische Laenge und echte Heapreserve getrennt; kein Spielstart oder Performancepatch.

Basis: `deb556d`; follow-up to [creation/selection](../evidence/HPOSE_CREATION_2026-10-17.md).
Read AGENTS.md and the current STATE/HANDOFF before working. Earlier findings are claims to re-check.

Completed bounded result: [allocator argument, transfer and exact remaining boundary](../evidence/HPOSE_ALLOCATION_2026-10-17.md).
Actual internal heap reservation and full pose lifetime were not established; current HANDOFF supplies the next task.

## Question and scope

From Grow `0x38D6D0` -> call `0x38D73E` -> `0x38D500`, follow the requested record capacity to the immediate
allocation argument and the stores to the same begin/end/capacity container. Include the Resize connection
`0x38DC70` -> call `0x38DCC1`. Keep O-relative offsets distinct from offsets relative to its container at O+0x18.

Identify the numerical domain, arithmetic overflow behavior and directly visible zero/failure branches. Describe
copy/transfer ordering only where needed to explain the final pointers. Do not expand into all allocation callers,
full resource-list count provenance, complete lifetime/reuse analysis or allocator internals unrelated to the call.

## Evidence and acceptance

- Re-check the original Exe/DLL identities from the creation evidence; use only a separate closed Ghidra project
  copy with `-readOnly -noanalysis` and matching program identity. Original installation/raw/audit/database stay intact.
- Each claimed transition names the function, RVA and object-relative field. Publish own scripts, SHA fingerprints,
  lengths and derived facts; raw bytes/listings and private paths remain in ignored local build outputs.
- Separate requested count, logical live count, capacity, bytes passed to the allocator and any unproved heap overhead.
  A nominal byte request is not a runtime measurement of reserved memory or proof that allocation succeeded.
- Verify code locations against the actual PE, with explicit build/schema failures also under `python -O`.
  Synthetic tests must demonstrate missing/tampered evidence is rejected; fingerprints alone do not prove semantics.
- If an own arithmetic model is useful, implement only a justified valid domain. Mark extra safety rejection behavior
  as our contract; do not emulate undefined/corrupt state or execute original Exe routines in a synthetic host.
- Run the applicable ordinary checks, own native checks if changed, and a focused independent interpretation review.
  Update findings, current STATE/HANDOFF and one exact next experiment. An unresolved indirect edge is valid if precise.

## Excluded

No new game recording, TEST installation, hook/observer change, cache/skip/pooling/threading patch, game asset export,
original-function execution or performance claim. No Git history rewrite or automatic GitHub publication.
Make a local commit after a coherent verified result; report when the accumulated research branch is ready to push.
