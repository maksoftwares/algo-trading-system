# Win Rate Policy

Status: RESEARCH_POLICY_ONLY

Win rate is useful, but it is not the primary target.

The primary target is:

```text
net expectancy in R after measured cost
```

## Required Formula

For a strategy with average win `avg_win_R`, average loss `avg_loss_R`, and average cost `cost_R`:

```text
expected_R = (win_rate * avg_win_R) - ((1 - win_rate) * abs(avg_loss_R)) - cost_R
```

The break-even win-rate formula is:

```text
break_even_win_rate = abs(avg_loss_R) / (avg_win_R + abs(avg_loss_R))
```

## Interpretation

A candidate with a 60% win rate can still fail if the average loss and cost_R are large.

A candidate with a 35% win rate can still be interesting if average wins are much larger than losses, costs are low, and drawdown/concentration gates pass.

Therefore every report must separate:

- raw win rate
- average win R
- average loss R
- payoff ratio
- cost_R
- net expectancy R
- sample size
- duplicate-family exposure

## Demo Data Rule

Demo win rate may diagnose failure modes. It does not authorize direct candidate tuning.

Small samples should be used to ask better questions:

- Are losses clustered in one session?
- Are stops too tight for measured spread?
- Are same-family EAs duplicating the same exposure?
- Does the accepted-only view differ from the provisional view?
- Does wider stop geometry improve cost_R without destroying the mechanism?

Every improvement must become a new versioned draft hypothesis before it is tested.
