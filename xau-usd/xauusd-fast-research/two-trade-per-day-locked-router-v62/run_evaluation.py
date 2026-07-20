from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from src.evaluator import (  # noqa: E402
    evaluate_windows,
    gate_results,
    load_v61_router,
    verify_locked_development,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    config_path = ROOT / "config" / "two_trade_per_day_locked_router_v62.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_dir = ROOT / config["outputs"]["directory"]
    contract_path = output_dir / config["outputs"]["contract_lock"]
    if not contract_path.is_file():
        raise FileNotFoundError("Lock the V62 contract before evaluation")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract["config_sha256"] != sha256_file(config_path):
        raise ValueError("V62 config changed after contract lock")
    for source_id, source in config["sources"].items():
        actual = sha256_file(REPO_ROOT / source["path"])
        if actual != source["sha256"]:
            raise ValueError(f"Source hash mismatch for {source_id}: {actual}")

    router = load_v61_router(REPO_ROOT / config["sources"]["v61_router_module"]["path"])
    actions = router.enrich_actions(
        pd.read_parquet(REPO_ROOT / config["sources"]["action_ledger"]["path"])
    )
    v57 = pd.read_parquet(
        REPO_ROOT / config["sources"]["qualified_v57_candidates"]["path"]
    )
    frozen = pd.read_parquet(
        REPO_ROOT / config["sources"]["frozen_v59_trades"]["path"]
    )
    for column in ("signal_time", "entry_time", "exit_time"):
        frozen[column] = pd.to_datetime(frozen[column], utc=True)

    policy = config["locked_policy"]
    health = router.causal_state_health(
        actions,
        policy["state_schema"],
        int(policy["short_window"]),
        int(policy["long_window"]),
    )
    candidates = router.eligible_actions(
        health,
        router.qualified_event_keys(v57),
        float(policy["maximum_risk_usd"]),
        int(policy["short_window"]),
        int(policy["long_window"]),
        float(policy["minimum_profit_factor"]),
    )
    new_trades = router.govern_new_lane(candidates, frozen, config["account"])
    new_trades["sleeve_id"] = "V62_CAUSAL_UNUSED_EVENT"
    combined = pd.concat(
        [
            frozen.assign(portfolio_source="FROZEN_V59"),
            new_trades.assign(portfolio_source="NEW_V62"),
        ],
        ignore_index=True,
        sort=False,
    ).sort_values(["entry_time", "trade_id"], kind="mergesort")
    windows = evaluate_windows(router, new_trades, combined, config["windows"])
    verify_locked_development(windows, config["locked_development_evidence"])
    gates = gate_results(windows, config["gates"])
    passed = bool(all(item["passed"] for item in gates))

    output_dir.mkdir(parents=True, exist_ok=True)
    new_trades.to_parquet(output_dir / config["outputs"]["new_trades"], index=False)
    combined.to_parquet(output_dir / config["outputs"]["combined_trades"], index=False)
    windows.to_csv(output_dir / config["outputs"]["windows"], index=False)
    payload = {
        "schema_version": config["schema_version"],
        "contract_sha256": sha256_file(contract_path),
        "locked_policy": policy,
        "candidate_events": int(len(candidates)),
        "selected_new_trades": int(len(new_trades)),
        "frozen_v59_trades": int(len(frozen)),
        "frozen_v59_trades_preserved": bool(
            set(frozen["trade_id"].astype(str)).issubset(
                set(combined["trade_id"].astype(str))
            )
        ),
        "gate_results": gates,
        "passed": passed,
        "research_controls": config["research_controls"],
    }
    result_path = output_dir / config["outputs"]["result_json"]
    result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Two-Trade-Per-Day Locked Router V62",
        "",
        f"Decision: **{'PASS' if passed else 'REJECT'}**",
        "",
        windows.to_markdown(index=False),
        "",
        "This is historical research only. It is not demo or live authorization.",
    ]
    (output_dir / config["outputs"]["result_markdown"]).write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(windows.to_string(index=False))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
