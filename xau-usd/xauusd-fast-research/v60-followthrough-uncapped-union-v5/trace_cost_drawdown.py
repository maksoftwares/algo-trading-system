from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile

import pandas as pd

import run_experiment as experiment


ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"


def drawdown_trace(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    trace = frame.copy().reset_index(drop=True)
    trace["event_sequence"] = range(len(trace))
    trace["cumulative_pnl_usd"] = trace["pnl_usd"].cumsum()
    trace["closed_peak_usd"] = trace["cumulative_pnl_usd"].cummax()
    trace["closed_drawdown_usd"] = (
        trace["closed_peak_usd"] - trace["cumulative_pnl_usd"]
    )
    trough_index = int(trace["closed_drawdown_usd"].idxmax())
    peak_index = int(
        trace.loc[:trough_index, "cumulative_pnl_usd"].idxmax()
    )
    return trace, {
        "closed_drawdown_usd": float(trace.loc[trough_index, "closed_drawdown_usd"]),
        "peak_event_sequence": peak_index,
        "peak_exit_time_utc": str(trace.loc[peak_index, "exit_time_utc"]),
        "trough_event_sequence": trough_index,
        "trough_exit_time_utc": str(trace.loc[trough_index, "exit_time_utc"]),
        "interval_trades": int(trough_index - peak_index),
        "interval_pnl_usd": float(
            trace.loc[peak_index + 1 : trough_index, "pnl_usd"].sum()
        ),
    }


def main() -> int:
    config = experiment.load_config()
    inputs = config["inputs"]
    evaluator = experiment.load_module(
        "v60_v5_trace_evaluator", experiment.resolve(inputs["shared_evaluator"]["path"])
    )
    selected = set(
        pd.read_csv(OUTPUTS / "PROPOSAL_AUDIT.csv")["trade_id"].astype(str)
    )
    features = pd.read_parquet(
        experiment.resolve(inputs["causal_feature_ledger"]["path"]),
        columns=["trade_id"],
    )
    features["rank"] = features["trade_id"].astype(str).map(
        lambda trade_id: 0.0 if trade_id in selected else 1.0
    )
    base = json.loads(
        experiment.resolve(inputs["base_challenger_config"]["path"]).read_text()
    )
    with tempfile.TemporaryDirectory(prefix="v60-v5-drawdown-trace-") as temporary:
        temporary = Path(temporary)
        rank_path = temporary / "POLICY_DECISIONS.parquet"
        features.to_parquet(rank_path, index=False)
        replay_config = deepcopy(base)
        replay_config["inputs"]["causal_rank_ledger"] = {
            "path": str(rank_path),
            "sha256": experiment.sha256_file(rank_path),
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
        replay_path = temporary / "challenger.json"
        replay_path.write_text(json.dumps(replay_config), encoding="utf-8")
        locked = evaluator.load_config(replay_path)
        replay = evaluator.load_module(
            "v60_v5_trace_replay",
            evaluator.resolve(locked["inputs"]["replay_source"]["path"]),
        )
        contract = replay.load_json(
            evaluator.resolve(locked["inputs"]["replay_contract"]["path"])
        )
        deployed = replay.load_json(
            evaluator.resolve(locked["inputs"]["deployed_config"]["path"])
        )
        deployed = replay.apply_portfolio_protection(contract, deployed)
        deployed = replay.apply_runtime_risk_mode(
            deployed,
            bool(
                contract["evaluation"].get(
                    "required_equity_fraction_limits_enabled", False
                )
            ),
        )
        candidates, population = replay.load_candidates(contract, deployed)
        candidates = evaluator.apply_additional_cost(candidates, 0.1)
        cache = replay.prepare_quote_cache(contract, candidates, population, force=False)
        quotes = replay.load_quote_cache(cache)
        spec = next(
            item
            for item in replay.scenario_specs(contract)
            if item.scenario_id == "deployed__full_runtime"
        )
        baseline_scenario = replay.Scenario(spec, deployed, contract, candidates)
        baseline_scenario.simulate(quotes)
        challenger_type = evaluator.challenger_class(replay)
        challenger_scenario = challenger_type(
            spec,
            deployed,
            contract,
            candidates,
            rank_map=evaluator.load_rank_map(rank_path),
            policy=replay_config["policy"],
        )
        challenger_scenario.simulate(quotes)
        baseline = evaluator.closed_trade_frame(baseline_scenario, candidates)
        challenger = evaluator.closed_trade_frame(challenger_scenario, candidates)

    baseline_trace, baseline_summary = drawdown_trace(baseline)
    challenger_trace, challenger_summary = drawdown_trace(challenger)
    baseline_ids = set(baseline["trade_id"])
    challenger_ids = set(challenger["trade_id"])
    summary = {
        "schema_version": "v60_v5_cost_stress_drawdown_trace_v1",
        "additional_cost_usd_per_trade": 0.1,
        "baseline": baseline_summary,
        "challenger": challenger_summary,
        "baseline_only_trade_ids": sorted(baseline_ids - challenger_ids),
        "challenger_only_trade_ids": sorted(challenger_ids - baseline_ids),
        "common_trade_count": len(baseline_ids & challenger_ids),
    }
    baseline_trace.to_csv(
        OUTPUTS / "COST_STRESS_0_10_BASELINE_TRACE.csv", index=False, lineterminator="\n"
    )
    challenger_trace.to_csv(
        OUTPUTS / "COST_STRESS_0_10_CHALLENGER_TRACE.csv", index=False, lineterminator="\n"
    )
    (OUTPUTS / "COST_STRESS_0_10_DRAWDOWN_TRACE.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
