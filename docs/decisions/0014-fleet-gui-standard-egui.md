# 0014 — Fleet GUI standard: egui (single static binary, crates.io-publishable)

**Status:** Accepted

## Context

A fleet GUI must obey the same shippability rule as a fleet CLI: it has to be a
**pure-Rust, single static binary** that `cargo install`s into a working app and
**publishes to crates.io** exactly like the `<x>4n6` tools. A GUI framework that
ships a JS/HTML bundle plus a bundler step (Tauri / `dioxus-desktop` / any
`wry`/webview stack) cannot be delivered by crates.io as a working artifact — it is
release-installer-distributed, not `cargo install`-able — so it breaks the fleet's
"one `cargo install` to a working tool" contract.

The UIs in question are data-dense analyst surfaces: super-timelines, event tables,
MFT/registry trees, hex views. That favours an immediate-mode toolkit that stays
pure Rust and compiles to one binary (and, as a bonus, to WASM for a browser build)
over a retained-mode/webview stack.

## Decision

1. **`egui` (`eframe`) is the default fleet GUI framework.** Immediate-mode, pure
   Rust, single static binary, no runtime deps, cross-platform, and the *same* code
   compiles to WASM for a browser build. A `-gui` crate then publishes to crates.io
   exactly like a `-cli`. `iced`/`slint` are acceptable for a more polished
   retained-mode app, but egui is the default. The progression TUI→GUI is
   `ratatui`→`egui`, which keeps the single-binary / `cargo install` / crates.io
   properties at every rung.
2. **Tauri / `dioxus-desktop` / any `wry`/webview bundle are banned for fleet GUIs.**
   They ship a JS/HTML bundle + a bundler step, so crates.io cannot deliver a working
   artifact. If one is *genuinely* required (rich web tech), it carries a documented
   reason **and** `publish = false`, so it never reads as a missing publish (e.g.
   `srum-gui`).
3. **Icons: `egui-phosphor`** — the ~6000-glyph Phosphor set (egui's built-ins are
   far too few). Pin it to the egui-matching version (e.g. egui 0.29 ↔ egui-phosphor
   0.7). Wire once at startup
   (`egui_phosphor::add_to_fonts(&mut fonts, egui_phosphor::Variant::Regular)`),
   then use glyph constants inline (`use egui_phosphor::regular;` →
   `ui.button(format!("{} Refresh", regular::ARROW_CLOCKWISE))`).

**Reference implementation:** `~/src/nameback` (`nameback-gui`).

## Consequences

- A fleet GUI ships and installs identically to a CLI: `cargo install <x>-gui`
  yields a working windowed app; the `-gui` crate publishes to crates.io.
- macOS distribution of a GUI still follows [ADR-0002](0002-macos-gui-homebrew-cask-signed.md)
  (Homebrew Cask, Developer-ID-signed + notarized) — this ADR governs the
  *framework/shippability*, that one governs *distribution*.
- A webview GUI is a deliberate, annotated exception (`publish = false` + a written
  reason), never a silent one.
- The egui-phosphor version pin is coupled to the egui version; an egui bump requires
  the matching egui-phosphor bump.
