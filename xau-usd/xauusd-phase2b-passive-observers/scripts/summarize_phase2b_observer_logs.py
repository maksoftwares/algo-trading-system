from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


def summarize_observer_logs(root: Path, input_dir: Path | None = None) -> dict[str, object]:
    input_dir = input_dir or root / "outputs" / "observer_logs"
    rows = []
    if input_dir.exists():
        for path in sorted(input_dir.glob("*.csv")):
            with path.open(encoding="utf-8", newline="") as handle:
                rows.extend(csv.DictReader(handle))
    signal_rows = [row for row in rows if row.get("would_signal", "").lower() == "true"]
    by_candidate = Counter(row.get("candidate_id", "unknown") for row in rows)
    cost_rows = [
        float(row["projected_cost_r_p95"])
        for row in rows
        if row.get("projected_cost_r_p95", "").replace(".", "", 1).isdigit()
    ]
    return {
        "rows": len(rows),
        "would_signal_rows": len(signal_rows),
        "candidate_counts": dict(by_candidate),
        "max_projected_cost_r_p95": max(cost_rows) if cost_rows else None,
    }


def write_summary_reports(root: Path, input_dir: Path | None = None) -> tuple[Path, Path]:
    summary = summarize_observer_logs(root, input_dir)
    report_dir = root / "outputs" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    signal_path = report_dir / "PHASE2B_OBSERVER_SIGNAL_SUMMARY.md"
    cost_path = report_dir / "PHASE2B_OBSERVER_COST_R_REPORT.md"
    signal_path.write_text(
        "\n".join(
            [
                "# Phase 2B Observer Signal Summary",
                "",
                f"Rows: {summary['rows']}",
                f"Would-signal rows: {summary['would_signal_rows']}",
                "",
                "No row in this report authorizes paper mode.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    cost_path.write_text(
        "\n".join(
            [
                "# Phase 2B Observer Cost R Report",
                "",
                f"Rows: {summary['rows']}",
                f"Max projected P95 cost_R: {summary['max_projected_cost_r_p95']}",
                "",
                "Measured-cost gates remain Phase 0R promotion blockers.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return signal_path, cost_path


def main(argv: list[str] | None = None) -> int:
    default_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Summarize Phase 2B observer CSV logs.")
    parser.add_argument("--root", type=Path, default=default_root)
    parser.add_argument("--input-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    signal_path, cost_path = write_summary_reports(args.root, args.input_dir)
    print(signal_path)
    print(cost_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
