#!/usr/bin/env python3
"""Fleet structural invariants — enforcement check.

Two invariants, both read from `origin/main` (never a local working tree — a
stale checkout reports phantom violations, as one was nearly filed):

  1. Per-parser pairing (ADR-0009): a repo with a top-level reader `-core` crate
     must also ship an analyzer. Scoped to PARSERS — foundation/utility/codec/
     orchestrator cores are exempt (they parse no evidence).

  2. Member-dir naming (ADR-0009): a SINGLE-parser repo (exactly one top-level
     `-core`) names its member directories for their ROLE (`core/`, `forensic/`,
     …), never for the crate (`<x>-core/`). Multi-parser repos (>1 top-level
     `-core`, e.g. chromium-storage) keep crate-named dirs — three parsers cannot
     share one `core/` — and suites nest under `crates/`; both are skipped.

`--self-test` proves each gate can go red (a green-only gate is unproven).
Otherwise enumerates the fleet from the working tree (the binding definition)
and reads each repo's state from origin/main. Exit non-zero on any violation.
"""
import subprocess, pathlib, re, sys

FLEET = pathlib.Path.home() / "src" / "ronin-issen"

EXEMPT_REPOS = {
    "components/knowledge/forensicnomicon",
    "components/utility/blazehash",
    "components/utility/timeglyph",
    "components/codec/lzvn",
    "components/orchestration/issen",
}
ANALYZER_SUFFIXES = ("-forensic", "-integrity", "-analysis")


def evaluate(rel, top_members, crate_of, exempt=EXEMPT_REPOS):
    """Pure core: given a repo's top-level member dirs and each dir's crate name,
    return the list of violation messages. No I/O — unit-testable."""
    out = []
    core_dirs = [m for m, c in crate_of.items() if c and c.endswith("-core")]

    # Invariant 2 — member-dir naming (single-parser repos only).
    if len(core_dirs) == 1:
        for m in top_members:
            if "-" in m.rstrip("/").split("/")[-1]:
                out.append(f"member dir '{m}' is crate-named; a single-parser repo "
                           f"names dirs for their role (core/forensic/…)")

    # Invariant 1 — per-parser pairing.
    if core_dirs and rel not in exempt:
        names = [c for c in crate_of.values() if c]
        if not any(n.endswith(ANALYZER_SUFFIXES) for n in names):
            out.append(f"reader {[crate_of[d] for d in core_dirs]} but no analyzer "
                       f"(-forensic/-integrity/-analysis) member")
    return out


# ── fleet I/O (reads origin/main) ────────────────────────────────────────────
def repos():
    out = subprocess.run(
        ["find", str(FLEET), "-maxdepth", "4", "-name", ".git",
         "-not", "-path", "*/.claude/*", "-not", "-path", "*/target/*"],
        capture_output=True, text=True).stdout.split("\n")
    return sorted(pathlib.Path(p).parent for p in out if p and "_deprecated" not in p)


def show(repo, path):
    r = subprocess.run(["git", "-C", str(repo), "show", f"origin/main:{path}"],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def members(cargo_text):
    m = re.search(r'(?ms)members\s*=\s*\[(.*?)\]', cargo_text or "")
    return re.findall(r'"([^"]+)"', m.group(1)) if m else []


def pkg_name(cargo_text):
    seg = re.search(r'(?ms)^\[package\]\s*(.*?)(?=^\[|\Z)', cargo_text or "")
    if not seg:
        return None
    nm = re.search(r'(?m)^\s*name\s*=\s*"([^"]+)"', seg.group(1))
    return nm.group(1) if nm else None


def run_fleet():
    violations = []
    for repo in repos():
        rel = str(repo.relative_to(FLEET))
        subprocess.run(["git", "-C", str(repo), "fetch", "-q", "origin"], capture_output=True)
        cargo = show(repo, "Cargo.toml")
        if cargo is None:
            continue
        top = [m for m in members(cargo)
               if not (m.startswith("crates/") or "/crates/" in m or "/" in m)]
        crate_of = {m: pkg_name(show(repo, f"{m}/Cargo.toml")) for m in top}
        for msg in evaluate(rel, top, crate_of):
            violations.append((rel, msg))
    for rel, msg in violations:
        print(f"VIOLATION  {rel}: {msg}")
    print(f"\n{len(violations)} violation(s)")
    return 1 if violations else 0


def self_test():
    cases = [
        # (name, rel, top, crate_of, expected_violation_count)
        ("clean single-parser (role dirs + analyzer)", "x",
         ["core", "forensic"], {"core": "snss-core", "forensic": "snss-forensic"}, 0),
        ("crate-named dirs (single-parser)", "x",
         ["snss-core", "snss-forensic"],
         {"snss-core": "snss-core", "snss-forensic": "snss-forensic"}, 2),
        ("reader with no analyzer", "x",
         ["core", "cli"], {"core": "foo-core", "cli": "foo-cli"}, 1),
        ("exempt foundation core", "components/knowledge/forensicnomicon",
         ["core"], {"core": "forensicnomicon-core"}, 0),
        ("multi-parser repo keeps crate-named dirs", "x",
         ["a-core", "a-forensic", "b-core", "b-forensic"],
         {"a-core": "a-core", "a-forensic": "a-forensic",
          "b-core": "b-core", "b-forensic": "b-forensic"}, 0),
    ]
    ok = True
    for name, rel, top, crate_of, want in cases:
        got = len(evaluate(rel, top, crate_of))
        flag = "ok" if got == want else "FAIL"
        if got != want:
            ok = False
        print(f"  [{flag}] {name}: {got} violation(s), expected {want}")
    print("self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(self_test() if "--self-test" in sys.argv else run_fleet())
