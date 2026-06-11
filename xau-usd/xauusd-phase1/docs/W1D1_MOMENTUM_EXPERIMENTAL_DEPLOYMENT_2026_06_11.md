# W1/D1 Momentum Continuation — Experimental Demo Deployment Note

Date: 2026-06-11
Artifact: `mt5/Experts/W1D1MomentumContinuationExperimental.mq5` (magic 932000)
Status: SOURCE_DELIVERED_NOT_ATTACHED — attaching, compiling, and enabling are owner actions.

## What this is, stated plainly

A real trading EA (places demo orders when armed) implementing, byte-faithfully, the locked
mechanical rules of `w1_d1_momentum_continuation_v0` — the 2026-06-10 locked full-window
campaign's **closest miss**: Dukascopy decade PF 1.276 over 193 trades, Pepperstone 1.275,
Capital.com 1.075; `FAIL_REJECTED_VERSION_FINAL` against the 1.30 canonical bar. It is an
**experimental forward test in the existing experimental demo lane** (same governance as the
WR50 variants), NOT an approved EA, NOT canonical Phase 2, and the canonical
`breakout_retest` suspension is unaffected. Its purpose is to generate fresh out-of-sample
demo evidence at live measured costs for an independent (non-breakout-retest) family.

## Rules (locked v0; constants marked DO NOT TUNE in source)

Signal on each completed D1 bar: range >= 0.75x ATR(14), body >= 35% of range,
20-day momentum >= 1.25x ATR and 5-day momentum >= 0.25x ATR (mirrored for shorts),
directional close in the outer 35% of the bar. Market entry on the next bar; stop beyond the
signal-bar extreme by 0.20x ATR (decade median ≈ 1500+ points → cost_R ≈ 0.03 at measured
spreads); fixed 1.5R target; one position at a time; max one setup per ISO week
(~25-50 trades/year — judge it on net-R after >= 100 trades, not weeks).

## Safety and setup

Demo-only guard; optional login allowlist; kill-switch file `W1D1_MOMENTUM_KILL.txt`;
spread cap 75 points; fixed 0.01 lots; ships with `InpAllowDemoTrading=false` (observer —
logs signals, sends nothing) — the owner arms it by setting it true in a local, git-ignored
preset, per standing preset policy. Attach to one XAUUSD chart (any timeframe; it acts on
D1 bar closes). It never touches other magics' positions.

## Pre-committed judgment (so this is evidence, not hope)

Track in the weekly comparison report alongside the existing lanes. Promotion conversation
only at >= 100 closed trades AND net_expectancy_R_after_measured_cost >= +0.15R; kill the
forward test early if realized net-R <= -0.10R after 40 trades. Win rate is diagnostic only.
