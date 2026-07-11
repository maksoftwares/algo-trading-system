# A1 XAUUSD H4 Profit-Preserving Hedge Findings

Date: 2026-07-11  
Boundary: development Strategy Tester only; no broker action is authorized.

## Locked objective

- USD 1,000 initial balance;
- original fixed 0.01 H4 primary entries and 2R targets retained;
- original objective: ten-year net profit at least USD 8,000 and native MT5
  maximum relative equity drawdown no more than 10%;
- revised near-target acceptance for the final repair: ten-year net at least
  USD 7,000 and native relative equity drawdown no more than 12%;
- Capital.com hedging-account behavior, native spread/swap, and zero execution errors.

## Exact MT5 results

| Variant | Window | Primary entries | Net USD | PF | Native relative equity DD | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| frozen original H4 | five-year | 156 | 6,823.25 | 2.9299 | 40.55% | profit pass / DD fail |
| frozen original H4 | ten-year | 307 | 8,159.08 | 2.4968 | 39.49% | profit pass / DD fail |
| per-ticket equal hedge at -0.25R | five-year | 156 | 6,484.57 | 2.3056 | 36.46% | fail |
| per-ticket equal hedge at -0.25R | ten-year | 307 | 7,617.81 | 2.0195 | 42.21% | fail |
| cluster hedge at 5% loss below balance / release 2% | five-year | 156 | 7,338.39 | 3.0027 | 37.15% | profit pass / DD fail |
| cluster hedge at 5% loss below balance / release 2% | ten-year | 307 | 8,536.42 | 2.4978 | 40.04% | profit pass / DD fail |
| cluster hedge at 5% floating high-water giveback / release 2% | five-year | 156 | 4,473.03 | 1.6330 | 38.77% | fail |
| cluster hedge at 5% floating high-water giveback / release 2% | ten-year | 307 | 7,561.56 | 1.8710 | 22.93% | fail |
| same V1 high-water state, scaled to 2% / 0.8% | five-year | 156 | 2,373.91 | 1.2320 | 42.48% | fail |
| same V1 high-water state, scaled to 2% / 0.8% | ten-year | 307 | 6,466.78 | 1.5878 | 27.86% | fail |
| transaction-accumulator total-MTM implementation V2 | five-year | 156 | 845.89 | 1.0639 | 33.94% | implementation fail |
| transaction-accumulator total-MTM implementation V2 | ten-year | 307 | 3,707.19 | 1.2503 | 23.77% | implementation fail |
| settlement-synchronized total-MTM V3 at 5% / 2% | five-year | 156 | 2,277.89 | 1.1958 | 25.40% | fail |
| settlement-synchronized total-MTM V3 at 5% / 2% | ten-year | 307 | 3,722.21 | 1.2511 | 23.68% | fail |

All completed rows retained 98% history quality and all 307/156 original primary
entries.  The final V3 runs had zero order failures, zero hedge-management failures,
fully reconciled hedge volume, and no residual positions.  V3 is therefore an
economic failure rather than a logging or execution failure.

Currency note: all R5 tester configurations, native reports, and reported results
are USD.  Shared raw-parser columns still named `profit_aed` or `pnl_aed` contain
tester-currency USD values; those legacy names are retained only for schema
compatibility and do not indicate an AED conversion.

## High-water state defect and final repair

The attractive USD 7,561.56 / 22.93% V1 row is not deployable.  Its exact maximum
drawdown ran from USD 7,559.23 equity on 2025-12-26 20:05 to USD 5,825.86 on
2025-12-31 10:00.  The full USD 1,733.37 decline was unhedged.  After a prior hedge
release, three primary take-profits converted USD 638.52 from floating P/L into
balance without changing equity; the floating-only high-water and stale rearm lock
misread that realization and never rearmed.

The 2%/0.8% run retained that state defect and worsened both profit and drawdown.
It rejects threshold scaling, not the defect diagnosis.

V3 corrected the invariant and MT5 event ordering.  It high-waters cumulative
realized primary P/L plus current floating primary P/L, synchronizes from deal
history when the primary cohort changes, defers action for that settlement tick,
and rearms directly after a successful release.  It removed the false TP lockout,
but 177 ten-year hedge cycles surrendered too much recovery: net fell to
USD 3,722.21 while drawdown remained 23.68%.

## Why the existing specialists do not solve it

The exact ten-year continuation and pullback shorts add USD 1,006.14, so original H4
plus both shorts earns about USD 9,165.22.  They do not hedge H4:

- zero of 237 short trades overlapped any of the 307 H4 holding intervals;
- zero shorts overlapped any of the 149 losing H4 positions;
- the USD 866.37 December 2025 H4 stop cluster had no active short;
- over major ten-year H4 drawdown episodes, the other specialists combined worsened
  P/L by USD 100.30 rather than offsetting it.

Thus an offline net-profit sum must not be presented as drawdown protection.

## Mechanistic conclusions

1. Per-ticket hedging misses correlated portfolio loss: many H4 tickets can each be
   above -0.25R while aggregate equity giveback is already large.
2. Hedging loss below balance does not protect prior floating-equity peaks, which are
   the basis of MT5 relative drawdown.
3. Floating-only high-water V1 missed the worst episode because TP realization
   corrupted its state; its USD 7,561.56 / 22.93% result is diagnostic, not safe.
4. The correct total-MTM implementation protected more episodes, but repeated full
   hedges reduced ten-year profit to USD 3,722.21 and still left 23.68% drawdown.
5. With a 0.01 primary position and a 0.01 minimum hedge, the smallest hedge is 100%
   of one primary ticket.  The account cannot express the partial hedge ratios needed
   to smooth equity without repeatedly neutralizing the return stream.

## Verdict

No tested causal mechanical hedge simultaneously retains even USD 7,000 ten-year net
and holds native relative equity drawdown to 12% on the USD 1,000 / 0.01-minimum
contract.  Threshold scaling failed, and the final realization-invariant state
repair made only USD 3,722.21 with 23.68% drawdown.  The mechanical high-water lane
is closed; another hedge threshold or state variant is not authorized.

The target is therefore not demonstrated under the current capital and contract-size
constraints.  Further threshold fitting against these same paths is prohibited.  A
credible next experiment requires at least one genuinely new degree of freedom:

- a smaller-than-0.01 XAUUSD contract so partial risk and hedge ratios are executable;
- materially more funded capital while keeping 0.01 lots; or
- a new contemporaneous bearish alpha source whose signals actually overlap H4
  exposure, developed and validated independently rather than mined from H4 losses.

That research has started.  The preregistered first probe was
`r5_upchop_downside_impulse_retest_q55_v1`: a short-only causal UPTREND/CHOP
transition specialist with fixed 2R, one 0.01 position, one entry per broker day,
and a 1,000-point structural-stop ceiling.  Frozen opportunity evidence found 324
risk-qualified q55 signals during common-window H4 exposure, touching 128/145 H4
positions and all 13 exposure episodes.

The locked exact test rejected that probe before any portfolio rescue:

| R5 q55 result | Trades | Net USD | PF | Native relative equity DD |
| --- | ---: | ---: | ---: | ---: |
| five-year | 412 | -317.65 | 0.7578 | 34.96% |
| ten-year | 612 | -380.64 | 0.7990 | 44.09% |

It did solve signal availability and independence: it touched 33/39 full-decade H4
exposure episodes, used only causally known UPTREND/CHOP states, and had -0.0081
Pearson correlation with H4 daily closed P/L.  It did not solve alpha quality:
ten-year win rate was 28.92%, only 2/10 non-overlapping July-to-June buckets were
profitable, and the stress result was USD -564.24.  The q55 UPTREND/CHOP cell is
therefore closed with no neighboring-parameter sweep and no portfolio test.  The
next independent-specialist study must use a genuinely different trigger family,
not tune this failed cell or relabel an existing fallback.
