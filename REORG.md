# Fleet Folder Reorganization — `~/src/ronin-issen/components/<category>/<repo>`

**Status:** DESIGN — nothing has been executed (two repos are staged on disk; see §0.5). ·
**Date:** 2026-07-19 (rev 3 — consolidated into the `ronin-issen` umbrella as the single source
of truth). · **Home:** this file — `~/src/ronin-issen/REORG.md` — is now the one authoritative
reorg plan.

**Consolidates and replaces three prior plans** (removed from `issen/docs/plans/` in the same
change that created this file; recoverable via issen git history):

- `2026-06-29-fleet-monorepo-consolidation.md` — recommended a history-merge **monorepo**;
  **overruled** by the user's 2026-07-04 folder-umbrella decision. Its empirical case *against*
  polyrepo (the fn-1.0 publish campaign — ~70 manual `cargo publish`es in topological order,
  stale-caret traps, local-ahead strands, recon-missed repos) is the rationale preserved in §2
  and §4.2(b); the answer chosen instead was **release-plz per repo**, not a merged history.
- `2026-07-04-fleet-umbrella-move-manifest.md` — the first umbrella manifest; its `~/src/issen`
  root (with the `.issen-umbrella` swap dance to dodge the umbrella/repo name collision) and its
  13-category / ~55-repo taxonomy are replaced by `~/src/ronin-issen` and the current taxonomy.
- `fleet-reorg-design.md` (rev 2, 2026-07-18) — the immediate predecessor, hardened after
  adversarial review; its content is carried forward here essentially intact.

---

> ## ⛔ HARD PRECONDITION — EXECUTION IS GATED ON A COMPLETED, VERIFIED BACKUP
>
> **The backup is NOT done as of 2026-07-19. Nothing in this document may be executed until it
> is.** This is a plan to be executed LATER. Do not start until every box below is checked:
>
> - [ ] **Full backup of `~/src` completed and verified** (Time Machine snapshot or rsync clone
>       to external storage) — verify by restoring one repo (e.g. `safe-read`) to `/tmp` and
>       running `git -C /tmp/safe-read fsck && cargo check`.
> - [ ] **Full backup of `~/.claude/` and `~/.claude.json`** (session history, per-repo memory,
>       skills) — verify by opening one restored `projects/*/…jsonl` file.
> - [ ] **Every moving repo is committed and pushed** — the dirty/ahead sweep (§6.1) reports
>       zero rows, or each remaining row is explicitly waived in writing.
> - [ ] **The two local-only fleet repos are remote-safe, individually verified**:
>       `archive-forensic` and `forensic-vfs-mount` currently have **no `origin` at all** — they
>       are single-disk-authoritative; a disk failure mid-move loses them entirely. For **each**,
>       record in `.migration/state-before.json`: (a) the created remote URL
>       (`SecurityRonin/<name>`), (b) the pushed HEAD SHA confirmed present on GitHub
>       (`git ls-remote origin HEAD` matches local), (c) `git fsck --full` clean, (d) a **restore
>       test** — fresh `git clone` to `/tmp/<name>-restore` builds (`cargo check` where
>       applicable). A generic "push all" does not satisfy this box.
> - [ ] **`bluetooth-forensic` — verify-only.** It was local-only when rev 2 was written; that is
>       now closed (it has a `SecurityRonin` remote and is published). Confirm
>       `git ls-remote origin HEAD` matches local and the tree is clean — no remote-creation step.
> - [ ] **Zero Claude/Codex/agent processes running** — `pgrep -fl 'claude|codex'` returns
>       nothing (the migration rewrites `~/.claude.json` and renames session dirs; any live
>       writer clobbers or races them), and no cargo builds anywhere under `~/src`.
> - [ ] **Release automation frozen for the migration window**: no release-plz PR merges, no
>       `v[0-9]*` tags pushed, no `cargo publish`, until the Phase-6 final gate passes
>       (rollback is only a pure inverse while nothing has been pushed or published — §6.7).
> - [ ] A rollback manifest location exists: `~/src/ronin-issen/.migration/` (created by the
>       runbook script itself, §6).

---

## 0.5 Current on-disk state & divergences (2026-07-19)

`~/src/ronin-issen/` exists but is a **bare staging skeleton**, consistent with "nothing has been
executed":

- It is a **plain folder with no `.git`** (as designed — §1).
- It contains only `components/_deprecated/` holding two fully-moved repos, each with its own
  nested `.git`: **`ewf`** and **`usnjrnl-forensic`**.

Three divergences between this staging and the design below — reconcile before/at execution:

1. **`_deprecated/` location.** The design (§3.1, §3.3) places `_deprecated/` at the umbrella
   root, `~/src/ronin-issen/_deprecated/<repo>` — a sibling of `components/`. On disk it sits
   **inside** `components/_deprecated/`. Canonical = the design (root-level); the two staged repos
   move up one level, or the design is amended — resolve before Phase 2 (a Gate-0/Phase-1
   decision, per §7.4).
2. **`ewf` placement.** §3.3 maps `ewf` to `container/` (it is an active container repo, commits
   this week). On disk it is staged under `_deprecated/`. This most likely reflects the still-open
   "fold `ewf` into `ewf-forensic`" question (§7.4) — **confirm intent**: a live `ewf` belongs in
   `container/ewf`; only a decision to fold-and-retire justifies `_deprecated/`. Resolve this
   before Phase 2 (§7.4) so `ewf`'s destination is unambiguous.
3. **`_deprecated/` set.** §3.3 lists `{tl, usnjrnl-forensic}`. On disk it holds
   `{ewf, usnjrnl-forensic}` (no `tl`, plus the mis-staged `ewf`). Regenerate the bucket from
   §3.3 at execution.

Because these two repos already carry their own `.git` and were relocated by a folder move, they
fold into the Phase-2 journal like any other move (idempotent: source gone + dest present with the
recorded HEAD = done).

---

## 1. Executive Summary

- **Form: nested separate repos, NOT a monorepo.** Each repo keeps its own `.git`, remote, CI,
  release-plz, tags, and crates.io identity; only its folder moves. This preserves the binding
  per-repo release standard (release-plz + `v[0-9]*` tags) and keeps the move reversible.
- **Root: `~/src/ronin-issen/components/<category>/<repo>`** — a plain folder (no `.git`, no
  `Cargo.toml`). The new root name eliminates the umbrella/repo name collision that forced the
  2026-07-04 plan's `.issen-umbrella` swap dance (`issen` the repo now nests cleanly at
  `components/orchestrator/issen`).
- **Path-dep strategy: the crux is already 95% solved.** The fn-1.0 migration registry-linked
  the fleet; a fresh scan (2026-07-18, all 251 dirs) finds **only 5 moving repos with
  cross-repo path deps** (~13 lines including forensic-vfs-mount's path-based
  `[patch.crates-io]`), most pointing at not-yet-published crates (`safe-read` and `forensic-vfs`
  are already published — see the §4.1 table). Fix: **generate** the
  authoritative rewrite list at execution time by TOML-parsing every manifest (all dep tables +
  `[patch]`), then script-rewrite to relpath-computed new paths (the uniform
  `components/<cat>/<repo>` depth makes it deterministic), and keep the standing policy of
  converting each to a registry dep when its target publishes.
- **Session history moves too — by exact-decode map, never prefix-match:** build a dry-run
  reviewed old→new map for `~/.claude/projects/` dirs (repo roots, verified worktrees,
  existence-verified subpaths; anything ambiguous is left in place and logged), rewrite
  `~/.claude.json` project keys atomically with zero live writers, and `git worktree repair`
  every moved repo.
- **No compatibility symlink layer** — the reference surface is small and enumerated (§5);
  rewrite it. Symlinks would resurrect the flat clutter and split future Claude sessions
  across two encoded paths.
- **Rollback:** every action is recorded in a manifest; rollback = replay inverse. Catastrophic
  fallback = the Gate-0 backup.

## 2. What changed since the prior plans (why this supersedes them)

| Prior-plan assumption | Reality now (verified 2026-07-18) |
|---|---|
| 2026-07-23: taxonomy had `compression/`, a `vfs/` folder, and `ad1-forensic` in `archive/` | Rulings 2026-07-28: `compression/` → **`codec/`**; the **`vfs/` folder is dissolved** — `forensic-vfs`/`-engine`/`-mount`/`4n6mount` in `filesystem/`, `disk-forensic` in `orchestration/`; **`ad1-forensic` is `container/`** (raw-disk logical container). Map is `.migration/map.tsv` (86 repos, 16 folders). |
| 2026-06-29: "consolidate into one monorepo, merge histories" | Overruled by user 2026-07-04: folder umbrella, repos stay separate. This design keeps that decision. The monorepo's real motivation — the fn-1.0 publish pain (~70 manual publishes, topological ordering, stale-caret traps, local-ahead strands) — is answered instead by **release-plz on every repo** (now the binding fleet standard), which delivers coordinated, reviewed releases without a history merge. |
| 2026-07-04: umbrella root = `~/src/issen` (name-collision swap via `.issen-umbrella`) | Root = `~/src/ronin-issen`; no collision, no swap step. |
| 2026-07-04: ~55 repos, 13 categories (mount/, history/, util/, no archive/encryption) | ~89 movable repos; taxonomy now has `archive`, `encryption`, `volume`, `state-history`, `tooling`; forensic-vfs split into contract (`forensic-vfs`) + `forensic-vfs-engine` + `forensic-vfs-mount`; FDE suite (bitlocker/luks/filevault/veracrypt) and ~10 new FS/parser repos exist. |
| 2026-07-04: "issen `[patch.crates-io]` absolute paths need repointing" | issen has **no active `[patch.crates-io]`** (removed at commit `18592d8`; only a comment remains in `issen-cli/Cargo.toml`). |
| Teammate brief: "~80 repos use `path = "..."` deps" | Measured: **5 moving repos** (+1 non-moving pair) have cross-repo path deps (~13 lines incl. one path-based `[patch.crates-io]`). Intra-repo workspace `path = "crates/…"` deps are unaffected by a folder move. |

## 3. Category taxonomy and the complete repo mapping

### 3.1 Category slugs

The umbrella taxonomy, as directory names (single-word slugs; `volume/partition` → `volume`,
`memory/paging` → `memory`, `state-history[H]` → `state-history`):

`knowledge · archive · container · volume · encryption · filesystem · memory · os-structure ·
log · parser · query · graph · state-history · orchestrator · tooling`

Two categories are **reserved, not created** (no empty dirs): `os-structure` (memf-windows /
memf-linux live inside the `memory-forensic` repo) and `query` (issen-remote-access /
velociraptor-parser live inside `issen`; RapidCollect is a standalone product, excluded). Create
them the day a standalone repo of that layer exists. A `_deprecated/` bucket sits at the umbrella
root — `~/src/ronin-issen/_deprecated/`, a sibling of `components/`, **not** inside it — for
repos kept only for reference.

### 3.2 Inclusion criteria (what moves)

A repo moves iff **all** of:
1. It is a SecurityRonin fleet repo (remote `SecurityRonin/*`, or local-only fleet work that
   gets a SecurityRonin remote at Gate 0: `archive-forensic` and `forensic-vfs-mount` —
   `bluetooth-forensic` already has its `SecurityRonin` remote);
2. It belongs to the forensic-fleet taxonomy — a layer crate, parser, analyzer, or a support
   library the fleet depends on (`safe-read`, `blazehash`, codecs, `timeglyph`, …);
3. It is not a standalone non-forensic product with its own identity.

Everything else stays flat at `~/src/` (see §3.4).

### 3.3 The complete mapping (89 repos)

All paths are `~/src/ronin-issen/components/<category>/<repo>`; the `_deprecated/` bucket sits at
the umbrella root, `~/src/ronin-issen/_deprecated/<repo>` — a sibling of `components/`, not inside it.

| Category | Repos |
|---|---|
| `knowledge/` (4) | forensicnomicon · forensic-vfs · jsonguard · safe-read |
| `archive/` (4) | archive-forensic † · zip-forensic · dar-forensic · cfb-forensic ‡ |
| `container/` (12) | ewf · ewf-forensic · vhd-forensic · vhdx-forensic · vmdk-forensic · qcow2-forensic · aff4-forensic · dmg-forensic · ad1-forensic · atx-forensic ⁑ · segb-forensic · livedisk-forensic |
| `volume/` (3) | mbr-partition-forensic · gpt-partition-forensic · apm-partition-forensic |
| `encryption/` (6) | bitlocker-forensic · luks-forensic · filevault-forensic · veracrypt-forensic · dpapi-forensic ‡ · elephant-diffuser |
| `filesystem/` (15) | ntfs-forensic · ext4fs-forensic · apfs-forensic · hfsplus-forensic · fat-forensic · xfs-forensic · zfs-forensic · btrfs-forensic · ufs-forensic · refs-forensic · udf-forensic · iso9660-forensic · 4n6mount · forensic-vfs-engine · forensic-vfs-mount † |
| `memory/` (1) | memory-forensic |
| `log/` (2) | winevt-forensic · journald-forensic |
| `parser/` (23) | browser-forensic · sqlite-forensic · srum-forensic · winreg-forensic · prefetch-forensic · lnk-forensic · shellitem · shimcache-forensic · amcache-forensic · bam-forensic · userassist-forensic · usb-forensic · peripheral-forensic · shellhist-forensic · trash-forensic · snss-forensic · leveldb-forensic · protobuf-forensic · ese-forensic · exec-pe-forensic · doc4n6 ⁑ · chat4n6 ⁑ · bluetooth-forensic |
| `graph/` (1) | git-forensic |
| `state-history/` (3) | state-history-forensic · snapshot-forensic · vsc-forensic |
| `orchestrator/` (3) | issen · disk-forensic · useract-forensic |
| `tooling/` (9) | blazehash · lzo · lzvn · xpress-huffman · timeglyph · blob-decoder · forensic-hashdb · name-variants · shrinkpath |
| `_deprecated/` (2) | tl ⁑ · usnjrnl-forensic ⁑ |

† local-only today — remote creation + push is a Gate-0 item; applies to `archive-forensic` and
`forensic-vfs-mount` only (`bluetooth-forensic` is now remote + published — verify-only).
⁑ placement resolved by the user on 2026-07-04 (chat4n6/doc4n6 → parser; atx → container;
tl + usnjrnl → deprecated) — carried over unchanged.
‡ judgment calls that diverge from or refine the 2026-07-04 manifest, flagged for review:
`dpapi-forensic` moves from parser → `encryption` (the new category is the better home for
Windows crypto-material extraction); `cfb-forensic` goes to `archive` alongside zip/dar (a
file-level structured container) rather than `container` (sector-stream decoders). Also:
`segb-forensic` stays `container` (per CLAUDE.md, segb-core is a CONTAINER crate);
`iso9660`/`udf` are `filesystem` (they navigate name→extent, not decode a stream);
`livedisk-forensic` is `container` (a live device is a raw byte-stream source);
`state-history-forensic` (the trait crate) anchors `state-history/` rather than `knowledge/` so
the [H] category is self-contained; `stem-branch` (in the 07-04 util list) is **excluded** —
h4x0r-owned and non-forensic.

Naming note: `knowledge`, `archive`, `filesystem` etc. contain both readers and analyzers of
their layer; the reader/analyzer split is *within* each repo (Pattern A), so the category never
needs a `-core`/`-forensic` distinction.

### 3.4 What does NOT move

- **Directory anchors:** `_archived/`, `_refs/`, `.attic/`, `sessions/`, `template/`.
- **Non-forensic SecurityRonin products** (own identity, no fleet coupling): alaya, clawpot,
  clawpot-console, clawscan, colligate, docx-mcp, doc-tooling misc (pdf2xlsx), ecb-penguin,
  general, homebrew-blazehash (Homebrew tap = distribution infra; tap paths are
  GitHub-referenced, never filesystem-referenced), leakguard, login-visualized,
  maintainable-vibe-coding, mpc-demo, nfchat, pipeguard, pipeguard-pro, RapidCollect,
  RapidProto, ronin-marketplace, shepherd, shepherd-pro, stackbudget, StrideMark,
  tls-handshake, web3-forensic (empty scaffold, no Cargo — revisit if it ever gets code),
  willitwork.
- **All h4x0r-remote and third-party clones** (nameback, inkblot, devblog, radare2, exiftool,
  APOLLO, bulk_extractor, ileapp, mac_apt, …) and every non-git working dir.
- Note: `pipeguard-pro → pipeguard` is the one cross-repo path dep among *non-moving* repos;
  both stay flat, so it is untouched by this migration.

## 4. Path-dependency migration (the crux) — chosen strategy

### 4.1 Ground truth (measured 2026-07-18, all 251 `~/src` dirs, every non-target `Cargo.toml`)

Cross-repo `path` deps that will break on move — the **complete** list:

| Consumer (moves to) | Path-dep targets (move to) | Registry-convertible today? |
|---|---|---|
| 4n6mount (`filesystem/`) | forensic-vfs-engine (`filesystem/`), archive-forensic (`archive/`), memory-forensic (`memory/`) | No — engine is `publish = false`; archive-forensic unpublished |
| disk-forensic (`orchestrator/`) | archive-forensic (`archive/`) | No — unpublished |
| forensic-vfs-mount (`filesystem/`) | forensic-vfs `crates/core` (`knowledge/`) — as a normal dep **and again in a path-based `[patch.crates-io]`** — plus ad1-forensic `core` (`container/`) | Partially — forensic-vfs is published, ad1's `vfs`/`testfix` features may be ahead of the registry |
| ad1-forensic (`container/`) | safe-read (`knowledge/`) | Yes — safe-read is published |
| livedisk-forensic (`container/`) | safe-read (`knowledge/`) | Yes |

Everything else in the fleet is **already registry-linked** (the fn-1.0 migration's doing), and
issen carries **no** `[patch.crates-io]`. Intra-repo workspace deps (`path = "crates/…"`,
`path = "core"`) are relative *within* a repo and survive any folder move untouched.

**This table is a snapshot, not the execution input.** The authoritative rewrite list is
**generated in Phase 1** by parsing every `Cargo.toml` in every moving repo (a TOML parse, not
a grep) across **all** path-carrying tables — `[dependencies]`, `[dev-dependencies]`,
`[build-dependencies]`, `[target.'cfg(…)'.dependencies]`, `[workspace.dependencies]`, and
`[patch.crates-io]` / `[patch.'<url>']` — resolving each `path` value against the manifest's
directory and flagging every resolution that escapes the repo root. Line count today lands at
~13; whatever the generator finds on execution day is the list. A post-rewrite gate re-runs the
generator and asserts **zero remaining escapes that resolve outside `ronin-issen`**.

### 4.2 Options weighed

- **(a) Convert everything to registry deps first.** Right long-term (it *is* fleet policy),
  wrong as a move-gate: 4 of the 8 lines point at unpublished/`publish = false` crates
  (archive-forensic is mid-build; the engine deliberately unpublished). Gating the folder move
  on publishing half-built crates inverts priorities.
- **(b) One top-level Cargo workspace at `ronin-issen/` (the 2026-06-29 monorepo).** Rejected.
  It would fight the binding per-repo standard: release-plz keys on each repo's own `main` and
  `Cargo.toml` graph; per-repo CI, MSRV floors, lockfiles, and the `v[0-9]*` / `<crate>-vX.Y.Z`
  tag scheme are all per-remote. A cross-git-repo workspace also breaks `cargo package`
  reproducibility and makes every repo's CI depend on siblings it can't check out. The monorepo's
  genuine upside — coordinated releases — is delivered instead by release-plz on every repo,
  **without** merging ~25 git histories (the 06-29 plan's own "most irreversible fleet change to
  date"). This is the same reasoning that killed the 06-29 monorepo, minus the history merge.
- **(c) `[patch.crates-io]` overlay.** Solves nothing here — patches can't cover unpublished
  crate names that were never on the registry, and a standing global patch file is exactly the
  hidden-state the fn-1.0 migration removed.
- **(d) Keep relative paths, choose uniform depth (+ optional symlinks).** The uniform depth is
  free in the chosen layout anyway; symlinks rejected (§5.3).

### 4.3 Decision

**(a)+(d) hybrid, without symlinks:** move everything, then **script-rewrite the generated
list** (§4.1 — ~13 lines today, `[patch]` included) to new relative paths computed with
`os.path.relpath` (never hand-typed) — deterministic because every repo sits at exactly
`components/<cat>/<repo>` (depth 2). Examples of the rewrite:

```
forensic-vfs-mount/Cargo.toml:
  "../forensic-vfs/crates/core"  →  "../../knowledge/forensic-vfs/crates/core"
                                     (both the dep entry AND the [patch.crates-io] entry)
  "../ad1-forensic/core"         →  "../../container/ad1-forensic/core"
4n6mount/Cargo.toml:
  "../archive-forensic"          →  "../../archive/archive-forensic"        (etc.)
ad1-forensic/core/Cargo.toml:
  "../../safe-read"              →  "../../../knowledge/safe-read"          (member: one more up)
```

Each rewrite is a one-line-per-dep commit in the consumer repo
(`build: repoint cross-repo path deps for ronin-issen layout`). `Cargo.lock` is untouched —
path deps record no source path in the lock.

**Standing policy (not a move-gate):** as each target publishes (safe-read already is;
archive-forensic and ad1's vfs feature when ready), convert its consumers to registry deps per
the Dependency Preference rule. The two safe-read lines can be converted to
`safe-read = "x.y"` *before* the move if preferred — that shrinks the rewrite to 6 lines.

### 4.4 Sequencing that keeps the tree building

Because links are registry-based, **build order is not move order** — nothing outside the 5
consumer repos can break. The window in which those 5 don't build is the minutes between their
`mv` and the rewrite commit. Order of operations:

1. Move all repos **leaves-first by taxonomy** (knowledge → archive/container/volume/encryption
   → filesystem/memory/log → parser/graph/state-history → tooling → orchestrator last) — not
   required for correctness, but it means at every instant a consumer's targets are already at
   their final path, so the rewrite for each consumer can land immediately after its own move.
2. After each of the 5 consumers moves: apply its path-dep rewrite → `cargo check` gate →
   commit.
3. All other repos: `cargo metadata` gate only (graph resolves; no compile needed for a folder
   move).

## 5. Session history, worktrees, and reference remediation

### 5.1 Claude session history (`~/.claude/projects/`)

Sessions live in path-encoded dirs: `/` → `-`; older Claude versions also encoded `.` → `-`,
newer keep the dot. Observed forms for one repo (all must be handled):

```
-Users-4n6h4x0r-src-<repo>                                   (main sessions + memory/MEMORY.md)
-Users-4n6h4x0r-src-<repo>-.claude-worktrees-<wt>            (new encoding; 69 dirs)
-Users-4n6h4x0r-src-<repo>--claude-worktrees-<wt>            (old encoding; 35 dirs)
-Users-4n6h4x0r-src-<repo>-.worktrees-<wt>                   (non-claude worktree layout; rare)
```

**Rename rule — exact-decode map, NEVER prefix-match.** The encoding is lossy (`/` and
sometimes `.` both become `-`), and the population is worse than repo-roots-plus-worktrees:
of 295 project dirs, 158 non-worktree `-src-` entries exist and many are **subpath-encoded**
sessions started inside a repo's subdirectory (e.g. `-src-…-tests-data`,
`-src-brave-browser-sessions-sessions`). Any prefix heuristic — including longest-repo-name
match — mis-folds those. So the rename is driven by a **fully materialized old→new map**,
built and dry-run-reviewed *before* any rename, in three tiers; a dir is renamed **only** if
it lands in a tier:

1. **Repo root**: the dir name equals `encode(/Users/4n6h4x0r/src/<repo>)` for a moving repo —
   exact string equality against the generated encoding, not a prefix test.
2. **Verified linked worktree**: the name equals `encode(<worktree-path>)` for a worktree path
   recorded in the Phase-1 `git worktree list --porcelain` snapshot of a moving repo — under
   **both** observed encodings of `/.claude/` (`--claude-worktrees-…` old, `-.claude-worktrees-…`
   new) plus the `-.worktrees-` layout.
3. **Existence-verified subpath**: the name decodes to a path that **exists on disk right now**
   (pre-move) strictly inside a moving repo. Decoding tests candidate `-`→`/` (and `-`→`.`)
   splits against the live filesystem; the decode must be **unique** — zero or ≥2 surviving
   candidates disqualifies the dir.

Anything not in a tier — orphan dirs of deleted repos (`-src-dar`, `-src-4n6`), ambiguous
decodes, non-moving repos — is **left in place and written to `.migration/session-skip.log`**
for optional manual remap; the script never guesses. Hard gates on the map itself, checked in
dry-run **before the first rename**: (a) injective — no two sources map to one target; (b) no
target name already exists; (c) every moving repo that has any session dir appears in the map;
(d) the full map is emitted for human review (`.migration/session-map.tsv`) and the apply step
refuses to run without a reviewed map file. **Abort, don't skip,** on any collision.

Per-repo auto-memory (`projects/<enc>/memory/MEMORY.md`) rides along with the dir rename —
nothing extra to do.

**Absolute paths that also need rewriting:**

- **`~/.claude.json` (316 KB) — MUST be rewritten, atomically, with zero live writers.** Its
  `.projects` object holds 108 entries, 89 under `~/src` — and that key set is **NOT the
  moving-repo set** (it includes subpath and non-moving-repo keys), so keys are mapped
  **exactly** from the migration map: a key is rewritten iff its path *is* a moving repo root
  *or is strictly inside one* (path-component-wise, never string-prefix — `…/src/ewf` must not
  capture `…/src/ewf-forensic`); every other key is untouched. Mechanic: (1) **hard-abort
  unless `pgrep -fl 'claude|codex'` is empty** — Claude Code rewrites this file continuously
  and a live writer loses the race; (2) timestamped backup; (3) `jq` key-rename via the exact
  map, plus the same exact-map replacement for embedded path values (`activeWorktreeSession`,
  history entries); (4) **atomic write** — emit to a temp file in the same directory, `fsync`,
  then `rename(2)` over `~/.claude.json`; (5) gates: `jq . >/dev/null` validity, total key
  count unchanged, per-map old-key-absent/new-key-present checks all pass.
- **Session `.jsonl` internals**: every message records `"cwd":"/Users/4n6h4x0r/src/<repo>"`.
  These are *historical metadata* — resume and history browsing key off the directory name, not
  the embedded cwd — so they are deliberately **left stale** (bulk-editing hundreds of MB of
  JSONL is the riskier operation). If a tool is ever found to re-derive project identity from
  embedded cwd, revisit.
- **Secondary stores, greped at execution time**: claude-mem's index, context-mode's knowledge
  base, and `~/.serena` each key on project paths; run the §5.4 grep across their data dirs and
  apply the same map where hits are found (all are caches — worst case is cold-start, not
  loss).

### 5.2 Git worktrees

Repos carry linked worktrees under `<repo>/.claude/worktrees/<wt>` (issen has 15; browser,
winevt, memory, mbr, trash, ewf-forensic, others a few). These move *with* the repo, but both
gitdir pointer files are **absolute** (`<wt>/.git` → `…/.git/worktrees/<wt>`, and the reverse
`gitdir` file), so every moved repo with worktrees is broken until repaired. **Prune is a
destructive operation and never runs first** — on a just-moved repo every linked worktree
looks broken, and a premature `prune` discards the admin data for worktrees that may hold
uncommitted work. Order and gates:

1. **Phase 1 (pre-move) snapshot, per linked worktree**: path, HEAD, branch, `git -C <wt>
   status --porcelain` output, and lock state (`git worktree list --porcelain` `locked`
   lines) recorded in `state-before.json`. **Abort the migration if any linked worktree is
   dirty or locked** (commit/stash/remove it, or waive explicitly) — a worktree carrying
   uncommitted work must never enter the move window unprotected.
2. **Post-move: `repair` FIRST**, never prune a worktree that hasn't been repaired or
   explicitly captured:
   ```
   git -C <newpath> worktree repair <moved-linked-path>…   # both directions fixed when
                                                           # main + linked moved together
   ```
3. **Then prune, narrowly**: `git worktree prune` runs only after `git worktree list` output
   is reconciled against the Phase-1 snapshot — every snapshot worktree must be either
   repaired-and-listed or affirmatively known-deleted. A worktree that is unreachable but was
   in the snapshot is an **abort**, not a prune.

Gate: `git worktree list` shows every snapshot worktree, with no `prunable`/`error`
annotations, and each repaired worktree's HEAD matches its snapshot.

### 5.3 Symlink layer — evaluated and REJECTED

A blanket `~/src/<repo> → ronin-issen/components/<cat>/<repo>` layer was considered to avoid
rewriting references. Rejected because it (1) resurrects the 89-entry flat clutter the reorg
exists to remove; (2) **splits future Claude sessions** — a session started via the symlink
path encodes the *old* path and lands in a new orphan project dir, silently forking history;
(3) creates dual identities for cargo/git tooling that canonicalizes paths (target-dir hashing,
worktree pointers); (4) hides stragglers forever — a broken reference that fails loud gets
fixed once; one that works through a symlink is permanent debt. The reference surface is small
and enumerated (below); rewrite it. (Fail-loud over paper-over.)

### 5.4 Absolute-path reference surface (enumerated) and rewrite plan

Measured hits for `4n6h4x0r/src` / `~/src/<repo>`:

| Surface | Extent | Action |
|---|---|---|
| Committed files in fleet repos | memory-forensic: 20 files; issen: 7 (docs/plans, corpus catalog); browser-forensic: 2; sampled others: 0 | Post-move fleet-wide `git grep` sweep; sed old→new; one commit per repo (`docs: repoint paths for ronin-issen layout`). Start the gitsign credential-cache first; wrap each commit in `timeout 60`, retry stragglers (bulk-commit discipline). |
| **Executable cross-repo fixture paths in source/tests** | Verified: `ewf` and `ewf-forensic` hard-code relative cross-repo corpus paths — `"../usnjrnl-forensic/tests/data/PC-MUS-001.E01"` (+ Szechuan, MaxPowers) in `tests/validate_*.rs` **and in `ewf/src/lib.rs:859`**. Others unknown until swept. | **Mandatory rewrite-or-waiver list, generated**: grep every moving repo's `*.rs` (and scripts) for string literals containing `../<any-moving-repo-name>` or `/Users/4n6h4x0r/src`; each hit is either rewritten to the new relpath or explicitly waived in `.migration/fixture-waivers.tsv`. Gate each affected repo with `cargo test --no-run` (compiles every test target; env-gated corpus tests still skip cleanly at run time when data is absent). Wrinkle to resolve at review: `usnjrnl-forensic` is mapped to `_deprecated/` yet its `tests/data/` hosts the shared E01 corpora ewf depends on — either relocate the corpora to their owning repo (test-data-belongs-to-its-parser rule) or accept `_deprecated/` in the rewritten paths. |
| `~/src/issen/CLAUDE.md` | references `~/src/*` siblings (`~/src/srum-forensic`, `~/src/blazehash`, corpus paths, Case-001 zips under `issen/tests/data`) | Rewrite in the same issen commit; corpus paths become `~/src/ronin-issen/components/orchestrator/issen/tests/data/…`. |
| `~/.claude/CLAUDE.personal.md` + `CLAUDE.core.md` | `~/src/issen/CLAUDE.md` pointers, `~/src/blazehash`, `~/src/nameback`, `~/src/devblog` | Rewrite the fleet ones (issen, blazehash); nameback/devblog don't move. (See also the fleet-value pointers in §5.5 — same edit pass.) |
| `~/.claude/projects/-…-issen/memory/MEMORY.md` + topic files | many `~/src/<repo>` mentions | Optional bulk sed (they're notes, not config); at minimum sed MEMORY.md index lines. |
| `~/.claude/skills/*` + `~/.claude/knowledge/*` | release skill, corpus-catalog references | Same sed sweep (see §5.5). |
| `~/.claude.json` | 89 project keys + embedded cwd values | §5.1 mechanic. |
| Corpus env vars (`WINREG_DC01_AMCACHE`, `SRUM_*`, `BDE_XTS_ORACLE`, `MEMF_SYMBOL_CACHE`, …) | **not** in `~/.zshrc`/`~/.zprofile`/`settings.json` (verified — zero hits); they are supplied per-invocation and documented in repo docs/validation files | Covered by the committed-file sweep; no shell-profile edits needed. |
| `*.code-workspace`, RTK config, gitsign | to be confirmed by the execution-day grep | `grep -rl '4n6h4x0r/src' ~/Library/Application\ Support/Code/User ~/.rtk* ~/.config 2>/dev/null` — rewrite hits with the same map. |
| `/tmp/*` extracted corpora | ephemeral by design | No action (re-extract per session as usual). |

The **single source of truth for all rewrites** is the migration map (old-path → new-path TSV)
generated from §3.3 and stored in `.migration/map.tsv`; every sed/jq consumes it.

### 5.5 Fleet-value pointers in `~/.claude` (the second reference wave)

Distinct from raw `~/src/<repo>` path hits: several config/skill files name `~/src/issen/CLAUDE.md`
(or `issen/tests/data/README.md`, `issen/docs/corpus-catalog.md`) as the **home of fleet
values/standards/secrets/repo-lists**. **Decision (2026-07-19, user):** `issen/CLAUDE.md` is
fleet-wide governance (~95% fleet law per the fleet/capstone classification), so it is **extracted
to `~/src/ronin-issen/CLAUDE.md`** — the fleet constitution — and these pointers repoint **there**
(not to `components/orchestrator/issen`). Exact file:line, verified 2026-07-19:

- `~/.claude/CLAUDE.personal.md` — `:21` (dependency-preference + crate-naming), `:33-34`
  (SecurityRonin fleet values / secrets / repo-lists — the canonical pointer), `:64`
  (test-data reference impl → `issen/tests/data/README.md`), `:88-90` (README SecurityRonin
  instantiation), `:102` (badge order).
- `~/.claude/skills/release.md` — `:619`, `:867`, `:1587` (Release & Distribution Standard home
  + "this skill is the mechanics" pointer).
- `~/.claude/skills/deterministic-coverage-fixtures.md` — `:29` (`issen/docs/corpus-catalog.md`
  as the fleet provenance index).
- **Second-wave danglers:** many per-crate `docs/validation.md` hardlink
  `issen/docs/corpus-catalog.md` as the machine index (e.g. apfs-forensic, apm-partition-forensic).
  These fall out of the §5.4 committed-file sweep once the corpus catalog's canonical path is
  fixed — sweep with the same map.

**Resolved (2026-07-19, user decision):** the fleet constitution is **lifted to
`~/src/ronin-issen/CLAUDE.md`** — the umbrella root, which every `components/<cat>/<repo>`
auto-inherits as a parent-dir `CLAUDE.md` once the folder move lands. `issen/CLAUDE.md`'s
fleet-law content moves there; issen (`components/orchestrator/issen`) keeps only a slim capstone
`CLAUDE.md` (its Strategic-Context framing + the Case-001 run-walkthrough) that `@import`s the
fleet constitution. `docs/corpus-catalog.md` and the `docs/validation.md` tier framing follow the
same lift. Because it is doc-only, this extraction can precede the gated folder move; the
`~/.claude` pointer repoint above lands in the same change. See §7.9.

## 6. Execution runbook (GATED on the §0 backup checklist)

Design goals: **scripted, idempotent, resumable, verifiable**. One driver script
(`fleet-reorg.sh`, to be written at execution time from this spec) that consumes
`.migration/map.tsv` and appends every completed action to `.migration/journal.jsonl`
(`{step, repo, from, to, sha_before, status}`). Re-running skips journaled steps — idempotent
and resumable by construction. `set -euo pipefail`; stop on first red.

### 6.0 Phase order

```
Phase 0  Gate check (backup checklist §0; abort if any box unchecked)
Phase 1  Freeze + snapshot state
Phase 2  Move repos (mv) + worktree repair            [pure renames]
Phase 3  Path-dep rewrite (5 repos) + build gates
Phase 4  Session-history migration (~/.claude)
Phase 5  Reference sweep (committed files + global config)
Phase 6  Fleet-wide final gate
```

### 6.1 Phase 1 — freeze + snapshot

- Generate `.migration/map.tsv` from §3.3; assert every source dir exists, no target exists.
  (`ronin-issen` itself already exists as a bare skeleton — assert it holds only
  `components/` + the two staged `_deprecated` repos and no target-collision names, then
  reconcile the §0.5 divergences into the map.)
- Repo-state sweep over all 89 repos. Per repo, gate on **all five** (explicit written waiver
  is the only exception): (a) clean — `git status --porcelain` empty; (b) **ahead = 0**;
  (c) **behind = 0**; (d) **not diverged** — both from
  `git rev-list --left-right --count @{u}...HEAD`; (e) **expected branch** — `HEAD` is on the
  recorded default branch, not detached. Behind/diverged matter as much as ahead: a repo
  hundreds of commits behind (verified: browser-forensic is **behind 379** today) moved
  mid-divergence turns the post-move reference-sweep commits into an accidental merge problem.
  Record per-repo `HEAD` sha, branch, `@{u}` sha, and `git worktree list --porcelain` (plus
  the per-worktree dirty/lock snapshot, §5.2) into `.migration/state-before.json`.
  (Snapshot 2026-07-18 for scale: ~25 fleet repos dirty or ahead — issen ahead=11,
  ewf dirty=462 + ahead=1, winevt-forensic dirty=541, git-forensic dirty=362 (verify whether
  those large counts are untracked test/fuzz artifacts to gitignore or real work), 4n6mount
  dirty+ahead=8, disk-forensic ahead=5, forensic-vfs/-engine ahead=2, zip-forensic ahead=7,
  veracrypt ahead=5, livedisk ahead=3 — plus browser-forensic behind=379. All must be landed,
  pulled, or waived at Gate 0.)
- Generate the authoritative artifacts the later phases consume: `.migration/map.tsv`
  (repo moves), the **path-dep rewrite list** (§4.1 TOML-parse generator), the
  **fixture-literal list** (§5.4), and the **session-dir map** (§5.1 three-tier decode,
  dry-run output for human review).

### 6.2 Phase 2 — move (per repo; order = §4.4)

```
mv ~/src/<repo> ~/src/ronin-issen/components/<cat>/<repo>     # same volume: atomic rename
git -C <new> rev-parse HEAD          == recorded sha          # .git arrived intact
git -C <new> status --porcelain      == recorded dirty set
git -C <new> worktree repair <moved-linked…>   # §5.2 — repair FIRST; prune only after
git -C <new> worktree list                     #   snapshot reconciliation; gate: no
                                               #   error/prunable, HEADs match snapshot
```

Journal the step. Idempotency: if source is gone and dest exists with the recorded HEAD, mark
done and continue. (The two already-staged `_deprecated` repos — `ewf`, `usnjrnl-forensic` — are
handled here: reconcile per §0.5 first, i.e. move `ewf` to its §3.3 home unless a fold-and-retire
decision is confirmed, relocate `_deprecated/` to the root, then journal as done.)

### 6.3 Phase 3 — path-dep rewrite

Consume the Phase-1 **generated** rewrite list (§4.1 — never the prose table): for each entry
compute the new relpath (`os.path.relpath`), patch the exact `path = "…"` string (including
`[patch.crates-io]` entries), then gate `cargo check` (workspace root), re-run the generator
to assert zero remaining out-of-tree escapes, and commit — **locally only; no push (§6.7)**.
Note: expect cold(ish) rebuilds fleet-wide afterwards — cargo dep-info records absolute paths,
so first builds at the new location recompile; harmless, just slow once.

### 6.4 Phase 4 — session-history migration

0. **Hard-abort unless `pgrep -fl 'claude|codex'` is empty** — re-checked here, not only at
   Gate 0 (hours may have passed).
1. `cp ~/.claude.json ~/.claude.json.bak-<ts>`; `tar -C ~/.claude -czf ~/.claude-projects-<ts>.tgz projects` (belt-and-braces beyond Gate 0).
2. **Dry-run**: emit the three-tier session map (§5.1) to `.migration/session-map.tsv` +
   `session-skip.log`; run the injectivity/no-target-exists/coverage gates; stop for human
   review of the map. The apply step refuses to run without the reviewed map.
3. Apply renames strictly from the reviewed map; journal each; idempotent (skip journaled).
4. Rewrite `~/.claude.json` per §5.1 (exact map, atomic temp+fsync+rename, key-count gates).
5. Verify: `claude --resume` (or `claude -c`) inside two moved repos (e.g. issen,
   browser-forensic) shows prior session history; `ls ~/.claude/projects | grep -c
   ronin-issen` equals the map's target count; zero map-source dirs remain; `session-skip.log`
   reviewed and accepted.

### 6.5 Phase 5 — reference sweep

Run the §5.4 table top-to-bottom (and the §5.5 fleet-value pointers), driven by `map.tsv` —
including the **executable fixture-literal list** (every hit rewritten or waived; affected repos
gated with `cargo test --no-run`). All commits stay **local** (§6.7). Final grep gate: for every
moved repo, `grep -rl "/Users/4n6h4x0r/src/<repo>" ~/src/ronin-issen ~/.claude ~/.claude.json`
returns only (a) session-jsonl historical cwd lines (accepted stale) and (b)
`_archived`/notes explicitly waived.

### 6.6 Phase 6 — fleet-wide final gate

- `cargo metadata` green in every Rust repo (cheap, catches any missed path dep).
- `cargo check` (or build) green in the 5 rewritten repos + the three orchestrators
  (issen, disk-forensic, 4n6mount).
- `issen --version` runs; optional heavy gate: the Case-001 four-source end-to-end
  (`issen <4 sources> -o /tmp/reorg-check.duckdb`) per the convergence-validation standard.
- Spot-check one release surface is untouched: `git -C …/container/ewf-forensic log -1` and its
  GitHub remote/CI still green on next push (folder moves are invisible to GitHub).
- Flip this document's status to "EXECUTED <date>" (plan-lifecycle law: the tree holds the
  conclusion). This edit lands wherever `REORG.md` is versioned (§7.8) — if the umbrella root gets
  a docs-only `.git`, commit it there, not in an issen commit. The three prior plans this file
  consolidated were removed from `issen/docs/plans/` as part of the change that created this file
  (rev 2 committed to issen git first, then all three `git rm`'d — recoverable via git history),
  so no further plan-doc deletion is needed here.
- **Only after every gate above is green: push.** Push the Phase-3/5 commits repo by repo
  (gitsign cache + `timeout 60` + straggler retry), then lift the release-automation freeze.
  This is the rollback-boundary crossing (§6.7) — deliberate, last, and all-at-once.

### 6.7 ROLLBACK — with an explicit boundary

**The rollback boundary is the Phase-6 push step.** Until then, every migration commit exists
only locally, no tag has been cut, no release-plz PR has merged, and nothing has been
published — that freeze (a §0 checklist box) is what makes rollback a true inverse. The two
regimes:

**Before the boundary (nothing pushed) — inverse replay:**

1. **Stop**; do not partially "fix forward" a broken half-state — decide roll back vs resume
   (the journal makes resume equally safe).
2. Replay `journal.jsonl` in reverse: `mv` each repo back to `~/src/<repo>`; rename each
   session dir back; `git worktree repair` again at the old locations.
3. Restore `~/.claude.json` from the timestamped backup (or reverse-apply the map).
4. `git reset --hard` each repo to its journaled pre-migration `HEAD` sha (safe: the Phase-3/5
   commits are unpushed by construction; the sha is in `state-before.json`).
5. Remove **only migration-created content** from `~/src/ronin-issen` — the moved repos under
   `components/<cat>/` — after asserting each is back at its flat `~/src/<repo>` home. **Do NOT
   `rm -rf ~/src/ronin-issen`**: the umbrella folder pre-existed this migration and holds this
   authoritative `REORG.md` (and any `.migration/` record, plus the two pre-staged `_deprecated`
   repos). The folder is fully removed only by a deliberate, separate decision to abandon the
   umbrella.
6. Catastrophic fallback (disk/manifest corruption): restore `~/src` + `~/.claude` from the
   Gate-0 backup. This is why the backup is a hard gate, not hygiene.

**After the boundary (commits pushed, freeze lifted) — forward-fix only.** A push cannot be
un-happened (remotes, CI, possible release automation have seen it); reverse replay of folder
moves would now diverge local from remote-visible reality. Any post-push defect is fixed
forward with new commits (`git revert` for content, a follow-up sweep for missed references).
A registry publish, if any slipped through, is irreversible by definition (yank-only) — which
is exactly why the freeze and the push-last rule exist.

## 7. Open risks / not fully resolved

1. **Large dirty counts** in ewf (462), winevt-forensic (541), git-forensic (362) are almost
   certainly untracked corpora/fuzz artifacts, but that is unverified — triage before Gate 0
   (gitignore or commit; never move an ambiguous tree unexamined).
2. **claude-mem / context-mode / serena stores**: path-keyed caches; the design greps and
   remaps at execution but their internal formats weren't audited. Worst case: cold-start of
   auxiliary memory, no data loss (session history proper is §5.1).
3. **Encoded-name decode residue**: the three-tier exact-decode map (§5.1) refuses ambiguous
   dirs rather than guessing, so some subpath-encoded session dirs will legitimately land in
   `session-skip.log` and keep their old names (their history stays browsable, just not
   co-located). Accepted; the log makes the residue visible for manual remap.
4. **ewf vs ewf-forensic duplication**: both are active repos (commits this week in each).
   Both move to `container/`; whether `ewf` should fold into `ewf-forensic` is a separate,
   later decision — out of scope here, but it is the likely reason `ewf` is staged under
   `_deprecated/` on disk today (§0.5). Resolve the fold-or-keep question before Phase 2 so
   `ewf`'s destination is unambiguous. Related: both hard-code fixture paths into
   `usnjrnl-forensic/tests/data/` (§5.4) — the corpora-home decision (relocate vs accept
   `_deprecated/` paths) must be made at the fixture-rewrite review.
5. **`web3-forensic`** (empty scaffold) and any GitHub-only fleet repos with no local clone are
   unmapped; execution day runs `gh repo list SecurityRonin` vs the map and either clones
   directly into the new tree or records the exclusion.
6. **Claude Code version behavior**: the `-.claude-` vs `--claude-` encoding split shows the
   encoder has changed before; if the installed version at execution time encodes differently
   again, re-derive the target names by *observing* a fresh throwaway session in the new tree
   before renaming (verify, don't assume).
7. **Stale embedded `cwd` in session JSONL** is accepted debt (see §5.1); revisit only if a
   consumer of that field surfaces.
8. **This plan lives in an unversioned folder.** `~/src/ronin-issen/` has no `.git`, so
   `REORG.md` is not itself version-controlled (the three source plans' history remains in
   issen). Recommend giving the umbrella root a **docs-only `.git`** that tracks `REORG.md` +
   `.migration/` tooling and `.gitignore`s `components/*` (each already its own repo) — this
   versions the migration record without making the umbrella a monorepo/workspace (the thing
   §1/§4.2 rejected). Decide before execution; until then, issen's git history is the archive of
   record for this plan's lineage.
9. **Governance home — RESOLVED (2026-07-19, user decision).** The fleet constitution is
   extracted from issen to **`~/src/ronin-issen/CLAUDE.md`** (umbrella root; auto-inherited by
   every component post-move via parent-dir `CLAUDE.md` loading). Scope of the lift: the fleet-law
   sections of `issen/CLAUDE.md` (~95% per the fleet/capstone classification),
   `docs/corpus-catalog.md`, and the T1/T2/T3 validation-tier framing (candidate for a dedicated
   `ronin-issen` validation standard + fleet-wide validation report). issen retains a slim capstone
   `CLAUDE.md` that `@import`s the fleet constitution plus its own Strategic-Context/Case-001
   specifics. Doc-only, so it can precede the gated folder move; the §5.5 pointer repoint lands in
   the same change. This is the immediate governance follow-up.
10. **Carried-over follow-up (non-reorg), preserved from the deleted 07-04 manifest.** The `vhd`
    reader was to be split into `vhd-core` (`[lib] vhd`) + a `vhd-forensic` analyzer; the split is
    **done on disk** (`~/src/vhd-forensic` is now that workspace). Open: whether crates.io still
    carries only bare `vhd 0.1.1` (publish state unverified this session — `curl` unavailable in
    shell). If unpublished, cut `vhd-core`/`vhd-forensic` (needs the crates.io token). Tracked here
    only so deleting the source plan does not drop it; relocate to the `vhd-forensic` tracker when
    convenient.
