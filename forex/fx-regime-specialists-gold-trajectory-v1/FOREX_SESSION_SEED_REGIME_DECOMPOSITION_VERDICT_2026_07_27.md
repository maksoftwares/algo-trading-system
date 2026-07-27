# USDJPY Session-Seed Regime Decomposition Verdict — 2026-07-27

Status: `NO_PORTFOLIO_FORMED`

Boundary: offline research only. The base seed and classifier remained frozen; no MT5 or broker runtime was used.

Raw frozen-seed signals before ownership: 2337.

## Ownership Census

| Owner | Signals |
| --- | ---: |
| `s3_compression_release_breakout` | 1036 |
| `SHOCK_CASH` | 500 |
| `s4_neutral_normal_breakout` | 375 |
| `DIRECTION_CONFLICT_CASH` | 235 |
| `s1_established_aligned_breakout` | 186 |
| `s2_transition_aligned_breakout` | 5 |

## Standalone Experts

| Expert | Trades | PF | Net R | Max DD R | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| S1 established aligned breakout | 70 | 1.9058 | 21.7983 | 3.0041 | `REJECTED_STANDALONE` |
| S2 transition aligned breakout | 5 | 1.4910 | 0.9846 | 2.0054 | `REJECTED_STANDALONE` |
| S3 compression-release breakout | 444 | 1.0839 | 17.9540 | 14.7485 | `REJECTED_STANDALONE` |
| S4 neutral-normal breakout | 162 | 1.2808 | 20.0092 | 7.0396 | `REJECTED_STANDALONE` |

### S1 established aligned breakout

| Window | Trades | PF | Net R | Expectancy R |
| --- | ---: | ---: | ---: | ---: |
| design | 19 | 3.7158 | 10.9203 | 0.5748 |
| validation | 27 | 1.6918 | 6.9338 | 0.2568 |
| adaptive_exam | 24 | 1.3935 | 3.9442 | 0.1643 |

Top-5%-winner removal: 17.8019R. Additional 0.5-pip stress: 20.7803R.

### S2 transition aligned breakout

| Window | Trades | PF | Net R | Expectancy R |
| --- | ---: | ---: | ---: | ---: |
| design | 2 | Infinity | 1.9919 | 0.9960 |
| validation | 1 | 0.0000 | -1.0024 | -1.0024 |
| adaptive_exam | 2 | 0.9951 | -0.0049 | -0.0024 |

Top-5%-winner removal: -0.0135R. Additional 0.5-pip stress: 0.9078R.

### S3 compression-release breakout

| Window | Trades | PF | Net R | Expectancy R |
| --- | ---: | ---: | ---: | ---: |
| design | 194 | 0.9489 | -5.0899 | -0.0262 |
| validation | 149 | 1.2174 | 14.6053 | 0.0980 |
| adaptive_exam | 101 | 1.1790 | 8.4385 | 0.0835 |

Top-5%-winner removal: -6.7806R. Additional 0.5-pip stress: 8.8562R.

### S4 neutral-normal breakout

| Window | Trades | PF | Net R | Expectancy R |
| --- | ---: | ---: | ---: | ---: |
| design | 76 | 1.0439 | 1.6321 | 0.0215 |
| validation | 39 | 2.2378 | 14.8873 | 0.3817 |
| adaptive_exam | 47 | 1.1583 | 3.4897 | 0.0742 |

Top-5%-winner removal: 10.4079R. Additional 0.5-pip stress: 16.9581R.

## Router

Admitted experts: none.
Router status: `NO_PORTFOLIO_FORMED`.

No failed expert is rescued by aggregation. This decomposition is development evidence, not demo evidence.
