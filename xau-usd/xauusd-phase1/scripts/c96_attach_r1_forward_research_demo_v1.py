from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_PACKET = Path("outputs/reports/A3_R1_FORWARD_RESEARCH_DEMO_V1_PACKET.json")
DEFAULT_REPORT = Path("outputs/reports/A3_R1_FORWARD_RESEARCH_DEMO_V1_ATTACH.json")
FILL_COLLECTION_EXPERT = "Phase2ExperimentalDemoExecutor"


def attach_r1_forward_research_demo(
    root: Path,
    *,
    packet_path: Path | None = None,
    report_path: Path | None = None,
    apply: bool = False,
    wait_seconds: int = 90,
) -> Path:
    root = root.resolve()
    packet_path = (packet_path or root / DEFAULT_PACKET).resolve()
    report_path = (report_path or root / DEFAULT_REPORT).resolve()
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    account = packet["account"]
    expert = packet["expert"]
    inputs = packet["inputs"]
    terminal_exe = Path(account["terminal_exe"])
    data_path = Path(account["data_path"])
    metaeditor_exe = terminal_exe.with_name("MetaEditor64.exe")
    profile_dir = data_path / "MQL5" / "Profiles" / "Charts" / "Default"
    source = (root / expert["source"]).resolve()

    state_before = _account_state(terminal_exe, expert["symbol"], int(expert["magic"]))
    inventory_before = _chart_inventory(profile_dir)
    checks = _preflight_checks(
        packet,
        packet_path,
        source,
        terminal_exe,
        metaeditor_exe,
        data_path,
        profile_dir,
        state_before,
        inventory_before,
    )
    if not apply or any(not item["passed"] for item in checks):
        status = "NOOP_READY_FOR_APPLY" if all(item["passed"] for item in checks) else "ATTACH_BLOCKED"
        payload = _payload(status, apply, checks, state_before, None, inventory_before, inventory_before)
        _write_report(report_path, payload)
        return report_path

    _close_terminal(terminal_exe)
    backup_dir = _backup_profile(profile_dir, data_path)
    paused_chart = _pause_fill_collection(profile_dir)
    deployed = _deploy(root, data_path, source, Path(packet["artifacts"]["preset"]))
    compile_log = _compile(metaeditor_exe, data_path, source.name)
    chart_path, chart_action = _upsert_target_chart(profile_dir, expert["name"], inputs)
    _launch_terminal(terminal_exe)
    runtime = _wait_for_runtime(
        data_path / "MQL5" / "Files" / inputs["InpStartupLogFileName"],
        inputs["InpRunId"],
        wait_seconds,
    )
    state_after = _account_state(terminal_exe, expert["symbol"], int(expert["magic"]))
    inventory_after = _chart_inventory(profile_dir)
    runtime_checks = _runtime_checks(packet, state_after, inventory_after, compile_log, runtime, chart_path)
    checks.extend(runtime_checks)
    status = "ATTACHED_RUNTIME_CONFIRMED" if all(item["passed"] for item in checks) else "ATTACHED_PENDING_OR_FAILED"
    payload = _payload(status, apply, checks, state_before, state_after, inventory_before, inventory_after)
    payload["deployment"] = {
        "backup_dir": str(backup_dir),
        "paused_fill_collection_chart": str(paused_chart),
        "deployed_files": deployed,
        "compile_log": str(compile_log),
        "target_chart": str(chart_path),
        "chart_action": chart_action,
        "runtime": runtime,
    }
    _write_report(report_path, payload)
    return report_path


def _preflight_checks(
    packet: dict[str, Any],
    packet_path: Path,
    source: Path,
    terminal_exe: Path,
    metaeditor_exe: Path,
    data_path: Path,
    profile_dir: Path,
    state: dict[str, Any],
    inventory: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    account = packet["account"]
    expert = packet["expert"]
    inputs = packet["inputs"]
    fill = [item for item in inventory if item["expert"] == FILL_COLLECTION_EXPERT]
    target = [
        item
        for item in inventory
        if item["expert"] == expert["name"]
        and (item["inputs"].get("InpRunId") == inputs["InpRunId"] or item["inputs"].get("InpMagicNumber") == inputs["InpMagicNumber"])
    ]
    allowed_armed_charts = {item["chart"] for item in fill + target}
    unexpected_armed = [item["chart"] for item in inventory if item["armed"] and item["chart"] not in allowed_armed_charts]
    kill_switch = data_path / "MQL5" / "Files" / inputs["InpKillSwitchFileName"]
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest() if source.exists() else ""
    return [
        _check("packet_ready", packet.get("status") == "READY_FOR_A3_ISOLATED_DEMO_ATTACH", packet.get("status", "")),
        _check("packet_exists", packet_path.exists(), str(packet_path)),
        _check("terminal_exists", terminal_exe.exists(), str(terminal_exe)),
        _check("metaeditor_exists", metaeditor_exe.exists(), str(metaeditor_exe)),
        _check("data_path_exists", data_path.exists(), str(data_path)),
        _check("profile_exists", profile_dir.exists(), str(profile_dir)),
        _check("source_hash_matches_packet", source_hash == packet["artifacts"]["source_sha256"], source_hash),
        _check("login_exact", str(state.get("login")) == account["login"], str(state.get("login"))),
        _check("server_exact", state.get("server") == account["server"], str(state.get("server"))),
        _check("trade_mode_demo", state.get("trade_mode") == 0, str(state.get("trade_mode"))),
        _check("account_currency_aed", state.get("currency") == "AED", str(state.get("currency"))),
        _check("terminal_connected", state.get("connected") is True, str(state.get("connected"))),
        _check("terminal_trade_allowed", state.get("trade_allowed") is True and state.get("terminal_trade_allowed") is True, json.dumps(state, sort_keys=True)),
        _check("zero_xauusd_positions", state.get("symbol_positions") == 0, str(state.get("symbol_positions"))),
        _check("zero_xauusd_orders", state.get("symbol_orders") == 0, str(state.get("symbol_orders"))),
        _check("target_magic_has_no_exposure", state.get("magic_positions") == 0 and state.get("magic_orders") == 0, json.dumps(state, sort_keys=True)),
        _check("kill_switch_absent", not kill_switch.exists(), str(kill_switch)),
        _check("single_fill_collection_chart", len(fill) == 1, ",".join(item["chart"] for item in fill)),
        _check("at_most_one_target_chart", len(target) <= 1, ",".join(item["chart"] for item in target)),
        _check("no_unexpected_armed_chart", not unexpected_armed, ",".join(unexpected_armed) or "none"),
        _check("risk_limit_is_30_aed", inputs.get("InpRiskAmountUsd") == "30.00" and inputs.get("InpMaxRiskOvershootPct") == "0.00", f"risk={inputs.get('InpRiskAmountUsd')}; overshoot={inputs.get('InpMaxRiskOvershootPct')}"),
        _check("one_entry_one_position", inputs.get("InpPortfolioMaxTradesPerDay") == "1" and inputs.get("InpOnePositionPerMagic") == "true", f"daily={inputs.get('InpPortfolioMaxTradesPerDay')}; one_position={inputs.get('InpOnePositionPerMagic')}"),
    ]


def _runtime_checks(
    packet: dict[str, Any],
    state: dict[str, Any],
    inventory: list[dict[str, Any]],
    compile_log: Path,
    runtime: dict[str, Any],
    chart_path: Path,
) -> list[dict[str, Any]]:
    account = packet["account"]
    expert = packet["expert"]
    inputs = packet["inputs"]
    fill = [item for item in inventory if item["expert"] == FILL_COLLECTION_EXPERT]
    target = [item for item in inventory if item["chart"] == chart_path.name]
    armed = [item for item in inventory if item["armed"]]
    target_values = target[0]["inputs"] if len(target) == 1 else {}
    return [
        _check("compile_zero_errors_zero_warnings", _compile_passed(compile_log), str(compile_log)),
        _check("runtime_init_ok", runtime.get("confirmed") is True, json.dumps(runtime, sort_keys=True)),
        _check("post_login_exact", str(state.get("login")) == account["login"], str(state.get("login"))),
        _check("post_server_demo_exact", state.get("server") == account["server"] and state.get("trade_mode") == 0, json.dumps(state, sort_keys=True)),
        _check("post_currency_aed", state.get("currency") == "AED", str(state.get("currency"))),
        _check("fill_collection_paused", len(fill) == 1 and not fill[0]["armed"], json.dumps(fill, sort_keys=True)),
        _check("exactly_one_armed_chart", len(armed) == 1 and armed[0]["chart"] == chart_path.name, json.dumps([item["chart"] for item in armed])),
        _check("target_chart_exact_identity", len(target) == 1 and target[0]["expert"] == expert["name"] and target_values.get("InpMagicNumber") == str(expert["magic"]), json.dumps(target, sort_keys=True)),
        _check("target_chart_exact_signal", target_values.get("InpSignalMode") == "7" and target_values.get("InpDirectionMode") == "1" and target_values.get("InpRegimeRouterMode") == "1", _input_detail(target_values, "InpSignalMode", "InpDirectionMode", "InpRegimeRouterMode")),
        _check("target_chart_exact_risk", target_values.get("InpRiskAmountUsd") == "30.00" and target_values.get("InpMaxRiskLots") == "0.01" and target_values.get("InpRejectRiskOvershootEnabled") == "true" and target_values.get("InpMaxRiskOvershootPct") == "0.00", _input_detail(target_values, "InpRiskAmountUsd", "InpMaxRiskLots", "InpRejectRiskOvershootEnabled", "InpMaxRiskOvershootPct")),
        _check("post_target_magic_no_exposure", state.get("magic_positions") == 0 and state.get("magic_orders") == 0, json.dumps(state, sort_keys=True)),
    ]


def _account_state(terminal_exe: Path, symbol: str, magic: int) -> dict[str, Any]:
    import MetaTrader5 as mt5

    if not mt5.initialize(path=str(terminal_exe)):
        raise RuntimeError(f"MT5 initialize failed for {terminal_exe}: {mt5.last_error()}")
    try:
        account = mt5.account_info()
        terminal = mt5.terminal_info()
        positions = list(mt5.positions_get() or [])
        orders = list(mt5.orders_get() or [])
        return {
            "login": getattr(account, "login", None),
            "server": getattr(account, "server", None),
            "trade_mode": getattr(account, "trade_mode", None),
            "currency": getattr(account, "currency", None),
            "balance": getattr(account, "balance", None),
            "equity": getattr(account, "equity", None),
            "trade_allowed": bool(getattr(account, "trade_allowed", False)),
            "connected": bool(getattr(terminal, "connected", False)),
            "terminal_trade_allowed": bool(getattr(terminal, "trade_allowed", False)),
            "symbol_positions": sum(getattr(item, "symbol", "") == symbol for item in positions),
            "symbol_orders": sum(getattr(item, "symbol", "") == symbol for item in orders),
            "magic_positions": sum(int(getattr(item, "magic", 0)) == magic for item in positions),
            "magic_orders": sum(int(getattr(item, "magic", 0)) == magic for item in orders),
        }
    finally:
        mt5.shutdown()


def _chart_inventory(profile_dir: Path) -> list[dict[str, Any]]:
    inventory = []
    for chart in sorted(profile_dir.glob("chart*.chr")):
        expert, inputs = _parse_expert(_read_text(chart))
        inventory.append({"chart": chart.name, "expert": expert, "inputs": inputs, "armed": _is_armed(inputs)})
    return inventory


def _parse_expert(text: str) -> tuple[str, dict[str, str]]:
    match = re.search(r"<expert>\s*(.*?)\s*</expert>", text, flags=re.DOTALL)
    if not match:
        return "", {}
    expert = ""
    inputs: dict[str, str] = {}
    in_inputs = False
    for raw in match.group(1).replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if line == "<inputs>":
            in_inputs = True
            continue
        if line == "</inputs>":
            in_inputs = False
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key == "name" and not in_inputs:
            expert = value
        elif in_inputs:
            inputs[key] = value
    return expert, inputs


def _is_armed(inputs: dict[str, str]) -> bool:
    allow_demo = inputs.get("InpAllowDemoTrading", "false").lower() == "true"
    broker_pair = (
        inputs.get("InpDryRunOnly", "true").lower() == "false"
        and inputs.get("InpBrokerActionAllowed", "false").lower() == "true"
    )
    return allow_demo or broker_pair


def _pause_fill_collection(profile_dir: Path) -> Path:
    matches = []
    for chart in profile_dir.glob("chart*.chr"):
        expert, _ = _parse_expert(_read_text(chart))
        if expert == FILL_COLLECTION_EXPERT:
            matches.append(chart)
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {FILL_COLLECTION_EXPERT} chart, found {matches}")
    chart = matches[0]
    text = _read_text(chart)
    text = _replace_expert_input(text, "InpDryRunOnly", "true")
    text = _replace_expert_input(text, "InpBrokerActionAllowed", "false")
    text = _replace_expert_input(text, "InpRunId", "A3_DEMO_FILL_COLLECTION_A3_V1_PAUSED_20260717")
    _write_chart(chart, text)
    return chart


def _replace_expert_input(text: str, key: str, value: str) -> str:
    match = re.search(r"<expert>\s*(.*?)\s*</expert>", text, flags=re.DOTALL)
    if not match:
        raise RuntimeError("Chart has no expert block")
    block = match.group(0)
    replaced, count = re.subn(rf"(?m)^{re.escape(key)}=.*$", f"{key}={value}", block, count=1)
    if count != 1:
        raise RuntimeError(f"Expected one {key} input in expert block")
    return text[: match.start()] + replaced + text[match.end() :]


def _deploy(root: Path, data_path: Path, source: Path, preset: Path) -> list[str]:
    del root
    expert_dir = data_path / "MQL5" / "Experts"
    preset_dir = data_path / "MQL5" / "Presets"
    expert_dir.mkdir(parents=True, exist_ok=True)
    preset_dir.mkdir(parents=True, exist_ok=True)
    target_source = expert_dir / source.name
    target_preset = preset_dir / "A3_R1_FORWARD_RESEARCH_DEMO_V1.local.set"
    shutil.copy2(source, target_source)
    shutil.copy2(preset, target_preset)
    return [str(target_source), str(target_preset)]


def _compile(metaeditor_exe: Path, data_path: Path, source_name: str) -> Path:
    source = data_path / "MQL5" / "Experts" / source_name
    ex5 = source.with_suffix(".ex5")
    log = data_path / "MQL5" / "Logs" / "compile_A3_R1_FORWARD_RESEARCH_DEMO_V1.log"
    ex5.unlink(missing_ok=True)
    log.unlink(missing_ok=True)
    result = subprocess.run(
        [str(metaeditor_exe), "/portable", f"/compile:{source}", f"/log:{log}"],
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    if result.returncode not in (0, 1) or not ex5.exists() or not _compile_passed(log):
        raise RuntimeError(
            f"MetaEditor compile failed ({result.returncode}). stdout={result.stdout!r} stderr={result.stderr!r} log={_read_text(log)!r}"
        )
    return log


def _compile_passed(log: Path) -> bool:
    text = _read_text(log).lower()
    return bool(re.search(r"0\s+errors?[,\s]+0\s+warnings?", text))


def _upsert_target_chart(profile_dir: Path, expert_name: str, inputs: dict[str, str]) -> tuple[Path, str]:
    matches = []
    for chart in profile_dir.glob("chart*.chr"):
        expert, values = _parse_expert(_read_text(chart))
        if expert == expert_name and (
            values.get("InpRunId") == inputs["InpRunId"] or values.get("InpMagicNumber") == inputs["InpMagicNumber"]
        ):
            matches.append(chart)
    if len(matches) > 1:
        raise RuntimeError(f"Multiple target R1 charts found: {matches}")
    if matches:
        chart = matches[0]
        action = "updated_existing_r1_chart"
    else:
        chart = profile_dir / f"chart{_next_chart_index(profile_dir):02d}.chr"
        action = "appended_new_r1_chart"
    _write_chart(chart, _render_chart(chart, expert_name, inputs))
    _prepend_order(profile_dir, chart.name)
    return chart, action


def _render_chart(chart: Path, expert_name: str, inputs: dict[str, str]) -> str:
    index = int(re.search(r"(\d+)", chart.stem).group(1))
    input_lines = [f"{key}={value}" for key, value in inputs.items()]
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
            "askline=1",
            "days=0",
            "windows_total=1",
            "",
            "<expert>",
            f"name={expert_name}",
            f"path=Experts\\{expert_name}.ex5",
            "expertmode=1",
            "<inputs>",
            *input_lines,
            "</inputs>",
            "</expert>",
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


def _next_chart_index(profile_dir: Path) -> int:
    indexes = [int(match.group(1)) for path in profile_dir.glob("chart*.chr") if (match := re.fullmatch(r"chart(\d+)\.chr", path.name))]
    return max(indexes, default=0) + 1


def _prepend_order(profile_dir: Path, chart_name: str) -> None:
    order = profile_dir / "order.wnd"
    names = [line.strip() for line in _read_text(order).splitlines() if line.strip() and line.strip() != chart_name]
    order.write_text("\r\n".join([chart_name, *names]) + "\r\n", encoding="ascii", newline="")


def _close_terminal(terminal_exe: Path) -> None:
    command = f"""
$target = (Resolve-Path -LiteralPath '{terminal_exe}').Path
$procs = Get-CimInstance Win32_Process | Where-Object {{ $_.ExecutablePath -eq $target }}
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
    result = subprocess.run(["powershell", "-NoProfile", "-Command", command], text=True, capture_output=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"Could not close A3 terminal: {result.stderr}")


def _backup_profile(profile_dir: Path, data_path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = data_path / "_codex_quarantine" / "profile_backups" / f"a3_r1_forward_research_before_attach_{stamp}"
    shutil.copytree(profile_dir, backup)
    return backup


def _launch_terminal(terminal_exe: Path) -> None:
    subprocess.Popen([str(terminal_exe), "/portable"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _wait_for_runtime(path: Path, run_id: str, wait_seconds: int) -> dict[str, Any]:
    deadline = time.time() + wait_seconds
    matched = ""
    while time.time() < deadline:
        lines = _read_text(path).splitlines()
        candidates = [line for line in lines if run_id in line]
        if candidates:
            matched = candidates[-1]
            if "INIT_OK" in matched:
                return {"confirmed": True, "startup_log": str(path), "matched_row": matched}
            if "INIT_FAILED" in matched:
                return {"confirmed": False, "startup_log": str(path), "matched_row": matched}
        time.sleep(2)
    return {"confirmed": False, "startup_log": str(path), "matched_row": matched, "reason": "timeout"}


def _payload(
    status: str,
    apply: bool,
    checks: list[dict[str, Any]],
    state_before: dict[str, Any],
    state_after: dict[str, Any] | None,
    inventory_before: list[dict[str, Any]],
    inventory_after: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "apply": apply,
        "scope": "A3 account 1033669 only; isolated R1 prospective demo research; never live or real.",
        "checks": checks,
        "state_before": state_before,
        "state_after": state_after,
        "inventory_before": inventory_before,
        "inventory_after": inventory_after,
    }


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    passed = sum(item["passed"] for item in payload["checks"])
    failed = len(payload["checks"]) - passed
    path.with_suffix(".md").write_text(
        "\n".join(
            [
                "# A3 R1 Forward-Research Demo V1 Attach",
                "",
                f"Status: `{payload['status']}`",
                "",
                f"Checks passed: {passed}; failed: {failed}.",
                "",
                "This is isolated prospective demo research. It is not live authorization, ML execution, strategy promotion, or a profit guarantee.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8", "utf-16", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeError:
            continue
    return path.read_text(errors="replace")


def _write_chart(path: Path, text: str) -> None:
    path.write_text(text.replace("\r\n", "\n").replace("\n", "\r\n"), encoding="utf-8", newline="")


def _input_detail(inputs: dict[str, str], *keys: str) -> str:
    return "; ".join(f"{key}={inputs.get(key, '')}" for key in keys)


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed), "detail": detail}


def _default_root() -> Path:
    cwd = Path.cwd()
    if (cwd / DEFAULT_PACKET).exists():
        return cwd
    phase1 = cwd / "xau-usd" / "xauusd-phase1"
    return phase1 if phase1.exists() else cwd


def main() -> int:
    parser = argparse.ArgumentParser(description="Attach the isolated A3 R1 prospective demo research lane.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--wait-seconds", type=int, default=90)
    args = parser.parse_args()
    report = attach_r1_forward_research_demo(
        args.root,
        packet_path=args.packet,
        report_path=args.report,
        apply=args.apply,
        wait_seconds=args.wait_seconds,
    )
    payload = json.loads(report.read_text(encoding="utf-8"))
    print(f"A3 R1 attach status: {payload['status']} ({report})")
    return 0 if payload["status"] in {"NOOP_READY_FOR_APPLY", "ATTACHED_RUNTIME_CONFIRMED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
