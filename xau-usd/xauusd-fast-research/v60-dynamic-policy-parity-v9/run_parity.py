from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG = ROOT / "config" / "parity.json"
OUTPUTS = ROOT / "outputs"
sys.path.insert(0, str(ROOT))

from src.parity import (
    annual_comparison,
    closed_metrics,
    exact_set_difference,
    feature_decisions,
    fixed_lifecycle_equity_drawdown,
    replacement_capacity_count,
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def load_config() -> dict[str, Any]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if any(config["authorization"].values()):
        raise ValueError("Parity audit must remain fully disarmed")
    for name, item in config["inputs"].items():
        actual = sha256_file(resolve(item["path"]))
        if actual != str(item["sha256"]):
            raise ValueError(f"Input identity changed: {name}: {actual}")
    return config


def utc_text(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000.0, UTC).isoformat().replace(
        "+00:00", "Z"
    )


def scenario_inputs(candidates, baseline_trades: pd.DataFrame, decisions):
    executed = set(baseline_trades["trade_id"].astype(str))
    outcomes = {
        str(row["trade_id"]): {
            "opened_at_utc": str(row["entry_time_utc"]),
            "closed_at_utc": str(row["exit_time_utc"]),
            "source_id": str(row["source_id"]),
            "pnl_usd": float(row["pnl_usd"]),
        }
        for row in baseline_trades.to_dict("records")
    }
    rows = []
    for candidate in candidates:
        candidate_id = str(candidate.trade_id)
        baseline_executed = candidate_id in executed
        rows.append(
            {
                "candidate_id": candidate_id,
                "source_id": str(candidate.source_id),
                "entry_time_utc": utc_text(int(candidate.entry_ms)),
                "baseline_executed": baseline_executed,
                "broker_outcome_resolved": baseline_executed,
                "broker_pnl_usd": (
                    float(outcomes[candidate_id]["pnl_usd"])
                    if baseline_executed
                    else None
                ),
            }
        )
    boundary = datetime.fromtimestamp(
        min(int(candidate.entry_ms) for candidate in candidates) / 1000.0, UTC
    ) - timedelta(seconds=1)
    return rows, outcomes, boundary


def expected_full_dynamic(result: dict[str, Any], cost: float) -> dict[str, Any]:
    if cost == 0.0:
        return {
            "trades": int(result["challenger"]["trades_closed"]),
            "net_pnl_usd": float(result["challenger"]["net_pnl_usd"]),
            "profit_factor": float(result["challenger"]["profit_factor"]),
            "closed_drawdown_usd": float(
                result["challenger"]["maximum_lifetime_closed_drawdown_usd"]
            ),
            "equity_drawdown_usd": float(
                result["challenger"]["maximum_lifetime_equity_drawdown_usd"]
            ),
            "vetoes": int(result["baseline_executed_veto_count"]),
        }
    item = result["cost_stress"][str(cost)]
    return {
        "trades": sum(int(row["challenger_trades"]) for row in item["annual"]),
        "net_pnl_usd": float(item["challenger_net_pnl_usd"]),
        "profit_factor": float(item["challenger_profit_factor"]),
        "closed_drawdown_usd": float(item["challenger_closed_drawdown_usd"]),
        "equity_drawdown_usd": float(item["challenger_equity_drawdown_usd"]),
        "vetoes": int(item["executed_vetoes"]),
    }


def main() -> int:
    config = load_config()
    inputs = config["inputs"]
    evaluator = load_module(
        "v60_v9_evaluator", resolve(inputs["shared_evaluator"]["path"])
    )
    replay = load_module("v60_v9_replay", resolve(inputs["replay_source"]["path"]))
    policy = load_module(
        "v60_v9_prospective_policy", resolve(inputs["prospective_policy"]["path"])
    )
    base = json.loads(resolve(inputs["base_challenger_config"]["path"]).read_text())
    v6 = json.loads(resolve(inputs["v6_config"]["path"]).read_text())
    v6_result = json.loads(resolve(inputs["v6_result"]["path"]).read_text())
    features = pd.read_parquet(resolve(inputs["causal_features"]["path"]))
    decisions = feature_decisions(features)

    contract = replay.load_json(resolve(inputs["replay_contract"]["path"]))
    deployed = replay.load_json(resolve(inputs["deployed_config"]["path"]))
    deployed = replay.apply_portfolio_protection(contract, deployed)
    deployed = replay.apply_runtime_risk_mode(
        deployed,
        bool(
            contract["evaluation"].get(
                "required_equity_fraction_limits_enabled", False
            )
        ),
    )
    nominal_candidates, population = replay.load_candidates(contract, deployed)
    cache_meta = replay.prepare_quote_cache(
        contract, nominal_candidates, population, force=False
    )
    quotes = replay.load_quote_cache(cache_meta)
    spec = next(
        item
        for item in replay.scenario_specs(contract)
        if item.scenario_id == "deployed__full_runtime"
    )
    expected_veto_frame = pd.read_csv(resolve(inputs["v6_vetoes"]["path"]))
    expected_nominal_vetoes = sorted(
        expected_veto_frame.loc[
            expected_veto_frame["baseline_runtime_executed"]
            .astype(str)
            .str.lower()
            .eq("true"),
            "trade_id",
        ].astype(str)
    )

    scenarios: dict[str, Any] = {}
    tolerance = float(config["metric_tolerance_usd"])
    for cost in map(float, config["additional_cost_usd_per_trade"]):
        candidates = evaluator.apply_additional_cost(nominal_candidates, cost)
        baseline_scenario = replay.Scenario(spec, deployed, contract, candidates)
        baseline_scenario.simulate(quotes)
        baseline_trades = evaluator.closed_trade_frame(baseline_scenario, candidates)
        rows, outcomes, boundary = scenario_inputs(
            candidates, baseline_trades, decisions
        )
        policy_audit = policy.apply_dynamic_union(
            rows,
            decisions,
            warm_start={
                "rows": [],
                "retained_history_counts_by_source": {},
            },
            broker_outcomes=outcomes,
            boundary=boundary,
            v2_policy=base["policy"],
            anti_rule=v6["anti_chase"],
        )
        veto_ids = sorted(
            str(row["candidate_id"])
            for row in rows
            if bool(row["baseline_executed"]) and bool(row["would_veto"])
        )
        common_path = baseline_trades.loc[
            ~baseline_trades["trade_id"].astype(str).isin(veto_ids)
        ].copy()
        baseline_metrics = closed_metrics(baseline_trades)
        common_metrics = closed_metrics(common_path)
        baseline_ids = baseline_trades["trade_id"].astype(str).tolist()
        common_ids = common_path["trade_id"].astype(str).tolist()
        baseline_fixed_equity_drawdown = fixed_lifecycle_equity_drawdown(
            candidates,
            baseline_scenario.event_rows,
            quotes,
            baseline_ids,
            starting_equity_usd=float(spec.starting_equity_usd),
        )
        common_fixed_equity_drawdown = fixed_lifecycle_equity_drawdown(
            candidates,
            baseline_scenario.event_rows,
            quotes,
            common_ids,
            starting_equity_usd=float(spec.starting_equity_usd),
        )
        baseline_equity_parity_error = abs(
            baseline_fixed_equity_drawdown
            - float(baseline_scenario.max_lifetime_equity_dd)
        )
        if baseline_equity_parity_error > tolerance:
            raise ValueError(
                "Fixed-lifecycle baseline equity replay differs from V60: "
                f"{baseline_equity_parity_error}"
            )
        baseline_metrics["equity_drawdown_usd"] = baseline_fixed_equity_drawdown
        common_metrics["equity_drawdown_usd"] = common_fixed_equity_drawdown
        full_dynamic = expected_full_dynamic(v6_result, cost)
        annual = annual_comparison(baseline_trades, common_path)
        end = pd.Timestamp(contract["evaluation"]["entry_end_exclusive_utc"])
        windows: dict[str, Any] = {}
        for months in (3, 6, 12):
            start = end - pd.DateOffset(months=months)
            windows[f"{months}m"] = {
                "start_utc": start.isoformat(),
                "baseline": evaluator.window_metrics(baseline_trades, start),
                "challenger": evaluator.window_metrics(common_path, start),
            }
        veto_values = baseline_trades.loc[
            baseline_trades["trade_id"].astype(str).isin(veto_ids), "pnl_usd"
        ].to_numpy(dtype=float)
        veto_profit_factor = evaluator.profit_factor(veto_values)
        retention = common_metrics["trades"] / baseline_metrics["trades"]
        acceptance = config["acceptance"]
        comparative_gates = {
            "net_not_below_baseline": common_metrics["net_pnl_usd"]
            >= baseline_metrics["net_pnl_usd"] - tolerance,
            "profit_factor_not_below_baseline": common_metrics["profit_factor"]
            >= baseline_metrics["profit_factor"],
            "closed_drawdown_not_above_baseline": common_metrics[
                "closed_drawdown_usd"
            ]
            <= baseline_metrics["closed_drawdown_usd"] + tolerance,
            "equity_drawdown_not_above_baseline": common_metrics[
                "equity_drawdown_usd"
            ]
            <= baseline_metrics["equity_drawdown_usd"] + tolerance,
            "trade_retention": retention
            >= float(acceptance["minimum_trade_retention_fraction"]),
            "frequency_retention": retention
            >= float(acceptance["minimum_frequency_retention_fraction"]),
            "no_negative_calendar_year_delta": all(
                float(row["delta_pnl_usd"]) >= -tolerance for row in annual
            ),
            "recent_windows_not_worse": all(
                item["challenger"]["net_pnl_usd"]
                >= item["baseline"]["net_pnl_usd"] - tolerance
                for item in windows.values()
            ),
            "veto_cohort_large_enough": len(veto_ids)
            >= int(acceptance["minimum_veto_cohort_rows"]),
            "veto_cohort_profit_factor_below_one": veto_profit_factor
            < float(acceptance["maximum_veto_profit_factor_exclusive"]),
        }
        key = str(cost)
        scenarios[key] = {
            "additional_cost_usd_per_trade": cost,
            "baseline_v60": baseline_metrics,
            "prospective_veto_only_common_path": common_metrics,
            "full_dynamic_v6": full_dynamic,
            "vetoes": len(veto_ids),
            "veto_trade_ids": veto_ids,
            "policy_audit": policy_audit,
            "baseline_fixed_lifecycle_equity_parity_error_usd": baseline_equity_parity_error,
            "annual": annual,
            "windows": windows,
            "trade_retention": retention,
            "veto_profit_factor": veto_profit_factor,
            "comparative_gates": comparative_gates,
            "all_comparative_gates_pass": all(comparative_gates.values()),
            "replacement_capacity_trade_count": replacement_capacity_count(
                baseline_metrics["trades"], len(veto_ids), full_dynamic["trades"]
            ),
            "full_dynamic_minus_common_path_net_pnl_usd": (
                full_dynamic["net_pnl_usd"] - common_metrics["net_pnl_usd"]
            ),
        }

    nominal = scenarios["0.0"]
    differences = exact_set_difference(
        expected_nominal_vetoes, nominal["veto_trade_ids"]
    )
    parity = {
        "veto_ids_exact": not differences["missing"]
        and not differences["unexpected"],
        "trade_count_exact": nominal["prospective_veto_only_common_path"]["trades"]
        == nominal["full_dynamic_v6"]["trades"],
        "net_pnl_exact": abs(
            nominal["prospective_veto_only_common_path"]["net_pnl_usd"]
            - nominal["full_dynamic_v6"]["net_pnl_usd"]
        )
        <= tolerance,
        "veto_set_difference": differences,
    }
    result = {
        "schema_version": config["schema_version"] + "_result",
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "decision": (
            "NOMINAL_POLICY_PARITY_PASSES"
            if all(
                parity[name]
                for name in ("veto_ids_exact", "trade_count_exact", "net_pnl_exact")
            )
            else "POLICY_PARITY_FAILS"
        ),
        "nominal_parity": parity,
        "scenarios": scenarios,
        "limitations": [
            "The common-path audit does not admit replacement trades.",
            "Common-path equity drawdown fixes each retained trade to its actual baseline lifecycle and validates against V60 equity drawdown.",
            "Replacement-capacity trades remain exclusive to the full dynamic replay.",
            "All outcomes are historical and exposed.",
        ],
        "broker_action_authorized": False,
        "deployment_authorized": False,
    }
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# V60 Dynamic Policy Parity V9 Result",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "| Added cost | Baseline net | Veto-only net | Full dynamic net | Retention | Replacement-capacity trades | Non-equity gates |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key in ("0.0", "0.1", "0.2"):
        item = scenarios[key]
        lines.append(
            f"| ${float(key):.2f} | ${item['baseline_v60']['net_pnl_usd']:.2f} | "
            f"${item['prospective_veto_only_common_path']['net_pnl_usd']:.2f} | "
            f"${item['full_dynamic_v6']['net_pnl_usd']:.2f} | "
            f"{item['trade_retention']:.3%} | "
            f"{item['replacement_capacity_trade_count']} | "
            f"{item['all_comparative_gates_pass']} |"
        )
    lines.extend(
        [
            "",
            "The observer and nominal historical V6 policy must match exactly.",
            "Stressed replacement-capacity effects are reported separately and cannot be claimed as forward broker evidence.",
            "",
        ]
    )
    (OUTPUTS / "RESULT.md").write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "nominal_parity": parity,
                "replacement_capacity_trade_counts": {
                    key: item["replacement_capacity_trade_count"]
                    for key, item in scenarios.items()
                },
            },
            sort_keys=True,
        )
    )
    return 0 if result["decision"] == "NOMINAL_POLICY_PARITY_PASSES" else 1


if __name__ == "__main__":
    raise SystemExit(main())
