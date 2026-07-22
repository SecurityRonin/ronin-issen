# SecurityRonin Fleet Glossary

The canonical definitions for the vocabulary, concepts, and **epistemological
distinctions** used across the forensic fleet. This is a *reference*: it defines
terms crisply and points at the binding sources. The **rules** live in
`CLAUDE.md` (the constitution) and the ADRs (`docs/decisions/`); a definition
here that ever conflicts with a rule there is a bug in this file — fix the
glossary, the rule wins.

**Living document.** Seeded with the highest-value cross-cutting terms; extend it
whenever a new fleet-wide concept or coinage is settled. Prefer one precise entry
with a cross-reference over re-explaining architecture already documented elsewhere.

---

## 1. Epistemology — three layers of a forensic claim

The most important distinction in the fleet. Every statement a tool emits — a
finding, a report caption, a UI label, a flag name — sits in exactly one of three
layers. Keep them distinct; never let a lower-confidence layer wear the clothes of
a higher one. (Binding source: `CLAUDE.md` → *Expert Witness Reports — Three Layers
of Epistemic Authority* and *Name evidence by the state or mechanism actually
measured*.)

1. **Observed fact** — what the evidence directly shows. State as a finding.
   *"200,000 USDT moved in a 7.5-minute sweep"; "an `$MFT` record has its `IN_USE`
   flag cleared"; "these sectors are claimed by no allocation structure".*
2. **Forensic inference** — what the pattern is **consistent with**. Use
   "consistent with" / "strongly consistent with" / "not consistent with" — never
   "confirms", "proves", or "establishes". *"consistent with intentional
   deletion"; "consistent with C2 beaconing".*
3. **Legal conclusion** — whether conduct is a crime, fraud, or breach. For the
   **tribunal**, not the tool or the expert. The canonical hand-off is *"the Court
   may draw its own conclusions."*

**Name the observable, never the conclusion** (the naming corollary). A default
name is a layer-1 claim, and a name that asserts a layer-2 story asserts it on
*every* invocation. So the name states the measured state, not the intent it
suggests:

| Observed state (correct) | Conclusion smuggled in (wrong) |
|---|---|
| `unallocated` (no allocation structure claims it) | `deleted` (asserts a deliberate act) |
| repeated failed logins | "brute-force attack" |
| sustained memory growth | "memory leak" |
| an on-disk file found running in memory | "malware injection" |

The conclusion-word is legitimate **only where the conclusion is itself the
recorded observable** — an `$MFT` record that is *flagged* deleted may be called
deleted, because the flag (not the deletion act, and not the intent) is what was
observed. Even then, prose attributes it: *"recorded as deleted by the
filesystem."* The test: *could the same observed state have arisen without the
story the name tells?* If yes, name the state.

---

## 2. Recovery & carving

The vocabulary for recovering evidence that the fast default pass does not surface.
(Binding sources: issen `docs/decisions/0018-carving-tiers-*.md`; the fleet ADR on
Tier-2 unallocated carving in `docs/decisions/` — the flag/engine law.)

### Data-state terms

- **Live set** — the allocated, referenced, in-use files a normal filesystem walk
  returns. The default of every tool.
- **Allocated / Unallocated** — whether an allocation structure (bitmap, `$Bitmap`,
  block group descriptor) claims a region. **Unallocated** is a pure layer-1
  observation: *no structure references these bytes.* It carries **no** claim that
  the data was ever deleted — it may be a deleted file, a reformatted prior volume,
  or bytes never referenced at all.
- **Tombstone** — a filesystem record that itself **records a deletion**: an `$MFT`
  FILE record with `IN_USE` cleared, an ext4 orphan inode, a SQLite freelist page.
  Here a deletion event was *observed* (the FS asserts it), so calling it
  **deleted** is a layer-1 fact, not an inference — see §1.
- **Slack** — the unused bytes between the logical end of a file and the end of its
  last allocated cluster/block; may hold residue of a prior file.
- **Residual data** — the union: everything outside the live set that is
  recoverable, whether FS-recorded-deleted (tombstones) or carved from unallocated
  space.

### Carving tiers (medium-universal)

The cost split that decides what runs by default. The **tier test**: *is the cost
bounded by the artifact already in hand, or by the whole medium?* It applies
identically to disk, memory, and log media.

- **Tier 1 — file-internal carving.** Recovery *within an artifact already located
  and opened* (SQLite freelist/WAL, EVTX unallocated `ElfChnk`, a located in-memory
  region). Cost **O(artifact)** — marginal on top of the parse already paid.
  **Default-on** in the parser.
- **Tier 2 — whole-medium carving.** Magic-byte scanning the *entire* image or
  memory dump for orphaned artifacts no structure references. Cost **O(image)** /
  **O(dump)**. **Opt-in.** On disk this is a genuinely new pass (the default
  pipeline navigates the FS to located files, it does not byte-sweep the image), so
  it must stay behind a flag.

### The recovery flags (fleet-wide law — identical in `issen` and every `*4n6` CLI)

| Flag | Recovers | Cost | Default |
|---|---|---|---|
| *(none)* | Tier-1 file-internal carving | O(artifact) | **on** |
| `--deleted [latest\|all\|off]` | FS-**recorded** tombstones (a deletion the FS itself flagged) | cheap (metadata-driven) | off |
| `--unallocated` (alias `--unalloc`) | Tier-2 whole-image unallocated carving — allocation observation, **no intent claim** | O(image) | off |
| `--residual` | **Both** of the above — all recoverable data outside the live file set | both | off |

- `--deleted` is **not** renamed and is **not** a synonym for carving: it means a
  *recorded* deletion (§1, tombstone). `ntfs deleted_nodes()` and `4n6mount
  --deleted latest|all|off` are its long-standing, correct implementations.
- `--unallocated` names the **observation** (allocation status), deliberately not
  `--deleted` (which would assert intent) nor `--non-live` (which collides with
  *live-response / live acquisition*).
- `--residual` is the umbrella; its help text describes it observationally — *"all
  recoverable data outside the live file set: filesystem-recorded deletions plus
  unallocated-space carving"* — not "everything deleted".
- **Memory:** the same tier test governs it. **Bounded** memory carving (within a
  located VAD/heap/pool region) is default-on; **whole-dump** scanning is opt-in
  until a shared, measured single-pass sweep exists. The disk flags govern the disk
  medium; memory carving is a separate axis (`RecoveryMethod::MemoryCarve`).

### Recovery-method provenance

Every recovered item is tagged with **how/where** it was recovered — the recovery
method (file-internal vs unallocated vs memory), the absolute offset, and a
confidence — so machine output round-trips it and an analyst can filter carved
evidence from live evidence. A carved record indistinguishable from a live one is a
fabrication hazard; the tag is structural, not optional. *(The exact type + its
crate home are being settled in the Tier-2 carving ADR; a `RecoveryMethod` enum
already exists in `browser-forensic-carve` — the fleet vocabulary must subsume it,
not fork a second type.)*

### Carving vs adjacent verbs

- **Carving** — recovering an artifact by its *content signature* (magic bytes,
  record structure), independent of filesystem metadata.
- **Parsing** — interpreting a *located* artifact's records into forensic meaning
  (the PARSER layer).
- **Recover** (as in `EwfRecover`) — reserved for *container repair* (rebuilding a
  damaged E01), a different layer from artifact/record recovery. Not a carving flag.

---

## 3. The five navigation primitives

How each evidence medium is addressed. (Full treatment: `CLAUDE.md` → *Multi-Repo
Architecture*.)

- **[P] Persistent storage** — `name → inode → block` (filesystem tree traversal).
- **[M] Memory** — `PID → EPROCESS → virtual address → physical address` (page-table walk).
- **[L] Log** — `timestamp / record-number → record boundary → field decode` (stream seek).
- **[Q] Live query** — `(endpoint, query, cursor) → result rows` (data produced, not retrieved).
- **[C] Content-addressed** — `hash → blob → content graph` (Merkle-DAG traversal; identity = hash).
- **[H] State-history** — a cross-cutting *functor*, not a sixth medium: lifts any
  base primitive to a time-indexed variant (VSS, APFS snapshots, hiberfil chains).

---

## 4. Layer hierarchy

Architectural layers; a single repo may contribute crates to several. (Full
dependency rules: `CLAUDE.md` → *The Layer Hierarchy*.)

- **KNOWLEDGE** — zero-I/O leaf: format constants + shared vocabulary
  (`forensicnomicon`), trait contracts (`state-history-forensic`, `forensic-vfs`).
  Everything depends *down* onto it; it depends on nothing.
- **CONTAINER** — decode a raw source format to an addressable byte stream (ewf,
  vmdk, qcow2, memf-format).
- **FILESYSTEM** — navigate a byte stream by path (ntfs, ext4fs, apfs); knows the
  allocation bitmap, so *unallocated = complement of allocated*.
- **PAGING** — navigate a page stream by virtual address (memf-hw).
- **OS STRUCTURE** — walk kernel objects (memf-windows, memf-linux).
- **LOG FORMAT** — navigate a log stream by timestamp/record (winevt, journal).
- **PARSER** — interpret artifact records into forensic meaning; **medium-agnostic**,
  accepts `Path` or `&[u8]`, **never** imports CONTAINER/FILESYSTEM/PAGING.
- **QUERY ENGINE / GRAPH NAVIGATION** — [Q] and [C] entry points.
- **ORCHESTRATION** — `issen`: wires all paths, correlates, emits the super-timeline.

---

## 5. Crate structure & naming

(Binding source: `CLAUDE.md` → *Crate-structure standard* + *Crate naming grammar*.)

- **`<x>-core`** — the reader/parser; exposes raw structure, no findings.
- **`<x>-forensic`** — the analyzer; emits graded `Finding`s. May depend on `-core`
  or drop lower when the audit needs raw structure the reader normalizes away.
- **Role suffixes** (multi-crate suites): `-carve` (recovery), `-memory`
  (medium-agnostic byte scanner), `-integrity` (tamper detection), `-analysis`
  (semantic, e.g. EventID→ATT&CK), `-triage` (one-click orchestrated report),
  `-cli` / `-tui` / `-mcp` (front-ends).
- **`<x>4n6`** — the CLI *binary* convention (`ev4n6`, `sqlite4n6`, `mem4n6`,
  `disk4n6`; `issen` is the orchestrator).
- **Dark parser** — a fleet capability that exists but is not wired into issen's
  auto-ingest pipeline (a stub `parse()`, or a crate with zero issen references).
  The opposite of *wired-deep*. See `issen/docs/fleet-capability-inventory.md`.

---

## 6. Report model

The normalized vocabulary every analyzer emits, so ORCHESTRATION and the GUI render
uniformly. (Binding source: `CLAUDE.md` → *The Reporting Model — `forensicnomicon::report`*.)

- **Finding** — one observation: `severity`, `category`, `code`, `note`, `source`,
  `subjects`, `evidence`, `context`. Built via a builder, never a struct literal.
- **Severity** — `Info < Low < Medium < High < Critical`; `Option<Severity>` where
  `None` ("not scored") is distinct from `Some(Info)` ("scored, benign").
- **Category** — the analytical lens: `Integrity, Structure, Residue, Provenance,
  History, Concealment, Threat`.
- **`code`** — a published contract: scheme-prefixed SCREAMING-KEBAB
  (`MEM-PROCESS-HOLLOWING`). Never changed once shipped.
- **Observation** — the producer trait an analyzer's typed anomaly kind implements
  to convert into a `Finding`. `RecoveryMethod`/`Carver` are its siblings for the
  carving path.
- **ExternalRef** — e.g. `mitre_attack("T1055.012")`: **"consistent with"**, never a
  verdict (§1).
- **Findings are observations, never legal conclusions** — the analyst/tribunal
  concludes (§1).

---

## 7. Evidence & test-data tiers

Trust tiers for empirical claims (distinct from *carving* tiers in §2). (Binding
source: `CLAUDE.md` → *Evidence-Based Rigor*.)

- **Tier 1** — an independent third party authored the artifact **and** the answer
  key, or it is real-world data. The gold standard for correctness.
- **Tier 2** — real engine/tool output whose ground truth is derivable from the
  documented construction or confirmed by an independent oracle.
- **Tier 3** — you authored both the fixture and the expected answer, nothing
  independent vouching — the maximal self-deception risk (the "LZNT1 trap"). Fine as
  fast CI regression scaffolding *under* a T1/T2 oracle; never the sole validation
  of a value-producing, oracle-checkable path.
