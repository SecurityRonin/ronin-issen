# Fleet Test Corpus Standard

Corpus catalog rules, how to mint filesystem fixtures on macOS, and the Case-001 convergence
validation set. Referenced from `CLAUDE.md`.

---

## Minting filesystem fixtures on macOS — rootless podman cannot `mknod`

Any fixture carrying a **character or block device** hits this, and the symptom points at the
wrong culprit. Rootless podman **cannot create a device node even with `--privileged`**:

```
$ podman run --rm --privileged ubuntu:24.04 mknod /tmp/c c 1 3
mknod: /tmp/c: Operation not permitted
$ grep CapEff /proc/self/status
CapEff: 000001ffffffffff          # cap_mknod IS present
```

The capability is namespaced; the kernel requires *real* (init-namespace) `CAP_MKNOD`. It has
nothing to do with the filesystem being written.

**Run the control before blaming the driver.** `mkfifo` succeeds in the same container while
`mknod` fails, which reads like a filesystem-driver limitation — it is not. One command settles
it: if `mknod /tmp/x c 1 3` fails on **tmpfs**, the container is the cause, and no mount option
will fix it. (Four ntfs-3g option sets — `permissions`, `acl`, `umask=000`, plain — were tried
before that control was run. All four fail identically, which is itself the tell.)

**The fix on macOS** — a rootful container *inside* the podman VM, no change to the machine's
default mode:

```sh
podman machine ssh 'sudo podman run --rm --privileged --device /dev/fuse \
  -v /Users/<you>/work:/work -v /Users/<you>/work/out:/out \
  docker.io/library/ubuntu:24.04 bash /work/mint.sh'
```

- `/Users` is already mounted into the VM, so host bind-mounts work from the rootful container.
- Image names need the `docker.io/library/` prefix there.
- **Loop devices:** the container's `/dev` carries only `loop0`, so `losetup -f` names a device
  that does not exist and fails with `No such file or directory`. Materialize them first —
  rootful `mknod` works: `for i in 0 1 2 3; do [ -e /dev/loop$i ] || mknod /dev/loop$i b 7 $i; done`
- **`apt-get update` is never optional** before `apt-get install`: the image pins exact `.deb`
  versions that 404 once Ubuntu supersedes them.

### What each filesystem can actually express

Do not assume a format records a type just because the OS has one:

| | symlink | char | block | FIFO | socket |
|---|---|---|---|---|---|
| **UDF** (ICB `file_type`) | `0x0C` | `0x07` | `0x06` | `0x09` | `0x0A` |
| **NTFS** — ntfs-3g Interix (default) | `IntxLNK` | `IntxCHR` | `IntxBLK` | **not recorded** | **not recorded** |
| **NTFS** — ntfs-3g `-o special_files=wsl` | `0xA000001D` | `0x80000025` | `0x80000026` | `0x80000024` | `0x80000023` |
| **NTFS** — classic Windows | `0xA000000C` | — | — | — | — |

- **Interix cannot express a FIFO or a socket distinguishably.** A FIFO is a zero-length `$DATA`
  and a socket a one-byte `$DATA`, with no magic — `libntfs-3g/dir.c`'s own comment reads
  *"FIFO or regular file."* A reader must report `File`; inferring a FIFO from "empty file"
  fabricates an observation the volume never made.
- **No Linux tool writes the classic `0xA000000C` / `0xA0000003` tags.** ntfs-3g writes Interix
  or WSL forms; the in-kernel `ntfs3` driver defines only `MOUNT_POINT` and `SYMLINK` and has no
  LX tags at all. For those, either author the buffer and let **ntfs-3g's read path** confirm it
  (it decodes classic tags via the `system.ntfs_reparse_data` xattr), or mint on real Windows
  with `mklink` and capture `fsutil reparsepoint query` as the answer key.

**"No local tool can create X" and "no local tool can validate X" are different claims.** Most
format libraries read far more than they write; check the read path separately before reaching
for heavier infrastructure.

---

## Test Corpus Catalog — keep it current (MANDATORY)

`ronin-issen/docs/test-data-catalog.md` is the **single fleet-wide catalog** of all forensic test data —
real datasets (what + source + hotlinked download URL + MD5) and synthetic fixtures (the **exact
command line(s)** that produce them). Because `tests/data/` is gitignored, this catalog is the only
committed record others can use to reproduce the corpus.

**Whenever you download or build test data anywhere in the fleet, update the catalog in the same
change:**
- **Downloaded a real dataset?** Add an entry with: what it is, authoritative source, **hotlinked
  download URL**, `md5` of the file, and a redistribution note. Confirm provenance by inspecting the
  artifact, not just the filename (Doer-Checker).
- **Built a synthetic fixture?** Record the **verbatim command(s)** that generate it (the
  `qemu-img` / `mkfs` / `xorriso` / `ewfacquire` / `dar` / `hdiutil` line, or the in-code Rust
  builder fn + `file:line`). Never write "generated for coverage" without the command — if there is
  no generator, say "NO GENERATOR IN REPO" rather than guessing.
- Classify each entry (`REAL-ext` / `REAL-self` / `SYNTHETIC` / `VENDORED` / `FUZZ`) and mark
  confidence (`✓` confirmed / `~` inferred / `?` undetermined).
- Keep the **§H MD5 manifest** in sync (hash new files; `tests/data/` is gitignored so hashes must
  live in the catalog).

**One repo-root `tests/data/` (MANDATORY layout — workspaces included; naming rationale in ADR-0004 — the directory is `tests/data/`, "corpus" classifies real datasets *within* it, never the directory).** Every repo keeps a *single*
`tests/data/` at the repo root, never per-member `<member>/tests/data/` directories. In a Cargo
workspace each member's integration tests reach the shared fixtures with a **relative `include_bytes!`
path** — from `<member>/tests/<file>.rs` the repo root is two levels up, so it is symmetric across
members: `include_bytes!("../../tests/data/<file>")`. This keeps one home, one README, and no
duplication, and it is conceptually neutral (a carving fixture used only by `<x>-forensic` need not
live "inside" `<x>-core`).

- **Never symlink fixtures** to fake a shared location. `include_bytes!` follows symlinks on Unix, but
  **git on Windows materializes a symlink as a text file containing the link target** — `include_bytes!`
  would then embed that path *string* instead of the file bytes, silently breaking the Windows CI
  runner. Use the relative path, not a symlink.
- **Verification gate:** after moving/adding fixtures, `cargo test` for every member must still compile
  (the `include_bytes!` paths must resolve) — a wrong path is a build error, not a silent miss.

**`tests/data/README.md` (one per repo, MANDATORY).** Modeled on
[`issen/tests/data/README.md`](../tests/data/README.md): a per-file `#### <filename>` entry giving
**Source / Identity / writeup URL(s) / original download URL (hotlinked) / MD5 (or sha256) / notable
contents** for real datasets, and the **verbatim generator command** (or builder `fn` at `file:line`)
for synthetic fixtures — never a download URL for something we generate. The README is the co-located
human-facing detail; `docs/test-data-catalog.md` stays the single machine-index — **cross-reference, never
duplicate** (the README links up to the catalog). Document large untracked/gitignored artifacts here
too (provenance even when the bytes aren't committed — e.g. a vendored oracle's test corpus). Use
straight ASCII in paths/commands.

### Convergence / release end-to-end validation corpus (Case-001 Szechuan)

Whenever a change could affect issen's runtime output across artifact types — a
fleet-wide dependency convergence (e.g. the forensicnomicon 0.11 sweep), a release
candidate, or any cross-cutting parser/report change — **confirm it end-to-end with a
single unified default-pipeline run (`issen <the four sources…> -o <db>`, no subcommand)
over these four Case-001 (DFIR Madness "Szechuan Sauce") sources, and NO others** (no pagefile, no pcap):

1. **DC01 memory** — `tests/data/dfirmadness-szechuan-sauce/DC01-memory.zip`
2. **DC01 disk** — `tests/data/dfirmadness-szechuan-sauce/DC01-E01.zip`
3. **Desktop (SDN1RPT) memory** — `tests/data/dfirmadness-szechuan-sauce/DESKTOP-SDN1RPT-memory.zip`
4. **Desktop (SDN1RPT) disk** — `tests/data/dfirmadness-szechuan-sauce/DESKTOP-E01.zip`

These four exercise both hosts × both media (disk + memory), so the ingest drives the
full analyzer set — NTFS / registry / EVTX / prefetch / LNK / SRUM / browser / Biome on
the disk legs and memf-windows on the memory legs — all feeding one `forensicnomicon::report`
aggregation. Extract the four to `/tmp` (never under `~/src` — the committed bytes are the
zips; see the provenance standard above).

The **default `issen <evidence…>` command unifies both media in one pass** — it ingests the
disk images and parses the memory dumps *into the same timeline*, so the one-command
end-to-end is:

- `issen <DC01.E01> <DESKTOP.E01> <DC01.mem> <DESKTOP.mem> -o /tmp/<name>.duckdb` — the disk leg
  drives NTFS / registry / EVTX / prefetch / LNK / SRUM / browser / Biome (each tagged with its
  evidence source); the memory leg feeds memf-windows events into the same
  `forensicnomicon::report` aggregation. (Pass only the FIRST `.E01` segment; ewf follows
  `.E02…` automatically. A folder of mixed images + `.mem`s works too.)

Two distinctions so the next reader isn't tripped up (see **ADR 0012**): the *explicit*
`issen ingest` subcommand is **disk-only** (it points a `.mem` at `issen memory`), and
`issen memory <dump>` runs the **deep** per-dump analysis (EPROCESS / netstat / hashdump / …) —
use it for the focused single-dump view rather than the unified sweep.

Both legs completing and producing populated, non-crashing output across all analyzers is
the runtime confirmation. Deliberately exclude pagefile and pcap.
