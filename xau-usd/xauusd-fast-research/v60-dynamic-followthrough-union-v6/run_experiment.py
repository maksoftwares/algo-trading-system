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

from src.scenario import combined_challenger_class


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


def feature_map(frame: pd.DataFrame) -> dict[str, dict]:
    if frame["trade_id"].duplicated().any():
        raise ValueError("Causal feature ledger has duplicate trade IDs")
    return {
        str(row["trade_id"]): row
        for row in frame.to_dict("records")
    }


def comparative_gates(gates: dict) -> dict[str, bool]:
    return {
        name: bool(value)
        for name, value in gates.items()
        if name not in {"baseline_net_identity", "baseline_trade_identity"}
    }


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


def main() -> int:
    config = load_config()
    inputs = config["inputs"]
    evaluator = load_module(
        "v60_v6_dynamic_evaluator", resolve(inputs["shared_evaluator"]["path"])
    )
    anti_module = load_module(
        "v60_v6_crossfeed", resolve(inputs["antichase_experiment_source"]["path"])
    )
    features = pd.read_parquet(resolve(inputs["causal_feature_ledger"]["path"]))
    features_by_trade = feature_map(features)
    original_factory = evaluator.challenger_class
    evaluator.challenger_class = lambda replay: combined_challenger_class(
        replay, evaluator, features_by_trade, config["anti_chase"]
    )

    base = json.loads(resolve(inputs["base_challenger_config"]["path"]).read_text())
    with tempfile.TemporaryDirectory(prefix="v60-dynamic-union-v6-") as temporary:
        replay_config = deepcopy(base)
        for name, value in config.get("v2_policy_overrides", {}).items():
            if name not in replay_config["policy"]:
                raise ValueError(f"Unknown V2 policy override: {name}")
            replay_config["policy"][name] = value
        replay_config["schema_version"] = config["schema_version"]
        replay_config["report_title"] = "V60 Dynamic Follow-Through Union V6"
        replay_config["gates"]["minimum_veto_cohort_rows"] = int(
            config["acceptance"]["minimum_executed_vetoes"]
        )
        replay_path = Path(temporary) / "challenger.json"
        replay_path.write_text(json.dumps(replay_config), encoding="utf-8")
        historical, annual, vetoes = evaluator.run(replay_path)
        cost_stress = {}
        for cost in config["acceptance"]["additional_cost_stress_usd_per_trade"]:
            stressed, stressed_annual, stressed_vetoes = evaluator.run(
                replay_path, additional_cost_usd_per_trade=float(cost)
            )
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
                "executed_vetoes": int(stressed["baseline_executed_veto_count"]),
                "veto_trade_ids": sorted(
                    stressed_vetoes.loc[
                        stressed_vetoes["baseline_runtime_executed"].astype(str).str.lower().eq("true"),
                        "trade_id",
                    ].astype(str)
                ),
                "annual": stressed_annual.to_dict("records"),
                "windows": stressed["windows"],
                "comparative_gates": stress_gates,
                "all_comparative_gates_pass": bool(all(stress_gates.values())),
            }
    evaluator.challenger_class = original_factory

    broker = pd.read_csv(resolve(inputs["exposed_broker_audit"]["path"]))
    broker = broker.loc[
        broker["entry_time_utc"].astype(str).str.startswith("2026-08-")
        & broker["baseline_executed"].astype(str).str.lower().eq("true")
        & broker["broker_outcome_resolved"].astype(str).str.lower().eq("true")
    ].copy()
    anti_audit = pd.read_csv(resolve(inputs["antichase_august_audit"]["path"]))
    anti_base = anti_audit["would_veto"].astype(str).str.lower().eq("true")
    ret_4h = pd.to_numeric(anti_audit["ret_4h"], errors="coerce")
    ret_24h = pd.to_numeric(anti_audit["ret_24h"], errors="coerce")
    followthrough = (
        ret_24h.gt(float(config["anti_chase"]["minimum_ret_24h_exclusive"]))
        & (ret_4h / ret_24h).lt(
            float(config["anti_chase"]["maximum_ret_4h_to_ret_24h_exclusive"])
        )
    )
    anti_audit["refined_antichase_proposal"] = anti_base & followthrough
    broker = broker.merge(
        anti_audit[["candidate_id", "refined_antichase_proposal"]],
        on="candidate_id",
        how="left",
        validate="one_to_one",
    )
    broker["v2_baseline_path_proposal"] = broker["would_veto"].astype(str).str.lower().eq("true")
    broker["refined_antichase_proposal"] = broker["refined_antichase_proposal"].fillna(False)
    broker["combined_veto"] = broker["v2_baseline_path_proposal"] | broker["refined_antichase_proposal"]
    broker = broker.sort_values(["broker_exit_time_utc", "candidate_id"], kind="stable")
    august = {
        "baseline_v60": closed_metrics(broker["broker_pnl_usd"]),
        "challenger": closed_metrics(broker.loc[~broker["combined_veto"], "broker_pnl_usd"]),
        "veto_cohort": closed_metrics(broker.loc[broker["combined_veto"], "broker_pnl_usd"]),
        "path_coupling_status": "V2_BASELINE_PATH_APPROXIMATION_NO_V2_PROPOSALS",
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
            "dynamic_policy": {
                "v2_policy": replay_config["policy"],
                "anti_chase": config["anti_chase"],
                "state_recomputed_per_scenario": True,
            },
            "composition_audit": {
                "executed_vetoes": int(historical["baseline_executed_veto_count"]),
                "trade_retention": retention,
                "proposal_rule_counts": vetoes["proposal_rule"].value_counts().to_dict(),
            },
            "august_2026_through_25": august,
            "august_gates": august_gates,
            "dukascopy_crossfeed": crossfeed,
            "cost_stress": cost_stress,
            "combined_gates": gates,
            "limitations": [
                "All historical and August outcomes were exposed before nomination.",
                "The follow-through threshold was selected post-hoc.",
                "August uses the observed V2 baseline path; clean forward combined-state replay is still required.",
                "Clean forward evidence is mandatory before deployment.",
            ],
        }
    )
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    annual.to_csv(OUTPUTS / "ANNUAL.csv", index=False, lineterminator="\n")
    vetoes.to_csv(OUTPUTS / "HISTORICAL_VETOES.csv", index=False, lineterminator="\n")
    broker.to_csv(OUTPUTS / "AUGUST_2026_TRADE_AUDIT.csv", index=False, lineterminator="\n")
    (OUTPUTS / "RESULT.md").write_text(
        "\n".join(
            [
                "# V60 Dynamic Follow-Through Union V6 Result",
                "",
                f"Decision: **{result['decision']}**",
                "",
                f"Historical: {historical['challenger']['trades_closed']} trades, ${historical['challenger']['net_pnl_usd']:.2f} net, PF {historical['challenger']['profit_factor']:.3f}, closed DD ${historical['challenger']['maximum_lifetime_closed_drawdown_usd']:.2f}, equity DD ${historical['challenger']['maximum_lifetime_equity_drawdown_usd']:.2f}.",
                f"August through 25: ${august['challenger']['net_pnl_usd']:.2f} net, PF {august['challenger']['profit_factor']:.3f}, closed DD ${august['challenger']['closed_drawdown_usd']:.2f}.",
                f"Trade retention: {retention:.4%}.",
                "",
                "Dynamic source health is recomputed independently in every cost scenario.",
                "This exposed retrospective result cannot authorize deployment.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"decision": result["decision"], "delta_net_pnl_usd": historical["delta"]["net_pnl_usd"], "trade_retention": retention, "august_delta_net_pnl_usd": august["delta_net_pnl_usd"], "gates": gates}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
