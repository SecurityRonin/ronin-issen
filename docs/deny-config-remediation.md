# Remediation — fleet-ci silently replaced 61 repos' `deny.toml`

**Status:** cause fixed in `fleet-ci#8` (open). Repin outstanding. **No masked
findings** — all 65 affected repos pass their own config today.

## Executive summary

`fleet-ci`'s `deny-config-repo` input defaulted to `SecurityRonin/fleet-config`.
Adopting the shared workflow therefore swapped each repo's own `deny.toml` for
the shared one, changing what `cargo deny` accepts. No adoption PR disclosed it,
because nobody involved knew.

The shared config is **looser** than what it replaced:

| | shared `fleet-config` | typical repo-local |
|---|---|---|
| advisory ignores | **21**, all bare ids, no reason, no removal condition | `0` |
| `bans.multiple-versions` | `warn` | `deny` in many repos |
| allowed licences | 16 | 7 |

Among the 21: `RUSTSEC-2023-0071` (rsa, Marvin timing attack) and
`RUSTSEC-2026-0222` (wasmtime). Bare ids also violate the fleet's own suppression
rule, which requires a truthful reason and a removal condition.

**Blast radius: 61 of 65 adopted repos** had a stricter local config and had their
advisory gate relaxed.

**Nothing was actually masked.** Every one of the 65 was re-checked against its
own `deny.toml`: **65 pass, 0 fail**. So the gate was weakened, but no finding
hid behind it. This is remediation of a control, not an incident response.

## What to do

### 1. Merge `fleet-ci#8` — flips the default *(blocks everything below)*

Makes `deny-config-repo` empty by default, so a repo uses its own `deny.toml`
unless it explicitly opts in. Also closes the mirror-image hole: with no shared
config *and* no local one, the job previously fell through to cargo-deny's
built-in defaults. Both directions now refuse.

Verified across all three paths: local present → uses it; neither → refuses
(new); shared configured but absent → refuses (unchanged).

### 2. Repin the 65 adopted repos

They pin pre-fix SHAs, so they keep the shared config until repinned. Mechanical
— one line per repo:

```bash
sed -i '' "s|rust-ci\.yml@[0-9a-f]\{40\}|rust-ci.yml@<NEW_SHA>|" .github/workflows/ci.yml
```

Verify per repo after CI runs: the `cargo-deny` job log should read
`Using repo-local deny.toml`.

### 3. Confirm no regression appears

The sweep says all 65 pass locally today, so the repin should be a no-op for
results. **If any repo goes red after repinning, that is a true finding its own
policy was always meant to catch** — fix it, do not re-point it at the shared
config.

### 4. Hold the 16 in-flight adoption PRs until 1–2 land

Otherwise they ship the same silent relaxation. Two already set
`deny-config-repo: ""` by hand; after the fix that line is redundant but
harmless.

### 5. Decide what `fleet-config/deny.toml` is *for* — separate PR

Not remediation, but it is now the open question. Either:

- it is a genuine fleet policy, in which case its 21 ignores each need a truthful
  reason and a removal condition (fleet rule: *a suppression whose stated reason
  is wrong is worse than a bare one* — 21 with no reason at all is worse still);
  or
- it is a starting template for repos with nothing, in which case say so and stop
  treating it as a default.

Opting in should stay explicit either way.

## How this happened

The rollout adopted 65 repos without comparing the shared config against the
configs it replaced. The input existed, the default looked reasonable, and no
adoption PR asked what it changed.

Found by three independent adoption agents that each read `fleet-config` against
the repos it was replacing and flagged it. Two set `deny-config-repo: ""`
themselves; one followed the given input list and escalated for a deliberate
call. They were briefed to report where the spec was wrong rather than follow it,
and that is exactly what surfaced this.

**The generalisable lesson — a shared default is a policy decision.** Migrating N
repos onto shared infrastructure silently adopts every default that
infrastructure carries. The defaults must be diffed against what each repo
already had, and any that differ are behaviour changes owed their own argument,
not side effects of a config move.
