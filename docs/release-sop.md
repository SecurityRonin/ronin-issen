# Release & Publish — Fleet SOP

**The complete, self-contained runbook for cutting a fleet release** — gates, release-plz,
the tag-driven binary/distribution pipeline, and Windows code signing. Deliberately **fat**:
a fleet doc must be executable without any personal `~/.claude` skill. The *binding law* is in
[`../CLAUDE.md`](../CLAUDE.md) §"Release & Distribution Standard"; this is how to *do* it.

---

## 0. The release flow at a glance

```
conventional commits → main
   │
   ├─ release-plz opens a version-bump PR (bump + CHANGELOG)          [§2]
   │     merge with a MERGE commit → publishes crate(s) to crates.io
   │                                  + tags <crate>-vX.Y.Z
   │
   └─ push a bare vX.Y.Z tag  (trigger: v[0-9]*)                       [§3–§5]
         release.yml → build matrix → SIGN Windows → SLSA attest
                     → GitHub Release → brew / apt / winget
                     → (idempotent) crate + wheels
```

Two publishers, non-colliding: **release-plz owns crates.io** (on PR merge); the **bare
`vX.Y.Z` tag owns binaries + distribution** (`release.yml`). Both are idempotent, so a re-tag
is safe. The two tag namespaces MUST be disjoint — see the `git_tag_name` gate in §6.

---

## 1. Gates — must pass before push / publish

### Pre-push gate (every `git push`)
- [ ] `cargo build` (workspace) green
- [ ] full test suite green (`cargo test --workspace`)
- [ ] `cargo clippy --all-targets --all-features -- -D warnings`
- [ ] `cargo fmt --check`
- [ ] secret scan clean (gitleaks CLI — see §7 for the org-repo license trap)
- [ ] no credential/debug artifact staged
- [ ] feature branch off `main` — **exception: a release itself lands on `main`**

### Pre-publish gate (any registry — everything above PLUS)
- [ ] **Dependency triad:** `renovate.json` (range `bump` + lockFileMaintenance) · `cargo deny check` green · `cargo vet` clean
- [ ] **CI actions SHA-pinned** (full commit SHAs, not floating tags)
- [ ] **Untrusted-input parsers:** a `cargo-fuzz` target per parsed structure + panic-free lints (`unwrap_used`/`expect_used` denied, `unsafe_code` forbidden/deny)
- [ ] **Tier-1 validation** documented in `docs/validation.md` (independent oracle / real data, not self-authored fixtures)
- [ ] **README to standard** (see §8) + **live Pages footer** (Privacy/Terms return real 200s)
- [ ] **version bumped** (not already on the registry) · license/description/repository/authors/MSRV complete · **name finalized**
- [ ] `cargo publish --dry-run` green (compiles from only the shipped files)
- [ ] **human provides the registry credential** — never fabricated/assumed

A crates.io/PyPI publish is **irreversible** (yank, never replace/reuse a version). Stop on red.

---

## 2. Crate publishing — release-plz (BINDING; PR-based)

Every repo publishing **library crates** uses release-plz — never a hand-cut bump, never
`release.yml`'s `crate` job as the *primary* path. Files:

1. **`.github/workflows/release-plz.yml`** — two jobs on push to `main` (`release-plz-pr` opens
   the bump PR; `release-plz-release` publishes any crate ahead of crates.io). SHA-pin actions.
   Copy `forensicnomicon`'s verbatim.
2. **`release-plz.toml`** — the essentials:
   ```toml
   [workspace]
   git_tag_enable = true
   git_tag_name   = "{{ package }}-v{{ version }}"   # MANDATORY — see §6 collision gate
   release_commits = "^(feat|fix|perf|refactor|doc|revert)"   # kills the changelog-churn loop
   ```
   Non-published members (build/codegen tools) set `release = false` + `publish = false`,
   **mirrored** in their `Cargo.toml`.
3. **`CARGO_REGISTRY_TOKEN`** — the org-level secret (fleet-wide; delete any repo-level shadow).
4. A **`CHANGELOG.md`** seed per published crate.

**Discipline:** conventional-commit type drives the bump (`feat`→minor, `fix`→patch, breaking→major;
`ci`/`chore`/`docs`/`test` ride along). **Merge the release PR with a MERGE commit, NOT squash**
(squash rewrites the commit release-plz keys on). An API-changing `feat` regenerates the
`public-api/*.txt` baseline in the SAME PR.

---

## 3. Binaries + distribution — `release.yml` (tag-driven)

Trigger on the **bare** binary tag; NEVER `v*`:
```yaml
on:
  push:
    tags: ["v[0-9]*"]    # a digit after v; release-plz's <crate>-v… tags never match
```
Jobs (gate downstream on `build` so a version that fails any target never ships/publishes):
- **`build`** (matrix: macOS arm64+x86_64, Linux musl arm64+x86_64, Windows x86_64) → build CLI
  (+ GUI on macOS/Windows) → **sign Windows** (§5) → package (`.tar.gz`/`.zip`) → upload artifacts.
- **`publish-crate`** (`needs: build`) — idempotent: skip if the version is already on crates.io
  (release-plz usually beat it), else `cargo publish --locked`. Belt-and-suspenders with §2.
- **`wheels` + `publish-wheels`** (if Python bindings) — build abi3 wheels, publish with
  `skip-existing`. Keep `bindings/*` version in **lockstep** with the crate (a `ci.yml` guard).
- **`release`** (`needs: build`) — download artifacts, `sha256sum` → `checksums.txt`, **SLSA
  attest** (`actions/attest-build-provenance`, `id-token: write`), create the GitHub Release,
  dispatch Homebrew.
- **`winget`** (`continue-on-error`) — `vedantmgoyal9/winget-releaser` updates the package.

`release.yml` permissions: `contents: write`; the build job adds `id-token: write` for signing (§5).

---

## 4. Multi-channel distribution setup

- **Homebrew** — one shared tap `SecurityRonin/homebrew-tap`. Each repo dispatches its OWN
  `event-type` (`update-<bin>`); the tap has a matching handler `update-<bin>.yml`. `securityronin-bot`
  needs **write** on the tap. Secret: `TAP_GITHUB_TOKEN`.
- **apt / Cloudsmith** — `cargo-deb` builds amd64+arm64 `.deb`, uploaded to the Release AND pushed
  to Cloudsmith repo `securityronin/<repo>` (must exist first). Secret: `CLOUDSMITH_API_KEY`.
- **winget** — `winget-releaser` does UPDATES only; **the first version is a manual bootstrap PR**
  (Windows-only `wingetcreate`, or hand-author 3 manifests via `securityronin-bot`). Keep the MSI
  `UpgradeCode` stable. Secret: `WINGET_TOKEN` (`securityronin-bot` PAT). CLIs use zip-portable
  (`installers-regex: '\.zip$'`); GUIs use MSI (`'\.msi$'`).

All distribution steps are `continue-on-error` so a release never fails on a not-yet-provisioned
channel. Org secrets are **SecurityRonin org-level** (visibility all repos); delete repo-level shadows.

---

## 5. Windows code signing (Authenticode via Azure Trusted / Artifact Signing)

Sign Windows `.exe`/`.msi` under **Security Ronin Ltd (UK)** → verified publisher in
Windows/SmartScreen/winget, no Defender friction.

### Fixed fleet resources — provisioned once (reference, do NOT recreate)

| Field | Value |
|---|---|
| Signing account | `securityronin` — **North Europe** → endpoint `https://neu.codesigning.azure.net` |
| Certificate profile | `securityronin-public` (**Public Trust**) |
| Validated identity | **Security Ronin Ltd** (UK), D&B / DUNS-verified |
| Azure subscription | `e4ba55d1-95a8-40b9-8a43-51419461e591` — UK/GBP **PAYG**; tenant identity `info@securityronin.com` |
| CI signer app | `securityronin-ci-signing` — appId `1381bf9d-c6b2-4f17-becd-0fb83083b90d`; role **Artifact Signing Certificate Profile Signer** on the account |
| Org secrets | `AZURE_TENANT_ID` · `AZURE_CLIENT_ID` · `AZURE_SUBSCRIPTION_ID` (identifiers, not secrets — OIDC, no client secret) |

### Onboard a new repo (as `info@securityronin.com` / `az login`, `h4x0r` / `gh`)

1. **Create the `release` GitHub environment** (the OIDC subject anchor):
   ```bash
   gh api -X PUT repos/SecurityRonin/<repo>/environments/release
   ```
2. **Add a federated credential** to the signer app for this repo's environment (one per repo —
   a classic FIC can't wildcard tag refs, which is why the job gates on `environment: release`):
   ```bash
   az ad app federated-credential create --id 1381bf9d-c6b2-4f17-becd-0fb83083b90d --parameters '{
     "name":"<repo>-release-env",
     "issuer":"https://token.actions.githubusercontent.com",
     "subject":"repo:SecurityRonin/<repo>:environment:release",
     "audiences":["api://AzureADTokenExchange"]
   }'
   ```
3. **Confirm the org secrets reach the repo** — `gh secret list -R SecurityRonin/<repo>` shows the
   `AZURE_*` trio; delete any repo-level shadow.
4. **Wire `release.yml`** — on the **Windows** build job, after `cargo build`, **before** zip/MSI:
   ```yaml
   build:
     environment: release          # OIDC subject → repo:SecurityRonin/<repo>:environment:release
     permissions:
       contents: read
       id-token: write             # mint the OIDC token
     # …steps…
       # OIDC login FIRST — the signer's DefaultAzureCredential does NOT do the exchange itself:
       - if: runner.os == 'Windows'
         uses: azure/login@<sha>                    # v3.x — SHA-pin
         with:
           client-id: ${{ secrets.AZURE_CLIENT_ID }}
           tenant-id: ${{ secrets.AZURE_TENANT_ID }}
           subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
       - if: runner.os == 'Windows'
         uses: azure/trusted-signing-action@<sha>   # v2.x — SHA-pin
         with:                                      # NO azure-* auth inputs — auth = the login session
           endpoint: https://neu.codesigning.azure.net
           trusted-signing-account-name: securityronin
           certificate-profile-name: securityronin-public
           files-folder: target/${{ matrix.target }}/release
           files-folder-filter: exe
           file-digest: SHA256
           timestamp-rfc3161: http://timestamp.acs.microsoft.com
           timestamp-digest: SHA256
   ```
5. **Verify** — cut a release; the sign step must be green. On Windows: the `.exe` → Properties →
   Digital Signatures reads **Security Ronin Ltd**. Reference impl: `timeglyph` `release.yml`, v0.7.1.

### Signing gotchas (all lived)
- **`azure/login` is MANDATORY before the signer** — the action's `DefaultAzureCredential` does NOT
  perform the GitHub-OIDC exchange; without it → `AzureCliCredential: Please run 'az login'` (a
  missing *step*, not a local mistake). *(timeglyph 0.7.1, 2026-07-20)*
- **Endpoint is region-specific** — `neu` (North Europe). Wrong endpoint = a confusing auth failure.
- **RBAC role names are `Artifact Signing …`**, NOT "Trusted Signing …" (rebrand):
  `az role definition list --query "[?contains(roleName,'Signing')].roleName"`.
- **New-resource RBAC propagation lags ~1–2 min** (a role assignment right after ARM deploy 404s).
- **PAYG required to SIGN** (profile creates on Free; a sign bills the Basic plan).
- **Sign in the `build` job** → a signing failure fails build → downstream skips → **nothing ships
  unsigned** (safe; re-tag after fix). **Sign BEFORE packaging**; **timestamp always** (cert lives ~3 days).
- **UK entity ONLY** — HK (Scarlet Monkey Ltd) is ineligible for Public Trust.

### New signing IDENTITY (rare — a *new legal entity*, not a new repo)
- Org must be **US/CA/EU/UK** (Public Trust geo-gate) — HK is out.
- Azure billing **country is fixed at an identity's first signup, irreversible** → use a **fresh
  identity that never touched Azure** to select the country (HK-tainted identities are HK-locked).
- Needs **DUNS** (D&B); validation matches the **legal name on a government ID** (not a nickname);
  the verify-email link is **WAF-sensitive** (clean residential IP + Chromium/Safari, no VPN).

---

## 6. Cross-cutting gotchas (lived — don't rediscover)

- **Tag-namespace collision (TWO controls, both required):** `release-plz.toml` `git_tag_name =
  "{{ package }}-v{{ version }}"` **and** `release.yml` `on.push.tags: ["v[0-9]*"]`. Without the
  first, release-plz's default bare `v{version}` tag collides with the binary tag and crashes
  "version ahead of registry but tag vX.Y.Z exists" (bit timeglyph 0.7.1). Without the second, a
  v-named crate's `<crate>-v…` tag wrongly fires the binary build.
- **One tag ships EVERY channel** — put wheels/npm/etc. in the SAME `release.yml`, never a parallel
  `py-v*`-style tag (silently-forgotten partial release + version drift).
- **Idempotent publishes** — crates.io skip-if-published, PyPI `skip-existing` — so a re-tag ships
  only the missing channel.
- **A green release ≠ a published crate** — verify on crates.io independently (`cargo search`/`cargo
  info`; the crates.io JSON API needs a `User-Agent` or it 403s to a silent empty).
- **crates.io/PyPI versions are IMMUTABLE** — README + metadata frozen at publish; each publishable
  crate needs its OWN README (a repo-root README does not become a member crate's README).
- **`rust-toolchain.toml` pin vs cross-build (`E0463`)** — pin `dtolnay/rust-toolchain@<sha>` to the
  SAME version on the build AND `.deb` jobs, or the cross-target lands on the wrong toolchain.
- **cargo-deb**: bin name ≠ package name → build yourself then `cargo deb --no-build`; add `authors`.
- **cargo-wix in a workspace**: `--package` mandatory; wxs `Source=` paths are relative to repo root
  (CWD), not the member dir; XML comments can't contain `--`.
- **Sign the release tag** (`git tag -s`) where the repo requires signed history. To move a
  not-yet-published tag: `git tag -d v… ; git push origin :refs/tags/v… ; git tag -s v… ; git push origin v…`.
- **GitHub Pages must be ENABLED** or the README footer Privacy/Terms links 404 (fake-200 trap) —
  verify with `curl -s -o /dev/null -w '%{http_code}' https://securityronin.github.io/<repo>/privacy/`.

---

## 7. Secret-scan job (org repos)

`gitleaks/gitleaks-action` requires a paid license on **org** repos. Run the **CLI binary** instead
(Apache-2.0, unrestricted), version **pinned** (never `releases/latest` — rate-limited, non-deterministic):
```yaml
- run: |
    VERSION=8.30.1
    curl -sSfL "https://github.com/gitleaks/gitleaks/releases/download/v${VERSION}/gitleaks_${VERSION}_linux_x64.tar.gz" | tar xz -C /tmp gitleaks
    /tmp/gitleaks detect --source . --config .gitleaks.toml
```

---

## 8. README + repo metadata (pre-push readiness)

- **README** to the fleet standard — reference impl `~/src/blazehash`: two-row badge block
  (Crates.io · Docs.rs · License Apache-2.0 · CI · Release · Sponsor `h4x0r` — **never a Stars
  badge**), bold tagline, 30-seconds-to-first-result above the fold, the mandated footer
  `[Privacy Policy](https://securityronin.github.io/<repo>/privacy/) · [Terms of Service](…/terms/) ·
  © 2026 Security Ronin Ltd`, and **no `## License` section**.
- **`docs/privacy.md` + `docs/terms.md` must exist** and Pages must be **enabled** (§6).
- **Repo About** — `gh repo edit SecurityRonin/<repo> --description "<mirror the tagline>" --add-topic
  rust,forensics,dfir,digital-forensics,incident-response,<artifact-family>,<formats>,cli`
  (≤20, most-specific-first). Leave **Homepage empty**.

---

## Org secrets — single source of truth (SecurityRonin org-level)

| Secret | Purpose |
|---|---|
| `CARGO_REGISTRY_TOKEN` | crates.io publish (release-plz + release.yml) |
| `TAP_GITHUB_TOKEN` | dispatch to `SecurityRonin/homebrew-tap` (`securityronin-bot`) |
| `WINGET_TOKEN` | PR to `microsoft/winget-pkgs` (`securityronin-bot`) |
| `CLOUDSMITH_API_KEY` | push `.deb` to Cloudsmith |
| `PYPI_API_TOKEN` | publish wheels to PyPI |
| `AZURE_TENANT_ID` · `AZURE_CLIENT_ID` · `AZURE_SUBSCRIPTION_ID` | Windows signing OIDC (§5) |

Shadowing trap: a repo-level secret **overrides** an org secret of the same name — delete repo-level copies.
