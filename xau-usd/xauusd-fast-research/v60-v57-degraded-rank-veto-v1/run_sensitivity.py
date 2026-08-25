from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path

import pandas as pd

from src import evaluate


VARIANTS = {
    "NOMINATED": {},
    "RANK_005": {"maximum_causal_rank_exclusive": 0.05},
    "RANK_015": {"maximum_causal_rank_exclusive": 0.15},
    "HEALTH_080": {"maximum_prior_profit_factor_exclusive": 0.8},
    "HEALTH_120": {"maximum_prior_profit_factor_exclusive": 1.2},
    "LOOKBACK_10": {"lookback_closed_trades": 10},
    "LOOKBACK_30": {"lookback_closed_trades": 30},
    "HEALTH_ONLY": {"maximum_causal_rank_exclusive": 1.01},
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=evaluate.CONFIG_PATH)
    parser.add_argument("--output-directory", type=Path, default=evaluate.OUTPUTS)
    args = parser.parse_args()
    output_directory = args.output_directory.resolve()
    config = evaluate.load_config(args.config.resolve())
    replay = evaluate.load_module(
        "v60_v57_sensitivity_replay",
        evaluate.resolve(config["inputs"]["replay_source"]["path"]),
    )
    contract = replay.load_json(
        evaluate.resolve(config["inputs"]["replay_contract"]["path"])
    )
    deployed = replay.load_json(
        evaluate.resolve(config["inputs"]["deployed_config"]["path"])
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
    cache_meta = replay.prepare_quote_cache(
        contract, candidates, population, force=False
    )
    quotes = replay.load_quote_cache(cache_meta)
    spec = next(
        item
        for item in replay.scenario_specs(contract)
        if item.scenario_id == "deployed__full_runtime"
    )
    rank_map = evaluate.load_rank_map(
        evaluate.resolve(config["inputs"]["causal_rank_ledger"]["path"])
    )
    scenario_type = evaluate.challenger_class(replay)
    baseline_result = json.loads(
        (output_directory / "RESULT.json").read_text(encoding="utf-8")
    )
    baseline = baseline_result["baseline"]
    baseline_annual = {
        int(row["year"]): float(row["baseline_net_pnl_usd"])
        for row in baseline_result["annual"]
    }
    tolerance = float(config["gates"]["metric_tolerance_usd"])

    rows = []
    annual_rows = []
    for variant_id, changes in VARIANTS.items():
        policy = deepcopy(config["policy"])
        policy.update(changes)
        scenario = scenario_type(
            spec,
            deployed,
            contract,
            candidates,
            rank_map=rank_map,
            policy=policy,
        )
        metrics = scenario.simulate(quotes)
        trades = evaluate.closed_trade_frame(scenario, candidates)
        trades["year"] = pd.to_datetime(
            trades["entry_time_utc"], utc=True, format="mixed"
        ).dt.year
        year_deltas = []
        for year, baseline_net in baseline_annual.items():
            challenger_net = float(
                trades.loc[trades["year"] == year, "pnl_usd"].sum()
            )
            delta = challenger_net - baseline_net
            year_deltas.append(delta)
            annual_rows.append(
                {
                    "variant_id": variant_id,
                    "year": year,
                    "baseline_net_pnl_usd": baseline_net,
                    "challenger_net_pnl_usd": challenger_net,
                    "delta_pnl_usd": delta,
                }
            )
        stable = (
            metrics["net_pnl_usd"] >= baseline["net_pnl_usd"]
            and metrics["profit_factor"] >= baseline["profit_factor"]
            and metrics["maximum_lifetime_closed_drawdown_usd"]
            <= baseline["maximum_lifetime_closed_drawdown_usd"] + tolerance
            and metrics["maximum_lifetime_equity_drawdown_usd"]
            <= baseline["maximum_lifetime_equity_drawdown_usd"] + tolerance
            and min(year_deltas) >= -tolerance
            and metrics["trades_closed"]
            >= baseline["trades_closed"]
            * float(config["gates"]["minimum_trade_retention_fraction"])
        )
        rows.append(
            {
                "variant_id": variant_id,
                "lookback": int(policy["lookback_closed_trades"]),
                "health_pf_threshold": float(
                    policy["maximum_prior_profit_factor_exclusive"]
                ),
                "rank_threshold": float(
                    policy["maximum_causal_rank_exclusive"]
                ),
                "vetoes": len(scenario.veto_audit),
                "trades": int(metrics["trades_closed"]),
                "net_pnl_usd": float(metrics["net_pnl_usd"]),
                "delta_pnl_usd": float(
                    metrics["net_pnl_usd"] - baseline["net_pnl_usd"]
                ),
                "profit_factor": float(metrics["profit_factor"]),
                "equity_drawdown_usd": float(
                    metrics["maximum_lifetime_equity_drawdown_usd"]
                ),
                "positive_delta_years": sum(delta > tolerance for delta in year_deltas),
                "negative_delta_years": sum(delta < -tolerance for delta in year_deltas),
                "worst_annual_delta_usd": min(year_deltas),
                "stable_all_gates": stable,
            }
        )

    frame = pd.DataFrame(rows)
    annual = pd.DataFrame(annual_rows)
    frame.to_csv(output_directory / "SENSITIVITY.csv", index=False)
    annual.to_csv(output_directory / "SENSITIVITY_ANNUAL.csv", index=False)
    lines = [
        "# V57 Degraded-Rank Sensitivity",
        "",
        "Diagnostics only. The nominated policy remains unchanged.",
        "",
        "| Variant | Vetoes | Net | Delta | PF | Equity DD | Positive years | Negative years | Stable |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in frame.itertuples(index=False):
        lines.append(
            f"| {row.variant_id} | {row.vetoes} | ${row.net_pnl_usd:.2f} | "
            f"${row.delta_pnl_usd:+.2f} | {row.profit_factor:.4f} | "
            f"${row.equity_drawdown_usd:.2f} | {row.positive_delta_years} | "
            f"{row.negative_delta_years} | {'PASS' if row.stable_all_gates else 'FAIL'} |"
        )
    (output_directory / "SENSITIVITY.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(frame.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
