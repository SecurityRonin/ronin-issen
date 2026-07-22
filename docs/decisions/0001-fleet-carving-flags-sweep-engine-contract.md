# 1. Fleet carving — one flag taxonomy, one sweep engine, one contract (disk unallocated + memory Plane V)

Date: 2026-07-22
Status: Accepted (fleet law; generalises issen ADR 0018 across every carver + medium)
Governs: issen, disk-forensic, forensic-carve (new), memory-forensic, winevt-forensic,
sqlite-forensic, browser-forensic, winreg-forensic, usb-forensic, and every future
`*-forensic` carver.

## Context

Deleted-artifact **carving** exists in the fleet at two cost tiers (issen ADR 0018):
Tier 1 file-internal (O(artifact), default-on) and Tier 2 whole-medium (O(image/dump),
opt-in). The fleet now needs Tier 2 everywhere, and divergence has begun — three
incompatible carve surfaces already exist (`winevt-carver` `CarveConfig`/`CarveResult`,
`sqlite-forensic` `CarvedRecord`, `winevt-memory`/`browser-forensic-memory`
`&[u8]` scanners), and a `RecoveryMethod` enum already lives in `browser-forensic-carve`.
No CLI has a carving flag yet — the flag namespace is a clean slate.

This ADR was designed with an LLM design pass (fable) and an adversarial critic pass
(codex) that verified every load-bearing claim against the trees. Verified facts that
shape the decision: `forensic-vfs::FileSystem::unallocated()` ships across NTFS/FAT/ext4/
XFS/APFS/Btrfs (`forensic-vfs/crates/core/src/fs.rs:341`); the report model lives in the
separately-published `forensicnomicon-core` 1.4.0 (a report-API change is ≥2 package
releases, not "one bump"); `Location`/`FindingContext`/`Finding` are `#[non_exhaustive]`
+ builder-constructed; the `browser-forensic-carve::RecoveryMethod` collision is real
(`browser-forensic/crates/browser-forensic-carve/src/lib.rs:27`); issen's `inventory`
registry decouples consumers from producers but is empty unless the binary force-links
producers (`issen-core/src/plugin/registry.rs`); `memf-core::VirtualAddressSpace` with
`virt_to_phys`/`read_virt`/pagefile exists (`memf-core/src/vas.rs:23`); `memf-windows`
exposes `walk_vad_tree` + `WinProcessInfo` but only coarse `WinVadInfo{protection,
is_private}` — there is **no** rich `VadKind`; `memf-carve` does not yet exist; and there
is **no** Case-001 performance measurement for memory carving.

## Decision

### §1 — The flag taxonomy (fleet-wide, identical in `issen` and every `*4n6` CLI)

Three flags, named by the **observed state**, never the inferred conclusion (see the
fleet glossary §A1/A2 — *name the observable, never the conclusion*):

| Flag | Recovers | Cost | Default |
|---|---|---|---|
| *(none)* | Tier-1 file-internal carving (freelist/WAL/`ElfChnk` slack in located files) | O(artifact) | on |
| `--deleted [latest\|all\|off]` | FS-**recorded** tombstones (`$MFT` cleared `IN_USE`, ext4 orphan) | cheap | off |
| `--unallocated` (alias `--unalloc`) | Tier-2 whole-image unallocated carving | O(image) | off |
| `--residual` | Both of the above — data outside the live file set | both | off |

- `--deleted` means a *recorded* deletion (a tombstone the FS itself flagged) — it is
  **not** a synonym for carving. It is correctly named and unchanged; `ntfs
  deleted_nodes()` and `4n6mount --deleted latest|all|off` are its implementations.
- `--unallocated` names the **allocation observation**, deliberately not `--deleted`
  (asserts intent), not `--non-live` (collides with *live-response / live acquisition*),
  not `--carve`/`--recover` (mechanism; `--recover` collides with ewf `EwfRecover`).
- `--residual` help text is observational: *"all recoverable data outside the live file
  set: filesystem-recorded deletions plus unallocated-space carving."*
- The verbatim `--unallocated` help line: *"Also carve unallocated disk space: whole-image
  scan for artifacts no filesystem references (slower; origin of the data — deleted,
  reformatted, or never referenced — is not determined)."*

### §2 — The sweep engine and the carving contract live in `forensic-carve`, NOT forensicnomicon

A new published crate **`forensic-carve`** owns the *entire* carving execution model:

- The contract: `Carver`, `Signature`, `CarveOptions`, `CarvedItem`, `CarveContext`,
  `CarverRegistration` (+ its `inventory::collect!` point), and `RecoveryMethod` (§3).
- The engine: `sweep(source, regions, carvers, opts) -> Iterator<SweptItem>` — one
  aho-corasick multi-pattern pass over the supplied regions, dispatching windows to the
  matching carver.
- Deps: `forensicnomicon` (magic-byte constants / format identifiers only) + `forensic-vfs`
  (positioned reads + extents). **`forensic-carve` depends on forensicnomicon, never the
  reverse.**

**The `Carver` trait does NOT go in forensicnomicon.** Even with a pure context, a carving
*execution* abstraction violates the KNOWLEDGE leaf's charter ("schemas and invariants,
NO parsing algorithms"). forensicnomicon contributes only the magic-byte constants.

**No forensicnomicon report bump in v1.** Recovery provenance rides *existing* report
types, translated at orchestration: `Evidence { field: "recovery_method", value:
"unallocated-carve" | ... }` + `Location::ByteOffset`/`Other` + a namespaced tag
(`recovery:unallocated`). The typed provenance envelope lives in `forensic-carve`. A typed
`forensicnomicon::report` field is revisited only after **≥2 report consumers query
recovery method structurally** — until then the cross-fleet cascade (≥2 package releases,
~21 dependents) is unjustified.

Each format's `Carver` impl lives in **its own PARSER crate** and sees only `&[u8]`
windows — medium-agnostic by construction, so the same carver serves disk and memory.

### §3 — `RecoveryMethod` vocabulary (carving *is* a recovery method)

`forensic_carve::RecoveryMethod` is the fleet-level provenance vocabulary — the general
concept owns the plain name:

```
RecoveryMethod { Tombstone, FileInternalCarve, UnallocatedCarve, MemoryCarve }
```

It maps 1:1 to §1 (`Tombstone`→`--deleted`, `FileInternalCarve`→default Tier-1,
`UnallocatedCarve`→`--unallocated`, `MemoryCarve`→memory leg) and even absorbs the
non-carving tombstone case, which an "origin"-flavoured name could not.

The existing narrower `browser-forensic-carve::RecoveryMethod` (`FreePage`,
`WalUncommitted`, `JournalRollback`, `DirectScan`) is a SQLite-record *substrate* detail
**under** `FileInternalCarve`, not a peer of the fleet enum. Rename it to
`SqliteRecoveryMethod` with a `#[deprecated] pub type RecoveryMethod = SqliteRecoveryMethod;`
alias for source compatibility. (Never a second fleet-level `RecoveryMethod`; never
`RecoveryOrigin`/`AcquisitionMethod` — "acquisition" means evidence imaging.)

### §4 — Disk Tier-2: `unallocated()` regions, detection ≠ materialization, recursion guard

- Regions come from the already-shipped `forensic-vfs::FileSystem::unallocated()`; volume
  slack / inter-partition gaps are computed engine-side (no forensic-vfs change).
- **Detection is separate from materialization** (the correctness crux). Signature overlap
  (`longest_signature − 1`) guarantees a magic spanning a scan-chunk boundary is *found*;
  it does **not** guarantee a large artifact receives its trailing bytes. So: scan for the
  signature → convert to an absolute source offset → ask the region source for the
  carver-declared bounded window / incremental `NeedMore { minimum_end }` up to a hard
  global cap → **explicitly mark truncation** when the cap or region prevents completeness.
- Distinguish **contiguous file carving** (a whole orphaned DB in contiguous unallocated
  extents → `ArtifactBytes`) from **page/record carving** (fragmented FS extents cannot be
  reassembled from one contiguous window → `Records`).
- `ArtifactBytes` re-enter issen's classify→parse pipeline so a recovered file gets full
  analyzer depth. **Recursion guard:** carry `InputStage::CarvedArtifact` and disable
  Tier-2 source scanning for derived artifacts (parsers still do their own file-internal
  recovery). Note issen `classify.rs` is path-based today (opens via `std::fs::File`);
  byte-native re-entry is a prerequisite work item, not assumed here.

### §5 — Memory carving: Plane V only for v1, opt-in until measured

A new `memory-forensic` member **`memf-carve`** owns memory region enumeration + the
sweep driver + attribution stamping, and holds **zero** format knowledge (carvers arrive
via the `forensic-carve` inventory registry; §8). v1 ships **Plane V only**:

- **Plane V = carving where a page-table root exists.** Detection and materialization run
  in **virtual order** via `memf-core::read_virt`, which un-scatters physically-discontiguous
  frames into the process's contiguous virtual stream. This is valid for **live processes**
  *and* **recently-terminated** processes reached by carving the freed `EPROCESS` →
  reading its `DirBase` → walking still-resident page tables. It recovers deleted data
  still resident in a live address space (freed-but-unreused heap, cached deleted rows,
  closed-file buffers).
- **`read_virt` requires a page-table root.** For truly-orphaned pages of a long-dead
  process whose page tables have been reused, there is **no map to walk** — that case is
  Plane P (§6), explicitly deferred. v1 must not claim `read_virt` reaches dead-process
  memory.
- **Materialize around the hit**, never eager 64 MB per VAD: a cheap virtual-order
  detection pass (signature-length carry-over across page boundaries so a straddling magic
  is caught), record hit VA/PFN, then materialize *only* the carver-declared window per
  hit. (Eager materialization = ~512 MB of buffers across 8 workers, and splitting resident
  runs at a gap loses a header-in-run-1/body-in-run-3 artifact.)
- **Gaps** (non-resident pages inside a window) → mark truncation + a recovered-extent map;
  **never zero-fill** (fabricates bytes a validator would trust). Pagefile gap-fill is
  deferred (§6).
- **Coarse attribution only.** The tree exposes `WinProcessInfo` (PID/name/`DirBase`/
  `_EPROCESS` VA) + `WinVadInfo` (protection/`is_private`) — **not** Heap/Stack/MappedFile
  kinds. v1 stamps PID/process/protection/private-vs-shared/physical-offset; richer
  `VadKind` is a separately-reviewed decoder, deferred.
- **Opt-in until measured.** Per-process VA scanning is not proven cheaper than a whole-dump
  scan (page-table walks + scattered reads; the union of resident mapped frames can approach
  all of RAM). Keep memory carving **opt-in**; build the Plane-V benchmark, measure on the
  four Case-001 dumps **plus** one high-memory workstation dump, and **flip the default to
  on only if it stays within ~25% of the memory leg's baseline wall-clock** — default by
  evidence, not assertion.

### §6 — Memory Plane P and the residual-memory universe (deferred, opt-in `--residual`)

Plane P scans **host** memory *beyond* live process working sets. Deferred from v1; when
built it is the memory arm of `--residual`. Its sources (all the **same machine**):

- **In-dump:** unmapped physical frames · standby/modified page lists · unattributed
  kernel pool · the Win10+ compressed store (`MemCompression`, Xpress-Huffman — decode via
  the fleet `xpress-huffman` crate).
- **On-disk companion (reached through the disk/NTFS path):** `pagefile.sys` ·
  `swapfile.sys` · `hiberfil.sys` (a full RAM snapshot, Xpress-Huffman; `memf-format`
  already reads it) · crash dumps (`MEMORY.DMP`, minidumps).

Honesty constraints for Plane P (no page tables for orphaned pages):
- **Sub-page / self-framing records recover reliably** (one EVTX record, SQLite cell, hive
  cell).
- **Multi-page artifacts recover only by per-format content-reassembly** (SQLite page
  numbers, NTFS sequence/VCN, EVTX record offsets order scattered frames) — heuristic,
  best-effort, and stamped with **lower confidence** than a Plane-V reassembly.
- `hiberfil.sys`/crash dumps are a **different point in time** (`[M^H]` host history) —
  their carved items stamp *which* image and *which* time; never conflated with the live
  dump's timeline.

Also deferred with Plane P: the PFN coverage bitmap, pagefile gap-fill for Plane V,
elaborate extent maps, shared-frame multi-attribution, and any hard-coded confidence floor
(calibrate on real dumps first).

### §7 — VM guest memory is a separate `[M]` source, not host Plane P

VMware `.vmem`/`.vmss`/`.vmsn`, Hyper-V `.vmrs`/`.bin`, VirtualBox `.sav` are a **different
machine's** RAM — their own address spaces, processes, and clock. They are **not** folded
into the host's Plane P. issen discovers them during disk triage and registers each as its
**own** `[M]` evidence source, running the full pipeline against it with **guest-scoped**
attribution and the guest's timeline (the same seam as multi-host ingest). Flat `.vmem` is
often raw and directly consumable; state-file variants need `memf-format` decoders — a
separate work item.

### §8 — The cross-medium contract (one carver, both media)

- `carve(&self, window: &[u8], ctx: &CarveContext) -> CarveResult` — `CarveContext` carries
  **plain values only** (absolute base offset, truncation state, confidence policy, labels);
  **never** `Read`/`Seek`, a VFS handle, or a memory provider. A carver that must chase
  virtual pointers is a memory *walker* and belongs in `memf-windows`, not a carver.
- `sweep` yields `SweptItem<R> { region: R, offset, item: CarvedItem }` — `CarvedItem`
  stays **medium-neutral**; PID/VA/PFN (memory) and volume/run ids (disk) are attribution
  the *driver* wraps *after* the call. No memory fields on `CarvedItem`.
- Confidence is a policy, not a hard engine floor: `confidence_policy: KeepAll |
  Minimum(Confidence)`; items lacking confidence are retained unless configured otherwise;
  medium defaults live in the drivers.
- `forensic-carve` owns **both** detection overlap **and** hit-window materialization/
  truncation (not per-driver).
- **`forensic-carve` publishes only after a shared conformance test proves the same
  registered carver runs unchanged over a disk (unallocated) adapter and a memory (VAD)
  adapter.** A second consumer that merely calls the same parser does not count.

### §9 — Provenance & attribution (technical attribution only)

Every carved item is provenance-tagged (`RecoveryMethod`, absolute offset, confidence) so
machine output round-trips it and an analyst can filter carved from live evidence — a
carved record indistinguishable from a live one is a fabrication hazard. Memory items add
PID/process/region/physical-offset and, for `[M^H]` sources, the point-in-time. **Per the
FACT framework (glossary §A2) this is *technical* attribution only** — artifact→device/
account/session, never person-level (investigative/legal) attribution.

### §10 — Fleet-law vs per-repo split

**Bound fleet-wide (this ADR):** the flag taxonomy + verbatim help/cost text (§1); the
`forensic-carve` home for the contract + engine and the no-fn-bump rule (§2); the
`RecoveryMethod` vocabulary + browser rename (§3); detection≠materialization + the
recursion guard (§4); Plane-V-only/opt-in-until-measured + the page-table-root scope (§5);
the deferral of Plane P/pagefile/floor (§6); VM-as-separate-source (§7); the cross-medium
contract + conformance gate (§8); technical-attribution-only tagging (§9).

**Per-repo (each owner implements):** its `Carver` impl(s) (magic + validation + confidence);
its native result types + edge conversion; its CLI wiring of the flags; its fuzz targets.

## Rejected alternatives

- **`Carver` trait in forensicnomicon** — violates the KNOWLEDGE-leaf "no parsing
  algorithms" charter; drags an execution abstraction into the zero-I/O leaf. → §2.
- **A `forensicnomicon::report::RecoveryMethod` + `FindingContext.recovery` bump** —
  ≥2-package cascade to ~21 dependents for provenance no consumer yet queries structurally;
  ride existing `Evidence`/`Location`/tags instead. → §2.
- **`RecoveryOrigin`/`AcquisitionMethod` for the fleet concept** — carving *is* a recovery
  method; the general concept owns the plain `RecoveryMethod`; "acquisition" means imaging. → §3.
- **Per-parser independent whole-medium scans** — N× O(image/dump); N container stacks in
  PARSER crates. → the single sweep, §2.
- **Signature overlap alone** for window completeness — finds the magic, truncates the
  artifact. → detection≠materialization, §4.
- **Eager per-VAD materialization** — ~512 MB of buffers; splitting resident runs loses
  cross-gap artifacts. → materialize-around-hit, §5.
- **`read_virt` over dead-process memory** — no page-table root once tables are reused;
  claiming it returns garbage. → Plane P sub-page/content-reassembly, §5/§6.
- **Zero-filling memory gaps** — fabricates bytes a validator trusts. → truncation + extent
  map, §5.
- **VM guest memory as host Plane P** — a different machine's address space/clock; would
  misattribute guest PIDs to the host. → separate `[M]` source, §7.
- **A hard-coded confidence floor (0.7)** before calibration — fake precision. →
  `confidence_policy`, calibrate later, §6/§8.
- **`memf-carve` depending on parser crates** — inverts the dependency; inventory +
  binary force-link decouples it. → §8.

## Consequences

- One flag story, one help text, one cost disclosure across `issen`/`usb4n6`/`ev4n6`/
  `sqlite4n6`; O(image/dump) paid once per source however many formats are hunted.
- **No forensicnomicon bump for v1** — the fleet does not converge for this feature.
- Two new publish surfaces: `forensic-carve` (full pre-publish gate) and, later, the
  `memf-carve` capability. A shared conformance suite gates `forensic-carve`'s publish.
- `browser-forensic-carve` takes a non-breaking rename (deprecated alias).
- Memory carving is opt-in until a real measurement flips it; Plane P and the residual-file
  universe are a deliberate, evidence-gated second phase.
- Truncated carves become a normal, visible output class (recovered-extent maps) that report
  rendering must present honestly.

## Migration path (TDD: RED then GREEN commit per step)

1. **`forensic-carve`** (new): contract (`Carver`/`Signature`/`CarveOptions`/`CarvedItem`/
   `CarveContext`/`CarverRegistration`/`RecoveryMethod`) + `sweep` (aho-corasick + detection/
   materialization split + overlap + truncation) + `confidence_policy`. Fuzz the chunk/window
   logic. Publish **only after** the shared disk+memory conformance test passes.
2. **`browser-forensic-carve`**: rename `RecoveryMethod` → `SqliteRecoveryMethod` + deprecated
   alias.
3. **Disk carvers** (`sqlite-forensic`, `winevt-carver`, `winreg-forensic` hive `regf`/`hbin`,
   later lnk/prefetch): implement `Carver`; keep native result types, convert at the edge;
   deprecate `winevt-carver::carve_from_ewf` (container knowledge in a PARSER crate).
4. **`memory-forensic` → `memf-carve`** (new member): `RegionProvider` over `walk_vad_tree`/
   `WinProcessInfo` → virtual-order detection (overlap) → around-hit materialization via
   `read_virt` → coarse attribution. Recently-dead via carved `EPROCESS`→`DirBase`. Plane V
   only. Tier-1 validation on the Case-001 memory dumps, oracle = Volatility 3 `filescan`/
   `dumpfiles`.
5. **`issen`**: `CarverSelector` inventory registry beside `ArtifactSelector`, force-linked via
   `crates/issen-parsers`; wire `--deleted`/`--unallocated`/`--unalloc`/`--residual`; one
   `sweep` per source; `ArtifactBytes` re-enter classify with the recursion guard; stamp
   provenance into `TimelineEvent`/DuckDB. VM-image discovery registers guest `[M]` sources.
6. **Measurement gate** (§5): benchmark memory Plane V on Case-001 + a high-memory dump; flip
   the default only if within ~25% baseline.
7. **Deferred phase** (own ADR when scheduled): Plane P + residual-file sources (§6), pagefile
   gap-fill, PFN bitmap, `VadKind` decoder, VM `memf-format` decoders, content-reassembly.

## Open questions

1. `forensic-carve` crate name — confirm within the crates.io 72-hour rename window.
2. Confidence calibration — disk vs memory floors, measured on Case-001 + a noise corpus.
3. Byte-native issen classification (prerequisite for `ArtifactBytes` re-entry, §4).
4. Content-reassembly heuristics per format (Plane P multi-page recovery, §6).

## References

- issen ADR 0018 — carving tiers (file-level default / whole-disk opt-in); this ADR is its
  fleet generalisation. Add a forward reference there.
- Fleet glossary (`docs/glossary.md`) §A1 epistemology, §A2 FACT attribution, §A3/§A4
  recovery vocabulary + tier test, §B1 the flag taxonomy.
