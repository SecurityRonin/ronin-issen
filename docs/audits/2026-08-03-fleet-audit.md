# Ronin–Issen Fleet Audit Report

**Assessment date:** 2026-08-03  
**Scope:** 86 canonical repositories in the Ronin–Issen forensic Rust fleet  
**Mode:** read-only static architecture, security, parser-robustness, product, release, packaging, and documentation audit  
**Snapshot:** repository heads and inventory recorded under `/home/selene/work/ronin-issen-fleet-audit/`

## Executive synthesis

The fleet has substantial engineering depth and many strong individual readers, analyzers, foundations, and quality controls. It is not yet one coherent, reproducible, truthfully documented end-to-end forensic product.

The dominant risk is **integration truthfulness**: repository existence, dependency declaration, compilation, registration, runtime invocation, persistence, user-visible reporting, and end-to-end test coverage are too often treated as equivalent. They are not.

Highest-priority actions are:

1. Fix Issen evidence and feed resume fingerprints so stale results cannot be silently reused.
2. Repair the unresolved and unwired USB path, and make capability claims depend on demonstrated end-to-end invocation.
3. Converge the parallel VFS/container paths and duplicate state-history contracts into one supported product route.
4. Fix confirmed hostile-input defects in AFF4, ZIP, raw NTFS `$MFT`, and QCOW2 error handling.
5. Make unsupported, failed, partial, and searched-absent outcomes distinct throughout the fleet.
6. Align the public CLI, quickstarts, output-format claims, install story, release assets, checksums, and MSRV with current source truth.
7. Enforce fleet-wide fuzz execution, line-coverage, corpus provenance, action pinning, cargo-vet, secret scanning, and release-integrity gates.

## Report structure

- **Part I — Mechanical inventory**
- **Part II — Architecture and end-to-end integration audit**
- **Part III — Security, parser robustness, and quality-gate audit**
- **Part IV — Product, release, packaging, documentation, and consumability audit**

## Validation limitation

The audit host did not have `cargo` installed. Manifest parsing and direct source/path/caller analysis were completed, but this report does not claim a fresh fleet-wide compile or test pass. Each workstream distinguishes confirmed static defects from runtime-validation hypotheses.

---
# Part I — Mechanical inventory

# Ronin-Issen Fleet Mechanical Inventory

Canonical repos: 86
Present: 86
Missing: 0

- cargo_lock: 86/86
- cargo_vet: 84/86
- changelog: 43/86
- deny_toml: 86/86
- deny_unsafe: 2/86
- forbid_unsafe: 41/86
- has_fuzz_targets: 72/86
- has_rust_tests: 86/86
- has_unpinned_actions: 77/86
- has_workflows: 86/86
- license: 85/86
- readme: 86/86
- release_plz: 81/86
- test_data_readme: 48/86


---

# Part II — Architecture and end-to-end integration

# Ronin–Issen Fleet Architecture Audit

**Scope:** all 86 canonical repositories in `inventory.json` (358 Cargo packages parsed by the dependency scanner; inventory records 361 package manifests including excluded/non-workspace packages; 414 cross-repository Cargo edges).  
**Snapshot:** repository heads recorded in `/home/selene/work/ronin-issen-fleet-audit/inventory.json`.  
**Assessment mode:** read-only static architecture and source audit. No repositories were modified.  
**Normative baseline:** umbrella `CLAUDE.md`, `README.md`, glossary, ADR-0006 (dependency/release order), ADR-0007 (normalized reports), ADR-0008 (reader/analyzer split), ADR-0011 (universal VFS), and ADR-0016 (multi-repo layers).

## Executive verdict

The fleet has strong *local* foundations—panic-resistant readers, a useful five-primitive `FileSystem` trait, normalized reporting in `disk-forensic`, and a real multi-layer VFS engine—but the claimed *fleet-wide* architecture is not yet true at the main product boundary.

The most consequential gaps are:

1. the canonical `issen` snapshot cannot resolve its in-workspace USB dependency;
2. the USB bridge itself is not called by any orchestration path;
3. neither `issen` nor `disk-forensic` uses `forensic-vfs-engine`, so the universal VFS is effectively a separate `4n6mount` product path;
4. state-history has two incompatible copies of the contract and no `HistoricalSource` implementation anywhere in the fleet;
5. several foundational APIs and high-value parser/memory paths collapse “unsupported”, “failed”, and “searched but absent” into the same empty success;
6. Issen resume keys can silently reuse stale disk, memory, and feed-derived results;
7. published capabilities remain dark or shallow (BAM, journald, LevelDB/IndexedDB, offline DPAPI, browser recovery, EVTX integrity/memory, and others already acknowledged by Issen’s own inventory).

The canonical dependency direction is mostly respected at the crate level. The major failure is not widespread reverse edges; it is **parallel architecture islands**: direct `Read+Seek` stacks, optional VFS adapters on multiple incompatible 0.x interfaces, the VFS engine, Issen’s own provider stack, and duplicate history/report models are all individually plausible but do not compose into one supported end-to-end route.

## Method and fleet coverage

I inspected every repository’s actual Cargo manifests (not only README claims), built a package/dependency map, and searched the Rust sources for:

- cross-fleet normal/dev/build dependencies and path dependencies;
- reader/analyzer/container/orchestrator role boundaries;
- `forensic-vfs`, `forensic-vfs-engine`, `forensicnomicon`, and `state-history-forensic` adoption;
- parser registration, force-linking, discovery, dispatch, and CLI reachability;
- `Ok(Vec::new())`, `unwrap_or_default()`, and analogous silent fallbacks;
- custom `Finding`/`Report` types and evidentiary assertion language;
- Issen pipeline state, fingerprints, classification, ingest, memory, correlation, scan, and USB seams;
- `disk-forensic` container opening, scheme dispatch, normalization, and VFS use.

The scanner covered these 86 canonical repositories:

`forensic-hashdb`, `forensicnomicon`, `blazehash`, `forensic-carve`, `jsonguard`, `name-variants`, `safe-read`, `shrinkpath`, `timeglyph`, `lzo`, `lzvn`, `xpress-huffman`, `ad1-forensic`, `aff4-forensic`, `dmg-forensic`, `ewf-forensic`, `qcow2-forensic`, `vhd-forensic`, `vhdx-forensic`, `vmdk-forensic`, `livedisk-forensic`, `archive-forensic`, `dar-forensic`, `zip-forensic`, `apm-partition-forensic`, `gpt-partition-forensic`, `mbr-partition-forensic`, `bitlocker-forensic`, `dpapi-forensic`, `elephant-diffuser`, `filevault-forensic`, `luks-forensic`, `veracrypt-forensic`, `4n6mount`, `apfs-forensic`, `btrfs-forensic`, `ext4fs-forensic`, `fat-forensic`, `forensic-vfs`, `forensic-vfs-engine`, `forensic-vfs-mount`, `hfsplus-forensic`, `iso9660-forensic`, `ntfs-forensic`, `refs-forensic`, `udf-forensic`, `ufs-forensic`, `xfs-forensic`, `zfs-forensic`, `memory-forensic`, `journald-forensic`, `winevt-forensic`, `amcache-forensic`, `atx-forensic`, `bam-forensic`, `blob-decoder`, `bluetooth-forensic`, `browser-forensic`, `cfb-forensic`, `ese-forensic`, `exec-pe-forensic`, `leveldb-forensic`, `lnk-forensic`, `peripheral-forensic`, `prefetch-forensic`, `protobuf-forensic`, `segb-forensic`, `shellhist-forensic`, `shellitem`, `shimcache-forensic`, `snss-forensic`, `sqlite-forensic`, `srum-forensic`, `trash-forensic`, `usb-forensic`, `userassist-forensic`, `winreg-forensic`, `git-forensic`, `snapshot-forensic`, `state-history-forensic`, `vsc-forensic`, `disk-forensic`, `issen`, `useract-forensic`, `ewf`, and `usnjrnl-forensic`.

### Validation limitation

`cargo` is not installed in the audit host (`FileNotFoundError: cargo` when attempting all-repository `cargo metadata --no-deps`), so this report does not claim a successful compile/test pass. TOML parsing succeeded for all inventory entries (`cargo_parse_errors = 0`), and filesystem/path reachability was checked directly. Findings that still require compilation or runtime evidence are explicitly labeled hypotheses.

## Canonical-law matrix

| Canonical law | Result | Evidence summary |
|---|---|---|
| Container → foundation → parser → orchestration direction | **Partial pass** | Most core readers depend only on foundations/knowledge. Orchestrators legitimately depend downward. However, multiple parallel container/VFS generations and duplicate EWF/history contracts prevent one coherent stack. |
| Parser medium-agnosticism | **Mostly pass for Issen plugins** | `ForensicParser::parse` receives `&dyn DataSource`; representative MFT, registry, shellbags, prefetch paths consume bytes rather than opening E01 themselves. Standalone CLI/orchestrator repos still own direct EWF/NTFS paths, which is appropriate only when clearly orchestration. |
| Reader/analyzer split | **Partial** | Many format repos follow `*-core` + `*-forensic`; exceptions remain (`atx-forensic`, `snss-forensic`, `ext4fs-forensic` have reader/core without analyzer; HFS+/ISO/UDF combine roles). |
| Universal VFS abstraction | **Fail at product integration** | The five primitives exist and many adapters exist, but `forensic-vfs-engine` has only one production consumer (`4n6mount`); Issen and `disk-forensic` use separate direct stacks. |
| Normalized forensicnomicon reporting | **Partial** | `disk-forensic/src/normalize.rs` is exemplary. Issen scan converts canonical findings into a lossy `FindingRow`; Issen correlation defines independent `Finding` and `Correlation` models. |
| Observed fact vs inference vs conclusion | **Partial** | Issen has `Observed/Correlated/Inferred` in one custom model and carefully says “consistent with” in another, but the distinction is not preserved through a single canonical persisted report schema. Several memory paths explicitly conflate absence with unavailable symbols/errors. |
| Five navigation primitives + state-history | **Five primitives pass; history fail** | `read_dir`, `lookup`, `meta`, `read_at`, and `extents` are required in `forensic-vfs::FileSystem`; forensic extensions default-empty. State-history has no fleet implementation and is duplicated in forensicnomicon. |
| Release/dependency ordering | **Fail for current integration head** | `peripheral-core` unpublished change → `usb-forensic` path dependency → Issen path dependency is an unfinished chain, and Issen’s relative path does not exist in the canonical snapshot layout. |

# Blocking findings

## B1 — Issen’s canonical workspace has an unresolved USB path dependency

- **Severity:** Critical
- **Classification:** Confirmed defect / release blocker
- **Repo:** `issen`
- **Exact evidence:**
  - `issen/Cargo.toml:3-6` includes `crates/issen-usb` as a workspace member.
  - `issen/crates/issen-usb/Cargo.toml:17-19` declares `usb-forensic = { version = "0.2", path = "../../../../parser/usb-forensic" }` and calls it unpublished.
  - Direct filesystem validation from `issen/crates/issen-usb` found that target absent (`test -e .../../../../../parser/usb-forensic/Cargo.toml` returned false). The canonical USB repository is instead at `repos/usb-forensic`.
- **Impact:** The canonical flat 86-repository snapshot cannot resolve the Issen workspace before compilation. CI/release behavior depends on a different umbrella directory topology not represented by the canonical fleet artifact. This also makes the product build non-reproducible from the declared fleet snapshot.
- **Concrete remediation:** Publish `usb-forensic` 0.2 and replace the path with a registry-only dependency, or define a documented Cargo patch/umbrella workspace generated as part of snapshot checkout. Add a clean-clone CI job that materializes exactly `inventory.json`’s flat layout and runs `cargo metadata --locked`, `cargo check --workspace`, and `cargo test --workspace`.

## B2 — The USB integration seam is orphan code, not an end-to-end capability

- **Severity:** High
- **Classification:** Confirmed defect / parser-present-but-not-wired
- **Repo:** `issen`
- **Exact evidence:**
  - `issen/crates/issen-usb/src/lib.rs:3-13` claims the artifact-locating seam and report routing are “wired by the correlation-stage caller”.
  - `issen/crates/issen-usb/src/lib.rs:44-63` implements only the event type conversion.
  - Fleet source search for `issen_usb::`, `usb_forensic::audit`, `HistorySources`, or non-test calls to `to_issen_event` found **no caller outside this crate**; the only `to_issen_event` uses are its own tests (`:83`, `:90`, `:97`, `:106`).
  - `issen/crates/issen-cli/Cargo.toml:26-86` does not depend on `issen-usb`; `issen-correlation` does not call it either.
- **Impact:** SetupAPI/registry/LNK/EVTX data may enter the timeline, but the advertised cross-source USB history/audit is never executed and canonical USB findings are never persisted. The dependency/build bridge adds risk without delivering capability.
- **Concrete remediation:** Make `issen-correlation` or `issen-cli` explicitly depend on `issen-usb`; implement the locator-to-`HistorySources` adapter; call `usb_forensic::audit`; convert both timeline events and canonical findings; persist them; add an end-to-end fixture that starts from SetupAPI + SYSTEM hive + LNK + EVTX and asserts a USB finding in the case DB.

## B3 — The “universal VFS” is not the Issen/disk product path

- **Severity:** High
- **Classification:** Architecture risk / missing end-to-end capability
- **Repos:** `issen`, `disk-forensic`, `forensic-vfs-engine`
- **Exact evidence:**
  - `forensic-vfs-engine/Cargo.toml:32-102` compiles the batteries-included container, volume, filesystem, archive, logical-container, and encryption stack.
  - Fleet manifest search for `forensic-vfs-engine` found only its own fuzz harness and `4n6mount/Cargo.toml:48` as consumers.
  - `disk-forensic/Cargo.toml:14-55` directly depends on archive/EWF/VMDK/QCOW2/VHDX/DMG/AFF4/AD1/DAR and has **no** `forensic-vfs` or `forensic-vfs-engine` dependency.
  - `disk-forensic/src/lib.rs:8-17` describes its independent `Read + Seek` container/scheme path.
  - `issen/crates/issen-cli/Cargo.toml:39-45,63-70` depends on `issen-disk`, `issen-unpack`, and bespoke provider crates; `forensic-vfs` appears only as a dev-dependency at `:91-95`.
- **Impact:** A format working through `Vfs::open`/`4n6mount` does not imply it works through `issen` or `disk4n6`. Fixes and support matrices can diverge. Deep navigation, encryption, logical containers, snapshots, and unsupported/error semantics are inconsistent across the three front doors.
- **Concrete remediation:** Choose one production resolver. Prefer making `forensic-vfs-engine` the single evidence-opening dependency beneath both Issen ingest and `disk-forensic`; keep format analyzers injected above its `dyn FileSystem`/`ImageSource`. Gate releases on the same end-to-end corpus through `4n6mount`, `disk4n6`, and `issen`, asserting identical layer locators and file bytes.

## B4 — State-history has duplicate incompatible contracts and no implementation

- **Severity:** High
- **Classification:** Confirmed architecture defect / missing capability
- **Repos:** `state-history-forensic`, `forensicnomicon`, `forensic-vfs-engine`
- **Exact evidence:**
  - `state-history-forensic/src/source.rs:47-70` defines `HistoricalSource`.
  - `forensicnomicon/src/history/source.rs:50-64` independently defines the same named trait and associated contract; `forensicnomicon/src/lib.rs:185` publicly exports that duplicate history module.
  - Fleet source search for `impl HistoricalSource` / `HistoricalSource for` returned **zero** implementations.
  - `forensic-vfs-engine/src/lib.rs:209-218` says APFS returns a bespoke `Vec<SnapshotView>` and that generic `HistoricalSource` wiring “lands” later.
  - `forensic-vfs-engine/src/lib.rs:223-239` implements APFS-only `snapshots`, while `:254-285` implements a separate APFS `open_snapshot` API.
- **Impact:** The `[H]` law is declarative, not operational. The two traits are distinct Rust types and cannot interoperate. VSS, SQLite WAL, ESE, Git, journald epochs, memory snapshots, and APFS snapshots cannot share one state-history consumer; even APFS bypasses the declared trait.
- **Concrete remediation:** Select `state-history-forensic` as the sole contract; remove/re-export (do not copy) forensicnomicon’s history types; implement `HistoricalSource` and `StateMaterializer` first for APFS using existing code; then VSS/WAL/Git/journald. Add compile-time cross-crate conformance tests and one history-aware orchestration command.

## B5 — Foundational VFS forensic APIs encode unsupported as clean empty

- **Severity:** High
- **Classification:** Confirmed architecture defect (unsupported-vs-negative ambiguity)
- **Repo:** `forensic-vfs`
- **Exact evidence:** `forensic-vfs/crates/core/src/fs.rs`:
  - `:370-373` default `data_streams` → `Ok(Vec::new())`;
  - `:375-378` default `hardlinks` → `Ok(Vec::new())`;
  - `:383-390` documents unsupported identity recovery but returns an empty deleted stream;
  - `:395-398` default `slack` → `Ok(None)`;
  - `:400-405` default `findings` → `Ok(Vec::new())`.
- **Impact:** Consumers cannot tell “the filesystem was searched and none exist” from “this reader does not implement the capability.” Coverage reports and courtroom claims can therefore overstate negative evidence. This ambiguity propagates to every adapter.
- **Concrete remediation:** Introduce an explicit capability descriptor plus tri-state result (`Supported(value)`, `Unsupported(reason)`, `Failed(error)`), or require methods and let each implementation return `VfsError::Unsupported`. Preserve “supported and empty” as a distinct value. Update the engine’s coverage manifest and CLI rendering before adding more adapters.

## B6 — Issen resume fingerprints can accept stale evidence and stale feeds

- **Severity:** High
- **Classification:** Confirmed defect
- **Repo:** `issen`
- **Exact evidence:**
  - `issen/crates/issen-cli/src/pipeline.rs:154-162` hashes disk evidence using only path + byte length.
  - `issen/crates/issen-cli/src/pipeline.rs:179-184` does the same for memory dumps.
  - `issen/crates/issen-cli/src/commands/pipeline_run.rs:39-44` hard-codes the feed snapshot to `"v0"` and says `--rerun` is required after feed updates.
  - `issen/crates/issen-cli/src/commands/pipeline_run.rs:249-267` uses these values as the persisted stage keys.
- **Impact:** Replacing evidence bytes while preserving path and size silently skips disk/memory processing. Updating threat-intel feeds silently skips scan. The case DB may report “up to date” for results produced from different evidence/content, undermining reproducibility and chain-of-custody.
- **Concrete remediation:** Fingerprint evidence with acquisition SHA-256 (or a documented immutable evidence ID including hash); fingerprint feed files by content/manifest digest; include parser/provider/rule binary versions and feature set. Store the full inputs in `run_manifest`, invalidate downstream stages transitively, and test same-size content replacement plus feed update.

## B7 — Non-ZIP memory archives are routed to the disk leg despite content-routing claims

- **Severity:** High
- **Classification:** Confirmed defect / missing end-to-end path
- **Repo:** `issen`
- **Exact evidence:**
  - `issen/crates/issen-cli/src/commands/pipeline_run.rs:46-60` claims a directory or archive is classified by what it holds and that a zipped `.mem` reaches memory.
  - `:99-108` recognizes ZIP, 7z, tar, gz/tgz, bz2/tbz2, xz/txz, and zst as archives.
  - `:111-124` explicitly peeks **only ZIP** and returns `None` for every other archive.
  - `:75-81` defaults unreadable/peekless archives to the extension-derived disk route.
  - `issen/crates/issen-cli/src/pipeline.rs:217-225` classifies all archive extensions as disk.
- **Impact:** A `.tar.gz`, `.7z`, `.xz`, or `.zst` containing a memory dump is sent to disk ingest, which can complete with “no disk artifacts,” rather than memory analysis. The front-door behavior contradicts its documented content-based contract.
- **Concrete remediation:** Use the existing safe archive layer to enumerate all supported archive formats, classify each member, and extract memory members with bomb/path/symlink caps. Add end-to-end tests for `.tar.gz`, `.7z`, and `.zst` memory bundles and mixed disk+memory archives; reject ambiguous mixes or process both explicitly.

## B8 — Remote ingest is a successful no-op

- **Severity:** High
- **Classification:** Confirmed defect / missing capability
- **Repo:** `issen`
- **Exact evidence:** `issen/crates/issen-cli/src/commands/ingest.rs:62-89` accepts recognized remote URIs, prints that GDrive/OpenDAL fetch “is a stub”, then returns `Ok(())` without downloading, parsing, creating coverage, or persisting events.
- **Impact:** Automation sees exit status 0 for an ingest that ingested nothing. This is silent-empty behavior at the highest-level evidence boundary and can be mistaken for completed acquisition/analysis.
- **Concrete remediation:** Until implemented, return an explicit `Unsupported` error and non-zero exit status. When implemented, stream to an immutable hashed temporary/source object, register provenance, run normal ingest, and emit coverage. Add one mock-object-store end-to-end test per URI adapter.

## B9 — Shellbags maps unreadable/corrupt input to “no artifacts”

- **Severity:** High
- **Classification:** Confirmed defect (silent-empty and unsupported-vs-negative ambiguity)
- **Repo:** `issen`
- **Exact evidence:**
  - `issen/crates/parsers/issen-parser-shellbags/src/lib.rs:35-45` explicitly promises `Ok(vec![])` for corrupt, empty, or non-shellbag hives; read errors and empty files take the same return.
  - `:56-59` maps `Hive::from_bytes` failure to empty.
  - `:135-139` maps zero-length plugin input to a successful zero-event `ParseStats`.
  - Tests at `:221-243` require nonexistent and empty files to return successful empty results.
- **Impact:** Missing file, permission/read error, malformed hive, unsupported hive, a valid hive without BagMRU, and a valid empty BagMRU are observationally equivalent. A coverage manifest can incorrectly imply the hive was successfully searched.
- **Concrete remediation:** Return an error for I/O/decode failures; return a structured `ParseOutcome::{Parsed(events), Unsupported(reason), SearchedAbsent}` for valid hives. Ensure `ParseCompletion::marks_complete` is false on decode failure and add corrupt-vs-clean-negative fixtures.

## B10 — Memory dispatch conflates failed/unsupported analysis with negative findings

- **Severity:** High
- **Classification:** Confirmed defect / evidentiary ambiguity
- **Repos:** `issen`, `memory-forensic`
- **Exact evidence:** `issen/crates/issen-mem/src/dispatch.rs`:
  - `:547-552` documents that Linux credential dispatch never returns `Err`;
  - `:587` converts process-walker failure with `unwrap_or_default()`;
  - `:639-645` inserts the single row “no credential artifacts found (or symbols unavailable)”;
  - `:1211-1215` likewise documents Windows credential dispatch never errors;
  - `:1242` defaults hive enumeration on error;
  - `:1260-1265` drops all hashdump errors/empty candidates into a default empty vector;
  - `:1277-1282` emits “no credential artifacts found (or symbols unavailable)”;
  - `:1293-1325` repeats the pattern for Linux security/capabilities.
- **Impact:** A report cannot distinguish a supported search that found no secrets/capabilities from missing symbols, profile mismatch, walker error, or unsupported kernel/version. Worse, the fallback is emitted as a normal row and can be ingested as an event, overstating negative evidence.
- **Concrete remediation:** Preserve per-walker `CoverageStatus` and errors; never manufacture “no findings” rows. Return structured results with `searched`, `unsupported`, `failed`, and `found` counts; persist coverage separately from observations; only render a clean negative when all mandatory walkers completed successfully.

## B11 — Issen has a dark BAM enum and a wider acknowledged dark/shallow fleet

- **Severity:** High
- **Classification:** Confirmed missing capability / orphan API
- **Repo:** `issen` (with fleet parsers named below)
- **Exact evidence:**
  - `issen/crates/issen-core/src/artifacts/types.rs:193-224` includes `ArtifactType::Bam` in the persisted round-trip set.
  - `issen/docs/fleet-capability-inventory.md:61-68` states BAM has no parser/classifier and lists no wrappers for LevelDB, journald, DPAPI, plus shallow browser/EVTX/Linux/PE capability at `:46-52`.
  - Fleet TOML search inside Issen found no dependency on `bam-forensic`, `journald-forensic`, `shellhist-forensic`, `exec-pe-*`, `leveldb-forensic`, `bluetooth-forensic`, `dpapi-forensic`, `peripheral-forensic`, or `git-forensic`.
  - The same inventory’s USB statement at `:63` is now stale in one direction: an `issen-usb` crate exists, but B2 shows it is still runtime-dark.
- **Impact:** Enum/schema presence and a repository in the canonical fleet can be misread as product support. Binary journals, browser IndexedDB/deleted browser rows, offline DPAPI, BAM execution, EVTX integrity/memory recovery, and specialized PE analysis have no Issen end-to-end route.
- **Concrete remediation:** Generate a machine-readable capability matrix from manifests + inventory registration + classifier + CLI reachability + E2E tests. Remove unimplemented enum variants or mark them `Unsupported` in coverage. Wire in release-order batches: foundational reader/analyzer release, Issen wrapper, registration/classification, then E2E DB assertion.

## B12 — EWF is duplicated across two canonical repositories and two incompatible release lines

- **Severity:** High
- **Classification:** Architecture risk / duplicate capability / version skew
- **Repos:** `ewf`, `ewf-forensic`, downstream consumers
- **Exact evidence:**
  - `ewf/Cargo.toml:1-22` publishes workspace package `ewf` at 0.2.3 from `SecurityRonin/ewf`.
  - `ewf/ewf/Cargo.toml:1-19` defines package `ewf` with no VFS feature.
  - `ewf-forensic/Cargo.toml:1-25` separately publishes package `ewf` at 0.4.7 from `SecurityRonin/ewf-forensic`.
  - `ewf-forensic/core/Cargo.toml:17-29` adds the forensic-vfs 0.7 adapter.
  - `blazehash/Cargo.toml:112` still depends on `ewf` 0.2; current disk/USB/VFS paths use 0.4, while `usnjrnl-forensic/Cargo.toml:61-72` optionally uses 0.3.
- **Impact:** The fleet has three EWF API generations and two canonical source repositories for the same crates.io package. Security/format fixes can land in one line without reaching consumers; lockfiles can resolve different behavior; “the fleet EWF reader” is ambiguous.
- **Concrete remediation:** Declare `ewf-forensic/core` the successor, deprecate/archive the old `ewf` repository and 0.2 line, migrate all consumers to one minimum 0.4.x release, and publish a migration note. Release EWF first, then dependent containers/orchestrators, then Issen.

# Additional architectural risks and missing capabilities

## R1 — Normalized reporting stops at subsystem boundaries

- **Severity:** Medium
- **Classification:** Architecture risk
- **Repos:** `issen`, `disk-forensic`
- **Evidence:**
  - Good reference: `disk-forensic/src/normalize.rs:1-35` converts analyzer `Observation`s into canonical `forensicnomicon::report::{Finding, Report, ...}`.
  - `issen/crates/issen-correlation/src/model.rs:182-218` defines a separate `AssertionLevel` and `Finding`.
  - `issen/crates/issen-correlation/src/correlation.rs:108-131` defines a second `Correlation` finding with canonical `Severity` but no canonical `Finding`, confidence, evidence object, or assertion level.
  - `issen/crates/issen-cli/src/scanning.rs:90-117` converts canonical `Finding` into a reduced `FindingRow` (severity/code/note/indicator/tags), dropping the canonical provenance/context structure.
- **Impact:** Correlation, signature scan, parser findings, USB findings, and disk findings cannot be queried/rendered with one lossless schema. “Observed/correlated/inferred” is present in one model but absent from another persisted path; no formal “analyst conclusion” layer exists.
- **Remediation:** Persist canonical `Finding` (or a versioned normalized superset) once, with evidence references, provenance, confidence, assertion level, and a distinct analyst-conclusion table. Adapt subsystem-native structs only at their boundary and round-trip-test serialization.

## R2 — The reader/analyzer split is not fleet-uniform

- **Severity:** Medium
- **Classification:** Missing capability / architecture drift
- **Repos:** `atx-forensic`, `snss-forensic`, `ext4fs-forensic`, `hfsplus-forensic`, `iso9660-forensic`, `udf-forensic`
- **Evidence:**
  - `atx-forensic/Cargo.toml:1-3` has only `core`.
  - `snss-forensic/Cargo.toml:1-4` has only `core`.
  - `ext4fs-forensic/Cargo.toml:1-3` has core/FUSE/CLI but no forensic analyzer.
  - `hfsplus-forensic/Cargo.toml:1-13` is one combined reader crate.
  - `iso9660-forensic/iso/Cargo.toml:1-7` explicitly combines reader and tamper analyzer.
  - UDF is likewise a single `udf-forensic` package in the inventory.
- **Impact:** Naming does not reliably communicate whether a crate emits observations or merely parses. ATX/SNSS/ext4 have no dedicated anomaly layer; combined crates cannot keep a minimal reader dependency surface.
- **Remediation:** Record intentional exceptions in ADR-0008, otherwise add `*-forensic` analyzers above existing cores and split combined HFS+/ISO/UDF implementations at API boundaries without duplicating decode logic.

## R3 — Optional VFS adapters target four incompatible 0.x interfaces

- **Severity:** Medium
- **Classification:** Version-skew architecture risk
- **Repos:** reader fleet, `forensic-vfs-engine`
- **Evidence:** Fleet manifests target `forensic-vfs` 0.1 (`dar-core`, `zip-forensic-core`), 0.2 (MBR/GPT), 0.3 (AFF4/VMDK/VHD/VHDX/QCOW2/APM/DMG), and 0.7 (current filesystem/encryption readers). Examples: `zip-forensic/core/Cargo.toml:46-49`, `gpt-partition-forensic/core/Cargo.toml:28-36`, `vmdk-forensic/core/Cargo.toml:26-45`. `forensic-vfs-engine/Cargo.toml:84-93` explicitly cannot use DAR’s adapter because it is a different trait version and builds a synthetic adapter instead.
- **Impact:** “Has a vfs feature” does not mean “implements the current fleet VFS.” Duplicate trait versions increase binary size and prevent direct composition; hand adapters accumulate in the engine.
- **Remediation:** Release adapters bottom-up against forensic-vfs 0.7 (or the next consolidated 1.0), yank/disable stale feature claims, then simplify engine wrappers. Add a CI assertion that every enabled `vfs` feature resolves exactly one `forensic-vfs` version.

## R4 — `disk-forensic` is normalized but narrower than its description suggests

- **Severity:** Medium
- **Classification:** Missing capability / claim not fully supported by code
- **Repo:** `disk-forensic`
- **Evidence:** `disk-forensic/Cargo.toml:8` says it decodes major containers and routes ISO; `disk-forensic/src/lib.rs:102-132` analyzes only APM or MBR/GPT after opening the stream. It does not mount NTFS/ext4/APFS/HFS+/FAT/Btrfs/UFS/UDF/XFS/ZFS and has no `forensic-vfs-engine` dependency.
- **Impact:** “Point it at any disk image” (`src/lib.rs:3`) yields partition-structure analysis, not a universal filesystem/artifact path. Consumers may mistake container support for filesystem support.
- **Remediation:** Narrow wording to “container + partition analysis” or route through the VFS engine and expose mounted filesystem capabilities/coverage.

## R5 — Issen’s scan fallback can complete with no loaded threat intelligence

- **Severity:** Medium
- **Classification:** Architecture risk / degraded-success ambiguity
- **Repo:** `issen`
- **Evidence:** `issen/crates/issen-cli/src/commands/ingest.rs:349-359` catches feed-load error, warns, constructs `ScanEngine::new()`, and continues. `issen/crates/issen-cli/src/scanning.rs:340-346` documents that the default returns an empty engine if the cache is absent or fails.
- **Impact:** An explicit scan may succeed with zero feed-backed detections. Native/timestomp detections can make the output non-empty, obscuring that IOC/Sigma coverage was absent.
- **Remediation:** Persist and render scan coverage by engine/ruleset. Under explicit `--scan`, require at least one requested engine/rule source or require an explicit `--allow-empty-feeds`; never label an empty-feed pass as equivalent to a completed feed scan.

# End-to-end trace spot checks

## 1. Disk image → MFT/registry/prefetch → timeline → correlation/scan (mostly complete, separate from universal VFS)

1. Issen front door classifies disk/archive extensions in `issen-cli/src/pipeline.rs:209-237`.
2. `commands/pipeline_run.rs:620-665` executes ingest and optional unallocated carving.
3. `commands/ingest.rs:190-301` runs `issen_fswalker::run_auto_parse_jobs`, commits each parse unit, and merges coverage/errors.
4. Issen’s parser umbrella force-links parser registrations (`issen/docs/fleet-capability-inventory.md:8-18` describes the three gates); MFT, registry, prefetch, SRUM, LNK, EVTX, SQLite, and others are classified and dispatched.
5. Events are normalized into `issen_core::TimelineEvent`, committed to DuckDB (`commands/ingest.rs:273-301`), then correlation and scan run in `commands/pipeline_run.rs:684-755`.

**Assessment:** This is a real E2E route and includes coverage, resumable parse-unit completion, and post-ingest findings. Its architectural weakness is that container/filesystem opening uses `issen-disk` and direct readers rather than the universal VFS engine; its correctness weakness is stale path+size fingerprints (B6).

## 2. Disk container → partition normalized report in `disk-forensic` (complete but narrow)

1. `disk-forensic::container::open` sniffs and returns a decoded `Read + Seek` stream (`src/lib.rs:8-13`).
2. `analyse_disk` detects APM/MBR/GPT and delegates to the scheme analyzer (`src/lib.rs:102-132`).
3. `src/normalize.rs:1-35` converts analyzer observations into canonical forensicnomicon findings.

**Assessment:** Clean container→orchestrator→reader/analyzer→normalized-report layering for partition analysis. It is not the fleet VFS route and does not provide general filesystem/artifact navigation (R4).

## 3. APFS image → five navigation primitives → snapshot history (navigation complete, history bespoke/orphaned)

1. `forensic-vfs-engine` registers APFS and all major filesystem probers (`src/lib.rs:363-380` onward).
2. The `FileSystem` contract requires `read_dir`, `extents`, `lookup`, `meta`, and `read_at` (`forensic-vfs/crates/core/src/fs.rs:338-366`).
3. APFS snapshots can be listed and opened through bespoke methods (`forensic-vfs-engine/src/lib.rs:209-285`).
4. No `HistoricalSource` implementation exists and only `4n6mount` consumes the engine.

**Assessment:** The five-primitives law is implemented. The “plus state-history” law is not; this path does not reach Issen and does not implement the declared generic contract (B3/B4).

## 4. USB artifact family (reader sources exist; correlation E2E is broken)

1. Fleet sources exist in `peripheral-core`, `winreg-core/artifacts`, `lnk-core`, and `winevt-extract`; `usb-forensic/Cargo.toml:29-66` declares the cross-source inputs.
2. `usb-forensic` exposes the correlation/audit capability.
3. Issen’s `issen-usb` converts resulting timestamps/events (`issen-usb/src/lib.rs:40-63`).
4. No Issen caller constructs sources or invokes audit; canonical path dependency is unresolved.

**Assessment:** Parser/analyzer capability is present but the orchestration edge is missing (B1/B2).

## 5. Windows shellbags (wired but evidentiary completion is unsafe)

1. NTUSER/UsrClass hives are discovered as `Registry`.
2. `ShellbagsParser` registers against `ArtifactType::Registry` and self-filters (`issen-parser-shellbags/src/lib.rs:117-174`).
3. It emits `ArtifactType::Shellbags` timeline events (`:75-94`).
4. Decode/read errors become a successful empty parse (`:35-59`).

**Assessment:** Registration/discovery mismatch is intentionally bridged, so the parser is live. Coverage cannot distinguish malformed/unsupported hives from a clean negative (B9).

## 6. Linux binary journald and browser IndexedDB/recovery (no Issen E2E)

Issen’s own inventory records hand-rolled text-log Linux parsing without `journald-forensic`/`shellhist-forensic`, shallow live-row browser parsing without browser-specific carving/clearing findings, and no LevelDB wrapper (`issen/docs/fleet-capability-inventory.md:46-64`).

**Assessment:** The standalone parser repositories exist, but these artifact families terminate before Issen classification/registration/persistence.

## 7. Memory dump → walkers → case DB (reachable but negative evidence is ambiguous)

1. Memory extensions are classified by `pipeline::classify` (`issen-cli/src/pipeline.rs:209-237`).
2. `commands/pipeline_run.rs:666-683` calls `correlate_mem::ingest_memory_leg` and reports event count.
3. `issen-mem` dispatch invokes multiple `memory-forensic` walkers.
4. Several dispatch functions suppress walker/profile/symbol failures and emit “no artifacts found (or symbols unavailable)” rows (B10).

**Assessment:** Reachable E2E, but the result model does not preserve support/coverage/error state, so absence claims are not reliable.

# Dependency/release order required to close blockers

A safe bottom-up sequence is:

1. **Foundation convergence:** choose one `state-history-forensic` contract; define tri-state VFS capability semantics; publish the consolidated forensic-vfs API.
2. **Reader adapters:** migrate all `vfs` features to that API; consolidate EWF onto `ewf-forensic/core`; publish peripheral-core’s shellbag/device changes.
3. **Analyzers:** release/update USB, BAM, journald, LevelDB/browser recovery, DPAPI, EVTX integrity/memory, and missing ATX/SNSS/ext4 analyzers against the converged foundations.
4. **VFS engine:** remove compatibility wrappers where possible; implement `HistoricalSource` for APFS first; run the common deep-image corpus.
5. **Orchestration:** make `disk-forensic` and Issen consume the engine; wire USB and dark parsers; preserve canonical findings/coverage; replace stale fingerprints.
6. **Product release:** release Issen only after a clean canonical-snapshot `cargo metadata/check/test`, then run artifact-family E2E tests asserting case-DB events, findings, coverage, and layer locators.

# Positive findings

- The fleet’s normal dependency direction is generally downward: format cores consume knowledge/foundation libraries, forensic analyzers consume cores, and orchestration consumes analyzers/readers. I did not find a systemic foundation→orchestrator reverse dependency.
- `forensic-vfs::FileSystem` makes the five navigation primitives required and object-safe (`fs.rs:338-366`), with positioned read-only bytes as the universal low-level edge.
- `forensic-vfs-engine` has meaningful deep-stack implementations and tests across E01/container, partition, filesystem, encryption, archive, logical container, and APFS snapshot paths.
- `disk-forensic` uses canonical `Observation`→`Finding` normalization rather than per-format display models.
- Issen’s main disk ingest has a thoughtful three-phase parse/commit design, per-unit resume records, per-source provenance, coverage summaries, and loud top-level parser errors (`commands/ingest.rs:145-330`).
- Issen correlation’s core narration explicitly describes results as “consistent with” behavior rather than verdicts (`issen-correlation/src/correlation.rs:108-130`), even though that semantics is not yet normalized across all finding stores.

# Runtime-validation hypotheses

These are not classified as confirmed defects without Cargo/runtime execution:

1. **Multiple forensic-vfs versions in one binary:** Cargo may compile parallel 0.1/0.2/0.3/0.7 copies without failure; the confirmed risk is type incompatibility, but actual duplicate versions/size require `cargo tree -d` on `forensic-vfs-engine`, `4n6mount`, browser imagecarve, and Issen.
2. **Path topology in organization CI:** Issen’s USB path may resolve in a private category-based umbrella checkout. It is still confirmed broken in the canonical snapshot layout supplied for this audit; organization CI behavior requires reproducing its checkout action.
3. **Memory placeholder persistence:** Dispatch returns placeholder rows; whether every placeholder becomes a persisted timeline event depends on `correlate_mem` conversion for each command. Runtime tests should assert coverage tables, not only stdout rows.
4. **Feature-gated reachability:** 62 manifest occurrences of `default-features = false` were reviewed as candidates; many are intentional dependency slimming. A full feature matrix (`cargo hack --each-feature`) is needed to detect hidden adapter/codec losses.

## Final conclusion

The fleet is not blocked by a lack of parsers; it is blocked by **integration truthfulness**. The strongest code lives in separate islands, while product-level claims often treat repository existence, dependency declaration, registration, compilation, reachability, and successful covered execution as the same thing. They are not. The next architecture milestone should be a machine-enforced capability graph whose terminal condition is an end-to-end case-DB assertion with explicit coverage—not another inventory of crates.


---

# Part III — Security, parser robustness, and quality gates

# Fleet Security, Parser Robustness, and Quality-Gate Audit

**Snapshot:** `/home/selene/work/ronin-issen-fleet-audit/repos`  
**Inventory:** 86/86 repository directories present  
**Audit mode:** read-only static and workflow audit; repository content treated as untrusted  
**Standard:** `/home/selene/work/ronin-issen-inspect/CLAUDE.md`

## Executive summary

The fleet has substantial positive engineering investment—82/86 repositories run `cargo-deny`, 79/86 invoke `cargo vet`, 72/86 contain fuzz targets, 31/86 enforce literal 100% line coverage, and several container readers use checked offsets, caps, and explicit decompression limits. It nevertheless **does not currently satisfy the Paranoid Gatekeeper standard fleet-wide**. I confirmed four production defects in high-risk parser/container paths and systemic assurance gaps that make the fleet's “input-fuzzed / panic-free by lint / 100% coverage” posture uneven.

### Confirmed production defects

1. **HIGH — AFF4 permits attacker-controlled, unbounded allocation and decompression.**
2. **HIGH — `zip-forensic` fallback random access materializes an entire hostile entry and trusts its declared size; arithmetic can wrap or panic.**
3. **HIGH — `blazehash`'s Windows raw-$MFT parser indexes beyond a short attribute header.**
4. **MEDIUM — `qcow2-forensic` silently converts active L1/L2 read failures into a clean-looking zero-allocation report.**

### Fleet-level assurance gaps

- Only **31/86** CI files enforce 100% **line** coverage. Ten enforce a lower line floor, 11 enforce only 100% functions, 17 have no coverage job, 16 run coverage with no floor, and one (`blazehash`) is advisory.
- Seventy-two repos contain fuzz targets, but **10 never execute them in CI**, and **21 execute only short smoke runs** with no >=10-minute scheduled run. `browser-forensic` defines 24 targets but executes only six; `winevt-forensic` defines eight and executes none.
- Real-corpus/oracle tests in **43 repositories** can return successfully when artifacts or tools are absent. A green job therefore does not prove the advertised oracle ran.
- **540 non-SHA action references across 77 repositories** leave only nine repos fully SHA-pinned.
- `cargo-vet` configuration contains **7,173 exemptions across 78 repositories**, commonly without the truthful notes required by policy; many “vet passes” are administrative exceptions rather than source-review evidence.
- Forty-five repos do not run gitleaks; seven do not run cargo-vet; four do not run cargo-deny.

The local environment has no `cargo` executable, so I could not execute the Rust test suites. This is an explicit validation limitation, not evidence that tests pass or fail.

## Scope and method

I enumerated all 86 inventory entries and inspected every repository's `.github/workflows`, Cargo manifests, fuzz directory and targets, corpus documentation, unsafe policy signal, release workflow, and supply-chain configuration. Mechanical searches were used only to generate candidates. I manually read representative high-risk production code in AFF4, ZIP, archive, VMDK, QCOW2, MFT/filesystem walking, memory/image, decompression, and VFS/container paths before confirming findings. Test-only `unwrap` and `expect` sites were separated from production paths.

The governing standard says every forensic parser must never panic/OOB/trust a length, must have one fuzz target per parsed structure plus a pipeline target, and must validate real artifacts at 100% coverage (`CLAUDE.md:76-78`). It requires blocking deny/vet gates and truthful vet exemptions (`CLAUDE.md:80-86`), bans feature-dropping fleet dependencies (`CLAUDE.md:90-92`), and describes 100% line coverage as the fleet trust proof (`CLAUDE.md:126-129`).

## Confirmed findings

### F-01 — AFF4 unbounded metadata, entry, chunk, and decompression paths (HIGH)

**Evidence**

- `aff4-forensic/core/src/logical.rs:84-89` reads `information.turtle` to an unbounded `String`.
- `aff4-forensic/core/src/logical.rs:123-134` exposes `read_file`, which calls `read_to_end` into an unbounded `Vec` for a ZIP member.
- `aff4-forensic/core/src/meta.rs:56-72` normalizes the complete turtle into a second `String` and collects every block into a `Vec<&str>`; there is no metadata byte/block cap.
- `aff4-forensic/core/src/lib.rs:262-275` trusts attacker-declared total size and chunk geometry to determine loop work.
- `aff4-forensic/core/src/lib.rs:291-294` allocates `chunk_size as usize` for every sparse chunk.
- `aff4-forensic/core/src/lib.rs:314-321` preallocates attacker-declared chunk size and uses unrestricted `ZlibDecoder::read_to_end`; decoded output is not capped to `chunk_size`.

**Exploitability / impact**

An analyst opening a malicious AFF4 or AFF4-L evidence container can be driven into large allocation, decompression-bomb expansion, or extremely long chunk iteration. The risk is local denial of service in a parser intentionally used on attacker-controlled evidence. The output-size declaration is not a safe cap because the decoder may exceed it.

**Remediation**

Add explicit configurable limits for metadata bytes, RDF blocks, logical members, per-entry bytes, chunk size, chunk count, aggregate decompressed bytes, and compression ratio. Decode through `Read::take(max + 1)` or an equivalent bounded writer, reject output above the declared or allowed size, use `try_reserve`, and expose streaming logical-file reads instead of mandatory `Vec` materialization.

### F-02 — ZIP fallback entry materialization, zip-bomb exposure, and unchecked arithmetic (HIGH)

**Evidence**

- `zip-forensic/core/src/lib.rs:222-227` computes `offset + buf.len() as u64` without `checked_add`; a public call near `u64::MAX` can overflow before clamping.
- `zip-forensic/core/src/lib.rs:252-265` reopens a compressed member, calls `Vec::with_capacity(self.uncompressed_size as usize)`, then `read_to_end` on every random read.
- `zip-forensic/core/src/lib.rs:271-320` gets `uncompressed_size` and `compressed_size` from archive metadata and routes all genuinely compressed or unsupported methods into that fallback without a per-entry or aggregate output limit.
- `zip-forensic/core/src/lib.rs:332-345` also computes `data_start + compressed_size` and `foff + 5` unchecked while walking hostile stream metadata.

**Exploitability / impact**

A crafted ZIP central directory can advertise a huge uncompressed length, causing immediate address-space pressure or OOM; a highly compressible member can force unrestricted expansion. The advertised random-access API becomes O(full-entry decompression and allocation) per call. Overflowing offsets can panic in checked builds and wrap into incorrect ranges in optimized builds. This can terminate an analysis process or produce incorrect reads.

**Remediation**

Require caller-supplied limits, reject declared sizes above the cap before allocation, bound actual decoder output independently of metadata, cache or stream with bounded checkpoints, replace arithmetic with `checked_add` and `checked_sub`, validate data ranges against file length, and use `usize::try_from` plus `try_reserve`.

### F-03 — Short NTFS attribute causes production OOB panic in `blazehash` (HIGH)

**Evidence**

- `blazehash/src/walk_windows_mft.rs:246-258` accepts any attribute with `attr_len >= 8`.
- `$FILE_NAME` then unconditionally indexes `buf[attr_off + 8]` and reads a u16 at `attr_off + 20` before proving the attribute is at least 22 bytes (`blazehash/src/walk_windows_mft.rs:171-180`).
- `$DATA` unconditionally reads `buf[off + 9]` after only the eight-byte check (`blazehash/src/walk_windows_mft.rs:274-276`), while `parse_data_size` may read through offset +16 (`blazehash/src/walk_windows_mft.rs:201-212`).

**Exploitability / impact**

A malformed raw NTFS `$MFT` record with a recognized attribute type and declared length 8 or 9 reaches direct indexing beyond the attribute and, near the end of the 1,024-byte record, beyond the slice. On Windows raw-MFT traversal this can panic the hashing process. This is production parser code, not a test-only unwrap.

**Remediation**

Validate the common header and each resident/non-resident subtype's minimum header length before any field access; use checked slice getters or fleet `safe-read` primitives; fuzz this exact raw-MFT parser with truncated attributes and each attribute type.

### F-04 — QCOW2 active mapping I/O errors become silent empty findings (MEDIUM)

**Evidence**

- `qcow2-forensic/core/src/refcount.rs:58-65` defines `read_u64_table` to turn every seek/read error into `Vec::new()`.
- The refcount table correctly uses the checked reader because it is a bootstrap structure (`qcow2-forensic/core/src/refcount.rs:218-224`).
- The equally essential active L1 table and every L2 table use the swallowing reader (`qcow2-forensic/core/src/refcount.rs:226-240`). The final report therefore remains `allocated_clusters = 0, orphan_clusters = 0` if these reads fail.

**Exploitability / correctness impact**

A truncated, sparse, concurrently changing, or malicious QCOW2 image can make active mapping reads fail while returning a successful report indistinguishable from “no allocated/orphan clusters.” This is a forensic false-negative and chain-of-custody concern rather than memory corruption.

**Remediation**

Propagate L1 errors. For L2 failures, either fail the report or return explicit incomplete/error counters and an `is_complete` flag; never encode “unreadable” as “empty.”

## Systemic quality and supply-chain findings

### S-01 — Coverage claims do not match the mandatory line gate (HIGH assurance gap)

Only 31 repos implement a true L100 gate. Good enforcement includes AFF4's LCOV zero-hit loop (`aff4-forensic/.github/workflows/ci.yml:63-104`). Lower floors include APFS at 95% (`apfs-forensic/.github/workflows/ci.yml:99-130`) and USN Journal at 99% **library-only** (`usnjrnl-forensic/.github/workflows/ci.yml:56-88`). `blazehash` only uploads coverage and explicitly sets `fail_ci_if_error: false` (`blazehash/.github/workflows/ci.yml:68-84`). Function-only gates, for example AD1 (`ad1-forensic/.github/workflows/ci.yml:39-45`) and SQLite (`sqlite-forensic/.github/workflows/ci.yml:60-63`), do not enforce the requested line invariant and can miss unexecuted branches within a covered function.

**Fleet distribution and affected repositories**

- **L100 (31):** aff4-forensic, amcache-forensic, bam-forensic, bitlocker-forensic, blob-decoder, bluetooth-forensic, btrfs-forensic, dar-forensic, elephant-diffuser, ext4fs-forensic, fat-forensic, filevault-forensic, luks-forensic, lzo, lzvn, ntfs-forensic, prefetch-forensic, refs-forensic, segb-forensic, shimcache-forensic, snapshot-forensic, snss-forensic, timeglyph, ufs-forensic, useract-forensic, userassist-forensic, veracrypt-forensic, vsc-forensic, xfs-forensic, zfs-forensic, zip-forensic.
- **Lower line floor (10):** apfs-forensic 95, archive-forensic 92, browser-forensic 89, ewf-forensic 85, iso9660-forensic 95, livedisk-forensic 90, qcow2-forensic 95, udf-forensic 96, usnjrnl-forensic 99, vmdk-forensic 97.
- **F100 only (11):** ad1-forensic, apm-partition-forensic, disk-forensic, gpt-partition-forensic, hfsplus-forensic, leveldb-forensic, mbr-partition-forensic, protobuf-forensic, safe-read, sqlite-forensic, xpress-huffman.
- **Coverage with no threshold (16):** atx-forensic, cfb-forensic, exec-pe-forensic, forensic-carve, forensic-hashdb, forensic-vfs, forensic-vfs-engine, forensic-vfs-mount, journald-forensic, lnk-forensic, peripheral-forensic, shellitem, state-history-forensic, trash-forensic, usb-forensic, vhd-forensic.
- **No coverage job (17):** 4n6mount, dmg-forensic, dpapi-forensic, ese-forensic, ewf, forensicnomicon, git-forensic, issen, jsonguard, memory-forensic, name-variants, shellhist-forensic, shrinkpath, srum-forensic, vhdx-forensic, winevt-forensic, winreg-forensic.
- **Advisory only (1):** blazehash.

These six groups account for all 86 repositories.

### S-02 — Fuzz targets exist but substantial parser surfaces are not executed (HIGH assurance gap)

- `browser-forensic/fuzz/Cargo.toml:29-30` explicitly promises one target per parsed structure and defines 24 targets, but its smoke and scheduled matrices list only six (`browser-forensic/.github/workflows/fuzz.yml:33-40,42-64`). Eighteen targets—including ASN.1/DPAPI, mozlz4, cache decompression, IndexedDB/V8, reconstruction, and persistent-state parsers—never run.
- `winevt-forensic/fuzz/Cargo.toml:16-62` defines eight targets covering headers, carving, integrity, BinXML, and decoding, while its entire CI has no fuzz job (`winevt-forensic/.github/workflows/ci.yml:1-66`).
- AFF4's scheduled workflow does run four targets for 10 minutes (`aff4-forensic/.github/workflows/fuzz.yml:20-34`), but the production unbounded read and decompression paths in F-01 lack limit invariants and allocation oracles.

Across the fleet, 14 repos have no targets; 10 have targets but no CI run (`4n6mount`, disk-forensic, dmg-forensic, ewf, livedisk-forensic, lzo, lzvn, memory-forensic, safe-read, winevt-forensic); 21 have only smoke runs; 41 have a >=10-minute scheduled or deep run. Target existence or build-only checks are not fuzz coverage. Add a generated matrix over every `fuzz/fuzz_targets/*.rs`, fail when a target is omitted, run per-structure targets plus a pipeline target, preserve corpora and crash artifacts, and assert output, work, and allocation bounds—not merely “must not panic.”

### S-03 — Real-corpus and oracle tests frequently pass by not running (MEDIUM assurance gap)

A scan found missing-artifact/tool early-success patterns in 43 repos. AFF4 tests simply `return` when reference images are absent (`aff4-forensic/core/tests/corpus.rs:30-45,60-65`). EWF differential tests silently return if `ewfexport` or corpus files are absent (`ewf-forensic/core/tests/corpus_differential.rs:1-21`). USN's real-MFT test is both ignored and returns when the environment variable is absent (`usnjrnl-forensic/tests/mft_parse_real.rs:13-20`). These are useful developer conveniences but not blocking oracle gates.

Use a dedicated CI job that provisions and verifies corpus hashes and authoritative tools, then fails if zero cases execute. Track executed corpus IDs and counts as artifacts. Keep optional local tests separate from the required oracle gate.

### S-04 — Action pinning is incomplete in 77/86 repositories (HIGH supply-chain gap)

The audit found 540 `uses:` instances pointing to mutable tags or toolchain names rather than 40-hex SHAs. APFS, for example, pins checkout but uses `dtolnay/rust-toolchain@stable` and `@1.85` (`apfs-forensic/.github/workflows/ci.yml:18-20,42-53`); ATX release also uses `@stable` (`atx-forensic/.github/workflows/release.yml:15-16`). Only AFF4, archive-forensic, dar-forensic, forensic-vfs, forensic-vfs-engine, qcow2-forensic, state-history-forensic, udf-forensic, and vmdk-forensic were fully pinned in the snapshot.

Pin every action—including `dtolnay/rust-toolchain`—to a reviewed full commit SHA with a version comment. Moving Rust toolchains belong in `rust-toolchain.toml`, not mutable action refs.

### S-05 — Cargo-vet is broadly exempted rather than evidencing review (HIGH supply-chain gap)

Although 79 repos run `cargo vet --locked`, 78 configs collectively contain 7,173 exemptions. AFF4 is representative: imported audit sets are configured (`aff4-forensic/supply-chain/config.toml:7-17`), but dependencies and even fleet-owned crates are marked `safe-to-deploy` as exemptions without notes (`aff4-forensic/supply-chain/config.toml:19-39`). This conflicts with the stated mechanism order and truthful-note requirement (`CLAUDE.md:80-86`). The largest exemption sets are `issen` 958, `blazehash` 787, `browser-forensic` 414, `4n6mount` 409, and `srum-forensic` 404.

Regenerate vet config using workspace or publisher trust and aggregate audits first; retain only unavoidable, version-specific exemptions with a truthful rationale and review/expiry owner. Add a CI policy check that rejects note-less exemptions and caps exemption growth.

### S-06 — Dependency, advisory, and secret gates are uneven (MEDIUM)

`cargo-deny` is absent from memory-forensic, name-variants, udf-forensic, and winreg-forensic. `cargo-vet` is absent from ewf, memory-forensic, name-variants, sqlite-forensic, usnjrnl-forensic, winevt-forensic, and winreg-forensic. Winevt further marks the advisories matrix leg non-blocking (`winevt-forensic/.github/workflows/ci.yml:43-58`). Gitleaks is absent from 45 repos. Representative “latest binary” installation downloads and untars gitleaks without checksum or signature verification (`aff4-forensic/.github/workflows/ci.yml:120-133`), creating a CI bootstrap risk even where scanning exists.

Use blocking deny advisories everywhere, vet everywhere, pinned and checksummed security-tool binaries, minimum job permissions, and a fleet-owned reusable workflow. Avoid direct secret interpolation into shell text as in AD1 publishes (`ad1-forensic/.github/workflows/release.yml:23-39`) and ATX (`atx-forensic/.github/workflows/release.yml:17-24`); pass tokens via `env` as USN does (`usnjrnl-forensic/.github/workflows/release.yml:69-78`).

### S-07 — Feature and license policy drift (MEDIUM compliance)

Two clear fleet-dependency feature reductions violate the batteries-included rule: `timeglyph` disables defaults on `forensicnomicon` (`timeglyph/Cargo.toml:72-77`) and `usnjrnl-forensic` disables defaults on `shrinkpath` (`usnjrnl-forensic/Cargo.toml:35-36`). Third-party `default-features=false` uses were not mechanically mislabeled as fleet-policy violations.

Most package manifests declare Apache-2.0, but MIT remains in `name-variants` (`name-variants/name-variants-rs/Cargo.toml:1-7`) and two `issen` subcrates; `shrinkpath` is dual MIT/Apache. This may be intentional, but it is not fleet-uniform. `forensic-vfs-mount` declares Apache-2.0 (`forensic-vfs-mount/Cargo.toml:1-8`) while the inventory records no root `LICENSE`, so the source distribution should be corrected or verified.

### S-08 — Release artifact integrity is inconsistent (MEDIUM)

Fourteen release workflows generate checksums, 13 contain platform signing, and two use provenance attestation. USN Journal is a good provenance example for both ZIP and MSI (`usnjrnl-forensic/.github/workflows/release.yml:8-11,42-58`). Conversely, `winevt-forensic` signs only the Windows executable and uploads four platform binaries without checksums or provenance (`winevt-forensic/.github/workflows/release.yml:20-33,44-68,70-80`). Library-only crates.io releases were not falsely classified as missing binary checksums; crates.io supplies registry checksums.

For every binary release, generate a signed SHA-256 manifest and attest each uploaded artifact or the manifest, verify tag-to-version, build with `--locked`, and preserve reproducible build metadata and an SBOM.

## Unsafe, panic, command/path, and archive handling assessment

- Inventory lint posture: 43 repos set `unsafe_code = "forbid"`, five set `deny`, and 38 have no repository-level unsafe lint signal. This is a posture gap, not 38 proven unsafe defects. I did not report test fixture `unwrap` or `expect` uses as production vulnerabilities; for example, AFF4 explicitly scopes those allowances to its test module (`aff4-forensic/core/src/logical.rs:175-187`).
- I found no confirmed production shell-command injection. Reviewed invocations use `std::process::Command` with separate arguments; the EWF oracle command is test-only (`ewf-forensic/core/tests/corpus_differential.rs:23-32`).
- I found no confirmed archive path traversal write in the inspected AFF4 and ZIP paths: they expose member bytes and do not extract names directly to host paths. This does not reduce the decompression and allocation findings above.
- Representative higher-quality patterns include APFS checked coverage of all features (`apfs-forensic/.github/workflows/ci.yml:99-130`), AFF4's SHA-pinned actions (`aff4-forensic/.github/workflows/ci.yml:19-20,29-33`), and QCOW2's explicit caps and checked bootstrap refcount-table read (`qcow2-forensic/core/src/refcount.rs:19-24,218-224`).

## Recommended priority order

1. **Immediately fix F-01 through F-04** and add regression and fuzz seeds for each trigger.
2. Generate fuzz execution matrices from the filesystem, fail on omitted targets, and add output, allocation, and work invariants.
3. Make real-corpus jobs fail closed when corpus or tool provisioning is missing; record executed case counts and hashes.
4. Move all repositories to L100, or document tightly scoped and independently reviewed exceptions; do not substitute function coverage.
5. SHA-pin every action and checksum CI bootstrap tools.
6. Rebuild cargo-vet configs to minimize exemptions with truthful notes; make deny, vet, and advisory checks blocking.
7. Standardize secret scan, unsafe lint, release attestation and checksums, license files, and fleet dependency features through reusable policy workflows.

## Validation limitations

- The snapshot was audited read-only; no repository files, issues, branches, or PRs were changed.
- Attempted targeted `cargo test --workspace --all-features` runs for AFF4, ZIP, and QCOW2 and `cargo test --all-features` for blazehash all failed before execution because `cargo` is not installed or in `PATH` (`cargo: command not found`). Findings are therefore based on direct code and control-flow review, not fabricated runtime results.
- This audit establishes confirmed defects and systemic control gaps; it is not a proof of absence for all possible defects in 86 evolving codebases.


---

# Part IV — Product, release, packaging, documentation, and consumability

# Product, release, packaging, documentation, and consumability audit

**Scope:** the 86 repositories in `inventory.json`, with the fleet snapshot at `repos/issen` treated as the current Issen source of truth.  
**Assessment date:** 2026-08-03. Read-only; no issues, branches, or files in the repositories were changed.

## Executive decision summary

The fleet is much stronger as a collection of implemented Rust components than as one installable, coherent product. The main decision is not “add more parsers.” It is to close the truth-and-delivery loop around the parsers that already exist:

1. **Make the Issen front door honest and reproducible.** It currently fingerprints evidence by path+size rather than content, never invalidates a resumed scan when feeds change, skips supported `.dmg`/`.ad1` inputs before provider probing, and does not print the claimed findings at the end of the default pipeline.
2. **Freeze public documentation against generated CLI/manifests.** The main README, docs home, validation pages, and Case-001 quickstart describe different products. Several published commands no longer exist; reporting and output-format claims exceed the actual CLI.
3. **Ship a release that matches its own install story.** README says Rust 1.80+, static binary, and Apple-silicon DMG; source requires Rust 1.96, release artifacts are macOS tarballs and GNU Linux `.deb`s, and the Debian assets are omitted from the release checksum file.
4. **Choose what “86-repo fleet” means operationally.** Thirty non-Issen repos are unreachable from Issen. Some are deliberately superseded or standalone front ends, but important evidence families (VSS/snapshots, journald, git, DPAPI, LevelDB, CFB, Bluetooth and many filesystems) exist without a consumable Issen path.
5. **Standardize release hygiene and validation provenance.** Forty-three repos have no changelog, five no release-plz, two no cargo-vet, one no repository license file, and corpus documentation is both inconsistently located and publicly broken in key places.

## Method and confidence

- Parsed all 86 inventory entries and their package/workflow signals; all 86 snapshots are present.
- Compared Issen README/docs against its Clap declarations, pipeline executor, provider/parser aggregators, manifests, CI, and release workflow.
- Checked all top-level READMEs for `cargo install` examples and broken relative Markdown links.
- Compared Issen’s registry dependency requirements with the current package versions in the fleet snapshot.
- Inspected representative CI/package claims rather than treating README badges as proof.
- **Execution limitation:** the host shell has no `cargo` executable, so `cargo metadata`, `cargo tree`, and a live `issen --help` build could not be rerun. The repository’s prior resolved-graph audit says its `cargo tree -e normal` completed successfully and records its method (`issen/docs/issen-wiring-audit.md:3-11,171-179`). CLI conclusions below are therefore based on the current Clap source and manifests, not guessed runtime output.

Severity: **P0** misleading/unsafe forensic behavior or unusable primary product path; **P1** release-blocking/product-completeness; **P2** fleet consistency/maintenance; **P3** cleanup.

---

## Prioritized gap register

### P0-01 — Resume is not content-addressed despite the public claim (**code defect + misleading docs**)

**Evidence.** README says ingest “fingerprints each artifact by content” and only reparses changed evidence (`issen/README.md:90-93`). The implementation hashes only `path` and byte size (`issen/crates/issen-cli/src/pipeline.rs:154-161,179-183`). A same-size in-place evidence change can therefore be treated as unchanged. The deterministic case ID uses the same weak material (`issen/crates/issen-cli/src/commands/pipeline_run.rs:269-285`).

**Impact.** A resumed forensic case can silently retain stale events after evidence replacement or mutation. This is more serious than documentation drift because the optimization changes evidentiary output.

**Next work / acceptance.** Hash content (or a documented strong sampled/Merkle identity for very large evidence), store hash algorithm+digest+size, and test a same-path/same-size byte mutation. Until then, change the README to “path and size fingerprint.”

### P0-02 — Feed updates do not invalidate the resumed Scan stage (**code defect**)

**Evidence.** `feed_snapshot()` is explicitly a placeholder returning constant `"v0"`; its comment instructs users to use `--rerun` after `issen feed update` (`issen/crates/issen-cli/src/commands/pipeline_run.rs:39-44`). Yet Scan’s resume fingerprint is represented as incorporating the feed snapshot (`issen/crates/issen-cli/src/commands/pipeline_run.rs:252-264`; `issen/crates/issen-cli/src/pipeline.rs:170-176`).

**Impact.** A normal rerun after refreshing threat intelligence can skip scanning and preserve findings from old feeds. The public command table presents `feed update` as the normal refresh path without the `--rerun` caveat (`issen/README.md:105-112`).

**Next work / acceptance.** Digest enabled feed IDs, versions, and cached content; record that digest in `run_manifest`; prove `feed update` alone changes Scan’s fingerprint and reruns only Scan.

### P0-03 — The default front door rejects providers that the binary actually links (**code defect / unusable component**)

**Evidence.** Provider aggregation links AFF4, archive, AD1, DD, DMG, EWF, ISO, QCOW2, VHD/VHDX, and VMDK (`issen/crates/issen-providers/Cargo.toml:15-29`). But the pre-provider extension classifier admits AFF4 and the common image/archive extensions while omitting `dmg` and `ad1` (`issen/crates/issen-cli/src/pipeline.rs:209-237`). Unrecognized files are warned and skipped before provider probing (`issen/crates/issen-cli/src/commands/pipeline_run.rs:212-238`). The same README promises unallocated recovery uniformly across DMG and other formats (`issen/README.md:146-155`).

**Impact.** Existing, linked readers cannot be consumed through the advertised `issen <evidence>` path. This is the clearest example of “component exists but is not consumable.”

**Next work / acceptance.** Probe content through the provider registry first; use extensions only as confidence hints. Add default-front-door tests for `.dmg`, `.ad1`, extensionless E01, renamed images, and malformed lookalikes.

### P0-04 — Public Case-001 quickstart is not executable against the current CLI (**stale docs, not missing parser code**)

**Evidence.** Current top-level commands are Timeline, Info, Feed, Scan, RemoteAccess, Memory, Rules, Report, Srum, Biome, Frequency, Processes, and Session (`issen/crates/issen-cli/src/lib.rs:202-581`). The quickstart still tells users to run removed top-level `issen correlate` (`issen/docs/szechuan-sauce-quickstart.md:97-115,239-250`), removed `issen supertimeline` (`:239-246`), and unsupported `-s case001` (`:170-176`). It also says those commands answer the case while later stating Prefetch/Shimcache/Amcache/LNK are not wired (`:256-264`), whereas the current parser aggregator links all four (`issen/crates/issen-parsers/Cargo.toml:21-49`). The guide’s advertised binary version is also 0.1.0 (`szechuan-sauce-quickstart.md:24-31`) while `issen-cli` is 0.1.3 (`issen/crates/issen-cli/Cargo.toml:1-4`).

**Impact.** The flagship public corpus walkthrough fails early and understates current parser wiring while overstating removed command surfaces.

**Next work / acceptance.** Rewrite from generated `--help`; make one CI job download or mount a license-permitted small corpus subset and execute every non-network command in the quickstart. Label results measured/partial/out-of-scope from current output, not historical notes.

### P0-05 — Public output/reporting claims exceed the implementation (**misleading docs; some missing product code**)

**Evidence.** README advertises timeline text/JSON/CSV/bodyfile (`issen/README.md:99-110`) but Clap permits only text or JSON and separately supports SQLite export (`issen/crates/issen-cli/src/lib.rs:204-242`). README’s capability table advertises terminal, JSON, HTML/PDF, STIX Attack Flow, `.afb`, Mermaid, DOT/PNG, CSV, bodyfile, and DuckDB (`issen/README.md:134-145`). The actual `report` command accepts only HTML, text, or ATT&CK Navigator JSON (`issen/crates/issen-cli/src/lib.rs:475-500`; `issen/crates/issen-cli/src/commands/report.rs:21-43,54-59`). There is no PDF option in the command.

**Impact.** Analysts will design handoff/report workflows around formats the current public CLI cannot emit. This is especially damaging because reporting is the stated product differentiator.

**Next work / acceptance.** Publish a generated capability matrix derived from Clap plus golden command tests. Either wire existing exporters into named commands or remove the claims. Keep roadmap formats in a clearly labeled “planned” table.

### P1-01 — The default command does not hand back the claimed ranked findings (**product completeness / docs drift**)

**Evidence.** README says the one command “hands you the findings, ranked by severity” (`issen/README.md:17-31`) and shows a “real run” ending in detailed correlations (`:35-63`). The actual Correlate stage prints only a count (`issen/crates/issen-cli/src/commands/pipeline_run.rs:684-711`), and completion prints run/skip stage counts (`:541-550`). Rendering correlated findings exists in `issen report --format text` (`issen/crates/issen-cli/src/commands/report.rs:28-38`), but the default pipeline does not call it.

**Impact.** The central “one command → attack story” experience requires an undocumented second command (or HTML generation) and the sample transcript is not representative of the current default stdout.

**Next work / acceptance.** End the default pipeline with the same ranked text renderer, or change the headline promise and show the exact two-command workflow. Add an output snapshot test.

### P1-02 — “Unified” pipeline behavior varies materially by evidence kind (**code/product gap**)

**Evidence.** Disk+memory uses Ingest → Memory → Correlate → Scan (`issen/crates/issen-cli/src/pipeline.rs:16-40,240-252`). Memory-only applies only Memory (`:552-563`), so it is not correlated or scanned. UAC collections bypass the resumable state machine entirely, ingest every run, and render a separate analysis/supertimeline/pivot path (`issen/crates/issen-cli/src/commands/pipeline_run.rs:319-355,358-397`). Collection parse misses are documented to degrade to empty (`:370-372`).

**Impact.** “Any mix … one resumable pass” is not one consistent contract. Collection reruns do unnecessary work, collection failures can look successful/empty, and memory-only results do not reach the same finding stages.

**Next work / acceptance.** Define one stage DAG with typed applicability and persisted coverage for disk, memory, and collections. Fail loud on a requested artifact family that was found but not parsed. Report per-stage coverage and partial status.

### P1-03 — Release artifacts contradict installation and “static binary” claims (**release/docs drift**)

**Evidence.** README says “One static binary” and advertises Windows `.exe/.msi`, Apple-silicon `.dmg`, and Linux (`issen/README.md:19-21,67-76`). Release workflow explicitly says macOS is tar.gz, “not a … .dmg” (`issen/.github/workflows/release.yml:102-108`), builds only a Windows MSI plus macOS tarballs (`:27-38,104-138`), and delivers Linux as GNU `.deb` because musl cross-builds cannot build bundled DuckDB (`:29-32,179-225`).

**Impact.** The artifact/install UX is misleading; GNU `.deb` packaging is not a portable static binary, and there is no DMG.

**Next work / acceptance.** Choose and document the actual matrix: macOS tarballs/Homebrew, signed MSI, Linux amd64/arm64 `.deb`. Remove “static” unless verified with platform-specific linkage tests. If a DMG is required, add and notarize it.

### P1-04 — Linux `.deb` files are not covered by published checksums (**release integrity gap**)

**Evidence.** The release job downloads only artifacts matching `issen-*-*`, generates `checksums.txt`, and creates the release (`issen/.github/workflows/release.yml:140-165`). Debian packages are built/uploaded later by separate `deb`/`release-deb` jobs (`:179-252`). The checksum file is never regenerated after `.deb` upload.

**Impact.** Linux users cannot verify the release-provided Debian assets against the release checksum manifest.

**Next work / acceptance.** Build all assets first; make one final manifest/SBOM/provenance job depend on all successful builders; sign and upload assets+checksums atomically.

### P1-05 — Release can publish a partial or mismatched version (**release design gap**)

**Evidence.** Artifact filenames derive from the tag (`issen/.github/workflows/release.yml:43-46`) while the binary version derives from `issen-cli`’s manifest (`issen/crates/issen-cli/Cargo.toml:1-4`). No workflow step asserts equality. Release intentionally runs under `always()` even when a target fails (`release.yml:140-165`), and `.deb` publication similarly uses `always()` (`:236-252`). Issen has neither changelog nor release-plz in the inventory.

**Impact.** A `vX` tag can label a binary reporting another version, and an incomplete release may be published without an explicit “partial” state.

**Next work / acceptance.** Gate tag == `issen --version` == package metadata; require all mandatory targets; allow a separate manual partial-release procedure with a prominent release note. Add changelog/release automation or document the intentional alternative.

### P1-06 — Platform support is built but not behavior-tested on Windows (**missing validation**)

**Evidence.** README claims Linux/macOS/Windows (`issen/README.md:12-14`). CI tests only Ubuntu and macOS (`issen/.github/workflows/ci.yml:57-82`). Windows is compiled and packaged in release workflow (`issen/.github/workflows/release.yml:27-38,76-118`) but does not run the workspace test suite there.

**Impact.** Path handling, ANSI behavior, locked-file semantics, and Windows-specific packaging can regress while all CI tests pass.

**Next work / acceptance.** Add a Windows test lane for CLI parsing, case DB creation, report generation, representative fixture ingest, path-with-spaces, and MSI smoke install/uninstall.

### P1-07 — Rust requirement is wrong in the main README and highly fragmented fleet-wide (**docs drift + fleet policy gap**)

**Evidence.** README badge says Rust 1.80+ (`issen/README.md:12`), while workspace and pinned toolchain require 1.96/1.96.0 (`issen/Cargo.toml:72-76`; `issen/rust-toolchain.toml:1-6`). Across concrete package declarations the inventory spans 1.70, 1.75, 1.80, 1.81, 1.85, 1.87, 1.88, 1.93, and 1.96, and many packages inherit a workspace value that the inventory cannot display concretely.

**Impact.** Source install fails for a user following the public requirement; fleet consumers cannot infer a coherent support floor.

**Next work / acceptance.** Generate badges/install prerequisites from manifests. Adopt explicit policies by layer (lean libraries versus applications), verify each MSRV in CI, and publish a machine-readable fleet matrix.

### P1-08 — Thirty repos are unreachable from Issen; several are not merely alternative front ends (**product scope / integration debt**)

**Evidence.** The resolved-graph audit classifies 37 direct, 16 transitive, and 30 orphaned non-Issen repos (`issen/docs/issen-wiring-audit.md:13-23`). The orphan list includes archive-forensic, DPAPI, Btrfs/FAT/HFS+/ReFS/UDF/UFS/XFS/ZFS, Git, snapshots/VSS, journald, Bluetooth, CFB, LevelDB, protobuf, and standalone VFS tools (`:90-125`). The same audit correctly distinguishes superseded in-tree parsers (Amcache/BAM/PE/Shimcache/UserAssist/USB) from genuine missing integration (`:94-125`). Parser wiring is mechanical and documented (`:146-169`).

**Impact.** “86 standalone libraries” is true as an inventory statement, not as an Issen capability statement. The largest user-value gaps are VSS/snapshot history, journald, modern browser LevelDB, DPAPI, and common non-NTFS filesystems.

**Next work / acceptance.** Publish three statuses per repo: `Issen-default`, `Issen-optional/standalone`, `superseded`. Prioritize integrations by real corpus demand; archive or clearly deprecate duplicates rather than leaving two apparent implementations.

### P1-09 — Known silent-wrong and silent-skip format gaps remain product risks (**code defects, already documented**)

**Evidence.** The format audit records hardcoded memory layouts, unwired NTFS LZNT1, SQLite UTF-16 mojibake, journald compression skips, browser schema drift, VHDX differencing, XPRESS dispatch errors, and Shimcache fallback as silent/misleading behaviors (`issen/docs/format-coverage-audit.md:69-89`). It correctly ranks common silent-wrong issues ahead of honest `Unsupported` errors (`:95-123`). The same document says real-artifact validation is sparse outside a handful of formats (`:31-35`).

**Impact.** A product-level report cannot be more trustworthy than a leaf parser that emits plausible wrong data.

**Next work / acceptance.** Execute that document’s Tier 0/1 list before breadth work. Require every variant dispatch to be validated or fail with a named `Unsupported(<variant>)` error.

### P1-10 — Corpus/provenance documentation is publicly broken and non-reproducible (**docs + validation gap**)

**Evidence.** Issen validation promises per-file provenance in `tests/data/README.md` (`issen/docs/validation.md:12-22,52-60`), but the snapshot has no `issen/tests` directory. The corpus catalog is now a local-layout redirect to `~/src/ronin-issen` and `../../ronin-issen/docs/test-data-catalog.md` (`issen/docs/corpus-catalog.md:1-13`), not a valid self-contained public path. Reproduction commands reference `~/src/memory-forensic`, `~/src/dpapi-forensic`, and large ignored files (`issen/docs/validation.md:68-72,347-369`). The SQLite and VSS READMEs link missing `tests/data/README.md` files (`sqlite-forensic/README.md:326-332`; `vsc-forensic/README.md:93-101`). Targeted scanning also found fixture directories without local provenance in `jsonguard/tests/corpus`, `ese-forensic/crates/ese-test-fixtures`, and `snss-forensic/core/tests/fixtures`.

**Impact.** Strong validation prose cannot be independently reproduced from a clone. Licenses, hashes, and oracle commands are not discoverable at the referenced locations.

**Next work / acceptance.** Put one public catalog in the umbrella repository using web-valid links; give every fixture a stable catalog ID, origin URL, license/redistribution status, cryptographic hash, real/synthetic classification, oracle, expected result, and fetch recipe. CI-check every catalog link and committed hash.

### P1-11 — At least one current CLI install command names no current package (**stale packaging docs**)

**Evidence.** `srum-forensic` instructs `cargo install srum-forensic` twice (`srum-forensic/README.md:21-24,39-44`), but the current workspace package is `srum-cli`, whose binary is `srum4n6` (`srum-forensic/crates/srum-cli/Cargo.toml:1-11`); the root is a virtual workspace (`srum-forensic/Cargo.toml:1-10`). No explicit artifact-release workflow exists in that repo snapshot. Issen’s docs home is also stale, installing removed `rt-cli` (`issen/docs/index.md:1-11`) instead of `issen-cli` (`issen/crates/issen-cli/Cargo.toml:1-4,18-24`).

**Impact.** First-run conversion fails before users can evaluate the tools.

**Next work / acceptance.** Test every README install line in clean CI containers. For multi-package workspaces, publish/install the exact package name or use `cargo install --git … --package <name>` consistently.

### P2-01 — Fleet release hygiene is incomplete and uneven (**packaging governance**)

Inventory-derived counts:

- **43/86 lack a changelog:** name-variants, ad1, AFF4, DMG, EWF-forensic, QCOW2, VHD/VHDX/VMDK, livedisk, archive, zip, APM/GPT/MBR, APFS/FAT/ISO/ReFS/XFS/ZFS, memory, journald, winevt, Amcache/ATX/BAM/Bluetooth/browser/ESE/exec-PE/prefetch/protobuf/shimcache/SNSS/SQLite/SRUM/trash/UserAssist/winreg/state-history/Issen/ewf.
- **5/86 lack release-plz:** bluetooth-forensic, snapshot-forensic, state-history-forensic, Issen, ewf.
- **2/86 lack cargo-vet:** ewf and usnjrnl-forensic. Seven repos have no CI vet signal (also name-variants, memory, winevt, SQLite, winreg).
- **1/86 lacks a repository license file:** forensic-vfs-mount, although its manifest declares Apache-2.0 (`forensic-vfs-mount/Cargo.toml:1-11`).
- All 86 have a README, Cargo.lock, and deny.toml; all have at least one workflow and test marker.

**Impact.** Users cannot reliably discover breaking changes or verify the intended license file in packaged source. Supply-chain standards are asserted fleet-wide but not uniformly enforced.

**Next work / acceptance.** Add a fleet conformance job that checks license file, changelog or explicit exemption, package README/LICENSE inclusion, cargo-vet config+CI, release workflow, and MSRV job.

### P2-02 — Package/version topology is difficult to consume and Issen pins old incompatible minor lines (**integration drift**)

**Evidence.** Issen requests `winevt-extract = "0.2"` while the fleet is 0.4.0; browser core 0.2 while current is 0.3.0; timeglyph 0.3 while current is 0.9.5; zip-forensic-core 0.1 while current is 0.2.1 (`issen/Cargo.toml:168-190,207,231-254`; current versions are in those repos’ manifests/inventory). Because Cargo’s `0.x` caret ranges do not cross minor versions, Issen is intentionally or accidentally consuming old published APIs rather than the current fleet. Multi-crate repos also use many independent version lines; examples include forensicnomicon (`1.10.0/1.5.0/1.3.3/0.1.10`), memory-forensic, winevt, browser, SRUM, and winreg.

**Impact.** A leaf fix may be “released” but absent from Issen. Users cannot infer compatibility from repo release tags alone.

**Next work / acceptance.** Generate a dependency freshness report from the inventory and lockfile. Define coupled-version groups or a compatibility matrix; require the capstone convergence suite against every proposed fleet release.

### P2-03 — A Python binding is marked publishable but lacks package metadata (**packaging defect**)

**Evidence.** `forensicnomicon-py` has only name/version/edition and a cdylib declaration, with no license, description, repository, readme, or explicit `publish = false` (`forensicnomicon/bindings/python/Cargo.toml:1-15`). Inventory classifies it as publishable.

**Impact.** Accidental `cargo publish --workspace` can attempt to publish an incomplete binding; intentional distribution lacks maturin/PyPI metadata.

**Next work / acceptance.** Either set `publish = false` and add a tested maturin/PyPI workflow, or complete crates.io metadata and package-list validation.

### P2-04 — Broken README links indicate repository reorganizations were not swept (**docs drift**)

Targeted top-level README checking found broken local links beyond the corpus cases: `memory-forensic/README.md:440` (`crates/forensic-hashdb/`), `winevt-forensic/README.md:350` (`crates/winevt-analyze/`), `srum-forensic/README.md:456-463` (four `crates/ese-*` paths), plus the missing SQLite/VSS test-data links above.

**Impact.** Documentation leads users to components that moved to sibling repositories without redirecting to the actual public URL.

**Next work / acceptance.** Run a Markdown link checker at fleet level after reorganizations; treat local-path links to sibling repos as errors.

### P2-05 — CI/release action pinning is inconsistent (**supply-chain/reproducibility gap**)

**Evidence.** Issen CI pins most actions by SHA but cargo-vet still uses floating `dtolnay/rust-toolchain@stable` (`issen/.github/workflows/ci.yml:112-129`). Representative SRUM CI uses floating `actions/checkout@v4`, `dtolnay/rust-toolchain@stable`, and `EmbarkStudios/cargo-deny-action@v2` (`srum-forensic/.github/workflows/ci.yml:14-78`). Inventory records unpinned actions throughout the fleet.

**Impact.** The “audited/pinned” posture is not uniformly reproducible, and a compromised/mutated action tag affects the release chain.

**Next work / acceptance.** Enforce full commit-SHA pins with Renovate comments; exempt only Rust channel selectors when independently pinned by `rust-toolchain.toml`.

### P3-01 — Historical planning/research docs are indexed as product docs without status banners (**docs information architecture**)

**Evidence.** Issen’s `north-star-advisor` documents describe proprietary Word/PDF reporting and commands such as `issen parse --source … --report …docx` (`issen/north-star-advisor/docs/BRAND_GUIDELINES.md:100-118,179-180,207-212,269-272`), while the current repo is Apache-2.0 and its CLI only exposes HTML/text/Navigator reporting. Workshop KANBAN explicitly says `issen correlate` was backlog/nonexistent (`issen/docs/workshop-3hr/KANBAN.md:9-12,53-56`) while current public quickstarts still invoke it.

**Impact.** Search results blur roadmap, discarded strategy, historical implementation names, and supported product behavior.

**Next work / acceptance.** Move historical research/plans under an archive excluded from MkDocs/search, add “historical—not current product documentation” banners, and define README + generated CLI reference as canonical.

---

## Capability truth table for immediate documentation repair

| Public claim | Current source truth | Disposition |
|---|---|---|
| Rust 1.80+ | Rust 1.96/1.96.0 | Fix docs now |
| One static binary | macOS tarball, Windows MSI, GNU Linux `.deb`; DuckDB C++ prevents musl release | Remove “static” or prove per target |
| Apple-silicon `.dmg` | macOS tar.gz; workflow explicitly rejects DMG | Fix install text |
| `issen <evidence>` auto-detects all linked containers | Extension prefilter omits DMG/AD1 | Fix code first |
| Content-fingerprinted resume | Path+size fingerprint | Fix code or qualify |
| Feed update refreshes detections | Feed fingerprint constant `v0`; requires `--rerun` | Fix code / document interim |
| One command prints ranked evidence-chain findings | Pipeline prints count/summary; text renderer is in `report --format text` | Wire renderer or show two commands |
| Timeline CSV/bodyfile | CLI text/JSON plus SQLite export | Remove/wire |
| Report PDF/STIX/.afb/Mermaid/DOT/PNG | Report HTML/text/Navigator JSON | Mark roadmap or wire |
| Case-001 commands are exact | Several removed/renamed commands and flags | Rewrite + CI execute |
| Fleet = Issen coverage | 30 repos unreachable; some deliberately superseded | Publish statuses |
| Provenance is in `tests/data/README.md` | Key referenced paths absent/moved | Repair catalog |

## Recommended engineering sequence

### Next 2 weeks — credibility and release blockers
1. Fix P0-01/P0-02/P0-03 and add regression tests.
2. Generate CLI reference/capability tables; rewrite main README, docs home, and Case-001 quickstart from current commands.
3. Make default pipeline render findings or revise the product promise.
4. Correct release matrix/MSRV/static/DMG language; include DEBs in checksums and enforce tag/version equality.

### Next 30–45 days — one trustworthy product path
5. Unify disk/memory/collection stage semantics and persist a coverage/partial-result manifest.
6. Run Windows behavioral CI and per-target install smoke tests.
7. Establish public corpus catalog and make one Case-001 subset reproducible in CI/manual release validation.
8. Execute silent-wrong Tier 0/1 fixes before adding reader breadth.

### Then — fleet rationalization
9. Classify all 86 repos as default-integrated / optional-standalone / superseded / experimental.
10. Prioritize VSS/snapshot, journald, LevelDB, DPAPI, Git, and demanded filesystems using real-case corpus coverage.
11. Add fleet conformance automation for license/changelog/vet/release/MSRV/package/link checks.
12. Align incompatible Issen dependency lines with current fleet releases and publish compatibility policy.

## Positive findings to preserve

- All 86 repositories are present, have READMEs, lockfiles, deny configuration, workflows, and Rust test markers.
- Issen’s parser/provider/carver aggregator pattern centralizes compile-time registration and includes drift tests; this is a strong defense against dead-code-elimination wiring mistakes (`issen/crates/issen-cli/src/lib.rs:52-69`; `issen/crates/issen-parsers/Cargo.toml:15-20`; `issen/crates/issen-providers/Cargo.toml:15-17`).
- The existing wiring audit distinguishes transitive, superseded, and genuinely orphaned components instead of treating every non-direct dependency as missing (`issen/docs/issen-wiring-audit.md:69-125`).
- The format audit uses the right forensic priority: silent plausible wrong output is a bug; explicit Unsupported is honest incompleteness (`issen/docs/format-coverage-audit.md:10-35,95-123`).
- Representative mature repos do enforce meaningful package/coverage/MSRV gates; SQLite tests three OSes, checks 100% function coverage, verifies library MSRV separately, and checks packaged README/LICENSE (`sqlite-forensic/.github/workflows/ci.yml:35-46,48-84,95-113`). The task is to make that discipline fleet-wide and ensure its own README links remain valid.
