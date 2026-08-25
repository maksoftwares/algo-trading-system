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
    apply_source_day_budget,
    august_comparison,
    load_locked_config,
    resolve,
    sha256_file,
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def historical_proposals(config: dict) -> pd.DataFrame:
    inputs = config["inputs"]
    v2 = json.loads(resolve(REPO_ROOT, inputs["v2_result"]["path"]).read_text())
    rows = [
        {
            "trade_id": row["trade_id"],
            "entry_time_utc": row["entry_time_utc"],
            "source_id": row["source_id"],
            "proposal_rule": "V2_SOURCE_HEALTH",
        }
        for row in v2["veto_audit"]
        if bool(row["baseline_runtime_executed"])
    ]
    anti = pd.read_csv(resolve(REPO_ROOT, inputs["antichase_historical_vetoes"]["path"]))
    for row in anti.to_dict("records"):
        if str(row["baseline_runtime_executed"]).lower() == "true":
            rows.append(
                {
                    "trade_id": row["trade_id"],
                    "entry_time_utc": row["entry_time_utc"],
                    "source_id": row["source_id"],
                    "proposal_rule": "V57_VOLATILITY_ANTICHASE",
                }
            )
    return pd.DataFrame(rows)


def markdown(result: dict) -> str:
    base = result["baseline"]
    changed = result["challenger"]
    august = result["august_2026_through_25"]
    return "\n".join(
        [
            "# V60 Dual-Veto Budget V3 Result",
            "",
            f"Decision: **{result['decision']}**",
            "",
            "| Scope | V60 net | Challenger net | V60 PF | Challenger PF | V60 DD | Challenger DD |",
            "|---|---:|---:|---:|---:|---:|---:|",
            f"| Historical | ${base['net_pnl_usd']:.2f} | ${changed['net_pnl_usd']:.2f} | {base['profit_factor']:.3f} | {changed['profit_factor']:.3f} | ${base['maximum_lifetime_closed_drawdown_usd']:.2f} | ${changed['maximum_lifetime_closed_drawdown_usd']:.2f} |",
            f"| August 2026 through 25 | ${august['baseline_v60']['net_pnl_usd']:.2f} | ${august['challenger']['net_pnl_usd']:.2f} | {august['baseline_v60']['profit_factor']:.3f} | {august['challenger']['profit_factor']:.3f} | ${august['baseline_v60']['closed_drawdown_usd']:.2f} | ${august['challenger']['closed_drawdown_usd']:.2f} |",
            "",
            f"Historical veto proposals: {result['composition_audit']['raw_proposals']}",
            f"Selected historical vetoes: {result['composition_audit']['selected_vetoes']}",
            f"Trade retention: {result['composition_audit']['trade_retention']:.4%}",
            "",
            "This is exposed retrospective evidence. Deployment remains prohibited pending clean forward proof.",
            "",
        ]
    )


def main() -> int:
    config = load_locked_config(CONFIG, REPO_ROOT)
    inputs = config["inputs"]
    maximum = int(config["composition"]["maximum_vetoes_per_source_utc_day"])
    proposals = historical_proposals(config)
    budget = apply_source_day_budget(proposals, maximum)
    selected_ids = set(budget.loc[budget["selected_veto"], "trade_id"].astype(str))

    base_config_path = resolve(REPO_ROOT, inputs["base_challenger_config"]["path"])
    base = json.loads(base_config_path.read_text(encoding="utf-8"))
    original_ledger = resolve(REPO_ROOT, base["inputs"]["causal_rank_ledger"]["path"])
    if sha256_file(original_ledger) != base["inputs"]["causal_rank_ledger"]["sha256"]:
        raise ValueError("Base causal rank ledger identity changed")
    decisions = pd.read_parquet(original_ledger, columns=["trade_id"])
    decisions["rank"] = decisions["trade_id"].astype(str).map(
        lambda trade_id: 0.0 if trade_id in selected_ids else 1.0
    )

    evaluator = load_module(
        "v60_dual_veto_budget_evaluator",
        resolve(REPO_ROOT, inputs["shared_evaluator"]["path"]),
    )
    with tempfile.TemporaryDirectory(prefix="v60-dual-veto-budget-v3-") as temporary:
        temporary = Path(temporary)
        decisions_path = temporary / "POLICY_DECISIONS.parquet"
        decisions.to_parquet(decisions_path, index=False)
        replay_config = deepcopy(base)
        replay_config["schema_version"] = config["schema_version"]
        replay_config["report_title"] = "V60 Dual-Veto Budget V3"
        replay_config["inputs"]["causal_rank_ledger"] = {
            "path": str(decisions_path),
            "sha256": hashlib.sha256(decisions_path.read_bytes()).hexdigest(),
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
        for additional_cost in config["acceptance"][
            "additional_cost_stress_usd_per_trade"
        ]:
            stressed, _, _ = evaluator.run(
                replay_path, additional_cost_usd_per_trade=float(additional_cost)
            )
            comparative_gates = {
                name: bool(value)
                for name, value in stressed["gates"].items()
                if name not in {"baseline_net_identity", "baseline_trade_identity"}
            }
            cost_stress[str(additional_cost)] = {
                "additional_cost_usd_per_trade": float(additional_cost),
                "baseline_net_pnl_usd": stressed["baseline"]["net_pnl_usd"],
                "challenger_net_pnl_usd": stressed["challenger"]["net_pnl_usd"],
                "delta_net_pnl_usd": stressed["delta"]["net_pnl_usd"],
                "baseline_profit_factor": stressed["baseline"]["profit_factor"],
                "challenger_profit_factor": stressed["challenger"]["profit_factor"],
                "baseline_closed_drawdown_usd": stressed["baseline"][
                    "maximum_lifetime_closed_drawdown_usd"
                ],
                "challenger_closed_drawdown_usd": stressed["challenger"][
                    "maximum_lifetime_closed_drawdown_usd"
                ],
                "baseline_equity_drawdown_usd": stressed["baseline"][
                    "maximum_lifetime_equity_drawdown_usd"
                ],
                "challenger_equity_drawdown_usd": stressed["challenger"][
                    "maximum_lifetime_equity_drawdown_usd"
                ],
                "gates": stressed["gates"],
                "comparative_gates": comparative_gates,
                "all_comparative_gates_pass": bool(all(comparative_gates.values())),
            }

    august, august_rows = august_comparison(
        pd.read_csv(resolve(REPO_ROOT, inputs["exposed_broker_audit"]["path"])),
        pd.read_csv(resolve(REPO_ROOT, inputs["antichase_august_audit"]["path"])),
        maximum,
    )
    anti_module = load_module(
        "v60_antichase_crossfeed",
        resolve(REPO_ROOT, inputs["antichase_experiment_source"]["path"]),
    )
    crossfeed = anti_module.crossfeed_comparison(
        pd.read_csv(resolve(REPO_ROOT, inputs["crossfeed_priced_runtime"]["path"]), low_memory=False),
        set(
            vetoes.loc[
                vetoes["baseline_runtime_executed"].astype(str).str.lower().eq("true"),
                "trade_id",
            ].astype(str)
        ),
    )
    baseline_trades = int(historical["baseline"]["trades_closed"])
    challenger_trades = int(historical["challenger"]["trades_closed"])
    composition = {
        "raw_proposals": int(len(budget)),
        "selected_vetoes": int(budget["selected_veto"].sum()),
        "budget_retained_proposals": int((~budget["selected_veto"]).sum()),
        "maximum_vetoes_per_source_utc_day": maximum,
        "trade_retention": challenger_trades / baseline_trades,
    }
    august_gates = {
        "positive_net_pnl": august["challenger"]["net_pnl_usd"]
        > float(config["acceptance"]["minimum_august_net_pnl_usd_exclusive"]),
        "net_above_v60": august["challenger"]["net_pnl_usd"]
        > august["baseline_v60"]["net_pnl_usd"],
        "profit_factor_above_v60": august["challenger"]["profit_factor"]
        > august["baseline_v60"]["profit_factor"],
        "closed_drawdown_not_worse": august["challenger"]["closed_drawdown_usd"]
        <= august["baseline_v60"]["closed_drawdown_usd"],
    }
    combined_gates = {
        "historical_evaluator_gates": bool(all(historical["gates"].values())),
        "source_day_budget_respected": not budget.loc[
            budget["selected_veto"]
        ].duplicated(["source_id", "utc_day"]).any(),
        "locked_trade_retention": composition["trade_retention"]
        >= float(config["acceptance"]["minimum_trade_retention_fraction"]),
        "august_diagnostic": bool(all(august_gates.values())),
        "crossfeed_delta_positive": crossfeed["delta_net_pnl_usd"] > 0.0,
        "crossfeed_every_year_nonnegative": bool(crossfeed["every_year_nonnegative"]),
        "cost_stress_comparative_gates": all(
            item["all_comparative_gates_pass"] for item in cost_stress.values()
        ),
        "clean_forward_evidence": False,
    }
    retrospective_pass = all(
        value for key, value in combined_gates.items() if key != "clean_forward_evidence"
    )
    result = historical
    result.update(
        {
            "schema_version": config["schema_version"] + "_result",
            "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "decision": (
                "HISTORICAL_CHALLENGER_PASSES_PROSPECTIVE_CONFIRMATION_REQUIRED"
                if retrospective_pass
                else "KEEP_DEPLOYED_V60"
            ),
            "deployment_authorized": False,
            "broker_action_authorized": False,
            "evidence_status": config["evidence_status"],
            "composition": config["composition"],
            "composition_audit": composition,
            "august_2026_through_25": august,
            "august_gates": august_gates,
            "dukascopy_crossfeed": crossfeed,
            "cost_stress": cost_stress,
            "combined_gates": combined_gates,
            "limitations": [
                "All historical and August outcomes were exposed before nomination.",
                "The causal veto budget was introduced after observing the raw union's retention failure.",
                "Clean forward evidence is mandatory before any deployment decision.",
            ],
        }
    )
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (OUTPUTS / "RESULT.md").write_text(markdown(result), encoding="utf-8")
    annual.to_csv(OUTPUTS / "ANNUAL.csv", index=False, lineterminator="\n")
    vetoes.to_csv(OUTPUTS / "HISTORICAL_VETOES.csv", index=False, lineterminator="\n")
    budget.to_csv(OUTPUTS / "PROPOSAL_BUDGET_AUDIT.csv", index=False, lineterminator="\n")
    august_rows.to_csv(OUTPUTS / "AUGUST_2026_TRADE_AUDIT.csv", index=False, lineterminator="\n")
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "historical_delta_net_pnl_usd": result["delta"]["net_pnl_usd"],
                "historical_trade_retention": composition["trade_retention"],
                "august_delta_net_pnl_usd": august["delta_net_pnl_usd"],
                "gates": combined_gates,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
