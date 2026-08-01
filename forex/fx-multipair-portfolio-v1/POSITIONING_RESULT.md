# US500 Positioning & Skew — Result

Date: 2026-08-01
Status: **`NO_TRADEABLE_POSITIONING_OR_SKEW_EDGE`**

## Data actually obtained

- **CFTC Traders in Financial Futures**, S&P 500 Consolidated (`13874+`):
  **841 weekly reports, 2010-06 to 2026-07** — dealer, asset-manager and
  leveraged-fund positioning. More history than preregistered (2010 vs 2016).
- **CBOE** `^SKEW` (from 1990), `^VIX`, `^VIX3M`, `^VVIX`, `^VIX9D`.

Publication lag enforced in the loader: each COT report is stamped
`tradable_from` = the Monday **after** the Friday 15:30 ET release. No test can
see a Tuesday snapshot before it was public.

## Every hypothesis failed, and failed the same way

| Hypothesis | Horizon | Design mean / t | Holdout mean / t |
|---|---|---|---|
| P1 leveraged-fund crowding (contrarian) | 1w | −0.112% / −0.71 | +0.052% / +0.25 |
| | 4w | −0.305% / −0.67 | +0.104% / +0.14 |
| P2 dealer net (contrarian) | 1w | −0.322% / −1.86 | +0.178% / +0.86 |
| | 4w | −1.268% / −1.59 | +1.035% / +1.49 |
| P3 asset-manager net (directional) | 2w | −0.618% / −1.93 | +0.288% / +0.76 |
| P4a SKEW high → long | 2w | −0.435% / −1.54 | +0.118% / +0.30 |
| P4b SKEW high → short | 2w | +0.435% / +1.54 | −0.118% / −0.30 |
| P5 VIX term backwardation | 1w | +0.320% / +1.49 | +0.292% / +1.34 |

**Survivors: 0.** Not one hypothesis reached |t| ≥ 2 on design.

The pattern is unmistakable: **every positioning signal is negative in design and
positive in holdout.** P1, P2 and P3 all flip sign, and they flip *together* —
which is what happens when three correlated series are all measuring the same
thing (market direction) and the market direction changed between the two
windows. It is not three independent failures; it is one.

P5 (VIX term backwardation) is the only signal with a consistent sign across
both windows (+0.320% design, +0.292% holdout at one week), but at t = +1.49 and
+1.34 it is well inside noise, and it did not clear the preregistered bar.

## Two silent failures found and fixed

**Contract code URL encoding.** `13874+` was sent unencoded, so Socrata read the
`+` as a space and matched zero rows. The first run returned an empty frame.

**Date alignment.** Yahoo stamps SPX at the 14:30 UTC open while the CBOE vol
indices are midnight-normalised — **zero overlapping timestamps**. SKEW and VIX
term were silently all-NaN and P4/P5 never executed; the first run reported "0
survivors" having tested only three of five hypotheses. The loader now
normalises, and a skipped test prints a SKIPPED line instead of vanishing.

The second bug is the more instructive one: a silent all-NaN join produces a
clean-looking negative result. Without the missing output rows being noticed,
this lane would have closed on evidence that was never gathered.

## Verdict

Positioning and skew do not provide a tradeable US500 edge at weekly frequency
on free public data. Per the preregistration, this lane closes here and no sixth
variant will be built to rescue it.

Honest limits on that claim: weekly COT is a coarse, heavily-revised aggregate
published with a three-day lag; `^SKEW` is a single summary statistic, not the
full surface. Dealer **gamma** positioning — which requires the option-by-option
open interest surface, not a free weekly aggregate — is a genuinely different
measurement and remains untested. It is the only version of "dealer positioning"
this result does not cover.

## Where US500 now stands

Seven independent approaches, all closed:

1. Bar-geometry families — 0 of 48 grid points profitable
2. Overnight effect — +0.62%/yr net
3. Daily reversal + 9 refinements — every filter made it worse
4. 14,400-attempt search + null — survivors matched sign-flipped noise
5. Corrected search (all review fixes) — holdout PF 1.009
6. Walk-forward, 5 folds — −390 net, 2 of 5 years positive
7. **Positioning and skew — 0 of 5 hypotheses reached |t| ≥ 2**
