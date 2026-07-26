# 13. Batteries-included — compile everything in

Date: 2026-07-26
Status: Accepted

## Context

A forensic tool in the field must do the whole job from one artifact — the analyst cannot
`cargo build --features gpu,cloud` on an evidence workstation, and a capability that isn't
compiled in is a capability that isn't there when it matters. The instinct to slim a dependency
(smaller dep tree, dodge a gate) ships a tool that silently can't do the thing. This ADR bans
that instinct as the fleet default.

## Decision

- **`default-features = false` is BANNED as a way to slim a fleet dependency.** Depend on fleet
  crates (and capability deps like `blazehash`) with their full default feature set; the analyst
  gets a single static binary that can hash, carve, decompress, query, and report without a
  rebuild. Slimming to "keep the dep tree small" or to dodge a gate is the wrong instinct — it
  ships a tool that silently can't do the thing.
- **When full features trip a gate, fix the GATE, not the feature set.** The canonical case:
  `blazehash` pulls `xxhash-rust` (BSL-1.0), which fails a downstream `cargo deny` license
  allowlist. The fix is to **allow BSL-1.0 in the fleet `deny.toml`** (xxhash is a legitimate
  forensic hash), NOT to `default-features = false` blazehash and lose every other algorithm.
  Same for a heavy transitive: address it in `deny.toml`/`Cargo.lock`, never by amputating
  capability. (A genuine pre-release in the graph — e.g. `ml-dsa 0.1.0-rc.8` — is publish
  hygiene: pin it, don't slim around it.) Deferring or dropping a capability to dodge a gate is
  banned.
- **Commit `Cargo.lock` in EVERY fleet repo — binary AND library (binding).** For binaries/apps
  it pins the batteries-included graph the analyst ships (a fresh resolution can pull a broken or
  license-tainted version — this bit 4n6mount: no committed lock → fresh resolution → CI red,
  mis-diagnosed as a blazehash compile bug — blazehash compiles fine). For **libraries the reason
  is cargo-vet stability**: a repo whose CI runs `cargo vet --locked` but does NOT commit its lock
  makes CI *fresh-resolve the latest of every dep on every run*, so the moment any transitive dep
  publishes a new version (serde_json 1.0.150→1.0.151, serde 1.0.229, forensicnomicon 1.8.1, …)
  the version-pinned exemptions go stale and vet turns red — the "freshness treadmill" (`cargo
  vet` passes locally off an older cached lock while CI fails, the most confusing form). Committing
  the lock makes CI honor the pinned graph, so exemptions stay valid until the lock is
  *deliberately* bumped, and **Renovate `lockFileMaintenance` bumps it in a controlled PR** (where
  the exemption/audit regen happens once, reviewed, not on every push). This inverts the old
  "libraries don't commit Cargo.lock" convention — and it's fine, because a consumer still ignores
  a dependency library's lock; committing it only governs *that library's own CI/dev*. Companion
  vet gotcha: the `vet` CI job needs a `cargo fetch` step before `cargo vet --locked` (without a
  committed lock `cargo metadata --locked` cannot create the lock it needs — "cannot create the
  lock file"); with the lock committed this is moot but keep it.
- **Lean library core, full binary (the preferred mechanism — binding).** When a capability crate
  is both a heavy end-user tool AND something other fleet *libraries* link for one primitive, split
  it the way the fleet splits readers: a lean `<x>-core` library carrying just the primitives (e.g.
  `blazehash-core` = the hash algorithms, no GPU/cloud/DuckDB/yara), and the full `<x>` app/binary
  crate (every feature compiled in) depending on `<x>-core`. Fleet *libraries* that need only the
  primitive depend on `<x>-core` (lean, so no `default-features = false` is ever needed); fleet
  *binaries* and the `<x>` tool itself stay batteries-included. One `default` cannot be both
  lean-for-libraries and full-for-the-binary — the **split**, not feature-juggling, is the answer.
  Reference: `blazehash` → `blazehash-core` (lean lib) + `blazehash` (full binary);
  `ext4fs-core`/`ewf-forensic` depend on `blazehash-core` for `algorithm::hash_bytes`, never the
  GPU+cloud app stack.
- **Decode/enrichment capability is NEVER opt-in — the `*-forensic`/analysis layer is capable by
  default.** Value/BLOB decoders (`blob-decoder` for bplist/protobuf/gzip/zlib/snappy/base64/utf16/
  json, recursively unwrapped), timestamp decipherment (`timeglyph`), and the like are ALWAYS
  compiled into the analysis layer — never behind a Cargo feature the analyst must know to enable.
  An examiner staring at an opaque SQLite BLOB must get "binary plist → {…}" / "protobuf → N fields"
  from the zero-config path, not a rebuild. A hard-coded special case (e.g. sqlite-forensic's
  WebKit-`.localstorage` UTF-16 helper) is a *narrow* known-artifact convenience — it does NOT
  substitute for wiring in the general decoder. **MSRV yields to capability here:** if pulling a
  capability dep raises the analysis crate's MSRV (e.g. `blob-decoder` → 1.88 via `plist`→`time`),
  TAKE the bump — do NOT feature-gate to preserve a low MSRV. The low-MSRV floor is preserved where
  it belongs via the split: the lean `*-core` reader stays low-MSRV for third-party library reuse;
  the `*-forensic` layer + the binary carry the full decode stack and whatever MSRV it needs.
  (Lived case: proposing an optional `blob-decode` feature on sqlite-forensic was wrong — it must
  **hard-dep** `blob-decoder` in the forensic layer, always on.)
- **Exception (the only one):** a genuinely optional, *rarely-wanted* heavy subsystem MAY be a named
  non-default feature **as long as the shipping binary turns it on**. The library's `default` may
  stay lean for third-party reuse, but every fleet binary that links it builds with the full feature
  set. The slim path is for outside consumers, never for our own tools.

## Consequences

- Every fleet binary is one batteries-included static artifact — hash, carve, decompress, decode,
  query, report — with no field rebuild.
- Gates are satisfied by fixing the gate (allow the license, pin the pre-release, commit the lock),
  never by amputating a capability; a `default-features = false` on a fleet dep is a reviewable
  regression.
- The lean-`-core` / full-binary split (companion to ADR-0008, ADR-0010) is how a low-MSRV library
  floor and a batteries-included binary coexist without feature-juggling one `default`.
- **Composition / aggregation layers are the capability-carrying tier, never a low-MSRV tier, and
  deferring a format to protect their MSRV is banned.** `forensic-vfs-engine` (which pulls every
  reader) and `disk-forensic` (which aggregates every container) must surface **every** supported
  format from `open`/`open_all`, never a reduced subset, and take whatever MSRV full coverage needs.
  The low-MSRV floor is preserved **only** in the contract crate (`forensic-vfs`, traits-only) and
  the lean `*-core` readers — not by dropping a format from the engine. (Lived case: proposing to
  *defer* AFF4-Logical out of `forensic-vfs-engine` to hold Rust 1.88 was wrong. The right fix kept
  full coverage **and** minimized MSRV — AFF4-Logical read via the `aff4` crate the engine already
  has, AD1/DAR via `ad1-core`/`dar-core`, sidestepping the heavy `disk-forensic` tree; the residual
  1.93 floor comes from `archive-core -> sevenz-rust2` (7z, incl. its 0.21.1 security fix) and is
  *taken*, not dodged.)
