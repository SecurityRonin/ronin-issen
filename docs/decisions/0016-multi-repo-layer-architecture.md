# 0016 — Multi-repo layer architecture: five navigation primitives, medium-agnostic parsers

**Status:** Accepted

## Context

Issen orchestrates a family of standalone forensic libraries. Each library is a
deep, self-contained expert in one artifact family; Issen is the thin wrapping and
correlation layer on top. The fleet needs one architecture that says, unambiguously,
*where a given capability lives* and *which direction dependencies flow*, so that a
reader/analyzer written for one medium (a live path, an image, a memory dump, a log,
a query, a hash store) never re-implements another medium's concerns.

The organizing insight is that all forensic evidence is reached through one of **five
navigation primitives**, and that the crate that *interprets* an artifact
(the PARSER) should be blind to which primitive delivered its bytes.

## Decision

### The layer hierarchy (layers are architectural concepts; a repo may contribute crates to several)

```
FOUNDATION      zero-dep artifact specs / format constants / contract traits
                 · PRIMITIVES (sub-foundation, strictly lowest): safe-read, jsonguard
                 · KNOWLEDGE + CONTRACTS: forensicnomicon, state-history-forensic,
                   forensic-hashdb, the forensic-vfs contract
CONTAINER      decode a raw source format → addressable data stream
                 ewf, vhdx, dd, segb-core, memf-format, (vmdk/qcow2/iso/aff4/dmg … planned)
FILESYSTEM     navigate a sector stream by path (name→inode→block)
                 ext4fs-forensic, 4n6mount (FUSE bridge), (ntfs/apfs … planned)
PAGING         navigate a page stream by virtual address (PID→EPROCESS→VA→PA)
                 memf-hw
OS STRUCTURE   walk OS objects in a VA space (EPROCESS/VAD/DPAPI/ETW)
                 memf-windows, (memf-linux … planned)  — MAY call PARSER when it locates artifact bytes
LOG FORMAT     navigate a log stream by timestamp / record number
                 winevt-forensic, (journal/tracev3/zeek/cloudtrail … planned)
QUERY ENGINE   execute a live query, stream result rows
                 issen-remote-access, velociraptor-parser
GRAPH NAV      navigate a content-addressed store by hash (Merkle DAG)
                 (cas-forensic, git-forensic, sigstore-forensic … planned)
PARSER         interpret artifact records → forensic meaning (medium-agnostic)
                 browser-forensic, winevt-forensic, srum-forensic, segb-forensic, …
ORCHESTRATION  wire all paths, cross-artifact correlation, user-facing CLI
                 Issen (issen-<artifact>, issen-correlation, forensic-pivot, issen-cli)
```

`[H] state-history-forensic` is a **cross-cutting functor**, not a vertical tier: it
lifts each base primitive to a time-indexed variant (`[P^H]` VSS/APFS snapshots,
`[M^H]` hiberfil/VM snapshot chains, `[L^H]` sealed/rotated logs, `[Q^H]`
point-in-time exports; `[C^H] ≅ [C]` since a CAS already encodes history) via shared
`TemporalCohort<H>` traits.

### The five navigation primitives

- **[P] Disk:** `name → inode → block address` (filesystem tree traversal)
- **[M] Memory:** `PID → EPROCESS → virtual address → physical address` (page-table walk)
- **[L] Log:** `timestamp / record-number → record boundary → field decode` (stream seek)
- **[Q] Live Query:** `(endpoint, query, cursor) → result_set → field` (ephemeral; data is produced, not retrieved)
- **[C] Content-Addressed:** `hash → blob → content_graph` (Merkle DAG; identity = hash)

The container paths are parallel and independent — none feeds another; all converge
at PARSER. (A disk path can *feed* a log or memory path — hiberfil.sys and EVTX live
on disk and are reached via the filesystem first. Cloud/streaming logs have no
disk/memory upstream. [Q] and [C] have no traditional container: the endpoint or hash
store *is* the entry point.)

### Dependency rules (the load-bearing part)

- **Within FOUNDATION there is one strict ordering: PRIMITIVES sit below KNOWLEDGE +
  CONTRACTS.** A knowledge/contract leaf (forensicnomicon, state-history-forensic,
  forensic-hashdb) MAY depend on a primitive (`safe-read`, `jsonguard`); a primitive
  MUST NOT depend on anything, inside FOUNDATION or out. This is the *only* sanctioned
  intra-layer edge in the fleet, and it is what makes ADR-0012's "every integer read
  goes through `safe-read`" apply to FOUNDATION itself rather than exempting it.
  Primitives stay zero-dependency so the edge can never become a cycle.
- CONTAINER depends on FOUNDATION only.
- FILESYSTEM / PAGING / OS STRUCTURE / LOG FORMAT depend on their container + FOUNDATION.
- OS STRUCTURE (memf-windows) MAY call PARSER repos when it locates artifact bytes in
  a VA region (e.g. a SQLite page in hiberfil.sys → browser-forensic-carve).
- **PARSER depends on FOUNDATION only; it accepts `Path` or `&[u8]` — never imports
  CONTAINER, FILESYSTEM, PAGING, OS STRUCTURE, or LOG FORMAT crates.**
- QUERY ENGINE / GRAPH NAV crates depend on FOUNDATION and produce result-row / CAS
  event types that feed PARSER or directly ORCHESTRATION.
- `[H]` crates depend on state-history-forensic (FOUNDATION) plus whichever layer they
  observe, and export `TemporalCohort<H>` upward.
- ORCHESTRATION is the primary wiring point between all layers.

### Why PARSER repos have no layer dependency below them (medium-agnostic by design)

Every source resolves an artifact to bytes/records *before* the parser sees it:

```
Live system     → OS opens Path normally            → browser-forensic(path)
4n6mount        → FUSE exposes path transparently   → browser-forensic(path)
ewf + ext4fs    → Issen extracts file bytes         → browser-forensic(bytes)
memf-windows    → extracts SQLite page from VA      → browser-forensic-carve(bytes)
winevt-forensic → decodes EVTX record               → EventRecord
velociraptor    → executes VQL query                → (parser)(result_rows)
cas-forensic    → resolves hash to blob content     → (parser)(bytes)
```

The wiring to a source happens in ORCHESTRATION or inside the OS STRUCTURE / LOG
FORMAT / QUERY ENGINE layer that located the artifact — never inside the parser.

### Practical decision rule (where does this code go?)

1. Fact about a format? → `forensicnomicon`
2. Decode an image/dump container? → CONTAINER
3. Navigate sectors by path (name→inode→block)? → FILESYSTEM
4. Navigate pages by virtual address (PID→EPROCESS→VA→PA)? → PAGING
5. Walk Windows/Linux kernel objects? → OS STRUCTURE
6. Navigate a log stream by timestamp/record number? → LOG FORMAT
7. Interpret artifact records as forensic evidence? → PARSER
8. Correlate findings / drive the UX? → Issen
9. Execute a live query and capture the result? → QUERY ENGINE
10. Navigate a content-addressed store by hash? → GRAPH NAV
11. Enumerate the temporal cohort of states for an artifact? → `[H]` state-history layer

## Consequences

- **The bottom layer is FOUNDATION (renamed from KNOWLEDGE).** It is defined by
  *dependency position* — zero-dep leaves that everything depends **down** onto —
  not by domain. It holds both domain-knowledge leaves (forensicnomicon,
  forensic-hashdb) AND generic utility leaves (jsonguard, safe-read, the
  `forensic-vfs` contract). The old name wrongly implied the whole tier was domain
  knowledge. **Layer ≠ folder:** in the reorg's physical folders this one layer spans
  both `knowledge/` (domain facts) and `utility/` (generic libs) — the *layer*
  (dependency position) and the *folder* (domain grouping) are distinct axes.
- Every capability has exactly one home, and the dependency direction is
  unambiguous (down toward FOUNDATION, never up, and sideways **only** on the one
  sanctioned PRIMITIVES edge inside FOUNDATION described in the dependency rules).
- **Amendment (2026-08-01) — the FOUNDATION PRIMITIVES band.** Originally this ADR
  described FOUNDATION as a flat tier of zero-dep leaves and forbade sideways edges
  outright. That left the ordering *between* FOUNDATION members undefined, and the
  cost was concrete: `forensicnomicon` kept hand-rolled bounds-checked readers in
  `catalog/decode.rs` that reimplemented `safe-read`'s published API — same
  `(data, offset)` signature, same "0 when out of range" contract — and accumulated
  seven wrapping `offset + N > len` guards, the exact defect class `safe-read` exists
  to prevent. Reviewers twice rejected adopting `safe-read` on the grounds that it
  would "invert the layering," reasoning from its `utility/` folder despite the
  Layer ≠ folder note below. Naming the PRIMITIVES band makes the correct dependency
  legal and explicit instead of re-derived (and re-derived wrongly) per review.
- PARSER repos are reusable across every medium for free, because they never learn
  where their bytes came from — the single most important invariant this ADR protects.
- **Release/publish order follows this graph bottom-up** — see
  [ADR-0006](0006-fleet-dependency-layering-release-order.md).
- The reader/analyzer split within a format repo is [ADR-0008](0008-reader-analyzer-core-forensic-split.md);
  the format-agnostic access abstraction that keeps consumers off per-format crates is
  [ADR-0011](0011-vfs-universal-container-abstraction.md). This ADR is the umbrella both
  refine.
- This is a living reference; `CLAUDE.md` keeps the condensed layer list + the
  decision rule in always-loaded context and points here for the full map, per-layer
  responsibilities, and rationale.
