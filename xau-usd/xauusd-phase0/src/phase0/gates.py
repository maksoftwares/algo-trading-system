from __future__ import annotations

import math
from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import GateResult
from phase0.metrics import add_cost_sensitivity_ratios


def evaluate_matrix_gates(matrix_metrics: pd.DataFrame, gates_config: dict[str, Any]) -> list[GateResult]:
    df = _require_matrix_columns(matrix_metrics)
    df = add_cost_sensitivity_ratios(df)
    total_cells = int(gates_config["total_cells"])
    min_cells_pf_pass = int(gates_config["min_cells_pf_pass"])
    min_pf = float(gates_config["min_pf_per_passing_cell"])
    min_trades = int(gates_config["min_trades_every_cell"])
    max_dd_pct = float(gates_config["max_drawdown_pct_every_cell"])
    min_total_return = float(gates_config["min_total_return_pct_every_cell"])
    max_largest = float(gates_config["max_largest_trade_pnl_share_pct"])
    max_top5 = float(gates_config["max_top5_trades_pnl_share_pct"])
    max_zero_months = int(gates_config["max_consecutive_zero_trade_months"])
    min_cost_ratio = float(gates_config["min_p95_to_best_pf_ratio"])

    results = [
        _multi_cell_survival(df, min_cells_pf_pass, total_cells, min_pf),
        _sample_size(df, min_trades, total_cells),
        _catastrophic_failure(df, max_dd_pct, min_total_return, total_cells),
        _concentration(df, max_largest, max_top5, total_cells),
        _activity(df, max_zero_months, total_cells),
        _cost_sensitivity(df, min_cost_ratio, min_trades),
    ]
    return results


def evaluate_decile_gate(decile_metrics: pd.DataFrame, gates_config: dict[str, Any]) -> GateResult:
    _require_columns(decile_metrics, ("profit_factor", "trade_count"), "decile metrics")
    min_positive = int(gates_config["decile_min_positive_deciles"])
    min_pf = float(gates_config["decile_min_pf"])
    max_multiple = float(gates_config["decile_max_pf_vs_median_multiple"])
    min_trades = int(gates_config["decile_min_trades"])
    pf = pd.to_numeric(decile_metrics["profit_factor"], errors="coerce")
    trade_count = pd.to_numeric(decile_metrics["trade_count"], errors="coerce")
    median_pf = float(pf.median())
    positive_deciles = int((pf > min_pf).sum())

    failures = []
    if median_pf <= 0 or math.isnan(median_pf):
        failures.append(f"median PF {median_pf} <= 0")
    if positive_deciles < min_positive:
        failures.append(f"{positive_deciles} deciles PF > {min_pf}, need {min_positive}")
    if (pf > max_multiple * median_pf).any():
        failures.append(f"one or more deciles exceed {max_multiple}x median PF")
    if (trade_count < min_trades).any():
        failures.append(f"one or more deciles below {min_trades} trades")

    return GateResult(
        name="decile_persistence",
        status="FAIL" if failures else "PASS",
        threshold=(
            f">={min_positive} deciles PF>{min_pf}; no PF>{max_multiple}x median; "
            f"each decile trades>={min_trades}"
        ),
        observed=f"positive_deciles={positive_deciles}, median_pf={median_pf:.4g}",
        message="; ".join(failures) if failures else "Decile persistence passed.",
    )


def evaluate_multisymbol_gate(
    multisymbol_metrics: pd.DataFrame,
    gates_config: dict[str, Any],
    xau_specific_mechanism: str = "",
) -> GateResult:
    _require_columns(multisymbol_metrics, ("symbol", "profit_factor"), "multisymbol metrics")
    min_pf = float(gates_config["multisymbol_min_pf"])
    by_symbol = {
        str(row["symbol"]).upper(): float(row["profit_factor"])
        for _, row in multisymbol_metrics.iterrows()
    }
    missing_or_failed = [
        symbol for symbol in ("EURUSD", "USDJPY") if by_symbol.get(symbol, float("-inf")) < min_pf
    ]
    if not missing_or_failed:
        status = "PASS"
        message = "EURUSD and USDJPY passed directionality threshold."
    elif xau_specific_mechanism.strip():
        status = "PASS_WITH_XAU_SPECIFIC_JUSTIFICATION"
        message = "Comparison symbols failed, but XAU-specific mechanism was supplied."
    else:
        status = "FAIL"
        message = f"Failed or missing symbols: {', '.join(missing_or_failed)}."

    return GateResult(
        name="multi_symbol_consistency",
        status=status,
        threshold=f"EURUSD PF >= {min_pf} and USDJPY PF >= {min_pf}",
        observed=", ".join(f"{symbol}={pf:.4g}" for symbol, pf in sorted(by_symbol.items())),
        message=message,
    )


def evaluate_adversarial_gate(
    logic_gap_failures_pct: float | None,
    gates_config: dict[str, Any],
    manual_review_complete: bool,
) -> GateResult:
    threshold = float(gates_config["adversarial_max_logic_gap_loser_pct"])
    if not manual_review_complete or logic_gap_failures_pct is None:
        return GateResult(
            name="adversarial_review",
            status="PENDING",
            threshold=f"logic_gap_failures_pct <= {threshold}",
            observed="manual review incomplete",
            message="Manual adversarial review is incomplete.",
        )

    passed = float(logic_gap_failures_pct) <= threshold
    return GateResult(
        name="adversarial_review",
        status="PASS" if passed else "FAIL",
        threshold=f"logic_gap_failures_pct <= {threshold}",
        observed=f"logic_gap_failures_pct={logic_gap_failures_pct}",
        message="Adversarial gate passed." if passed else "Logic-gap failure rate exceeded threshold.",
    )


def gate_results_to_dataframe(results: list[GateResult]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "name": result.name,
                "status": result.status,
                "threshold": result.threshold,
                "observed": result.observed,
                "message": result.message,
            }
            for result in results
        ]
    )


def _multi_cell_survival(
    df: pd.DataFrame,
    min_cells_pf_pass: int,
    total_cells: int,
    min_pf: float,
) -> GateResult:
    passing = int((pd.to_numeric(df["profit_factor"], errors="coerce") >= min_pf).sum())
    complete = len(df) >= total_cells
    passed = complete and passing >= min_cells_pf_pass
    return GateResult(
        name="multi_cell_survival",
        status="PASS" if passed else "FAIL",
        threshold=f">={min_cells_pf_pass}/{total_cells} cells PF >= {min_pf}",
        observed=f"{passing}/{len(df)} cells PF >= {min_pf}",
        message="Multi-cell survival passed." if passed else "Too few profitable cells.",
    )


def _sample_size(df: pd.DataFrame, min_trades: int, total_cells: int) -> GateResult:
    trade_count = pd.to_numeric(df["trade_count"], errors="coerce")
    failed_cells = df.loc[trade_count < min_trades, "cell_id"].astype(str).tolist()
    complete = len(df) >= total_cells
    passed = complete and not failed_cells
    return GateResult(
        name="sample_size",
        status="PASS" if passed else "FAIL",
        threshold=f"trade_count >= {min_trades} in every cell",
        observed=(
            "all cells meet threshold"
            if not failed_cells
            else f"failed cells: {', '.join(failed_cells)}"
        ),
        message="Sample-size gate passed." if passed else "One or more cells have too few trades.",
    )


def _catastrophic_failure(
    df: pd.DataFrame,
    max_dd_pct: float,
    min_total_return: float,
    total_cells: int,
) -> GateResult:
    dd = pd.to_numeric(df["max_drawdown_pct"], errors="coerce")
    returns = pd.to_numeric(df["total_return_pct"], errors="coerce")
    failed = df.loc[(dd > max_dd_pct) | (returns < min_total_return), "cell_id"].astype(str).tolist()
    complete = len(df) >= total_cells
    passed = complete and not failed
    return GateResult(
        name="no_catastrophic_failure",
        status="PASS" if passed else "FAIL",
        threshold=f"max_drawdown_pct <= {max_dd_pct}; total_return_pct >= {min_total_return}",
        observed="all cells meet threshold" if not failed else f"failed cells: {', '.join(failed)}",
        message="Catastrophic-failure gate passed." if passed else "One or more cells breached loss limits.",
    )


def _concentration(
    df: pd.DataFrame,
    max_largest: float,
    max_top5: float,
    total_cells: int,
) -> GateResult:
    largest = pd.to_numeric(df["largest_single_trade_pct_of_pnl"], errors="coerce")
    top5 = pd.to_numeric(df["top5_trades_pct_of_pnl"], errors="coerce")
    failed = df.loc[(largest > max_largest) | (top5 > max_top5), "cell_id"].astype(str).tolist()
    complete = len(df) >= total_cells
    passed = complete and not failed
    return GateResult(
        name="concentration",
        status="PASS" if passed else "FAIL",
        threshold=f"largest <= {max_largest}%; top5 <= {max_top5}%",
        observed="all cells meet threshold" if not failed else f"failed cells: {', '.join(failed)}",
        message="Concentration gate passed." if passed else "Profit is too concentrated.",
    )


def _activity(df: pd.DataFrame, max_zero_months: int, total_cells: int) -> GateResult:
    zero_months = pd.to_numeric(df["max_consecutive_zero_trade_months"], errors="coerce")
    failed = df.loc[zero_months > max_zero_months, "cell_id"].astype(str).tolist()
    complete = len(df) >= total_cells
    passed = complete and not failed
    return GateResult(
        name="activity",
        status="PASS" if passed else "FAIL",
        threshold=f"max_consecutive_zero_trade_months <= {max_zero_months}",
        observed="all cells meet threshold" if not failed else f"failed cells: {', '.join(failed)}",
        message="Activity gate passed." if passed else "One or more cells are inactive too long.",
    )


def _cost_sensitivity(df: pd.DataFrame, min_ratio: float, min_trades: int) -> GateResult:
    failures: list[str] = []
    observations: list[str] = []
    for best_cell, p95_cell in ((1, 3), (4, 6), (7, 9)):
        best_rows = df[df["cell_id"].astype(int) == best_cell]
        p95_rows = df[df["cell_id"].astype(int) == p95_cell]
        if best_rows.empty or p95_rows.empty:
            failures.append(f"missing pair {best_cell}/{p95_cell}")
            continue
        best = best_rows.iloc[0]
        p95 = p95_rows.iloc[0]
        best_pf = float(best["profit_factor"])
        p95_pf = float(p95["profit_factor"])
        p95_trades = int(p95["trade_count"])
        if math.isinf(best_pf):
            passed = math.isinf(p95_pf) and p95_trades >= min_trades
            ratio_text = "inf/inf" if math.isinf(p95_pf) else f"{p95_pf}/inf"
        else:
            ratio = 0.0 if best_pf == 0 else p95_pf / best_pf
            passed = ratio >= min_ratio
            ratio_text = f"{ratio:.4g}"
        observations.append(f"{best_cell}/{p95_cell}={ratio_text}")
        if not passed:
            failures.append(f"pair {best_cell}/{p95_cell}")

    return GateResult(
        name="cost_sensitivity",
        status="FAIL" if failures else "PASS",
        threshold=f"p95_pf / best_case_pf >= {min_ratio} for pairs 1/3, 4/6, 7/9",
        observed="; ".join(observations),
        message="Cost-sensitivity gate passed." if not failures else f"Failed pairs: {', '.join(failures)}.",
    )


def _require_matrix_columns(matrix_metrics: pd.DataFrame) -> pd.DataFrame:
    required = (
        "cell_id",
        "profit_factor",
        "trade_count",
        "max_drawdown_pct",
        "total_return_pct",
        "largest_single_trade_pct_of_pnl",
        "top5_trades_pct_of_pnl",
        "max_consecutive_zero_trade_months",
    )
    _require_columns(matrix_metrics, required, "matrix metrics")
    return matrix_metrics.copy()


def _require_columns(df: pd.DataFrame, columns: tuple[str, ...], name: str) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ConfigError(f"{name} missing required column(s): {', '.join(missing)}.")
