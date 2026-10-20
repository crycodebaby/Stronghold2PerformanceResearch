# H-resource initializer: bounded effects and pointer identity

> Kurzfassung: Drei optionale Initialisierer bauen Lightmap-/Normalmap-/Lights-Occlusion-Dateinamen und speichern Lookup-Rueckgaben in R. Direkte Schreibbereiche und eine wirkungslose Kontextuebergabe sind belegt; globale Lookup-/Aliaswirkungen bleiben offen. Kein Live-Posevergleich oder Performancegewinn.

Date: 2026-10-17. Basis `12b8050`; follows [resource provenance/release](HPOSE_RESOURCE_RELEASE_2026-10-17.md),
[creation](HPOSE_CREATION_2026-10-17.md), [cleanup](HPOSE_CLEANUP_2026-10-17.md) and
[pose contract](POSE_CONTRACT_2026-10-16.md). All code addresses below are Exe **RVAs**; reproduction arguments
are **VAs**, Exe base `0x00400000`. R is the resource working label, not a recovered class name.
Exe SHA-256 `f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b`;
Granny SHA-256 `94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd`.

## Result and limits

The three callees assemble names for lightmaps, a normal map, and a lights/occlusion map, then store returned
references in separate R fields. These roles are supported by literal strings and observed field/dataflow;
the original engine types, lookup implementation and full ownership rules are not recovered.
The inspected bodies have no direct R+0 Vptr, R+4 reference-count, R+0xC model or R+0x10 file reads/stores.
The small reserve/allocator bridge writes only the R+0x14/+0x18/+0x1C container fields through its R-derived
context; its allocator discards the incoming R-derived ECX before using it. Thus that apparent further R escape
is closed locally. This is a bounded direct dataflow result: no direct Vptr replacement was found in these bodies.

It does **not** prove global unchangedness across calls. The shared lookup receives a global context and names,
has unexamined effects/possible pre-existing aliases, and can return pointers whose alias relationships are unknown.
Imports and runtime calls remain implementation boundaries. Consequently the dynamic target at `0x38E428`
remains unresolved; cache-hit type coverage, generation/lifetime and reentrancy guarantees remain open.
No general cache understanding is claimed or imposed as a prerequisite for every future bounded pose comparison.

## Caller identity and conditions

Initializer `0x395CC0` holds incoming R in EDI (`0x395CF8`, previously pinned). The model/file stores and earlier
producer-to-H provenance from the preceding evidence continue to apply. The three additional calls are conditional:

- `0x395E4F -> 0x394350`: when initializer stack argument +0x10 is nonzero (`0x395E33`/`0x395E3D`),
  ECX=EDI=R (`0x395E3F`); one name pointer is selected from the local alternative or primary pointer
  (`0x395E41`..`0x395E4E`). The model-derived prerequisite check at `0x395E2A` can bypass this region altogether.
- `0x395E63 -> 0x3949A0`: argument +0x14 nonzero (`0x395E54`/`0x395E58`), ECX=R at `0x395E61`,
  primary name pointer pushed at `0x395E60`.
- `0x395E7E -> 0x394000`: argument +0xC nonzero (`0x395E68`/`0x395E6C`), ECX=R at `0x395E7C`,
  alternative/primary name selection at `0x395E6E`..`0x395E7B`.

Each callee ends with RET 4 and a boolean-like AL result. The caller continues to the next condition and then
the R+0xC store at `0x395E92`; it does not branch on these AL results. This does not establish success of all
resource requests or exception safety.

## Lightmap collection: 0x394350

Incoming ECX is saved at `0x394380` in stack local EBP-0xEC; `0x39482A` reloads it into EDI=R.
The filename argument is copied/processed in temporary string objects. Literal name ingredients include
`.lightmap.` (data RVA `0x5F49C4`), `.lightmap` (`0x5F49B8`), decimal ordinal conversion through `_itoa`
(IAT `0x50031C`, call `0x394524`), and the three extension pointers at `0x5F22C0` to `dds`, `tga`, `bmp`.
The outer progression increments an ordinal at `0x394984`; the extension cursor advances at `0x394897`.
There is also a global-flag-dependent `-open`/`-closed` name fallback (`0x39463C` onward).
The exact string-helper algorithms are boundaries; this is not a replacement filename-resolution specification.

Lookup boundary `0x363FD0` is called at `0x3944C6`, `0x3945A4`, `0x394763`: ECX is global **VA `0x011521E0`**,
with a constructed name pointer plus nine scalar stack arguments (six -1 values and three zeros).
R and its field addresses are not explicit arguments at those calls. A nonnull returned candidate reaches
the append region `0x39482A`; failed candidate attempts either advance the extension/fallback search or end it.

The append region reads R+0x14 start, R+0x18 end, R+0x1C capacity. An alias-source branch checks whether the
address of the local candidate is within the existing pointer range (`0x394830`..`0x394846`); it preserves its
index across reserve. Calls `0x3948FD` and `0x39495E` pass ECX=R+0x14 and a requested element count to
`0x3D8A20`. The two append stores are through the current end pointer (`0x394915`, `0x394972`), followed by
R+0x18 += 4 (`0x394917`, `0x394974`). The latter path stores the local lookup return; the former reloads an
element by preserved index. These are pointer-container operations, not R reference-count adjustments.
The function tests the resulting end-start at `0x3948A9`..`0x3948B5` and returns AL indicating nonempty storage
at `0x3948CD`/RET `0x3948EE`; it does not clear pre-existing entries first. Excessive element counts reach the
`std::_Xlength_error` import at `0x394994` (IAT `0x5000F0`), outside the normal-return result.

### Small identity bridge, not recursive engine reconstruction

`0x3D8A20` (51 instructions) saves incoming R+0x14 as ESI at `0x3D8A27`. If existing capacity suffices,
branch `0x3D8A45` returns without reallocating. Otherwise `0x3D8A4D -> 0x25EF50` receives a count on stack
and ECX=ESI+0xC=R+0x20 (`0x3D8A4A`). `0x25EF50` is only 28 instructions: its first ECX operation
`0x25EF53` overwrites ECX with the stack count. It never reads, stores or publishes the incoming interior pointer.
Count zero returns null; count <= `0x3FFFFFFF` requests 4*count bytes at `0x25EF67`/`0x25EF6F -> 0x40FBB6`.
Oversized count or null allocation reaches local exception construction/throw boundaries (`0x25EF89`,
`0x25EF9F`); no CRT internals were descended into.

On the reserve normal path, `0x3D8A65` uses imported memmove (IAT `0x50024C`) to transfer existing pointer
bytes, `0x3D8A7D -> 0x40FB8C` deletes the old nonnull pointer buffer, and `0x3D8A8F`/`0x3D8A94`/`0x3D8A91`
publish new start/end/capacity to R+0x14/+0x18/+0x1C. Deleting the buffer is not releasing each pointed resource.
Its count overflow branch calls length_error at `0x3D8A35`. Allocation success, valid ordered ranges, absence of
unexpected aliases and normal callee return are conditions of this local container reading, not global invariants.

## Normal-map request: 0x3949A0

Incoming R is saved at `0x3949CF` in EBP-0x6C and restored to ECX at `0x394A9D`.
It constructs names using `.normalmap.` (data RVA `0x5F22CC`) and the same dds/tga/bmp extension table.
Call `0x394A98 -> 0x363FD0` has the same global ECX/name-plus-nine-scalars argument form.
`0x394AA0` stores the returned pointer directly in R+0x28, including null on an unsuccessful attempt.
It searches up to the three extensions (`0x394ADE`..`0x394AE4`), exits true on a nonnull result, and returns
false after exhausting them (`0x394AFB`); true is assigned at `0x394B2C`, RET 4 at `0x394B18`.
There is no direct load/release of the old R+0x28 value, reference-count exchange or publication of R itself
in this body. Ownership effects inside the lookup remain unproved.

## Lights/occlusion-map request: 0x394000

Incoming R is saved at `0x394035` in EBP-0x88. Reloads `0x39415E`/`0x394290` restore ECX=R before stores
`0x394164`/`0x394296` to R+0x24 from the returns of `0x394159`/`0x39428B -> 0x363FD0`.
Names use `.lightsandocclusionmap.` (data RVA `0x5F49A0`), the same extension table, and a conditional
`-open`/`-closed` fallback governed by the byte at **VA `0x021ED068`** (`0x39419B`) and failed first lookup.
Calls have the same global ECX/name-plus-nine-scalars argument form; R is not an explicit lookup argument.
The R+0x24 nonnull tests at `0x3941AD`/`0x3942E3` lead to the true exit `0x394331`/`0x394342`;
failed extensions advance until cursor 0xC (`0x3942E8`..`0x3942FA`) then return false at `0x394311`.
RET 4 is `0x39432E`. No direct old-pointer release, R count adjustment, R+0/+4/+0xC/+0x10 access or R
publication was found. A failed attempt can overwrite R+0x24 with null; ownership correctness is not inferred.

## Other bounded call effects and evidence gates

Filename/temporary-object helpers remain exact direct boundaries: `0x006D20`, `0x0072F0`, `0x0074E0`,
`0x05A7E0`, `0x273E90`, `0x33A040`, `0x33ABA0`, `0x33ABF0`, `0x3938A0`, `0x393D50`.
Their explicit contexts/arguments in the three bodies are local string objects, their derived contents, constants
or helper returns, rather than the saved incoming R. No semantics is inferred from automatic call names.
`0x40FBA0` is retained as a runtime boundary; temporary heap-string deletes go through previously pinned
`0x40FB8C`. Unwinding/callback/thread behaviour and arbitrary global effects are not established by this inventory.

The existing resource verifier/manifest were extended rather than duplicated. Version 2 pins the original 15
functions plus the three initializer callees and two small identity bridges: 20 functions/24 ranges, nine imports,
one constructor table slot and 16 explicit call/context/store/name bindings. All 2907 final exported instructions
were compared against the original Exe file through the existing identity-checked PE reader. Fingerprints pin
locations/bytes, not semantic correctness. The verifier still reports `dynamic_target_resolved: false`.
Fifteen synthetic tests passed normally and with `-O`, including new missing-body coverage, binding
coverage/duplicate/name/extent/type/digest/byte-mutation and reader rejection tests. Original-file CLI passed
normally and with `-O`. No full integrated run was performed before freeze; parent integration owns that check.

## Reproduction

```text
python -I tools/hpose_resource_verify.py --exe <original-exe> --dll <original-dll>
python -O -I tools/hpose_resource_verify.py --exe <original-exe> --dll <original-dll>
python -I tools/test_hpose_resource.py
python -O -I tools/test_hpose_resource.py
```

Only the designated separate SH2 copy was opened, using `-readOnly -noanalysis`; no decompiler or original
code execution. Final common export is ignored `build/hpose-initializer/FINAL2/`, 20 function files,
2907 instructions and `xrefs.tsv` with 15811 references (730396 bytes including identity header).
The initial common FINAL attempt exceeded the exporter's 10000-reference ceiling at a common string helper;
it is incomplete and not evidence. The only Java change raises that bounded ceiling to 100000 so all required
targets fit in one final export; the 64-target/32-function/50000-instruction limits remain. FINAL2 compiled/ran
that final source version. Earlier exports remain unchanged. Complete 62 VA arguments (literal `x:` means
reference-only boundary inventory, no function-body semantics):

```text
0078E0A0 0078CF70 0078DDC0 007BB400 00795B30 00796470 007963A0 00796240
0078E3C0 0080FB8C 0080FBB0 0080FBB6 00795CC0 007BB320 006CF1D0 009F49D4
00900A60 00900A64 00900B04 00900984 00900224 0090024C 00900A78 00900564
00900568 00900A68 00900B00 x:00797630 x:00795810 x:007952E0 00794350
007949A0 00794000 007D8A20 0065EF50 x:00406D20 x:004072F0 x:004074E0
x:0045A7E0 x:00673E90 x:0073A040 x:0073ABA0 x:0073ABF0 x:00763FD0
x:007938A0 x:00793D50 x:0080FBA0 x:0080FBBC x:009000F0 x:00900218
x:0090031C x:009F22BC x:009F22C0 x:009F22CC x:009F22D8 x:009F22DC
x:009F22E0 x:009F4990 x:009F4998 x:009F49A0 x:009F49B8 x:009F49C4
```

No game run, observer/hook/cache/recording/installation/native-code change, original DB write or push.
The result supports local Vptr persistence only within the inspected direct operations; shared lookup/global
alias effects and successful-resource generations prevent elevating it to the dynamic release target proof.

## Independent review and next decision

A fresh reviewer confirmed all 2907 final instruction bytes, 20 function fingerprints/24 ranges and 16 bindings
using an independent PE reader, then repeated the 15 tests and original-file CLI normally and under -O.
The review corrected four VA/RVA labels for generic helper boundaries before acceptance; the published VA export
arguments were already correct. No remaining blocking defect was found in the bounded statement.
The project lead independently checked the final export, fingerprints/bindings and allocator prologue again.

Final integrated acceptance: all 14/14 ordinary check groups pass, including the extended 15-test resource suite
and documentation lint. The project lead repeated the targeted tests and original-file verifier normally and
with -O; the verifier reports 20 functions, nine imports, one table slot, 16 bindings and unresolved dynamic target.
Native code was unchanged: no new C++ build/CTest or real-DLL host run. Hub/observer code and raw data were
unchanged, so no audit recount, Hub E2E or game run was performed. No new GitHub CI run is claimed.

The next proof is selected in [pose-comparison readiness](../design/POSE_COMPARISON_READINESS_2026-10-17.md):
establish the valid initialized output extent at the known sample boundary. Do not automatically recurse into
the shared filename lookup or require complete cache/type reconstruction. Existing lifetime, generation and
concurrent/reentrant-read obligations remain; no observer implementation or new recording is authorized here.
