# EURUSD Cross-Pair Compression own-price specialist

Date: 2026-07-30

Status: **HISTORICAL_VALIDATION_REJECTED**

Demo-order authorization: **false**

## Decision

The first independent Cross-Pair Compression mechanism is rejected at the
development gate. None of its six preregistered EURUSD own-price rules was
eligible, so the locked 2022-2026 validation outcomes were not used to select
or rescue a rule.

The specialist used the same 20:00 UTC entry, 8-pip stop, 12-pip target,
six-hour maximum hold, bid/ask outcomes, Friday cash rule, and upstream
ownership vetoes as the residual portfolio. Its only new information was
EURUSD's own completed 15-, 60-, or 240-minute price displacement inside the
Cross-Pair Compression regime.

## Development result, 2016H2-2021

All six rules had 418 trades:

| Rule | Net R | PF | Stressed PF |
|---|---:|---:|---:|
| 15-minute fade | -46.6625 | 0.7870 | 0.6898 |
| 15-minute momentum | -33.3625 | 0.8453 | 0.7421 |
| 60-minute fade | -22.4250 | 0.8925 | 0.7829 |
| 60-minute momentum | -57.6000 | 0.7453 | 0.6536 |
| 240-minute fade | -57.0375 | 0.7479 | 0.6565 |
| 240-minute momentum | -22.9875 | 0.8898 | 0.7799 |

The best rule still lost 22.425R and had stressed PF only 0.783. The protocol
therefore selected `CASH`, produced no validation trades, and left the
protected M15 result unchanged.

This failure is useful: the Compression regime does have 695 complete
historical opportunities, but neither simple cross-pair direction nor simple
own-price displacement predicts the 8-pip/12-pip six-hour outcome. The next
Compression mechanism must be structurally different, such as a selective
intraday exhaustion/rejection setup rather than always choosing a side at
20:00.

## Reproducibility

Run:

```powershell
uv run --offline --with pandas --with numpy --with pyarrow python run_compression_own_price_family.py
```

Implementation hashes:

- config:
  `a793b2b442a58fc111faf2a78ad770b8d3baaf1a21b76b68e8153b8cdb6af337`
- source:
  `728d6498c86c45228b950efb39d6683546627bec00555adc4e77122e0fa56dee`

Output hashes:

- `DEVELOPMENT_CANDIDATES.csv`:
  `4fe4a9bdd63cdacffda5c11a29fc28ed3e0d1e7d6799e79035ee60b1a73f4d41`
- `VALIDATION_TRADES.csv`:
  `d6164fe569c099b2e08d7863e712b6a1db2f3b566ee0ed882c1b266f535cf67e`
- `MONTHLY.csv`:
  `c7d4430cb8d9f14b097db57be88df1ed970d261eff97831a2156492d97021d2c`
- `RESULT.json`:
  `9ab232730a680d964e9e3eea6eb89881719ae02a673a111eba3fc1d7cbfd3106`
- `RESULT.md`:
  `3a47c1fd4302939261d47a6b8416096f127712e64043ea91c15817e022a8870c`
