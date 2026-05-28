# Phase 3 Family De-Duplication Audit

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: REVIEW_READY

## Summary

| Field | Value |
| --- | --- |
| Safe source rows | 116 |
| Family groups | 65 |
| Multi-row groups | 51 |

## Classification Counts

| Field | Value |
| --- | --- |
| SAME_BAR_DISTINCT_LEVEL | 1 |
| TRUE_DUPLICATE | 64 |

## Multi-Row Groups

| family_event_id | bar_time | group_size | classification | differing_fields | observers | directions | level_kinds | level_prices | entry_prices | stop_losses | take_profits | stop_distance_points |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FAM00001 | 2026.05.22 11:25:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4514.67 | 4511.74 | 4516.09 | 4505.22 | 434.91 |
| FAM00002 | 2026.05.22 11:50:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4517.11 | 4522.94 | 4516.58 | 4532.47 | 635.57 |
| FAM00003 | 2026.05.22 12:45:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4517.11 | 4518.58 | 4514.30 | 4525.01 | 428.49 |
| FAM00004 | 2026.05.22 12:50:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4517.11 | 4519.58 | 4515.40 | 4525.85 | 417.78 |
| FAM00005 | 2026.05.22 14:05:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4514.87 | 4511.45 | 4517.35 | 4502.59 | 590.46 |
| FAM00006 | 2026.05.25 05:50:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4559.47 | 4555.14 | 4561.13 | 4546.16 | 598.55 |
| FAM00007 | 2026.05.25 07:40:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4559.47 | 4553.95 | 4562.05 | 4541.80 | 810.11 |
| FAM00008 | 2026.05.25 12:50:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4567.36 | 4566.19 | 4569.52 | 4561.19 | 333.04 |
| FAM00009 | 2026.05.25 13:20:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4567.36 | 4562.45 | 4568.88 | 4552.81 | 642.90 |
| FAM00010 | 2026.05.25 15:05:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4565.43 | 4566.87 | 4564.95 | 4569.75 | 191.81 |
| FAM00011 | 2026.05.25 15:15:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4565.43 | 4568.04 | 4565.21 | 4572.29 | 283.09 |
| FAM00012 | 2026.05.25 16:45:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4570.39 | 4571.01 | 4569.24 | 4573.67 | 177.04 |
| FAM00013 | 2026.05.25 16:50:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4570.39 | 4572.27 | 4569.98 | 4575.71 | 229.12 |
| FAM00014 | 2026.05.25 22:20:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4572.59 | 4574.04 | 4571.76 | 4577.46 | 228.11 |
| FAM00015 | 2026.05.25 22:45:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4571.28 | 4573.37 | 4569.19 | 4579.63 | 417.54 |
| FAM00017 | 2026.05.26 05:50:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4529.75 | 4527.70 | 4533.13 | 4519.56 | 542.99 |
| FAM00018 | 2026.05.26 07:40:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4528.04 | 4522.83 | 4530.14 | 4511.87 | 730.56 |
| FAM00019 | 2026.05.26 08:30:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4528.04 | 4525.98 | 4530.32 | 4519.46 | 434.44 |
| FAM00020 | 2026.05.26 12:00:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4511.97 | 4510.47 | 4516.04 | 4502.11 | 557.44 |
| FAM00021 | 2026.05.26 12:15:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4511.97 | 4506.21 | 4512.59 | 4496.64 | 637.74 |
| FAM00022 | 2026.05.26 12:30:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4511.97 | 4507.95 | 4513.28 | 4499.96 | 532.66 |
| FAM00023 | 2026.05.26 13:20:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4515.76 | 4522.42 | 4515.02 | 4533.53 | 740.49 |
| FAM00024 | 2026.05.26 14:15:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4515.71 | 4514.70 | 4520.85 | 4505.48 | 614.72 |
| FAM00025 | 2026.05.26 14:30:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4515.76 | 4517.25 | 4511.57 | 4525.76 | 567.58 |
| FAM00026 | 2026.05.26 15:00:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4515.71 | 4515.46 | 4519.95 | 4508.73 | 448.53 |
| FAM00027 | 2026.05.26 15:05:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4515.71 | 4512.45 | 4516.62 | 4506.19 | 417.23 |
| FAM00028 | 2026.05.26 15:35:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4507.59 | 4504.70 | 4508.69 | 4498.72 | 398.52 |
| FAM00029 | 2026.05.26 16:05:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4507.59 | 4505.95 | 4509.94 | 4499.96 | 399.46 |
| FAM00030 | 2026.05.26 16:10:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4507.59 | 4505.20 | 4508.77 | 4499.85 | 356.91 |
| FAM00031 | 2026.05.26 16:50:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4507.59 | 4505.97 | 4509.09 | 4501.29 | 312.02 |
| FAM00032 | 2026.05.26 22:20:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4504.51 | 4510.11 | 4500.06 | 4525.19 | 1005.34 |
| FAM00033 | 2026.05.27 01:15:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4513.55 | 4517.33 | 4512.05 | 4525.26 | 528.50 |
| FAM00034 | 2026.05.27 06:05:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4497.68 | 4496.22 | 4500.36 | 4490.01 | 413.76 |
| FAM00036 | 2026.05.27 08:45:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4489.04 | 4492.69 | 4487.80 | 4500.02 | 488.54 |
| FAM00037 | 2026.05.27 09:15:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4489.04 | 4492.27 | 4488.02 | 4498.64 | 424.54 |
| FAM00038 | 2026.05.27 09:40:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4489.04 | 4490.62 | 4486.31 | 4497.08 | 430.64 |
| FAM00039 | 2026.05.27 09:55:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4489.04 | 4489.79 | 4487.67 | 4492.97 | 211.67 |
| FAM00040 | 2026.05.27 11:55:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4442.48 | 4438.79 | 4445.41 | 4428.86 | 662.26 |
| FAM00042 | 2026.05.27 15:50:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4435.37 | 4432.76 | 4441.56 | 4419.55 | 880.43 |
| FAM00043 | 2026.05.27 17:20:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4441.36 | 4445.62 | 4440.92 | 4452.66 | 469.56 |
| FAM00052 | 2026.05.28 01:10:00 | 2 | SAME_BAR_DISTINCT_LEVEL | observer;level_kind;level_price | breakout_retest;swing_breakout_retest_v0 | SHORT | previous_weekly_low;latest_swing_low | 4453.16;4455.11 | 4445.47 | 4459.17 | 4424.92 | 1370.29 |
| FAM00053 | 2026.05.28 03:20:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4396.23 | 4391.51 | 4397.86 | 4381.99 | 634.91 |
| FAM00054 | 2026.05.28 05:40:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4375.03 | 4387.50 | 4374.37 | 4407.20 | 1313.46 |
| FAM00055 | 2026.05.28 06:20:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4375.03 | 4381.41 | 4373.91 | 4392.66 | 749.79 |
| FAM00056 | 2026.05.28 06:25:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4375.03 | 4380.16 | 4373.43 | 4390.25 | 672.74 |
| FAM00057 | 2026.05.28 08:00:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | LONG | latest_swing_high | 4385.30 | 4389.19 | 4382.19 | 4399.69 | 700.14 |
| FAM00061 | 2026.05.28 11:25:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4389.67 | 4386.49 | 4390.90 | 4379.88 | 440.67 |
| FAM00062 | 2026.05.28 11:30:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4389.67 | 4385.45 | 4390.50 | 4377.88 | 504.76 |
| FAM00063 | 2026.05.28 11:45:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4389.67 | 4385.69 | 4390.52 | 4378.45 | 482.78 |
| FAM00064 | 2026.05.28 11:50:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4389.67 | 4384.90 | 4390.74 | 4376.13 | 584.41 |
| FAM00065 | 2026.05.28 12:25:00 | 2 | TRUE_DUPLICATE | observer | breakout_retest;swing_breakout_retest_v0 | SHORT | latest_swing_low | 4389.67 | 4387.42 | 4393.17 | 4378.79 | 575.40 |

## Scope

This audit does not change execution eligibility. It only identifies whether the current same-bar family grouping is collapsing true duplicates, conflicts, or potentially distinct same-bar opportunities.
