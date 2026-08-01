# Fleet DRY Audit — Cross-Repo Duplication and Divergence

**Scope:** all 91 git repos under `~/src/ronin-issen/components/`.
**Date:** 2026-08-01.
**Method:** six independent read-only sweeps (byte primitives, temporal logic, repo scaffolding, report model, IO/container layer, tests/docs/tooling). No code was executed against evidence; no changes were made.

---

## Executive Summary

The fleet's duplication problem is not primarily a maintenance-cost problem. It is a **correctness** problem wearing a DRY costume.

Copy-pasted code across independently-published repos is expected and often load-bearing — a crate on crates.io cannot `use` a sibling's private module. What this audit found is that the copies have **silently diverged**, and in several places the divergence changes what the tools *report about evidence*.

Three findings outrank everything else and are not really DRY findings at all:

1. **A fabricated guarantee.** `parser/shellitem/README.md:60` states the crate is “fuzzed over `parse_idlist`.” No fuzz target exists, and `git log --all -- fuzz` confirms one never has. `shellitem` parses untrusted `ITEMIDLIST` structures. This is a published claim that the repository's own history contradicts.

2. **Two timestamp converters with wrong edge behavior — both latent, neither reachable today.** `orchestration/issen/crates/issen-correlation/src/temporal_checks.rs:36` saturates *negative* overflow to `i64::MAX`, so a zero FILETIME would sort at the far end of a super-timeline instead of reading as absent; it has no non-test callers. `parser/prefetch-forensic/forensic/src/bin/prefetch4n6.rs:68` has no zero guard and returns `Some("1601-01-01T00:00:00Z")` for an unset value; `prefetch-core` filters non-positive FILETIMEs upstream (`core/src/lib.rs:159`), so the binary's `-` fallback already fires correctly. Both are wrong functions guarded by circumstance, not by their own contract.

3. **A panic-capable reader in a Paranoid-Gatekeeper crate.** `container/vmdk-forensic/core/src/bytes.rs:6` panics on any input shorter than four bytes, in a crate whose stated contract is that malformed images never panic. It has **no live caller today** (see 1.4), so this is a latent hazard rather than an active bug — but it sits in published API of a crate that forbids exactly this.

Beneath those, the headline DRY finding is broader than a count of duplicated files. **205 hand-rolled fixed-width integer readers exist across 47 repos**, and **42 of those repos carry no `safe-read` dependency at all** — against ADR-0012, which states every integer read goes through `safe-read` and never a hand-rolled `bytes.rs`. The shared crate is published (0.2.1) and healthy; adoption simply never happened. Only 12 repos declare it, two of those declare it without a single call site, and one (`ntfs-forensic`) is split-brain, using `safe_read::` in four modules while eight others still use its own identical local copy.

The divergence is measurable and it is the reason this matters:

| Primitive | Independent implementations | Distinct semantics | Consequence of the divergence |
|---|---|---|---|
| FILETIME conversion | 22 across 14 repos | **7** different results for input `0` | “No timestamp” is representation-dependent across a single timeline |
| UTF-16LE decode | ≥14 | **4** NUL policies | Same bytes decode to different strings by repo |
| LEB128 varint | 6 hand-rolled | reject vs silently truncate | Malformed input errors in one parser, yields a plausible wrong number in another |
| Byte-reader overflow | 205 fns | **4** dialects + 2 panic paths | Debug-build panics; one release-build OOB read |
| Mixed-endian GUID | 7 hand-rolled | case and brace divergence | Preventive — no GUID join exists today; any future one must normalize first |

Encouragingly, the fleet has already proved it can converge when a mechanism exists: `rust-toolchain.toml` is **uniform at `1.96.0` across all 90 repos that have it**, and `release-plz.yml` has 87 copies but only **2** normalized variants. Where a shared mechanism is absent, drift is total: `ci.yml` has 91 copies in **89** distinct normalized variants.

**Recommended sequence:** fix the three integrity/correctness defects immediately (they are small, local edits); then land the two structural enablers — a reusable org CI workflow and the `forensicnomicon::temporal` sentinel API — because most remaining items are mechanical sweeps that ride on those two.

---

## Epistemic status

Every claim below is **Tier 2**: derived by reading source and running measurement commands over the working tree. Nothing was validated by executing the fleet's binaries against evidence images. Counts are measured, not estimated; where a measurement was wrong, the correction is noted rather than quietly replaced. Claims about semantic *consequence* (for example, “this would misplace an event in a timeline”) are inferences from reading the code path, not observed failures — they are stated as consistent-with, and the two marked **DEFECT** below warrant a reproducing test before any fix is called complete.

**Adversarial verification pass.** A second reviewer independently re-derived the load-bearing claims — reading the cited function bodies, running `cargo deny check --help`, and re-counting from the working tree. It **confirmed exactly**: 91 repos; 17 `bytes.rs` files summing 1,385 lines; 12 real `safe-read` dependencies; `channel = "1.96.0"` in all 90 `rust-toolchain.toml` files with no exceptions; the `46 + 17 → 54` `impl Observation` arithmetic; 6 of 7 rows of the FILETIME zero-semantics table at the cited line numbers; both defects in 1.2; the whole shellitem finding; and both Part 4 tool-capability corrections. It **rejected three claims**, all now corrected in place: the GUID-join consequence (2.4), the vmdk panic mechanism and its implied live risk (1.4), and the snapshot-forensic tense claim (1.1). One figure could not be reproduced at stated precision and is flagged where it appears (2.1).

---

## Part 1 — Correctness and integrity findings

These are not DRY findings. They surfaced during the sweep and outrank it.

### 1.1 Unearned fuzzing claim — `shellitem`

`parser/shellitem/README.md:60` claims the crate is “fuzzed over `parse_idlist`.”

- No `fuzz/` or `fuzz_targets/` directory exists in the repo.
- No fuzz target anywhere in the fleet calls `parse_idlist`.
- `git log --all -- fuzz` in `shellitem` returns nothing — it never existed.
- The only occurrence of “fuzz” in its CI is a path exclusion in the coverage gate (`parser/shellitem/.github/workflows/ci.yml:88`).

ADR-0012 requires a fuzz target for untrusted-input parsers regardless, so the remedy is to add the target and make the sentence true — not to delete the sentence.

**Resolved.** Two targets now exist and have been run: `idlist` (`parse_idlist` alone — framing loop, class dispatch, per-class decoders, the `0xbeef0004` extension block) at **8,229,495 executions**, and `pipeline` (`parse_idlist` → `reconstruct_path` → `display_name`) at **9,131,724 executions**. **No crashes.** Two targets cover the whole surface because the crate exports exactly two public functions.

The README was rewritten rather than left alone, even though the original sentence had become literally true. Two reasons, both worth recording:

- **Measured wording beats a bare adjective** — it now uses the fleet's paired-bullet form: a *Fuzzed* bullet naming both targets with exec counts, beside a *Panic-free by lint* bullet carrying the static posture. The result is stated as “no crashes in N executions” with the budget spelled out — present-robustness evidence over the inputs libFuzzer reached, never “fuzzed, therefore panic-free.”
- **The same sentence carried a second factual error.** It cited `#![forbid(unsafe_code)]` as an inner attribute; the lint is actually declared in `Cargo.toml` under `[lints.rust]`. Identical guarantee, but anyone grepping for the attribute would have found nothing and concluded the claim was false.

**Not a comparable instance — recorded so it is not re-raised.** `snapshot-forensic/README.md:36` reads “both crates are `#![forbid(unsafe_code)]`, **will be** panic-free against attacker-controllable input, fuzzed with `cargo-fuzz`, and validated against real artifacts plus an independent oracle.” The “will be” is a shared auxiliary governing all three coordinated predicates — standard English ellipsis, not mixed tense. Every format-support row in that README is marked “planned,” and no fuzz target exists, which is consistent. This is an aspirational README for an unimplemented crate, **not a false claim**, and it should not be filed alongside the shellitem finding.

### 1.2 Seventeen repos publish a Terms of Service naming the wrong licence

**`docs/terms.md` states MIT in 17 repos whose `LICENSE` file and `Cargo.toml` both say Apache-2.0.** Spot-verified on five independently:

| Repo | `docs/terms.md` | `LICENSE` | `Cargo.toml` |
|---|---|---|---|
| `ewf-forensic` | **MIT** | Apache License | `Apache-2.0` |
| `ext4fs-forensic` | **MIT** | Apache License | `Apache-2.0` |
| `srum-forensic` | **MIT** | Apache License | `Apache-2.0` |
| `blazehash` | **MIT** | Apache License | `Apache-2.0` |
| `lzo` | **MIT** | Apache License | `Apache-2.0` |

Also affected: all three partition repos, among 17 total. `lzo` and `lzvn` go further and say the work is *“governed solely by that licence,”* pointing at a licence they do not ship.

**This is almost certainly stale residue, not a licensing dispute.** The constitution records that the fleet *“standardized on **Apache-2.0** for its explicit patent grant — migrate any residual MIT repos.”* The `LICENSE` files and manifests were migrated; these `terms.md` files were not. Two independent sources agree against the third.

It is recorded in Part 1 rather than among the DRY findings because it is not duplication — it is a **published legal document making a false statement about the terms a user receives the software under**, on 17 public repositories. Every DRY finding in this report is a maintenance cost; this one is an assertion to third parties that does not match the shipped licence.

Structural remedy, beyond correcting the text: the legal-doc generator derives the licence from `Cargo.toml`/`LICENSE` and **the template cannot override it**, so a rendered document is incapable of disagreeing with the shipped licence. That is the secure-by-design form of the fix — the wrong state becomes unrepresentable rather than merely corrected once.

### 1.3 Two live unsoundness advisories are invisible to the gate meant to catch them

Consolidating the 91 `deny.toml` files surfaced a cargo-deny behaviour that silently disarms part of the advisory gate.

**Observed, by four-way bisect on one repo against one advisory DB:** in cargo-deny 0.19.0, advisories carrying `informational = "unsound"` are *evaluated* when `unmaintained` is set to `"workspace"` or `"transitive"`, and **silently skipped** under the unset default and under the explicit `"all"` and `"none"` values. (`none` → ok, `workspace` → FAILED, `transitive` → FAILED, `all` → ok.) This is reported as observed behaviour; the cause was not traced to cargo-deny's source.

Consequence, verified against the working tree:

| Repo | Crate present | Advisory | Gate state |
|---|---|---|---|
| `container/ewf-forensic` | `lru 0.12.5` | `RUSTSEC-2026-0002` — `IterMut` violates Stacked Borrows | Listed in its own `ignore`, with a comment asserting it was “genuinely fixed”. `unmaintained` unset |
| `filesystem/4n6mount` | `fuser 0.15.1` | `RUSTSEC-2021-0154` — uninitialised memory read + leak | Listed in its own `ignore`. `unmaintained` unset |

Both repos pass their current gate. Both believe the advisory is dead. **Both still carry the affected crate version.** Two memory-safety unsoundness advisories, in a fleet whose crates parse attacker-controlled evidence images, are currently not surfaced by the mechanism that exists to surface them.

Fixes are ordinary caret widenings — `lru = "0.16"` (≥0.16.3 patched) and `fuser = "0.16"` — and both advisories begin firing under the unified config, which is how they were found.

### 1.4 Timestamp defects

**DEFECT — wrong-direction saturation.** `orchestration/issen/crates/issen-correlation/src/temporal_checks.rs:36`

The fallback is `i64::try_from(unix_100ns * 100).unwrap_or(i64::MAX)`. FILETIME `0` — and any value before roughly 1677, the lower bound of i64-nanosecond range — overflows *negatively* and returns `i64::MAX`, a year-2262 instant. In a sorted super-timeline that would place an absent timestamp at the very end.

**Confirmed by test, not by reading.** `assert_eq!(filetime_to_unix_ns(0), i64::MIN)` fails with `left: 9223372036854775807`. This is the one finding in Part 1 that has been demonstrated rather than inferred.

**Control-flow correction.** The function is not a bare `try_from(...).unwrap_or(i64::MAX)`. A `timeglyph::format("filetime")` decode path sits in front, and the buggy expression lives in a fallback closure reached only when timeglyph cannot represent the value — so the path to the defect runs *through* timeglyph rather than directly. The outcome is unchanged, but anyone reasoning from the quoted line alone will miss a hop.

**Blast radius is this one site.** The other two converters in the same workspace are correct: `issen-parser-evtx/src/lib.rs:448` clamps both directions via `.clamp(i128::from(i64::MIN), i128::from(i64::MAX))`, and `issen-parser-usnjrnl/src/lib.rs:166` is correct by construction using `saturating_sub`/`saturating_mul`.

**Corroboration that this is a bug and not a taste question:** `browser-forensic-core/src/timestamp.rs:53` hits the identical negative-overflow scenario and saturates to `i64::MIN` — the correct direction. Two fleet crates, same arithmetic, opposite saturation.

Mitigating: no non-test callers of this `pub fn` exist today, so the impact is latent — but it is published API of the crate.

**LATENT — unset value has a rendering it should not.** `parser/prefetch-forensic/forensic/src/bin/prefetch4n6.rs:68`

`filetime_to_iso` has no zero guard and returns `Some("1601-01-01T00:00:00Z")` for input `0` — confirmed by a failing test written against it. Sibling tools in the same fleet render `-` for exactly this input.

**Correction to an earlier draft of this report.** That draft asserted the call site “therefore prints `1601-01-01T00:00:00Z` for an unset first run-slot.” **It does not.** `prefetch-core` filters non-positive FILETIMEs upstream at `core/src/lib.rs:159` (`Some(t) if t > 0 => last_run_times.push(t), _ => break`), so `last_run_filetimes` never carries a zero for a record parsed by this workspace, `.first()` returns `None`, and the `-` fallback already engages. This was verified empirically, not by reading: a synthetic SCCA v30 with all eight last-run FILETIMEs zeroed, run through `prefetch_core::parse_decompressed`, yields an empty vector.

The finding survives as hardening rather than a live bug: `ExecutionRecord`'s fields are public, so a consumer can construct one holding a zero, and the conversion should be correct on its own terms rather than resting on an upstream invariant its call site never states.

**Fail-loud violation.** `parser/srum-forensic/crates/srum-core/src/lib.rs:55`

`filetime_to_datetime` is total and uses `saturating_sub` plus `unwrap_or(UNIX_EPOCH)`, so any pre-epoch or garbage FILETIME becomes exactly `1970-01-01T00:00:00Z` — a valid-looking `Timestamp` with no absence signal. The same pattern appears in `ole_date_to_datetime` (`srum-core/src/lib.rs:65`) for non-finite input. A timestomped SRUM row silently becomes a 1970 timeline entry.

**srum-core is the outlier, not the pioneer.** `winreg_core::key::filetime_to_datetime` already returns `Option<jiff::Timestamp>` with exactly the zero/pre-epoch guard this section recommends. The correct signature was next door the whole time — which is itself the argument against adding a second, parallel converter to preserve the wrong one.

**The fix only reaches half the problem, and the other half is one layer up.** `crates/srum-parser/src/lib.rs:51` — `collect_table` calls `decode(&data, page, tag).ok()`, discarding **every** decode error, including the pre-existing truncation errors. Making the converters fallible removes the *fabrication* (no false 1970 entry reaches the timeline) but the record is then silently **dropped** rather than loudly reported. Eliminating fabricated evidence is a strict improvement over a false timestamp; it is not fail-loud. Restoring the loud half changes `parse_*` public semantics (hard error versus a warnings channel) and needs its own scoped decision.

Consumer check, which shaped the remedy: `filetime_to_datetime` has **zero call sites fleet-wide** — dead public API — and `ole_date_to_datetime` has 6, all inside `srum-parser` in the same workspace. So the breaking change is contained to one repo.

### 1.5 Panic-capable and OOB readers

| Site | Problem | Live caller today? |
|---|---|---|
| `container/vmdk-forensic/core/src/bytes.rs:6` | `u32::from_le_bytes(b[..4].try_into().expect("4 bytes"))`. The panic fires at the **`b[..4]` slice index** (“range end index 4 out of range for slice of length N”) for any `b.len() < 4`. The `.try_into().expect("4 bytes")` that follows is **unreachable dead code** — once the slice succeeds it is exactly 4 bytes, so the conversion cannot fail | **No.** `le_u32` is called only from `le_u32_table` via `b.chunks_exact(4).map(le_u32)`, and `chunks_exact(4)` yields only exact-length chunks. Latent, but published API |
| `knowledge/forensicnomicon/crates/core/src/catalog/decode.rs` — **7 instances**, not 1: `read_u16_le`, `read_u32_le`, `read_u64_le`, `read_i32_le`, `read_i64_le`, `decode_binary_field`, `Decoder::FiletimeAt` | Guard `if offset + N > data.len()` wraps for `offset` near `usize::MAX`. **Both modes demonstrated by test:** release — guard wraps, passes, then `index out of bounds: the len is 8 but the index is 18446744073709551614`; debug — the addition itself panics first with `attempt to add with overflow` | **Not attacker-reachable.** Every catalog offset is a compile-time literal in range 0..60; `Decoder`/`BinaryField`/`ArtifactDescriptor` derive `Serialize` only, never `Deserialize`, so no evidence file can become a descriptor at runtime. **But** `ForensicCatalog::decode` is public and `#[non_exhaustive]` restricts matching, not construction — so a downstream crate can write `Decoder::FiletimeAt { offset: usize::MAX }` and panic a published FOUNDATION API through entirely safe code |
| `acquisition/livedisk-forensic/core/src/drive_layout.rs:99` (note: `core/`, a two-member workspace) | GUID formatter indexes `b[8]`–`b[15]` directly on a `&[u8]` without a length check. The real flaw is *internal inconsistency* — `safe-read` for the leading three fields, raw indexing for the trailing eight | **No.** `format_guid` is private with one production call site, `format_guid(&entry[32..48])`, where `entry` is formed only after an `e + ENTRY_SIZE > buf.len()` guard with `ENTRY_SIZE = 144`. The `fuzzing`-feature entry point was traced too: the same 144-byte guard sits between it and the formatter, so even the fuzzer cannot reach it |

All three crates sit under the Paranoid-Gatekeeper standard, which forbids exactly this — reachability affects urgency, not whether the code should exist.

**All three are unreachable — and one of them explains why the class exists.** `vmdk-forensic` denies `unwrap_used` in `[workspace.lints.clippy]` but **not `expect_used`**. ADR-0012's lint recipe requires both, and that single missing line is the mechanical reason an `.expect("4 bytes")` survived review in a crate whose stated contract is that it never panics. This reframes 2.6's `workspace.lints` divergence from a tidiness issue into a **defect-admitting** one: the lint gaps are not cosmetic, they are what let this class of bug through. Adding the line is one edit but would light up other call sites, so it is its own piece of work.

**Characterize the forensicnomicon one precisely.** It is an **API-contract defect in a published crate**, not an evidence-driven one: “safe-Rust panic on public API misuse,” not “malicious image crashes the parser.” The distinction matters because ADR-0012's threat model is attacker-controlled *images*, and this guard is not on that path. It is still worth fixing — a guard wrong on its own terms, in the FOUNDATION crate every analyzer depends on — but the severity should not be inflated to match the other two.

### 1.6 Silent test gates

**79 of 206 env-gated test sites (38%) skip silently** — an `Option`-returning helper plus a bare early return, with no notice printed. A gate that never fires is indistinguishable from a gate that passed. Concentrations: `SQLITE3_BIN` is 2 loud / 11 silent; `SZECHUAN_DC_MEM` is 0 loud / 7 silent; `AZURE_STORAGE_ACCOUNT` is 0 / 6.

Representative silent form: `container/qcow2-forensic/core/tests/corpus.rs:6` (`fn corpus_dir() -> Option<PathBuf>`, cloned in `vhd`, `vhdx`, `vmdk`).
Representative loud form: `filesystem/apfs-forensic/core/tests/keyed_nav.rs:120-123`.

### 1.7 Mandate gaps

| Mandate | Compliant | Gap |
|---|---|---|
| Fuzz target (ADR-0012) | 78/91 | **13 repos have none**: blazehash, dpapi-forensic, exec-pe-forensic, forensic-vfs-mount, jsonguard, name-variants, prefetch-forensic, shellitem, shrinkpath, snapshot-forensic, srum-forensic, state-history-forensic, useract-forensic |
| Coverage job in CI | 75/91 | 16 repos have none, including forensicnomicon, memory-forensic, winevt-forensic, issen |
| Secret scan in `ci.yml` | 43/91 | **48 repos** — the largest single policy hole |
| Fully SHA-pinned actions | **10/91** | 81 repos carry at least one floating tag, most often `dtolnay/rust-toolchain@stable` |
| SHA pins whose version comment is **true** | see below | **56 repos (87 files) pin a rust-cache commit that matches no release tag**, ~290 labelled `# v2.7.8` |
| `docs/validation.md` | 70/91 | 21 missing (a stated pre-push gate) |
| `docs/PRD.md` | 81/91 | 10 missing (a stated pre-push gate) |

**A SHA pin can be sound and still lie about what it pins.** **56 repos**, across **87 workflow files**, pin `Swatinem/rust-cache` at `9bdad043e88c75890e36ad3bbc8d27f0090dd609`. Of ~316 occurrences, **~290 carry the comment `# v2.7.8`** — the false ones — while ~26 carry `# v2`, which is arguably *true* since it is a v2-series commit. Only the `# v2.7.8` labels assert something untrue. Two repos (`orchestration/issen`, `parser/browser-forensic`) pin **both** this SHA and the real one in different workflows, so they are internally inconsistent about which rust-cache they run. Verified against the GitHub API: that commit is genuine (2024-05-03, *“fix: usage of `deprecated` version of `node` (#197)”*) but matches **no release tag** — v2.7.3 → `23bce251a8cd`, v2.7.5 → `82a92a6e8fbe`, v2.7.7 → `f0deed1e0edf`, **v2.7.8 → `9d47c6ad4b02`**, v2.8.0 → `98c8021b5502`.

State the severity precisely: **the pin is sound; the provenance label is fiction.** A SHA is immutable, so the supply-chain control is working as designed — this is not a vulnerability. The defect is *traceability*: 86 repos run untagged mid-tree code while asserting a release version, so any audit that answers “are we on released versions?” by reading pin comments gets a wrong answer, and Renovate's digest-pinning cannot cleanly map that SHA back to a version.

This sharpens the row above rather than adding to it. “10 of 91 fully SHA-pinned” understated the problem: of the pinning that *does* exist, the most widely-copied pin in the fleet carries a false version label — and it is copied across 87 files in 56 repos, which is itself the scaffolding-duplication finding expressing itself in the supply chain.

**Two further violations surfaced while implementing fixes, not by the sweeps** — both are the kind a file-shaped audit structurally cannot see:

- **`crates/srum-gui` is a Tauri app.** ADR-0014 bans Tauri, `dioxus-desktop`, and any `wry`/webview bundle outright, because crates.io cannot deliver them; the fleet GUI standard is `egui`/`eframe`. A documented exception requires `publish = false` and a stated reason.
- **`useract-forensic` pins `srum-core = "0.1"`** while 0.2.0 is published — the layer-1 stale-caret pattern (requirement too narrow for `cargo update` to cross). It cannot reach 0.2, let alone the 0.3 the fail-loud fix requires. This is the same failure class as `blazehash`'s `ewf = "0.2"` against the fleet's 0.4 (2.8), suggesting a fleet-wide caret-width audit is worth its own pass.
- **`issen`'s committed `Cargo.lock` records `forensicnomicon-core` 1.4.0** while the sibling working tree is at 1.5.0 — layer-2 drift (lock behind requirement). Surfaced incidentally when a build regenerated the lock; reverted rather than committed, since it is unrelated to the change that found it.

**A tooling landmine worth recording, because it will recur.** issen's manifests use relative `path` deps into sibling repos (`../../parser/...`). Working from `.claude/worktrees/<name>/` breaks them — cargo fails with `failed to load manifest for workspace member`. This is the same sibling-repo `path`-dep hazard the constitution already documents for release tooling (release-plz, `cargo package`), and it bites `git worktree` for the identical reason: the sibling is no longer next door. CI is unaffected, since it uses the normal layout.

---

## Part 2 — DRY violations, ranked

Ranked by consequence, not by copy count.

### 2.1 Hand-rolled byte readers vs `safe-read` — 205 functions, 47 repos

`safe-read` is published (0.1.0 / 0.2.0 / 0.2.1, none yanked; local equals published), `no_std`, `forbid(unsafe_code)`, `checked_add` throughout.

**Adoption is the problem, not the crate.**

- 17 literal `src/bytes.rs` files totalling **~1,385 lines** (plus `filevault-forensic/core/src/read.rs`, 99 lines, same pattern).
- **205 production hand-rolled fixed-width reader functions across 47 repos** (test helpers and fuzz harnesses excluded; the raw grep over-matched by ~7% and only filtered counts are reported). **This is the one headline figure independent verification could not reproduce at the stated precision** — a blunter proxy (files containing `from_le_bytes`/`from_be_bytes` outside tests/fuzz/target) gives 500 files across 72 repos, a superset consistent with a filtered 205/47 but not a confirmation of it. Treat 205/47 as plausible-but-unverified; the *direction* (most of the fleet hand-rolls) is not in doubt.
- **12 repos declare a real `safe-read` dependency.** Of those, only `iso9660-forensic` (38 call sites), `browser-forensic` (29) and `ext4fs-forensic` (27) genuinely internalized it. `discord-desktop-forensic` and `whatsapp-desktop-forensic` declare it with **zero call sites** — dead dependencies. `ntfs-forensic` is **split-brain**: `use safe_read::` in four modules (`core/src/usn/carver.rs:8`, `usn/reader.rs:12`, `carve.rs:7`, `logfile/usn_extractor.rs:11`) while eight others still use `crate::bytes::` (`boot.rs:24`, `attribute.rs:21`, `index.rs:15`, and others).
- **42 repos hand-roll with no `safe-read` dependency at all.**
- 6 repos pin `safe-read = "0.1"` while 0.2.1 is current, so they cannot reach the `try_*`/`u8` API: ext4fs, iso9660, ntfs, udf, browser-forensic, gpt-partition. **The cause is upstream documentation, not six independent mistakes:** `safe-read`'s own `README.md` install snippet still reads `safe-read = "0.1"`. Every repo that followed the published instructions inherited a caret too narrow for `cargo update` to ever cross. Worth generalizing — a stale version in a crate's own README manufactures the layer-1 staleness pattern in every consumer that copies it, so the README belongs in the release checklist alongside the manifest.
- **10+ repos clear `safe-read` through cargo-vet the wrong way.** They carry `[[exemptions.safe-read]]` where ADR-0018 requires a `trust` entry — mechanism 2 (“ours, from crates.io → `cargo vet trust <crate> h4x0r`”), and the ADR is explicit that “reaching for a weaker one is a defect.” Affected: keychain, 4n6mount, ext4fs, iso9660, forensic-vfs-mount, forensic-vfs-engine, ntfs, udf, discord-desktop, livedisk. An exemption asserts “unreviewed, accepted anyway”; a trust entry asserts the publisher is ours. The distinction is the point of the mechanism. Cheap fleet sweep, and it should be folded into whatever PR wave migrates the hand-rolled readers.

**The copies have diverged on overflow.** Out-of-range → `0` is near-universal, matching `safe-read`, but overflow splits four ways:

| Dialect | Sites |
|---|---|
| `off + N` unchecked (debug-build panic) | luks `bytes.rs:17`, btrfs `:21`, ntfs `:19`, refs `:22`, xfs `:20`, zfs `:48`, vsc `:18`, lnk `lib.rs:200`, cfb `raw.rs:106`, qcow2 `header.rs:20`, ewf `sections.rs:47` |
| `saturating_add` | bitlocker `bytes.rs:19`, ufs `bytes.rs:87` |
| `wrapping_add` | shellitem `reader.rs:21`, winreg-core `bytes.rs:12` |
| `checked_add` (matches `safe-read`) | userassist `lib.rs:212`, sqlite `carve.rs:53`, hfsplus `decmpfs.rs:320` |

**`safe-read` is a legitimate home for this — the layering objection that disqualified `timeglyph` does not apply.** ADR-0016 (line 115) names it among the “generic utility leaves” at the bottom of the hierarchy, and the manifest bears that out: **zero dependencies**, `unsafe_code = "forbid"`, `no_std`, and `rust-version = "1.75"` chosen deliberately so “every fleet reader can depend on it without raising theirs.” Anything added must stay inside that 1.75 floor and must not pull a dependency.

**What `safe-read` should gain:**

```rust
// (a) signed readers — needed by winevt cursor.rs:122-152, forensicnomicon decode.rs:102/115,
//     lnk lib.rs:208, snss lib.rs:293, segb common.rs:77.
//     Unambiguous: same macro shape, no policy decision.
pub fn le_i16(data: &[u8], off: usize) -> i16;   // + be_/i32/i64 + try_ twins

// (b) array window — ntfs `arr`, vsc read_guid (bytes.rs:36), vhdx guid_at (integrity.rs:67)
//     each re-derive this. The bounded_reader! macro ALREADY does it internally;
//     this only surfaces an existing primitive.
pub fn try_bytes<const N: usize>(data: &[u8], off: usize) -> Option<[u8; N]>;
```

**What `safe-read` should NOT gain — two proposals from an earlier draft of this report, withdrawn:**

**LEB128 varint.** Withdrawn. Four reasons, none of which were checked before proposing it:

1. It is a *format*, not a bounded read. `safe-read`'s contract is “N bytes at a fixed offset, bounds-checked, benign default.” A variable-length encoding with its own validity rules is a different kind of thing.
2. **`safe-read` structurally cannot express the forensically interesting answer.** It returns `0`/`None`; `protobuf-core` returns typed errors carrying offsets (`TruncatedVarint`, `OverlongVarint`, `VarintOverflow`). An overlong varint is an evasion signal worth *reporting*, and flattening it to `None` destroys that signal. Centralizing would degrade the best implementation to the level of the weakest.
3. **They may not be the same format.** `chromium-storage/util.rs:6` documents itself as decoding IndexedDB's `EncodeVarInt` — Chromium's own encoding, not the protobuf wire varint. The earlier draft asserted an equivalence it had not verified.
4. **Signatures are incompatible.** `protobuf-core` is a `&mut self` cursor method; `segb` takes `pos: &mut usize`; only `chromium` uses the pure-offset shape.

The underlying finding stands (2.5): the implementations disagree on the tenth byte — `protobuf-core` rejects a payload above `0x01`, while `segb` and `chromium-storage` silently drop the high bits. The remedy is a documented fleet rule with `protobuf-core` as the reference, not a shared function in a crate that cannot say *why* it rejected.

**UTF-16 decoding.** Withdrawn from `safe-read`:

1. `safe-read` is `no_std` with **zero dependencies and no features**; UTF-16 → `String` requires alloc, so this means a feature flag on a deliberately minimal leaf.
2. **The four NUL policies (2.3) are different operations, not variants of one.** A NUL-terminated registry value and a length-prefixed NTFS filename are genuinely different reads; one function serving both needs a policy parameter, at which point sharing buys little.
3. **The best implementation is richer than `-> String`.** `leveldb-forensic/value.rs:53` tracks a `lossy` flag and dangling surrogate halves — precisely the “return types carry security-relevant state” rule. Collapsing to `String` would discard it.

If UTF-16 is centralized at all it belongs in **`forensicnomicon`** — already allocating, already FOUNDATION, already the home of format facts — as several explicitly-named functions rather than one.

GUID handling splits correctly across the two: byte *extraction* via `try_bytes::<16>` above, string *formatting* via the `uuid` crate (2.4), not `safe-read`.

**FOUNDATION should adopt `safe-read` too — the objection to it does not survive checking.** When the wrapping-guard fix above was implemented, `safe-read` was considered and rejected on the grounds that pulling a dependency into FOUNDATION “inverts the layering.” That reasoning is wrong on the facts. ADR-0016's own Consequences section places `safe-read` **inside FOUNDATION**, alongside `forensicnomicon`:

> It holds both domain-knowledge leaves (forensicnomicon, forensic-hashdb) AND generic utility leaves (jsonguard, safe-read, the `forensic-vfs` contract). … **Layer ≠ folder**: in the reorg's physical folders this one layer spans both `knowledge/` (domain facts) and `utility/` (generic libs) — the *layer* (dependency position) and the *folder* (domain grouping) are distinct axes.

`safe-read` is a peer, not something above. The `utility/` folder is what misleads here, and ADR-0016 anticipates precisely that confusion.

The supporting facts all point the same way:

- **`safe-read` has no dependencies at all**, so adoption adds one graph node with no transitive tail — categorically unlike the `uuid` decision in 2.4, which the two superficially resemble.
- **`forensicnomicon` is not literally a zero-dep leaf today** — `forensicnomicon-core` already depends on `serde` (optional). The FOUNDATION definition is aspirational, not strict.
- **The empirical case is decisive:** the hand-rolled readers in this very crate produced **seven** wrapping-guard defects in one file (1.4) — exactly the class `safe-read` exists to make impossible.
- **Credibility:** ADR-0012 mandates `safe-read` for every integer read across 42 repos. That is hard to enforce from the one crate that exempts itself.

**One amendment is genuinely required first.** ADR-0016 states that dependencies flow “down toward FOUNDATION, **never sideways or up**,” and a FOUNDATION→FOUNDATION edge is literally sideways. So ADR-0016 needs a strict *intra*-FOUNDATION ordering: `safe-read` and `jsonguard` are sub-foundation primitives that other FOUNDATION crates may depend on, with nothing depending back up. ADR-0006 already places `safe-read` in the first release wave, so publish order needs no change.

Leaving that ordering implicit is what allowed a hand-rolled reader to survive inside the crate that defines the standard — and what let a reviewer reject the fix on a layering argument the ADR does not actually make.

### 2.2 FILETIME and epoch conversion — 22 converters, 7 zero-semantics

**The epoch arithmetic is correct everywhere.** Every site uses `116444736000000000` / `11644473600` correctly; no arithmetic error was found. This is a clean negative result.

The duplication is in the **edge policy**, re-decided 22 times. For input `0` — the Windows “not set” sentinel — the fleet produces seven different answers:

| Result for FILETIME `0` | Count | Examples |
|---|---|---|
| `None` (absent) | 11 | forensicnomicon `temporal.rs:18`, ntfs `time.rs`, issen-parser-mft, issen-timeline |
| Rendered `1601-01-01` | 4 | timeglyph `secs.rs:13` (deliberate scanner semantics), prefetch4n6 `:68`, zip `vfs.rs:234`, winevt `value.rs:244` |
| `i64::MIN` | 2 | browser-forensic `timestamp.rs:53`, issen-parser-usnjrnl `:166` |
| `0` (i.e. 1970) | 2 | lnk `lib.rs:222`, issen-parser-evtx `:448` |
| Clamped `1970-01-01` | 1 | srum-core `lib.rs:55` |
| `"-"` | 1 | memory-forensic `main.rs:2059` |
| `i64::MAX` | 1 | issen-correlation `temporal_checks.rs:28` (**DEFECT**, see 1.3) |

When these converge in issen's DuckDB super-timeline, “no timestamp” becomes representation-dependent: genuine absence, plus three distinct fabricated instants (1601, 1677/`i64::MIN`, 1970).

Six sites already delegate the arithmetic to `timeglyph` — the wrappers around it are what diverged.

**Other epochs:** Chrome/WebKit has 2 independent implementations (`i64::MIN` sentinel vs `None`; nanoseconds vs milliseconds) plus a third constant in `snss-forensic/core/src/lib.rs:441`. Cocoa/Mac-absolute has **3 implementations with 3 different zero/NaN policies**, and browser-forensic's silently truncates sub-second precision. HFS+ duplicates its epoch constant within one repo at two different types (`vfs.rs:24` as `i128`, `findings.rs:28` as `u32`).

**Formatting is 6-way divergent** — the same FILETIME renders as six different strings and precisions depending on which tool prints it.

**Home crate — corrected twice; the second correction supersedes the first.**

An earlier draft proposed depending on `timeglyph` fleet-wide. A second draft rejected that and proposed `forensicnomicon::temporal` instead. **Both are wrong**, and the second is wrong in a way the audit should have caught: it creates a *second* home for timestamp logic, splitting it between `forensicnomicon` and `timeglyph` — the exact split-brain this report criticizes elsewhere. Time conversion should have one home.

The blockers on `timeglyph` as it stands are real and decisive:

- **Cycle.** `timeglyph/Cargo.toml:77` declares `forensicnomicon = { version = "1.3", default-features = false }` — timeglyph depends on forensicnomicon, so forensicnomicon can never depend on timeglyph. Its own `filetime_to_iso8601` could not move there. (That `default-features = false` is separately an ADR-0013 violation.)
- **MSRV bleed, already realized.** `protobuf-forensic/protobuf-forensic/Cargo.toml:6` records it plainly: *“Depends on timeglyph (MSRV 1.96), so this crate's floor follows the pinned…”* — a published PARSER crate whose MSRV promise was raised to 1.96 by this dependency.
- **Weight, including an inherited hazard.** timeglyph carries `jiff = ">=0.2, <0.2.33"`, capped because jiff 0.2.33 panics on out-of-range input instead of returning `Err`. Every consumer inherits that cap.
- **Consumers are badly stale:** `issen` pins `timeglyph = "0.3"` and `protobuf-forensic` pins `"0.4"` against a published **0.9.5** — layer-1 stale caret, five minor versions behind.

**The correct home is a new `timeglyph-core`**, using the mechanism ADR-0013 already prescribes: *“the lean `<x>-core` library + full `<x>` binary split is the mechanism when a dep is both a library primitive and a heavy tool.”* timeglyph is exactly that — a primitive (epoch arithmetic) and a heavy tool (CLI, MCP, lens GUI, wasm, Python bindings).

`timeglyph-core` holds the pure integer conversions plus the sentinel policy, with **zero dependencies and MSRV 1.75**, registered as a FOUNDATION **primitive** (ADR-0016's PRIMITIVES band). Then `forensicnomicon` may depend on it, parsers may depend on it, and `timeglyph` itself builds on it — one home, no cycle, no MSRV bleed.

**The seam falls naturally: integer arithmetic below, calendar and rendering above.** `(ft - EPOCH_OFFSET) * 100` needs nothing; ISO-8601 formatting needs jiff. This also explains forensicnomicon's hand-rolled civil-date math in `filetime_to_iso8601` — it is reinventing jiff because it cannot depend on it. FOUNDATION should return integers and let callers render, which removes that reimplementation rather than relocating it.

```rust
/// None when ft == 0 (the "not set" sentinel), ft < FILETIME_EPOCH_OFFSET,
/// or the ns value overflows i64.
pub fn filetime_to_unix_ns(ft: u64) -> Option<i64>;
/// Chrome/WebKit 1601-epoch microseconds, same sentinel policy.
pub fn webkit_micros_to_unix_ns(us: u64) -> Option<i64>;
/// Cocoa/Core-Data 2001-epoch seconds; None for 0.0 / non-finite; preserves sub-second.
pub fn cocoa_secs_to_unix_ns(secs: f64) -> Option<i64>;
```

The `None`-on-sentinel policy is defensible because 11 of the 22 sites already implement exactly it. Total-function call sites wrap with an explicit local sentinel, which forces the decision to be *visible* rather than accidental. `timeglyph` keeps its scanner semantics — decoding `0` to 1601 is correct for a tool whose job is identifying what a value *could* be.

### 2.3 UTF-16LE decoding — ≥14 implementations, 4 NUL policies

Same bytes, different strings, depending on which repo reads them:

| Policy | Sites |
|---|---|
| Whole-slice lossy | lnk `lib.rs:520` and issen `issen-parser-usnjrnl/src/lib.rs:257` — **verbatim clones** |
| Stop at first NUL | winreg-core `value.rs:162`, trash `windows.rs:315`, shellitem `reader.rs:64` |
| Trim trailing NULs only (interior kept) | dpapi `blob.rs:153` |
| `Option`-returning | prefetch `lib.rs:108` |
| Lossy-flag + dangling-half tracking (richest) | leveldb-forensic `value.rs:53` |

Big-endian twins exist in `chromium-storage/util.rs:26` and `trash/macos.rs:376`.

The richest implementation (leveldb's, which reports a `lossy` flag) is the one that matches the constitution's “return types carry security-relevant state” rule — it should be the template, not the outlier.

### 2.4 Mixed-endian GUID formatting — 7 copies rendering three different ways

| Rendering | Sites |
|---|---|
| lowercase | bitlocker `guid.rs:14` |
| UPPERCASE | livedisk `drive_layout.rs:99` (also panic-capable), memf-symbols `pe_debug.rs:25`, lnk `lib.rs:233` |
| UPPERCASE with braces | memf-windows `dpapi_keys.rs:59` |

**This is preventive, not a live bug.** An earlier draft claimed the divergence “breaks string-equality GUID joins in issen's correlation layer.” That was an inference stated as an observed consequence, and verification refuted it: `issen-correlation/src/` contains **no GUID reference at all**, and the only GUID-chaining code in the fleet (`issen-evtx/src/process_tree.rs`, linking Sysmon `ProcessGuid`/`ParentProcessGuid`) draws both sides from the *same* parser and formatter, so it cannot diverge. No code today compares a GUID from one of these formatters against one from another. The finding stands as a hazard to remove before such a join is written, not damage to repair.

Two repos already do the right thing and delegate to the `uuid` crate (`vsc/guid.rs:25`; `winevt/value.rs:212-219`, whose comment reads “Reuse the vetted crate instead of the hand-rolled formatter”). Standardize on `uuid::Uuid::from_bytes_le` — already a dependency in 8+ repos — plus one case convention.

Note: `ext4`/`btrfs` `uuid_string` are RFC-order straight bytes, a legitimately different rendering. Not duplicates.

**Migrating one formatter proved the approach and priced it.** `livedisk-forensic` now uses `uuid::Uuid::from_bytes_le(...).hyphenated().encode_upper(...)`, and its pre-existing assertion — `EBD0A0A2-B9E5-4433-87C0-68B6B72699C7`, authored before the change against the documented layout — still passes byte-for-byte. That is an independent check that the `uuid` crate reproduces the hand-rolled mixed-endian logic exactly.

Two caveats the migration surfaced:

- **This converges byte order, not case.** `vsc`, `winevt` and `dpapi` render lowercase via `to_string()`; `livedisk` renders uppercase and keeps doing so, because changing it would alter consumer-visible strings. Six hand-rolled formatters become one crate call; the **case divergence survives** and is a separate, output-changing decision.
- **`uuid` is a larger supply-chain expansion than it looks.** It records 11 crates in the lock graph via its *optional* `js` feature (js-sys, wasm-bindgen ×4, futures-core/task/util, once_cell, pin-project-lite). None of it compiles for macOS/Linux/Windows — the deps are `optional = true` behind `cfg(target_arch = "wasm32")` — but Cargo.lock records optional deps and cargo-vet audits the whole graph, costing +44 lines of `supply-chain/config.toml` and +18 of `audits.toml` for one crate. `vsc-forensic` already carries the identical footprint, so there is precedent, but a repo that was previously lean pays a real price. The zero-dependency alternative (`safe_read::u8(b, 8)`…`u8(b, 15)` inside the existing `format!`) fixes the bounds bug while keeping a hand-rolled formatter — it trades DRY convergence for supply-chain leanness, and is a legitimate choice per repo.

### 2.5 LEB128 varint — 6 hand-rolled, and they disagree on malformed input

| Behaviour on overlong/out-of-range input | Site |
|---|---|
| Strictly rejects (10th-byte payload > 0x01) | protobuf-core `reader.rs:42` |
| **Silently drops out-of-range bits and accepts** | segb `proto.rs:75-104` |
| Silently truncates at shift 63 | chromium-storage `util.rs:6`, browser-forensic `varint.rs:21` |

The same malformed bytes produce an error in one parser and a wrong-but-plausible number in another. `leveldb-core` uses third-party `integer-encoding` — an ADR-0010 migration candidate. SQLite's varint (big-endian, 9-byte) is a genuinely different format and is load-bearing; keep it.

### 2.6 CI and repo scaffolding — total drift where no mechanism exists

| Artifact | Copies | Distinct normalized variants |
|---|---|---|
| `ci.yml` | 91 | **89** (66 distinct feature profiles) |
| `deny.toml` | 91 | **43** (25 distinct license allow-lists) |
| `renovate.json` | 90 | **37** |
| `docs/privacy.md` | 90 | **63** after name normalization |
| `docs/terms.md` | 90 | **55** after name normalization |
| README badge sets | 91 | **76** |
| Coverage-gate implementation | 75 | **6**, with **2 different semantics** |
| `release-plz.yml` | 87 | **2** |
| `rust-toolchain.toml` | 90 | **1** effective (`1.96.0` everywhere) |

The last two rows are the proof of concept: where the fleet adopted a shared mechanism, it converged completely. Where it did not, essentially every repo is unique.

**License policy has drifted into 25 allow-lists.** BSL-1.0 is allowed in 13 repos, the OpenSSL license in 4, Unlicense in 6, with CC0-1.0 / CDLA-Permissive-2.0 / MIT-0 / 0BSD / bzip2-1.0.6 scattered ad hoc across ~15. Twelve repos carry RUSTSEC ignores, the same advisory copy-pasted independently — RUSTSEC-2026-0194 in 6 repos, RUSTSEC-2026-0195 in 5. Each copy can go stale on its own.

**The coverage gate is worse than a DRY problem.** Six implementations exist, and the 21 repos using `--fail-under-lines`-style flags get **no `// cov:unreachable` exemption handling**, while the script and inline variants honor it. “100% coverage” does not mean the same thing in two fleet repos. One script (`scripts/coverage-gate.py`) is byte-identical across 9 repos.

**Two of the three semantics actively pressure you to delete the code that keeps a parser safe.** Under an aggregate floor, a provably-unreachable defensive guard is indistinguishable from an untested line; under the naive `grep DA:n,0` variant (`dar-forensic`), the only route back to green is deleting the guard. ADR-0012 *requires* those guards, so two of the three are in direct tension with the security standard. Only the per-line, `cov:unreachable`-aware form (36 repos) preserves defence in depth. Floors also conceal *which* lines rot — and every floor in the fleet carries a never-actioned “ratchet it up” comment.

**Scope is part of the semantics, and one gate is misnamed because of it.** `ntfs-forensic` runs coverage as `--lib` with no features under a job named **“Coverage (100% lines)”**, which leaves the whole `vfs` adapter — **37 lines of `core/src/vfs.rs`** — outside the measurement entirely. The number is true of what it measures; the job name is not true of the crate. A consolidation that standardizes the *threshold* while leaving scope per-repo would preserve exactly this class of misstatement, so scope has to be part of the shared definition.

**Correction to this report:** an earlier draft said 22 repos carry an explicit `permissions:` block and a later pass claimed 0. Measured: `grep -rl '^permissions:' --include=ci.yml` returns 23 files, one of which is a packaged copy under `codec/xpress-huffman/target/package/`. **22 real repos** have a top-level block; none have it job-level. The original figure was right.

**`rust-version` contradicts the toolchain uniformity:** 13 distinct values across root manifests (1.85 × 36, 1.81 × 16, 1.75 × 9, absent × 7, 1.96 × 4, 1.93 × 4, 1.88 × 5, 1.80 × 4, 1.87 × 3, 1.83 × 2, 1.70 × 1) — wider than the stated 1.75/1.80 library floor, though some are dependency-dictated (btrfs documents 1.87 forced by `ruzstd`).

**Corrected mechanism note:** `cargo-deny` has **no include or inherit mechanism**. Verified two ways — `cargo deny check --help` (v0.19.0) offers only `-c/--config <path>`, and the config-schema documentation defines no `extends` field. The workable approach is to run one shared config via `--config` from inside a reusable CI workflow, which removes the per-repo file entirely. License `exceptions` and advisory `ignore` entries are crate-scoped, so per-repo needs live safely in one shared file as a union.

### 2.7 Report-layer boilerplate — 661 mechanical lines

54 `impl Observation` blocks across 48 repos, 2,469 impl-body lines. A methodology note worth recording: a naive `rg "impl Observation"` finds only 46 — **17 more use the fully-qualified `impl forensicnomicon::report::Observation for`**.

| Component | Measure | Verdict |
|---|---|---|
| Variant → constant match arms in `severity()`/`code()`/`category()`/`mitre()` | **157 arms, 661 lines (27% of all impl-body code)** | Accidental — `#[derive(Observation)]` candidate |
| Pure-delegation impls (`Some(self.severity)`, `self.code`) | ≥8 crates (the `findings.rs` group) | Accidental — shared struct + blanket impl |
| `category()` overridden despite `Category::from_code` default | 34 of 54 (63%) | The keyword classifier is not pulling its weight |
| Duplicate canonical-shaped `Severity` enums | 2, both inside issen: `issen-signatures/src/matching/results.rs:36`, `forensic-pivot/src/rule.rs:7` | Real violation — migrate to `forensicnomicon::report::Severity` |
| `severity_rank` / `severity_token` helpers | 3+ near-identical | Add `Severity::rank()` / `Severity::token()` upstream |
| CLI `OutputFormat` enums | **8 independent**, split vocabulary | `Jsonl` vs `Ndjson`, `Table` vs `Text` — one-concept-one-name violation |

Two CLIs ship **no human-readable format at all**: `winevt-cli` (`Json`/`Csv` only) and `srum-cli` (`Json`/`Csv`/`Ndjson`).

**Anomaly-code namespace — one real problem.** There are **zero cross-crate code collisions**; 17 apparent ones were traced and all cleared (GPT partition-type GUIDs, CVE ids, `#[cfg(test)]` fixtures, issen test assertions). Casing convention is clean fleet-wide. However:

- **issen mints codes in `ntfs-forensic`'s namespace**, and worse, names the same phenomenon twice: issen emits `"NTFS-TIMESTOMP-SI-FN-MISMATCH"` (`issen-correlation/src/timestomp.rs:30`) while ntfs-forensic emits `"NTFS-TIMESTOMP"` (`ntfs-forensic/forensic/src/lib.rs:183`). **A consumer grouping findings by code counts one detection as two.** issen already owns `CORR-` and `HEUR-` prefixes covering 32 of its 71 codes.
- `parser/ese-forensic/crates/ese-integrity` owns 14 `SRUM-*` codes while a separate `srum-forensic` repo exists. No collision today; nothing prevents one.
- Uniqueness is currently an accident of discipline across ~450 code literals. A cheap structural fix: each crate exposes `pub const CODES: &[&str]`, issen aggregates and asserts uniqueness in a test.

### 2.8 Container-abstraction leakage — 5 ADR-0011 breaches

The abstraction is real and content-sniffing: `orchestration/disk-forensic/src/container.rs` covers E01/EWF, VMDK, VHDX, VHD, QCOW2, DMG and physical AFF4; `logical.rs` covers AD1/AFF4-L.

| Site | Dispatches on | Breach |
|---|---|---|
| `parser/usb-forensic/src/bin/usb4n6.rs:160,165,173` | hand-rolled 0x55AA + EVF magic, direct `ewf::EwfReader::open` | **Yes** — repo already depends on `disk_forensic` elsewhere |
| `log/winevt-forensic/crates/winevt-carver/src/lib.rs:320` `carve_from_ewf` | EWF only | **Yes** — the literal `if ewf {…}` smell |
| `filesystem/ext4fs-forensic/ext4fs-core/src/lib.rs:277-284` `Ext4Fs::open_ewf` | EWF only | **Yes** — FILESYSTEM importing CONTAINER |
| `utility/blazehash/src/forensic_image/mod.rs:19-37` | **file extension**, not content | **Yes** — and pins `ewf = "0.2"` while the fleet is on 0.4 |
| `parser/browser-forensic/.../cli.rs:1533-1553` | magic sniff, detection-only gate | Partial — re-declares three magics forensicnomicon owns |

Each breach also hides a **capability gap**: those paths handle E01 but silently not VMDK/VHDX/QCOW2.

**The structural cause matters more than the sites.** `disk-forensic` sits in the ORCHESTRATION layer, so LOG, FILESYSTEM, PARSER and UTILITY consumers *cannot* depend on it without inverting ADR-0016 — so each imported `ewf` directly. This is a layering decision, not a set of careless mistakes. Two honest options: delete the in-crate opening and let the orchestrator hand down bytes (preferred, and matches the PARSER-accepts-`Path`/`&[u8]` rule), or give container-open a CONTAINER-layer home below these consumers.

The container format set is independently enumerated **4 times** beyond forensicnomicon: disk-forensic, forensic-vfs-engine's `default_openers()`, issen's provider crates, and `issen-signatures/src/heuristics/magic_table.rs`.

**Format facts are re-declared as literals** despite forensicnomicon owning them: the EVF magic in **6 production sites** (including `ewf-forensic/forensic/src/integrity.rs:61`, which re-declares EVF2 rather than importing its own knowledge crate) and the ZIP local-file-header magic in **7**.

**Hashing:** `blazehash-core`'s published API is bytes-only (`hash_bytes(algo, &[u8])`); the streaming/mmap machinery lives in the app crate. Consumers therefore *cannot* reuse it for streaming file hashes, which is why hand-rolled loops like `issen-fswalker/src/sources.rs:141-155` exist. Lift `hash_reader`/`hash_file` into `blazehash-core` first, then migrate.

### 2.9 Test and docs infrastructure

- **`rot13` — 4+ independent implementations, and the shared home already exists.** `forensicnomicon/crates/core/src/catalog/decode.rs`, `memf-windows/src/userassist.rs:54`, `userassist-forensic/core/src/lib.rs`, `winreg-artifacts/src/userassist.rs`. That UserAssist values are ROT13-encoded is a **format fact**, which ADR-0016's decision rule #1 assigns to `forensicnomicon` — where an implementation already sits. Every consumer depends on FOUNDATION already, so the other three migrate with no new dependency edge and no new crate. `blob-decoder` would be the wrong home (MSRV 1.88, and it sits above these consumers). Missed by the sweeps despite an explicit brief to find decode primitives duplicated 3+ times.

  Worth stating the general test, since “mint a crate” is the tempting answer: a new FOUNDATION crate is justified only by **multiple consumers + a stable contract + a workable dependency direction + nothing existing that fits.** `rot13` fails the last condition. `timeglyph-core` (2.2) passes all four. A six-line function gets a *home*, not a crate.
- **Cursor structs:** 5 byte-identical `{buf: &[u8], pos: usize}` definitions (winevt `cursor.rs:31`, leveldb-core `bytes.rs:11`, protobuf `reader.rs:15`, trash `macos.rs:261`, state-history `identity.rs:308`) plus 2 extended.
- **`corpus_dir()`** copy-pasted across 5 repos.
- **187 distinct env-gate variable names** with no grammar: `_ORACLE` × 25, `_ORACLE_IMAGE` × 3, `_ORACLE_IMG` × 3, `_IMAGE` × 4, `_IMG` × 1, `_FIXTURE` × 3, `_BIN` × 5, and 105 unclassifiable.
- **Test-data catalog has drifted:** 61 repos have `tests/data/`, 55 have a README, 6 lack one; the fleet catalog names only 51 repos, and **16 repos with a `tests/data/README.md` are absent from the catalog entirely**.
- **README footer:** 4 repos render “Security Ronin Ltd.” with a trailing period; `forensic-carve` has no footer at all.
- **Copied scaffolding rots in place — a concrete instance.** `shellitem/CONTRIBUTING.md` instructed contributors to run `cargo +nightly fuzz run shelllink   # or: forensic` — **`lnk-forensic`'s target names**, carried over when the scaffolding was copied and never updated, in a repo that had no fuzz targets at all. Its ADR 0003 and `docs/PRD.md` likewise both claimed no `ci.yml` existed, which had been stale for some time. This is what the 89-variant `ci.yml` and 63-variant `privacy.md` counts look like at the level of a single file: the copy is made once, the original moves on, and nothing detects the divergence. Instructions that name another repo's artifacts are the highest-signal tell.
- **Coverage badges:** the constitution mandates a Codecov badge row; **zero Codecov badges exist fleet-wide**, and only 2 repos carry any coverage badge (static shields). The standard is unenforced — either enforce it or relax it.

---

## Part 3 — Duplication examined and cleared

Recording what was checked and found justified is as useful as the findings, and prevents re-litigation.

| Pattern | Why it is justified |
|---|---|
| Per-crate `AnomalyKind` enums | By design (ADR-0007) — type safety plus independent publishing |
| `note()` bodies (87 arms) | Format-specific prose interpolating variant payloads; a derive would need a template language worse than the code |
| `evidence()` (31) / `subjects()` (10) overrides | Payload-shaped, not mechanical |
| `Observation::to_finding` | Already centralized in forensicnomicon (`crates/core/src/report.rs:512-537`); no analyzer re-implements Finding assembly |
| srum-analysis's native `Severity` (`Clean`/`Informational`/`Suspicious`/`Critical`) | A genuinely different scale, normalized to canonical at `record.rs:67-80` — exactly ADR-0007's prescribed pattern |
| Analyzer entry-point signature variation | Input domains genuinely differ (bytes / reader / pre-parsed metadata). A trait would need associated-type gymnastics with no consumer that benefits. Only the *naming* is accidental |
| `disk-forensic`'s own format dispatch | That is its job — it is the abstraction, not a consumer |
| EWF extension-based `.E02…` segment chaining | Format mechanics owned by EWF itself |
| Fuzz-harness boilerplate (130 files of ≤8 lines) | A 5-line harness costs less than any abstraction |
| `docs/privacy.md` / `terms.md` existing per repo | Each Pages site must serve its own. **The files must duplicate; the 63 and 55 distinct wordings must not** |
| `mkdocs.yml` (52 variants) | Nav genuinely differs per repo |
| 30+ container `*Reader` structs | `io::Read`/`Seek` domain logic, load-bearing |
| SQLite's 9-byte big-endian varint | A different format from LEB128 |
| `ext4`/`btrfs` `uuid_string` | RFC-order rendering, legitimately different from mixed-endian GUIDs |
| Path `normalize*` functions (41) | Semantically distinct — registry ids, URLs, macOS firmlinks, device prefixes. Centralizing would couple unrelated semantics |
| Small hash-an-identifier sites | Ordinary `sha2` use, not duplication |
| ewf-forensic's 22 MD5/SHA1 sites | Format-mandated — E01 stores these digests |

---

## Part 4 — Corrections to the prior audit

An earlier pass over the same question produced several claims this audit contradicts. Recording them because the failure modes are instructive.

| Prior claim | Corrected | Cause |
|---|---|---|
| “cargo deny supports `[graph.targets]` and `include` directives” | **False.** cargo-deny has no include/extends mechanism (verified against `--help` v0.19.0 and the config schema) | Asserted a tool capability without checking it |
| “Depend on `timeglyph` fleet-wide for FILETIME” | **Not viable.** timeglyph pins `rust-version 1.96.0`, breaking published parsers' 1.75/1.80 floors; ADR-0016 bars PARSER→utility | Recommended a fix without checking the constraint |
| “24 Cargo.toml files depend on `safe-read`” | **12 repos.** The grep matched comments and doc text, not dependencies | Counted grep hits as facts |
| “1,325 lines of duplicated `bytes.rs`” | **~1,385.** | Arithmetic error |
| “The fleet has ~92 repos” | **91.** | Used a `ci.yml` file count as a repo count |
| “~23 repos missing `workspace.lints`” | **71/91 canonical, 16 divergent, 4 absent** | Conflated divergent with missing, against a wrong denominator |
| “~20 FILETIME sites across ~12 repos” | **22 converters across 14 repos** | Figure was never actually measured |
| “`decode_utf16le` — 4+ implementations” | **≥14, with 4 distinct NUL policies** | Stopped at the first few grep hits |
| “Post-reorg monorepo would eliminate the config problem” | Premise stale — `REORG.md` no longer exists; all 91 repos have independent public remotes | Reasoned from a document that had been archived |
| Framed `bytes.rs` as “17 copies” | The real scope is **205 reader functions across 47 repos**; 42 have no `safe-read` dep | Counted files matching a filename rather than the pattern |

Dimensions the prior audit **missed entirely**: the report/analyzer layer (2.7), container-abstraction leakage (2.8), all of Part 1 — including the fabricated fuzzing claim, both timestamp defects, and the panic-capable readers — the 48-repo secret-scan hole, and the 81-repo floating-action-pin problem.

Two prior claims **survived** verification: the `bytes.rs`-versus-`safe-read` finding is real and understated, and `forensicnomicon` as the timestamp home (offered as a fallback) is the correct answer.

---

## Part 5 — Remediation sequence

**Immediate — small local edits, no coordination:**

1. `issen-correlation/src/temporal_checks.rs:36` — saturate negatives to `i64::MIN`, or return `Option`.
2. `prefetch4n6.rs:68` — add the zero guard. Hardening, not a hotfix: upstream filtering makes the bad path unreachable today (see 1.3).
3. `srum-core/src/lib.rs:55,65` — return `Option<Timestamp>` instead of clamping to `UNIX_EPOCH`.
4. `vmdk-forensic/core/src/bytes.rs:6` — replace the `b[..4]` slice index with a bounds-checked read (and drop the unreachable `.expect()`). No live caller, so this is hygiene, not a hotfix.
5. `forensicnomicon/crates/core/src/catalog/decode.rs:85-99` — use `checked_add` in the guard.
6. `livedisk-forensic/src/drive_layout.rs:99` — bounds-check before indexing.
7. `shellitem` — add the `parse_idlist` fuzz target (required by ADR-0012 regardless), which makes the README sentence true. Note that `lnk-forensic` and `winreg-forensic` both depend on `shellitem` and have real fuzz harnesses that may reach this code incidentally; that does not rescue a first-person “fuzzed over `parse_idlist`” claim, which asserts a dedicated harness.

Each of items 1–6 wants a failing test first, per the TDD discipline.

No action on `snapshot-forensic` — see 1.1; its README is already future-tense.

**Structural enablers — these unlock most of the rest:**

9. **One org reusable CI workflow** (`SecurityRonin/.github`), callers reduced to ~10-line stubs. Verified viable: cross-repo `workflow_call` works for public repos, `secrets: inherit` passes org secrets, and the called workflow should be pinned to a full SHA. This single change collapses 89 `ci.yml` variants to 1 and simultaneously closes the 48-repo secret-scan hole, the 81-repo floating-pin problem, the 69-repo missing-`permissions` problem, and — by running `cargo deny --config <shared>` — the 43-variant `deny.toml` problem.
10. **`forensicnomicon::temporal`** gains the three sentinel-policy functions (2.2); migrate the 22 converters.
11. **`safe-read` 0.3** gains signed readers and `try_bytes::<N>` only (2.1) — staying `no_std`, dependency-free, and inside the 1.75 floor; then sweep the 42 non-adopting repos. Explicitly **not** LEB128 or UTF-16: see 2.1 for why both were withdrawn.

**Mechanical sweeps, once the above land:**

12. Renovate org preset — per-repo file becomes one `extends` line. Only 40 of 90 currently comply with the mandated `lockFileMaintenance` + `automerge` + `rangeStrategy: bump` trio.
13. One canonical coverage-gate action with `// cov:unreachable` semantics, replacing 6 implementations and 2 meanings of “100%”.
14. `forensic-testgate` dev-dependency whose only API is loud-by-construction, making the silent skip unwritable — secure-by-default applied to tests. Migrates 79 silent gates.
15. Canonical `privacy.md` / `terms.md` templates plus a drift check. These are legal texts currently maintained in 63 and 55 wordings.
16. Standardize GUID formatting on `uuid::Uuid::from_bytes_le`; pick one case convention (2.4).
17. Retire the issen `NTFS-` prefix encroachment; add the `CODES` uniqueness test (2.7).
18. Decide the container-layer question (2.8) — it is a layering decision, not a cleanup.
19. `[workspace.lints]` sweep for the 20 divergent/absent repos, prioritizing journald/winevt/srum, which have **no `unsafe_code` key at all** while parsing untrusted input.
20. One deliberate fleet license-policy decision, then delete the 25 ad-hoc allow-lists.

**No action:** `rust-toolchain.toml` is already converged.

---

## Appendix — measurement notes

Two methodology failures were caught and corrected mid-audit; both would have produced confidently wrong numbers:

- An unquoted shell glob in `find -name bytes.rs` returned **zero** results. The true count is 17. Any conclusion drawn from that first run would have been inverted.
- `rg "impl Observation"` finds 46 of 54 impls; the other 17 use the fully-qualified path. (The arithmetic here is not an error: 46 + 17 = 63 includes overlap between naive and qualified matches within the same files; the deduplicated total is 54.)

Reported false-positive rates: the raw `extension()` grep was ~97% false-positive for container dispatch (131 hits → 1 genuine production site); the magic-literal grep ~77%; the integer-reader grep ~7%. Only filtered counts appear above.

**A systematic failure mode in the first draft, worth naming so it is not repeated.** Three findings asserted a *consequence* that follow-up verification could not reproduce, and all three failed the same way: the function was read correctly, and the call graph was not checked.

| Claim | What was missing |
|---|---|
| Divergent GUID formatting “breaks string-equality joins in issen's correlation layer” (2.4) | No such join exists — `issen-correlation/` contains no GUID reference at all |
| `prefetch4n6` “prints `1601-01-01…` for an unset run-slot” (1.2) | `prefetch-core` filters non-positive FILETIMEs upstream, so the path is unreachable |
| `vmdk-forensic`'s reader “panics on any input shorter than 4 bytes” (1.4) | True of the function; `chunks_exact(4)` means no caller can supply short input |

The first draft *did* apply this check to the issen saturation defect (“no non-test callers… but it is published API”) and then failed to apply it to the next three findings, while stating them with equal or greater confidence. Reading a function body proves what the function does; it does not prove anything reaches it. Both questions have to be asked, and the answer to the second belongs in the finding — a wrong function guarded by circumstance is still worth fixing, but it is not an active bug and should not be sold as one.

Every finding in this report now carries a reachability answer or an explicit “not assessed.”

**A second failure mode, and a cheap heuristic that catches it.** Three counts in this audit were wrong because a file count was reported as a repo count (`grep -rl` lists files; 91 repos hold roughly 350 workflow files between them). A fourth — a claim that **0 of 91** repos set a `permissions:` block — came from a regex written `^\s*permissions:` without `re.MULTILINE`, so `^` anchored to the start of the file and matched nothing.

The heuristic that would have caught the last one, and is worth applying generally: **an extreme value is exactly where you check twice.** A universal negative about 91 independently-maintained repositories should read as implausible on its face. “Zero of ninety-one” is a claim about a *population*, and populations that size rarely agree on anything — so the number is more likely to be measuring the instrument than the fleet.

Corollaries used throughout the later passes: any figure sourced from `grep -rl` needs `cut -d/ -f1,2 | sort -u` before it can be called a repo count; and a count that has not been reproduced by a second, differently-shaped method should be reported with that caveat attached.

Counts throughout are from Python `os.walk` scans excluding `target/`, `.git/`, `.claude/`, `node_modules/`, and vendored third-party trees, with duplicate bodies opened and read rather than inferred from grep, and file clustering by content hash both raw and name-normalized.
