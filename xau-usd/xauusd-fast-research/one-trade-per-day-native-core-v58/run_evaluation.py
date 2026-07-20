from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from src.audit import (
    build_native_core,
    combine_trades,
    evaluate_gates,
    govern_addons,
    rows_for_windows,
    sha256_file,
    verify_sources,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "one_trade_per_day_native_core_v58.json"


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return json_ready(value.item())
    return value


def canonical_sha256(value: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(json_ready(value), sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def _assert_inherited_policy(config: dict[str, Any]) -> None:
    overlay_path = REPO_ROOT / config["sources"]["v57_overlay_config"]["path"]
    base_path = REPO_ROOT / config["sources"]["v53_base_config"]["path"]
    overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
    base = json.loads(base_path.read_text(encoding="utf-8"))
    inherited_account = {**base["account"], **overlay["account_overrides"]}
    if inherited_account != config["account"]:
        raise ValueError("V58 account policy differs from frozen V57")
    if base["windows"] != config["windows"]:
        raise ValueError("V58 windows differ from frozen V57")
    if base["gates"] != config["gates"]:
        raise ValueError("V58 gates differ from frozen V57")
    inherited_target = base["v50_policy"]
    policy = config["v50_policy"]
    if inherited_target["target_specialist_id"] != policy["target_specialist_id"]:
        raise ValueError("V58 target specialist differs from V57")
    if inherited_target["target_source_strategy"] != policy["target_source_strategy"]:
        raise ValueError("V58 target strategy differs from V57")


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    contract_path = output / config["outputs"]["contract_lock"]
    if not contract_path.is_file():
        raise FileNotFoundError("Lock the V58 contract before evaluation")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract["config_sha256"] != sha256_file(CONFIG_PATH):
        raise ValueError("V58 config changed after contract lock")
    source_hashes = verify_sources(REPO_ROOT, config["sources"])
    if source_hashes != contract["source_hashes"]:
        raise ValueError("V58 source set changed after contract lock")
    implementation_hashes = {
        "audit": sha256_file(ROOT / "src" / "audit.py"),
        "runner": sha256_file(ROOT / "run_evaluation.py"),
    }
    if implementation_hashes != contract["implementation_hashes"]:
        raise ValueError("V58 implementation changed after contract lock")
    _assert_inherited_policy(config)

    normalized = pd.read_parquet(
        REPO_ROOT / config["sources"]["normalized_core"]["path"]
    )
    reconciliation = pd.read_csv(
        REPO_ROOT / config["sources"]["native_reconciliation"]["path"]
    )
    candidates = pd.read_parquet(
        REPO_ROOT / config["sources"]["v57_candidates"]["path"]
    )
    core, r1_decisions, repair_audit = build_native_core(
        normalized,
        reconciliation,
        config["native_r1"],
        config["v50_policy"],
    )
    addons, addon_decisions = govern_addons(candidates, core, config["account"])
    combined = combine_trades(core, addons)
    windows = rows_for_windows(
        core,
        addons,
        combined,
        config["windows"],
        int(config["gates"]["top_winners_removed"]),
    )
    gate = evaluate_gates(windows, config)
    decision = (
        "V58_NATIVE_POSITION_ONE_TRADE_PER_DAY_GATE_PASS"
        if gate["passed"]
        else "V58_NATIVE_POSITION_ONE_TRADE_PER_DAY_GATE_FAIL_TERMINAL"
    )
    result = {
        "schema_version": "xauusd_one_trade_per_day_native_core_v58_result",
        "decision": decision,
        "contract_sha256": contract["contract_sha256"],
        "source_hashes": source_hashes,
        "implementation_hashes": implementation_hashes,
        "repair_audit": repair_audit,
        "corrected_core_trades": int(len(core)),
        "candidate_addons": int(len(candidates)),
        "accepted_addons": int(len(addons)),
        "accepted_by_sleeve": addons["sleeve_id"].value_counts().sort_index().to_dict(),
        "addon_decision_reason_counts": addon_decisions["decision_reason"]
        .value_counts()
        .sort_index()
        .to_dict(),
        "gate": gate,
        "windows": windows.to_dict(orient="records"),
        "limitations": {
            "complete_fee_evidence": False,
            "whole_account_floating_equity_proven": False,
            "prospective_shadow_required": True,
            "mt5_portfolio_parity_required": True,
        },
        "research_controls": config["research_controls"],
    }
    result["result_sha256"] = canonical_sha256(result)

    core.to_parquet(output / config["outputs"]["corrected_core"], index=False)
    r1_decisions.to_parquet(output / config["outputs"]["r1_decisions"], index=False)
    addon_decisions.to_parquet(
        output / config["outputs"]["addon_decisions"], index=False
    )
    combined.to_parquet(output / config["outputs"]["trades"], index=False)
    windows.to_csv(output / config["outputs"]["windows"], index=False, lineterminator="\n")
    (output / config["outputs"]["result_json"]).write_text(
        json.dumps(json_ready(result), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# One-Trade-Per-Day Native Core V58 Result",
        "",
        f"Decision: `{decision}`",
        "",
        f"Native R1 rows repaired: **{repair_audit['native_r1_rows']}**",
        f"Corrected R1 target accepted: **{repair_audit['target_rows_after_cap']} / {repair_audit['target_rows_before_cap']}**",
        f"Unified add-ons accepted: **{len(addons)} / {len(candidates)}**",
        "",
        "| Window | Portfolio | Trades | Trades/day | Net USD | PF | DD USD | Top-5 removed | Positive months |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in windows.to_dict(orient="records"):
        lines.append(
            "| {window} | {portfolio_id} | {trades} | {trades_per_weekday:.3f} | "
            "{net_usd:.2f} | {profit_factor:.3f} | {closed_drawdown_usd:.2f} | "
            "{winner_removed_net_usd:.2f} | {positive_month_share:.1%} |".format(**row)
        )
    failed = [name for name, passed in gate["checks"].items() if not passed]
    lines.extend(
        [
            "",
            f"Failed gates: `{failed}`",
            "",
            "The native deal logs do not provide complete fee evidence. Whole-account floating equity is not yet proven.",
            "",
            "Historical research only; no execution authority.",
        ]
    )
    (output / config["outputs"]["result_markdown"]).write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    artifacts = {}
    for key in (
        "contract_lock",
        "corrected_core",
        "r1_decisions",
        "addon_decisions",
        "trades",
        "windows",
        "result_json",
        "result_markdown",
    ):
        path = output / config["outputs"][key]
        artifacts[key] = {
            "path": str(path.relative_to(REPO_ROOT)),
            "sha256": sha256_file(path),
        }
    manifest = {
        "schema_version": "xauusd_one_trade_per_day_native_core_v58_manifest",
        "artifacts": artifacts,
    }
    (output / config["outputs"]["manifest"]).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(decision)
    print(result["result_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
