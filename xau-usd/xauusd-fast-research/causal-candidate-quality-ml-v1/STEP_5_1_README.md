# Step 5.1 AED Correction Result

Step 5.1 corrects the Step 5 account-unit error for Capital.com demo account
`1033030`. The account balance and equity are AED, while the source XAUUSD
trade economics are USD. The broker snapshot, conversion rates, unchanged
portfolio rules, and implementation were frozen before the corrected result
was opened.

The corrected primary portfolio fails its evidence gate. It accepted `389`
trades, earned `AED 879.24`, reported PF `1.241`, and reached an M5 floating
drawdown of `AED 393.61` (`10.85%` of starting equity). The account governor
crossed its frozen 10% closed-drawdown suspension in September 2020. With fixed
`0.01` lot sizing, no smaller recovery size exists, so every later otherwise
eligible candidate remained suspended and the trailing five-year windows have
zero entries.

This result supersedes Step 5's account-specific percentage and risk claims for
account `1033030`. It does not invalidate the source trade labels or the larger
historical-policy comparators. It does block prospective MT5 parity, EA
attachment, shadow execution, and demo activation for this account under the
current fixed-lot policy.

On 2026-07-22 the owner separately waived minimum-balance eligibility for
prospective **demo data collection**. That operational waiver does not turn
this failed historical gate into a pass and cannot be used on a live account.
The canonical demo runtime retains its fixed-lot, drawdown, emergency-close,
position, daily-entry, spread, and guardian controls.

Run verification with:

```powershell
uv run --with-requirements requirements-step5-1.txt python verify_step_5_1.py
```

The next research decision must address the minimum-lot/capital constraint
without loosening the risk limits after seeing this result. Defensible options
are a sufficiently capitalized account, a broker that supports smaller XAUUSD
volume, or a newly preregistered portfolio that remains flat whenever `0.01`
lot exceeds the original risk budget.
