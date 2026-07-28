# Can ML close a V60 position early, before it reaches the stop?

Decision: **CLAUDE_V60_EARLY_EXIT_ML_REJECTED_NO_NEGATIVE_FORWARD_POPULATION**

Historical research only. `ml_runtime_authorized: false`. No runtime, EA, demo,
live or broker change is authorized.

## Answer

**No — and the reason is structural, not a modelling failure.** Cutting a losing
V60 position destroys money, because positions that are down have significantly
*positive* forward expectancy.

Early exit does reduce drawdown, consistently and substantially. It is a genuine
risk dial. It is not a free one: it costs roughly as much profit as it saves
drawdown.

## Measurement 1: losing positions recover

For every position still open and **down** at a checkpoint, the P&L it earns from
that point to its actual exit:

| checkpoint | n down | win rate | mean forward $ | t |
|---|---|---|---|---|
| 0.5h | 843 | 34.6% | **+$3.57** | **4.79** |
| 1h | 453 | 31.8% | **+$2.88** | **3.14** |
| 2h | 301 | 32.2% | **+$4.21** | **3.57** |
| 4h | 167 | 35.9% | +$5.81 | 2.04 |
| 8h | 83 | 26.5% | +$1.39 | 0.45 |

Restricting to deeper losers (worse than −0.5 ATR) does not change the sign:
+$4.56 at 0.5h (t 4.79), +$2.21 at 1h (t 2.91), +$4.00 at 2h (t 2.83).

Their win rate is low — about a third — so most of these positions really do end
as losers. But the recoveries are large enough that the *expected* forward P&L is
positive at high significance. This is mechanically consistent with V60's sleeves
being reversal and confirmation strategies: a position that has moved against you
is nearer its edge, not further from it.

Note the conditioning is exactly right for the decision being made. Positions
that already hit their stop are closed and excluded, so this is the population an
early-exit rule would actually face at decision time.

## Measurement 2: a model cannot find the non-recoverers either

5,350 mid-flight decision points on 1,774 trades, 18 features (unrealised P&L,
MAE, MFE, excursion recovery, time in trade, live ATR/volatility/momentum,
microstructure flow and efficiency, sleeve, direction). Target is forward P&L
from the checkpoint. Causal walk-forward by year, 48h purge, identical protocol
to the sizing lane.

The model has real but weak ranking power — `corr(pred, actual) = 0.105`:

| predicted decile | predicted $ | **actual $** | % negative |
|---|---|---|---|
| 0 (worst) | −3.15 | **+5.97** | 45.0 |
| 1 | −1.10 | +1.30 | 53.0 |
| 4 | +0.78 | +1.09 | 51.8 |
| 8 | +3.43 | +8.57 | 46.1 |
| 9 (best) | +7.05 | +12.45 | 40.9 |

**Every decile has positive actual forward P&L.** The positions the model is most
confident will lose $3.15 go on to make $5.97. The share of negative outcomes
sits near 50% in every decile — essentially no discrimination on sign.

This is the same structure found at entry, where the worst score quintiles are
near-zero winners rather than losers. **V60 has no negative-expectancy
population to remove — not at entry, and not in flight.**

## Measurement 3: what cutting actually costs

Baseline over the 1,425 trades with reconstructable paths: net $6,011,
maxDD $246, net/DD 24.39, WR 50.4%, PF 2.08.

| threshold | cuts | net | maxDD | net/DD | vs base |
|---|---|---|---|---|---|
| < $0 | 666 | $3,614 | **$131** | 27.60 | **−$2,397** |
| < −$1 | 394 | $4,061 | $176 | 23.10 | −$1,951 |
| < −$2 | 211 | $4,288 | $202 | 21.26 | −$1,723 |
| < −$4 | 54 | $4,633 | $246 | 18.80 | −$1,378 |
| < −$8 | 4 | $6,040 | $246 | 24.51 | +$29 |

Every threshold that cuts a meaningful number of positions loses money. The most
aggressive setting cuts 47% of the book and forfeits 40% of all profit.

Pricing is exact and not the issue: implied position size is 1.0 unit on all
2,194 ledger trades, so closing at the checkpoint mid realises
`(mid − entry) × sign`, and round-trip cost (~$1.17) is unchanged by exiting
early — still one open and one close.

## The one argument for cutting, and why it fails

Drawdown falls consistently — in every single year, not just in aggregate — so
the natural rescue is to cut and then lever back up to the original risk:

| threshold | maxDD | lever to match base DD | levered net | vs base |
|---|---|---|---|---|
| < $0 | $131 | 1.88x | $6,804 | **+$793** |
| < −$1 | $176 | 1.40x | $5,694 | −$318 |
| < −$2 | $202 | 1.22x | $5,239 | −$772 |

Only the most aggressive threshold survives, at +13%, and it fails on inspection:

- **It loses in 5 of 6 years before levering** (2021 −$146, 2023 −$607,
  2024 −$127, 2025 −$738, 2026 −$843; only 2022 gains, at +$64).
- The entire case rests on **maxDD, a single order statistic** — the noisiest
  number in the report — and the threshold was chosen after seeing it.
- It assumes 1.88x leverage is actually available, which on a 0.01-lot floor it
  may not be.

Trading a large, consistent, significant profit loss for a rescue that depends on
one noisy extreme value is a bad exchange.

## What this is good for

If drawdown reduction is wanted for its own sake, early exit is a real dial with
a roughly 1:1 price: **cutting at predicted forward < $0 buys 47% less drawdown
for 40% less profit**, and the drawdown reduction holds in every year tested.

But the sizing overlay in `RESULT.md` dominates it — that adds net *and* improves
net/DD. If the objective is "better output, fewer bad trades", sizing is strictly
the better instrument. Early exit is only interesting to someone who wants less
risk and is willing to pay proportionally for it.

## Reproduce

```
PYTHONPATH=src ../balanced-horizon-ml-v5/.venv/Scripts/python.exe src/e1_recovery_diagnostic.py
PYTHONPATH=src ../balanced-horizon-ml-v5/.venv/Scripts/python.exe src/e2_early_exit_ml.py
```
