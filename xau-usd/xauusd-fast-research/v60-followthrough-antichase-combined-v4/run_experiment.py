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

from src.policy import followthrough_mask


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_config() -> dict:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    for name, item in config["inputs"].items():
        actual = sha256_file(resolve(item["path"]))
        if actual != item["sha256"]:
            raise ValueError(f"Input identity changed: {name}: {actual}")
    return config


def build_historical_proposals(
    config: dict, utilities
) -> tuple[pd.DataFrame, pd.DataFrame]:
    v2 = json.loads(resolve(config["inputs"]["v2_result"]["path"]).read_text())
    proposal_rows = [
        {
            "trade_id": row["trade_id"],
            "entry_time_utc": row["entry_time_utc"],
            "source_id": row["source_id"],
            "proposal_rule": "V2_SOURCE_HEALTH",
        }
        for row in v2["veto_audit"]
        if bool(row["baseline_runtime_executed"])
    ]
    anti = pd.read_csv(resolve(config["inputs"]["antichase_historical_vetoes"]["path"]))
    features = pd.read_parquet(
        resolve(config["inputs"]["causal_feature_ledger"]["path"]),
        columns=["trade_id", "ret_4h", "ret_24h"],
    )
    if features["trade_id"].duplicated().any():
        raise ValueError("Causal feature ledger has duplicate trade IDs")
    anti = anti.merge(features, on="trade_id", how="left", validate="one_to_one")
    anti["followthrough_selected"] = followthrough_mask(
        anti, config["followthrough"]
    )
    for row in anti.loc[
        anti["baseline_runtime_executed"].astype(str).str.lower().eq("true")
        & anti["followthrough_selected"]
    ].to_dict("records"):
        proposal_rows.append(
            {
                "trade_id": row["trade_id"],
                "entry_time_utc": row["entry_time_utc"],
                "source_id": row["source_id"],
                "proposal_rule": "V57_WEAK_FOLLOWTHROUGH_ANTICHASE",
            }
        )
    proposals = pd.DataFrame(proposal_rows)
    budget = utilities.apply_source_day_budget(
        proposals, int(config["composition"]["maximum_vetoes_per_source_utc_day"])
    )
    return budget, anti


def comparative_gates(gates: dict) -> dict[str, bool]:
    return {
        name: bool(value)
        for name, value in gates.items()
        if name not in {"baseline_net_identity", "baseline_trade_identity"}
    }


def markdown(result: dict) -> str:
    base = result["baseline"]
    changed = result["challenger"]
    august = result["august_2026_through_25"]
    stress = result["cost_stress"]
    lines = [
        "# V60 Follow-Through Anti-Chase Combined V4 Result",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "| Scope | V60 net | Challenger net | V60 PF | Challenger PF | V60 closed DD | Challenger closed DD |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| Historical | ${base['net_pnl_usd']:.2f} | ${changed['net_pnl_usd']:.2f} | {base['profit_factor']:.3f} | {changed['profit_factor']:.3f} | ${base['maximum_lifetime_closed_drawdown_usd']:.2f} | ${changed['maximum_lifetime_closed_drawdown_usd']:.2f} |",
        f"| August through 25 | ${august['baseline_v60']['net_pnl_usd']:.2f} | ${august['challenger']['net_pnl_usd']:.2f} | {august['baseline_v60']['profit_factor']:.3f} | {august['challenger']['profit_factor']:.3f} | ${august['baseline_v60']['closed_drawdown_usd']:.2f} | ${august['challenger']['closed_drawdown_usd']:.2f} |",
        "",
        f"Trade retention: {result['composition_audit']['trade_retention']:.4%}",
        f"Selected historical vetoes: {result['composition_audit']['selected_vetoes']}",
        "",
        "## Cost stress",
        "",
        "| Extra cost/trade | Delta net | Challenger PF | Challenger closed DD | Comparative gates |",
        "|---:|---:|---:|---:|---|",
    ]
    for key in sorted(stress, key=float):
        item = stress[key]
        lines.append(
            f"| ${item['additional_cost_usd_per_trade']:.2f} | ${item['delta_net_pnl_usd']:.2f} | {item['challenger_profit_factor']:.3f} | ${item['challenger_closed_drawdown_usd']:.2f} | {'PASS' if item['all_comparative_gates_pass'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "All outcomes used here were exposed. This result cannot authorize deployment.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config = load_config()
    inputs = config["inputs"]
    utilities = load_module("v60_v3_budget_utilities", resolve(inputs["v3_experiment_source"]["path"]))
    evaluator = load_module("v60_v4_evaluator", resolve(inputs["shared_evaluator"]["path"]))
    anti_module = load_module("v60_v4_crossfeed", resolve(inputs["antichase_experiment_source"]["path"]))
    budget, anti_history = build_historical_proposals(config, utilities)
    selected_ids = set(budget.loc[budget["selected_veto"], "trade_id"].astype(str))

    base_path = resolve(inputs["base_challenger_config"]["path"])
    base = json.loads(base_path.read_text(encoding="utf-8"))
    decisions = pd.read_parquet(resolve(inputs["causal_feature_ledger"]["path"]), columns=["trade_id"])
    decisions["rank"] = decisions["trade_id"].astype(str).map(
        lambda trade_id: 0.0 if trade_id in selected_ids else 1.0
    )

    with tempfile.TemporaryDirectory(prefix="v60-followthrough-v4-") as temporary:
        temporary = Path(temporary)
        decisions_path = temporary / "POLICY_DECISIONS.parquet"
        decisions.to_parquet(decisions_path, index=False)
        replay_config = deepcopy(base)
        replay_config["schema_version"] = config["schema_version"]
        replay_config["report_title"] = "V60 Follow-Through Anti-Chase Combined V4"
        replay_config["inputs"]["causal_rank_ledger"] = {
            "path": str(decisions_path),
            "sha256": sha256_file(decisions_path),
        }
        replay_config["policy"] = {
            "source_id": "*",
            "state_condition": "CONSECUTIVE_LOSSES",
            "minimum_consecutive_losses": 0,
            "minimum_prior_source_closed_trades": 0,
            "lookback_closed_trades": 20,
            "maximum_causal_rank_exclusive": 0.5,
            "missing_rank_action": "RETAIN",
        }
        replay_config["gates"]["minimum_veto_cohort_rows"] = int(
            config["acceptance"]["minimum_executed_vetoes"]
        )
        replay_path = temporary / "challenger.json"
        replay_path.write_text(json.dumps(replay_config), encoding="utf-8")
        historical, annual, vetoes = evaluator.run(replay_path)
        cost_stress = {}
        for cost in config["acceptance"]["additional_cost_stress_usd_per_trade"]:
            stressed, _, _ = evaluator.run(
                replay_path, additional_cost_usd_per_trade=float(cost)
            )
            gates = comparative_gates(stressed["gates"])
            cost_stress[str(cost)] = {
                "additional_cost_usd_per_trade": float(cost),
                "baseline_net_pnl_usd": stressed["baseline"]["net_pnl_usd"],
                "challenger_net_pnl_usd": stressed["challenger"]["net_pnl_usd"],
                "delta_net_pnl_usd": stressed["delta"]["net_pnl_usd"],
                "baseline_profit_factor": stressed["baseline"]["profit_factor"],
                "challenger_profit_factor": stressed["challenger"]["profit_factor"],
                "baseline_closed_drawdown_usd": stressed["baseline"]["maximum_lifetime_closed_drawdown_usd"],
                "challenger_closed_drawdown_usd": stressed["challenger"]["maximum_lifetime_closed_drawdown_usd"],
                "baseline_equity_drawdown_usd": stressed["baseline"]["maximum_lifetime_equity_drawdown_usd"],
                "challenger_equity_drawdown_usd": stressed["challenger"]["maximum_lifetime_equity_drawdown_usd"],
                "comparative_gates": gates,
                "all_comparative_gates_pass": bool(all(gates.values())),
            }

    august_audit = pd.read_csv(resolve(inputs["antichase_august_audit"]["path"]))
    original_anti = august_audit["would_veto"].astype(str).str.lower().eq("true")
    august_audit["followthrough_selected"] = followthrough_mask(
        august_audit, config["followthrough"]
    )
    august_audit["would_veto"] = original_anti & august_audit["followthrough_selected"]
    august, august_rows = utilities.august_comparison(
        pd.read_csv(resolve(inputs["exposed_broker_audit"]["path"])),
        august_audit,
        int(config["composition"]["maximum_vetoes_per_source_utc_day"]),
    )
    executed_ids = set(
        vetoes.loc[
            vetoes["baseline_runtime_executed"].astype(str).str.lower().eq("true"),
            "trade_id",
        ].astype(str)
    )
    crossfeed = anti_module.crossfeed_comparison(
        pd.read_csv(resolve(inputs["crossfeed_priced_runtime"]["path"]), low_memory=False),
        executed_ids,
    )
    baseline_trades = int(historical["baseline"]["trades_closed"])
    challenger_trades = int(historical["challenger"]["trades_closed"])
    composition_audit = {
        "raw_proposals": int(len(budget)),
        "selected_vetoes": int(budget["selected_veto"].sum()),
        "budget_retained_proposals": int((~budget["selected_veto"]).sum()),
        "trade_retention": challenger_trades / baseline_trades,
        "historical_antichase_proposals_before_followthrough": int(len(anti_history)),
        "historical_antichase_proposals_after_followthrough": int(anti_history["followthrough_selected"].sum()),
    }
    august_gates = {
        "positive_net_pnl": august["challenger"]["net_pnl_usd"]
        > float(config["acceptance"]["minimum_august_net_pnl_usd_exclusive"]),
        "net_above_v60": august["challenger"]["net_pnl_usd"] > august["baseline_v60"]["net_pnl_usd"],
        "profit_factor_above_v60": august["challenger"]["profit_factor"] > august["baseline_v60"]["profit_factor"],
        "closed_drawdown_not_worse": august["challenger"]["closed_drawdown_usd"] <= august["baseline_v60"]["closed_drawdown_usd"],
    }
    gates = {
        "nominal_historical_gates": bool(all(historical["gates"].values())),
        "locked_trade_retention": composition_audit["trade_retention"] >= float(config["acceptance"]["minimum_trade_retention_fraction"]),
        "cost_stress_comparative_gates": all(item["all_comparative_gates_pass"] for item in cost_stress.values()),
        "august_diagnostic": bool(all(august_gates.values())),
        "crossfeed_delta_positive": crossfeed["delta_net_pnl_usd"] > 0.0,
        "crossfeed_every_year_nonnegative": bool(crossfeed["every_year_nonnegative"]),
        "clean_forward_evidence": False,
    }
    retrospective_pass = all(value for name, value in gates.items() if name != "clean_forward_evidence")
    result = historical
    result.update(
        {
            "schema_version": config["schema_version"] + "_result",
            "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "decision": "HISTORICAL_CHALLENGER_PASSES_PROSPECTIVE_CONFIRMATION_REQUIRED" if retrospective_pass else "KEEP_DEPLOYED_V60",
            "deployment_authorized": False,
            "broker_action_authorized": False,
            "evidence_status": config["evidence_status"],
            "followthrough": config["followthrough"],
            "composition": config["composition"],
            "composition_audit": composition_audit,
            "august_2026_through_25": august,
            "august_gates": august_gates,
            "dukascopy_crossfeed": crossfeed,
            "cost_stress": cost_stress,
            "combined_gates": gates,
            "limitations": [
                "The follow-through refinement was nominated after historical and August outcomes were exposed.",
                "The independent price path reuses Capital candidate timing and is not an independent strategy replay.",
                "Clean forward evidence is mandatory before deployment.",
            ],
        }
    )
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUTPUTS / "RESULT.md").write_text(markdown(result), encoding="utf-8")
    annual.to_csv(OUTPUTS / "ANNUAL.csv", index=False, lineterminator="\n")
    vetoes.to_csv(OUTPUTS / "HISTORICAL_VETOES.csv", index=False, lineterminator="\n")
    budget.to_csv(OUTPUTS / "PROPOSAL_BUDGET_AUDIT.csv", index=False, lineterminator="\n")
    anti_history.to_csv(OUTPUTS / "FOLLOWTHROUGH_AUDIT.csv", index=False, lineterminator="\n")
    august_rows.to_csv(OUTPUTS / "AUGUST_2026_TRADE_AUDIT.csv", index=False, lineterminator="\n")
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "delta_net_pnl_usd": result["delta"]["net_pnl_usd"],
                "trade_retention": composition_audit["trade_retention"],
                "august_delta_net_pnl_usd": august["delta_net_pnl_usd"],
                "gates": gates,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
