from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG = ROOT / "config" / "experiment.json"
OUTPUTS = ROOT / "outputs"
sys.path.insert(0, str(ROOT))

from src.experiment import (
    august_comparison,
    crossfeed_comparison,
    load_locked_config,
    policy_mask,
    resolve,
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    config = load_locked_config(CONFIG, REPO_ROOT)
    inputs = config["inputs"]
    evaluator = load_module(
        "v60_antichase_evaluator",
        resolve(REPO_ROOT, inputs["shared_evaluator"]["path"]),
    )
    feature_ledger = pd.read_parquet(
        resolve(REPO_ROOT, inputs["causal_feature_ledger"]["path"])
    )
    if feature_ledger["trade_id"].duplicated().any():
        raise ValueError("Causal feature ledger has duplicate trade IDs")
    selected = policy_mask(feature_ledger, config["rule"])
    derived = pd.DataFrame(
        {
            "trade_id": feature_ledger["trade_id"],
            "rank": (~selected).astype(float),
        }
    )
    with tempfile.TemporaryDirectory(prefix="v60-antichase-v1-") as temporary:
        temporary = Path(temporary)
        derived_path = temporary / "POLICY_DECISIONS.parquet"
        derived.to_parquet(derived_path, index=False)
        base = json.loads(
            resolve(REPO_ROOT, inputs["base_challenger_config"]["path"]).read_text(
                encoding="utf-8"
            )
        )
        replay_config = deepcopy(base)
        replay_config["schema_version"] = config["schema_version"]
        replay_config["report_title"] = "V60 V57 Volatility Anti-Chase V1"
        replay_config["inputs"]["causal_rank_ledger"] = {
            "path": str(derived_path),
            "sha256": hashlib.sha256(derived_path.read_bytes()).hexdigest(),
        }
        replay_config["policy"] = {
            "source_id": config["rule"]["source_id"],
            "state_condition": "CONSECUTIVE_LOSSES",
            "minimum_consecutive_losses": 0,
            "minimum_prior_source_closed_trades": config["rule"][
                "minimum_prior_source_closed_trades"
            ],
            "lookback_closed_trades": 20,
            "maximum_causal_rank_exclusive": 0.5,
            "missing_rank_action": "RETAIN",
        }
        replay_config["gates"]["minimum_veto_cohort_rows"] = 1
        replay_path = temporary / "challenger.json"
        replay_path.write_text(json.dumps(replay_config), encoding="utf-8")
        historical, annual, vetoes = evaluator.run(replay_path)

    broker = pd.read_csv(
        resolve(REPO_ROOT, inputs["exposed_broker_audit"]["path"])
    )
    august_features = pd.read_csv(
        resolve(REPO_ROOT, inputs["august_causal_features"]["path"])
    )
    august, august_rows = august_comparison(
        broker, august_features, config["rule"]
    )
    executed_veto_ids = set(
        vetoes.loc[
            vetoes["baseline_runtime_executed"].astype(str).str.lower().eq("true"),
            "trade_id",
        ].astype(str)
    )
    crossfeed = crossfeed_comparison(
        pd.read_csv(
            resolve(REPO_ROOT, inputs["crossfeed_priced_runtime"]["path"]),
            low_memory=False,
        ),
        executed_veto_ids,
    )
    preservation = bool(all(historical["gates"].values()))
    august_gates = {
        "positive_challenger_net_pnl": august["challenger"]["net_pnl_usd"]
        > float(config["acceptance"]["minimum_august_net_pnl_usd_exclusive"]),
        "net_pnl_above_v60": august["challenger"]["net_pnl_usd"]
        > august["baseline_v60"]["net_pnl_usd"],
        "profit_factor_above_v60": float(
            august["challenger"]["profit_factor"] or 0.0
        )
        > float(august["baseline_v60"]["profit_factor"] or 0.0),
        "closed_drawdown_not_worse": august["challenger"][
            "closed_drawdown_usd"
        ]
        <= august["baseline_v60"]["closed_drawdown_usd"],
    }
    proof_gates = {
        "historical_preservation": preservation,
        "august_stress_diagnostic": bool(all(august_gates.values())),
        "crossfeed_mechanism_support": crossfeed["delta_net_pnl_usd"] > 0.0
        and float(crossfeed["veto_cohort"]["profit_factor"] or 0.0) < 0.8
        and bool(crossfeed["every_year_nonnegative"]),
        "minimum_pre_august_executed_vetoes": historical[
            "baseline_executed_veto_count"
        ]
        >= int(
            config["acceptance"][
                "minimum_historical_executed_vetoes_for_deployment"
            ]
        ),
        "clean_forward_evidence": False,
    }
    promising = proof_gates["historical_preservation"] and proof_gates[
        "august_stress_diagnostic"
    ]
    result = {
        "schema_version": config["schema_version"] + "_result",
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "decision": (
            "PROMISING_POSTHOC_FORWARD_CONFIRMATION_REQUIRED"
            if promising
            else "REJECT"
        ),
        "deployment_authorized": False,
        "broker_action_authorized": False,
        "evidence_status": config["evidence_status"],
        "rule": config["rule"],
        "selection_disclosure": {
            "variants_screened": len(config["screened_variants"]),
            "august_outcomes_exposed_before_nomination": True,
        },
        "historical": historical,
        "august_2026_through_25": august,
        "dukascopy_crossfeed": crossfeed,
        "august_gates": august_gates,
        "proof_gates": proof_gates,
        "limitations": [
            "Only two pre-August baseline executions satisfy the frozen rule.",
            "August outcomes were exposed before the rule was nominated.",
            "The result cannot authorize deployment without clean forward evidence.",
        ],
    }
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    annual.to_csv(OUTPUTS / "ANNUAL.csv", index=False, lineterminator="\n")
    vetoes.to_csv(OUTPUTS / "HISTORICAL_VETOES.csv", index=False, lineterminator="\n")
    august_rows.to_csv(
        OUTPUTS / "AUGUST_2026_TRADE_AUDIT.csv", index=False, lineterminator="\n"
    )
    base = historical["baseline"]
    changed = historical["challenger"]
    aug_base = august["baseline_v60"]
    aug_changed = august["challenger"]
    lines = [
        "# V60 V57 Volatility Anti-Chase V1",
        "",
        f"Decision: **{result['decision']}**. Deployment is unauthorized.",
        "",
        "| Metric | V60 history | Challenger history | Change |",
        "|---|---:|---:|---:|",
        f"| Trades | {base['trades_closed']} | {changed['trades_closed']} | {historical['delta']['trades']:+d} |",
        f"| Net P/L | ${base['net_pnl_usd']:.2f} | ${changed['net_pnl_usd']:.2f} | ${historical['delta']['net_pnl_usd']:+.2f} |",
        f"| PF | {base['profit_factor']:.4f} | {changed['profit_factor']:.4f} | {historical['delta']['profit_factor']:+.4f} |",
        f"| Closed DD | ${base['maximum_lifetime_closed_drawdown_usd']:.2f} | ${changed['maximum_lifetime_closed_drawdown_usd']:.2f} | ${historical['delta']['closed_drawdown_usd']:+.2f} |",
        f"| Equity DD | ${base['maximum_lifetime_equity_drawdown_usd']:.2f} | ${changed['maximum_lifetime_equity_drawdown_usd']:.2f} | ${historical['delta']['equity_drawdown_usd']:+.2f} |",
        "",
        "| Metric | V60 August | Challenger August | Change |",
        "|---|---:|---:|---:|",
        f"| Trades | {aug_base['trades']} | {aug_changed['trades']} | {aug_changed['trades'] - aug_base['trades']:+d} |",
        f"| Net P/L | ${aug_base['net_pnl_usd']:.2f} | ${aug_changed['net_pnl_usd']:.2f} | ${august['delta_net_pnl_usd']:+.2f} |",
        f"| PF | {aug_base['profit_factor']:.4f} | {aug_changed['profit_factor']:.4f} |  |",
        f"| Win rate | {100*aug_base['win_rate']:.2f}% | {100*aug_changed['win_rate']:.2f}% |  |",
        f"| Closed DD | ${aug_base['closed_drawdown_usd']:.2f} | ${aug_changed['closed_drawdown_usd']:.2f} | ${august['delta_closed_drawdown_usd']:+.2f} |",
        "",
        f"Dukascopy same-timing check: {crossfeed['covered_vetoes']} covered vetoes, "
        f"veto-cohort P/L ${crossfeed['veto_cohort']['net_pnl_usd']:.2f}, "
        f"PF {crossfeed['veto_cohort']['profit_factor']:.4f}, challenger change "
        f"${crossfeed['delta_net_pnl_usd']:+.2f}.",
        "",
        "The rule preserves every frozen historical gate and makes exposed August positive, but only two pre-August executions support it. Clean forward proof is mandatory.",
    ]
    (OUTPUTS / "RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "historical_delta_net_pnl_usd": historical["delta"][
                    "net_pnl_usd"
                ],
                "august_delta_net_pnl_usd": august["delta_net_pnl_usd"],
                "proof_gates": proof_gates,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
