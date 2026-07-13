# A1 XAUUSD H4 Profit/Drawdown Frontier Findings

Date: 2026-07-11  
Boundary: development Strategy Tester evidence only; no broker action is authorized.

## Exact result comparison

| Variant | Horizon | Trades | WR | PF | Net USD | Net retained | Native relative equity DD |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| frozen H4 control | five-year | 156 | 56.41% | 2.9299 | 6,823.25 | 100.00% | 40.55% |
| episode identity / one position | five-year | 40 | 52.50% | 2.4048 | 1,295.90 | 18.99% | 19.06% |
| 6% aggregate stop-risk heat | five-year | 45 | 53.33% | 2.2336 | 1,106.53 | 16.22% | 20.30% |
| 6% heat plus default 0.8R/0.2R lock | five-year | 56 | 69.64% | 2.8918 | 1,270.96 | 18.63% | 16.25% |
| frozen H4 control | ten-year | 307 | 51.47% | 2.4968 | 8,159.08 | 100.00% | 39.49% |
| episode identity / one position | ten-year | 74 | 52.70% | 2.3996 | 1,743.43 | 21.37% | 14.49% |
| 6% aggregate stop-risk heat | ten-year | 117 | 48.72% | 1.7647 | 1,476.02 | 18.09% | 20.50% |
| 6% heat plus default 0.8R/0.2R lock | ten-year | 166 | 72.29% | 2.4223 | 2,007.45 | 24.60% | 17.43% |

None satisfies the locked combination of at least 60% net-profit retention and no
more than 10% native relative equity drawdown on USD 1,000.

## What the experiments establish

1. Duplicate correlated H4 exposure is real, but removing it alone removes too much
   profitable exposure.
2. A 6% accepted-entry heat invariant is not a 6% MT5 equity-drawdown guarantee.
   Open winning equity can be surrendered before the original target or stop.
3. The pre-existing +0.8R trigger / +0.2R hard-stop lock worked mechanically with no
   modification failures and raised the ten-year win rate to 72.29%, but it could not
   restore the removed net-profit stream or meet the 10% DD gate.
4. At Capital.com's 0.01 minimum XAUUSD size, some single H4 original stops risk far
   more than the small-account budget.  The repaired ten-year ledger observed a
   minimum candidate contract risk of USD 5.92 and later individual fixed-lot risk up
   to USD 191.91.  The instrument is indivisible below that minimum in the tested
   contract.

## Router holding-path diagnostic

The exact, outcome-sealed 2022-07 through 2026-06 path evidence contains 145 H4
positions.  A diagnostic join, not a trading-rule qualification, found:

- 132 positions changed away from UPTREND during holding and earned +USD 6,560.93;
- 13 did not change and earned +USD 489.49;
- among changed positions, 78 were eventual winners and 54 eventual losers;
- first-change unrealized R averaged +0.1224 for eventual winners and -0.0404 for
  eventual losers.

A blanket regime-change exit would therefore truncate the dominant profitable path.
These post-outcome state counts must not be mined into a new selective exit rule.

## Decision

The requested high absolute H4 profit and sub-10% drawdown are not simultaneously
supported for a USD 1,000 account under the 0.01 minimum contract.  Preserving the
old absolute net would preserve materially more exposure than the drawdown budget can
carry.  H4 remains quarantined as a full-size small-account specialist.

The viable system direction is portfolio-level replacement of the lost return:

- retain H4 only at contract-feasible, hard-capped risk;
- obtain independent return from the H1 long and short specialists in their regimes;
- enforce one portfolio heat budget and one portfolio equity-DD guardian;
- evaluate profit and DD on the integrated portfolio, not demand that unsafe H4
  stacking remain the sole profit engine.

If the owner requires the frozen H4 absolute dollar profit by itself, the honest
alternative is materially more funded capital or an instrument/broker contract below
0.01 lots.  It is not achievable by relabeling skipped small-account trades as a
drawdown-controlled strategy.
