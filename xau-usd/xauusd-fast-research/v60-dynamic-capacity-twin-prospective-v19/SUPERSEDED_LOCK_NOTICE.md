# Superseded V19 Lock Notice

Contract `564888356ed4c56153c4c903e3bf484f2423a03e5e01479e63bbfe9f85f7601b`
is **superseded and ineligible for evidence**.

It was locked at `2026-08-25T20:54:08.374250Z` and invalidated before the
`2026-08-26T00:00:00Z` boundary. Its only runs contained zero candidates, zero
resolved outcomes, and zero portfolio events. The end-to-end mechanism audit
found that the replay snapshot lacked `evaluation.usd_to_aed`, which would
have failed closed when the guardian evaluated the first candidate.

The original contract, status, and readiness records remain preserved under
filenames beginning with `SUPERSEDED_564888356ed4c561` or
`SUPERSEDED_*_564888356ed4c561`. They must never be merged with evidence from
the corrected operative contract.
