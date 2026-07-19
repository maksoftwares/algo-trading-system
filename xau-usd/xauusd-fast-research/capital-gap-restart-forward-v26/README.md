# Capital Gap-Restart Forward V26

V26 is one forward-only XAUUSD quote hypothesis. It targets directional quote
flow immediately after a two-to-five-second silence, a state excluded by V24.1's
continuous-burst rule. The candidate clock was calibrated on 2026-07-17 using
only source structure and causal candidate timestamps. The full calibration file
was loaded to enumerate events, but no post-candidate price was used to label or
economically evaluate a candidate.

The first 20 complete Capital weekdays after 2026-07-20 form validation. The
next 20 form confirmation and remain sealed until validation passes unchanged.
V26 adds a five-weekday circular block-bootstrap test at a Bonferroni-adjusted
2.5% one-sided level because V24.1 and V26 are two registered hypotheses sharing
the forward evidence stream. V24.1 must satisfy the same external admission
recheck before either candidate can be selected from this family.

Nothing in this package authorizes model training, Python predictions, EA
consumption, demo trading, live trading, or broker action.
