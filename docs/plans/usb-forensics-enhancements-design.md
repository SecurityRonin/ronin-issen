# USB Forensics Enhancements — Design & Implementation Plan

Status: proposed · Date: 2026-07-28 · Owner: fleet
Trigger: gap analysis of a public NTFS host-based USB-forensics writeup
(JulianDerry/Computer-Forensics) against the fleet's `usb-forensic` +
`peripheral-forensic`.

## Executive Summary

A Tier-1 review (reading the actual `.rs` source, not assuming) found the fleet's
USB coverage **already meets or exceeds** a typical practitioner USB writeup:
`peripheral-forensic/core` + `usb-forensic` already parse USBSTOR/USB/SCSI enum,
MountedDevices, per-user MountPoints2, EMDMgmt, VolumeInfoCache, setupapi (Vista+
and XP grammars), the Kernel-PnP / DriverFrameworks / Partition-Diagnostic event
logs, and LNK/jump-lists — plus cross-source timestamp scoring, OS-generated-serial
detection, and macOS/Linux sources the writeup never touches.

**Only four additive items surfaced**, in priority order:

1. **VID/PID → vendor/product name** enrichment (a bundled `usb.ids` lookup) — the
   one self-contained parsing win.
2. **Wire shellbags** (`parser/shellitem`) into `usb-forensic` as a corroborating
   source (drive letter + directories browsed on the device).
3. **issen pivot — USN `$J` file-copy** (was a file copied to/from the device?).
4. **issen pivot — Amcache/Prefetch "executed from `E:\`"** (was a binary run off it?).

Items 3–4 are **orchestration pivots, not parser gaps** — the underlying crates
exist; they are simply not correlated against the USB drive letter yet.

**The one methodology insight to encode:** the **4-byte volume serial** is the
load-bearing join between the registry world (EMDMgmt / VolumeInfoCache) and the
file world (LNK / jump-list `DriveSerialNumber`) — treat it as a **primary key**,
not merely the USBSTOR iSerial. Resolving **MountPoints2 GUID → user across every
loaded NTUSER hive** is what answers *who* plugged the device in.

**Source license:** the writeup has no LICENSE (default all-rights-reserved), but
its content is established public forensic methodology (SANS FOR500, Zimmerman,
Carvey's *Windows Registry Forensics*) — take it as confirmation, copy no text or
code, do not vendor the README.

---

## What the fleet already ships (do NOT rebuild)

Verified in source: USBSTOR serial + LastWrite (`registry.rs`); Enum\USB + Enum\SCSI
incl. Thunderbolt/1394/eSATA/SDBUS (exceeds); `{83da6326-97a6-4088-9453-a1923f573b29}`
`0064/0065/0066/0067` FILETIMEs tagged authoritative-vs-inferred; MountedDevices
12-byte MBR (disk-sig + offset) bridge (`mounted_volumes.rs`); MountPoints2
(`mountpoints2.rs`); EMDMgmt (`emdmgmt.rs`); VolumeInfoCache (`volume_info.rs`);
setupapi both grammars (`setupapi.rs`); the three USB event-log providers; LNK +
jump-lists (`usb-forensic/src/sources/`); OS-generated-serial heuristic; cross-source
timestamp reconciliation (`usb-forensic/src/correlate.rs`, `reconcile.rs`).

## Enhancements (bottom-up by dependency tier)

Each follows the fleet gate: panic-free lints, fuzz where untrusted bytes are parsed,
real-artifact validation, README/PRD/ADR as applicable. TDD: RED commit (failing
tests) then GREEN commit (impl), separate commits.

### Phase 1 — KNOWLEDGE (forensicnomicon), add only what's absent
Confirm-then-add the *specs* the parsing steps below rely on (many may already
exist): the `{83da6326…}` GUID + `0064–0067` timestamp semantics, the MountedDevices
12-byte MBR layout, the EMDMgmt naming grammar, the MountPoints2 path, and a
reference entry for the `usb.ids` vendor database. Specs only — no parsing.

### Phase 2 — PARSING

**E1 — VID/PID → vendor/product name (`peripheral-forensic/core`).** *[highest value, self-contained]*
- Bundle the public `usb.ids` database; add a `vendor_name(vid) / product_name(vid,pid)`
  lookup exposed on the device record as a **marked, non-authoritative** enrichment
  field (raw numeric VID/PID stays the authoritative value — Human/Machine-output
  discipline). New file e.g. `core/src/usb_ids.rs`.
- **License gate (blocking):** `usb.ids` (linux-usb.org) is dual GPL-2 / 3-clause-BSD;
  vendor it under the BSD arm only, record provenance + license in the repo, and
  confirm redistribution is compatible with the crate's Apache-2.0 **before** committing
  the data. If incompatible, ship the lookup as an optional runtime-loaded file, not bundled.
- Validation: spot-check known devices (e.g. `VID_349C` → resolved vendor) against the
  live `usb.ids`; unit-test unknown VID/PID returns `None`, never a wrong name.

**E2 — Shellbags source (`usb-forensic`).** Wire `parser/shellitem` in as a new entry
under `usb-forensic/src/sources/` (alongside `lnk.rs`, `jumplist.rs`): parse BagMRU
from the loaded NTUSER/UsrClass hives, surface directories browsed on a removable
volume, and feed the drive-letter + user corroboration into the existing
`correlate.rs`/`reconcile.rs` scoring. Depends on `shellitem` (parser peer dep).

### Phase 3 — ORCHESTRATION (issen)
**Prerequisite (must do first):** confirm how issen actually invokes `usb-forensic`
and where cross-analyzer correlation lives — the gap-analysis could **not** verify
issen's wiring (its source layout didn't match the expected grep). Scope E3/E4 only
after reading issen's real correlation path.

**E3 — USN `$J` file-copy pivot.** Correlate NTFS `$UsnJrnl:$J` create/rename events
on the device's drive letter to answer "was a file copied to/from the device?" — the
question the writeup leaves open (and which NTFS Last-Access cannot answer reliably).
NTFS/USN crates already exist; this is a join in issen, not a new parser.

**E4 — "Executed from `E:\`" pivot.** Join Amcache / Shimcache / Prefetch execution
records whose path resolves to the USB drive letter, so an examiner sees binaries run
off the device. Crates exist; correlate against the USB volume in issen.

## The correlation model issen should encode

Device → volume → letter → user → files → execution:

`USBSTOR/USB serial + {83da6326} times` → **(disk-signature, partition-offset)** MBR
bridge in MountedDevices → `\DosDevices\X:` + `\??\Volume{GUID}` → **MountPoints2{GUID}
per-user** (⇒ *which user* + last-mounted) → **VolumeInfoCache / EMDMgmt** (label +
4-byte volume serial) → **LNK / jump-list `DriveSerialNumber`** join on that serial
(⇒ *which files*) → **Amcache / Prefetch** on `E:\*.exe` (⇒ *executed*) → **USN `$J`**
(⇒ *copied*).

Two invariants: (a) the **4-byte volume serial is the primary join key** between
registry and file artifacts; (b) resolve **MountPoints2 GUID → user for every loaded
NTUSER profile** to answer *who*. Score timestamp agreement (setupapi / 0065 / 0066–67
/ Kernel-PnP / MountPoints2 / LNK-MAC) as corroboration — never treat any single one
as more than "last committed transaction."

## Validation

Real-artifact, env-gated: a Windows host image with a known USB insertion (the
writeup's Win11 25H2 scenario is a reasonable reference to reproduce, or a CFReDS
USB image). Differential against the established oracle — Eric Zimmerman's
`MountPoints2`/`USBDeviceForensics` + RegRipper `usbstor`/`mountdev` plugins — and
reconcile serial, timestamps, drive letter, and user. Document in each repo's
`docs/validation.md`.

## Where the knowledge belongs
- **forensicnomicon** — GUID/timestamp semantics, MountedDevices MBR layout, EMDMgmt
  grammar, MountPoints2 path, `usb.ids` reference (specs/constants).
- **peripheral-forensic/core + usb-forensic** — existing readers + E1 vendor-name +
  E2 shellbag source (parsing).
- **issen** — E3 (USN copy) + E4 (executed-from-USB) cross-analyzer pivots + the
  §correlation model.

## Sequencing, effort, risk
- **E1 first** — smallest, self-contained, highest analyst value; gated only on the
  `usb.ids` license check.
- **E2** next — one new source file + a `shellitem` dep, feeds existing scoring.
- **E3/E4** last — gated on the issen-wiring verification; they are joins, so effort
  is in the correlation model, not new parsing.
- **Biggest risk:** the `usb.ids` redistribution license (E1) and the unverified issen
  wiring (E3/E4). Resolve both before committing to those phases.
- **Not in scope:** anything the fleet already ships (§"already ships") — this plan
  adds only the four items, and rebuilds nothing.
