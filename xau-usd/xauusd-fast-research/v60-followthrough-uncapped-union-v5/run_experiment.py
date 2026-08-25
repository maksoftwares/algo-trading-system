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


def closed_metrics(values: pd.Series) -> dict:
    pnl = pd.to_numeric(values, errors="raise").astype(float)
    wins = pnl.loc[pnl.gt(0.0)]
    losses = pnl.loc[pnl.lt(0.0)]
    gross_profit = float(wins.sum())
    gross_loss = -float(losses.sum())
    equity = pd.Series([0.0, *pnl.cumsum().tolist()])
    drawdown = equity.cummax() - equity
    return {
        "trades": int(len(pnl)),
        "wins": int(len(wins)),
        "losses": int(len(losses)),
        "net_pnl_usd": float(pnl.sum()),
        "profit_factor": gross_profit / gross_loss if gross_loss else None,
        "win_rate": float(len(wins) / len(pnl)) if len(pnl) else None,
        "closed_drawdown_usd": float(drawdown.max()),
    }


def comparative_gates(gates: dict) -> dict[str, bool]:
    return {
        name: bool(value)
        for name, value in gates.items()
        if name not in {"baseline_net_identity", "baseline_trade_identity"}
    }


def main() -> int:
    config = load_config()
    inputs = config["inputs"]
    policy = load_module("v60_v5_followthrough", resolve(inputs["followthrough_policy_source"]["path"]))
    evaluator = load_module("v60_v5_evaluator", resolve(inputs["shared_evaluator"]["path"]))
    anti_module = load_module("v60_v5_crossfeed", resolve(inputs["antichase_experiment_source"]["path"]))

    v2 = json.loads(resolve(inputs["v2_result"]["path"]).read_text(encoding="utf-8"))
    proposals = [
        {
            "trade_id": row["trade_id"],
            "entry_time_utc": row["entry_time_utc"],
            "source_id": row["source_id"],
            "proposal_rule": "V2_SOURCE_HEALTH",
        }
        for row in v2["veto_audit"]
        if bool(row["baseline_runtime_executed"])
    ]
    features = pd.read_parquet(resolve(inputs["causal_feature_ledger"]["path"]))
    if features["trade_id"].duplicated().any():
        raise ValueError("Causal feature ledger has duplicate trade IDs")
    anti_history = pd.read_csv(resolve(inputs["antichase_historical_vetoes"]["path"]))
    anti_history = anti_history.merge(
        features[["trade_id", "ret_4h", "ret_24h"]],
        on="trade_id",
        how="left",
        validate="one_to_one",
    )
    anti_history["followthrough_selected"] = policy.followthrough_mask(
        anti_history, config["followthrough"]
    )
    for row in anti_history.loc[
        anti_history["baseline_runtime_executed"].astype(str).str.lower().eq("true")
        & anti_history["followthrough_selected"]
    ].to_dict("records"):
        proposals.append(
            {
                "trade_id": row["trade_id"],
                "entry_time_utc": row["entry_time_utc"],
                "source_id": row["source_id"],
                "proposal_rule": "V57_WEAK_FOLLOWTHROUGH_ANTICHASE",
            }
        )
    proposal_audit = pd.DataFrame(proposals)
    if proposal_audit[["trade_id", "entry_time_utc", "source_id"]].isna().any().any():
        raise ValueError("Proposal metadata is incomplete")
    proposal_audit = (
        proposal_audit.groupby(["trade_id", "entry_time_utc", "source_id"], as_index=False)
        .agg(proposal_rule=("proposal_rule", lambda value: "+".join(sorted(set(value)))))
        .sort_values(["entry_time_utc", "trade_id"], kind="stable")
    )
    selected_ids = set(proposal_audit["trade_id"].astype(str))
    decisions = features[["trade_id"]].copy()
    decisions["rank"] = decisions["trade_id"].astype(str).map(
        lambda trade_id: 0.0 if trade_id in selected_ids else 1.0
    )

    base = json.loads(resolve(inputs["base_challenger_config"]["path"]).read_text())
    with tempfile.TemporaryDirectory(prefix="v60-followthrough-v5-") as temporary:
        temporary = Path(temporary)
        decisions_path = temporary / "POLICY_DECISIONS.parquet"
        decisions.to_parquet(decisions_path, index=False)
        replay_config = deepcopy(base)
        replay_config["schema_version"] = config["schema_version"]
        replay_config["report_title"] = "V60 Follow-Through Uncapped Union V5"
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
        replay_config["gates"]["minimum_veto_cohort_rows"] = int(config["acceptance"]["minimum_executed_vetoes"])
        replay_path = temporary / "challenger.json"
        replay_path.write_text(json.dumps(replay_config), encoding="utf-8")
        historical, annual, vetoes = evaluator.run(replay_path)
        cost_stress = {}
        for cost in config["acceptance"]["additional_cost_stress_usd_per_trade"]:
            stressed, _, _ = evaluator.run(replay_path, additional_cost_usd_per_trade=float(cost))
            stress_gates = comparative_gates(stressed["gates"])
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
                "comparative_gates": stress_gates,
                "all_comparative_gates_pass": bool(all(stress_gates.values())),
            }

    broker = pd.read_csv(resolve(inputs["exposed_broker_audit"]["path"]))
    broker = broker.loc[
        broker["entry_time_utc"].astype(str).str.startswith("2026-08-")
        & broker["baseline_executed"].astype(str).str.lower().eq("true")
        & broker["broker_outcome_resolved"].astype(str).str.lower().eq("true")
    ].copy()
    august_anti = pd.read_csv(resolve(inputs["antichase_august_audit"]["path"]))
    original_anti = august_anti["would_veto"].astype(str).str.lower().eq("true")
    august_anti["followthrough_selected"] = policy.followthrough_mask(
        august_anti, config["followthrough"]
    )
    august_anti["refined_antichase_proposal"] = original_anti & august_anti["followthrough_selected"]
    broker = broker.merge(
        august_anti[["candidate_id", "refined_antichase_proposal"]],
        on="candidate_id",
        how="left",
        validate="one_to_one",
    )
    broker["v2_proposal"] = broker["would_veto"].astype(str).str.lower().eq("true")
    broker["refined_antichase_proposal"] = broker["refined_antichase_proposal"].fillna(False)
    broker["combined_veto"] = broker["v2_proposal"] | broker["refined_antichase_proposal"]
    broker = broker.sort_values(["broker_exit_time_utc", "candidate_id"], kind="stable")
    august = {
        "baseline_v60": closed_metrics(broker["broker_pnl_usd"]),
        "challenger": closed_metrics(broker.loc[~broker["combined_veto"], "broker_pnl_usd"]),
        "veto_cohort": closed_metrics(broker.loc[broker["combined_veto"], "broker_pnl_usd"]),
    }
    august["delta_net_pnl_usd"] = august["challenger"]["net_pnl_usd"] - august["baseline_v60"]["net_pnl_usd"]
    august["delta_closed_drawdown_usd"] = august["challenger"]["closed_drawdown_usd"] - august["baseline_v60"]["closed_drawdown_usd"]

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
    retention = historical["challenger"]["trades_closed"] / historical["baseline"]["trades_closed"]
    august_gates = {
        "positive_net_pnl": august["challenger"]["net_pnl_usd"] > float(config["acceptance"]["minimum_august_net_pnl_usd_exclusive"]),
        "net_above_v60": august["challenger"]["net_pnl_usd"] > august["baseline_v60"]["net_pnl_usd"],
        "profit_factor_above_v60": august["challenger"]["profit_factor"] > august["baseline_v60"]["profit_factor"],
        "closed_drawdown_not_worse": august["challenger"]["closed_drawdown_usd"] <= august["baseline_v60"]["closed_drawdown_usd"],
    }
    gates = {
        "nominal_historical_gates": bool(all(historical["gates"].values())),
        "locked_trade_retention": retention >= float(config["acceptance"]["minimum_trade_retention_fraction"]),
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
            "composition_audit": {
                "proposal_count": int(len(proposal_audit)),
                "executed_vetoes": int(historical["baseline_executed_veto_count"]),
                "trade_retention": retention,
            },
            "august_2026_through_25": august,
            "august_gates": august_gates,
            "dukascopy_crossfeed": crossfeed,
            "cost_stress": cost_stress,
            "combined_gates": gates,
            "limitations": [
                "All historical and August outcomes were exposed before nomination.",
                "The follow-through threshold was selected post-hoc.",
                "Clean forward evidence is mandatory before deployment.",
            ],
        }
    )
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    annual.to_csv(OUTPUTS / "ANNUAL.csv", index=False, lineterminator="\n")
    vetoes.to_csv(OUTPUTS / "HISTORICAL_VETOES.csv", index=False, lineterminator="\n")
    proposal_audit.to_csv(OUTPUTS / "PROPOSAL_AUDIT.csv", index=False, lineterminator="\n")
    anti_history.to_csv(OUTPUTS / "FOLLOWTHROUGH_AUDIT.csv", index=False, lineterminator="\n")
    broker.to_csv(OUTPUTS / "AUGUST_2026_TRADE_AUDIT.csv", index=False, lineterminator="\n")
    (OUTPUTS / "RESULT.md").write_text(
        "\n".join(
            [
                "# V60 Follow-Through Uncapped Union V5 Result",
                "",
                f"Decision: **{result['decision']}**",
                "",
                f"Historical: {historical['challenger']['trades_closed']} trades, ${historical['challenger']['net_pnl_usd']:.2f} net, PF {historical['challenger']['profit_factor']:.3f}, closed DD ${historical['challenger']['maximum_lifetime_closed_drawdown_usd']:.2f}.",
                f"August through 25: ${august['challenger']['net_pnl_usd']:.2f} net, PF {august['challenger']['profit_factor']:.3f}, closed DD ${august['challenger']['closed_drawdown_usd']:.2f}.",
                f"Trade retention: {retention:.4%}.",
                "",
                "This is exposed retrospective evidence and cannot authorize deployment.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"decision": result["decision"], "delta_net_pnl_usd": historical["delta"]["net_pnl_usd"], "trade_retention": retention, "august_delta_net_pnl_usd": august["delta_net_pnl_usd"], "gates": gates}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
