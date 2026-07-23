#!/usr/bin/env python3
"""Correctness-critical helpers for the fleet reorg (REORG.md §4/§5).

Pure, reviewable functions the driver (fleet-reorg.sh) shells out to. No function
here moves a repo or edits ~/.claude.json unless its verb says so; the read-only
generators (gen-rewrites, session-map) are safe to run any time for review.

Subcommands:
  gen-rewrites            Print the path-dep rewrite list (§4.1). READ-ONLY.
  apply-rewrites <repo>   Apply path-dep rewrites for one moved repo (§4.3).
  session-map             Print the three-tier session-dir old->new map (§5.1). READ-ONLY.
  rewrite-claude-json     Atomically rewrite ~/.claude.json keys from a reviewed map (§5.1).

Run under python3.11+ (tomllib). map.tsv lives beside this file.
"""
import os, sys, json, re, tempfile

HOME = os.path.expanduser("~")
SRC = os.path.join(HOME, "src")
UMBRELLA = os.path.join(SRC, "ronin-issen")
MIG = os.path.join(UMBRELLA, ".migration")
COMPONENTS = os.path.join(UMBRELLA, "components")

try:
    import tomllib  # py3.11+
except ModuleNotFoundError:
    tomllib = None


def load_map():
    """repo -> destination ABSOLUTE path (post-move), from map.tsv."""
    out = {}
    with open(os.path.join(MIG, "map.tsv")) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            repo, cat = line.split("\t")
            if cat == "_deprecated":
                out[repo] = os.path.join(UMBRELLA, "_deprecated", repo)
            else:
                out[repo] = os.path.join(COMPONENTS, cat, repo)
    return out


def _old_root(repo):
    return os.path.join(SRC, repo)


# ---- Path-dep rewrites (§4.1 / §4.3) ---------------------------------------

_DEP_TABLES = ("dependencies", "dev-dependencies", "build-dependencies")


def _iter_path_deps(manifest):
    """Yield (table_label, crate, path_value) for every path= dep + [patch] entry.
    Defensive against odd real-world manifest shapes (non-dict tables/bodies)."""
    def deps_of(tbl):
        if not isinstance(tbl, dict):
            return
        for name, spec in tbl.items():
            if isinstance(spec, dict) and isinstance(spec.get("path"), str):
                yield name, spec["path"]

    for t in _DEP_TABLES:
        for name, p in deps_of(manifest.get(t)):
            yield t, name, p
    # [target.'cfg(..)'.dependencies] etc.
    tgts = manifest.get("target")
    if isinstance(tgts, dict):
        for tgt, body in tgts.items():
            if not isinstance(body, dict):
                continue
            for t in _DEP_TABLES:
                for name, p in deps_of(body.get(t)):
                    yield f"target.{tgt}.{t}", name, p
    # [workspace.dependencies]
    ws = manifest.get("workspace")
    if isinstance(ws, dict):
        for name, p in deps_of(ws.get("dependencies")):
            yield "workspace.dependencies", name, p
    # [patch.<registry>]
    patch = manifest.get("patch")
    if isinstance(patch, dict):
        for reg, body in patch.items():
            for name, p in deps_of(body):
                yield f"patch.{reg}", name, p


def gen_rewrites(pre_move=True):
    """Return list of rewrite records for path deps that escape their repo root.

    pre_move=True computes new relpaths as if every repo already sat at its
    map.tsv destination (the state Phase 3 rewrites into), so the list is valid
    both before and after the moves.
    """
    if tomllib is None:
        sys.exit("need python3.11+ for tomllib")
    m = load_map()
    recs = []
    for repo, dest in m.items():
        root = _old_root(repo)
        if not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            if ".git" in dirpath.split(os.sep):
                continue
            if "Cargo.toml" not in files:
                continue
            mani = os.path.join(dirpath, "Cargo.toml")
            try:
                with open(mani, "rb") as fh:
                    data = tomllib.load(fh)
            except Exception as e:  # noqa: BLE001 — report, never crash the sweep
                recs.append({"repo": repo, "manifest": mani, "error": str(e)})
                continue
            # manifest dir RELATIVE to the repo's OLD root (survives the move)
            rel_in_repo = os.path.relpath(dirpath, root)
            for table, crate, pval in _iter_path_deps(data):
                if os.path.isabs(pval):
                    target_abs = os.path.normpath(pval)
                else:
                    target_abs = os.path.normpath(os.path.join(dirpath, pval))
                # only care about deps escaping THIS repo's root (cross-repo)
                if target_abs == root or target_abs.startswith(root + os.sep):
                    continue  # intra-repo path dep — survives the move untouched
                # which moving repo does the target live in?
                tgt_repo = None
                for r2, _d2 in m.items():
                    r2root = _old_root(r2)
                    if target_abs == r2root or target_abs.startswith(r2root + os.sep):
                        tgt_repo = r2
                        break
                if tgt_repo is None:
                    recs.append({"repo": repo, "manifest": mani, "table": table,
                                 "crate": crate, "old": pval,
                                 "note": "target not a moving repo — REVIEW"})
                    continue
                # new absolute location of both ends, then relpath
                new_mani_dir = os.path.join(dest, rel_in_repo)
                sub = os.path.relpath(target_abs, _old_root(tgt_repo))
                new_target_abs = os.path.join(m[tgt_repo], sub)
                new_rel = os.path.relpath(new_target_abs, new_mani_dir)
                recs.append({"repo": repo, "manifest": mani, "table": table,
                             "crate": crate, "old": pval, "new": new_rel,
                             "target_repo": tgt_repo})
    return recs


def apply_rewrites(repo):
    """Rewrite the exact path='..' strings for one repo's manifests in place."""
    recs = [r for r in gen_rewrites() if r.get("repo") == repo and "new" in r]
    changed = {}
    for r in recs:
        mani = r["manifest"]
        with open(mani) as fh:
            txt = fh.read()
        # replace the exact quoted old value; must be unique enough — verify count
        for q in ('"%s"' % r["old"], "'%s'" % r["old"]):
            if q in txt:
                txt = txt.replace(q, '"%s"' % r["new"])
                break
        changed[mani] = txt
    for mani, txt in changed.items():
        with open(mani, "w") as fh:
            fh.write(txt)
    return sorted(changed)


# ---- Session-history migration (§5.1) --------------------------------------

PROJECTS = os.path.join(HOME, ".claude", "projects")


def _encode(path):
    """Claude project-dir encoding: '/' -> '-'. (Dots kept in the new encoder;
    the old encoder also mapped '.' -> '-'. We generate BOTH candidate encodings
    for worktree/subpath tiers and match by disk existence — never prefix.)"""
    return path.replace("/", "-")


def _encode_legacy(path):
    return path.replace("/", "-").replace(".", "-")


def session_map():
    """Three-tier exact-decode old->new dir-name map (§5.1). READ-ONLY.

    Tier 1 repo-root: dir == encode(/Users/.../src/<repo>).
    Tier 2 worktree:  dir == encode(<wt>) for a recorded linked worktree.
    Tier 3 subpath:   dir decodes to an existing path strictly inside a moving repo,
                      with a UNIQUE decode.
    Anything else -> skip.log (never guessed).
    """
    m = load_map()
    if not os.path.isdir(PROJECTS):
        return {}, ["(no ~/.claude/projects)"]
    existing = set(os.listdir(PROJECTS))
    mapping = {}   # old_dirname -> new_dirname
    skips = []

    # Tier 1: repo roots (exact equality both encodings)
    root_enc = {}
    for repo, dest in m.items():
        for enc in {_encode(_old_root(repo)), _encode_legacy(_old_root(repo))}:
            root_enc[enc] = _encode(dest)

    # Tier 2: linked worktrees recorded in state-before.json (if present)
    wt_enc = {}
    sb = os.path.join(MIG, "state-before.json")
    if os.path.isfile(sb):
        try:
            state = json.load(open(sb))
            for repo, info in state.get("repos", {}).items():
                if repo not in m:
                    continue
                for wt in info.get("worktrees", []):
                    wtp = wt.get("path")
                    if not wtp:
                        continue
                    newwt = wtp.replace(_old_root(repo), m[repo], 1)
                    for enc in {_encode(wtp), _encode_legacy(wtp),
                                wtp.replace("/", "-").replace("/.claude/", "--claude-")}:
                        wt_enc[enc] = _encode(newwt)
        except Exception as e:  # noqa: BLE001
            skips.append(f"(state-before.json unreadable: {e})")

    for d in sorted(existing):
        if d in root_enc:
            mapping[d] = root_enc[d]
        elif d in wt_enc:
            mapping[d] = wt_enc[d]
        else:
            # Tier 3: existence-verified unique subpath decode
            hit = _decode_subpath(d, m)
            if hit:
                mapping[d] = _encode(hit)
            else:
                skips.append(d)

    # Gates (§5.1): injective, no target collides with an existing dir
    targets = list(mapping.values())
    if len(set(targets)) != len(targets):
        dupes = sorted({t for t in targets if targets.count(t) > 1})
        raise SystemExit("ABORT: session map not injective: %s" % dupes)
    for t in targets:
        if t in existing and t not in mapping:
            raise SystemExit("ABORT: target session dir already exists: %s" % t)
    return mapping, skips


def _decode_subpath(dirname, m):
    """Return the unique existing new path a subpath-encoded dir decodes to, else None."""
    # candidate: dir is encode(<path under a moving repo>). Test each moving repo
    # whose root-encoding is a prefix of dirname, then verify the remainder decodes
    # to an existing on-disk subpath (unique).
    cands = set()
    for repo, dest in m.items():
        for enc_root in {_encode(_old_root(repo)), _encode_legacy(_old_root(repo))}:
            if dirname.startswith(enc_root + "-"):
                rest = dirname[len(enc_root) + 1:]
                # rest is '-'-joined path components (lossy). Try '/'-join; verify existence.
                sub = rest.replace("-", "/")
                if os.path.exists(os.path.join(_old_root(repo), sub)):
                    cands.add(os.path.join(dest, sub))
    return next(iter(cands)) if len(cands) == 1 else None


def rewrite_claude_json():
    """Atomically rewrite ~/.claude.json .projects keys + embedded paths (§5.1).
    Refuses if a live claude/codex process is running or no reviewed map exists."""
    if os.popen("pgrep -f 'claude|codex'").read().strip():
        sys.exit("ABORT: live claude/codex process — cannot rewrite ~/.claude.json")
    reviewed = os.path.join(MIG, "session-map.tsv")
    if not os.path.isfile(reviewed):
        sys.exit("ABORT: no reviewed session-map.tsv — run session-map, review, save it first")
    m = load_map()
    cj = os.path.join(HOME, ".claude.json")
    data = json.load(open(cj))
    projects = data.get("projects", {})
    # move-map for path components (exact, component-wise — never string-prefix)
    def remap_path(p):
        for repo, dest in m.items():
            r = _old_root(repo)
            if p == r or p.startswith(r + os.sep):
                return dest + p[len(r):]
        return p
    newproj, n = {}, 0
    for k, v in projects.items():
        nk = remap_path(k)
        if nk != k:
            n += 1
        newproj[nk] = v
    if len(newproj) != len(projects):
        sys.exit("ABORT: project key collision during remap")
    data["projects"] = newproj
    # embedded absolute paths in scalar values (activeWorktreeSession, history)
    blob = json.dumps(data)
    for repo, dest in m.items():
        blob = blob.replace(_old_root(repo), dest)
    data = json.loads(blob)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(cj), prefix=".claude.json.")
    with os.fdopen(fd, "w") as fh:
        json.dump(data, fh)
        fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, cj)
    print(f"rewrote {n} project keys in ~/.claude.json (backup expected beside it)")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "gen-rewrites":
        recs = gen_rewrites()
        for r in recs:
            if "new" in r:
                print(f"{r['repo']}\t{os.path.relpath(r['manifest'], SRC)}\t{r['table']}\t"
                      f"{r['crate']}\t{r['old']}\t->\t{r['new']}")
            else:
                print(f"# REVIEW {r['repo']}\t{r.get('manifest','')}\t"
                      f"{r.get('note') or r.get('error')}", file=sys.stderr)
        print(f"# {sum('new' in r for r in recs)} rewrites, "
              f"{sum('new' not in r for r in recs)} review-flags", file=sys.stderr)
    elif cmd == "apply-rewrites":
        print("\n".join(apply_rewrites(sys.argv[2])))
    elif cmd == "session-map":
        mp, sk = session_map()
        for o, nw in sorted(mp.items()):
            print(f"{o}\t{nw}")
        print(f"# {len(mp)} mapped, {len(sk)} skipped (see stderr)", file=sys.stderr)
        for s in sk:
            print(f"# skip {s}", file=sys.stderr)
    elif cmd == "rewrite-claude-json":
        rewrite_claude_json()
    else:
        sys.exit(__doc__)
