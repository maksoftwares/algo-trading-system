# A3 ML Dukascopy M5 Momentum Portability V1 Result

Date: `2026-07-15`

Classification: `DUKASCOPY_M5_MOMENTUM_PORTABILITY_NO_SURVIVOR`

## Decision

Do not promote the frozen MT5 clean long/short portfolio from this experiment.

The independent replication window was profitable after the frozen stress costs, but the package failed the required frequency, older-history stability, lane stability, concentration, and bootstrap gates. The result is a useful research lead, not authorization for Python predictions, EA consumption, demo execution, or broker action.

## Reproduction Lock

- Pre-outcome commit: `55c35c0f`.
- EA SHA-256: `c590adabc92fe4b63dac22812e4ac9a12882b23b6ed8242848470f90fd01e265`.
- Portfolio specification SHA-256: `e5d7a0fe3283820ac73800bd8562eab9f098d70e5747346c2e8e7cca07d8576a`.
- Verified raw-tick source months: `72`.
- Source-bound M5 bars: `425,311`.
- Raw candidates SHA-256: `70af7ca943d50ecf5216ecab331d95d0cf913e7ddc541bc4f21fa43404d2c2f9`.
- Raw labels SHA-256: `8c62bf3e05c22177fe6bdb6ff0a15d04b97e345f7b2ec5ce90c348c2ea6565d0`.
- Selected labels SHA-256: `411690ea6e9b50bce190cacc52bb14088b6df0469fbb7d5c828bbd8a6b870580`.

An immediate second run reused all `72` monthly caches and reproduced all three artifact hashes exactly.

## Evidence

| Window | Trades | Win rate | Stress PF | Average stress R | Net USD | Max DD USD | Trades/source day |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Prehistory, 2018-07 through 2022-06 | 75 | 48.00% | 0.6677 | -0.2514 | -85.97 | 111.24 | 0.073 |
| Replication, 2022-07 through 2024-06 | 45 | 73.33% | 1.6751 | 0.2118 | 68.23 | 32.28 | 0.087 |

Replication was positive in both lanes: long produced `+$52.03` at PF `1.6178`, and short produced `+$16.20` at PF `1.9620`. Its calendar-month bootstrap average-R lower bound was also positive at `0.0108R`.

Those recent positives are not sufficient. Prehistory was negative overall and in both lanes, its bootstrap interval remained below zero, and removing the top 25 winners made both windows negative.

## Frequency Diagnosis

The exact rules generated `2,842` raw candidates across `1,548` source days, approximately `1.84` candidates per source day. Only `120` trades survived the frozen execution controls.

The dominant block was the portfolio's own `0.05R` maximum spread-to-stop cost gate:

- estimated cost above maximum: `2,627` candidates;
- spread above 75 points: `37` candidates;
- no quote inside entry window: `35` candidates;
- lane already occupied: `22` candidates;
- cooldown: `1` candidate.

This means the signal generator reached the desired raw opportunity range, but most opportunities were not economically executable under the locked Dukascopy bid/ask feed and risk controls. The cost gate is verified against the frozen portfolio specification; this is not a point-unit translation defect.

## Next Research Direction

Do not loosen the `0.05R` gate against these exposed outcomes and present the result as validation. Use the raw-candidate population only as exploratory evidence for a separately preregistered cost-aware strategy family. Any replacement must create wider expected movement relative to spread, preserve approximately one to two candidates per source day, and be evaluated on a new time holdout or prospective data.

No strategy promotion or deployment authorization is granted.
