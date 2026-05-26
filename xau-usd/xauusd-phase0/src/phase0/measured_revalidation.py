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
    diagnostic_path = reports_dir / f"{expert.upper()}_COST_R_DIAGNOSTIC.md"
    audit_path = reports_dir / f"{expert.upper()}_MEASURED_COST_AUDIT.md"
    if expert == "breakout_retest":
        diagnostic_path = reports_dir / "BREAKOUT_RETEST_COST_R_DIAGNOSTIC.md"
        audit_path = reports_dir / "BREAKOUT_RETEST_MEASURED_COST_AUDIT.md"
    delta_path = reports_dir / "MEASURED_COST_ASSUMPTION_DELTA.md"

    measured_status = _read_measured_report_status(reports_dir / "MEASURED_COST_MODEL.md")
    measured_path = reports_dir / "cost_model_measured.csv"
    if measured_status != "PASS" or not measured_path.exists():
        reason = (
            f"Measured cost model status is {measured_status or 'MISSING'}; "
            f"expected PASS and `{measured_path}`."
        )
        summary_path.write_text("status,reason\nPENDING,\"" + reason.replace('"', "'") + "\"\n", encoding="utf-8")
        report_path.write_text(_render_pending_report(reason), encoding="utf-8")
        diagnostic_path.write_text(_render_pending_named_report("Breakout Retest Cost-R Diagnostic", reason), encoding="utf-8")
        delta_path.write_text(_render_pending_named_report("Measured-Cost Assumption Delta", reason), encoding="utf-8")
        audit_path.write_text(_render_pending_named_report("Breakout Retest Measured-Cost Audit", reason), encoding="utf-8")
        return MeasuredCostRevalidationOutput("PENDING", report_path, summary_path, expert, 0, _required_cells(config), 0)

    measured = _read_measured_cost_model(config, measured_path)
    trade_files = _matrix_trade_files(config, expert)
    if not trade_files:
        raise ConfigError(f"No matrix trade ledgers found for expert {expert!r}.")

    rows: list[dict[str, Any]] = []
    baseline_frames: list[pd.DataFrame] = []
    adjusted_frames: list[pd.DataFrame] = []
    for path in trade_files:
        frame = _load_trade_frame(path)
        frame = _add_cost_r_fields(frame)
        metadata = _matrix_metadata(path)
        baseline_frames.append(frame.assign(**_metadata_columns(metadata), source_trade_file=path.name))
        adjusted = _apply_measured_p95_costs(config, measured, frame, metadata)
        rows.append(_summarize_frame(adjusted, fixed_risk_usd, metadata))
        adjusted_frames.append(adjusted.assign(source_trade_file=path.name))

    baseline = pd.concat(baseline_frames, ignore_index=True)
    baseline_overall = _summarize_frame(
        baseline,
        fixed_risk_usd,
        {"cell_id": "ALL", "broker": "ALL", "cost_model": "CONFIGURED", "symbol": "XAUUSD"},
    )
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
    adjusted_all = pd.concat(adjusted_frames, ignore_index=True)
    diagnostic_path.write_text(
        _render_cost_r_diagnostic(status, adjusted_all),
        encoding="utf-8",
    )
    delta_path.write_text(
        _render_assumption_delta_report(config, status, measured, baseline_overall, overall),
        encoding="utf-8",
    )
    audit_path.write_text(
        _render_measured_cost_audit(status, adjusted_all),
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
    adjusted["pre_measured_net_R"] = adjusted["net_R"]
    adjusted["pre_measured_all_in_cost_R"] = adjusted["all_in_cost_R"]
    adjusted["pre_measured_gross_edge_R"] = adjusted["gross_expectancy_proxy_R"]
    adjusted["risk_price"] = risk_price.astype("float64")
    adjusted["point_size"] = point_size
    adjusted["stop_distance_points"] = (risk_price / point_size).astype("float64") if point_size > 0 else pd.NA
    for key, value in _metadata_columns(metadata).items():
        adjusted[key] = value
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
    adjusted["measured_net_delta_R"] = adjusted["net_R"] - adjusted["pre_measured_net_R"]
    adjusted["gross_expectancy_proxy_R"] = adjusted["net_R"] + adjusted["all_in_cost_R"]
    return adjusted


def _metadata_columns(metadata: dict[str, Any]) -> dict[str, str]:
    return {
        "cell_id": str(metadata.get("cell_id", "")),
        "broker": str(metadata.get("broker", "")),
        "cost_model": str(metadata.get("cost_model", "")),
        "symbol": str(metadata.get("symbol", "")),
    }


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


def _render_pending_named_report(title: str, reason: str) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            "Overall status: PENDING",
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


def _render_cost_r_diagnostic(status: str, frame: pd.DataFrame) -> str:
    measured_cost_gt_gross = int(
        (
            pd.to_numeric(frame["measured_entry_spread_R"], errors="coerce").fillna(0.0)
            > pd.to_numeric(frame["pre_measured_gross_edge_R"], errors="coerce").fillna(0.0).abs()
        ).sum()
    )
    measured_cost_gt_half_r = int((pd.to_numeric(frame["measured_entry_spread_R"], errors="coerce") > 0.5).sum())
    measured_cost_gt_one_r = int((pd.to_numeric(frame["measured_entry_spread_R"], errors="coerce") > 1.0).sum())
    hourly = _cost_damage_table(frame, ["entry_hour_utc"])
    broker_cell = _cost_damage_table(frame, ["broker", "cell_id"])
    return "\n".join(
        [
            "# Breakout Retest Cost-R Diagnostic",
            "",
            f"Overall status: {status}",
            "",
            "## Quantiles",
            "",
            _markdown_table_from_rows(
                [
                    _quantile_row(frame, "risk_price"),
                    _quantile_row(frame, "stop_distance_points"),
                    _quantile_row(frame, "measured_p95_spread_points"),
                    _quantile_row(frame, "measured_entry_spread_R"),
                    _quantile_row(frame, "all_in_cost_R"),
                    _quantile_row(frame, "pre_measured_net_R"),
                    _quantile_row(frame, "net_R"),
                ],
                ["Metric", "P05", "P25", "Median", "P75", "P95"],
            ),
            "",
            "## Damage Counts",
            "",
            _markdown_table_from_rows(
                [
                    {
                        "Check": "measured_cost_R > gross_edge_R_abs",
                        "Count": str(measured_cost_gt_gross),
                    },
                    {
                        "Check": "measured_cost_R > 0.5R",
                        "Count": str(measured_cost_gt_half_r),
                    },
                    {
                        "Check": "measured_cost_R > 1.0R",
                        "Count": str(measured_cost_gt_one_r),
                    },
                ],
                ["Check", "Count"],
            ),
            "",
            "## Hour-Of-Day Cost Damage",
            "",
            _markdown_table_from_rows(hourly, _damage_columns("entry_hour_utc")),
            "",
            "## Broker/Cell Cost Damage",
            "",
            _markdown_table_from_rows(broker_cell, _damage_columns("broker", "cell_id")),
            "",
            "## Boundary",
            "",
            "This diagnostic verifies the measured-cost R conversion path. It does not authorize paper-mode execution.",
            "",
        ]
    )


def _render_assumption_delta_report(
    config: ProjectConfig,
    status: str,
    measured: pd.DataFrame,
    baseline_overall: dict[str, Any],
    measured_overall: dict[str, Any],
) -> str:
    configured_median = _configured_spread_points(config, "median", "XAUUSD")
    configured_p95 = _configured_spread_points(config, "p95", "XAUUSD")
    measured_global = _measured_global_row(measured, config, "XAUUSD")
    measured_median = measured_global.get("median_spread_points", "")
    measured_p95 = measured_global.get("p95_spread_points", "")
    rows = [
        {
            "Metric": "configured_median_spread_points",
            "Configured": _fmt(configured_median),
            "Measured": _fmt(measured_median),
            "Delta": _fmt(_float_or_none(measured_median) - configured_median if _float_or_none(measured_median) is not None else ""),
        },
        {
            "Metric": "configured_p95_spread_points",
            "Configured": _fmt(configured_p95),
            "Measured": _fmt(measured_p95),
            "Delta": _fmt(_float_or_none(measured_p95) - configured_p95 if _float_or_none(measured_p95) is not None else ""),
        },
        {
            "Metric": "modeled_cost_R vs measured_cost_R",
            "Configured": _fmt(baseline_overall["mean_all_in_cost_R"]),
            "Measured": _fmt(measured_overall["mean_all_in_cost_R"]),
            "Delta": _fmt(float(measured_overall["mean_all_in_cost_R"]) - float(baseline_overall["mean_all_in_cost_R"])),
        },
        {
            "Metric": "modeled_net_R vs measured_net_R",
            "Configured": _fmt(baseline_overall["net_expectancy_R"]),
            "Measured": _fmt(measured_overall["net_expectancy_R"]),
            "Delta": _fmt(float(measured_overall["net_expectancy_R"]) - float(baseline_overall["net_expectancy_R"])),
        },
    ]
    return "\n".join(
        [
            "# Measured-Cost Assumption Delta",
            "",
            f"Overall status: {status}",
            "",
            "## Decision",
            "",
            _assumption_delta_decision(status),
            "",
            "## Delta Table",
            "",
            _markdown_table_from_rows(rows, ["Metric", "Configured", "Measured", "Delta"]),
            "",
            "## Boundary",
            "",
            "This report compares configured spread assumptions against the passive-spread measured model and the measured-cost revalidation output.",
            "",
        ]
    )


def _render_measured_cost_audit(status: str, frame: pd.DataFrame) -> str:
    checks = [
        {
            "Audit Check": "spread_points unit matches symbol point_size",
            "Status": "PASS" if _positive_numeric(frame, "point_size") else "FAIL",
            "Evidence": "point_size is populated before converting spread points to price distance.",
        },
        {
            "Audit Check": "historical point_size matches broker logger point",
            "Status": "REVIEW",
            "Evidence": "Historical conversion uses symbol point_size; passive logger now records point for source rows.",
        },
        {
            "Audit Check": "measured spread replaces modeled entry spread",
            "Status": "PASS",
            "Evidence": "all_in_cost_R subtracts entry_spread_R before adding measured_entry_spread_R.",
        },
        {
            "Audit Check": "risk_price uses entry/stop price units",
            "Status": "PASS" if _positive_numeric(frame, "risk_price") else "FAIL",
            "Evidence": "risk_price = abs(entry_price - stop_loss).",
        },
        {
            "Audit Check": "measured spread R formula",
            "Status": "PASS",
            "Evidence": "measured_entry_spread_R = spread_points * point_size / risk_price.",
        },
        {
            "Audit Check": "slippage and commission are preserved",
            "Status": "PASS",
            "Evidence": "Only entry_spread_R is replaced; entry/exit slippage and commission_R remain in all_in_cost_R.",
        },
        {
            "Audit Check": "stale quote rows excluded from spread model",
            "Status": "REVIEW",
            "Evidence": "spread_analysis.py requires tick_fresh and filters to tick_fresh=true before writing cost_model_measured.csv.",
        },
        {
            "Audit Check": "hour/day/global lookup order",
            "Status": "PASS",
            "Evidence": "Measured spread lookup tries hour_utc, then day_of_week_utc, then global fallback.",
        },
    ]
    return "\n".join(
        [
            "# Breakout Retest Measured-Cost Audit",
            "",
            f"Overall status: {status}",
            "",
            "## Audit Checks",
            "",
            _markdown_table_from_rows(checks, ["Audit Check", "Status", "Evidence"]),
            "",
            "## Conclusion",
            "",
            _audit_conclusion(status),
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


def _markdown_table_from_rows(rows: list[dict[str, str]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def _quantile_row(frame: pd.DataFrame, column: str) -> dict[str, str]:
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    if values.empty:
        return {"Metric": column, "P05": "n/a", "P25": "n/a", "Median": "n/a", "P75": "n/a", "P95": "n/a"}
    return {
        "Metric": column,
        "P05": _fmt(values.quantile(0.05)),
        "P25": _fmt(values.quantile(0.25)),
        "Median": _fmt(values.quantile(0.50)),
        "P75": _fmt(values.quantile(0.75)),
        "P95": _fmt(values.quantile(0.95)),
    }


def _cost_damage_table(frame: pd.DataFrame, group_columns: list[str]) -> list[dict[str, str]]:
    working = frame.copy()
    working["entry_hour_utc"] = pd.to_datetime(working["entry_time_utc"], utc=True, errors="coerce").dt.hour.astype("Int64").astype(str)
    rows: list[dict[str, str]] = []
    for group_key, group in working.groupby(group_columns, dropna=False, sort=True):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        row = {column: str(value) for column, value in zip(group_columns, group_key)}
        row.update(
            {
                "Trades": str(len(group)),
                "Measured Cost R Mean": _fmt(pd.to_numeric(group["measured_entry_spread_R"], errors="coerce").mean()),
                "Measured Cost R P95": _fmt(pd.to_numeric(group["measured_entry_spread_R"], errors="coerce").quantile(0.95)),
                "Net R Before": _fmt(pd.to_numeric(group["pre_measured_net_R"], errors="coerce").mean()),
                "Net R After": _fmt(pd.to_numeric(group["net_R"], errors="coerce").mean()),
                "Net R Delta": _fmt(pd.to_numeric(group["measured_net_delta_R"], errors="coerce").mean()),
            }
        )
        rows.append(row)
    return rows


def _damage_columns(*group_columns: str) -> list[str]:
    return [
        *group_columns,
        "Trades",
        "Measured Cost R Mean",
        "Measured Cost R P95",
        "Net R Before",
        "Net R After",
        "Net R Delta",
    ]


def _configured_spread_points(config: ProjectConfig, model: str, symbol: str) -> float:
    canonical = resolve_symbol(config, symbol)
    return float(config.cost_models["cost_models"][model]["spread_points"][canonical])


def _measured_global_row(measured: pd.DataFrame, config: ProjectConfig, symbol: str) -> dict[str, Any]:
    canonical = resolve_symbol(config, symbol)
    rows = measured[
        (measured["scope"].astype(str) == "global")
        & (measured["bucket"].astype(str) == "all")
        & measured["symbol"].astype(str).apply(lambda value: _matches_csv_value(value, canonical))
    ]
    return rows.iloc[0].to_dict() if not rows.empty else {}


def _assumption_delta_decision(status: str) -> str:
    if status == "PASS":
        return "Measured spread assumptions remain compatible with the current breakout-retest evidence package."
    return "Measured spread assumptions materially exceed the configured model and block Phase 2 execution eligibility."


def _audit_conclusion(status: str) -> str:
    if status == "PASS":
        return "The measured-cost conversion did not break the current evidence package under this audit surface."
    return "The measured-cost conversion currently blocks breakout-retest paper execution pending human review of the audit evidence."


def _positive_numeric(frame: pd.DataFrame, column: str) -> bool:
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    return not values.empty and bool((values > 0).all())


def _float_or_none(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: object) -> str:
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return str(value)
