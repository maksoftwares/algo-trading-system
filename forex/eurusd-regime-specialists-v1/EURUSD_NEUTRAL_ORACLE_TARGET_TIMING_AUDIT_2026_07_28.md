# EURUSD Neutral oracle target-timing audit

Date: `2026-07-28`

Status: `DEVELOPMENT_TARGET_DEFINITION_AUDIT`

The full-calendar hindsight oracle is not temporally neutral. It scans every
M5 entry in chronological order and stops after finding the first four
target-before-stop winners. Consequently, entry time is dominated by the
search order.

The source-hashed ledger contains 7,816 oracle rows. Its Neutral slice has
2,615 rows on 662 UTC dates:

- 1,321 LONG and 1,294 SHORT;
- all 2,615 use the primary four-pip risk tier;
- 1,636 entries occur from 00:00 through 00:15 UTC; and
- 2,482 entries, or 94.91%, occur before 01:00 UTC.

The frozen prospective macro specialist enters around 12:45 UTC after a
12:30 release. Across the development oracle, zero Neutral entries lie within
15, 60, or 240 minutes of 12:45. Even perfect causal side selection at that
clock therefore cannot produce a temporal oracle match under those windows.

This separates two legitimate claims:

1. A strategy can be a profitable causal specialist owned by the Neutral
   regime without reproducing the oracle's chronological clock artifact.
2. A strategy may claim temporal hindsight-oracle imitation only if it passes
   the separately frozen one-to-one timing evaluation.

The macro strategy remains unchanged and prospective-only. Its profitability
test should continue because the user has made frequency negotiable, but it
must not be described as a temporal clone of the midnight oracle. A future
temporal imitator would need genuinely new information available before the
UTC open; the price, flow, OCO, paired-side, and fitted midnight families
already recorded in this package are closed and cannot be cosmetically
retuned.

Reproduce:

```powershell
uv run --offline --with pandas python audit_neutral_oracle_target.py
```
