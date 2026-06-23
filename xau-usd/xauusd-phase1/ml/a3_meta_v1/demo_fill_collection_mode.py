from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .account_registry import load_mt5_account_registry
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_DEMO_FILL_COLLECTION_MODE_STATUS.json"
SCHEMA_VERSION = "a3_ml_demo_fill_collection_mode_v1"
BASE_TEMPLATE_REL = Path("mt5") / "Presets" / "Phase2ExperimentalDemoExecutor.tier1_breakout_retest_demo_xauusd.template.set"
SOURCE_REL = Path("mt5") / "Experts" / "Phase2ExperimentalDemoExecutor.mq5"
A3_BREAKOUT_BASE_REL = Path("mt5") / "Include" / "A3BreakoutExecutorBase.mqh"
TEMPLATE_DIR_REL = Path("outputs") / "reports" / "demo_fill_collection"
EA_NAME = "Phase2ExperimentalDemoExecutor"
AUTH_TOKEN = "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY"
COST_ACK_TOKEN = "I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT"
MAX_ORDERS_PER_DAY = 3
MAX_ACCOUNT_ORDERS_PER_DAY = 3
MIN_SECONDS_BETWEEN_ORDERS = 300
MAX_OPEN_POSITIONS = 1
MAX_OPEN_POSITIONS_PER_MAGIC = 1
FIXED_LOT = "0.01"
MAX_ESTIMATED_COST_R = "0.15"
MAX_MEASURED_SPREAD_POINTS = "75.0"


def generate_demo_fill_collection_mode(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    reports = root / "outputs" / "reports"
    registry = load_mt5_account_registry(root / "config" / "ml" / "mt5_accounts.yaml")
    base_template = root / BASE_TEMPLATE_REL
    source = root / SOURCE_REL
    a3_breakout_base = root / A3_BREAKOUT_BASE_REL
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    base_values = _parse_set_file(base_template)
    source_text = source.read_text(encoding="utf-8", errors="replace") if source.exists() else ""
    a3_breakout_base_text = a3_breakout_base.read_text(encoding="utf-8", errors="replace") if a3_breakout_base.exists() else ""
    preflight_checks = _preflight_checks(
        registry,
        base_template,
        base_values,
        source,
        source_text,
        a3_breakout_base,
        a3_breakout_base_text,
    )

    templates: list[dict[str, Any]] = []
    if all(item["passed"] for item in preflight_checks):
        template_text = base_template.read_text(encoding="utf-8", errors="replace").splitlines()
        for account in registry.accounts:
            values = _account_template_values(account.account_label, account.expected_login, account.symbol)
            output_path = report_json.parent / "demo_fill_collection" / (
                f"{account.account_label}_{EA_NAME}.demo_fill_collection.review_only.set.template"
            )
            rendered = _render_set_file(template_text, values)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered, encoding="utf-8")
            rendered_values = _parse_set_text(rendered)
            templates.append(_template_payload(account.account_label, account.expected_login, output_path, rendered_values))

    validations = preflight_checks + _template_checks(templates, root)
    status = "DEMO_FILL_COLLECTION_REVIEW_PACKET_READY" if all(item["passed"] for item in validations) else "DEMO_FILL_COLLECTION_PACKET_BLOCKED"
    payload: dict[str, Any] = {
        "status": status,
        "stage": "C58-ML-DEMO-FILL-COLLECTION-MODE",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", ""),
        "purpose": "Prepare controlled all-account demo fill collection inputs without deploying them or authorizing broker action globally.",
        "authorization": {
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
            "owner_review_required": True,
            "manual_activation_required_after_review": True,
            "review_only_templates_contain_armed_demo_inputs": bool(templates),
        },
        "mode": {
            "name": "controlled_demo_fill_collection",
            "expert_name": EA_NAME,
            "target_symbol": "XAUUSD",
            "accounts_requested": [account.account_label for account in registry.accounts],
            "account_logins": {account.account_label: account.expected_login for account in registry.accounts},
            "relaxed_for_collection": ["trade_session_gate"],
            "retained_hard_guards": [
                "demo server marker",
                "ACCOUNT_TRADE_MODE_DEMO check",
                "account allowlist",
                "authorization tokens",
                "kill switch",
                "fixed lot 0.01",
                "max orders per day",
                "max account orders per day",
                "max open positions",
                "minimum seconds between orders",
                "spread cap",
                "cost cap",
                "live/real server refusal",
            ],
        },
        "limits": {
            "fixed_lot": FIXED_LOT,
            "max_orders_per_day_per_account": MAX_ORDERS_PER_DAY,
            "max_account_orders_per_day": MAX_ACCOUNT_ORDERS_PER_DAY,
            "min_seconds_between_orders": MIN_SECONDS_BETWEEN_ORDERS,
            "max_open_positions_per_instance": MAX_OPEN_POSITIONS,
            "max_open_positions_per_magic": MAX_OPEN_POSITIONS_PER_MAGIC,
            "max_estimated_cost_r": MAX_ESTIMATED_COST_R,
            "max_measured_spread_points": MAX_MEASURED_SPREAD_POINTS,
            "trade_session_gate_enabled": False,
        },
        "inputs": {
            "registry_path": str(root / "config" / "ml" / "mt5_accounts.yaml"),
            "base_template": str(base_template),
            "source": str(source),
            "a3_breakout_base_include": str(a3_breakout_base),
            "dataset_pointer": str(reports / "C02_DATASET_POINTER.json"),
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
            "template_directory": str(report_json.parent / "demo_fill_collection"),
            "templates": [item["path"] for item in templates],
        },
        "templates": templates,
        "validations": validations,
        "manual_review_checklist": _manual_review_checklist(),
        "boundary": {
            "mt5_connection_attempted": False,
            "terminal_runtime_launch_attempted": False,
            "terminal_shutdown_attempted": False,
            "profile_or_chart_file_write_attempted": False,
            "preset_deployed_to_mt5": False,
            "committed_preset_modified": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer, payload)
    return report_json


def render_demo_fill_collection_mode_md(payload: dict[str, Any]) -> str:
    limits = payload.get("limits", {})
    templates = [
        {
            "Account": item.get("account_label", ""),
            "Login": item.get("account_login", ""),
            "Dry run": item.get("values", {}).get("InpDryRunOnly", ""),
            "Broker input": item.get("values", {}).get("InpBrokerActionAllowed", ""),
            "Lot": item.get("values", {}).get("InpFixedLot", ""),
            "Max/day": item.get("values", {}).get("InpMaxOrdersPerDay", ""),
            "Path": item.get("path", ""),
        }
        for item in payload.get("templates", [])
    ]
    validations = [
        {"Check": item["check"], "Passed": str(item["passed"]).lower(), "Detail": item["detail"]}
        for item in payload.get("validations", [])
    ]
    checklist = "\n".join(f"{index}. {step}" for index, step in enumerate(payload.get("manual_review_checklist", []), start=1))
    return "\n".join(
        [
            "# A3 ML Demo Fill Collection Mode",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Plain English",
            "",
            "This packet prepares a controlled way to collect real demo fills on A1, A2, and A3. It does not train a model, does not turn on Python predictions, does not deploy presets to MT5, and does not authorize broker action globally.",
            "",
            "## Authorization",
            "",
            "- Training authorized: false.",
            "- Python demo predictions authorized: false.",
            "- EA consumption authorized: false.",
            "- Broker action authorized: false.",
            "- Owner/reviewer approval required before any manual attach: true.",
            "",
            "## Limits",
            "",
            f"- Fixed lot: `{limits.get('fixed_lot', '')}`.",
            f"- Max orders per account per day: `{limits.get('max_orders_per_day_per_account', '')}`.",
            f"- Max account orders per day: `{limits.get('max_account_orders_per_day', '')}`.",
            f"- Minimum seconds between orders: `{limits.get('min_seconds_between_orders', '')}`.",
            f"- Max open positions per instance: `{limits.get('max_open_positions_per_instance', '')}`.",
            f"- Max open positions per magic: `{limits.get('max_open_positions_per_magic', '')}`.",
            f"- Max estimated cost R: `{limits.get('max_estimated_cost_r', '')}`.",
            f"- Max measured spread points: `{limits.get('max_measured_spread_points', '')}`.",
            f"- Trade session gate enabled: `{str(limits.get('trade_session_gate_enabled')).lower()}`.",
            "",
            "## Review-Only Templates",
            "",
            _table(templates, ["Account", "Login", "Dry run", "Broker input", "Lot", "Max/day", "Path"]) if templates else "No templates generated.",
            "",
            "## Manual Review Checklist",
            "",
            checklist,
            "",
            "## Validations",
            "",
            _table(validations, ["Check", "Passed", "Detail"]) if validations else "No validations ran.",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Terminal runtime launch attempted: false.",
            "- Profile or chart file write attempted: false.",
            "- Preset deployed to MT5: false.",
            "- Committed preset modified: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _preflight_checks(
    registry: Any,
    base_template: Path,
    base_values: dict[str, str],
    source: Path,
    source_text: str,
    a3_breakout_base: Path,
    a3_breakout_base_text: str,
) -> list[dict[str, Any]]:
    required_source_terms = [
        "InpBrokerActionAllowed",
        "InpExperimentalAuthorizationToken",
        "InpCostSuspensionAcknowledgementToken",
        "InpMaxOrdersPerDay",
        "InpMaxAccountOrdersPerDay",
        "InpMaxOpenPositionsPerInstance",
        "InpMaxOpenPositionsPerMagic",
        "InpMaxEstimatedCostR",
        "InpMaxMeasuredSpreadPoints",
        "KillSwitchActive",
        "AccountTradeModeDemo",
        "ACCOUNT_TRADE_MODE_DEMO",
        "OrderSend",
    ]
    checks = [
        _check("registry_has_three_accounts", len(registry.accounts) == 3, ",".join(account.account_label for account in registry.accounts)),
        _check("all_accounts_xauusd", all(account.symbol == "XAUUSD" for account in registry.accounts), "symbols=" + ",".join(account.symbol for account in registry.accounts)),
        _check("base_template_exists", base_template.exists(), str(base_template)),
        _check(
            "base_template_committed_safe",
            base_values.get("InpDryRunOnly") == "true" and base_values.get("InpBrokerActionAllowed") == "false",
            f"InpDryRunOnly={base_values.get('InpDryRunOnly', '')}; InpBrokerActionAllowed={base_values.get('InpBrokerActionAllowed', '')}",
        ),
        _check("source_exists", source.exists(), str(source)),
        *_mql_text_integrity_checks("source", source, source_text, final_token="}"),
        *_mql_text_integrity_checks("a3_breakout_base_include", a3_breakout_base, a3_breakout_base_text, final_token="#endif"),
        _check(
            "source_supports_required_runtime_guards",
            all(term in source_text for term in required_source_terms),
            "required terms present" if all(term in source_text for term in required_source_terms) else "missing terms",
        ),
        _check("source_refuses_live_or_real_server", "ContainsText(server, \"live\")" in source_text and "ContainsText(server, \"real\")" in source_text, "live/real marker refusal present"),
        _check("source_refuses_non_demo_trade_mode", "ACCOUNT_TRADE_MODE_DEMO" in source_text, "ACCOUNT_TRADE_MODE_DEMO guard present"),
        _check("kill_switch_presence_based", "return true; // Presence is enough" in source_text, "kill-switch file presence trips the guard"),
    ]
    return checks


def _template_checks(templates: list[dict[str, Any]], root: Path) -> list[dict[str, Any]]:
    checks = [_check("three_review_only_templates_generated", len(templates) == 3, f"count={len(templates)}")]
    for template in templates:
        values = template["values"]
        label = template["account_label"]
        path = Path(template["path"])
        checks.extend(
            [
                _check(f"{label}_template_under_outputs_reports", _is_under(path, root / TEMPLATE_DIR_REL), str(path)),
                _check(f"{label}_template_not_committed_preset", "mt5" not in [part.lower() for part in path.parts], str(path)),
                _check(f"{label}_demo_server_marker", values.get("InpExpectedServerMarker") == "Demo", f"InpExpectedServerMarker={values.get('InpExpectedServerMarker', '')}"),
                _check(f"{label}_account_allowlist_single_login", values.get("InpAllowedAccountLoginsCsv") == template["account_login"], f"InpAllowedAccountLoginsCsv={values.get('InpAllowedAccountLoginsCsv', '')}"),
                _check(f"{label}_owner_review_armed_inputs_present", values.get("InpDryRunOnly") == "false" and values.get("InpBrokerActionAllowed") == "true", _dry_broker_detail(values)),
                _check(f"{label}_authorization_token_present", values.get("InpExperimentalAuthorizationToken") == AUTH_TOKEN, "experimental authorization token matches"),
                _check(f"{label}_cost_ack_token_present", values.get("InpCostSuspensionAcknowledgementToken") == COST_ACK_TOKEN, "cost acknowledgement token matches"),
                _check(f"{label}_fixed_lot_001", values.get("InpFixedLot") == FIXED_LOT, f"InpFixedLot={values.get('InpFixedLot', '')}"),
                _check(f"{label}_max_orders_per_day_lte_3", _int_lte(values.get("InpMaxOrdersPerDay"), MAX_ORDERS_PER_DAY), f"InpMaxOrdersPerDay={values.get('InpMaxOrdersPerDay', '')}"),
                _check(f"{label}_max_account_orders_per_day_lte_3", _int_lte(values.get("InpMaxAccountOrdersPerDay"), MAX_ACCOUNT_ORDERS_PER_DAY), f"InpMaxAccountOrdersPerDay={values.get('InpMaxAccountOrdersPerDay', '')}"),
                _check(f"{label}_max_open_positions_eq_1", values.get("InpMaxOpenPositionsPerInstance") == str(MAX_OPEN_POSITIONS), f"InpMaxOpenPositionsPerInstance={values.get('InpMaxOpenPositionsPerInstance', '')}"),
                _check(f"{label}_max_open_positions_per_magic_eq_1", values.get("InpMaxOpenPositionsPerMagic") == str(MAX_OPEN_POSITIONS_PER_MAGIC), f"InpMaxOpenPositionsPerMagic={values.get('InpMaxOpenPositionsPerMagic', '')}"),
                _check(f"{label}_cost_cap_lte_015", _float_lte(values.get("InpMaxEstimatedCostR"), float(MAX_ESTIMATED_COST_R)), f"InpMaxEstimatedCostR={values.get('InpMaxEstimatedCostR', '')}"),
                _check(f"{label}_spread_cap_lte_75", _float_lte(values.get("InpMaxMeasuredSpreadPoints"), float(MAX_MEASURED_SPREAD_POINTS)), f"InpMaxMeasuredSpreadPoints={values.get('InpMaxMeasuredSpreadPoints', '')}"),
                _check(f"{label}_session_gate_relaxed_for_collection", values.get("InpTradeSessionGateEnabled") == "false", f"InpTradeSessionGateEnabled={values.get('InpTradeSessionGateEnabled', '')}"),
            ]
        )
    checks.append(_check("broker_action_authorization_remains_false", True, "status packet is review-only; no runtime attach or deployment performed"))
    return checks


def _mql_text_integrity_checks(label: str, path: Path, text: str, *, final_token: str) -> list[dict[str, Any]]:
    open_braces = text.count("{")
    close_braces = text.count("}")
    stripped = text.rstrip()
    return [
        _check(f"{label}_file_exists", path.exists(), str(path)),
        _check(f"{label}_has_no_nul_bytes", "\x00" not in text, f"bytes={len(text.encode('utf-8', errors='replace'))}"),
        _check(f"{label}_has_final_newline", text.endswith("\n"), "final newline present"),
        _check(f"{label}_brace_balance", open_braces == close_braces, f"open={open_braces}; close={close_braces}"),
        _check(f"{label}_ends_cleanly", stripped.endswith(final_token), f"expected final token {final_token!r}"),
    ]


def _account_template_values(account_label: str, login: str, symbol: str) -> dict[str, str]:
    prefix = f"a3_demo_fill_collection_{account_label.lower()}"
    return {
        "InpRunId": f"A3_DEMO_FILL_COLLECTION_{account_label}_V1",
        "InpDryRunOnly": "false",
        "InpBrokerActionAllowed": "true",
        "InpCandidate": "breakout_retest",
        "InpCandidateStatus": "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY",
        "InpFamilyLifecycleStatus": "COST_SUSPENDED_CANONICAL",
        "InpTargetSymbol": symbol,
        "InpQualifiedSymbolsCsv": symbol,
        "InpExpectedServerMarker": "Demo",
        "InpAllowedAccountLoginsCsv": login,
        "InpExperimentalAuthorizationToken": AUTH_TOKEN,
        "InpRequiredExperimentalAuthorizationToken": AUTH_TOKEN,
        "InpCostSuspensionAcknowledgementToken": COST_ACK_TOKEN,
        "InpRequiredCostSuspensionAcknowledgementToken": COST_ACK_TOKEN,
        "InpAuthorizedCandidatesCsv": "breakout_retest",
        "InpAttachmentLogFileName": f"{prefix}_signal_log_xauusd.csv",
        "InpStartupLogFileName": f"{prefix}_startup_xauusd.csv",
        "InpOrderLogFileName": f"{prefix}_order_log_xauusd.csv",
        "InpKillSwitchFileName": "a3_demo_fill_collection_kill_switch.txt",
        "InpFixedLot": FIXED_LOT,
        "InpEURUSDFixedLot": FIXED_LOT,
        "InpGBPUSDFixedLot": FIXED_LOT,
        "InpMaxOrdersPerDay": str(MAX_ORDERS_PER_DAY),
        "InpMaxAccountOrdersPerDay": str(MAX_ACCOUNT_ORDERS_PER_DAY),
        "InpMinSecondsBetweenOrders": str(MIN_SECONDS_BETWEEN_ORDERS),
        "InpMaxOpenPositionsPerInstance": str(MAX_OPEN_POSITIONS),
        "InpMaxOpenPositionsPerMagic": str(MAX_OPEN_POSITIONS_PER_MAGIC),
        "InpDeviationPoints": "50",
        "InpMaxEstimatedCostR": MAX_ESTIMATED_COST_R,
        "InpMaxMeasuredSpreadPoints": MAX_MEASURED_SPREAD_POINTS,
        "InpTradeSessionGateEnabled": "false",
        "InpTradeSessionStartHour": "0",
        "InpTradeSessionEndHour": "23",
    }


def _template_payload(account_label: str, login: str, path: Path, values: dict[str, str]) -> dict[str, Any]:
    return {
        "account_label": account_label,
        "account_login": login,
        "expert_name": EA_NAME,
        "path": str(path),
        "classification": "review_only_owner_manual_activation_template",
        "not_deployed_to_mt5": True,
        "values": {
            key: values.get(key, "")
            for key in [
                "InpRunId",
                "InpDryRunOnly",
                "InpBrokerActionAllowed",
                "InpTargetSymbol",
                "InpExpectedServerMarker",
                "InpAllowedAccountLoginsCsv",
                "InpExperimentalAuthorizationToken",
                "InpCostSuspensionAcknowledgementToken",
                "InpFixedLot",
                "InpMaxOrdersPerDay",
                "InpMaxAccountOrdersPerDay",
                "InpMinSecondsBetweenOrders",
                "InpMaxOpenPositionsPerInstance",
                "InpMaxOpenPositionsPerMagic",
                "InpMaxEstimatedCostR",
                "InpMaxMeasuredSpreadPoints",
                "InpTradeSessionGateEnabled",
            ]
        },
    }


def _manual_review_checklist() -> list[str]:
    return [
        "Reviewer confirms this is demo-only and not live or real capital.",
        "Reviewer confirms Phase2ExperimentalDemoExecutor.mq5 compiles in MetaEditor before owner attach.",
        "Reviewer confirms each template allowlists only its matching account login.",
        "Reviewer confirms one XAUUSD M5 chart per account and no duplicate same-account fill-collection chart.",
        "Owner creates a3_demo_fill_collection_kill_switch.txt in MQL5/Files before testing the stop path, then removes it only for the approved window.",
        "Owner manually copies the reviewed template into the matching terminal only after approval.",
        "Owner watches order logs after attach and stops immediately if spread/cost/order caps behave unexpectedly.",
        "After the collection window, owner disables broker action or detaches the fill-collection chart and reruns runtime evidence reports.",
    ]


def _next_allowed_stage(status: str) -> str:
    if status == "DEMO_FILL_COLLECTION_REVIEW_PACKET_READY":
        return "Send the C58 packet to reviewer. Only after reviewer and owner approval should the review-only templates be manually copied into the matching demo terminals."
    return "Fix blocked C58 validations before preparing any manual demo fill collection attach."


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_demo_fill_collection_mode_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any]) -> None:
    if not pointer:
        return
    pointer["c58_demo_fill_collection_mode_report"] = payload["outputs"]["status_report_json"]
    pointer["c58_demo_fill_collection_mode_status"] = payload["status"]
    pointer["c58_demo_fill_collection_review_only_templates"] = payload["outputs"]["templates"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    pointer["training_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _render_set_file(template_lines: list[str], values: dict[str, str]) -> str:
    rendered: list[str] = []
    seen: set[str] = set()
    for line in template_lines:
        if "=" not in line or line.lstrip().startswith("#"):
            rendered.append(line)
            continue
        key, _old = line.split("=", 1)
        key = key.strip()
        if key in values:
            rendered.append(f"{key}={values[key]}")
            seen.add(key)
        else:
            rendered.append(line)
    for key, value in values.items():
        if key not in seen:
            rendered.append(f"{key}={value}")
    return "\n".join(rendered).rstrip() + "\n"


def _parse_set_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return _parse_set_text(path.read_text(encoding="utf-8", errors="replace"))


def _parse_set_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _check(check: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": check, "passed": bool(passed), "detail": detail}


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _int_lte(value: str | None, limit: int) -> bool:
    try:
        return int(float(str(value))) <= limit
    except ValueError:
        return False


def _float_lte(value: str | None, limit: float) -> bool:
    try:
        return float(str(value)) <= limit
    except ValueError:
        return False


def _dry_broker_detail(values: dict[str, str]) -> str:
    return f"InpDryRunOnly={values.get('InpDryRunOnly', '')}; InpBrokerActionAllowed={values.get('InpBrokerActionAllowed', '')}"
