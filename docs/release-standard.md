# Fleet Release & Distribution Standard

SecurityRonin-specific release values, secrets and overrides. General mechanics live in the `release` skill (`~/.claude/skills/release.md`); this file holds what is fleet-specific. Referenced from `CLAUDE.md`.

---

## Release & Distribution Standard — binaries + Homebrew/apt/winget (every app/CLI repo)

> **The general release/pre-push *mechanics* — the build matrix, repo "About"
> metadata (description/topics), GitHub Pages enablement + footer/docs link
> verification, README readiness (adapt from `~/src/blazehash`), the winget
> bootstrap, the cargo-wix/cargo-deb gotchas, and all verify commands — live in
> the `release` skill (`~/.claude/skills/release.md`), the primary source. This
> section keeps only **fleet-specific values & overrides** (SecurityRonin org
> secrets, the shared tap, the Cloudsmith org, repo lists, forensic-crate
> specifics).**

Reference implementations (both verified end-to-end): **`blazehash`** and **`disk-forensic`** —
`.github/workflows/release.yml` is byte-identical between them except for the binary/crate name and
the Homebrew dispatch `event-type`. Copy from one of those, then apply the rules below. This applies
to **apps/CLIs** (the `*4n6` binaries, `blazehash`, GUI tools) — the `v*` tag drives their binaries +
Homebrew/apt/winget. **Library *crate* publishing to crates.io is NOT done by the `release.yml` `crate`
job — it is release-plz's job** (next subsection); a repo that is both a lib and a CLI runs both
(release-plz publishes the lib crates on merge to `main`; the `v*` tag ships the binary).

### Library crate publishing — release-plz (PR-based, BINDING fleet standard)

Every repo that publishes **library crates** to crates.io uses **release-plz**, not a hand-cut version
bump and not the `release.yml` `crate` job. release-plz watches `main`, computes per-crate SemVer bumps
from conventional-commit types, and opens a **release PR** that edits the `Cargo.toml` versions + writes
the `CHANGELOG`s; **merging that PR publishes** (a dependency-ordered `cargo publish`). The PR is not
code review — for a solo dev it is the reviewable, one-click checkpoint before an *irreversible*
crates.io publish (versions yank-but-never-delete; names claimed forever), and it hands you the
changelog for free. Full mechanics live in the `release` skill (`~/.claude/skills/release.md` →
"release-plz (PR-based library publishing)"); this section is the binding policy + lived gotchas.
Reference (verified end-to-end): **`forensicnomicon`** — facade `1.7.0` + core `1.2.0` + data `1.3.0`
all published via one release PR.

**Adopt it in a library repo with:**
1. **`.github/workflows/release-plz.yml`** — two jobs, both on push to `main`, SHA-pinned actions:
   `release-plz-pr` (`command: release-pr`) opens/updates the PR; `release-plz-release`
   (`command: release`) publishes any crate whose `Cargo.toml` version is ahead of crates.io. Copy
   forensicnomicon's verbatim.
2. **`release-plz.toml`** with `release_commits = "^(feat|fix|perf|refactor|doc|revert)"` — the allowlist
   that kills the changelog-churn release loop (`chore`/`ci`/`test`/`style`/`build` never release) and
   skips release-plz's own release commits. For every **non-published** workspace member (build/codegen
   tools like forensicnomicon's `ingest`) set `release = false` + `publish = false`, **mirrored** in its
   `Cargo.toml` (release-plz cross-checks the two).
3. **`CARGO_REGISTRY_TOKEN`** — the same ORG-level secret the tag pipeline already uses (fleet-wide, no
   per-repo setup); delete any repo-level shadow copy (the shadowing trap above).
4. A **`CHANGELOG.md`** seed per published crate (release-plz appends to it).

**Discipline & gotchas (all lived on the forensicnomicon cut):**
- **Conventional-commit types drive the bump** — `feat`→minor, `fix`→patch, breaking→major; `test`/
  `chore`/`docs`-only work rides along without cutting a release. **A security fix uses
  `fix(security):`** (a `fix` with a `security` scope) so it cuts a patch release — NEVER a bare
  `security:` type, which `release_commits` (`^(feat|fix|perf|refactor|doc|revert)`) does not match,
  silently stranding the fix on `main` unpublished (lived case: the RUSTSEC-2026-0190 `anyhow` bumps).
- **Merge the release PR with a MERGE commit, NOT squash** — squash rewrites the version-bump commit
  release-plz keys on.
- **An API-changing `feat` must regenerate the `public-api/*.txt` baseline in the SAME release**, or the
  `public-api` tripwire turns the release PR red:
  `cargo public-api -p <crate> --all-features --omit blanket-impls,auto-trait-impls,auto-derived-impls > public-api/<crate>.txt`
  (pin the tool to the version in `public-api.yml`).
- **`release.yml`'s tag trigger MUST be `v[0-9]*`, never `v*`** — release-plz cuts per-crate library
  tags `<crate>-vX.Y.Z`, and a crate whose name starts with `v` (fleet has `vhd`/`vhdx`/`vmdk`/`vsc`/
  `veracrypt`/`volume-core`…) produces `v…-vX.Y.Z`, which the `v*` glob **wrongly matches** → a library
  publish fires a binary build. `v[0-9]*` requires a digit right after `v`, which a `<name>-v…` tag never
  has (a crate name's first char is a letter), so bare `vX.Y.Z` tags match and per-crate tags don't. Fix
  any existing `release.yml` still on `v*` (the `blazehash`/`disk-forensic` reference workflows too).
- **The complementary control: set `git_tag_name = "{{ package }}-v{{ version }}"` in `release-plz.toml`.**
  Without it, release-plz's *default* tag for a single-crate workspace is the bare `v{{ version }}`, which
  **collides with the binary `v[0-9]*` tags** — release-plz then sees a manually-pushed `v0.7.1` and dies
  `local package … has a greater version (0.7.1) … but the git tag v0.7.1 exists` (bit timeglyph 0.7.1,
  2026-07-20). The `{{ package }}-v` prefix is what actually makes the "release-plz cuts `<crate>-vX.Y.Z`"
  assumption above hold. **Both controls are required**: `git_tag_name` (release-plz side) *and* the
  `v[0-9]*` trigger (release.yml side) — audit every dual release-plz + tag-release repo for the pair.
- **Verify the publish landed** on crates.io (independent oracle — the crates.io JSON API needs a
  `User-Agent`), never from a green run alone.
- **A release PR whose ONLY red check is `Cargo Vet` failing `<own-crate>:<newver> missing ["safe-to-deploy"]` means that crate is not declared first-party** — set `audit-as-crates-io = false` under its `[policy."<crate>"]`, never exempt the version (an exemption re-breaks on the very next bump). Every version bump reds the vet job until you do; it silently blocked 28 of 44 open fleet release PRs. Full decision tree for this and every other vet finding: **[ADR-0018](docs/decisions/0018-supply-chain-vet-renovate-policy.md)**.
- **A `git filter-repo` history rewrite on a PUBLISHED repo silently breaks release-plz — re-point the release tags afterwards.** Rewriting content (a PII/secret scrub) changes the bytes of the already-published version's source, so **no commit reproduces the published `.crate` tarball any more**. release-plz's package-equality check then walks *backwards past the release tag* hunting for a content match, and dies on the first commit whose manifest cannot resolve in an isolated clone — aborting with `failed to determine next versions` / `failed to check package equality for <crate> at commit <sha>`, so **no release PR is ever opened** and the fix sits unpublished while crates.io keeps serving the buggy version. The rewrite also **mis-maps the tags**: filter-repo rewrote `<crate>-v0.1.0` onto a commit *before* the `chore: release v0.1.0` commit that actually carries that version's tree. **Fix: `git tag -f -a <crate>-v<ver> <the chore: release commit>` and `git push --force origin <tag>`** — release-plz then computes the diff and opens the PR normally (never hand-bump the version to work around it; that skips the one reviewable checkpoint before an irreversible publish, and CLAUDE.core.md forbids it). Diagnose with: clone the repo ALONE into a temp dir (`git clone --no-local`) and run `cargo metadata` at HEAD, at the tag, and at the commit named in the error — that isolates which commit is unresolvable. Lived case: discord-desktop-forensic, after the user-id scrub (2026-07-30).
- **`version + path` deps pointing at SIBLING repos are a release-tooling landmine that CI never catches.** `dep = { version = "0.1", path = "../other-repo/crate" }` resolves fine locally and in CI (the sibling is checked out next door in the components tree) but fails for **every tool that clones the repo alone** — release-plz, `cargo package`, `cargo publish --dry-run` — with `failed to read ../other-repo/crate/Cargo.toml`. Migrate to registry-only (`dep = "0.1"`) as soon as the sibling publishes, and remember the *old commits keep the landmine* for any historical operation (which is exactly how the case above detonated). Verify with an isolated `git clone --no-local` + `cargo metadata`, not a local build.

### What one `v*` tag delivers

A single annotated, signed tag (`git tag -s vX.Y.Z && git push origin vX.Y.Z`) triggers
`release.yml`, which produces **all** of:
- **Standalone executables for macOS (aarch64 + x86_64), Linux (aarch64 + x86_64, musl-static), and Windows (x86_64 MSI)** — attached to a GitHub Release with a `checksums.txt`.
  - **GUI apps** (a repo shipping a windowed binary — e.g. timeglyph's `timeglyph-lens` overlay): the Windows **MSI must install the GUI binary AND create a Start Menu shortcut**. A portable winget **zip** gives the CLI a PATH alias but **no launcher**, so the GUI ends up *"nowhere to be found"* (lived case: winget installed only `timeglyph.exe`, never the lens). Two binaries from two crates + the ICE-clean shortcut pattern (HKCU keypath in a ProgramMenuFolder subfolder; never `light -sval`) are in the **release skill → gotcha #7 (GUI-app MSI)**. On **macOS the same rule applies — GUI ⇒ Homebrew Cask** (a `.app` icon), and Homebrew has two modes, chosen by whether the app has a GUI:
    - **Pure CLI → Homebrew Formula** (`brew install <name>`): `bin.install` puts the binary on `$PATH`. For headless CLIs — most fleet tools.
    - **GUI → Homebrew Cask** (`brew install --cask <name>`): the cask's `app "<Gui>.app"` stanza installs a `.app` bundle into `/Applications` (Launchpad / Spotlight / Dock icon); a `binary` stanza also exposes the GUI's CLI on `$PATH`. **MANDATORY whenever the repo ships a GUI** — a Formula only drops a bare binary with no icon, so a windowed app is "nowhere to be found" (the macOS twin of the winget-portable-zip trap).

    A CLI+GUI repo ships **both** (timeglyph is the fleet's first): the **Formula** carries the pure CLI (`timeglyph`), and a **Cask** carries the GUI (`timeglyph-lens.app` + its CLI via the `binary` stanza, `depends_on` the formula so one `--cask` install brings the CLI too). Mechanics — building the `.app` bundle (Info.plist + `.icns`), the release `.app.zip` artifact (zipped with `ditto`), and generating the cask in the shared tap's `update-<pkg>` handler — are in the **release skill → "macOS GUI: ship a Homebrew Cask, not a bare binary."** The fleet builds **no DMGs** (a cask ships the `.app` inside a `ditto` zip; the release-skill DMG recipe is a generic template, not our standard). **A cask `.app` MUST be Developer-ID-signed + notarized — this is a hard prerequisite, not optional.** Homebrew Cask quarantines by default; an unsigned/un-notarized `.app` is Gatekeeper-blocked ("app is damaged"), the `--no-quarantine` / `quarantine false` bypass is deprecated + being removed, and **Homebrew drops support for casks that fail Gatekeeper on 2026-09-01**. So a GUI cask needs an **Apple Developer account** ($99/yr) + `codesign --deep --options runtime` (Developer ID Application) + `xcrun notarytool submit --wait` + `xcrun stapler staple` in `release.yml`, mirroring the Windows Azure-Trusted-Signing step. (The **Formula CLI runs unsigned** — Rust ad-hoc-signs the arm64 binary, and formula artifacts aren't quarantined like cask downloads — but signing the CLI too is good hygiene.)
- **crates.io** publish (`crate` job).
- **Homebrew** formula bump (dispatch → shared tap).
- **apt/.deb** for amd64 + arm64, uploaded to the Release **and** pushed to Cloudsmith (`apt` repo).
- **winget** auto-PR (after the one-time manual bootstrap — see below).

Build matrix targets: `aarch64-apple-darwin`, `x86_64-apple-darwin`, `x86_64-unknown-linux-musl`,
`aarch64-unknown-linux-musl`, `x86_64-pc-windows-msvc` (binaries); `x86_64-unknown-linux-gnu` +
`aarch64-unknown-linux-gnu` (the `deb` job only).

### Secrets — ORG-level, single source of truth

All four release secrets live as **SecurityRonin organization** secrets (visibility = all repos), so
every fleet repo inherits them and rotation is one update:

| Secret | Purpose | Notes |
|---|---|---|
| `CARGO_REGISTRY_TOKEN` | crates.io publish | crate-scoped tokens are *more* secure than one broad token, but org-wide is the chosen trade-off for fleet convenience |
| `TAP_GITHUB_TOKEN` | dispatch to `SecurityRonin/homebrew-tap` | owned by `securityronin-bot`; the bot must have **write** (push) on the tap (see Homebrew) |
| `WINGET_TOKEN` | PR to `microsoft/winget-pkgs` | `securityronin-bot` PAT, `public_repo`; the fork lives at `securityronin-bot/winget-pkgs`; `release.yml` sets `fork-user: securityronin-bot` |
| `CLOUDSMITH_API_KEY` | push `.deb` to Cloudsmith | account-wide; works for any repo |

- **Shadowing rule (the trap):** a **repo-level** secret *overrides* an org secret of the same name.
  After adding an org secret, **delete the repo-level copies** or the repo keeps using its stale local
  value and silently ignores the org one. (`gh secret delete <NAME> -R SecurityRonin/<repo>`.)
- **Secret values are write-only** — they cannot be read back via API or copied between repos; they
  live only in GitHub's vault (and your password manager). "We have it in <repo>" means it's set on
  that repo's GitHub, not recoverable from the checkout.
- **Org secrets need `admin:org`** to manage via CLI (`gh auth refresh -h github.com -s admin:org`),
  or use the web UI (org owner can always do it there).
- **Binaries + GitHub Release need only the built-in `GITHUB_TOKEN`** — the four secrets are only for
  crates.io / Homebrew / winget / Cloudsmith. A release with *just* the executables works with zero
  external secrets.

### Windows code signing — Authenticode under Security Ronin Ltd (UK)

Fleet Windows binaries (`.exe`, and the Profile-B `.msi`) are **Authenticode-signed under
Security Ronin Ltd (the UK company)** via **Azure Trusted Signing / Artifact Signing**, so
Windows/**SmartScreen** show a *verified publisher* and winget installs don't warn — and because
it's one identity, SmartScreen reputation accrues **fleet-wide**. Fixed values:

| Field | Value |
|---|---|
| Trusted Signing account | `securityronin` — region **North Europe** → endpoint `https://neu.codesigning.azure.net` |
| Certificate profile | `securityronin-public` (**Public Trust**) |
| Validated identity | **Security Ronin Ltd** (UK), D&B / DUNS-verified |
| Azure subscription | UK / GBP, **PAYG**; tenant identity `info@securityronin.com` (fresh UK-born identity — see below) |
| CI auth | Entra app `securityronin-ci-signing` + **OIDC** federated credential (subject `…:environment:release`), role `Artifact Signing Certificate Profile Signer`; secrets `AZURE_TENANT_ID` + `AZURE_CLIENT_ID` + `AZURE_SUBSCRIPTION_ID` (non-sensitive IDs — OIDC, no client secret). CI **must run `azure/login` before the signer** (the action's DefaultAzureCredential doesn't do the OIDC exchange itself) — see [`docs/release-sop.md`](docs/release-sop.md) §5. |

- **Sign under the UK entity ONLY.** HK (**Scarlet Monkey Ltd**) is **ineligible for Public
  Trust** (Azure Artifact Signing serves US/CA/EU/UK orgs only) — never sign fleet binaries under
  it. The publisher on every signed binary reads **"Security Ronin Ltd"**.
- **Country is fixed at an identity's first Azure signup and is irreversible** — `albert@` is
  HK-locked forever, so the UK account was created with a **fresh identity** (`info@`, no prior
  Azure) that could select United Kingdom. Reuse `info@` for anything UK-Azure; never retry under
  an HK-tainted identity.
- Add `AZURE_TENANT_ID` + `AZURE_CLIENT_ID` as **SecurityRonin org secrets** (same model + shadowing
  rule as the four distribution secrets above).
- **Per-repo onboarding procedure — [`docs/release-sop.md`](docs/release-sop.md) §5 "Windows code
  signing"** (fleet-owned, self-contained): create the repo's federated credential, wire the two
  `release.yml` steps (`azure/login` → `trusted-signing-action`), verify. §5 carries the one-time
  Azure resources + every lived gotcha (azure/login-first, `Artifact Signing …` role names,
  region-specific endpoint, PAYG-to-sign, legal-name match, WAF'd verify link). **Law + values here;
  full runbook in the SOP.**
- **Immutable OIDC subjects break the plain-name FIC — every renamed/transferred repo needs its
  own credential (since 2026-07-15).** GitHub now auto-applies the immutable-ID subject form
  `repo:SecurityRonin@233419394/<repo>@<repoid>:environment:release` to any repo **created, renamed,
  or transferred** after 2026-07-15; the IDs survive renames, so you **cannot** revert to plain
  names. A credential matching only plain names — the flexible `securityronin-fleet-release`
  (`claims['sub'] matches 'repo:SecurityRonin/*:environment:release'`) — then fails
  **`AADSTS7002131 No matching federated identity record`**. You can't just broaden that wildcard:
  the flexible-expression validator **rejects** the `@id` shape
  (`InvalidFederatedIdentityCredentialValue`), and the expression language has **no `or`** (only
  `matches`/`eq`/`and`). Fix (Microsoft's immutable-subjects migration) — add a **standard
  subject-based** FIC on `securityronin-ci-signing` (appId `1381bf9d-c6b2-4f17-becd-0fb83083b90d`)
  with the repo's exact literal subject; leave the shared wildcard untouched:
  `az ad app federated-credential create --id 1381bf9d-c6b2-4f17-becd-0fb83083b90d --parameters '{"name":"<repo>-release-immutable","issuer":"https://token.actions.githubusercontent.com","subject":"repo:SecurityRonin@233419394/<repo>@<repoid>:environment:release","audiences":["api://AzureADTokenExchange"]}'`.
  Get the exact subject verbatim from the failing run's log (it prints `subject claim - …`).
  **prop-window** (renamed from prop-browser) was the first to hit this.
- **Migration debt:** current Profile-A CLIs ship the Windows `.zip` **unsigned** — wire the signing
  step into each app/CLI `release.yml`.

### Gotchas that fail — or silently skip — despite a green-looking run

1. **`rust-toolchain.toml` pin overrides the cross-build → `error[E0463]: can't find crate for core`.**
   If the repo pins `rust-toolchain.toml` (apps pin to the dev toolchain, e.g. `1.96.0`), that pin
   overrides whatever toolchain the `dtolnay/rust-toolchain` action installs. The action adds the
   cross-*target* to its default `stable`, but cargo actually builds with the pinned version — which
   lacks the target → every cross build fails. **Fix:** pin the action to the *same* version, so the
   target lands on the toolchain cargo uses:
   ```yaml
   - uses: dtolnay/rust-toolchain@<sha> # stable
     with:
       toolchain: 1.96.0          # MUST match rust-toolchain.toml
       targets: ${{ matrix.target }}
   ```
   Apply to **both** the `build` job and the `deb` job (native `crate`/publish is unaffected).
   Symptom is platform-independent and fails in ~20s (before real compilation). A *native* `cargo
   publish --dry-run` will NOT catch it — only a `--target` build does.
2. **`cargo-deb` (v3.x) errors `The package must have a copyright or authors property`.** Add
   `authors = ["Albert Hui <albert@securityronin.com>"]` to `[package]` in `Cargo.toml`. (blazehash
   had it; disk-forensic didn't — that's the whole difference.) Verify locally before tagging:
   `cargo install cargo-deb && cargo deb` must package past the copyright check (the macOS-only
   `strip: unrecognized option --strip-unneeded` warning is harmless — GNU strip on the Linux runner
   is fine).
3. **The `crate` job can be silently ABSENT — a green release that never publishes** (bit
   `timeglyph`). The template above lists a `crate` publish job, but a repo can drift and lack it
   entirely: the `v*` tag goes green, the GitHub Release + binaries + Homebrew/apt/winget all ship, and
   **crates.io never gets the crate** — nothing fails. `timeglyph` 0.1–0.3 were hand-published, so the
   gap hid until 0.4.0 (release fully green, crates.io stuck at 0.3.0). **Audit every app/CLI repo:**
   `grep -rn "cargo publish" .github/workflows`; if absent, add a `publish-crate` job `needs: build`
   running `cargo publish --locked` with `CARGO_REGISTRY_TOKEN` (the org secret above — all repos). The
   general failure mode + job template are in [`docs/release-sop.md`](docs/release-sop.md) §3.
4. **Non-workspace GUI (`lens`/overlay) crate builds into its OWN `target/` → packaging can't find the
   binary** (bit `timeglyph` 0.4.0). When the GUI crate is `exclude`d from the workspace, `cargo build
   --manifest-path <gui>/Cargo.toml` outputs to `<gui>/target/`, not the root `target/`; the
   macOS/Windows package step (`tar … target/<triple>/release/<gui-bin>`) and the `cargo-deb --variant
   gui` merge-asset then fail `Cannot stat: No such file` — and *only* on the GUI-building targets
   (Linux musl is CLI-only, so it passes and the failure reads as platform-specific). **Fix:** set
   `CARGO_TARGET_DIR: ${{ github.workspace }}/target` on every GUI-crate build step so it co-locates
   with the CLI binary.
5. **A channel on its OWN tag = a silently-forgotten partial release** (bit `timeglyph` — PyPI wheels
   were on a separate `py-v*` tag). The `v*` release shipped the crate + binaries + brew/apt/winget, but
   the wheels never went out (no `py-v*` tag cut) **and** `bindings/python` was never bumped (stuck at
   0.3.0 vs the crate's 0.4.0), so a belated `py-v0.4.0` would have built a stale 0.3.0 wheel. **Fix:**
   one `v*` tag fans out to **every** channel — put the `wheels` + `publish-wheels` jobs *in*
   `release.yml`, not a parallel `py-v*` workflow; a `ci.yml` guard enforces `bindings/` version ==
   crate version (lockstep); make `publish-crate` idempotent (skip if the version is already on
   crates.io) so a re-tag ships only the missing channel. **PyPI auth: `PYPI_API_TOKEN` secret** —
   `publish-wheels` uses `pypa/gh-action-pypi-publish` with `password: ${{ secrets.PYPI_API_TOKEN }}`;
   set it once from the token in `~/.pypirc` (`gh secret set PYPI_API_TOKEN -R <org>/<repo>`, or org-wide
   like the other release secrets). (OIDC Trusted Publishing — `id-token: write`, no stored secret — is
   the alternative if you'd rather not manage a token; it needs a one-time trusted-publisher
   registration on pypi.org.) General pattern in [`docs/release-sop.md`](docs/release-sop.md) §3.

### crates.io versioning rule

A crate version can be published **once**. **Bump `version` in `Cargo.toml` before every release tag**
— a tag whose `crate` job re-publishes an existing version fails "already exists." Re-tagging the
*same* `vX.Y.Z` is only safe if the prior run never reached the `crate`/`release` jobs (e.g. it died
in `build`); once published, you must bump (e.g. `0.8.2` → `0.8.3`). To move a not-yet-published tag:
`git tag -d v… ; git push origin :refs/tags/v… ; git tag -s v… ; git push origin v…`.

### On a `0.x` library, release-plz turns `feat:` into a fleet migration

release-plz picks the bump from the **commit type**, not from whether the change
actually breaks anything. On a `0.x` crate a `feat:` commit cuts a **minor**
(`0.7.2` → `0.8.0`), and cargo treats `0.7` and `0.8` as incompatible crates.

Lived, 2026-08-23: a purely *additive* `forensic-vfs` change — a new trait plus
variants on two already-`#[non_exhaustive]` enums — released as **0.8.0** and
instantly stranded `forensic-vfs-engine` and the **18 reader crates** it links
with `features = ["vfs"]` on 0.7. Mixing the two is `E0277` (two incompatible
`FileSystem`/`DynFs` traits), so a one-line change became an 18-repo coordinated
release train. A `0.7.3` would have carried the identical API and every consumer
would have picked it up on a lockfile refresh.

**Before merging a release PR for a `0.x` crate, read the version it proposes and
count who is pinned to the current minor:**

```bash
grep -rl 'forensic-vfs = .*"0\.7"' --include=Cargo.toml ~/src/ronin-issen \
  | grep -v /target/ | cut -d/ -f1-7 | sort -u | wc -l
```

If the change is additive and the answer is more than a couple, keep it a patch
(`fix:`/`chore:` framing, or override the version in the release PR). The release
PR looks routine and the diff is a version string — nothing warns you.

### App requirement: conventional `--version`

The CLI must support `-V`/`--version` printing `<bin> X.Y.Z` to stdout and exiting **0** (use
`env!("CARGO_PKG_VERSION")`). The Homebrew formula `test do` block asserts on it
(`assert_match "<bin> #{version}", shell_output("#{bin}/<bin> --version")`). disk4n6 originally lacked
it and treated `--version` as a path — add it (TDD: RED parse test → GREEN).

### Homebrew — shared tap, per-project dispatch + handler

- One tap for the whole fleet: **`SecurityRonin/homebrew-tap`** (`brew install SecurityRonin/tap/<bin>`).
- **Each project dispatches its OWN `event-type`** (`update-<bin>`, e.g. `update-blazehash`,
  `update-disk4n6`) and the tap has a **matching per-project handler workflow** `update-<bin>.yml`
  listening on that type. **Never share a generic `update-formula` event** — two projects on the same
  event collide (the second project's release fires the first project's updater). Each handler downloads
  the release `checksums.txt`, fills the SHA256s, and writes `Formula/<bin>.rb`.
- **`securityronin-bot` must have `write` (push) on `homebrew-tap`** — `repository_dispatch` requires
  write access; a read collaborator gets 403. (Granting it creates an *invitation* the bot must accept:
  `gh api -X PUT repos/SecurityRonin/homebrew-tap/collaborators/securityronin-bot -f permission=push`
  then accept as the bot via `gh api -X PATCH user/repository_invitations/<id>`.)
- Formula class name is the bin name capitalized, digits kept (`disk4n6` → `class Disk4n6 < Formula`).
- The tap handler commits via the GitHub API / `github-actions[bot]` (GitHub-verified) — consistent
  with the tap's existing bot-commit style.

### winget — action does UPDATES only; first version is a MANUAL bootstrap

`vedantmgoyal9/winget-releaser` **cannot create a new package** — it only bumps an existing one. So
the `winget` job is `continue-on-error: true` and **fails harmlessly until the first version is
submitted by hand**. After the first PR merges, every future release auto-PRs the update. The PR
title tells which is which: a manual first submission says **"New package: …"** / "Add …"; the
action's auto-PRs say **"New version: …"**. (blazehash's 0.2.0 was a manual PR by `h4x0r`; 0.2.1+ were
auto by the bot.)

**Bootstrapping the first version from a Mac (no Windows, no `wingetcreate` — it's Windows-only):**
1. `brew install msitools` and extract the MSI GUIDs:
   `msiinfo export <bin>-X.Y.Z-x86_64-pc-windows-msvc.msi Property | grep -iE 'ProductCode|UpgradeCode|ProductVersion'`.
2. Get the installer SHA256 from the release `checksums.txt` (winget wants it **uppercase**).
3. Hand-author the **3 manifests** (model them on an existing fleet package already in winget-pkgs,
   e.g. `manifests/s/SecurityRonin/blazehash/<v>/`): `<Id>.yaml` (version), `<Id>.installer.yaml`
   (InstallerType `wix`, Scope `machine`, `ProductCode`, `AppsAndFeaturesEntries` with Product+Upgrade
   codes, the installer URL + SHA256), `<Id>.locale.en-US.yaml` (publisher/license/description/tags).
4. Submit via the bot, API-only (don't clone the huge winget-pkgs repo): `gh auth switch --user
   securityronin-bot` → `gh repo sync securityronin-bot/winget-pkgs --source microsoft/winget-pkgs` →
   create a branch ref at master → `PUT` the 3 files under
   `manifests/s/SecurityRonin/<bin>/X.Y.Z/` → `POST` a PR `head: securityronin-bot:<branch>`,
   `base: master` → `gh auth switch --user h4x0r`.
- **`PackageIdentifier` must be identical** between the manual first PR and the action's `identifier:`
  input (`SecurityRonin.<bin>`), or future auto-updates orphan.
- **Keep the MSI `UpgradeCode` stable across versions** (it's fixed in `wix/main.wxs`) — winget keys
  upgrades off it; a changing UpgradeCode makes each release look like an unrelated package.

### Cloudsmith (apt)

- One account-wide `CLOUDSMITH_API_KEY`. **The destination repo must exist first** —
  `securityronin/<repo>` at cloudsmith.io (the push 404s otherwise). Public install path:
  `curl -1sLf https://dl.cloudsmith.io/public/securityronin/<repo>/setup.deb.sh | sudo bash`.

### Pre-tag checklist

1. `version` bumped in `Cargo.toml` (not already on crates.io).
2. `[package] authors` present (cargo-deb).
3. `release.yml` toolchain pinned to `rust-toolchain.toml`'s version (if pinned).
4. CLI has `--version`.
5. Org secrets present; repo-level shadows deleted.
6. Homebrew: per-project `update-<bin>.yml` exists in the tap; dispatch `event-type` matches; bot has
   write on the tap.
7. Cloudsmith repo created.
8. First winget version bootstrapped (or accept `continue-on-error` until you do).
9. Tag is **signed** (`git tag -s`).
