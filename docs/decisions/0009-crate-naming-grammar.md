# 9. Crate naming grammar

Date: 2026-07-26
Status: Accepted

## Context

A crate name is read *bare* — in crates.io search, `cargo add`, and transitive dependency
lists — with all repo/GitHub context stripped. Names chosen ad hoc drift (`-rt` in one repo,
`-triage` in another), over-claim (a suite analyzer renamed `<repo>-forensic`), or fail to
claim a namespace (a generic-word prefix that reads as an unrelated third-party lib). This
grammar fixes one naming pattern per repo shape so names are self-describing and consistent
fleet-wide. It applies to every fleet repo; decide which shape a repo is *before* naming its
crates.

## Decision

**Pattern A — single-format repo** (containers/filesystems: vmdk, vhdx, ntfs, qcow2, segb).
Exactly two crates: `<x>-core` (reader) + `<x>-forensic` (analyzer). The `<x>-forensic`
*crate* name is reserved for this one-reader/one-analyzer shape (see the Crate-structure
standard, ADR-0008).

**Pattern B — multi-crate PARSER/domain suite** (browser, winevt, memf). Decompose *by
concern* with role suffixes. The repo name is the **umbrella and is NOT itself a crate** —
`memory-forensic` → `memf-*`, `winevt-forensic` → `winevt-*`, `browser-forensic` →
`browser-forensic-*` (its short form `browser-*` is a generic word → keep the full prefix;
see the self-describing rule below); there is no `memory-forensic` / `winevt-forensic` /
`browser-forensic` *crate*. Never rename a suite's analyzer to `<repo>-forensic` (it
over-claims, collides with the repo name, and breaks Pattern B).

**Per-parser invariant — every parser is a reader *and* an analyzer (binding).** A "suite"
(Pattern B) is an *organizational* grouping of parsers under one repo/prefix; it is **not** a
licence to ship a parser as a reader alone. Every parser — a Pattern-A `<x>` or a Pattern-B
*family-name* reader crate — owes both a reader and an analyzer, because reading and analysis
are different concerns pulling in opposite directions (a reader normalizes/skips broken data;
an auditor must *see* it — ADR-0008). In Pattern B this means each *family-name* reader
(`browser-forensic-chrome`) has a matching analyzer; the `-integrity` / `-analysis` slots are
where those analyzers live, never an excuse to omit them. A reader with no analyzer is an
*incomplete parser*, not a smaller one.

**The invariant is scoped to PARSERS — a `-core` suffix does not imply one.** `-core` is
overloaded: a *reader* core (a parser over an evidence artifact format) sits beside *domain /
shared-types* cores (`forensicnomicon-core` — the report model itself), *utility* cores
(`blazehash-core`, `timeglyph-core`), *codec* primitives (`lzvn-core`), and the *orchestrator*
core (`issen-core`). None of the latter parse evidence, so none owe a `-forensic` — they are
not parsers, not "exempt parsers." So the question a reviewer or a CI check must answer is *"is
this a parser?"*, never *"does it have a `-core`?"*: the second is a naming coincidence, not the
property. (This is exactly the misclassification to avoid — `forensicnomicon-core` having no
`forensicnomicon-forensic` is correct, because `forensicnomicon` is foundation, not a parser.)

**Suite vs. co-located parsers — decide by the dependency arrows, not the folder.** Crates
sharing a repo are a genuine *suite* only if they share code (inter-crate `path` deps on a
common `-core` / domain crate). Parsers that sit in one repo but have **zero** inter-crate
dependencies are not a suite — they are independent Pattern-A parsers that merely co-locate,
and each takes the Pattern-A `<x>-core` + `<x>-forensic` shape in its own right. (Lived:
`chromium-storage-{cache,indexeddb,localstorage}` were grouped as a "suite" yet share no code —
each depends only on `forensicnomicon` and leaf reader crates, never a sibling; each is its own
parser and now carries its own core/forensic pair.)

**Member directories are named for their ROLE, the crate for the format.** A
single-parser repo's directories are `core/`, `forensic/`, `fuse/`, `cli/` — not
`<x>-core/`, `<x>-forensic/`. The crate keeps its format-prefixed name via
`package.name`; only the directory is the bare role. (A multi-parser co-located
repo is the sole exception — three parsers cannot each own a `core/`, so it keeps
crate-named directories; a Pattern-B suite nests its crates under `crates/`.)
Enforced by `scripts/fleet_structure_check.py` (fleet root), which also enforces
the per-parser pairing above; its self-test proves both gates go red.

Suffixes:

| suffix | role | examples |
|---|---|---|
| `-core` | shared/domain types + format constants | browser-forensic-core, winevt-core |
| *family name* | a reader (one format/source) | browser-forensic-chrome / -firefox / -safari |
| `-carve` | recovery (free-page / WAL / record / unallocated) | browser-forensic-carve, winevt-carver |
| `-memory` | pure byte-pattern scanner, **medium-agnostic** | browser-forensic-memory, winevt-memory |
| `-integrity` | tamper / clearing / corruption detection (analyzer slot) | browser-forensic-integrity |
| `-analysis` | semantic analysis (e.g. event-ID → ATT&CK) | winevt-analysis |
| `-triage` | one-click **orchestrated report** (NOT `-rt`, NOT `-orchestrator`) | winevt-triage, browser-forensic-triage |
| `-cli` | front-end: CLI tool (may carry an interactive TUI *mode*) | browser-forensic-cli (`br4n6`), winevt-cli (`ev4n6`) |
| `-tui` | front-end: interactive TUI, no scriptable surface | *(pure-TUI only)* |
| `-mcp` | front-end: MCP server (agent-facing) | browser-forensic-mcp |

**Binding rules:**

- **The suite prefix must be self-describing on crates.io.** A crate name is read *bare* — in
  search, `cargo add`, and transitive dependency lists — with all repo/GitHub context stripped;
  the name alone must claim a namespace. A *distinctive* short prefix (`memf-`, `winevt-`,
  `snss-`) stands alone and is preferred for import brevity. A *generic-word* prefix does
  **not** stand alone, so that suite takes the full `<repo>-*` form: `browser-forensic-*`, never
  `browser-*` (which reads as a generic browser lib). The `repository` link is GitHub-only and
  never travels into the name.
- **Name by the role the analyst recognizes (the outcome), not by internal mechanism.** The
  orchestrated-report crate is `-triage` (what the user gets), never `-orchestrator` (how it is
  built) — and "orchestration" is reserved for issen's fleet-wiring layer. *One concept, one
  name* across the fleet: do not use `-rt` in one repo and `-triage` in another.
- **Name by the knowledge the crate owns; the dependency arrow then follows.** A format's
  byte-scanner is `<format>-memory` and lives **with the format parser**, depending DOWN on
  `<format>-core` — never `memf-<format>`. `memf-*` owns *memory navigation* (VA→PA, EPROCESS,
  VADs) and hands `&[u8]` across the boundary; the artifact-pattern knowledge is parser-side.
  PARSER crates must never import PAGING/OS-STRUCTURE, so a `memf-browser` would invert the
  dependency. (A memf-side *locator* that walks a process's VADs to find a region is a
  legitimately separate crate that *feeds* `<format>-memory` its bytes — complementary, not a
  rename.)
- **Front-end binaries follow the `<x>4n6` convention:** br4n6 (browser-forensic-cli), ev4n6
  (winevt-cli), sqlite4n6, mem4n6, disk4n6. The *binary* is `<x>4n6`; the *crate* is
  `<artifact>-cli` (a CLI tool, which may carry an interactive TUI *mode*), `-tui` (pure-TUI
  only), or `-mcp` (agent-facing server). A **dual-mode** tool is `-cli` for fleet consistency
  (the CLI is the primary surface; the TUI is a mode), never `-tui` (that hides the CLI).
  **`-cli` is intentionally overloaded to cover dual-mode** — one consistent suffix fleet-wide
  is worth more than the precision of a separate `-term` (deliberate, non-purist; e.g.
  browser-forensic-cli is CLI + TUI yet stays `-cli`).
- **A reconstructor/`-writer` is read-only-safe** only when it emits derived artifacts to NEW
  paths (carved/repaired output), never the source. Prefer `-reconstruct` / `-rebuild` over
  `-writer` in a read-only suite to avoid the "evidence editor" misread.

**crates.io rename window:** a crate can be *deleted* (name freed, not merely yanked) within
**72h of first publish**, or later only if single-owner + <500 downloads + no dependents.
Settle names *before* publishing; if a rename is needed, do it inside the 72h window (delete +
republish = clean, no orphan). After 72h, a yank leaves the old name as a permanent reserved
orphan.

## Consequences

- Every repo's crates carry consistent, self-describing, bare-readable names; the analyst and
  the crates.io reader see one grammar, not N ad-hoc conventions.
- Collisions on `<x>` / `<x>-core` are handled by ADR-0008's `[lib] name` mechanism without
  breaking import paths.
- Because names are permanent on crates.io after the 72h window, the grammar is settled up
  front rather than corrected post-publish.
- The per-parser invariant makes "is this parser complete?" answerable — a parser reader with
  no analyzer is a defect, not a judgment call a reviewer must remember. "Suite" stops being a
  naming exception and becomes what it always was: a folder. Mechanical enforcement, though,
  needs a **declared** signal of *"this repo is a parser"* (e.g. `[package.metadata.fleet]`
  role, or the `components/<layer>/` taxonomy): a heuristic keyed on `-core` presence or on the
  analyzer's emission shape misclassifies, because `-core` is overloaded and fleet analyzers do
  not share one detectable finding-emission signature.
