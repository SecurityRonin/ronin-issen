# 18. Supply-chain policy — cargo-vet mechanisms and Renovate posture

Date: 2026-07-30
Status: Accepted

## Context

Three gates keep fleet dependencies trustworthy, and each catches a threat the other two
miss: **Renovate** keeps them *fresh*, **`cargo deny`** catches *known-bad* (published
RustSec advisories, forbidden licenses, banned duplicates), and **`cargo vet`** catches
*unreviewed code* — the supply-chain-injection layer neither of the others sees, since it
demands a human source review of every dependency version and so blocks a compromised
maintainer's backdoor *before* any advisory exists (the xz-utils scenario).

The `deny` half has been stable. The `vet` and Renovate halves accumulated rules
piecemeal, and a survey of what the fleet actually *does* against what is actually
*written* found three divergences worth deciding rather than restating:

1. **A mechanism in daily use was undocumented.** The written rules named two ways to
   satisfy `vet` — first-party declaration and `[[exemptions]]`. But repos also carry
   `[[trusted.*]]` **publisher-trust** entries (timeglyph trusts `displaydoc`'s publisher
   Manishearth, whom Mozilla's audit set already trusts, and our own `forensicnomicon`,
   `forensicnomicon-core`, `forensicnomicon-data` under `h4x0r`). Publisher trust is
   *stronger* than an exemption — it asserts a trust relationship rather than admitting
   an unreviewed crate — yet no rule told anyone to prefer it, so the choice among the
   three was being made ad hoc.

2. **The Renovate rules emphasised the wrong layer.** The written guidance leads with
   `rangeStrategy: "bump"` as the cure for staleness. That fixes a *narrow requirement*
   (layer 1), which is real but rare. The failure that actually recurred was **lock lag**
   (layer 2) — a caret that could reach the new version while the committed lock sat
   behind it. `rangeStrategy` cannot fix that; `lockFileMaintenance` **with automerge**
   is what does, and repos were missing the automerge half.

3. **The library-vs-app automerge split left hybrids undecided, and rested on human
   vigilance.** The rule was "automerge patch/minor for *app* repos; never auto-bump a
   published library's deps in a way that raises its MSRV." A repo that publishes a
   library *and* ships binaries (timeglyph) fits both halves, so the rule gave no answer —
   and the library half protected the MSRV promise by asking a human to notice an MSRV
   regression in a bump PR, which is exactly the kind of enforcement-by-instruction the
   fleet rejects elsewhere.

## Decision

### 1. cargo-vet — four cases, one decision tree

Every unsatisfied `vet` finding falls into exactly one case. Work **down** the list and
use the first that applies; each is stronger than the ones below it, so reaching for a
lower mechanism when a higher one fits is a defect.

| # | The crate is… | Mechanism | Why this and not the next one down |
|---|---|---|---|
| 1 | **ours, a workspace member** | `[policy."<crate>"] audit-as-crates-io = false` in `supply-chain/config.toml` | It is first-party code, not a crates.io dependency. Auditing it *as* crates.io is simply the wrong classification, and it makes every version bump red (see below). |
| 2 | **ours, consumed from crates.io** | `[[trusted.<crate>]]` with `user-id = 347968` (`h4x0r`) in `audits.toml` — via `cargo vet trust <crate> h4x0r` | Case 1 doesn't apply (it genuinely is a registry dep), but we know the publisher: us. A trust entry says so once and covers every future version. |
| 3 | **third-party, published by someone an imported aggregate auditor already trusts** | `cargo vet trust <crate> <publisher>` | A real trust assertion, transitively grounded in Google/Mozilla/Bytecode-Alliance/Embark's own review, and version-agnostic. Strictly better than admitting the crate is unreviewed. |
| 4 | **third-party, and the locked version outruns the aggregate audits** | `[[exemptions]]` with a truthful note (`"not individually source-reviewed — aggregate-audit lag"`) | The honest floor. cargo-vet credits only exact-version or delta-chain matches, so a genuine version gap (Google audits `serde` to `1.0.219`, the tree is on `1.0.229`) has no better answer. An exemption **admits** the crate is unreviewed, which is the accurate statement. |

**Never `cargo vet certify --accept-all`.** A certify record asserts *a human reviewed
this source*. Bulk-certifying without reading the source fabricates the gate's pass
condition — worse than an honest exemption, because it converts "unreviewed" into a false
positive claim of review. This is the adler2 law applied to supply chain: eliminating a
signal by asserting something untrue is not a fix. (Guard-flagged three times before the
rule was written down; the fleet's bulk-certified repos were converted to exemptions.)

**Import the aggregate audit sets** so cases 3 and 4 stay small and vet stays a real gate
rather than CI noise: `bytecode-alliance`, `embark`, `google`, `mozilla` in
`[imports.*]`. A mis-maintained cargo-vet — a red gate nobody acts on — is worse than no
cargo-vet; keep the imports current or remove the gate, never leave it half-configured.

**Case 1 is the fleet's most expensive lived failure.** An own crate left on the default
`audit-as-crates-io = true` makes `cargo vet --locked` audit the *workspace member* as if
it were the published crates.io crate, demanding a per-version audit the freshly-bumped
version cannot have. So **every** release-plz version bump turns the release PR's vet job
red while every other check is green. This silently blocked **28 of 44** open release PRs
across the fleet — they had accumulated unmerged for weeks precisely because each looked
"CI-red" and nobody chased the single vet line. Declaring own crates first-party flipped
all 28 green in one pass. Do **not** band-aid this by adding the new version to
`[[exemptions]]`: that re-breaks on the very next bump.

### 2. Renovate — lock currency is the primary control

```jsonc
{
  "lockFileMaintenance": { "enabled": true, "automerge": true },
  "rangeStrategy": "bump",
  "packageRules": [ /* grouped into one PR per wave; scoped to our namespace */ ]
}
```

- **`lockFileMaintenance` with `automerge: true` is the load-bearing setting**, because
  lock lag (layer 2) is the staleness that actually recurs. Enabling maintenance without
  automerge just produces a PR queue that ages into the same staleness it was meant to
  cure.
- **`rangeStrategy: "bump"`** widens the requirement itself, which is the *only* fix for a
  caret that cannot reach a published major (layer 1) — Renovate's default does not widen
  ranges. Necessary, but not the common case.
- **Group** bumps into one PR per wave and **scope** to our crate namespace, so a wave is
  one review rather than N.
- Neither setting can reach **layer 3** (newest code exists only locally, never
  published). That is a *release* gap, fixed by release-plz / a tag-driven release that
  actually publishes — a green source tag is not a published crate.

### 3. Automerge is gated by the MSRV job, not by repo role

**Any repo may automerge patch/minor dependency bumps — library, app, or both — provided
its low-MSRV job is a required, blocking status check.**

This supersedes the "apps only" split. The thing a published library must protect is its
**MSRV promise**, and the honest enforcement of that promise is the MSRV CI job: if a bump
raises the minimum Rust version, the job fails and automerge cannot complete. Structural
enforcement, not a human remembering to check a bump PR. It resolves the hybrid case
directly — timeglyph publishes a library *and* ships binaries, and its MSRV job is what
decides, so no role classification is needed.

The corollary is a hard prerequisite: **a repo without a required MSRV check does not
automerge.** Turning automerge on there removes the only thing standing between a
dependency wave and a silently-raised MSRV.

### 4. Which gates block, and therefore what a red means

| Gate | Posture | A red means |
|---|---|---|
| fmt · clippy · test · MSRV · `cargo deny` · `cargo vet` | **Blocking** (required status checks; `enforce_admins: false` so release-plz and direct pushes still work) | Fix it. It stops a merge. |
| dependency-freshness / `cargo outdated` | **Advisory** (`continue-on-error: true`) | Bot-owned. Renovate clears it on its next cadence. |

**Do not fire-drill an advisory red.** Hand-running `cargo update`, committing to `main`,
and pushing to chase a `continue-on-error` freshness X is self-inflicted churn that fixes
nothing that was broken — it was chased three times in one session while Renovate was
already configured to clear it. Read the job's `continue-on-error` and the branch's
required checks *before* reacting; "red" is not "blocking."

The dual still holds: reds *you* introduced, and genuinely required checks, are yours to
fix before pushing.

**Pair Renovate with the vet gate.** Making `Cargo Vet (supply-chain)` a required check
means a bump PR whose locked versions outrun the audits fails vet and cannot merge, so the
exemption list self-shrinks as the aggregators catch up instead of drifting.

## Consequences

- One decision tree replaces ad-hoc choice among the vet mechanisms, and it prefers the
  strongest applicable one — so exemptions shrink to what genuinely is unreviewed.
- The release-PR-blocking failure (case 1) becomes a one-time per-repo fix rather than a
  recurring per-version tax.
- `certify --accept-all` is closed off explicitly, so greening the gate can no longer be
  done by asserting something untrue.
- Automerge safety becomes a property of CI configuration that can be *audited* (does this
  repo have a required MSRV check?) rather than of repo taxonomy that has to be judged.

**Adoption debt, stated honestly:** the required-status-check posture in §3 and §4 is the
decision, not yet the fleet's uniform state — timeglyph, for one, currently has no branch
protection, so its checks advise rather than block. Until a repo's MSRV and vet jobs are
actually required, §3's automerge permission does not apply to it.

## References

- [ADR-0010](0010-prefer-our-own-crates.md) — prefer our own crates (cases 1 and 2 exist
  because the fleet consumes its own published crates).
- [ADR-0012](0012-paranoid-gatekeeper-security-standard.md) — the security standard these
  gates enforce for `*-core` / `*-forensic` crates.
- [ADR-0013](0013-batteries-included.md) — when full features trip a gate, fix the gate,
  not the feature set. The exemption/trust mechanisms here are how a gate gets fixed
  honestly.
- `~/.claude/skills/release.md` — release mechanics, including the release-plz PR flow
  whose vet interaction case 1 describes.
