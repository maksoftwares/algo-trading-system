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
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(V53_SRC))

from overlay import build_overlay_candidates, govern_incremental_overlay  # noqa: E402
from policy import resolve_config  # noqa: E402
from portfolio import (  # noqa: E402
    causal_shadow_health_gate,
    combine_trades,
    evaluate_gates,
    execute_single_rule,
    load_addon_candidates,
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
    config_path = ROOT / "config" / "one_trade_per_day_break_overlay_v56.json"
    config, overlay = resolve_config(REPO_ROOT, config_path)
    base_path = REPO_ROOT / overlay["base_config_path"]
    output = ROOT / config["outputs"]["directory"]
    contract_path = output / config["outputs"]["contract_lock"]
    if not contract_path.is_file():
        raise FileNotFoundError("Lock the V56 contract before evaluation")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract["overlay_config_sha256"] != sha256_file(config_path):
        raise ValueError("V56 overlay changed after contract lock")
    if contract["base_config_sha256"] != sha256_file(base_path):
        raise ValueError("V53 base changed after V56 contract lock")
    source_hashes = verify_sources(REPO_ROOT, config["sources"])
    if source_hashes != contract["source_hashes"]:
        raise ValueError("V56 sources changed after contract lock")
    implementation_hashes = {
        "base_portfolio": sha256_file(V53_SRC / "portfolio.py"),
        "policy": sha256_file(ROOT / "src" / "policy.py"),
        "overlay": sha256_file(ROOT / "src" / "overlay.py"),
    }
    if implementation_hashes != contract["implementation_hashes"]:
        raise ValueError("V56 implementation changed after contract lock")

    base_candidates = load_addon_candidates(REPO_ROOT, config)
    actions = pd.read_parquet(
        REPO_ROOT / config["sources"]["expansion_actions"]["path"]
    )
    candidates, candidate_audit = build_overlay_candidates(
        actions,
        base_candidates,
        config["overlay_sleeve"],
        execute_single_rule,
        causal_shadow_health_gate,
    )
    fixed = pd.read_parquet(REPO_ROOT / config["sources"]["v54_trades"]["path"])
    for column in ("signal_time", "entry_time", "exit_time"):
        fixed[column] = pd.to_datetime(fixed[column], utc=True)
    core = fixed.loc[fixed["sleeve_id"].eq("V50_CORE")].copy()
    base_addons = fixed.loc[fixed["sleeve_id"].ne("V50_CORE")].copy()
    overlay_trades, decisions = govern_incremental_overlay(
        candidates, fixed, config["account"]
    )
    addons = pd.concat([base_addons, overlay_trades], ignore_index=True)
    combined = combine_trades(core, addons)
    windows = rows_for_windows(
        core,
        addons,
        combined,
        config["windows"],
        int(config["gates"]["top_winners_removed"]),
    )
    gate = evaluate_gates(windows, config)
    base_preserved = set(base_addons["trade_id"].astype(str)).issubset(
        set(addons["trade_id"].astype(str))
    )
    decision = (
        "V56_ONE_TRADE_PER_DAY_HISTORICAL_GATE_PASS"
        if gate["passed"] and base_preserved
        else "V56_ONE_TRADE_PER_DAY_HISTORICAL_GATE_FAIL_TERMINAL"
    )
    result = {
        "schema_version": "xauusd_one_trade_per_day_break_overlay_v56_result",
        "decision": decision,
        "contract_sha256": contract["contract_sha256"],
        "source_hashes": source_hashes,
        "implementation_hashes": implementation_hashes,
        "fixed_v54_addons": int(len(base_addons)),
        "fixed_v54_addons_preserved": bool(base_preserved),
        "candidate_audit": candidate_audit,
        "overlay_candidates": int(len(candidates)),
        "overlay_accepted": int(len(overlay_trades)),
        "decision_reason_counts": decisions["decision_reason"]
        .value_counts()
        .sort_index()
        .to_dict(),
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
        "# One-Trade-Per-Day Break Overlay V56 Result",
        "",
        f"Decision: `{decision}`",
        "",
        f"Fixed V54 add-ons preserved: **{len(base_addons)} / {len(base_addons)}**",
        f"Non-duplicated overlay accepted: **{len(overlay_trades)} / {len(candidates)}**",
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
            "This is exposed-history research. It grants no Python, EA, MT5, demo, live, or broker authority.",
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
        "schema_version": "xauusd_one_trade_per_day_break_overlay_v56_manifest",
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
