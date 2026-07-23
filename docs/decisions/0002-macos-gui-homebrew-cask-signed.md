# 2. macOS GUI apps ship as a signed + notarized Homebrew Cask; pure CLIs as a Formula

Date: 2026-07-22
Status: Accepted (fleet distribution law)
Governs: every fleet repo that ships a GUI — timeglyph (`timeglyph-lens` overlay) is
the first; any future `*-gui` / overlay / desktop binary — plus the shared Homebrew
tap (`SecurityRonin/homebrew-tap`).

## Context

The fleet ships CLIs through a Homebrew **Formula** (`bin.install` → a binary on
`$PATH`). timeglyph is the first fleet repo with a **GUI** (the `timeglyph-lens`
cursor overlay), and a Formula is the wrong vehicle for it: `bin.install` drops a
bare binary with **no `/Applications` entry and no Launchpad / Spotlight / Dock
icon**, so the GUI is "nowhere to be found." This is the macOS twin of the Windows
**winget portable-zip trap** — a zip that installed only the CLI and gave the GUI no
launcher — which we fixed with an MSI + Start Menu shortcut (timeglyph `wix/main.wxs`).

macOS adds a hard constraint the Windows side does not. **Homebrew Cask quarantines
installed apps by default**, so an unsigned / un-notarized `.app` is Gatekeeper-
blocked (*"app is damaged and can't be opened"*). The escape hatches are **gone**:
`--no-quarantine` / `quarantine false` are deprecated and being removed
(`Cask::Quarantine` is private API), and **Homebrew ends support for every cask that
fails Gatekeeper on 2026-09-01**. (Verified Jul 2026 — an earlier working assumption
that "`brew` strips quarantine, so notarization is optional" was **wrong** and is
retracted.)

## Decision

Homebrew distribution has **two modes, chosen by whether the app has a GUI**:

- **Pure CLI → Formula** (`brew install <name>`): `bin.install`. Most fleet tools.
- **GUI → Cask** (`brew install --cask <name>`): the cask's `app "<Gui>.app"` stanza
  installs a `.app` bundle into `/Applications` (Launchpad/Spotlight/Dock icon); a
  `binary` stanza also exposes the GUI's CLI on `$PATH`. **Mandatory whenever the
  repo ships a GUI** — a Formula only gives a bare, icon-less binary.

A **CLI + GUI** repo ships **both**: the Formula carries the pure CLI; the Cask
carries the GUI `.app` + its CLI (`binary` stanza) and `depends_on formula:` so one
`--cask` install brings the CLI too. Distinct package names disambiguate and prevent
the "where's my app?" confusion (`timeglyph` = the CLI, `timeglyph-lens` = the GUI —
the Docker / 1Password model), and the Formula's `caveats` points CLI-installers at
the cask.

A cask `.app` **MUST be Developer-ID-signed + notarized** — an **Apple Developer
account is a hard prerequisite for shipping any fleet GUI**. The macOS legs of
`release.yml` build the `.app` (see the release skill), then
`codesign --deep --force --options runtime --sign "Developer ID Application: …"`,
`xcrun notarytool submit <zip> --wait`, and `xcrun stapler staple` — the macOS mirror
of the Windows Azure Trusted Signing step. The fleet builds **no DMGs**; a cask ships
the stapled `.app` inside a `ditto` zip.

## Consequences

macOS users get a real clickable app (Launchpad/Spotlight/Dock), consistent with the
Windows MSI + Start-Menu-shortcut model — the fleet's GUI-launcher story is now
symmetric across desktop platforms. A stable `CFBundleIdentifier` in the bundle also
gives the macOS **Accessibility-permission** grant (the overlay's element picker) a
stable identity across upgrades, which a bare relocated binary lacks.

The cost is a real prerequisite: shipping a fleet GUI now needs an **Apple Developer
account ($99/yr)** + a Developer ID Application cert + notarization wired into CI.
Without it the cask ships a **Gatekeeper-blocked** app *and* loses Homebrew support
after 2026-09-01 — so signing is not optional, it gates the cask. The **Formula CLI
is unaffected**: it runs unsigned (Rust ad-hoc-signs the arm64 binary, and formula
artifacts are not quarantined like cask downloads), though signing it too is good
hygiene.

Alternatives rejected: **`bin.install` of the GUI binary** (the status quo — a bare
binary with no icon); the **`quarantine false` / `--no-quarantine` bypass**
(deprecated and being removed by Homebrew — a dead end); a **single all-in-one cask**
that also carries the CLI with no Formula (rejected for a CLI-*primary* tool like
timeglyph — it would force the `.app` onto headless / pipeline users who want only
the CLI); and a **DMG** (a cask ships the `.app` in a `ditto` zip; the fleet builds
no DMGs).

## References

- Release skill → "macOS GUI: ship a Homebrew Cask, not a bare binary" (the `.app`
  bundling + signing + cask-generation recipe) and gotcha #7 (the Windows GUI-MSI
  twin).
- ronin-issen `CLAUDE.md` → the release standard's two-mode Homebrew rule.
- timeglyph: `scripts/bundle-lens-app.sh`, `wix/main.wxs` (Windows twin), PR #3;
  `SecurityRonin/homebrew-tap` PR #1 (the `timeglyph-lens` cask generation — the
  fleet's first cask).
- Homebrew Gatekeeper policy: [brew#20755 (removing `--no-quarantine`)](https://github.com/Homebrew/brew/issues/20755),
  [Homebrew Discussion #6482](https://github.com/orgs/Homebrew/discussions/6482),
  [HN: Homebrew no longer allows bypassing Gatekeeper](https://news.ycombinator.com/item?id=45907259)
  — casks that fail Gatekeeper lose support 2026-09-01.
