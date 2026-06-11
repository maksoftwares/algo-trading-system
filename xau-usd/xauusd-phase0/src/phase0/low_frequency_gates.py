from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import pandas as pd

from phase0.data_contracts import GateResult


@dataclass(frozen=True)
class CostPrecheckResult:
    status: str
    expected_median_stop_points: float
    expected_cost_r: float
    message: str


def normalized_top_trade_r(top_positive_trade_r: float, mean_abs_r: float, n_trades: int) -> float:
    return _normalized_concentration(top_positive_trade_r, mean_abs_r, n_trades)


def normalized_top5_trade_r(top5_positive_sum_r: float, mean_abs_r: float, n_trades: int) -> float:
    return _normalized_concentration(top5_positive_sum_r, mean_abs_r, n_trades)


def structural_cost_precheck(
    expected_median_stop_points: float,
    expected_cost_r_at_measured_spread: float,
    preferred_stop_points: float = 375.0,
    minimum_stop_points: float = 250.0,
    preferred_cost_r: float = 0.15,
    maximum_cost_r: float = 0.30,
) -> CostPrecheckResult:
    stop = float(expected_median_stop_points)
    cost_r = float(expected_cost_r_at_measured_spread)
    if stop < minimum_stop_points or cost_r > maximum_cost_r:
        return CostPrecheckResult(
            status="BLOCKED_COST_FRAGILE_BY_DESIGN",
            expected_median_stop_points=stop,
            expected_cost_r=cost_r,
            message="Expected stop distance or measured-spread cost_R breaches the absolute G9A limit.",
        )
    if stop < preferred_stop_points or cost_r > preferred_cost_r:
        return CostPrecheckResult(
            status="PASS_WITH_COST_CAUTION",
            expected_median_stop_points=stop,
            expected_cost_r=cost_r,
            message="Candidate clears the absolute G9A limit but misses the preferred cost-feasibility band.",
        )
    return CostPrecheckResult(
        status="PASS",
        expected_median_stop_points=stop,
        expected_cost_r=cost_r,
        message="Candidate clears the preferred G9A cost-feasibility band.",
    )


def evaluate_low_frequency_matrix_gates(
    matrix_metrics: pd.DataFrame,
    gates_config: dict[str, Any],
) -> list[GateResult]:
    df = matrix_metrics.copy()
    required = {
        "cell_id",
        "broker",
        "cost_model",
        "profit_factor",
        "trade_count",
        "total_net_r",
        "mean_abs_r",
        "top_positive_trade_r",
        "top5_positive_sum_r",
        "max_drawdown_pct",
        "total_return_pct",
        "max_consecutive_zero_trade_months",
        "realized_median_cost_r",
        "realized_p95_cost_r",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Low-frequency gate metrics missing columns: {', '.join(missing)}")

    total_cells = int(gates_config.get("total_cells", 9))
    min_pf = float(gates_config.get("min_pf_per_passing_cell", 1.30))
    min_pf_cells = int(gates_config.get("min_cells_pf_pass", 7))
    min_trades = int(gates_config.get("min_trades_every_cell", 40))
    max_dd_pct = float(gates_config.get("max_drawdown_pct_every_cell", 30.0))
    min_total_return = float(gates_config.get("min_total_return_pct_every_cell", -25.0))
    max_zero_months = int(gates_config.get("max_consecutive_zero_trade_months", 3))

    n_trades = pd.to_numeric(df["trade_count"], errors="coerce")
    mean_abs_r = pd.to_numeric(df["mean_abs_r"], errors="coerce")
    df["norm_top"] = [
        normalized_top_trade_r(top, mean_abs, int(count))
        for top, mean_abs, count in zip(df["top_positive_trade_r"], mean_abs_r, n_trades)
    ]
    df["norm_top5"] = [
        normalized_top5_trade_r(top5, mean_abs, int(count))
        for top5, mean_abs, count in zip(df["top5_positive_sum_r"], mean_abs_r, n_trades)
    ]

    return [
        _pf_survival(df, min_pf_cells, total_cells, min_pf),
        _sample_size(df, min_trades, total_cells),
        _catastrophic(df, max_dd_pct, min_total_return, total_cells),
        _normalized_concentration_gate(df, total_cells),
        _activity(df, max_zero_months, total_cells),
        _cost_sensitivity(df),
        _cross_venue_floor(df),
        _modern_era_integrity(df),
        _realized_cost_gate(df),
        _decile_placeholder(),
    ]


def _normalized_concentration(value: float, mean_abs_r: float, n_trades: int) -> float:
    if n_trades <= 0 or mean_abs_r <= 0 or math.isnan(mean_abs_r):
        return math.inf
    return float(value) / (float(mean_abs_r) * math.sqrt(float(n_trades)))


def _pf_survival(df: pd.DataFrame, min_cells: int, total_cells: int, min_pf: float) -> GateResult:
    pf = pd.to_numeric(df["profit_factor"], errors="coerce")
    passing = int((pf >= min_pf).sum())
    passed = len(df) >= total_cells and passing >= min_cells
    return GateResult(
        name="G1_pf_survival",
        status="PASS" if passed else "FAIL",
        threshold=f">={min_cells}/{total_cells} cells PF >= {min_pf}",
        observed=f"{passing}/{len(df)} cells",
        message="PF survival passed." if passed else "Too few low-frequency cells reached PF threshold.",
    )


def _sample_size(df: pd.DataFrame, min_trades: int, total_cells: int) -> GateResult:
    trade_count = pd.to_numeric(df["trade_count"], errors="coerce")
    failed = df.loc[trade_count < min_trades, "cell_id"].astype(str).tolist()
    passed = len(df) >= total_cells and not failed
    return GateResult(
        name="G2_sample_size",
        status="PASS" if passed else "FAIL",
        threshold=f"every cell trade_count >= {min_trades}",
        observed="all cells" if not failed else f"failed cells: {', '.join(failed)}",
        message="Sample-size gate passed." if passed else "One or more cells have too few trades.",
    )


def _catastrophic(
    df: pd.DataFrame,
    max_dd_pct: float,
    min_total_return: float,
    total_cells: int,
) -> GateResult:
    dd = pd.to_numeric(df["max_drawdown_pct"], errors="coerce")
    returns = pd.to_numeric(df["total_return_pct"], errors="coerce")
    failed = df.loc[(dd > max_dd_pct) | (returns < min_total_return), "cell_id"].astype(str).tolist()
    passed = len(df) >= total_cells and not failed
    return GateResult(
        name="G3_catastrophic_failure",
        status="PASS" if passed else "FAIL",
        threshold=f"max_drawdown_pct <= {max_dd_pct}; total_return_pct >= {min_total_return}",
        observed="all cells" if not failed else f"failed cells: {', '.join(failed)}",
        message="Catastrophic-failure gate passed." if passed else "One or more cells breached loss limits.",
    )


def _normalized_concentration_gate(df: pd.DataFrame, total_cells: int) -> GateResult:
    net_r = pd.to_numeric(df["total_net_r"], errors="coerce")
    norm_top = pd.to_numeric(df["norm_top"], errors="coerce")
    norm_top5 = pd.to_numeric(df["norm_top5"], errors="coerce")
    failed = df.loc[(net_r <= 0) | (norm_top > 1.0) | (norm_top5 > 2.5), "cell_id"].astype(str).tolist()
    passed = len(df) >= total_cells and not failed
    return GateResult(
        name="G4_low_frequency_concentration",
        status="PASS" if passed else "FAIL",
        threshold="net_R > 0; norm_top <= 1.00; norm_top5 <= 2.50",
        observed="all cells" if not failed else f"failed cells: {', '.join(failed)}",
        message="Frequency-normalized concentration passed."
        if passed
        else "One or more cells are too concentrated or net-negative.",
    )


def _activity(df: pd.DataFrame, max_zero_months: int, total_cells: int) -> GateResult:
    zero_months = pd.to_numeric(df["max_consecutive_zero_trade_months"], errors="coerce")
    failed = df.loc[zero_months > max_zero_months, "cell_id"].astype(str).tolist()
    passed = len(df) >= total_cells and not failed
    return GateResult(
        name="G5_activity",
        status="PASS" if passed else "FAIL",
        threshold=f"max consecutive zero-trade months <= {max_zero_months}",
        observed="all cells" if not failed else f"failed cells: {', '.join(failed)}",
        message="Activity gate passed." if passed else "One or more cells are inactive too long.",
    )


def _cost_sensitivity(df: pd.DataFrame) -> GateResult:
    failures: list[str] = []
    observations: list[str] = []
    for broker, broker_df in df.groupby("broker"):
        best = broker_df.loc[broker_df["cost_model"] == "best_case", "profit_factor"]
        p95 = broker_df.loc[broker_df["cost_model"] == "p95", "profit_factor"]
        if best.empty or p95.empty:
            failures.append(str(broker))
            continue
        best_pf = float(best.iloc[0])
        p95_pf = float(p95.iloc[0])
        ratio = math.inf if best_pf == 0 and p95_pf > 0 else (0.0 if best_pf == 0 else p95_pf / best_pf)
        observations.append(f"{broker}={ratio:.4g}")
        if ratio < 0.50:
            failures.append(str(broker))
    return GateResult(
        name="G6_cost_sensitivity",
        status="PASS" if not failures else "FAIL",
        threshold="P95-cell PF / best-cell PF >= 0.50 per broker",
        observed=", ".join(observations),
        message="Cost sensitivity passed." if not failures else f"Failed brokers: {', '.join(failures)}.",
    )


def _cross_venue_floor(df: pd.DataFrame) -> GateResult:
    failures: list[str] = []
    observations: list[str] = []
    for cost_model, cost_df in df.groupby("cost_model"):
        p = cost_df.loc[cost_df["broker"] == "pepperstone", "profit_factor"]
        d = cost_df.loc[cost_df["broker"] == "dukascopy", "profit_factor"]
        if p.empty or d.empty:
            failures.append(str(cost_model))
            continue
        mean_pf = (float(p.iloc[0]) + float(d.iloc[0])) / 2.0
        observations.append(f"{cost_model}={mean_pf:.4g}")
        if mean_pf < 1.20:
            failures.append(str(cost_model))
    return GateResult(
        name="G7_cross_venue_floor",
        status="PASS" if not failures else "FAIL",
        threshold="mean(Pepperstone PF, Dukascopy PF) >= 1.20 in every cost model",
        observed=", ".join(observations),
        message="Cross-venue floor passed." if not failures else f"Failed cost models: {', '.join(failures)}.",
    )


def _modern_era_integrity(df: pd.DataFrame) -> GateResult:
    if "era_slice" not in df.columns:
        return GateResult(
            name="G8_modern_era_integrity",
            status="PENDING",
            threshold="2022-01-01 to 2025-06-30 median-cost PF >= 1.10 in at least 2 of 3 brokers",
            observed="era_slice column absent",
            message="Modern-era slice must be evaluated from era-slice output.",
        )
    modern = df[(df["era_slice"] == "2022-2025-06-30") & (df["cost_model"] == "median")]
    passing = int((pd.to_numeric(modern["profit_factor"], errors="coerce") >= 1.10).sum())
    return GateResult(
        name="G8_modern_era_integrity",
        status="PASS" if passing >= 2 else "FAIL",
        threshold="median-cost modern-era PF >= 1.10 in at least 2 of 3 brokers",
        observed=f"{passing}/3 brokers",
        message="Modern-era integrity passed." if passing >= 2 else "Modern era did not persist.",
    )


def _realized_cost_gate(df: pd.DataFrame) -> GateResult:
    median_cost = pd.to_numeric(df["realized_median_cost_r"], errors="coerce").median()
    p95_cost = pd.to_numeric(df["realized_p95_cost_r"], errors="coerce").max()
    passed = float(p95_cost) <= 0.30
    preferred = float(median_cost) <= 0.15
    return GateResult(
        name="G9B_realized_measured_cost",
        status="PASS" if passed else "FAIL",
        threshold="realized median cost_R <= 0.15 preferred; realized P95 cost_R <= 0.30 absolute",
        observed=f"median={median_cost:.4g}; p95={p95_cost:.4g}; preferred={preferred}",
        message="Realized measured-cost gate passed." if passed else "Realized P95 cost_R breached 0.30.",
    )


def _decile_placeholder() -> GateResult:
    return GateResult(
        name="G10_decile_persistence",
        status="PENDING",
        threshold="PF > 1.0 in >=8/10 deciles; no decile PF > 2x median",
        observed="requires decile output",
        message="Run full-history decile persistence only after matrix gates pass.",
    )
