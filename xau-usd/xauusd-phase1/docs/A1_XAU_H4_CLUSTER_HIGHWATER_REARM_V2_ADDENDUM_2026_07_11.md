# A1 XAUUSD H4 Cluster High-Water Rearm V2 Addendum

Date: 2026-07-11
Boundary: one causal state-machine repair in development Strategy Tester only; no
broker action is authorized.

## Defect found before this run

The prior 5.00% trigger / 2.00% release high-water result made USD 7,561.56 with
22.93% ten-year native relative equity drawdown.  Exact path forensics showed that
its maximum-drawdown window was completely unhedged:

- equity peak: USD 7,559.23 on 2025-12-26 20:05;
- equity trough: USD 5,825.86 on 2025-12-31 10:00;
- decline: USD 1,733.37, or 22.93051%;
- active cluster hedge throughout that peak-to-trough window: none.

After a successful hedge release, V1 set rearm false until primary floating profit
returned to the prior cluster peak.  Primary take-profits subsequently converted
floating profit to balance and reduced the still-open cohort's floating P/L.  The
old peak therefore no longer represented the current cohort, and a new adverse move
could not rearm the hedge.

## Locked repair

Keep every prior strategy and hedge input unchanged, including:

- original H4 entries, fixed 0.01 lot, stop, 2R target, and session expiry;
- high-water trigger `5.00%` and release `2.00%`;
- equal total short hedge volume and separate hedge magic number.

Replace the non-invariant floating-only watermark with one cluster metric:

`primary cluster MTM = cumulative realized primary P/L + current primary floating P/L`

The cumulative term includes profit, commission, swap, and fee for primary-magic
deals since the current cluster began.  Hedge-magic deals are excluded.  The rule:

1. high-water primary-cluster total MTM rather than floating P/L alone;
2. trigger at the unchanged 5.00% giveback;
3. release at the unchanged 2.00% giveback;
4. after a fully successful release, rearm directly without rebasing the peak;
5. return on the release tick so a hedge cannot reopen on that tick;
6. reset cluster realized MTM and its peak only after the last primary is flat and
   any remaining hedge has closed successfully.

There is no position outcome, H4 loss label, date, month, hour, or future value in
the rule.  Realizing a TP moves value from floating P/L into cumulative realized
P/L, leaving total MTM unchanged.  The 5%/2% hysteresis prevents immediate
trigger/release chatter.  Failed or deferred closes do not reset or rearm.

## One-run acceptance rule

Run the frozen five-year and ten-year windows once.  The ten-year result is the
primary decision and passes only if:

- net profit is at least USD 7,000;
- native MT5 maximum relative equity drawdown is at most 12.00%;
- profit factor is at least 1.30;
- all 307 original ten-year primary entries are retained;
- order and management failures are zero;
- every position and hedge volume reconciles and finishes flat.

The five-year diagnostic must retain all 156 primary entries, have profit factor at
least 1.30, and pass the same execution/reconciliation checks.  Its profit and
drawdown will be disclosed.  A failure ends this mechanical high-water repair lane;
it does not authorize another parameter or state-machine sweep.
