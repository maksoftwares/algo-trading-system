# A3 ML R1 Structural Risk Preregistration

Date: 2026-07-16

## Purpose

Measure whether the frozen Dukascopy R1 baseline can survive exact shared floating-equity, overlap, original-stop-risk, margin, and capital stress. This is Iteration 2 of the demo-readiness program.

The audit uses known historical R1 outcomes. It is portfolio engineering evidence, not new alpha evidence and not an untouched holdout.

## Frozen Source

- Family: `r1_box_clean_strict_uptrend`.
- Source: the 310 selected R1 labels from the completed R1/R2 Dukascopy portability exam.
- Signal, router, stop, target, direction, spread, cost, and holding-stress rules remain unchanged.
- R2 is excluded because Iteration 1 rejected it as a qualified specialist.
- Every source hash and expected reconciliation value is locked in `config/ml/a3_ml_r1_structural_risk_v1.json`.

## Exact Equity Rule

The audit must replay native Dukascopy Bid/Ask ticks only while at least one accepted R1 position is open or an entry/exit event occurs.

- Long positions enter at their recorded ask fill and mark to the current bid.
- Recorded gross exit P/L must reconcile exactly.
- USD 0.30 execution stress is charged at entry.
- USD 0.35 per 24 hours of holding stress accrues continuously while a position is open.
- Floating-equity peaks and troughs use the true chronological tick path, not H1 high/low ordering assumptions.
- Original-stop risk and margin are measured at each admission decision without using future trade outcomes.

## Frozen Profiles

`frozen_r1_baseline` must admit all 310 source trades under the original 32-position ceiling.

`demo_guard_10k` uses:

- USD 10,000 starting balance;
- 50:1 leverage;
- 0.01 fixed lot;
- no more than eight concurrent positions;
- no more than 0.5% initial stop risk per trade;
- no more than 2.0% total and same-direction original-stop risk;
- no more than 20% margin utilization;
- no new entries after 2% realized loss in the server day.

These are standard account-risk limits selected before inspecting the floating-equity result. They are not alpha filters and may not inspect future P/L.

## Frozen Gates

The structural audit passes only if all machine-readable gates pass:

- source trade count and stress net reconcile;
- baseline exact floating-equity drawdown is no more than 15% of USD 10,000;
- controlled stress PF is at least 1.30;
- controlled trade and net retention are each at least 50%;
- controlled exact floating-equity drawdown is no more than 10%;
- the best controlled episode contributes no more than 35% of net;
- controlled net remains positive after removing the top three winning episodes;
- at least 65% of rolling six-month windows are positive;
- episode-block Monte Carlo ruin probability is no more than 1%;
- episode-block probability of exceeding 15% drawdown is no more than 10%;
- every risk and margin admission limit is respected.

Capital observations at USD 1,000, USD 5,000, and USD 10,000 are diagnostics. They may not be used to choose a favorable starting balance after the result.

## Decision Policy

- `STRUCTURAL_RISK_PASS`: R1 may remain a research baseline for the later shared-account and diversification stages. This does not authorize demo execution.
- `STRUCTURAL_RISK_FAIL`: R1 cannot be treated as the demo-ready core. Preserve it only as a research comparator and move specialist development toward a new version or orthogonal regimes.
- A failed gate may not be rescued by changing this contract after outcomes are inspected.

All authorization flags remain false.
