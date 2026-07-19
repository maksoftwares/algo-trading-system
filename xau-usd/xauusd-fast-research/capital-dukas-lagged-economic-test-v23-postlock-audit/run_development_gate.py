from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
V23 = ROOT.parent / "capital-dukas-lagged-economic-test-v23"
sys.path.insert(0, str(V23))
sys.path.insert(0, str(V23 / "src"))

from download_sealed_dukascopy import verify_contract  # noqa: E402
from economic_test import (  # noqa: E402
    full_weekdays,
    load_config,
    load_development_candidates,
    load_development_paired,
    metrics_for_trades,
    simulate_trades,
)


def canonical_hash(payload: dict[str, Any]) -> str:
    normalized = dict(payload)
    normalized.pop("audit_sha256", None)
    encoded = json.dumps(
        normalized,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def render_markdown(audit: dict[str, Any]) -> str:
    primary = audit["primary_development_metrics"]
    checks = audit["development_gate_checks"]
    lines = [
        "# V23 Post-Lock Development Gate",
        "",
        f"- Decision: `{audit['decision']}`",
        f"- Frozen V23 contract: `{audit['contract_sha256']}`",
        "- Confirmation data opened: `false`",
        f"- Full development weekdays: {primary['full_weekdays']}",
        f"- Primary trades: {primary['trades']}",
        (
            "- Primary frequency: "
            f"{primary['trades_per_full_weekday']:.6f} trades/full weekday"
        ),
        f"- Primary base net: ${primary['base_net_pnl_dollars']:.2f}",
        f"- Primary base PF: {primary['base_profit_factor']:.6f}",
        f"- Positive-net gate: `{str(checks['positive_net']).lower()}`",
        f"- PF gate: `{str(checks['minimum_profit_factor']).lower()}`",
        "",
        "## Clock Robustness",
        "",
        "| Safety lag | Trades/day | Net | PF | Stress PF |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in audit["development_metrics"]:
        lines.append(
            f"| {row['safety_lag_ms']} ms "
            f"| {row['trades_per_full_weekday']:.6f} "
            f"| ${row['base_net_pnl_dollars']:.2f} "
            f"| {row['base_profit_factor']:.6f} "
            f"| {row['stress_profit_factor']:.6f} |"
        )
    lines.extend(
        [
            "",
            "V23 failed before confirmation. Its direction, threshold, horizon,",
            "costs, and filters remain frozen; same-version tuning is forbidden.",
            "This result provides no trading or model authorization.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config = load_config(V23)
    contract = verify_contract(config)
    paired = load_development_paired(config, V23)
    candidates = load_development_candidates(config, V23)
    eligible_dates = full_weekdays(paired, config)
    trades = simulate_trades(paired, candidates, eligible_dates, config)
    lags = [
        int(config["feature"]["primary_safety_lag_ms"]),
        *[
            int(value)
            for value in config["feature"]["robustness_safety_lags_ms"]
        ],
    ]
    metrics = [
        metrics_for_trades(
            trades,
            "DEVELOPMENT",
            lag,
            eligible_dates,
            config,
        )[0]
        for lag in lags
    ]
    primary = metrics[0]
    gates = config["gates"]
    gate_checks = {
        "positive_net": bool(
            not gates["development_require_positive_net"]
            or float(primary["base_net_pnl_dollars"]) > 0.0
        ),
        "minimum_profit_factor": bool(
            float(primary["base_profit_factor"])
            >= float(gates["development_min_profit_factor"])
        ),
    }
    passed = all(gate_checks.values())
    audit: dict[str, Any] = {
        "schema_version": "xauusd_v23_postlock_development_gate_audit",
        "contract_sha256": contract["contract_sha256"],
        "confirmation_data_opened": False,
        "confirmation_economic_outcomes_opened": False,
        "development_candidate_rows": int(len(candidates)),
        "development_simulated_trade_rows_all_lags": int(len(trades)),
        "primary_development_metrics": primary,
        "development_metrics": metrics,
        "development_gates": {
            "require_positive_net": bool(
                gates["development_require_positive_net"]
            ),
            "minimum_profit_factor": float(
                gates["development_min_profit_factor"]
            ),
        },
        "development_gate_checks": gate_checks,
        "development_gate_passed": passed,
        "decision": (
            "V23_DEVELOPMENT_GATE_PASS_CONFIRMATION_REQUIRED"
            if passed
            else "V23_DEVELOPMENT_GATE_FAIL_NO_CONFIRMATION_REQUIRED"
        ),
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "broker_action_authorized": False,
    }
    audit["audit_sha256"] = canonical_hash(audit)
    output = ROOT / "outputs"
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "CROSSVENUE_V23_DEVELOPMENT_GATE_AUDIT.json"
    markdown_path = output / "CROSSVENUE_V23_DEVELOPMENT_GATE_AUDIT.md"
    json_path.write_text(
        json.dumps(audit, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(audit), encoding="utf-8")
    print(json.dumps(audit, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
