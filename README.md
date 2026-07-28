<p align="center">
  <img src="assets/issen-banner.png#gh-dark-mode-only"
       alt="ronin-issen — SecurityRonin forensic-fleet umbrella" width="640" />
  <img src="assets/issen-banner-light.png#gh-light-mode-only"
       alt="ronin-issen — SecurityRonin forensic-fleet umbrella" width="640" />
</p>

# ronin-issen — SecurityRonin forensic-fleet umbrella

**Governance root for the SecurityRonin forensic fleet.** This is a **docs-only** repo:
it holds the fleet *constitution* and migration plan — not code. Component repos
(parsers, container readers, the `*4n6` CLIs, the issen capstone, …) live under
`components/<category>/<repo>` as their **own independent git repos** and are gitignored
here, by design — this is deliberately *not* a monorepo (see [`REORG.md`](REORG.md) §1, §4.2).

## What's here

| Path | What it is |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | **The fleet constitution.** Layer hierarchy, crate naming, the reader/analyzer (`core`/`forensic`) split, the Paranoid-Gatekeeper security standard, and the README / corpus / validation / **release & Windows code-signing** / secrets / distribution standards. Every component inherits it (via `@import`, and parent-dir loading once repos move under `components/`). |
| [`REORG.md`](REORG.md) | The `components/` reorganization taxonomy + decisions. |
| [`docs/components-diagram.html`](docs/components-diagram.html) | Rendered component layout — tier flow (evidence → timeline) + the cross-cutting rail. Self-contained dark-theme SVG; open locally in any browser. |
| `docs/` | Fleet-wide reference (corpus catalog, etc.). |
| `components/`, `_deprecated/` | The actual fleet repos — **separate gits, never tracked here** (gitignored). |

## Why this repo doesn't wear the product-README standard

The fleet's README / badge / GitHub-Pages / Privacy-Terms standard targets **published
crates and CLIs** and their end users. `ronin-issen` is a **governance / umbrella** repo —
its audience is fleet maintainers, so it carries a governance README (this file), stays
**private**, and is secret-scanned, but skips the crates.io/docs.rs badges, the 30-second
install hook, and the public docs-site apparatus. Standards bend to repo **role** — the
same principle as MSRV-by-role.

Private · © 2026 Security Ronin Ltd
