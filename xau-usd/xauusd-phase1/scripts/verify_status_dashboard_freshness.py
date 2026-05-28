from __future__ import annotations

import argparse
import html
import json
import re
import tempfile
from pathlib import Path
from typing import Any

from generate_project_status_page import generate_project_status_page


def verify_status_dashboard_freshness(repo_root: Path, status_path: Path | None = None) -> list[str]:
    repo_root = repo_root.resolve()
    status_path = (status_path or repo_root / "status.html").resolve()
    phase0_reports = repo_root / "xau-usd" / "xauusd-phase0" / "outputs" / "reports"
    phase1_reports = repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase3_reports = repo_root / "xau-usd" / "xauusd-phase3-experimental" / "outputs" / "reports"

    canonical_paths = {
        "phase1_summary": phase1_reports / "PHASE1_STATUS_SUMMARY.json",
        "measured_cost": phase0_reports / "MEASURED_COST_MODEL.md",
        "phase2_readiness": phase1_reports / "PHASE2_READINESS_REPORT.md",
        "phase3_status": phase3_reports / "PHASE3_EXPERIMENTAL_STATUS.json",
    }
    errors = [f"missing status dashboard: {status_path}"] if not status_path.exists() else []
    for label, path in canonical_paths.items():
        if not path.exists():
            errors.append(f"missing canonical report {label}: {path}")
    if errors:
        return errors

    actual = status_path.read_text(encoding="utf-8", errors="replace")
    with tempfile.TemporaryDirectory(prefix="status-dashboard-freshness-") as temp_dir:
        expected_path = Path(temp_dir) / "status.html"
        generate_project_status_page(repo_root, expected_path)
        expected = expected_path.read_text(encoding="utf-8", errors="replace")
    if _normalize_dashboard(actual) != _normalize_dashboard(expected):
        errors.append("status.html does not match a fresh render from canonical local reports")

    phase1_summary = _read_json(canonical_paths["phase1_summary"])
    phase3_status = _read_json(canonical_paths["phase3_status"])
    measured_cost = _parse_measured_cost(canonical_paths["measured_cost"])
    phase2_status = _markdown_status(canonical_paths["phase2_readiness"])

    runtime = _mapping(phase1_summary.get("runtime"))
    latest = _mapping(runtime.get("latest_row"))
    soak = _mapping(phase1_summary.get("soak"))
    core_expectations = {
        "decision row count": runtime.get("decision_rows"),
        "latest bar": latest.get("bar_time"),
        "soak observed days": soak.get("observed_days"),
        "soak progress pct": f"{_to_float(soak.get('progress_pct')):.2f}%" if _to_float(soak.get("progress_pct")) is not None else None,
        "measured cost status": measured_cost.get("status"),
        "measured cost observed rows": measured_cost.get("observed_rows"),
        "measured cost observed days": measured_cost.get("observed_days"),
        "phase2 readiness status": phase2_status,
        "phase3 experimental status": phase3_status.get("status"),
    }
    for label, value in core_expectations.items():
        if value is None or value == "":
            continue
        text = html.escape(str(value), quote=True)
        if text not in actual:
            errors.append(f"status.html is missing {label}: {value}")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _markdown_status(path: Path) -> str:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Overall status:") or line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _parse_measured_cost(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"status": _markdown_status(path)}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("|") or "Observed Rows" not in line or "Observed Days" not in line:
            continue
        if index + 2 >= len(lines):
            continue
        headers = [part.strip() for part in line.strip("|").split("|")]
        values = [part.strip() for part in lines[index + 2].strip("|").split("|")]
        row = dict(zip(headers, values))
        result["observed_rows"] = row.get("Observed Rows", "")
        result["observed_days"] = row.get("Observed Days", "")
        result["required_days"] = row.get("Required Days", "")
        break
    return result


def _normalize_dashboard(text: str) -> str:
    text = re.sub(r"(Generated )[^<]+( from local artifacts\.)", r"\1<TIMESTAMP>\2", text)
    text = re.sub(
        r'(<div class="rail-label">Updated</div>\s*<div class="sidebar-path">)[^<]+(</div>)',
        r"\1<TIMESTAMP>\2",
        text,
    )
    return text


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _to_float(value: object) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description="Verify that status.html matches canonical project reports.")
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument("--status-path", type=Path, default=None)
    args = parser.parse_args(argv)
    errors = verify_status_dashboard_freshness(args.repo_root, args.status_path)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("Status dashboard freshness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
