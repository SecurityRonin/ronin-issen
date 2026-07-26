# 12. Security & robustness standard — Paranoid Gatekeeper

Date: 2026-07-26
Status: Accepted

## Context

Every `*-core` / `*-forensic` crate parses **untrusted, attacker-controllable disk images**.
A panic, an out-of-bounds read, or a trusted-length-field overflow in a forensic parser is not
a mere bug — it is a crash or a memory-safety hole reachable from evidence a subject controls.
These crates therefore hold a bar *above* the global panic-free / pre-publish discipline: the
forensic superset below.

## Decision

These crates *never panic, never read out of bounds, never trust a length field.* They meet the
global **panic-free lint recipe, pre-publish gate, and CI shape** (`~/.claude/CLAUDE.core.md` →
*Rust Lint Posture* + *Pre-Push & Pre-Publish Discipline*); the **forensic superset adds**:

- **`unsafe` mmap exception:** a reader that legitimately needs one bounded `unsafe` (e.g.
  `memmap2::Mmap::map`) downgrades the base `unsafe_code = "forbid"` to `"deny"` + a justified
  per-site `#[allow(unsafe_code)]` (`forbid` can't be locally overridden). ewf-forensic does
  this for its 4 mmap sites; every other `unsafe` stays a hard error.
- **Bounds-checked readers on the image — route through the `safe-read` crate; NEVER hand-roll a
  per-crate `bytes.rs`.** Every integer field read goes through the published **`safe-read`**
  crate (`no_std`, `forbid(unsafe)`, fuzzed): `le/be_u16/u32/u64` + `u8` return `0` out of range
  (never panic), and the `try_*` twins return `None` when `0` must be distinguished from
  absent/truncated. This is the fleet's single audited implementation — **do not re-derive
  `read_uNN_le`/`bytes.rs` in each crate** (the recurring DRY+robustness failure: hand-rolled
  copies drift and some `data.get(off..off+4)` variants can overflow `usize`, which `safe-read`'s
  `checked_add` cannot). `forensic-vfs` re-exports `safe-read`, so umbrella crates get it
  transitively (**forensic-vfs ADR-0005** is the decision record). `safe-read` handles
  *fixed-width integer fields only*; range-checking every length/offset/count *from the image*
  before use and capping allocations against alloc bombs remain the reader's job.
- **Fuzzing — one target per parsed structure** (ntfs is the model: `boot`, `record`,
  `attributes`, `attribute_list`, `runlist`, `index_buffer`, `compress`, …) **plus** a
  `fuzz_forensic` target driving the full inspect/audit pipeline; `fuzz.yml` builds + smoke-runs
  every target.
- **Real-artifact CI validation:** beyond the global gates, validate `inspect()` / `audit()`
  against **real artifacts** (e.g. qcow2 vs qemu-img images with backing-file/snapshot/encryption
  + a CirrOS corpus), not only synthetic fixtures; **100% line coverage** (`cargo llvm-cov
  --lib`, `// cov:unreachable` per the coverage-gate standard in ADR-0008).

## Consequences

- A crafted evidence image cannot panic or corrupt memory in a fleet parser by construction
  (lints) and is tested for it empirically (fuzzing) against real artifacts.
- `safe-read` is the single audited integer-read implementation; a hand-rolled `bytes.rs` in a
  new crate is a reviewable regression, not an option.

### Compliance snapshot (2026-06-08)

qcow2, vmdk, vhdx, ewf, ntfs-forensic all enforce the `unwrap_used`/`expect_used = deny` panic
lints with panic-free bounds-checked readers, and all have `fuzz.yml`. Panic-free remediation
counts: vhdx 80 reads, ewf 47, ntfs 44+2, qcow2 clean by construction. Residual debt to clear in
a *separate* pass (not security — pre-existing pedantic/fmt style): vhdx ~30 pedantic warnings,
ewf broad stylistic allow-list + fmt diffs. The safety lints are hard denies everywhere.
