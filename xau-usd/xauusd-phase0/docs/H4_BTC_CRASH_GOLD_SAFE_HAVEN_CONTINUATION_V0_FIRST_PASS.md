# H4 BTC Crash Gold Safe-Haven Continuation v0 First Pass

Date: 2026-06-07

Expert: `h4_btc_crash_gold_safe_haven_continuation_v0`

Hypothesis file: `docs/hypothesis_h4_btc_crash_gold_safe_haven_continuation_v0.md`

SHA256: `c5b24ea3141dd4bb2b5d84af7d55c47da42d1024e26065303ca1f829d9d17be9`

## Verdict

REJECTED_FIRST_PASS. Do not tune v0.

This candidate tested a distinct BTC mechanism from the rejected BTC stress-reversal family: shifted BTC crash pressure plus completed H4 XAU breakout confirmation, long-only, with weekly throttling. It failed because the matrix was far too sparse, only Pepperstone showed a positive pocket, and Capital.com/Dukascopy were negative.

## Smoke

PASS.

- Signals: 1
- Phase 0 result run allowed: false

## Matrix Summary

| Cell | Broker | Cost | Trades | PF | Return % | Max DD % | Max zero months | Concentration |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 6 | 0.4570 | -0.8889 | 1.1830 | 10 | 100.00 |
| 2 | capital_com | median | 6 | 0.4570 | -0.8889 | 1.1830 | 10 | 100.00 |
| 3 | capital_com | p95 | 6 | 0.4501 | -0.9069 | 1.1985 | 10 | 100.00 |
| 4 | pepperstone | best_case | 5 | 1.8719 | 0.7496 | 0.4474 | 7 | 83.60 |
| 5 | pepperstone | median | 5 | 1.8719 | 0.7496 | 0.4474 | 7 | 83.60 |
| 6 | pepperstone | p95 | 5 | 1.8615 | 0.7424 | 0.4482 | 7 | 84.20 |
| 7 | dukascopy | best_case | 7 | 0.4988 | -1.0224 | 1.4341 | 12 | 100.00 |
| 8 | dukascopy | median | 7 | 0.4713 | -1.1124 | 1.4986 | 12 | 100.00 |
| 9 | dukascopy | p95 | 7 | 0.4824 | -1.0424 | 1.4174 | 12 | 100.00 |

## Gate Read

- PF >= 1.30 cells: 3/9
- Trade-count cells: 0/9
- Positive broker windows: Pepperstone only
- Capital.com: negative across all costs
- Dukascopy: negative across all costs
- Max zero-trade months: 12
- Concentration: failed; top-trade concentration is effectively dominant due sparse sample

## Decision

Reject without tuning. The BTC crash safe-haven-continuation framing did not turn the earlier sparse BTC clue into a robust EA. Any future BTC work should require a genuinely better crypto data class or a materially different source of information, not another threshold variant on shifted daily Yahoo BTC OHLCV.
