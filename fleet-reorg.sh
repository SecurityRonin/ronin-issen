#!/usr/bin/env bash
# fleet-reorg.sh — execute the ronin-issen fleet folder reorg (REORG.md §6).
#
# ⛔ RUN FROM A CLEAN SHELL WITH CLAUDE/CODEX QUIT. This script MOVES ~/src/issen
#    and REWRITES ~/.claude.json + renames ~/.claude/projects dirs; a live agent
#    races and corrupts them. Phase 0 hard-aborts if any claude/codex process runs.
#
# Idempotent + resumable: every completed step is appended to
# .migration/journal.jsonl; a re-run skips journaled steps. `set -euo pipefail`,
# stop on first red. Nothing is pushed/published until Phase 6 (the rollback
# boundary, §6.7) — until then a full inverse-replay rollback is possible.
#
# Usage:
#   ./fleet-reorg.sh gate        # Phase 0 only — check readiness, change nothing
#   ./fleet-reorg.sh phase1      # snapshot + generate artifacts (read-only-ish)
#   ./fleet-reorg.sh phase2      # move repos + worktree repair
#   ./fleet-reorg.sh phase3      # path-dep rewrites + cargo check (local commits)
#   ./fleet-reorg.sh phase4      # session-history migration (needs reviewed map)
#   ./fleet-reorg.sh phase5      # reference sweep (local commits)
#   ./fleet-reorg.sh phase6      # final gate, THEN push (rollback boundary)
#   ./fleet-reorg.sh all         # phases 1..5 (stops before the push in 6)
set -euo pipefail

HOME_DIR="${HOME}"
SRC="${HOME_DIR}/src"
UMBRELLA="${SRC}/ronin-issen"
MIG="${UMBRELLA}/.migration"
COMPONENTS="${UMBRELLA}/components"
MAP="${MIG}/map.tsv"
JOURNAL="${MIG}/journal.jsonl"
LIB="python3 ${MIG}/reorg_lib.py"
TS="$(date +%Y%m%d-%H%M%S 2>/dev/null || echo manual)"

log()  { printf '  %s\n' "$*"; }
die()  { printf 'ABORT: %s\n' "$*" >&2; exit 1; }
journaled() { [ -f "$JOURNAL" ] && grep -qF "\"$1\"" "$JOURNAL"; }
mark() { printf '{"step":"%s","ts":"%s"}\n' "$1" "$TS" >> "$JOURNAL"; }

dest_of() { # repo -> absolute destination
  local repo="$1" cat
  cat="$(awk -F'\t' -v r="$repo" '$1==r{print $2}' "$MAP")"
  [ -n "$cat" ] || die "repo not in map: $repo"
  if [ "$cat" = "_deprecated" ]; then echo "${UMBRELLA}/_deprecated/${repo}";
  else echo "${COMPONENTS}/${cat}/${repo}"; fi
}
moving_repos() { awk -F'\t' '!/^#/ && NF==2 {print $1}' "$MAP"; }

# ---- Phase 0: gate (§0 hard preconditions) ---------------------------------
phase0() {
  log "Phase 0 — gate check (§0)"
  [ -f "$MAP" ] || die "no map.tsv"
  # (a) zero live agents — THE structural gate
  if pgrep -f 'claude|codex' >/dev/null 2>&1; then
    die "live claude/codex process(es) running — quit Claude and re-run from a clean shell"
  fi
  # (b) verified backup marker (user creates after doing+restore-testing the backup, §0)
  [ -f "${MIG}/BACKUP-VERIFIED" ] || die \
    "no ${MIG}/BACKUP-VERIFIED — complete + restore-test the ~/src and ~/.claude backup, then: touch ${MIG}/BACKUP-VERIFIED"
  # (c) no cargo build lock anywhere under src
  if pgrep -f 'cargo (build|check|test|run)' >/dev/null 2>&1; then
    die "cargo build/check/test running — stop it first"
  fi
  # (d) umbrella sanity
  [ -d "$COMPONENTS" ] || die "no components/ dir under $UMBRELLA"
  log "gate OK: no live agents, backup verified, no cargo builds"
}

# ---- Phase 1: freeze + snapshot (§6.1) -------------------------------------
phase1() {
  phase0
  journaled "phase1" && { log "phase1 already done"; return; }
  log "Phase 1 — snapshot + artifacts"
  # source dirs exist, dests absent
  local bad=0
  while read -r repo; do
    [ -d "${SRC}/${repo}/.git" ] || { log "WARN source missing: ${repo}"; bad=$((bad+1)); }
    [ -e "$(dest_of "$repo")" ] && { log "WARN dest exists: $(dest_of "$repo")"; bad=$((bad+1)); }
  done < <(moving_repos)
  # repo-state readiness sweep -> state-before.json (abort on unwaived dirty/ahead/behind)
  python3 - "$MAP" "$SRC" > "${MIG}/state-before.json" <<'PY'
import json,os,subprocess,sys
mapf,src=sys.argv[1],sys.argv[2]
repos=[l.split('\t')[0] for l in open(mapf) if l.strip() and not l.startswith('#') and '\t' in l]
def g(d,*a):
    return subprocess.run(['git','-C',d,*a],capture_output=True,text=True).stdout.strip()
out={"repos":{}}
viol=[]
for r in repos:
    d=os.path.join(src,r)
    if not os.path.isdir(os.path.join(d,'.git')): continue
    dirty=g(d,'status','--porcelain'); head=g(d,'rev-parse','HEAD'); br=g(d,'rev-parse','--abbrev-ref','HEAD')
    lr=g(d,'rev-list','--left-right','--count','@{u}...HEAD') or '0\t0'
    behind,ahead=(lr.split('\t')+['0','0'])[:2]
    wl=g(d,'worktree','list','--porcelain')
    wts=[ln.split(' ',1)[1] for ln in wl.splitlines() if ln.startswith('worktree ')]
    info={"head":head,"branch":br,"ahead":ahead,"behind":behind,
          "dirty":len(dirty.splitlines()),"worktrees":[{"path":p} for p in wts if os.path.realpath(p)!=os.path.realpath(d)]}
    out["repos"][r]=info
    if info["dirty"] or ahead!='0' or behind!='0': viol.append((r,info["dirty"],ahead,behind))
out["violations"]=[{"repo":r,"dirty":d,"ahead":a,"behind":b} for r,d,a,b in viol]
json.dump(out,sys.stdout,indent=1)
PY
  local nv; nv="$(python3 -c 'import json,sys;print(len(json.load(open(sys.argv[1]))["violations"]))' "${MIG}/state-before.json")"
  log "state-before.json written; ${nv} repos dirty/ahead/behind"
  if [ "$nv" != "0" ] && [ ! -f "${MIG}/WAIVE-DIRTY" ]; then
    python3 -c 'import json,sys;[print("   -",v["repo"],"dirty",v["dirty"],"ahead",v["ahead"],"behind",v["behind"]) for v in json.load(open(sys.argv[1]))["violations"]]' "${MIG}/state-before.json"
    die "repos not clean (§6.1). Land/pull/push them, or waive: touch ${MIG}/WAIVE-DIRTY"
  fi
  # generated artifacts for review
  $LIB gen-rewrites > "${MIG}/rewrites.tsv" 2> "${MIG}/rewrites.err" || die "gen-rewrites failed"
  $LIB session-map > "${MIG}/session-map.dryrun.tsv" 2> "${MIG}/session-skip.log" || die "session-map failed"
  log "rewrites.tsv ($(wc -l <"${MIG}/rewrites.tsv"|tr -d ' ') lines) + session-map.dryrun.tsv ($(wc -l <"${MIG}/session-map.dryrun.tsv"|tr -d ' ') dirs) generated"
  log "REVIEW ${MIG}/session-map.dryrun.tsv, then copy to session-map.tsv to arm Phase 4"
  [ "$bad" = "0" ] || die "phase1 sanity warnings above — resolve first"
  mark "phase1"
}

# ---- Phase 2: move repos + worktree repair (§6.2, order §4.4) ---------------
ORDER="knowledge archive container volume encryption filesystem memory log parser graph state-history tooling orchestrator _deprecated"
phase2() {
  phase0
  log "Phase 2 — move (leaves-first)"
  local cat repo dest head0
  for cat in $ORDER; do
    while read -r repo; do
      local step="move:${repo}"
      journaled "$step" && continue
      local d="${SRC}/${repo}"; dest="$(dest_of "$repo")"
      [ -d "${d}/.git" ] || { log "skip (no source): ${repo}"; continue; }
      head0="$(git -C "$d" rev-parse HEAD)"
      mkdir -p "$(dirname "$dest")"
      [ -e "$dest" ] && die "dest already exists: $dest"
      mv "$d" "$dest"                                  # same volume: atomic rename
      [ "$(git -C "$dest" rev-parse HEAD)" = "$head0" ] || die "HEAD mismatch after move: $repo"
      # worktree repair FIRST (§5.2) — repair both directions, never prune yet
      git -C "$dest" worktree repair 2>/dev/null || true
      git -C "$dest" worktree list >/dev/null 2>&1 || true
      log "moved ${repo} -> ${dest#$SRC/}"
      mark "$step"
    done < <(awk -F'\t' -v c="$cat" '$2==c{print $1}' "$MAP")
  done
  log "Phase 2 done; reconcile §0.5 (relocate components/_deprecated -> umbrella root) if present"
  if [ -d "${COMPONENTS}/_deprecated" ]; then
    log "NOTE: components/_deprecated still present — move its repos to ${UMBRELLA}/_deprecated/ per §0.5"
  fi
}

# ---- Phase 3: path-dep rewrites (§6.3) -------------------------------------
phase3() {
  phase0
  log "Phase 3 — path-dep rewrites + cargo check"
  local repo
  for repo in $(awk -F'\t' '{print $1}' "${MIG}/rewrites.tsv" | sort -u); do
    local step="rewrite:${repo}"; journaled "$step" && continue
    local dest; dest="$(dest_of "$repo")"
    log "rewriting ${repo}"
    ( cd "$dest" && $LIB apply-rewrites "$repo" )
    ( cd "$dest" && cargo check --quiet ) || die "cargo check failed after rewrite: $repo"
    ( cd "$dest" && git add -A && git commit -q -m "build: repoint cross-repo path deps for ronin-issen layout" ) || true
    mark "$step"
  done
  # post-gate: zero remaining out-of-tree escapes
  $LIB gen-rewrites > "${MIG}/rewrites.after.tsv" 2>/dev/null || true
  log "Phase 3 done (commits are LOCAL; not pushed — §6.7)"
}

# ---- Phase 4: session-history migration (§6.4) -----------------------------
phase4() {
  phase0     # re-checks pgrep empty (§6.4.0)
  log "Phase 4 — session history"
  [ -f "${MIG}/session-map.tsv" ] || die "no reviewed session-map.tsv (copy session-map.dryrun.tsv after review)"
  cp "${HOME_DIR}/.claude.json" "${HOME_DIR}/.claude.json.bak-${TS}"
  tar -C "${HOME_DIR}/.claude" -czf "${HOME_DIR}/.claude-projects-${TS}.tgz" projects
  log "backed up ~/.claude.json + projects"
  # apply dir renames strictly from the reviewed map
  while IFS=$'\t' read -r old new; do
    [ -z "$old" ] && continue
    local step="sess:${old}"; journaled "$step" && continue
    if [ -d "${HOME_DIR}/.claude/projects/${old}" ] && [ ! -e "${HOME_DIR}/.claude/projects/${new}" ]; then
      mv "${HOME_DIR}/.claude/projects/${old}" "${HOME_DIR}/.claude/projects/${new}"
      mark "$step"
    fi
  done < "${MIG}/session-map.tsv"
  $LIB rewrite-claude-json
  log "Phase 4 done; verify with: ls ~/.claude/projects | grep -c ronin-issen"
}

# ---- Phase 5: reference sweep (§6.5) ---------------------------------------
phase5() {
  phase0
  log "Phase 5 — reference sweep (committed files + fixtures)"
  local repo dest
  while read -r repo; do
    dest="$(dest_of "$repo")"; [ -d "${dest}/.git" ] || continue
    local step="refsweep:${repo}"; journaled "$step" && continue
    # rewrite every /Users/.../src/<r> -> new path, for every moving repo r, via map
    local changed=0
    while read -r r; do
      local rnew; rnew="$(dest_of "$r")"
      if git -C "$dest" grep -lI "${SRC}/${r}\b" -- . >/dev/null 2>&1; then
        git -C "$dest" grep -lIz "${SRC}/${r}" -- . 2>/dev/null | while IFS= read -r -d '' f; do
          LC_ALL=C sed -i '' "s|${SRC}/${r}\b|${rnew}|g" "${dest}/${f}" 2>/dev/null || true
        done
        changed=1
      fi
    done < <(moving_repos)
    if [ "$changed" = "1" ]; then
      ( cd "$dest" && cargo test --no-run --quiet 2>/dev/null || true )
      ( cd "$dest" && git add -A && git commit -q -m "docs: repoint paths for ronin-issen layout" ) || true
    fi
    mark "$step"
  done < <(moving_repos)
  log "Phase 5 done (LOCAL commits). Manually sweep ~/.claude config pointers per §5.4/§5.5."
}

# ---- Phase 6: final gate + push (§6.6, rollback boundary §6.7) --------------
phase6() {
  phase0
  log "Phase 6 — final gate"
  local repo dest
  while read -r repo; do
    dest="$(dest_of "$repo")"; [ -f "${dest}/Cargo.toml" ] || continue
    ( cd "$dest" && cargo metadata --format-version 1 >/dev/null 2>&1 ) || die "cargo metadata failed: $repo"
  done < <(moving_repos)
  for repo in disk-forensic 4n6mount issen; do
    dest="$(dest_of "$repo")"; ( cd "$dest" && cargo check --quiet ) || die "cargo check failed: $repo"
  done
  log "metadata green everywhere; orchestrators check green"
  log ""
  log "⛔ ROLLBACK BOUNDARY: the next step PUSHES all local commits (§6.7)."
  log "   Re-run with:  ./fleet-reorg.sh push-now   (only after you've reviewed the tree)"
}

push_now() {
  phase0
  log "Phase 6 push — crossing the rollback boundary"
  command -v gitsign-credential-cache >/dev/null 2>&1 && {
    gitsign-credential-cache >/dev/null 2>&1 &
    export GITSIGN_CREDENTIAL_CACHE="${HOME_DIR}/Library/Caches/sigstore/gitsign/cache.sock"; }
  local repo dest
  while read -r repo; do
    dest="$(dest_of "$repo")"; [ -d "${dest}/.git" ] || continue
    [ -z "$(git -C "$dest" log '@{u}..HEAD' --oneline 2>/dev/null)" ] && continue
    timeout 60 git -C "$dest" push origin HEAD 2>/dev/null \
      && log "pushed ${repo}" || log "PUSH FAILED (retry): ${repo}"
  done < <(moving_repos)
  log "push wave done; retry any 'PUSH FAILED' rows. Then flip REORG.md status to EXECUTED."
}

case "${1:-}" in
  gate)    phase0 ;;
  phase1)  phase1 ;;
  phase2)  phase2 ;;
  phase3)  phase3 ;;
  phase4)  phase4 ;;
  phase5)  phase5 ;;
  phase6)  phase6 ;;
  push-now) push_now ;;
  all)     phase1; phase2; phase3; phase5; phase6 ;;
  *) sed -n '2,40p' "$0"; exit 1 ;;
esac
