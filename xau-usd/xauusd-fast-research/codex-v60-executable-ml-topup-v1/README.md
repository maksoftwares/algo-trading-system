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
