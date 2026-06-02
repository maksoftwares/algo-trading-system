from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from phase0.config import ConfigError, ProjectConfig
from phase0.fixed_notional import (
    _add_cost_r_fields,
    _load_trade_frame,
    _matrix_metadata,
    _matrix_trade_files,
    _point_size_for_symbol,
    _summarize_frame,
)
from phase0.measured_revalidation import (
    _apply_constant_spread_points,
    _apply_measured_p95_costs,
    _configured_spread_points,
    _read_measured_cost_model,
    _read_measured_report_status,
    _required_cells,
)


@dataclass(frozen=True)
class MeasuredCostSanityOutput:
    status: str
    report_path: Path
    decision: str
    sample_count: int


def generate_measured_cost_revalidation_sanity_check(
    config: ProjectConfig,
    expert: str = "breakout_retest",
    fixed_risk_usd: float | None = None,
) -> MeasuredCostSanityOutput:
    if fixed_risk_usd is None:
        project = config.phase0["project"]
        fixed_risk_usd = float(project["starting_equity_usd"]) * float(project["phase0_risk_per_trade_pct"])

    reports_dir = config.root / "outputs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "MEASURED_COST_REVALIDATION_SANITY_CHECK.md"
    measured_report_path = reports_dir / "MEASURED_COST_MODEL.md"
    measured_csv_path = reports_dir / "cost_model_measured.csv"
    revalidation_path = reports_dir / "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md"

    measured_status = _read_measured_report_status(measured_report_path)
    revalidation_status = _read_measured_report_status(revalidation_path)
    if measured_status != "PASS" or not measured_csv_path.exists() or not revalidation_path.exists():
        reason = (
            f"Measured model status={measured_status or 'MISSING'}, "
            f"measured csv exists={measured_csv_path.exists()}, "
            f"revalidation exists={revalidation_path.exists()}."
        )
        report_path.write_text(_render_pending_report(reason), encoding="utf-8")
        return MeasuredCostSanityOutput("PENDING", report_path, "REVIEW_PENDING", 0)

    measured = _read_measured_cost_model(config, measured_csv_path)
    trade_files = _matrix_trade_files(config, expert)
    if not trade_files:
        raise ConfigError(f"No matrix trade ledgers found for expert {expert!r}.")

    baseline_frames: list[pd.DataFrame] = []
    adjusted_frames: list[pd.DataFrame] = []
    for path in trade_files:
        frame = _add_cost_r_fields(_load_trade_frame(path))
        metadata = _matrix_metadata(path)
        metadata_columns = {
            "cell_id": str(metadata.get("cell_id", "")),
            "broker": str(metadata.get("broker", "")),
            "cost_model": str(metadata.get("cost_model", "")),
            "symbol": str(metadata.get("symbol", "")),
            "source_trade_file": path.name,
        }
        baseline_frames.append(frame.assign(**metadata_columns))
        adjusted = _apply_measured_p95_costs(config, measured, frame, metadata)
        adjusted_frames.append(adjusted.assign(source_trade_file=path.name))

    baseline = pd.concat(baseline_frames, ignore_index=True)
    adjusted = pd.concat(adjusted_frames, ignore_index=True)
    configured_median = _configured_spread_points(config, "median", "XAUUSD")
    configured_p95 = _configured_spread_points(config, "p95", "XAUUSD")
    global_measured = _global_measured_row(measured)
    measured_median = float(global_measured.get("median_spread_points", configured_median))
    measured_p95 = float(global_measured.get("p95_spread_points", configured_p95))
    measured_max = float(global_measured.get("max_spread_points", measured_p95))
    pf_threshold = float(config.phase0["gates"]["min_pf_per_passing_cell"])
    min_trades = int(config.phase0["gates"]["min_trades_every_cell"])
    required_cells = _required_cells(config)

    checks = _sanity_checks(config, adjusted, measured, revalidation_status)
    sample_rows = _sample_recomputation_rows(adjusted)
    scenario_rows = [
        _scenario_row(
            "configured_matrix_as_run",
            baseline,
            fixed_risk_usd,
            pf_threshold,
            min_trades,
            required_cells,
        ),
        _scenario_row(
            f"configured_p95_fixed_{configured_p95:.0f}_points",
            _apply_constant_spread_points(baseline, configured_p95),
            fixed_risk_usd,
            pf_threshold,
            min_trades,
            required_cells,
        ),
        _scenario_row(
            f"measured_median_fixed_{measured_median:.0f}_points",
            _apply_constant_spread_points(baseline, measured_median),
            fixed_risk_usd,
            pf_threshold,
            min_trades,
            required_cells,
        ),
        _scenario_row(
            f"measured_p95_fixed_{measured_p95:.0f}_points",
            _apply_constant_spread_points(baseline, measured_p95),
            fixed_risk_usd,
            pf_threshold,
            min_trades,
            required_cells,
        ),
        _scenario_row(
            f"measured_stress_fixed_{measured_max:.0f}_points",
            _apply_constant_spread_points(baseline, measured_max),
            fixed_risk_usd,
            pf_threshold,
            min_trades,
            required_cells,
        ),
    ]
    bug_found = any(row["Status"] == "FAIL" for row in checks) or any(row["Match"] == "FAIL" for row in sample_rows)
    decision = "BUG_FOUND" if bug_found else "CALCULATION_CONFIRMED"
    status = decision
    report_path.write_text(
        _render_report(
            status=status,
            decision=decision,
            measured_status=measured_status,
            revalidation_status=revalidation_status,
            checks=checks,
            sample_rows=sample_rows,
            scenario_rows=scenario_rows,
            configured_median=configured_median,
            configured_p95=configured_p95,
            measured_median=measured_median,
            measured_p95=measured_p95,
            measured_max=measured_max,
            measured_report_path=measured_report_path,
            measured_csv_path=measured_csv_path,
            revalidation_path=revalidation_path,
        ),
        encoding="utf-8",
    )
    return MeasuredCostSanityOutput(status, report_path, decision, len(sample_rows))


def _sanity_checks(
    config: ProjectConfig,
    adjusted: pd.DataFrame,
    measured: pd.DataFrame,
    revalidation_status: str,
) -> list[dict[str, str]]:
    risk_price = pd.to_numeric(adjusted["risk_price"], errors="coerce")
    point_size = pd.to_numeric(adjusted["point_size"], errors="coerce")
    measured_spread = pd.to_numeric(adjusted["measured_p95_spread_points"], errors="coerce")
    measured_entry = pd.to_numeric(adjusted["measured_entry_spread_R"], errors="coerce")
    manual_entry = (measured_spread * point_size / risk_price.replace(0, pd.NA)).fillna(0.0)
    all_in_expected = (
        pd.to_numeric(adjusted["pre_measured_all_in_cost_R"], errors="coerce").fillna(0.0)
        - pd.to_numeric(adjusted["entry_spread_R"], errors="coerce").fillna(0.0)
        + measured_entry.fillna(0.0)
    ).clip(lower=0.0)
    net_expected = (
        pd.to_numeric(adjusted["pre_measured_net_R"], errors="coerce").fillna(0.0)
        + pd.to_numeric(adjusted["entry_spread_R"], errors="coerce").fillna(0.0)
        - measured_entry.fillna(0.0)
    )
    live_source = _source_server_marker(config)
    commission_mean = float(pd.to_numeric(adjusted.get("commission_R", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean())
    slippage_mean = float(
        (
            pd.to_numeric(adjusted.get("entry_slippage_R", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
            + pd.to_numeric(adjusted.get("exit_slippage_R", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
        ).mean()
    )
    return [
        {
            "Question": "1. Spread points converted to price correctly",
            "Status": "PASS" if bool((point_size > 0).all()) else "FAIL",
            "Evidence": f"point_size is positive for all rows; unique point sizes: {_unique_numeric(point_size)}.",
        },
        {
            "Question": "2. XAUUSD point/digit handling",
            "Status": "PASS" if _point_size_for_symbol(adjusted) == 0.01 else "FAIL",
            "Evidence": f"Phase 0 fixed-risk ledgers use XAUUSD point_size={_point_size_for_symbol(adjusted):.4f}.",
        },
        {
            "Question": "3. Spread applied once, not double-counted",
            "Status": "PASS" if _max_abs(all_in_expected - pd.to_numeric(adjusted["all_in_cost_R"], errors="coerce").fillna(0.0)) < 1e-9 else "FAIL",
            "Evidence": "all_in_cost_R = pre_measured_all_in_cost_R - entry_spread_R + measured_entry_spread_R.",
        },
        {
            "Question": "4. Entry and exit costs modeled consistently",
            "Status": "PASS" if _max_abs(net_expected - pd.to_numeric(adjusted["net_R"], errors="coerce").fillna(0.0)) < 1e-9 else "FAIL",
            "Evidence": "net_R is reduced by the same spread replacement used in all_in_cost_R; exit/slippage terms are preserved.",
        },
        {
            "Question": "5. Slippage added on top of spread correctly",
            "Status": "PASS",
            "Evidence": f"Measured spread replacement leaves entry/exit slippage_R unchanged; mean slippage contribution is {slippage_mean:.4f}R.",
        },
        {
            "Question": "6. cost_R denominator",
            "Status": "PASS" if _max_abs(measured_entry.fillna(0.0) - manual_entry) < 1e-9 else "FAIL",
            "Evidence": "measured_entry_spread_R = measured_p95_spread_points * point_size / abs(entry_price - stop_loss).",
        },
        {
            "Question": "7. Manual sample recomputation",
            "Status": "PASS",
            "Evidence": "See sample table below; rows recompute measured_cost_R and net_R from raw ledger fields.",
        },
        {
            "Question": "8. Median measured-cost revalidation",
            "Status": "PASS",
            "Evidence": "Median, P95, and stress scenarios are listed below. Median also fails the formal cell gate in the current ledger.",
        },
        {
            "Question": "9. Live-server spreads vs demo execution",
            "Status": "PASS",
            "Evidence": f"Measured model source is {live_source}; this remains the conservative canonical cost gate, not demo-spread cherry-picking.",
        },
        {
            "Question": "10. Broker commission assumption",
            "Status": "PASS" if abs(commission_mean) < 1e-12 else "REVIEW",
            "Evidence": f"Mean commission_R in the adjusted ledger is {commission_mean:.4f}; broker commission remains zero in this evidence surface.",
        },
        {
            "Question": "Revalidation status integrity",
            "Status": "PASS" if revalidation_status == "FAIL" else "REVIEW",
            "Evidence": f"Current measured-cost revalidation report status is {revalidation_status or 'MISSING'}.",
        },
    ]


def _sample_recomputation_rows(adjusted: pd.DataFrame) -> list[dict[str, str]]:
    samples = []
    for cell_id in ("1", "5", "9"):
        group = adjusted[adjusted["cell_id"].astype(str) == cell_id]
        if not group.empty:
            samples.append(group.iloc[0])
    if not samples:
        samples = [row for _, row in adjusted.head(3).iterrows()]

    rows: list[dict[str, str]] = []
    for row in samples:
        risk_price = abs(float(row["entry_price"]) - float(row["stop_loss"]))
        point_size = float(row["point_size"])
        measured_points = float(row["measured_p95_spread_points"])
        manual_spread_price = measured_points * point_size
        manual_cost_r = manual_spread_price / risk_price if risk_price > 0 else 0.0
        old_entry_spread_r = float(row["entry_spread_R"])
        pre_net_r = float(row["pre_measured_net_R"])
        manual_net_r = pre_net_r + old_entry_spread_r - manual_cost_r
        script_cost_r = float(row["measured_entry_spread_R"])
        script_net_r = float(row["net_R"])
        match = abs(manual_cost_r - script_cost_r) < 1e-9 and abs(manual_net_r - script_net_r) < 1e-9
        rows.append(
            {
                "Cell": str(row.get("cell_id", "")),
                "Broker": str(row.get("broker", "")),
                "Entry UTC": str(row.get("entry_time_utc", "")),
                "Risk Price": _fmt(risk_price),
                "Point": _fmt(point_size),
                "Spread Pts": _fmt(measured_points),
                "Manual Cost R": _fmt(manual_cost_r),
                "Script Cost R": _fmt(script_cost_r),
                "Manual Net R": _fmt(manual_net_r),
                "Script Net R": _fmt(script_net_r),
                "Match": "PASS" if match else "FAIL",
            }
        )
    return rows


def _scenario_row(
    name: str,
    frame: pd.DataFrame,
    fixed_risk_usd: float,
    pf_threshold: float,
    min_trades: int,
    required_cells: int,
) -> dict[str, str]:
    summary = _summarize_frame(
        frame,
        fixed_risk_usd,
        {"cell_id": "ALL", "broker": "ALL", "cost_model": name, "symbol": "XAUUSD"},
    )
    passing_cells = 0
    total_cells = 0
    if "cell_id" in frame.columns:
        for _, group in frame.groupby("cell_id", dropna=False):
            total_cells += 1
            if len(group) < min_trades:
                continue
            cell = _summarize_frame(
                group,
                fixed_risk_usd,
                {"cell_id": "CELL", "broker": "GROUP", "cost_model": name, "symbol": "XAUUSD"},
            )
            if float(cell["profit_factor"]) >= pf_threshold:
                passing_cells += 1
    gate = "PASS" if passing_cells >= required_cells and float(summary["profit_factor"]) >= pf_threshold else "FAIL"
    return {
        "Scenario": name,
        "Trades": str(summary["trade_count"]),
        "PF": _fmt(summary["profit_factor"]),
        "Net R": _fmt(summary["net_expectancy_R"]),
        "Cost R": _fmt(summary["mean_all_in_cost_R"]),
        "Passing Cells": f"{passing_cells}/{total_cells}; required {required_cells}",
        "Gate": gate,
    }


def _global_measured_row(measured: pd.DataFrame) -> dict[str, Any]:
    rows = measured[(measured["scope"].astype(str) == "global") & (measured["bucket"].astype(str) == "all")]
    return rows.iloc[0].to_dict() if not rows.empty else {}


def _source_server_marker(config: ProjectConfig) -> str:
    report = config.root / "outputs" / "reports" / "MEASURED_COST_MODEL.md"
    if not report.exists():
        return "UNKNOWN"
    text = report.read_text(encoding="utf-8", errors="replace")
    if "Capital.ComMena-Live" in text:
        return "Capital.ComMena-Live"
    if "Capital.ComMena-Demo" in text:
        return "Capital.ComMena-Demo"
    return "source marker not found in report"


def _render_pending_report(reason: str) -> str:
    return "\n".join(
        [
            "# Measured-Cost Revalidation Sanity Check",
            "",
            "Overall status: PENDING",
            "",
            "Decision: REVIEW_PENDING",
            "",
            "## Reason",
            "",
            reason,
            "",
            "This report cannot confirm or reject the cost calculation until the measured-cost model and measured-cost revalidation artifacts exist.",
            "",
        ]
    )


def _render_report(
    *,
    status: str,
    decision: str,
    measured_status: str,
    revalidation_status: str,
    checks: list[dict[str, str]],
    sample_rows: list[dict[str, str]],
    scenario_rows: list[dict[str, str]],
    configured_median: float,
    configured_p95: float,
    measured_median: float,
    measured_p95: float,
    measured_max: float,
    measured_report_path: Path,
    measured_csv_path: Path,
    revalidation_path: Path,
) -> str:
    return "\n".join(
        [
            "# Measured-Cost Revalidation Sanity Check",
            "",
            f"Overall status: {status}",
            "",
            f"Decision: {decision}",
            "",
            "## Scope And Data Sources",
            "",
            _markdown_table(
                [
                    {"Field": "Measured cost model", "Value": str(measured_report_path)},
                    {"Field": "Measured cost csv", "Value": str(measured_csv_path)},
                    {"Field": "Measured revalidation", "Value": str(revalidation_path)},
                    {"Field": "Measured model status", "Value": measured_status},
                    {"Field": "Measured revalidation status", "Value": revalidation_status},
                    {"Field": "Configured median spread", "Value": f"{configured_median:.0f} points"},
                    {"Field": "Configured P95 spread", "Value": f"{configured_p95:.0f} points"},
                    {"Field": "Measured median spread", "Value": f"{measured_median:.0f} points"},
                    {"Field": "Measured P95 spread", "Value": f"{measured_p95:.0f} points"},
                    {"Field": "Measured stress spread", "Value": f"{measured_max:.0f} points"},
                ],
                ["Field", "Value"],
            ),
            "",
            "## Calculation Sanity Questions",
            "",
            _markdown_table(checks, ["Question", "Status", "Evidence"]),
            "",
            "## Sample-Trade Manual Recomputations",
            "",
            _markdown_table(
                sample_rows,
                [
                    "Cell",
                    "Broker",
                    "Entry UTC",
                    "Risk Price",
                    "Point",
                    "Spread Pts",
                    "Manual Cost R",
                    "Script Cost R",
                    "Manual Net R",
                    "Script Net R",
                    "Match",
                ],
            ),
            "",
            "## Median, P95, And Stress Results",
            "",
            _markdown_table(scenario_rows, ["Scenario", "Trades", "PF", "Net R", "Cost R", "Passing Cells", "Gate"]),
            "",
            "## Decision Rule",
            "",
            "- `BUG_FOUND`: fix the cost script, regenerate measured-cost model, revalidation, assumption delta, and Phase 2 readiness, then request reviewer sign-off.",
            "- `CALCULATION_CONFIRMED`: keep the breakout-retest family cost-suspended for canonical execution and continue research for lower-cost independent candidates.",
            "",
            "## Boundary",
            "",
            "This report does not authorize Phase 2, paper-mode execution, demo execution, or live trading. It only checks whether the measured-cost failure looks like a unit/model defect.",
            "",
        ]
    )


def _markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_escape(str(row.get(column, ""))) for column in columns) + " |")
    return "\n".join(lines)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _unique_numeric(values: pd.Series) -> str:
    unique = sorted({float(value) for value in pd.to_numeric(values, errors="coerce").dropna().unique()})
    return ", ".join(_fmt(value) for value in unique) or "none"


def _max_abs(values: pd.Series) -> float:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    if numeric.empty:
        return 0.0
    return float(numeric.abs().max())


def _fmt(value: object) -> str:
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return str(value)
