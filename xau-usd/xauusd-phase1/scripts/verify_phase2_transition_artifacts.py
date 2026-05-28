from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_phase2_demo_preflight_report import generate_phase2_demo_preflight_report
from generate_phase2_demo_countdown_report import generate_phase2_demo_countdown_report
from generate_phase2_demo_next_actions_report import generate_phase2_demo_next_actions_report
from generate_phase2_owner_action_packet import generate_phase2_owner_action_packet
from generate_phase2_readiness_report import generate_phase2_readiness_report
from generate_phase2_vps_bootstrap_packet import generate_phase2_vps_bootstrap_packet
from generate_phase2_vps_first_day_verification import generate_phase2_vps_first_day_verification
from generate_phase2_vps_selection_decision_check import generate_phase2_vps_selection_decision_check
from verify_status_dashboard_freshness import verify_status_dashboard_freshness


def verify_phase2_transition_artifacts(
    root: Path,
    repo_root: Path | None = None,
    status_path: Path | None = None,
) -> list[str]:
    root = root.resolve()
    repo_root = (repo_root or root.parents[1]).resolve()
    status_path = (status_path or repo_root / "status.html").resolve()
    report_dir = root / "outputs" / "reports"
    errors: list[str] = []

    expected_files = {
        "demo countdown json": report_dir / "PHASE2_DEMO_COUNTDOWN.json",
        "demo countdown markdown": report_dir / "PHASE2_DEMO_COUNTDOWN.md",
        "readiness markdown": report_dir / "PHASE2_READINESS_REPORT.md",
        "demo preflight json": report_dir / "PHASE2_DEMO_PREFLIGHT.json",
        "demo preflight markdown": report_dir / "PHASE2_DEMO_PREFLIGHT_REPORT.md",
        "demo next-actions json": report_dir / "PHASE2_DEMO_NEXT_ACTIONS.json",
        "demo next-actions markdown": report_dir / "PHASE2_DEMO_NEXT_ACTIONS.md",
        "owner action json": report_dir / "PHASE2_OWNER_ACTION_PACKET.json",
        "owner action markdown": report_dir / "PHASE2_OWNER_ACTION_PACKET.md",
        "VPS bootstrap json": report_dir / "PHASE2_VPS_BOOTSTRAP_PACKET.json",
        "VPS bootstrap markdown": report_dir / "PHASE2_VPS_BOOTSTRAP_PACKET.md",
        "VPS first-day json": report_dir / "PHASE2_VPS_FIRST_DAY_VERIFICATION.json",
        "VPS first-day markdown": report_dir / "PHASE2_VPS_FIRST_DAY_VERIFICATION.md",
        "VPS selection decision check json": report_dir / "PHASE2_VPS_SELECTION_DECISION_CHECK.json",
        "VPS selection decision check markdown": report_dir / "PHASE2_VPS_SELECTION_DECISION_CHECK.md",
        "VPS latency markdown": report_dir / "PHASE2_VPS_LATENCY_REPORT.md",
        "local MT5 network baseline markdown": report_dir / "PHASE2_LOCAL_MT5_NETWORK_BASELINE.md",
        "VPS evidence workspace manifest": report_dir / "vps_evidence_workspace_manifest.json",
    }
    for label, path in expected_files.items():
        if not path.exists():
            errors.append(f"missing committed {label}: {path}")
    if errors:
        return errors

    with tempfile.TemporaryDirectory(prefix="phase2-transition-verify-") as tmp:
        tmp_dir = Path(tmp)
        generated_first_day = generate_phase2_vps_first_day_verification(
            root,
            report_path=tmp_dir / "PHASE2_VPS_FIRST_DAY_VERIFICATION.md",
            json_path=tmp_dir / "PHASE2_VPS_FIRST_DAY_VERIFICATION.json",
        )
        generated_vps_selection_check = generate_phase2_vps_selection_decision_check(
            root,
            tmp_dir / "PHASE2_VPS_SELECTION_DECISION_CHECK.json",
        )
        generated_readiness = generate_phase2_readiness_report(
            root,
            tmp_dir / "PHASE2_READINESS_REPORT.md",
        )
        generated_countdown = generate_phase2_demo_countdown_report(
            root,
            tmp_dir / "PHASE2_DEMO_COUNTDOWN.json",
        )
        generated_preflight = generate_phase2_demo_preflight_report(
            root,
            tmp_dir / "PHASE2_DEMO_PREFLIGHT.json",
        )
        generated_owner = generate_phase2_owner_action_packet(
            root,
            tmp_dir / "PHASE2_OWNER_ACTION_PACKET.json",
        )
        generated_bootstrap = generate_phase2_vps_bootstrap_packet(
            root,
            tmp_dir / "PHASE2_VPS_BOOTSTRAP_PACKET.json",
        )
        generated_next_actions = generate_phase2_demo_next_actions_report(
            root,
            tmp_dir / "PHASE2_DEMO_NEXT_ACTIONS.json",
        )
        errors.extend(
            _compare_json(
                "PHASE2_VPS_FIRST_DAY_VERIFICATION.json",
                expected_files["VPS first-day json"],
                generated_first_day.json_path,
            )
        )
        errors.extend(
            _compare_text(
                "PHASE2_VPS_FIRST_DAY_VERIFICATION.md",
                expected_files["VPS first-day markdown"],
                generated_first_day.report_path,
            )
        )
        errors.extend(
            _compare_json(
                "PHASE2_VPS_SELECTION_DECISION_CHECK.json",
                expected_files["VPS selection decision check json"],
                generated_vps_selection_check.json_path,
            )
        )
        errors.extend(
            _compare_text(
                "PHASE2_VPS_SELECTION_DECISION_CHECK.md",
                expected_files["VPS selection decision check markdown"],
                generated_vps_selection_check.markdown_path,
            )
        )
        errors.extend(
            _compare_text(
                "PHASE2_READINESS_REPORT.md",
                expected_files["readiness markdown"],
                generated_readiness.report_path,
            )
        )
        errors.extend(
            _compare_json(
                "PHASE2_DEMO_COUNTDOWN.json",
                expected_files["demo countdown json"],
                generated_countdown.json_path,
            )
        )
        errors.extend(
            _compare_text(
                "PHASE2_DEMO_COUNTDOWN.md",
                expected_files["demo countdown markdown"],
                generated_countdown.markdown_path,
            )
        )
        errors.extend(
            _compare_json(
                "PHASE2_DEMO_PREFLIGHT.json",
                expected_files["demo preflight json"],
                generated_preflight.json_path,
            )
        )
        errors.extend(
            _compare_text(
                "PHASE2_DEMO_PREFLIGHT_REPORT.md",
                expected_files["demo preflight markdown"],
                generated_preflight.markdown_path,
            )
        )
        errors.extend(
            _compare_json(
                "PHASE2_OWNER_ACTION_PACKET.json",
                expected_files["owner action json"],
                generated_owner.json_path,
            )
        )
        errors.extend(
            _compare_text(
                "PHASE2_OWNER_ACTION_PACKET.md",
                expected_files["owner action markdown"],
                generated_owner.markdown_path,
            )
        )
        errors.extend(
            _compare_json(
                "PHASE2_VPS_BOOTSTRAP_PACKET.json",
                expected_files["VPS bootstrap json"],
                generated_bootstrap.json_path,
            )
        )
        errors.extend(
            _compare_text(
                "PHASE2_VPS_BOOTSTRAP_PACKET.md",
                expected_files["VPS bootstrap markdown"],
                generated_bootstrap.markdown_path,
            )
        )
        errors.extend(
            _compare_json(
                "PHASE2_DEMO_NEXT_ACTIONS.json",
                expected_files["demo next-actions json"],
                generated_next_actions.json_path,
            )
        )
        errors.extend(
            _compare_text(
                "PHASE2_DEMO_NEXT_ACTIONS.md",
                expected_files["demo next-actions markdown"],
                generated_next_actions.markdown_path,
            )
        )

    errors.extend(_authorization_boundary_errors(root, repo_root))
    errors.extend(_owner_packet_recommendation_errors(root))
    errors.extend(_vps_latency_baseline_errors(root))
    errors.extend(verify_status_dashboard_freshness(repo_root, status_path))
    return errors


def _compare_json(label: str, committed_path: Path, generated_path: Path) -> list[str]:
    committed = _normalize_json(json.loads(committed_path.read_text(encoding="utf-8")))
    generated = _normalize_json(json.loads(generated_path.read_text(encoding="utf-8")))
    if committed == generated:
        return []
    return [f"{label} is stale relative to canonical inputs; regenerate and commit it."]


def _compare_text(label: str, committed_path: Path, generated_path: Path) -> list[str]:
    committed = _normalize_text(committed_path.read_text(encoding="utf-8"))
    generated = _normalize_text(generated_path.read_text(encoding="utf-8"))
    if committed == generated:
        return []
    return [f"{label} is stale relative to canonical inputs; regenerate and commit it."]


def _authorization_boundary_errors(root: Path, repo_root: Path) -> list[str]:
    report_dir = root / "outputs" / "reports"
    phase3_status_path = repo_root / "xau-usd" / "xauusd-phase3-experimental" / "outputs" / "reports" / "PHASE3_EXPERIMENTAL_STATUS.json"
    checks = [
        (
            "PHASE2_DEMO_PREFLIGHT.json",
            report_dir / "PHASE2_DEMO_PREFLIGHT.json",
            {
                "demo_trading_authorized": False,
                "live_trading_authorized": False,
            },
        ),
        (
            "PHASE2_OWNER_ACTION_PACKET.json",
            report_dir / "PHASE2_OWNER_ACTION_PACKET.json",
            {
                "paper_mode_authorized": False,
                "demo_trading_authorized": False,
                "broker_execution_authorized": False,
                "live_trading_authorized": False,
            },
        ),
        (
            "PHASE2_DEMO_COUNTDOWN.json",
            report_dir / "PHASE2_DEMO_COUNTDOWN.json",
            {
                "paper_mode_authorized": False,
                "broker_execution_authorized": False,
                "live_trading_authorized": False,
            },
        ),
        (
            "PHASE2_VPS_BOOTSTRAP_PACKET.json",
            report_dir / "PHASE2_VPS_BOOTSTRAP_PACKET.json",
            {
                "paper_mode_authorized": False,
                "demo_trading_authorized": False,
                "broker_execution_authorized": False,
                "live_trading_authorized": False,
            },
        ),
        (
            "PHASE2_VPS_FIRST_DAY_VERIFICATION.json",
            report_dir / "PHASE2_VPS_FIRST_DAY_VERIFICATION.json",
            {
                "phase2_paper_mode_authorized": False,
                "demo_trading_authorized": False,
                "live_trading_authorized": False,
            },
        ),
        (
            "PHASE3_EXPERIMENTAL_STATUS.json",
            phase3_status_path,
            {
                "authorized_for_deployment": False,
                "broker_action_code_allowed": False,
                "mt5_runtime_touched": False,
            },
        ),
    ]
    errors: list[str] = []
    for label, path, expected in checks:
        if not path.exists():
            errors.append(f"missing authorization-boundary artifact {label}: {path}")
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for key, expected_value in expected.items():
            if payload.get(key) is not expected_value:
                errors.append(f"{label} must keep {key}={expected_value!r}; found {payload.get(key)!r}.")

    preflight = json.loads((report_dir / "PHASE2_DEMO_PREFLIGHT.json").read_text(encoding="utf-8"))
    preflight_status = preflight.get("status")
    preflight_paper = preflight.get("paper_mode_implementation_authorized")
    if preflight_status != "PASS" and preflight_paper is not False:
        errors.append(
            "PHASE2_DEMO_PREFLIGHT.json must keep paper_mode_implementation_authorized=false unless status=PASS."
        )
    if preflight_status == "PASS" and preflight_paper is not True:
        errors.append("PHASE2_DEMO_PREFLIGHT.json status=PASS must explicitly set paper_mode_implementation_authorized=true.")

    phase3 = json.loads(phase3_status_path.read_text(encoding="utf-8"))
    if phase3.get("owner_approval_flow") != "excluded_from_real_phase2_phase3_approval_flow":
        errors.append(
            "PHASE3_EXPERIMENTAL_STATUS.json must keep owner_approval_flow="
            "excluded_from_real_phase2_phase3_approval_flow."
        )
    return errors


def _owner_packet_recommendation_errors(root: Path) -> list[str]:
    report_dir = root / "outputs" / "reports"
    json_path = report_dir / "PHASE2_OWNER_ACTION_PACKET.json"
    markdown_path = report_dir / "PHASE2_OWNER_ACTION_PACKET.md"
    errors: list[str] = []
    if not json_path.exists():
        return [f"missing owner action packet json: {json_path}"]
    if not markdown_path.exists():
        errors.append(f"missing owner action packet markdown: {markdown_path}")
        markdown = ""
    else:
        markdown = markdown_path.read_text(encoding="utf-8", errors="replace")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    recommendation = payload.get("vps_selection_recommendation")
    if not isinstance(recommendation, dict):
        errors.append("PHASE2_OWNER_ACTION_PACKET.json must include vps_selection_recommendation.")
        return errors
    decision_sheet = payload.get("one_screen_vps_decision_sheet")
    if not isinstance(decision_sheet, dict):
        errors.append("PHASE2_OWNER_ACTION_PACKET.json must include one_screen_vps_decision_sheet.")
    elif decision_sheet.get("status") != "WAITING_OWNER_SELECTION":
        errors.append("PHASE2_OWNER_ACTION_PACKET.json one_screen_vps_decision_sheet must wait for owner selection.")

    required_fields = {
        "status": "VPS recommendation status",
        "primary_trial": "Primary VPS trial",
        "backup_trial": "Backup VPS trial",
        "defer": "Deferred VPS option",
    }
    for key, label in required_fields.items():
        value = str(recommendation.get(key, "")).strip()
        if not value or value.upper() in {"PENDING OWNER SELECTION", "PENDING", "TBD", "TODO", "UNKNOWN"} and key != "status":
            errors.append(f"PHASE2_OWNER_ACTION_PACKET.json must include a concrete {label}.")
            continue
        if markdown and value not in markdown:
            errors.append(f"PHASE2_OWNER_ACTION_PACKET.md must display {label}: {value}.")
    if markdown and "## VPS Selection Recommendation" not in markdown:
        errors.append("PHASE2_OWNER_ACTION_PACKET.md must include a VPS Selection Recommendation section.")
    if markdown and "## One-Screen VPS Decision Sheet" not in markdown:
        errors.append("PHASE2_OWNER_ACTION_PACKET.md must include a One-Screen VPS Decision Sheet section.")
    if isinstance(decision_sheet, dict):
        for key in ("recommended_first_trial", "backup_trial", "decision_record_path"):
            value = str(decision_sheet.get(key, "")).strip()
            if not value:
                errors.append(f"PHASE2_OWNER_ACTION_PACKET.json one_screen_vps_decision_sheet must include {key}.")
            elif markdown and value not in markdown:
                errors.append(f"PHASE2_OWNER_ACTION_PACKET.md must display one-screen VPS value {key}: {value}.")
    return errors


def _vps_latency_baseline_errors(root: Path) -> list[str]:
    report_dir = root / "outputs" / "reports"
    latency_path = report_dir / "PHASE2_VPS_LATENCY_REPORT.md"
    baseline_path = report_dir / "PHASE2_LOCAL_MT5_NETWORK_BASELINE.md"
    errors: list[str] = []
    if not latency_path.exists():
        return [f"missing VPS latency report: {latency_path}"]
    if not baseline_path.exists():
        errors.append(f"missing local MT5 network baseline report: {baseline_path}")
    else:
        baseline_status = _read_markdown_status(baseline_path)
        if baseline_status != "PASS":
            errors.append(f"PHASE2_LOCAL_MT5_NETWORK_BASELINE.md must be PASS; found {baseline_status or 'missing'}.")

    text = latency_path.read_text(encoding="utf-8", errors="replace")
    if "local_baseline_comparison" not in text:
        errors.append("PHASE2_VPS_LATENCY_REPORT.md must include a local_baseline_comparison check.")
    if "Local MT5 baseline:" not in text:
        errors.append("PHASE2_VPS_LATENCY_REPORT.md must include the Local MT5 baseline evidence path.")
    if _read_markdown_status(latency_path) == "PASS" and "| local_baseline_comparison | PASS |" not in text:
        errors.append("PHASE2_VPS_LATENCY_REPORT.md status=PASS must prove local_baseline_comparison PASS.")
    return errors


def _normalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_json(item) for key, item in value.items() if key != "created_at_utc"}
    if isinstance(value, list):
        return [_normalize_json(item) for item in value]
    if isinstance(value, str):
        return _normalize_text(value)
    return value


def _normalize_text(value: str) -> str:
    normalized = value.replace("\r\n", "\n").replace("\r", "\n").replace("\\", "/")
    return re.sub(r"(?:[A-Za-z]:/|/)[^`|\n]*?(xau-usd/)", r"<repo>/\1", normalized)


def _read_markdown_status(path: Path) -> str:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Overall status:") or line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify Phase 2 transition artifacts are fresh and non-authorizing.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--status-path", type=Path, default=None)
    args = parser.parse_args(argv)
    errors = verify_phase2_transition_artifacts(args.root, args.repo_root, args.status_path)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("Phase 2 transition artifacts: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
