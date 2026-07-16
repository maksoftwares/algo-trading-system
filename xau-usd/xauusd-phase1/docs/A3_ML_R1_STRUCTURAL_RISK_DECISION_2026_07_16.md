# A3 ML R1 Structural Risk Decision

Date: 2026-07-16

## Decision

The frozen Iteration 2 classification is `STRUCTURAL_RISK_FAIL`.

- R1 cannot serve as the demo-ready core strategy.
- R1 remains a research comparator and possible future low-frequency sleeve only.
- The frozen USD 10,000 account-risk guard is retained as a valid engineering pattern for future specialists.
- No R1 entry, stop, target, router, risk threshold, or gate may be tuned against this result under the same version.
- Strategy promotion, Python demo prediction, EA consumption, and broker action remain disabled.

The authoritative result is identified by:

- contract SHA256: `0eaf5e723278d6d4f67edc4947f286c88fe5809ce86ad7cbfd009e4301d769da`
- report JSON SHA256: `26b2034eea842be00add42198bc2a575d623ca6538e3e0852303be86d1eb70ad`
- admissions CSV SHA256: `7627125574113a0f07a3e737fcf0a58c623cc1280776b2b309d235efdaa15a99`
- hourly-equity CSV SHA256: `a6f231ce845573d5f681e82a41eb21f37960d7223fe826220353b64874bcb587`
- episodes CSV SHA256: `b9f65db4e26cca08c523e2ba2403b28cd536966c9f57a8f07b8812f902a53aea`

## Exact Baseline

The engine marked 137,247,008 chronological Dukascopy ticks during R1 exposure and reconciled every recorded exit price and final stress balance.

| Metric | Frozen R1 baseline |
| --- | ---: |
| Trades | 310 |
| Stress net | USD 10,120.70 |
| Stress PF | 2.750 |
| Win rate | 54.52% |
| Closed drawdown | USD 934.64 |
| Exact floating drawdown | USD 1,284.17 |
| Exact floating drawdown on USD 10,000 | 10.83% |
| Maximum concurrent positions | 13 |
| Maximum original-stop risk | USD 1,225.62 |
| Maximum margin used | USD 749.61 |
| Approximate trades per trading day | 0.123 |

At fixed 0.01 lot, the same path produced 48.01% maximum relative floating drawdown when shifted to a USD 1,000 starting balance and 19.01% at USD 5,000. A fixed-lot capital base of approximately USD 12,842 is required for the observed absolute drawdown to equal 10% of starting capital, before adding any safety buffer.

## Frozen Risk Guard

The causal USD 10,000 demo guard accepted 215 trades and rejected 95:

- 75 exceeded 0.5% initial risk at the broker's 0.01 minimum lot;
- 18 exceeded 2% aggregate same-direction initial risk;
- 2 exceeded eight concurrent positions.

| Metric | Demo guard |
| --- | ---: |
| Accepted trades | 215 |
| Trade retention | 69.35% |
| Stress net | USD 2,716.52 |
| Net retention | 26.84% |
| Stress PF | 1.818 |
| Win rate | 50.70% |
| Exact floating drawdown | USD 783.75 |
| Exact floating drawdown on USD 10,000 | 6.93% |
| Maximum original-stop risk | USD 224.38 |
| Maximum margin utilization | 2.59% |
| Approximate trades per trading day | 0.085 |

The guard improved risk shape materially. It passed floating drawdown, PF, trade retention, episode concentration, top-three-episode removal, margin, risk-limit, and Monte Carlo gates. Episode-block Monte Carlo reported zero 50%-equity ruin events in 10,000 seeded simulations and a 0.10% probability of drawdown reaching 15%.

## Decisive Failures

1. Controlled net retention was 26.84%, below the frozen 50% minimum.
2. Only 58.26% of rolling six-month windows were positive, below the frozen 65% minimum.
3. Frequency fell from approximately 0.123 to 0.085 trades per trading day, moving farther from the opportunity-coverage goal.

The first failure occurs because many recent high-price, wide-stop R1 trades cannot fit a 0.5% risk budget at the broker's 0.01 minimum lot. Relaxing the risk limit after observing those profits would be outcome-driven and is prohibited.

## Capital Interpretation

There was no modeled margin call at USD 1,000, USD 5,000, or USD 10,000, but absence of liquidation is not an acceptable drawdown standard. The exact path shows that a small account can survive while still experiencing an owner-unacceptable equity decline.

The risk guard requires roughly USD 7,838 for its observed USD 783.75 drawdown to equal 10% of starting capital, before a safety buffer. This capital observation does not turn the failed strategy into a qualified core.

## Next Iteration

The next research iteration must target orthogonal opportunity sources for compression, chop, and shock recovery, with naturally shorter holding periods and smaller stop distances that fit 0.01-lot account risk. Candidate generation must be trained or designed on a historical development partition and judged on later chronological and cross-feed partitions.

A full shared-account composition test is premature until at least two specialists independently qualify. R1 may remain in that future test only as an explicitly unqualified comparator or after a genuinely new version is preregistered and validated.

The six-stage minimum remains intact, but two completed stages have rejected the current core. Four formal stages remain, and specialist discovery may require multiple research cycles before one is allowed to advance.
