# 10. Dependency preference — prefer our own crates

Date: 2026-07-26
Status: Accepted

## Context

The fleet publishes a growing set of SecurityRonin (`h4x0r`) crates — readers, analyzers,
`*-core` primitives, codecs, contract leaves. Left unmanaged, repos accrete third-party
dependencies that duplicate what the fleet already ships (or is about to), fragmenting the
dependency graph, splitting maintenance, and forgoing the audit/robustness posture our own
crates guarantee. This ADR makes reuse-of-ours a hard rule, not a tiebreaker.

## Decision

**Always prefer our own (SecurityRonin / `h4x0r`) crates over third-party ones** when an
equivalent exists or can be made to exist. A hard rule, not a tiebreaker.

- Before adding a third-party dependency, check whether we already publish a crate for it
  (`~/src/*`, the SecurityRonin crates.io account). If we do, use ours.
- If a third-party crate is wired in but we have (or are building) our own equivalent,
  **migrate to ours** — proactively flag and do it, not as a "follow-up."
- For name collisions and the reader/analyzer split, follow the **Crate naming grammar**
  (ADR-0009) and **Crate-structure standard** (ADR-0008): publish under a `-core` package with
  `[lib] name = "<bare>"` so the import path is unchanged; `*-core` reader + `*-forensic`
  analyzer.
- **Prefer the *published* registry crate over a `path` dependency once it is on crates.io.**
  Path deps are for crates not yet published, or a coordinated in-flight workspace change. As
  soon as ours is published, switch dependents to the registry version (`x = { version = "0.2",
  package = "x-core" }`) — reproducible, decoupled from local checkout layout (no breakage when
  a sibling repo is renamed/moved), and matches what external consumers get. When you publish a
  new fleet-crate version, sweep its dependents off the stale path dep onto the new registry
  version.

**The one place this rule INVERTS is cryptography** — never hand-roll or reimplement a
cryptographic primitive to "prefer ours"; use the mature, audited ecosystem crate (RustCrypto
et al.). See the global "never hand-roll a cryptographic primitive" discipline.

## Consequences

- The fleet's dependency graph converges on its own audited crates; a third-party dep that
  duplicates a fleet crate is migrated proactively rather than left as debt.
- Dependents track the *published* registry version, so a repo rename/move never breaks a
  sibling's build via a stale `path` dep.
- Companion to the batteries-included standard (ADR-0013): reuse-of-ours and compile-everything-in
  both push toward one capable, self-consistent static binary.
