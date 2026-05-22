from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_REPORT = Path("outputs") / "reports" / "PHASE1_REVIEW_INDEX.md"


@dataclass(frozen=True)
class ReviewIndexItem:
    artifact: str
    status: str
    path: Path
    note: str


@dataclass(frozen=True)
class ReviewIndexOutput:
    status: str
    report_path: Path
    items: tuple[ReviewIndexItem, ...]


def generate_phase1_review_index(
    root: Path,
    report_path: Path | None = None,
    expected_bundle_path: Path | None = None,
    expected_manifest_path: Path | None = None,
    include_phase2_readiness: bool = True,
) -> ReviewIndexOutput:
    root = root.resolve()
    if report_path is None:
        report_path = root / DEFAULT_REPORT
    report_path = report_path.resolve()
    report_dir = root / "outputs" / "reports"
    summary_path = report_dir / "PHASE1_STATUS_SUMMARY.json"

    items = [
        _markdown_item("Acceptance report", report_dir / "PHASE1_ACCEPTANCE_REPORT.md"),
        _markdown_item("Runtime health report", report_dir / "PHASE1_RUNTIME_HEALTH_REPORT.md"),
        _markdown_item("Runtime log report", report_dir / "PHASE1_DRY_RUN_LOG_REPORT.md"),
        _markdown_item("Soak/drift report", report_dir / "PHASE1_SOAK_DRIFT_REPORT.md"),
        _markdown_item("Would-signal report", report_dir / "PHASE1_WOULD_SIGNAL_REPORT.md"),
        _markdown_item("Soak history report", report_dir / "PHASE1_SOAK_HISTORY_REPORT.md"),
        _file_item("Status summary JSON", summary_path),
        _file_item("Would-signal review CSV", report_dir / "PHASE1_WOULD_SIGNAL_REVIEW.csv"),
        _file_item("Soak history CSV", report_dir / "PHASE1_SOAK_HISTORY.csv"),
    ]
    if include_phase2_readiness:
        items.insert(6, _markdown_item("Phase 2 readiness report", report_dir / "PHASE2_READINESS_REPORT.md"))

    summary = _read_json(summary_path)
    status = _overall_status(items)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _render_report(status, root, items, summary, expected_bundle_path, expected_manifest_path),
        encoding="utf-8",
    )
    return ReviewIndexOutput(status, report_path, tuple(items))


def _markdown_item(artifact: str, path: Path) -> ReviewIndexItem:
    if not path.exists():
        return ReviewIndexItem(artifact, "FAIL", path, "Missing artifact.")
    status = _read_markdown_status(path)
    if status:
        return ReviewIndexItem(artifact, status, path, f"Overall status: {status}.")
    return ReviewIndexItem(artifact, "WARN", path, "No overall status line found.")


def _file_item(artifact: str, path: Path) -> ReviewIndexItem:
    if path.exists() and path.stat().st_size > 0:
        return ReviewIndexItem(artifact, "PASS", path, f"Present; {path.stat().st_size} bytes.")
    return ReviewIndexItem(artifact, "FAIL", path, "Missing or empty artifact.")


def _read_markdown_status(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if line.startswith("Overall status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _overall_status(items: list[ReviewIndexItem]) -> str:
    phase1_items = [item for item in items if item.artifact != "Phase 2 readiness report"]
    if any(item.status == "FAIL" for item in phase1_items):
        return "FAIL"
    acceptance = next((item.status for item in phase1_items if item.artifact == "Acceptance report"), "")
    if acceptance == "PASS":
        return "PASS"
    return "PENDING"


def _render_report(
    status: str,
    root: Path,
    items: list[ReviewIndexItem],
    summary: dict[str, Any],
    expected_bundle_path: Path | None,
    expected_manifest_path: Path | None,
) -> str:
    runtime = _mapping(summary.get("runtime"))
    latest = _mapping(runtime.get("latest_row"))
    soak = _mapping(summary.get("soak"))
    would_signal = _mapping(summary.get("would_signal"))
    status_fields = _mapping(summary.get("status"))
    soak_history_note = _historical_soak_note(root / "outputs" / "reports" / "PHASE1_SOAK_HISTORY.csv")

    bundle_path = expected_bundle_path or _latest_path(root / "outputs" / "review_bundles", "*_BUNDLE_*.zip")
    manifest_path = expected_manifest_path or _latest_path(root / "outputs" / "review_bundles", "*_manifest.json")

    return "\n".join(
        [
            "# Phase 1 Review Index",
            "",
            f"Overall status: {status}",
            "",
            "## Current Decision",
            "",
            _decision_text(status),
            "",
            "## Latest Runtime Snapshot",
            "",
            _markdown_table(
                [
                    {
                        "Decision Rows": _cell(runtime.get("decision_rows")),
                        "Latest Bar": _cell(latest.get("bar_time")),
                        "Dry Run": _cell(latest.get("dry_run")),
                        "Permission": _cell(latest.get("trade_permission")),
                        "Server Time": _cell(latest.get("server_time_status")),
                        "BR Stage": _cell(latest.get("br_stage")),
                    }
                ],
                ["Decision Rows", "Latest Bar", "Dry Run", "Permission", "Server Time", "BR Stage"],
            ),
            "",
            "## Gate Snapshot",
            "",
            _markdown_table(
                [
                    {
                        "Log": _cell(status_fields.get("log_verification")),
                        "Soak": _cell(status_fields.get("soak_analysis")),
                        "Runtime": _cell(status_fields.get("runtime_health")),
                        "Would-Signal": _cell(status_fields.get("would_signal")),
                        "Acceptance": _cell(status_fields.get("acceptance")),
                        "Soak Progress": f"{_cell(soak.get('progress_pct'))}%",
                        "Would Rows": _cell(would_signal.get("rows")),
                        "Clusters": _cell(would_signal.get("clusters")),
                    }
                ],
                ["Log", "Soak", "Runtime", "Would-Signal", "Acceptance", "Soak Progress", "Would Rows", "Clusters"],
            ),
            "",
            "## Primary Artifacts",
            "",
            _markdown_table(
                [
                    {
                        "Artifact": item.artifact,
                        "Status": item.status,
                        "Path": str(item.path),
                        "Note": item.note,
                    }
                    for item in items
                ],
                ["Artifact", "Status", "Path", "Note"],
            ),
            "",
            "## Historical Note",
            "",
            soak_history_note,
            "",
            "## Review Bundle",
            "",
            f"- Bundle: `{bundle_path if bundle_path else 'not generated yet'}`",
            f"- Manifest: `{manifest_path if manifest_path else 'not generated yet'}`",
            "",
            "## Boundary",
            "",
            "- Current work remains dry-run only.",
            "- Broker-action code remains outside the approved scope.",
            "- Final Phase 1 acceptance still depends on the five-trading-day soak gate.",
            "",
        ]
    )


def _decision_text(status: str) -> str:
    if status == "PASS":
        return "Phase 1 review evidence is complete for the current dry-run scope."
    if status == "FAIL":
        return "One or more review artifacts are missing or failing. Keep the shell dry-run and resolve the failed evidence."
    return "Phase 1 is progressing. Continue the scheduled dry-run soak and review the remaining pending gate."


def _latest_path(directory: Path, pattern: str) -> Path | None:
    if not directory.exists():
        return None
    paths = sorted((path for path in directory.glob(pattern) if path.is_file()), key=lambda path: path.stat().st_mtime)
    return paths[-1] if paths else None


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _historical_soak_note(path: Path) -> str:
    if not path.exists():
        return "Soak-history CSV not found, so no historical anomaly note is available."
    import csv

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return "No soak-history rows available for anomaly review."

    fail_rows = [row for row in rows if row.get("acceptance", "") == "FAIL"]
    if not fail_rows:
        return "No historical acceptance FAIL rows recorded."

    acceptance_only_fail_rows = [
        row
        for row in fail_rows
        if all(row.get(field, "") == "PASS" for field in ("log_verification", "soak_analysis", "runtime_health"))
        and row.get("would_signal", "") == "PASS"
    ]
    first_fail = fail_rows[0].get("created_at_utc", "n/a")
    last_fail = fail_rows[-1].get("created_at_utc", "n/a")
    if acceptance_only_fail_rows:
        return (
            f"Historical acceptance FAIL rows were seen from {first_fail} to {last_fail}; "
            "some were acceptance-only while all underlying runtime checks were PASS, so treat them as reporting transients."
        )
    return (
        f"Historical acceptance FAIL rows were seen from {first_fail} to {last_fail}; "
        "compare them against the latest healthy row before treating them as active regressions."
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
    parser = argparse.ArgumentParser(description="Generate the Phase 1 reviewer entry-point index.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Phase 1 workspace root.",
    )
    parser.add_argument("--report", type=Path, default=None, help="Markdown review index path.")
    parser.add_argument("--expected-bundle", type=Path, default=None, help="Expected review bundle path.")
    parser.add_argument("--expected-manifest", type=Path, default=None, help="Expected review bundle manifest path.")
    args = parser.parse_args(argv)

    output = generate_phase1_review_index(args.root, args.report, args.expected_bundle, args.expected_manifest)
    print(f"Phase 1 review index: {output.status}")
    print(output.report_path)
    for item in output.items:
        print(f"{item.status}: {item.artifact} - {item.path}")
    return 1 if output.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
