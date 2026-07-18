# Out-of-Era Specialist Replication V2

This research-only package performs one sealed 2010-2016 replication of four
fixed XAUUSD specialist candidates and measures their pairwise independence.

Run order:

1. `python acquire_official_fomc.py`
2. `python preflight_candidates.py` (optional, outcome-free)
3. `python lock_definitions.py`
4. wait for all 78 Dukascopy months and normalize them
5. `python lock_final_contract.py`
6. `python run_research.py`

The final two commands fail until collection and normalization are exactly
complete. The outcome runner is one-shot.
