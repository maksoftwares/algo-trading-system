from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from simulate_phase3_from_would_signals import PHASE2_AUTHORITY_SENTENCE, _source_row_is_safe


MATERIAL_FIELDS = (
    "observer",
    "direction",
    "level_kind",
    "level_price",
    "entry_price",
    "stop_loss",
    "take_profit",
    "stop_distance_points",
)


def generate_family_dedup_audit(input_csv: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = _read_csv(input_csv)
    safe_rows = [row for row in rows if _source_row_is_safe(row)]
    groups = _groups(safe_rows)
    audit_rows = [_audit_row(index, key, group) for index, (key, group) in enumerate(groups.items(), start=1)]
    classification_counts = dict(sorted(Counter(row["classification"] for row in audit_rows).items()))
    summary = {
        "status": "REVIEW_READY",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": PHASE2_AUTHORITY_SENTENCE,
        "input_csv": str(input_csv),
        "safe_source_rows": len(safe_rows),
        "family_group_count": len(audit_rows),
        "multi_row_group_count": sum(1 for row in audit_rows if int(row["group_size"]) > 1),
        "classification_counts": classification_counts,
        "rows": audit_rows,
    }
    csv_path = output_dir / "PHASE3_FAMILY_DEDUP_AUDIT.csv"
    md_path = output_dir / "PHASE3_FAMILY_DEDUP_AUDIT.md"
    json_path = output_dir / "PHASE3_FAMILY_DEDUP_AUDIT.json"
    _write_csv(csv_path, audit_rows)
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(summary), encoding="utf-8")
    return json_path


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _groups(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (row.get("symbol", ""), row.get("bar_time", "") or row.get("timestamp_broker", ""))
        grouped.setdefault(key, []).append(row)
    return grouped


def _audit_row(index: int, key: tuple[str, str], group: list[dict[str, str]]) -> dict[str, str]:
    differing_fields = _differing_fields(group)
    classification = _classification(group, differing_fields)
    symbol, bar_time = key
    return {
        "family_event_id": f"FAM{index:05d}",
        "symbol": symbol,
        "bar_time": bar_time,
        "group_size": str(len(group)),
        "classification": classification,
        "differing_fields": ";".join(differing_fields),
        "source_cluster_ids": _joined(group, "cluster_id"),
        "observers": _joined(group, "observer"),
        "directions": _joined(group, "direction"),
        "level_kinds": _joined(group, "level_kind"),
        "level_prices": _joined(group, "level_price"),
        "entry_prices": _joined(group, "entry_price"),
        "stop_losses": _joined(group, "stop_loss"),
        "take_profits": _joined(group, "take_profit"),
        "stop_distance_points": _joined(group, "stop_distance_points"),
    }


def _differing_fields(group: list[dict[str, str]]) -> list[str]:
    differing: list[str] = []
    for field in MATERIAL_FIELDS:
        values = {row.get(field, "") for row in group}
        if len(values) > 1:
            differing.append(field)
    return differing


def _classification(group: list[dict[str, str]], differing_fields: list[str]) -> str:
    if len(group) <= 1:
        return "TRUE_DUPLICATE"
    if "direction" in differing_fields:
        return "SAME_BAR_DIRECTION_CONFLICT"
    if "level_kind" in differing_fields or "level_price" in differing_fields:
        return "SAME_BAR_DISTINCT_LEVEL"
    execution_fields = {"entry_price", "stop_loss", "take_profit", "stop_distance_points"}
    if any(field in differing_fields for field in execution_fields):
        return "SAME_BAR_EXECUTION_CONFLICT"
    return "TRUE_DUPLICATE"


def _joined(group: list[dict[str, str]], field: str) -> str:
    values: list[str] = []
    for row in group:
        value = row.get(field, "")
        if value and value not in values:
            values.append(value)
    return ";".join(values)


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "family_event_id",
        "symbol",
        "bar_time",
        "group_size",
        "classification",
        "differing_fields",
        "source_cluster_ids",
        "observers",
        "directions",
        "level_kinds",
        "level_prices",
        "entry_prices",
        "stop_losses",
        "take_profits",
        "stop_distance_points",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _render_markdown(summary: dict[str, Any]) -> str:
    rows = summary.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    return "\n".join(
        [
            "# Phase 3 Family De-Duplication Audit",
            "",
            PHASE2_AUTHORITY_SENTENCE,
            "",
            f"Overall status: {summary['status']}",
            "",
            "## Summary",
            "",
            _table(
                [
                    ("Safe source rows", str(summary["safe_source_rows"])),
                    ("Family groups", str(summary["family_group_count"])),
                    ("Multi-row groups", str(summary["multi_row_group_count"])),
                ]
            ),
            "",
            "## Classification Counts",
            "",
            _table(sorted((key, str(value)) for key, value in summary["classification_counts"].items())),
            "",
            "## Multi-Row Groups",
            "",
            _rows_table([row for row in rows if int(str(row.get("group_size", "0"))) > 1]),
            "",
            "## Scope",
            "",
            "This audit does not change execution eligibility. It only identifies whether the current same-bar family grouping is collapsing true duplicates, conflicts, or potentially distinct same-bar opportunities.",
            "",
        ]
    )


def _rows_table(rows: list[Any]) -> str:
    if not rows:
        return "No multi-row groups."
    columns = [
        "family_event_id",
        "bar_time",
        "group_size",
        "classification",
        "differing_fields",
        "observers",
        "directions",
        "level_kinds",
        "level_prices",
        "entry_prices",
        "stop_losses",
        "take_profits",
        "stop_distance_points",
    ]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for raw in rows:
        row = raw if isinstance(raw, dict) else {}
        body.append("| " + " | ".join(_escape(row.get(column, "")) for column in columns) + " |")
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
    repo_root = phase3_root.parents[1]
    reports = phase3_root / "outputs" / "reports"
    parser = argparse.ArgumentParser(description="Generate Phase 3 family de-duplication audit.")
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports" / "PHASE1_WOULD_SIGNAL_REVIEW.csv",
    )
    parser.add_argument("--output-dir", type=Path, default=reports)
    args = parser.parse_args(argv)
    path = generate_family_dedup_audit(args.input_csv, args.output_dir)
    print(f"Phase 3 family de-dup audit: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
