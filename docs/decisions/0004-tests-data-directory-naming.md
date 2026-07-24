# 4. Test inputs live in `tests/data/`; "corpus" is a classification, not the directory name

Date: 2026-07-24
Status: Accepted

## Context

Test-input files drifted in naming across the fleet — `tests/data/`, `tests/fixtures/`,
`tests/samples/`, `testdata/`, a top-level `corpus/` — and in prose ("test corpus" vs
"test data"). The fleet needs one directory convention and a clear line between the
*location* of test inputs and the *classification* of a subset of them. (Related standing
rules: `CLAUDE.md` → "One repo-root `tests/data/`" and "Test Corpus Catalog".)

## Decision

- **All test-input files live under a single repo-root `tests/data/`.** Integration tests
  reach them by the relative path `include_bytes!("../../tests/data/<file>")`, symmetric
  across every workspace member. Not `tests/fixtures/`, `tests/samples/`, `testdata/`, or a
  top-level `corpus/`.
- **"Corpus" is reserved for a *kind* of test data — a curated real-world dataset — and is
  never the directory name.** `tests/data/` holds the honest superset: real datasets, tiny
  synthetic fixtures, hand-built byte buffers, oracle inputs. Most of those are not a corpus.

## Why `tests/data/`, not "corpus"

1. **Location vs classification.** `tests/data/` names *where test inputs live* — a path
   convention. "Corpus" names *what a subset of them are* — a curated collection, a word
   that carries an ML/linguistics/fuzzing connotation of a large sampled set. Naming the
   *directory* "corpus" over-claims: a 1 KB hand-built MBR fixture, or a byte buffer with a
   deliberately-lying length field, is test **data**, not a corpus.
2. **Convention + discoverability.** `tests/data/` sits beside the `tests/` integration
   tests and is reached by a predictable relative include path every workspace member
   shares. A developer — or a `docs-gate`/CI check — knows exactly where to look.
   `tests/corpus/` would be idiosyncratic and break the include-path symmetry.
3. **Accuracy as a superset.** "data" is the honest umbrella for everything under it (the
   catalog's own REAL-ext / REAL-self / SYNTHETIC / VENDORED / FUZZ classes). "corpus"
   covers only the real-dataset rows. One accurate directory name beats one over-specific one.
4. **"Corpus" keeps a legitimate home — the catalog.** `docs/test-data-catalog.md` and each
   `tests/data/README.md` rightly call a real third-party dataset a "corpus" — there it is a
   *content classification*, not a path.

## Consequences

- The directory is `tests/data/` fleet-wide; per-file provenance in `tests/data/README.md`,
  the fleet index in `docs/test-data-catalog.md`.
- Prose uses "corpus" only for real curated datasets; the generic term for the directory's
  contents is "test data."
- The catalog filename standardizes on **`docs/test-data-catalog.md`** (data — the superset),
  not `corpus-catalog.md`; the stray `issen/docs/corpus-catalog.md` folds into it and its
  inbound references (e.g. `tests/data/README.md`) are repointed. (Cleanup, tracked.)
