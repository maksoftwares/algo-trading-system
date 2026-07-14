# London breakout provisional bar screen v1

This research-only lane implements the reviewer authorization dated 2026-07-14. It is based on commit `11055777a30c193640cdf546898071fb10dfc59d` and is confined to this directory.

The runner audits the frozen Capital.com H1/M15/M5 inputs before any signal or trade scoring. It fails closed if fewer than three declared scoring instruments have complete bars through 2026-06-30, if quote basis or spread units cannot be established, or if any required execution path is unavailable.

Run:

```powershell
python run_provisional_screen.py
python -m pytest tests -q
```

The current repository inputs stop on 2025-06-30, so the runner emits `LONDON_BREAKOUT_V1_PROVISIONAL_DATA_INVALID` and deliberately leaves all signal, trade, performance, and stress ledgers empty. No account-dollar, lot-sizing, leverage, engineering, or deployment conclusion is produced.
