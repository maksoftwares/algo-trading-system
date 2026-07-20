from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
V53_SRC = ROOT.parent / "one-trade-per-day-health-portfolio-v53" / "src"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(V53_SRC))

from policy import resolve_config  # noqa: E402
from portfolio import (  # noqa: E402
    combine_trades,
    evaluate_gates,
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
    config_path = ROOT / "config" / "one_trade_per_day_health_portfolio_v54.json"
    config, overlay = resolve_config(REPO_ROOT, config_path)
    base_path = REPO_ROOT / overlay["base_config_path"]
    output = ROOT / config["outputs"]["directory"]
    contract_path = output / config["outputs"]["contract_lock"]
    if not contract_path.is_file():
        raise FileNotFoundError("Lock the V54 contract before evaluation")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract["overlay_config_sha256"] != sha256_file(config_path):
        raise ValueError("V54 overlay changed after contract lock")
    if contract["base_config_sha256"] != sha256_file(base_path):
        raise ValueError("V53 base changed after V54 contract lock")
    source_hashes = verify_sources(REPO_ROOT, config["sources"])
    if source_hashes != contract["source_hashes"]:
        raise ValueError("V54 sources changed after contract lock")

    core = load_v50_core(REPO_ROOT, config)
    candidates = load_addon_candidates(REPO_ROOT, config)
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
        "V54_ONE_TRADE_PER_DAY_HISTORICAL_GATE_PASS"
        if gate["passed"]
        else "V54_ONE_TRADE_PER_DAY_HISTORICAL_GATE_FAIL_TERMINAL"
    )
    result = {
        "schema_version": "xauusd_one_trade_per_day_health_portfolio_v54_result",
        "decision": decision,
        "contract_sha256": contract["contract_sha256"],
        "source_hashes": source_hashes,
        "candidate_addons": int(len(candidates)),
        "accepted_addons": int(len(addons)),
        "decision_reason_counts": decisions["decision_reason"]
        .value_counts()
        .sort_index()
        .to_dict(),
        "gate": gate,
        "windows": windows.to_dict(orient="records"),
        "research_controls": config["research_controls"],
    }
    result["result_sha256"] = payload_sha256(result)

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
        "# One-Trade-Per-Day Health Portfolio V54 Result",
        "",
        f"Decision: `{decision}`",
        "",
        f"Accepted add-ons: **{len(addons)} / {len(candidates)}**",
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
            "V50 and every add-on signal are unchanged. This is exposed-history research only and grants no execution authority.",
        ]
    )
    (output / config["outputs"]["result_markdown"]).write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    artifacts = {}
    for key in (
        "contract_lock",
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
        "schema_version": "xauusd_one_trade_per_day_health_portfolio_v54_manifest",
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
