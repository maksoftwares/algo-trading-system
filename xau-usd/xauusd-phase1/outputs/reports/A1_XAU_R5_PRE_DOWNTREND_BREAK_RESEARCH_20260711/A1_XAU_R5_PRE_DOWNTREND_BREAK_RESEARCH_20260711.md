# A1 XAU R5 Pre-Downtrend Opportunity Evidence

Status: `RESEARCH_AVAILABILITY_ONLY_NOT_STRATEGY_VALIDATION`

The proposed live rule does not read H4 positions, H4 P/L, drawdown, or outcomes. H4 intervals are used only after signal construction to test contemporaneous availability.

## Causal router availability

The common evidence window contains 145 H4 positions in 13 merged exposure episodes.  Across 84596 causal M5 snapshots while H4 was exposed:

| State | M5 snapshots |
| --- | ---: |
| `CHOP` | 24155 |
| `COMPRESSION` | 2532 |
| `SHOCK` | 11370 |
| `UPTREND` | 46539 |
| `UPTREND + CHOP` | 70694 (83.57%) |

## Frozen q55 opportunity incidence

| Measure | Count |
| --- | ---: |
| Raw UPTREND/CHOP blocked-signal rows | 1185 |
| Raw broker dates | 462 |
| Rows after spread <=75, cost <=0.05R, stop <=1000 | 767 |
| Eligible broker dates | 326 |
| Eligible rows during H4 exposure | 324 |
| H4 positions touched | 128 / 145 |
| H4 episodes touched | 13 / 13 |

These are pre-daily-cap and pre-own-position-cap opportunities, not predicted executions. The common window ends in June 2026; full-decade execution and overlap remain unknown until the preregistered exact MT5 run.
