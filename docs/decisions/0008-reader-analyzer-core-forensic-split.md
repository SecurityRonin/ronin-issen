# 8. Crate-structure standard — reader/analyzer split (`core/` + `forensic/`)

Date: 2026-07-26
Status: Accepted

## Context

A format needs two very different things from its code: a robust reader that turns
valid data into usable structures, and an auditor that hunts anomalies. These pull in
opposite directions — a reader normalizes/skips broken data, an auditor must *see* it.
Collapsing both into one crate produces either a reader that leaks audit concerns or an
auditor contorted through a happy-path API. The fleet standardized on splitting them
(adopted 2026-06-08; reference impl: `ntfs-forensic`).

(Companion: issen's own ADR-0003 records the same split from the orchestrator's side.)

## Decision

**Standard layout for every format:**

- **One workspace repo, named `<x>-forensic`** (the analyzer is the headline; keep this
  name even though the repo also holds the core crate).
- Two members:
  - **`core/`** → crate **`<x>-core`** — the raw reader/parser, exposes `Read + Seek`
    (containers) or `NtfsFs`-style navigation (filesystems). No findings.
  - **`forensic/`** → crate **`<x>-forensic`** — the anomaly auditor: `AnomalyKind`/`Anomaly`
    + `audit()`/`audit_record()` emitting `forensicnomicon::report::Finding` via `impl
    Observation`, **depending on `<x>-core` *by default*** (path within the workspace,
    registry version for publish) — but see the principle below: this dependency is the
    default, not a requirement.
- Optional `cli/` member for a debug CLI (the end-user CLI is still `disk4n6`/Issen).

### `-forensic` is NOT required to depend on `-core` — it may need to go lower (binding design principle)

A `-core` reader is built to read *valid* data robustly, so it abstracts away exactly the
detail a forensic auditor must SEE: raw byte/section layout, slack between records,
deleted/overwritten regions, malformed fields a robust reader silently normalizes or
skips, checksums it transparently verifies-and-discards. Forensic examination "often needs
to go much lower level than the `-core` API." So a `-forensic` analyzer MAY parse the format
itself at a lower level (over the raw `Read + Seek` / container bytes), or depend on a layer
*below* `-core` (e.g. the CONTAINER byte stream, or `forensicnomicon` format constants
directly), **instead of — or in addition to — `-core`**.

Decision rule: build `-forensic` on `-core` when `-core`'s API exposes everything the audit
needs; drop to lower-level or independent parsing when it doesn't. Never contort an audit
through a happy-path reader API that hides the very anomaly it is hunting — the auditor needs
the raw, possibly-broken structure, not the reader's normalized view.

Established models in the fleet (verified 2026-06-29): **ewf-forensic** consumes only
`ewf::sections` (the low-level structural parser), explicitly *not* the reader's `Read + Seek`
data interface (its Cargo.toml says so); **ntfs-forensic** takes raw bytes directly —
`audit_record(&[u8])`, `audit_mft_mirror(&[u8], &[u8])`, `audit_logfile(&[u8])` — parsing
headers in-situ so it can see deleted/overwritten/slack records `ntfs-core`'s reader would
normalize or reject. The strongest opportunities to formalize this (where `-forensic`
currently re-parses raw structure or hacks around the reader): **ntfs-forensic** and
**vmdk-forensic** (HIGH); qcow2/vhdx (MEDIUM). This refines the "depending on `<x>-core`"
default above: prefer it, do not mandate it.

### Naming / imports

- If the bare `<x>` crate name is taken on crates.io by a third party we can co-exist with
  safely (obscure/ours), publish `<x>-core` with `[lib] name = "<x>"` so consumers write
  `use <x>::…`. If the bare name is a *popular* crate (e.g. `ntfs` = Colin Finck's), do
  **not** hijack the import — keep `<x>_core` (ntfs-core imports as `ntfs_core`).
- **If `<x>-core` itself is taken** on crates.io by an *unrelated* third party (e.g.
  `zfs-core` = the `libzfs_core` FFI bindings), the reader publishes under the **`<repo>-core`
  form — `<x>-forensic-core`** — mirroring the generic-word `browser-forensic-core` case
  (self-describing on crates.io as "the core of the `<x>-forensic` suite"). Keep the import
  path `<x>_core` via `[lib] name = "<x>_core"` so consumers are unaffected; the analyzer
  stays `<x>-forensic`. (Reference: `zfs-forensic-core` reader + `zfs-forensic` analyzer.)
- Reader = `<x>-core`, analyzer = `<x>-forensic`. Always.

### Coverage gate

Each crate keeps 100% line coverage (`cargo llvm-cov --lib`, fail on any `DA:n,0`) **except
lines annotated `// cov:unreachable`**. The analyzer's `audit_record`-style entry points are
tested end-to-end (build a valid record, drive parse→extract→audit), not just the component
helpers.

**Coverage is a backstop, not a 100%-for-its-own-sake target.** The number exists to prove
behavior is exercised and to catch regressions — never pursue it by deleting defensive code or
contriving meaningless tests. **Pure-library crates** (the reference: vmdk/vhdx/ntfs/qcow2)
gate on `--lib` at 100%. **Binary-shipping repos** (CLI/TUI/server — e.g. browser-forensic
with `br4n6`/`bw`/MCP) gate on **`--workspace`** instead, because `--lib` neither counts
integration-test coverage nor measures `main()`/render-loop bins, so it *understates* a binary
repo. For those, keep the bin glue thin via the **Humble Object** pattern (decisions in
testable libs, only an irreducible draw/read/transport shell in `main()`/the loop), ratchet
the `--workspace` threshold to the actual achieved level (no slack), and document the residual
untestable shell — do not exempt the glue silently nor drop the bar to hide it.

**`// cov:unreachable` — defence-in-depth over coverage purism (binding standard).** Panic-free
parsers keep defensive guard arms (`let Some(x) = … else { continue }`, bounds-checked `.get()`
fallbacks, length checks) that are *provably unreachable* under a dominating invariant but are
kept so the code degrades gracefully if that invariant is ever broken by a future change. Such
an arm cannot be exercised by any test. **Never delete or restructure a defensive guard solely
to satisfy the coverage gate** — that trades robustness for a number, the exact opposite of the
Paranoid Gatekeeper standard (ADR-0012). Instead append `// cov:unreachable: <the dominating
invariant>` to the uncovered line (the `continue;`/`return …;`/guard expression). The CI gate
exempts only annotated lines; every other zero-hit line still fails. Prefer restructuring to
*infallible-by-construction* (e.g. `split_at_mut` so there is no `Option` to guard) where it
loses no defence; reach for a crafted-input test before annotating (only annotate
genuinely-unreachable arms); the `code-coverage` CI job reads each `DA:n,0` line's source and
fails unless it carries the marker.

## Consequences

- Every single-format repo is `core/` + `forensic/`; readers stay clean, auditors see the raw
  structure. `vmdk`, `vhdx`, `ntfs`, and `qcow2` are all migrated to the workspace standard
  (vmdk-forensic, vhdx-forensic, ntfs-forensic, qcow2-forensic).
- The naming grammar (ADR-0009) governs the crate names when `<x>` or `<x>-core` collides on
  crates.io; the reader/analyzer split is the shape those names attach to.
- The coverage gate proves the audit path is exercised end-to-end, with defensive arms kept
  (annotated) rather than deleted for a number.
