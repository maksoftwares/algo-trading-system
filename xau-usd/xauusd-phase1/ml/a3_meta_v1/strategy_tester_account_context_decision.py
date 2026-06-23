from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .isolated_strategy_tester_terminal_root import LAUNCH_APPROVAL_TOKEN
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_STRATEGY_TESTER_ACCOUNT_CONTEXT_DECISION_STATUS.json"
DEFAULT_C53_JSON = Path("outputs") / "reports" / "A3_ML_ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_STATUS.json"
DEFAULT_C54_JSON = Path("outputs") / "reports" / "A3_ML_STRATEGY_TESTER_REPLAY_LAUNCH_STATUS.json"
SCHEMA_VERSION = "a3_ml_strategy_tester_account_context_decision_status_v1"
STATUS_DECISION_REQUIRED = "STRATEGY_TESTER_ACCOUNT_CONTEXT_DECISION_REQUIRED"
STATUS_PENDING_EVIDENCE = "STRATEGY_TESTER_ACCOUNT_CONTEXT_PENDING_REPLAY_EVIDENCE"
STATUS_NOT_REQUIRED = "STRATEGY_TESTER_ACCOUNT_CONTEXT_DECISION_NOT_REQUIRED"
ACCOUNT_CONTEXT_PHRASES = (
    "tester not started because the account is not specified",
    "account is not specified",
)


def generate_strategy_tester_account_context_decision(
    root: Path,
    report_json: Path | None = None,
    *,
    c53_json: Path | None = None,
    c54_json: Path | None = None,
) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    c53_json = (c53_json or root / DEFAULT_C53_JSON).resolve()
    c54_json = (c54_json or root / DEFAULT_C54_JSON).resolve()
    c53 = _read_json(c53_json)
    c54 = _read_json(c54_json)
    selected = c53.get("selected_lane", {}) if isinstance(c53.get("selected_lane"), dict) else {}
    evidence = _account_context_evidence(c54)
    status = _status(c54, evidence)
    payload = {
        "status": status,
        "stage": "C55-STRATEGY-TESTER-ACCOUNT-CONTEXT-DECISION",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": c54.get("dataset_version") or c53.get("dataset_version", ""),
        "selected_lane_id": c54.get("selected_lane_id") or c53.get("selected_lane_id", ""),
        "launch_summary": _launch_summary(c54),
        "isolated_terminal": _isolated_terminal(selected),
        "account_context_blocker_detected": bool(evidence),
        "detected_log_evidence": evidence,
        "recommended_decision": "MANUAL_LOGIN_TO_ISOLATED_ROOT" if evidence else "",
        "decision_options": _decision_options(bool(evidence)),
        "reviewer_prompt": _reviewer_prompt(c53, c54, evidence),
        "commands": _commands(root, selected),
        "authorization": {
            "account_context_decision_authorizes_training": False,
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted_by_c55": False,
            "terminal_launch_attempted_by_c55": False,
            "strategy_tester_launch_attempted_by_c55": False,
            "active_terminal_root_write_attempted": False,
            "terminal_config_or_account_secret_copied": False,
            "account_dat_copied": False,
            "server_dat_copied": False,
            "history_cache_copied": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "inputs": {
            "c53_isolated_terminal_root": str(c53_json),
            "c54_replay_launch": str(c54_json),
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(reports / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_strategy_tester_account_context_decision_md(payload: dict[str, Any]) -> str:
    launch = payload.get("launch_summary", {})
    terminal = payload.get("isolated_terminal", {})
    evidence_rows = [
        {
            "Path": item.get("path", ""),
            "Phrase": item.get("phrase", ""),
            "Excerpt": item.get("excerpt", ""),
        }
        for item in payload.get("detected_log_evidence", [])
    ]
    option_rows = [
        {
            "Decision": item.get("decision", ""),
            "Recommended": str(item.get("recommended", False)).lower(),
            "Action": item.get("action", ""),
            "Risk": item.get("risk", ""),
        }
        for item in payload.get("decision_options", [])
    ]
    command_lines = "\n".join(f"- {key}: `{value}`" for key, value in payload.get("commands", {}).items())
    return "\n".join(
        [
            "# A3 ML Strategy Tester Account Context Decision",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            f"Selected lane: {payload.get('selected_lane_id', '')}",
            "",
            "## Launch Evidence",
            "",
            f"- C54 status: {launch.get('c54_status', '')}.",
            f"- Attempted: {str(launch.get('attempted', False)).lower()}.",
            f"- Timed out: {str(launch.get('timed_out', False)).lower()}.",
            f"- Return code: {launch.get('returncode')}.",
            f"- Replay output count: {launch.get('replay_output_count', 0)}.",
            f"- Account context blocker detected: {str(payload.get('account_context_blocker_detected', False)).lower()}.",
            "",
            "## Isolated Terminal",
            "",
            f"- Root: {terminal.get('terminal_root', '')}.",
            f"- Terminal executable: {terminal.get('isolated_terminal_exe', '')}.",
            f"- Tester config: {terminal.get('tester_config_path', '')}.",
            "",
            "## Detected Log Evidence",
            "",
            _table(evidence_rows, ["Path", "Phrase", "Excerpt"]) if evidence_rows else "No account-context blocker phrase detected.",
            "",
            "## Decision Options",
            "",
            _table(option_rows, ["Decision", "Recommended", "Action", "Risk"]) if option_rows else "No account-context decision required.",
            "",
            "## Reviewer Prompt",
            "",
            "```markdown",
            payload.get("reviewer_prompt", ""),
            "```",
            "",
            "## Commands",
            "",
            command_lines,
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted by C55: false.",
            "- Terminal launch attempted by C55: false.",
            "- Strategy Tester launch attempted by C55: false.",
            "- Active terminal root write attempted: false.",
            "- Terminal config or account secret copied: false.",
            "- accounts.dat copied: false.",
            "- servers.dat copied: false.",
            "- History cache copied: false.",
            "- Model training authorized: false.",
            "- Python demo predictions authorized: false.",
            "- EA consumption authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _launch_summary(c54: dict[str, Any]) -> dict[str, Any]:
    launch = c54.get("launch_result", {}) if isinstance(c54.get("launch_result"), dict) else {}
    return {
        "c54_status": c54.get("status", "MISSING"),
        "attempted": bool(launch.get("attempted", False)),
        "timed_out": bool(launch.get("timed_out", False)),
        "returncode": launch.get("returncode"),
        "duration_seconds": launch.get("duration_seconds", 0),
        "replay_output_count": len(c54.get("replay_outputs", [])) if isinstance(c54.get("replay_outputs"), list) else 0,
    }


def _isolated_terminal(selected: dict[str, Any]) -> dict[str, str]:
    return {
        "terminal_root": str(selected.get("terminal_root", "")),
        "isolated_terminal_exe": str(selected.get("isolated_terminal_exe", "")),
        "tester_config_path": str(selected.get("tester_config_path", "")),
    }


def _account_context_evidence(c54: dict[str, Any]) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    outputs = c54.get("replay_outputs", [])
    if not isinstance(outputs, list):
        return evidence
    for item in outputs:
        if not isinstance(item, dict):
            continue
        path = Path(str(item.get("path", "")))
        text = _tail_text(path)
        if not text:
            continue
        lowered = text.casefold()
        for phrase in ACCOUNT_CONTEXT_PHRASES:
            if phrase in lowered:
                evidence.append(
                    {
                        "path": str(path),
                        "phrase": phrase,
                        "excerpt": _line_excerpt(text, phrase),
                    }
                )
                break
    return evidence


def _decision_options(blocker_found: bool) -> list[dict[str, Any]]:
    if not blocker_found:
        return []
    return [
        {
            "decision": "MANUAL_LOGIN_TO_ISOLATED_ROOT",
            "recommended": True,
            "action": "Owner opens the isolated terminal root and logs into the demo account manually; Codex never handles the password.",
            "risk": "Lowest secret-handling risk, but requires one manual operator step.",
            "requires_owner_approval": True,
            "authorizes_training_or_broker_action": False,
        },
        {
            "decision": "APPROVE_MINIMAL_ISOLATED_ACCOUNT_CONTEXT_COPY",
            "recommended": False,
            "action": "Reviewer names the exact MT5 account/server files allowed to be copied into the isolated root.",
            "risk": "Potential credential/cache exposure; must not be committed or copied without explicit approval.",
            "requires_owner_approval": True,
            "authorizes_training_or_broker_action": False,
        },
        {
            "decision": "APPROVE_SERVER_METADATA_ONLY",
            "recommended": False,
            "action": "Reviewer confirms whether server metadata alone is non-secret and worth testing before any account cache copy.",
            "risk": "May not fix the MT5 account-context error; still needs explicit approval.",
            "requires_owner_approval": True,
            "authorizes_training_or_broker_action": False,
        },
        {
            "decision": "RUN_ON_ACTIVE_A2_PAUSED_TERMINAL",
            "recommended": False,
            "action": "Pause collection and run Strategy Tester from the already logged-in A2 portable terminal.",
            "risk": "Touches the live collection terminal and can interrupt data collection; use only as a last resort.",
            "requires_owner_approval": True,
            "authorizes_training_or_broker_action": False,
        },
    ]


def _reviewer_prompt(c53: dict[str, Any], c54: dict[str, Any], evidence: list[dict[str, str]]) -> str:
    if not c54:
        return (
            "Review C51-C53 readiness and confirm whether a bounded C54 isolated Strategy Tester replay launch may be run. "
            "Do not authorize model training, Python demo predictions, EA consumption, or broker action from this review alone."
        )
    if not evidence:
        return (
            "Review the C54 isolated Strategy Tester replay output. No account-context blocker phrase was detected by C55. "
            "Confirm whether the replay output is valid and whether any replay labels may be considered for a separate import review. "
            "Do not authorize model training, Python demo predictions, EA consumption, or broker action from this review alone."
        )
    terminal = c53.get("selected_lane", {}) if isinstance(c53.get("selected_lane"), dict) else {}
    return "\n".join(
        [
            "Please review the isolated Strategy Tester replay blocker.",
            "",
            f"- C54 status: {c54.get('status', 'MISSING')}",
            f"- Selected lane: {c54.get('selected_lane_id') or c53.get('selected_lane_id', '')}",
            f"- Isolated terminal root: {terminal.get('terminal_root', '')}",
            "- Detected blocker: MT5 logged that the tester was not started because the account is not specified.",
            "",
            "Choose one decision:",
            "1. MANUAL_LOGIN_TO_ISOLATED_ROOT, recommended: owner manually logs into the isolated demo terminal, then C54 is rerun.",
            "2. APPROVE_MINIMAL_ISOLATED_ACCOUNT_CONTEXT_COPY: approve exact MT5 files to copy, after classifying secret risk.",
            "3. APPROVE_SERVER_METADATA_ONLY: approve only non-secret server metadata if you believe it may be sufficient.",
            "4. RUN_ON_ACTIVE_A2_PAUSED_TERMINAL: last resort; pause collection and run tester from the logged-in A2 terminal.",
            "",
            "This decision must not authorize model training, Python demo predictions, EA consumption, or broker action.",
        ]
    )


def _commands(root: Path, selected: dict[str, Any]) -> dict[str, str]:
    python = _quote(sys.executable)
    c54 = _quote(str(root / "scripts" / "c54_run_isolated_strategy_tester_replay.py"))
    c55 = _quote(str(root / "scripts" / "c55_generate_strategy_tester_account_context_decision.py"))
    root_arg = _quote(str(root))
    terminal = _quote(str(selected.get("isolated_terminal_exe", "<isolated_terminal64.exe>")))
    return {
        "manual_login_open_isolated_terminal": f"{terminal} /portable",
        "rerun_c54_after_manual_login": f"{python} {c54} --root {root_arg} --approval-token {LAUNCH_APPROVAL_TOKEN} --timeout-seconds 180",
        "regenerate_c55": f"{python} {c55} --root {root_arg}",
    }


def _status(c54: dict[str, Any], evidence: list[dict[str, str]]) -> str:
    if not c54:
        return STATUS_PENDING_EVIDENCE
    if evidence:
        return STATUS_DECISION_REQUIRED
    return STATUS_NOT_REQUIRED


def _next_allowed_stage(status: str) -> str:
    if status == STATUS_DECISION_REQUIRED:
        return (
            "Recommended next step: owner manually logs into the isolated terminal root, then rerun C54. "
            "Do not copy accounts.dat, servers.dat, or any terminal account cache unless the reviewer explicitly approves exact files."
        )
    if status == STATUS_PENDING_EVIDENCE:
        return "Run the bounded C54 isolated Strategy Tester replay launch before asking for an account-context decision."
    return "No account-context blocker was detected by C55; inspect C54 outputs and request separate review before importing any replay labels."


def _tail_text(path: Path, limit: int = 20000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    tail = data[-limit:]
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", errors="ignore")[-limit:]
    if tail.count(b"\x00") > max(8, len(tail) // 10):
        return tail.decode("utf-16-le", errors="ignore")
    return tail.decode("utf-8", errors="ignore")


def _line_excerpt(text: str, phrase: str) -> str:
    lowered_phrase = phrase.casefold()
    for line in text.splitlines():
        if lowered_phrase in line.casefold():
            return line.strip()[:240]
    index = text.casefold().find(lowered_phrase)
    if index < 0:
        return ""
    start = max(0, index - 80)
    end = min(len(text), index + len(phrase) + 80)
    return text[start:end].replace("\n", " ").strip()[:240]


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_strategy_tester_account_context_decision_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c55_strategy_tester_account_context_decision_report"] = payload["outputs"]["status_report_json"]
    pointer["c55_strategy_tester_account_context_decision_status"] = payload["status"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _quote(value: str) -> str:
    return f'"{value}"' if " " in value else value
