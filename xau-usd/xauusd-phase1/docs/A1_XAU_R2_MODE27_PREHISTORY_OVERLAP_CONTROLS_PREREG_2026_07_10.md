# A1 XAU R2 Mode27 Prehistory Overlap Controls Preregistration

Date: `2026-07-10`

Status: `LOCKED_NOT_RUN`

`HISTORICAL_RUN_AUTHORIZED=False`. This package must not invoke MetaTrader 5 until that
constant is changed after explicit authorization. Static validation is allowed.

## Purpose

Produce the missing exact-MT5 control ledgers for the frozen mode27 overlap audit over
`2016.01.01` through `2021.12.31`. This is an evidence-completion run, not strategy
research. It cannot add a threshold, change an input, introduce a sixth cell, select a
winner, or promote any control.

## Frozen controls

| Control ID | Authoritative source runner | Authoritative variant | Frozen tester-input SHA-256 | Original priority |
| --- | --- | --- | --- | ---: |
| `r2_pullback_rejection_v1_h1` | `run_a1_r2_pullback_rejection_short_v1_exact.py` | `r2_pullback_short_h1_confirm` | `9c84ccab846a723465a2ed23b2f31f2c94364ea18eff66610d98d3aadfff6466` | 84 |
| `r2_pullback_rejection_v2_body58` | `run_a1_r2_pullback_rejection_short_v2_repair_exact.py` | `r2_h1_m5_body58` | `c7b68ed3187cf6c1303b556c9e81b2ec74add0c94dd7e920f50d2dc95c05468a` | 91 |
| `r2_continuation_v1_body45` | `run_a1_r2_continuation_short_v1_exact.py` | `r2_impulse_retest_body45` | `bab0cd951b34fed2d5bb8ff93a53c7bbf37833223b965d1f0a22efcf3df179af` | 98 |
| `r2_continuation_v2_break15_30` | `run_a1_r2_continuation_short_v2_repair_exact.py` | `r2_impulse_break15_30_cap20` | `b1c2290ecd60e597c34f0f47150e238c00989b491c1b0ee49235e6dc518697e9` | 102 |
| `r2_continuation_v4_atr45` | `run_a1_r2_continuation_short_v4_volatility_gate_exact.py` | `r2_impulse_body45_atr45` | `4643f786ef326c314dd26f9102c99b8ab2f902d3689772140fc396b99f1ef635` | 121 |

The runner imports each source's `build_variants()` and selects the named variant. It
does not copy, merge, or override a tester-input dictionary. Input-hash drift is a hard
failure before MT5 starts.

## Exact tester boundary

- Symbol/timeframe/EA: the existing common exact runner and
  `A1XauM5MomentumContinuationExecutor.mq5`.
- Window: `2016.01.01` through `2021.12.31`.
- Tester account: `1000 USD`, matching every authoritative source run.
- Exactly one common compile and the five variants above.
- The EA source and every authoritative source runner are hashed before the run and
  must be unchanged afterward.

## Publication and reconciliation

The five expected normalized filenames are published only when all five controls pass:

1. `ORDER_SEND_OK == MT5 Total Trades`.
2. MT5 trades equal summary trades, raw trade-CSV rows, and normalized rows.
3. Order-send failure counts reconcile and every failure is described.
4. Every normalized position is closed, short, and entered inside the frozen window.
5. The selected tester-input hash still equals its preregistered hash.

Each ledger includes row-level source-runner, variant, input-hash, EA-hash, window, and
manifest-path provenance. The atomic JSON manifest is
`A1_XAU_R2_CONTROL_PREHISTORY_201601_202112_PROVENANCE.json`; it records the source
runner/variant, full frozen inputs, EA source and compiled hashes, all MT5 artifact
paths, normalized-ledger hashes, and the complete reconciliation result.

## Commands

Locked static readiness check:

```powershell
uv run --python 3.12 python xau-usd/xauusd-phase1/scripts/run_a1_r2_mode27_prehistory_overlap_controls_exact.py --static-only
```

Historical command after explicit authorization changes the source lock:

```powershell
uv run --python 3.12 python xau-usd/xauusd-phase1/scripts/run_a1_r2_mode27_prehistory_overlap_controls_exact.py --variant-timeout-seconds 1200
```
