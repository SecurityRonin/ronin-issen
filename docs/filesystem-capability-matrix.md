# Filesystem Capability Matrix

**Status:** living. **Scope:** every filesystem the fleet reads or intends to read.

## Why this document exists

An external contributor sent us symlink fixes for two readers:

| repo | what we had silently not decoded |
|---|---|
| `ntfs-forensic` | reparse-point symlinks, **and ntfs-3g's `IntxLNK`** |
| `udf-forensic` | `PATH_COMPONENT` symlinks |

Both are merged. The point of this document is not those two bugs — it is that
**we had no way to notice them before someone outside told us**, and the same
blind spot has since produced two more silent losses (extended attributes, NTFS
alternate data streams).

A capability we do not decode is not reported as missing. It is reported as
**absent from the evidence**. That is the failure mode this matrix exists to
make impossible.

---

## Part 1 — The structural cause, not the individual bugs

`forensic_vfs::FileSystem` has **5 methods whose default implementation returns
empty**: [OBSERVED, counted from `crates/core/src/fs.rs`]

```
data_streams    hardlinks    deleted_nodes    slack    findings
```

A reader that never overrides one of these reports *"this filesystem has none of
that"*. There is no third state. **"Not implemented" and "not present in the
evidence" are the same value**, and the caller cannot tell them apart.

That single design choice explains all three losses:

| loss | mechanism |
|---|---|
| extended attributes | `data_streams` defaulted empty in 8 readers |
| NTFS alternate data streams | `data_streams` still defaults empty for NTFS |
| symlinks (the PRs) | `read_link` returned `Ok(empty)` for encodings not handled |

**The fix is structural, not per-feature.** Three candidate designs:

1. `Capability` declaration — a reader states which capabilities it implements;
   an unimplemented one returns `Err(NotImplemented)`, never empty.
2. Make the methods **required** (no default). Adding one then breaks every
   reader at compile time until each decides, explicitly, what it supports.
3. A `Supported { yes, no, unimplemented }` tri-state return.

(2) is the cheapest and the loudest: the compiler becomes the matrix. It is also
what this fleet already does elsewhere — `check_selectable` in `4n6mount`
deliberately has no catch-all arm so a new backend fails to compile.

---

## Part 2 — Measured coverage

[OBSERVED] Grepped from each reader's `impl FileSystem` source (not tests —
an earlier pass measured `core/tests/vfs.rs` for XFS and produced a wrong row).

| reader | read_link | data_streams | hardlinks | deleted_nodes | slack | findings |
|---|---|---|---|---|---|---|
| ntfs | yes | yes | **yes** | yes | **yes** | no |
| apfs | yes | yes | no | no | no | no |
| hfsplus | yes | yes | no | no | no | no |
| ext4 | yes | yes | no | no | no | no |
| xfs | yes | yes | no | no | no | no |
| btrfs | yes | yes | **yes** | no | no | no |
| udf | yes | yes | no | no | no | no |
| ufs | yes | yes | no | no | no | no |
| zfs | yes | yes | no | no | no | no |
| fat | n/a (correctly empty) | no | no | no | no | no |
| iso9660 | **stub** | no | no | no | no | no |
| refs | *no `impl FileSystem` at all* | | | | | |

**Read this table as a list of things we currently report as absent from every
image we examine.**

> **This table's unit of measurement is wrong, and Part 7 explains why.** It
> counts whether a method exists, not whether it returns anything. `iso9660` was
> scored `read_link: yes` while its body was `Ok(Vec::new())` with the comment
> "Rock Ridge SL symlinks are not surfaced" — the precise bug an outside
> contributor fixed for us twice. It has since been fixed. Treat every `yes`
> below as unverified until a named fixture exercises it.

- `hardlinks` — **2 of 11** (NTFS + Btrfs, 2026-09-21). ext4, XFS, Btrfs, ZFS, UFS,
  APFS and HFS+ also support hard links and still say no file has any. NTFS was
  done first because it is the only one where the answer is a direct read:
  each name is its own `$FILE_NAME` attribute carrying its own parent
  reference. The others need a directory walk, except **Btrfs** (`INODE_REF`)
  and **APFS** (sibling-link records), which have back-references too — Btrfs
  is now done; APFS recognises `SiblingLink` as a record type but does not yet
  decode its parent/name.
  Fixture exercised: `ntfs_windows_reparse.img` MFT 39 (`target.txt` +
  `hardlink.txt`), plus MFT 35 of the sample volume as a must-not-over-report
  control for the 8.3 DOS alias.
- `slack` — **1 of 11** (NTFS, 2026-09-21). Fixture exercised: `$Bitmap`
  (MFT 6), 1792 bytes in 4 clusters → 256 bytes at image offset 2_437_888.
- `findings` — **0 of 11**.
- `deleted_nodes` — **1 of 11** (NTFS).
- `data_streams` — 8 of 11 after the recent xattr work; **NTFS is missing**.

### The NTFS alternate-data-stream case is the sharpest example

[OBSERVED] `ntfs-forensic` *can* read an ADS: `read_named_stream(path, stream)`
exists and a test reads `Zone.Identifier`. But the VFS adapter:

- does not implement `data_streams`, so streams cannot be **enumerated**; and
- `stream_name(StreamId::Named(n))` **refuses**, with the comment *"a named-stream
  id cannot be mapped back to its ADS name"*.

So an ADS is readable only by someone who already knows its name. Through the
VFS and any mount, `Zone.Identifier` — the mark-of-the-web, the record of where
a file came from — is invisible and unenumerable.

---

## Part 3 — What the model cannot express at all

The more dangerous category: **absent from the trait ⇒ absent from the matrix ⇒
nobody notices.** [OBSERVED, crate-wide grep with a passing control]

| concept | in `forensic-vfs`? | consequence |
|---|---|---|
| **ACLs** — POSIX draft, NFSv4, NTFS SD/SID | **0 hits crate-wide** | NTFS ownership and permissions cannot be carried at all |
| **`rdev` (major/minor)** | **absent** | `NodeKind::CharDevice` exists but not *which* device — `/dev/null` and `/dev/sda` are indistinguishable |
| NTFS object id (`$ObjId`) | absent | link-tracking / GUID evidence unavailable |
| short name (8.3) | absent | the alternate name an artifact may reference |
| raw reparse tag | absent | cannot report an unrecognised tag as unrecognised |
| generation / version | absent | inode reuse undetectable |

The `rdev` case is worth stating precisely because it nearly escaped: a
case-insensitive grep for `rdev` returns 6 hits, **all of which are substrings
of `CharDevice`**. There is no field.

---

## Part 4 — The feature union

Organised by the axis that actually causes misses: **one logical capability,
many on-disk encodings.** A reader that handles one encoding and returns empty
for the rest is the `IntxLNK` bug repeating.

Provenance: [SPEC] = from the format specification or kernel source;
[OBSERVED] = measured in our tree. Entries without a tag are domain knowledge
and **must be verified against a spec before being relied on**.

### 4.1 Symlinks — the class that already bit us

| filesystem | encodings a reader must handle |
|---|---|
| ext2/3/4 | **fast** (target inline in `i_block`, < 60 bytes) vs **slow** (in data blocks). Two code paths. |
| XFS | `di_format` local (inline) vs extents |
| UFS2 | inline (`di_size <= maxsymlinklen`) vs data blocks |
| Btrfs | inline extent |
| ZFS | SA `ZPL_SYMLINK` vs spill / data |
| APFS | `com.apple.fs.symlink` **xattr**, not a data fork |
| HFS+ | file with type/creator `slnk`/`rhap`; target in data fork |
| NTFS | `IO_REPARSE_TAG_SYMLINK` (0xA000000C) with *relative/absolute* flag **and** print-name vs substitute-name; `IO_REPARSE_TAG_MOUNT_POINT` (0xA0000003) = junction; **ntfs-3g `IntxLNK`** marker in the data stream; WSL `IO_REPARSE_TAG_LX_SYMLINK` (0xA000001D); **Cygwin** (system-attribute file with a magic prefix, or an EA) |
| ISO9660 | Rock Ridge `SL` entry, component-by-component with flags |
| UDF | `PATH_COMPONENT` records (type 1 = "agreed location", 2 = root, 3 = parent, 4 = current, 5 = name) |
| FAT/exFAT | none natively — but a `.lnk` shell shortcut is *not* a symlink and must not be reported as one |

**The trap:** NTFS alone has at least five distinct symlink-ish encodings from
three different operating-system communities. Decoding one and returning empty
for the others is exactly the reported bug.

### 4.2 Metadata stored somewhere unexpected

The category the fleet is weakest on. [OBSERVED] **no filesystem reader decodes
any of these**; `winreg-forensic` knows LXSS only on the registry side.

| mechanism | where it hides | what is lost if ignored |
|---|---|---|
| **WSL1** | NTFS EAs `$LXUID`, `$LXGID`, `$LXMOD`, `$LXDEV` | real POSIX uid/gid/mode and device numbers |
| **WSL2 / `wsl --mount`** | NTFS EA `LXATTRB` (and `LXXATTR` for Linux xattrs) | same, plus the Linux xattrs themselves |
| **Cygwin** | POSIX perms in NTFS ACL entries; symlinks as system-attr files | permissions and link structure |
| **SFU / Interix / "Subsystem for UNIX"** | EAs / reparse | uid/gid/mode |
| **macOS on non-Apple volumes** | AppleDouble `._name` sidecars | resource fork + Finder info on FAT/exFAT/SMB |
| **HFS+/APFS decmpfs** | `com.apple.decmpfs` xattr + **resource fork** | the file's actual contents — an uncompressed read returns 0 bytes |
| **NTFS WOF / WIM-backed** | `IO_REPARSE_TAG_WOF`, data in `WofCompressedData` ADS | contents; the `$DATA` is empty |
| **OneDrive / cloud placeholders** | `IO_REPARSE_TAG_CLOUD*` | file is a stub; contents are not local |
| **NTFS dedup** | `IO_REPARSE_TAG_DEDUP`, chunks in `System Volume Information` | contents |

**Rule this suggests:** whenever a file's *contents* or *identity* can live
outside its obvious home, a reader that reads only the obvious home returns a
confident wrong answer.

### 4.3 Special node types

| type | ext4/XFS/UFS/Btrfs/ZFS | NTFS | FAT/exFAT | ISO9660 | UDF | APFS/HFS+ |
|---|---|---|---|---|---|---|
| char device | mode + rdev | WSL `LX_CHR` reparse | — | Rock Ridge `PN` | ICB type 6 | mode + rdev |
| block device | mode + rdev | WSL `LX_BLK` | — | Rock Ridge `PN` | ICB type 5 | mode + rdev |
| FIFO | mode | WSL `LX_FIFO` | — | Rock Ridge | ICB type 9 | mode |
| socket | mode | WSL `AF_UNIX` | — | — | ICB type 10 | mode |
| hard link | `nlink > 1` | multiple `$FILE_NAME` / MFT links | — | — | ICB link count | `nlink` |
| whiteout | overlayfs char 0:0 | — | — | — | ICB type 8 | — |
| junction / mount point | — | `MOUNT_POINT` tag | — | — | — | firmlink (APFS) |

### 4.4 Timestamps

| filesystem | count | epoch | resolution | timezone | notes |
|---|---|---|---|---|---|
| NTFS | **8** | 1601 | 100 ns | UTC | 4 in `$STANDARD_INFORMATION` + 4 in `$FILE_NAME` — the `$SI`/`$FN` divergence is a timestomping indicator |
| ext4 | 4–5 | 1970 | ns (if `i_extra`) | UTC | `crtime` only with large inodes |
| XFS | 3–4 | 1970 | ns | UTC | `crtime` on v5; **bigtime** changes the epoch |
| APFS | 4 | 1970 | ns | UTC | |
| HFS+ | 5 | **1904** | 1 s | UTC (local on very old) | includes backup time; 1904 is also the "never" marker |
| FAT | 3 | **1980** | **2 s** (mtime), 10 ms (ctime), 1 day (atime) | **LOCAL TIME** | no timezone recorded — a real ambiguity |
| exFAT | 3 | 1980 | 10 ms | local **+ UTC offset byte** | |
| UFS2 | 4 | 1970 | ns | UTC | |
| ZFS | 4 | 1970 | ns | UTC | |
| ISO9660 | 1–4 | — | 1 s | offset recorded | Rock Ridge `TF` adds more |
| UDF | 3–4 | — | µs | offset recorded | |

**Traps:** FAT stores *local* time with no zone — any UTC rendering is an
inference, not a reading. HFS+ 1904 is both an epoch and a sentinel. NTFS `$FN`
timestamps are the ones malware forgets to forge.

### 4.5 Data representation

| capability | where it appears |
|---|---|
| inline / resident data | NTFS resident `$DATA`, ext4 `inline_data`, Btrfs inline extent, APFS, HFS+, ZFS SA |
| sparse / holes | ext4, XFS, Btrfs, ZFS, APFS, NTFS (sparse attribute) |
| preallocated / unwritten | XFS, ext4 (`fallocate`), NTFS (valid-data-length < allocated) |
| **compression** | NTFS LZNT1 + **WOF (XPRESS/LZX)**; Btrfs zlib/lzo/zstd; ZFS lz4/gzip/zstd/zle; HFS+/APFS decmpfs (zlib/lzvn/lzfse); ReFS; F2FS |
| **encryption** | NTFS EFS ($EFS attribute); ext4 fscrypt; APFS FileVault; ZFS native; and volume-level BitLocker / LUKS / FileVault2 below the filesystem |
| dedup | ZFS, NTFS dedup reparse, Btrfs |
| reflink / CoW clone | Btrfs, XFS, APFS clonefile, ZFS |
| snapshots | ZFS, Btrfs, APFS, NTFS **VSS**, LVM |
| multi-device | Btrfs, ZFS (vdev), LVM |
| alternate streams | NTFS ADS; HFS+/APFS resource fork |

### 4.6 Naming

Case sensitivity (ext4 `casefold`, APFS case-insensitive variants, NTFS
case-preserving-insensitive, HFS+ HFSX), Unicode normalisation (**HFS+ stores
NFD** — a name read as NFC will not match), name encoding (UTF-16LE on NTFS,
OSTA CS0 on UDF, Joliet UCS-2 vs Rock Ridge on ISO9660, arbitrary bytes on
POSIX), 8.3 short names, max name/path length, directory indexing (ext4 htree,
NTFS `$I30` B-tree — whose **slack holds deleted entries**).

### 4.7 Forensic-only surfaces

Slack (file/RAM/`$I30`), unallocated, orphan inodes, journals (ext4 jbd2, NTFS
`$LogFile`, XFS log, HFS+ journal), **NTFS `$UsnJrnl`**, `$Extend` metafiles,
trash/recycle semantics, timestomping indicators, object ids, quotas.

---

## Part 5 — Ranked by evidence lost, not by effort

Ranking is by **how much evidence disappears silently**, weighted by how
ordinary the trigger is.

| # | gap | why it ranks here |
|---|---|---|
| 1 | **`hardlinks` unimplemented in 9 of 11 readers** (NTFS + Btrfs done 2026-09-21) | every remaining reader asserts no file has a hard link. Affects 7 more of our filesystems. A link count > 1 is how you show one object had several names — routinely material. **Btrfs `INODE_REF` and APFS sibling links are direct reads like NTFS; the rest need a directory walk.** |
| 2 | ~~**NTFS ADS unenumerable**~~ — **fixed 2026-09-20** | `data_streams` now enumerates named `$DATA` attributes and `read_at` resolves `StreamId::Named(i)`, validated against TSK `istat` on MFT 8. |
| 3 | **No ACL / security-descriptor concept anywhere** | NTFS ownership and permissions cannot even be carried. "Who could access this" is unanswerable through our model. |
| 4 | **WSL POSIX metadata undecoded** | `$LXUID`/`$LXGID`/`$LXMOD`/`$LXDEV`, `LXATTRB`. A developer laptop with WSL is now an ordinary exhibit; uid/gid/mode read as absent. |
| 5 | **`slack` unimplemented in 10 of 11** (NTFS done 2026-09-21) | file slack is primary evidence and every remaining reader reports none. |
| 6 | **No `rdev`** | device nodes are reported as a class without identity. |
| 7 | **Contents that live elsewhere** (decmpfs, WOF, dedup, cloud placeholder) | a plain read returns 0 bytes or a stub, with no error — the worst available failure. |
| 8 | **`deleted_nodes` in 10 of 11** | recovery surface absent outside NTFS. |
| 9 | **`refs-forensic` has no `impl FileSystem`** | the reader is invisible to the engine entirely. |

## Part 6 — The rule that would have caught all of it

> **A capability a reader does not implement must be distinguishable, by the
> caller, from a capability the evidence does not contain.**

Everything in Part 5 is a violation of that one sentence. It is the same rule
already applied elsewhere in the fleet:

- `4n6mount` mount fidelity: the mount *declares* what its transport drops, and
  says an absence seen through it is **UNKNOWN**, not a finding.
- `zfs-forensic::has_unread_spill_xattrs`: reports when attributes sit in a
  spill block the reader does not follow, so "not recovered" ≠ "none present".
- `check_selectable`: no catch-all arm, so an unhandled case fails to compile.

### Concrete next steps

1. **Make the 5 empty-default methods required.** The compiler then enumerates
   this matrix for us, and a new capability cannot be silently skipped.
2. **A conformance test per reader**, generated from the matrix: for each
   capability the filesystem *has*, assert either a real result or an explicit
   `NotImplemented` — never empty.
3. **Corpus obligation.** The xattr work found `xattr_passthrough` had been red
   for weeks because its three images carried no attributes at all. A capability
   claim needs a fixture that *exercises* it; otherwise the test measures
   nothing. Each row of this matrix should name its fixture.
4. Add `rdev`, ACLs and raw reparse tag to `FsMeta` before claiming device,
   permission or reparse support.

---

## Part 7 — Adversarial review, and what it changed

This matrix was attacked by an independent model before publication. It landed
two hits that materially changed the document, and one of them found a live bug.

### Hit 1 — "Claim 1 overstates causality"

My original thesis was *empty trait defaults are the root cause*. The critique
pointed out that **my own symlink incident refutes it**: `read_link` WAS
implemented in every reader. A mandatory method would not have caught it,
because the method existed and still returned empty for encodings it did not
recognise.

The stronger diagnosis, adopted here:

> **The system does not reliably distinguish unsupported interpretation,
> incomplete enumeration, and verified absence.**

Empty defaults are only one mechanism. Others, all present in this fleet:

| mechanism | instance |
|---|---|
| an explicit override returning empty | ISO9660 `read_link` — "SL symlinks are not surfaced" |
| recognising only ONE encoding of a feature | NTFS symlink vs `IntxLNK` vs `LX_SYMLINK` |
| `filter_map(Result::ok)` discarding malformed records | swallows corruption as absence |
| a metadata struct with nowhere to put a field | no `rdev`, no ACL |
| an adapter exposing less than the reader knows | NTFS ADS, ISO9660 `SL`, xattrs |
| fixtures produced by one OS / one writer | `xattr_passthrough` was red for weeks over images with no attributes |

"Make the methods required" fixes only the first row. It is still worth doing,
but it is not the fix.

### Hit 2 — "your matrix measures the wrong thing"

Part 2 counts *whether a method exists*, not whether it returns anything. The
critique predicted this would hide real gaps. **It did, immediately:**

ISO9660 scored `read_link: yes`. Its body was:

```rust
// Rock Ridge SL symlinks are not surfaced; a node reads as an empty target
Ok(Vec::new())
```

That is the exact bug an outside contributor fixed for us twice. My matrix was
scoring it as coverage. Fixed in `iso9660-forensic` (Rock Ridge `SL` now
decoded), and wiring it exposed a worse defect beneath: extent-less nodes share
one `FileId`, so two symlinks alias and one reports the other's target.

**Therefore: a row in this matrix means nothing unless it names the fixture that
exercises it.** "Implemented" is not a measurement. "Returns X for fixture Y" is.

### Capability vs outcome — the representation this suggests

Two different things need saying, and one value cannot say both:

| capability (per reader, static) | outcome (per examination) |
|---|---|
| Supported, for these encodings/versions | Complete within an explicit scope |
| Partially supported | Partial — these regions/features omitted |
| Unsupported | Not examined |
| Not applicable to this format | Reasoned non-applicability |
| Unknown | Unclassified feature encountered |

Corruption, a missing device, an unavailable key and a resource limit must stay
distinguishable from each other and from "absent". The critique's warning
against solving this with a hundred-method trait is taken: prefer composable
capability interfaces over widening `FileSystem`.

### Terminology

Call these **evidence omissions**, not "evidence loss" — nothing was destroyed;
it was never surfaced. The distinction matters in a report.
