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

FRESHNESS_COLUMNS = ("tick_time", "tick_time_msc", "seconds_since_tick", "tick_fresh")


@dataclass(frozen=True)
class SpreadAnalysisOutput:
    status: str
    measured_cost_model_path: Path
    measured_report_path: Path
    report_path: Path
    source_files: tuple[Path, ...]
    observation_count: int
    observed_days: int


def analyze_spread_logs(
    config: ProjectConfig,
    input_dir: str | Path | None = None,
    file_glob: str = "spread_log_*.csv",
    min_observations: int = 500,
    min_observed_days: int = 5,
    allow_pending: bool = False,
) -> SpreadAnalysisOutput:
    directory = Path(input_dir) if input_dir is not None else config.root / "outputs" / "logs"
    if not directory.is_absolute():
        directory = config.root / directory
    files = sorted(directory.glob(file_glob))
    reports_dir = config.root / "outputs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    measured_path = reports_dir / "cost_model_measured.csv"
    measured_report_path = reports_dir / "MEASURED_COST_MODEL.md"
    report_path = reports_dir / "spread_distribution_report.md"

    if not files and allow_pending:
        measured_report_path.write_text(
            _render_measured_cost_model_report(
                status="PENDING",
                metrics=pd.DataFrame(),
                files=[],
                observation_count=0,
                observed_days=0,
                min_observations=min_observations,
                min_observed_days=min_observed_days,
                note=f"No spread logger CSV files found in {directory} matching {file_glob}.",
            ),
            encoding="utf-8",
        )
        report_path.write_text("# Spread Distribution Report\n\nNo spread logs found.\n", encoding="utf-8")
        return SpreadAnalysisOutput("PENDING", measured_path, measured_report_path, report_path, tuple(), 0, 0)
    if not files:
        raise ConfigError(f"No spread logger CSV files found in {directory} matching {file_glob}.")

    frame = _load_spread_logs(files)
    source_row_count = int(frame.attrs.get("source_row_count", len(frame)))
    stale_row_count = int(frame.attrs.get("stale_row_count", 0))
    missing_tick_fresh_row_count = int(frame.attrs.get("missing_tick_fresh_row_count", 0))
    weekend_row_count = int(frame.attrs.get("weekend_row_count", 0))
    freshness_available = bool(frame.attrs.get("freshness_available", False))
    missing_freshness_columns = str(frame.attrs.get("missing_freshness_columns", ""))
    metrics = _spread_metrics(frame)
    observation_count = int(len(frame))
    observed_days = int(frame["gmt_time"].dt.date.nunique())
    status = "PASS" if observation_count >= min_observations and observed_days >= min_observed_days else "PENDING"
    metrics.to_csv(measured_path, index=False)
    report_path.write_text(
        _render_spread_report(
            metrics,
            files,
            source_row_count,
            stale_row_count,
            missing_tick_fresh_row_count,
            weekend_row_count,
            freshness_available,
            missing_freshness_columns,
        ),
        encoding="utf-8",
    )
    measured_report_path.write_text(
        _render_measured_cost_model_report(
            status=status,
            metrics=metrics,
            files=files,
            observation_count=observation_count,
            observed_days=observed_days,
            min_observations=min_observations,
            min_observed_days=min_observed_days,
            source_row_count=source_row_count,
            stale_row_count=stale_row_count,
            missing_tick_fresh_row_count=missing_tick_fresh_row_count,
            weekend_row_count=weekend_row_count,
            freshness_available=freshness_available,
            missing_freshness_columns=missing_freshness_columns,
            note=_measured_cost_note(
                freshness_available,
                missing_freshness_columns,
                stale_row_count,
                missing_tick_fresh_row_count,
                weekend_row_count,
            ),
        ),
        encoding="utf-8",
    )
    return SpreadAnalysisOutput(
        status,
        measured_path,
        measured_report_path,
        report_path,
        tuple(files),
        observation_count,
        observed_days,
    )


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
    source_row_count = int(len(combined))
    missing_freshness_columns = [column for column in FRESHNESS_COLUMNS if column not in combined.columns]
    freshness_available = "tick_fresh" in combined.columns
    combined["spread_points"] = pd.to_numeric(combined["spread_points"], errors="coerce")
    combined["gmt_time"] = pd.to_datetime(combined["gmt_time"], errors="coerce", utc=True)
    combined = combined.dropna(subset=["spread_points", "gmt_time"])
    if freshness_available:
        combined["seconds_since_tick"] = pd.to_numeric(
            combined.get("seconds_since_tick", pd.Series(index=combined.index, dtype="float64")),
            errors="coerce",
        )
        missing_tick_fresh_row_count = int(combined["tick_fresh"].isna().sum())
        fresh_mask = combined["tick_fresh"].astype(str).str.lower().isin({"true", "1", "yes"})
    else:
        missing_tick_fresh_row_count = int(len(combined))
        fresh_mask = pd.Series(True, index=combined.index)
    stale_row_count = int((~fresh_mask).sum())
    combined = combined[fresh_mask].copy()
    if combined.empty:
        raise ConfigError("Spread logs contain no usable fresh spread rows.")
    combined["hour_utc"] = combined["gmt_time"].dt.hour
    combined["day_of_week_utc"] = combined["gmt_time"].dt.day_name()
    weekend_mask = combined["day_of_week_utc"].isin({"Saturday", "Sunday"})
    weekend_row_count = int(weekend_mask.sum())
    combined = combined[~weekend_mask].copy()
    if combined.empty:
        raise ConfigError("Spread logs contain no usable weekday market rows after filtering weekend quotes.")
    combined.attrs["source_row_count"] = source_row_count
    combined.attrs["stale_row_count"] = stale_row_count
    combined.attrs["missing_tick_fresh_row_count"] = missing_tick_fresh_row_count
    combined.attrs["weekend_row_count"] = weekend_row_count
    combined.attrs["freshness_available"] = freshness_available
    combined.attrs["missing_freshness_columns"] = ",".join(missing_freshness_columns)
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


def _render_spread_report(
    metrics: pd.DataFrame,
    files: list[Path],
    source_row_count: int,
    stale_row_count: int,
    missing_tick_fresh_row_count: int,
    weekend_row_count: int,
    freshness_available: bool,
    missing_freshness_columns: str,
) -> str:
    return "\n".join(
        [
            "# Spread Distribution Report",
            "",
            "## Admission Filters",
            "",
            f"- Source rows: {source_row_count}",
            f"- Freshness columns available: {'yes' if freshness_available else 'no'}",
            f"- Missing freshness columns: {missing_freshness_columns or 'none'}",
            f"- Rows excluded because tick_fresh was not true or was missing: {stale_row_count}",
            f"- Rows missing tick_fresh: {missing_tick_fresh_row_count}",
            f"- Weekend/closed-market rows excluded: {weekend_row_count}",
            f"- Weekday rows used: {source_row_count - stale_row_count - weekend_row_count}",
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


def _render_measured_cost_model_report(
    status: str,
    metrics: pd.DataFrame,
    files: list[Path],
    observation_count: int,
    observed_days: int,
    min_observations: int,
    min_observed_days: int,
    source_row_count: int = 0,
    stale_row_count: int = 0,
    missing_tick_fresh_row_count: int = 0,
    weekend_row_count: int = 0,
    freshness_available: bool = False,
    missing_freshness_columns: str = "",
    note: str = "",
) -> str:
    global_rows = metrics[metrics["scope"] == "global"] if not metrics.empty else pd.DataFrame()
    return "\n".join(
        [
            "# Measured Cost Model",
            "",
            f"Overall status: {status}",
            "",
            "## Decision",
            "",
            _measured_decision_text(status),
            "",
            "## Coverage",
            "",
            _markdown_table_from_rows(
                [
                    {
                        "Observed Rows": str(observation_count),
                        "Required Rows": str(min_observations),
                        "Observed Days": str(observed_days),
                        "Required Days": str(min_observed_days),
                        "Source Rows": str(source_row_count),
                        "Rows Missing Tick Fresh": str(missing_tick_fresh_row_count),
                        "Weekend Rows Excluded": str(weekend_row_count),
                        "Tick Freshness": "available" if freshness_available else "legacy_missing",
                        "Source Files": str(len(files)),
                    }
                ],
                [
                    "Observed Rows",
                    "Required Rows",
                    "Observed Days",
                    "Required Days",
                    "Source Rows",
                    "Rows Missing Tick Fresh",
                    "Weekend Rows Excluded",
                    "Tick Freshness",
                    "Source Files",
                ],
            ),
            "",
            "## Global Cost Model",
            "",
            _markdown_table(global_rows),
            "",
            "## Source Files",
            "",
            "\n".join(f"- {path}" for path in files) if files else "No source files yet.",
            "",
            "## Note",
            "",
            note,
            "",
            "## Why Observed Days Reset",
            "",
            (
                "Legacy spread logs before the freshness-aware logger redeployment did not include "
                "`tick_fresh` / `seconds_since_tick`, so they are retained as diagnostic source files "
                "but excluded from authoritative measured-cost gating. Fresh observed market days, "
                "not source-file count or legacy row count, control PASS/PENDING."
                if (freshness_available and missing_tick_fresh_row_count > 0) or missing_freshness_columns
                else "Observed days count only admitted fresh market rows that pass the current measured-cost filters."
            ),
            "",
            "Missing freshness columns: " + (missing_freshness_columns or "none"),
            "",
        ]
    )


def _measured_decision_text(status: str) -> str:
    if status == "PASS":
        return "Measured spread evidence is sufficient for measured-cost revalidation."
    return "Measured spread evidence is not sufficient yet. Keep Phase 2 readiness pending."


def _measured_cost_note(
    freshness_available: bool,
    missing_freshness_columns: str,
    stale_row_count: int,
    missing_tick_fresh_row_count: int,
    weekend_row_count: int,
) -> str:
    freshness_text = (
        "after filtering to tick_fresh=true rows. "
        f"Rows excluded because tick_fresh was not true or was missing: {stale_row_count}; "
        f"rows missing tick_fresh: {missing_tick_fresh_row_count}."
        if freshness_available
        else "from legacy spread logs that do not expose tick freshness fields."
    )
    return (
        "Measured cost model generated from passive spread logger data "
        f"{freshness_text} Weekend/closed-market rows excluded: {weekend_row_count}. "
        f"Missing freshness columns: {missing_freshness_columns or 'none'}."
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


def _markdown_table_from_rows(rows: list[dict[str, str]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(row.get(column, "") for column in columns) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _broker_label(group: pd.DataFrame) -> str:
    if "broker" not in group.columns:
        return "all"
    values = sorted(value for value in group["broker"].dropna().astype(str).unique() if value)
    return ",".join(values) if values else "all"
