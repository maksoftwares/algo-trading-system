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
from generate_phase2_owner_action_packet import generate_phase2_owner_action_packet
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
        "demo preflight json": report_dir / "PHASE2_DEMO_PREFLIGHT.json",
        "demo preflight markdown": report_dir / "PHASE2_DEMO_PREFLIGHT_REPORT.md",
        "owner action json": report_dir / "PHASE2_OWNER_ACTION_PACKET.json",
        "owner action markdown": report_dir / "PHASE2_OWNER_ACTION_PACKET.md",
    }
    for label, path in expected_files.items():
        if not path.exists():
            errors.append(f"missing committed {label}: {path}")
    if errors:
        return errors

    with tempfile.TemporaryDirectory(prefix="phase2-transition-verify-") as tmp:
        tmp_dir = Path(tmp)
        generated_preflight = generate_phase2_demo_preflight_report(
            root,
            tmp_dir / "PHASE2_DEMO_PREFLIGHT.json",
        )
        generated_owner = generate_phase2_owner_action_packet(
            root,
            tmp_dir / "PHASE2_OWNER_ACTION_PACKET.json",
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

    errors.extend(_authorization_boundary_errors(root, repo_root))
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
