# Fleet Test-Data Catalog

Single source of truth for **all forensic test corpus across the SecurityRonin fleet** — what
each artifact is, where real data came from, and how synthetic data was made. Lives in `issen`
(the orchestration repo) because it spans every crate.

_Compiled 2026-06-09. Sizes are on-disk (`du`). Most large real datasets are **gitignored** —
download/regenerate per the provenance notes; they are not committed._

## Validation tiers

Every entry below is tagged **T1/T2/T3** by the fleet Evidence-Based Rigor axis — *who vouches for
the ground truth*, not whether the bytes are "synthetic":

- **T1** — an independent third party authored the artifact **and** the answer key, **or** it is
  real-world data (real disk/memory images, published corpora, genuine OS artifacts, real carved
  files — even small ones).
- **T2** — real engine/tool **output** whose ground truth is derivable from documented construction
  **or** confirmed by an **independent oracle**, but *we* chose the scenario (images minted with
  `qemu-img`/`mkfs`/`hdiutil`/`sgdisk`/… and reconciled against Sleuth Kit, `qemu-img`, `udfinfo`,
  a reference codec, …). A minted/synthetic fixture **with** an independent oracle is **T2, not T3**.
- **T3** — we authored **both** the fixture and the expected answer with nothing independent
  vouching (hand-built byte buffers, spec-exact detection fixtures, PRNG/fuzz corpora, pure
  synthetic schemas).

Entries bundling artifacts of different tiers carry the headline tier plus a `(mixed: …)` note.

## Legend & classification

| Class | Meaning |
|---|---|
| **REAL — external** | Captured/published by a third party (CTF, vendor, lab). Carries source license. |
| **REAL — self-collected** | Genuine OS artifacts we collected from a real/controlled host (UAC, Velociraptor, `hdiutil`, `qemu`). Real telemetry, not fabricated. |
| **SYNTHETIC** | Fixture the code/tooling builds (hand-written bytes, `mkfs`/`qemu-img`/`hdiutil`-generated empties, reference-compressor round-trips). |
| **VENDORED** | Third-party corpus copied in for coverage (attack-sample repos, format standard suites). Not ours. |
| **FUZZ** | Coverage-guided libFuzzer corpora — machine-evolved mutations, not curated samples. |

**Provenance confidence:** ✓ confirmed (documented in-repo or inspected this session) · ~ inferred
(agent reasoned from filenames/test code, not explicitly documented) · ? undetermined.

---

## Summary — the big real datasets (issen/tests/data)

| Dataset | Size | Class | Source |
|---|---|---|---|
| Magnet Virtual Summit 2023 CTF — Win11 (`PC-MUS-001.E01`) | 49 GB | REAL-ext | Magnet/Champlain DFA |
| Magnet Virtual Summit **2025** CTF (iOS 18 / Android 14 / Win 11 / Chromebook) | *pending download* | REAL-ext `?` | Hexordia (K. Pagano) + Champlain DFA / NIST CFReDS |
| DEF CON DFIR CTF 2018 (`MaxPowersCDrive.E01`) | 29 GB | REAL-ext | DEF CON / D. Cowen |
| Josh Hickman iOS 17.3 image (Apple Biome **SEGB** streams) | 22 GB (.tar.gz) | REAL-ext | Joshua Hickman / DigitalCorpora |
| Josh Hickman **macOS Big Sur** image (APFS, split EWF in zip) | 32 GiB zip → 80 GB image | REAL-ext | Joshua Hickman / thebinaryhick.blog |
| DFIR Madness "Stolen Szechuan Sauce" Case 001 (both hosts, full) | ~13 GB | REAL-ext | dfirmadness.com |
| Hal Pomeranz "Linux Forensic Scenario" (UAC, incl. `avml.lime`) | 5.9 GB | REAL-ext | Hal Pomeranz / righteousit.com |
| Collection-A380 (**Velociraptor**, Win11 24H2) | 2.2 GB | REAL-self | self, Velociraptor offline collector |
| SecurityNik TOTAL RECALL 2024 (memory) | 1.2 GB | REAL-ext | Nik Alleyne — securitynik.com / github.com/SecurityNik/CTF |
| CyberSpace CTF 2024 — "Memory" (memory) | 671 MB | REAL-ext | CyberSpace CTF 2024 (CTFtime #2428) |
| CyberDefenders lab #78 "DeepDive" (memory) | 537 MB | REAL-ext | cyberdefenders.org |
| Volatility `cridex.vmem` | 38 MB | REAL-ext | Volatility Foundation public sample |
| LogHub `OpenSSH_2k.log` — real sshd `auth.log` | 220 KB | REAL-ext | logpai/loghub (ISSRE'23) |
| BitLocker oracle `bdetogo.raw` (`bitlocker-forensic`) | 64 MB | REAL-ext | log2timeline/dfvfs (Apache-2.0) |
| Lone Wolf 2018 — Win10 `SYSTEM` hive (BTHPORT zero-pairings edge case) | 12 MB hive (carved from 12.9 GB image) | REAL-ext | Digital Corpora / GMU CFRS 780 (T. Moore) |
| FileVault CoreStorage oracle `fvdetest.qcow2` (`filevault-forensic`) | 16 MB | REAL-ext | log2timeline/dfvfs (Apache-2.0) |
| BitLocker `bitlocker-1.dd` — AES-128-CBC (0x8002) (`bitlocker-forensic`) | 100 MB | REAL-ext | picoCTF 2025 |
| BitLocker `vault.raw` — XTS-128 (0x8004) (`bitlocker-forensic`) | 2 GB | REAL-ext | BelkaCTF6 (**not redistributable**) |
| BitLocker `m8003/m8004/m8005.raw` — AES-256-CBC / XTS-128 / XTS-256 | 133 MB ea. | SYNTHETIC | self-minted (manage-bde) |
| BitLocker `sk8004.raw` + `.BEK` — startup-key (0x0200), XTS-128 | 128 MB | SYNTHETIC | self-minted (manage-bde -StartupKey) |

**Encryption-layer Tier-1 oracles (dfvfs, Apache-2.0).** Third-party images with
*published* unlock keys — genuine Tier-1 for the decryptor crates. Full provenance
in each repo's `tests/data/README.md`; not in `issen/tests/data/` (env-gated,
downloaded).
- `bdetogo.raw` — BitLocker-To-Go, md5 `fcba22f9363388101ae66c741588bc45`, password
  `bde-TEST`, method 0x8000 (AES-128-CBC + Elephant Diffuser). Oracle for
  `bitlocker-core`; validated via `pybde`. URL:
  <https://raw.githubusercontent.com/log2timeline/dfvfs/main/test_data/bdetogo.raw>
- `fvdetest.qcow2` — CoreStorage/FileVault 2 (AES-XTS), md5
  `dd7b1d584f2e07112ec7003d5fcd9864`, password `fvde-TEST`, CS partition at LBA 40.
  Oracle for `filevault-core`; validated via `pyfvde`. URL:
  <https://raw.githubusercontent.com/log2timeline/dfvfs/main/test_data/fvdetest.qcow2>

**BitLocker cipher-method oracles (`bitlocker-core`, validated via `pybde`; kept in
`/tmp`, env-gated, document-don't-commit).** Cover the full modern method table:
- `bitlocker-1.dd` — **Tier-1** (picoCTF 2025 Bitlocker-1), md5
  `22c3492cbc26ff648df066e1ed5329a7`, password `jacqueline`, method **0x8002**
  (AES-128-CBC, no diffuser), bare volume @0.
- `vault.raw` (from BelkaCTF6 "Bogus Bill" `vault.vhdx`) — **Tier-1**, md5
  `faac779e252ee133b48f26c878168467`, recovery password
  `590238-514580-359986-088242-029766-319495-410509-636911`, method **0x8004**
  (XTS-AES-128), BitLocker volume @ byte 16777216. **License: Belkasoft CTF — not
  confirmed redistributable; provenance only, never committed.**
- `m8003/m8004/m8005.raw` — **Tier-2 self-minted** (Parallels Win11 `manage-bde`;
  we authored them, so redistributable), partition @ byte 65536, recovery-password
  protectors: m8003 = **0x8003** (AES-256-CBC) rk `068002-…-375705`; m8004 = **0x8004**
  (XTS-128) rk `435743-…-447194`; m8005 = **0x8005** (XTS-256) rk `031174-…-262174`.
  Ground truth: `/tmp/bde-mint-oracle/GROUND-TRUTH.md`. (0x8000 = the dfvfs `bdetogo.raw`
  above; 0x8001 AES-256-CBC+diffuser is deferred — Vista/7-only, un-mintable on Win11.)
- `sk8004.raw` + `<GUID>.BEK` — **Tier-2 self-minted** startup-key oracle (Parallels
  Win11 `manage-bde -protectors -add -StartupKey`), md5 `d12f27801f52256cc3a900820cc1466d`,
  partition @ byte 65536, method **0x8004** (XTS-128). Protectors: **startup key**
  (`0x0200`, external-key GUID `F8A2B017-…`, key in the `.BEK`) + recovery safety net
  `154583-…-073667`. `pybde read_startup_key` verified; oracle for
  `bitlocker-core::unlock_with_startup_key`. Ground truth:
  `/tmp/bde-startupkey-oracle/GROUND-TRUTH.md`.

---

## A. Real case & CTF datasets — `issen/tests/data/`

### A1 · DEF CON DFIR CTF 2018 — `MaxPowersCDrive.E01` (29 GB) · REAL-ext ✓ · **T1**
C: drive of user `mpowers`. EWF case "MaxPowers-1", examiner "Professor Frink", acquired 2018-05-05
via f-response. **MD5** `10c1fbc9c01d969789ada1c67211b89f`. Has pagefile/swapfile, no hiberfil.
Source: hecfblog Daily Blog 451; writeup or10nlabs.tech. **Used by** `ntfs-forensic` boot-sector
ground-truth (see C-layer). Redistribution: DEF CON public CTF — non-commercial.
**Download:** <https://www.hecfblog.com/2018/08/daily-blog-451-defcon-dfir-ctf-2018.html> (Image 3;
original `https://www.dropbox.com/s/jvaqb4rfi3jojbk/Image3.7z` may be expired).

### A2 · Magnet Virtual Summit 2023 CTF — `PC-MUS-001.E01` (49 GB) · REAL-ext ✓ · **T1**
Win11 physical drive. By Jessica Hyde + Champlain College DFA for Magnet. EnCase 6, acquired
2023-01-07. **MD5** `522df9db8289f4f8132cf47b14d20fb8`. Contains `hiberfil.sys` (MFT #54, 3.37 GB)
— real corpus for the `memf-format` hiberfil provider. Redistribution: Magnet/Champlain — verify.
**Download:** <https://getdataforensics.com/capture-the-flag/> (Magnet Virtual Summit 2023 — Win11).

### A2b · Magnet Virtual Summit **2025** CTF — Hexordia (iOS 18 / Android 14 / Win 11 / Chromebook) · REAL-ext `?` (download pending) · **T1**

By the **Hexordia** team (Kevin Pagano) with Champlain College DFA interns, for Magnet Forensics.
Scenario: personas "Ruth" + "Mary", Nov–Dec 2024, across mobile/computer/web. Authoritative public
host: **NIST CFReDS** <https://cfreds.nist.gov/all/Hexordia/2025MVSCTF> (documents per-file hashes).
Winners writeup: <https://www.magnetforensics.com/blog/announcing-the-winners-of-the-2025-magnet-virtual-summit-ctf/>.
A Google Drive mirror (<https://drive.google.com/drive/folders/1qLwXFZTZidkx1tWpG8uenVQnX6zWF-Oa>)
holds `userbss.ad1` (AccessData **AD1** logical image) among others, but is **Google-quota-blocked**
as of 2026-06-29 — pull from CFReDS instead. **Bytes not yet downloaded**; sizes + MD5/SHA256 to be
filled from CFReDS on acquisition. Detail: `issen/tests/data/README.md` → `magnet-summit-2025-ctf/`.

### A3 · DFIR Madness "Stolen Szechuan Sauce" Case 001 (~13 GB) · REAL-ext ✓ · **T1**
Folder: `tests/data/dfirmadness-szechuan-sauce/` (folder name predates the
DC host; now holds **both**). By James Smith (dfirmadness.com). **Downloaded in full**
(2026-06-09) — all 11 files:

| File | Size | Note |
|---|---|---|
| `DESKTOP-E01.zip` | 6.4 GB | Win10 desktop disk · MD5 `71C5C3509331F472ABCDF81EB6EFFF07` |
| `DC01-E01.zip` | 4.84 GB | Server 2012R2 DC disk |
| `DESKTOP-SDN1RPT-memory.zip` | 766 MB | desktop RAM |
| `DC01-memory.zip` | 535 MiB | DC RAM |
| `Desktop-SDN1RPT-pagefile.zip` | 212 MB | desktop pagefile |
| `DC01-pagefile.zip` | 13 MB | DC pagefile |
| `case001-pcap.zip` | 151 MB | network capture |
| `DESKTOP-SDN1RPT-Protected Files.zip` | 17 MB | pre-extracted |
| `DC01-ProtectedFiles.zip` | 12 MB | pre-extracted |
| `DESKTOP-SDN1RPT-autorunsc.zip` | 279 KB | autoruns |
| `DC01-autorunsc.zip` | 177 KB | autoruns |

**Download:** case page <https://dfirmadness.com/the-stolen-szechuan-sauce/> · direct per-file
hotlinks `https://dfirmadness.com/case001/<file>` (e.g.
<https://dfirmadness.com/case001/DC01-E01.zip>, `…/DESKTOP-E01.zip`, `…/case001-pcap.zip` — every
filename in the table above). **Used by** `usnjrnl-forensic` integration tests (`#[ignore]`, desktop
E01); the DC01 `SYSTEM` hive (§A3b) is consumed by `forensicnomicon`'s
`tests/services_dc01_isolation.rs` (env-gated on `ISSEN_DC01_SYSTEM_HIVE`) to
prove its known-good service-binary catalog isolates the `coreupdater.exe`
service masquerade (453 services → 7-entry System32-root OwnProcess gate set →
`coreupdater.exe` the lone uncatalogued one). `case001-pcap.zip` is also the reference archive for
**4n6mount**'s on-demand archive-read e2e (`tests/e2e_archive_read.rs`, env-gated on
`FN_E2E_ARCHIVE_ZIP`): it reads the `.zip` through the mount's own `archive_core::Archive` reader,
picks the member at the 66% position, and asserts its content magic matches its extension —
`FN_E2E_ARCHIVE_ZIP=<path>/case001-pcap.zip cargo test --test e2e_archive_read -- --nocapture`
verifies `case001.pcap` (197,583,252 bytes, pcapng magic `0a 0d 0d 0a`). Redistribution:
dfirmadness.com — educational/research.

> **Reference assets & on-demand extractions.** The committed permanent data is the 11 raw zips only.
> The published answer-key + writeup HTML lives in the clean subdir `szechuan-sauce-writeups/`
> (reference-only). Registry hives and E01 segments are **not persisted under `~/src`** — extract them
> on demand to `/tmp` (hives per §A3b, regenerable from `DC01-ProtectedFiles.zip`; the disk image by
> unzipping `DC01-E01.zip`/`DESKTOP-E01.zip`). Consuming tests point at the `/tmp` path and skip when
> absent. All paths are clean (no spaces/quotes/em-dashes), safe in Rust `include!`/`Path::new`
> literals and shell. Per-file MD5 manifest (all 11 files): `issen/tests/data/README.md` →
> `dfirmadness-szechuan-sauce/`; this catalog is the cross-reference.

#### A3b · Registry hives extracted from `DC01-ProtectedFiles.zip` (loose, gitignored) · REAL-ext ✓ · **T1**

Used by the registry parsers' real-data CADET category tests
(`crates/parsers/issen-parser-{runkeys,userassist,shimcache,sam,shellbags,registry,typedurls,svcdiff}/tests/real_hive_category.rs`,
which skip cleanly when absent). **NO download — extract from A3's `DC01-ProtectedFiles.zip`:**

```sh
cd tests/data/dfirmadness-szechuan-sauce
unzip -o -j DC01-ProtectedFiles.zip Protected/SAM Protected/SECURITY Protected/software \
  Protected/system Users/Administrator/NTUSER.DAT -d /tmp/szechuan-hives
cd /tmp/szechuan-hives && mv -f software SOFTWARE && mv -f system SYSTEM
```

Yields `/tmp/szechuan-hives/{SAM,SECURITY,SOFTWARE,SYSTEM,NTUSER.DAT}` (all `regf`; ephemeral — re-extract per session, not persisted under `~/src`). MD5s:

| Hive | Bytes | MD5 |
|---|---|---|
| `SAM` | 262144 | `36456b3ccffc110e00c4a7ec5240abb1` |
| `SECURITY` | 262144 | `919ea108536018ab651e91e2984682e0` |
| `SOFTWARE` | 45875200 | `477c82a44f2f59f3f36afc0f13413cc3` |
| `SYSTEM` | 12845056 | `05cd86230d5bdbcade8fd6da1d5313a4` |
| `NTUSER.DAT` (Administrator) | 524288 | `9f540e3d52a70c8060a54d0d8ee7e1bf` |

**`UsrClass.dat` + `Amcache.hve` (carved from the Desktop E01, NOT a protected-files zip)** — used by
`issen-parser-{comhijack,amcache}/tests/real_hive_category.rs`. Carve with the committed `issen-disk`
examples (`extract_usrclass` / `extract_amcache` / `extract_security`):

```sh
unzip -o -j dfirmadness-szechuan-sauce/DESKTOP-E01.zip '*.E0*' -d /tmp/desktop-e01   # ~6.4GB, 4 EWF segments
E01=/tmp/desktop-e01/20200918_0417_DESKTOP-SDN1RPT.E01
cargo run --release --example extract_usrclass -- "$E01" tests/data/case001-hives
cp -f tests/data/case001-hives/UsrClass-ricksanchez.dat tests/data/case001-hives/UsrClass.dat   # primary user
cargo run --release --example extract_amcache  -- "$E01" tests/data/case001-hives
```

| File | Bytes | MD5 |
|---|---|---|
| `UsrClass.dat` (ricksanchez — Win10 per-user COM CLSID) | 3407872 | `5e28f59f5414e754b4e6e4868fa9d7a0` |
| `Amcache.hve` (`Windows\AppCompat\Programs\`, program execution) | 1572864 | `0512afeba75e21c724fa75a365bb81d1` |

`UsrClass-ricksanchez.dat` also backs **peripheral-forensic**'s shellbag `BagMRU`
differential (`peripheral-forensic/core/tests/shellbag_oracle_diff.rs`, env-gated on
`SHELLBAG_TEST_HIVE`): its `BagMRU` records drives **Z:** (`My Computer\Z:\`) and **E:**
(`E:\`, with `E:\FTK Imager` browsed on it). **Independent oracle = regipy + libyal
pyfwsi (libfwsi)** — `pip install 'regipy[full]'`; the bundled
`core/tests/oracle/shellbags_oracle.py` decodes the same tree and the test reconciles
drive letters + path. **T1.** Our walk's `Z:` is confirmed by libfwsi; `E:` is a documented
gap (a delegate-wrapped volume item the `shellitem` primitive does not yet decode — see
`peripheral-forensic/docs/validation.md`). Run:
`SHELLBAG_TEST_HIVE=/tmp/case001-hives/UsrClass-ricksanchez.dat cargo test -p peripheral-core --test shellbag_oracle_diff -- --nocapture`.

The `SECURITY` hive's `Policy\Secrets` **is** present (`$MACHINE.ACC`/`DPAPI_SYSTEM`/`NL$KM`) and now
backs `issen-parser-lsasecrets/tests/real_hive_category.rs` (AccountActivity, T1003.004).

Still-unsatisfiable from this corpus (parsers left untagged, not faked): **DCC2 cache** (`issen-parser-dcc2`).
`SECURITY\Cache` has **0 `NL$n` slots on every image we hold** — verified by driving `parse_lsadump`
over Case-001 DC **and** Desktop, DEF CON `MaxPowers`, and Magnet `PC-MUS-001` (all 0). DCC2 is cached
on domain-member workstations with cached-logon enabled; none of our images materialized it. (`Policy\Secrets`
*is* present in the SECURITY hives — a viable alternate path if issen's lsadump is extended beyond DCC2.)
`svcdiff` & `comhijack` were NOT data gaps — they were parser bugs, fixed in **winreg-artifacts 0.1.2**
(offline `ControlSet001` resolution / `UsrClass.dat` root CLSID) and now tagged.

#### A3c · LZNT1 real-stream regression fixtures (`ntfs-forensic/tests/data/`) · REAL-ext ✓ · **T1**

Carved from A3's **DC01 C: drive** E01 to pin the `lznt1` LZNT1 codec to a genuine on-disk
NTFS-compressed stream with **TSK as the independent plaintext oracle** (`ntfs-forensic/core/tests/lznt1_real.rs`).
Source file `C:\ProgramData\Microsoft\Windows\WER\...\Report.wer` — **MFT inode 437**, a
`$DATA Non-Resident, Compressed` stream of actual size **1832 bytes** in a single 16-cluster LZNT1 unit
occupying one allocated cluster (**LCN 291553**). NTFS partition at sector **offset 718848**, cluster size **4096**.

```sh
E01=".../extracted/E01-DC01/20200918_0347_CDrive.E01"
istat  -o 718848 "$E01" 437                                   # $DATA Non-Resident, Compressed  size 1832 → LCN 291553
icat   -o 718848 "$E01" 437      > lznt1_real.expected         # TSK-decompressed plaintext (1832 B, oracle)
blkcat -o 718848 "$E01" 291553 1 > lznt1_real.bin             # raw on-disk LZNT1 stream (one 4096 B cluster)
```

Verified `ntfs_core::decompress(lznt1_real.bin)` truncated to 1832 B equals `lznt1_real.expected` byte-for-byte.

| File | Bytes | MD5 |
|---|---|---|
| `lznt1_real.bin` (raw LZNT1 stream, 1 cluster) | 4096 | `8c791f1d34a7f4a9aaeaddce71210a26` |
| `lznt1_real.expected` (TSK `icat` plaintext) | 1832 | `f4cc46d7e07ab76540a46471622e10af` |

#### A3d · Recycle Bin `$I` index extracted from A3's DC01 C: drive (trash-forensic Windows Recycle Bin wiring validation) · REAL-ext ✓ · **T1**

Carved from A3's **DC01 C: drive** E01 to validate **`trash-forensic`**'s Windows Recycle Bin
wiring (`trash-core::windows::parse_index` + `scan_pairs`, the `$I`⇄`$R` pair walker) against a
genuine on-disk `$I` index, with **`rifiuti-vista` as the independent oracle**. (Windows
`$Recycle.Bin` is one leg of `trash-forensic`'s cross-OS trash family — there is no separate
recyclebin repo.) The single Recycle Bin entry on the DC lives under the Administrator SID
(`S-1-5-21-2232410529-1445159330-2725690660-500`): `$IU2L112.txt` (**MFT inode 87102**), paired with
`$RU2L112.txt`. It is a **version-1** `$I` (544 B = 24-byte header + 520-byte fixed UTF-16LE name).
NTFS partition at sector **offset 718848**.

```sh
E01=".../extracted/E01-DC01/20200918_0347_CDrive.E01"
fls  -o 718848 "$E01" 85070                       # SID dir: $IU2L112.txt = inode 87102
icat -o 718848 "$E01" 87102 > '$IU2L112.txt'      # the $I index (544 B)
```

Decoded fields (`trash-forensic`'s Windows parser agrees with `rifiuti-vista -f json`):
original path `C:\FileShare\Secret\SECRET_beth.txt`, original size **28** bytes, deletion time
**2020-09-19T03:34:27Z** (FILETIME `132449600672980000`; our `timestamp_ns` `1600486467298000000`
keeps the .298 s sub-second that rifiuti truncates). Emitted as one `FileDelete` /
`source = RecycleBin` event. (This is the DC file-share copy; the famous DESKTOP-SDN1RPT desktop copy
of `SECRET_beth.txt` referenced by CTF answers F24/F43 is on the **DESKTOP** image, not in this
DC-only E01.)

| File | Bytes | MD5 |
|---|---|---|
| `$IU2L112.txt` (raw v1 `$I` index, icat inode 87102) | 544 | `ba140375cf27bf63268784cd71a18827` |

#### A3e · Single `$MFT` record from A3's DC01 C: drive (FILETIME 100 ns-precision guard) · REAL-ext ✓ · **T1**

One 1024-byte `$MFT` FILE record carved from A3's **DC01 C: drive** E01 to guard `issen-mft-tree`'s
FILETIME precision (the `mft` crate's `winstructs` truncates 100 ns → µs). Entry **74419** (seq 1):
`Classic_{37E2F32E-C821-4094-B429-2B4E8EA810AA}.settingcontent-ms` — a benign WinSxS component-store
record. NTFS partition at sector **offset 718848**. **TSK `istat` is the independent oracle**: `$SI`
Modified `2013-06-18T15:02:18.305856600Z`, Created/Accessed `2013-08-22T06:57:33.897202300Z` — each
trailing 100 ns digit (`600`, `300`) is what a microsecond-truncating converter drops to `…000`.

```sh
E01=".../E01-DC01/20200918_0347_CDrive.E01"
icat -o 718848 "$E01" 0 | dd bs=1024 skip=74419 count=1 of=dc01_mft_record_74419.bin
```

| File | Bytes | MD5 | Location |
|---|---|---|---|
| `dc01_mft_record_74419.bin` | 1024 | `4c911975cff69016c3095553ed4540c6` | `issen/crates/issen-mft-tree/tests/data/` **and** `issen/crates/parsers/issen-parser-mft/tests/data/` (two-repo pattern, like A3a) |

Consumed by `from_mft_preserves_100ns_filetime_precision` (`issen-mft-tree/src/parse.rs`, the file
tree) and `parse_preserves_100ns_si_precision` (`issen-parser-mft/src/lib.rs`, the timeline ingester);
per-repo detail in [`issen-mft-tree/tests/data/README.md`](../crates/issen-mft-tree/tests/data/README.md).

#### A3a · Prefetch fixtures derived from A3 (committed in two repos) · SYNTHETIC-from-REAL ✓ · **T1** (mixed: also T2 — xpress-huffman codec vectors vs dissect.util oracle)

Three Win10 `.pf` files extracted from the Case 001 **Desktop** image above, small enough to commit
(provenance confirmed by parsing, not filename). Cross-ref the per-repo `tests/data/README.md`; do
not re-download — they come from `DESKTOP-E01.zip`.

| File | MD5 | Committed in | Decompressed |
|---|---|---|---|
| `COREUPDATER.EXE-157C54BB.pf` | `d3db6935c7ad9f93964b0893997af049` | `prefetch-forensic/tests/data/` + `issen/crates/parsers/issen-parser-prefetch/tests/data/` (depth test) | 24316 B, SCCA v30, the implant |
| `AUDIODG.EXE-AB22E9A6.pf` | `18bcdd9d31865769309053816e812811` | `prefetch-forensic/tests/data/` | 35954 B, run count 8 |
| `AM_DELTA.EXE-78CA83B0.pf` | `0d48c5b117a3c9e71b66d51fad454354` | `prefetch-forensic/tests/data/` | 6948 B |

`xpress-huffman/tests/data/` commits the Xpress-Huffman **codec** test vectors carved from two of
these (the `MAM\x04` payload with the 8-byte header stripped, plus the decompressed bytes):
`am_delta.xhuff` (md5 `f3548390c17ed5af3845ea830ea66d48`) / `am_delta.expected`
(`193b1fc2f87f4fac2afeea27aaaeb085`), and `audiodg.xhuff` / `audiodg.expected`. Generators + the
external-oracle validation (dissect.util byte-identical, windowsprefetch field-match) live in each
repo's `tests/data/README.md` and `docs/validation.md`.

### A4 · Hal Pomeranz "Linux Forensic Scenario" (Righteous IT) (5.9 GB) · REAL-ext ✓ · **T1**
Published challenge by **Hal Pomeranz** (Righteous IT), "Linux Forensic Scenario" contest
(2026-03-27): a Linux CI/CD-pipeline worker VM deliberately compromised (planted malware, hidden
high-CPU process, reverse shell on 22/tcp; single `worker` account with NOPASSWD sudo; jump host
192.168.4.35), then captured with **UAC** (github.com/tclahr/uac). Our `…234043.tar.gz` (5.9 GB,
incl. `memory_dump/avml.lime` ~5.5 GB) **is Hal's published download**; `…193807.tar.gz` (143 MB,
fs-only, CI) is a smaller companion capture. **Used by** `issen-parser-uac`, `issen-navigator`, AVML
provider + Linux process/module/network walking.
**Download:** scenario <https://righteousit.com/2026/03/27/linux-forensic-scenario/> · image (the
5.9 GB `…234043.tar.gz`)
<https://deerrunassoc-my.sharepoint.com/:u:/g/personal/hal_deer-run_com/IQAGrMUqVLwEQ4Ceus_70Pn0AVxMaWSs7POONKw6ss103Bc?e=4N5uje>
· class <https://archive.org/details/HalLinuxForensics/>. Redistribution: Hal Pomeranz / Righteous
IT — credit the author.

### A5 · Collection-A380 — **Velociraptor** (2.2 GB) · REAL-self ✓ · **T1**
`Collection-A380_localdomain-2025-08-10T03_41_20Z.zip`. Velociraptor offline collector v0.74.5,
artifact `Windows.KapeFiles.Targets` (`_SANS_Triage`). Host `A380` / Win11 Pro 24H2 / standalone /
operator `4n6h4x0r`, 2025-08-10. Disk-artifact triage only (no RAM), 2,952 files. Benign baseline
(real daily-driver host), **not** an intrusion scenario; virtualization undetected (may be bare
metal). **Used by** `issen-parser-velociraptor`, `issen-navigator`. Redistribution: self-generated
(contains personal artifacts — sanitize before external sharing).
**Download:** none — self-collected, not publicly hosted (regenerate with the Velociraptor offline
collector, `Windows.KapeFiles.Targets` + `_SANS_Triage`, on any Windows host).

### A6 · Memory-forensics CTFs · REAL-ext ✓ · **T1**
All four **confirmed** 2026-06-09 by inspecting the archive contents + web corroboration (not just
filenames). Not yet referenced by a committed test.

- **SecurityNik — TOTAL RECALL 2024** (1.2 GB zip): `SECURITYNIK-WIN-20231116-235706.dmp` (4.29 GB
  Win11 build 22621 crash dump; acquired with **DumpIt 3.0**; host `SECURITYNIK-WIN`, user
  `securitynik`) + sidecar `.json`. **SHA256**
  `cabe2fd543eac1cd2eab9ccd0a840d83481a3f00e16015287323b2cb44fe0686`. By Nik Alleyne.
  **Download:** <https://github.com/SecurityNik/CTF> · write-up
  <https://www.securitynik.com/2024/03/total-recall-2024-memory-forensics-self.html>.
- **CyberDefenders — lab #78 "DeepDive"** (537 MB zip): `banking-malware.vmem` (2.0 GB, Win7SP1x64).
  **Emotet** banking trojan, DKOM-hidden `vds_ps.exe`.
  **Download:** <https://cyberdefenders.org/blueteam-ctf-challenges/deepdive/> (free account).
- **CyberSpace CTF 2024 — "Memory"** (671 MB zip): `mem.dmp` (2.0 GB, MS Win x64 crash dump).
  recover-deleted-`flag.jpg` via PowerShell/AES/env-vars.
  **Download:** event <https://ctftime.org/event/2428> (30 Aug–01 Sep 2024; challenge files via the
  event / published write-ups).
- **Volatility Foundation — Cridex** (38 MB zip): `cridex.vmem` (512 MB, WinXP) — the canonical
  public Memory Sample. **Download:**
  <https://github.com/volatilityfoundation/volatility/wiki/Memory-Samples> (Cridex row; original
  `files.sempersecurus.org` mirror now returns 403).

Nine further **memory-forensic-owned** corpora live in `memory-forensic/tests/data/` (full
provenance in [`memory-forensic/tests/data/README.md`](../../memory-forensic/tests/data/README.md));
all gitignored + downloaded manually. MD5s for most are pending (download-then-hash):

- **13Cubed Mini Memory CTF** (1.3 GB zip, `13cubed-mini-memory-ctf/`): Win7 SP1 x86 (build 7601,
  profile `Win7SP1x86`). By Richard Davis. **Download:**
  <https://cdn.13cubed.com/downloads/mini_memory_ctf.zip> · solutions guide
  <https://cdn.13cubed.com/downloads/mini_memory_ctf_solutions_guide.pdf>.
- **13Cubed Windows Memory Forensics Challenge** (1.4 GB zip, `13cubed-windows-memory-forensics-challenge/`):
  Win10 x64 (build TBD — run `imageinfo`). By Richard Davis. **Info:** <https://www.13cubed.com/>.
- **Houseplant CTF 2020 — Imagery** (584 MB 7z, `houseplant-ctf-2020-imagery/`): Win10 (`win10`
  Volatility profile). **Info:** <https://ctftime.org/event/1041>.
- **InCTF International 2019 — NotchItUp** (342 MB 7z, `inctf-2019-notchitup/`): Win7 SP1 x64
  (build 7601, `Win7SP1x64`). By bi0s. **Write-up:**
  <https://blog.bi0s.in/2019/09/24/Forensics/InCTFi19-NotchItUp/>.
- **MemLabs Lab1 — Beginner's Luck** (151 MB 7z, `memlabs-lab1-beginners-luck/`): Win7 SP1 x64
  (build 7601). By stuxnet0 (MIT). **Source:** <https://github.com/stuxnet0/MemLabs>.
- **MemLabs Lab3 — The Evil's Den** (242 MB 7z, `memlabs-lab3-the-evils-den/`): Win7 SP1 x86
  (build 7601, `Win7SP1x86_23418`). By stuxnet0 (MIT). **Source:** <https://github.com/stuxnet0/MemLabs>.
- **OtterCTF 2018** (484 MB 7z, `otterctf-2018/`): Win7 SP1 x64 (build 7601). **Walkthrough:**
  <https://tcert.net/otterctf-2018-memory-forensic-walkthrough/>.
- **Sam Bowne CNIT 121 Project P5** (124 MB 7z, `samsclass-volatility-project/`): WinXP SP2 x86
  (build 2600, `WinXPSP2x86`). **Source:** <https://samsclass.info/121/proj/p5-Vol.htm>.
- **WannaCry memory analysis** (42 MB 7z, `wannacry-memory-analysis/`): Win7 x86 (build 7601) with an
  active WannaCry infection. By null0x4d5a. **Write-up:**
  <https://www.null0x4d5a.com/2017/05/memory-analsyis-of-wannacry-ransomware.html>.

Redistribution: SecurityNik & Volatility public; CyberDefenders educational license; CyberSpace CTF
event terms; 13Cubed / InCTF / OtterCTF / Houseplant / samsclass / WannaCry public-educational;
MemLabs MIT — verify before redistribution.

---

### A7 · Josh Hickman iOS 17.3 image — Apple Biome **SEGB** streams (22 GB `.tar.gz`) · REAL-ext ✓ · **T1**

Public iOS file-system image by **Joshua Hickman** (The Binary Hick), hosted by **DigitalCorpora** —
a synthetic test persona (`thisisdfir@gmail.com`), freely licensed for training/education/testing/
research. iPhone 11 (A2111), **iOS 17.3 build 21D50**, Cellebrite UFED full-file-system extraction.
Download (key-free S3):
<https://digitalcorpora.s3.amazonaws.com/corpora/mobile/iOS17/iOS_17_Public_Image.tar.gz> (22 GB);
image-creation doc (hashes, app list):
<https://digitalcorpora.s3.amazonaws.com/corpora/mobile/iOS17/iOS17-ImageCreation.pdf>; announcement
<https://thebinaryhick.blog/2024/09/14/triple-trouble-ios-16-android-14-and-ios-17-images-now-available/>.

- **Why it's here:** the **only public, committable-provenance source of real Apple Biome SEGB files**.
  iOS uses the *same* SEGB v1/v2 container as macOS (`/private/var/db/biome/streams/restricted/*/local`
  and `/private/var/mobile/Library/Biome/...`). **Used by** `segb-core` to validate its SEGB container
  reader against real Apple data + the ccl-segb reference oracle, publicly and reproducibly.
- **VALIDATED (2026-06-14):** segb-core reconciles **exactly** with the ccl-segb reference across
  **all 401 real iOS 17 Biome SEGB files** in this image (139 SEGB **v1** + 262 SEGB **v2**) — record
  counts match on every file, **401 PASS / 0 MISMATCH**. Streams include `_DKEvent.Safari.History`,
  `_DKEvent.Device.BatteryPercentage`, `MicroLocationVisit`, `Siri.SelfTriggerSuppression`,
  DuetActivityScheduler app-launch/kill, `unifiedMessageStream`, etc. The SEGB files live in
  `private/var/db/biome/streams/restricted/*/local/*` and
  `private/var/mobile/Library/.../Biome/.../local/*` — note these dirs unzip with restrictive Apple
  modes (0700), so `chmod -R u+rwX` is needed before scanning. (A prior macOS 15.7 private-stream
  check also matched 785/785; this iOS image is the public, reproducible, **both-variant** validation.)
- **macOS 26.5 (Tahoe) committed regression:** `segb-forensic/tests/data/biome/Device.Display.Backlight.tahoe26.v2.segb`
  — a real SEGB **v2** stream from Tahoe (build 25F71) whose post-magic header field is `0x08` vs iOS 17 v2's
  `0x07`; the v2 reader parses it (8 records, every CRC valid). Captured from a read-only mount of a
  `macos-tahoe-base` (cirruslabs, public) VM disk. Asserted in `core/tests/real_fixtures.rs::real_tahoe26_segb_v2_backlight`.
- **`iOS_17_Public_Image.tar.gz` MD5:** `e115f051d15178fa1334489e24c9f0fd` (22,132,295,131 bytes).
- **Structure:** a Cellebrite UFED package — `iOS_17/Cellebrite_Extraction/.../EXTRACTION_FFS 01/
  EXTRACTION_FFS.zip` (the full file system; biome streams live under
  `private/var/db/biome/streams/restricted/*/local` and
  `private/var/mobile/.../Library/Biome/`), plus an iTunes `Backup/…zip` and a `sysdiagnose/…tar.gz`.
  Extract the biome subset from the nested FFS zip (zip random access), then reconcile segb-core vs
  `ccl_segb_cli.py`. Stored under `issen/tests/data/Josh Hickman iOS 17 (Biome SEGB)/` (gitignored;
  only the biome subset kept on disk). Note: `App.MenuItem` is macOS-Tahoe-26-only, so it is **not**
  in this iOS image — this validates the SEGB *container*, not the App.MenuItem protobuf field mapping.

### A7b · Josh Hickman **macOS Big Sur** image — APFS, split EWF-in-zip (32 GiB zip → 80 GB image) · REAL-ext ✓ · **T1**

Public **macOS Big Sur** forensic reference image by **Joshua Hickman** (The Binary Hick), freely
licensed for training/education/testing/research (attribution). An 80 GB **APFS** virtual disk
(167,772,160 × 512-byte sectors) acquired 2021-02-20 with **FTK Imager 4.5.0.3** from an Arsenal-mounted
VM, packaged as a 22-segment split EWF inside one zip. Writeup:
<https://thebinaryhick.blog/2021/02/20/ios-14-macos-big-sur-lots-of-images/> (index
<https://thebinaryhick.blog/images/>).

- **Path:** `issen/tests/data/josh-hickman-mac-bigsur/macOS - BigSur.zip` (gitignored; download manually).
- **Zip MD5:** `1047921dcc695be98fa648ad54a111d6` (34,408,655,935 bytes).
- **Image hashes** (FTK, from the embedded `macOS-BigSur.E01.txt`): MD5 `768785635426d008df76200fbc421063`,
  SHA1 `e3a73cd1b750a851c12c7b608e95edbef1606504`.
- **Structure:** `macOS/macOS-BigSur.E01`–`.E22` (~1.57 GB **Deflated** zip entries) + `…E01.txt`. Pass
  the first segment to `ewf`; it follows the rest automatically.
- **Validated (Tier-1, 2026-06-29):** streamed the *full* 80 GB image through `ewf` opened zip-direct
  over the `DeflateSeekReader` (zran) path and recomputed the MD5 — `768785635426d008df76200fbc421063`,
  an **exact match** to FTK's acquisition hash. Independent third-party image + third-party answer key
  (FTK), so this is a Tier-1 end-to-end correctness check of the EWF zip-direct + seekable-DEFLATE
  segment reads on a real multi-segment macOS/APFS image (not a synthetic round-trip).
- **Why it's here:** real macOS/APFS test data (apfs-forensic, planned), and the live regression for
  issen's **EWF zip-direct + `DeflateSeekReader` (zran)** path — a genuine multi-segment Deflated
  E01-in-zip, the exact shape that exercises bounded-RAM seekable-DEFLATE segment reads.

### A8 · LogHub `OpenSSH_2k.log` — real sshd `auth.log` (220 KB) · REAL-ext ✓ · **T1**

Pre-journald **real** Linux SSH auth events (text `auth.log` syslog format) from a real `LabSZ`
server — unsanitized, with genuine attacker IPs / brute-force `Failed password` floods / invalid
users. 1999 lines, **md5** `72efdaaf373b8d6c8a809cc86b2a951f`. The 2k-sample slice of the loghub
OpenSSH dataset (ISSRE'23). **Used by** `issen-parser-linux` to validate `parse_auth_log` against
real evidence (the Hal Linux UAC corpus is journald-only, so it has no text `auth.log`): ingested as
`auth.log` → **519 events** (1 Accepted + 518 Failed), exact match to an independent grep oracle.
Stored at `tests/data/loghub-openssh/OpenSSH_2k.log`; rename/copy to `auth.log` to exercise discovery.
Redistribution: freely available for research; cite loghub (Zhu et al., ISSRE 2023).
**Download:** <https://raw.githubusercontent.com/logpai/loghub/master/OpenSSH/OpenSSH_2k.log>
(dataset: <https://github.com/logpai/loghub/tree/master/OpenSSH>)

## B. Disk-image / container-format fixtures

### B1 · qcow2-forensic — `tests/data/cirros-0.6.3-x86_64-disk.img` (21 MB) · REAL-ext ✓ · **T1** (mixed: also T2 qemu-img differential, T3 in-code synthetic buffers)
CirrOS 0.6.3 (repo-root `tests/data/`). Redistribution: CirrOS permissive.
**Download:** <https://download.cirros-cloud.net/0.6.3/cirros-0.6.3-x86_64-disk.img>.
**CI coverage is driven from committed bytes only** — every reader feature branch
(compressed clusters, unallocated/zero clusters, seek variants, refcount widths
1/2/4/8/16/32/64-bit, snapshot edge cases, header rejection arms) is exercised by
**in-code synthetic QCOW2 byte buffers** (no committed `.qcow2` files, no `qemu-img`);
builders: `testutil::test_qcow2`, `lib.rs::compressed_qcow2`/`qcow2_header_bytes`,
`refcount.rs::build_order`/`build`, `snapshots.rs::header`/`entry`, `header.rs::build`/`ext`
(see `tests/data/README.md`). The `qemu-img` differential + snapshot/backing/encryption
variants (`core/tests/real_images.rs`, `docs/validation.md`) remain the env-gated **Tier-1
correctness** path and do NOT drive the coverage gate.

### B2 · ewf-forensic — `tests/data/` · SYNTHETIC + VENDORED ✓ · **T2** (ewfacquire/libewf output; mixed: also T1 vendored sleuthkit blobs)
Synthetic E01/Ex01 built with `ewfacquire`, exact recipes in `tests/data/README.md`:
```bash
# zeros_128s.Ex01
dd if=/dev/zero bs=512 count=128 | ewfacquirestream -f encase7-v2 -d sha1 -d sha256 -t /tmp/test_ex01
# multiseg_v1.E01..E08  (segmented)
dd if=/dev/urandom bs=1M count=10 of=urandom_10m.img
ewfacquire -u -f encase6 -S 1500000 -c none -t multiseg_v1 -d md5 -d sha1 urandom_10m.img
# ewfacquire_clean.E01
dd if=/dev/zero bs=512 count=8192 of=blank_4mb.img
ewfacquire -u -f encase6 -c none -t ewfacquire_clean -d md5 -d sha1 blank_4mb.img
```
VENDORED error-path blobs from sleuthkit `test/data`: `bogus.E01`/`E02` (0-byte), `gpt_130_partitions.E01`.
`zeros_128s_compressed.Ex01` hand-built via Python `zlib.compress(level=1)` (structure documented,
command not scripted). Fuzz corpus 188 KB / 1.1 MB.

### B3 · vmdk-forensic — `core/tests/data/` (6.8 MB) · SYNTHETIC ✓ · **T2** (qemu-img authored)
`qemu-img`, per `core/tests/data/README.md`:
```bash
qemu-img create -f vmdk minimal.vmdk 1M
qemu-img create -f vmdk -o subformat=streamOptimized   stream_opt.vmdk 1M
qemu-img create -f vmdk -o subformat=twoGbMaxExtentFlat flat.vmdk 1M
```
Fuzz corpus 111 MB (coverage-guided).

### B4 · vhdx-forensic — `*/tests/data` (~121 MB) · SYNTHETIC ✓ / ~ · **T2** (qemu-img / Hyper-V authored)
`qemu-img`, per `docs/validation.md`:
```bash
qemu-img create -f vhdx                  qemu_empty_dynamic.vhdx 16M
qemu-img create -f vhdx -o subformat=fixed qemu_fixed.vhdx        8M
```
`fat-parent.vhdx` + `fat-differential.vhdx` (Hyper-V parent/differential chain) and `ext2.vhd` are
committed without a scripted command — provenance **~** (Hyper-V tooling, not recorded).
`_archived/vhdx-core` holds the pre-split legacy copies (86 MB).

### B5 · vhd — `vhd/tests/data/` (5 MB) · SYNTHETIC ✓ · **T2** (qemu-img authored)
`qemu-img`, per `vhd/tests/data/README.md`:
```bash
qemu-img create -f vpc                  minimal.vhd 1M
qemu-img create -f vpc -o subformat=fixed fixed.vhd 1M
```

### B6 · dd — `dd/dd/tests/data/` (16 MB) · SYNTHETIC ~  ·  dmg — `dmg/dmg/tests/data/` (840 KB) · REAL-self ~ · **T2** (dmg via hdiutil; mixed: also T3 — dd raw, no oracle)
dmg fixtures via macOS `hdiutil`; dd raw images for the flat provider. **Generators not scripted in
the repos** — provenance ~ (regenerate dd via `dd if=… of=…`; dmg via `hdiutil create`).

### B7 · aff4 — `aff4/tests/data/` (14 MB) · REAL-ext + VENDORED ✓ · **T1**
Evimetry/AFF4 sample images; **VENDORED** AFF4 Canonical Images from github.com/aff4/Standard.
Redistribution: AFF4 standard suite license.

### B8 · iso9660-forensic — `iso/tests/data/` (1.7 GB) · REAL-ext + SYNTHETIC ✓ · **T1** (mixed: also T2 — xorriso/hdiutil-minted ISOs)
Synthetic ISOs via `xorriso`/`hdiutil` + real downloads, per `docs/validation.md` (`SRC` = a
populated source dir):
```bash
xorriso -as mkisofs -o rock_ridge.iso -V ROCK_RIDGE -r "$SRC"
xorriso -as mkisofs -o joliet.iso     -V JOLIET     -J "$SRC"
xorriso -as mkisofs -o eltorito.iso   -V EL_TORITO -b boot.img -c boot.catalog -no-emul-boot -r -J \
        -graft-points boot.img=/tmp/boot.img "$SRC"
hdiutil makehybrid -o udf_bridge.iso -iso -joliet -udf "$SRC"            # macOS
curl -L https://github.com/log2timeline/dfvfs/raw/main/test_data/iso9660.raw -o dfvfs_plain.iso
curl -L https://github.com/exiftool/exiftool/raw/master/t/images/ISO.iso       -o truncated.iso
```
Real OS ISOs (**gitignored, user-downloaded**): `debian-13.5.0-amd64-netinst.iso` (755 MB, GPL),
Windows Server `17763.1.*.iso` (335 MB — MS license, do not redistribute). **issen mirror:**
`crates/issen-iso/tests/data/ubuntu-20.04-mini.iso` (74 MB, Canonical).

### B9 · udf-forensic — `tests/data/udf_{vat,spar,plain}.img` (8 MB each, committed) · REAL-self ✓ · **T2** (mkudffs-minted, `udfinfo` oracle)
Real UDF images authored by **`mkudffs` (udftools 2.3)** and cross-checked by the independent
**`udfinfo`** decoder (the oracle). Mostly-zero, so committed (a `.gitignore` negation un-ignores them);
excluded from the published crate via `Cargo.toml` `exclude = ["tests/data/*.img"]`. Minted on macOS via
a rootless Linux container (`podman run ubuntu:24.04`). Verbatim generators:
```bash
dd if=/dev/zero of=udf_vat.img   bs=1M count=8 && mkudffs --media-type=cdr   --udfrev=0x0150 udf_vat.img
dd if=/dev/zero of=udf_spar.img  bs=1M count=8 && mkudffs --media-type=dvdrw --udfrev=0x0201 udf_spar.img
dd if=/dev/zero of=udf_plain.img bs=1M count=8 && mkudffs --media-type=hd    --udfrev=0x0201 udf_plain.img
```
`udfinfo` ground truth: vat → udfrev=1.50, writeonce, PSPACE start=257; spar → udfrev=2.01, overwritable,
SSPACE+PSPACE start=1296; plain → udfrev=2.01, blocksize=512, PSPACE start=257 (the 512-byte-block case —
the crate detects block size from the AVDP location rather than assuming 2048). Asserted by `src/lib.rs
mod real_media_tests` (kind + `partition_start` + `block_size` vs udfinfo PSPACE, across 2048 + 512 media).
Full per-file provenance + captured oracle output: `udf-forensic/tests/data/README.md`. Redistribution:
mkudffs output is freely redistributable.

---

## C. Filesystem / partition / compression fixtures

### C1 · ntfs-forensic — `core/tests/data/defcon2018_cdrive_boot.bin` (4 KB) · REAL-ext ✓ · **T1**
NTFS boot sector extracted from the **DEF CON 2018** `MaxPowers` E01 via TSK
`fsstat -o 1026048`. Ground-truth values asserted in `core/tests/real_image.rs`. Redistribution:
DEF CON CTF.

### C2 · mft — `samples/MFT` (13 MB) + `samples/entry_*` + `testdata/*` · REAL ? · **T1** (real $MFT; provenance undocumented) 
A full real `$MFT` plus hand-picked single records exercising fixup/data-run/ADS edge cases
(`entry_102130_fixup_issue`, `entry_long_name_and_res_ads_002`, …), extracted via `icat`. **Source
image not documented — provenance undetermined; likely private casework.** Flag for redistribution
review before any external release.

### C3 · ext4fs-forensic — `tests/data/{minimal,forensic}.img` (10 MB) · SYNTHETIC ✓ · **T2** (mkfs.ext4-minted, Sleuth Kit oracle)
Built by committed scripts `tests/create-minimal-image.sh` and `tests/create-forensic-img.sh`
(the latter in a `--privileged debian:bookworm-slim` container):
```bash
# minimal.img
dd if=/dev/zero of=minimal.img bs=1M count=4
mkfs.ext4 -F -b 4096 -O extents,metadata_csum,64bit,extra_isize -L test-ext4 minimal.img
mount -o loop minimal.img /mnt; echo -n 'Hello, ext4!' > /mnt/hello.txt; mkdir /mnt/subdir; umount /mnt
# forensic.img
dd if=/dev/zero of=forensic.img bs=1M count=32
mkfs.ext4 -F -L forensic-test -O has_journal,metadata_csum,64bit,extents -b 4096 forensic.img
# mount → write files + symlinks + setfattr xattrs → create deleted-file.txt/deleted-large.txt,
# save their inode #s to deleted-ino.txt (stat -c %i), then rm them and umount  (deleted-inode recovery)
```
`forensic.img` also backs the `forensic::findings` `EXT4-*` `Observation` adapter, whose engine
outputs are cross-checked (Tier 2) against **The Sleuth Kit** on the same image: `fls -rd` →
deleted inodes 21/22 (`EXT4-DELETED-INODE`), `fsstat` → 1 block group / no SB backups
(`EXT4-SUPERBLOCK-BACKUP-MISMATCH` empty), `jls` → journal commit order. See
`ext4fs-forensic/docs/validation.md` § "Finding adapter".

### C4 · hfsplus-forensic — `tests/data/hfs_plus_*.bin` (1.6 MB) · REAL-self ✓ · **T2** (hdiutil-minted, Sleuth Kit oracle)
HFS+ volumes created via macOS `hdiutil create -layout SPUD`; real Apple filesystem structures
with known files (`HELLO.TXT` = "hello hfs"). Asserted in `tests/catalog.rs`. These same images
(plus C4b's `hfs_decmpfs_volume.bin`) also back the **HFS+ anomaly analyzer** (`findings::audit`,
`tests/findings.rs`): clean-volume true-negatives are cross-checked against **The Sleuth Kit**
`fsstat`/`istat`/`fls` (2 files/3 folders, block size 4096, comp.bin compressed w/ resource fork
present — all agree, 0 anomalies); positives are crafted in-test by flipping real volume bytes
(no new committed fixtures).

### C4b · hfsplus-forensic decmpfs — `tests/data/decmpfs/` (~4.3 MB) · REAL-self ✓ · **T2** (Apple-compressor output, kernel/original-file oracle; mixed: also T3 — one synthetic `zlib_type3_stored`)
HFS+/APFS transparent-compression (`decmpfs`) fixtures — **every codec validated against REAL
macOS-produced bytes** (oracle = the original file). **LZVN (7/8):** `lzvn.rsrc`+`lzvn.expected`
(`ditto --hfsCompression`, type-8, 2×64 KiB, 80000 B) and `hfs_decmpfs_volume.bin` (4 MiB layout-NONE
HFS+ volume: `comp.bin` = type-8 LZVN 262144 B + `plain.bin` uncompressed control; payload = LCG block
×32 regenerated in-test). **zlib (3/4) + LZFSE (11/12):** `real_{zlib,lzfse}_rsrc.rsrc` and
`real_{zlib,lzfse}_inline.payload`, minted via `afsctool -c -T ZLIB|LZFSE` (Apple's real compressor —
macOS ships only LZVN). Only synthetic fixture: `zlib_type3_stored.payload` (the `0xFF` "stored" marker,
which the real compressor never emits). macOS hides `com.apple.decmpfs`; type read via
`getxattr(..., XATTR_SHOWCOMPRESSION)`. Real data caught 2 bugs synthetic fixtures masked (zlib offset
base = headerSize+4; LZFSE zero-padded chunk table). Generators in `hfsplus-forensic/tests/data/README.md`.
Asserted in `core` lib tests + `tests/decmpfs_integration.rs`.
**Tahoe (macOS 26.5, build 25F71) regression:** `tahoe_type8.rsrc`+`.expected` (a real type-8 LZVN
resource fork that carries 80–300 trailing bytes *after* the end-of-stream opcode) and
`tahoe_type9.decmpfs`+`.expected` (a real type-9 uncompressed-inline xattr with its 1-byte `0xCC`
storage marker). Captured by mounting a `macos-tahoe-vanilla` VM disk read-only on the host and reading
`com.apple.decmpfs`/`com.apple.ResourceFork` via `getxattr(..., XATTR_SHOWCOMPRESSION=0x20)`; oracle =
Apple `COMPRESSION_LZVN` (`0x900`) + the kernel's transparent read. Exposed 2 bugs synthetic `ditto`
fixtures masked — type-8 strict-trailing reject (fixed via the `lzvn` crate) and type-9 unstripped
marker — taking real-sample decoding from **0/35 → 35/35**.

### C5 · apm-partition-forensic — `tests/data/apm_map{,_32k}.bin` · REAL-self ✓ · **T2** (hdiutil-minted, `mmls`+`pdisk` oracles — doc calls it "Tier-1 differential")
Apple Partition Map + DDM from `hdiutil` HFS+ images (2 partitions: `Apple_partition_map` +
`Apple_HFS`, block size 512). `apm_map.bin` (2 KB, md5 `5d87d4730a865a763f49180a7949b8e2`)
drives `forensic/tests/map.rs` + `analyse_tests.rs`. **`apm_map_32k.bin`** (32 KB, md5
`cf93a0aa136bd22b36b5f397dca942a2`) is the **Tier-1 oracle differential** in
`forensic/tests/real_apm_oracle.rs` — re-decoded by `mmls -t mac` (TSK) AND `pdisk -dump`
(Apple), reconciling entry count/type/start/count. 32 KB = smallest head both oracles fully
decode. Generator:
```bash
hdiutil create -size 8m -layout SPUD -fs HFS+ -volname OracleTest /tmp/apm_oracle
dd if=/tmp/apm_oracle.dmg of=tests/data/apm_map_32k.bin bs=1024 count=32
```

### C6 · usnjrnl-forensic — feature-gated `tests/data/` · REAL-ext ✓ (external) · **T1** (consumes Szechuan desktop E01)
Uses the **Szechuan Sauce desktop E01** (A3) for `image_integration.rs` / `precision_recall.rs`
(`#[ignore]`, manual placement). Own committed `tests/data` is 0 B (report tests are synthetic).

### C7 · dar-forensic — `forensic/tests/data/v7..v11_hello.dar` (5 files) · SYNTHETIC ✓ · **T2** (upstream `dar` releases authored each format)
Each archive built with the matching upstream `dar` release (2.3.12→2.8.5 = format 7→11; v7 in a
`gcc:4.9` container), per `forensic/tests/data/README.md`:
```bash
mkdir -p /tmp/corpus/files && printf 'hello format 7\n' > /tmp/corpus/files/hello.txt
<dar-2.3.12>/dar -Q -c /tmp/archive -R /tmp/corpus -g files/hello.txt && cp /tmp/archive.1.dar v7_hello.dar
# then dar 2.4.24 → v8, 2.5.3 → v9, 2.6.16 → v10, 2.8.5 → v11 (same shape, version-specific text)
```

### C8 · lzo — `tests/data/*.{raw,lzo}` (8 pairs) · SYNTHETIC + REAL ✓ · **T2** (reference `liblzo2` oracle)
`.lzo` produced by the reference `liblzo2` via `validation/lzo_compress.c`, per `docs/validation.md`:
```bash
cc -O2 -I"$(brew --prefix lzo)/include" validation/lzo_compress.c -L"$(brew --prefix)/lib" -llzo2 -o /tmp/lzo_compress
/tmp/lzo_compress 1   empty.raw  empty.lzo     # lzo1x_1 opcode probes: empty/hello/run_a/pattern/incompressible
/tmp/lzo_compress 999 readme.raw readme.lzo    # lzo1x_999 on REAL content: README.md, src/lib.rs
```
`.raw` inputs = hand-crafted probes + the project's own `README.md`/`src/lib.rs`.

### C8b · lzvn (`SecurityRonin/lzvn`, crate `lzvn-core`) — `tests/data/*.{lzvn,expected}` (4 pairs) · SYNTHETIC (Apple-encoded) ✓ · **T2** (Apple encoder over synthetic inputs; mixed: also T1 — 25 real macOS 26.5 blocks)
`.lzvn` = real Apple LZVN streams from Apple's own `compression_encode_buffer(COMPRESSION_LZVN, 0x900)`
over synthetic inputs (`text_small`, `text_repeats` = heavy match/overlap, `mixed`, `near_random`), each
padded with trailing bytes after end-of-stream to exercise length-tolerance (the `decmpfs` block shape).
Inputs are synthetic so the fixtures are freely redistributable. The decoder was additionally validated
against the 25 real macOS 26.5 type-8 blocks above (C4b `tahoe_type8.*`) vs the same Apple oracle. Generator
in `lzvn/docs/validation.md`; fuzz target `decode` (clean over 1.37M runs).

### C9 · gpt-partition-forensic — `tests/data/gpt_real_3part.img` (8 MiB) · REAL-self ✓ · **T2** (sgdisk-minted, TSK `mmls` oracle — doc calls it "Tier-1 differential")
Real GPT disk image, **minted by `sgdisk` (GPT fdisk 1.0.10)** and independently re-decoded by
**TSK `mmls` 4.12.1** (separate codebases — the cross-tool oracle). MD5 `cbda08767efb84203c5f02b827fc2a94`.
3 partitions (BASICDATA/Microsoft-basic-data, LINUXFS/Linux-filesystem, EFISYSTEM/EFI-system) with
distinct type + unique GUIDs; whole 8 MiB committed so primary **and** backup GPT are present.
Generator (verbatim) + captured oracle output in `gpt-partition-forensic/tests/data/README.md`;
consumed by `forensic/tests/real_gpt_oracle.rs` (Tier-1 structural-parse differential).

### C9b · mbr-partition-forensic, ntfs/usnjrnl records · SYNTHETIC ✓ · **T3** (hand-built anomaly-detector fixtures, no oracle)
No committed images — fixtures are constructed **byte-by-byte by Rust builders in the tests** (no
shell): gpt anomaly-**detector** fixtures `header_sector()`/`entry_bytes()`/`build()`
(`forensic/tests/reconcile_tests.rs`; need deliberately corrupted bytes no tool mints), mbr
`windows7_boot()`/`disk_with_boot_and_serial()` (`forensic/tests/disk_signature_tests.rs`), and the
ntfs/usnjrnl USN+MFT record constructors in unit tests. Fuzz corpora harness-seeded.

### C10 · 4n6mount — `fuzz/corpus/session_deserialize/` (23 MB) · FUZZ · **T3** (machine-evolved robustness corpus, no oracle)
Coverage-guided session-deserialization corpus; no curated seeds.

### C11 · apfs-forensic — `tests/data/apfs_{nxsb_head,container_chain,fstree,content}.bin` · REAL-self ✓ · **T2** (hdiutil-minted; libfsapfs/TSK/macOS oracles)
Real APFS container partitions minted by Apple's own `hdiutil` (`hdiutil create -size {64,128}m
-fs APFS -volname APFSORACLE -layout GPTSPUD`), carved with `dd … bs=4096` from the attached
`/dev/diskNs1` (Apple_APFS slice), so every on-disk structure incl. the stored Fletcher-64
checksums is Apple-authored.
- **`apfs_nxsb_head.bin`** (68 KiB, 17 blocks; MD5 `81505414be7754a3927091574aaea5a4`): block 0 +
  the checkpoint descriptor ring → live NXSB. **P1** (object/container/checkpoint). Oracle:
  Apple `diskutil` (block size 4096, container UUID `40115033-…`).
- **`apfs_container_chain.bin`** (1.38 MiB, 345 blocks; MD5 `b25546419bbcd153317232888701a98a`):
  strict superset reaching the container omap (block 343) → omap B-tree (block 344) → volume
  superblock APSB (block 342). **P2** (omap/btree/volume-superblock resolution). **Independent
  oracle = libfsapfs `fsapfsinfo`** (built into `apfs-forensic/tools/`, oracle-only) run on the
  committed fixture → `Number of volumes: 1`, id `fa8b74aa-…`, name `APFSORACLE`; cross-checked
  by Apple `diskutil apfs list`. The reader resolves exactly one APSB (paddr 342) carrying magic
  `0x42535041` + a valid Fletcher-64.
- **`apfs_fstree.bin`** (1.46 MiB, 374 blocks; MD5 `976d6ab26b34c46f38bc44960e934be9`): a richer
  self-minted image (`hdiutil create -size 128m -fs APFS -volname APFSP3 -layout GPTSPUD`) carrying
  a **known directory tree** — `/top.txt`(inode 22, 15 B), `/Dir1`(18), `/Dir1/Beth.txt`(20, 38 B),
  `/Dir1/Sub`(19), `/Dir1/Sub/secret.bin`(21, 26 B) — carved (blocks 0–373) to reach the full chain
  NXSB→checkpoint→container omap→APSB(371)→volume omap(366/367)→**virtual fs-tree leaf(365)**. **P3**
  (volume APSB parse, j_key dispatch, inode metadata, **name→inode path navigation**). **Independent
  oracle = TSK `fls -r`/`istat`** (pool `-o 40 -B 371`) + macOS `stat`: the reader's resolved inode
  numbers, sizes, mode, uid/gid, and ns-timestamps reconcile per file (e.g. Beth.txt create
  `1782060082608648902`, access `…733745215`, both matching `istat`); volume count cross-checked by
  Apple `diskutil`/TSK `pstat` (one volume `APFSP3`, APSB block 371, oid 1026, xid 6).
- **`apfs_content.bin`** (1.73 MiB, 442 blocks; MD5 `edb98667c10e8457d9ed6a4eb97d111f`): a
  self-minted image (`hdiutil create -size 128m -fs APFS -volname APFSP4 -layout GPTSPUD`) carrying
  **known content for every file-read path** — a plain file, a **sparse** file (64 KiB hole + tail),
  a **transparently-compressed** file (`ditto --hfsCompression` → decmpfs **type 8 LZVN resource
  fork**, 180000 B), a file with **custom xattrs**, and a **symlink** — carved (blocks 0–441) to
  reach the live APSB(438)→volume omap(433/434)→fs-tree leaf(432) plus every file's data extents +
  resource fork (345–426). **P4** (file byte read, sparse holes, decmpfs decompression, xattrs,
  symlink). **Independent oracle = macOS `cp`/`shasum -a 256` byte-identical**: `read_data`'s
  assembled bytes hash-match macOS for plain (`289af0a0…`), sparse (`fe0fc4fa…`), nested (`ee7c2682…`)
  and the **decompressed** type-8 file (`3f58a418…`); xattrs match `xattr -l`
  (`com.example.tag`/`user.note`), symlink target matches `readlink` (`Dir1/Beth.txt`). decmpfs codec
  stack REUSED from `forensicnomicon::decmpfs` + `flate2`/`lzvn-core`/`lzfse_rust` (validated 25/25 on
  real macOS in hfsplus-forensic).
Generators (verbatim) + captured oracle output in `apfs-forensic/tests/data/README.md`; consumed by
`apfs-forensic/core/tests/{object,container,checkpoint,container_open,omap,btree,btree_descend,volume_resolve,volume,fsrecord,inode,dir,extent,compression,xattr}.rs`.

### C12 · btrfs-forensic — `tests/data/btrfs_superblock.bin` (4 KiB, committed) + gitignored 512 MiB image · REAL-self ✓ · **T2** (mkfs.btrfs-minted, `btrfs inspect-internal dump-super` oracle)
btrfs P0 superblock fixture minted on Parallels "Ubuntu 24.04 (with Rosetta)" (`btrfs-progs v6.6.3`):
`dd if=/dev/zero of=btrfs.img bs=1M count=512`; `mkfs.btrfs -f -L BTRFS_ORACLE --csum crc32c btrfs.img`;
loop-mounted and populated with 3 known files (`small.txt`, `mid.bin` 64 KiB, `dir/sub/leaf.txt`),
`sync`, unmounted. The committed **`btrfs_superblock.bin`** (MD5 `812c99bb8ddd898a011abcd3ac5c3bbe`)
is the 4096-byte block at physical offset 0x10000 (`dd skip=65536 count=4096`); the full 512 MiB
`btrfs.img` (MD5 `58cc07f6e3e7f950152e03ee71330477`) is **gitignored** (`/tests/data/*.img`) and
consumed env-gated via `BTRFS_ORACLE_IMG`.
- **Independent oracle = `btrfs inspect-internal dump-super -f`** (btrfs-progs, a different impl from
  our reader), captured verbatim in `tests/data/btrfs.dump-super.txt`. **P0** asserts every field:
  magic `_BHRfS_M`@0x40, csum_type 0(crc32c) + csum `0xd9136f60` `[match]`, fsid
  `fe9599cb-e209-4d5c-b734-642c457fbc01`, generation 9, root(logical) 30720000, chunk_root 22036480,
  sectorsize 4096, nodesize 16384, total_bytes 536870912, bytes_used 212992, num_devices 1,
  incompat_flags 0x361, and the `sys_chunk_array` bootstrap (one SYSTEM|DUP entry, key
  (256,228,22020096), 2 stripes @22020096/30408704, single-device DUP logical→physical map). Scalar
  offsets were **verified byte-for-byte against dump-super** (the +0x18-shifted draft offsets in the
  task brief, missing `log_root_transid`, were corrected). `btrfs.chunk-tree.txt`
  (`dump-tree -b 22036480`) is committed as the **P1** chunk-tree walk oracle (deferred phase).
Generators (verbatim) + dump-super ground truth in `btrfs-forensic/tests/data/README.md`; consumed by
`btrfs-forensic/core/tests/superblock.rs`. (Repo `~/src/btrfs-forensic` is LOCAL-ONLY at P0.)

---

## D. Log / memory / application-artifact corpora

### D1 · winevt-forensic — `tests/data/` (1.4 GB) · REAL-ext + VENDORED ✓ · **T1**
- **CyberDefenders "CorporateSecrets" Lab** — `…/evtx/*.evtx` (~101 real Windows EVTX channels).
  cyberdefenders.org (educational license).
- **Fox-IT DanderSpritz** — `fox-it-danderspritz/pre-Security.evtx` (+ pair). Publicly published;
  the **differential-parity oracle** in `tests/real_corpus_parity.rs` (decoder vs omerbenamram).
- **DEF CON DFIR CTF 2018** EVTX subset.
- **VENDORED attack samples:** `EVTX-ATTACK-SAMPLES` (markbaggett, ~278), Hayabusa
  (Yamato-Security, ~292), MITRE samples, DFIRArtifactMuseum. Attribution required on derivatives.

### D2 · srum-forensic — `tests/data/` (16 MB) · REAL ~ · **T1** (real SRUDB.dat; provenance undocumented)
`SRUDB.dat` ESE database sample(s) for the SRUM parser. Source not explicitly documented — confirm
before redistribution.

### D3 · memory-forensic — `tests/data/` (24 KB) · SYNTHETIC ✓ · **T3** (small self-authored structures, no oracle)
Small synthetic structures only. **The large memory CTFs (Cridex, TOTAL_RECALL, CyberSpace,
DeepDive) physically live in `issen/tests/data` (A6), not here** — referenced cross-repo.

### D4 · brave-browser-sessions (snss-core) — `crates/snss-core/tests/fixtures` (4.3 MB) · REAL-self ✓ · **T1** (genuine SNSS browsing state)
Real Chromium/Brave SNSS session-restore snapshots (3). Contain real browsing state — sanitize
before external sharing.

### D5 · chat4n6 — plugin `tests/fixtures` · SYNTHETIC ~ / UNDETERMINED ? · **T3** (synthetic schema DDL, no oracle)
WhatsApp/Telegram/Signal/iOS SQLite **schema DDL** fixtures (synthetic schemas). Some android/social
fixture dirs present but contents not enumerable — undetermined.

### D6 · ufed — `ufed/tests/data` (1 MB) · SYNTHETIC ✓ · **T3** (deterministic PRNG corpus, no oracle)
Deterministic xorshift-PRNG corpus (regenerable from seed `0xDEADBEEF`).

### D7 · RapidCollect — `crates/*/tests/fixtures` · SYNTHETIC ~ / UNDETERMINED ? · **T3** (synthetic manifest fixture, no oracle)
Integration-manifest roundtrip fixture (synthetic); android/twitter/instagram fixture dirs
undetermined.

### D8 · sqlite-forensic text-encoding fixtures — `sqlite-forensic/tests/data/` · REAL-self ✓ · **T2** (genuine `sqlite3`-engine output)
Genuine `sqlite3`-engine output validating per-encoding TEXT decode (header byte 56).
Generators (the `PRAGMA encoding` must precede any table):
```
sqlite3 utf8.sqlite    "PRAGMA page_size=512; PRAGMA encoding='UTF-8';    CREATE TABLE t(s TEXT); INSERT INTO t VALUES('héllo wörld');"
sqlite3 utf16le.sqlite "PRAGMA page_size=512; PRAGMA encoding='UTF-16le'; CREATE TABLE t(s TEXT); INSERT INTO t VALUES('héllo wörld');"
sqlite3 utf16be.sqlite "PRAGMA page_size=512; PRAGMA encoding='UTF-16be'; CREATE TABLE t(s TEXT); INSERT INTO t VALUES('héllo wörld');"
```
MD5: `utf8` 1d0923bb2ad0fee1c6f8cd8140a9ac61 · `utf16le` f2c418e5a1e14ce7f56e28b0e2266f9f ·
`utf16be` 8f260ddb30f34b7de3c9e13a23f7981a. Consumed by `core/tests/utf16_text_tests.rs`
(skip-if-absent). Header byte 56 = 1/2/3 respectively.

### D9 · peripheral-forensic — `tests/data/` (committed) · SYNTHETIC (spec-exact) ✓ · **T3** (hand-authored spec-exact logs, no oracle)
External-device (peripheral) connection forensics. Hand-authored `setupapi.dev.log` / `setupapi.log`
fixtures matching the Microsoft SetupAPI text-log grammar — NO generator command (spec-exact bytes;
the build host is macOS and has no real log). Consumed by `forensic/tests/real_data.rs`.
- **Spec citations:** *SetupAPI Text Logs* + *Format of a Text Log Section Header*
  (learn.microsoft.com/.../setupapi-text-logs); USB id grammar `USB\VID_v(4)&PID_d(4)&REV_r(4)`
  (.../standard-usb-identifiers); OS-generated-serial rule (instance-id 2nd char `&`)
  (.../instance-ids).
- **Real-capture path:** mount a USB/FireWire/Thunderbolt device on a Windows VM, copy
  `C:\Windows\INF\setupapi.dev.log` (Vista+) / `C:\Windows\setupapi.log` (XP). Never commit a real
  person's log — it embeds every device serial they ever attached.
- MD5: `setupapi.dev.log` 8e86d3a0c7e5d1209a4d7c81d3b0a023 ·
  `setupapi_xp.log` d1bdd7199b5f134421143ce5dc445474.

### D10 · useract-forensic — `tests/data/real_bash_history` (committed) · REAL-self ✓ · **T2** (genuine bash history-writer output; ground truth from documented construction)
User-activity correlation layer (merges `shellhist-core` + `peripheral-core` into one `UserActivity`
timeline). The one fixture is a genuine `.bash_history` authored by the `bash` shell's own history
writer (`history -s` + `history -w`, `HISTTIMEFORMAT` set so bash emits `#<epoch>` lines), with a
planted `curl … | sh` and `unset HISTFILE`; the device side of the test is a real
`peripheral_core::DeviceConnection` built in-code (no fixture). Full per-file detail + verbatim
generator command in
[`useract-forensic/tests/data/README.md`](https://github.com/SecurityRonin/useract-forensic/blob/main/tests/data/README.md).
- MD5: `real_bash_history` 2a4ead0e64d175c7414bb37f23dbed73 (epoch values differ per run; structure
  fixed).

### D11 · lnk-forensic — `tests/data/` (committed) · MIXED: `.lnk` SYNTHETIC (spec-exact) ✓ + Jump Lists REAL-ext ✓ · **T1** (real captured Jump Lists; mixed: also T3 — spec-exact `.lnk`)
Windows Shell Link (`.lnk`) + Jump List forensics. The three `.lnk` fixtures are hand-authored
(the build host is macOS and cannot author a real `.lnk`); full per-file detail + the generators in
[`lnk-forensic/tests/data/README.md`](https://github.com/SecurityRonin/lnk-forensic/blob/main/tests/data/README.md).
The two Jump List fixtures are now **real captured Windows OLE/CFB artifacts** extracted from the
DFIR Madness "Stolen Szechuan Sauce" DC01 image (provenance below; per-file detail in
[`issen/crates/parsers/issen-parser-lnk/tests/data/README.md`](../crates/parsers/issen-parser-lnk/tests/data/README.md)).
- **`.lnk` fixtures** (`gen_lnk.rs`, dependency-free `rustc`): `removable_media.lnk`
  (DRIVE_REMOVABLE, serial 0xDEADBEEF, label KINGSTON USB, TrackerDataBlock ANALYST-PC) +
  `network_share.lnk` (CommonNetworkRelativeLink `\\SERVER\share`, device `Z:`). Both are also
  vendored into `issen/crates/parsers/issen-parser-lnk/tests/data/` for the wrapper depth tests
  (USB-origin + UNC-share-origin regressions). A third issen-only fixture
  `command_args.lnk` (md5 `93628f2fb784ca33ea2cd63e8ed87eff`, SYNTHETIC spec-exact, generated by
  a dependency-free `rustc` program modeled on `gen_lnk.rs`) carries `StringData` arguments
  `-nop -w hidden -enc <b64>` + working dir `C:\Windows\System32` + comment, for the
  command-line-arguments depth regression.
- **Jump List fixtures — REAL-ext** (captured from DFIR Madness "Stolen Szechuan Sauce",
  `20200918_0347_CDrive.E01` / DC01, NTFS partition byte-offset `718848`, extracted with TSK
  `icat -o 718848 "$E01" <inode>`):
  - `9b9cdc69c1c24e2b.automaticDestinations-ms` (inode **86968**, AppID = Notepad) — a genuine
    OLE/CFB compound file (confirmed via the published `cfb-forensic` crate: `live_entry_names`
    returns live streams `Root Entry`, `DestList`, `1`–`5`). Five DestList entries for files under
    `C:\FileShare\Secret\` (`Beth_Secret.txt`, `Szechuan Sauce.txt`, `SECRET_beth.txt`,
    `PortalGunPlans.txt`, `NoJerry.txt`), recorded on host `citadel-dc01`. Each embedded LNK's
    `TrackerDataBlock` records origin machine `citadel-dc01` and birth-droid object UUID-v1s with
    node (MAC) `00:0C:29:E1:84:E6` (VMware OUI `00:0C:29`) — the wrapper now surfaces these as
    `birth_droid_machine` / `birth_droid_mac` / `droid_mac` (cross-machine origin).
  - `28c8b86deab549a1.customDestinations-ms` (inode **87092**, AppID = Internet Explorer 32-bit) —
    the flat, non-CFB custom form (`cfb-forensic::live_entry_names` returns `None`), entries
    targeting `C:\Program Files\Internet Explorer\iexplore.exe`.
  - **License/redistribution:** DFIR Madness corpus, educational / research use.
- **Spec citations:** `[MS-SHLLINK]` (Shell Link); libyal `dtformats` *Jump lists format* (DestList /
  CustomDestinations); kacos2000 `Jumplist-Browser` `AppIdlist.csv` (AppID map).
- MD5: `removable_media.lnk` ba3dbe2429bdfa93d8a0a9be80ca0fbe · `network_share.lnk`
  547e0d2686e6652d8d144fb1b767bf9a · `command_args.lnk` 93628f2fb784ca33ea2cd63e8ed87eff ·
  `9b9cdc69c1c24e2b.automaticDestinations-ms` 18b8fe1fee7120db495c5a6aba947533 ·
  `28c8b86deab549a1.customDestinations-ms` a4af29faae0cdfd56fe2295611d54488.

### D12 · journald-forensic — `tests/data/` + mint procedure + fuzz · MIXED: REAL-self journal (T1) + SYNTHETIC malformed buffers (T3) · **T1** (journalctl differential oracle; mixed: also T3 — in-code robustness buffers)
systemd journal (`.journal`) forensic reader. Three provenance classes:
- **`classic-system.journal`** (524288 B, committed) · **REAL-self** ✓ · **T1**. Real
  `systemd-journald` output (systemd 239, RHEL 8) produced as PID 1 in a
  `registry.access.redhat.com/ubi8/ubi-init` container under Podman: 21 messages logged via
  `logger -t jdtest`, then `journalctl --sync && --flush`, and
  `/var/log/journal/<machine-id>/system.journal` copied out. **systemd 239 chosen** because v252+
  writes the COMPACT + KEYED_HASH layout the reader does not yet decode; 239 predates both (classic
  layout, `Incompatible Flags: <none>`). **Oracle = `journalctl`** (systemd decoding its own format):
  `crates/journald-binary/tests/journalctl_oracle.rs` reconciles `parse_entries` against
  `journalctl --file <f> -o json` — entry count + a MESSAGE/SYSLOG_IDENTIFIER/_PID/PRIORITY/_COMM
  field sample. Confirmed in a Linux container with real journalctl: **30 entries reconciled**
  (`journalctl --header`: 30 Entry Objects; machine-id `e7d87b83baf96ba14eb77adc0a769ed2`). The
  end-to-end oracle test is **env-gated** (`JOURNALD_TEST_CORPUS` + `journalctl` on PATH), skips
  cleanly otherwise; the pure reconciliation helpers are unit-tested unconditionally.
  Redistribution: only fixture log lines + journald housekeeping — freely redistributable.
- **Mint procedure — `scripts/mint-journal.sh`** · **REAL-self** (operator-run on Linux/systemd;
  ground truth documented, not committed). Verbatim generator:
  ```
  scripts/mint-journal.sh [OUTPUT_PATH]   # logs jd4n6-mint events (logger -p user.info/user.err
                                          # + systemd-cat), journalctl --sync/--flush, copies
                                          # /var/log/journal/<machine-id>/system.journal, writes
                                          # OUTPUT_PATH.truth.txt (md5/sha256, incompat-flags,
                                          # journalctl entry count, exact messages logged)
  ```
  For a classic-format (reader-parseable) file, run it inside a systemd-239 container (recipe in the
  script header — same provenance as `classic-system.journal`). Minted journals are consumed via the
  env-gated oracle test, not committed.
- **Malformed-input hardening** · **SYNTHETIC** ✓ · **T3** (no external oracle; robustness property).
  `crates/journald-binary/tests/malformed_input.rs` (byte-exact in-source buffers: truncated /
  oversized / all-0xFF / LCG-garbage / extreme-size / boundary-offset / self-referential) + the
  `fuzz_parse_entries` cargo-fuzz target (`fuzz/`). Invariant: never panic. **No systemd LGPL fuzz
  seeds committed** — the repo is Apache-2.0, so seeds are synthetic to keep the tree license-clean
  (see `journald-forensic/docs/validation.md`). Fuzz confirmed: 1.45M execs / 91s, zero crashes.
- MD5: `classic-system.journal` cb1b9af3366d6d3e4f1470e3c7d203a4.

### D13 · leveldb-forensic — `tests/data/chromium-local-storage/leveldb/` (committed, 376 B) · REAL-self ✓ · **T2** (real Chrome engine output; ground truth from documented `localStorage.setItem` writes)

A **real Chromium-authored** Local Storage `leveldb` store minted by driving
Google Chrome 150.0.7871.187 (macOS aarch64, headless) to a page that runs four
known `localStorage.setItem` writes under origin `http://127.0.0.1:8117`. The
bytes are real Chrome output; the ground truth is the four documented writes:
`case_id=CASE-001`, `greeting=Hello, forensics!`, `count=42` (all Latin-1,
prefix `0x01`), and `unicode=日本語 café ☕` (UTF-16-LE, prefix `0x00`). Chrome
also emits the origin `META:` record (WebKit-µs timestamp + size) and a
`VERSION` key — both surface via the decoder.

- Consumed by `leveldb-forensic/tests/real_chromium_local_storage.rs`
  (`decode_local_storage` over the committed dir; asserts each write + META).
  This is the tier-1/2 real-profile follow-up called out in
  `components/parser/leveldb-forensic/docs/validation.md`.
- Files: `CURRENT` (16 B) + `MANIFEST-000001` (41 B) + `000003.log` (319 B). No
  `.ldb` SSTable — the small dataset stayed in the WAL. `LOCK`/`LOG` excluded
  (Chrome-runtime-only).
- **Verbatim generator** (needs Google Chrome/Chromium + `python3`):
  ```
  components/parser/leveldb-forensic/tests/data/chromium-local-storage/mint.sh
  ```
  Serves the committed `mint.html` (single source of truth for the four writes)
  on `127.0.0.1:8117`, drives headless Chrome with a throwaway profile, gracefully
  shuts it down (flushing the LocalStorage commit timer), copies the store files
  out. Only the `META:` timestamp varies per run (real wall-clock); the test
  asserts exact equality for the four writes and a plausible range for the
  timestamp.
- Redistribution: synthetic writes to a loopback origin, no third-party/personal
  data — freely redistributable. Per-file provenance:
  `components/parser/leveldb-forensic/tests/data/README.md`.

### D14 · bluetooth-forensic — `BTHPORT` `SYSTEM`-hive walk · SYNTHETIC (not committed) · **T2** (regipy independent-oracle differential; tier-1 positive operator-supplied/pending)

Windows Bluetooth pairing forensics (`SYSTEM\…\BTHPORT\Parameters\{Devices,Keys}` →
paired device MAC / friendly `Name` / `LastSeen`/`LastConnected` / stored classic
link key). The `devices_from_hive` seam is validated over a **synthetic** REGF
`SYSTEM` hive built byte-by-byte at test time — no image is committed.
- **Generator (no external command):**
  `components/parser/bluetooth-forensic/forensic/tests/common/mod.rs::build_system_hive`
  — a minimal valid REGF v1.5 hive with two devices under `ControlSet001`
  (`AA:BB:CC:DD:EE:FF` "Sony WH-1000XM4" + REG_SZ name + both FILETIMEs + a stored
  link key; `00:1A:7D:DA:71:13` "Mouse" + REG_BINARY name + no timestamps) plus a
  non-MAC `NotAMacSubkey` that `parse_mac` rejects.
- **Independent oracle (T2):** the same bytes are re-parsed by **regipy** (third-party
  REGF parser) via
  `components/parser/bluetooth-forensic/scripts/bthport_oracle.py` and reconciled
  field-by-field in `forensic/tests/hive_seam_oracle.rs` (skip-when-absent: no
  `python3`/`regipy` → SKIP + pass). Building it caught a real fixture infidelity
  (root `nk` emitted last, not as the first hbin cell) that regipy — which finds the
  root by first-cell — surfaced.
- **Tier-1 positive — pending, operator-supplied.** No public `SYSTEM` hive with
  Bluetooth pairings exists (the 2018 Lone Wolf hive above has the BTHPORT stack + a
  host adapter but **zero** paired devices), and one cannot be minted on macOS or a
  cloud VM (no BT radio). Mint procedure:
  `components/parser/bluetooth-forensic/scripts/mint-bt-hive.md` (pair a classic BT
  device on a live Windows box → `reg save HKLM\SYSTEM` → reconcile against the regipy
  oracle and RegRipper `bthport.pl`). Real-hive tests are env-gated on
  `BLUETOOTH_TEST_SYSTEM_HIVE`. Per-file provenance:
  `components/parser/bluetooth-forensic/core/tests/data/README.md`.

---

### D15 · whatsapp-desktop-forensic — `tests/data/indexeddb/http_127.0.0.1_8731.indexeddb.leveldb/` (committed, ~6.3 KB) · REAL-self ✓ · **T2** (real Chrome/V8 engine output in WhatsApp Web's documented schema; ground truth from the documented IndexedDB writes)

A **real Chromium-authored** IndexedDB `model-storage` store minted by driving
Google Chrome 150.0.7871.187 (macOS aarch64, headless) to a page that writes the
WhatsApp Web schema (object stores `message`/`chat`/`contact`, keyPath `id`). The
bytes are real Chrome/V8 output; the ground truth is the documented writes: a text
message with an AES-CBC-encrypted body (`msgRowOpaqueData:{_keyId,iv,_data}`), an
image message with media fields (`mimetype`/`filehash`/`mediaKey`/`directPath`/
`size`/`width`/`height`), a `put`→`delete`d message leaving a recoverable
tombstone, plus one `chat` and one `contact` row. Schema authority: Mazzoli
(<https://mazzo.li/posts/whatsapp-backup.html>) + MDPI *Future Internet* 12(11):184
(<https://www.mdpi.com/1999-5903/12/11/184>).

- Consumed by `whatsapp-desktop-core/tests/{message,media,chat,contact,store}.rs`
  and `whatsapp-desktop-forensic/tests/audit.rs`. This is **not** a real message
  corpus (none was available — the host's WhatsApp is the native macOS SQLite
  client); the extraction path's ceiling is T2. See
  `components/parser/whatsapp-desktop-forensic/docs/validation.md`.
- Files: `CURRENT` (16 B) + `MANIFEST-000001` (23 B) + `000003.log` (6215 B). No
  `.ldb` SSTable — the small dataset stayed in the WAL. `LOCK`/`LOG` excluded.
- **Verbatim generator** (needs Google Chrome/Chromium + `python3`):
  ```
  components/parser/whatsapp-desktop-forensic/scripts/mint/mint.sh
  ```
  Serves the committed `scripts/mint/index.html` (single source of truth for the
  writes) on `127.0.0.1:8731`, drives headless Chrome with a throwaway profile,
  SIGTERMs it to flush the LevelDB, copies the store out. Decoded records are
  stable across runs; raw bytes (sequence numbers, file names) are not, so tests
  assert on decoded content. MD5 (this mint): `000003.log`
  `6fd64ebd0191eaec3d2acc75da0dbcf9`, `CURRENT` `46295cac801e5d4857d09837238a6394`,
  `MANIFEST-000001` `3fd11ff447c1ee23538dc4d9724427a3`.
- Redistribution: synthetic writes to a loopback origin, no third-party/personal
  data — freely redistributable. Per-file provenance:
  `components/parser/whatsapp-desktop-forensic/tests/data/README.md`.
- The crypto path (`decrypt_body`, AES-CBC) is validated separately at **T1**
  against independent openssl KAT vectors — not from this store.

---

## E. issen-internal & misc

- `issen/crates/issen-dd/tests/data/ext4.raw` (4 MB) · **REAL-ext** — downloaded from log2timeline
  dfvfs (per `crates/issen-dd/docs/corpus-validation.md`):
  `curl -L https://github.com/log2timeline/dfvfs/raw/main/test_data/ext4.raw -o ext4.raw`. (Apache-2.0.)
- `issen/crates/issen-iso/tests/data/ubuntu-20.04-mini.iso` (74 MB) · REAL-ext — Canonical
  (<https://old-releases.ubuntu.com/releases/20.04/>; mini netboot ISO).
- `issen/crates/issen-remote-access/tests/fixtures/lolrmm/*.yaml` (~30 KB) · SYNTHETIC — RMM rule fixtures.
- `disk-forensic/tests/data/` (21 MB) · SYNTHETIC — multi-format mini images (`df.qcow2`, `df.vhdx`,
  `df.iso`, `gpt_130_partitions.E01`, …) for the container/normalize tests. `ntfs.vmdk` wraps the
  **real** NTFS boot region from the DEF CON 2018 `MaxPowers` E01 (per `docs/VALIDATION.md`;
  hand-constructed, no scripted command).
- `blazehash/tests/data/nps-2010-emails.E01` (508 KB) · REAL-ext — NIST/NPS **nps-2010-emails**
  reference corpus (Garfinkel real-data corpus; public).

### E1 · Real-artifact / independent-oracle test fixtures (fleet `*-forensic` crates) · REAL-ext ✓ · **T1**

Genuine artifacts carved from published corpora, each validated in its crate's
real-data test against an **independent** tool (not the crate under test). Per-file
provenance lives in each repo's `tests/data/README.md` (cross-referenced here).

| Fixture | Bytes | MD5 | Carved from / source | Oracle reconciled |
|---|---|---|---|---|
| `lnk-forensic/tests/data/PortalGunPlans.lnk` | 840 | `e3ef792e3b68877bf29831863cfa4f38` | Szechuan Sauce CITADEL-DC01 C: E01, `Users/Administrator/AppData/Roaming/Microsoft/Windows/Recent/PortalGunPlans.lnk` (MFT inode 84630), `icat -o 718848 <E01> 84630` | LnkParse3 1.6.0 |
| `exec-pe-forensic/tests/data/hostname.exe` | 13312 | `de8c54bc39c31726df5479697f988a7b` | Szechuan Sauce CITADEL-DC01 C: E01, `Windows/System32/hostname.exe` (MFT inode 29911), `icat -o 718848 <E01> 29911` | pefile 2024.8.26 |
| `iso9660-forensic/iso/tests/data/multi_extent_8k.iso` | 122880 | `ab4592264b549fbbd393671db251e3fb` | libcdio project test corpus, <https://raw.githubusercontent.com/libcdio/libcdio/master/test/data/multi_extent_8k.iso> | cdrtools `isoinfo` |

All three reconciled **exactly** with the independent oracle — no parser
divergence found. (`hostname.exe` SHA-256 `f63e711e2d3c0696563f8c374fdaddf04a3cefdad676e442678dad2d757e0ba8`;
`multi_extent_8k.iso` SHA-256 `c929aa5932527932fcca905cddea466d3ff768bac992dbafca94af6c4fbdbc85`.)

---

## F. Fuzz corpora (machine-evolved — not curated samples)

libFuzzer corpora across the fleet, coverage-guided mutations (no hand-curated seeds unless noted):
`vmdk-forensic` 111 MB · `vhdx-forensic` build dirs · `4n6mount` 23 MB · `ntfs-forensic` 3.9 MB ·
`dar-forensic` 4.4 MB · `usnjrnl-forensic` 1.4 MB · `ewf-forensic` 1.1 MB · `ext4fs-forensic` 268 KB
· `iso9660`/`aff4`/`dd`/`dmg`/`qcow2`/`vhd`/`apm`/`gpt`/`mbr` (seeded by harness). Reproducible by
re-running `cargo fuzz`; safe to regenerate/delete.

---

## G. Provenance caveats & actions

1. **Undetermined real sources to resolve:** `mft/samples/MFT` (13 MB) and `srum-forensic` SRUDB
   lack in-repo source documentation. Resolve before any redistribution.
2. **Do-not-redistribute:** Windows Server ISO (B8, MS license); anything with real personal data
   (`Collection-A380`, Brave SNSS, `mft/samples/MFT` if casework) — sanitize/verify first.
3. **Integrity:** every corpus file MD5-verified 2026-06-09 (manifest in §H). `DESKTOP-E01.zip`
   matches DFIR Madness's published MD5 exactly. The DEFCON/Magnet "MD5" values quoted above are EWF
   *media* hashes (`ewfinfo` — the imaged drive), **not** container-file hashes, so the file-MD5s in
   §H correctly differ. Re-verify with `md5` / `Get-FileHash` for evidence-grade use.

---

## H. MD5 manifest

File hashes of every downloadable corpus artifact (`md5`, 2026-06-09). `tests/data/` is gitignored,
so these are recorded here. Verify a download with `md5 <file>` (macOS) / `md5sum <file>` (Linux) /
`Get-FileHash -Algorithm MD5 <file>` (PowerShell). `Szechuan/` = the
`dfirmadness-szechuan-sauce/` folder.

| File | Size (bytes) | MD5 |
|---|---|---|
| `loghub-openssh/OpenSSH_2k.log` | 225216 | `72efdaaf373b8d6c8a809cc86b2a951f` |
| `DEF CON DFIR CTF 2018/MaxPowersCDrive.E01` | 31577797290 | `bed3b3ddece20d136a56aa653f0de608` |
| `Magnet Virtual Summit 2023 … Windows 11/PC-MUS-001.E01` | 52629766482 | `8cf0c007391f4a72ddc12a570a115b46` |
| `Szechuan/DESKTOP-E01.zip` | 6843484923 | `71c5c3509331f472abcdf81eb6efff07` |
| `Szechuan/DC01-E01.zip` | 4836649413 | `e57fc636e833c5f1ab58dface873bbde` |
| `Szechuan/DESKTOP-SDN1RPT-memory.zip` | 802767348 | `cf31e2635c77811aaa1bb04a92a721e2` |
| `Szechuan/DC01-memory.zip` | 561424278 | `64a4e2cb47138084a5c2878066b2d7b1` |
| `Szechuan/Desktop-SDN1RPT-pagefile.zip` | 222055350 | `45c096f2688a0b5de0346fb72391b245` |
| `Szechuan/DC01-pagefile.zip` | 13540216 | `964eeaf0009d08cc101de4a83a4e5d23` |
| `Szechuan/case001-pcap.zip` | 151610116 | `422046b753cf8a4df49d2c4ce892db16` |
| `Szechuan/DESKTOP-SDN1RPT-Protected Files.zip` | 17127742 | `3e1a358d50003a9351ac2160ae6f0495` |
| `Szechuan/DC01-ProtectedFiles.zip` | 12297759 | `ad29830a583efe49c8c1c35faffd264f` |
| `Szechuan/DESKTOP-SDN1RPT-autorunsc.zip` | 278645 | `3627dcafa54e1365489a4ec0cc3d6a1c` |
| `Szechuan/DC01-autorunsc.zip` | 177298 | `964f2d710687d170c77c94947da29e66` |
| `Hal Linux DFIR Challenge/uac-vbox-linux-20260324193807.tar.gz` | 149915196 | `a76f795aa8e35218f93bb44801023009` |
| `Hal Linux DFIR Challenge/uac-vbox-linux-20260324234043.tar.gz` | 6205082254 | `ddc894d978fffd4f722539dd52dfd00f` |
| `Collection-A380_localdomain-2025-08-10T03_41_20Z.zip` | 2352737548 | `8294ee2768f934e84d5a8b8b150a6138` |
| `CyberDefenders/78-DeepDive.zip` | 562807907 | `2c6d06eef52cae743e16633fe4ee1734` |
| `CyberSpace CTF 2024/csctf-2024_forensics_memory.zip` | 703693665 | `c4821afa54754127a3a2161bafccea90` |
| `SecurityNik/TOTAL_RECALL_memory_forensics_CHALLENGE.zip` | 1317299287 | `7dceb1fcae2ed8beacc8f81f85bf935c` |
| `Volatility/cridex_memdump.zip` | 40352364 | `ebcbb798f7fa5df87375dbc4ee329209` |
| `gpt-partition-forensic/tests/data/gpt_real_3part.img` (committed, §C9) | 8388608 | `cbda08767efb84203c5f02b827fc2a94` |
| `udf-forensic/tests/data/udf_vat.img` (committed, §B9) | 8388608 | `1258d2b17f095af79bdb1141059eac84` |
| `udf-forensic/tests/data/udf_spar.img` (committed, §B9) | 8388608 | `70285bf8979a026380517bfc48ae6ee6` |
| `udf-forensic/tests/data/udf_plain.img` (committed, §B9) | 8388608 | `31d06a9942f8bc4983617631a9ac4e30` |
| `leveldb-forensic/tests/data/chromium-local-storage/leveldb/000003.log` (committed, §D13) | 319 | `7259318b8db2a78a96f2b32e257d9e97` |
| `leveldb-forensic/tests/data/chromium-local-storage/leveldb/CURRENT` (committed, §D13) | 16 | `46295cac801e5d4857d09837238a6394` |
| `leveldb-forensic/tests/data/chromium-local-storage/leveldb/MANIFEST-000001` (committed, §D13) | 41 | `5af87dfd673ba2115e2fcf5cfdb727ab` |
| `chromium-storage-forensic/tests/data/local-storage/leveldb/000003.log` (committed, §D14) | 243 | `c615e82a28579922d3d0caa1fdc176d1` |
| `chromium-storage-forensic/tests/data/local-storage/leveldb/CURRENT` (committed, §D14) | 16 | `46295cac801e5d4857d09837238a6394` |
| `chromium-storage-forensic/tests/data/local-storage/leveldb/MANIFEST-000001` (committed, §D14) | 41 | `5af87dfd673ba2115e2fcf5cfdb727ab` |
| `chromium-storage-forensic/tests/data/indexeddb/http_127.0.0.1_8731.indexeddb.leveldb/000003.log` (committed, §D14) | 1360 | `dd48c7a058efaa2e81490f4629dd6b01` |
| `chromium-storage-forensic/tests/data/indexeddb/http_127.0.0.1_8731.indexeddb.leveldb/CURRENT` (committed, §D14) | 16 | `46295cac801e5d4857d09837238a6394` |
| `chromium-storage-forensic/tests/data/indexeddb/http_127.0.0.1_8731.indexeddb.leveldb/MANIFEST-000001` (committed, §D14) | 23 | `3fd11ff447c1ee23538dc4d9724427a3` |
| `chromium-storage-forensic/tests/data/simple-cache/ea2e47cbdc22305e_0` (committed, §D14) | 449 | `58a8001d87b2d970be5e5d4293896f4e` |
| `chromium-storage-forensic/tests/data/simple-cache/d9c2c72a2ec24e84_0` (committed, §D14) | 4853 | `34c8262922bc9d8ddd1f5a7d9ef3ff0c` |

### §D14 — chromium-storage-forensic (Simple Cache + IndexedDB + Local Storage), **T2**, REAL-self

Real Chromium storage minted on-host by driving headless Google Chrome against a local
cacheable page, then copying the profile's `Local Storage/leveldb`,
`IndexedDB/*.indexeddb.leveldb`, and `Cache/Cache_Data` dirs. Known writes are the oracle:
localStorage `greeting=hello` + `mint_ls_key=mint_ls_value_δ`; IndexedDB `mintdb`/`notes`
`put({title:'first note',n:42,tags:['a','b']},'note-1')`; a cached resource with body
`CACHED-CONTENT-MARKER-9427`. Full mint command + flags in
`components/parser/chromium-storage-forensic/tests/data/README.md`. Confidence: ✓ (verified —
tests decode the known writes).

(The inner `…-235706.dmp` carries its own published SHA256 — see §A6.)
