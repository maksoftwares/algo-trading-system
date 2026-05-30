from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from verify_status_dashboard_freshness import verify_status_dashboard_freshness


def verify_status_report_freshness(repo_root: Path, status_path: Path | None = None) -> list[str]:
    repo_root = repo_root.resolve()
    status_path = (status_path or repo_root / "status.html").resolve()
    phase1_reports = repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase3_reports = repo_root / "xau-usd" / "xauusd-phase3-experimental" / "outputs" / "reports"

    errors = verify_status_dashboard_freshness(repo_root, status_path)
    required_paths = {
        "phase1_summary": phase1_reports / "PHASE1_STATUS_SUMMARY.json",
        "phase1_acceptance": phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md",
        "phase1_review_index": phase1_reports / "PHASE1_REVIEW_INDEX.md",
        "phase2_readiness": phase1_reports / "PHASE2_READINESS_REPORT.md",
        "status_html": status_path,
    }
    for label, path in required_paths.items():
        if not path.exists():
            errors.append(f"missing report freshness input {label}: {path}")
    if errors:
        return errors

    summary = _read_json(required_paths["phase1_summary"])
    acceptance_text = required_paths["phase1_acceptance"].read_text(encoding="utf-8", errors="replace")
    review_index_text = required_paths["phase1_review_index"].read_text(encoding="utf-8", errors="replace")
    phase2_text = required_paths["phase2_readiness"].read_text(encoding="utf-8", errors="replace")
    status_html = status_path.read_text(encoding="utf-8", errors="replace")

    status_fields = _mapping(summary.get("status"))
    runtime = _mapping(summary.get("runtime"))
    latest = _mapping(runtime.get("latest_row"))
    soak = _mapping(summary.get("soak"))

    acceptance_status = _markdown_status_from_text(acceptance_text)
    review_index_status = _markdown_status_from_text(review_index_text)
    phase2_status = _markdown_status_from_text(phase2_text)

    expected_acceptance = str(status_fields.get("acceptance", ""))
    if expected_acceptance and acceptance_status != expected_acceptance:
        errors.append(
            "PHASE1_ACCEPTANCE_REPORT.md status is stale versus summary: "
            f"report={acceptance_status!r}; summary={expected_acceptance!r}"
        )
    if review_index_status == "PASS" and expected_acceptance != "PASS":
        errors.append(
            "PHASE1_REVIEW_INDEX.md is PASS while summary acceptance is not PASS: "
            f"review_index={review_index_status!r}; summary_acceptance={expected_acceptance!r}"
        )

    acceptance_rows = _markdown_rows_by_first_cell(acceptance_text)
    _expect_gate_status(
        errors,
        acceptance_rows,
        "Runtime log verification",
        str(status_fields.get("log_verification", "")),
        "PHASE1_ACCEPTANCE_REPORT.md",
    )
    _expect_gate_status(
        errors,
        acceptance_rows,
        "Soak/drift analysis",
        str(status_fields.get("soak_analysis", "")),
        "PHASE1_ACCEPTANCE_REPORT.md",
    )
    _expect_gate_status(
        errors,
        acceptance_rows,
        "Runtime health",
        str(status_fields.get("runtime_health", "")),
        "PHASE1_ACCEPTANCE_REPORT.md",
    )
    _expect_gate_status(
        errors,
        acceptance_rows,
        "Would-signal evidence",
        str(status_fields.get("would_signal", "")),
        "PHASE1_ACCEPTANCE_REPORT.md",
    )
    _expect_gate_status(
        errors,
        acceptance_rows,
        "Five trading day soak",
        _five_day_soak_status(soak),
        "PHASE1_ACCEPTANCE_REPORT.md",
    )
    _expect_gate_status(
        errors,
        acceptance_rows,
        "Active-market 72-hour soak",
        _active_market_status(soak),
        "PHASE1_ACCEPTANCE_REPORT.md",
    )
    _expect_gate_status(
        errors,
        acceptance_rows,
        "Process/code-freeze 96-hour gate",
        _process_freeze_status(soak),
        "PHASE1_ACCEPTANCE_REPORT.md",
    )

    report_fragments = {
        "acceptance latest bar": latest.get("bar_time"),
        "review index latest bar": latest.get("bar_time"),
        "phase2 readiness latest bar": latest.get("bar_time"),
        "review index decision rows": runtime.get("decision_rows"),
        "phase2 readiness decision rows": runtime.get("decision_rows"),
        "review index soak progress": _percent(soak.get("progress_pct")),
        "phase2 readiness soak progress": _percent(soak.get("progress_pct")),
        "review index acceptance status": expected_acceptance,
        "phase2 readiness dry_run": latest.get("dry_run"),
        "phase2 readiness trade_permission": latest.get("trade_permission"),
        "phase2 readiness server_time_status": latest.get("server_time_status"),
    }
    _expect_fragment(errors, "PHASE1_ACCEPTANCE_REPORT.md", acceptance_text, "acceptance latest bar", latest.get("bar_time"))
    for label, value in report_fragments.items():
        target_text = review_index_text if label.startswith("review index") else phase2_text
        target_name = "PHASE1_REVIEW_INDEX.md" if label.startswith("review index") else "PHASE2_READINESS_REPORT.md"
        _expect_fragment(errors, target_name, target_text, label, value)

    d2_required = "Candidate-level D2 remains preserved audit evidence"
    _expect_fragment(errors, "PHASE2_READINESS_REPORT.md", phase2_text, "D2 authority clarification", d2_required)

    if _dashboard_shows_phase3(status_html):
        phase3_md = phase3_reports / "PHASE3_EXPERIMENTAL_STATUS.md"
        phase3_json = phase3_reports / "PHASE3_EXPERIMENTAL_STATUS.json"
        if not phase3_md.exists():
            errors.append(f"status.html shows Phase 3 status but markdown report is missing: {phase3_md}")
        if not phase3_json.exists():
            errors.append(f"status.html shows Phase 3 status but JSON report is missing: {phase3_json}")
        if phase3_md.exists() and phase3_json.exists():
            phase3_status = _read_json(phase3_json)
            phase3_markdown_status = _markdown_status_from_text(
                phase3_md.read_text(encoding="utf-8", errors="replace")
            )
            if phase3_status.get("status") and phase3_markdown_status != phase3_status.get("status"):
                errors.append(
                    "PHASE3_EXPERIMENTAL_STATUS.md status is stale versus JSON: "
                    f"markdown={phase3_markdown_status!r}; json={phase3_status.get('status')!r}"
                )
            comparisons = {
                "real_phase1_acceptance": acceptance_status,
                "real_phase2_readiness": phase2_status,
                "latest_phase1_bar": latest.get("bar_time"),
                "latest_phase1_dry_run": latest.get("dry_run"),
                "latest_phase1_trade_permission": latest.get("trade_permission"),
            }
            for key, current in comparisons.items():
                if current in {None, ""}:
                    continue
                if str(phase3_status.get(key, "")) != str(current):
                    errors.append(
                        f"PHASE3_EXPERIMENTAL_STATUS.json {key} is stale: "
                        f"phase3={phase3_status.get(key)!r}; current={current!r}"
                    )

    _expect_fragment(errors, "status.html", status_html, "phase1 acceptance status", acceptance_status)
    _expect_fragment(errors, "status.html", status_html, "phase2 readiness status", phase2_status)
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _markdown_status_from_text(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("Overall status:") or line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _markdown_rows_by_first_cell(text: str) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        parts = [part.strip().replace("\\|", "|") for part in stripped.strip("|").split("|")]
        if len(parts) >= 2 and parts[0] and parts[0].lower() not in {"gate", "artifact", "field"}:
            rows[parts[0]] = parts
    return rows


def _expect_gate_status(
    errors: list[str],
    rows: dict[str, list[str]],
    gate: str,
    expected: str,
    report_name: str,
) -> None:
    if not expected:
        return
    row = rows.get(gate)
    if row is None:
        errors.append(f"{report_name} is missing gate row: {gate}")
        return
    actual = row[1] if len(row) > 1 else ""
    if actual != expected:
        errors.append(f"{report_name} gate `{gate}` is stale: report={actual!r}; expected={expected!r}")


def _expect_fragment(
    errors: list[str],
    report_name: str,
    text: str,
    label: str,
    value: object,
) -> None:
    if value is None or value == "":
        return
    raw = str(value)
    escaped = html.escape(raw, quote=True)
    if raw not in text and escaped not in text:
        errors.append(f"{report_name} is missing current {label}: {raw}")


def _percent(value: object) -> str:
    numeric = _to_float(value)
    if numeric is None:
        return ""
    if numeric.is_integer():
        return f"{numeric:.1f}%" if numeric != 100.0 else "100.0%"
    return f"{numeric}%"


def _five_day_soak_status(soak: dict[str, Any]) -> str:
    progress = _to_float(soak.get("progress_pct"))
    return "PASS" if progress is not None and progress >= 100.0 else "PENDING"


def _active_market_status(soak: dict[str, Any]) -> str:
    required = _to_float(soak.get("required_uninterrupted_streak_hours")) or 72.0
    longest = _to_float(soak.get("active_market_streak_hours")) or _to_float(soak.get("longest_streak_hours"))
    if soak.get("uninterrupted_soak_pass") is True and longest is not None and longest >= required:
        return "PASS"
    return "PENDING"


def _process_freeze_status(soak: dict[str, Any]) -> str:
    required = _to_float(soak.get("required_code_freeze_hours")) or 96.0
    uptime = _to_float(soak.get("process_uptime_streak_hours"))
    freeze = _to_float(soak.get("code_freeze_hours"))
    if soak.get("process_code_freeze_pass") is True and uptime is not None and freeze is not None:
        if uptime >= required and freeze >= required:
            return "PASS"
    return "PENDING"


def _to_float(value: object) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _dashboard_shows_phase3(status_html: str) -> bool:
    return "PHASE3_EXPERIMENTAL_STATUS" in status_html or "Phase 3 experimental status" in status_html


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(
        description="Verify that Phase 1/2/3 reports and status.html match the canonical Phase 1 summary."
    )
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument("--status-path", type=Path, default=None)
    args = parser.parse_args(argv)

    errors = verify_status_report_freshness(args.repo_root, args.status_path)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("Status report freshness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
