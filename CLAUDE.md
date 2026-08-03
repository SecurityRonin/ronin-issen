## Strategic Context

This project was planned using North Star Advisor.
Before implementing features, read:

- `north-star-advisor/ai-context.yml` - Strategic context (start here)
- `north-star-advisor/docs/INDEX.md` - Documentation hub

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

Two repo shapes, two naming patterns (decide the shape *before* naming crates): **Pattern A** single-format repo = exactly `<x>-core` (reader) + `<x>-forensic` (analyzer); **Pattern B** multi-crate suite = role-suffixed crates (`-core`/`-carve`/`-memory`/`-integrity`/`-analysis`/`-triage`/`-cli`/`-tui`/`-mcp`) under a self-describing prefix — the repo name is an umbrella, NOT itself a crate. The suite prefix must stand alone on crates.io (distinctive short `memf-`/`winevt-`; a generic word takes the full `<repo>-*` form, e.g. `browser-forensic-*`). Name by the analyst-facing outcome and the knowledge the crate owns, not the mechanism (`-triage` not `-orchestrator`; `<format>-memory` not `memf-<format>`). Front-ends: binary `<x>4n6`, crate `-cli`/`-tui`/`-mcp`. Settle names before publishing (72h crates.io delete window). **See [ADR-0009](docs/decisions/0009-crate-naming-grammar.md).**

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

The universal README discipline lives in the global `~/.claude/CLAUDE.core.md` ("README Standard — Convert the Reader, Above the Fold"); the personal instantiation (sponsor handle, reference impl) in `~/.claude/CLAUDE.personal.md`; the **pre-push readiness + verify mechanics** (adapt the README from `~/src/blazehash`, set repo About description/topics, enable Pages, confirm footer/docs links resolve) live in the `release` skill (`~/.claude/skills/release.md`). The **forensic-specific** load-bearing points for these crates:

- **Goal:** convert the target reader (forensic analyst *or* Rust dev) into an active user in **30 seconds** — `cargo add` to a result they care about, above the fold.
- **Badges (badge the guarantees we already enforce; plan for TWO rows — 9 badges wrap on GitHub, and accidental wrapping destroys the information architecture):**
  - *Row 1 — identity + adoption decision:* **Crates.io** version (both `<x>-core` and `<x>-forensic`) · **Docs.rs** (libraries) · **Rust MSRV** (e.g. `Rust 1.80+` — a build-compat go/no-go, so it pairs with identity, NOT buried in a meta tail) · **License: Apache-2.0** · **Sponsor** (`h4x0r`).
  - *Row 2 — trust proof:* **CI** (Actions passing) · **Coverage** (Codecov — the 100% line-coverage gate) · **`unsafe forbidden`** — only for crates that are genuinely `unsafe_code = forbid` (winreg/vhdx/ntfs/qcow2/sqlite-core…); the mmap crates (`ewf`, `memory-forensic`) are `unsafe_code = deny` + bounded-allow, so they **skip** this badge rather than misrepresent · **Security advisories clean** (RustSec / cargo-deny).
  - *Single-row order (when it doesn't wrap):* Crates.io · Docs.rs · Rust 1.80+ · CI · Coverage · unsafe-forbidden · security-audit · License · Sponsor.
  - *Optional / later:* Crates.io **Downloads** · **deps.rs** · a **fuzzing** badge ONLY with a real fuzz-CI story behind it (an unearned fuzz badge damages trust).
  - *Never badge:* a **Stars** badge — GitHub already renders the star count natively in the repo header; a README copy is pure redundancy.
  - Rationale (Codex-reviewed): lead with identity/installability (crates.io → docs → MSRV) so both audiences orient *before* the proof claims; **Coverage** bridges CI→security (read as a natural escalation of rigor); **unsafe-forbidden before security-audit** because memory-safety is the sharper differentiator for evidence parsers than dependency hygiene. Coverage/unsafe-forbidden/security-audit turn standards we *already meet* into visible proof — the "trust but verify" pitch.
- **GitHub repo metadata (the "About" panel — standardize across the fleet):**
  - **Description** (one line): `<Domain> forensic <library|reader|analyzer> — <what it parses/does>, <headline capabilities>. <differentiator>.` Mirror the README tagline (one concept, one name); lead with the artifact family, then capabilities (parse/detect/carve/recover), then the differentiator (input-fuzzed · panic-free by lint · single static binary · no runtime deps · deleted-record carving). e.g. browser-forensic: *"Browser forensic library suite — parse Chrome/Firefox/Safari artifacts, detect history clearing, carve deleted records. Single static binary, no runtime deps."*
  - **Topics** (GitHub topics, ≤ 20, most-specific first): always `rust` + the DFIR set `forensics · dfir · digital-forensics · incident-response`; plus the **artifact-family** topic (`browser-forensics` / `memory-forensics` / `registry` / `ntfs` …) and the **specific formats/tools** it handles (`chrome · firefox · safari · sqlite`; `registry · windows`; etc.); add `cli` if it ships one.
  - **Homepage** (the "About" website field): **leave EMPTY by default.** It is reserved for a genuine product/landing page if one ever exists — it is **not** the docs site. Docs are reached from the README's **docs badge** only; pointing Homepage at the Pages docs mis-slots documentation into the landing-page spot (and never add a separate "Full documentation →" prose link in the README — the docs badge covers that). Same destination may appear once per *surface* (About sidebar vs README body), never twice within the README.
- **Above the fold:** a bold one-line tagline (never copied between repos), then the single fastest path — for a `*-forensic` workspace lead with the *analyzer* hook (`audit_path(...)` → graded findings), since that is the differentiator, then show the reader.
- **Body:** the two-crate split (`<x>-core` reader / `<x>-forensic` analyzer), the anomaly-code table, and a "trust but verify" paragraph (input-fuzzed, panic-free by lint, validated against real artifacts).
- **Robustness wording — lead with the measured evidence, qualify the claim (binding).** "Panic-free" as a **bare, standalone claim or badge** asserts an unprovable universal (*for all inputs, no panic* — covering `unwrap`/`expect`/`panic!`, OOB indexing, slice/arith panics, alloc failure). That is a self-graded absolute, not earned evidence — it violates *Evidence-Based Rigor* ("earn the claim, never self-grade"). So:
  - The **differentiator / headline / badge word is "input-fuzzed"** (or **"fuzzed"**, with the exec count, e.g. `fuzzed · 20M execs`) — *measured* evidence against the *real* threat (untrusted parser input), verifiable and tier-1.
  - **"Panic-free" appears ONLY as the qualified *static* half beside it** — **"panic-free by lint"** or **"panic-free bounded-checked readers"** (i.e. `unwrap_used`/`expect_used = deny`, `forbid(unsafe)`, readers that return 0 out of range). Never a bare "**Panic-free.**" lead or a `panic-free` badge.
  - They are **complementary, not interchangeable**: the lints make panics unreachable *by construction*; the fuzzer *tests* that empirically (fuzzing shows present-robustness over N execs, never proves absence of all panics). The canonical "trust but verify" bullets are the paired form — a **Fuzzed** bullet (evidence + exec counts) beside a **Panic-free-by-lint** bullet (the static posture); `forensic-vfs`/`ntfs-forensic` READMEs are the model. `never-panic` / `cannot panic` bare claims get the same treatment.
- **Comparison / capability tables** (the "What's Different" vs-competitors matrix, the artifact-coverage matrix): mark a supported cell with **`✅`** (U+2705), not a plain `✓` — the emoji reads at a glance and renders consistently. Use `—` (em dash) for "not supported" and the literal word `partial` for partial support; reserve `❌` only when an *explicit* negative is the point being made.
- **Footer (mandatory, exact):** `[Privacy Policy](https://securityronin.github.io/<repo>/privacy/) · [Terms of Service](https://securityronin.github.io/<repo>/terms/) · © 2026 Security Ronin Ltd` — and `docs/privacy.md` + `docs/terms.md` **must exist** to back the links.
- **Docs site must be LIVE at publish — no dangling links (publish gate).** A repo that carries a docs badge or the Pages footer links MUST ship a `.github/workflows/docs.yml` that builds mkdocs and deploys to GitHub Pages (reference: `sqlite-forensic/.github/workflows/docs.yml` — `mkdocs build --strict` → `configure-pages`/`upload-pages-artifact`/`deploy-pages`, pinned SHAs, `pages: write` + `id-token: write`), **and** Pages must be enabled (source = GitHub Actions). At publish, **verify the docs badge URL and the footer Privacy/Terms URLs actually resolve** (HTTP 200 *and* real content — beware fake-200s), exactly as the global "no dangling footer links" rule requires. A 404 docs badge on a published repo is the canonical dangling-link failure (it happened to sqlite-forensic — shipped with mkdocs.yml + docs/ but no deploy workflow, so the Pages URL 404'd). Never publish the badge before the site builds.
- **Documentation site = MkDocs, never rustdoc-only (fleet standard). Reference implementation: `sqlite-forensic`.** Every fleet repo's docs site is a **curated MkDocs site** — `docs.yml` runs `mkdocs build --strict` and deploys the rendered site to Pages. A `cargo doc` / rustdoc deploy does **NOT** satisfy this: rustdoc serves an auto-generated API reference, not the curated pages that back the README **docs badge** and the **Privacy/Terms footer links** — so on a rustdoc-only repo those footer URLs 404 (the dangling-link failure above). Copy the three pieces from `sqlite-forensic` and adapt names:
  1. **`mkdocs.yml`** — `site_name: <repo>`, `site_url: https://securityronin.github.io/<repo>/`, `repo_url`, `theme: { name: material }`, a `nav:` listing `index.md` + the repo's analysis docs (e.g. `validation.md`, `recovery-comparison.md`, `test-data-catalog.md`) + `privacy.md` + `terms.md`, `markdown_extensions` (`admonition`, `attr_list`, `md_in_html`, `pymdownx.superfences`, `tables`), `plugins: [search]`.
  2. **`docs/`** — at minimum `index.md` + `privacy.md` + `terms.md` (the footer-link targets) + `validation.md` (the Doer-Checker evidence); add per-domain pages as warranted.
  3. **`.github/workflows/docs.yml`** — `pip install mkdocs mkdocs-material` → `mkdocs build --strict --site-dir site` → `actions/upload-pages-artifact` / `actions/configure-pages` / `actions/deploy-pages` (pinned SHAs), `permissions: pages: write` + `id-token: write`, triggered on push to `docs/**` + `mkdocs.yml` (+ `workflow_dispatch`).
- **No `## License` section** (the Apache-2.0 badge → `LICENSE` is the single source of truth; the fleet standardized on **Apache-2.0** for its explicit patent grant — migrate any residual MIT repos).
- A `docs/validation.md` documents the differential/real-artifact validation (Doer-Checker evidence). **Carving/recovery analyzers must validate against an *independent* reference tool, not only against records we deleted ourselves** — the established oracle per domain (e.g. SQLite deleted-record carving → **fqlite**; NTFS → analyzeMFT/the Sleuth Kit; registry → RegRipper/yarp) is the yardstick: run it on the same artifact and reconcile counts + contents, explaining any divergence.
  - **Desktop-messenger / Chromium-storage oracles, and the two layers they cover.** For the desktop-messenger and Chromium-storage parsers the oracles are **`cclgroupltd/ccl_chromium_reader`** (cloned at `~/src/ccl_chromium_reader`) for the *byte-decode* layer — LevelDB / IndexedDB / V8-Blink / LocalStorage — and **`abrignoni/DLEAPP`** for the *app-schema interpretation* layer (which store/table/column/JSON field means what, and which timestamp is authoritative). Signal's SQLCipher read is reconciled against the **`sqlcipher` CLI**. Env-gate each differential (`CCL_*_ORACLE`, `SIGNAL_SQLCIPHER_ORACLE`) so the committed gate never depends on a host tool.
  - **Check an oracle's LINEAGE before calling it independent — DLEAPP vendors ccl.** `DLEAPP/scripts/ccl/{ccl_leveldb,ccl_v8_value_deserializer,ccl_blink_value_deserializer}.py` *is* ccl_chromium_reader, so running DLEAPP adds **zero** independence at the decode layer (a correlated oracle, not a second opinion); its independent value is only the interpretation layer above it. Generally: **two oracles that share a vendored dependency are not independent for the shared layer** — verify lineage, never infer independence from a different project name.
  - **Tier honestly: reading a reference implementation's SOURCE is T2, RUNNING it is T1.** A source-differential (compare our field mappings / SQL / key schemas against the reference's code) is a *specified-oracle* cross-check — the answer key is independently authored (so it beats T3), but nothing executes, so a mapping can be transcribed right and implemented wrong, and we choose the comparison set. Only an *execution* differential (run the tool on the same artifact, reconcile output rows) earns T1. **Do both**: the source-diff catches whole classes the execution-diff structurally cannot — it found that our Signal reader read `received_at` where DLEAPP reads `received_at_ms` (a different column; ours is an ordering counter, not an epoch), a defect our *self-minted* fixture concealed because we had written an epoch value into that column ourselves. That is circular validation caught by an independent spec.
- After a `*-core`→`*-core`/`*-forensic` restructure, **rewrite the README**: badges/links/repo-name/`cargo add` lines all point at the new crate names, not the pre-split single crate.

## Test Corpus Catalog — keep it current (MANDATORY)

`ronin-issen/docs/test-data-catalog.md` is the **single fleet-wide catalog** of all forensic test data —
real datasets (what + source + hotlinked download URL + MD5) and synthetic fixtures (the **exact
command line(s)** that produce them). Because `tests/data/` is gitignored, this catalog is the only
committed record others can use to reproduce the corpus.

**Whenever you download or build test data anywhere in the fleet, update the catalog in the same
change:**
- **Downloaded a real dataset?** Add an entry with: what it is, authoritative source, **hotlinked
  download URL**, `md5` of the file, and a redistribution note. Confirm provenance by inspecting the
  artifact, not just the filename (Doer-Checker).
- **Built a synthetic fixture?** Record the **verbatim command(s)** that generate it (the
  `qemu-img` / `mkfs` / `xorriso` / `ewfacquire` / `dar` / `hdiutil` line, or the in-code Rust
  builder fn + `file:line`). Never write "generated for coverage" without the command — if there is
  no generator, say "NO GENERATOR IN REPO" rather than guessing.
- Classify each entry (`REAL-ext` / `REAL-self` / `SYNTHETIC` / `VENDORED` / `FUZZ`) and mark
  confidence (`✓` confirmed / `~` inferred / `?` undetermined).
- Keep the **§H MD5 manifest** in sync (hash new files; `tests/data/` is gitignored so hashes must
  live in the catalog).

**One repo-root `tests/data/` (MANDATORY layout — workspaces included; naming rationale in ADR-0004 — the directory is `tests/data/`, "corpus" classifies real datasets *within* it, never the directory).** Every repo keeps a *single*
`tests/data/` at the repo root, never per-member `<member>/tests/data/` directories. In a Cargo
workspace each member's integration tests reach the shared fixtures with a **relative `include_bytes!`
path** — from `<member>/tests/<file>.rs` the repo root is two levels up, so it is symmetric across
members: `include_bytes!("../../tests/data/<file>")`. This keeps one home, one README, and no
duplication, and it is conceptually neutral (a carving fixture used only by `<x>-forensic` need not
live "inside" `<x>-core`).

- **Never symlink fixtures** to fake a shared location. `include_bytes!` follows symlinks on Unix, but
  **git on Windows materializes a symlink as a text file containing the link target** — `include_bytes!`
  would then embed that path *string* instead of the file bytes, silently breaking the Windows CI
  runner. Use the relative path, not a symlink.
- **Verification gate:** after moving/adding fixtures, `cargo test` for every member must still compile
  (the `include_bytes!` paths must resolve) — a wrong path is a build error, not a silent miss.

**`tests/data/README.md` (one per repo, MANDATORY).** Modeled on
[`issen/tests/data/README.md`](../tests/data/README.md): a per-file `#### <filename>` entry giving
**Source / Identity / writeup URL(s) / original download URL (hotlinked) / MD5 (or sha256) / notable
contents** for real datasets, and the **verbatim generator command** (or builder `fn` at `file:line`)
for synthetic fixtures — never a download URL for something we generate. The README is the co-located
human-facing detail; `docs/test-data-catalog.md` stays the single machine-index — **cross-reference, never
duplicate** (the README links up to the catalog). Document large untracked/gitignored artifacts here
too (provenance even when the bytes aren't committed — e.g. a vendored oracle's test corpus). Use
straight ASCII in paths/commands.

### Convergence / release end-to-end validation corpus (Case-001 Szechuan)

Whenever a change could affect issen's runtime output across artifact types — a
fleet-wide dependency convergence (e.g. the forensicnomicon 0.11 sweep), a release
candidate, or any cross-cutting parser/report change — **confirm it end-to-end with a
single unified default-pipeline run (`issen <the four sources…> -o <db>`, no subcommand)
over these four Case-001 (DFIR Madness "Szechuan Sauce") sources, and NO others** (no pagefile, no pcap):

1. **DC01 memory** — `tests/data/dfirmadness-szechuan-sauce/DC01-memory.zip`
2. **DC01 disk** — `tests/data/dfirmadness-szechuan-sauce/DC01-E01.zip`
3. **Desktop (SDN1RPT) memory** — `tests/data/dfirmadness-szechuan-sauce/DESKTOP-SDN1RPT-memory.zip`
4. **Desktop (SDN1RPT) disk** — `tests/data/dfirmadness-szechuan-sauce/DESKTOP-E01.zip`

These four exercise both hosts × both media (disk + memory), so the ingest drives the
full analyzer set — NTFS / registry / EVTX / prefetch / LNK / SRUM / browser / Biome on
the disk legs and memf-windows on the memory legs — all feeding one `forensicnomicon::report`
aggregation. Extract the four to `/tmp` (never under `~/src` — the committed bytes are the
zips; see the provenance standard above).

The **default `issen <evidence…>` command unifies both media in one pass** — it ingests the
disk images and parses the memory dumps *into the same timeline*, so the one-command
end-to-end is:

- `issen <DC01.E01> <DESKTOP.E01> <DC01.mem> <DESKTOP.mem> -o /tmp/<name>.duckdb` — the disk leg
  drives NTFS / registry / EVTX / prefetch / LNK / SRUM / browser / Biome (each tagged with its
  evidence source); the memory leg feeds memf-windows events into the same
  `forensicnomicon::report` aggregation. (Pass only the FIRST `.E01` segment; ewf follows
  `.E02…` automatically. A folder of mixed images + `.mem`s works too.)

Two distinctions so the next reader isn't tripped up (see **ADR 0012**): the *explicit*
`issen ingest` subcommand is **disk-only** (it points a `.mem` at `issen memory`), and
`issen memory <dump>` runs the **deep** per-dump analysis (EPROCESS / netstat / hashdump / …) —
use it for the focused single-dump view rather than the unified sweep.

Both legs completing and producing populated, non-crashing output across all analyzers is
the runtime confirmation. Deliberately exclude pagefile and pcap.

## Release & Distribution Standard — binaries + Homebrew/apt/winget (every app/CLI repo)

> **The general release/pre-push *mechanics* — the build matrix, repo "About"
> metadata (description/topics), GitHub Pages enablement + footer/docs link
> verification, README readiness (adapt from `~/src/blazehash`), the winget
> bootstrap, the cargo-wix/cargo-deb gotchas, and all verify commands — live in
> the `release` skill (`~/.claude/skills/release.md`), the primary source. This
> section keeps only **fleet-specific values & overrides** (SecurityRonin org
> secrets, the shared tap, the Cloudsmith org, repo lists, forensic-crate
> specifics).**

Reference implementations (both verified end-to-end): **`blazehash`** and **`disk-forensic`** —
`.github/workflows/release.yml` is byte-identical between them except for the binary/crate name and
the Homebrew dispatch `event-type`. Copy from one of those, then apply the rules below. This applies
to **apps/CLIs** (the `*4n6` binaries, `blazehash`, GUI tools) — the `v*` tag drives their binaries +
Homebrew/apt/winget. **Library *crate* publishing to crates.io is NOT done by the `release.yml` `crate`
job — it is release-plz's job** (next subsection); a repo that is both a lib and a CLI runs both
(release-plz publishes the lib crates on merge to `main`; the `v*` tag ships the binary).

### Library crate publishing — release-plz (PR-based, BINDING fleet standard)

Every repo that publishes **library crates** to crates.io uses **release-plz**, not a hand-cut version
bump and not the `release.yml` `crate` job. release-plz watches `main`, computes per-crate SemVer bumps
from conventional-commit types, and opens a **release PR** that edits the `Cargo.toml` versions + writes
the `CHANGELOG`s; **merging that PR publishes** (a dependency-ordered `cargo publish`). The PR is not
code review — for a solo dev it is the reviewable, one-click checkpoint before an *irreversible*
crates.io publish (versions yank-but-never-delete; names claimed forever), and it hands you the
changelog for free. Full mechanics live in the `release` skill (`~/.claude/skills/release.md` →
"release-plz (PR-based library publishing)"); this section is the binding policy + lived gotchas.
Reference (verified end-to-end): **`forensicnomicon`** — facade `1.7.0` + core `1.2.0` + data `1.3.0`
all published via one release PR.

**Adopt it in a library repo with:**
1. **`.github/workflows/release-plz.yml`** — two jobs, both on push to `main`, SHA-pinned actions:
   `release-plz-pr` (`command: release-pr`) opens/updates the PR; `release-plz-release`
   (`command: release`) publishes any crate whose `Cargo.toml` version is ahead of crates.io. Copy
   forensicnomicon's verbatim.
2. **`release-plz.toml`** with `release_commits = "^(feat|fix|perf|refactor|doc|revert)"` — the allowlist
   that kills the changelog-churn release loop (`chore`/`ci`/`test`/`style`/`build` never release) and
   skips release-plz's own release commits. For every **non-published** workspace member (build/codegen
   tools like forensicnomicon's `ingest`) set `release = false` + `publish = false`, **mirrored** in its
   `Cargo.toml` (release-plz cross-checks the two).
3. **`CARGO_REGISTRY_TOKEN`** — the same ORG-level secret the tag pipeline already uses (fleet-wide, no
   per-repo setup); delete any repo-level shadow copy (the shadowing trap above).
4. A **`CHANGELOG.md`** seed per published crate (release-plz appends to it).

**Discipline & gotchas (all lived on the forensicnomicon cut):**
- **Conventional-commit types drive the bump** — `feat`→minor, `fix`→patch, breaking→major; `test`/
  `chore`/`docs`-only work rides along without cutting a release. **A security fix uses
  `fix(security):`** (a `fix` with a `security` scope) so it cuts a patch release — NEVER a bare
  `security:` type, which `release_commits` (`^(feat|fix|perf|refactor|doc|revert)`) does not match,
  silently stranding the fix on `main` unpublished (lived case: the RUSTSEC-2026-0190 `anyhow` bumps).
- **Merge the release PR with a MERGE commit, NOT squash** — squash rewrites the version-bump commit
  release-plz keys on.
- **An API-changing `feat` must regenerate the `public-api/*.txt` baseline in the SAME release**, or the
  `public-api` tripwire turns the release PR red:
  `cargo public-api -p <crate> --all-features --omit blanket-impls,auto-trait-impls,auto-derived-impls > public-api/<crate>.txt`
  (pin the tool to the version in `public-api.yml`).
- **`release.yml`'s tag trigger MUST be `v[0-9]*`, never `v*`** — release-plz cuts per-crate library
  tags `<crate>-vX.Y.Z`, and a crate whose name starts with `v` (fleet has `vhd`/`vhdx`/`vmdk`/`vsc`/
  `veracrypt`/`volume-core`…) produces `v…-vX.Y.Z`, which the `v*` glob **wrongly matches** → a library
  publish fires a binary build. `v[0-9]*` requires a digit right after `v`, which a `<name>-v…` tag never
  has (a crate name's first char is a letter), so bare `vX.Y.Z` tags match and per-crate tags don't. Fix
  any existing `release.yml` still on `v*` (the `blazehash`/`disk-forensic` reference workflows too).
- **The complementary control: set `git_tag_name = "{{ package }}-v{{ version }}"` in `release-plz.toml`.**
  Without it, release-plz's *default* tag for a single-crate workspace is the bare `v{{ version }}`, which
  **collides with the binary `v[0-9]*` tags** — release-plz then sees a manually-pushed `v0.7.1` and dies
  `local package … has a greater version (0.7.1) … but the git tag v0.7.1 exists` (bit timeglyph 0.7.1,
  2026-07-20). The `{{ package }}-v` prefix is what actually makes the "release-plz cuts `<crate>-vX.Y.Z`"
  assumption above hold. **Both controls are required**: `git_tag_name` (release-plz side) *and* the
  `v[0-9]*` trigger (release.yml side) — audit every dual release-plz + tag-release repo for the pair.
- **Verify the publish landed** on crates.io (independent oracle — the crates.io JSON API needs a
  `User-Agent`), never from a green run alone.
- **A release PR whose ONLY red check is `Cargo Vet` failing `<own-crate>:<newver> missing ["safe-to-deploy"]` means that crate is not declared first-party** — set `audit-as-crates-io = false` under its `[policy."<crate>"]`, never exempt the version (an exemption re-breaks on the very next bump). Every version bump reds the vet job until you do; it silently blocked 28 of 44 open fleet release PRs. Full decision tree for this and every other vet finding: **[ADR-0018](docs/decisions/0018-supply-chain-vet-renovate-policy.md)**.
- **A `git filter-repo` history rewrite on a PUBLISHED repo silently breaks release-plz — re-point the release tags afterwards.** Rewriting content (a PII/secret scrub) changes the bytes of the already-published version's source, so **no commit reproduces the published `.crate` tarball any more**. release-plz's package-equality check then walks *backwards past the release tag* hunting for a content match, and dies on the first commit whose manifest cannot resolve in an isolated clone — aborting with `failed to determine next versions` / `failed to check package equality for <crate> at commit <sha>`, so **no release PR is ever opened** and the fix sits unpublished while crates.io keeps serving the buggy version. The rewrite also **mis-maps the tags**: filter-repo rewrote `<crate>-v0.1.0` onto a commit *before* the `chore: release v0.1.0` commit that actually carries that version's tree. **Fix: `git tag -f -a <crate>-v<ver> <the chore: release commit>` and `git push --force origin <tag>`** — release-plz then computes the diff and opens the PR normally (never hand-bump the version to work around it; that skips the one reviewable checkpoint before an irreversible publish, and CLAUDE.core.md forbids it). Diagnose with: clone the repo ALONE into a temp dir (`git clone --no-local`) and run `cargo metadata` at HEAD, at the tag, and at the commit named in the error — that isolates which commit is unresolvable. Lived case: discord-desktop-forensic, after the user-id scrub (2026-07-30).
- **`version + path` deps pointing at SIBLING repos are a release-tooling landmine that CI never catches.** `dep = { version = "0.1", path = "../other-repo/crate" }` resolves fine locally and in CI (the sibling is checked out next door in the components tree) but fails for **every tool that clones the repo alone** — release-plz, `cargo package`, `cargo publish --dry-run` — with `failed to read ../other-repo/crate/Cargo.toml`. Migrate to registry-only (`dep = "0.1"`) as soon as the sibling publishes, and remember the *old commits keep the landmine* for any historical operation (which is exactly how the case above detonated). Verify with an isolated `git clone --no-local` + `cargo metadata`, not a local build.

### What one `v*` tag delivers

A single annotated, signed tag (`git tag -s vX.Y.Z && git push origin vX.Y.Z`) triggers
`release.yml`, which produces **all** of:
- **Standalone executables for macOS (aarch64 + x86_64), Linux (aarch64 + x86_64, musl-static), and Windows (x86_64 MSI)** — attached to a GitHub Release with a `checksums.txt`.
  - **GUI apps** (a repo shipping a windowed binary — e.g. timeglyph's `timeglyph-lens` overlay): the Windows **MSI must install the GUI binary AND create a Start Menu shortcut**. A portable winget **zip** gives the CLI a PATH alias but **no launcher**, so the GUI ends up *"nowhere to be found"* (lived case: winget installed only `timeglyph.exe`, never the lens). Two binaries from two crates + the ICE-clean shortcut pattern (HKCU keypath in a ProgramMenuFolder subfolder; never `light -sval`) are in the **release skill → gotcha #7 (GUI-app MSI)**. On **macOS the same rule applies — GUI ⇒ Homebrew Cask** (a `.app` icon), and Homebrew has two modes, chosen by whether the app has a GUI:
    - **Pure CLI → Homebrew Formula** (`brew install <name>`): `bin.install` puts the binary on `$PATH`. For headless CLIs — most fleet tools.
    - **GUI → Homebrew Cask** (`brew install --cask <name>`): the cask's `app "<Gui>.app"` stanza installs a `.app` bundle into `/Applications` (Launchpad / Spotlight / Dock icon); a `binary` stanza also exposes the GUI's CLI on `$PATH`. **MANDATORY whenever the repo ships a GUI** — a Formula only drops a bare binary with no icon, so a windowed app is "nowhere to be found" (the macOS twin of the winget-portable-zip trap).

    A CLI+GUI repo ships **both** (timeglyph is the fleet's first): the **Formula** carries the pure CLI (`timeglyph`), and a **Cask** carries the GUI (`timeglyph-lens.app` + its CLI via the `binary` stanza, `depends_on` the formula so one `--cask` install brings the CLI too). Mechanics — building the `.app` bundle (Info.plist + `.icns`), the release `.app.zip` artifact (zipped with `ditto`), and generating the cask in the shared tap's `update-<pkg>` handler — are in the **release skill → "macOS GUI: ship a Homebrew Cask, not a bare binary."** The fleet builds **no DMGs** (a cask ships the `.app` inside a `ditto` zip; the release-skill DMG recipe is a generic template, not our standard). **A cask `.app` MUST be Developer-ID-signed + notarized — this is a hard prerequisite, not optional.** Homebrew Cask quarantines by default; an unsigned/un-notarized `.app` is Gatekeeper-blocked ("app is damaged"), the `--no-quarantine` / `quarantine false` bypass is deprecated + being removed, and **Homebrew drops support for casks that fail Gatekeeper on 2026-09-01**. So a GUI cask needs an **Apple Developer account** ($99/yr) + `codesign --deep --options runtime` (Developer ID Application) + `xcrun notarytool submit --wait` + `xcrun stapler staple` in `release.yml`, mirroring the Windows Azure-Trusted-Signing step. (The **Formula CLI runs unsigned** — Rust ad-hoc-signs the arm64 binary, and formula artifacts aren't quarantined like cask downloads — but signing the CLI too is good hygiene.)
- **crates.io** publish (`crate` job).
- **Homebrew** formula bump (dispatch → shared tap).
- **apt/.deb** for amd64 + arm64, uploaded to the Release **and** pushed to Cloudsmith (`apt` repo).
- **winget** auto-PR (after the one-time manual bootstrap — see below).

Build matrix targets: `aarch64-apple-darwin`, `x86_64-apple-darwin`, `x86_64-unknown-linux-musl`,
`aarch64-unknown-linux-musl`, `x86_64-pc-windows-msvc` (binaries); `x86_64-unknown-linux-gnu` +
`aarch64-unknown-linux-gnu` (the `deb` job only).

### Secrets — ORG-level, single source of truth

All four release secrets live as **SecurityRonin organization** secrets (visibility = all repos), so
every fleet repo inherits them and rotation is one update:

| Secret | Purpose | Notes |
|---|---|---|
| `CARGO_REGISTRY_TOKEN` | crates.io publish | crate-scoped tokens are *more* secure than one broad token, but org-wide is the chosen trade-off for fleet convenience |
| `TAP_GITHUB_TOKEN` | dispatch to `SecurityRonin/homebrew-tap` | owned by `securityronin-bot`; the bot must have **write** (push) on the tap (see Homebrew) |
| `WINGET_TOKEN` | PR to `microsoft/winget-pkgs` | `securityronin-bot` PAT, `public_repo`; the fork lives at `securityronin-bot/winget-pkgs`; `release.yml` sets `fork-user: securityronin-bot` |
| `CLOUDSMITH_API_KEY` | push `.deb` to Cloudsmith | account-wide; works for any repo |

- **Shadowing rule (the trap):** a **repo-level** secret *overrides* an org secret of the same name.
  After adding an org secret, **delete the repo-level copies** or the repo keeps using its stale local
  value and silently ignores the org one. (`gh secret delete <NAME> -R SecurityRonin/<repo>`.)
- **Secret values are write-only** — they cannot be read back via API or copied between repos; they
  live only in GitHub's vault (and your password manager). "We have it in <repo>" means it's set on
  that repo's GitHub, not recoverable from the checkout.
- **Org secrets need `admin:org`** to manage via CLI (`gh auth refresh -h github.com -s admin:org`),
  or use the web UI (org owner can always do it there).
- **Binaries + GitHub Release need only the built-in `GITHUB_TOKEN`** — the four secrets are only for
  crates.io / Homebrew / winget / Cloudsmith. A release with *just* the executables works with zero
  external secrets.

### Windows code signing — Authenticode under Security Ronin Ltd (UK)

Fleet Windows binaries (`.exe`, and the Profile-B `.msi`) are **Authenticode-signed under
Security Ronin Ltd (the UK company)** via **Azure Trusted Signing / Artifact Signing**, so
Windows/**SmartScreen** show a *verified publisher* and winget installs don't warn — and because
it's one identity, SmartScreen reputation accrues **fleet-wide**. Fixed values:

| Field | Value |
|---|---|
| Trusted Signing account | `securityronin` — region **North Europe** → endpoint `https://neu.codesigning.azure.net` |
| Certificate profile | `securityronin-public` (**Public Trust**) |
| Validated identity | **Security Ronin Ltd** (UK), D&B / DUNS-verified |
| Azure subscription | UK / GBP, **PAYG**; tenant identity `info@securityronin.com` (fresh UK-born identity — see below) |
| CI auth | Entra app `securityronin-ci-signing` + **OIDC** federated credential (subject `…:environment:release`), role `Artifact Signing Certificate Profile Signer`; secrets `AZURE_TENANT_ID` + `AZURE_CLIENT_ID` + `AZURE_SUBSCRIPTION_ID` (non-sensitive IDs — OIDC, no client secret). CI **must run `azure/login` before the signer** (the action's DefaultAzureCredential doesn't do the OIDC exchange itself) — see [`docs/release-sop.md`](docs/release-sop.md) §5. |

- **Sign under the UK entity ONLY.** HK (**Scarlet Monkey Ltd**) is **ineligible for Public
  Trust** (Azure Artifact Signing serves US/CA/EU/UK orgs only) — never sign fleet binaries under
  it. The publisher on every signed binary reads **"Security Ronin Ltd"**.
- **Country is fixed at an identity's first Azure signup and is irreversible** — `albert@` is
  HK-locked forever, so the UK account was created with a **fresh identity** (`info@`, no prior
  Azure) that could select United Kingdom. Reuse `info@` for anything UK-Azure; never retry under
  an HK-tainted identity.
- Add `AZURE_TENANT_ID` + `AZURE_CLIENT_ID` as **SecurityRonin org secrets** (same model + shadowing
  rule as the four distribution secrets above).
- **Per-repo onboarding procedure — [`docs/release-sop.md`](docs/release-sop.md) §5 "Windows code
  signing"** (fleet-owned, self-contained): create the repo's federated credential, wire the two
  `release.yml` steps (`azure/login` → `trusted-signing-action`), verify. §5 carries the one-time
  Azure resources + every lived gotcha (azure/login-first, `Artifact Signing …` role names,
  region-specific endpoint, PAYG-to-sign, legal-name match, WAF'd verify link). **Law + values here;
  full runbook in the SOP.**
- **Migration debt:** current Profile-A CLIs ship the Windows `.zip` **unsigned** — wire the signing
  step into each app/CLI `release.yml`.

### Gotchas that fail — or silently skip — despite a green-looking run

1. **`rust-toolchain.toml` pin overrides the cross-build → `error[E0463]: can't find crate for core`.**
   If the repo pins `rust-toolchain.toml` (apps pin to the dev toolchain, e.g. `1.96.0`), that pin
   overrides whatever toolchain the `dtolnay/rust-toolchain` action installs. The action adds the
   cross-*target* to its default `stable`, but cargo actually builds with the pinned version — which
   lacks the target → every cross build fails. **Fix:** pin the action to the *same* version, so the
   target lands on the toolchain cargo uses:
   ```yaml
   - uses: dtolnay/rust-toolchain@<sha> # stable
     with:
       toolchain: 1.96.0          # MUST match rust-toolchain.toml
       targets: ${{ matrix.target }}
   ```
   Apply to **both** the `build` job and the `deb` job (native `crate`/publish is unaffected).
   Symptom is platform-independent and fails in ~20s (before real compilation). A *native* `cargo
   publish --dry-run` will NOT catch it — only a `--target` build does.
2. **`cargo-deb` (v3.x) errors `The package must have a copyright or authors property`.** Add
   `authors = ["Albert Hui <albert@securityronin.com>"]` to `[package]` in `Cargo.toml`. (blazehash
   had it; disk-forensic didn't — that's the whole difference.) Verify locally before tagging:
   `cargo install cargo-deb && cargo deb` must package past the copyright check (the macOS-only
   `strip: unrecognized option --strip-unneeded` warning is harmless — GNU strip on the Linux runner
   is fine).
3. **The `crate` job can be silently ABSENT — a green release that never publishes** (bit
   `timeglyph`). The template above lists a `crate` publish job, but a repo can drift and lack it
   entirely: the `v*` tag goes green, the GitHub Release + binaries + Homebrew/apt/winget all ship, and
   **crates.io never gets the crate** — nothing fails. `timeglyph` 0.1–0.3 were hand-published, so the
   gap hid until 0.4.0 (release fully green, crates.io stuck at 0.3.0). **Audit every app/CLI repo:**
   `grep -rn "cargo publish" .github/workflows`; if absent, add a `publish-crate` job `needs: build`
   running `cargo publish --locked` with `CARGO_REGISTRY_TOKEN` (the org secret above — all repos). The
   general failure mode + job template are in [`docs/release-sop.md`](docs/release-sop.md) §3.
4. **Non-workspace GUI (`lens`/overlay) crate builds into its OWN `target/` → packaging can't find the
   binary** (bit `timeglyph` 0.4.0). When the GUI crate is `exclude`d from the workspace, `cargo build
   --manifest-path <gui>/Cargo.toml` outputs to `<gui>/target/`, not the root `target/`; the
   macOS/Windows package step (`tar … target/<triple>/release/<gui-bin>`) and the `cargo-deb --variant
   gui` merge-asset then fail `Cannot stat: No such file` — and *only* on the GUI-building targets
   (Linux musl is CLI-only, so it passes and the failure reads as platform-specific). **Fix:** set
   `CARGO_TARGET_DIR: ${{ github.workspace }}/target` on every GUI-crate build step so it co-locates
   with the CLI binary.
5. **A channel on its OWN tag = a silently-forgotten partial release** (bit `timeglyph` — PyPI wheels
   were on a separate `py-v*` tag). The `v*` release shipped the crate + binaries + brew/apt/winget, but
   the wheels never went out (no `py-v*` tag cut) **and** `bindings/python` was never bumped (stuck at
   0.3.0 vs the crate's 0.4.0), so a belated `py-v0.4.0` would have built a stale 0.3.0 wheel. **Fix:**
   one `v*` tag fans out to **every** channel — put the `wheels` + `publish-wheels` jobs *in*
   `release.yml`, not a parallel `py-v*` workflow; a `ci.yml` guard enforces `bindings/` version ==
   crate version (lockstep); make `publish-crate` idempotent (skip if the version is already on
   crates.io) so a re-tag ships only the missing channel. **PyPI auth: `PYPI_API_TOKEN` secret** —
   `publish-wheels` uses `pypa/gh-action-pypi-publish` with `password: ${{ secrets.PYPI_API_TOKEN }}`;
   set it once from the token in `~/.pypirc` (`gh secret set PYPI_API_TOKEN -R <org>/<repo>`, or org-wide
   like the other release secrets). (OIDC Trusted Publishing — `id-token: write`, no stored secret — is
   the alternative if you'd rather not manage a token; it needs a one-time trusted-publisher
   registration on pypi.org.) General pattern in [`docs/release-sop.md`](docs/release-sop.md) §3.

### crates.io versioning rule

A crate version can be published **once**. **Bump `version` in `Cargo.toml` before every release tag**
— a tag whose `crate` job re-publishes an existing version fails "already exists." Re-tagging the
*same* `vX.Y.Z` is only safe if the prior run never reached the `crate`/`release` jobs (e.g. it died
in `build`); once published, you must bump (e.g. `0.8.2` → `0.8.3`). To move a not-yet-published tag:
`git tag -d v… ; git push origin :refs/tags/v… ; git tag -s v… ; git push origin v…`.

### App requirement: conventional `--version`

The CLI must support `-V`/`--version` printing `<bin> X.Y.Z` to stdout and exiting **0** (use
`env!("CARGO_PKG_VERSION")`). The Homebrew formula `test do` block asserts on it
(`assert_match "<bin> #{version}", shell_output("#{bin}/<bin> --version")`). disk4n6 originally lacked
it and treated `--version` as a path — add it (TDD: RED parse test → GREEN).

### Homebrew — shared tap, per-project dispatch + handler

- One tap for the whole fleet: **`SecurityRonin/homebrew-tap`** (`brew install SecurityRonin/tap/<bin>`).
- **Each project dispatches its OWN `event-type`** (`update-<bin>`, e.g. `update-blazehash`,
  `update-disk4n6`) and the tap has a **matching per-project handler workflow** `update-<bin>.yml`
  listening on that type. **Never share a generic `update-formula` event** — two projects on the same
  event collide (the second project's release fires the first project's updater). Each handler downloads
  the release `checksums.txt`, fills the SHA256s, and writes `Formula/<bin>.rb`.
- **`securityronin-bot` must have `write` (push) on `homebrew-tap`** — `repository_dispatch` requires
  write access; a read collaborator gets 403. (Granting it creates an *invitation* the bot must accept:
  `gh api -X PUT repos/SecurityRonin/homebrew-tap/collaborators/securityronin-bot -f permission=push`
  then accept as the bot via `gh api -X PATCH user/repository_invitations/<id>`.)
- Formula class name is the bin name capitalized, digits kept (`disk4n6` → `class Disk4n6 < Formula`).
- The tap handler commits via the GitHub API / `github-actions[bot]` (GitHub-verified) — consistent
  with the tap's existing bot-commit style.

### winget — action does UPDATES only; first version is a MANUAL bootstrap

`vedantmgoyal9/winget-releaser` **cannot create a new package** — it only bumps an existing one. So
the `winget` job is `continue-on-error: true` and **fails harmlessly until the first version is
submitted by hand**. After the first PR merges, every future release auto-PRs the update. The PR
title tells which is which: a manual first submission says **"New package: …"** / "Add …"; the
action's auto-PRs say **"New version: …"**. (blazehash's 0.2.0 was a manual PR by `h4x0r`; 0.2.1+ were
auto by the bot.)

**Bootstrapping the first version from a Mac (no Windows, no `wingetcreate` — it's Windows-only):**
1. `brew install msitools` and extract the MSI GUIDs:
   `msiinfo export <bin>-X.Y.Z-x86_64-pc-windows-msvc.msi Property | grep -iE 'ProductCode|UpgradeCode|ProductVersion'`.
2. Get the installer SHA256 from the release `checksums.txt` (winget wants it **uppercase**).
3. Hand-author the **3 manifests** (model them on an existing fleet package already in winget-pkgs,
   e.g. `manifests/s/SecurityRonin/blazehash/<v>/`): `<Id>.yaml` (version), `<Id>.installer.yaml`
   (InstallerType `wix`, Scope `machine`, `ProductCode`, `AppsAndFeaturesEntries` with Product+Upgrade
   codes, the installer URL + SHA256), `<Id>.locale.en-US.yaml` (publisher/license/description/tags).
4. Submit via the bot, API-only (don't clone the huge winget-pkgs repo): `gh auth switch --user
   securityronin-bot` → `gh repo sync securityronin-bot/winget-pkgs --source microsoft/winget-pkgs` →
   create a branch ref at master → `PUT` the 3 files under
   `manifests/s/SecurityRonin/<bin>/X.Y.Z/` → `POST` a PR `head: securityronin-bot:<branch>`,
   `base: master` → `gh auth switch --user h4x0r`.
- **`PackageIdentifier` must be identical** between the manual first PR and the action's `identifier:`
  input (`SecurityRonin.<bin>`), or future auto-updates orphan.
- **Keep the MSI `UpgradeCode` stable across versions** (it's fixed in `wix/main.wxs`) — winget keys
  upgrades off it; a changing UpgradeCode makes each release look like an unrelated package.

### Cloudsmith (apt)

- One account-wide `CLOUDSMITH_API_KEY`. **The destination repo must exist first** —
  `securityronin/<repo>` at cloudsmith.io (the push 404s otherwise). Public install path:
  `curl -1sLf https://dl.cloudsmith.io/public/securityronin/<repo>/setup.deb.sh | sudo bash`.

### Pre-tag checklist

1. `version` bumped in `Cargo.toml` (not already on crates.io).
2. `[package] authors` present (cargo-deb).
3. `release.yml` toolchain pinned to `rust-toolchain.toml`'s version (if pinned).
4. CLI has `--version`.
5. Org secrets present; repo-level shadows deleted.
6. Homebrew: per-project `update-<bin>.yml` exists in the tap; dispatch `event-type` matches; bot has
   write on the tap.
7. Cloudsmith repo created.
8. First winget version bootstrapped (or accept `continue-on-error` until you do).
9. Tag is **signed** (`git tag -s`).
