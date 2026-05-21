from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from phase0.config import ConfigError, ProjectConfig
from phase0.constants import EXPERTS


@dataclass(frozen=True)
class IntrabarAmbiguityOutput:
    expert: str
    report_path: Path
    summary_path: Path
    trade_files: int
    total_trades: int
    ambiguous_exit_trades: int
    same_timestamp_exit_trades: int
    adverse_first_profit_factor: str


def generate_intrabar_ambiguity_report(
    config: ProjectConfig,
    expert: str,
) -> list[IntrabarAmbiguityOutput]:
    experts = EXPERTS if expert == "all" else (expert,)
    if expert != "all" and expert not in EXPERTS:
        raise ConfigError(f"Unknown expert {expert!r}.")
    return [_generate_one(config, item) for item in experts]


def _generate_one(config: ProjectConfig, expert: str) -> IntrabarAmbiguityOutput:
    matrix_dir = config.root / "outputs" / "matrix_results" / expert
    trade_paths = sorted(matrix_dir.glob("*_trades.csv")) if matrix_dir.exists() else []
    rows = [_summarize_trade_file(path) for path in trade_paths]
    total_trades = sum(int(row["trade_count"]) for row in rows)
    ambiguous = sum(int(row["ambiguous_exit_trades"]) for row in rows)
    same_timestamp = sum(int(row["same_timestamp_exit_trades"]) for row in rows)
    all_pnl = []
    for path in trade_paths:
        frame = pd.read_csv(path)
        if "net_pnl_usd" in frame.columns:
            all_pnl.extend(pd.to_numeric(frame["net_pnl_usd"], errors="coerce").dropna().tolist())
    pf = _profit_factor(all_pnl)

    output_dir = config.root / "outputs" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / f"{expert}_intrabar_ambiguity_summary.csv"
    report_path = output_dir / f"{expert}_intrabar_ambiguity_report.md"
    pd.DataFrame(rows, columns=_SUMMARY_COLUMNS).to_csv(summary_path, index=False)
    report_path.write_text(
        _render_report(
            expert=expert,
            rows=rows,
            trade_files=len(trade_paths),
            total_trades=total_trades,
            ambiguous_exit_trades=ambiguous,
            same_timestamp_exit_trades=same_timestamp,
            adverse_first_profit_factor=pf,
            summary_path=summary_path.relative_to(config.root).as_posix(),
        ),
        encoding="utf-8",
    )
    return IntrabarAmbiguityOutput(
        expert=expert,
        report_path=report_path,
        summary_path=summary_path,
        trade_files=len(trade_paths),
        total_trades=total_trades,
        ambiguous_exit_trades=ambiguous,
        same_timestamp_exit_trades=same_timestamp,
        adverse_first_profit_factor=pf,
    )


_SUMMARY_COLUMNS = (
    "path",
    "trade_count",
    "ambiguous_exit_trades",
    "same_timestamp_exit_trades",
    "adverse_first_profit_factor",
)


def _summarize_trade_file(path: Path) -> dict[str, Any]:
    frame = pd.read_csv(path)
    pnl = pd.to_numeric(frame.get("net_pnl_usd", pd.Series(dtype=float)), errors="coerce").dropna()
    ambiguous = _truthy_series(frame.get("metadata_ambiguous_exit", pd.Series(dtype=object)))
    same_timestamp = _same_timestamp_exit_count(frame)
    return {
        "path": path.as_posix(),
        "trade_count": int(len(frame)),
        "ambiguous_exit_trades": int(ambiguous.sum()),
        "same_timestamp_exit_trades": same_timestamp,
        "adverse_first_profit_factor": _profit_factor(pnl.tolist()),
    }


def _truthy_series(series: pd.Series) -> pd.Series:
    if series.empty:
        return pd.Series(dtype=bool)
    return series.fillna(False).astype(str).str.lower().isin({"1", "true", "yes"})


def _same_timestamp_exit_count(frame: pd.DataFrame) -> int:
    if "entry_time_utc" not in frame.columns or "exit_time_utc" not in frame.columns:
        return 0
    entries = pd.to_datetime(frame["entry_time_utc"], utc=True, errors="coerce")
    exits = pd.to_datetime(frame["exit_time_utc"], utc=True, errors="coerce")
    return int((entries.notna() & exits.notna() & (entries == exits)).sum())


def _profit_factor(pnl_values: list[float]) -> str:
    gross_profit = sum(value for value in pnl_values if value > 0)
    gross_loss = -sum(value for value in pnl_values if value < 0)
    if gross_profit <= 0 and gross_loss <= 0:
        return "n/a"
    if gross_loss == 0:
        return "inf"
    return f"{gross_profit / gross_loss:.6g}"


def _render_report(
    *,
    expert: str,
    rows: list[dict[str, Any]],
    trade_files: int,
    total_trades: int,
    ambiguous_exit_trades: int,
    same_timestamp_exit_trades: int,
    adverse_first_profit_factor: str,
    summary_path: str,
) -> str:
    ambiguity_pct = 0.0 if total_trades == 0 else ambiguous_exit_trades / total_trades * 100.0
    same_timestamp_pct = 0.0 if total_trades == 0 else same_timestamp_exit_trades / total_trades * 100.0
    return "\n".join(
        [
            f"# Intrabar Ambiguity Report: {expert}",
            "",
            "This report is generated from Phase 0 matrix trade CSVs. The engine uses the configured "
            "`adverse_first` policy when a bar touches both stop loss and take profit.",
            "",
            "## Summary",
            "",
            f"- Trade files inspected: {trade_files}",
            f"- Total trades: {total_trades}",
            f"- Ambiguous exit trades: {ambiguous_exit_trades} ({ambiguity_pct:.2f}%)",
            f"- Same-timestamp entry/exit trades: {same_timestamp_exit_trades} ({same_timestamp_pct:.2f}%)",
            f"- PF under adverse-first policy: {adverse_first_profit_factor}",
            f"- PF under neutral assumption: not_available_without_tick_or_replay_model",
            f"- PF under worst-case assumption: adverse_first_currently_used",
            "",
            "## File Summary",
            "",
            _markdown_table(rows, list(_SUMMARY_COLUMNS)) if rows else "No trade files found.",
            "",
            "## Review Note",
            "",
            "Neutral intrabar ordering is intentionally not inferred from OHLC bars. If this report shows "
            "material ambiguity, the next review step is tick-level replay or a separately specified "
            "neutral ordering simulator before Phase 1 approval.",
            "",
            f"CSV summary: {summary_path}",
            "",
        ]
    )


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(str(row.get(column, "")) for column in columns) + " |" for row in rows]
    return "\n".join([header, separator, *body])
