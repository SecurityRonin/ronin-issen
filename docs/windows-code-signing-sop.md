# Windows Code Signing — Fleet SOP

**Sign a fleet repo's Windows binaries (`.exe`/`.msi`) under Security Ronin Ltd (UK)** via
Azure Trusted Signing (a.k.a. Azure Artifact Signing), so Windows / SmartScreen / winget show a
verified publisher and there's no Defender friction. This is the per‑repo runbook; the *law*
(what/whether) is in [`../CLAUDE.md`](../CLAUDE.md) §"Windows code signing".

## Fixed fleet resources — provisioned once (reference, do NOT recreate)

| Field | Value |
|---|---|
| Signing account | `securityronin` — region **North Europe** → endpoint `https://neu.codesigning.azure.net` |
| Certificate profile | `securityronin-public` (**Public Trust**) |
| Validated identity | **Security Ronin Ltd** (UK), D&B / DUNS-verified |
| Azure subscription | `e4ba55d1-95a8-40b9-8a43-51419461e591` — UK/GBP **PAYG**; tenant identity `info@securityronin.com` |
| CI signer app | `securityronin-ci-signing` — appId `1381bf9d-c6b2-4f17-becd-0fb83083b90d`; role **Artifact Signing Certificate Profile Signer** on the account |
| Org secrets | `AZURE_TENANT_ID` · `AZURE_CLIENT_ID` · `AZURE_SUBSCRIPTION_ID` (non‑sensitive IDs — OIDC, **no client secret**) |

## Onboard a new repo (the repeatable procedure)

Do this signed in as `info@securityronin.com` (`az login`) and `h4x0r` (`gh`). For `SecurityRonin/<repo>`:

1. **Create the `release` GitHub environment** (the OIDC subject anchor):
   ```bash
   gh api -X PUT repos/SecurityRonin/<repo>/environments/release
   ```
2. **Add a federated credential** to the signer app for this repo's environment (one per repo — a
   classic FIC can't wildcard tag refs, which is why the workflow gates on `environment: release`):
   ```bash
   az ad app federated-credential create --id 1381bf9d-c6b2-4f17-becd-0fb83083b90d --parameters '{
     "name":"<repo>-release-env",
     "issuer":"https://token.actions.githubusercontent.com",
     "subject":"repo:SecurityRonin/<repo>:environment:release",
     "audiences":["api://AzureADTokenExchange"]
   }'
   ```
3. **Confirm the org secrets reach the repo** — `gh secret list -R SecurityRonin/<repo>` shows the
   `AZURE_*` trio (org‑level, inherited by all repos); delete any repo‑level shadow copy.
4. **Wire `release.yml`** — on the **Windows** build job, after `cargo build` produces the `.exe`,
   **before** zip/MSI/attestation (sign the shipped bytes, then package):
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
5. **Verify** — cut a release; the sign step must be green. On a Windows box, the shipped `.exe` →
   Properties → Digital Signatures reads **Security Ronin Ltd**; winget/SmartScreen show the
   verified publisher. (Reference implementation: `timeglyph` `release.yml`, v0.7.1.)

## Gotchas (all lived — don't rediscover)

- **`azure/login` is MANDATORY before the signer** — the action's `DefaultAzureCredential` does NOT
  perform the GitHub‑OIDC exchange; without it, `AzureCliCredential: Please run 'az login'` (a
  misleading error — a missing *step*, not a local mistake). *(timeglyph 0.7.1, 2026‑07‑20)*
- **Endpoint is region‑specific** — `neu` (North Europe). A wrong endpoint = a confusing auth failure.
- **RBAC role names are `Artifact Signing …`**, NOT "Trusted Signing …" (the rebrand desyncs docs
  from the definition strings): `az role definition list --query "[?contains(roleName,'Signing')].roleName"`.
- **New‑resource RBAC propagation lags ~1–2 min** — a role assignment right after an ARM deploy 404s.
- **PAYG required to SIGN** — the account/profile create on a Free subscription, but a sign bills the Basic plan.
- **The sign step lives in the `build` job** → a signing failure fails the build, downstream
  `needs: build` jobs skip, and **nothing ships unsigned** (safe; re‑tag after a fix — crate publish is idempotent).
- **Sign BEFORE packaging** so the signature is inside the shipped `.exe`; **timestamp always** (the cert lives ~3 days).
- **Sign under the UK entity ONLY** — HK (Scarlet Monkey Ltd) is ineligible for Public Trust.

## New signing IDENTITY (rare — only if a *new legal entity* must sign)

Not needed for a new repo under Security Ronin Ltd. If a genuinely new entity ever signs:
- The org must be **US/CA/EU/UK** (Public Trust geo‑gate) — **HK is out**.
- Azure billing **country is fixed at an identity's first signup and is irreversible** — use a
  **fresh identity that never touched Azure** to select the right country (an identity that ever had
  HK Azure is HK‑locked forever).
- Needs a **DUNS** (D&B) for org validation; validation matches the **legal name on a government ID**
  (use the legal name, not a nickname); the "verify your email" link is **WAF‑sensitive** (open on a
  clean residential IP in Chromium/Safari, not a VPN).
