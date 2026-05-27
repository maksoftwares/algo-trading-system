from __future__ import annotations

import argparse
import csv
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from simulate_phase3_from_would_signals import (
    PHASE2_AUTHORITY_SENTENCE,
    VALID_COST_MODES,
    simulate_phase3_from_would_signals,
)


COST_MODE_ORDER = (
    "entry_only_proxy",
    "entry_exit_proxy",
    "p95_fresh_proxy",
    "stress_2x_p95_proxy",
)


def generate_cost_mode_comparison(input_csv: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="phase3-cost-modes-") as temp_dir:
        temp_root = Path(temp_dir)
        for mode in COST_MODE_ORDER:
            if mode not in VALID_COST_MODES:
                raise ValueError(f"Unsupported cost mode configured for comparison: {mode}")
            simulation = simulate_phase3_from_would_signals(
                input_csv=input_csv,
                output_dir=temp_root / mode,
                cost_mode=mode,
            )
            summary = _read_json(simulation.summary_path)
            ledger_rows = _read_csv(simulation.ledger_path)
            rows.append(_comparison_row(mode, summary, ledger_rows))

    status = {
        "status": "REVIEW_READY",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": PHASE2_AUTHORITY_SENTENCE,
        "input_csv": str(input_csv),
        "cost_modes": COST_MODE_ORDER,
        "rows": rows,
    }
    csv_path = output_dir / "PHASE3_COST_MODE_COMPARISON.csv"
    md_path = output_dir / "PHASE3_COST_MODE_COMPARISON.md"
    json_path = output_dir / "PHASE3_COST_MODE_COMPARISON.json"
    _write_csv(csv_path, rows)
    json_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(status), encoding="utf-8")
    return json_path


def _comparison_row(mode: str, summary: dict[str, Any], ledger_rows: list[dict[str, str]]) -> dict[str, Any]:
    kill_counts = _mapping(summary.get("kill_rule_counts"))
    suspend_family_ids = {
        row.get("family_event_id", "")
        for row in ledger_rows
        if row.get("kill_rule_state") == "SUSPEND_FAMILY" and row.get("family_event_id")
    }
    return {
        "cost_mode": mode,
        "raw_observer_events": summary.get("raw_observer_event_count", 0),
        "family_unique_events": summary.get("family_unique_event_count", 0),
        "primary_stream_allowed": summary.get("primary_stream_allowed_count", 0),
        "observer_duplicates": summary.get("observer_duplicate_count", 0),
        "observer_conflicts": summary.get("observer_conflict_count", 0),
        "median_proxy_cost_r": summary.get("median_proxy_cost_r"),
        "mean_proxy_cost_r": summary.get("mean_proxy_cost_r"),
        "median_net_after_proxy_cost_r": summary.get("median_net_after_proxy_cost_r"),
        "mean_net_after_proxy_cost_r": summary.get("mean_net_after_proxy_cost_r"),
        "gross_expectancy_r_source": summary.get("gross_expectancy_r_source"),
        "baseline_assumed_cost_r": summary.get("baseline_assumed_cost_r"),
        "baseline_net_expectancy_r": summary.get("baseline_net_expectancy_r"),
        "median_net_delta_vs_assumed_baseline_r": summary.get("median_net_delta_vs_assumed_baseline_r"),
        "mean_net_delta_vs_assumed_baseline_r": summary.get("mean_net_delta_vs_assumed_baseline_r"),
        "normal_count": kill_counts.get("NORMAL", 0),
        "cost_watch_count": kill_counts.get("COST_WATCH", 0),
        "suspend_family_count": kill_counts.get("SUSPEND_FAMILY", 0),
        "suspend_family_unique_events": len(suspend_family_ids),
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "cost_mode",
        "raw_observer_events",
        "family_unique_events",
        "primary_stream_allowed",
        "observer_duplicates",
        "observer_conflicts",
        "median_proxy_cost_r",
        "mean_proxy_cost_r",
        "median_net_after_proxy_cost_r",
        "mean_net_after_proxy_cost_r",
        "gross_expectancy_r_source",
        "baseline_assumed_cost_r",
        "baseline_net_expectancy_r",
        "median_net_delta_vs_assumed_baseline_r",
        "mean_net_delta_vs_assumed_baseline_r",
        "normal_count",
        "cost_watch_count",
        "suspend_family_count",
        "suspend_family_unique_events",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _render_markdown(status: dict[str, Any]) -> str:
    rows = status.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    return "\n".join(
        [
            "# Phase 3 Cost Mode Comparison",
            "",
            PHASE2_AUTHORITY_SENTENCE,
            "",
            f"Overall status: {status['status']}",
            "",
            "## Comparison",
            "",
            _rows_table(rows),
            "",
            "## Cost Semantics",
            "",
            "Baseline net expectancy is the Phase 0 fixed-notional net after the originally assumed cost model. Net after proxy cost is baseline gross expectancy minus the offline Phase 3 proxy cost; the delta columns show how far that proxy result sits above or below the assumed baseline net.",
            "",
            "## Interpretation",
            "",
            "This report compares offline cost assumptions only. It does not authorize Phase 2, paper-mode execution, or broker-side order logic.",
            "",
        ]
    )


def _rows_table(rows: list[Any]) -> str:
    if not rows:
        return "No rows."
    columns = [
        "cost_mode",
        "family_unique_events",
        "primary_stream_allowed",
        "median_proxy_cost_r",
        "mean_proxy_cost_r",
        "median_net_after_proxy_cost_r",
        "mean_net_after_proxy_cost_r",
        "baseline_assumed_cost_r",
        "baseline_net_expectancy_r",
        "median_net_delta_vs_assumed_baseline_r",
        "normal_count",
        "cost_watch_count",
        "suspend_family_count",
        "suspend_family_unique_events",
    ]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for raw in rows:
        row = raw if isinstance(raw, dict) else {}
        body.append("| " + " | ".join(_escape(row.get(column, "")) for column in columns) + " |")
    return "\n".join([header, separator, *body])


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    phase3_root = Path(__file__).resolve().parents[1]
    repo_root = phase3_root.parents[1]
    reports = phase3_root / "outputs" / "reports"
    parser = argparse.ArgumentParser(description="Generate Phase 3 cost-mode comparison report.")
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports" / "PHASE1_WOULD_SIGNAL_REVIEW.csv",
    )
    parser.add_argument("--output-dir", type=Path, default=reports)
    args = parser.parse_args(argv)
    path = generate_cost_mode_comparison(args.input_csv, args.output_dir)
    print(f"Phase 3 cost-mode comparison: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
