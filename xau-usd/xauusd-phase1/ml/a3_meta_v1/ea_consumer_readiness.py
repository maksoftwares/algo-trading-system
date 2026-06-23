from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_EA_CONSUMER_READINESS_STATUS.json"
SCHEMA_VERSION = "a3_ml_ea_consumer_readiness_v1"
OBSERVER_EXPERT = "A3MlPredictionObserver"
HANDOFF_FILE_NAME = "A3_ML_EA_HANDOFF.csv"
HANDOFF_INCLUDE_NAME = "A3MlEaHandoff.mqh"
HANDOFF_READER_FN = "A3MlEaHandoffReadLatest"


def audit_ea_ml_consumers(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    registry = load_mt5_account_registry(root / "config" / "ml" / "mt5_accounts.yaml")
    pointer = _read_json(root / "outputs" / "reports" / "C02_DATASET_POINTER.json")
    repo_sources = _scan_expert_sources(root / "mt5" / "Experts")
    accounts = [_account_payload(account) for account in registry.accounts]
    validations = _validations(accounts)
    status = _status(validations, accounts)
    payload = {
        "status": status,
        "stage": "C16-EA-ML-CONSUMER-READINESS-AUDIT",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", ""),
        "authorization": {
            "python_demo_predictions_authorized": False,
            "passive_observer_ml_consumer_ready": all(item["observer_consumer_ready"] for item in accounts),
            "broker_executor_ml_consumer_ready": status == "BROKER_EXECUTOR_CONSUMERS_READY",
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "inputs": {
            "registry_path": str(root / "config" / "ml" / "mt5_accounts.yaml"),
            "repo_experts_dir": str(root / "mt5" / "Experts"),
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "repo_sources": repo_sources,
        "accounts": accounts,
        "validations": validations,
        "boundary": {
            "mt5_connection_attempted": False,
            "terminal_runtime_launch_attempted": False,
            "terminal_shutdown_attempted": False,
            "profile_or_chart_file_write_attempted": False,
            "expert_file_write_attempted": False,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer, payload)
    return report_json


def render_ea_consumer_readiness_md(payload: dict[str, Any]) -> str:
    accounts = [
        {
            "Account": item["account_label"],
            "Observer": str(item["observer_consumer_ready"]).lower(),
            "Active executors": _short_list([entry["expert_name"] for entry in item["active_broker_executors"]]),
            "ML-ready": _short_list([entry["expert_name"] for entry in item["active_broker_executors"] if entry["can_consume_ml_handoff"]]),
            "Gap": _short_list([entry["expert_name"] for entry in item["active_broker_executors"] if not entry["can_consume_ml_handoff"]]),
        }
        for item in payload.get("accounts", [])
    ]
    validations = [
        {"Check": item["check"], "Passed": str(item["passed"]).lower(), "Detail": item["detail"]}
        for item in payload.get("validations", [])
    ]
    gaps = _broker_gap_lines(payload.get("accounts", []))
    return "\n".join(
        [
            "# A3 ML EA Consumer Readiness Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Authorization",
            "",
            f"- Passive observer ML consumer ready: {str(payload['authorization']['passive_observer_ml_consumer_ready']).lower()}.",
            f"- Broker executor ML consumer ready: {str(payload['authorization']['broker_executor_ml_consumer_ready']).lower()}.",
            "- Python demo predictions authorized: false.",
            "- EA consumption authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Account Summary",
            "",
            _table(accounts, ["Account", "Observer", "Active executors", "ML-ready", "Gap"]) if accounts else "No accounts configured.",
            "",
            "## Broker Executor Gaps",
            "",
            "\n".join(gaps) if gaps else "- none",
            "",
            "## Validations",
            "",
            _table(validations, ["Check", "Passed", "Detail"]) if validations else "No validations ran.",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Terminal runtime launch attempted: false.",
            "- Terminal shutdown attempted: false.",
            "- Profile or chart file write attempted: false.",
            "- Expert file write attempted: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _account_payload(account: MT5AccountSpec) -> dict[str, Any]:
    data_root = Path(account.expected_data_path or "")
    files_root = Path(account.files_roots[0]) if account.files_roots else data_root / "MQL5" / "Files"
    sources = _scan_expert_sources(data_root / "MQL5" / "Experts")
    source_by_name = {item["expert_name"].lower(): item for item in sources}
    compiled_experts = _compiled_experts(data_root / "MQL5" / "Experts")
    attached_profiles = _scan_attached_profile_experts(data_root)
    active_names = _active_profile_expert_names(attached_profiles)
    observer_source = source_by_name.get(OBSERVER_EXPERT.lower(), {})
    active_broker_executors = [_active_broker_payload(name, source_by_name) for name in active_names if _expert_role(name) == "broker_executor_candidate"]
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "role": account.role,
        "data_root": str(data_root),
        "files_root": str(files_root),
        "include_path": str(data_root / "MQL5" / "Include" / HANDOFF_INCLUDE_NAME),
        "include_exists": (data_root / "MQL5" / "Include" / HANDOFF_INCLUDE_NAME).exists(),
        "handoff_path": str(files_root / HANDOFF_FILE_NAME),
        "handoff_exists": (files_root / HANDOFF_FILE_NAME).exists(),
        "observer_ex5_path": str(data_root / "MQL5" / "Experts" / f"{OBSERVER_EXPERT}.ex5"),
        "observer_ex5_exists": (data_root / "MQL5" / "Experts" / f"{OBSERVER_EXPERT}.ex5").exists(),
        "observer_source_path": observer_source.get("path", ""),
        "observer_consumer_ready": bool(observer_source.get("can_consume_ml_handoff")) and (data_root / "MQL5" / "Experts" / f"{OBSERVER_EXPERT}.ex5").exists(),
        "source_experts": sources,
        "compiled_experts": compiled_experts,
        "attached_profiles": attached_profiles,
        "active_broker_executors": active_broker_executors,
    }


def _active_broker_payload(name: str, source_by_name: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source = source_by_name.get(name.lower())
    if not source:
        return {
            "expert_name": name,
            "source_path": "",
            "source_found": False,
            "can_consume_ml_handoff": False,
            "detail": "active profile references compiled expert but no .mq5 source was found to inspect",
        }
    return {
        "expert_name": name,
        "source_path": source["path"],
        "source_found": True,
        "can_consume_ml_handoff": bool(source["can_consume_ml_handoff"]),
        "detail": source["detail"],
    }


def _scan_expert_sources(experts_dir: Path) -> list[dict[str, Any]]:
    if not experts_dir.exists():
        return []
    rows = []
    for path in sorted(experts_dir.rglob("*.mq5")):
        rows.append(_scan_expert_source(path, experts_dir))
    return rows


def _scan_expert_source(path: Path, base_dir: Path) -> dict[str, Any]:
    include_root = base_dir.parent / "Include"
    try:
        combined_text, resolved_includes = _source_with_includes(path, include_root, set())
        read_error = ""
    except OSError as exc:
        combined_text = ""
        resolved_includes = []
        read_error = f"{type(exc).__name__}: {exc}"
    includes_handoff = HANDOFF_INCLUDE_NAME in combined_text or HANDOFF_FILE_NAME in combined_text
    reads_handoff = HANDOFF_READER_FN in combined_text
    can_consume = includes_handoff and reads_handoff
    return {
        "expert_name": path.stem,
        "role": _expert_role(path.stem),
        "path": str(path),
        "relative_path": _safe_relative(path, base_dir),
        "uses_handoff_include_or_file": includes_handoff,
        "uses_handoff_reader": reads_handoff,
        "can_consume_ml_handoff": can_consume,
        "resolved_includes": resolved_includes,
        "read_error": read_error,
        "detail": "uses A3 ML handoff reader" if can_consume else "does not call A3 ML handoff reader",
    }


def _compiled_experts(experts_dir: Path) -> list[dict[str, str]]:
    if not experts_dir.exists():
        return []
    return [
        {"expert_name": path.stem, "path": str(path), "relative_path": _safe_relative(path, experts_dir)}
        for path in sorted(experts_dir.rglob("*.ex5"))
    ]


def _scan_attached_profile_experts(data_root: Path) -> list[dict[str, Any]]:
    roots = [data_root / "MQL5" / "Profiles" / "Charts", data_root / "Profiles" / "Charts"]
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.chr")):
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            rows.extend(_profile_expert_rows(path, root))
    return rows


def _profile_expert_rows(path: Path, profile_root: Path) -> list[dict[str, Any]]:
    try:
        text = _read_text_lossy(path)
    except OSError:
        return []
    profile_kind = _profile_kind(path)
    rows = []
    for block in re.findall(r"(?is)<expert>(.*?)</expert>", text):
        name = _profile_field(block, "name")
        expert_path = _profile_field(block, "path")
        expertmode = _profile_field(block, "expertmode")
        if not name and expert_path:
            name = Path(expert_path.replace("\\", "/")).stem
        if not name:
            continue
        rows.append(
            {
                "profile_chart": str(path),
                "profile_relative_path": _safe_relative(path, profile_root),
                "profile_kind": profile_kind,
                "expert_name": name,
                "expert_path": expert_path,
                "enabled": expertmode == "1",
                "role": _expert_role(name),
            }
        )
    return rows


def _profile_field(block: str, key: str) -> str:
    match = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(.*)$", block)
    return match.group(1).strip() if match else ""


def _profile_kind(path: Path) -> str:
    parts = {part.lower() for part in path.parts}
    lowered = str(path).lower()
    if "_codex_quarantine" in parts or "backup" in lowered:
        return "backup_or_quarantine"
    return "current_profile_file"


def _active_profile_expert_names(attached_profiles: list[dict[str, Any]]) -> list[str]:
    names = {
        item["expert_name"]
        for item in attached_profiles
        if item.get("enabled") is True and item.get("profile_kind") == "current_profile_file"
    }
    return sorted(names)


def _expert_role(name: str) -> str:
    lowered = name.lower()
    if lowered == OBSERVER_EXPERT.lower():
        return "ml_passive_observer"
    if "executor" in lowered:
        return "broker_executor_candidate"
    if "guardian" in lowered or "manager" in lowered:
        return "account_guardian_or_manager"
    if "observer" in lowered or "publisher" in lowered:
        return "observer_or_publisher"
    return "other_ea"


def _validations(accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = [
        _check("three_accounts_configured", len(accounts) == 3, f"observed={len(accounts)} required=3"),
        _check(
            "passive_observer_consumer_ready_all_accounts",
            all(item["observer_consumer_ready"] for item in accounts),
            _missing_accounts(accounts, "observer_consumer_ready") or "observer can read handoff on A1/A2/A3",
        ),
        _check(
            "handoff_file_exists_all_accounts",
            all(item["handoff_exists"] for item in accounts),
            _missing_accounts(accounts, "handoff_exists") or "handoff file exists on A1/A2/A3",
        ),
        _check(
            "handoff_include_exists_all_accounts",
            all(item["include_exists"] for item in accounts),
            _missing_accounts(accounts, "include_exists") or "handoff include exists on A1/A2/A3",
        ),
    ]
    active_count = sum(len(item["active_broker_executors"]) for item in accounts)
    gaps = _broker_gaps(accounts)
    checks.append(
        _check(
            "active_broker_executor_consumers_ready",
            active_count > 0 and not gaps,
            "no active broker executor gaps" if active_count > 0 and not gaps else _gap_detail(active_count, gaps),
        )
    )
    checks.append(_check("broker_action_false", True, "audit is read-only and does not authorize broker action"))
    return checks


def _status(validations: list[dict[str, Any]], accounts: list[dict[str, Any]]) -> str:
    required_preflight = {
        "three_accounts_configured",
        "passive_observer_consumer_ready_all_accounts",
        "handoff_file_exists_all_accounts",
        "handoff_include_exists_all_accounts",
    }
    validation_map = {item["check"]: item["passed"] for item in validations}
    if not all(validation_map.get(check) for check in required_preflight):
        return "PREFLIGHT_BLOCKED"
    active_count = sum(len(item["active_broker_executors"]) for item in accounts)
    gaps = _broker_gaps(accounts)
    if active_count > 0 and not gaps:
        return "BROKER_EXECUTOR_CONSUMERS_READY"
    if active_count > 0:
        return "BROKER_EXECUTOR_CONSUMER_GAP"
    return "OBSERVER_ONLY_CONSUMER_READY"


def _broker_gaps(accounts: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for account in accounts:
        for item in account["active_broker_executors"]:
            if not item["can_consume_ml_handoff"]:
                rows.append(
                    {
                        "account_label": account["account_label"],
                        "expert_name": item["expert_name"],
                        "detail": item["detail"],
                    }
                )
    return rows


def _gap_detail(active_count: int, gaps: list[dict[str, str]]) -> str:
    if active_count == 0:
        return "no active broker executors found in current profile files"
    return "not ML-ready: " + ", ".join(f"{item['account_label']}:{item['expert_name']}" for item in gaps)


def _broker_gap_lines(accounts: list[dict[str, Any]]) -> list[str]:
    return [f"- {item['account_label']}: {item['expert_name']} - {item['detail']}" for item in _broker_gaps(accounts)]


def _missing_accounts(accounts: list[dict[str, Any]], key: str) -> str:
    missing = [item["account_label"] for item in accounts if not item.get(key)]
    return "missing " + ",".join(missing) if missing else ""


def _short_list(values: list[str], limit: int = 4) -> str:
    clean = [value for value in values if value]
    if not clean:
        return "-"
    if len(clean) <= limit:
        return ", ".join(clean)
    return ", ".join(clean[:limit]) + f", +{len(clean) - limit} more"


def _next_allowed_stage(status: str) -> str:
    if status == "BROKER_EXECUTOR_CONSUMERS_READY":
        return "EA consumer plumbing is present. Keep broker action disabled, then use C10 readiness gates before any demo prediction handoff is trusted."
    if status == "BROKER_EXECUTOR_CONSUMER_GAP":
        return "Add shadow-only A3 ML handoff reading to the active broker executor EAs, then rerun C16. Do not authorize broker action."
    if status == "OBSERVER_ONLY_CONSUMER_READY":
        return "Passive observer can read handoff. Attach/confirm observer runtime logs, then decide which broker executor should receive shadow-only ML gating."
    return "Fix missing observer, handoff include, or handoff file artifacts, then rerun C09/C13/C16."


def _safe_relative(path: Path, base_dir: Path) -> str:
    try:
        return str(path.relative_to(base_dir))
    except ValueError:
        return path.name


def _source_with_includes(path: Path, include_root: Path, seen: set[Path]) -> tuple[str, list[str]]:
    resolved_path = path.resolve()
    if resolved_path in seen:
        return "", []
    seen.add(resolved_path)
    text = _read_text_lossy(path)
    include_paths: list[str] = []
    combined = [text]
    for include_name in _include_names(text):
        include_path = include_root / include_name
        if not include_path.exists():
            continue
        child_text, child_includes = _source_with_includes(include_path, include_root, seen)
        include_paths.append(str(include_path))
        include_paths.extend(child_includes)
        combined.append(child_text)
    return "\n".join(combined), include_paths


def _include_names(text: str) -> list[str]:
    names = []
    for match in re.finditer(r'(?m)^\s*#include\s+[<"]([^>"]+)[>"]', text):
        include_name = match.group(1).replace("\\", "/")
        if "/" in include_name:
            continue
        names.append(include_name)
    return names


def _read_text_lossy(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace").replace("\x00", "")


def _check(check: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": check, "passed": bool(passed), "detail": detail}


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_ea_consumer_readiness_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any]) -> None:
    if not pointer:
        return
    pointer["c16_ea_consumer_readiness_report"] = payload["outputs"]["status_report_json"]
    pointer["c16_ea_consumer_readiness_status"] = payload["status"]
    pointer["passive_observer_ml_consumer_ready"] = bool(payload["authorization"]["passive_observer_ml_consumer_ready"])
    pointer["broker_executor_ml_consumer_ready"] = bool(payload["authorization"]["broker_executor_ml_consumer_ready"])
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
