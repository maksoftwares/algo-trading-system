# Codex V60 Executable ML Top-Up V1

This offline lane tests whether a causal, source-aware ML model can improve the
deterministic V60 portfolio using only broker-expressible lots.

The base policy remains unchanged: every accepted V60 trade receives `0.01`
lots. ML may only propose an additional `0.01` lots for a high-confidence
candidate. The existing source, account, directional, add-on, and concurrency
risk limits can reject that proposal.

This lane cannot authorize ML shadow consumption, demo orders, live orders, EA
changes, account changes, or MT5 runtime changes. See `PREREGISTRATION.md` and
`config/EXECUTABLE_TOPUP_CONTRACT.json`.

## Result

V1 is rejected and quarantined.

- It used zero incomplete M5 bars and skipped zero baseline trades.
- It proposed 174 top-ups and the existing risk limits accepted 135.
- Net changed from `$5,045.67` to `$5,047.13`, but PF fell from `1.721` to
  `1.681` and floating drawdown rose from `$335.34` to `$383.77`.
- The weekly-block one-sided 95% lower delta bound was `-$136.47`.
- The accepted top-ups themselves had PF `1.004`, showing no reliable
  executable selection edge.
- No MT5 or runtime setting was changed.

See `outputs/RESULT.md` and `outputs/RESULT.json`.
