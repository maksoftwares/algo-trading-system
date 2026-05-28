from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from simulate_phase3_from_would_signals import PHASE2_AUTHORITY_SENTENCE


DECISION_COLUMNS = (
    "family_event_id",
    "primary_event_id",
    "decision_bar_time",
    "direction",
    "level_kind",
    "stop_distance_points",
    "spread_points",
    "measured_cost_r_proxy",
    "net_after_proxy_from_gross_r",
    "net_delta_vs_assumed_baseline_r",
    "diagnosis",
    "suggested_reviewer_annotation",
    "codex_review_decision",
    "future_rule",
    "review_notes",
)


def generate_suspend_family_decision(rows_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = _read_csv(rows_path)
    primary_rows = [row for row in rows if row.get("primary_stream_allowed") == "true"]
    decision_rows = [_decision_row(row) for row in primary_rows]
    status = {
        "status": "REVIEW_READY_KEEP_SUSPENDED",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": PHASE2_AUTHORITY_SENTENCE,
        "rows_path": str(rows_path),
        "raw_suspend_rows": len(rows),
        "primary_suspend_rows": len(primary_rows),
        "unique_family_events": len({row.get("family_event_id", "") for row in decision_rows if row.get("family_event_id")}),
        "codex_review_decision_counts": dict(sorted(Counter(row["codex_review_decision"] for row in decision_rows).items())),
        "suggested_annotation_counts": dict(
            sorted(Counter(row["suggested_reviewer_annotation"] for row in decision_rows).items())
        ),
        "future_rule_counts": dict(sorted(Counter(row["future_rule"] for row in decision_rows).items())),
        "decision_rows": decision_rows,
    }
    json_path = output_dir / "PHASE3_SUSPEND_FAMILY_DECISION.json"
    md_path = output_dir / "PHASE3_SUSPEND_FAMILY_DECISION.md"
    csv_path = output_dir / "PHASE3_SUSPEND_FAMILY_DECISION.csv"
    _write_csv(csv_path, decision_rows)
    json_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(status), encoding="utf-8")
    return json_path


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _decision_row(row: dict[str, str]) -> dict[str, str]:
    annotation = row.get("suggested_reviewer_annotation", "") or "UNKNOWN"
    return {
        "family_event_id": row.get("family_event_id", ""),
        "primary_event_id": row.get("event_id", ""),
        "decision_bar_time": row.get("decision_bar_time", ""),
        "direction": row.get("direction", ""),
        "level_kind": row.get("level_kind", ""),
        "stop_distance_points": row.get("stop_distance_points", ""),
        "spread_points": row.get("spread_points", ""),
        "measured_cost_r_proxy": row.get("measured_cost_r_proxy", ""),
        "net_after_proxy_from_gross_r": row.get("net_after_proxy_from_gross_r", ""),
        "net_delta_vs_assumed_baseline_r": row.get("net_delta_vs_assumed_baseline_r", ""),
        "diagnosis": row.get("diagnosis", ""),
        "suggested_reviewer_annotation": annotation,
        "codex_review_decision": "KEEP_SUSPENDED",
        "future_rule": _future_rule(annotation),
        "review_notes": _review_notes(annotation),
    }


def _future_rule(annotation: str) -> str:
    if annotation == "TIGHT_STOP_ISSUE":
        return "REQUIRE_TIGHT_STOP_COST_BLOCK"
    if annotation == "COST_ISSUE":
        return "REQUIRE_COST_R_AND_SPREAD_BLOCK"
    if annotation == "DUPLICATED_OBSERVER_ISSUE":
        return "REQUIRE_FAMILY_DEDUP_NO_EXTRA_EXPOSURE"
    return "REQUIRE_MANUAL_REVIEW_BEFORE_PROMOTION"


def _review_notes(annotation: str) -> str:
    if annotation == "TIGHT_STOP_ISSUE":
        return "Keep suspended in future paper-shadow design unless tight-stop cost survival is proven."
    if annotation == "COST_ISSUE":
        return "Keep suspended in future paper-shadow design unless cost-in-R and spread gates block this condition."
    if annotation == "DUPLICATED_OBSERVER_ISSUE":
        return "Observer duplicate must not create additional paper or live exposure."
    return "Keep suspended pending manual review; current evidence does not justify promotion."


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DECISION_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _render_markdown(status: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 3 Suspend Family Decision",
            "",
            PHASE2_AUTHORITY_SENTENCE,
            "",
            f"Overall status: {status['status']}",
            "",
            "## Summary",
            "",
            _table(
                [
                    ("Raw suspend rows", str(status["raw_suspend_rows"])),
                    ("Primary suspend rows", str(status["primary_suspend_rows"])),
                    ("Unique family events", str(status["unique_family_events"])),
                    ("Decision counts", str(status["codex_review_decision_counts"])),
                    ("Suggested annotation counts", str(status["suggested_annotation_counts"])),
                    ("Future rule counts", str(status["future_rule_counts"])),
                ]
            ),
            "",
            "## Decision",
            "",
            "All primary suspended family events remain `KEEP_SUSPENDED` in the future design. This is not owner approval and does not authorize paper-mode execution. It only converts the current cost-survival evidence into explicit future implementation requirements.",
            "",
            "## Primary Suspended Events",
            "",
            _rows_table(status["decision_rows"]),
            "",
        ]
    )


def _rows_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "No primary suspended events."
    columns = (
        "family_event_id",
        "primary_event_id",
        "decision_bar_time",
        "direction",
        "measured_cost_r_proxy",
        "net_after_proxy_from_gross_r",
        "diagnosis",
        "suggested_reviewer_annotation",
        "codex_review_decision",
        "future_rule",
    )
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(_escape(row.get(column, "")) for column in columns) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def _table(rows: list[tuple[str, str]]) -> str:
    if not rows:
        return "No rows."
    body = [f"| {_escape(key)} | {_escape(value)} |" for key, value in rows]
    return "\n".join(["| Field | Value |", "| --- | --- |", *body])


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    phase3_root = Path(__file__).resolve().parents[1]
    reports = phase3_root / "outputs" / "reports"
    parser = argparse.ArgumentParser(description="Generate Phase 3 suspend-family decision artifact.")
    parser.add_argument("--rows-path", type=Path, default=reports / "PHASE3_SUSPEND_FAMILY_ROWS.csv")
    parser.add_argument("--output-dir", type=Path, default=reports)
    args = parser.parse_args(argv)
    path = generate_suspend_family_decision(args.rows_path, args.output_dir)
    print(f"Phase 3 suspend-family decision: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
