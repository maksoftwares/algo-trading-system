# COMEX-Spot Receipt Innovation V69 Engineering Result

Date: 2026-07-20
Decision: `V69_ENGINEERING_STOP_PRE_OUTCOME`

V69 completed its outcome-blind calibration and selected policy
`H2000__CM100__IN040__FI30__VO10` at exactly 0.80 candidates per eligible
weekday, with eight long and eight short calibration candidates. The immutable
contract SHA-256 is
`747c43a0e476941a08a4e0c87be78efde0c986cf45be8a6fe67cabec61ae4586`.

The development runner stopped before writing candidates, labels, an audit, or
any economic result. The normalization code incorrectly required every
Databento `ts_recv` to be greater than or equal to the publisher `ts_event`.
The first violating source day contained 18 such records among 93,990 trades,
with a minimum difference of -10.83 ms.

Databento defines `ts_recv` as its capture-server receive timestamp and the
primary timestamp for sorting/indexing. It also documents that publisher event
clocks are not guaranteed to be synchronized with Databento's clock. Therefore
the rejected ordering is not a valid causality invariant for a receipt-time
strategy.

The V69 contract remains immutable and will not be edited or rerun. A successor
must preregister the engineering correction, repeat calibration, freeze a new
contract, and keep all strategy thresholds and economic gates unchanged.
