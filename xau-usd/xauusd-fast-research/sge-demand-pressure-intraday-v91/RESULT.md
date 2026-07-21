# V91 SGE Demand-Pressure Intraday Decision

Decision: **RETIRED AT DISCOVERY**

Contract: `3026be62207c71d8e5601168a2c64d965d5d1b44654e43fbdfadf59db8d85741`

V91 opened Discovery once for the 1,000 locked attempts `122001-123000`.
No policy passed every preregistered gate, so Replication, Development 2,
Confirmation, and Final remain sealed. V59/V60 was not modified.

## Discovery summary

- Policies evaluated: 1,000
- Policies with positive stress net R: 24
- Policies with stress PF at least 1.20: 14
- Policies with frequency at least 0.34 per weekday: 242
- Gate-passing policies: 0
- Minimum raw p-value: 0.03828
- Minimum Benjamini-Hochberg q-value: 1.0000
- Best observed stress PF: 3.083, from only 10 trades
- Highest observed frequency: 0.942 trades per weekday

Every policy failed multiple-testing control. Nearly every policy also failed
segment stability and top-winner robustness. The nearest dense positive policy
had 134 trades, 0.206 trades per weekday, PF 1.404, and 27.06 net R, but only two
of three segments were profitable, its worst-segment PF was 0.926, its positive
month share was 30%, and its q-value was 1.0.

## Mechanism evidence

| Mechanic | Positive / 200 | Best PF | Best frequency | Minimum p | Minimum q |
|---|---:|---:|---:|---:|---:|
| Cash momentum breakout | 8 | 1.361 | 0.942 | 0.2484 | 1.0000 |
| Cash volume pressure | 4 | 1.517 | 0.801 | 0.0383 | 1.0000 |
| Deferred basis reversion | 0 | 0.987 | 0.910 | 1.0000 | 1.0000 |
| Deferred OI expansion | 7 | 2.530 | 0.710 | 0.0927 | 1.0000 |
| Delivery direction pressure | 5 | 3.083 | 0.759 | 0.0568 | 1.0000 |

The high-PF observations are sparse and do not support an additive specialist.
V91 may not be retuned, direction-reversed, or rescued. The accepted SGE source
remains available for future materially different hypotheses, but these five
mechanics are closed.
