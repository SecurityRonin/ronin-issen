# Fleet maintenance scripts

## `fleet_structure_check.py` — structural-invariant enforcement

Checks the two fleet structural invariants from ADR-0009 against every repo's
**`origin/main`** (never a local working tree — a stale checkout reports phantom
violations):

1. **Per-parser pairing** — a repo with a top-level reader `-core` crate must
   also ship an analyzer (`-forensic` / `-integrity` / `-analysis`). Scoped to
   parsers; foundation/utility/codec/orchestrator cores are exempt (they parse no
   evidence — see `EXEMPT_REPOS` in the script).
2. **Member-dir naming** — a single-parser repo (exactly one top-level `-core`)
   names its member directories for their **role** (`core/`, `forensic/`, …),
   never for the crate (`<x>-core/`). Multi-parser repos (chromium-storage) keep
   crate-named dirs — three parsers cannot share one `core/` — and suites nest
   under `crates/`; both are skipped automatically.

### Run the full fleet audit (maintainer)

From a checkout that has the fleet under `~/src/ronin-issen`:

```bash
python3 scripts/fleet_structure_check.py
```

Fetches and reads each repo's `origin/main`, prints any violations, and exits
non-zero if any are found. Today the fleet is clean (0 violations).

### Self-test (runs in CI)

```bash
python3 scripts/fleet_structure_check.py --self-test
```

Feeds synthetic layouts through the check's pure core and asserts each gate goes
**red** on a real violation (crate-named single-parser dirs; a reader with no
analyzer) and green on clean/exempt/multi-parser cases. The `fleet-structure`
workflow runs this on every change to the check — a green-only gate is unproven,
so CI proves the gate can fail.

### Unattended full audit (scheduled CI)

The component repos are separate git repos not present in this repo's checkout,
so CI materializes the fleet from a committed manifest — **`fleet-repos.txt`**,
the CI-visible fleet definition (the fleet is the working tree, not the GitHub
org, so it cannot be enumerated from CI). The `fleet-audit` job in
`.github/workflows/fleet-structure.yml` runs **weekly and on demand**: it
shallow-clones every manifest repo and runs the full audit over their default
branches, failing on any violation (and failing loudly if any manifest repo
cannot be cloned — no silent coverage gaps).

Keep `fleet-repos.txt` in sync when a repo is added to or removed from the fleet.
The check reads `FLEET_ROOT` (the clone directory) so the same code serves both
the local working-tree run and the CI clone layout; non-parser repos are matched
by basename in `EXEMPT_NAMES`.
