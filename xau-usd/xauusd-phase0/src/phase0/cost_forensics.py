from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
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
from phase0.measured_revalidation import (
    _apply_measured_p95_costs,
    _metadata_columns,
    _read_measured_cost_model,
    _read_measured_report_status,
)


MEASURED_MODEL = "MEASURED_COST_MODEL.md"
MEASURED_MODEL_CSV = "cost_model_measured.csv"
MEASURED_REVALIDATION = "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md"
MEASURED_ASSUMPTION_DELTA = "MEASURED_COST_ASSUMPTION_DELTA.md"
MEASURED_SANITY = "MEASURED_COST_REVALIDATION_SANITY_CHECK.md"


@dataclass(frozen=True)
class CostForensicOutput:
    status: str
    report_path: Path
    rows: int = 0


def generate_measured_cost_forensic_review(
    config: ProjectConfig,
    expert: str = "breakout_retest",
    fixed_risk_usd: float | None = None,
) -> CostForensicOutput:
    context = _load_context(config, expert, fixed_risk_usd)
    reports = config.root / "outputs" / "reports"
    path = reports / _named_report(expert, "MEASURED_COST_FORENSIC_REVIEW.md")
    checks = [
        _unit_conversion_check(context.adjusted),
        _spread_replacement_check(context.adjusted),
        _point_size_check(context.adjusted, context.spread_logs),
        _stop_distance_check(context.adjusted),
        _freshness_filter_check(reports / MEASURED_MODEL, context.measured),
        _broker_source_check(reports / MEASURED_MODEL, context.measured),
    ]
    status = "CALCULATION_CONFIRMED" if all(row["Status"] in {"PASS", "WARN"} for row in checks) else "REVIEW_REQUIRED"
    path.write_text(_render_forensic_review(status, context, checks), encoding="utf-8")
    return CostForensicOutput(status, path, len(context.adjusted))


def generate_cost_r_sample_audit(
    config: ProjectConfig,
    expert: str = "breakout_retest",
    sample_size: int = 100,
    fixed_risk_usd: float | None = None,
) -> CostForensicOutput:
    context = _load_context(config, expert, fixed_risk_usd)
    reports = config.root / "outputs" / "reports"
    path = reports / ("COST_R_SAMPLE_AUDIT.csv" if expert == "breakout_retest" else f"{expert}_cost_r_sample_audit.csv")
    sample = _deterministic_sample(context.adjusted, sample_size)
    risk_price = pd.to_numeric(sample["risk_price"], errors="coerce").replace(0, pd.NA)
    replacement_expected = (
        pd.to_numeric(sample["pre_measured_all_in_cost_R"], errors="coerce")
        - pd.to_numeric(sample["entry_spread_R"], errors="coerce")
        + pd.to_numeric(sample["measured_entry_spread_R"], errors="coerce")
    )
    sample_out = pd.DataFrame(
        {
            "source_trade_file": sample.get("source_trade_file", ""),
            "entry_time_utc": sample.get("entry_time_utc", ""),
            "cell_id": sample.get("cell_id", ""),
            "broker": sample.get("broker", ""),
            "entry_price": sample["entry_price"],
            "stop_loss": sample["stop_loss"],
            "risk_price": sample["risk_price"],
            "point_size": sample["point_size"],
            "stop_distance_points": sample["stop_distance_points"],
            "modeled_entry_spread_R": sample["entry_spread_R"],
            "measured_p95_spread_points": sample["measured_p95_spread_points"],
            "measured_entry_spread_R": sample["measured_entry_spread_R"],
            "pre_measured_all_in_cost_R": sample["pre_measured_all_in_cost_R"],
            "expected_all_in_cost_R": replacement_expected,
            "actual_all_in_cost_R": sample["all_in_cost_R"],
            "all_in_cost_abs_error": (pd.to_numeric(sample["all_in_cost_R"], errors="coerce") - replacement_expected).abs(),
            "pre_measured_net_R": sample["pre_measured_net_R"],
            "net_R": sample["net_R"],
            "measured_net_delta_R": sample["measured_net_delta_R"],
            "unit_formula_measured_spread_R": (
                pd.to_numeric(sample["measured_p95_spread_points"], errors="coerce")
                * pd.to_numeric(sample["point_size"], errors="coerce")
                / risk_price
            ),
        }
    )
    sample_out["status"] = sample_out["all_in_cost_abs_error"].apply(lambda value: "PASS" if float(value) <= 1e-9 else "FAIL")
    sample_out.to_csv(path, index=False)
    status = "PASS" if (sample_out["status"] == "PASS").all() else "FAIL"
    return CostForensicOutput(status, path, len(sample_out))


def generate_point_size_and_digits_audit(
    config: ProjectConfig,
    symbol: str = "XAUUSD",
    expert: str = "breakout_retest",
    fixed_risk_usd: float | None = None,
) -> CostForensicOutput:
    context = _load_context(config, expert, fixed_risk_usd)
    reports = config.root / "outputs" / "reports"
    path = reports / "POINT_SIZE_AND_DIGITS_AUDIT.md"
    rows = _point_size_rows(context.adjusted, context.spread_logs, config, symbol)
    status = "PASS" if all(row["Status"] in {"PASS", "WARN"} for row in rows) else "FAIL"
    path.write_text(_render_point_size_audit(status, symbol, rows), encoding="utf-8")
    return CostForensicOutput(status, path, len(rows))


def generate_spread_replacement_audit(
    config: ProjectConfig,
    expert: str = "breakout_retest",
    fixed_risk_usd: float | None = None,
) -> CostForensicOutput:
    context = _load_context(config, expert, fixed_risk_usd)
    reports = config.root / "outputs" / "reports"
    path = reports / "SPREAD_REPLACEMENT_AUDIT.md"
    replacement = _spread_replacement_check(context.adjusted)
    path.write_text(_render_spread_replacement_audit(replacement), encoding="utf-8")
    return CostForensicOutput(replacement["Status"], path, len(context.adjusted))


def generate_stale_quote_rollover_audit(
    config: ProjectConfig,
    symbol: str = "XAUUSD",
) -> CostForensicOutput:
    reports = config.root / "outputs" / "reports"
    path = reports / "STALE_QUOTE_AND_ROLLOVER_EXCLUSION_AUDIT.md"
    model_path = reports / MEASURED_MODEL
    measured = _load_measured(config)
    rows = _freshness_rows(model_path, measured, config, symbol)
    status = "PASS" if all(row["Status"] in {"PASS", "WARN"} for row in rows) else "FAIL"
    path.write_text(_render_stale_rollover_audit(status, rows), encoding="utf-8")
    return CostForensicOutput(status, path, len(rows))


def generate_cost_break_even_analysis(
    config: ProjectConfig,
    expert: str = "breakout_retest",
    fixed_risk_usd: float | None = None,
) -> CostForensicOutput:
    context = _load_context(config, expert, fixed_risk_usd)
    reports = config.root / "outputs" / "reports"
    path = reports / _named_report(expert, "COST_BREAK_EVEN_ANALYSIS.md")
    rows = _break_even_rows(context)
    status = "BLOCKED_BY_MEASURED_COST" if context.measured_overall["profit_factor"] < 1.0 else "PASS"
    path.write_text(_render_break_even_analysis(status, context, rows), encoding="utf-8")
    return CostForensicOutput(status, path, len(rows))


def generate_candidate_cost_feasibility(
    config: ProjectConfig,
    expert: str,
    median_stop_points: float | None = None,
) -> CostForensicOutput:
    reports = config.root / "outputs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    if median_stop_points is None:
        median_stop_points = _parse_hypothesis_stop_points(config.root / "docs" / f"hypothesis_{expert}.md")
    if median_stop_points is None or median_stop_points <= 0:
        raise ConfigError("median_stop_points must be supplied or present in the hypothesis document.")

    measured = _load_measured(config)
    global_row = _measured_global_row(measured, config, "XAUUSD")
    median_spread = float(global_row.get("median_spread_points", 50.0))
    p95_spread = float(global_row.get("p95_spread_points", 75.0))
    median_cost_r = median_spread / median_stop_points
    p95_cost_r = p95_spread / median_stop_points
    if median_stop_points < 250.0:
        status = "REJECT_COST_FRAGILE"
        reason = "Expected median stop distance is below 250 points."
    elif p95_cost_r > 0.30:
        status = "REJECT_P95_COST_TOO_HIGH"
        reason = "Measured P95 cost_R exceeds 0.30R."
    elif median_stop_points < 375.0:
        status = "PASS_WITH_COST_CAUTION"
        reason = "Candidate clears the hard cost screen but is below the preferred 375 point stop budget."
    else:
        status = "PASS"
        reason = "Candidate clears measured-cost structural pre-screen."
    path = reports / f"{expert}_candidate_cost_feasibility.md"
    path.write_text(
        _render_candidate_feasibility(
            expert,
            status,
            reason,
            median_stop_points,
            median_spread,
            p95_spread,
            median_cost_r,
            p95_cost_r,
        ),
        encoding="utf-8",
    )
    return CostForensicOutput(status, path, 1)


@dataclass(frozen=True)
class _CostContext:
    expert: str
    fixed_risk_usd: float
    measured: pd.DataFrame
    baseline: pd.DataFrame
    adjusted: pd.DataFrame
    baseline_overall: dict[str, Any]
    measured_overall: dict[str, Any]
    spread_logs: pd.DataFrame


def _load_context(
    config: ProjectConfig,
    expert: str,
    fixed_risk_usd: float | None,
) -> _CostContext:
    if fixed_risk_usd is None:
        project = config.phase0["project"]
        fixed_risk_usd = float(project["starting_equity_usd"]) * float(project["phase0_risk_per_trade_pct"])
    measured = _load_measured(config)
    trade_files = _matrix_trade_files(config, expert)
    if not trade_files:
        raise ConfigError(f"No matrix trade ledgers found for expert {expert!r}.")
    baseline_frames: list[pd.DataFrame] = []
    adjusted_frames: list[pd.DataFrame] = []
    for path in trade_files:
        frame = _add_cost_r_fields(_load_trade_frame(path))
        metadata = _matrix_metadata(path)
        baseline_frames.append(frame.assign(**_metadata_columns(metadata), source_trade_file=path.name))
        adjusted_frames.append(
            _apply_measured_p95_costs(config, measured, frame, metadata).assign(source_trade_file=path.name)
        )
    baseline = pd.concat(baseline_frames, ignore_index=True)
    adjusted = pd.concat(adjusted_frames, ignore_index=True)
    baseline_overall = _summarize_frame(
        baseline,
        fixed_risk_usd,
        {"cell_id": "ALL", "broker": "ALL", "cost_model": "CONFIGURED", "symbol": "XAUUSD"},
    )
    measured_overall = _summarize_frame(
        adjusted,
        fixed_risk_usd,
        {"cell_id": "ALL", "broker": "ALL", "cost_model": "MEASURED_P95", "symbol": "XAUUSD"},
    )
    return _CostContext(
        expert=expert,
        fixed_risk_usd=fixed_risk_usd,
        measured=measured,
        baseline=baseline,
        adjusted=adjusted,
        baseline_overall=baseline_overall,
        measured_overall=measured_overall,
        spread_logs=_load_available_spread_logs(config),
    )


def _load_measured(config: ProjectConfig) -> pd.DataFrame:
    reports = config.root / "outputs" / "reports"
    status = _read_measured_report_status(reports / MEASURED_MODEL)
    path = reports / MEASURED_MODEL_CSV
    if status != "PASS" or not path.exists():
        raise ConfigError(f"Measured cost model must be PASS and `{path}` must exist.")
    return _read_measured_cost_model(config, path)


def _load_available_spread_logs(config: ProjectConfig) -> pd.DataFrame:
    candidates = [
        config.root / "outputs" / "logs",
        Path("C:/MT5PortableSpreadLogger/MQL5/Files"),
    ]
    frames: list[pd.DataFrame] = []
    for directory in candidates:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("spread_log_*.csv")):
            try:
                frame = pd.read_csv(path)
            except Exception:
                continue
            frame["source_file"] = path.name
            frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _unit_conversion_check(frame: pd.DataFrame) -> dict[str, str]:
    expected = (
        pd.to_numeric(frame["measured_p95_spread_points"], errors="coerce")
        * pd.to_numeric(frame["point_size"], errors="coerce")
        / pd.to_numeric(frame["risk_price"], errors="coerce").replace(0, pd.NA)
    )
    error = (expected - pd.to_numeric(frame["measured_entry_spread_R"], errors="coerce")).abs().fillna(0.0)
    max_error = float(error.max()) if len(error) else 0.0
    return {
        "Check": "Unit conversion",
        "Status": "PASS" if max_error <= 1e-9 else "FAIL",
        "Evidence": f"max_abs_error={max_error:.12f}; formula=spread_points * point_size / risk_price",
    }


def _spread_replacement_check(frame: pd.DataFrame) -> dict[str, str]:
    expected = (
        pd.to_numeric(frame["pre_measured_all_in_cost_R"], errors="coerce")
        - pd.to_numeric(frame["entry_spread_R"], errors="coerce")
        + pd.to_numeric(frame["measured_entry_spread_R"], errors="coerce")
    )
    actual = pd.to_numeric(frame["all_in_cost_R"], errors="coerce")
    error = (actual - expected).abs().fillna(0.0)
    max_error = float(error.max()) if len(error) else 0.0
    return {
        "Check": "Spread replacement",
        "Status": "PASS" if max_error <= 1e-9 else "FAIL",
        "Evidence": f"max_abs_error={max_error:.12f}; measured spread replaces modeled entry spread.",
    }


def _point_size_check(frame: pd.DataFrame, spread_logs: pd.DataFrame) -> dict[str, str]:
    ledger_points = sorted({round(float(value), 8) for value in pd.to_numeric(frame["point_size"], errors="coerce").dropna()})
    if spread_logs.empty or "point" not in spread_logs.columns:
        return {
            "Check": "Point size and digits",
            "Status": "WARN",
            "Evidence": f"ledger_point_sizes={ledger_points}; spread source logs not available in repo.",
        }
    logger_points = sorted({round(float(value), 8) for value in pd.to_numeric(spread_logs["point"], errors="coerce").dropna()})
    logger_digits = sorted({str(value) for value in spread_logs.get("digits", pd.Series(dtype=str)).dropna().astype(str).unique()})
    status = "PASS" if set(ledger_points) <= set(logger_points) or ledger_points == [0.01] else "FAIL"
    return {
        "Check": "Point size and digits",
        "Status": status,
        "Evidence": f"ledger_point_sizes={ledger_points}; logger_point_sizes={logger_points}; logger_digits={logger_digits}",
    }


def _stop_distance_check(frame: pd.DataFrame) -> dict[str, str]:
    stops = pd.to_numeric(frame["stop_distance_points"], errors="coerce").dropna()
    median = float(stops.median()) if len(stops) else 0.0
    p75_cost = float(pd.to_numeric(frame["all_in_cost_R"], errors="coerce").quantile(0.75))
    return {
        "Check": "Stop distance distribution",
        "Status": "PASS" if median > 0 else "FAIL",
        "Evidence": f"median_stop_points={median:.4f}; p75_all_in_cost_R={p75_cost:.4f}",
    }


def _freshness_filter_check(model_path: Path, measured: pd.DataFrame) -> dict[str, str]:
    text = model_path.read_text(encoding="utf-8", errors="replace") if model_path.exists() else ""
    has_tick_fresh = "Tick Freshness" in text and "available" in text
    weekdays_only = not measured[
        (measured["scope"].astype(str) == "day_of_week_utc")
        & measured["bucket"].astype(str).isin({"Saturday", "Sunday"})
    ].empty
    status = "PASS" if has_tick_fresh and not weekdays_only else "WARN"
    return {
        "Check": "Freshness and closed-market filtering",
        "Status": status,
        "Evidence": f"tick_fresh_reported={has_tick_fresh}; weekend_buckets_present={weekdays_only}",
    }


def _broker_source_check(model_path: Path, measured: pd.DataFrame) -> dict[str, str]:
    brokers = sorted({str(value) for value in measured.get("broker", pd.Series(dtype=str)).dropna().astype(str).unique()})
    text = model_path.read_text(encoding="utf-8", errors="replace") if model_path.exists() else ""
    status = "PASS" if "Capital.ComMena-Live" in text or any("Capital" in broker for broker in brokers) else "WARN"
    return {
        "Check": "Broker source policy",
        "Status": status,
        "Evidence": f"measured_brokers={brokers or ['unknown']}; conservative source documented={status == 'PASS'}",
    }


def _deterministic_sample(frame: pd.DataFrame, sample_size: int) -> pd.DataFrame:
    if sample_size <= 0:
        raise ConfigError("sample_size must be positive.")
    if len(frame) <= sample_size:
        return frame.copy()
    stride = max(1, len(frame) // sample_size)
    return frame.sort_values(["entry_time_utc", "source_trade_file"]).iloc[::stride].head(sample_size).copy()


def _point_size_rows(frame: pd.DataFrame, spread_logs: pd.DataFrame, config: ProjectConfig, symbol: str) -> list[dict[str, str]]:
    canonical = resolve_symbol(config, symbol)
    rows = [_point_size_check(frame, spread_logs)]
    ledger_digits = "2" if _point_size_for_symbol(frame) == 0.01 else "5"
    rows.append(
        {
            "Check": "Historical ledger symbol metadata",
            "Status": "PASS",
            "Evidence": f"symbol={canonical}; inferred_point_size={_point_size_for_symbol(frame):.4f}; inferred_digits={ledger_digits}",
        }
    )
    if not spread_logs.empty and "symbol" in spread_logs.columns:
        matching = spread_logs[spread_logs["symbol"].astype(str).str.upper() == canonical.upper()]
        points = sorted({str(value) for value in matching.get("point", pd.Series(dtype=str)).dropna().astype(str).unique()})
        digits = sorted({str(value) for value in matching.get("digits", pd.Series(dtype=str)).dropna().astype(str).unique()})
        rows.append(
            {
                "Check": "Measured logger symbol metadata",
                "Status": "PASS" if points else "WARN",
                "Evidence": f"symbol={canonical}; logger_points={points or ['not found']}; logger_digits={digits or ['not found']}",
            }
        )
    return rows


def _freshness_rows(model_path: Path, measured: pd.DataFrame, config: ProjectConfig, symbol: str) -> list[dict[str, str]]:
    rows = [_freshness_filter_check(model_path, measured)]
    canonical = resolve_symbol(config, symbol)
    global_row = _measured_global_row(measured, config, canonical)
    rows.append(
        {
            "Check": "Authoritative global measured model",
            "Status": "PASS" if global_row else "FAIL",
            "Evidence": f"symbol={canonical}; global_row_present={bool(global_row)}; p95={global_row.get('p95_spread_points', 'n/a')}",
        }
    )
    rollover = measured[measured["scope"].astype(str) == "rollover"]
    rows.append(
        {
            "Check": "Rollover diagnostic retained separately",
            "Status": "PASS" if not rollover.empty else "WARN",
            "Evidence": f"rollover_rows={len(rollover)}; rollover rows are diagnostic, not a same-family rescue filter.",
        }
    )
    weekdays = sorted(
        measured[measured["scope"].astype(str) == "day_of_week_utc"]["bucket"].dropna().astype(str).unique()
    )
    rows.append(
        {
            "Check": "Weekend exclusion",
            "Status": "PASS" if not {"Saturday", "Sunday"} & set(weekdays) else "FAIL",
            "Evidence": f"day_of_week_buckets={weekdays}",
        }
    )
    return rows


def _break_even_rows(context: _CostContext) -> list[dict[str, str]]:
    global_row = _measured_global_row(context.measured, None, "XAUUSD")
    measured_p95 = float(global_row.get("p95_spread_points", 75.0))
    baseline_gross = float(context.baseline_overall["gross_expectancy_R"])
    measured_net = float(context.measured_overall["net_expectancy_R"])
    rows = []
    for target in (0.15, 0.20, 0.30, 0.50, baseline_gross):
        if target <= 0:
            continue
        rows.append(
            {
                "Target cost_R": f"{target:.4f}",
                "Required stop points": f"{measured_p95 / target:.2f}",
                "Interpretation": _target_interpretation(target, baseline_gross, measured_net),
            }
        )
    return rows


def _target_interpretation(target: float, baseline_gross: float, measured_net: float) -> str:
    if math.isclose(target, baseline_gross, rel_tol=1e-6, abs_tol=1e-6):
        return f"Approximate zero-edge cost ceiling from baseline gross expectancy; current measured net={measured_net:.4f}R."
    if target <= 0.15:
        return "Strong cost discipline target."
    if target <= 0.20:
        return "Preferred candidate screening target."
    if target <= 0.30:
        return "Hard upper tolerance for pre-screening."
    return "Too expensive for modest-edge systems."


def _measured_global_row(measured: pd.DataFrame, config: ProjectConfig | None, symbol: str) -> dict[str, Any]:
    canonical = resolve_symbol(config, symbol) if config is not None else symbol
    rows = measured[
        (measured["scope"].astype(str) == "global")
        & (measured["bucket"].astype(str) == "all")
        & measured["symbol"].astype(str).str.upper().str.contains(canonical.upper(), regex=False)
    ]
    return rows.iloc[0].to_dict() if not rows.empty else {}


def _parse_hypothesis_stop_points(path: Path) -> float | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    patterns = (
        r"Expected median stop(?: distance)?(?: points)?:\s*([0-9]+(?:\.[0-9]+)?)",
        r"expected median stop(?: distance)?(?: points)?\s*(?:>=|=|:)\s*([0-9]+(?:\.[0-9]+)?)",
        r"Preferred median stop:\s*>=\s*([0-9]+(?:\.[0-9]+)?)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def _named_report(expert: str, suffix: str) -> str:
    return f"{expert.upper()}_{suffix}" if expert != "breakout_retest" else f"BREAKOUT_RETEST_{suffix}"


def _render_forensic_review(status: str, context: _CostContext, checks: list[dict[str, str]]) -> str:
    return "\n".join(
        [
            "# Breakout-Retest Measured-Cost Forensic Review",
            "",
            f"Overall status: {status}",
            f"Generated at UTC: {_now()}",
            "",
            "## Decision Boundary",
            "",
            "This forensic review checks whether the measured-cost failure looks reproducible. It does not authorize Phase 2, demo execution, broker execution, or live capital.",
            "",
            "## Evidence Summary",
            "",
            _table(
                [
                    ("Expert", context.expert),
                    ("Trades audited", str(len(context.adjusted))),
                    ("Baseline PF", _fmt(context.baseline_overall["profit_factor"])),
                    ("Measured PF", _fmt(context.measured_overall["profit_factor"])),
                    ("Baseline net expectancy R", _fmt(context.baseline_overall["net_expectancy_R"])),
                    ("Measured net expectancy R", _fmt(context.measured_overall["net_expectancy_R"])),
                    ("Baseline mean cost R", _fmt(context.baseline_overall["mean_all_in_cost_R"])),
                    ("Measured mean cost R", _fmt(context.measured_overall["mean_all_in_cost_R"])),
                ]
            ),
            "",
            "## Checks",
            "",
            _markdown_table(checks, ["Check", "Status", "Evidence"]),
            "",
            "## Decision",
            "",
            "No canonical Phase 2 execution may reopen from this report alone. If these checks remain confirmed, the correct action is Phase 0R replacement research.",
            "",
        ]
    )


def _render_point_size_audit(status: str, symbol: str, rows: list[dict[str, str]]) -> str:
    return "\n".join(
        [
            "# Point Size And Digits Audit",
            "",
            f"Overall status: {status}",
            f"Generated at UTC: {_now()}",
            f"Symbol: `{symbol}`",
            "",
            _markdown_table(rows, ["Check", "Status", "Evidence"]),
            "",
            "This report verifies symbol metadata for cost-R conversion only. It does not authorize Phase 2.",
            "",
        ]
    )


def _render_spread_replacement_audit(row: dict[str, str]) -> str:
    return "\n".join(
        [
            "# Spread Replacement Audit",
            "",
            f"Overall status: {row['Status']}",
            f"Generated at UTC: {_now()}",
            "",
            _markdown_table([row], ["Check", "Status", "Evidence"]),
            "",
            "The measured spread must replace the modeled entry spread. It must not be added on top of the modeled spread.",
            "",
        ]
    )


def _render_stale_rollover_audit(status: str, rows: list[dict[str, str]]) -> str:
    return "\n".join(
        [
            "# Stale Quote And Rollover Exclusion Audit",
            "",
            f"Overall status: {status}",
            f"Generated at UTC: {_now()}",
            "",
            _markdown_table(rows, ["Check", "Status", "Evidence"]),
            "",
            "Rollover and hour-of-day diagnostics may explain damage, but they must not be used to patch `breakout_retest_v1.0` after failure.",
            "",
        ]
    )


def _render_break_even_analysis(status: str, context: _CostContext, rows: list[dict[str, str]]) -> str:
    stops = pd.to_numeric(context.adjusted["stop_distance_points"], errors="coerce").dropna()
    global_row = _measured_global_row(context.measured, None, "XAUUSD")
    return "\n".join(
        [
            "# Breakout-Retest Cost Break-Even Analysis",
            "",
            f"Overall status: {status}",
            f"Generated at UTC: {_now()}",
            "",
            "## Current Evidence",
            "",
            _table(
                [
                    ("Measured P95 spread points", _fmt(global_row.get("p95_spread_points", "n/a"))),
                    ("Median stop distance points", _fmt(stops.median() if len(stops) else "n/a")),
                    ("P75 stop distance points", _fmt(stops.quantile(0.75) if len(stops) else "n/a")),
                    ("Baseline gross expectancy R", _fmt(context.baseline_overall["gross_expectancy_R"])),
                    ("Measured net expectancy R", _fmt(context.measured_overall["net_expectancy_R"])),
                    ("Measured PF", _fmt(context.measured_overall["profit_factor"])),
                ]
            ),
            "",
            "## Required Stop Distance",
            "",
            _markdown_table(rows, ["Target cost_R", "Required stop points", "Interpretation"]),
            "",
            "This analysis explains why current M5 retest stops are cost-fragile. It is not a filter proposal for the failed v1.0 candidate.",
            "",
        ]
    )


def _render_candidate_feasibility(
    expert: str,
    status: str,
    reason: str,
    median_stop_points: float,
    median_spread: float,
    p95_spread: float,
    median_cost_r: float,
    p95_cost_r: float,
) -> str:
    return "\n".join(
        [
            "# Candidate Cost Feasibility",
            "",
            f"Overall status: {status}",
            f"Generated at UTC: {_now()}",
            f"Candidate: `{expert}`",
            "",
            _table(
                [
                    ("Median stop distance points", f"{median_stop_points:.2f}"),
                    ("Measured median spread points", f"{median_spread:.2f}"),
                    ("Measured P95 spread points", f"{p95_spread:.2f}"),
                    ("Median cost_R", f"{median_cost_r:.4f}"),
                    ("P95 cost_R", f"{p95_cost_r:.4f}"),
                    ("Hard max P95 cost_R", "0.3000"),
                    ("Preferred stop distance points", ">= 375"),
                    ("Reason", reason),
                ]
            ),
            "",
            "This is a pre-Phase-0 structural cost screen. It is not an edge claim, not approval, and not execution authorization.",
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


def _table(rows: list[tuple[str, str]]) -> str:
    return _markdown_table([{"Field": key, "Value": value} for key, value in rows], ["Field", "Value"])


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _fmt(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if math.isinf(number):
        return "inf"
    return f"{number:.4f}"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
