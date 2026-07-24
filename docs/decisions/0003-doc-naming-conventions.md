# 3. Canonical documentation filenames across the fleet

Date: 2026-07-24
Status: Accepted

## Context

The per-repo documentation standard (`CLAUDE.md` → "PRD & ADR Standard") mandates a
PRD/intent doc, ADRs, and validation evidence in every non-internal repo. Left to
per-repo drift, the *filenames* diverged and broke the fleet's own "one concept, one
name" discipline:

- the intent doc appeared as `docs/PRD.md`, `docs/DESIGN.md`, and an inline README
  "Purpose & Scope" section — three names for one artifact;
- validation evidence appeared as `docs/validation.md` (61 repos) and
  `docs/corpus-validation.md` (2 repos) for the same purpose.

A reader (or a `docs-gate` CI check) cannot rely on a path that has three spellings,
and cross-repo links and tooling break when the same artifact is named differently
per repo.

## Decision

One canonical filename per documentation artifact, fleet-wide:

- **ADRs → `docs/decisions/NNNN-title.md`** (zero-padded sequence, Nygard format:
  `# N. Title` / `Date` / `Status` / `## Context` / `## Decision` / `## Consequences`).
- **Intent doc → `docs/PRD.md`, always, every tier.** The *filename* is unified;
  the *content depth* varies by tier (a product ships a full PRD — problem, users,
  scope, non-goals, validation approach; a library ships a lighter Purpose & Scope
  in the same `docs/PRD.md`). There is no `docs/DESIGN.md` and no README-only intent
  section — "PRD is PRD, not DESIGN."
- **Validation evidence → `docs/validation.md`, always.** Not `corpus-validation.md`
  or any other spelling; a carving/recovery comparison against a reference tool is a
  section *within* `validation.md` (or a clearly-named sibling like
  `docs/recovery-comparison.md` only when it is a distinct, large artifact — the
  Doer-Checker evidence itself lives in `validation.md`).

## Consequences

- The `docs-gate` (pre-push hook + CI) checks these exact paths, so it is
  deterministic across every repo.
- Existing `docs/DESIGN.md` and README "Purpose & Scope" sections are migrated to
  `docs/PRD.md`; the two `docs/corpus-validation.md` files fold into
  `docs/validation.md`.
- `CLAUDE.md`'s PRD & ADR Standard references this ADR as the naming authority and
  no longer offers `DESIGN.md`/README-section alternatives.
- New repos and the reverse-write wave emit only these canonical names.
