# A3 ML Dukascopy M5 Discovery Train V1 Result

Date: `2026-07-15`

Classification: `DUKASCOPY_M5_DISCOVERY_TRAIN_NO_SURVIVOR`

## Decision

Reject all 12 trend-aligned M5 profiles. Do not open validation, test, or new-holdout outcomes for this family.

The campaign achieved high trade frequency, but every profile had negative expectancy after verified bid/ask execution and frozen stress costs. This rejects the trend pullback, continuation breakout, and trend sweep/reclaim premise as implemented; it does not justify loosening the profitability gates.

## Reproduction Lock

- Pre-outcome commit: `b295f40c`.
- Source months: `37`, all source-bound caches reused.
- Training source days: `774`.
- Raw candidates: `72,374`.
- Raw resolved labels: `72,058`.
- Executed profile trades: `17,331`.
- Candidate SHA-256: `88d3c97f412e5ba871315826e6b7af94c5347e7ca146bc5a91073dec22081fc3`.
- Raw-label SHA-256: `4cfcae98b0f6c9e74a90d816eb7d71c763d22d9d7e31bbb0f3341ef06c95760d`.
- Executed-label SHA-256: `9db8f27e27133c1fca702181a0f093d9ca5a1e84817286c4cdff9948a78131c2`.

An immediate second run reproduced all three hashes exactly.

## Evidence

All data-quality gates passed. Per-profile frequency ranged from `1.049` to `3.034` trades per source day, so opportunity coverage was not the problem.

The best profile by stress PF was `breakout_h1_rr1p5`:

- trades: `1,857`;
- trades per source day: `2.399`;
- win rate: `37.05%`;
- stress PF: `0.765`;
- average stress return: `-0.1762R`;
- stress net: `-$1,384.30` at fixed `0.01` lot;
- maximum closed drawdown: `$1,396.81`.

Across all 12 profiles, stress PF ranged from `0.646` to `0.765`. Every profile had negative average R and negative net P&L. No profile passed the train selection gates.

## Holdout Protection

- selected profile: none;
- reserved outcomes opened: false;
- validation authorization: false;
- test authorization: false;
- strategy promotion: prohibited.

## Next Research Direction

The next bounded campaign should test mechanically distinct mean-reversion behavior rather than another trend-continuation threshold variant: volatility-band overextension fades, exhaustion fades, and non-trending sweep/reclaims. It must retain bid/ask costs, high-frequency gates, drawdown controls, train-only selection, and the unopened later windows.

No Python prediction, EA consumption, demo, live, or broker action is authorized.
