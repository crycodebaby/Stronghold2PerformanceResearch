# H-resource release: constructor-bound candidate and open provenance

> Kurzfassung: No single dynamic target of Exe RVA 0x38E428 is proved. A concrete constructor/table candidate releases mesh/file resources and reaches additional indirect calls. Cache provenance and intervening initialization remain explicit boundaries; no lifetime or optimization clearance.

Date: 2026-10-17. Research basis `183762c`, branch `hpose-allocation-proof`.
Later tooling follow-up: [initializer effects](HPOSE_INITIALIZER_EFFECTS_2026-10-17.md) extends this same verifier
and manifest to schema 2. The 15-function/schema-1 counts in this dated report describe revision `12b8050`;
check out that revision to reproduce that original tool/manifest pair. No historical claim is silently upgraded.
[Scope](../tasks/HPOSE_RESOURCE_RELEASE_2026-10-17.md). Follows [cleanup](HPOSE_CLEANUP_2026-10-17.md),
[creation](HPOSE_CREATION_2026-10-17.md), [allocation](HPOSE_ALLOCATION_2026-10-17.md).
All addresses below are **Exe RVAs**, except expressly identified VAs. Exe base `0x00400000`,
SHA-256 `f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b`.
Granny identity checked only as file SHA-256 `94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd`.
No dragonfly implementation was analyzed; Exe import names identify that boundary only.
O, H and R are working labels, not recovered C++ types; R=*(H+0xC).

## Provenance actually observed

Creation `0x38E0A0` calls producer `0x3BB400` at `0x38E10E`; result is saved locally at `0x38E113`.
Call `0x38E14B` passes its address to list-node helper `0x38CF70`. That helper allocates a node,
copies the pointed value into node+8 (`0x38CF96`..`0x38CF9B`) and returns the node.
Creation later reads node+8 at `0x38E270` and stores it to H+0xC at `0x38E276`.
This proves one immediate producer-to-H transfer, not all list content or all callers.
The other list-processing helper `0x38DDC0` also calls this producer (calls `0x38DE8A`, `0x38DF55`);
its entire list-content invariant is not claimed.

Producer has distinct paths:

- Existing entry: reads entry+0x28 at `0x3BB52F`/`0x3BB537`, increments that referent's +4 count,
  returns the same value via `0x3BB56F` and edge `0x3BB571` to `0x3BB80E`.
  No constructor or Vptr check is performed on this hit path.
- New object: allocation call `0x3BB57B`, then constructor `0x395B30` at `0x3BB593`.
  Constructor stores count 1 at R+4 (`0x395B5C`) and table **VA `0x009F49D4`** at R+0 (`0x395B65`).
  PE bytes at table slot 0, **RVA `0x5F49D4`**, contain **VA `0x00796470`**, hence candidate RVA `0x396470`.
  This is a concrete constructor/table binding, not a proof that every later H resource retains it.
- Between construction and successful normal return there are initialization calls to `0x395CC0`
  (`0x3BB5D8`, `0x3BB69B`) on the produced object. The producer also contains a failure-path
  indirect slot-0 release at `0x3BB6EF`; failed/null returns are not successful resource bindings.
  The successful later value is carried through local -0x88 and EDI to the return at `0x3BB80C`.
- Producer builds a cache node with `0x3BB320` (`0x3BB7A6`) and passes it into insertion helper
  `0x2CF1D0` (`0x3BB7B5`). Node construction copies source+0x1C to node+0x28 (`0x3BB3A5`/`0x3BB3A8`),
  where source is the producer's temporary key/value structure carrying the resource pointer.
  This demonstrates a local insertion representation, not all cache writers or hit generations.

No source class name or exhaustive set of alternative classes is asserted. The known table is a candidate
for this provenance, not an arbitrary enumerated class target and not a globally resolved call target.

## Narrow initialization inventory and precise remaining escape

Initializer `0x395CC0` captures incoming R in EDI at `0x395CF8`. Its direct field stores include R+0x10
at `0x395DCE` (Granny file-return storage), R+8 at `0x395DF0` and model-pointer R+0xC at `0x395E92`.
The latter comes from the file-info-derived model array; creation consumes R+0xC at `0x38E279` before
`GrannyInstantiateModel`. This strengthens the source-model/resource interpretation without recovering a type.
No direct R+0 Vptr replacement was identified in this bounded initializer inventory. This observation is not
an invariant across calls. In particular it passes R as ECX into `0x394350` at `0x395E4F`, `0x3949A0`
at `0x395E63`, and `0x394000` at `0x395E7E`; these bodies were not descended into. Consequently preservation
of the constructor Vptr across initialization is still open at those exact edges.
Imports `_GrannyReadEntireFileFromMemory@8` (IAT `0x500A68`), `_GrannyGetFileInfo@4` (`0x500B00`),
`_GrannyFreeFileSection@8` (`0x500A78`) and `_GrannyFreeFile@4` (`0x500B04`) concern file/derived pointers;
register-indirect calls `0x3961CF` through `0x3961FF` use the imported FreeFileSection pointer, not an
unresolved R virtual slot. The pack-file imports at `0x500564`/`0x500568` remain imported implementation boundaries.
No recursive initializer/callee reconstruction was performed.

## What the concrete table candidate would do

Conditional on R carrying that table at release time, `0x396470` calls `0x3963A0` with the same object
at `0x396476`; it calls CRT delete at `0x396482` when argument bit 0 is set (the cleanup passes 1).
Destructor `0x3963A0` stores the same table at `0x3963CC`, then calls resource-clear helper `0x396240`
at `0x3963D9`. Its remaining direct calls include `0x397630`, `0x395810` and CRT delete;
these are boundary inventories, not fully analyzed helper semantics.

The three central release callees examined are wrapper `0x396470`, destructor `0x3963A0`, and helper `0x396240`.
The helper traverses subrecords from R+0x2C, releasing their +8 mesh-deformer and +0xC mesh-binding pointers
through `_GrannyFreeMeshDeformer@4` at `0x39626C` (IAT `0x500A60`) and `_GrannyFreeMeshBinding@4`
at `0x39627A` (IAT `0x500A64`). At `0x39638B` it passes the field value *(R+0x10), not the field address, to `_GrannyFreeFile@4`
(IAT `0x500B04`) and then nulls R+0x10 at `0x396391`.
The helper also processes additional arrays/references and reaches these unresolved dynamic effects:

- `0x396262`: table slot +8 on a subrecord+0x70 referent.
- `0x3962BD`: reference-count-to-zero slot 0 on an element in the subrecord +0x3C/+0x40 pointer range.
- `0x396327`, `0x396339`: slot +8 on R+0x24 and R+0x28 referents respectively.
- `0x39634E`: slot +8 on an element reached through R+0x14.

Direct helper boundaries `0x3952E0`/`0x395810` and imported CRT allocation/deallocation remain separate.
IAT `0x50024C` is **memmove**, not free: its presence must not be called a deallocation.
These facts identify a file/mesh-bearing resource cleanup candidate, distinct from the already freed three H
Granny objects. They do not establish every ownership relationship, original type, or full destruction effects.

The unresolved virtual calls and initializer escapes can reconnect to O/H/pose processing through effects not
visible in this limited direct inventory. Neither absent direct references to `0x38E4D0`/`0x38E3C0` nor this
candidate's direct call list proves callback absence, reentrancy freedom, or thread safety.
The cleanup still resets O+0x4C only later, as F158 states. No actual stale access or UAF is inferred.

## Reproduction and checks actually run

```text
python -I tools/hpose_resource_verify.py --exe <original-exe> --dll <original-dll>
python -O -I tools/hpose_resource_verify.py --exe <original-exe> --dll <original-dll>
python -I tools/test_hpose_resource.py
python -O -I tools/test_hpose_resource.py
python -I tools/run_checks.py
```

The new `ghidra_scripts/hpose_resource.java` derives the existing bounded exporter and adds `x:` arguments
for reference-only boundary inventory. Final common export: ignored `build/hpose-resource/FINAL3/`,
15 functions plus shared `xrefs.tsv`; all used concrete address targets are in this fresh export.
It ran only on the designated separate SH2 project with `-readOnly -noanalysis`. Earlier exports were preserved.
No decompiler, original execution or database writes were used.

Run `hpose_resource.java` on the matching Exe in a separate project copy with `-readOnly -noanalysis`,
script path `ghidra_scripts`, a fresh local output directory, and these VA arguments (including the literal x: prefix):

```text
0078E0A0 0078CF70 0078DDC0 007BB400 00795B30 00796470 007963A0 00796240
0078E3C0 0080FB8C 0080FBB0 0080FBB6 00795CC0 007BB320 006CF1D0 009F49D4
00900A60 00900A64 00900B04 00900984 00900224 0090024C 00900A78 00900564
00900568 00900A68 00900B00 x:00794350 x:007949A0 x:00794000
x:00797630 x:00795810 x:007952E0
```

`tools/hpose_resource_manifest.json` pins 15 function fingerprints (18 ranges) and the one table slot.
`tools/hpose_resource_verify.py` checks Exe/DLL SHA, PE32/x86 identity/base, six imports, strict exact manifest
fields/coverage/extents and table value; duplicate JSON keys are rejected. The table uses Exe VA/RVA conventions.
Byte fingerprints establish identity and locations, not semantics or target closure.
Original-file verifier passed both normal Python and `-O`. Ten synthetic tests passed normally and with `-O`:
success, identities/version, unknown fields, missing/duplicate/unknown function, fixed range/type checks,
digest/byte mutation, reader type/length, table mutation, duplicate JSON, unknown-binary CLI failure.
No assert-dependent gate. No game/compiler, new capture, Hub/native change, installation or push.
A fresh reviewer independently checked both file identities, all 1925 exported instructions, the 15 function
fingerprints/18 ranges, the table slot and six imports using an independent PE parser. The reviewer confirmed
the producer/list/H pointer transfer and the conditional release semantics; the initially identified post-constructor
initialization gap remains explicit as the three R escapes above. Verifier and ten tests passed in both modes.
No relevant remaining defect was found in that bounded candidate statement. Final integrated checks are recorded below.

Final integrated acceptance: `python -I tools/run_checks.py` passed all 14/14 groups, including this new suite and
documentation lint. The project lead independently repeated the original-file verifier and ten new tests in both
normal and optimized Python and checked all 1925 final exported instructions plus the constructor store/table value
with the existing independent audit PE parser. The verifier explicitly reports `dynamic_target_resolved: false`.
Native sources were unchanged, so no new C++ build/CTest or real-DLL host was run for this step. No Hub/observer
code was changed; audit recount, Hub stand-in/E2E and in-game tests were not rerun. No new GitHub CI run is claimed.

## Exactly one prioritized next proof

Follow only the escaped R from initializer call `0x395E4F` into `0x394350`, then its relevant Vptr-affecting
or escaping operations, to decide whether the constructor table survives this first unresolved post-construction
edge. If that edge cannot be closed locally, retain the exact escape instead of assigning a target to `0x38E428`.
Cache-hit writer coverage and later generation/aliasing guarantees remain separate unresolved obligations;
this next proof is not permission for a general cache/engine analysis or any skip/cache optimization.
