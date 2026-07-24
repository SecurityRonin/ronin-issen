# Indicator Extraction + OSINT Enrichment — Fleet Integration Design (`~/src/intel`)

**Status: DRAFT for review — not yet adopted.** Investigation + design only; no code exists
yet. Adversarially reviewed by Codex (GPT-5, reasoning high); §8 records the critique and
how each point was resolved.

## Executive Summary

**Yes — build the module, in gated stages.** The fleet should gain a first-class capability
that (a) digs indicator-shaped data — emails, IPs, URLs, and later domains, phones, wallets,
usernames — out of forensic artifacts, and (b) enriches those indicators through our own
`~/src/intel` OSINT engine. The two halves are epistemically different and must never blend:

- **Extraction** yields an *observed occurrence* (these bytes, at this location, in this
  artifact) plus a *classification* (they parse as an email) that is itself a documented,
  versioned inference — recorded as a candidate indicator, not asserted as truth. It is
  pure, offline, deterministic, always compiled in. Prior art: bulk_extractor. The fleet
  has already hand-rolled it three times
  (`browser-forensic-search/src/ioc.rs:146-183`, `issen-navigator/src/investigation/alerts/correlation.rs:124`,
  `issen-parser-pe/src/parser.rs:137`) — the DRY signal that a shared implementation is due.
- **Enrichment** yields a *third-party assertion at a point in time* ("ip-api asserted at
  2026-07-23T11:02Z that 8.8.8.8 geolocates to Ashburn"). It is supplementary analysis
  material — never contents of the seized evidence — preserved as a captured exchange
  (request + response + parser identity) so the *parsing* is repeatable and the *input* is
  preserved. It is compiled in (batteries-included) but performs **zero network egress
  without an explicit, preflight-confirmed analyst action**: sending evidence-derived
  indicators to third-party APIs discloses case data, can tip off an adversary, spends
  quota/money, and carries legal/ToS obligations (breach databases, victim PII).

`~/src/intel` is ours, well-shaped, and is the right enrichment engine. Integration needs
one structural seam in it — splitting each connector into `acquire → CapturedExchange` and
`parse(CapturedExchange) → assertions` so live runs and replays share one parsing path —
plus landing its unmerged worktree onto `main`. Its crate names must be settled before
first publish (`intel-core` reads as Intel's CPU line on a bare crates.io reading).

**First slice ships offline value only**: four proven scanners (email/IPv4/IPv6/URL, seeded
from browser-forensic-search) run at ingest over parsed artifact text, writing an
occurrences table (full provenance) + canonical-indicators table into the case DuckDB —
inside the issen workspace, no new repos, no publishing, no network. Enrichment integration
is gated on measured false-positive data from that slice.

---

## 1. What `~/src/intel` is (investigated 2026-07-23)

A Rust workspace, ours (`h4x0r`, Apache-2.0, `repository = github.com/h4x0r/intel`),
**unpublished** (0.1.0). The real code sits on an **unmerged worktree branch**
(`.claude/worktrees/osint-intel-layer/`); `main` holds only an initial commit. Two crates:

- **`intel-core`** — a multi-source OSINT enrichment library.
  - `Indicator { kind, value }` with `IndicatorKind` = Ip, Domain, Url, Email, Username,
    Phone, Hash, Asn, Wallet (`crates/intel-core/src/indicator.rs:15-34`);
    `Indicator::detect()` auto-classifies a raw string (pure, no network).
  - `Source` async trait — `name() / supports(kind) / enrich(&Indicator) -> Result<Facets, SourceError>`
    (`src/source.rs`). Humble Object: thin HTTP shell over a pure, unit-tested `parse`.
    `SourceError` is fail-loud (Network / Auth / RateLimited / Http / Parse / NotConfigured);
    a per-indicator *miss* is empty `Facets`, never an error — the distinction is explicit.
  - `Engine` fans one indicator out across all supporting sources concurrently and merges
    contributions into `EnrichedProfile { indicator, facets, runs }`; `runs` is a per-source
    log `SourceRun { source, status: Ok|Skipped|Error, duration_ms, items, error }`
    (`src/engine.rs`, `src/profile.rs`). Every facet carries a `source` field.
  - `Facets` — normalized union: geolocation / network / whois (singletons, first-seen wins)
    + reputation, dns, certificates, technologies, breaches, credentials, accounts,
    exposures, scans, related_domains (lists, appended).
  - Sources: **ip-api** (free; IP/domain geo+ASN — free tier is **HTTP-only plaintext**),
    **crt.sh** (free; CT logs, passive subdomains), **Webamon** (free tier or Cognito SRP
    login — the optional `aws-cognito-srp` dep), **OSINT Industries** (API key; account
    presence across ~450 platforms, breach records).
  - Deps: tokio, reqwest(rustls), serde, async-trait, thiserror, futures, url.
    `unsafe_code = forbid`, fleet-style clippy posture, rust-version 1.82.
- **`intel-cli`** — the `intel` binary: `enrich | detect | sources | webamon login/status/logout`,
  `--json` output.

**Build-vs-reuse verdict: reuse.** It is our crate (Dependency Preference law), its `Source`
trait is the extension seam a fleet integration needs, and its error/run model is fail-loud.
It contains **no extraction** capability — which is precisely the module the fleet lacks.

**Gaps to close for forensic use** (details in §4): the connector API conflates acquisition
with parsing (no replay boundary); singleton facet merge discards inter-source disagreement;
no captured-exchange record (request, headers, redirects, status are not preserved); one
source is plaintext-HTTP.

## 2. Where each half lives in the layer model

### Extraction — starts in ORCHESTRATION, with a documented promotion path

The scanner interprets no artifact *format*; it scans text/bytes handed to it. Its eventual
architectural slot is the cross-cutting utility leaf (`jsonguard`/`blob-decoder` company) —
but it does **not start there**. v0 lives as `issen-indicators`, a workspace-internal crate
in the issen repo (matching that workspace's per-concern granularity — 35+ crates), owning
both the scanners and the case-DB wiring. Promotion to a standalone published crate happens
when the second out-of-repo consumer (browser-forensic-search's planned migration) makes the
boundary real — the naming decision (§3) is taken then, not now. This stages the DRY
consolidation instead of minting public crates ahead of a proven abstraction.

Extraction does **not** depend on `intel-core` (that would drag tokio/reqwest into the
offline ingest path) and does not reuse `intel`'s `Indicator` type: an extraction *candidate*
(uncertain, provenance-rich, possibly ambiguous) and an enrichment *query indicator*
(canonical, API-acceptable) are different things. The mapping happens once, at `issen
enrich` time, in the one crate that already links `intel-core`.

### Enrichment — [Q]-adjacent supplementary material, wired at ORCHESTRATION

Enrichment resembles the [Q] navigation primitive — `(endpoint, query, cursor) → rows`,
"the query itself is part of the evidence chain" — and borrows its acquisition-provenance
discipline. But it is **not** claimed to implement the fleet QUERY ENGINE contract, and its
results are classified as **supplementary analysis material**, never as acquired contents
of the seized evidence. `intel-core` is consumed as an external engine by the issen-side
adapter; nothing else in the fleet may import it.

### What already exists nearby (and stays where it is)

- `issen-signatures` (`crates/issen-signatures/src/engines/ioc_network.rs`) **matches**
  indicators against known-bad feeds (offline, deterministic). Complementary — extraction
  feeds it more candidates; nothing is replaced.
- `forensic-pivot` (`crates/forensic-pivot/src/downloader.rs` — `SyncManifest`,
  `stale_feeds`) already implements the feed-cache/manifest pattern; extracted indicators
  become natural pivot keys in a later slice.
- `RESEARCH_INTEL.md` (issen repo) already recommends an `AtomicIndicator` internal model
  and files enrichment under "Treat As Normalization / Enrichment, Not Intel Rules" — this
  design is that line made concrete.

## 3. Crate shape + names

### Slice-one shape (no new repos, nothing published)

| Crate / surface | Repo | Role |
|---|---|---|
| `issen-indicators` *(new, workspace-internal)* | issen | scanners (email/IPv4/IPv6/URL) + occurrence/canonical tables in the case DuckDB; `ScanSummary` run manifest |
| `issen enrich` *(new subcommand — slice 4)* | issen | preflight-gated enrichment driving `intel-core`; captured-exchange store |
| `intel-core` connector split *(slice 4)* | intel | `acquire → CapturedExchange` / `parse(CapturedExchange) → assertions`; deterministic merge policy |

Dependency arrows: `issen-indicators` → (std, `linkify`, `regex`, `memchr`) only.
`issen-cli` → `issen-indicators` + `intel-core` (the only crate that links it). PARSER
crates gain **no** new dependency — extraction runs at ORCHESTRATION over their outputs.

### Deferred shape (when browser-forensic migrates)

The scanners extract into a standalone published crate; candidates for its name are decided
then, against the naming grammar's bare-crates.io test. **Open question, settle before any
publish:** the `intel` repo's crate names. `intel-core` on crates.io reads as "Intel Core"
(the CPU line of a famously litigious trademark holder); `intel` alone reads as the company.
Codex's counter-proposal (`indicator-enrichment-core` / `indicator-extract-core`) is
self-describing but leaden; `osintel-*` risks reading as "OS intel". No option is clearly
right yet — the decision is explicitly deferred to the pre-publish gate of slice 4, where it
blocks publishing. (Names are claimed forever; the 72-hour delete window is the only escape.)

**Migrations flagged now (Dependency Preference law), executed at promotion time with a
differential-test matrix (§6):** `browser-forensic-search/src/ioc.rs`,
`issen-navigator`'s `extract_ip_from_description`, and an inventory pass for any other
hand-rolled extractor before the crate is published.

## 4. Data model + epistemics

Four layers, each with its own epistemic status, never blended:

| Layer | Status | Where it lands |
|---|---|---|
| 0. Occurrence | **Observed fact** — these bytes at this location in this artifact | `indicator_occurrences` table (immutable rows) |
| 1. Classification | **Documented inference** — scanner R at version V classifies the decoded text as kind K with confidence C | columns on the occurrence + `indicators` canonical table |
| 2. Offline match | **Local inference** — canonical indicator ∈ known-bad list L at feed-version V | graded `Finding` (issen-signatures, exists today) |
| 3. Online enrichment | **Third-party assertion at time T** — "source S asserted P at T" | `CapturedExchange` + `ExternalAssertion`; a `Finding` only via a local analytic rule |

### Layers 0–1: occurrences and candidates

Extraction output is a **candidate indicator**, not an asserted truth (glossary §A1: the
observed fact is the bytes' presence; "this is an email" is an inference the scanner makes
under stated rules). Each occurrence row carries:

- **Provenance coordinates with a named byte domain** — a decoded-text offset is not an
  evidence byte offset. Every hit records: evidence id → artifact locator → the
  transformation chain that produced the scanned text (e.g. "SQLite `moz_places.url` field",
  "UTF-16LE-decoded registry value", "carved region @ LBA range") → offset *within that
  domain*. A raw evidence byte range is recorded only when directly traceable.
- The matched value **verbatim** (never truncated) + decoding method + scanner rule id +
  scanner version + config digest (the run manifest makes reruns comparable — determinism
  is a property of *scanner version + config*, and both are recorded).
- **Validation tier**: `checksum` (structure with internal check: base58check/bech32
  wallet, Luhn — later kinds), `parser` (accepted by an authoritative parser: `Ipv4Addr`/
  `Ipv6Addr`/`url`), `pattern` (shape-only: email boundary match). Tier names say what was
  checked, not that the value is "valid" or benign.
- A short, bounded context window for triage. The case DuckDB already contains the parsed
  artifact text this was mined from, so context adds no new exposure class; exports are
  formula-guarded via `jsonguard`, and redacted-export policy applies (§5).

**Dedup never erases occurrences.** Canonicalization (case-folding a domain, E.164
normalization) lives in the separate `indicators` table; many occurrence rows reference one
canonical indicator. Enrichment operates on canonical indicators; provenance questions
always resolve through occurrences.

Layer 1 emits **no findings by default** — a phone number in a contacts DB is data. A
warninglist annotation (`warninglist_matches`: list name + version + rule — *not* a
`known_benign` boolean; presence on a warninglist means FP-prone, not benign) is a display
filter input, never a deletion. Warninglist ingestion itself is deferred past v0.

### Layer 3: enrichment as captured exchanges

The structural seam in `intel-core` (the one honest seam this design asks of it): split each
connector into

```text
acquire(CanonicalRequest)                  -> CapturedExchange   // network happens here
parse(&CapturedExchange, ParserIdentity)   -> Facets             // pure; live + replay share it
```

- `CapturedExchange` preserves the **whole exchange**, not just the body: canonical request
  (method, URL, params, non-secret headers), response status + headers + redirect chain +
  body bytes, resolved endpoint, TLS peer-certificate fingerprints where available,
  timestamps. Auth material is **redacted before storage** and replaced by a named
  credential identity ("webamon: account X, cognito session") — secrets never enter the
  case store.
- Multi-request sources (pagination, token refresh, discovery) record an **ordered exchange
  set** per source run with a termination reason.
- Storage: content-addressed blobs (sha256) + unique acquisition ids + a run manifest,
  transactionally committed. `--refresh` creates a **new acquisition** alongside the old;
  the schema has no update path for prior acquisitions. (This is a schema discipline, not a
  tamper-proofing claim — the case store is an ordinary file; hash-chained audit logging is
  a possible later hardening, not promised here.)
- **Replay**: rerunning analysis re-parses stored exchanges by acquisition id — same
  exchange + same parser version ⇒ same assertions, and a parser upgrade re-parses
  *preserved* input rather than re-querying a changed world. Cache reuse for a *new* enrich
  run keys on the canonical-request digest + source identity, never on (indicator, source)
  alone.
- **What this does and does not establish**: repeatable parsing over preserved acquisition
  records, and an exact record of what entered the analysis. It does **not** by itself
  prove the remote service produced those bytes (transport can be intercepted; ip-api is
  plaintext) — service attribution rests on transport controls, which is why transport
  metadata is recorded and plaintext sources are off by default (§5).
- **Inter-source disagreement is preserved.** The fleet stores per-source
  `ExternalAssertion`s (each pointing at its exchange + parser identity); `intel-core`'s
  merged singleton `Facets` view ("first-seen wins") is a display convenience only and is
  never what the case store keeps. Merge order for display follows source *registration*
  order — a documented, deterministic precedence — not network completion order.

### Findings from enrichment — only via local analytic rules

A provider's reputation flag is an assertion, not a finding. Enrichment data becomes a
`Finding` only when a **local, versioned analytic rule** (the issen-signatures /
forensic-pivot rule mechanism) fires over assertions — the rule, not the provider response,
is the source of severity, category, and code (`INTEL-*`). Such findings are phrased
"consistent with", carry `FindingContext.confidence` and the `queried_at` timestamp, and
reference the acquisition id; an `ExternalRef { scheme: "osint-<source>" }` carries no
query-bearing URL (rendering one would leak the indicator and may be authenticated or
ephemeral). Report prose states attribution: *"According to ip-api (queried
2026-07-23T11:02Z), 8.8.8.8 …"* — the observed fact remains only that the artifact
contained `8.8.8.8`.

**forensicnomicon needs no breaking change.** Indicators ride as
`SubjectRef { scheme: "indicator", kind: "email", id: <value> }` (report.rs:190-199);
`ExternalRef` is already "consistent with, never a verdict" (report.rs:201-212). Any
convenience constructor later is an additive minor bump.

## 5. The offline/online split — batteries-included, egress-governed

- **Compiled in always.** No Cargo feature gates on extraction or enrichment
  (Batteries-Included law governs compile-time capability). Runtime *policy* may restrict
  use (below) — that is configuration, not amputation.
- **Extraction runs in the default pipeline** with safe compiled resource limits; when a
  limit is hit the `ScanSummary` says so **loudly** (an explicit truncated/incomplete
  status in the run manifest and CLI output) — silent caps would be a fail-loud violation.
- **Enrichment: explicit invocation + informed preflight.** `issen enrich` never fires as
  a side effect of ingest. Before any egress it prints a **preflight plan** — which
  indicators (count by kind), to which sources, over which transport, under which
  credential identity, estimated request count/budget — and requires confirmation
  (`--yes` for scripted use, still logged). Rationale: case-data disclosure, adversary
  tip-off (querying infrastructure the adversary controls or monitors), reproducibility,
  quota/cost, and the analyst may not have authority to send victim PII anywhere.
- **Source policy classes**: breach/account-enumeration sources (OSINT Industries) are a
  distinct class requiring per-source opt-in — submitting victim emails to a breach index
  is a governance decision, not a default. **Plaintext-HTTP sources (ip-api free tier) are
  disabled by default** and require a per-source override; assertions derived over
  plaintext are marked transport-untrusted in the store and the report.
- **Governance hooks (design-level, not a GRC suite)**: per-source enable/disable in org
  config (so policy can forbid a source without a rebuild), provider-ToS/retention notes
  per connector, and the credential-identity model of §4 (secrets outside the case store).
  Rate/cost control: per-source concurrency caps, budgets, backoff honoring
  `RateLimited`, and a resumable queue so a long enrich run can be cancelled and continued.

## 6. Robustness + validation (extraction runs on attacker-controlled bytes)

- **Panic-free posture**: fleet parser recipe — `forbid(unsafe)`, `unwrap_used`/
  `expect_used` denied, a fuzz target per scanner + a whole-scan target.
- **No ReDoS by construction**: Rust `regex` is linear-time; the seed scanners are
  shape-regex + authoritative-parser validation (`Ipv4Addr`/`Ipv6Addr` as oracle — exactly
  how `browser-forensic-search/src/ioc.rs:166-190` already does it, plus `linkify`'s
  boundary-aware email scanner). Resource guards: bounded match counts and context
  allocation **with loud truncation status** (§5), never silent.
- **Primary API is streaming + sink-based** (`scan(reader, base_coordinate, config, sink)
  -> ScanSummary`) with defined overlap windows so chunk boundaries cannot split matches;
  the `&[u8]` convenience wrapper sits on top. v0's parsed-text path uses the wrapper; the
  streaming path is what carved/unallocated scanning (later slice) needs, and designing the
  API around it now avoids a breaking rework.
- **Acceptance criteria before promotion/publish (Doer-Checker, tiered):** a labeled
  extraction corpus with expected spans (real third-party data — the Case-001 Szechuan
  corpus is the fleet's convergence corpus; bulk_extractor on the same images serves as the
  independent oracle to reconcile against), per-kind false-positive ceilings, chunk-boundary
  equivalence tests, bounded-memory tests, and — for enrichment — live-capture vs replay
  parse-equivalence tests and cache-key separation tests. Fuzzing proves robustness, not
  correctness; the corpus + oracle carry correctness.

## 7. Slices (each gated on the last)

1. **`issen-indicators` v0** (offline, issen-internal): email/IPv4/IPv6/URL scanners
   (seeded from browser-forensic-search `ioc.rs`), UTF-8 + UTF-16LE, occurrence +
   canonical tables, `ScanSummary` manifest, fuzz targets. Run at ingest over parsed
   artifact text. **Gate to slice 2: measured FP rates + analyst usefulness on the
   Szechuan corpus, reconciled against bulk_extractor.**
2. **More kinds** as evidence warrants: domains, phone (E.164-normalized, `pattern` tier),
   wallet (checksum tier), hashes. Each with corpus + ceiling before merge.
3. **Land `~/src/intel`'s worktree onto `main`**; implement the acquire/parse connector
   split + `CapturedExchange` store; deterministic merge policy; settle crate names
   (pre-publish gate).
4. **`issen enrich`**: preflight plan, source policy classes, captured-exchange storage,
   replay, local analytic rules for `INTEL-*` findings.
5. **Promotion + migrations**: extract the scanner crate; migrate browser-forensic-search
   and issen-navigator with a differential-test matrix; indicators as forensic-pivot pivot
   keys; carved/unallocated-space extraction via the streaming API.

## 8. Adversarial critique (Codex GPT-5) and reconciliation

Codex produced 35 numbered critiques (transcript:
`~/.claude/jobs/cc3ae0c8/tmp/codex-critique.md`). Disposition — **accepted (design changed)**
unless noted:

| # | Critique (condensed) | Disposition |
|---|---|---|
| 1 | "Extraction is an observation" is epistemically false — classification is inference | **Accepted.** §4 now splits occurrence (fact) from classification (versioned inference); "candidate indicator" language throughout |
| 2 | Deterministic extraction requires extractor identity | **Accepted.** Run manifest: scanner version + rule id + config digest per run |
| 3 | Cache replay determinism unsupported without an acquire/parse split | **Accepted.** The connector split *is* now the intel-core seam (§4) |
| 4 | Body+hash is not a transcript — capture the whole exchange | **Accepted.** `CapturedExchange` with request, headers, redirects, status, TLS fingerprints |
| 5 | "Courtroom reproducibility" overclaims; preservation ≠ attribution | **Accepted.** Reworded to "repeatable parsing over preserved acquisition records"; transport limits stated |
| 6 | [Q]-layer framing launders OSINT into evidence semantics | **Accepted in substance.** Enrichment reclassified as supplementary analysis material, "[Q]-adjacent"; no claim of implementing the QUERY ENGINE contract |
| 7 | "Append-only" is rhetoric, not a storage guarantee | **Accepted, scaled.** Content-addressed blobs + acquisition ids + no-update schema; explicitly *not* claimed tamper-proof; hash-chained audit deferred |
| 8 | Cache key unspecified | **Accepted.** Canonical-request digest + source identity; replay by acquisition id |
| 9 | EnrichmentRecord collapses acquisition/parse/logging | **Accepted, scaled.** Exchange vs assertion split; five-table taxonomy folded to the minimal set (Codex itself: "keep the first implementation small") |
| 10 | Pagination/multi-request ignored | **Accepted.** Ordered exchange sets + termination reason |
| 11 | First-seen-wins merge is nondeterministic and hides disagreement | **Accepted.** Per-source assertions preserved; merged view display-only, registration-order precedence |
| 12 | "Fabrication structurally impossible" indefensible | **Accepted.** Claim deleted; assertions must reference their exchange + parser run |
| 13 | intel repo is the wrong home for forensic extraction | **Accepted via staging.** v0 lives issen-side; standalone home decided at promotion, not defaulted into `intel` |
| 14 | `intel-indicator` split premature; candidate ≠ query indicator | **Accepted.** No split; extraction has its own candidate type; mapping to `Indicator` only at enrich time — the split proposal is dropped entirely |
| 15 | `Indicator::detect()` is an attractive nuisance | **Partially accepted.** Extraction never uses `detect` (kind-specific scanners; ambiguity carried as multiple candidates). `detect` stays for interactive CLI input with `--kind` override — single-value UX, human in the loop |
| 16 | Parsed-text offsets destroy provenance | **Accepted.** Named byte domains + transformation chain (§4); raw byte ranges only when traceable |
| 17 | Silent caps violate fail-loud | **Accepted.** Loud truncated/incomplete `ScanSummary` status; defaults recorded in manifest |
| 18 | Context capture is a PII/minimization hazard | **Partially accepted.** Bounded windows, redacted-export policy, jsonguard. Rejected as scoped here: table-level encryption/access control is a case-store-wide concern (the DuckDB already holds the full parsed evidence text; context adds no new exposure class), not this module's |
| 19 | Egress guard too coarse — subcommand ≠ informed consent | **Accepted.** Mandatory preflight plan + confirmation; per-source authorization for sensitive classes |
| 20 | Legal/contractual threat model missing | **Accepted, scaled.** §5 governance hooks (ToS/retention notes, org-config source disable, credential identity); a full GRC framework is out of scope and said so |
| 21 | Plaintext ip-api deserves more than a warning | **Accepted.** Plaintext sources disabled by default; per-source override; transport-untrusted marking |
| 22 | Credential/secret handling absent | **Accepted.** Secrets outside case store; redaction before storage; named credential identity |
| 23 | Rate/cost/abuse behavior undesigned | **Accepted, scaled.** Budgets, per-source concurrency caps, backoff, resumable queue; preflight carries the estimate |
| 24 | `known_benign` is semantically sloppy | **Accepted.** `warninglist_matches` with list+version; no benign boolean |
| 25 | Warninglists violate v0 simplicity | **Accepted.** Explicitly deferred past v0 |
| 26 | v0 scanner scope too broad; drop email too | **Partially accepted.** Phones/wallets/cards/usernames/hashes deferred (CCN wasn't even in `IndicatorKind` — correct catch). **Email stays in v0**: the fleet already runs a boundary-aware, `linkify`-based email scanner in production (browser-forensic-search); porting proven code is not new risk, and email is the highest-value kind for the use case that motivated this design |
| 27 | Full-buffer scan API is wrong | **Accepted.** Streaming sink-based primary API; slice wrapper on top |
| 28 | Dedup erases evidentiary occurrences | **Accepted.** Occurrences (immutable) vs canonical indicators (normalized) — two tables |
| 29 | ExternalRef misuse (ephemeral/leaky URLs) | **Accepted.** Findings reference acquisition ids; no query-bearing URLs in refs |
| 30 | Auto-grading provider flags as Threat contaminates | **Accepted.** Findings only via local, versioned analytic rules; the rule is the severity source |
| 31 | `osintel` weak; binary `intel` retains confusion | **Partially accepted.** Agreed nothing proposed is clearly right → naming is now an explicitly open, publish-blocking decision (§3) rather than a recommendation. Codex's `indicator-enrichment-core` is honest but leaden; the personal CLI's local binary name is the owner's call and blocks nothing until publish |
| 32 | `issen-indicators` is premature indirection | **Rejected (with the spirit kept).** A small per-concern crate matches the issen workspace's existing granularity (35+ crates) and keeps the ingest path's dependency surface auditable; it stays unpublished. The spirit — no public crates before a proven boundary — is adopted (13/14) |
| 33 | Migration plan incomplete | **Accepted.** Inventory + differential-test matrix at promotion time (§7 slice 5) |
| 34 | No verification corpus / acceptance criteria | **Accepted.** §6: labeled corpus, bulk_extractor as independent oracle on the Szechuan images, per-kind FP ceilings, replay-equivalence tests |
| 35 | Premature "yes — build" | **Partially accepted.** The yes stands (three in-fleet duplications + the user's direct ask are the demand signal), but the plan is restructured into Codex's "narrow experiment": slice 1 is offline-only, issen-internal, and gates everything else on measured FP data |

**Codex's top-3 and their resolution:** (1) extraction epistemics → the occurrence/
classification split is now the foundation of §4; (2) transcript/replay insufficiency →
the acquire/parse connector split + `CapturedExchange` is now the central intel-core seam;
(3) egress governance → preflight plans, source policy classes, plaintext-off-by-default,
and credential separation are now §5. The strongest deliberate rejections: keeping email in
v0 (proven in-fleet code), keeping `issen-indicators` as a workspace crate (fits local
convention), and scoping case-store encryption out (a store-wide concern, not this module's).
