from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .market_data_export import _sha256_file, _table, _utc_now, _write_json_atomic
from .observer_deploy import _log_says_zero_errors, _read_text_auto, _select_metaeditor, _tail


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_BROKER_SHADOW_CONSUMER_DEPLOY_STATUS.json"
SCHEMA_VERSION = "a3_ml_broker_shadow_consumer_deploy_v1"
SCRATCH_ROOT = Path("C:/MT5CompileScratch/A3MlBrokerShadowConsumersC17")
ACCOUNT_SOURCES = {
    "A1": ("Phase2ExperimentalDemoExecutor.mq5", "Phase2ExperimentalDemoRepairExecutor.mq5"),
    "A2": ("Phase2ExperimentalDemoExecutor.mq5",),
    "A3": (
        "Account3BreakoutImprovedExecutor.mq5",
        "Account3BreakoutPlainExecutor.mq5",
        "Account3BreakoutTier1CompatExecutor.mq5",
        "Account3SoftRetestExecutor.mq5",
    ),
}


def deploy_broker_shadow_consumers(
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
    pointer = _read_json(root / "outputs" / "reports" / "C02_DATASET_POINTER.json")
    accounts: tuple[MT5AccountSpec, ...] = ()
    targets: list[dict[str, Any]] = []
    validations: list[dict[str, Any]] = []
    validations.append(_check("registry_exists", registry_path.exists(), str(registry_path)))
    try:
        registry = load_mt5_account_registry(registry_path)
        accounts = registry.accounts
        validations.append(_check("registry_parses", True, ",".join(account.account_label for account in accounts)))
        targets = _target_records(accounts)
        validations.append(_check("all_target_paths_safe", _targets_safe(targets), _target_safety_detail(targets)))
    except Exception as exc:
        validations.append(_check("registry_parses", False, f"{type(exc).__name__}: {exc}"))

    source_names = _all_source_names()
    include_dir = root / "mt5" / "Include"
    expert_dir = root / "mt5" / "Experts"
    validations.append(_check("repo_include_dir_exists", include_dir.exists(), str(include_dir)))
    for source_name in source_names:
        validations.append(_check(f"source_exists_{source_name}", (expert_dir / source_name).exists(), str(expert_dir / source_name)))
    validations.append(_check("shadow_tap_include_exists", (include_dir / "A3MlShadowTap.mqh").exists(), str(include_dir / "A3MlShadowTap.mqh")))
    validations.append(_check("handoff_include_exists", (include_dir / "A3MlEaHandoff.mqh").exists(), str(include_dir / "A3MlEaHandoff.mqh")))

    compile_result = _compile_sources_scratch(
        root,
        source_names,
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
            deployed_files = _deploy_files(root, targets, compile_result)
        except Exception as exc:
            deployment_error = f"{type(exc).__name__}: {exc}"
            validations.append(_check("deploy_copy_completed", False, deployment_error))

    if deployment_error:
        status = "DEPLOY_FAILED"
    elif deploy_attempted and compile_result.get("attempted"):
        status = "DEPLOYED_COMPILED_SHADOW_CONSUMERS"
    elif deploy_attempted:
        status = "DEPLOYED_SOURCE_ONLY_SHADOW_CONSUMERS"
    elif ready:
        status = "PREFLIGHT_READY"
    else:
        status = "PREFLIGHT_BLOCKED"

    payload = {
        "status": status,
        "stage": "C17-BROKER-SHADOW-CONSUMER-DEPLOY",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "mode": "DEPLOY" if deploy else "PREFLIGHT_ONLY",
        "dataset_version": pointer.get("dataset_version", ""),
        "authorization": {
            "broker_shadow_consumer_deploy_requested": bool(deploy),
            "broker_shadow_consumer_deploy_attempted": deploy_attempted,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "inputs": {
            "registry_path": str(registry_path),
            "experts_dir": str(expert_dir),
            "include_dir": str(include_dir),
            "source_names": source_names,
        },
        "targets": targets,
        "compile": compile_result,
        "deployed_files": deployed_files,
        "validations": validations,
        "boundary": {
            "mt5_connection_attempted": False,
            "terminal_runtime_launch_attempted": False,
            "terminal_shutdown_attempted": False,
            "profile_or_chart_file_write_attempted": False,
            "expert_file_deploy_attempted": deploy_attempted,
            "compiled_ex5_deploy_attempted": deploy_attempted and bool(compile_result.get("attempted")),
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


def render_broker_shadow_consumer_deploy_md(payload: dict[str, Any]) -> str:
    validation_rows = [{"Check": item["check"], "Passed": str(item["passed"]).lower(), "Detail": item["detail"]} for item in payload.get("validations", [])]
    compile_rows = [
        {"Source": item.get("source_name", ""), "Passed": str(item.get("passed", False)).lower(), "Detail": item.get("detail", "")}
        for item in payload.get("compile", {}).get("sources", [])
    ]
    deployed_lines = "\n".join(f"- {item['account_label']} {item['artifact']}: {item['target_path']}" for item in payload.get("deployed_files", [])) or "- none"
    return "\n".join(
        [
            "# A3 ML Broker Shadow Consumer Deploy Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Authorization",
            "",
            "- Python demo predictions authorized: false.",
            "- EA consumption authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Compile",
            "",
            f"- Attempted: {str(payload.get('compile', {}).get('attempted', False)).lower()}.",
            f"- Passed: {str(payload.get('compile', {}).get('passed', False)).lower()}.",
            f"- MetaEditor: {payload.get('compile', {}).get('metaeditor_path', '') or 'not selected'}.",
            "",
            _table(compile_rows, ["Source", "Passed", "Detail"]) if compile_rows else "No per-source compile rows.",
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
            "- Terminal runtime launch attempted: false.",
            "- Terminal shutdown attempted: false.",
            "- Profile or chart file write attempted: false.",
            f"- Expert file deploy attempted: {str(payload['boundary']['expert_file_deploy_attempted']).lower()}.",
            f"- Compiled EX5 deploy attempted: {str(payload['boundary']['compiled_ex5_deploy_attempted']).lower()}.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _compile_sources_scratch(
    root: Path,
    source_names: list[str],
    *,
    accounts: tuple[MT5AccountSpec, ...],
    enabled: bool,
    scratch_root: Path,
    metaeditor_path: Path | None,
) -> dict[str, Any]:
    if not enabled:
        return {"attempted": False, "passed": True, "status": "SKIPPED", "detail": "scratch compile disabled for this run", "sources": []}
    metaeditor = _select_metaeditor(metaeditor_path, accounts)
    if metaeditor is None:
        return {"attempted": False, "passed": False, "status": "BLOCKED", "detail": "MetaEditor64.exe was not found", "sources": []}

    run_dir = scratch_root / ("run_" + _utc_now().replace(":", "_").replace("-", "_").replace(".", "_"))
    scratch_mql5 = run_dir / "MQL5"
    scratch_experts = scratch_mql5 / "Experts"
    scratch_include = scratch_mql5 / "Include"
    scratch_experts.mkdir(parents=True, exist_ok=True)
    shutil.copytree(root / "mt5" / "Include", scratch_include, dirs_exist_ok=True)
    shutil.copytree(root / "mt5" / "Include", scratch_experts, dirs_exist_ok=True)
    _rewrite_local_includes_in_tree(scratch_experts)

    rows = []
    all_passed = True
    for source_name in source_names:
        source = root / "mt5" / "Experts" / source_name
        scratch_source = scratch_experts / source_name
        shutil.copy2(source, scratch_source)
        scratch_source.write_text(_rewrite_local_includes(scratch_source.read_text(encoding="utf-8"), scratch_experts, scratch_source.parent), encoding="utf-8")
        log_path = run_dir / f"compile_{Path(source_name).stem}.log"
        command = [str(metaeditor), f"/compile:{scratch_source}", f"/log:{log_path}"]
        completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=120)
        log_text = _read_text_auto(log_path)
        ex5_path = scratch_source.with_suffix(".ex5")
        passed = ex5_path.exists() and _log_says_zero_errors(log_text)
        all_passed = all_passed and passed
        rows.append(
            {
                "source_name": source_name,
                "passed": passed,
                "detail": "compiled with 0 errors" if passed else "compile failed or EX5 missing",
                "scratch_source_path": str(scratch_source),
                "log_path": str(log_path),
                "ex5_path": str(ex5_path) if ex5_path.exists() else "",
                "returncode": completed.returncode,
                "stdout_tail": _tail(completed.stdout),
                "stderr_tail": _tail(completed.stderr),
                "log_tail": _tail(log_text),
            }
        )
    return {
        "attempted": True,
        "passed": all_passed,
        "status": "PASS" if all_passed else "FAIL_CLOSED",
        "detail": "all broker shadow consumers compiled with 0 errors" if all_passed else "one or more broker shadow consumers failed scratch compile",
        "metaeditor_path": str(metaeditor),
        "run_dir": str(run_dir),
        "sources": rows,
    }


def _rewrite_local_includes_in_tree(root: Path) -> None:
    for path in sorted(root.rglob("*.mqh")):
        path.write_text(_rewrite_local_includes(path.read_text(encoding="utf-8"), root, path.parent), encoding="utf-8")


def _rewrite_local_includes(text: str, local_root: Path, current_dir: Path) -> str:
    def replace(match):
        include_name = match.group(1).replace("\\", "/")
        target = local_root / include_name
        if target.exists():
            relative = _relative_include_path(target, current_dir)
            return f'#include "{relative}"'
        return match.group(0)

    import re

    return re.sub(r'(?m)^\s*#include\s+<([^>"]+)>', replace, text)


def _relative_include_path(target: Path, current_dir: Path) -> str:
    import os

    return os.path.relpath(target, current_dir).replace("\\", "/")


def _deploy_files(root: Path, targets: list[dict[str, Any]], compile_result: dict[str, Any]) -> list[dict[str, Any]]:
    deployed: list[dict[str, Any]] = []
    source_ex5 = {
        item.get("source_name", ""): Path(item.get("ex5_path", ""))
        for item in compile_result.get("sources", [])
        if item.get("ex5_path")
    }
    for target in targets:
        if not _target_record_safe(target):
            raise ValueError(f"unsafe target paths for {target.get('account_label', 'UNKNOWN')}")
        experts_dir = Path(target["experts_dir"])
        include_dir = Path(target["include_dir"])
        experts_dir.mkdir(parents=True, exist_ok=True)
        include_dir.mkdir(parents=True, exist_ok=True)
        for include_source in sorted((root / "mt5" / "Include").rglob("*.mqh")):
            relative = include_source.relative_to(root / "mt5" / "Include")
            deployed.append(_copy_file(include_source, include_dir / relative, target, "include"))
        for source_name in target["source_names"]:
            source = root / "mt5" / "Experts" / source_name
            deployed.append(_copy_file(source, experts_dir / source_name, target, "expert_source"))
            ex5_source = source_ex5.get(source_name)
            if ex5_source and ex5_source.exists():
                deployed.append(_copy_file(ex5_source, experts_dir / Path(source_name).with_suffix(".ex5").name, target, "compiled_ex5"))
    return deployed


def _copy_file(source: Path, target: Path, target_record: dict[str, Any], artifact: str) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
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
        data_root = Path(account.expected_data_path or "")
        records.append(
            {
                "account_label": account.account_label,
                "account_scope": account.account_scope,
                "data_root": str(data_root),
                "experts_dir": str(data_root / "MQL5" / "Experts"),
                "include_dir": str(data_root / "MQL5" / "Include"),
                "source_names": list(ACCOUNT_SOURCES.get(account.account_label, ())),
            }
        )
    return records


def _target_record_safe(target: dict[str, Any]) -> bool:
    experts_dir = Path(target.get("experts_dir", ""))
    include_dir = Path(target.get("include_dir", ""))
    if not _path_has_suffix(experts_dir, ("mql5", "experts")):
        return False
    if not _path_has_suffix(include_dir, ("mql5", "include")):
        return False
    source_names = target.get("source_names", [])
    allowed = set(ACCOUNT_SOURCES.get(target.get("account_label", ""), ()))
    return bool(source_names) and set(source_names).issubset(allowed)


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
    names = sorted({name for sources in ACCOUNT_SOURCES.values() for name in sources})
    return names


def _next_allowed_stage(status: str) -> str:
    if status == "DEPLOYED_COMPILED_SHADOW_CONSUMERS":
        return "Rerun C16. The active broker EAs should now be able to read and log ML handoff in shadow-only mode; Python prediction authority still depends on C03/C05/C04/C06 readiness."
    if status == "DEPLOYED_SOURCE_ONLY_SHADOW_CONSUMERS":
        return "Sources/includes were copied, but compiled EX5 files were not refreshed. Run C17 with scratch compile enabled before relying on active EA consumer readiness."
    if status == "PREFLIGHT_READY":
        return "Rerun C17 with --deploy to copy compiled shadow-consumer EAs and includes to all three MT5 data roots. Broker action remains false for ML."
    return "Fix C17 blocked validations before deploying broker shadow consumers."


def _check(check: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": check, "passed": bool(passed), "detail": detail}


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_broker_shadow_consumer_deploy_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any]) -> None:
    if not pointer:
        return
    pointer["c17_broker_shadow_consumer_deploy_report"] = payload["outputs"]["status_report_json"]
    pointer["c17_broker_shadow_consumer_deploy_status"] = payload["status"]
    pointer["broker_shadow_consumer_deployed"] = payload["status"] == "DEPLOYED_COMPILED_SHADOW_CONSUMERS"
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
