# 11. VFS & universal container abstraction — format-agnostic image/filesystem access

Date: 2026-07-26
Status: Accepted

## Context

Many consumers read evidence images: carvers, the timeline engine, the CLIs. If each one
sniffs container magic and branches per format (`if ewf {…} else if vmdk {…}`), the fleet ends
up with N parallel detection stacks, N places to add a new format, and N chances to special-case
one format wrong. That is the container/filesystem application of *Dependency Preference*
(ADR-0010) + DRY: one open-any-image entry point, not a detection stack per consumer.

## Decision

**A consumer that reads an evidence image MUST NOT know one container or filesystem format from
another.** It asks the abstraction to open the path and gets back a uniform byte source; only
the abstraction layer knows E01 from VMDK, or NTFS from APFS.

- **Raw disk images → `disk_forensic::container::open(path)`** (the published `disk-forensic`
  crate). It sniffs the container magic and decodes it to a uniform `OpenedImage { format, size,
  reader: Box<dyn ReadSeek> }` — Raw/dd, **EWF/E01, VMDK, QCOW2, VHD, VHDX, DMG, ISO, AFF4**
  (physical). Rename a `.vmdk` to `.bin` and it still works. A corrupt/unsupported-variant
  container fails **loud** (`OpenError`), never silent wrong output.
- **Logical file containers → `disk_forensic::logical::open(path)`.** AD1 (FTK Custom Content)
  and logical AFF4 (`aff4:FileImage`) are file trees, **not** sector-level disks — there is no
  raw disk underneath. `container::open` on one returns a typed `OpenError::LogicalContainer(_)`
  pointing at `logical::open` (which yields `entries()` + `read_file`), **never** a bogus disk
  reader. Keep the raw-disk vs logical distinction honest at the type level — do not shoehorn a
  file archive into the raw-disk contract.
- **Filesystems over a byte source → `forensic-vfs`.** `forensic-vfs` is the KNOWLEDGE-leaf
  contract crate: the `ImageSource` positioned-byte edge + volume-system / crypto-layer /
  filesystem-probe traits + the recursive `PathSpec` locator (no parsers). Readers implement the
  traits; `forensic-vfs-engine` composes the concrete decoders (ewf/vmdk/dmg + ntfs/fat/ext4/
  apfs/hfsplus …) so a whole stack — `E01 → GPT → BitLocker → NTFS` — reads as one `Arc<dyn
  ImageSource>` that N workers share and no path can write.
- **The rule:** a consumer depends on the ABSTRACTION (`disk-forensic` / `forensic-vfs`),
  **never** on a per-format container crate (`ewf`/`vmdk`/`dmg`/`qcow2`/…) or a per-filesystem
  crate directly. Adding a new format then benefits every consumer at once. **A consumer that
  special-cases one format is the smell this policy exists to catch** (e.g. an `if ewf { … }`
  branch in a carver is wrong — call `container::open` and let it decode). Migrate any such
  branch to the abstraction proactively, not as a "follow-up".

**Honest current gaps (state them, don't hide them):** `forensic-vfs-engine` is `publish =
false`, so cross-repo *filesystem* composition still uses a path/git dep until it publishes;
`disk-forensic`'s `ReadSeek` trait lacks a `Send` bound, so a `Send + Sync` `ImageSource`
adapter needs a worker-thread seam until `+ Send` is added; multi-segment E01/AD1 coverage
follows the underlying reader.

## Consequences

- Adding a new container/filesystem format benefits every consumer at once (one place to add
  it), instead of touching N detection stacks.
- Raw-disk and logical-container contracts stay distinct at the type level; a file archive is
  never returned as a bogus disk reader.
- A per-format special-case in a consumer is a reviewable smell to migrate onto the abstraction,
  not accepted debt.
