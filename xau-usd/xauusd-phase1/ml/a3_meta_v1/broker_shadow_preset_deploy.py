from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .broker_shadow_consumer_deploy import ACCOUNT_SOURCES
from .broker_shadow_manual_attach_packet import HANDOFF_FILE_NAME, SHADOW_TAP_LOG_NAME
from .market_data_export import _sha256_file, _table, _utc_now, _write_json_atomic


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_BROKER_SHADOW_PRESET_DEPLOY_STATUS.json"
SCHEMA_VERSION = "a3_ml_broker_shadow_preset_deploy_v1"
PRESET_SUFFIX = "a3_ml_shadow_readonly"
REQUIRED_INPUTS = (
    "InpDryRunOnly",
    "InpBrokerActionAllowed",
    "InpMlShadowReadEnabled",
    "InpMlHandoffFileName",
    "InpMlShadowLogFileName",
    "InpTargetSymbol",
    "InpExpectedServerMarker",
    "InpAllowedAccountLoginsCsv",
)


def deploy_broker_shadow_presets(
    root: Path,
    report_json: Path | None = None,
    *,
    deploy: bool = False,
) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    reports = root / "outputs" / "reports"
    registry_path = root / "config" / "ml" / "mt5_accounts.yaml"
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    c17 = _read_json(reports / "A3_ML_BROKER_SHADOW_CONSUMER_DEPLOY_STATUS.json")
    accounts: tuple[MT5AccountSpec, ...] = ()
    validations: list[dict[str, Any]] = []
    targets: list[dict[str, Any]] = []
    source_inputs: dict[str, list[str]] = {}

    validations.append(_check("registry_exists", registry_path.exists(), str(registry_path)))
    try:
        registry = load_mt5_account_registry(registry_path)
        accounts = registry.accounts
        validations.append(_check("registry_parses", True, ",".join(account.account_label for account in accounts)))
    except Exception as exc:
        validations.append(_check("registry_parses", False, f"{type(exc).__name__}: {exc}"))

    expert_dir = root / "mt5" / "Experts"
    include_dir = root / "mt5" / "Include"
    validations.append(_check("c17_compiled_shadow_consumers_deployed", c17.get("status") == "DEPLOYED_COMPILED_SHADOW_CONSUMERS", c17.get("status", "MISSING")))
    validations.append(_check("repo_experts_dir_exists", expert_dir.exists(), str(expert_dir)))
    validations.append(_check("repo_include_dir_exists", include_dir.exists(), str(include_dir)))

    for source_name in _all_source_names():
        source_path = expert_dir / source_name
        validations.append(_check(f"source_exists_{source_name}", source_path.exists(), str(source_path)))
        inputs = _source_input_names(source_path, include_dir) if source_path.exists() else set()
        source_inputs[source_name] = sorted(inputs)
        missing = [name for name in REQUIRED_INPUTS if name not in inputs]
        validations.append(
            _check(
                f"source_supports_safe_inputs_{source_name}",
                not missing,
                "ok" if not missing else "missing inputs: " + ",".join(missing),
            )
        )

    if accounts:
        targets = _target_records(accounts, source_inputs)
        validations.append(_check("all_target_paths_safe", _targets_safe(targets), _target_safety_detail(targets)))
        for target in targets:
            for preset in target.get("presets", []):
                validations.append(
                    _check(
                        f"preset_content_safe_{target['account_label']}_{preset['expert_name']}",
                        _preset_content_safe(preset["content"]),
                        preset["preset_name"],
                    )
                )

    ready = all(item["passed"] for item in validations)
    deploy_attempted = bool(deploy and ready)
    deployed_presets: list[dict[str, Any]] = []
    deployment_error = ""
    if deploy_attempted:
        try:
            deployed_presets = _deploy_presets(targets)
        except Exception as exc:
            deployment_error = f"{type(exc).__name__}: {exc}"
            validations.append(_check("deploy_write_completed", False, deployment_error))

    if deployment_error:
        status = "DEPLOY_FAILED"
    elif deploy_attempted:
        status = "DEPLOYED_SAFE_PASSIVE_PRESETS"
    elif ready:
        status = "PREFLIGHT_READY"
    else:
        status = "PREFLIGHT_BLOCKED"

    payload = {
        "status": status,
        "stage": "C30-BROKER-SHADOW-PRESET-DEPLOY",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "mode": "DEPLOY" if deploy else "PREFLIGHT_ONLY",
        "dataset_version": pointer.get("dataset_version", ""),
        "authorization": {
            "broker_shadow_preset_deploy_requested": bool(deploy),
            "broker_shadow_preset_deploy_attempted": deploy_attempted,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "inputs": {
            "registry_path": str(registry_path),
            "c17_broker_shadow_consumer_deploy": str(reports / "A3_ML_BROKER_SHADOW_CONSUMER_DEPLOY_STATUS.json"),
            "experts_dir": str(expert_dir),
            "include_dir": str(include_dir),
            "required_inputs": list(REQUIRED_INPUTS),
        },
        "targets": _targets_for_report(targets),
        "source_inputs": source_inputs,
        "deployed_presets": deployed_presets,
        "validations": validations,
        "boundary": {
            "mt5_connection_attempted": False,
            "terminal_runtime_launch_attempted": False,
            "terminal_shutdown_attempted": False,
            "profile_or_chart_file_write_attempted": False,
            "preset_file_deploy_attempted": deploy_attempted,
            "broker_action_authorized": False,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer, payload)
    return report_json


def render_broker_shadow_preset_deploy_md(payload: dict[str, Any]) -> str:
    target_rows = []
    for target in payload.get("targets", []):
        for preset in target.get("presets", []):
            target_rows.append(
                {
                    "Account": target.get("account_label", ""),
                    "Expert": preset.get("expert_name", ""),
                    "Preset": preset.get("preset_name", ""),
                    "Safe": str(preset.get("content_safe", False)).lower(),
                }
            )
    validations = [
        {"Check": item["check"], "Passed": str(item["passed"]).lower(), "Detail": item["detail"]}
        for item in payload.get("validations", [])
    ]
    deployed_lines = "\n".join(
        f"- {item['account_label']} {item['expert_name']}: {item['target_path']}"
        for item in payload.get("deployed_presets", [])
    ) or "- none"
    return "\n".join(
        [
            "# A3 ML Broker Shadow Preset Deploy Status",
            "",
            f"Overall status: {payload['status']}",
            f"Mode: {payload.get('mode', '')}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Authorization",
            "",
            f"- Broker-shadow preset deploy requested: {str(payload['authorization']['broker_shadow_preset_deploy_requested']).lower()}.",
            f"- Broker-shadow preset deploy attempted: {str(payload['authorization']['broker_shadow_preset_deploy_attempted']).lower()}.",
            "- Python demo predictions authorized: false.",
            "- EA consumption authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Targets",
            "",
            _table(target_rows, ["Account", "Expert", "Preset", "Safe"]) if target_rows else "No targets.",
            "",
            "## Deployed Presets",
            "",
            deployed_lines,
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
            f"- Preset file deploy attempted: {str(payload['boundary']['preset_file_deploy_attempted']).lower()}.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _target_records(accounts: tuple[MT5AccountSpec, ...], source_inputs: dict[str, list[str]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for account in accounts:
        data_root = Path(account.expected_data_path or "")
        presets_dir = data_root / "MQL5" / "Presets"
        preset_records = []
        for source_name in ACCOUNT_SOURCES.get(account.account_label, ()):
            expert_name = Path(source_name).stem
            preset_name = f"{expert_name}.{account.account_label}.{PRESET_SUFFIX}.set"
            settings = _preset_settings(account, source_inputs.get(source_name, []))
            content = _render_preset(settings)
            preset_records.append(
                {
                    "source_name": source_name,
                    "expert_name": expert_name,
                    "preset_name": preset_name,
                    "target_path": str(presets_dir / preset_name),
                    "settings": settings,
                    "content": content,
                    "content_safe": _preset_content_safe(content),
                    "content_sha256": _sha256_text(content),
                }
            )
        records.append(
            {
                "account_label": account.account_label,
                "account_scope": account.account_scope,
                "data_root": str(data_root),
                "presets_dir": str(presets_dir),
                "presets": preset_records,
            }
        )
    return records


def _preset_settings(account: MT5AccountSpec, input_names: list[str]) -> dict[str, str]:
    desired = {
        "InpDryRunOnly": "true",
        "InpBrokerActionAllowed": "false",
        "InpMlShadowReadEnabled": "true",
        "InpMlHandoffFileName": HANDOFF_FILE_NAME,
        "InpMlShadowLogFileName": SHADOW_TAP_LOG_NAME,
        "InpTargetSymbol": account.symbol or "XAUUSD",
        "InpExpectedServerMarker": "Demo",
        "InpAllowedAccountLoginsCsv": account.account_scope,
    }
    supported = set(input_names)
    return {key: value for key, value in desired.items() if key in supported}


def _render_preset(settings: dict[str, str]) -> str:
    ordered = [key for key in REQUIRED_INPUTS if key in settings]
    return "\n".join(f"{key}={settings[key]}" for key in ordered) + "\n"


def _deploy_presets(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deployed: list[dict[str, Any]] = []
    for target in targets:
        if not _target_record_safe(target):
            raise ValueError(f"unsafe target paths for {target.get('account_label', 'UNKNOWN')}")
        presets_dir = Path(target["presets_dir"])
        presets_dir.mkdir(parents=True, exist_ok=True)
        for preset in target["presets"]:
            if not _preset_content_safe(preset["content"]):
                raise ValueError(f"unsafe preset content for {preset['preset_name']}")
            target_path = Path(preset["target_path"])
            target_path.write_text(preset["content"], encoding="utf-8")
            deployed.append(
                {
                    "artifact": "broker_shadow_safe_preset",
                    "account_label": target["account_label"],
                    "account_scope": target["account_scope"],
                    "source_name": preset["source_name"],
                    "expert_name": preset["expert_name"],
                    "preset_name": preset["preset_name"],
                    "target_path": str(target_path),
                    "bytes": target_path.stat().st_size,
                    "sha256": _sha256_file(target_path),
                }
            )
    return deployed


def _targets_for_report(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for target in targets:
        rows.append(
            {
                **{key: value for key, value in target.items() if key != "presets"},
                "presets": [
                    {key: value for key, value in preset.items() if key != "content"}
                    for preset in target.get("presets", [])
                ],
            }
        )
    return rows


def _source_input_names(source_path: Path, include_dir: Path) -> set[str]:
    text = _source_with_includes(source_path, include_dir, set())
    return set(re.findall(r"\binput\s+(?:bool|string|int|long|double|datetime)\s+([A-Za-z_][A-Za-z0-9_]*)\b", text))


def _source_with_includes(path: Path, include_dir: Path, seen: set[Path]) -> str:
    path = path.resolve()
    if path in seen or not path.exists():
        return ""
    seen.add(path)
    text = path.read_text(encoding="utf-8")
    chunks = [text]
    for include_name in re.findall(r'(?m)^\s*#include\s+[<"]([^>"]+)[>"]', text):
        include_path = _resolve_include(include_name, path.parent, include_dir)
        if include_path is not None:
            chunks.append(_source_with_includes(include_path, include_dir, seen))
    return "\n".join(chunks)


def _resolve_include(include_name: str, current_dir: Path, include_dir: Path) -> Path | None:
    normalized = include_name.replace("\\", "/")
    candidates = [current_dir / normalized, include_dir / normalized]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _preset_content_safe(content: str) -> bool:
    values = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "=" not in line:
            return False
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().casefold()
    return (
        values.get("InpDryRunOnly") == "true"
        and values.get("InpBrokerActionAllowed") == "false"
        and values.get("InpMlShadowReadEnabled") == "true"
        and values.get("InpMlHandoffFileName") == HANDOFF_FILE_NAME.casefold()
        and values.get("InpMlShadowLogFileName") == SHADOW_TAP_LOG_NAME.casefold()
    )


def _target_record_safe(target: dict[str, Any]) -> bool:
    presets_dir = Path(target.get("presets_dir", ""))
    if not _path_has_suffix(presets_dir, ("mql5", "presets")):
        return False
    allowed = set(ACCOUNT_SOURCES.get(target.get("account_label", ""), ()))
    for preset in target.get("presets", []):
        source_name = preset.get("source_name", "")
        target_path = Path(preset.get("target_path", ""))
        if source_name not in allowed:
            return False
        if target_path.parent != presets_dir or target_path.suffix.casefold() != ".set":
            return False
        expected_prefix = f"{Path(source_name).stem}.{target.get('account_label')}.{PRESET_SUFFIX}"
        if target_path.stem != expected_prefix:
            return False
    return bool(target.get("presets"))


def _targets_safe(targets: list[dict[str, Any]]) -> bool:
    return bool(targets) and all(_target_record_safe(target) for target in targets)


def _path_has_suffix(path: Path, suffix: tuple[str, ...]) -> bool:
    parts = tuple(part.casefold() for part in path.parts)
    return len(parts) >= len(suffix) and parts[-len(suffix) :] == suffix


def _target_safety_detail(targets: list[dict[str, Any]]) -> str:
    if not targets:
        return "no targets"
    return "; ".join(f"{target.get('account_label')}={_target_record_safe(target)}" for target in targets)


def _all_source_names() -> list[str]:
    return sorted({name for sources in ACCOUNT_SOURCES.values() for name in sources})


def _next_allowed_stage(status: str) -> str:
    if status == "DEPLOYED_SAFE_PASSIVE_PRESETS":
        return "Safe broker-shadow presets are deployed. In MT5, load the account-specific preset for the attached broker-shadow expert, then run C28."
    if status == "PREFLIGHT_READY":
        return "Rerun C30 with --deploy to write safe passive broker-shadow presets into all three MT5 MQL5/Presets folders."
    if status == "DEPLOY_FAILED":
        return "Fix the preset deploy error and rerun C30 with --deploy before manual MT5 attach."
    return "Fix blocked C30 validations before manual MT5 attach."


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_broker_shadow_preset_deploy_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any]) -> None:
    if not pointer:
        return
    pointer["c30_broker_shadow_preset_deploy_report"] = payload["outputs"]["status_report_json"]
    pointer["c30_broker_shadow_preset_deploy_status"] = payload["status"]
    pointer["broker_shadow_safe_presets_deployed"] = payload["status"] == "DEPLOYED_SAFE_PASSIVE_PRESETS"
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _check(check: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": check, "passed": bool(passed), "detail": detail}


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
