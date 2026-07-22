# SecurityRonin Fleet Glossary

Canonical definitions for the vocabulary, concepts, and **epistemology** used across
the forensic fleet. A *reference*, not law: it defines terms and points at the binding
sources. The **rules** live in `CLAUDE.md` (the constitution) and the ADRs
(`docs/decisions/`); a definition here that conflicts with a rule there is a bug in
this file — fix the glossary, the rule wins.

**Two parts.** **Part A** is *general* forensic/DFIR knowledge — portable, true
anywhere, safe to share with anyone. **Part B** is *SecurityRonin-fleet-specific* —
our crates, flags, layers, and coinages — and each entry links **back up** to the Part
A concept it instantiates. When a term is universal, define it once in A and reference
it from B; never duplicate.

**Living document.** Seeded with the highest-value cross-cutting terms; extend it
whenever a new fleet-wide concept is settled.

---

# Part A — General forensic concepts (portable)

## A1. Epistemology — three layers of a forensic claim

The most important distinction in the fleet. Every statement a tool emits — a finding,
a caption, a UI label, a flag name — sits in exactly one layer. Keep them distinct;
never let a lower-confidence layer wear the clothes of a higher one. (Binding source:
`CLAUDE.md` → *Expert Witness Reports — Three Layers of Epistemic Authority* and *Name
evidence by the state or mechanism actually measured*.)

1. **Observed fact** — what the evidence directly shows. State as a finding. *"an
   `$MFT` record has its `IN_USE` flag cleared"; "these sectors are claimed by no
   allocation structure".*
2. **Forensic inference** — what the pattern is **consistent with**. Use "consistent
   with" / "not consistent with" — never "confirms", "proves", "establishes".
   *"consistent with intentional deletion".*
3. **Legal conclusion** — whether conduct is a crime, fraud, or breach. For the
   **tribunal**, not the tool or the expert. *"the Court may draw its own conclusions."*

**Name the observable, never the conclusion** (the naming corollary). A default name is
a layer-1 claim, and a name that asserts a layer-2 story asserts it on *every*
invocation. So the name states the measured state, not the intent it suggests:

| Observed state (correct) | Conclusion smuggled in (wrong) |
|---|---|
| `unallocated` (no allocation structure claims it) | `deleted` (asserts a deliberate act) |
| repeated failed logins | "brute-force attack" |
| sustained memory growth | "memory leak" |
| an on-disk file found running in memory | "malware injection" |

The conclusion-word is legitimate **only where the conclusion is itself the recorded
observable** — an `$MFT` record *flagged* deleted may be called deleted, because the
flag (not the deletion act, not the intent) is what was observed; even then prose
attributes it: *"recorded as deleted by the filesystem."* The test: *could the same
observed state have arisen without the story the name tells?* If yes, name the state.

## A2. Attribution — activity ≠ identity ≠ attribution (the FACT framework)

Attribution is the discipline of *not* confusing what a device/account did with who did
it. The fleet adopts **Brett Shavers' FACT Attribution Framework™** (v1.1, Dec 2025) as
the reference model, because it makes the ladder our epistemology (A1) implies explicit:

> *"DF/IR fails at the exact moment someone confuses **activity** with **identity**, and
> then confuses **identity** with **attribution**."* — B. Shavers

**The identity ladder** — a finding sits on exactly one rung, and a tool must not
silently promote it: `artifact → device → account → user/session → person`.

**Three kinds of attribution** (increasing scope; a forensic *tool* reaches only the first):

- **Technical attribution** — associating observed activity with specific artifacts,
  devices, accounts, or sessions. The examiner's/tool's core expertise. It does **not**
  by itself establish which *person* acted.
- **Investigative attribution** — integrating digital **and** non-digital evidence
  (physical, testimonial, behavioral, organizational) to identify the most plausible
  person and exclude reasonable alternatives. An investigative function.
- **Legal attribution** — formal assignment of responsibility by a court, tribunal, or
  regulator under the applicable burden of proof.

**The F.A.C.T. four stages:** **F**orensic Compliance (legal authority + acquisition
validity) → **A**nalyze Evidence (identification: device/account/action) → **C**orrelate
& Sequence (bridge evidence↔identity via temporal coherence) → **T**estify & Transfer
Findings (defensible articulation; separate the examiner from the attribution role).

**Fleet rule:** a SecurityRonin tool produces **technical attribution only** — it links
an artifact to a device/account/session (the lower rungs). It never asserts person-level
(investigative/legal) attribution; that is the analyst's and the tribunal's, exactly as
A1 layer-3 is handed off. Provenance we stamp (e.g. a carved artifact's owning process —
see [B5](#b5-recovery-provenance--attribution-in-the-fleet)) is technical attribution,
labeled as such.

*Source:* Brett Shavers, *FACT Attribution Framework* — DOI-registered, open access:
<https://zenodo.org/records/18005597> · author: <https://brettshavers.com/>.

## A3. Data states — the vocabulary of recovery

- **Live set** — the allocated, referenced, in-use files a normal filesystem walk
  returns. Every tool's default view.
- **Allocated / Unallocated** — whether an allocation structure (`$Bitmap`, block-group
  descriptor, freelist) claims a region. **Unallocated** is a pure layer-1 observation
  (*no structure references these bytes*); it carries **no** claim the data was ever
  deleted — it may be a deleted file, a reformatted prior volume, or bytes never
  referenced at all. (See A1: `unallocated` observed, `deleted` inferred.)
- **Tombstone** — a filesystem record that itself **records a deletion**: an `$MFT`
  record with `IN_USE` cleared, an ext4 orphan inode. Here a deletion event was
  *observed* (the FS asserts it), so **deleted** is a layer-1 fact here, not an inference.
- **Slack** — unused bytes between a file's logical end and the end of its last allocated
  cluster/block; may hold prior-file residue.
- **Residual data** — the union: everything outside the live set that is recoverable,
  whether FS-recorded-deleted (tombstones) or carved from unallocated space.

## A4. Carving & the tier test (medium-universal)

- **Carving** — recovering an artifact by its *content signature* (magic bytes, record
  structure), independent of filesystem metadata. Contrast **parsing** (interpreting a
  *located* artifact) and container **recovery**/repair (rebuilding a damaged image).
- **The tier test** — *is the cost bounded by the artifact already in hand, or by the
  whole medium?* It decides what runs by default, identically on disk, memory, and log:
  - **Tier 1 — bounded / file-internal.** Recovery within an artifact already located
    (freelist/WAL/slack, a located in-memory region). Cost O(artifact). **Default-on.**
  - **Tier 2 — whole-medium.** Signature-scan the *entire* image/dump for orphaned
    artifacts. Cost O(image)/O(dump). **Opt-in.**

## A5. Evidence & test-data trust tiers

(Distinct from the *carving* tiers in A4. Binding source: `CLAUDE.md` → *Evidence-Based
Rigor*.)

- **Tier 1** — an independent third party authored the artifact **and** the answer key,
  or it is real-world data. Gold standard.
- **Tier 2** — real engine/tool output whose ground truth is derivable from the
  documented construction or confirmed by an independent oracle.
- **Tier 3** — you authored both the fixture and the expected answer, nothing
  independent vouching (the "LZNT1 trap"). Fine as fast CI regression scaffolding *under*
  a T1/T2 oracle; never the sole validation of a value-producing, oracle-checkable path.

## A6. Report primitives (general)

- **Finding / Observation** — a single observed fact plus its grade; never a legal
  conclusion (A1).
- **Severity** — an ordered scale; "not scored" is distinct from "scored, benign".
- **Provenance** — how/where a datum was obtained, carried with it so downstream
  consumers can weigh and filter it.
- **Confidence** — a graded, stated likelihood; qualitative confidence is never rendered
  as false-precision quantitative area (no radar charts of vibes).

---

# Part B — SecurityRonin fleet specifics

Each entry instantiates a Part A concept; the up-links show which.

## B1. The recovery flags

The fleet-wide recovery taxonomy. **Authority: fleet ADR 0001**
([`decisions/0001-fleet-carving-flags-sweep-engine-contract.md`](decisions/0001-fleet-carving-flags-sweep-engine-contract.md))
— the decision + rationale (why `--unallocated` over `--deleted`/`--non-live`, the
tombstone reconciliation, the sweep engine + contract). This table is the *definition*;
the ADR is the *record*.
Instantiates → [A3](#a3-data-states--the-vocabulary-of-recovery),
[A4](#a4-carving--the-tier-test-medium-universal).

| Flag | Recovers | Cost | Default |
|---|---|---|---|
| *(none)* | Tier-1 file-internal carving (freelist/WAL/`ElfChnk` slack in located files) | O(artifact) | **on** |
| `--deleted [latest\|all\|off]` | FS-**recorded** tombstones (A3) — *unchanged; correctly named* | cheap | off |
| `--unallocated` (alias `--unalloc`) | Tier-2 whole-image unallocated carving — allocation **observation**, no intent claim (A1) | O(image) | off |
| `--residual` | **Both** of the above — all recoverable data outside the live file set | both | off |

- `--deleted` means a *recorded* deletion (A3 tombstone) and is **not** a synonym for
  carving; `ntfs deleted_nodes()` and `4n6mount --deleted latest|all|off` are its
  long-standing correct implementations.
- `--unallocated` names the **observation** (A1), deliberately not `--deleted` (asserts
  intent) nor `--non-live` (collides with *live-response / live acquisition*).
- `--residual`'s help text is observational — *"all recoverable data outside the live
  file set"* — not "everything deleted".
- **Memory:** same tier test (A4). Bounded (located-region) carving is default-on;
  whole-dump scanning is opt-in until a shared, measured single pass exists. Memory
  carving is a separate axis from the disk flags (design in progress; see the carving ADR).

## B2. Layer hierarchy & the five navigation primitives

Instantiates → the general medium/addressing model. (Full treatment: `CLAUDE.md` →
*Multi-Repo Architecture*.)

- **Navigation primitives:** **[P]** disk `name→inode→block` · **[M]** memory
  `PID→EPROCESS→VA→PA` · **[L]** log `timestamp/record→field` · **[Q]** live query
  `(endpoint,query,cursor)→rows` · **[C]** content-addressed `hash→blob→graph` · **[H]**
  state-history (a cross-cutting *functor* lifting any primitive to a time-indexed variant).
- **Layers (top depends down):** KNOWLEDGE (`forensicnomicon`, `forensic-vfs`,
  `state-history-forensic` — zero-I/O) → CONTAINER (ewf, vmdk, memf-format) → FILESYSTEM
  (ntfs, ext4fs, apfs) / PAGING (memf-hw / memf-core) / OS STRUCTURE (memf-windows) / LOG
  FORMAT (winevt) → PARSER (medium-agnostic; **never** imports CONTAINER/FILESYSTEM/PAGING)
  → ORCHESTRATION (`issen`).

## B3. Crate structure & naming

(Binding source: `CLAUDE.md` → *Crate-structure standard* + *Crate naming grammar*.)

- **`<x>-core`** — the reader/parser; raw structure, no findings.
- **`<x>-forensic`** — the analyzer; emits graded findings; may depend on `-core` or drop
  lower when the audit needs raw structure the reader normalizes away.
- **Role suffixes:** `-carve` (recovery — A4), `-memory` (interpreter of memory-resident
  runtime structures), `-integrity` (tamper), `-analysis` (semantic, e.g. EventID→ATT&CK),
  `-triage` (one-click orchestrated report), `-cli`/`-tui`/`-mcp` (front-ends).
- **`<x>4n6`** — the CLI *binary* convention (`ev4n6`, `sqlite4n6`, `mem4n6`, `disk4n6`;
  `issen` is the orchestrator).
- **Dark parser** — a fleet capability that exists but is not wired into issen's
  auto-ingest (a stub `parse()`, or zero issen references); opposite of *wired-deep*. See
  `issen/docs/fleet-capability-inventory.md`.

## B4. The report model — `forensicnomicon::report`

The normalized vocabulary every analyzer emits. Instantiates →
[A1](#a1-epistemology--three-layers-of-a-forensic-claim),
[A6](#a6-report-primitives-general). (Binding source: `CLAUDE.md` → *The Reporting Model*.)

- **Finding** — `severity, category, code, note, source, subjects, evidence, context`;
  built via a builder, never a struct literal.
- **Severity** — `Info < Low < Medium < High < Critical`; `Option<Severity>` (`None` =
  "not scored" ≠ `Some(Info)` = "scored, benign").
- **Category** — the analytical lens: `Integrity, Structure, Residue, Provenance,
  History, Concealment, Threat`.
- **`code`** — a published contract: scheme-prefixed SCREAMING-KEBAB
  (`MEM-PROCESS-HOLLOWING`); never changed once shipped.
- **Observation** — the producer trait an analyzer's typed anomaly kind implements to
  convert into a `Finding`.
- **ExternalRef** — e.g. `mitre_attack("T1055.012")`: **"consistent with"**, never a
  verdict (A1).
- **Findings are observations, never legal conclusions** — the analyst/tribunal concludes.

## B5. Recovery provenance & attribution in the fleet

Instantiates → [A2](#a2-attribution--activity--identity--attribution-the-fact-framework),
[A4](#a4-carving--the-tier-test-medium-universal).

Every recovered/carved item is tagged with **how and where** it was recovered — the
recovery method (file-internal / unallocated / memory), the absolute offset, and a
confidence — so machine output round-trips it and an analyst can filter carved evidence
from live. A carved record indistinguishable from a live one is a fabrication hazard; the
tag is structural, not optional.

For memory-carved items, the provenance additionally records the owning process
(PID/name), the VA region kind, and the physical offset. **Per FACT (A2) this is
technical attribution only** — it links an artifact to a device/account/session, never to
a *person*. The fleet stamps and labels it as such; it never promotes it up the identity
ladder.

The provenance type is `forensic_carve::RecoveryMethod { Tombstone, FileInternalCarve,
UnallocatedCarve, MemoryCarve }` (fleet ADR 0001 §3). The pre-existing
`browser-forensic-carve::RecoveryMethod` is renamed `SqliteRecoveryMethod` — a
record-substrate detail *under* `FileInternalCarve`, not a second fleet-level type.
