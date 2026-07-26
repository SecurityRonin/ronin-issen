# 0015 — PRD & ADR standard: preserve the rationale (every non-internal repo; pre-push gate)

**Status:** Accepted

## Context

The *why* behind what shipped is lost the moment the author's context evaporates.
Every non-internal fleet repo must preserve its rationale in durable, discoverable
docs. Two artifacts answer different questions and carry different honesty risks, so
they are gated at different tiers. Scope is **repo-level, not per-crate**: a
multi-crate repo gets ONE repo-level PRD and ONE `docs/decisions/` set, never one per
member.

## Decision

**ADRs — gated FLEET-WIDE (every non-internal repo).** Each repo carries
`docs/decisions/NNNN-title.md` capturing its **load-bearing decisions**: the
reader/analyzer (`core/`+`forensic/`) split, dependency direction, `forbid(unsafe)`
vs `deny`+bounded-allow, format/offset/endianness choices, crate-naming decisions
(e.g. the `bluetooth-forensic-core` rename around the crates.io `bluetooth_core`
collision), the `-core` low-MSRV floor, batteries-included feature calls. ADRs
**reverse-write honestly**: a decision + its context + consequences genuinely
happened and is visible in the code, so reconstructing one is real history, not
fiction. They are lightweight and additive (one per decision). Reverse-write the key
past decisions wherever a `docs/decisions/` dir is missing or empty.

**PRD — gated ONLY for the user-facing PRODUCT tier (~15-20 repos).** A PRD is a
*requirements* artifact (users, use cases, scope, non-goals, success criteria); it
only makes sense where there is a genuine **product to have requirements for** — the
things an examiner *runs*: the `<x>4n6` CLIs, browser-forensic, disk-forensic, issen,
the `-gui` tools, MCP servers. Library crates — the things a developer *links*
(`safe-read`, `forensicnomicon`, the `*-core` readers, KNOWLEDGE leaves, contract
crates) — do **NOT** get a product PRD; forcing one produces a hollow,
reverse-engineered fiction that violates the anti-stale-doc discipline. A library's
`docs/PRD.md` is instead a LIGHTER artifact — a concise **Purpose & Scope** (what it
is, who links it, scope/non-goals). **The filename is unified — `docs/PRD.md` for
every tier ([ADR-0003](0003-doc-naming-conventions.md)); only the content depth
varies.** There is no `docs/DESIGN.md` and no README-only intent section.

**The product-vs-library line (how to assign the tier):** a repo is **product tier**
if it ships a binary an examiner runs (a `<x>4n6` CLI, a GUI, an MCP server) OR is a
full analyzer suite with a user-facing front-end. It is **library tier** if it is
only *linked* (container/filesystem readers, `*-core` crates, KNOWLEDGE/contract
leaves, pure-computation codecs). A repo that is both a library and a CLI (e.g.
blazehash, sqlite-forensic) is **product tier** (it has a runnable surface) and gets
both the PRD and the ADRs.

**Reverse-writing produces REAL artifacts, never stubs.** A stub-to-pass-the-gate is
worse than nothing — a hollow doc reads as current and misleads. Reverse-writing is
genuine per-repo research: read the code, README, and git history; state what the
tool actually is, who uses it, its real scope/non-goals, and the decisions that
shaped it. If the honest artifact is thin, it is thin *and true*, not padded.

## Pre-push gate (enforced before every push to GitHub; mirrored CI-side)

- **Every non-internal repo:** `docs/decisions/` holds ≥1 real ADR, AND `docs/PRD.md`
  exists (a full PRD for product tier; a lighter Purpose & Scope — same filename — for
  library tier).
- **Validation evidence** (repos making correctness claims): `docs/validation.md`
  (canonical name, not `corpus-validation.md`).
- Enforcement follows the fleet pre-commit⇄CI-parity pattern: a `pre-push` hook
  blocks the push locally, and a CI `docs-gate` job fails red as the backstop. The
  gate checks *presence + non-emptiness*, not prose quality — the "real artifact, not
  stub" bar is a review discipline, not something CI can grade.
- **Internal-only repos are exempt** (the `ronin-issen` umbrella itself, throwaway
  scaffolding). When in doubt, a repo that is published or externally consumed is
  *not* internal and is in scope.

## Consequences

- Every non-internal repo becomes self-documenting for *why* it is shaped the way it
  is, surviving author turnover.
- The doc gate is content work (reverse-writing real artifacts), not a file-existence
  checkbox — CI enforces presence, review enforces honesty.
- Filename discipline (`docs/PRD.md` everywhere, `docs/validation.md`,
  `docs/decisions/NNNN-*`) is owned by [ADR-0003](0003-doc-naming-conventions.md);
  internal-crate exemption by [ADR-0005](0005-internal-crates-never-published.md).
