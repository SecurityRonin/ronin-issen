# DLEAPP Feature-Parity — Design & Implementation Plan

Status: proposed · Date: 2026-07-28 · Owner: fleet
Source research: `abrignoni/DLEAPP` @ `4e104cc` (v2026.2.0, MIT, © Alexis Brignoni)

## Executive Summary

DLEAPP ("Desktop Logs Events And Protobuf Parser") parses **Electron/Chromium
desktop-app artifacts** — Discord, Signal, Wire, WhatsApp desktop — by reading
Chromium storage subsystems (Simple Cache, IndexedDB-over-LevelDB, Local Storage)
and decrypting app databases (SQLCipher + OS safeStorage key recovery).

**The parity insight: DLEAPP is app-level; the fleet is format-level.** DLEAPP
bundles the format decoders and the app knowledge into one Python module per
artifact. The fleet already owns the *primitives* it lacks the *Chromium storage
decode layer* above them (we have leveldb/protobuf/sqlite, not IndexedDB→V8 or the
disk-cache container) and the *app schemas*. So parity is **not** porting 21 Python
modules — it is building **~4 reusable format/crypto readers once**, then thin
**app-knowledge crates** on top. The format layer then benefits browser-forensic
and every future desktop-app parser, not just messengers.

**Recommendation:** a five-phase, bottom-up build (KNOWLEDGE → utility decoder →
Chromium-storage + crypto readers → app parsers → issen orchestration), with
**DLEAPP itself as the tier-1 differential oracle** on shared corpora. Signal is
the reference app (cleanest: SQLCipher + one keychain unwrap); Discord second (the
IndexedDB + Simple Cache showcase); Wire and WhatsApp follow the same rails.

**One open taxonomy decision (flagged, not blocking):** the messenger app parsers
want a home. This plan proposes a new **`application/`** category (desktop-app
artifact interpreters — a coherent, growing family: Slack/Teams/Telegram desktop
later). The alternative is placing them in `parser/`. Proceeding with
`application/`; easily changed pre-publish (proximity rule, ADR-0007).

**License:** MIT → Apache-2.0 is clean. Artifact-path/schema knowledge and the
pure-Python `ccl_*` decoders are reusable with attribution; we reimplement in Rust,
citing DLEAPP/CCL as the reference and validating against them as oracle.

---

## What parity requires (capability → fleet gap → target)

| DLEAPP capability | Fleet today | Target (new unless noted) |
|---|---|---|
| Chromium **Simple Cache** (`*_0` entries, index) | gap | `chromium-storage-forensic` → cache reader |
| **IndexedDB** envelope over LevelDB | gap (have leveldb) | `chromium-storage-forensic` → indexeddb reader |
| **Blink/V8** serialized-value deserialize | gap | **extend `blob-decoder`** (always-on decode stack) |
| Chromium **Local Storage** schema | partial (leveldb only) | `chromium-storage-forensic` → localstorage reader |
| **SQLCipher** DB decryption | gap | **extend `sqlite-forensic`** (RustCrypto) |
| **macOS keychain** offline recovery | gap (have DPAPI/Win) | `keychain-forensic` (encryption/) |
| Chromium **safeStorage** key (Win/mac/Linux) | partial (dpapi only) | `chromium-safestorage` (encryption/) |
| **Discord/Signal/Wire/WhatsApp** desktop schemas | gap | `application/` app crates |
| Privacy-preserving **regression baselines** | partial | fleet test-data standard update |
| Declarative **conversation view** | gap | issen timeline feature |

Everything below `application/` is reusable infrastructure; only the app crates
carry per-vendor knowledge.

---

## Architecture & dependency order (ADR-0006 bottom-up)

```
KNOWLEDGE   forensicnomicon
              + Chromium storage constants (Simple Cache magic/Fletcher,
                IndexedDB key prefixes, LocalStorage schema)
              + V8/Blink serialization tag tables
              + messenger artifact specs (paths, schema versions)

UTILITY     blob-decoder
              + V8 value deserializer + Blink value deserializer
                (recursive, feeds the always-on decode stack — batteries-included)

PARSER      chromium-storage-forensic   (NEW, Pattern-B suite)
  (format)     chromium-storage-cache        Simple Cache container → HTTP entries
               chromium-storage-indexeddb    IndexedDB → records (uses leveldb-forensic
                                             + blob-decoder V8)
               chromium-storage-localstorage LocalStorage LevelDB schema
            sqlite-forensic  (EXTEND)    SQLCipher page decryption (RustCrypto)
            leveldb-forensic (reuse)     unchanged — the storage engine underneath

ENCRYPTION  keychain-forensic  (NEW)     login.keychain-db offline decrypt → secrets
            chromium-safestorage (NEW)   OS-dispatch safeStorage key:
                                          Win→dpapi-forensic, mac→keychain-forensic,
                                          Linux→gnome-keyring / v10 "peanuts"

APPLICATION discord-forensic · signal-forensic · wire-forensic ·
  (NEW cat)  whatsapp-desktop-forensic
               each: app schema knowledge; calls chromium-storage + sqlite
               (SQLCipher) + chromium-safestorage; emits forensicnomicon events

ORCHESTRATION issen
               + conversation timeline view (declarative column→chat mapping)
               + messenger-event correlation into the unified DuckDB timeline
```

**Dependency rules honored:** app crates are PARSER-tier consumers — they take
`Path`/`&[u8]` and call peer format readers + the safeStorage key provider; they
never import CONTAINER/FILESYSTEM. `chromium-safestorage` depends *down* onto the
OS crypto readers. `blob-decoder`'s V8 decoder stays medium-agnostic. All readers
keep the `core/`+`forensic/` split and the Paranoid-Gatekeeper posture.

---

## Crypto: reuse, never roll (fleet law)

Every decryption path is standard and maps to a vetted RustCrypto crate — no
hand-rolled primitives, no placeholders:

- **SQLCipher**: PBKDF2-HMAC-SHA(1/512) key derivation → AES-256-CBC page decrypt →
  per-page HMAC auth. Crates: `pbkdf2`, `aes`, `cbc`, `hmac`, `sha1`/`sha2`.
- **macOS safeStorage**: PBKDF2-HMAC-SHA1 (salt `saltysalt`, 1003 iters) → AES-128-CBC.
- **macOS `login.keychain-db`**: PBKDF2 + 3DES-CBC (legacy) / AES — documented format
  (`des`, `aes`, `cbc`, `pbkdf2`).
- **Windows safeStorage**: DPAPI → existing `dpapi-forensic`.
- **Linux safeStorage**: `v11` gnome-keyring/kwallet, `v10` hardcoded `peanuts` +
  fixed PBKDF2 — no secret needed for `v10`.

The key material (Signal/Discord safeStorage password, keychain login password) is
a **caller-supplied input**, never fabricated; a missing/wrong key fails loud.

---

## Phased build

Each repo follows the fleet gate: `core/`+`forensic/` split, `unwrap_used`/
`expect_used = deny`, one fuzz target per parsed structure, 100% `--lib` coverage
(`// cov:unreachable` for defensive arms), README/PRD/ADR/`validation.md`, MkDocs +
Pages, release automation. Every task is **RED commit (failing tests) then GREEN
commit (impl)** — no combined commits; subagents get this instruction verbatim.

### Phase 1 — KNOWLEDGE + decoder (leaves; unblocks everything)
1. **forensicnomicon**: add Chromium storage constants, V8/Blink tag tables, and a
   messenger artifact-spec module (paths + schema versions per app/OS). `feat` → minor.
2. **blob-decoder**: add V8 + Blink value deserializers (recursive; a V8 blob inside
   an IndexedDB value unwraps like bplist/protobuf do today). Fuzz target added.
   Validate against `ccl_v8_value_deserializer` output on captured blobs.

### Phase 2 — Chromium storage + crypto readers (the reusable core)
3. **chromium-storage-forensic** (new Pattern-B repo): `-cache`, `-indexeddb`,
   `-localstorage` readers + shared `-core`. indexeddb reader composes
   `leveldb-forensic` + `blob-decoder`. Real-artifact validation vs DLEAPP.
4. **sqlite-forensic**: SQLCipher support — given a key, expose a decrypted page
   stream the existing reader consumes (VFS-crypto-layer shaped). `feat` → minor.
5. **keychain-forensic** (new): offline `login.keychain-db` decrypt → secret items.
6. **chromium-safestorage** (new): OS-dispatch key provider over dpapi/keychain/linux.

### Phase 3 — application parsers (parity headline)
7. **signal-forensic** (reference impl): SQLCipher DB + one macOS-keychain safeStorage
   unwrap → messages/account/contacts as forensicnomicon events. Establishes the
   app-crate template.
8. **discord-forensic**: IndexedDB + Simple Cache showcase — messages, media, cache
   records, account/contacts/searches; cached responses tagged point-in-time.
9. **wire-forensic**, **whatsapp-desktop-forensic**: same rails; reuse the template.
   (`whatsapp-desktop-` prefix keeps it distinct from any future mobile WhatsApp.)

### Phase 4 — issen orchestration
10. **Conversation view**: a declarative column→chat mapping (sender/text/time/
    direction/media), adapted from DLEAPP's `data_views.conversation`, rendering any
    messenger event set as a thread with no per-app UI code.
11. **Correlation**: messenger events into the unified DuckDB timeline, cross-linked
    with existing artifacts (e.g. a Discord install in prefetch/amcache).

### Cross-cutting — test data & validation
12. **DLEAPP as tier-1 oracle**: differential validation — run DLEAPP on the same
    corpus, reconcile row counts + contents per artifact; document divergences in
    each repo's `docs/validation.md`.
13. **Mint corpora**: no public desktop-messenger ground-truth image exists (DLEAPP's
    are private). Create documented synthetic profiles per app/OS; catalog in
    `docs/test-data-catalog.md` with generator commands.
14. **Privacy-preserving baselines** (adopt into the fleet standard): commit
    regression fingerprints = row counts + column list + per-column digests +
    populated-value counts, **never actual rows** — so coverage ships without
    publishing private content. Add to the test-data standard in CLAUDE.md.

---

## Sequencing, effort, risk

- **Critical path**: Phase 1 → 2 → Signal (Phase 3.7) is the first end-to-end
  vertical slice (decrypt + read + emit + timeline). Ship that, then fan out apps.
- **Parallelizable after Phase 2**: the four app crates are independent; Wire and
  WhatsApp can run as subagents once the Signal template lands.
- **Biggest technical risk**: the Blink/V8 deserializer (versioned, complex) — mitigate
  by porting `ccl_v8_value_deserializer` semantics and differencing on real blobs.
- **Biggest process risk**: corpus provenance — minting realistic app data with known
  ground truth. Start corpus minting in Phase 1 (parallel to code), not at the end.
- **Not in scope**: mobile messenger extraction (iLEAPP/ALEAPP territory), live
  acquisition, network capture.

## Deliverables checklist (per new repo)
core/+forensic/ · panic-free lints · fuzz targets · `validation.md` (DLEAPP oracle)
· README (badges = enforced guarantees) · PRD + ADRs · MkDocs+Pages · release-plz/
tag release · MIT-attribution note to DLEAPP/CCL in NOTICE or README acknowledgements.

## Open decision
`application/` new category vs `parser/` for the app crates — proceeding with
`application/`; revisit before the first app-crate publish (cheap rename, ADR-0007).
