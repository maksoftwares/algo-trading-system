# A3 ML Signal Grouping Contract V1

Status: PRELOCK_CONTRACT

This contract owns exact IDs, fuzzy setup grouping, group integrity, and sensitivity diagnostics.

## Exact Signal ID

Create exact_signal_id from:

- account_scope;
- symbol;
- base_family;
- direction;
- level_kind;
- normalized_level_price;
- break_bar_time_utc;
- retest_bar_time_utc;
- confirmation_bar_time_utc.

Hash the normalized string with SHA256.

## Fuzzy Setup Group

Create setup_group_id after exact deduplication.

Signals are in the same fuzzy setup group when all are true:

- same symbol;
- same base family;
- same direction;
- absolute level-price difference <= 0.10 x earlier-signal M5 ATR14;
- decision timestamps within 10 minutes;
- break/retest windows overlap;
- connected-component span <= 20 minutes.

If the earlier-signal M5 ATR14 is missing, zero, negative, stale, or not causally available, the fuzzy ATR edge is not eligible. The row may still exact-deduplicate, but it must not be fuzzy-merged by substituting zero or a global ATR.

## Algorithm

1. Exact-deduplicate first.
2. Sort chronologically.
3. Build graph edges using the primary fuzzy rule.
4. Find connected components.
5. Split components spanning more than 20 minutes.
6. Select earliest valid decision as canonical row.
7. Aggregate lanes, magics, duplicate count, and source IDs as metadata.
8. Assign setup_group_id.

## Integrity Rules

setup_group_id may not cross train/test boundaries.

Lane, magic, source row IDs, and duplicate count are metadata only. They are never model features.

## Sensitivity Diagnostics

Report mechanics at:

- 0.05 ATR;
- 0.10 ATR primary;
- 0.20 ATR.

Only 0.10 ATR defines the locked dataset.
