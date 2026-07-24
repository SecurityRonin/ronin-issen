# 5. Internal / workspace-only crates are never published to crates.io

Date: 2026-07-24
Status: Accepted

## Context

The fleet's release automation (release-plz) publishes any workspace member whose
version is ahead of crates.io. Many fleet crates are **internal implementation
details of an application** — e.g. the ~62 `issen-*` crates that make up the Issen
orchestrator (parsers, carvers, providers, correlation, CLI glue). These exist only
to structure one binary; no external consumer should ever `cargo add` them.

Publishing such crates is a one-way mistake: crates.io **claims a name forever on
first publish** and a version can be yanked but never deleted. Auto-publishing 62
internal `issen-*` crates would permanently squat 62 registry names, pollute search,
imply an external-support contract we don't offer, and expand the fleet's public API
surface to code that was never meant to be depended on.

## Decision

**A crate that is an internal implementation detail of an application is NEVER
published to crates.io.** Concretely:

- Mark every internal member `publish = false` in its own `Cargo.toml` AND
  `release = false` in the repo's `release-plz.toml` (belt-and-suspenders — the first
  stops `cargo publish`, the second stops release-plz).
- The **application binary itself** ships through the app pipeline (a signed `v*` tag
  → `release.yml` → GitHub Release + Homebrew/apt/winget), NOT crates.io.
- Only crates with genuine **third-party reuse value** — a reader/analyzer/codec/
  contract another repo could legitimately link — are published. When in doubt, a
  crate is internal (do not publish); publishing is the deliberate, reversible-only-
  by-yank exception.

**The test:** *would an external developer ever add this crate as a dependency of a
different project?* If no, it is internal → `publish = false` + `release = false`.
Application-internal crates (the `issen-*` members, a binary's private helper crates)
answer no by construction.

## Consequences

- `issen` and every future application repo declare their internal members
  `publish = false` + `release = false`; release-plz never cuts them, and a stray
  `cargo publish` is refused by cargo itself.
- The published fleet surface stays limited to the deliberately-public libraries
  (readers, analyzers, `*-core` crates, contract leaves, codecs, tooling libs).
- This complements the PRD/ADR standard's product-vs-library tiering: *product*
  repos have a runnable surface but their internal crates are still `publish = false`;
  the runnable surface ships via the app pipeline, not the registry.
- Reversing an accidental internal publish is limited to a yank (name stays claimed),
  which is exactly why the gate is `publish = false` at the source, not a post-hoc cleanup.
