from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .market_data_export import _sha256_file, _table, _utc_now, _write_json_atomic


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_OBSERVER_DEPLOY_STATUS.json"
OBSERVER_DEPLOY_SCHEMA_VERSION = "a3_ml_observer_deploy_status_v1"
OBSERVER_SOURCE = Path("mt5") / "Experts" / "A3MlPredictionObserver.mq5"
HANDOFF_INCLUDE = Path("mt5") / "Include" / "A3MlEaHandoff.mqh"
OBSERVER_PRESET = Path("mt5") / "Presets" / "A3MlPredictionObserver.passive_xauusd.set"
SCRATCH_ROOT = Path("C:/MT5CompileScratch/A3MlPredictionObserverC09")


def prepare_observer_deploy(
    root: Path,
    report_json: Path | None = None,
    *,
    deploy: bool = False,
    compile_scratch: bool = True,
    scratch_root: Path | None = None,
    metaeditor_path: Path | None = None,
) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    registry_path = root / "config" / "ml" / "mt5_accounts.yaml"
    source_path = root / OBSERVER_SOURCE
    include_path = root / HANDOFF_INCLUDE
    preset_path = root / OBSERVER_PRESET
    pointer_path = root / "outputs" / "reports" / "C02_DATASET_POINTER.json"
    validations: list[dict[str, Any]] = []
    targets: list[dict[str, Any]] = []
    accounts: tuple[MT5AccountSpec, ...] = ()

    validations.append(_check("registry_exists", registry_path.exists(), str(registry_path)))
    try:
        registry = load_mt5_account_registry(registry_path)
        accounts = registry.accounts
        labels = ",".join(account.account_label for account in accounts)
        validations.append(_check("registry_parses", True, f"accounts={labels}"))
        targets = _target_records(accounts)
        validations.append(_check("all_accounts_have_data_roots", all(account.expected_data_path for account in accounts), _data_root_detail(accounts)))
        validations.append(_check("all_target_paths_safe", _targets_safe(targets), _target_safety_detail(targets)))
    except Exception as exc:
        validations.append(_check("registry_parses", False, f"{type(exc).__name__}: {exc}"))

    source_artifacts = {
        "observer_source": str(source_path),
        "handoff_include": str(include_path),
        "passive_preset": str(preset_path),
    }
    validations.extend(
        [
            _check("observer_source_exists", source_path.exists(), str(source_path)),
            _check("handoff_include_exists", include_path.exists(), str(include_path)),
            _check("passive_preset_exists", preset_path.exists(), str(preset_path)),
        ]
    )

    compile_result = _compile_observer_scratch(
        source_path,
        include_path,
        accounts=accounts,
        enabled=compile_scratch,
        scratch_root=scratch_root or SCRATCH_ROOT,
        metaeditor_path=metaeditor_path,
    )
    validations.append(_check("scratch_compile_passed", bool(compile_result.get("passed")), compile_result.get("detail", "")))

    ready = all(item["passed"] for item in validations)
    deploy_attempted = bool(deploy and ready)
    deployed_files: list[dict[str, Any]] = []
    deployment_error = ""
    if deploy_attempted:
        try:
            deployed_files = _deploy_files(
                source_path=source_path,
                include_path=include_path,
                preset_path=preset_path,
                ex5_path=Path(str(compile_result.get("ex5_path", ""))) if compile_result.get("ex5_path") else None,
                targets=targets,
            )
        except Exception as exc:
            deployment_error = f"{type(exc).__name__}: {exc}"
            validations.append(_check("deploy_copy_completed", False, deployment_error))

    if deployment_error:
        status = "DEPLOY_FAILED"
    elif deploy_attempted:
        status = "DEPLOYED_PASSIVE_OBSERVER"
    elif ready:
        status = "PREFLIGHT_READY"
    else:
        status = "PREFLIGHT_BLOCKED"

    payload = {
        "status": status,
        "stage": "C09-ML-OBSERVER-DEPLOY",
        "created_at_utc": _utc_now(),
        "schema_version": OBSERVER_DEPLOY_SCHEMA_VERSION,
        "mode": "DEPLOY" if deploy else "PREFLIGHT_ONLY",
        "authorization": {
            "passive_observer_deploy_requested": bool(deploy),
            "passive_observer_deploy_attempted": deploy_attempted,
            "ea_attachment_authorized": False,
            "chart_or_profile_change_authorized": False,
            "python_demo_predictions_authorized": False,
            "broker_action_authorized": False,
        },
        "inputs": {
            "registry_path": str(registry_path),
            **source_artifacts,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
            "deployed_files": deployed_files,
        },
        "accounts": [_account_payload(account) for account in accounts],
        "targets": targets,
        "compile": compile_result,
        "validations": validations,
        "boundary": {
            "mt5_connection_attempted": False,
            "terminal_runtime_change_authorized": False,
            "profile_or_chart_change_authorized": False,
            "ea_source_deploy_attempted": deploy_attempted,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(pointer_path, payload)
    return report_json


def render_observer_deploy_status_md(payload: dict[str, Any]) -> str:
    validation_rows = [
        {"Check": item.get("check", ""), "Passed": str(item.get("passed", False)).lower(), "Detail": item.get("detail", "")}
        for item in payload.get("validations", [])
    ]
    target_rows = [
        {
            "Account": item.get("account_label", ""),
            "Login": item.get("account_scope", ""),
            "Data root": item.get("data_root", ""),
            "Expert": item.get("source_target", ""),
            "Include": item.get("include_target", ""),
            "Preset": item.get("preset_target", ""),
        }
        for item in payload.get("targets", [])
    ]
    deployed = payload.get("outputs", {}).get("deployed_files", [])
    deployed_lines = "\n".join(f"- {item['target_path']}" for item in deployed) if deployed else "- none"
    compile_result = payload.get("compile", {})
    return "\n".join(
        [
            "# A3 ML Observer Deploy Status",
            "",
            f"Overall status: {payload['status']}",
            f"Mode: {payload['mode']}",
            "",
            "## Authorization",
            "",
            f"- Passive observer deploy requested: {str(payload['authorization']['passive_observer_deploy_requested']).lower()}.",
            f"- Passive observer deploy attempted: {str(payload['authorization']['passive_observer_deploy_attempted']).lower()}.",
            "- EA attachment authorized: false.",
            "- Chart or profile change authorized: false.",
            "- Python demo predictions authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Targets",
            "",
            _table(target_rows, ["Account", "Login", "Data root", "Expert", "Include", "Preset"]) if target_rows else "No targets.",
            "",
            "## Compile",
            "",
            f"- Attempted: {str(compile_result.get('attempted', False)).lower()}.",
            f"- Passed: {str(compile_result.get('passed', False)).lower()}.",
            f"- MetaEditor: {compile_result.get('metaeditor_path', '') or 'not selected'}.",
            f"- Scratch source: {compile_result.get('scratch_source_path', '')}.",
            f"- EX5 path: {compile_result.get('ex5_path', '')}.",
            f"- Log path: {compile_result.get('log_path', '')}.",
            f"- Detail: {compile_result.get('detail', '')}.",
            "",
            "## Validations",
            "",
            _table(validation_rows, ["Check", "Passed", "Detail"]) if validation_rows else "No validations ran.",
            "",
            "## Deployed Files",
            "",
            deployed_lines,
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Terminal runtime change authorized: false.",
            "- Profile or chart change authorized: false.",
            f"- EA source deploy attempted: {str(payload['boundary']['ea_source_deploy_attempted']).lower()}.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _compile_observer_scratch(
    source_path: Path,
    include_path: Path,
    *,
    accounts: tuple[MT5AccountSpec, ...],
    enabled: bool,
    scratch_root: Path,
    metaeditor_path: Path | None,
) -> dict[str, Any]:
    if not enabled:
        return {"attempted": False, "passed": True, "status": "SKIPPED", "detail": "scratch compile disabled for this run"}
    if not source_path.exists() or not include_path.exists():
        return {"attempted": False, "passed": False, "status": "BLOCKED", "detail": "source or include file is missing"}
    metaeditor = _select_metaeditor(metaeditor_path, accounts)
    if metaeditor is None:
        return {"attempted": False, "passed": False, "status": "BLOCKED", "detail": "MetaEditor64.exe was not found"}

    run_dir = scratch_root / _scratch_run_id()
    experts_dir = run_dir / "MQL5" / "Experts"
    experts_dir.mkdir(parents=True, exist_ok=True)
    scratch_source = experts_dir / source_path.name
    scratch_include = experts_dir / include_path.name
    log_path = run_dir / "compile_A3MlPredictionObserver.log"
    ex5_path = scratch_source.with_suffix(".ex5")
    source_text = source_path.read_text(encoding="utf-8")
    source_text = source_text.replace("#include <A3MlEaHandoff.mqh>", '#include "A3MlEaHandoff.mqh"')
    scratch_source.write_text(source_text, encoding="utf-8")
    shutil.copy2(include_path, scratch_include)

    command = [str(metaeditor), f"/compile:{scratch_source}", f"/log:{log_path}"]
    completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=90)
    log_text = _read_text_auto(log_path)
    passed = ex5_path.exists() and _log_says_zero_errors(log_text)
    return {
        "attempted": True,
        "passed": passed,
        "status": "PASS" if passed else "FAIL_CLOSED",
        "detail": "scratch compile produced EX5 with 0 errors" if passed else "scratch compile did not produce a clean EX5",
        "metaeditor_path": str(metaeditor),
        "scratch_source_path": str(scratch_source),
        "scratch_include_path": str(scratch_include),
        "log_path": str(log_path),
        "ex5_path": str(ex5_path) if ex5_path.exists() else "",
        "returncode": completed.returncode,
        "stdout_tail": _tail(completed.stdout),
        "stderr_tail": _tail(completed.stderr),
        "log_tail": _tail(log_text),
    }


def _deploy_files(
    *,
    source_path: Path,
    include_path: Path,
    preset_path: Path,
    ex5_path: Path | None,
    targets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    deployed: list[dict[str, Any]] = []
    for target in targets:
        experts_dir = Path(target["experts_dir"])
        include_dir = Path(target["include_dir"])
        presets_dir = Path(target["presets_dir"])
        if not _target_record_safe(target):
            raise ValueError(f"unsafe target paths for {target.get('account_label', 'UNKNOWN')}")
        experts_dir.mkdir(parents=True, exist_ok=True)
        include_dir.mkdir(parents=True, exist_ok=True)
        presets_dir.mkdir(parents=True, exist_ok=True)
        deployed.extend(
            [
                _copy_file(source_path, Path(target["source_target"]), target, "observer_source"),
                _copy_file(include_path, Path(target["include_target"]), target, "handoff_include"),
                _copy_file(preset_path, Path(target["preset_target"]), target, "passive_preset"),
            ]
        )
        if ex5_path is not None and ex5_path.exists():
            deployed.append(_copy_file(ex5_path, Path(target["ex5_target"]), target, "compiled_ex5"))
    return deployed


def _copy_file(source: Path, target: Path, target_record: dict[str, Any], artifact: str) -> dict[str, Any]:
    shutil.copy2(source, target)
    return {
        "artifact": artifact,
        "account_label": target_record["account_label"],
        "account_scope": target_record["account_scope"],
        "source_path": str(source),
        "target_path": str(target),
        "bytes": target.stat().st_size,
        "sha256": _sha256_file(target),
    }


def _target_records(accounts: tuple[MT5AccountSpec, ...]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for account in accounts:
        data_root = Path(account.expected_data_path) if account.expected_data_path else None
        experts_dir = data_root / "MQL5" / "Experts" if data_root else None
        include_dir = data_root / "MQL5" / "Include" if data_root else None
        presets_dir = data_root / "MQL5" / "Presets" if data_root else None
        records.append(
            {
                "account_label": account.account_label,
                "account_scope": account.account_scope,
                "data_root": str(data_root) if data_root else "",
                "experts_dir": str(experts_dir) if experts_dir else "",
                "include_dir": str(include_dir) if include_dir else "",
                "presets_dir": str(presets_dir) if presets_dir else "",
                "source_target": str(experts_dir / OBSERVER_SOURCE.name) if experts_dir else "",
                "ex5_target": str(experts_dir / OBSERVER_SOURCE.with_suffix(".ex5").name) if experts_dir else "",
                "include_target": str(include_dir / HANDOFF_INCLUDE.name) if include_dir else "",
                "preset_target": str(presets_dir / OBSERVER_PRESET.name) if presets_dir else "",
            }
        )
    return records


def _targets_safe(targets: list[dict[str, Any]]) -> bool:
    return bool(targets) and all(_target_record_safe(target) for target in targets)


def _target_record_safe(target: dict[str, Any]) -> bool:
    expected_suffixes = {
        "experts_dir": ("mql5", "experts"),
        "include_dir": ("mql5", "include"),
        "presets_dir": ("mql5", "presets"),
    }
    for key, suffix in expected_suffixes.items():
        path_text = target.get(key, "")
        if not path_text or not _path_has_suffix(Path(path_text), suffix):
            return False
    target_names = {
        "source_target": OBSERVER_SOURCE.name,
        "ex5_target": OBSERVER_SOURCE.with_suffix(".ex5").name,
        "include_target": HANDOFF_INCLUDE.name,
        "preset_target": OBSERVER_PRESET.name,
    }
    for key, name in target_names.items():
        path_text = target.get(key, "")
        if not path_text or Path(path_text).name != name:
            return False
    return True


def _path_has_suffix(path: Path, suffix: tuple[str, ...]) -> bool:
    parts = tuple(part.casefold() for part in path.parts)
    return len(parts) >= len(suffix) and parts[-len(suffix) :] == suffix


def _select_metaeditor(metaeditor_path: Path | None, accounts: tuple[MT5AccountSpec, ...]) -> Path | None:
    candidates: list[Path] = []
    if metaeditor_path is not None:
        candidates.append(metaeditor_path)
    candidates.append(Path("C:/Program Files/MetaTrader 5/MetaEditor64.exe"))
    for account in accounts:
        candidates.append(Path(account.terminal_exe).with_name("MetaEditor64.exe"))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_observer_deploy_status_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    pointer["c09_observer_deploy_status_report"] = payload["outputs"]["status_report_json"]
    pointer["c09_observer_deploy_status"] = payload["status"]
    pointer["passive_observer_deployed"] = payload["status"] == "DEPLOYED_PASSIVE_OBSERVER"
    pointer["python_demo_predictions_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _account_payload(account: MT5AccountSpec) -> dict[str, Any]:
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "role": account.role,
        "expected_data_path": account.expected_data_path or "",
        "files_roots": list(account.files_roots),
    }


def _next_allowed_stage(status: str) -> str:
    if status == "DEPLOYED_PASSIVE_OBSERVER":
        return "Passive observer files are copied. Attach only with the passive preset; Python predictions still require C03 PASS, C05 trained model, C04 shadow bridge, and C06 handoff."
    if status == "PREFLIGHT_READY":
        return "Rerun C09 with --deploy when you are ready to copy passive observer files to all three MT5 terminal data roots. No chart attach is performed."
    return "Fix blocked validations, then rerun C09 preflight. Do not attach an observer until this report is ready."


def _check(check: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": check, "passed": bool(passed), "detail": detail}


def _data_root_detail(accounts: tuple[MT5AccountSpec, ...]) -> str:
    return "; ".join(f"{account.account_label}={account.expected_data_path or 'missing'}" for account in accounts)


def _target_safety_detail(targets: list[dict[str, Any]]) -> str:
    if not targets:
        return "no targets"
    return "; ".join(f"{target.get('account_label')}={_target_record_safe(target)}" for target in targets)


def _scratch_run_id() -> str:
    return "run_" + re.sub(r"[^0-9A-Za-z]+", "_", _utc_now()).strip("_")


def _log_says_zero_errors(text: str) -> bool:
    normalized = text.casefold()
    return bool(re.search(r"\b0\s+errors?\b", normalized) or re.search(r"\b0\s+error\(s\)", normalized))


def _read_text_auto(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8", "utf-16"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def _tail(text: str, max_chars: int = 2000) -> str:
    text = text.strip()
    return text[-max_chars:] if len(text) > max_chars else text
