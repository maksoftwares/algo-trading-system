# A1 XAUUSD H4 Profit-Preserving Hedge Findings

Date: 2026-07-11  
Boundary: development Strategy Tester only; no broker action is authorized.

## Locked objective

- USD 1,000 initial balance;
- original fixed 0.01 H4 primary entries and 2R targets retained;
- ten-year net profit at least USD 8,000;
- native MT5 maximum relative equity drawdown no more than 10%;
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

The clean final high-water runs had 98% history quality, all 307/156 original primary
entries, zero primary order failures, zero hedge-management failures, fully reconciled
hedge volume, and zero open residual positions.  The result is an economic failure,
not a logging or execution failure.

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
3. High-water hedging materially reduced ten-year DD from 39.49% to 22.93%, but its
   full 0.01 hedge legs surrendered too much recovery profit and still missed 10%.
4. With a 0.01 primary position and a 0.01 minimum hedge, the smallest hedge is 100%
   of one primary ticket.  The account cannot express the partial hedge ratios needed
   to smooth equity without repeatedly neutralizing the return stream.

## Verdict

No tested causal strategy simultaneously retains USD 8,000 ten-year net and holds
native relative equity drawdown to 10% on the USD 1,000 / 0.01-minimum contract.
The strongest profit-preserving hedge made USD 8,536.42 but retained 40.04% DD; the
strongest ten-year DD reduction reached 22.93% but net fell to USD 7,561.56.

The target is therefore not demonstrated under the current capital and contract-size
constraints.  Further threshold fitting against these same paths is prohibited.  A
credible next experiment requires at least one genuinely new degree of freedom:

- a smaller-than-0.01 XAUUSD contract so partial risk and hedge ratios are executable;
- materially more funded capital while keeping 0.01 lots; or
- a new contemporaneous bearish alpha source whose signals actually overlap H4
  drawdowns, developed and validated independently rather than mined from H4 losses.
