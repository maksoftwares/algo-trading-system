# V92 Shared Portfolio Precommitment

Any unchanged V92 final survivor is added to byte-identical V59/V60. The audit
must use original V59 trades, the V60 price reconstruction, side-correct stressed
V92 trades, one account, overlapping exposure, spread, slippage, ticket and
holding costs, and all V60 controls.

Every required window must satisfy all of the following:

- Development-2, Confirmation, and Final each reach at least `2.00` combined
  trades per calendar weekday.
- Combined stress PF is at least `1.50` and net P&L is positive.
- V92 standalone stress PF is at least the locked stage gate and its P&L remains
  positive after removing the locked number of top winners.
- No V59/V60 trade is removed, resized, delayed, or relabeled.
- Aggregate entry risk does not exceed the V60 account risk budget.
- V92 accepts at most two total entries per UTC date across all surviving
  policies. At each V92 entry, existing V59 add-ons and accepted V92 positions
  must remain within the frozen two-position and USD `45` concurrent initial-risk
  limits. A later frozen V59 entry is never skipped; any resulting historical
  limit breach fails the shared audit.
- The frozen V59 closed-drawdown circuit also governs V92: new V92 entries are
  suspended at USD `225` closed drawdown and may resume only after recovery to
  USD `180`, using only P&L realized by that decision time.
- Buffered floating drawdown does not exceed the frozen V60 hard cap of
  USD `449.7675`.
- Absolute daily P&L correlation between V92 and V59/V60 does not exceed `0.50`.

Failure retires V92 as an additive sleeve without changing V59/V60.
