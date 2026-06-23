from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_DEMO_FILL_COLLECTION_ATTACH_STATUS.json"
EA_NAME = "Phase2ExperimentalDemoExecutor"
SCRATCH_EX5 = Path("C:/MT5CompileScratchC58/MQL5/Experts/Phase2ExperimentalDemoExecutor.ex5")
SCRATCH_COMPILE_LOG = Path("C:/MT5CompileScratchC58/compile.log")
TEMPLATE_DIR = Path("outputs") / "reports" / "demo_fill_collection"
C58_REPORT = Path("outputs") / "reports" / "A3_ML_DEMO_FILL_COLLECTION_MODE_STATUS.json"
KILL_SWITCH_NAME = "a3_demo_fill_collection_kill_switch.txt"
AUTH_TOKEN = "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY"
COST_ACK_TOKEN = "I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT"


def _default_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "config" / "ml" / "mt5_accounts.yaml").exists():
        return cwd
    phase1 = cwd / "xau-usd" / "xauusd-phase1"
    if (phase1 / "config" / "ml" / "mt5_accounts.yaml").exists():
        return phase1
    return cwd


def attach_demo_fill_collection(
    root: Path,
    report_json: Path | None = None,
    *,
    apply: bool = False,
    wait_seconds: int = 90,
    account_labels: set[str] | None = None,
) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    report_json.parent.mkdir(parents=True, exist_ok=True)
    registry = _read_json(root / "config" / "ml" / "mt5_accounts.yaml")
    c58 = _read_json(root / C58_REPORT)
    registry_accounts = _accounts(registry)
    accounts = _select_accounts(registry_accounts, account_labels)
    checks = _preflight_checks(root, c58, registry_accounts, accounts)
    if not apply:
        payload = _payload("NOOP_APPLY_REQUIRED", checks, [], apply, wait_seconds)
        _write_report(report_json, payload)
        return report_json
    if any(not item["passed"] for item in checks):
        payload = _payload("ATTACH_BLOCKED", checks, [], apply, wait_seconds)
        _write_report(report_json, payload)
        return report_json

    results = []
    for account in accounts:
        results.append(_attach_account(root, account, wait_seconds))
    status = "ATTACHED_AND_RUNTIME_CONFIRMED" if all(item["status"] == "ATTACHED_RUNTIME_CONFIRMED" for item in results) else "ATTACHED_PENDING_RUNTIME"
    payload = _payload(status, checks, results, apply, wait_seconds)
    _write_report(report_json, payload)
    return report_json


def _attach_account(root: Path, account: dict[str, Any], wait_seconds: int) -> dict[str, Any]:
    label = account["account_label"]
    data_path = Path(account["expected_data_path"])
    terminal_exe = Path(account["terminal_exe"])
    profile_dir = data_path / "MQL5" / "Profiles" / "Charts" / "Default"
    files_dir = data_path / "MQL5" / "Files"
    preset_dir = data_path / "MQL5" / "Presets"
    logs_dir = data_path / "MQL5" / "Logs"
    template = root / TEMPLATE_DIR / f"{label}_{EA_NAME}.demo_fill_collection.review_only.set.template"
    values = _parse_set(template)
    startup_log = files_dir / values["InpStartupLogFileName"]
    terminal_closed = _close_terminal(terminal_exe)
    backup_dir = _backup_profile(profile_dir, data_path, label)
    deployed = _deploy_runtime_files(root, data_path, template, label)
    before_charts = _inventory(profile_dir)
    target_chart, chart_action = _write_or_update_chart(profile_dir, values)
    _launch_terminal(terminal_exe, bool(account.get("portable")))
    runtime = _wait_for_startup(startup_log, values["InpRunId"], wait_seconds)
    after_charts = _inventory(profile_dir)
    compile_log = logs_dir / "compile_c58_demo_fill_collection.log"
    if SCRATCH_COMPILE_LOG.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SCRATCH_COMPILE_LOG, compile_log)
    status = "ATTACHED_RUNTIME_CONFIRMED" if runtime["confirmed"] else "ATTACHED_RUNTIME_PENDING"
    return {
        "status": status,
        "account_label": label,
        "account_login": account["expected_login"],
        "terminal_exe": str(terminal_exe),
        "data_path": str(data_path),
        "profile_backup": str(backup_dir),
        "chart": str(target_chart),
        "chart_action": chart_action,
        "terminal_closed_before_profile_edit": terminal_closed,
        "terminal_relaunched": True,
        "deployed_files": deployed,
        "compile_log": str(compile_log),
        "startup_log": str(startup_log),
        "runtime": runtime,
        "template_values": {
            key: values.get(key, "")
            for key in (
                "InpRunId",
                "InpAllowedAccountLoginsCsv",
                "InpDryRunOnly",
                "InpBrokerActionAllowed",
                "InpFixedLot",
                "InpMaxOrdersPerDay",
                "InpMaxAccountOrdersPerDay",
                "InpMaxOpenPositionsPerInstance",
                "InpMaxOpenPositionsPerMagic",
                "InpMinSecondsBetweenOrders",
                "InpMaxEstimatedCostR",
                "InpMaxMeasuredSpreadPoints",
                "InpTradeSessionGateEnabled",
            )
        },
        "before_charts": before_charts,
        "after_charts": after_charts,
    }


def _preflight_checks(
    root: Path,
    c58: dict[str, Any],
    registry_accounts: list[dict[str, Any]],
    accounts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks = [
        _check("c58_ready", c58.get("status") == "DEMO_FILL_COLLECTION_REVIEW_PACKET_READY", c58.get("status", "MISSING")),
        _check("scratch_ex5_exists", SCRATCH_EX5.exists(), str(SCRATCH_EX5)),
        _check("compile_log_0_errors_0_warnings", _compile_log_passed(SCRATCH_COMPILE_LOG), str(SCRATCH_COMPILE_LOG)),
        _check("three_accounts_present", len(registry_accounts) == 3, ",".join(item.get("account_label", "") for item in registry_accounts)),
    ]
    for account in accounts:
        label = account["account_label"]
        data_path = Path(account["expected_data_path"])
        template = root / TEMPLATE_DIR / f"{label}_{EA_NAME}.demo_fill_collection.review_only.set.template"
        values = _parse_set(template)
        identity = _mt5_identity(Path(account["terminal_exe"]))
        exposure = _xauusd_exposure(Path(account["terminal_exe"]))
        kill_switch = data_path / "MQL5" / "Files" / KILL_SWITCH_NAME
        charts = _inventory(data_path / "MQL5" / "Profiles" / "Charts" / "Default")
        existing_fill = [item for item in charts if item.get("run_id", "").startswith("A3_DEMO_FILL_COLLECTION_")]
        existing_phase2 = [item for item in charts if item.get("expert") == EA_NAME]
        checks.extend(
            [
                _check(f"{label}_terminal_exists", Path(account["terminal_exe"]).exists(), account["terminal_exe"]),
                _check(f"{label}_data_path_exists", data_path.exists(), str(data_path)),
                _check(f"{label}_template_exists", template.exists(), str(template)),
                _check(f"{label}_template_login_matches", values.get("InpAllowedAccountLoginsCsv") == account["expected_login"], values.get("InpAllowedAccountLoginsCsv", "")),
                _check(f"{label}_template_hard_caps", _hard_caps_ok(values), _hard_caps_detail(values)),
                _check(f"{label}_identity_login_matches", str(identity.get("login", "")) == account["expected_login"], json.dumps(identity, sort_keys=True)),
                _check(f"{label}_identity_server_demo", "Demo" in str(identity.get("server", "")) and "Live" not in str(identity.get("server", "")), json.dumps(identity, sort_keys=True)),
                _check(f"{label}_identity_trade_mode_demo", identity.get("trade_mode") == 0, json.dumps(identity, sort_keys=True)),
                _check(f"{label}_xauusd_exposure_zero", exposure.get("total", 0) == 0, json.dumps(exposure, sort_keys=True)),
                _check(f"{label}_kill_switch_absent", not kill_switch.exists(), str(kill_switch)),
                _check(f"{label}_fill_collection_chart_count_lte_1", len(existing_fill) <= 1, ",".join(item.get("chart", "") for item in existing_fill) or "none"),
                _check(f"{label}_phase2_chart_count_lte_1", len(existing_phase2) <= 1, str([item.get("chart", "") for item in existing_phase2])),
            ]
        )
    return checks


def _deploy_runtime_files(root: Path, data_path: Path, template: Path, label: str) -> list[str]:
    mql5 = data_path / "MQL5"
    experts = mql5 / "Experts"
    include = mql5 / "Include"
    phase1 = include / "Phase1"
    presets = mql5 / "Presets"
    experts.mkdir(parents=True, exist_ok=True)
    include.mkdir(parents=True, exist_ok=True)
    phase1.mkdir(parents=True, exist_ok=True)
    presets.mkdir(parents=True, exist_ok=True)
    plan = [
        (root / "mt5" / "Experts" / f"{EA_NAME}.mq5", experts / f"{EA_NAME}.mq5"),
        (SCRATCH_EX5, experts / f"{EA_NAME}.ex5"),
        (root / "mt5" / "Include" / "DirectionStateShadow.mqh", include / "DirectionStateShadow.mqh"),
        (root / "mt5" / "Include" / "A3MlShadowTap.mqh", include / "A3MlShadowTap.mqh"),
        (root / "mt5" / "Include" / "A3MlEaHandoff.mqh", include / "A3MlEaHandoff.mqh"),
        (root / "mt5" / "Include" / "Phase1" / "Phase1Types.mqh", phase1 / "Phase1Types.mqh"),
        (root / "mt5" / "Include" / "Phase1" / "Phase1BreakoutRetest.mqh", phase1 / "Phase1BreakoutRetest.mqh"),
        (template, presets / f"{EA_NAME}.{label}.demo_fill_collection.local.set"),
    ]
    deployed = []
    for source, target in plan:
        if not source.exists():
            raise FileNotFoundError(source)
        shutil.copy2(source, target)
        deployed.append(str(target))
    return deployed


def _write_or_update_chart(profile_dir: Path, values: dict[str, str]) -> tuple[Path, str]:
    profile_dir.mkdir(parents=True, exist_ok=True)
    phase2_charts = [chart for chart in sorted(profile_dir.glob("chart*.chr")) if f"name={EA_NAME}" in _read_text(chart)]
    expert_block = _expert_block(values)
    if len(phase2_charts) == 1:
        chart = phase2_charts[0]
        text = _read_text(chart)
        _write_mt5_text(chart, _replace_expert_block(text, expert_block))
        return chart, "updated_existing_phase2_chart"
    if len(phase2_charts) > 1:
        raise RuntimeError(f"Refusing to attach with multiple existing {EA_NAME} charts: {phase2_charts}")
    chart = profile_dir / f"chart{_next_chart_index(profile_dir):02d}.chr"
    _write_mt5_text(chart, _new_chart_text(chart, values, expert_block))
    _prepend_order(profile_dir, chart.name)
    return chart, "appended_new_phase2_chart"


def _expert_block(values: dict[str, str]) -> str:
    return "\n".join(
        [
            "<expert>",
            f"name={EA_NAME}",
            f"path=Experts\\{EA_NAME}.ex5",
            "expertmode=1",
            "<inputs>",
            *[f"{key}={value}" for key, value in values.items()],
            "</inputs>",
            "</expert>",
        ]
    )


def _replace_expert_block(text: str, expert_block: str) -> str:
    text = _normalize_newlines(text)
    start = text.find("<expert>")
    end = text.find("</expert>", start)
    if start < 0 or end < 0:
        raise RuntimeError("Existing chart is missing a replaceable expert block.")
    end += len("</expert>")
    return text[:start].rstrip() + "\n\n" + expert_block + "\n" + text[end:].lstrip()


def _new_chart_text(chart: Path, values: dict[str, str], expert_block: str) -> str:
    index = _chart_number(chart)
    left = ((index - 1) % 2) * 515
    top = ((index - 1) // 2) * 526
    return "\n".join(
        [
            "<chart>",
            f"id={int(time.time())}{index:04d}",
            "symbol=XAUUSD",
            "description=Gold",
            "period_type=0",
            "period_size=5",
            "digits=2",
            "tick_size=0.010000",
            "scale=3",
            "mode=1",
            "fore=0",
            "grid=0",
            "volume=0",
            "scroll=1",
            "shift=1",
            "one_click=0",
            "bidline=1",
            "askline=1",
            "days=0",
            f"window_left={left}",
            f"window_top={top}",
            f"window_right={left + 515}",
            f"window_bottom={top + 526}",
            "windows_total=1",
            "",
            expert_block,
            "",
            "<window>",
            "height=100.000000",
            "objects=0",
            "<indicator>",
            "name=Main",
            "path=",
            "apply=1",
            "</indicator>",
            "</window>",
            "</chart>",
            "",
        ]
    )


def _backup_profile(profile_dir: Path, data_path: Path, label: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = data_path / "_codex_quarantine" / "profile_backups" / f"c59_demo_fill_collection_{label}_{stamp}"
    if profile_dir.exists():
        shutil.copytree(profile_dir, backup)
    else:
        backup.mkdir(parents=True, exist_ok=True)
    return backup


def _wait_for_startup(path: Path, run_id: str, wait_seconds: int) -> dict[str, Any]:
    before_lines = _csv_line_count(path)
    deadline = time.time() + max(1, wait_seconds)
    while time.time() < deadline:
        text = _read_text(path)
        lines = [line for line in text.splitlines() if line.strip()]
        if any(run_id in line and "ATTACHED_DEMO_EXECUTOR_ENABLED" in line for line in lines[before_lines:]):
            return {
                "confirmed": True,
                "line_count_before": before_lines,
                "line_count_after": len(lines),
                "last_line": lines[-1] if lines else "",
            }
        time.sleep(1.0)
    lines = [line for line in _read_text(path).splitlines() if line.strip()]
    return {
        "confirmed": False,
        "line_count_before": before_lines,
        "line_count_after": len(lines),
        "last_line": lines[-1] if lines else "",
    }


def _close_terminal(terminal_exe: Path) -> bool:
    command = f"""
$target = (Resolve-Path -LiteralPath '{terminal_exe}').Path
$procs = Get-CimInstance Win32_Process | Where-Object {{ $_.ExecutablePath -eq $target }}
if(-not $procs) {{ exit 0 }}
foreach($proc in $procs) {{
  $p = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
  if($p) {{ [void]$p.CloseMainWindow() }}
}}
Start-Sleep -Seconds 5
foreach($proc in $procs) {{
  $p = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
  if($p) {{ Stop-Process -Id $proc.ProcessId -Force }}
}}
exit 0
"""
    result = subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True, timeout=45)
    return result.returncode == 0


def _launch_terminal(terminal_exe: Path, portable: bool) -> None:
    command = [str(terminal_exe)]
    if portable:
        command.append("/portable")
    subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _mt5_identity(terminal_exe: Path) -> dict[str, Any]:
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:
        return {"ok": False, "error": f"MetaTrader5 import failed: {exc}"}
    if not mt5.initialize(path=str(terminal_exe)):
        return {"ok": False, "error": str(mt5.last_error())}
    try:
        info = mt5.account_info()
        terminal = mt5.terminal_info()
        return {
            "ok": info is not None,
            "login": int(getattr(info, "login", 0)) if info is not None else None,
            "server": getattr(info, "server", "") if info is not None else "",
            "trade_mode": int(getattr(info, "trade_mode", -1)) if info is not None else None,
            "connected": bool(getattr(terminal, "connected", False)) if terminal is not None else False,
        }
    finally:
        mt5.shutdown()


def _xauusd_exposure(terminal_exe: Path) -> dict[str, Any]:
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:
        return {"ok": False, "error": f"MetaTrader5 import failed: {exc}", "total": 999}
    if not mt5.initialize(path=str(terminal_exe)):
        return {"ok": False, "error": str(mt5.last_error()), "total": 999}
    try:
        positions = mt5.positions_get(symbol="XAUUSD") or []
        orders = mt5.orders_get(symbol="XAUUSD") or []
        return {
            "ok": True,
            "positions": len(positions),
            "orders": len(orders),
            "total": len(positions) + len(orders),
            "position_tickets": [int(getattr(item, "ticket", 0)) for item in positions],
            "order_tickets": [int(getattr(item, "ticket", 0)) for item in orders],
        }
    finally:
        mt5.shutdown()


def _inventory(profile_dir: Path) -> list[dict[str, str]]:
    rows = []
    for chart in sorted(profile_dir.glob("chart*.chr")) if profile_dir.exists() else []:
        text = _read_text(chart)
        values = _inputs(text)
        rows.append(
            {
                "chart": chart.name,
                "symbol": _value(text, "symbol"),
                "period_size": _value(text, "period_size"),
                "expert": _expert_name(text),
                "run_id": values.get("InpRunId", ""),
                "broker_action_allowed": values.get("InpBrokerActionAllowed", ""),
                "dry_run_only": values.get("InpDryRunOnly", ""),
                "login_allowlist": values.get("InpAllowedAccountLoginsCsv", ""),
                "max_orders_per_day": values.get("InpMaxOrdersPerDay", ""),
                "max_account_orders_per_day": values.get("InpMaxAccountOrdersPerDay", ""),
            }
        )
    return rows


def _accounts(registry: dict[str, Any]) -> list[dict[str, Any]]:
    accounts = registry.get("accounts", {})
    return [accounts[key] for key in sorted(accounts)]


def _select_accounts(accounts: list[dict[str, Any]], labels: set[str] | None) -> list[dict[str, Any]]:
    if not labels:
        return accounts
    selected = [account for account in accounts if account.get("account_label") in labels]
    found = {account.get("account_label") for account in selected}
    missing = sorted(labels - found)
    if missing:
        raise ValueError(f"Unknown account label(s): {','.join(missing)}")
    return selected


def _hard_caps_ok(values: dict[str, str]) -> bool:
    expected = {
        "InpDryRunOnly": "false",
        "InpBrokerActionAllowed": "true",
        "InpFixedLot": "0.01",
        "InpMaxOrdersPerDay": "3",
        "InpMaxAccountOrdersPerDay": "3",
        "InpMaxOpenPositionsPerInstance": "1",
        "InpMaxOpenPositionsPerMagic": "1",
        "InpMinSecondsBetweenOrders": "300",
        "InpMaxEstimatedCostR": "0.15",
        "InpMaxMeasuredSpreadPoints": "75.0",
        "InpTradeSessionGateEnabled": "false",
        "InpExperimentalAuthorizationToken": AUTH_TOKEN,
        "InpCostSuspensionAcknowledgementToken": COST_ACK_TOKEN,
    }
    return all(values.get(key) == value for key, value in expected.items())


def _hard_caps_detail(values: dict[str, str]) -> str:
    keys = [
        "InpDryRunOnly",
        "InpBrokerActionAllowed",
        "InpFixedLot",
        "InpMaxOrdersPerDay",
        "InpMaxAccountOrdersPerDay",
        "InpMaxOpenPositionsPerInstance",
        "InpMaxOpenPositionsPerMagic",
        "InpMinSecondsBetweenOrders",
        "InpMaxEstimatedCostR",
        "InpMaxMeasuredSpreadPoints",
        "InpTradeSessionGateEnabled",
    ]
    return "; ".join(f"{key}={values.get(key, '')}" for key in keys)


def _inputs(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    in_inputs = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped == "<inputs>":
            in_inputs = True
            continue
        if stripped == "</inputs>":
            in_inputs = False
            continue
        if in_inputs and "=" in stripped:
            key, value = stripped.split("=", 1)
            values[key] = value
    return values


def _expert_name(text: str) -> str:
    in_expert = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped == "<expert>":
            in_expert = True
            continue
        if stripped == "</expert>":
            in_expert = False
            continue
        if in_expert and stripped.startswith("name="):
            return stripped.split("=", 1)[1]
    return ""


def _value(text: str, key: str) -> str:
    prefix = f"{key}="
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith(prefix):
            return stripped.split("=", 1)[1]
    return ""


def _parse_set(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _csv_line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len([line for line in _read_text(path).splitlines() if line.strip()])


def _compile_log_passed(path: Path) -> bool:
    text = _read_text(path).lower()
    return "result: 0 errors, 0 warnings" in text or "result: 0 error(s), 0 warning(s)" in text


def _next_chart_index(profile_dir: Path) -> int:
    return max((_chart_number(path) for path in profile_dir.glob("chart*.chr")), default=0) + 1


def _chart_number(path: Path) -> int:
    match = re.search(r"chart(\d+)", path.stem, re.IGNORECASE)
    return int(match.group(1)) if match else 1


def _prepend_order(profile_dir: Path, chart_name: str) -> None:
    order = profile_dir / "order.wnd"
    lines = [line.strip() for line in _read_text(order).splitlines() if line.strip()]
    lines = [chart_name, *[line for line in lines if line.lower() != chart_name.lower()]]
    _write_mt5_text(order, "\n".join(lines) + "\n")


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _write_mt5_text(path: Path, text: str) -> None:
    normalized = _normalize_newlines(text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(normalized.replace("\n", "\r\n").encode("utf-8"))


def _payload(status: str, checks: list[dict[str, Any]], accounts: list[dict[str, Any]], apply: bool, wait_seconds: int) -> dict[str, Any]:
    return {
        "status": status,
        "stage": "C59-ML-DEMO-FILL-COLLECTION-ATTACH",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": "Owner requested compile and attach for controlled demo fill collection. Demo-only; no live trading; no Python ML prediction authorization.",
        "apply": apply,
        "wait_seconds": wait_seconds,
        "authorization": {
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "canonical_broker_action_authorized": False,
            "manual_demo_fill_collection_attached": status.startswith("ATTACHED"),
        },
        "checks": checks,
        "accounts": accounts,
    }


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    path.with_suffix(".md").write_text(_render_md(payload), encoding="utf-8")


def _render_md(payload: dict[str, Any]) -> str:
    checks = payload.get("checks", [])
    accounts = payload.get("accounts", [])
    lines = [
        "# A3 ML Demo Fill Collection Attach Status",
        "",
        f"Overall status: {payload['status']}",
        "",
        str(payload["authority"]),
        "",
        "## Authorization",
        "",
        "- Training authorized: false.",
        "- Python demo predictions authorized: false.",
        "- Canonical broker action authorized: false.",
        f"- Manual demo fill collection attached: {str(payload['authorization']['manual_demo_fill_collection_attached']).lower()}.",
        "",
        "## Checks",
        "",
        "| Check | Passed | Detail |",
        "|---|---:|---|",
    ]
    lines.extend(f"| {item['check']} | {str(item['passed']).lower()} | {_escape(item['detail'])} |" for item in checks)
    lines.extend(["", "## Accounts", ""])
    if accounts:
        lines.extend(["| Account | Login | Status | Chart action | Startup confirmed | Startup log |", "|---|---:|---|---|---:|---|"])
        for item in accounts:
            lines.append(
                "| {label} | {login} | {status} | {action} | {confirmed} | {log} |".format(
                    label=item.get("account_label", ""),
                    login=item.get("account_login", ""),
                    status=item.get("status", ""),
                    action=item.get("chart_action", ""),
                    confirmed=str(item.get("runtime", {}).get("confirmed", False)).lower(),
                    log=_escape(item.get("startup_log", "")),
                )
            )
    else:
        lines.append("No account mutations performed.")
    lines.append("")
    return "\n".join(lines)


def _check(check: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": check, "passed": bool(passed), "detail": detail}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    data = path.read_bytes()
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        return data.decode("utf-16", errors="replace")
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig", errors="replace")
    for encoding in ("utf-8", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Attach controlled C58 demo fill-collection charts.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--wait-seconds", type=int, default=90)
    parser.add_argument("--account-label", action="append", choices=["A1", "A2", "A3"], help="Attach only the selected account label. Repeatable.")
    args = parser.parse_args(argv)
    labels = set(args.account_label) if args.account_label else None
    report = attach_demo_fill_collection(args.root, args.report_json, apply=args.apply, wait_seconds=args.wait_seconds, account_labels=labels)
    payload = _read_json(report)
    print(f"C59 demo fill collection attach status: {payload.get('status', 'UNKNOWN')}")
    print(report)
    return 0 if payload.get("status") in {"ATTACHED_AND_RUNTIME_CONFIRMED", "NOOP_APPLY_REQUIRED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
