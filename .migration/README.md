# Fleet reorg — execution kit

Turnkey tooling for REORG.md. **The reorg cannot run from inside a live Claude
session** — Phase 4 renames the current session's `~/.claude/projects/` dir and
rewrites `~/.claude.json` while Claude writes them, and Phase 2 moves `~/src/issen`
out from under the session. `fleet-reorg.sh`'s Phase-0 gate hard-aborts if any
`claude`/`codex` process is running, so it is safe by construction — but it means
**you run it from a clean shell (Terminal.app, no Claude/Codex open).**

## Files

- `map.tsv` — repo → destination (REORG.md §3.3). Source of truth for the moves.
- `reorg_lib.py` — path-dep rewrites (§4.1) + session-history three-tier decode (§5.1). Pure/reviewable.
- `rewrites.tsv` — **generated** path-dep rewrite list (16 lines, 6 consumer repos). The real Phase-3 input.
- `session-map.dryrun.tsv` — **generated** old→new session-dir map (34 repo-root dirs). Review this.
- `session-skip.log` — dirs deliberately left in place (orphans, ambiguous subpaths, non-moving repos).
- `../fleet-reorg.sh` — the driver (phases 0–6, journaled, idempotent, resumable).

## Procedure

1. **Backup (the hard gate, §0).** Full verified backup of `~/src` and `~/.claude/`
   + `~/.claude.json` (Time Machine or rsync to external storage). Restore-test one
   repo to `/tmp` (`git fsck && cargo check`) and open one restored `projects/*/…jsonl`.
   Then arm the gate:  `touch .migration/BACKUP-VERIFIED`
2. **Land/pull/push or waive every dirty-or-ahead repo** (Phase 1 writes
   `state-before.json` and refuses to proceed otherwise; `touch .migration/WAIVE-DIRTY`
   only after a conscious decision).
3. **Quit Claude and Codex completely** (`pgrep -fl 'claude|codex'` must be empty).
   Open a plain Terminal.
4. From `~/src/ronin-issen`, run **one phase at a time**, reviewing between:
   ```
   ./fleet-reorg.sh gate      # confirms clean environment
   ./fleet-reorg.sh phase1    # snapshot + regenerate rewrites.tsv + session dry-run
   #   → REVIEW session-map.dryrun.tsv, then: cp session-map.dryrun.tsv session-map.tsv
   ./fleet-reorg.sh phase2    # move repos + worktree repair
   ./fleet-reorg.sh phase3    # path-dep rewrites + cargo check (LOCAL commits)
   ./fleet-reorg.sh phase4    # session-history migration (needs session-map.tsv)
   ./fleet-reorg.sh phase5    # reference sweep (LOCAL commits)
   ./fleet-reorg.sh phase6    # final gate (stops BEFORE the push)
   ./fleet-reorg.sh push-now  # crosses the rollback boundary — pushes everything
   ```
5. **Rollback (§6.7):** before `push-now`, every change is local — replay
   `journal.jsonl` in reverse (`mv` repos back, restore `~/.claude.json.bak-*`,
   `git reset --hard` to `state-before.json` HEADs). After `push-now`, forward-fix only.

## Still manual (by design)

- `~/.claude/CLAUDE.personal.md`, `skills/*`, `knowledge/*` fleet-value pointers
  (§5.5) — sed with `map.tsv` in the same clean session.
- The §0.5 reconciliation: `components/_deprecated/{ewf,usnjrnl-forensic}` — move
  `ewf` to `container/ewf` (live repo) and relocate `_deprecated/` to the umbrella
  root; Phase 2 flags this.
- Governance lift (§7.9) is already done: `ronin-issen/CLAUDE.md` is the constitution.
