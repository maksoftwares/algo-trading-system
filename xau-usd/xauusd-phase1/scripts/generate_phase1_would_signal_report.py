from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


DECISION_LOG = "decision_log.csv"


@dataclass(frozen=True)
class WouldSignalCheck:
    name: str
    status: str
    message: str


@dataclass(frozen=True)
class WouldSignalReport:
    status: str
    report_path: Path
    csv_path: Path
    signal_count: int
    cluster_count: int
    observer_conflict_counts: dict[str, int]
    checks: tuple[WouldSignalCheck, ...]


def generate_phase1_would_signal_report(
    files_dir: Path,
    report_path: Path | None = None,
    csv_path: Path | None = None,
) -> WouldSignalReport:
    files_dir = files_dir.resolve()
    if report_path is None:
        report_path = Path.cwd() / "outputs" / "reports" / "PHASE1_WOULD_SIGNAL_REPORT.md"
    if csv_path is None:
        csv_path = report_path.with_name("PHASE1_WOULD_SIGNAL_REVIEW.csv")

    rows = _read_csv(files_dir / DECISION_LOG)
    signal_rows = _would_signal_rows(rows)
    clusters = _signal_clusters(signal_rows)
    observer_conflict_counts = _observer_conflict_counts(rows)
    checks = [
        _check_signal_rows(signal_rows),
        _check_signal_clusters(clusters),
        _check_signal_rows_are_dry(signal_rows),
        _check_signal_rows_permission_locked(signal_rows),
    ]
    status = _overall_status(checks)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    _write_review_csv(csv_path, signal_rows, clusters)
    report_path.write_text(
        _render_report(status, files_dir, checks, signal_rows, clusters, csv_path, observer_conflict_counts),
        encoding="utf-8",
    )
    return WouldSignalReport(
        status=status,
        report_path=report_path,
        csv_path=csv_path,
        signal_count=len(signal_rows),
        cluster_count=len(clusters),
        observer_conflict_counts=observer_conflict_counts,
        checks=tuple(checks),
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _would_signal_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    signal_rows: list[dict[str, str]] = []
    for row in rows:
        if row.get("br_would_signal", "").lower() == "true" or row.get("br_stage", "") == "WOULD_SIGNAL":
            signal = dict(row)
            signal["observer"] = "breakout_retest"
            signal_rows.append(signal)
        if row.get("sbr_would_signal", "").lower() == "true" or row.get("sbr_stage", "") == "WOULD_SIGNAL":
            signal = dict(row)
            signal["observer"] = "swing_breakout_retest_v0"
            signal["br_direction"] = row.get("sbr_direction", "")
            signal["br_level_kind"] = row.get("sbr_level_kind", "")
            signal["br_level_price"] = row.get("sbr_level_price", "")
            signal["br_entry_price"] = row.get("sbr_entry_price", "")
            signal["br_stop_loss"] = row.get("sbr_stop_loss", "")
            signal["br_take_profit"] = row.get("sbr_take_profit", "")
            signal["br_stop_distance_points"] = row.get("sbr_stop_distance_points", "")
            signal["br_reason_code"] = row.get("sbr_reason_code", "")
            signal_rows.append(signal)
    return signal_rows


def _observer_conflict_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts = {
        "br_only": 0,
        "sbr_only": 0,
        "both_same_direction": 0,
        "both_opposite_direction": 0,
    }
    for row in rows:
        br_signal = _is_true_signal(row, "br")
        sbr_signal = _is_true_signal(row, "sbr")
        if br_signal and sbr_signal:
            br_direction = row.get("br_direction", "").upper()
            sbr_direction = row.get("sbr_direction", "").upper()
            if br_direction and br_direction == sbr_direction:
                counts["both_same_direction"] += 1
            else:
                counts["both_opposite_direction"] += 1
        elif br_signal:
            counts["br_only"] += 1
        elif sbr_signal:
            counts["sbr_only"] += 1
    return counts


def _is_true_signal(row: dict[str, str], prefix: str) -> bool:
    return (
        row.get(f"{prefix}_would_signal", "").lower() == "true"
        or row.get(f"{prefix}_stage", "") == "WOULD_SIGNAL"
    )


def _check_signal_rows(rows: list[dict[str, str]]) -> WouldSignalCheck:
    if rows:
        return WouldSignalCheck("would_signal_rows", "PASS", f"Would-signal rows observed: {len(rows)}.")
    return WouldSignalCheck("would_signal_rows", "WARN", "No would-signal rows observed yet.")


def _check_signal_clusters(clusters: list[dict[str, str]]) -> WouldSignalCheck:
    if clusters:
        return WouldSignalCheck("would_signal_clusters", "PASS", f"Setup clusters observed: {len(clusters)}.")
    return WouldSignalCheck("would_signal_clusters", "WARN", "No would-signal clusters available yet.")


def _check_signal_rows_are_dry(rows: list[dict[str, str]]) -> WouldSignalCheck:
    bad = [
        row.get("timestamp_broker", "")
        for row in rows
        if row.get("dry_run", "").lower() != "true" or row.get("lifecycle_state", "") != "DRY_RUN"
    ]
    if bad:
        return WouldSignalCheck("would_signal_dry_run", "FAIL", f"Rows outside dry-run state: {len(bad)}.")
    return WouldSignalCheck("would_signal_dry_run", "PASS", "All would-signal rows stayed dry-run.")


def _check_signal_rows_permission_locked(rows: list[dict[str, str]]) -> WouldSignalCheck:
    bad = [row.get("timestamp_broker", "") for row in rows if row.get("trade_permission", "").lower() != "false"]
    if bad:
        return WouldSignalCheck("would_signal_permission_lock", "FAIL", f"Rows with permission not false: {len(bad)}.")
    return WouldSignalCheck("would_signal_permission_lock", "PASS", "All would-signal rows kept permission false.")


def _overall_status(checks: list[WouldSignalCheck]) -> str:
    if any(check.status == "FAIL" for check in checks):
        return "FAIL"
    if any(check.status == "WARN" for check in checks):
        return "WARN"
    return "PASS"


def _signal_key(row: dict[str, str]) -> tuple[str, ...]:
    return (
        row.get("observer", "breakout_retest"),
        row.get("br_direction", ""),
        row.get("br_level_kind", ""),
        row.get("br_level_price", ""),
        row.get("br_entry_price", ""),
        row.get("br_stop_loss", ""),
        row.get("br_take_profit", ""),
    )


def _signal_clusters(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    clusters: dict[tuple[str, ...], dict[str, str]] = {}
    order: list[tuple[str, ...]] = []
    for row in rows:
        key = _signal_key(row)
        if key not in clusters:
            clusters[key] = {
                "cluster_id": f"WS{len(order) + 1:03d}",
                "observer": key[0],
                "direction": key[1],
                "level_kind": key[2],
                "level_price": key[3],
                "entry_price": key[4],
                "stop_loss": key[5],
                "take_profit": key[6],
                "first_bar_time": row.get("bar_time", ""),
                "last_bar_time": row.get("bar_time", ""),
                "rows": "0",
            }
            order.append(key)
        cluster = clusters[key]
        cluster["rows"] = str(int(cluster["rows"]) + 1)
        cluster["last_bar_time"] = row.get("bar_time", "")
    return [clusters[key] for key in order]


def _cluster_id_for_row(row: dict[str, str], clusters: list[dict[str, str]]) -> str:
    for cluster in clusters:
        if (
            row.get("observer", "breakout_retest") == cluster.get("observer", "breakout_retest")
            and
            row.get("br_direction", "") == cluster["direction"]
            and row.get("br_level_kind", "") == cluster["level_kind"]
            and row.get("br_level_price", "") == cluster["level_price"]
            and row.get("br_entry_price", "") == cluster["entry_price"]
            and row.get("br_stop_loss", "") == cluster["stop_loss"]
            and row.get("br_take_profit", "") == cluster["take_profit"]
        ):
            return cluster["cluster_id"]
    return ""


def _write_review_csv(
    path: Path,
    signal_rows: list[dict[str, str]],
    clusters: list[dict[str, str]],
) -> None:
    fieldnames = [
        "cluster_id",
        "observer",
        "timestamp_broker",
        "timestamp_utc",
        "timestamp_local",
        "bar_time",
        "run_id",
        "symbol",
        "direction",
        "level_kind",
        "level_price",
        "entry_price",
        "stop_loss",
        "take_profit",
        "stop_distance_points",
        "spread_points",
        "risk_state",
        "execution_state",
        "server_time_status",
        "reason_code",
        "trade_permission",
        "dry_run",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in signal_rows:
            writer.writerow(
                {
                    "cluster_id": _cluster_id_for_row(row, clusters),
                    "observer": row.get("observer", "breakout_retest"),
                    "timestamp_broker": row.get("timestamp_broker", ""),
                    "timestamp_utc": row.get("timestamp_utc", ""),
                    "timestamp_local": row.get("timestamp_local", ""),
                    "bar_time": row.get("bar_time", ""),
                    "run_id": row.get("run_id", ""),
                    "symbol": row.get("symbol", ""),
                    "direction": row.get("br_direction", ""),
                    "level_kind": row.get("br_level_kind", ""),
                    "level_price": row.get("br_level_price", ""),
                    "entry_price": row.get("br_entry_price", ""),
                    "stop_loss": row.get("br_stop_loss", ""),
                    "take_profit": row.get("br_take_profit", ""),
                    "stop_distance_points": row.get("br_stop_distance_points", ""),
                    "spread_points": row.get("spread_points", ""),
                    "risk_state": row.get("risk_state", ""),
                    "execution_state": row.get("execution_state", ""),
                    "server_time_status": row.get("server_time_status", ""),
                    "reason_code": row.get("br_reason_code", ""),
                    "trade_permission": row.get("trade_permission", ""),
                    "dry_run": row.get("dry_run", ""),
                }
            )


def _render_report(
    status: str,
    files_dir: Path,
    checks: list[WouldSignalCheck],
    signal_rows: list[dict[str, str]],
    clusters: list[dict[str, str]],
    csv_path: Path,
    observer_conflict_counts: dict[str, int],
) -> str:
    return "\n".join(
        [
            "# Phase 1 Would-Signal Report",
            "",
            f"Overall status: {status}",
            "",
            f"Files directory: `{files_dir}`",
            "",
            "## Checks",
            "",
            _markdown_table(
                [{"Check": item.name, "Status": item.status, "Message": item.message} for item in checks],
                ["Check", "Status", "Message"],
            ),
            "",
            "## Summary",
            "",
            f"- Would-signal rows: {len(signal_rows)}",
            f"- Setup clusters: {len(clusters)}",
            f"- Directions observed: {', '.join(_unique(signal_rows, 'br_direction')) or 'none'}",
            f"- Level kinds observed: {', '.join(_unique(signal_rows, 'br_level_kind')) or 'none'}",
            f"- Observers observed: {', '.join(_unique(signal_rows, 'observer')) or 'none'}",
            f"- Review CSV: `{csv_path}`",
            "",
            "## Observer Conflict Counts",
            "",
            _observer_conflict_table(observer_conflict_counts),
            "",
            "## Setup Clusters",
            "",
            _markdown_table(
                [
                    {
                        "Cluster": cluster["cluster_id"],
                        "Observer": cluster["observer"],
                        "Rows": cluster["rows"],
                        "Direction": cluster["direction"],
                        "Level Kind": cluster["level_kind"],
                        "Level": cluster["level_price"],
                        "Entry": cluster["entry_price"],
                        "Stop": cluster["stop_loss"],
                        "Target": cluster["take_profit"],
                        "First Bar": cluster["first_bar_time"],
                        "Last Bar": cluster["last_bar_time"],
                    }
                    for cluster in clusters
                ],
                [
                    "Cluster",
                    "Observer",
                    "Rows",
                    "Direction",
                    "Level Kind",
                    "Level",
                    "Entry",
                    "Stop",
                    "Target",
                    "First Bar",
                    "Last Bar",
                ],
            ),
            "",
            "## Direction Counts",
            "",
            _count_table(row.get("br_direction", "") for row in signal_rows),
            "",
            "## Level Kind Counts",
            "",
            _count_table(row.get("br_level_kind", "") for row in signal_rows),
            "",
            "## Would-Signal Rows",
            "",
            _markdown_table(
                [
                    {
                        "Observer": row.get("observer", "breakout_retest"),
                        "Broker Time": row.get("timestamp_broker", ""),
                        "Bar Time": row.get("bar_time", ""),
                        "Direction": row.get("br_direction", ""),
                        "Level Kind": row.get("br_level_kind", ""),
                        "Level": row.get("br_level_price", ""),
                        "Entry": row.get("br_entry_price", ""),
                        "Stop": row.get("br_stop_loss", ""),
                        "Target": row.get("br_take_profit", ""),
                        "Spread": row.get("spread_points", ""),
                        "Risk": row.get("risk_state", ""),
                        "Execution": row.get("execution_state", ""),
                        "Permission": row.get("trade_permission", ""),
                        "Dry Run": row.get("dry_run", ""),
                    }
                    for row in signal_rows[-50:]
                ],
                [
                    "Observer",
                    "Broker Time",
                    "Bar Time",
                    "Direction",
                    "Level Kind",
                    "Level",
                    "Entry",
                    "Stop",
                    "Target",
                    "Spread",
                    "Risk",
                    "Execution",
                    "Permission",
                    "Dry Run",
                ],
            ),
            "",
        ]
    )


def _unique(rows: list[dict[str, str]], column: str) -> list[str]:
    return sorted({row.get(column, "") for row in rows if row.get(column, "")})


def _count_table(values) -> str:
    counts: dict[str, int] = {}
    for value in values:
        key = value or "blank"
        counts[key] = counts.get(key, 0) + 1
    return _markdown_table(
        [{"Value": key, "Count": str(value)} for key, value in sorted(counts.items())],
        ["Value", "Count"],
    )


def _observer_conflict_table(counts: dict[str, int]) -> str:
    labels = {
        "br_only": "BR only",
        "sbr_only": "SBR only",
        "both_same_direction": "Both same direction",
        "both_opposite_direction": "Both opposite direction",
    }
    return _markdown_table(
        [{"Bucket": labels[key], "Count": str(counts.get(key, 0))} for key in labels],
        ["Bucket", "Count"],
    )


def _markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_escape(str(row.get(column, ""))) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Phase 1 dry-run would-signal report.")
    parser.add_argument("--files-dir", type=Path, required=True, help="MT5 MQL5/Files directory.")
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("outputs") / "reports" / "PHASE1_WOULD_SIGNAL_REPORT.md",
        help="Markdown report path.",
    )
    args = parser.parse_args(argv)

    output = generate_phase1_would_signal_report(args.files_dir, args.report)
    print(f"Phase 1 would-signal report: {output.status}")
    print(output.report_path)
    print(f"Review CSV: {output.csv_path}")
    print(f"Would-signal rows: {output.signal_count}")
    print(f"Setup clusters: {output.cluster_count}")
    for check in output.checks:
        print(f"{check.status}: {check.name} - {check.message}")
    return 1 if output.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
