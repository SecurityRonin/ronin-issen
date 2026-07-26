# 7. The normalized reporting model — `forensicnomicon::report`

Date: 2026-07-26
Status: Accepted

## Context

Format specs are one role of the KNOWLEDGE leaf; the **normalized reporting
vocabulary** is the other. Before it existed, every analyzer shipped its own bespoke
`XxxAnalysis` type, so ORCHESTRATION (Issen, disk4n6) and any future GUI had to render
N unrelated shapes. We wanted one model every analyzer emits, so consumers render
findings uniformly. The model is the **union (superset) of the analyzers' data, not a
flattening** — no analyzer loses information by conforming to it.

(Companion: issen's own ADR-0002 "forensicnomicon knowledge leaf and report model"
records the same decision from the orchestrator's side.)

## Decision

Every analyzer in the fleet emits its findings as the single `forensicnomicon::report`
model.

### Core types (`forensicnomicon::report`)

- `Severity` — `Info < Low < Medium < High < Critical`. A finding carries
  `Option<Severity>`: `None` ("not scored") is forensically distinct from
  `Some(Info)` ("scored, benign"). Emit `None` only when the analyzer genuinely
  cannot grade in isolation (e.g. a PE writable+executable section); otherwise grade.
- `Category` — the analytical lens: `Integrity, Structure, Residue, Provenance,
  History, Concealment, Threat`. Coarse by design; fine taxonomy lives in `code` + MITRE.
- `Finding { severity, category, code, note, source, subjects, evidence, context }`
  — constructed **only** via `Finding::observation(sev, cat, code)` /
  `Finding::unrated(cat, code)` + the returned builder, never a struct literal.
- `FindingContext { confidence, occurrences, timestamps, external_refs, tags }`
  — the behavioral superset; disk findings leave it empty, memory/winevt/srum populate it.
- `Location` — `ByteOffset/Lba/Sector/Rva/RecordId/Path/Field/Key/Other{space,value}`.
- `SubjectRef { scheme, kind, id, label }` — non-disk subjects (process/module/registry/…).
- `ExternalRef` (e.g. `ExternalRef::mitre_attack("T1055.012")`) — **"consistent with", never a verdict.**
- `Report { findings, provenance, timeline, metadata }` — the aggregate Issen renders;
  `Report::{max_severity, findings_at_least, unrated_findings}`.

### The producer pattern

Each analyzer KEEPS its typed `AnomalyKind`/event type (domain knowledge) and
converts to canonical Findings — `forensicnomicon` never enumerates every anomaly kind:

- **Static codes** → `impl forensicnomicon::report::Observation` for the kind
  (`severity/category/code/note` required; `subjects/evidence/mitre/confidence` optional).
  `Observation::to_finding(Source)` assembles the `Finding` in one place.
- **Dynamic codes** (usnjrnl rule names, memory `Finding::Other(String)`, srum filter
  flags) → an inherent `fn to_finding(&self, Source) -> Finding` using the builder directly,
  because `Observation::code()` returns `&'static str`.

### Conventions (binding across the fleet)

- **`code` is a published contract**: scheme-prefixed SCREAMING-KEBAB
  (`VMDK-RGD-MISMATCH`, `MBR-PART-OVERLAP`, `MEM-PROCESS-HOLLOWING`,
  `WINEVT-PROVIDER-GUID-SPOOFING`). Never change a shipped code; new variants get new codes.
- **Category** defaults to `Category::from_code(code)`; override per-variant only where the
  keyword classifier is wrong (e.g. overloaded `BOOT-` prefixes).
- **Findings are observations, never legal conclusions** — the analyst/tribunal concludes.
  Use "consistent with" for MITRE/threat narration.
- **`#[non_exhaustive]` + builders** keep the model additively evolvable: a new field,
  `Location`, or `Category` variant is a non-breaking `forensicnomicon` minor bump, not a
  fleet-wide break. Consumers must use a `_` arm when matching the shared enums.

### Severity normalization (the canonical mapping every analyzer applies)

| Native scale | → canonical |
|---|---|
| 5-level (mbr, gpt, apm, iso9660, usnjrnl, memory) | identity |
| 4-level (vhdx, ewf, winevt, ese-integrity) | `Info→Info, Warning→Medium, Error→High, Critical→Critical` |
| 3-level (vmdk: `Info/Warning/Error`) | per-variant re-grade (a forensic judgment, not a blanket rename) |
| triage (srum-analysis: `Clean/Informational/Suspicious/Critical`) | `Clean→Info, Informational→Low, Suspicious→High, Critical→Critical` |
| unrated (exec-pe `PeAnomaly`) | graded per-variant on migration, or `severity: None` |

## Consequences

- ORCHESTRATION and a future GUI render one model, not N bespoke `XxxAnalysis` types.
- **Dependency direction is unchanged:** `forensicnomicon` is the leaf — every analyzer
  depends **down** onto it; it depends on no one. Adding `report` did not change that.
  disk-forensic / Issen depend down onto both the migrated analyzers and
  `forensicnomicon::report` to aggregate findings into one `Report`.
- The model evolves additively (`#[non_exhaustive]` + builders): new fields/variants are
  non-breaking minor bumps, so the fleet does not break in lockstep on a schema change.
