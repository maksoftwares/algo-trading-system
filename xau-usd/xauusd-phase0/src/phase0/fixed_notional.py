from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from phase0.config import ConfigError, ProjectConfig


@dataclass(frozen=True)
class FixedNotionalReportOutput:
    status: str
    report_path: Path
    summary_path: Path
    manifest_path: Path
    expert: str
    fixed_risk_usd: float
    trade_count: int
    net_expectancy_r: float
    mean_all_in_cost_r: float


def generate_fixed_notional_report(
    config: ProjectConfig,
    expert: str = "breakout_retest",
    fixed_risk_usd: float | None = None,
) -> FixedNotionalReportOutput:
    if fixed_risk_usd is None:
        project = config.phase0["project"]
        fixed_risk_usd = float(project["starting_equity_usd"]) * float(project["phase0_risk_per_trade_pct"])
    if fixed_risk_usd <= 0:
        raise ConfigError("fixed_risk_usd must be positive.")

    trade_files = _matrix_trade_files(config, expert)
    if not trade_files:
        raise ConfigError(f"No matrix trade ledgers found for expert {expert!r}.")

    cell_rows: list[dict[str, Any]] = []
    frames = []
    for path in trade_files:
        frame = _load_trade_frame(path)
        frame = _add_cost_r_fields(frame)
        metadata = _matrix_metadata(path)
        cell_rows.append(_summarize_frame(frame, fixed_risk_usd, metadata))
        frames.append(frame.assign(source_trade_file=path.name))
    all_trades = pd.concat(frames, ignore_index=True)
    overall = _summarize_frame(
        all_trades,
        fixed_risk_usd,
        {"cell_id": "ALL", "broker": "ALL", "cost_model": "ALL", "symbol": "XAUUSD"},
    )
    status = "PASS" if overall["net_expectancy_R"] > 0 and overall["profit_factor"] > 1.0 else "REVIEW"

    reports_dir = config.root / "outputs" / "reports"
    manifests_dir = config.root / "outputs" / "manifests"
    reports_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "FIXED_NOTIONAL_REPORT.md"
    summary_path = reports_dir / "FIXED_NOTIONAL_SUMMARY.csv"
    manifest_path = manifests_dir / "FIXED_NOTIONAL_REPORT_MANIFEST.json"

    pd.DataFrame([overall, *cell_rows]).to_csv(summary_path, index=False)
    report_path.write_text(
        _render_report(status, expert, fixed_risk_usd, overall, cell_rows),
        encoding="utf-8",
    )
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "expert": expert,
        "fixed_risk_usd": fixed_risk_usd,
        "report_path": str(report_path.relative_to(config.root)),
        "summary_path": str(summary_path.relative_to(config.root)),
        "overall": overall,
        "source_files": [str(path.relative_to(config.root)) for path in trade_files],
        "report_sha256": _sha256(report_path),
        "summary_sha256": _sha256(summary_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return FixedNotionalReportOutput(
        status=status,
        report_path=report_path,
        summary_path=summary_path,
        manifest_path=manifest_path,
        expert=expert,
        fixed_risk_usd=fixed_risk_usd,
        trade_count=int(overall["trade_count"]),
        net_expectancy_r=float(overall["net_expectancy_R"]),
        mean_all_in_cost_r=float(overall["mean_all_in_cost_R"]),
    )


def _matrix_trade_files(config: ProjectConfig, expert: str) -> list[Path]:
    root = config.root / "outputs" / "matrix_results" / expert
    return sorted(root.glob("*_trades.csv")) if root.exists() else []


def _load_trade_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {
        "entry_time_utc",
        "entry_price",
        "stop_loss",
        "gross_pnl_usd",
        "costs_usd",
        "net_pnl_usd",
        "r_multiple",
        "metadata_spread_points",
        "metadata_entry_slippage_price",
        "metadata_exit_slippage_price",
        "metadata_actual_risk_usd",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ConfigError(f"Trade ledger {path} missing required columns: {', '.join(missing)}")
    for column in required - {"entry_time_utc"}:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["entry_time_utc"] = pd.to_datetime(frame["entry_time_utc"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["entry_time_utc", "entry_price", "stop_loss", "r_multiple"])
    if frame.empty:
        raise ConfigError(f"Trade ledger {path} has no valid rows.")
    return frame


def _add_cost_r_fields(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    risk_price = (result["entry_price"] - result["stop_loss"]).abs().replace(0, pd.NA)
    actual_risk = result["metadata_actual_risk_usd"].abs().replace(0, pd.NA)
    point_size = _point_size_for_symbol(result)
    result["entry_spread_R"] = (result["metadata_spread_points"].fillna(0.0) * point_size / risk_price).fillna(0.0)
    result["entry_slippage_R"] = (result["metadata_entry_slippage_price"].abs().fillna(0.0) / risk_price).fillna(0.0)
    result["exit_slippage_R"] = (result["metadata_exit_slippage_price"].abs().fillna(0.0) / risk_price).fillna(0.0)
    result["commission_R"] = (result["costs_usd"].abs().fillna(0.0) / actual_risk).fillna(0.0)
    result["all_in_cost_R"] = (
        result["entry_spread_R"]
        + result["entry_slippage_R"]
        + result["exit_slippage_R"]
        + result["commission_R"]
    )
    result["net_R"] = pd.to_numeric(result["r_multiple"], errors="coerce").fillna(0.0)
    result["gross_expectancy_proxy_R"] = result["net_R"] + result["all_in_cost_R"]
    return result


def _point_size_for_symbol(frame: pd.DataFrame) -> float:
    if "symbol" not in frame.columns:
        return 0.01
    symbols = set(frame["symbol"].dropna().astype(str).str.upper())
    if symbols <= {"XAUUSD"}:
        return 0.01
    return 0.0001


def _matrix_metadata(trade_file: Path) -> dict[str, Any]:
    summary_path = trade_file.with_name(trade_file.name.replace("_trades.csv", ".csv"))
    if not summary_path.exists():
        return {"cell_id": "", "broker": "", "cost_model": "", "symbol": ""}
    row = pd.read_csv(summary_path).iloc[0].to_dict()
    return {
        "cell_id": row.get("cell_id", ""),
        "broker": row.get("broker", ""),
        "cost_model": row.get("cost_model", ""),
        "symbol": row.get("symbol", ""),
    }


def _summarize_frame(
    frame: pd.DataFrame,
    fixed_risk_usd: float,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    net_r = pd.to_numeric(frame["net_R"], errors="coerce").fillna(0.0)
    fixed_pnl = net_r * fixed_risk_usd
    equity = fixed_pnl.cumsum()
    drawdown = equity.cummax().fillna(0.0) - equity
    gross_profit_r = float(net_r[net_r > 0].sum())
    gross_loss_r = float(-net_r[net_r < 0].sum())
    profit_factor = math.inf if gross_loss_r == 0 and gross_profit_r > 0 else (
        gross_profit_r / gross_loss_r if gross_loss_r > 0 else 0.0
    )
    gross_expectancy = float(frame["gross_expectancy_proxy_R"].mean())
    mean_cost = float(frame["all_in_cost_R"].mean())
    cost_consumption = mean_cost / gross_expectancy * 100.0 if gross_expectancy > 0 else math.inf
    return {
        "cell_id": metadata.get("cell_id", ""),
        "broker": metadata.get("broker", ""),
        "cost_model": metadata.get("cost_model", ""),
        "symbol": metadata.get("symbol", ""),
        "trade_count": int(len(frame)),
        "win_rate": float((net_r > 0).mean()),
        "profit_factor": profit_factor,
        "average_R": float(net_r.mean()),
        "median_R": float(net_r.median()),
        "gross_expectancy_R": gross_expectancy,
        "net_expectancy_R": float(net_r.mean()),
        "mean_all_in_cost_R": mean_cost,
        "median_cost_R": float(frame["all_in_cost_R"].median()),
        "p95_cost_R": float(frame["all_in_cost_R"].quantile(0.95)),
        "entry_spread_R": float(frame["entry_spread_R"].mean()),
        "entry_slippage_R": float(frame["entry_slippage_R"].mean()),
        "exit_slippage_R": float(frame["exit_slippage_R"].mean()),
        "commission_R": float(frame["commission_R"].mean()),
        "cost_edge_consumption_pct": cost_consumption,
        "cost_edge_flag": _cost_flag(cost_consumption),
        "fixed_risk_usd": fixed_risk_usd,
        "fixed_notional_total_pnl_usd": float(fixed_pnl.sum()),
        "fixed_notional_max_dd_usd": float(drawdown.max()) if len(drawdown) else 0.0,
        "max_losing_streak": _max_losing_streak(net_r),
    }


def _cost_flag(cost_consumption_pct: float) -> str:
    if cost_consumption_pct <= 40:
        return "GREEN"
    if cost_consumption_pct <= 60:
        return "YELLOW"
    if cost_consumption_pct <= 80:
        return "ORANGE"
    return "RED"


def _max_losing_streak(values: pd.Series) -> int:
    current = 0
    longest = 0
    for value in values:
        if value < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _render_report(
    status: str,
    expert: str,
    fixed_risk_usd: float,
    overall: dict[str, Any],
    cell_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# Fixed-Notional Cost Report",
            "",
            f"Overall status: {status}",
            f"Generated at UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}",
            f"Expert: `{expert}`",
            f"Fixed risk per trade: `${fixed_risk_usd:.2f}`",
            "",
            "## Reporting Boundary",
            "",
            "This report is the primary no-compounding review surface. Compounding dollar PnL remains a diagnostic only and is not an operational target.",
            "",
            "## Overall",
            "",
            _markdown_table([_display_row(overall)], _display_headers()),
            "",
            "## Matrix Cells",
            "",
            _markdown_table([_display_row(row) for row in cell_rows], _display_headers()),
            "",
            "## Cost Interpretation",
            "",
            "- `gross_expectancy_R` is approximated as net R plus explicit modeled cost R.",
            "- `net_expectancy_R` is the existing trade R after modeled execution and commission effects.",
            "- `cost_edge_consumption_pct` compares mean modeled cost R against gross expectancy R.",
            "- Review #2 requires measured-cost replacement before Phase 2 authorization; this report is the assumed-cost baseline.",
            "",
        ]
    )


def _display_headers() -> list[str]:
    return [
        "Cell",
        "Broker",
        "Cost",
        "Trades",
        "Win %",
        "PF",
        "Avg R",
        "Gross R",
        "Cost R",
        "Net R",
        "Cost %",
        "Flag",
        "Fixed PnL",
        "Fixed Max DD",
    ]


def _display_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "Cell": str(row["cell_id"]),
        "Broker": str(row["broker"]),
        "Cost": str(row["cost_model"]),
        "Trades": str(row["trade_count"]),
        "Win %": f"{float(row['win_rate']) * 100:.2f}",
        "PF": _fmt(row["profit_factor"]),
        "Avg R": _fmt(row["average_R"]),
        "Gross R": _fmt(row["gross_expectancy_R"]),
        "Cost R": _fmt(row["mean_all_in_cost_R"]),
        "Net R": _fmt(row["net_expectancy_R"]),
        "Cost %": _fmt(row["cost_edge_consumption_pct"]),
        "Flag": str(row["cost_edge_flag"]),
        "Fixed PnL": f"{float(row['fixed_notional_total_pnl_usd']):.2f}",
        "Fixed Max DD": f"{float(row['fixed_notional_max_dd_usd']):.2f}",
    }


def _markdown_table(rows: list[dict[str, str]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def _fmt(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if math.isinf(number):
        return "inf"
    return f"{number:.4f}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
