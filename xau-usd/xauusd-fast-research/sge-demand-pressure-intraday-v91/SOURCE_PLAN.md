# V91 Shanghai Gold Exchange Source Plan

Date: 2026-07-21

This source foundation collects public Shanghai Gold Exchange daily reports for
2016-07-01 through 2026-06-30. It is outcome-blind: collection and normalization
may inspect SGE report fields but may not inspect XAUUSD post-entry prices,
returns, labels, or strategy metrics.

The normalized source preserves daily contract open, high, low, close, weighted
average, volume, amount, open interest, direction, and delivery volume. Historical
HTML and normalized Parquet remain outside Git under
`C:/SgeGoldDemandFoundationV1`. Only code and later aggregate/hash evidence may be
committed.

Older reports use the official SGE daily-history index and detail pages. Reports
from 2024 onward use the official paginated daily endpoint. Collection is
resumable, bounded to the registered period, rate-limited by a small worker pool,
and fails on conflicting duplicate `(date, contract)` rows.

No strategy, model, EA, demo, live, broker, payment, or Databento authority is
granted by this source plan.
