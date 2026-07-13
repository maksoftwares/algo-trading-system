# XAUUSD Chop Fast Discovery V1

This isolated research lane screens three frozen, economically distinct chop strategies on M5, M15, M30, and H1. It does not modify existing research packages, invoke MT5, authorize execution, or create deployment artifacts.

The authoritative regime uses completed H4 Capital.com bars with frozen ADX, efficiency-ratio, displacement, range-width, and hysteresis rules. Entries use completed bars and the next executable Bid/Ask open. M30 is causally aggregated from six complete Capital.com M5 bars.

Run:

```powershell
python -m pytest xau-usd/xauusd-fast-research/chop-v1/tests -q
python xau-usd/xauusd-fast-research/chop-v1/run_chop_fast_discovery_v1.py --config xau-usd/xauusd-fast-research/chop-v1/config/chop_fast_discovery_v1.json
```

Raw broker data remains outside this lane and is not committed. Generated research artifacts are written to `outputs/`.

The reviewer-authorized bounded M30 verification writes its portable, hash-verified evidence under `outputs/bounded_followup_v1/`. M30 exits are replayed on ordered M5 sub-bars; regime exits use executable-open timestamps, maximum holds use elapsed UTC time, and gap-through-stop exits use the worse executable Bid/Ask open. The frozen Capital.com inputs end on 2025-07-01, so the bounded outcome is `FOLLOWUP_DATA_INCOMPLETE_NO_ADVANCEMENT` and no engineering or deployment advancement is authorized.
