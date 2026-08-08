# 0019 — FOUNDATION holds knowledge; algorithms live in primitive crates

**Status:** Accepted (implementation pending — `safe-decode` and `timeglyph-core` are not yet built)

## Context

[ADR-0016](0016-multi-repo-layer-architecture.md) defines FOUNDATION as *"zero-dep artifact
specs / format constants / contract traits"* — specs, constants, traits. Not algorithms. Its
amendment names two bands: PRIMITIVES (`safe-read`, `jsonguard`) below KNOWLEDGE + CONTRACTS
(`forensicnomicon`, `state-history-forensic`, `forensic-hashdb`).

In practice `forensicnomicon` drifted across that line. `crates/core/src/catalog/decode.rs`
holds a ROT13 implementation, a FILETIME→ISO-8601 converter with hand-rolled civil-date
arithmetic, UTF-16 and `MultiSz`/`MruListEx` decoding, and five bounds-checked integer readers
that reimplement `safe-read`'s published API verbatim — same `(data, offset)` signature, same
"0 when out of range" contract, same doc wording.

**The crate's own `Decoder` enum shows the intended design, and shows where it broke:**

```rust
pub enum Decoder {
    Rot13Name,                    // the FACT: this artifact's name is ROT13-encoded
    Utf16Le,                      // the FACT: these bytes are UTF-16LE
    FiletimeAt { offset: usize }, // the FACT: a FILETIME lives at this offset
    MultiSz, MruListEx,           // facts about encoding
    EseDatabase,                  // the FACT: this is ESE/JET Blue
}
```

Every variant is knowledge. **`Decoder::EseDatabase` is the existence proof of the correct
pattern** — forensicnomicon does not implement ESE; it names the format and delegates to a crate
that does. Only the *heavy* decoders received that treatment. `rot13`, FILETIME, UTF-16,
`MultiSz` and `MruListEx` were inlined because each looked individually too trivial to warrant a
home.

That accretion has a measured cost. The inlined integer readers accumulated **seven** wrapping
`offset + N > len` guards (see the fleet DRY audit, §1.3) — precisely the defect class
`safe-read` exists to prevent — and the FILETIME path carries hand-rolled civil-date math that
reimplements what `jiff` already does correctly.

The forcing function for that last one is a type: **`ArtifactValue::Timestamp(String)`.** The
universal output contract demands a *rendered* timestamp, so the crate must format; it cannot
depend on `jiff` or `timeglyph` (see the cycle below), so it hand-rolls the calendar. Relocating
the function without changing the contract would let the problem grow back.

Two constraints bound the solution:

- **`timeglyph` cannot be a FOUNDATION dependency.** `timeglyph/Cargo.toml:77` declares
  `forensicnomicon = { version = "1.3", default-features = false }` — timeglyph depends on
  forensicnomicon, so the reverse edge is a cycle. It also pins `rust-version = "1.96.0"`, which
  has already raised a published PARSER crate's MSRV floor (`protobuf-forensic` records this in
  its own manifest comment), and caps `jiff = ">=0.2, <0.2.33"` because jiff 0.2.33 panics on
  out-of-range input instead of returning `Err`.
- **`safe-read` cannot absorb the string decoders.** It is `no_std` with zero dependencies and no
  features; `rot13` and UTF-16 decoding require `alloc`.

## Decision

### 1. FOUNDATION knowledge crates describe; primitive crates implement

A KNOWLEDGE + CONTRACTS crate owns **facts, taxonomies, offsets, field schemas and contract
traits**. It names an encoding; it does not implement one. Implementations live in PRIMITIVES
crates below it, per the intra-FOUNDATION ordering in ADR-0016.

The test: *if this code would still be correct with no forensic domain knowledge at all, it is an
algorithm and belongs in a primitive.* `fn rot13` passes (it is a character rotation).
`Decoder::Rot13Name` fails (it encodes that UserAssist obfuscates its name field) and stays.

### 2. Two new PRIMITIVES crates

| Crate | Contract | Holds |
|---|---|---|
| `safe-read` *(exists, 0.2.1)* | `no_std`, **no alloc**, zero deps, MSRV 1.75 | Bounded integer reads over untrusted bytes |
| **`safe-decode`** *(new)* | **alloc**, zero deps, MSRV 1.75, panic-free | Byte→value transforms with no domain knowledge |
| **`timeglyph-core`** *(new)* | zero deps, MSRV 1.75, panic-free | Epoch/temporal integer conversion + sentinel policy |

The **alloc boundary** separates the first two and is not arbitrary: it is exactly why UTF-16
decoding could not be added to `safe-read`.

**`safe-decode` membership test — all four required:** panic-free · allocating · format-agnostic ·
no domain knowledge.

**Refinement, from applying it in practice.** "Can this be described without naming Windows?" is a
useless question — almost anything can be. The decidable form is:

> **Would this still be correct for a format I have never seen that shares the structure?**

That is the No-Special-Cases discipline applied to crate membership. Splitting a UTF-16 buffer on
NUL code units: yes, any format with that structure. Stopping at a *double* NUL and discarding the
tail: only for formats that happen to agree with the Windows registry. `0xFFFFFFFF` as a list
terminator: no — that is one vendor's convention wearing a structural costume.

**Worked example — `MultiSz` splits along that line; `MruListEx` fails it outright.**

- `split_utf16le_on_nul` / `split_utf16be_on_nul` are **in**: total and structural, `n` NULs yield
  `n + 1` segments, empty ones included. They describe the bytes and assert nothing about them.
- The `REG_MULTI_SZ` *convention* is **out** — that a double NUL terminates, that trailing empties
  are padding rather than data. Those are registry facts, and the caller composes them in one line
  in the crate where the fact already lives.
- `MruListEx` is **out entirely**. Generalizing to `read_u32le_list_until(bytes, sentinel)` would
  produce a function whose whole content is three iterator combinators over `safe_read::le_u32` —
  no bounds risk to centralize, no divergent behaviour to converge, no defect class prevented. It
  fails the domain-knowledge condition on the sentinel *and* the worth-a-shared-home bar on
  triviality.

The deciding consideration is §3's own warning: admitting a named constant from one vendor's
format would make "no domain knowledge" **negotiable**, and a primitive crate whose membership
test is negotiable becomes precisely the junk drawer one layer down that this ADR exists to
prevent. Excluding it is what keeps the test decidable.

**Close the matrix, do not ship only the used cells.** `safe-decode` provides all 8 endianness ×
NUL-policy combinations rather than the 5 with a current consumer. Endianness affects only the
byte-pair → code-unit step and is orthogonal to NUL policy; **a hole in a primitive gets filled by
hand at the call site, which is how fourteen UTF-16 decoders came to exist in the first place.**

- **Passes:** `rot13`; the UTF-16 family (all four NUL policies × both endiannesses, each
  *explicitly named* rather than collapsed behind a policy flag — see the audit §2.3); hex
  formatting; the structural half of `MultiSz` (NUL splitting).
- **Fails:** FILETIME conversion (temporal — `timeglyph-core`); ESE (has its own crate);
  `MruListEx` and the `REG_MULTI_SZ` terminator convention (registry facts); anything needing a
  format catalog.

**Lossiness is part of the return type, not a lost detail.** UTF-16 decoding returns a struct
carrying `unpaired_surrogates: usize` and `dangling_byte: bool`, not a bare `String`. This
follows the fleet rule that return types carry security-relevant state — and it *splits*
`leveldb-forensic`'s single `lossy: bool`, because that bool conflates two different forensic
findings: a mangled surrogate is a text-encoding defect, while an odd input length is a
structural anomaly in the record. A count rather than a flag lets a report say *how much* was
lost. `#[non_exhaustive]` means a consumer cannot fabricate a non-lossy result via a struct
literal.

**`timeglyph-core` exists because `timeglyph` is both a library primitive and a heavy tool** —
CLI, MCP server, lens GUI, wasm and Python bindings. [ADR-0013](0013-batteries-included.md)
already prescribes the mechanism: *"the lean `<x>-core` library + full `<x>` binary split is the
mechanism when a dep is both a library primitive and a heavy tool."* The seam is **integer
arithmetic below, calendar and rendering above**: `(ft - EPOCH_OFFSET) * 100` needs nothing;
ISO-8601 formatting needs `jiff`.

This keeps **one home for time**. Splitting temporal logic between `forensicnomicon::temporal`
and `timeglyph` was considered and rejected — it creates the split-brain this fleet's DRY
standards exist to prevent.

### 3. Naming: no membership-test-free names

Crate names must satisfy [ADR-0009](0009-crate-naming-grammar.md) — *name by what the crate owns,
not the mechanism*. **`misc`, `util`, `common`, `helpers` and equivalents are banned as crate
names**, because a crate whose name states no inclusion criterion admits everything and becomes a
second junk drawer one layer down. `safe-decode` inherits the established `safe-*` prefix and its
panic-free posture, and its membership test is decidable.

### 4. `ArtifactValue::Timestamp` carries an integer, not a String

`ArtifactValue::Timestamp(String)` is what drags rendering into FOUNDATION. It becomes an integer
(Unix nanoseconds), produced via `timeglyph-core`; **rendering moves to consumers**, which may
depend on `timeglyph` freely.

This also serves the fleet's human-versus-machine output rule: a rendered string in the *model*
type forces forensicnomicon's formatting choice on every consumer, and the DRY audit already
records six divergent FILETIME renderings across the fleet. A timestamp in the model should be an
instant; formatting is a projection-layer concern.

This is a **semver-breaking change** to `forensicnomicon`. It is release-plz's job to compute the
bump; never hand-edit the version.

## Consequences

- `forensicnomicon` returns to being knowledge: the `Decoder` taxonomy, catalog descriptors,
  offsets, field schemas, and `decode_artifact` dispatch over three primitive crates. `decode.rs`
  sheds `rot13`, `filetime_to_iso8601`, UTF-16, `MultiSz`/`MruListEx`, and the five integer
  readers.
- **The hand-rolled civil-date math is deleted, not relocated** — once `ArtifactValue::Timestamp`
  carries an instant, nothing in FOUNDATION needs a calendar.
- ADR-0012's *"every integer read goes through `safe-read`"* applies to FOUNDATION itself. The
  crate that anchors the standard stops being its own exception.
- `rot13` converges from 4+ independent implementations (`forensicnomicon`,
  `memf-windows/userassist.rs`, `userassist-forensic`, `winreg-artifacts/userassist.rs`) onto
  one, reachable by all of them since every layer depends on FOUNDATION.
- **Sequencing.** `safe-decode` and `timeglyph-core` must be published before the migrations can
  land; `safe-read` also needs signed readers and `try_bytes::<N>` (audit §2.1) before
  `decode.rs`'s `read_i32_le`/`read_i64_le` can move. Interim local fixes — such as the private
  `fits` predicate closing the seven wrapping guards — are correct to land first and are
  superseded later, not blocked on this ADR.
- Publish order is unaffected: [ADR-0006](0006-fleet-dependency-layering-release-order.md)
  already places primitives in the first wave. Both new crates join it.
- **Risk this ADR accepts:** three primitive crates instead of one is more surface to maintain.
  The mitigation is that each has a written, decidable membership test; the failure mode being
  avoided — a `misc` crate — has none, and was judged the worse trade.
