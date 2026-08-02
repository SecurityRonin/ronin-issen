# Fleet merge order — 150 open PRs

**Generated:** 2026-08-02. **Scope:** every open PR across the 91 component repos plus `ronin-issen`.

150 open PRs. **140 from the DRY-audit campaign; 10 are pre-existing `release-plz` release PRs** that predate it and are independent of everything below.

Nothing here is merged. This document is a sequence, not an instruction — the ordering constraints are real, the phase boundaries are a recommendation.

---

## The one thing to read first

**Merging this volume before fixing the gates is the wrong order.** The audit established that several gates report success over work they never did — most sharply, `cargo vet --locked` asserts nothing in **80 of 81 repos**, because `cargo fetch` rewrites `Cargo.lock` in the runner before `--locked` is evaluated. Landing 140 PRs through gates known to be broken buys volume and no assurance.

Phase 1 exists for that reason. It is small.

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

- `forensicnomicon` **#26** — untrack 781 files under `bindings/python/target/`
- `vhd-forensic` **#5** — untrack 391 files under `fuzz/target/`

Both are index-only: files stay on disk, no source change. A `cargo sweep` already deleted 1,143 tracked files once because of this.

---

## Phase 3 — the actual defects (~15 PRs)

These fix real bugs. Small, independent, and the highest value per merge.

| Repo | PR | Defect |
|---|---|---|
| `state-history-forensic` | #2 | Release-mode wrapping subtraction — `nearest()` returns the **wrong** cohort member |
| `shrinkpath` | #3 | `dir_length(0)` overflows from the documented public API |
| `disk-forensic` | #6 | Unbounded 16 GiB allocation from an untrusted VHD length field |
| `ewf-forensic` | #7 | `EwfReader::open` panics on a trailing-dot path |
| `memory-forensic` | #7 | Byte-slice panic on a REG_SZ value from a memory image |
| `jsonguard` | #5 | CSV formula guard fires only on character 0 |
| `leveldb` #5 · `sqlite` #8 · `browser` #8 · `srum` #5 · `winevt` #7 · `blazehash` #6 | | CSV formula injection — attacker-controlled evidence written unguarded |
| `issen` #12 · `prefetch` #4 · `srum` #2 | | Timestamp edge-semantics; `srum` is **semver-breaking** (0.2→0.3) |
| `forensicnomicon` #24 | | 7 wrapping `offset + N > len` guards |
| `vmdk` #3 · `livedisk` #2 | | Panic-capable readers |

**Order within Phase 3:** `jsonguard` **#5 first** — the six CSV consumers resolve to published `jsonguard`, and its guard is incomplete until #5 ships as 0.2.5.

**Ordering constraint:** `ewf-forensic` #6 (`lru`) must merge **and publish** before `4n6mount` can drop its transitive `lru` ignore. `4n6mount` #11 carries that ignore with the removal condition stated inline.

---

## Phase 4 — supply-chain bulk (73 PRs)

`fix/vet-trust-our-crates` — 73 repos, config-only, no code. Clears the single largest finding: 79 repos clearing our own crates by `exemption` where ADR-0018 requires `trust`.

**Merge after Phase 3**, not before. `ewf-forensic` #6 and `4n6mount` #11 both add `supply-chain/config.toml` lines; landing 73 supply-chain PRs first forces two rebases, landing them after forces 73. Fewer rebases the other way round.

---

## Phase 5 — lint sweep (27 PRs)

`lints/canonical-lints` (12) · `lints/workspace-lints-sweep` (8) · `chore/workspace-lints-canonical` (6) · `lints/canonical-workspace-lints` (1).

Code changes, each independently gated. Conflicts with Phase 3 and Phase 6 on `Cargo.toml` in shared repos — see the per-repo table below.

---

## Phase 6 — test infrastructure (7 PRs) — BLOCKED on 0.4

- `testgate/loud-skips` (3): `qcow2` #4, `vhd` #2, `vhdx` #4 — **use a `path` dev-dependency and cannot merge until `forensic-testgate` publishes**
- `fix/oracle-path-resolution` (4): `vhd` #4, `vhdx` #5, `qcow2` #6, `ewf` #8 — mergeable now; touches `tests/` and `ci.yml`

---

## Phase 7 — CI consolidation (3 pilots + rollout) — BLOCKED on 0.3

`ci/adopt-reusable-workflow`: `luks` #2, `ewf` #4, `ntfs` #5. **They pin a repo that does not exist yet**, and the pinned SHA is now stale after the `cargo fetch --locked` fix. Repin after 0.3.

Merge one pilot and watch a real run before the remaining 88.

---

## Phase 8 — quality-of-life (decide whether to keep)

- `chore/output-format-vocab` (2): `memory-forensic` #4, `winevt` #5
- Legal-doc templates (local, not yet PRs) — gated on 0.2

These are the candidates to close if the queue is too long. They are correctness-neutral.

---

## Per-repo sequences — the 13 repos with 3+ PRs

Merge **top to bottom**. Everything below the first merge in each repo needs a rebase.

| Repo | Order | Note |
|---|---|---|
| **ewf-forensic** (5) | #6 → #7 → #8 → #5 → #4 | #6 first: `4n6mount` waits on its publish. #5/#4 last (supply-chain, CI) |
| **vhd-forensic** (5) | #5 → #3 → #4 → #1 → #2 | #5 first (index-only). #2 blocked on `forensic-testgate` |
| **winevt-forensic** (5) | #7 → #6 → #4 → #5 → #3 | #3 is pre-existing release-plz; rebase it last |
| **blazehash** (4) | **#5 → #6 → #7 → #8** | **Hard sequence.** #7/#8 target #5's branch — retarget to `main` after #5. #6 needs its lock regenerated |
| **forensicnomicon** (4) | #26 → #24 → #25 → #23 | #26 first (index-only, largest diff). #23 is release-plz |
| **memory-forensic** (4) | #7 → #6 → #5 → #4 | #7 is the panic fix |
| **srum-forensic** (4) | #5 → #2 → #4 → #3 | #2 is **semver-breaking**; release-plz computes the bump |
| **vhdx-forensic** (4) | #2 → #5 → #3 → #4 | #4 blocked on `forensic-testgate` |
| **4n6mount** (3) | #11 → #12 → #10 | #11 **after** `ewf-forensic` #6 publishes |
| **disk-forensic** (3) | #6 → #7 → #5 | #6 carries the 16 GiB allocation fix |
| **forensic-vfs-engine** (3) | #9 → #8 → #7 | |
| **leveldb-forensic** (3) | #5 → #4 → #3 | #5 is the CSV injection fix |
| **qcow2-forensic** (3) | #6 → #5 → #4 | #4 blocked on `forensic-testgate` |

---

## Cannot merge yet — summary

| Count | What | Unblocked by |
|---|---|---|
| 3 | `testgate/loud-skips` — `path` dev-dep | Publishing `forensic-testgate` (0.4) |
| 3 | CI pilots — pin a non-existent repo | Creating it public (0.3) |
| 2 | `blazehash` #7, #8 — target a feature branch, **no CI has run** | Merging #5, then retargeting |

An empty check list on those three means **not run**, not **passed**.

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
