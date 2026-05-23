from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


DEFAULT_REPORT = Path("outputs") / "reports" / "PHASE2_PAPER_LEDGER_SCHEMA_REPORT.md"
DEFAULT_COLUMNS_CSV = Path("outputs") / "reports" / "PHASE2_PAPER_LEDGER_COLUMNS.csv"
SCHEMA_DOC = Path("docs") / "PHASE2_PAPER_LEDGER_SCHEMA.md"

REQUIRED_COLUMNS = (
    ("event_id", "string", "paper ledger", "Unique stable event id."),
    ("paper_session_id", "string", "paper ledger", "Stable for one paper-mode run."),
    ("source_run_id", "string", "decision_log.csv", "Must match source run_id."),
    ("source_decision_row_number", "integer", "decision_log.csv", "One-based source row number."),
    ("timestamp_broker", "datetime", "decision_log.csv", "Broker timestamp from source row."),
    ("timestamp_utc", "datetime", "decision_log.csv", "UTC timestamp from source row."),
    ("timestamp_local", "datetime", "decision_log.csv", "Local timestamp from source row."),
    ("symbol", "string", "decision_log.csv", "Approved symbol."),
    ("expert_family", "string", "policy", "Current approved family identifier."),
    ("expert", "string", "decision_log.csv", "Source observer or future paper expert id."),
    ("observer", "string", "decision_log.csv", "Source observer lane."),
    ("decision_bar_time", "datetime", "decision_log.csv", "Source bar_time."),
    ("paper_event_type", "enum", "paper ledger", "WOULD_OPEN, WOULD_CLOSE, STATE_UPDATE, or BLOCKED."),
    ("paper_state", "enum", "paper ledger", "PAPER_FLAT, PAPER_OPEN, PAPER_CLOSED, or PAPER_BLOCKED."),
    ("direction", "enum", "decision_log.csv", "LONG, SHORT, or NONE."),
    ("level_kind", "string", "decision_log.csv", "Source level type."),
    ("level_price", "decimal", "decision_log.csv", "Source level price."),
    ("entry_price_projected", "decimal", "decision_log.csv", "Source projected entry."),
    ("stop_price_projected", "decimal", "decision_log.csv", "Source projected stop."),
    ("target_price_projected", "decimal", "decision_log.csv", "Source projected target."),
    ("stop_distance_points", "decimal", "decision_log.csv", "Source projected stop distance."),
    ("risk_pct_requested", "decimal", "risk policy", "Requested paper risk percentage."),
    ("risk_pct_allowed", "decimal", "risk policy", "Allowed risk after lock checks."),
    ("risk_state", "enum", "decision_log.csv", "Source risk state."),
    ("spread_points", "decimal", "decision_log.csv", "Source spread."),
    ("slippage_points_assumed", "decimal", "paper fill model", "Assumed paper slippage."),
    ("modeled_cost_R", "decimal", "Phase 0 baseline", "Modeled baseline all-in cost in R."),
    ("measured_cost_R", "decimal", "Phase 2 measurement", "Measured paper cost proxy in R."),
    ("net_expectancy_R_baseline", "decimal", "Phase 0 baseline", "Baseline net expectancy in R."),
    (
        "net_expectancy_R_after_measured_cost",
        "decimal",
        "Phase 2 measurement",
        "Viability metric after measured costs.",
    ),
    ("execution_state", "enum", "decision_log.csv", "Source execution state."),
    ("news_state", "enum", "decision_log.csv", "Source news state."),
    ("router_regime", "enum", "decision_log.csv", "Source regime/router state."),
    ("session", "enum", "decision_log.csv", "Source session state."),
    ("trade_permission", "boolean", "decision_log.csv", "Must remain false at source."),
    ("dry_run", "boolean", "decision_log.csv", "Must remain true at source."),
    ("block_reason", "string", "decision_log.csv", "Source blocked reason."),
    ("kill_rule_state", "enum", "paper policy", "NORMAL, COST_WATCH, SUSPEND_FAMILY, or MANUAL_LOCK."),
    ("review_status", "enum", "reviewer", "PENDING, REVIEWED, ACCEPTED, or REJECTED."),
    ("review_notes", "string", "reviewer", "Human review notes."),
)

REQUIRED_TOKENS = (
    "paper-only",
    "dry_run=true",
    "trade_permission=false",
    "+0.10R",
    "SUSPEND_FAMILY",
    "breakout_retest",
    "swing_breakout_retest_v0",
)


@dataclass(frozen=True)
class SchemaCheck:
    name: str
    status: str
    message: str


@dataclass(frozen=True)
class SchemaReportOutput:
    status: str
    report_path: Path
    columns_csv_path: Path
    checks: tuple[SchemaCheck, ...]


def generate_phase2_paper_ledger_schema_report(
    root: Path,
    report_path: Path | None = None,
    columns_csv_path: Path | None = None,
) -> SchemaReportOutput:
    root = root.resolve()
    report_path = (root / DEFAULT_REPORT if report_path is None else report_path).resolve()
    columns_csv_path = (root / DEFAULT_COLUMNS_CSV if columns_csv_path is None else columns_csv_path).resolve()
    schema_doc = root / SCHEMA_DOC

    text = schema_doc.read_text(encoding="utf-8", errors="replace") if schema_doc.exists() else ""
    checks = [
        _doc_exists_check(schema_doc),
        _required_columns_check(text),
        _required_controls_check(text),
    ]
    status = _overall_status(checks)

    columns_csv_path.parent.mkdir(parents=True, exist_ok=True)
    _write_columns_csv(columns_csv_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(status, root, schema_doc, columns_csv_path, checks), encoding="utf-8")

    return SchemaReportOutput(status, report_path, columns_csv_path, tuple(checks))


def _doc_exists_check(path: Path) -> SchemaCheck:
    if path.exists() and path.stat().st_size > 0:
        return SchemaCheck("schema_doc", "PASS", f"Found `{path}`.")
    return SchemaCheck("schema_doc", "FAIL", f"Missing or empty `{path}`.")


def _required_columns_check(text: str) -> SchemaCheck:
    missing = [name for name, *_ in REQUIRED_COLUMNS if name not in text]
    if missing:
        return SchemaCheck("required_columns", "FAIL", "Missing column(s): " + ", ".join(missing))
    return SchemaCheck("required_columns", "PASS", f"All {len(REQUIRED_COLUMNS)} required columns are documented.")


def _required_controls_check(text: str) -> SchemaCheck:
    missing = [token for token in REQUIRED_TOKENS if token not in text]
    if missing:
        return SchemaCheck("required_controls", "FAIL", "Missing control token(s): " + ", ".join(missing))
    return SchemaCheck("required_controls", "PASS", "Paper boundary, cost threshold, and single-family controls are documented.")


def _overall_status(checks: list[SchemaCheck]) -> str:
    if any(check.status == "FAIL" for check in checks):
        return "FAIL"
    if any(check.status == "WARN" for check in checks):
        return "WARN"
    return "PASS"


def _write_columns_csv(path: Path) -> None:
    fieldnames = ("column", "required", "type", "source", "validation")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for column, data_type, source, validation in REQUIRED_COLUMNS:
            writer.writerow(
                {
                    "column": column,
                    "required": "yes",
                    "type": data_type,
                    "source": source,
                    "validation": validation,
                }
            )


def _render_report(
    status: str,
    root: Path,
    schema_doc: Path,
    columns_csv_path: Path,
    checks: list[SchemaCheck],
) -> str:
    return "\n".join(
        [
            "# Phase 2 Paper Ledger Schema Report",
            "",
            f"Overall status: {status}",
            "",
            "## Decision",
            "",
            _decision(status),
            "",
            "## Checks",
            "",
            _markdown_table(
                [{"Check": check.name, "Status": check.status, "Message": check.message} for check in checks],
                ["Check", "Status", "Message"],
            ),
            "",
            "## Schema Artifacts",
            "",
            f"- Schema doc: `{schema_doc}`",
            f"- Column template: `{columns_csv_path}`",
            f"- Required columns: {len(REQUIRED_COLUMNS)}",
            "",
            "## Boundary",
            "",
            "- This report prepares Phase 2 paper-mode evidence only.",
            "- It does not authorize paper-mode implementation.",
            "- It does not change the current dry-run account boundary.",
            "- Paper-mode implementation remains blocked until Phase 2 readiness is PASS.",
            f"- Workspace root: `{root}`",
            "",
        ]
    )


def _decision(status: str) -> str:
    if status == "PASS":
        return "The paper-ledger evidence contract is defined and ready for reviewer inspection."
    return "The paper-ledger evidence contract is incomplete. Keep Phase 2 readiness pending."


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
    parser = argparse.ArgumentParser(description="Generate the Phase 2 paper-ledger schema report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--columns-csv", type=Path, default=None)
    args = parser.parse_args(argv)

    output = generate_phase2_paper_ledger_schema_report(args.root, args.report, args.columns_csv)
    print(f"Phase 2 paper-ledger schema report: {output.status}")
    print(output.report_path)
    print(output.columns_csv_path)
    for check in output.checks:
        print(f"{check.status}: {check.name} - {check.message}")
    return 1 if output.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
