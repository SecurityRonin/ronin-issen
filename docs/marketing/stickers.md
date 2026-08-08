# Issen conference stickers — campaign plan

Status: **planned, not printed.** Deferred from Black Hat / DEF CON 2026 (insufficient
lead time — see §Timeline) to the next con with real lead time. This doc is the
ready-to-execute spec.

Provenance: strategy drafted by Fable 5 (xhigh), overstatement caught by Albert,
adversarially critiqued and reshaped by Codex (GPT-5.6). Copy is locked to be
**defensible under cross-examination** — Albert is a court-approved DFIR expert
witness, and any claim on a sticker is quotable back at him.

## Audience & goal

Overworked incident responders and digital-forensics investigators at Black Hat /
DEF CON / BSidesLV. Cynical about vendor swag, allergic to hype, time-poor. Goal:
**conversion** — sticker taken → QR scanned → `issen` tried — plus passive peer
advertising once it's on a laptop lid. Person-to-person after a short demo converts
far better than bulk table placement.

## Locked copy (no completeness claim anywhere)

- **Hero:** `One command. Correlated leads.`
- **Sub-line:** `Correlate selected disk & memory artifacts · Findings with ATT&CK context`
- **CTA:** `Try it on a test image.`  *(never "your live case" — don't invite unvalidated use on live evidence)*
- **Brand tagline option:** `Cut through forensic noise.`  *(ties to 一閃, "one cut")*
- **Micro-copy:** `No Python runtime required`  *(verify against the release build before printing)*

**Banned (overstatement — do not print):** "the whole story", "one timeline out"
(implies one authoritative chronology), "ATT&CK-mapped" as a verdict, "parse every
artifact", "no dependency hell", "one static binary" (unless release-verified).

## QR mechanics

- Encode the **canonical URL directly**: `https://github.com/SecurityRonin/issen`.
  **No redirect / vanity domain / tracking shortener** — this audience distrusts QR
  codes that hide their destination (FBI/FTC QR warnings); a bare GitHub URL previews
  to match the print = trust. Measure via GitHub traffic/stars/release-downloads.
- QR in a **visually separate panel labelled "Source + install"**, four-module quiet
  zone preserved, ≥0.8" — NOT buried in fake terminal chrome (hurts scan rate).
- **Always print the URL in text** beneath the QR (a chunk of this audience types, not scans).
- **Test-scan the actual printed proof** under poor lighting on two phones before the full run.

## Design set (for the lead-time run)

1. **Terminal** (conversion workhorse) — ~3.5×2" rounded rect, matte, dark terminal window
   showing a **real, tested** `issen` invocation (copy from `issen --help`, not invented
   syntax) + hero/sub copy + the "Source + install" QR panel.
2. **Rōnin** (cred/art) — ~2×3" contour die-cut, matte, low-poly rōnin figure, `ISSEN` + 一閃,
   **no QR** (art piece for laptop lids), URL in micro-text. Easter egg along the blade:
   the **EWF1/E01 magic** `45 56 46 09 0D 0A FF 00` (verified: `EVF\x09\x0D\x0A\xFF\x00`;
   label it EWF1/E01 — EWF2/Ex01 starts `EVF2`).
3. **Holo Rōnin** (rare) — design 2 on holographic vinyl, small run, **earned not given**
   (after a demo / solving the challenge), leveraging DEF CON collector culture.

## Print spec

- White vinyl, matte laminate, UV/outdoor-rated (survives laptops + airport handling);
  holo = holographic gloss. Contour die-cut cut-line as a named spot-color path, 1/8"
  bleed, text ≥1/16" inside the cut line (4pt micro-text easter egg is the one exception).
  Vector PDF, CMYK, raster ≥300 dpi.
- Quantity: driven by a real quote + distribution estimate, not a round number. MVP
  ≈ 500–1,000 Terminal; add art/holo only if art is print-ready and adds no schedule risk.

## Distribution & permissions

- **Person-to-person after a 30-second demo** on Albert's laptop is the primary, highest-
  conversion channel (his standing as a court-approved expert + DC852 president converts).
- **Get permission before bulk placement.** DEF CON prohibits sticking to venue property;
  community sticker tables need the organizer's OK. Black Hat is sponsor-controlled — an
  attendee badge is not vendor rights. Ask the village/table organizer first.
- **Demo hygiene:** synthetic corpus only, no client data, notifications off, and an
  **offline screenshot/recording fallback** (con Wi-Fi is unreliable).

## Timeline / why deferred

Rush-print realism (checked): Sticker Mule = 3-day rush (US, <$500, 24h proof approval);
StickerGiant = 1-day production but rush does **not** speed shipping. Ordering ~a week out
left Black Hat high-risk and DEF CON tight, with hotel receiving as an extra failure point.
Decision: **hold for a con with lead time**; ship to home/office before travel, not a hotel.

## Pre-work gate (must be done before printing — the real single point of failure)

A polished sticker pointing at an unready repo damages credibility more than no sticker.
Before any print order:
1. README carries a **scope / non-completeness** statement (see the repo README "Scope &
   limitations" section) — selective triage; absence of a finding ≠ absence of the artifact;
   ATT&CK mappings are context, not proof of conduct.
2. The **printed command actually runs**, verified against `issen --help` on the released build.
3. A **synthetic demo corpus** (CFReDS-style, documented provenance/checksums — per the
   fleet test-data-provenance standard), for the demo and any future "case" challenge.
   Never a scrubbed real case (PII / malware-distribution / licensing risk).
4. **Checksummed release** so the one-command quickstart works from the QR.
