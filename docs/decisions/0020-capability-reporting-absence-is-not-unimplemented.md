# 20. A capability we did not implement must never look like evidence that is not there

Date: 2026-09-20

Status: Accepted — the rule is binding on every reader; the mechanism is staged

## Context

An external contributor sent us symlink fixes for two readers:

| repo | silently not decoded |
|---|---|
| `ntfs-forensic` | reparse-point symlinks **and ntfs-3g `IntxLNK`** |
| `udf-forensic` | `PATH_COMPONENT` symlinks |

Both merged. The problem is not those two bugs. It is that **nobody inside the
fleet could have noticed them**, and the same blind spot has since produced
three more:

| instance | shape |
|---|---|
| extended attributes | `data_streams` defaulted empty in 8 readers; the readers had the data |
| NTFS alternate data streams | reader reads an ADS by name; adapter cannot enumerate, so `Zone.Identifier` is invisible |
| ISO 9660 Rock Ridge `SL` | `read_link` returned `Ok(Vec::new())` under the comment *"SL symlinks are not surfaced"* while `rock_ridge::symlink_target()` sat unused in the same crate |

One shape, four times: **the reader can decode it; the VFS adapter never asks.**
Every one reaches the examiner as *"this file has no such thing"*.

### The first diagnosis was wrong

The obvious reading is *empty trait defaults are the cause* —
`forensic_vfs::FileSystem` has five methods defaulting to empty (`data_streams`,
`hardlinks`, `deleted_nodes`, `slack`, `findings`).

Adversarial review refuted it with our own symlink incident: **`read_link` was
implemented in all eleven readers** and still returned empty for encodings it did
not recognise. Making the method mandatory would not have caught it.

## Decision

**A capability a reader does not implement must be distinguishable, by the
caller, from a capability the evidence does not contain.**

That is the binding rule. Empty defaults are one mechanism that breaks it; these
are the others, all observed in this fleet:

| mechanism | instance |
|---|---|
| an explicit override returning empty | ISO 9660 `read_link` |
| recognising only ONE encoding of a feature | NTFS symlink vs `IntxLNK` vs `LX_SYMLINK` |
| `filter_map(Result::ok)` discarding malformed records | corruption read as absence |
| a metadata struct with nowhere to put a field | no `rdev`; no ACL concept at all |
| an adapter exposing less than the reader knows | xattrs, NTFS ADS, Rock Ridge `SL` |
| fixtures produced by one OS or one writer | `xattr_passthrough` sat red for weeks over three images that carried no attributes |

### Two values, because one cannot say both

| capability — per reader, static | outcome — per examination |
|---|---|
| Supported, for these encodings/versions | Complete within an explicit scope |
| Partially supported | Partial — these regions/features omitted |
| Unsupported | Not examined |
| Not applicable to this format | Reasoned non-applicability |
| Unknown | Unclassified feature encountered |

Corruption, a missing device, an unavailable key and a resource limit stay
distinguishable from each other and from *absent*.

### What this does NOT license

**Do not widen `FileSystem` into a hundred-method trait.** Keep the live
navigation interface small; express capabilities as composable interfaces a
reader opts into. A reader that opts out says so explicitly, and the caller can
read that.

## Consequences

### A matrix row means nothing until a fixture exercises it

The first capability matrix scored ISO 9660 `read_link: yes` over a body that
said *"not surfaced"*. **"Implemented" is not a measurement. "Returns X for
fixture Y" is.** Every row of
[`docs/filesystem-capability-matrix.md`](../filesystem-capability-matrix.md)
must name the fixture that exercises it, or be marked unverified.

This is the same lesson as the xattr corpus: a test whose fixtures cannot
exercise its claim is not evidence about the code.

### Precedents already in the fleet

The rule is not new here; it was applied case by case and never generalised:

- `4n6mount` mount fidelity — the mount declares what its transport drops and
  states that an absence seen through it is **UNKNOWN**, not a finding.
- `zfs-forensic::has_unread_spill_xattrs` — reports when attributes sit in a
  spill block the reader does not follow, so *not recovered* ≠ *none present*.
- `ufs-forensic` / `udf-forensic` xattr decoders — an unrecognised namespace
  index is still LISTED, as `unknown.<n>.<name>`, rather than dropped.

### Staged, not big-bang

1. **Now, binding:** no new reader may return empty for a capability the format
   has. Say `Unsupported` or decode it.
2. **Next:** conformance tests generated from the matrix — for each capability
   the filesystem *has*, assert a real result or an explicit not-implemented,
   never empty.
3. **Then:** the capability/outcome types above, and the `FsMeta` fields the
   model cannot currently express — `rdev` (so `CharDevice` can say *which*),
   ACLs/security descriptors (absent entirely: 0 hits crate-wide), raw reparse
   tag, object id, short name.

### Known defect left deliberately visible

`iso9660-forensic` identifies a node by its data LBA, which extent-less nodes do
not uniquely have: two symlinks in one directory share a `FileId` and report
each other's target — a *wrong* answer, worse than a missing one. Pinned by
`known_defect_extentless_nodes_share_one_file_id`, which fails when identity is
fixed. That is the signal to delete it.
