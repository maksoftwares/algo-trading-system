from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from phase0.config import ConfigError, ProjectConfig, resolve_symbol
from phase0.fixed_notional import (
    _add_cost_r_fields,
    _load_trade_frame,
    _matrix_metadata,
    _matrix_trade_files,
    _point_size_for_symbol,
    _summarize_frame,
)


@dataclass(frozen=True)
class MeasuredCostRevalidationOutput:
    status: str
    report_path: Path
    summary_path: Path
    expert: str
    passing_cells: int
    required_passing_cells: int
    trade_count: int


def generate_measured_cost_revalidation(
    config: ProjectConfig,
    expert: str = "breakout_retest",
    fixed_risk_usd: float | None = None,
) -> MeasuredCostRevalidationOutput:
    if fixed_risk_usd is None:
        project = config.phase0["project"]
        fixed_risk_usd = float(project["starting_equity_usd"]) * float(project["phase0_risk_per_trade_pct"])

    reports_dir = config.root / "outputs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"{expert.upper()}_MEASURED_COST_REVALIDATION.md"
    if expert == "breakout_retest":
        report_path = reports_dir / "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md"
    summary_path = reports_dir / f"{expert}_measured_cost_revalidation_summary.csv"

    measured_status = _read_measured_report_status(reports_dir / "MEASURED_COST_MODEL.md")
    measured_path = reports_dir / "cost_model_measured.csv"
    if measured_status != "PASS" or not measured_path.exists():
        reason = (
            f"Measured cost model status is {measured_status or 'MISSING'}; "
            f"expected PASS and `{measured_path}`."
        )
        summary_path.write_text("status,reason\nPENDING,\"" + reason.replace('"', "'") + "\"\n", encoding="utf-8")
        report_path.write_text(_render_pending_report(reason), encoding="utf-8")
        return MeasuredCostRevalidationOutput("PENDING", report_path, summary_path, expert, 0, _required_cells(config), 0)

    measured = _read_measured_cost_model(config, measured_path)
    trade_files = _matrix_trade_files(config, expert)
    if not trade_files:
        raise ConfigError(f"No matrix trade ledgers found for expert {expert!r}.")

    rows: list[dict[str, Any]] = []
    adjusted_frames: list[pd.DataFrame] = []
    for path in trade_files:
        frame = _load_trade_frame(path)
        frame = _add_cost_r_fields(frame)
        metadata = _matrix_metadata(path)
        adjusted = _apply_measured_p95_costs(config, measured, frame, metadata)
        rows.append(_summarize_frame(adjusted, fixed_risk_usd, metadata))
        adjusted_frames.append(adjusted)

    overall = _summarize_frame(
        pd.concat(adjusted_frames, ignore_index=True),
        fixed_risk_usd,
        {"cell_id": "ALL", "broker": "ALL", "cost_model": "MEASURED_P95", "symbol": "XAUUSD"},
    )
    required_cells = _required_cells(config)
    pf_threshold = float(config.phase0["gates"]["min_pf_per_passing_cell"])
    min_trades = int(config.phase0["gates"]["min_trades_every_cell"])
    passing_cells = sum(
        1 for row in rows if row["profit_factor"] >= pf_threshold and row["trade_count"] >= min_trades
    )
    status = "PASS" if passing_cells >= required_cells and overall["profit_factor"] > 1.0 else "FAIL"

    summary = pd.DataFrame([overall, *rows])
    summary.to_csv(summary_path, index=False)
    report_path.write_text(
        _render_revalidation_report(status, overall, rows, passing_cells, required_cells, pf_threshold, min_trades),
        encoding="utf-8",
    )
    return MeasuredCostRevalidationOutput(
        status=status,
        report_path=report_path,
        summary_path=summary_path,
        expert=expert,
        passing_cells=passing_cells,
        required_passing_cells=required_cells,
        trade_count=int(overall["trade_count"]),
    )


def _apply_measured_p95_costs(
    config: ProjectConfig,
    measured: pd.DataFrame,
    frame: pd.DataFrame,
    metadata: dict[str, Any],
) -> pd.DataFrame:
    adjusted = frame.copy()
    broker = str(metadata.get("broker") or "")
    symbol = str(metadata.get("symbol") or "XAUUSD")
    point_size = _point_size_for_symbol(adjusted)
    risk_price = (adjusted["entry_price"] - adjusted["stop_loss"]).abs().replace(0, pd.NA)
    measured_spreads = [
        _lookup_measured_spread(config, measured, symbol, broker, timestamp)
        for timestamp in adjusted["entry_time_utc"]
    ]
    adjusted["measured_p95_spread_points"] = measured_spreads
    adjusted["measured_entry_spread_R"] = (
        adjusted["measured_p95_spread_points"].fillna(0.0) * point_size / risk_price
    ).fillna(0.0)
    adjusted["all_in_cost_R"] = (
        adjusted["all_in_cost_R"] - adjusted["entry_spread_R"] + adjusted["measured_entry_spread_R"]
    ).clip(lower=0.0)
    adjusted["net_R"] = adjusted["net_R"] + adjusted["entry_spread_R"] - adjusted["measured_entry_spread_R"]
    adjusted["gross_expectancy_proxy_R"] = adjusted["net_R"] + adjusted["all_in_cost_R"]
    return adjusted


def _lookup_measured_spread(
    config: ProjectConfig,
    measured: pd.DataFrame,
    symbol: str,
    broker: str,
    timestamp: pd.Timestamp,
) -> float:
    canonical_symbol = resolve_symbol(config, symbol)
    timestamp = pd.Timestamp(timestamp)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_convert("UTC")
    candidates: list[tuple[str, str]] = [
        ("hour_utc", str(int(timestamp.hour))),
        ("day_of_week_utc", timestamp.day_name()),
        ("global", "all"),
    ]
    for scope, bucket in candidates:
        rows = measured[
            (measured["scope"].astype(str) == scope)
            & (measured["bucket"].astype(str) == bucket)
            & measured["symbol"].astype(str).apply(lambda value: _matches_csv_value(value, canonical_symbol))
        ]
        if rows.empty:
            continue
        if "broker" in rows.columns:
            rows = rows[
                rows["broker"].astype(str).apply(lambda value: value == "all" or _matches_csv_value(value, broker))
            ]
        if rows.empty:
            continue
        value = pd.to_numeric(rows.iloc[0]["p95_spread_points"], errors="coerce")
        if pd.notna(value):
            return float(value)
    raise ConfigError(f"No measured P95 spread found for {symbol} / {broker} at {timestamp}.")


def _read_measured_cost_model(config: ProjectConfig, path: Path) -> pd.DataFrame:
    measured = pd.read_csv(path)
    required = {"scope", "bucket", "symbol", "p95_spread_points"}
    missing = sorted(required - set(measured.columns))
    if missing:
        raise ConfigError(f"Measured cost model {path} missing column(s): {', '.join(missing)}.")
    measured["p95_spread_points"] = pd.to_numeric(measured["p95_spread_points"], errors="coerce")
    measured = measured.dropna(subset=["p95_spread_points"])
    if measured.empty:
        raise ConfigError(f"Measured cost model {path} has no usable P95 spread rows.")
    for symbol in measured["symbol"].astype(str).unique():
        for part in str(symbol).split(","):
            if part.strip():
                resolve_symbol(config, part.strip())
    return measured


def _read_measured_report_status(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Overall status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _required_cells(config: ProjectConfig) -> int:
    return int(config.phase0["gates"]["min_cells_pf_pass"])


def _matches_csv_value(csv_value: str, wanted: str) -> bool:
    wanted_normalized = wanted.strip().upper()
    values = {part.strip().upper() for part in str(csv_value).split(",") if part.strip()}
    return wanted_normalized in values


def _render_pending_report(reason: str) -> str:
    return "\n".join(
        [
            "# Breakout Retest Measured-Cost Revalidation",
            "",
            "Overall status: PENDING",
            "",
            "## Decision",
            "",
            "Measured-cost revalidation cannot be completed yet. Keep Phase 2 readiness pending.",
            "",
            "## Reason",
            "",
            reason,
            "",
        ]
    )


def _render_revalidation_report(
    status: str,
    overall: dict[str, Any],
    rows: list[dict[str, Any]],
    passing_cells: int,
    required_cells: int,
    pf_threshold: float,
    min_trades: int,
) -> str:
    return "\n".join(
        [
            "# Breakout Retest Measured-Cost Revalidation",
            "",
            f"Overall status: {status}",
            "",
            "## Decision",
            "",
            _decision_text(status),
            "",
            "## Gate",
            "",
            f"- Required passing cells: {required_cells}",
            f"- Observed passing cells: {passing_cells}",
            f"- Cell PF threshold: {pf_threshold:.2f}",
            f"- Minimum trades per cell: {min_trades}",
            "",
            "## Overall",
            "",
            _markdown_table([_display_row(overall)]),
            "",
            "## Cells",
            "",
            _markdown_table([_display_row(row) for row in rows]),
            "",
            "## Boundary",
            "",
            "This report applies measured P95 spread cost to the existing fixed-risk trade ledger. It does not authorize Phase 2 by itself.",
            "",
        ]
    )


def _decision_text(status: str) -> str:
    if status == "PASS":
        return "Measured P95 spread costs do not invalidate the current breakout-retest evidence package."
    return "Measured P95 spread costs invalidate or materially weaken the current breakout-retest evidence package."


def _display_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "Cell": str(row["cell_id"]),
        "Broker": str(row["broker"]),
        "Trades": str(row["trade_count"]),
        "PF": _fmt(row["profit_factor"]),
        "Net R": _fmt(row["net_expectancy_R"]),
        "Cost R": _fmt(row["mean_all_in_cost_R"]),
        "Cost %": _fmt(row["cost_edge_consumption_pct"]),
        "Fixed PnL": f"{float(row['fixed_notional_total_pnl_usd']):.2f}",
        "Fixed Max DD": f"{float(row['fixed_notional_max_dd_usd']):.2f}",
    }


def _markdown_table(rows: list[dict[str, str]]) -> str:
    columns = ["Cell", "Broker", "Trades", "PF", "Net R", "Cost R", "Cost %", "Fixed PnL", "Fixed Max DD"]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row.get(column, "") for column in columns) + " |")
    return "\n".join(lines)


def _fmt(value: object) -> str:
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return str(value)
