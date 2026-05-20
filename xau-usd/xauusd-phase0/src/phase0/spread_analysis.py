from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from phase0.config import ConfigError, ProjectConfig


REQUIRED_SPREAD_COLUMNS = (
    "broker_time",
    "gmt_time",
    "local_time",
    "account",
    "server",
    "symbol",
    "bid",
    "ask",
    "spread_price",
    "spread_points",
    "point",
    "digits",
    "session_label",
    "is_rollover_window",
)


@dataclass(frozen=True)
class SpreadAnalysisOutput:
    measured_cost_model_path: Path
    report_path: Path
    source_files: tuple[Path, ...]


def analyze_spread_logs(
    config: ProjectConfig,
    input_dir: str | Path | None = None,
    file_glob: str = "spread_log_*.csv",
) -> SpreadAnalysisOutput:
    directory = Path(input_dir) if input_dir is not None else config.root / "outputs" / "logs"
    if not directory.is_absolute():
        directory = config.root / directory
    files = sorted(directory.glob(file_glob))
    if not files:
        raise ConfigError(f"No spread logger CSV files found in {directory} matching {file_glob}.")

    frame = _load_spread_logs(files)
    metrics = _spread_metrics(frame)
    reports_dir = config.root / "outputs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    measured_path = reports_dir / "cost_model_measured.csv"
    report_path = reports_dir / "spread_distribution_report.md"
    metrics.to_csv(measured_path, index=False)
    report_path.write_text(_render_spread_report(metrics, files), encoding="utf-8")
    return SpreadAnalysisOutput(measured_path, report_path, tuple(files))


def _load_spread_logs(files: list[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in files:
        frame = pd.read_csv(path)
        missing = [column for column in REQUIRED_SPREAD_COLUMNS if column not in frame.columns]
        if missing:
            raise ConfigError(f"Spread log {path} missing column(s): {', '.join(missing)}.")
        frame["source_file"] = path.name
        frames.append(frame)
    combined = pd.concat(frames, ignore_index=True)
    combined["spread_points"] = pd.to_numeric(combined["spread_points"], errors="coerce")
    combined["gmt_time"] = pd.to_datetime(combined["gmt_time"], errors="coerce", utc=True)
    combined = combined.dropna(subset=["spread_points", "gmt_time"])
    if combined.empty:
        raise ConfigError("Spread logs contain no usable spread rows.")
    combined["hour_utc"] = combined["gmt_time"].dt.hour
    combined["day_of_week_utc"] = combined["gmt_time"].dt.day_name()
    return combined


def _spread_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    rows.extend(_group_rows(frame, "global", pd.Series(["all"] * len(frame), index=frame.index)))
    rows.extend(_group_rows(frame, "hour_utc", frame["hour_utc"]))
    rows.extend(_group_rows(frame, "day_of_week_utc", frame["day_of_week_utc"]))

    rollover = frame[
        frame["is_rollover_window"].astype(str).str.lower().isin({"true", "1", "yes"})
        | (frame["session_label"].astype(str).str.upper() == "ROLLOVER")
    ]
    if not rollover.empty:
        rows.extend(
            _group_rows(rollover, "rollover", pd.Series(["all"] * len(rollover), index=rollover.index))
        )

    if "event_label" in frame.columns:
        news = frame[frame["event_label"].fillna("").astype(str).str.len() > 0]
        if not news.empty:
            rows.extend(_group_rows(news, "news_window", news["event_label"].astype(str)))
    return pd.DataFrame(rows)


def _group_rows(frame: pd.DataFrame, scope: str, buckets: pd.Series) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    working = frame.assign(bucket=buckets.astype(str))
    for bucket, group in working.groupby("bucket", sort=True):
        spread = pd.to_numeric(group["spread_points"], errors="coerce").dropna()
        if spread.empty:
            continue
        rows.append(
            {
                "scope": scope,
                "bucket": bucket,
                "broker": _broker_label(group),
                "symbol": ",".join(sorted(group["symbol"].astype(str).unique())),
                "observations": int(len(spread)),
                "median_spread_points": float(spread.median()),
                "p95_spread_points": float(spread.quantile(0.95)),
                "max_spread_points": float(spread.max()),
            }
        )
    return rows


def _render_spread_report(metrics: pd.DataFrame, files: list[Path]) -> str:
    return "\n".join(
        [
            "# Spread Distribution Report",
            "",
            "## Source Files",
            "",
            "\n".join(f"- {path}" for path in files),
            "",
            "## Global Distribution",
            "",
            _markdown_table(metrics[metrics["scope"] == "global"]),
            "",
            "## Hourly Distribution",
            "",
            _markdown_table(metrics[metrics["scope"] == "hour_utc"]),
            "",
            "## Day-Of-Week Distribution",
            "",
            _markdown_table(metrics[metrics["scope"] == "day_of_week_utc"]),
            "",
            "## Rollover Distribution",
            "",
            _markdown_table(metrics[metrics["scope"] == "rollover"]),
            "",
            "## News-Window Distribution",
            "",
            _markdown_table(metrics[metrics["scope"] == "news_window"]),
            "",
        ]
    )


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "No rows."
    columns = [
        "scope",
        "bucket",
        "broker",
        "symbol",
        "observations",
        "median_spread_points",
        "p95_spread_points",
        "max_spread_points",
    ]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = []
    for _, row in frame[columns].iterrows():
        rows.append("| " + " | ".join(_format_value(row[column]) for column in columns) + " |")
    return "\n".join([header, separator, *rows])


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _broker_label(group: pd.DataFrame) -> str:
    if "broker" not in group.columns:
        return "all"
    values = sorted(value for value in group["broker"].dropna().astype(str).unique() if value)
    return ",".join(values) if values else "all"
