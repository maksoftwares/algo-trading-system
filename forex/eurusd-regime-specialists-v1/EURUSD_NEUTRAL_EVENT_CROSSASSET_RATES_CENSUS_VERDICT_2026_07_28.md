# EURUSD Neutral event-conditioned cross-asset rates census verdict

## Verdict

`CENSUS_FAIL_NO_PNL_ALLOWED`

The exact strategy is closed without opening P&L. Its event source, title
taxonomy, cross-asset reaction, regime ownership, risk contract, and sample
gates were hash-locked and pushed before the candidate census.

## Outcome-blind census

| Stage | Count |
|---|---:|
| Qualifying USD event rows | 2,477 |
| Unique qualifying event-time clusters | 890 |
| Opposite-sign DXY/Treasury candidates before regime | 402 |
| Neutral candidates after the complete frozen contract | 53 |
| Candidate UTC dates | 51 |
| LONG / SHORT | 26 / 27 |

The 53 Neutral candidates were distributed as follows:

| Frozen window | Candidates | Required |
|---|---:|---:|
| 2019-2022 development | 28 | 50 |
| 2023 | 4 | 8 |
| 2024 | 10 | 8 |
| 2025 | 6 | 8 |
| 2026 H1 | 5 | 8 |
| Total | 53 | 100 |

Only the balanced-direction gate passed. The total, development,
full-forward-year, and latest-half-year sample gates failed.

## Cash attribution

Of the 890 frozen event clusters:

- 39 lacked an exact DXY or Treasury baseline/endpoint quote;
- 236 had same-direction or zero DXY/Treasury reactions;
- 212 exceeded the frozen 25-pip structure-risk ceiling;
- 349 otherwise valid agreement candidates were not owned by the causal
  Neutral, non-shock, non-compression regime;
- one entry was outside the EURUSD archive.

These are decision-time capacity diagnostics, not outcome diagnostics.

## Why no backtest is shown

The preregistration explicitly says that a failed census forbids loading P&L.
Running the backtest on 53 trades, lowering the sample gates, widening the
stop ceiling, deleting weak windows, or relaxing Neutral ownership after
seeing these counts would break the experiment.

The conclusion is therefore about *capacity only*: this exact mechanism
cannot support a statistically credible Regime 1 expert on the available
2019-June 2026 archive. It says nothing positive or negative about the unseen
trade returns.

## Integrity

Deterministic census:

`outputs/neutral_event_crossasset_rates/CENSUS.json`

SHA-256:

`b9e50e6099543ab91ed80841b5e41adc8b0d7b10963f569bdf57e02419ae013f`

No demo or live action is authorized.
