# COMEX-Spot Receipt Innovation V69

V69 tests whether a just-received COMEX gold price innovation leads the latest
already-known Dukascopy XAUUSD quote over 250 milliseconds to five seconds.

The calibration stage registers exactly 1,000 policies and may inspect only
causal source features, candidate frequency, active-day coverage, and direction
balance. It cannot inspect any post-decision spot quote or economic outcome.

Run in this order:

```powershell
uv run --with-requirements requirements.txt python run_calibration.py
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python run_stage.py --stage development
```

Validation and exam remain sealed until every preceding gate passes. This is
historical research only and grants no model, EA, demo, live, payment, or broker
authority.
