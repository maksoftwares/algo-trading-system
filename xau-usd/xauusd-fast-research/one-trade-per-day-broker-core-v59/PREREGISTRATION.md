# V59 Broker-Expressible Core Repair

## Known defect

V58 correctly repairs native R1 positions, but the frozen R5 Transition router
counts trades whose recorded economics use `risk_weight < 1.0`. On a broker with
a 0.01 minimum lot and 0.01 lot step, those sub-minimum positions are not
executable as recorded.

## Frozen repair

- Join every V58 R5 Core row to router attempt `27135` by `candidate_id`.
- Keep only rows with `risk_weight == 1.0` within absolute tolerance `1e-12`.
- Reject, rather than round up, every fractional row.
- Keep every non-R5 Core row unchanged.
- Replay the frozen V57 add-on candidates through the unchanged V57/V58 causal
  account governor.
- Retain all V57/V58 windows, gates, and account thresholds.

The structural source audit established 330 R5 rows: 10 full-lot rows and 320
fractional rows. No P/L outcome is used to select among them.

## Terminal decision

V59 passes only if every inherited required-window gate passes. Failure is
terminal for V59; no same-version threshold change or fractional rounding is
allowed.

This package remains historical research. Complete fee stress, whole-account
floating equity, prospective shadow, and MT5 portfolio parity remain required.
No Python serving, EA, demo, live, or broker action is authorized.
