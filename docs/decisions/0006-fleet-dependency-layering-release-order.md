# 6. Fleet dependency layering and bottom-up release order

Date: 2026-07-25
Status: Accepted

## Context

The fleet is ~80 standalone crates wired into a strict dependency DAG (the
"Multi-Repo Architecture" in [`CLAUDE.md`](../../CLAUDE.md)). Any operation that
touches many repos at once — merging a backlog of release-plz PRs, a
cargo-publish sweep, a convergence version bump, a cargo-vet wave — **must respect
that graph or it breaks in a specific, recurring way.**

A crate cannot publish (or build during publish-verify) until every fleet crate it
depends on is already on crates.io at a satisfying version. Publish a dependent
before its dependency and you get the **split-graph failure class**: `cargo publish`
fails "failed to select a version", or two versions of a mid-layer crate resolve
into the tree and trait impls stop matching (`E0277`/`E0308`). This cycle alone it
bit us three times — the forensic-vfs 0.7 convergence, the memf 0.3.1 republish, and
the browser-forensic `-storage`/`-webcache` publishes (all needed a lower layer
published first).

The ordering was **tribal knowledge** — derived by hand every time (most recently to
merge a 44-PR release backlog). It was never written down. This ADR writes it down.

## Decision

**Cross-fleet release/publish/bump operations proceed strictly bottom-up: a tier is
fully published before any crate in the tier above it is merged/published.** The
tiers collapse the dependency DAG and align to the architecture layers in
`CLAUDE.md`:

### Tier 0 — KNOWLEDGE leaves & pure codecs (zero fleet deps)
`forensicnomicon` (facade / `-core` / `-data`) · `state-history-forensic` ·
`safe-read` · `jsonguard` · `shrinkpath` · `forensic-hashdb` · `shellitem` ·
`timeglyph` · `protobuf-forensic` · codecs: `lzo` · `lzvn` · `lzfse` ·
`xpress-huffman` · `elephant-diffuser`

### Tier 1 — CONTAINER readers & crypto layers (depend on Tier 0)
Containers: `ewf` · `vmdk` · `vhdx` · `qcow2` · `aff4-forensic` · `ad1-forensic` ·
`dmg` · `dd` · `iso9660-forensic` · `udf-forensic` · `zip-forensic` · `dar-forensic` ·
`cfb-forensic` · `archive-forensic` · `livedisk-forensic` · `segb-core` ·
`memf-format`. Crypto layers: `dpapi-forensic` · `bitlocker-forensic` ·
`filevault-forensic` · `veracrypt-forensic` · `vsc-forensic`.

### Tier 2 — VFS abstraction & FILESYSTEM / PAGING (depend on Tier 1)
`forensic-vfs` · `forensic-vfs-engine` · filesystems `ext4fs-forensic` ·
`ntfs-forensic` · `hfsplus-forensic` · `fat-forensic` · `xfs-forensic` ·
`ufs-forensic` · `apfs-forensic` · `exfat` · paging `memf-hw`.

### Tier 3 — PARSER & OS-STRUCTURE (accept bytes; depend on KNOWLEDGE, sometimes containers)
`browser-forensic` · `winevt-forensic` · `srum-forensic` · `winreg-forensic` ·
`prefetch-forensic` · `lnk-forensic` · `bam-forensic` · `usb-forensic` ·
`snss-forensic` · `git-forensic` · `segb-forensic` · `sqlite-forensic` ·
`amcache-forensic` · `userassist-forensic` · `shellhist-forensic` ·
`trash-forensic` · `peripheral-forensic` · `useract-forensic` (parser +
correlation) · OS-structure `memf-windows` / `memf-linux` (may call parsers).

### Tier 4 — ORCHESTRATION / aggregators / apps (depend on everything below)
`disk-forensic` (container abstraction — aggregates every Tier-1 reader) ·
`memory-forensic` (the memf stack top) · `issen` · `4n6mount`.

**Within a tier, order by intra-tier dependency:** a repo's `<x>-core` reader before
its `<x>-forensic` analyzer; `elephant-diffuser` before `bitlocker-forensic`;
`segb-core` before `segb-forensic` before `useract-forensic`.

**How to place a crate you're unsure about:** read its `[dependencies]` for other
fleet crates (or `cargo tree`). It publishes *after* all of them. When two crates
have no dependency between them, their relative order is free.

**Caret requirements soften, they don't remove, the rule.** Because fleet deps are
caret (`^0.2`), a dependent can usually publish against an *already-published* older
version even if a newer sibling is mid-release — so a slightly-out-of-order merge
often still resolves. But a dependent whose new code requires the *bumped* version
(`^0.2.1`) will fail until that version lands. Bottom-up is the order that never
fails; treat any other order as a gamble you don't need to take.

## Operational note — crates.io publish throttle

Independent of dependency order, crates.io rate-limits **updates to existing crates**
(a burst, then ~1/min; HTTP 429 "too many updates to existing crates"). A large
sweep (this cycle: 44 PRs) *will* trip it. **Pace publish-triggering merges ~3 min
apart** for large batches. release-plz's `release` job is idempotent — a throttled
publish just needs the job re-run after the cooldown; nothing double-publishes.

## Consequences

- Publishes never fail waiting on an unpublished sibling; convergence bumps (the
  memf / engine wave pattern) propagate cleanly from the bottom up.
- The order is now derivable from this doc + `cargo tree`, not re-derived by hand.
- Companion to [ADR-0005](0005-internal-crates-never-published.md) (which crates
  publish *at all*) and the release mechanics in the `release` skill (the *how* of a
  single cut).
