# EURUSD Neutral GDELT coverage-census preregistration

Date: `2026-07-28`

Status: `FROZEN_BEFORE_MULTI_DATE_DOWNLOAD_AND_BEFORE_EURUSD_OUTCOMES`

The single GDELT schema sample is technically valid but semantically
asymmetric. This bounded census asks only whether strict ECB and Federal
Reserve news coverage is sufficiently complete and balanced to justify a
later causal hypothesis. It does not create a direction, entry, threshold,
or trade.

## Frozen dates and files

The sample is the first and third Tuesday of every UTC month from August 2025
through July 2026: 24 explicitly listed entry dates. For each entry date the
census requests only the four prior-date GKG batches at 23:00, 23:15, 23:30,
and 23:45 UTC, for exactly 96 target files.

This deterministic sample avoids selecting news-heavy or profitable days.
The hypothetical earliest strategy clock is 00:15 UTC, leaving 30 minutes
after the last source-batch timestamp. Historical archive timestamps can
measure coverage but cannot prove real publication latency; any later
strategy must record prospective local and provider observation times.

## Strict source-only measurements

Every retained archive must contain one strict-UTF-8 member with 27 tab-
separated fields per row. Raw archives, request metadata, and normalized
census rows must be hashed. Missing files remain missing.

An ECB or Fed article requires both:

1. a central-bank or monetary-policy GKG theme; and
2. an explicit ECB/European Central Bank or Fed/Federal Reserve organization
   name.

Documents are deduplicated by their GKG document identifier. The census
reports source concentration separately for both sides.

## Frozen capacity gates

The source may proceed only if:

- at least 95% of 96 files succeed;
- at least 20 of 24 entry dates have all four batches;
- at least 12 dates contain both a strict ECB and strict Fed article;
- both sides have at least 24 total strict articles and ten unique sources;
- no source supplies more than 50% of either side; and
- duplicate document share is no more than 25%.

Failure closes this source lane without inventing a looser keyword or
direction rule. Passing permits only a separately preregistered prospective
capture and signal design.

EURUSD prices, returns, oracle rows, and P&L are forbidden from the census.
No threshold may change after download and no broker action is authorized.
