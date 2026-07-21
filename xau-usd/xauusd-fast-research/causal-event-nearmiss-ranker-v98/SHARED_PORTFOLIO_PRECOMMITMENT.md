# V98 Shared-Portfolio Precommitment

Only policies surviving Discovery, Confirmation, and Final may enter this
audit. Their ledgers are routed chronologically against the byte-identical V60
price ledger under the frozen V59 limits: at most two add-on positions, USD 45
concurrent add-on initial risk, two V98 entries per UTC date, and the USD
225/180 drawdown suspend/resume state.

The shared audit reuses the hash-bound V97 shared-audit calculations and the
frozen V60 M5 floating-equity reconstruction. The adapter may rename V97 fields
to V98 fields but may not alter routing order, P&L, frequency, correlation,
position-risk, or drawdown arithmetic.

Each required window must independently pass:

- combined frequency at least 2.0 trades per weekday;
- combined stressed PF at least 1.5 and positive stressed net;
- V98 standalone PF and winner-removal gate for that stage;
- absolute daily P&L correlation at most 0.5;
- all position and concurrent-risk limits; and
- buffered floating drawdown at most USD 449.7675.

Failure is terminal and grants no execution authority.
