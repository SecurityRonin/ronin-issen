# Fleet merge order — 152 open PRs

**Generated:** 2026-08-02. **Scope:** every open PR across the 91 component repos plus `ronin-issen`.

152 open PRs. **140 from the DRY-audit campaign; 10 are pre-existing `release-plz` release PRs** that predate it and are independent of everything below.

Nothing here is merged. This document is a sequence, not an instruction — the ordering constraints are real, the phase boundaries are a recommendation.

---

## The one thing to read first

**Merging this volume before fixing the gates is the wrong order.** The audit established that several gates report success over work they never did — most sharply, `cargo vet --locked` asserts nothing in **80 of 81 repos**, because `cargo fetch` rewrites `Cargo.lock` in the runner before `--locked` is evaluated. Landing 140 PRs through gates known to be broken buys volume and no assurance.

Phase 1 exists for that reason. It is small.

---

## Live CI status — 2026-08-02

Collected read-only via `gh pr list --json statusCheckRollup` across all 92 repos. Status codes used throughout this document:

| Code | Bucket | Count |
|---|---|---|
| **G** | **GREEN** — every dispatched check passed | **115** |
| **R** | **RED** — at least one check failing | **29** |
| **N** | **NONE** — no CI check ever dispatched | **8** |
| **P** | PENDING — still running | 0 |
| **C** | CONFLICT — `mergeable == CONFLICTING` | 0 |

**Nothing is pending and nothing conflicts.** Every PR has settled; the queue is a static picture, not a moving one.

### Two counting rules that change the answer

**Socket Security is not CI.** `Socket Security: Project Report` and `Socket Security: Pull Request Alerts` are a GitHub App that runs on every PR regardless of branch filters. They appear on all 152 PRs. Counting them makes a PR with no CI look green — that is exactly how `blazehash` #7/#8 read as passing. Every count above excludes them.

**A green check from an unrelated workflow is not a green CI run.** `luks-forensic` #2 carries four passing `Fuzz` checks while its `CI` workflow produced *zero* check-runs. It is **N**, not **G** — the same startup failure as its two sibling pilots, just masked by a workflow that did dispatch.

### The NONE bucket — no checks means *not run*, never *passed*

All 8, with the reason each one dispatched nothing:

| PR | Head branch | Why no checks |
|---|---|---|
| `blazehash` **#7** | `fix/vet-prune-orphaned-exemptions` | **Wrong base.** Targets `fix/lock-refresh-vet-and-csv`; `ci.yml` triggers on `pull_request: branches: [main]`, so nothing dispatches |
| `blazehash` **#8** | `fix/widen-ewf-caret-0.4` | **Wrong base.** Same as #7 |
| `ronin-issen` **#8** | `docs/fleet-dry-audit` | **Repo has no CI.** No `.github/workflows` directory exists |
| `ronin-issen` **#9** | `docs/split-constitution` | **Repo has no CI.** Same as #8 |
| `ewf-forensic` **#4** | `ci/adopt-reusable-workflow` | **Workflow startup failure.** Runs *are* dispatched (`event: pull_request`) and fail with **0 jobs** — `uses: SecurityRonin/fleet-config/.github/workflows/rust-ci.yml@29f8011615059de76d9ad1a41ade1c6f9b70162c` cannot resolve, because `SecurityRonin/fleet-config` returns 404 to an org-owner token. No check-runs are created, so the rollup is empty |
| `ntfs-forensic` **#5** | `ci/adopt-reusable-workflow` | **Workflow startup failure.** Same unresolvable `uses:` reference |
| `luks-forensic` **#2** | `ci/adopt-reusable-workflow` | **Workflow startup failure.** Same unresolvable `uses:`. Its four green `Fuzz` checks come from a separate workflow and say nothing about CI |
| `vhdx-forensic` **#6** | `agent/fix-partial-present-blocks` | **Awaiting approval.** `isCrossRepository: true` — a fork PR from `ebrig`. Both `CI` and `Docs` runs sit at `action_required` pending a maintainer's approval to run |

The three CI pilots are one root cause, not three: **Phase 0.3 is what unblocks them.** `blazehash` #7/#8 are unblocked by merging #5 and retargeting. `vhdx-forensic` #6 needs a human to click *Approve and run* — it is the only fork PR in the fleet and the only one this document has not previously accounted for.

### The RED bucket — 29 PRs, and most are not the PR's fault

Established by comparing each failing check against the **same-named check on that repo's `main` head**, then reading the failing job log. Job-name matching alone is not sufficient — see the time-dependent note below.

**Introduced by the PR — 14, genuinely blocking**

| PR | Failing | Cause |
|---|---|---|
| `qcow2-forensic` **#4** | all 8 jobs | `core/Cargo.toml` commits `forensic-testgate = { path = "/Users/4n6h4x0r/.claude/jobs/6125d941/tmp/forensic-testgate" }` — a **machine-local absolute path**. `cargo metadata` fails, so every job dies at once. Carries its own `# TODO(before merge)` marker |
| `vhd-forensic` **#2** | all 10 jobs | Same local path dep |
| `vhdx-forensic` **#4** | all 6 jobs | Same local path dep |
| `ewf-forensic` **#8** | `Test (ubuntu-latest)` | Real test failure: 2 of 13 fail, `differential_zeros_128s_both_clean` and `differential_zeros_compressed_both_clean` panic at `forensic/tests/differential_tests.rs:110:5`; `libewf_glob: invalid filename - missing extension` |
| `browser-forensic` **#8** | `Cargo Vet` | `A file in the store is not correctly formatted` — the PR commits a malformed vet store |
| `aff4-forensic` #3 · `dmg-forensic` #3 · `ewf-forensic` #7 | `Cargo Vet` | `safe-read:0.2.1 missing ["safe-to-deploy"]` |
| `disk-forensic` #5 | `Cargo Vet` | `ewf:0.4.7 missing ["safe-to-deploy"]` |
| `disk-forensic` #6 | `Clippy`, `Coverage`, `Cargo Vet` | `ewf:0.4.7` + `safe-read:0.2.1` unvetted, plus a real clippy and coverage regression |
| `leveldb-forensic` #5 · `srum-forensic` #5 | `Cargo Vet` | `jsonguard:0.2.4 missing ["safe-to-deploy"]` |
| `journald-forensic` #3 | `Cargo Vet`, `Coverage` | `safe-read:0.2.1` unvetted + uncovered production lines |

The nine `Cargo Vet` entries are **one mechanical defect repeated**: the `fix/vet-trust-our-crates` PRs add `trust` entries but miss the newly-published versions their own lock pulls in. Each is a one-line `cargo vet trust <crate> h4x0r` per ADR-0018 — not a design problem.

**Pre-existing on `main` — 13, inheriting a known-red gate**

| PR | Failing | Also red on `main` |
|---|---|---|
| `issen` **#12, #13, #14** | `Rustfmt`, `Clippy`, `Test (ubuntu/macos)`, `Cargo Deny`, `Cargo Vet` | Yes — all five fail on `main` head (2026-07-29). `issen`'s `main` is broken independently of these PRs |
| `forensic-vfs-engine` **#7, #9** | `cargo vet` | Yes — `zfs-forensic-core:0.1.1 missing ["safe-to-deploy"]` fails on `main` |
| `bluetooth-forensic` **#3** | `Cargo Vet`, `Coverage (100% lib)` | Yes — both fail on `main` (`itoa`, `memchr`, `serde_json`, `zmij` missing `safe-to-run`) |
| `chromium-storage-forensic` **#2** · `signal-desktop-forensic` **#2** | `public-api` | Yes — the `public-api` diff fails on `main` |
| `wire-desktop-forensic` **#1** | `public-api`, `SemVer (vs crates.io)` | Yes — both fail on `main` with `error: invalid toolchain name ''`. A broken workflow input, not a code problem |
| `blob-decoder` **#5** | `coverage`, `freshness` | `coverage` yes (uncovered lines lacking `// cov:unreachable`). `freshness` is advisory — see below |
| `timeglyph` **#24, #25** | `freshness` only | Yes — and `freshness` is `continue-on-error: true`. **These two gate nothing and are effectively green** |

**Time-dependent gates — main's green is stale, not the PR's doing — 2 (+3 overlapping)**

`cargo deny` and `cargo audit` fetch the advisory database at run time, so a job that passed on a `main` head from days ago is not evidence the PR broke it.

- `blazehash` **#5, #6** — `deny` fails on **RUSTSEC-2026-0222** via `wasmtime 25.0.3` ← `yara-x 0.9.0`. `main`'s `deny` shows *success*, but that run is from **2026-07-28**, before the advisory. `origin/main`'s own `Cargo.lock` pins the identical `wasmtime 25.0.3` / `yara-x 0.9.0`, so `main` would fail the same way if re-run today. **Not blocking, and not introduced by these PRs.**
- `issen` **#12, #13, #14** — `Cargo Audit` flags the same RUSTSEC-2026-0222 against a `main` run from 2026-07-29. Same reasoning. (These three are already blocked by the pre-existing failures above.)

**Infrastructure flakes — 2, no gate actually evaluated**

- `ewf-forensic` **#5** — `Cargo Deny` never ran: `failed to resolve source metadata for docker.io/library/rust:1.85.0-alpine3.20`, `dial tcp … i/o timeout`, `DeadlineExceeded`.
- `vsc-forensic` **#2** — `Cargo Vet` never ran: `[56] Failure when receiving data from the peer (OpenSSL SSL_read … unexpected eof)` while fetching `syn`.

Both would likely clear on a re-run. No re-runs were dispatched for this survey.

### Ready to merge right now

**87 PRs are green, conflict-free, and first in their repo's sequence.** That is the technically-mergeable set, and it is genuinely large — the campaign is in better shape than the RED count suggests.

**But the plan's own ordering says merge far fewer than 87 today.** Phase 1 is the stated gate for the bulk, and 55 of those 87 are `fix/vet-trust-our-crates` (Phase 4, explicitly *after* Phase 3). The set that is green **and** at the front of the plan's queue:

- **Phase 2 — both green, merge now:** `forensicnomicon` **#26**, `vhd-forensic` **#5**
- **Phase 3 — 13 of 20 green:** `jsonguard` **#5** (merge first — the six CSV consumers need it as 0.2.5), then `state-history-forensic` #2, `shrinkpath` #3, `ewf-forensic` #6, `memory-forensic` #7, `sqlite-forensic` #8, `winevt-forensic` #7, `prefetch-forensic` #4, `srum-forensic` #2, `forensicnomicon` #24, `vmdk-forensic` #3, `livedisk-forensic` #2, `4n6mount` #11
- **Phase 3 — 7 red, all diagnosed above:** `disk-forensic` #6, `ewf-forensic` #7, `leveldb-forensic` #5, `browser-forensic` #8, `srum-forensic` #5, `blazehash` #6, `issen` #12

So: **15 PRs are ready and at the front of the queue.** The remaining 72 of the technically-ready 87 are waiting on the plan's phase order, not on their own CI.

Two PRs report `mergeable: UNKNOWN` (`xpress-huffman` #3, `zfs-forensic` #2) — GitHub had not finished computing mergeability; re-check before merging. One is `BLOCKED` by branch protection or a required review (`chromium-safestorage` #2) despite being green.

---

## Phase 0 — decisions and prerequisites (no PRs merge here)

| # | Item | Blocks |
|---|---|---|
| 0.1 | **Branch protection** — 9 of 10 sampled repos have none while Renovate automerges. ADR-0018's automerge rule has no enforcement layer to stand on | Everything; without it no check is required |
| 0.2 | **Licence decision** — 17 repos publish a Terms of Service naming MIT against an Apache-2.0 `LICENSE`. Evidence says the docs are wrong; it is a published legal statement, so it is your call | The legal-doc rollout |
| 0.3 | **Create `fleet-config` and the reusable-workflow repo, both PUBLIC** — a public caller can only reference a public callee. Private makes the mechanism inert | Phase 1, Phase 7 |
| 0.4 | **Publish the four new crates** — `safe-decode`, `timeglyph-core`, `forensic-testgate`, `forensicnomicon-derive` are local-only | Phase 6, and every migration that justifies them |

---

## Phase 1 — fix the gates (small, high leverage)

| Item | Detail |
|---|---|
| **`cargo fetch --locked`** | 80 repos. Route it through the reusable workflow rather than 80 PRs — already fixed there at `f49dff5`. This restores a supply-chain guarantee that is currently false fleet-wide |
| **Coverage-gate semantics** | 6 implementations, 2 meanings of “100%”. Two of the three actively pressure you to delete defensive guards ADR-0012 requires |
| **Coverage scope** | `ntfs-forensic` runs `--lib` with no features under a job named “Coverage (100% lines)”, leaving 37 lines outside the measurement |

---

## Phase 2 — remove the cleanup trap (2 PRs)

Do this early. It is two PRs and it removes a live hazard for anyone running any `target/`-cleaning tool.

- `forensicnomicon` **#26** — **G** — untrack 781 files under `bindings/python/target/`
- `vhd-forensic` **#5** — **G** — untrack 391 files under `fuzz/target/`

Both green, both first in their repo's sequence. **This phase is ready to merge today.**

Both are index-only: files stay on disk, no source change. A `cargo sweep` already deleted 1,143 tracked files once because of this.

---

## Phase 3 — the actual defects (~15 PRs)

These fix real bugs. Small, independent, and the highest value per merge.

| Repo | PR | Status | Defect |
|---|---|---|---|
| `state-history-forensic` | #2 | **G** | Release-mode wrapping subtraction — `nearest()` returns the **wrong** cohort member |
| `shrinkpath` | #3 | **G** | `dir_length(0)` overflows from the documented public API |
| `disk-forensic` | #6 | **R** | Unbounded 16 GiB allocation from an untrusted VHD length field |
| `ewf-forensic` | #7 | **R** | `EwfReader::open` panics on a trailing-dot path |
| `memory-forensic` | #7 | **G** | Byte-slice panic on a REG_SZ value from a memory image |
| `jsonguard` | #5 | **G** | CSV formula guard fires only on character 0 |
| `leveldb` #5 **R** · `sqlite` #8 **G** · `browser` #8 **R** · `srum` #5 **R** · `winevt` #7 **G** · `blazehash` #6 **R** | | | CSV formula injection — attacker-controlled evidence written unguarded |
| `issen` #12 **R** · `prefetch` #4 **G** · `srum` #2 **G** | | | Timestamp edge-semantics; `srum` is **semver-breaking** (0.2→0.3) |
| `forensicnomicon` #24 | | **G** | 7 wrapping `offset + N > len` guards |
| `vmdk` #3 **G** · `livedisk` #2 **G** | | | Panic-capable readers |

**13 of these 20 are green.** Of the 7 red, five are the PR's own doing — `disk-forensic` #6 (a real `Clippy` + `Coverage` regression on top of two missing trust lines), and `ewf-forensic` #7, `leveldb` #5, `srum` #5, `browser` #8 (each one `cargo vet` entry short). The other two, `blazehash` #6 and `issen` #12, are red on gates their own `main` already fails.

### The jsonguard chain — order-sensitive, do this first

All six CSV consumers require `jsonguard = "0.2"` (a caret that already admits 0.2.5) but their committed locks pin **0.2.4**. So **no manifest edit is needed anywhere** — only a lock refresh, and only after publish.

| Step | Action |
|---|---|
| 1 | Merge **`jsonguard #5`** — ready for review, `mergeable: CLEAN`, all 8 checks pass |
| 2 | Merge the **release-plz PR** it triggers. Its commits are `fix:` type, so 0.2.4 → **0.2.5** |
| 3 | In each of the six: `cargo update -p jsonguard` — lock moves 0.2.4 → 0.2.5 |
| 4 | Merge `leveldb #5`, `sqlite #8`, `browser #8`, `srum #5`, `winevt #7`, `blazehash #6` |

**Why the order matters.** Merging the six *before* 0.2.5 publishes ships them against **0.2.4**, which has the `= + - @` guard but **not** the whitespace/`Cf` lead-in fix. They would close the plain injection vector while leaving `" =cmd"`, `\r=cmd` and the zero-width family bypassing it — and read as complete. Still a net improvement, but not the fix the PR titles imply.

**Order within Phase 3:** `jsonguard` **#5 first** — the six CSV consumers resolve to published `jsonguard`, and its guard is incomplete until #5 ships as 0.2.5.

**Ordering constraint:** `ewf-forensic` #6 (`lru`) must merge **and publish** before `4n6mount` can drop its transitive `lru` ignore. `4n6mount` #11 carries that ignore with the removal condition stated inline.

---

## Phase 4 — supply-chain bulk (73 PRs)

`fix/vet-trust-our-crates` — 73 repos, config-only, no code. Clears the single largest finding: 79 repos clearing our own crates by `exemption` where ADR-0018 requires `trust`.

**67 of the 73 are green; 6 are red** — `aff4` #3, `dmg` #3, `ewf` #7, `journald` #3, `leveldb` #5, `srum` #5 (plus `browser` #8 on a malformed store and `disk` #5). Every one is the same omission: the PR adds `trust` entries but its lock pulls a *newly published* version of one of our crates that has no audit record — `safe-read:0.2.1`, `ewf:0.4.7`, `jsonguard:0.2.4`, `zfs-forensic-core:0.1.1`. One `cargo vet trust <crate> h4x0r` line each. Worth fixing as a single sweep rather than six separate follow-ups.

**Merge after Phase 3**, not before. `ewf-forensic` #6 and `4n6mount` #11 both add `supply-chain/config.toml` lines; landing 73 supply-chain PRs first forces two rebases, landing them after forces 73. Fewer rebases the other way round.

---

## Phase 5 — lint sweep (27 PRs)

`lints/canonical-lints` (12) · `lints/workspace-lints-sweep` (8) · `chore/workspace-lints-canonical` (6) · `lints/canonical-workspace-lints` (1).

Code changes, each independently gated. Conflicts with Phase 3 and Phase 6 on `Cargo.toml` in shared repos — see the per-repo table below.

---

## Phase 6 — test infrastructure (7 PRs) — BLOCKED on 0.4

- `testgate/loud-skips` (3): `qcow2` #4 **R**, `vhd` #2 **R**, `vhdx` #4 **R** — **all three red on every job.** The `path` dev-dependency is a machine-local absolute path (`/Users/4n6h4x0r/.claude/jobs/…`), so `cargo metadata` fails before any gate runs. Cannot merge until `forensic-testgate` publishes *and* the path is replaced with `forensic-testgate = "0.1"`
- `fix/oracle-path-resolution` (4): `vhd` #4 **G**, `vhdx` #5 **G**, `qcow2` #6 **G**, `ewf` #8 **R** — three are mergeable now; **`ewf` #8 is not.** It fails `Test (ubuntu-latest)` with two real panics at `forensic/tests/differential_tests.rs:110:5`, which `main` does not have

---

## Phase 7 — CI consolidation (3 pilots + rollout) — BLOCKED on 0.3

`ci/adopt-reusable-workflow`: `luks` #2 **N**, `ewf` #4 **N**, `ntfs` #5 **N**. **They pin a repo that does not exist yet** — `SecurityRonin/fleet-config` returns 404 — and the pinned SHA is now stale after the `cargo fetch --locked` fix. Repin after 0.3.

All three are **N**, and this is the trap worth naming: the runs *are* dispatched and *do* fail, but with **zero jobs**, so GitHub creates no check-runs and the PR shows an empty (not failing) check list. `luks` #2 is the sharpest case — it displays four passing `Fuzz` checks from an unrelated workflow, which makes it read as green in any rollup that does not group by workflow.

Merge one pilot and watch a real run before the remaining 88.

---

## Phase 8 — quality-of-life (decide whether to keep)

- `chore/output-format-vocab` (2): `memory-forensic` #4, `winevt` #5
- Legal-doc templates (local, not yet PRs) — gated on 0.2

These are the candidates to close if the queue is too long. They are correctness-neutral.

---

## Per-repo sequences — the 13 repos with 3+ PRs

Merge **top to bottom**. Everything below the first merge in each repo needs a rebase.

Status codes: **G** green · **R** red · **N** no CI dispatched.

| Repo | Order (with live status) | Note |
|---|---|---|
| **ewf-forensic** (5) | #6&nbsp;G &rarr; #7&nbsp;R &rarr; #8&nbsp;R &rarr; #5&nbsp;R &rarr; #4&nbsp;N | #6 first: `4n6mount` waits on its publish. #5/#4 last (supply-chain, CI). #7 needs a `safe-read` trust line; #8 has 2 real test failures; #5 is a docker.io flake; #4 is a CI pilot |
| **vhd-forensic** (5) | #5&nbsp;G &rarr; #3&nbsp;G &rarr; #4&nbsp;G &rarr; #1&nbsp;G &rarr; #2&nbsp;R | #5 first (index-only). #2 blocked on `forensic-testgate` — and its local `path` dep reds all 10 jobs |
| **winevt-forensic** (5) | #7&nbsp;G &rarr; #6&nbsp;G &rarr; #4&nbsp;G &rarr; #5&nbsp;G &rarr; #3&nbsp;G | #3 is pre-existing release-plz; rebase it last. **Whole repo is green** |
| **blazehash** (4) | **#5&nbsp;R &rarr; #6&nbsp;R &rarr; #7&nbsp;N &rarr; #8&nbsp;N** | **Hard sequence.** #7/#8 target #5's branch — retarget to `main` after #5. #5/#6 red only on RUSTSEC-2026-0222, which `main` shares — **not blocking** |
| **forensicnomicon** (4) | #26&nbsp;G &rarr; #24&nbsp;G &rarr; #25&nbsp;G &rarr; #23&nbsp;G | #26 first (index-only, largest diff). #23 is release-plz. **Whole repo is green** |
| **memory-forensic** (4) | #7&nbsp;G &rarr; #6&nbsp;G &rarr; #5&nbsp;G &rarr; #4&nbsp;G | #7 is the panic fix. **Whole repo is green** |
| **srum-forensic** (4) | #5&nbsp;R &rarr; #2&nbsp;G &rarr; #4&nbsp;G &rarr; #3&nbsp;G | #2 is **semver-breaking**; release-plz computes the bump. #5 needs a `jsonguard:0.2.4` trust line |
| **vhdx-forensic** (5) | #2&nbsp;G &rarr; #5&nbsp;G &rarr; #3&nbsp;G &rarr; #4&nbsp;R | #4 blocked on `forensic-testgate`. **#6 (`N`) is a fork PR awaiting approval — not in this sequence** |
| **4n6mount** (3) | #11&nbsp;G &rarr; #12&nbsp;G &rarr; #10&nbsp;G | #11 **after** `ewf-forensic` #6 publishes. **Whole repo is green** |
| **disk-forensic** (3) | #6&nbsp;R &rarr; #7&nbsp;G &rarr; #5&nbsp;R | #6 carries the 16 GiB allocation fix — but has a real `Clippy` + `Coverage` regression on top of two missing trust lines |
| **forensic-vfs-engine** (3) | #9&nbsp;R &rarr; #8&nbsp;G &rarr; #7&nbsp;R | #9/#7 fail `cargo vet` on `zfs-forensic-core:0.1.1` — **`main` fails identically**, so not introduced here |
| **leveldb-forensic** (3) | #5&nbsp;R &rarr; #4&nbsp;G &rarr; #3&nbsp;G | #5 is the CSV injection fix; needs a `jsonguard:0.2.4` trust line |
| **qcow2-forensic** (3) | #6&nbsp;G &rarr; #5&nbsp;G &rarr; #4&nbsp;R | #4 blocked on `forensic-testgate` — its local `path` dep reds all 8 jobs |

---

## Status corrections — 2026-08-02, later

Three items previously listed as blocked are resolved.

**`safe-decode 0.1.0` and `forensic-testgate 0.1.0` are PUBLISHED on crates.io.** An earlier draft said they awaited release-PR approval. That was wrong: **release-plz publishes a crate's *first* version directly**, because there is no prior version to bump from and therefore nothing to open a bump PR about. Only `jsonguard` needs its release PR merged, and only because 0.2.4 already existed. Verified on the registry, not inferred from the workflow.

**The three `testgate/loud-skips` PRs are now green.** `qcow2 #4` (13/13), `vhd #2` (17/17), `vhdx #4` (10/10). They committed a machine-local absolute path to `forensic-testgate`; with the crate published, they now take `forensic-testgate = "0.1"` from the registry. The `TODO(before merge)` was removed rather than reworded — a marker citing a blocker that no longer exists is itself the stale-marker defect. `cargo vet` cleared via `trust` with criteria **`safe-to-run`** (dev-dependency), per ADR-0018 mechanism 2.

**`jsonguard #5` is merged** — `main` at `41b6438d`, carrying `is_lead_in_skippable = c.is_whitespace() || is_format_char(c)`, so the whole `Cf` category is covered. Release PR **#6 (`chore: release v0.2.5`)** is open, `MERGEABLE`/`CLEAN`, 8 checks passing, bump and CHANGELOG verified correct. Merging it publishes 0.2.5 and unblocks the six lock refreshes in the chain above.

## Cannot merge yet — summary

| Count | What | Status | Unblocked by |
|---|---|---|---|
| 3 | `testgate/loud-skips` — `path` dev-dep | **R** (all jobs) | Publishing `forensic-testgate` (0.4) |
| 3 | CI pilots — pin a non-existent repo | **N** | Creating it public (0.3) |
| 2 | `blazehash` #7, #8 — target a feature branch | **N** | Merging #5, then retargeting |
| 2 | `ronin-issen` #8, #9 — repo has no CI at all | **N** | Nothing; they cannot be gated |
| 1 | `vhdx-forensic` #6 — fork PR from `ebrig` | **N** (`action_required`) | A maintainer clicking *Approve and run* |

An empty check list on any of these means **not run**, not **passed**.

The three `testgate` PRs are worse than "waiting on a publish": all three commit `forensic-testgate = { path = "/Users/4n6h4x0r/.claude/jobs/6125d941/tmp/forensic-testgate" }` — an absolute path into a scratch directory on one machine. That reference can never resolve in CI, which is why all 8/10/6 jobs go red rather than just the build. Each carries a `# TODO(before merge)` comment saying it must become `forensic-testgate = "0.1"`.

---

## Conflict surface by branch family

| Family | Count | Touches | Collides with |
|---|---|---|---|
| `fix/vet-trust-our-crates` | 73 | `supply-chain/` | The two security PRs that add exemption lines |
| `lints/*`, `chore/workspace-lints-canonical` | 27 | `Cargo.toml`, `src/` | CSV guard (adds `jsonguard`), testgate (adds dev-dep) |
| `fix/csv-formula-guard` | 6 | `src/`, `Cargo.toml` | lints |
| `fix/oracle-path-resolution` | 4 | `tests/`, `ci.yml` | CI adoption |
| `testgate/loud-skips` | 3 | `tests/`, `Cargo.toml` | lints |
| `ci/adopt-reusable-workflow` | 3 | `ci.yml` | oracle-path |
| `fix/untrack-build-artifacts` | 2 | `.gitignore`, index | Nothing — merge early |
| `release-plz-*` | 10 | versions, `CHANGELOG` | Pre-existing; rebase last in each repo |
