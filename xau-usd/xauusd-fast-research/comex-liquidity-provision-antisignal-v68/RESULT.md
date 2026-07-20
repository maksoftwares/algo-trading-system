# COMEX Liquidity-Provision Anti-Signal V68 Result

Date: 2026-07-20
Decision: `V68_DEVELOPMENT_FAIL_TERMINAL`
Authority: historical research only

V68 froze one outcome-independent union of the previously failed V44 and V45
COMEX candidates. It inverted each source direction exactly once, retained the
first candidate per UTC date, and changed no source threshold, session, stop,
target, hold, cost, or risk rule.

The development stage produced 479 selected candidates over 491 eligible full
weekdays. Of those, 475 resolved, for 0.967413 trades per full weekday. The
sample was balanced at 235 longs and 240 shorts, but the economics failed
decisively:

- base net: USD -365.52;
- stress net: USD -402.40;
- base PF: 0.4338;
- stress PF: 0.4006;
- profitable-day share: 29.53%;
- positive-month share: 0%;
- first/second-half stress PF: 0.3804 / 0.4241;
- stress net after removing five winners: USD -425.19;
- closed stress drawdown: USD 410.41; and
- one-sided block-bootstrap p-value: 1.0.

The frequency, sample-size, direction-balance, and maximum-frequency gates
passed. Every economic, stability, significance, and drawdown gate failed.
Validation and exam remain sealed and must never be opened for V68.

This result rejects the hypothesis that the failed V44/V45 continuation
families contain a clean, mechanically recoverable reversal edge. It also
retires threshold, quota, and mirror reuse on these exposed outcomes. V59/V60
remain the accepted immutable control.

Contract SHA-256:
`89385b6604d6012f5ba16bc383a24d3c302a8b2bf122b3feec746738b5b4fca3`

Development audit SHA-256:
`d4ee2fa4363e026aa2479909548b140053117406c39a36dc4aa235f8e0152aa7`
