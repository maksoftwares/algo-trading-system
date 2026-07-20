from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

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


def digest_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(json_ready(payload), sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def main() -> int:
    config_path = ROOT / "config" / "one_trade_per_day_health_portfolio_v53.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    contract_path = output / config["outputs"]["contract_lock"]
    if not contract_path.is_file():
        raise FileNotFoundError("Lock the V53 contract before evaluation")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract["config_sha256"] != sha256_file(config_path):
        raise ValueError("V53 config changed after contract lock")
    source_hashes = verify_sources(REPO_ROOT, config["sources"])
    if source_hashes != contract["source_hashes"]:
        raise ValueError("V53 source set changed after contract lock")

    core = load_v50_core(REPO_ROOT, config)
    candidates = load_addon_candidates(REPO_ROOT, config)
    addons, decisions = govern_addons(candidates, core, config["account"])
    combined = combine_trades(core, addons)
    top = int(config["gates"]["top_winners_removed"])
    windows = rows_for_windows(core, addons, combined, config["windows"], top)
    gate = evaluate_gates(windows, config)
    decision = (
        "V53_ONE_TRADE_PER_DAY_HISTORICAL_GATE_PASS"
        if gate["passed"]
        else "V53_ONE_TRADE_PER_DAY_HISTORICAL_GATE_FAIL_TERMINAL"
    )

    result = {
        "schema_version": "xauusd_one_trade_per_day_health_portfolio_v53_result",
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
    result["result_sha256"] = digest_payload(result)

    output.mkdir(parents=True, exist_ok=True)
    decisions.to_parquet(output / config["outputs"]["decisions"], index=False)
    combined.to_parquet(output / config["outputs"]["trades"], index=False)
    windows.to_csv(
        output / config["outputs"]["windows"], index=False, lineterminator="\n"
    )
    result_path = output / config["outputs"]["result_json"]
    result_path.write_text(
        json.dumps(json_ready(result), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )

    lines = [
        "# One-Trade-Per-Day Health Portfolio V53 Result",
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
            "V50 is unchanged. V53 is exposed-history research only and grants no model, EA, demo, live, or broker authority.",
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
        "schema_version": "xauusd_one_trade_per_day_health_portfolio_v53_manifest",
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
