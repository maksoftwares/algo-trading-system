from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
V53_SRC = ROOT.parent / "one-trade-per-day-health-portfolio-v53" / "src"
V56_SRC = ROOT.parent / "one-trade-per-day-break-overlay-v56" / "src"
sys.path.insert(0, str(V56_SRC))
sys.path.insert(0, str(V53_SRC))
sys.path.insert(0, str(ROOT / "src"))

from overlay import build_overlay_candidates  # noqa: E402
from policy import resolve_config  # noqa: E402
from portfolio import (  # noqa: E402
    causal_shadow_health_gate,
    combine_trades,
    evaluate_gates,
    execute_single_rule,
    govern_addons,
    load_addon_candidates,
    load_v50_core,
    rows_for_windows,
    sha256_file,
    verify_sources,
)


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


def payload_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(json_ready(payload), sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def main() -> int:
    config_path = ROOT / "config" / "one_trade_per_day_unified_portfolio_v57.json"
    config, overlay = resolve_config(REPO_ROOT, config_path)
    base_path = REPO_ROOT / overlay["base_config_path"]
    output = ROOT / config["outputs"]["directory"]
    contract_path = output / config["outputs"]["contract_lock"]
    if not contract_path.is_file():
        raise FileNotFoundError("Lock the V57 contract before evaluation")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract["overlay_config_sha256"] != sha256_file(config_path):
        raise ValueError("V57 overlay changed after contract lock")
    if contract["base_config_sha256"] != sha256_file(base_path):
        raise ValueError("V53 base changed after V57 contract lock")
    source_hashes = verify_sources(REPO_ROOT, config["sources"])
    if source_hashes != contract["source_hashes"]:
        raise ValueError("V57 sources changed after contract lock")
    implementation_hashes = {
        "base_portfolio": sha256_file(V53_SRC / "portfolio.py"),
        "candidate_builder": sha256_file(V56_SRC / "overlay.py"),
        "policy": sha256_file(ROOT / "src" / "policy.py"),
        "runner": sha256_file(ROOT / "run_evaluation.py"),
    }
    if implementation_hashes != contract["implementation_hashes"]:
        raise ValueError("V57 implementation changed after contract lock")

    core = load_v50_core(REPO_ROOT, config)
    base_candidates = load_addon_candidates(REPO_ROOT, config)
    actions = pd.read_parquet(
        REPO_ROOT / config["sources"]["expansion_actions"]["path"]
    )
    overlay_candidates, candidate_audit = build_overlay_candidates(
        actions,
        base_candidates,
        config["overlay_sleeve"],
        execute_single_rule,
        causal_shadow_health_gate,
    )
    overlay_candidates["trade_id"] = "V9_BREAK_" + overlay_candidates[
        "event_id"
    ].astype(str)
    overlay_candidates["sleeve_id"] = config["overlay_sleeve"]["sleeve_id"]
    columns = [
        "trade_id",
        "sleeve_id",
        "signal_time",
        "entry_time",
        "exit_time",
        "direction",
        "pnl_usd",
        "risk_usd",
    ]
    candidates = (
        pd.concat(
            [base_candidates[columns], overlay_candidates[columns]], ignore_index=True
        )
        .sort_values(["entry_time", "trade_id"], kind="mergesort")
        .reset_index(drop=True)
    )
    if candidates["trade_id"].duplicated().any():
        raise ValueError("Duplicate unified candidate trade IDs")
    addons, decisions = govern_addons(candidates, core, config["account"])
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
        "V57_ONE_TRADE_PER_DAY_HISTORICAL_GATE_PASS"
        if gate["passed"]
        else "V57_ONE_TRADE_PER_DAY_HISTORICAL_GATE_FAIL_TERMINAL"
    )
    result = {
        "schema_version": "xauusd_one_trade_per_day_unified_portfolio_v57_result",
        "decision": decision,
        "contract_sha256": contract["contract_sha256"],
        "source_hashes": source_hashes,
        "implementation_hashes": implementation_hashes,
        "candidate_audit": candidate_audit,
        "base_candidates": int(len(base_candidates)),
        "overlay_candidates": int(len(overlay_candidates)),
        "accepted_addons": int(len(addons)),
        "decision_reason_counts": decisions["decision_reason"]
        .value_counts()
        .sort_index()
        .to_dict(),
        "accepted_by_sleeve": addons["sleeve_id"].value_counts().sort_index().to_dict(),
        "gate": gate,
        "windows": windows.to_dict(orient="records"),
        "research_controls": config["research_controls"],
    }
    result["result_sha256"] = payload_sha256(result)

    candidates.to_parquet(output / config["outputs"]["candidate_trades"], index=False)
    decisions.to_parquet(output / config["outputs"]["decisions"], index=False)
    combined.to_parquet(output / config["outputs"]["trades"], index=False)
    windows.to_csv(
        output / config["outputs"]["windows"], index=False, lineterminator="\n"
    )
    (output / config["outputs"]["result_json"]).write_text(
        json.dumps(json_ready(result), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )

    lines = [
        "# One-Trade-Per-Day Unified Portfolio V57 Result",
        "",
        f"Decision: `{decision}`",
        "",
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
            "All add-on decisions use one actual causal closed-equity path. This is exposed-history research and grants no execution authority.",
        ]
    )
    (output / config["outputs"]["result_markdown"]).write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    artifacts = {}
    for key in (
        "contract_lock",
        "candidate_trades",
        "decisions",
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
        "schema_version": "xauusd_one_trade_per_day_unified_portfolio_v57_manifest",
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
