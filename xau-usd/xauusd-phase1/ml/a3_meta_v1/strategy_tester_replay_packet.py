from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .market_data_export import _table, _utc_now, _write_json_atomic, parse_utc


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_STRATEGY_TESTER_REPLAY_PACKET_STATUS.json"
DEFAULT_PACKET_DIR = Path("outputs") / "reports" / "strategy_tester_replay"
SCHEMA_VERSION = "a3_ml_strategy_tester_replay_packet_status_v1"
STATUS_READY = "STRATEGY_TESTER_REPLAY_PACKET_READY"
STATUS_BLOCKED = "STRATEGY_TESTER_REPLAY_PACKET_BLOCKED_MISSING_SAFE_EVIDENCE"
DEFAULT_DEMO_SERVER = "Capital.ComMena-Demo"


LANE_DEFINITIONS = (
    {
        "account_label": "A1",
        "expert_name": "Phase2ExperimentalDemoExecutor",
        "deployed_preset_name": "Phase2ExperimentalDemoExecutor.A1.a3_ml_shadow_readonly.set",
        "repo_preset_name": "Phase2ExperimentalDemoExecutor.tier1_breakout_retest_demo_xauusd.template.set",
        "timeframe": "M5",
        "replay_intent": "standard experimental demo dry-run shadow replay",
    },
    {
        "account_label": "A2",
        "expert_name": "Phase2ExperimentalDemoExecutor",
        "deployed_preset_name": "Phase2ExperimentalDemoExecutor.A2.a3_ml_shadow_readonly.set",
        "repo_preset_name": "Phase2ExperimentalDemoExecutor.tier1_breakout_retest_demo_xauusd.template.set",
        "timeframe": "M5",
        "replay_intent": "tier1 breakout dry-run shadow replay",
    },
    {
        "account_label": "A3",
        "expert_name": "Account3BreakoutPlainExecutor",
        "deployed_preset_name": "Account3BreakoutPlainExecutor.A3.a3_ml_shadow_readonly.set",
        "repo_preset_name": "Account3BreakoutPlainExecutor.safe_xauusd.set",
        "timeframe": "M5",
        "replay_intent": "repair-lane plain breakout dry-run shadow replay",
    },
    {
        "account_label": "A3",
        "expert_name": "Account3BreakoutImprovedExecutor",
        "deployed_preset_name": "Account3BreakoutImprovedExecutor.A3.a3_ml_shadow_readonly.set",
        "repo_preset_name": "Account3BreakoutImprovedExecutor.safe_xauusd.set",
        "timeframe": "M5",
        "replay_intent": "repair-lane improved breakout dry-run shadow replay",
    },
    {
        "account_label": "A3",
        "expert_name": "Account3BreakoutTier1CompatExecutor",
        "deployed_preset_name": "Account3BreakoutTier1CompatExecutor.A3.a3_ml_shadow_readonly.set",
        "repo_preset_name": "Account3BreakoutTier1CompatExecutor.safe_xauusd.set",
        "timeframe": "M5",
        "replay_intent": "repair-lane tier1-compatible dry-run shadow replay",
    },
    {
        "account_label": "A3",
        "expert_name": "Account3SoftRetestExecutor",
        "deployed_preset_name": "Account3SoftRetestExecutor.A3.a3_ml_shadow_readonly.set",
        "repo_preset_name": "Account3SoftRetestExecutor.safe_xauusd.set",
        "timeframe": "M5",
        "replay_intent": "repair-lane soft-retest dry-run shadow replay",
    },
)


def generate_strategy_tester_replay_packet(
    root: Path,
    report_json: Path | None = None,
    *,
    registry_path: Path | None = None,
    packet_dir: Path | None = None,
) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    packet_dir = (packet_dir or root / DEFAULT_PACKET_DIR).resolve()
    registry = load_mt5_account_registry((registry_path or root / "config" / "ml" / "mt5_accounts.yaml").resolve())
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    c50 = _read_json(reports / "A3_ML_HISTORICAL_BACKFILL_REPLAY_PLAN_STATUS.json")
    dataset_version = str(pointer.get("dataset_version") or c50.get("dataset_version") or "UNKNOWN_DATASET")
    window = _window(pointer, c50)
    dataset_packet_dir = packet_dir / _safe_name(dataset_version)
    lanes = _lanes(root, registry.by_label(), dataset_packet_dir, window)
    ready = bool(lanes) and all(bool(lane.get("config_ready")) for lane in lanes)
    status = STATUS_READY if ready else STATUS_BLOCKED
    payload = {
        "status": status,
        "stage": "C51-STRATEGY-TESTER-REPLAY-PACKET",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": dataset_version,
        "window": window,
        "lane_count": len(lanes),
        "ready_lane_count": sum(1 for lane in lanes if lane.get("config_ready")),
        "lanes": lanes,
        "commands": _commands(root, report_json, lanes),
        "evidence_rules": _evidence_rules(),
        "operator_sequence": _operator_sequence(),
        "authorization": {
            "strategy_tester_launch_authorized": False,
            "historical_export_authorized_by_this_packet": False,
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "strategy_tester_launch_attempted": False,
            "terminal_runtime_change_authorized": False,
            "terminal_data_root_write_attempted": False,
            "profile_or_chart_file_write_attempted": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
            "packet_dir": str(dataset_packet_dir),
            "config_dir": str(dataset_packet_dir / "configs"),
            "tester_report_dir": str(dataset_packet_dir / "tester_reports"),
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(reports / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_strategy_tester_replay_packet_md(payload: dict[str, Any]) -> str:
    lane_rows = [
        {
            "Account": lane.get("account_label", ""),
            "Expert": lane.get("expert_name", ""),
            "Preset": Path(str(lane.get("preset_path", ""))).name,
            "Ready": str(lane.get("config_ready", False)).lower(),
            "Config": lane.get("config_path", ""),
        }
        for lane in payload.get("lanes", [])
    ]
    guard_rows = [
        {
            "Account": lane.get("account_label", ""),
            "Expert": lane.get("expert_name", ""),
            "Check": check.get("check", ""),
            "Pass": str(check.get("passed", False)).lower(),
            "Detail": check.get("detail", ""),
        }
        for lane in payload.get("lanes", [])
        for check in lane.get("preset_guard_checks", [])
    ]
    command_lines = "\n".join(f"- {key}: `{value}`" for key, value in payload.get("commands", {}).items())
    rules = [
        {
            "Evidence": item.get("evidence", ""),
            "Use": item.get("allowed_use", ""),
            "Cannot Do": item.get("cannot_do", ""),
        }
        for item in payload.get("evidence_rules", [])
    ]
    sequence = "\n".join(f"{index}. {item}" for index, item in enumerate(payload.get("operator_sequence", []), start=1))
    window = payload.get("window", {})
    return "\n".join(
        [
            "# A3 ML Strategy Tester Replay Packet",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            f"Ready lanes: {payload.get('ready_lane_count', 0)} / {payload.get('lane_count', 0)}",
            "",
            "## Window",
            "",
            f"- Historical start UTC: {window.get('historical_start_utc', '')}.",
            f"- Snapshot cutoff UTC: {window.get('snapshot_cutoff_utc', '')}.",
            f"- Symbol: {window.get('symbol', '')}.",
            "",
            "## Replay Lanes",
            "",
            _table(lane_rows, ["Account", "Expert", "Preset", "Ready", "Config"]),
            "",
            "## Guard Checks",
            "",
            _table(guard_rows, ["Account", "Expert", "Check", "Pass", "Detail"]),
            "",
            "## Evidence Rules",
            "",
            _table(rules, ["Evidence", "Use", "Cannot Do"]),
            "",
            "## Commands",
            "",
            command_lines,
            "",
            "## Operator Sequence",
            "",
            sequence,
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Strategy Tester launch attempted: false.",
            "- Terminal runtime change authorized: false.",
            "- Terminal data-root write attempted: false.",
            "- Profile or chart file write attempted: false.",
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


def _lanes(
    root: Path,
    accounts_by_label: dict[str, MT5AccountSpec],
    dataset_packet_dir: Path,
    window: dict[str, str],
) -> list[dict[str, Any]]:
    lanes: list[dict[str, Any]] = []
    for definition in LANE_DEFINITIONS:
        account = accounts_by_label[str(definition["account_label"])]
        expert_name = str(definition["expert_name"])
        data_path = Path(str(account.expected_data_path or ""))
        expert_path = data_path / "MQL5" / "Experts" / f"{expert_name}.ex5"
        preset_path, preset_source = _preset_path(root, account, definition)
        preset_values = _read_preset_values(preset_path)
        guard_checks = _preset_guard_checks(preset_path, preset_values, account)
        config_ready = expert_path.exists() and preset_path.exists() and all(check["passed"] for check in guard_checks)
        lane_name = _safe_name(f"{account.account_label}_{expert_name}_{account.symbol}_{definition['timeframe']}")
        config_path = dataset_packet_dir / "configs" / f"{lane_name}.ini"
        tester_report_path = dataset_packet_dir / "tester_reports" / f"{lane_name}.html"
        if config_ready:
            _write_tester_config(
                config_path,
                account=account,
                expert_name=expert_name,
                preset_path=preset_path,
                report_path=tester_report_path,
                window=window,
                timeframe=str(definition["timeframe"]),
            )
        lanes.append(
            {
                "account_label": account.account_label,
                "account_scope": account.account_scope,
                "role": account.role,
                "terminal_exe": account.terminal_exe,
                "terminal_data_path": account.expected_data_path or "",
                "portable": account.portable,
                "symbol": account.symbol,
                "timeframe": definition["timeframe"],
                "expert_name": expert_name,
                "expert_deployed_path": str(expert_path),
                "expert_deployed_exists": expert_path.exists(),
                "preset_path": str(preset_path),
                "preset_source": preset_source,
                "preset_exists": preset_path.exists(),
                "preset_guard_checks": guard_checks,
                "replay_intent": definition["replay_intent"],
                "config_ready": config_ready,
                "config_path": str(config_path) if config_ready else "",
                "tester_report_path": str(tester_report_path) if config_ready else "",
            }
        )
    return lanes


def _preset_path(root: Path, account: MT5AccountSpec, definition: dict[str, str]) -> tuple[Path, str]:
    deployed = Path(account.expected_data_path or "") / "MQL5" / "Presets" / str(definition["deployed_preset_name"])
    if deployed.exists():
        return deployed, "terminal_deployed_shadow_readonly"
    return root / "mt5" / "Presets" / str(definition["repo_preset_name"]), "repository_fallback"


def _preset_guard_checks(path: Path, values: dict[str, str], account: MT5AccountSpec) -> list[dict[str, Any]]:
    return [
        _check("preset_exists", path.exists(), str(path)),
        _check("dry_run_only_true", _bool_text(values.get("InpDryRunOnly")) is True, f"InpDryRunOnly={values.get('InpDryRunOnly', '')}"),
        _check(
            "broker_action_allowed_false",
            _bool_text(values.get("InpBrokerActionAllowed")) is False,
            f"InpBrokerActionAllowed={values.get('InpBrokerActionAllowed', '')}",
        ),
        _check("target_symbol_xauusd", values.get("InpTargetSymbol") == account.symbol, f"InpTargetSymbol={values.get('InpTargetSymbol', '')}"),
        _check(
            "account_allowlist_matches_scope",
            _account_allowlist_matches(values.get("InpAllowedAccountLoginsCsv", ""), account.account_scope),
            f"InpAllowedAccountLoginsCsv={values.get('InpAllowedAccountLoginsCsv', '')}",
        ),
        _check(
            "authorization_tokens_blank",
            _tokens_blank(values),
            "experimental/cost authorization token inputs are blank or absent",
        ),
    ]


def _write_tester_config(
    path: Path,
    *,
    account: MT5AccountSpec,
    expert_name: str,
    preset_path: Path,
    report_path: Path,
    window: dict[str, str],
    timeframe: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    from_date = _tester_date(window.get("historical_start_utc", ""))
    to_date = _tester_date(window.get("snapshot_cutoff_utc", ""))
    lines = [
        "; Generated by C51. Review-only candidate. Do not launch against active live-collection roots.",
        f"; AccountLabel={account.account_label}",
        f"; TerminalExe={account.terminal_exe}",
        f"; TerminalDataPath={account.expected_data_path or ''}",
        f"; PresetSourcePath={preset_path}",
        "[Common]",
        f"Login={account.account_scope}",
        f"Server={DEFAULT_DEMO_SERVER}",
        "ProxyEnable=0",
        "NewsEnable=0",
        "",
        "[Tester]",
        f"Expert={expert_name}",
        f"ExpertParameters={preset_path.name}",
        f"Symbol={account.symbol}",
        f"Period={timeframe}",
        f"Login={account.account_scope}",
        "Model=0",
        "ExecutionMode=0",
        "Optimization=0",
        f"FromDate={from_date}",
        f"ToDate={to_date}",
        "ForwardMode=0",
        "Deposit=10000",
        "Currency=USD",
        "Leverage=1:100",
        f"Report={report_path}",
        "ReplaceReport=1",
        "ShutdownTerminal=1",
        "Visual=0",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _window(pointer: dict[str, Any], c50: dict[str, Any]) -> dict[str, str]:
    c50_window = c50.get("window", {}) if isinstance(c50.get("window"), dict) else {}
    cutoff = str(pointer.get("snapshot_cutoff_utc") or c50_window.get("snapshot_cutoff_utc") or "")
    start = str(c50_window.get("historical_start_utc") or "")
    if not cutoff:
        cutoff = datetime.now(timezone.utc).replace(second=0, microsecond=0).isoformat().replace("+00:00", "Z")
    if not start:
        start = cutoff
    return {
        "historical_start_utc": _iso(parse_utc(start)),
        "snapshot_cutoff_utc": _iso(parse_utc(cutoff)),
        "symbol": "XAUUSD",
    }


def _commands(root: Path, report_json: Path, lanes: list[dict[str, Any]]) -> dict[str, str]:
    python = _quote(sys.executable)
    script = _quote(str(root / "scripts" / "c51_generate_strategy_tester_replay_packet.py"))
    root_arg = _quote(str(root))
    ready_configs = [lane.get("config_path", "") for lane in lanes if lane.get("config_ready")]
    first_config = str(ready_configs[0]) if ready_configs else "<config.ini>"
    return {
        "regenerate_packet": f"{python} {script} --root {root_arg} --report-json {_quote(str(report_json))}",
        "future_manual_launch_template": f"<isolated-terminal64.exe> /portable /config:{_quote(first_config)}",
        "reviewer_question": "Ask reviewer whether dry-run Strategy Tester replay logs can be admitted as label/setup evidence and which gates they may satisfy.",
    }


def _evidence_rules() -> list[dict[str, str]]:
    return [
        {
            "evidence": "Dry-run Strategy Tester signal/order logs",
            "allowed_use": "Reviewer-gated research evidence for setup frequency, direction behavior, and label-candidate expansion.",
            "cannot_do": "Cannot count as live fills, live slippage, official training labels, or Python demo readiness without reviewer approval.",
        },
        {
            "evidence": "Strategy Tester virtual deals",
            "allowed_use": "Only a future reviewer-approved tester-only simulation contract may admit them.",
            "cannot_do": "This packet does not enable virtual order sending because every preset remains dry-run and broker-action false.",
        },
        {
            "evidence": "Live A1/A2/A3 collection",
            "allowed_use": "Remains the authoritative evidence for fill/slippage deficits and demo shadow freshness.",
            "cannot_do": "Does not get interrupted or replaced by this C51 packet.",
        },
    ]


def _operator_sequence() -> list[str]:
    return [
        "Keep A1/A2/A3 live collection running in the background.",
        "Review the generated C51 configs and guard checks before any tester launch.",
        "Use an isolated tester terminal copy for replay; do not launch Strategy Tester against active live-collection data roots.",
        "Copy the compiled EA and exact safe preset into the isolated tester root before launching.",
        "Run one config at a time, collect tester reports and MQL5 file/log outputs, then hash the outputs.",
        "Ask the reviewer whether replay evidence can be admitted before rebuilding labels or training anything from replay output.",
    ]


def _next_allowed_stage(status: str) -> str:
    if status == STATUS_READY:
        return (
            "C51 replay configs are ready for reviewer/operator inspection. "
            "A separate explicit launch step must use an isolated tester root and cannot authorize training, EA consumption, or broker action."
        )
    return (
        "Fix missing compiled EAs or unsafe/missing presets, then regenerate C51. "
        "Do not launch Strategy Tester until every lane is ready or deliberately excluded."
    )


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_strategy_tester_replay_packet_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c51_strategy_tester_replay_packet_report"] = payload["outputs"]["status_report_json"]
    pointer["c51_strategy_tester_replay_packet_status"] = payload["status"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _read_preset_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed), "detail": detail}


def _bool_text(value: str | None) -> bool | None:
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return None


def _account_allowlist_matches(value: str, expected_scope: str) -> bool:
    return expected_scope in {item.strip() for item in value.split(",") if item.strip()}


def _tokens_blank(values: dict[str, str]) -> bool:
    token_keys = [key for key in values if "Token" in key and not key.startswith("InpRequired")]
    return all(not values.get(key, "").strip() for key in token_keys)


def _tester_date(value: str) -> str:
    return parse_utc(value).strftime("%Y.%m.%d")


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "unnamed"


def _quote(value: str) -> str:
    return f'"{value}"' if " " in value else value


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
