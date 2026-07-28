# 0017 — Fleet folder umbrella + component taxonomy (executed)

Date: 2026-07-28 · Status: accepted (executed)

## Context

The fleet's ~86 repos needed an on-disk expression of the architecture. A
2026-06-29 proposal to merge everything into a history-merged **monorepo** was
overruled (2026-07-04) in favour of a **folder umbrella**: one governance repo
whose tree groups the fleet by category, while every component stays its own
independent git repo. The migration plan and runbook lived in `REORG.md` +
`fleet-reorg.sh` + `.migration/`; this ADR is the durable record now that the
reorg has shipped and those plan artifacts are archived to git history.

## Decision

- **Form: nested separate repos, NOT a monorepo.** Each component keeps its own
  `.git`, remote, CI, release-plz, tags, and crates.io identity — only its folder
  moves. GitHub sees remotes (URLs), not paths, so folder moves need no pushes.
  This preserves the per-repo release standard and keeps the move reversible.
- **Layout:** `~/src/ronin-issen/components/<category>/<repo>`, a plain folder (no
  `.git`, no `Cargo.toml`); `components/*` and `_deprecated/*` are gitignored by
  the umbrella. `_deprecated/` sits at the umbrella root, a sibling of
  `components/`.
- **Why not a monorepo:** the monorepo's real motivation was the fn-1.0 publish
  pain (~70 manual publishes, topological ordering, stale-caret traps,
  local-ahead strands). That is answered instead by **release-plz on every repo**
  (the binding fleet release standard), which delivers coordinated, reviewed
  releases without a history merge.
- **Categories group by the proximity rule:** same conceptual idea → same folder;
  contract crates live with their families (e.g. `forensic-vfs` with its engine +
  mount in `filesystem/`); sub-groups get a label in the table, not a folder. The
  **folders govern where a human looks**; the conceptual dependency **tiers**
  (FOUNDATION → CONTAINER → … → ORCHESTRATION, ADR-0016) govern dependency
  direction and release order (ADR-0006). Related, deliberately not identical.
- **Reserved-not-created categories** (no empty dirs): `os-structure`
  (memf-windows/-linux live inside `memory-forensic`) and `query`
  (issen-remote-access/velociraptor-parser live inside `issen`) — created the day
  a standalone repo of that layer exists.

### Taxonomy rulings (2026-07-28)

`compression/` → **`codec/`**; the `vfs/` folder is dissolved
(`forensic-vfs`/`-engine`/`-mount`/`4n6mount` → `filesystem/`, `disk-forensic` →
`orchestration/`); `ad1-forensic` is `container/` (a raw-disk logical container),
not `archive/`.

## The taxonomy (86 repos · 16 folders)

The component tree is the registry; this table is its canonical statement.

| Category | Role | Repos |
|---|---|---|
| `knowledge/` (2) | FOUNDATION leaf — compile-time format facts, hash DBs; zero fleet deps | forensic-hashdb · forensicnomicon |
| `utility/` (7) | cross-cutting mechanisms — owns no format, serves many layers | blazehash · forensic-carve · jsonguard · name-variants · safe-read · shrinkpath · timeglyph |
| `codec/` (3) | pure-Rust decompressors | lzo · lzvn · xpress-huffman |
| `container/` (8) | decode an image/dump → addressable byte stream | ad1-forensic · aff4-forensic · dmg-forensic · ewf-forensic · qcow2-forensic · vhd-forensic · vhdx-forensic · vmdk-forensic |
| `acquisition/` (1) | live-host disk enumeration + acquisition-integrity grading | livedisk-forensic |
| `archive/` (3) | file containers (not raw disks) | archive-forensic · dar-forensic · zip-forensic |
| `partition/` (3) | partition schemes | apm-partition-forensic · gpt-partition-forensic · mbr-partition-forensic |
| `encryption/` (6) | crypto layers + bespoke primitives | bitlocker-forensic · dpapi-forensic · elephant-diffuser · filevault-forensic · luks-forensic · veracrypt-forensic |
| `filesystem/` (16) | navigate sectors by path (name→inode→block); vfs stack + FUSE mount | 4n6mount · apfs-forensic · btrfs-forensic · ext4fs-forensic · fat-forensic · forensic-vfs · forensic-vfs-engine · forensic-vfs-mount · hfsplus-forensic · iso9660-forensic · ntfs-forensic · refs-forensic · udf-forensic · ufs-forensic · xfs-forensic · zfs-forensic |
| `memory/` (1) | memory dump → page stream; OS-structure walking | memory-forensic |
| `log/` (2) | navigate a log stream by timestamp / record number | journald-forensic · winevt-forensic |
| `parser/` (25) | interpret artifact records → forensic meaning (medium-agnostic) | amcache-forensic · atx-forensic · bam-forensic · blob-decoder · bluetooth-forensic · browser-forensic · cfb-forensic · ese-forensic · exec-pe-forensic · leveldb-forensic · lnk-forensic · peripheral-forensic · prefetch-forensic · protobuf-forensic · segb-forensic · shellhist-forensic · shellitem · shimcache-forensic · snss-forensic · sqlite-forensic · srum-forensic · trash-forensic · usb-forensic · userassist-forensic · winreg-forensic |
| `graph/` (1) | content-addressed / Merkle-DAG navigation | git-forensic |
| `history/` (3) | [H] state-history temporal cohorts | snapshot-forensic · state-history-forensic · vsc-forensic |
| `orchestration/` (3) | cross-artifact correlation → one unified timeline | disk-forensic · issen · useract-forensic |
| `_deprecated/` (2) | superseded; kept for reference | ewf · usnjrnl-forensic |

## Consequences

- The umbrella `README.md` carries this table as the canonical layout; the visual
  is `docs/components-diagram.html`. The **current state is the design** — there is
  no separate plan doc.
- `REORG.md`, `fleet-reorg.sh`, `.migration/`, and `docs/components-reorg.md` are
  removed from the working tree; `git log --follow` is their archive.
- New repos are placed by the proximity rule and added to the README table (and
  this ADR, on a taxonomy change) in the same commit that creates them.
