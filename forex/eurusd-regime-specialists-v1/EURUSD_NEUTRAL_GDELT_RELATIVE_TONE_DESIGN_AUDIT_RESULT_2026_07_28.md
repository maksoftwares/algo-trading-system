# EURUSD Neutral GDELT relative-tone design-audit result

Date: `2026-07-28`

Status: `PASS_SOURCE_ONLY_TRANSFORM_CAPACITY`

The one transform frozen before tone inspection parsed finite tone for all
790 strict documents. Twelve of the 24 sampled dates met the two-source
quorum on both ECB and Fed sides. Six dates exceeded the fixed
MAD-normalized strength threshold, split evenly between three hypothetical
long and three hypothetical short candidates. Every source-only gate passed.

No EURUSD price, return, oracle row, or P&L was loaded. Therefore this is not
evidence that tone predicts EURUSD. It only permitted the exact transform to
be preregistered prospectively before its first source capture.

The prospective expert now uses the same transform without historical
backtesting. It has no frequency quota, risks four pips for a six-pip target,
and remains shadow-only until the frozen 12-month and 30-trade gates pass.

Result SHA-256:
`f61fb06dfbb1683a0df88b2e6081e70307356991c9ef7bbb6f16bf1160698248`.
