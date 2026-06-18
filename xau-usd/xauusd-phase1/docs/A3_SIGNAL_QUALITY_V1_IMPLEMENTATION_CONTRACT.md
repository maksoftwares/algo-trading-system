# A3 Signal Quality V1 Implementation Contract

Status: `LOCKED_PENDING_SHADOW_BUILD`

Scope:

- Account: `1033669`
- Symbol: `XAUUSD`
- Family: breakout-retest
- Runtime mode: shadow only
- Broker action: prohibited
- Existing A3 entry lanes: remain paused
- Profit-lock manager: remains dry-run/disarmed

This contract defines what a future A3 signal-quality V1 observer may implement. It does not authorize broker execution, chart attach, preset arming, MT5 profile edits, lot changes, SL/TP changes, or account changes.

## Locked Inputs

- Hypothesis file: `docs/A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_18.md`
- Hypothesis manifest: `outputs/manifests/A3_SIGNAL_QUALITY_HYPOTHESES_V1.sha256.json`
- Threshold provenance: `docs/A3_SIGNAL_QUALITY_V1_THRESHOLD_PROVENANCE.md`
- Implementation contract manifest: `outputs/manifests/A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_CONTRACT.sha256.json`

## Observer Requirements

The future observer must log would-signal rows only. It must not call `OrderSend`, `CTrade`, `TRADE_ACTION_DEAL`, `TRADE_ACTION_SLTP`, `PositionModify`, `PositionClose`, or `OrderDelete`.

The observer must record, at minimum:

- source commit hash;
- compiled binary hash, if a binary is produced for a local shadow attach;
- locked hypothesis hash;
- implementation contract hash;
- forward-window start timestamp;
- minimum forward-window end timestamp;
- account login and server marker;
- symbol and timeframe;
- all V1 threshold decisions;
- raw signal reason, guard reason, and pass/fail result;
- regime tags needed to verify coverage.

## Forward Protocol

The forward shadow window may start only after the observer source commit, binary hash, hypothesis hash, and contract hash are recorded in one startup row and one report artifact.

The minimum forward window is one full trading week after first verified startup row. Results before the recorded start timestamp are implementation validation only and must not be used as forward evidence.

Regime coverage must include at least:

- one London/early-New-York overlap sample or an explicit `NO_SAMPLE` record;
- one afternoon server-hour sample or an explicit `NO_SAMPLE` record;
- both long and short candidates or an explicit `ONE_SIDE_ONLY` record;
- spread/cost distribution summary for every observed signal.

## Data Embargo

No threshold may be changed under V1 after forward observation starts. If forward results reveal a defect, V1 must be retired and a new V2 hypothesis plus manifest must be created before any new threshold is evaluated.

## Reactivation Boundary

A passing shadow result is necessary but not sufficient for A3 reactivation. Any future broker-action work requires a separate reviewer-approved implementation plan, owner authorization packet, dry-run proof, mutex/containment proof, and preflight gate.
