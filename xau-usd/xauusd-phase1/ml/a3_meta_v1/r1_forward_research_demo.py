from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = Path("config/ml/a3_r1_forward_research_demo_v1.json")
DEFAULT_REPORT = Path("outputs/reports/A3_R1_FORWARD_RESEARCH_DEMO_V1_PACKET.json")
DEFAULT_PRESET = Path(
    "outputs/reports/a3_r1_forward_research_demo/"
    "A3_A1XauM5MomentumContinuationExecutor.r1_forward_research.review_only.set.template"
)


def generate_r1_forward_research_demo_packet(
    root: Path,
    *,
    config_path: Path | None = None,
    report_path: Path | None = None,
    preset_path: Path | None = None,
) -> Path:
    root = root.resolve()
    config_path = (config_path or root / DEFAULT_CONFIG).resolve()
    report_path = (report_path or root / DEFAULT_REPORT).resolve()
    preset_path = (preset_path or root / DEFAULT_PRESET).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    source_path = (root / config["expert"]["source"]).resolve()
    source = source_path.read_text(encoding="utf-8", errors="replace")
    inputs = config["inputs"]

    checks = _checks(config, source, inputs)
    status = "READY_FOR_A3_ISOLATED_DEMO_ATTACH" if all(item["passed"] for item in checks) else "PACKET_BLOCKED"
    preset_text = _render_set(inputs)
    preset_path.parent.mkdir(parents=True, exist_ok=True)
    preset_path.write_text(preset_text, encoding="utf-8")

    payload: dict[str, Any] = {
        "status": status,
        "schema_version": config["schema_version"],
        "purpose": config["purpose"],
        "account": config["account"],
        "expert": config["expert"],
        "risk": config["risk"],
        "isolation": config["isolation"],
        "authorization": config["authorization"],
        "inputs": inputs,
        "checks": checks,
        "artifacts": {
            "config": str(config_path),
            "source": str(source_path),
            "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            "preset": str(preset_path),
            "preset_sha256": hashlib.sha256(preset_text.encode("utf-8")).hexdigest(),
            "report": str(report_path),
        },
        "boundary": {
            "terminal_contacted": False,
            "profile_edited": False,
            "expert_compiled": False,
            "expert_attached": False,
            "broker_action_started": False,
        },
        "next": (
            "Run the A3 isolation/identity preflight, pause the old armed fill-collection chart, compile, attach, and verify INIT_OK."
            if status == "READY_FOR_A3_ISOLATED_DEMO_ATTACH"
            else "Fix every failed packet check before terminal deployment."
        ),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    report_path.with_suffix(".md").write_text(_render_markdown(payload), encoding="utf-8")
    return report_path


def _checks(config: dict[str, Any], source: str, inputs: dict[str, str]) -> list[dict[str, Any]]:
    account = config["account"]
    expert = config["expert"]
    risk = config["risk"]
    auth = config["authorization"]
    required_source_terms = (
        "ACCOUNT_TRADE_MODE_DEMO",
        "InpAllowedAccountLogin",
        "InpExpectedServerMarker",
        "KillSwitchPresent",
        "InpMaxSpreadPoints",
        "InpMaxEstimatedCostR",
        "InpPortfolioDailyLossStopUsd",
        "InpRejectRiskOvershootEnabled",
        "minimum_lot_risk_excess",
    )
    checks = [
        _check("account_is_a3_1033669", account.get("label") == "A3" and account.get("login") == "1033669", str(account)),
        _check("account_currency_is_aed", account.get("currency") == "AED", str(account.get("currency"))),
        _check("server_is_exact_demo", account.get("server") == "Capital.ComMena-Demo", str(account.get("server"))),
        _check("fresh_magic_934100", expert.get("magic") == 934100 and inputs.get("InpMagicNumber") == "934100", str(expert.get("magic"))),
        _check("source_has_runtime_guards", all(term in source for term in required_source_terms), "required fail-closed terms present"),
        _check("source_has_frozen_signal_enum", "SIGNAL_D1_COMPRESSION_H4_EXPANSION = 7" in source, "mode 7"),
        _check("source_has_frozen_router_enum", "REGIME_ROUTER_LONG_R1_UPTREND_ONLY = 1" in source, "router 1"),
        _check("demo_only_inputs", inputs.get("InpAllowDemoTrading") == "true" and inputs.get("InpAllowNonDemoAccounts") == "false", _detail(inputs, "InpAllowDemoTrading", "InpAllowNonDemoAccounts")),
        _check("single_account_allowlist", inputs.get("InpAllowedAccountLogin") == "1033669", _detail(inputs, "InpAllowedAccountLogin")),
        _check("frozen_r1_signal", _matches(inputs, {"InpSignalMode": "7", "InpDirectionMode": "1", "InpRegimeRouterMode": "1"}), _detail(inputs, "InpSignalMode", "InpDirectionMode", "InpRegimeRouterMode")),
        _check("frozen_r1_shape", _matches(inputs, {"InpD1CompressionAtrPercentileMax": "80.00", "InpD1CompressionBoxDays": "2", "InpD1CompressionRangeMedianMax": "1.50", "InpD1CompressionH4MinBodyFraction": "0.35", "InpRiskReward": "2.00"}), "frozen historical geometry"),
        _check("risk_is_account_currency_aed", risk.get("input_units") == "account_currency_AED", str(risk.get("input_units"))),
        _check("risk_cap_30_aed", _matches(inputs, {"InpUseRiskNormalizedLots": "true", "InpRiskAmountUsd": "30.00", "InpMaxRiskLots": "0.01", "InpRejectRiskOvershootEnabled": "true", "InpMaxRiskOvershootPct": "0.00"}), _detail(inputs, "InpRiskAmountUsd", "InpMaxRiskLots", "InpMaxRiskOvershootPct")),
        _check("one_position_and_one_entry", _matches(inputs, {"InpMaxTradesPerDay": "1", "InpPortfolioMaxTradesPerDay": "1", "InpOnePositionPerMagic": "true", "InpMaxOpenPositionsPerMagic": "1"}), "one entry/day; one position"),
        _check("daily_loss_60_aed", inputs.get("InpPortfolioDailyGuardEnabled") == "true" and inputs.get("InpPortfolioDailyLossStopUsd") == "60.00", _detail(inputs, "InpPortfolioDailyGuardEnabled", "InpPortfolioDailyLossStopUsd")),
        _check("cost_guards_retained", _matches(inputs, {"InpMaxSpreadPoints": "75", "InpMaxEstimatedCostR": "0.15"}), _detail(inputs, "InpMaxSpreadPoints", "InpMaxEstimatedCostR")),
        _check("no_ml_execution", auth.get("ml_execution") is False, str(auth.get("ml_execution"))),
        _check("not_live_or_promoted", auth.get("live_or_real_account") is False and auth.get("strategy_promoted") is False, str(auth)),
        _check("other_broker_action_forbidden", config["isolation"].get("require_no_other_broker_action_chart") is True, str(config["isolation"])),
    ]
    input_names = set(_source_input_names(source))
    unknown = sorted(set(inputs) - input_names)
    checks.append(_check("all_preset_inputs_exist_in_source", not unknown, "unknown=" + ",".join(unknown)))
    return checks


def _source_input_names(source: str) -> list[str]:
    names = []
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped.startswith("input ") or "=" not in stripped:
            continue
        left = stripped.split("=", 1)[0].strip()
        names.append(left.split()[-1])
    return names


def _render_set(inputs: dict[str, str]) -> str:
    return "\n".join(f"{key}={value}" for key, value in inputs.items()) + "\n"


def _render_markdown(payload: dict[str, Any]) -> str:
    checks = "\n".join(
        f"- {'PASS' if item['passed'] else 'FAIL'}: `{item['check']}` - {item['detail']}"
        for item in payload["checks"]
    )
    return "\n".join(
        [
            "# A3 R1 Forward-Research Demo V1 Packet",
            "",
            f"Status: `{payload['status']}`",
            "",
            "This packet prepares one low-frequency R1 specialist for isolated prospective demo evidence. It has not contacted or changed MT5.",
            "",
            "## Fixed Limits",
            "",
            "- Account: `1033669 / Capital.ComMena-Demo`.",
            "- Account currency: AED.",
            "- Requested risk: AED 30 per trade.",
            "- Daily closed-loss stop: AED 60.",
            "- Maximum lot: 0.01.",
            "- Maximum one new entry per day and one open position.",
            "- Live/real accounts and ML execution: forbidden.",
            "",
            "## Checks",
            "",
            checks,
            "",
            "## Next",
            "",
            payload["next"],
            "",
        ]
    )


def _matches(values: dict[str, str], expected: dict[str, str]) -> bool:
    return all(values.get(key) == value for key, value in expected.items())


def _detail(values: dict[str, str], *keys: str) -> str:
    return "; ".join(f"{key}={values.get(key, '')}" for key in keys)


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed), "detail": detail}
