# Portable ML Top-Up V3 Demo Deployment

Decision: **PASS - ACTIVE PROSPECTIVE DEMO, BASELINE PRESERVED**

The portable V3 ensemble is active on demo account `1033030`. The
deterministic V60 order is always submitted and durably recorded before any
model evaluation. ML can only request one separate `0.01`-lot top-up. Any
artifact, feature, model, state, broker, or risk failure leaves the baseline
trade unchanged and produces no top-up.

## Evidence

- The exact forty-model 2026 ensemble reproduces all 147 stored 2026 scores
  and ranks with `0.0` maximum absolute error.
- Training contains 1,918 rows and ends at the purged
  `2025-12-30T00:00:00Z` cutoff.
- Outcome-free July parity used 4,896 common completed bars and 19,584 fixed
  contexts.
- Capital versus Dukascopy score/rank Spearman correlations are
  `0.9825/0.9825`.
- Mean rank difference is `0.0310`; top-quintile Jaccard agreement is
  `0.8892`.
- Capital top-quintile precision/recall are `0.9548/0.9283`.
- Every preregistered reproduction and parity gate passed.

Historical development evidence improves V60 from USD `5,045.67` to
`5,296.78`, with PF `1.721` to `1.723` and floating drawdown USD `335.34` to
`329.35`. The USD `251.10` delta has a moving-week-block lower 95% bound of USD
`92.38`. These figures are historical development evidence, not a promise of
future profit.

## Runtime

At `2026-07-29T18:12:57.946771Z`:

- status: `ACTIVE_DEMO_BROKER_ACTION`
- account: `1033030`, `Capital.ComMena-Demo`
- balance/equity: AED `3,648.06 / 3,648.06`
- open XAUUSD positions: `0`
- feeds healthy: `true`
- ML ready: `true`
- failure policy: `BASELINE_ONLY`
- minimum balance requirement: `false`
- risk mode: `ABSOLUTE_USD_ONLY`
- ML shadow: `false`
- live authority: `false`

Risk-eligible sources are R2, R3, R4, V7, V8, V25, and V57. R1 box and
pullback remain baseline-only because their historical training rows lacked
initial-risk labels. At most one ML top-up may be open and at most two may be
opened per UTC day. Existing source, account, direction, add-on, position,
drawdown, guardian, and emergency-close controls remain active.

Verification: portfolio `41/41`, tick replay `9/9`, prospective V3 `4/4`, and
Python compilation all pass. The active executor has no stderr output and no
duplicate process.
