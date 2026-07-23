# EURUSD Phase-0 Evidence Audit

Status: `WORKING_RESEARCH_STRATEGY_FORWARD_NOT_AUTHORIZED`

This is a working research baseline, not deployment authority.

## Exact MT5 evidence

| Metric | Value |
|---|---:|
| Period | 2022.07.01 to 2026.07.02 |
| History quality | 99% |
| Trades | 831 |
| Win rate | 59.33% |
| MT5 net | $101.82 |
| MT5 profit factor | 1.20 |
| MT5 maximal equity drawdown | 30.85 (2.95%) |
| Order-send failures | 3 |

## Parsed trade diagnostics

The trade CSV `profit` field excludes some account-level costs represented in
the MT5 report. It is used for concentration/path diagnostics, not as a
replacement for MT5 total net profit.

| Metric | Value |
|---|---:|
| Trade rows | 831 |
| Parsed price-profit net | $114.80 |
| MT5 net less parsed price-profit | $-12.98 |
| Parsed PF | 1.2325 |
| Parsed maximum closed drawdown | $27.85 |
| Top-10 winners removed net | $80.99 |
| Positive/active months | 34 / 49 |
| Worst 250-trade net | $-3.62 |

## Calendar-year parsed net

| Year | USD |
|---|---:|
| 2022 | 25.00 |
| 2023 | 22.67 |
| 2024 | 13.20 |
| 2025 | 42.32 |
| 2026 | 11.61 |

## Working-research gates

- [x] `actual_mt5_strategy_tester`
- [x] `minimum_trades`
- [x] `minimum_mt5_profit_factor`
- [x] `positive_mt5_net`
- [x] `maximum_mt5_equity_drawdown`
- [x] `positive_both_chronological_splits`
- [x] `positive_top10_removed`
- [x] `source_hash_match`
- [x] `ex5_hash_match`
- [x] `zero_warning_compile`
- [x] `exact_trade_ledger_parity`
- [x] `tester_only_guard`
- [x] `completed_bar_signal`
- [x] `preset_research_identity`

## Promotion blockers

- The selected entry-hour mask is retrospective development evidence.
- No locked prospective shadow sample exists.
- Repository Capital.com bar exports are not current or promotion-grade Bid/Ask evidence.
- No combined XAUUSD/EURUSD shared-risk or USD-factor exposure test exists.

## Decision

The candidate is executable and historically profitable in actual MT5, so it
is a valid working EURUSD research strategy. Its edge is thin and selected
after historical inspection. Freeze it here; do not add another hour, indicator,
or threshold filter. The exact-MT5 parity rerun is hash-attested and reproduced
the inherited trade ledger byte-for-byte. The next valid evidence is prospective
shadow collection on refreshed broker data.
