# XAUUSD M30 Bounded Verification V1

- Branch: `codex/xau-chop-m30-bounded-verification-v1`
- Base commit: `2cddc16f380f531c3cf4b5922f5bd9fca8e29fff`
- Frozen candidate: `CHOP_RANGE_ROTATION_CONTINUATION_V1 / M30`
- Outcome: `FOLLOWUP_DATA_INCOMPLETE_NO_ADVANCEMENT`
- Engineering/deployment authorization: `NOT_AUTHORIZED`

## Corrected result

- Trades/setups/episodes: `141` / `129` / `118`.
- PF / expectancy / net R: `1.261` / `0.126` / `17.813`.
- Stress PF / stress net R: `1.142` / `10.258`.
- Later PF / later net R: `1.044067` / `1.015`.
- Unchanged strategy gate passed: `False`.

## Data boundary

- Requested end: `2026-06-30T23:59:59+00:00`.
- Common actual end: `2025-07-01T00:00:00+00:00`.
- No trustworthy Capital.com extension through 2026-06-30 was present locally; the mandated incomplete-data outcome therefore overrides advancement.

## Execution corrections

- Regime exits and cooldowns use the next executable bar open timestamp.
- Maximum holds use elapsed UTC time and report unavoidable market-closure overruns.
- Long/short gap-through-stop exits fill at the worse executable Bid/Ask open.
- M30 stop/target ordering and MFE/MAE use causal ordered M5 sub-bars.
- Half-life and variance ratios do not cross chop episodes or timestamp gaps.
- Boundary-return and remaining-regime-duration fields are explicitly ex-post diagnostics and are not trading or gate inputs.

## Final action

Close chop-v1 without another rescue variant unless the owner supplies the missing frozen-period broker history under a separately authorized task.
