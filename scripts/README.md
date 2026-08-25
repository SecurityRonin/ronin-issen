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

The component repos are separate git repos not present in this repo's checkout,
so the full audit cannot enumerate them in CI; it is a maintainer command. Fully
unattended fleet-audit-in-CI would need a committed fleet manifest (the fleet is
defined by the working tree, not the GitHub org) — a deliberate follow-up.
