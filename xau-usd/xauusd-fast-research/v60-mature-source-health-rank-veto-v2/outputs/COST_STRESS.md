# V60 Mature Source-Health V2 Cost Stress

Diagnostic only. The nominated V2 policy is unchanged and deployment remains unauthorized.

The exact replay population has 1703 candidates. Existing modeled open cost averages $0.572 and has a $0.515 median.

| Added cost/trade | vs existing mean | V60 net | V2 net | Delta | V60 PF | V2 PF | V60 closed DD | V2 closed DD | V60 equity DD | V2 equity DD | Vetoes (common path) | Min annual delta | Comparative gates |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| $0.00 | 0% | $3603.57 | $3655.75 | $+52.19 | 1.7107 | 1.7289 | $223.28 | $217.46 | $238.28 | $238.28 | 12 (12) | $+0.00 | PASS |
| $0.10 | 17% | $3468.49 | $3552.44 | $+83.95 | 1.6760 | 1.6955 | $220.41 | $215.15 | $242.13 | $232.80 | 22 (15) | $+0.00 | PASS |
| $0.20 | 35% | $3358.66 | $3398.14 | $+39.48 | 1.6458 | 1.6588 | $222.29 | $221.39 | $244.02 | $241.21 | 18 (17) | $-6.91 | FAIL |
| $0.25 | 44% | $2893.20 | $3340.95 | $+447.74 | 1.5616 | 1.6435 | $245.95 | $220.76 | $266.68 | $240.33 | 19 (16) | $-6.86 | FAIL |
| $0.50 | 87% | $3029.29 | $2678.09 | $-351.20 | 1.5602 | 1.5094 | $223.88 | $239.18 | $245.60 | $259.16 | 23 (21) | $-236.05 | FAIL |
| $1.00 | 175% | $1226.56 | $1314.58 | $+88.02 | 1.3695 | 1.3585 | $340.42 | $310.16 | $357.11 | $318.02 | 14 (12) | $-6.11 | FAIL |

The added cost is charged to both V60 and V2. Because the replay is rerun from ticks, the surcharge can change health state, veto decisions, drawdown controls, and exit paths.
