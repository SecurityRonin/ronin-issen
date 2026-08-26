## Strategic Context

This project was planned using North Star Advisor.
Before implementing features, read:

- `north-star-advisor/ai-context.yml` - Strategic context (start here)
- `north-star-advisor/docs/INDEX.md` - Documentation hub

## What IS the fleet (binding — the denominator for every fleet-wide count)

**The fleet is the set of git repositories under `~/src/ronin-issen`.** Nothing
else. Enumerate it from the working tree, never from the GitHub org:

```bash
find ~/src/ronin-issen -maxdepth 4 -name .git \
  -not -path '*/.claude/*' -not -path '*/target/*' | sed 's|/\.git$||'
```

Exclude `_deprecated/` (moved or archived repos kept only for history). That
yields **93 live repos**.

- **`gh repo list SecurityRonin` is NOT the fleet.** The org holds ~134 repos and
  sweeps in unrelated projects — alaya, shepherd, pipeguard, colligate, pdf2xlsx,
  clawpot, doc4n6, nameback, prop-window, rapidcollect,
  maintainable-vibe-coding — none of which are fleet components.
- **The wrong denominator corrupts every claim built on it.** A health sweep read
  *116/134 green, 17 red* against the org and *91/93 green, 1 actionable red*
  against the fleet: 11 of those reds belonged to repos nobody had asked about,
  and one more was an archived repo. Percentages over 93 and 134 are not
  interchangeable.
- **Read state from `origin/main` or the API, never a local checkout.** A local
  clone sits at whatever commit it happens to hold. Reading `Cargo.lock` /
  `ci.yml` locally has produced a *false regression report* right after fixes
  merged, and a "0 adopters" count when two repos had already adopted. Always
  `git fetch` then `git show origin/main:<path>`.

An extreme fleet-wide number (0 of N, all of N) is where to check twice — with a
second, differently-shaped method — before reporting it.

## Fleet Glossary

Canonical vocabulary, concepts, and the forensic **epistemology** (observed fact vs
inference vs conclusion; *name the observable, not the conclusion*; the
`deleted`/`unallocated`/`residual` recovery taxonomy; carving tiers) live in
[`docs/glossary.md`](docs/glossary.md) — the term-definitions home. The binding
*rules* stay in this file and in `docs/decisions/`; the glossary defines and
cross-references them, never restating law.

## Multi-Repo Architecture

Issen orchestrates a family of standalone forensic libraries — each a deep expert in
one artifact family; Issen is the thin wrapping + correlation layer on top. All
evidence is reached through **five navigation primitives**, and PARSER crates are
**medium-agnostic** (they never learn where their bytes came from). The full layer
map, per-layer responsibilities, the `[H]` state-history functor, and the rationale
live in **[ADR-0016](docs/decisions/0016-multi-repo-layer-architecture.md)** (release
order: [ADR-0006](docs/decisions/0006-fleet-dependency-layering-release-order.md);
reader/analyzer split: [ADR-0008](docs/decisions/0008-reader-analyzer-core-forensic-split.md);
VFS abstraction: [ADR-0011](docs/decisions/0011-vfs-universal-container-abstraction.md)).
Canonical vocabulary is in [`docs/glossary.md`](docs/glossary.md).

**Layers** (dependencies flow down toward FOUNDATION; a repo may span several):
FOUNDATION (forensicnomicon, state-history-forensic, jsonguard) → CONTAINER (ewf-forensic,
vhdx, dd, segb-core, memf-format) → FILESYSTEM (ext4fs-forensic, 4n6mount) / PAGING
(memf-hw) / OS STRUCTURE (memf-windows) / LOG FORMAT (winevt-forensic) / QUERY ENGINE
(issen-remote-access, velociraptor-parser) / GRAPH NAV (cas/git/sigstore-forensic) →
PARSER (browser/winevt/srum/segb-forensic, …) → ORCHESTRATION (Issen).

**Five navigation primitives:** `[P]` Disk `name→inode→block` · `[M]` Memory
`PID→EPROCESS→VA→PA` · `[L]` Log `timestamp/record→field` · `[Q]` Live Query
`(endpoint,query,cursor)→rows` · `[C]` Content-Addressed `hash→blob→graph`. `[H]`
state-history is a cross-cutting functor lifting each base primitive to a
time-indexed variant (`TemporalCohort<H>`).

**Dependency rules (load-bearing):** CONTAINER depends on FOUNDATION only;
FILESYSTEM/PAGING/OS-STRUCTURE/LOG depend on their container + FOUNDATION; **PARSER
depends on FOUNDATION only and accepts `Path`/`&[u8]` — it never imports a
CONTAINER/FILESYSTEM/PAGING/OS/LOG crate**; OS STRUCTURE MAY call PARSER when it
locates artifact bytes in a VA region; ORCHESTRATION is the primary wiring point.

**Where does this code go?** format fact → forensicnomicon · decode a container →
CONTAINER · sectors-by-path → FILESYSTEM · pages-by-VA → PAGING · kernel objects →
OS STRUCTURE · log-by-time/record → LOG FORMAT · interpret records → PARSER ·
correlate/UX → Issen · live query → QUERY ENGINE · hash store → GRAPH NAV ·
temporal cohort → `[H]` state-history. **See [ADR-0016](docs/decisions/0016-multi-repo-layer-architecture.md).**

## The Reporting Model — `forensicnomicon::report`

Every fleet analyzer emits its findings as the single normalized `forensicnomicon::report` model — the union (superset) of the analyzers' data, not a flattening. `Finding`s are built only via the `Finding::observation(...)` / `Finding::unrated(...)` builders (never struct literals), carry `Option<Severity>` (`Info<Low<Medium<High<Critical`; `None` = not-scored, distinct from `Some(Info)`), are `#[non_exhaustive]` for additive evolution, and are observations never legal conclusions ("consistent with", never a verdict). Every native severity scale normalizes to the canonical scale; each analyzer keeps its typed `AnomalyKind` and converts via `impl Observation`. `forensicnomicon` stays the leaf — analyzers depend down onto it. **See [ADR-0007](docs/decisions/0007-normalized-report-model.md).**

## Crate-structure standard — reader/analyzer split (core/ + forensic/)

Every format is one workspace repo `<x>-forensic` with two members: `core/` → `<x>-core` (raw reader — exposes `Read + Seek`/navigation, no findings) and `forensic/` → `<x>-forensic` (anomaly auditor emitting `forensicnomicon::report::Finding` via `impl Observation`). `-forensic` depends on `-core` by default but MAY drop lower (raw bytes / container / `forensicnomicon` constants) when `-core`'s happy-path reader hides the very anomaly it hunts. Reader = `<x>-core`, analyzer = `<x>-forensic`, always (crates.io name collisions handled via `[lib] name`, per ADR-0009). Coverage gate: 100% line coverage over **every test target** (`cargo llvm-cov --workspace` with `--ignore-filename-regex '(^|/)src/(main\.rs|bin/)'`; never `--lib`, which builds only the lib's own unit tests and so cannot see integration-test coverage — `--workspace` selects packages, not targets, and does not compensate) with `// cov:unreachable` on provably-dead defensive arms — never delete a defensive guard to satisfy the gate. **See [ADR-0008](docs/decisions/0008-reader-analyzer-core-forensic-split.md).**

## Crate naming grammar (binding — applies to every fleet repo)

Two repo shapes, two naming patterns (decide the shape *before* naming crates): **Pattern A** single-format repo = exactly `<x>-core` (reader) + `<x>-forensic` (analyzer); **Pattern B** multi-crate suite = role-suffixed crates (`-core`/`-carve`/`-memory`/`-integrity`/`-analysis`/`-triage`/`-cli`/`-tui`/`-mcp`) under a self-describing prefix — the repo name is an umbrella, NOT itself a crate. The suite prefix must stand alone on crates.io (distinctive short `memf-`/`winevt-`; a generic word takes the full `<repo>-*` form, e.g. `browser-forensic-*`). Name by the analyst-facing outcome and the knowledge the crate owns, not the mechanism (`-triage` not `-orchestrator`; `<format>-memory` not `memf-<format>`). Front-ends: binary `<x>4n6`, crate `-cli`/`-tui`/`-mcp`. Settle names before publishing (72h crates.io delete window). **Per-parser invariant:** every parser is a reader *and* an analyzer — a "suite" is an organizational grouping, NOT a licence to ship a reader with no `-forensic`; and crates that co-locate in one repo but share no inter-crate deps are independent Pattern-A parsers, not a suite (decide by the dependency arrows, not the folder). Scoped to **parsers only**: a `-core` suffix does not imply one — foundation (`forensicnomicon-core`), utility (`blazehash-core`), codec (`lzvn-core`), and orchestrator (`issen-core`) cores are not parsers and owe no `-forensic`. The question is "is this a parser?", never "does it have a `-core`?". **See [ADR-0009](docs/decisions/0009-crate-naming-grammar.md).**

## Dependency Preference — prefer our own crates (binding)

Always prefer our own (SecurityRonin / `h4x0r`) crates over third-party equivalents — a hard rule, not a tiebreaker; before adding a third-party dep check whether we already publish one, and migrate any wired-in third-party dep to ours proactively when an equivalent exists or can be built. Prefer the *published* registry crate over a `path` dep once ours is on crates.io. (The one inversion: never hand-roll crypto — use the audited ecosystem crate.) **See [ADR-0010](docs/decisions/0010-prefer-our-own-crates.md).**

## VFS & Universal Container Abstraction (binding — format-agnostic image/filesystem access)

A consumer that reads an evidence image MUST NOT know one container/filesystem format from another — it depends on the ABSTRACTION, never on a per-format crate: raw disk images via `disk_forensic::container::open(path)`, logical file containers via `disk_forensic::logical::open(path)`, filesystems over a byte source via `forensic-vfs`. A format special-case (`if ewf {…}`) in a consumer is the smell this policy exists to catch; migrate it to the abstraction. **See [ADR-0011](docs/decisions/0011-vfs-universal-container-abstraction.md).**

## Security & Robustness Standard — Paranoid Gatekeeper (MANDATORY for every `*-core` / `*-forensic` crate)

Every `*-core`/`*-forensic` crate parses untrusted, attacker-controllable images: *never panic, never read out of bounds, never trust a length field.* It meets the global panic-free lint recipe + pre-publish gate + CI shape, plus the forensic superset — bounded `unsafe` only for mmap (`forbid`→`deny` + per-site allow), every integer read through the published `safe-read` crate (NEVER a hand-rolled `bytes.rs`), one fuzz target per parsed structure + a full-pipeline `fuzz_forensic`, and real-artifact CI validation at 100% coverage. **See [ADR-0012](docs/decisions/0012-paranoid-gatekeeper-security-standard.md).**

## Supply-Chain Policy — cargo-vet mechanisms & Renovate posture (binding)

Three gates, each catching what the others miss: **Renovate** keeps deps *fresh*, **`cargo deny`** catches *known-bad*, **`cargo vet`** catches *unreviewed code* (the injection layer — a compromised maintainer's backdoor, before any advisory exists).

**Every vet finding takes the FIRST mechanism that applies — reaching for a weaker one is a defect:** (1) ours, a workspace member → `audit-as-crates-io = false`; (2) ours, from crates.io → `cargo vet trust <crate> h4x0r`; (3) third-party whose publisher an imported aggregate auditor already trusts → `cargo vet trust <crate> <publisher>`; (4) third-party outrunning the audits → `[[exemptions]]` with a truthful note. **Never `cargo vet certify --accept-all`** — a certify record asserts a human read the source, so bulk-certifying *fabricates* the pass condition (worse than an honest exemption; the adler2 law). Import the `google`/`mozilla`/`bytecode-alliance`/`embark` audit sets so (3) and (4) stay small.

**Renovate:** `lockFileMaintenance` **with `automerge: true`** is the load-bearing setting (lock lag is the staleness that actually recurs); `rangeStrategy: "bump"` for requirement currency; grouped, scoped. **Automerge is gated by whether the MSRV promise is PROTECTED, not by repo role** — a repo that publishes a library (including a lib+binary hybrid) declares a low `rust-version` downstreams pin against, so it automerges only with a **required, blocking low-MSRV check**; a pure app's `rust-version` is just its pinned toolchain, so it has no promise to regress and may automerge without one. Enforcement is a CI job, never a reviewer noticing. Blocking: fmt · clippy · test · MSRV · deny · vet. Advisory and bot-owned: freshness — **never fire-drill it**.

**See [ADR-0018](docs/decisions/0018-supply-chain-vet-renovate-policy.md).**

## Batteries-Included — Compile Everything In (binding fleet default)

Compile every capability in; a capability not compiled in is not there in the field. `default-features = false` is BANNED as a way to slim a fleet dependency; when full features trip a gate, fix the GATE (allow the license, pin the pre-release, commit the lock), not the feature set; deferring or dropping a capability to dodge a gate is banned. Commit `Cargo.lock` in EVERY fleet repo — binary AND library. The lean `<x>-core` library + full `<x>` binary split is the mechanism when a dep is both a library primitive and a heavy tool. Decode/enrichment (`blob-decoder`, `timeglyph`) is always-on in the `*-forensic`/analysis layer, never feature-gated (MSRV yields to capability). **See [ADR-0013](docs/decisions/0013-batteries-included.md).**

## Fleet GUI Standard — egui (single binary, crates.io-publishable)

A fleet GUI is a **pure-Rust, single static binary** that `cargo install`s and
publishes to crates.io like a `<x>4n6` CLI: **`egui`/`eframe` is the default**
(immediate-mode, one binary, WASM-capable, fits data-dense analyst UIs; `-gui`
publishes like `-cli`). **Tauri / `dioxus-desktop` / any `wry`/webview bundle are
banned** (crates.io cannot deliver them) — a genuine exception carries a documented
reason + `publish = false` (e.g. `srum-gui`). Icons: **`egui-phosphor`**, pinned to
the egui-matching version. macOS GUI *distribution* follows
[ADR-0002](docs/decisions/0002-macos-gui-homebrew-cask-signed.md). Reference:
`~/src/nameback` (`nameback-gui`). **See [ADR-0014](docs/decisions/0014-fleet-gui-standard-egui.md).**

## PRD & ADR Standard — preserve the rationale (every non-internal repo; pre-push gate)

Every non-internal fleet repo preserves its *why* in durable, **repo-level** docs
(never per-crate). **ADRs are gated fleet-wide** — `docs/decisions/NNNN-title.md`
capturing load-bearing decisions, reverse-written honestly from the code + git
history (real artifacts, never stubs). **A PRD is gated only for the user-facing
PRODUCT tier** — things an examiner *runs* (`<x>4n6` CLIs, GUIs, MCP servers, full
analyzer suites); a **library** repo instead gets a lighter **Purpose & Scope** under
the *same* filename `docs/PRD.md` (only the depth varies;
[ADR-0003](docs/decisions/0003-doc-naming-conventions.md)). A lib+CLI repo is product
tier and gets both. **Pre-push gate (mirrored CI-side as `docs-gate`):** every
non-internal repo has ≥1 real ADR + `docs/PRD.md`; correctness-claiming repos add
`docs/validation.md`; internal-only repos are exempt. **See [ADR-0015](docs/decisions/0015-prd-adr-standard.md).**

## README Standard (every forensic repo)

The universal discipline lives in `~/.claude/CLAUDE.core.md`; the personal instantiation in
`~/.claude/CLAUDE.personal.md`; the pre-push readiness + verify mechanics in the `release`
skill. **The forensic-specific binding rules — badge rows, repo About metadata, above-the-fold
shape, the robustness wording rule ("input-fuzzed", never a bare "panic-free"), comparison-table
conventions, the exact footer, and the MkDocs requirement — are in
[`docs/readme-standard.md`](docs/readme-standard.md).**

## Test Corpus Catalog — keep it current (MANDATORY)

`docs/test-data-catalog.md` is the single fleet-wide catalog of all forensic test data. **Whenever you
download or build test data anywhere in the fleet, update the catalog in the same change** — real
datasets get source + hotlinked URL + MD5 + redistribution note; synthetic fixtures get the verbatim
generator command. One repo-root `tests/data/` per repo (never per-member), reached from members via
a relative `include_bytes!` — **never a symlink** (git on Windows materializes it as a text file).

**The full standard — per-file provenance entries, the classification and confidence markers, the
large-artifact `/tmp` extraction rule, and the Case-001 Szechuan convergence validation set — is in
[`docs/test-corpus-standard.md`](docs/test-corpus-standard.md).**

## Fleet Lessons Learned — read before a cross-repo change

[`docs/lessons-learned.md`](docs/lessons-learned.md) records findings that cost real time and
would otherwise be re-derived in whichever component hits them next: what a `forensic-vfs` version
bump actually costs (18 reader crates, `E0277` on a mixed graph), why an unseeded fuzz target
reports millions of clean runs while testing only a magic check, how an ADR's claim about a
*consumer* rots without any test noticing, and the `git -C … worktree add` relative-path trap that
makes a multi-repo sweep lie without erroring.

Each entry is a failure that **did not announce itself** — a green run, a plausible number, a
confident sentence — plus the cheap check that would have caught it. Every entry carries the date it
was observed, because a lesson naming a version or a count is a fact about a day: verify before
relying on it. Topic standards own their own gotchas (release-plz's live in
[`docs/release-standard.md`](docs/release-standard.md)); that file is for what has no better home.

## Release & Distribution Standard — binaries + Homebrew/apt/winget (every app/CLI repo)

**Law:** releases are automated and reviewed, never hand-cut. **Libraries publish via release-plz**
(PR-based, on merge to `main`); **binaries/CLIs publish from a signed `v[0-9]*` tag**; a lib+CLI repo
runs both. A crate version publishes once — bump before every tag.

General mechanics live in the `release` skill (`~/.claude/skills/release.md`). **The fleet-specific
values and overrides — org secrets and the shadowing rule, the shared Homebrew tap, Cloudsmith,
winget bootstrap, Windows Authenticode under Security Ronin Ltd, the build matrix, the release-plz
gotchas, and the pre-tag checklist — are in
[`docs/release-standard.md`](docs/release-standard.md).** Per-repo onboarding runbook:
[`docs/release-sop.md`](docs/release-sop.md).
