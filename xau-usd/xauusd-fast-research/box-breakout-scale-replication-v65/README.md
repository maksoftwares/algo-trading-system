# Box-Breakout Scale Replication V65

V65 tests whether the proven higher-timeframe box mechanism survives mechanical
translation to H4/H1 and H1/M15 while preserving broker-side cost and causal
execution assumptions.

## Result

The sealed pre-final census evaluated all 256 registered variants and produced
zero survivors. No final-year prices or outcomes were loaded for selection.

- The best H4/H1 long minimum-window stressed PF was `1.013`. Its three window
  PF values were `1.013`, `1.085`, and `1.465`, but development-1 average return,
  winner-removal, and positive-month gates failed.
- The best H4/H1 short minimum-window stressed PF was `0.870`.
- The best H1/M15 long and short minimum-window stressed PF values were `0.698`
  and `0.639`. The lower-timeframe translation increased event frequency but
  did not preserve edge after executable spread and stress costs.
- Decision: `V65_NO_PREFINAL_SURVIVOR`. The scaled box-breakout family is
  retired and the frozen V59/V60 control is unchanged.

Result SHA-256:
`49789c525c96189cd0fcf9772eda9be5544e64a398c5409d0c7f6608c4ed76cf`.
Metrics SHA-256:
`c15090cdb709650a435ca31d23dd008eac11dd9fd223584ecc6bd458df1dd646`.
