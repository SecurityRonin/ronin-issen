# Fleet Lessons Learned

Hard-won findings that cost real time and would otherwise be re-derived in
whichever component hits them next. Each entry is a **failure that did not
announce itself** — a green run, a plausible number, a confident sentence — plus
the cheap check that would have caught it.

This file is deliberately narrow. General engineering discipline lives in
`~/.claude/CLAUDE.core.md`; topic standards live in their own `docs/*.md` and own
their own gotchas. An entry belongs here only when it is fleet-specific, was
observed rather than reasoned, and has no better home.

**Every entry states the date it was observed.** A lesson is a fact about a day,
not a standing property — verify before relying on one that names a version, a
count, or a tool's behaviour.

---

## A `forensic-vfs` version bump is a fleet release train

*Observed 2026-08-23.*

`forensic-vfs-engine` links **18** reader crates each with `features = ["vfs"]`,
so every one compiles against the engine's `forensic-vfs`: ewf, ntfs-core,
ext4fs-core, xfs-core, iso9660-forensic, apfs-core, hfsplus-forensic, fat-core,
btrfs-core, ufs-core, udf-forensic, zfs-forensic-core, archive-core, ad1-core,
bitlocker-core, luks-core, filevault-core, veracrypt-core.

Mixing two `forensic-vfs` versions in one graph is **`E0277`** — two incompatible
`FileSystem`/`DynFs` traits. `4n6mount`'s own `Cargo.toml` carries a comment
recording a previous occurrence (engine 0.1.4 on 0.4 against the crate's 0.7),
which is why it takes registry versions rather than path deps.

Five of the 18 live in repos whose names don't match the crate: `iso9660-forensic`,
and `bitlocker`/`luks`/`filevault`/`veracrypt` under `components/encryption/*-forensic`.

**Apply:** order any such change readers → engine → consumers, and price the
coordination before agreeing to it. The per-repo work is usually a one-line bump
(verified on ewf-forensic: 486 tests pass on a bare `0.7 → 0.8`), so the cost is
the release train, not the code. Better still, avoid the bump — see
*"On a `0.x` library, release-plz turns `feat:` into a fleet migration"* in
[`release-standard.md`](release-standard.md).

---

## An unseeded fuzz target tests the magic check, not the parser

*Observed 2026-08-21.*

`ios-backup-core`'s `parse_manifest` target ran **3,094,501 executions, added 2
corpus units, and reported zero crashes**. `read_files` rejects anything without
the SQLite header immediately, so the fuzzer never reached the parser — the clean
result described the front door. Seeded from the committed fixtures, the same
target crashed in **143,853 runs**, finding a `usize` overflow in `sqlite-core`
reachable from any consumer parsing untrusted SQLite.

"Robust" and "never executed" produce identical output. The distinguishing signal
is **`new_units_added`**, not the crash count: near-zero over millions of runs
means the corpus never got inside the format.

**Apply:** seed every target from `tests/data/` before trusting a green run; make
the CI seeding step **fail if it seeds nothing**, because an empty corpus reads as
coverage that does not exist; and read `new_units_added` alongside the crash
count. Note the shared `fuzz-build` job only *builds* targets and skips cleanly
when a repo has none — a green CI says nothing about whether fuzzing ever ran.

---

## An ADR's claim about a *consumer* rots silently

*Observed 2026-08-23.*

`ios-backup-forensic`'s ADR-0005 opened by stating that `4n6mount` reaches
logical containers through `disk_forensic::logical::open`, and specified an
upstream change to `disk-forensic` on that basis. **`disk-forensic` is not a
dependency of `4n6mount` at all** — it goes through `forensic-vfs` and
`forensic-vfs-engine`. The specified change would have been correct, tested,
documented, and worth nothing.

The claim was never observed. It propagated into `core/src/logical.rs`'s module
docs, where it justified a type's shape, and into a `vfs` feature flag that
declared an optional `forensic-vfs` dependency and contained zero references to
it. Re-deriving it cost one `grep` over the consumer's manifest.

The sentence in a design doc most likely to rot is the one about **someone else's
code** — no test, compiler or CI job ever re-checks it, and it reads as settled
fact months later.

**Apply:** before building on an ADR statement about a downstream consumer, open
that consumer's `Cargo.toml` on `origin/main` and confirm the dependency exists.
When a premise turns out false, correct **every** place it propagated — the ADR,
the code docs, the feature flag, the nav label — and leave the original body
intact under a supersession note. The retraction is the part worth keeping.

---

## `git -C <repo> worktree add <relative-path>` resolves inside the repo

*Observed 2026-08-23.*

In a sweep across 18 repos, `git -C "$d" worktree add "$w" origin/main` with both
paths **relative** created
`ntfs-forensic/components/filesystem/ntfs-forensic/.claude/worktrees/vfs08` — git
resolved `$w` against the repo, not the shell's cwd. Every later step looked at
the intended path, found nothing, and the sweep reported *"no forensic-vfs
dependency"* for **17 of 18** repos, all of which declare one.

It does not error. It produces a uniform, flattering answer ("nothing to
migrate") and leaves stray worktrees and branches in every repo it touched.

**Apply:** pass **absolute** paths to `git -C … worktree add`, confirm with
`git -C <repo> worktree list` before trusting a multi-repo sweep, and re-derive
one case by hand whenever a sweep returns the same answer for nearly every repo.
Clean up with `worktree remove --force` plus `branch -D` rather than leaving
debris in someone's checkouts.
