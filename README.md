<p align="center">
  <img src="assets/issen-banner.png#gh-dark-mode-only"
       alt="ronin-issen — SecurityRonin forensic-fleet umbrella" width="640" />
  <img src="assets/issen-banner-light.png#gh-light-mode-only"
       alt="ronin-issen — SecurityRonin forensic-fleet umbrella" width="640" />
</p>

# ronin-issen — SecurityRonin forensic-fleet umbrella

**Governance root for the SecurityRonin forensic fleet.** This is a **docs-only** repo:
it holds the fleet *constitution* and the canonical component layout — not code. Component
repos (parsers, container readers, the `*4n6` CLIs, the issen capstone, …) live under
`components/<category>/<repo>` as their **own independent git repos** and are gitignored
here, by design — this is deliberately *not* a monorepo
([ADR-0017](docs/decisions/0017-fleet-folder-umbrella-taxonomy.md)).

## What's here

| Path | What it is |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | **The fleet constitution.** Layer hierarchy, crate naming, the reader/analyzer (`core`/`forensic`) split, the Paranoid-Gatekeeper security standard, and the README / corpus / validation / **release & Windows code-signing** / secrets / distribution standards. Every component inherits it. |
| [`docs/decisions/`](docs/decisions/) | Fleet-level ADRs — the folder umbrella + taxonomy ([ADR-0017](docs/decisions/0017-fleet-folder-umbrella-taxonomy.md)), the conceptual layer architecture ([ADR-0016](docs/decisions/0016-multi-repo-layer-architecture.md)), release order ([ADR-0006](docs/decisions/0006-fleet-dependency-layering-release-order.md)), and more. |
| [`docs/components-diagram.html`](docs/components-diagram.html) | Rendered component layout — tier flow (evidence → timeline) + the cross-cutting rail. Self-contained dark-theme SVG; open locally in any browser. |
| `docs/` | Fleet-wide reference (glossary, test-data catalog, release SOP). |
| `components/`, `_deprecated/` | The actual fleet repos — **separate gits, never tracked here** (gitignored). |

## Component layout (canonical)

`components/<category>/<repo>` — **86 repos, 16 folders**. The component tree is the
registry; this table is its canonical statement. Categories group by the **proximity
rule**: same conceptual idea → same folder; contract crates live with their families;
sub-groups get a label here, not a folder. New repos are placed by that rule and added
to this table in the same commit that creates them. Rationale + reserved categories:
[ADR-0017](docs/decisions/0017-fleet-folder-umbrella-taxonomy.md).

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

These folders govern **where a human looks**. The conceptual dependency **tiers**
(FOUNDATION → CONTAINER → … → ORCHESTRATION — [ADR-0016](docs/decisions/0016-multi-repo-layer-architecture.md))
govern dependency direction and release order ([ADR-0006](docs/decisions/0006-fleet-dependency-layering-release-order.md)).
Related, deliberately not identical.

## Why this repo doesn't wear the product-README standard

The fleet's README / badge / GitHub-Pages / Privacy-Terms standard targets **published
crates and CLIs** and their end users. `ronin-issen` is a **governance / umbrella** repo —
its audience is fleet maintainers, so it carries a governance README (this file), stays
**private**, and is secret-scanned, but skips the crates.io/docs.rs badges, the 30-second
install hook, and the public docs-site apparatus. Standards bend to repo **role** — the
same principle as MSRV-by-role.

Private · © 2026 Security Ronin Ltd
