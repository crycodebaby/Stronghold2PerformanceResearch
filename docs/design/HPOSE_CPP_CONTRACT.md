# H-pose: requirements for own native code

> Kurzfassung: Konkrete C++-Abnahmeregeln fuer den begrenzten H-Pose-Pfad. Keine Freigabe fuer Live-Zugriffe, Cache/Skip oder einen Engine-Ersatz.

Scope: own synthetic hosts and future bounded observation of the verified Win32 build. These are engineering
requirements, not claims about the original source code. Current binary evidence and unresolved edges belong in the
[H-pose creation evidence](../evidence/HPOSE_CREATION_2026-10-17.md) and the current STATE/HANDOFF.

## Implemented preparation: checked address arithmetic

`tools/hpose_contract/record_range.h` is a small independent C++17 reference model for the direct in-range selection:
ordered begin/end address IDs, byte difference at most `INT32_MAX`, a whole number of 20-byte records, and an unsigned
index below the count. It performs no allocations, I/O, original calls or memory reads. It returns a status, count and
selected numeric address. Even an accepted address of zero proves no pointer validity.

`python -I tools/hpose_native.py` builds/runs it in a separate MSVC Win32 Release host: 6,393 explicit checks pass,
including literal boundary cases and exhaustive small valid ranges. Logs/source/host hashes are in ignored
`build/hpose-native/`. The signed extent restriction follows the original count-arithmetic domain; invalid inputs are
our rejected cases. The game's geometric fallback for an excluded index is deliberately outside this model. These
are own-contract tests, not differential execution of the game or evidence of speedup. No sanitizer run is claimed.

The [allocation follow-up](../evidence/HPOSE_ALLOCATION_2026-10-17.md) adds `allocation_request.h`: no allocation
for zero, exact 20*n requested bytes for 1..0x0CCCCCCC, own status rejection above that limit. Ten literal witnesses
cover both sides of the signed selection limit and the unsigned allocation limit. This is not a Grow-policy,
CRT-exception or heap implementation; numerical request validity does not imply a possible/live allocation.

Follow-up: the [native acceptance contract](../evidence/HPOSE_NATIVE_ACCEPTANCE_2026-10-17.md) now validates a
versioned JSON host report before atomically persisting success. The independent runner uses CMake on PATH or
`--cmake`; no Hub or Granny helper is needed. Game-free failure tests run in the ordinary Python suite. A mandatory
Win32 build/run step is prepared in the workflow; no new GitHub run has been claimed.

## Representation and ownership

- Separate file RVA, target-process address, H-record index, bone count and byte extent. A `uint32_t` captured address
  is an identifier, not an invitation to cast it to a native pointer or dereference an old recording.
- The verified H stride is 20 bytes; the observed instance/world/local fields are at +0/+4/+8. Any native projection
  needs compile-time size/offset assertions, explicit 32-bit fields and a documented input byte extent. Unknown fields
  retain neutral names. A decoded copy is not an owning representation of the game's object.
  In particular, matrix-array alignment and H-record alignment are different: adding `alignas(16)` must not silently
  turn the verified 20-byte descriptor stride into a padded 32-byte native layout.
- RAII owns only memory/resources acquired by our own component under a proven matching release contract. Game
  objects and library-returned borrowed arrays must not acquire automatic deleters merely because their address is known.
- Target-process layout and own host layout are separate contracts. Do not rely on compiler packing, host pointer
  width, C++ object lifetime or alignment when decoding copied bytes. Decode checked bytes or use `memcpy` into a
  suitable trivially copyable scalar; do not type-pun an arbitrary buffer into an invented engine class.

## Bounds and state

- Record count, container capacity, allocated pose capacity, requested sample count and initialized output extent are
  distinct quantities. Evidence for one never silently authorizes another.
- Check subtraction/order, record-size divisibility, index bounds, multiplication/addition overflow and available
  bytes before access. Validate in a wider integer domain before narrowing to Win32 sizes. Own guarded code may reject
  an invalid input that original machine arithmetic would wrap; label that as a safety restriction, not equivalence.
- An address alone is not a generation. Cross-call comparisons need observed lifetime/reuse boundaries and explicit
  gaps. Equal matrices would still not establish equal hidden state or permission to skip the original call.
- The [sample writer proof](../evidence/POSE_SAMPLE_EXTENT_2026-10-17.md) covers conditional full 64-byte matrix
  stores in two direct writers. A future reader must establish the actual selected path, initialized sources and
  destination capacity; normal Sample return alone is insufficient. Keep World and Composite extents separate
  from allocation size. Do not turn an unresolved path or a no-write local callback into a valid empty observation.
- The [special callback](../evidence/POSE_SPECIAL_CALLBACK_2026-10-17.md) has an optional first-matrix fast route
  before its loop guard. A zero loop count alone cannot authorize an empty whole-call observation. Known helper
  writes cover a conditional prefix bounded additionally by the binding count; do not substitute HeaderN for it.
- The [first-bone follow-up](../evidence/POSE_FIRST_BONE_FAST_2026-10-18.md) separates complete destination byte
  coverage from valid transform-value provenance. A future raw-byte comparator must preserve this distinction,
  handle matrix0 equality as a matrix0-only result and prove live capacity/generation/read interval independently.
  A/C source uncertainty cannot be converted into replacement correctness or an engine-defect claim.
- The [bounded cleanup path](../evidence/HPOSE_CLEANUP_2026-10-17.md) clears O+0x4C only after its pose-release
  calls and further helpers. A nonzero selected-H field is therefore insufficient evidence of live referents.
  For a future observer, invalidate an observed generation at the relevant release boundary, before forwarding the
  original release; do not wait for this later null store. This is an engineering requirement, not an implemented hook
  or a proof that all release paths, reentrant calls and threads have been covered. Missing lifecycle events must
  make a comparison unknown. No own deleter or ownership transfer follows from this static sequence.
- Invalid/unknown inputs yield an explicit result and preserve output state; do not turn them into zero-sized valid
  observations. In a later observer, retain the original call and account for skipped observation separately.

## Native acceptance

- Keep the existing MSVC Win32 C++17 contract. New independent targets use `/W4 /WX`, checked size/offset invariants
  and explicit failures in Release. Do not use a compiled-out `assert` as an external-input gate.
- Keep deterministic synthetic inputs, boundary cases and rejection tests. Include zero/one/multiple records, truncated
  or misaligned extents, end/index boundaries and the largest representable safe byte count without huge allocations.
- Test the own contract independently of byte fingerprints. A synthetic model demonstrates our specified behavior;
  it does not execute or establish the original game's allocator, error handling or complete object lifetime.
- Use sanitizer/guard-page checks where the local toolchain supports them, and report what actually ran. A clean
  synthetic sanitizer run says nothing about unobserved pointers in the game.
- Keep `/fp:strict` for any pose-math reference work; this alone does not recreate original x87 rounding. A faster
  floating-point variant needs separately declared comparison criteria and side-effect analysis.

## What can be prepared for performance work

Bounded, allocation-free arithmetic and parsing on our own already-owned buffers can be implemented now once their
contract is explicit. A later observer may use preallocated fixed-size storage and move formatting/I/O away from the
observed thread; its exact memory budget, failure/drop semantics and overhead controls must precede installation.
These are preparations for low observation overhead, not measured game speedups.

Before a change to game computation, specify one workload, a correctness oracle, applicable state/lifetime boundaries,
an unchanged reference path and matching repeated controls. Cache keys, SIMD math, allocator replacement, pooling and
parallel pose work remain candidates only: current evidence does not establish their invalidation, numerical or
threading contracts. Preserve a simple reference implementation to compare any future candidate against.

## Primary references

- [C++ Core Guidelines: resource management and ownership](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#S-resource)
- [MSVC floating-point behavior](https://learn.microsoft.com/en-us/cpp/build/reference/fp-specify-floating-point-behavior?view=msvc-170)
- [MSVC AddressSanitizer](https://learn.microsoft.com/en-us/cpp/sanitizers/asan?view=msvc-170)
