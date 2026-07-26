# Fleet Reorg — `ronin-issen/components/<folder>/`

**Status: Proposed — draft for review.** This is a proposal for a human to review and
reshape, not a decision. **No repo has been moved, renamed, or `mv`-ed** — this document is
the only artifact. Folder assignments, the move order, and every ambiguous-repo verdict below
are proposals to accept, reject, or refine.

The taxonomy reuses the fleet's own layer architecture (`~/src/issen/CLAUDE.md` →
"Multi-Repo Architecture") plus the forensic-vfs 5-layer open model
(Container / Archive / Volume / Encryption / FileSystem) as the `components/` folder structure,
so the on-disk layout mirrors the dependency hierarchy the fleet already documents.

---

## 1. Proposed `components/` tree

```
ronin-issen/components/
  knowledge/       zero-dep cross-cutting facts — format specs + forensic reference data
  utility/         generic tooling libs (not domain knowledge) — safe reads, hashing, output-safety
  compression/     pure byte-stream decompressors (codecs) — transform bytes, don't bundle files
  archive/         packaging formats (ArchiveOpen) — unpack a file tree from a bundle
  container/       acquisition IMAGES (ContainerOpen) — decode a dump → sector stream
  partition/       partition tables over a byte stream (MBR/GPT/APM)
  encryption/      FDE / credential decryption layers (EncryptionOpen)
  filesystem/      navigate a byte stream by path (name → inode → block)
  memory/          navigate a page stream by VA (PID → EPROCESS → VA → PA)
  vfs/             format-agnostic image/FS abstraction + mount
  log/             navigate a log stream by timestamp / record number
  parser/          interpret artifact records → forensic meaning
  graph/           content-addressed / Merkle-DAG navigation (hash → blob → graph)
  acquisition/     live-host edge — running-disk enumeration + acquisition-integrity triage
  history/         the [H] state-history domain — trait vocabulary + concrete snapshot/shadow-copy readers
  orchestration/   cross-artifact correlation, timeline, user-facing CLI (capstone)
  # volume/ dropped — empty after vsc→history/; a planned LVM reader would reinstate it
```

Per-folder rationale and membership:

| Folder | Rationale (one line) | Repos |
|---|---|---|
| `knowledge/` | Cross-cutting fleet-wide facts: compile-time format specs + forensic reference data — no binary deserialization by charter; everything depends **down** onto it. | forensicnomicon, forensic-hashdb |
| `utility/` | Generic tooling libraries — not domain knowledge: safe positioned reads, hashing, output-sanitization, timestamp math, path/name utilities. Reusable outside forensics. | safe-read, blazehash, jsonguard, timeglyph, shrinkpath, name-variants |
| `compression/` | Pure byte-stream decompressors — a codec transforms bytes, it doesn't bundle files (not `archive/`) and it isn't a pure fact/spec (not `knowledge/`). | xpress-huffman, lzo, lzvn |
| `archive/` | Packaging formats (`ArchiveOpen`) — unpack a logical file tree from a bundle. Distinct from an acquisition image. | archive-forensic, zip-forensic, dar-forensic, ad1-forensic |
| `container/` | Acquisition **images** (`ContainerOpen`) — decode a dump/image → raw sector stream. | ewf-forensic, vmdk-forensic, vhdx-forensic, vhd-forensic, qcow2-forensic, dmg-forensic, aff4-forensic, ufed |
| `partition/` | Partition-table decode over a byte source. | mbr-partition-forensic, gpt-partition-forensic, apm-partition-forensic |
| `encryption/` | FDE / credential decryption between the volume and the filesystem (matches forensic-vfs `EncryptionLayer`/`EncryptionOpen`); includes crypto transforms serving FDE. | bitlocker-forensic, luks-forensic, filevault-forensic, veracrypt-forensic, dpapi-forensic, elephant-diffuser |
| `filesystem/` | Navigate a sector stream by path (`FileSystemOpen`). | ntfs-forensic, ext4fs-forensic, fat-forensic, apfs-forensic, hfsplus-forensic, xfs-forensic, btrfs-forensic, zfs-forensic, refs-forensic, ufs-forensic, iso9660-forensic, udf-forensic *(iso9660/udf — confirmed filesystem/)* |
| `memory/` | Navigate a physical page stream by virtual address. | memory-forensic |
| `vfs/` | The format-agnostic open-any-image / mount abstraction. | forensic-vfs, forensic-vfs-engine, forensic-vfs-mount, 4n6mount, disk-forensic |
| `log/` | Navigate a log stream by timestamp / record number. | winevt-forensic, journald-forensic |
| `parser/` | Medium-agnostic artifact interpreters (`Path`/`&[u8]` in → findings out), incl. shared binary-structure deserializers/decoders. | browser-forensic, winreg-forensic, srum-forensic, prefetch-forensic, lnk-forensic, amcache-forensic, shimcache-forensic, userassist-forensic, bam-forensic, peripheral-forensic, bluetooth-forensic, atx-forensic, snss-forensic, sqlite-forensic, ese-forensic, exec-pe-forensic, segb-forensic, protobuf-forensic, blob-decoder, shellitem, cfb-forensic, trash-forensic, shellhist-forensic, leveldb-forensic, useract-forensic, usb-forensic |
| `graph/` | Content-addressed / Merkle-DAG navigation. | git-forensic *(cas-forensic, sigstore-forensic — planned, no repo yet)* |
| `acquisition/` | Live-host edge — enumerate the running machine's physical disks and grade acquisition integrity. | livedisk-forensic *(RapidCollect returns here after its rewrite)* |
| `history/` | The whole `[H]` state-history domain — both the zero-dep `[H]` trait **vocabulary** (state-history-forensic) AND the concrete `[H]` **readers** (vsc-forensic, snapshot-forensic) that depend down on it. Groups the domain the way `vfs/` groups the VFS contract + engine + mount + readers. | state-history-forensic, vsc-forensic, snapshot-forensic |
| `orchestration/` | The single fleet-wiring capstone — cross-artifact correlation, super-timeline, user-facing CLI. | issen |

*`volume/` dropped — empty after vsc-forensic → `history/`; no placeholder kept. A future LVM reader would fold into `partition/` or reintroduce its own folder then.*

**Present fleet repos assigned: 84.** Counts by folder: knowledge 2 · utility 6 · compression 3 ·
archive 4 · container 8 · partition 3 · encryption 6 · filesystem 12 · memory 1 · vfs 5 ·
log 2 · parser 26 · graph 1 · acquisition 1 · history 3 · orchestration 1. (`cas-forensic` and
`sigstore-forensic` are named in the architecture but have no `~/src` repo yet — listed as
planned, not counted.)

---

## 2. Per-repo table

`movable-now?` reflects the session audit (104 movable-now / 8 pinned fleet-wide). Only the
repos with a real cross-repo *path/patch* pin are flagged; everything else is movable now.

### knowledge/
| repo | movable-now? | notes |
|---|---|---|
| forensicnomicon | ✅ | KNOWLEDGE leaf; `report` model + format specs |
| forensic-hashdb | ✅ | forensic reference data — NSRL / malware / LOLDrivers IOC hash sets (domain knowledge, **resolved: knowledge/**) |

### utility/
| repo | movable-now? | notes |
|---|---|---|
| safe-read | ✅ | bounds-checked positioned reads (**moved from knowledge/**; **Wave-0 publish target** — 0.2.0) |
| blazehash | ✅ | hashing (`blazehash-core` lean lib + full binary) (**moved from knowledge/**) |
| jsonguard | ✅ | output-sanitization (**moved from knowledge/**) |
| timeglyph | ✅ | timestamp math/decipherment (**moved from knowledge/**) |
| shrinkpath | ✅ | path-shortening / display utility (**moved from tooling/**) |
| name-variants | ✅ | name-variant generation — `name-variants-rs` + `name-variants-py` (**added to fleet 2026-07-27**) |

### compression/
| repo | movable-now? | notes |
|---|---|---|
| xpress-huffman | ✅ | [MS-XCA] codec (**moved from knowledge/**) |
| lzo | ✅ | codec (**moved from knowledge/**; GPL note — license gate, unrelated to move) |
| lzvn | ✅ | codec (**moved from knowledge/**) |

### archive/
| repo | movable-now? | pinned-to | notes |
|---|---|---|---|
| archive-forensic | ✅ | — | ships `archive-core` (**Wave-0 publish target**; disk-forensic + 4n6mount pin its path) |
| zip-forensic | ✅ | — | |
| dar-forensic | ✅ | — | |
| ad1-forensic | ❌ pinned | path→safe-read (req `"0.1"`, safe-read is 0.2.0) | **moved from vfs** — AD1 is a logical file tree (`disk_forensic::logical::open`), not a raw-disk mount; cheap req-bump (Wave 1) |

### container/
| repo | movable-now? | notes |
|---|---|---|
| ewf-forensic | ✅ | E01 acquisition image |
| vmdk-forensic | ✅ | |
| vhdx-forensic | ✅ | |
| vhd-forensic | ✅ | |
| qcow2-forensic | ✅ | |
| dmg-forensic | ✅ | |
| aff4-forensic | ✅ | |
| ufed | ✅ | **verdict below** — Cellebrite UFED physical-dump (mobile acquisition image) |

### partition/
| repo | movable-now? | notes |
|---|---|---|
| mbr-partition-forensic | ✅ | |
| gpt-partition-forensic | ✅ | |
| apm-partition-forensic | ✅ | Apple Partition Map |

### encryption/
| repo | movable-now? | notes |
|---|---|---|
| bitlocker-forensic | ✅ | |
| luks-forensic | ✅ | |
| filevault-forensic | ✅ | |
| veracrypt-forensic | ✅ | |
| dpapi-forensic | ✅ | credential decryption |
| elephant-diffuser | ✅ | BitLocker Elephant Diffuser — crypto transform serving FDE (**moved from knowledge/**) |

### filesystem/
| repo | movable-now? | notes |
|---|---|---|
| ntfs-forensic | ✅ | **patch→forensic-vfs now cleared**; pins `forensic-vfs "0.4.3"` (registry) — movable |
| ext4fs-forensic | ✅ | |
| fat-forensic | ✅ | |
| apfs-forensic | ✅ | |
| hfsplus-forensic | ✅ | |
| xfs-forensic | ✅ | |
| btrfs-forensic | ✅ | |
| zfs-forensic | ✅ | `zfs-forensic-core` + `zfs-forensic` (name-collision form) |
| refs-forensic | ✅ | |
| ufs-forensic | ✅ | |
| iso9660-forensic | ✅ | optical `FileSystemOpen` — **confirmed filesystem/** (doubles as a disc-image format, but placed as a filesystem) |
| udf-forensic | ✅ | optical `FileSystemOpen` — **confirmed filesystem/** |

### memory/
| repo | movable-now? | notes |
|---|---|---|
| memory-forensic | ✅ | `memf-*` suite (Pattern B) |

### vfs/
| repo | movable-now? | pinned-to | notes |
|---|---|---|---|
| forensic-vfs | ✅ | — | leaf contract crate (published 0.4.3) |
| forensic-vfs-engine | ✅ | — | `publish = false` (**Wave-0 publish target**) |
| forensic-vfs-mount | ❌ pinned | path→forensic-vfs, ad1-core; patch→forensic-vfs | clears after Wave-0/2 |
| 4n6mount | ❌ pinned | path→forensic-vfs-engine, archive-core, memf-\*; patch→6 readers | **last to move** (Wave 4) |
| disk-forensic | ❌ pinned | path→archive-core | clears when archive-core published (Wave 0→1) |

### log/
| repo | movable-now? | notes |
|---|---|---|
| winevt-forensic | ✅ | LOG FORMAT + PARSER (boundary internal) |
| journald-forensic | ✅ | `jd4n6` CLI |

### parser/
| repo | movable-now? | notes |
|---|---|---|
| browser-forensic | ✅ | only cross-repo refs were stale `.claude/worktrees/` checkouts — **clean the worktree first**, then movable |
| winreg-forensic | ✅ | `winreg-*` suite |
| srum-forensic | ⚠️ hygiene | git→ese-test-fixtures (`publish=false`) resolves from remote regardless of dir — move won't break it |
| prefetch-forensic | ✅ | |
| lnk-forensic | ✅ | |
| amcache-forensic | ✅ | |
| shimcache-forensic | ✅ | |
| userassist-forensic | ✅ | |
| bam-forensic | ✅ | |
| peripheral-forensic | ✅ | **verdict below** — setupapi + SYSTEM-hive device reader |
| bluetooth-forensic | ✅ | **verdict below** — SYSTEM-hive Bluetooth pairing reader (`bluetooth4n6`) |
| atx-forensic | ✅ | **verdict below** — iOS ATX image-cache decoder |
| snss-forensic | ✅ | |
| sqlite-forensic | ✅ | |
| ese-forensic | ✅ | |
| exec-pe-forensic | ✅ | |
| segb-forensic | ✅ | SEGB/Biome (`segb-core` + analyzer) |
| protobuf-forensic | ✅ | shared decoder (could also be `knowledge/` — adopted as drafted, see §6 Resolved) |
| blob-decoder | ✅ | recursive value/BLOB decoder (bplist/protobuf/gzip/zlib/snappy/base64/utf16/json) — **moved from knowledge/** (binary deserialization → parser) |
| shellitem | ✅ | shell-item ID-list (ITEMIDLIST) deserializer — **moved from knowledge/** (binary deserialization → parser, shared by lnk/jumplist) |
| cfb-forensic | ✅ | OLE/CFB compound-file reader (third-party `cfb` reader) — **moved from archive/**; carves the artifact-container for deleted-stream residue rather than peeling a general VFS layer |
| trash-forensic | ✅ | |
| shellhist-forensic | ✅ | |
| leveldb-forensic | ✅ | **verdict below** — key-value store artifact (Chrome storage), **moved from filesystem/** |
| useract-forensic | ✅ | user-activity correlation (consumes segb-core) — a domain artifact-interpreter (see §6 Resolved) |
| usb-forensic | ✅ | **verdict below** — USB device-history correlation over Windows artifacts (see §6 Resolved) |

### graph/
| repo | movable-now? | notes |
|---|---|---|
| git-forensic | ✅ | `git-core` + `git-forensic` published |

### acquisition/
| repo | movable-now? | pinned-to | notes |
|---|---|---|---|
| livedisk-forensic | ❌ pinned | path→safe-read (req `"0.1"`, safe-read is 0.2.0) | **moved from vfs/** — enumerates the RUNNING host's physical disks (IOKit / sysfs / DeviceIoControl) + grades acquisition integrity (no write-blocker, mounted-during-acquisition, removable, 512e/4Kn mismatch); never reads an image. Cheap req-bump (Wave 1). |

*RapidCollect returns to `acquisition/` after its rewrite (currently Excluded — pending rewrite).*

### history/
| repo | movable-now? | notes |
|---|---|---|
| state-history-forensic | ✅ | the `[H]` trait **vocabulary** (HistoricalSource/TemporalCohort/ClockProvenance/EpochTag), zero-dep — **moved from knowledge/** (thematic: the `[H]` vocabulary lives with its domain) |
| vsc-forensic | ✅ | VSS shadow copies — `[H]` state-history reader (**moved from volume/**, which is now empty) |
| snapshot-forensic | ✅ | snapshot/backup reader — APFS snapshots / Time Machine / btrfs, an `[H]` implementation (**moved from container/**); early scaffold |

### orchestration/
| repo | movable-now? | notes |
|---|---|---|
| issen | ✅ | the single fleet-wiring capstone; consumes registry deps, not paths |

---

## 3. Move order

Two viable strategies. **Both are proposals** — pick one.

### Option A — staged waves (lowest risk per step)

| Wave | Action | Repos |
|---|---|---|
| **0** | Publish the pinned leaves so path deps can become registry deps | safe-read (0.2.0), archive-core (in archive-forensic), forensic-vfs-engine; forensic-vfs already published (0.4.3, done) |
| **1** | Cheap requirement bumps + drop paths | ad1-forensic & livedisk-forensic: bump `safe-read` req `"0.1"`→`"0.2"`, drop path; disk-forensic: archive-core path→registry |
| **2** | Drop the `forensic-vfs` `[patch]` cluster | forensic-vfs-mount (and any residual patchers) |
| **3** | Move everything already movable-now (the 104) | all non-pinned fleet repos, folder by folder |
| **4** | Move the mount/VFS tip last | 4n6mount (path→forensic-vfs-engine, archive-core, memf-\*; patch→6 readers) |

`ntfs-forensic` needs no wave — its `forensic-vfs` patch was already removed and it now pins the
registry version (`"0.4.3"`), so it moves with the general Wave-3 batch.

### Option B — one-commit VFS/mount cluster

Move the mutually-pinned cluster as a **single commit**. Because every pin inside it is
*internal* to the set, the relative `../<sibling>` path deps stay resolvable after the move —
nothing has to be published first (the cluster spans the new `knowledge/`, `archive/`,
`memory/`, `filesystem/`, and `vfs/` folders, which is fine — the pins are what must stay
resolvable, not the folder layout):

```
{ safe-read, ad1-forensic, forensic-vfs, forensic-vfs-engine,
  archive-forensic, memory-forensic, forensic-vfs-mount,
  4n6mount, ntfs-forensic }   →  components/<folder>/  in ONE commit
```

Everything else (the remaining movable-now repos) moves independently in any order. Option B
trades "publish-first" ceremony for a larger atomic commit; Option A keeps each step small and
independently verifiable. **Recommendation to weigh:** Option A if you want each move CI-green
before the next; Option B if you'd rather not cut Wave-0 publishes just to relocate folders.

Cross-cutting caveats regardless of option:
- **browser-forensic:** delete the stale `.claude/worktrees/` checkouts *before* moving — they
  are the only thing that reads as a cross-repo dep.
- **srum-forensic:** the `ese-test-fixtures` git dep resolves from the remote regardless of
  on-disk location, so the move is safe; it is a hygiene pin only.

---

## 4. Excluded repos (not the forensic fleet)

Three groups. Group A is non-forensic. Group B is forensic-*domain* but sits **outside the Rust
fleet-crate layer architecture** (a Python tool, an Electron app, a dashboard product, a
tutorial) — so it does not belong in `components/`. Group C is fleet-adjacent but **pending a
rewrite** (parked out of the fleet for now, not abandoned).

### Group A — non-forensic (as supplied)
pipeguard, pipeguard-pro, clawback, clawpot, clawscan, clawtrader, ccchat, alaya,
multiai, general, hacker-film-mockup, mgrs, npmls, stem-branch, StrideMark, tl,
edng, domfuzz, 1-click-github-sec, clusterpoi, nameback, nameback.bak.

*(pipeguard-pro is one of the 8 audit "pinned" repos — path→pipeguard — but it is non-fleet, so
its pin is irrelevant to the fleet move.)*

### Group C — pending rewrite (returns to the fleet later, not abandoned)
| repo | note |
|---|---|
| RapidCollect | live-acquisition collector — **pending rewrite**; returns to `acquisition/` afterward. Left the fleet count for now (83 → 82). |
| chat4n6 | pending rewrite (grouped with RapidCollect). |

### Group B — forensic-domain, but not a fleet layer crate (evidence below)
| repo | evidence (description / README) | why excluded |
|---|---|---|
| ma2tl | "Apple Unified Logs converter for ma2tl" — a **Python** DFIR tool (mac_apt → timeline) | Python, not a Rust fleet crate; derived from external ma2tl/mac_apt |
| doc4n6 | "Forensic document investigation tool. An **Electron** desktop app backed by a **Python MCP** server" | Electron + Python; violates the egui single-binary standard; not `cargo install`-able |
| web3-forensic | "Blockchain forensic investigation **dashboard** for web3 examiners and legal teams" | standalone product/dashboard, not a `components/` layer crate |
| signal-cli-api | "Native REST + WebSocket API bridge for signal-cli" (Signal bots/integrations) | not forensic |
| shepherd | "One screen. Every agent. Full control." — agent-management UI | not forensic |
| SQLite_Forensics | "SQLite Main Database File Header Parser — Tutorial Video: …" | tutorial/learning repo, superseded by `sqlite-forensic` |
| forensic-justice | no Cargo `description`, no README content found in the checkout | **user-confirmed not part of the fleet** |

---

## 5. Ambiguous-repo verdicts (with evidence)

Each verdict is backed by the repo's own `[package].description` / README first line.

| repo | verdict | folder | evidence | note |
|---|---|---|---|---|
| **ufed** | FLEET | container | "Pure-Rust Cellebrite UFED physical dump reader — UFD XML segment mapping over `.bin` data files." | Reads a physical-dump acquisition image → sector stream = CONTAINER (mobile). |
| **atx-forensic** | FLEET | parser | "Reader/decoder for Apple ATX (AAPL) texture-image containers — iOS UI image caches … decodes ASTC (incl. LZFSE-wrapped) payloads to RGBA." | Interprets an application artifact (iOS image cache) → PARSER. |
| **leveldb-forensic** | FLEET | parser (**was filesystem in draft**) | "Chrome/Chromium Local Storage and Session Storage decoder … reads every raw SSTable/WAL record incl. tombstones." | LevelDB is a key-value application store, not a filesystem — same slot as sqlite-forensic/ese-forensic. |
| **peripheral-forensic** | FLEET | parser | "External-device connection forensic **reader**: parses setupapi.dev.log and SYSTEM-hive device keys into typed DeviceConnection records." | A reader/parser of two artifact sources. |
| **usb-forensic** | FLEET | parser | "USB device-history **correlation engine** — reconstructs USB connection history from **every** Windows artifact and scores cross-source timestamp consistency." | A domain artifact-interpreter → `parser/`; the capstone slot (issen) is reserved for fleet-wiring only (see §6 Resolved). |
| **bluetooth-forensic** | FLEET | parser | "read-only decoder for Windows Bluetooth pairing/connection evidence under …BTHPORT… + bluetooth4n6 CLI." | SYSTEM-hive artifact reader → PARSER (peer of peripheral-forensic). |
| **snapshot-forensic** | FLEET | history (**was container in draft**) | "Reader for snapshot & backup container formats (temporal filesystem reconstruction) — APFS snapshots, Time Machine, btrfs, VSS-adjacent." | A concrete `[H]` state-history reader → `history/` (alongside vsc-forensic); early scaffold. |
| **ad1-forensic** | FLEET | archive (**was vfs in draft**) | "AD1 / FTK Custom Content logical container" — a logical file tree via `disk_forensic::logical::open`, not a raw disk. | Packaging/`ArchiveOpen`, not a mount component. |
| **ma2tl / signal-cli-api / shepherd** | NON-FLEET | — | see §4 Group B / A | ma2tl = Python; signal-cli-api & shepherd = not forensic. |

**usb-forensic vs peripheral-forensic — should they merge?** They share the *domain* (device
connection history) but sit at **different layers**: peripheral-forensic is the artifact
**reader** (setupapi + registry → records); usb-forensic is the cross-artifact **correlation
engine** (scores consistency across every source). **Resolved: keep separate** — both live in
`parser/` (reader + correlator are distinct crates; usb-forensic consumes peripheral-forensic's
records), while `orchestration/` stays reserved for the single fleet-wiring capstone (issen).

---

## 6. Open questions for the human

None — all resolved (see the Resolved block below). The taxonomy is fully settled.

### Resolved (recorded for the reviewer)

- **forensic-hashdb → `knowledge/`** — forensic reference data (NSRL / malware / LOLDrivers IOC
  hash sets) is domain knowledge, not domain-agnostic tooling.
- **`volume/` dropped, no placeholder** — empty after vsc-forensic → `history/`; a future LVM
  reader would fold into `partition/` or reintroduce its own folder then.
- **useract-forensic + usb-forensic → `parser/`** — domain artifact-interpreters (user-activity
  and USB-history correlation), moved out of `orchestration/`, which stays reserved for the
  single fleet-wiring capstone (issen).
- **`history/` folder groups the whole `[H]` domain** — the `[H]` trait **vocabulary**
  (state-history-forensic, moved from `knowledge/`) sits with its concrete readers vsc-forensic
  (from `volume/`) and snapshot-forensic (from `container/`), the way `vfs/` groups the VFS
  contract + engine + mount + readers.
- **`utility/` folder added** — safe-read, blazehash, jsonguard, timeglyph moved out of
  `knowledge/` as generic (non-domain) tooling libraries.
- **cfb-forensic → `parser/`** — OLE/CFB carves an artifact-container for deleted-stream residue
  rather than peeling a general VFS layer; moved out of `archive/`.
- **blob-decoder → `parser/`** — binary decoder/deserializer (bplist/protobuf/gzip/zlib/snappy/
  base64/utf16/json), same logic as shellitem; moved out of `knowledge/`.
- **shellitem → `parser/`** — ITEMIDLIST binary deserializer; moved out of `knowledge/`.
- **iso9660-forensic + udf-forensic → `filesystem/`** — confirmed `FileSystemOpen` optical
  filesystems.
- **forensic-justice → Excluded** — user-confirmed not part of the fleet.
- **usb-forensic / peripheral-forensic → keep separate** — reader (peripheral-forensic) and
  correlation engine (usb-forensic) are distinct crates, both in `parser/`.
- **Adopted as drafted:** `vfs/` kept as one folder (abstraction + mount tools together);
  protobuf-forensic in `parser/`; the planned-but-absent graph repos (cas-forensic,
  sigstore-forensic) get a reserved `graph/` slot, added when the repos exist.
  (`velociraptor-parser` is dropped — not ours.)
