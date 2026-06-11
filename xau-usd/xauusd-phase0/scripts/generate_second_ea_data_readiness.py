from __future__ import annotations

import csv
import json
import sys
import hashlib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PHASE0_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PHASE0_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from phase0.second_ea_partial_data import validate_partial_data_decision
from phase0.constants import COST_MODELS, SECOND_EA_CAMPAIGN_CANDIDATES, SECOND_EA_LANE_A_CANDIDATES

RAW_ROOT = PHASE0_ROOT / "data" / "raw"
REPORT_MD = PHASE0_ROOT / "outputs" / "reports" / "SECOND_EA_DATA_EXTENSION_READINESS.md"
REPORT_JSON = PHASE0_ROOT / "outputs" / "reports" / "SECOND_EA_DATA_EXTENSION_READINESS.json"
MANIFEST_CSV = PHASE0_ROOT / "outputs" / "reports" / "SECOND_EA_MATRIX_MANIFEST.csv"
TRUE_HOLDOUT_CUTOFF = pd.Timestamp("2025-06-30T23:59:59Z")


@dataclass(frozen=True)
class ReadinessRow:
    broker: str
    symbol: str
    timeframe: str
    start_utc: str
    end_utc: str
    bar_count: int
    missing_bar_count: int
    duplicate_bar_count: int
    largest_gap_minutes: float
    true_holdout_excluded: bool
    history_asymmetry_note: str
    data_status: str


def main() -> int:
    rows = build_readiness_rows()
    overall_status = "PASS" if all(row.data_status == "PASS" for row in rows) else "PARTIAL"
    stable_payload = {
        "overall_status": overall_status,
        "true_holdout_cutoff_utc": TRUE_HOLDOUT_CUTOFF.isoformat(),
        "rows": [asdict(row) for row in rows],
    }
    readiness_content_sha256 = hashlib.sha256(
        json.dumps(stable_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    partial_decision = validate_partial_data_decision(
        PHASE0_ROOT,
        current_readiness_content_sha256=readiness_content_sha256,
    )
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "readiness_content_sha256": readiness_content_sha256,
        "overall_status": overall_status,
        "matrix_runs_allowed": overall_status == "PASS"
        or (overall_status == "PARTIAL" and partial_decision.status == "OWNER_ACCEPTED_PARTIAL"),
        "owner_accepted_partial_data": partial_decision.status == "OWNER_ACCEPTED_PARTIAL",
        "partial_data_decision_status": partial_decision.status,
        "true_holdout_cutoff_utc": TRUE_HOLDOUT_CUTOFF.isoformat(),
        "rows": [asdict(row) for row in rows],
    }
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_markdown(payload), encoding="utf-8")
    write_matrix_manifest(rows)
    print(f"SECOND_EA_DATA_READINESS_{overall_status} report={REPORT_MD}")
    return 0


def build_readiness_rows() -> list[ReadinessRow]:
    targets = {
        "capital_com": {
            "M5": ("2016-01-01", "2025-06-30"),
            "M15": ("2016-01-01", "2025-06-30"),
            "H1": ("2016-01-01", "2025-06-30"),
            "H4": ("2016-01-01", "2025-06-30"),
            "D1": ("2016-01-01", "2025-06-30"),
        },
        "pepperstone": {
            "M5": ("2016-01-01", "2025-06-30"),
            "M15": ("2016-01-01", "2025-06-30"),
            "H1": ("2016-01-01", "2025-06-30"),
            "H4": ("2016-01-01", "2025-06-30"),
            "D1": ("2016-01-01", "2025-06-30"),
        },
        "dukascopy": {
            "M5": ("2016-01-01", "2025-06-30"),
            "M15": ("2016-01-01", "2025-06-30"),
            "H1": ("2016-01-01", "2025-06-30"),
            "H4": ("2016-01-01", "2025-06-30"),
            "D1": ("2016-01-01", "2025-06-30"),
        },
    }
    rows: list[ReadinessRow] = []
    for broker, timeframe_targets in targets.items():
        for timeframe, (target_start, target_end) in timeframe_targets.items():
            rows.append(assess_series(broker, "XAUUSD", timeframe, target_start, target_end))
    return rows


def assess_series(
    broker: str,
    symbol: str,
    timeframe: str,
    target_start: str,
    target_end: str,
) -> ReadinessRow:
    files = sorted((RAW_ROOT / broker).glob(f"{symbol}_{timeframe}_*.csv"))
    timestamps = load_timestamps(files)
    target_start_ts = pd.Timestamp(f"{target_start}T00:00:00Z")
    target_end_ts = pd.Timestamp(f"{target_end}T23:59:59Z")
    if timestamps.empty:
        return ReadinessRow(
            broker=broker,
            symbol=symbol,
            timeframe=timeframe,
            start_utc="",
            end_utc="",
            bar_count=0,
            missing_bar_count=0,
            duplicate_bar_count=0,
            largest_gap_minutes=0.0,
            true_holdout_excluded=True,
            history_asymmetry_note=f"No offline raw {symbol} {timeframe} files found for {broker}.",
            data_status="FAIL",
        )

    timestamps = timestamps.sort_values()
    duplicate_count = int(timestamps.duplicated().sum())
    unique = timestamps.drop_duplicates()
    start = unique.iloc[0]
    end = unique.iloc[-1]
    diffs = unique.diff().dropna()
    largest_gap_minutes = float(diffs.max().total_seconds() / 60.0) if not diffs.empty else 0.0
    expected_minutes = _timeframe_minutes(timeframe)
    missing_bar_count = int((diffs.dt.total_seconds() / 60.0 > expected_minutes).sum())
    excluded = bool(end <= TRUE_HOLDOUT_CUTOFF)

    has_start = start <= target_start_ts + pd.Timedelta(days=3)
    has_end = end >= target_end_ts - pd.Timedelta(days=1)
    status = "PASS" if has_start and has_end and excluded else "PARTIAL"
    note = (
        "Full target window is available offline."
        if status == "PASS"
        else f"Target {target_start} through {target_end}; actual {start.isoformat()} through {end.isoformat()}."
    )
    return ReadinessRow(
        broker=broker,
        symbol=symbol,
        timeframe=timeframe,
        start_utc=start.isoformat(),
        end_utc=end.isoformat(),
        bar_count=int(len(unique)),
        missing_bar_count=missing_bar_count,
        duplicate_bar_count=duplicate_count,
        largest_gap_minutes=largest_gap_minutes,
        true_holdout_excluded=excluded,
        history_asymmetry_note=note,
        data_status=status,
    )


def load_timestamps(files: list[Path]) -> pd.Series:
    series: list[pd.Series] = []
    for path in files:
        header = pd.read_csv(path, nrows=0)
        if {"<DATE>", "<TIME>"}.issubset(header.columns):
            frame = pd.read_csv(path, usecols=["<DATE>", "<TIME>"])
            raw = frame["<DATE>"].astype(str) + " " + frame["<TIME>"].astype(str)
            parsed = pd.to_datetime(raw, format="%Y.%m.%d %H:%M:%S", utc=True, errors="coerce")
        elif "timestamp_utc" in header.columns:
            frame = pd.read_csv(path, usecols=["timestamp_utc"])
            parsed = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
        elif "timestamp" in header.columns:
            frame = pd.read_csv(path, usecols=["timestamp"])
            parsed = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
        else:
            continue
        series.append(parsed.dropna())
    if not series:
        return pd.Series([], dtype="datetime64[ns, UTC]")
    return pd.concat(series, ignore_index=True)


def render_markdown(payload: dict[str, object]) -> str:
    status = str(payload["overall_status"])
    runs_allowed = bool(payload["matrix_runs_allowed"])
    lines = [
        "# Second EA Data Extension Readiness",
        "",
        f"Overall status: {status}",
        f"Generated at UTC: {payload['generated_at_utc']}",
        f"Readiness content SHA256: {payload['readiness_content_sha256']}",
        f"Matrix runs allowed: {str(runs_allowed).lower()}",
        f"Owner accepted partial data: {str(payload['owner_accepted_partial_data']).lower()}",
        f"Partial data decision status: {payload['partial_data_decision_status']}",
        "",
    ]
    if status != "PASS":
        lines.extend(
            [
                "## Campaign Blocker",
                "",
                "`DATA_WINDOW_ASYMMETRY_PRESENT`",
                "",
                "The campaign may not run candidate matrices until this report is PASS or the owner explicitly signs `OWNER_ACCEPTED_PARTIAL_DATA`.",
                "",
            ]
        )
    lines.extend(
        [
            "## Readiness Table",
            "",
            "| broker | symbol | timeframe | start_utc | end_utc | bar_count | missing_bar_count | duplicate_bar_count | largest_gap_minutes | true_holdout_excluded | data_status | history_asymmetry_note |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for row in payload["rows"]:  # type: ignore[index]
        lines.append(
            "| {broker} | {symbol} | {timeframe} | {start_utc} | {end_utc} | {bar_count} | {missing_bar_count} | {duplicate_bar_count} | {largest_gap_minutes:.1f} | {true_holdout_excluded} | {data_status} | {history_asymmetry_note} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Data was assessed from existing offline raw CSV files only.",
            "- Processed-bar files were intentionally not inspected because some filenames extend to 2025-07-01; this readiness audit preserves the 2025-06-30 true-holdout cutoff.",
            "- No MT5 runtime, terminal, broker account, or passive exporter was used.",
            "- Missing-bar counts are gap-event counts from consecutive timestamps and include normal market closures.",
            "",
        ]
    )
    return "\n".join(lines)


def write_matrix_manifest(rows: list[ReadinessRow]) -> None:
    MANIFEST_CSV.parent.mkdir(parents=True, exist_ok=True)
    broker_rows = _broker_matrix_windows(rows)
    with MANIFEST_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "candidate_id",
                "lane",
                "cell_id",
                "broker",
                "cost_model",
                "symbol",
                "timeframe_scope",
                "start_utc",
                "end_utc",
                "data_status",
                "true_holdout_excluded",
                "history_asymmetry_note",
                "matrix_cell_status",
                "run_permission",
            ],
        )
        writer.writeheader()
        for candidate in SECOND_EA_CAMPAIGN_CANDIDATES:
            lane = "A" if candidate in SECOND_EA_LANE_A_CANDIDATES else "B"
            cell_id = 1
            for broker in ("capital_com", "pepperstone", "dukascopy"):
                broker_window = broker_rows[broker]
                for cost_model in COST_MODELS:
                    writer.writerow(
                        {
                            "candidate_id": candidate,
                            "lane": lane,
                            "cell_id": cell_id,
                            "broker": broker,
                            "cost_model": cost_model,
                            "symbol": "XAUUSD",
                            "timeframe_scope": "M5/M15/H1/H4/D1 readiness intersection",
                            "start_utc": broker_window["start_utc"],
                            "end_utc": broker_window["end_utc"],
                            "data_status": broker_window["data_status"],
                            "true_holdout_excluded": broker_window["true_holdout_excluded"],
                            "history_asymmetry_note": broker_window["history_asymmetry_note"],
                            "matrix_cell_status": "BLOCKED_PREFLIGHT",
                            "run_permission": "false",
                        }
                    )
                    cell_id += 1


def _broker_matrix_windows(rows: list[ReadinessRow]) -> dict[str, dict[str, str]]:
    by_broker: dict[str, list[ReadinessRow]] = {}
    for row in rows:
        by_broker.setdefault(row.broker, []).append(row)

    windows: dict[str, dict[str, str]] = {}
    for broker, broker_rows in by_broker.items():
        starts = [pd.Timestamp(row.start_utc) for row in broker_rows if row.start_utc]
        ends = [pd.Timestamp(row.end_utc) for row in broker_rows if row.end_utc]
        statuses = {row.data_status for row in broker_rows}
        status = "FAIL" if "FAIL" in statuses else ("PARTIAL" if "PARTIAL" in statuses else "PASS")
        asymmetric_notes = [
            f"{row.timeframe}: {row.history_asymmetry_note}"
            for row in broker_rows
            if row.data_status != "PASS"
        ]
        windows[broker] = {
            "start_utc": max(starts).isoformat() if starts else "",
            "end_utc": min(ends).isoformat() if ends else "",
            "data_status": status,
            "true_holdout_excluded": str(all(row.true_holdout_excluded for row in broker_rows)).lower(),
            "history_asymmetry_note": " | ".join(asymmetric_notes)
            if asymmetric_notes
            else "Full assessed timeframe intersection is available offline.",
        }
    return windows


def _timeframe_minutes(timeframe: str) -> int:
    return {
        "M5": 5,
        "M15": 15,
        "H1": 60,
        "H4": 240,
        "D1": 1440,
    }[timeframe]


if __name__ == "__main__":
    raise SystemExit(main())
