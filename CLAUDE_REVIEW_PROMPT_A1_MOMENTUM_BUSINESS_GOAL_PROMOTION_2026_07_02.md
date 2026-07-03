# Claude Review Prompt - A1 Momentum Business-Goal Promotion Decision

Please independently review this promotion decision. The owner has clarified that sparse systems are not acceptable as the primary path. The target is a frequent intraday XAUUSD M5 demo strategy with multiple trades on active days, win rate above 50%, positive PF/net, and enough robustness that it is not just a few lucky trades.

Boundary: offline/repo review only. Do not touch MT5 runtime, charts, presets, orders, or open positions.

Files to inspect:

- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_SCOREBOARD_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_SCOREBOARD_2026_07_02.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_SCOREBOARD_2026_07_02.csv`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_PROMOTION_PACKET_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_PROMOTION_PACKET_2026_07_02.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_CALENDAR_CADENCE_AUDIT_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_CALENDAR_CADENCE_AUDIT_2026_07_02.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_SEARCH_CAUSAL_2026_07_03.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_SEARCH_CAUSAL_2026_07_03.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_SEARCH_CAUSAL_2026_07_03.csv`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_SEARCH_CAUSAL_2026_07_03_BEST_KEPT_DROPPED.csv`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_STRESS_CAUSAL_2026_07_03.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_STRESS_CAUSAL_2026_07_03.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_STRESS_CAUSAL_2026_07_03_TRADES.csv`
- `xau-usd/xauusd-phase1/docs/A1_MOMENTUM_BUSINESS_GOAL_OWNER_AUTHORIZATION_2026_07_02.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_FORWARD_DRAFT_2026_07_02.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_FORWARD_DRAFT_2026_07_02.md.sha256.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_READINESS_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_READINESS_2026_07_02.json`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_FORWARD_DRAFT_2026_07_02.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_FORWARD_DRAFT_2026_07_02.md.sha256.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_READINESS_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_READINESS_2026_07_02.json`
- `xau-usd/xauusd-phase1/scripts/attach_a1_xau_m5_momentum_continuation.py`
- `xau-usd/xauusd-phase1/tests/test_a1_xau_m5_momentum_continuation.py`
- `status_summary.md`

Current recommendation:

| Role | Candidate | Trades | WR | PF | Net | Trades/market day | Trades/active day | 3+ market days | Positive active days |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Primary | `residual_plus75_high_net` | 2231 | 69.48% | 1.54 | +2400.90 USD | 2.15 | 3.90 | 28.08% | 60.66% |
| Fallback | `residual_plus50_10m` | 1823 | 69.17% | 1.53 | +1863.81 USD | 1.75 | 3.19 | 28.08% | 62.94% |

Important cadence caveat: these packages are not sparse like RR2, but they also do not produce 3+ trades on every market day. They are frequent on active days, with quiet days still expected. Please challenge whether that is acceptable for the owner's "multiple trades per day" objective.

After the owner objected that the above +75/+50 packages still do not fully match the original multiple-trades/day vision, Codex generated a stricter market-day coverage search. Your first review rejected the original 2026-07-02 headline as stated because the guard layer likely leaked outcomes. Codex then patched the shared guard helper to `event_time_causal_v2`, where daily PnL targets, cooldowns, loss counts, and state stops only update after a kept trade reaches its exit time. Please verify that this causal correction is faithful.

Current top market-day coverage candidate after the causal rerun:

| Candidate | Daily overlay | Trades | WR | PF | Net | Trades/market day | Trades/active day | 3+ market days | Positive active days | Top100 removed | Top200 removed | Top300 removed |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `residual_plus75_high_net + freq_h1_h4_rr0p7_cost005_block_bad_hours + v6_freq_v4_rr0p7_max2` | `+75 target, 10m loss cooldown`, causal guard | 3714 | 64.27% | 1.29 | +2391.40 USD | 3.57 | 5.02 | 46.35% | 51.49% | +1142.41 USD | +191.20 USD | -629.28 USD |

Stress highlights after causal fix: all 8 half-year buckets and all 16 quarter buckets are positive, top-200 winners removed remains +191.20, but top-300 winners removed is negative, 339 rolling 250-trade windows are negative, and the stress decision is `REVISE_ROBUSTNESS`. Important: this is a review/revise candidate, not an approved runtime replacement. Please stress it for search bias, overlap/duplicate artifacts, runtime parity, guard causality, and whether it genuinely supersedes the simpler +75/+50 choices or should be demoted.

Planned primary runtime if approved:

- A1 only: account `1025742`, `Capital.ComMena-Demo`
- XAUUSD M5 only
- Fixed lot `0.01`
- Magics `932300/932301`
- `+75 USD` package target
- No shared max-trade cap
- `10m` cooldown after package loss
- Existing sparse RR2 lane should be replaced/disarmed only after owner approval

Questions to answer:

1. Recompute the +75 and +50 metrics from source JSON/CSV where possible. Do the scoreboard and promotion packet faithfully represent the evidence?
2. Is `residual_plus75_high_net` genuinely the best match for the owner goal, or does the lower positive-day rate make `residual_plus50_10m` the better demo choice?
3. Is the no shared max-trade cap in +75 acceptable, given the fixed 0.01 lot and cooldown-after-loss, or should the +50 max-6 cap be preferred for first forward test?
4. Does the candidate pass the sparse-strategy veto? The hard minimum is 2 trades/active day; preferred is 3+ trades/active day and at least 50% 3+ trade active days. Also review the stricter calendar cadence audit: +75 is 2.15 trades/market day and 28.08% 3+ market days; +50 is 1.75 trades/market day and 28.08% 3+ market days.
5. Did Codex correctly fix the guard leakage? Recompute or inspect the kept/dropped audit CSV and confirm whether the guard now behaves like a real-time event-state guard rather than using future outcomes.
6. Does the causal market-day coverage portfolio solve the owner's cadence objection enough to become the new primary review candidate, or is it too search-fit/overlapped/fragile to promote?
7. Challenge robustness: top-100/top-200/top-300 removed, older/newer split, month/quarter distribution, positive-day rate, max DD, duplicate-drop rate, rolling 250/500 windows, and source-variant contribution. Is any result too concentrated?
8. Verify attach readiness for the old +75/+50 packet only:
   - +75 magics are `932300/932301`
   - +75 spec SHA256 is `de637fb4be82b0328ea98e8725936a1bf307810a28ab3dc58fcddfe932c4c39a`
   - +50 magics are `932298/932299`
   - +50 spec SHA256 is `1339a7b154bdd04dcd45f5946f91c336f3db9e47c897bc2e81aeba51d7b8ee71`
   - no committed armed preset is introduced
   - current packet does not touch MT5 runtime
9. Review the forward-test pass/kill rules. Are 4 weeks / 150 trades enough for a first read, or should the minimum be stricter?
10. Give a verdict:
   - `APPROVE_PLUS75_FOR_OWNER_AUTHORIZATION`
   - `APPROVE_PLUS50_FOR_OWNER_AUTHORIZATION`
   - `APPROVE_CAUSAL_MARKET_DAY_COVERAGE_FOR_NEW_RUNTIME_SPEC`
   - `APPROVE_WITH_CHANGES`
   - `REVISE`
   - `REJECT`

If approving, provide the exact owner authorization wording and any pre-attach checks you require. If rejecting, say whether to continue the search inside the existing momentum family or start a different entry family.
