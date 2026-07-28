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
| [`knowledge/`](components/knowledge/) (2) | FOUNDATION leaf — compile-time format facts, hash DBs; zero fleet deps | [forensic-hashdb](https://github.com/SecurityRonin/forensic-hashdb) · [forensicnomicon](https://github.com/SecurityRonin/forensicnomicon) |
| [`utility/`](components/utility/) (7) | cross-cutting mechanisms — owns no format, serves many layers | [blazehash](https://github.com/SecurityRonin/blazehash) · [forensic-carve](https://github.com/SecurityRonin/forensic-carve) · [jsonguard](https://github.com/SecurityRonin/jsonguard) · [name-variants](https://github.com/SecurityRonin/name-variants) · [safe-read](https://github.com/SecurityRonin/safe-read) · [shrinkpath](https://github.com/SecurityRonin/shrinkpath) · [timeglyph](https://github.com/SecurityRonin/timeglyph) |
| [`codec/`](components/codec/) (3) | pure-Rust decompressors | [lzo](https://github.com/SecurityRonin/lzo) · [lzvn](https://github.com/SecurityRonin/lzvn) · [xpress-huffman](https://github.com/SecurityRonin/xpress-huffman) |
| [`container/`](components/container/) (8) | decode an image/dump → addressable byte stream | [ad1-forensic](https://github.com/SecurityRonin/ad1-forensic) · [aff4-forensic](https://github.com/SecurityRonin/aff4-forensic) · [dmg-forensic](https://github.com/SecurityRonin/dmg-forensic) · [ewf-forensic](https://github.com/SecurityRonin/ewf-forensic) · [qcow2-forensic](https://github.com/SecurityRonin/qcow2-forensic) · [vhd-forensic](https://github.com/SecurityRonin/vhd-forensic) · [vhdx-forensic](https://github.com/SecurityRonin/vhdx-forensic) · [vmdk-forensic](https://github.com/SecurityRonin/vmdk-forensic) |
| [`acquisition/`](components/acquisition/) (1) | live-host disk enumeration + acquisition-integrity grading | [livedisk-forensic](https://github.com/SecurityRonin/livedisk-forensic) |
| [`archive/`](components/archive/) (3) | file containers (not raw disks) | [archive-forensic](https://github.com/SecurityRonin/archive-forensic) · [dar-forensic](https://github.com/SecurityRonin/dar-forensic) · [zip-forensic](https://github.com/SecurityRonin/zip-forensic) |
| [`partition/`](components/partition/) (3) | partition schemes | [apm-partition-forensic](https://github.com/SecurityRonin/apm-partition-forensic) · [gpt-partition-forensic](https://github.com/SecurityRonin/gpt-partition-forensic) · [mbr-partition-forensic](https://github.com/SecurityRonin/mbr-partition-forensic) |
| [`encryption/`](components/encryption/) (6) | crypto layers + bespoke primitives | [bitlocker-forensic](https://github.com/SecurityRonin/bitlocker-forensic) · [dpapi-forensic](https://github.com/SecurityRonin/dpapi-forensic) · [elephant-diffuser](https://github.com/SecurityRonin/elephant-diffuser) · [filevault-forensic](https://github.com/SecurityRonin/filevault-forensic) · [luks-forensic](https://github.com/SecurityRonin/luks-forensic) · [veracrypt-forensic](https://github.com/SecurityRonin/veracrypt-forensic) |
| [`filesystem/`](components/filesystem/) (16) | navigate sectors by path (name→inode→block); vfs stack + FUSE mount | [4n6mount](https://github.com/SecurityRonin/4n6mount) · [apfs-forensic](https://github.com/SecurityRonin/apfs-forensic) · [btrfs-forensic](https://github.com/SecurityRonin/btrfs-forensic) · [ext4fs-forensic](https://github.com/SecurityRonin/ext4fs-forensic) · [fat-forensic](https://github.com/SecurityRonin/fat-forensic) · [forensic-vfs](https://github.com/SecurityRonin/forensic-vfs) · [forensic-vfs-engine](https://github.com/SecurityRonin/forensic-vfs-engine) · [forensic-vfs-mount](https://github.com/SecurityRonin/forensic-vfs-mount) · [hfsplus-forensic](https://github.com/SecurityRonin/hfsplus-forensic) · [iso9660-forensic](https://github.com/SecurityRonin/iso9660-forensic) · [ntfs-forensic](https://github.com/SecurityRonin/ntfs-forensic) · [refs-forensic](https://github.com/SecurityRonin/refs-forensic) · [udf-forensic](https://github.com/SecurityRonin/udf-forensic) · [ufs-forensic](https://github.com/SecurityRonin/ufs-forensic) · [xfs-forensic](https://github.com/SecurityRonin/xfs-forensic) · [zfs-forensic](https://github.com/SecurityRonin/zfs-forensic) |
| [`memory/`](components/memory/) (1) | memory dump → page stream; OS-structure walking | [memory-forensic](https://github.com/SecurityRonin/memory-forensic) |
| [`log/`](components/log/) (2) | navigate a log stream by timestamp / record number | [journald-forensic](https://github.com/SecurityRonin/journald-forensic) · [winevt-forensic](https://github.com/SecurityRonin/winevt-forensic) |
| [`parser/`](components/parser/) (25) | interpret artifact records → forensic meaning (medium-agnostic) | [amcache-forensic](https://github.com/SecurityRonin/amcache-forensic) · [atx-forensic](https://github.com/SecurityRonin/atx-forensic) · [bam-forensic](https://github.com/SecurityRonin/bam-forensic) · [blob-decoder](https://github.com/SecurityRonin/blob-decoder) · [bluetooth-forensic](https://github.com/SecurityRonin/bluetooth-forensic) · [browser-forensic](https://github.com/SecurityRonin/browser-forensic) · [cfb-forensic](https://github.com/SecurityRonin/cfb-forensic) · [ese-forensic](https://github.com/SecurityRonin/ese-forensic) · [exec-pe-forensic](https://github.com/SecurityRonin/exec-pe-forensic) · [leveldb-forensic](https://github.com/SecurityRonin/leveldb-forensic) · [lnk-forensic](https://github.com/SecurityRonin/lnk-forensic) · [peripheral-forensic](https://github.com/SecurityRonin/peripheral-forensic) · [prefetch-forensic](https://github.com/SecurityRonin/prefetch-forensic) · [protobuf-forensic](https://github.com/SecurityRonin/protobuf-forensic) · [segb-forensic](https://github.com/SecurityRonin/segb-forensic) · [shellhist-forensic](https://github.com/SecurityRonin/shellhist-forensic) · [shellitem](https://github.com/SecurityRonin/shellitem) · [shimcache-forensic](https://github.com/SecurityRonin/shimcache-forensic) · [snss-forensic](https://github.com/SecurityRonin/snss-forensic) · [sqlite-forensic](https://github.com/SecurityRonin/sqlite-forensic) · [srum-forensic](https://github.com/SecurityRonin/srum-forensic) · [trash-forensic](https://github.com/SecurityRonin/trash-forensic) · [usb-forensic](https://github.com/SecurityRonin/usb-forensic) · [userassist-forensic](https://github.com/SecurityRonin/userassist-forensic) · [winreg-forensic](https://github.com/SecurityRonin/winreg-forensic) |
| [`graph/`](components/graph/) (1) | content-addressed / Merkle-DAG navigation | [git-forensic](https://github.com/SecurityRonin/git-forensic) |
| [`history/`](components/history/) (3) | [H] state-history temporal cohorts | [snapshot-forensic](https://github.com/SecurityRonin/snapshot-forensic) · [state-history-forensic](https://github.com/SecurityRonin/state-history-forensic) · [vsc-forensic](https://github.com/SecurityRonin/vsc-forensic) |
| [`orchestration/`](components/orchestration/) (3) | cross-artifact correlation → one unified timeline | [disk-forensic](https://github.com/SecurityRonin/disk-forensic) · [issen](https://github.com/SecurityRonin/issen) · [useract-forensic](https://github.com/SecurityRonin/useract-forensic) |
| [`_deprecated/`](_deprecated/) (2) | superseded; kept for reference | [ewf](https://github.com/SecurityRonin/ewf) · [usnjrnl-forensic](https://github.com/SecurityRonin/usnjrnl-forensic) |

These folders govern **where a human looks**. The conceptual dependency **tiers**
(FOUNDATION → CONTAINER → … → ORCHESTRATION — [ADR-0016](docs/decisions/0016-multi-repo-layer-architecture.md))
govern **what may import what**; the bottom-up **publish order** that graph forces is
its corollary ([ADR-0006](docs/decisions/0006-fleet-dependency-layering-release-order.md)).
Related but not 1:1 — the **16 folders collapse onto 5 dependency tiers** (e.g. `knowledge/`,
`utility/`, and `codec/` are three folders but one zero-dep tier; `utility`/`codec` are
cross-cutting rails depended on from every tier, not a rung). A folder is chosen by *what a
repo is*; its tier is *derived from what it imports*.

## Why this repo doesn't wear the product-README standard

The fleet's README / badge / GitHub-Pages / Privacy-Terms standard targets **published
crates and CLIs** and their end users. `ronin-issen` is a **governance / umbrella** repo —
its audience is fleet maintainers, so it carries a governance README (this file), stays
**private**, and is secret-scanned, but skips the crates.io/docs.rs badges, the 30-second
install hook, and the public docs-site apparatus. Standards bend to repo **role** — the
same principle as MSRV-by-role.

Private · © 2026 Security Ronin Ltd
