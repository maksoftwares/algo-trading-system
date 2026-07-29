from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "PORTABLE_MATURE_TOPUP_V2.json"
LOCK_PATH = ROOT / "config" / "IMPLEMENTATION_LOCK.json"
OUTPUTS = ROOT / "outputs"
PNL = "fee_stress_pnl_usd"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_config() -> dict[str, Any]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for item in config["inputs"].values():
        path = REPO_ROOT / str(item["path"])
        if sha256_file(path) != str(item["sha256"]):
            raise ValueError(f"Input identity changed: {path}")
    verify_implementation_lock()
    return config


def verify_implementation_lock() -> None:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if not bool(lock["locked_before_result"]):
        raise ValueError("Implementation was not locked before the result")
    for relative, expected in lock["files"].items():
        path = ROOT / relative
        if sha256_file(path) != expected:
            raise ValueError(f"Implementation identity changed: {path}")


def topup_profit_factor(meta: pd.DataFrame, factors: np.ndarray) -> float:
    selected = np.asarray(factors, dtype=float) == 2.0
    pnl = meta.loc[selected, PNL].to_numpy(dtype=float)
    gross_loss = -float(pnl[pnl < 0.0].sum())
    return float(pnl[pnl > 0.0].sum() / gross_loss) if gross_loss > 0 else float("inf")


def policy_factors(
    primary: pd.DataFrame,
    meta: pd.DataFrame,
    config: dict[str, Any],
    demo_config: dict[str, Any],
    topup: ModuleType,
    prior: ModuleType,
) -> tuple[np.ndarray, dict[str, Any]]:
    policy = config["policy"]
    proposals = (
        meta["entry_time"].dt.year.ge(int(policy["maturity_entry_year"])).to_numpy()
        & primary["rank"].gt(float(policy["minimum_rank_exclusive"])).to_numpy()
    )
    factors, audit = topup.topup_factors(
        meta,
        proposals,
        demo_config,
        {key: float(value) for key, value in config["risk_limits"].items()},
        prior,
    )
    if bool(policy["retain_every_baseline_trade"]) and np.any(factors < 1.0):
        raise ValueError("Portable top-up removed a baseline trade")
    return factors, audit


def subset_metrics(
    prior: ModuleType,
    meta: pd.DataFrame,
    factors: np.ndarray,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict[str, Any]:
    mask = meta["entry_time"].ge(start) & meta["entry_time"].lt(end)
    closed, _, _ = prior.closed_metrics(
        meta.loc[mask].reset_index(drop=True),
        np.asarray(factors)[mask.to_numpy()],
    )
    return closed


def run() -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    config = load_config()
    prior_path = REPO_ROOT / config["inputs"]["causal_retest_source"]["path"]
    topup_path = REPO_ROOT / config["inputs"]["topup_source"]["path"]
    prior = load_module("portable_topup_prior", prior_path)
    topup = load_module("portable_topup_policy", topup_path)
    prior_contract = json.loads(
        (REPO_ROOT / config["inputs"]["causal_retest_contract"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    demo_config = json.loads(
        (REPO_ROOT / config["inputs"]["demo_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    feature_module = prior.load_module(
        "portable_topup_features", prior.FEATURES_PATH
    )
    cooldown_module = prior.load_module(
        "portable_topup_cooldown", prior.COOLDOWN_PATH
    )
    floating_module = prior.load_module(
        "portable_topup_floating", prior.FLOATING_AUDIT_PATH
    )
    ledger, population_audit = prior.load_current_population(
        prior_contract, cooldown_module
    )
    full_X, full_meta, feature_audit = prior.build_corrected_features(
        ledger, feature_module
    )
    X = full_X[list(config["feature_columns"])].copy()
    if set(config["excluded_feed_specific_features"]) & set(X.columns):
        raise ValueError("A feed-specific feature reached the portable model")

    primary_all = prior.walkforward(
        X, full_meta, prior_contract, int(prior_contract["model"]["primary_seed"])
    )
    scored = primary_all["rank"].notna().to_numpy()
    primary = primary_all.loc[scored].reset_index(drop=True)
    meta = full_meta.loc[scored].reset_index(drop=True)
    features = X.loc[scored].reset_index(drop=True)
    factors, risk_audit = policy_factors(
        primary, meta, config, demo_config, topup, prior
    )
    bars, market_audit = prior.load_floating_bars(floating_module, meta)
    baseline_factors = np.ones(len(meta), dtype=float)
    baseline_closed, _, baseline_yearly = prior.closed_metrics(
        meta, baseline_factors
    )
    policy_closed, _, policy_yearly = prior.closed_metrics(meta, factors)
    baseline_floating = prior.weighted_floating_metrics(
        bars, meta, baseline_factors
    )
    policy_floating = prior.weighted_floating_metrics(bars, meta, factors)
    delta = meta[PNL].to_numpy(dtype=float) * (factors - 1.0)
    bootstrap = prior.moving_week_block_bootstrap(meta, delta)
    topup_pf = topup_profit_factor(meta, factors)

    recent = config["recent_window"]
    recent_start = pd.Timestamp(recent["start_utc"])
    recent_end = pd.Timestamp(recent["end_utc_exclusive"])
    recent_baseline = subset_metrics(
        prior, meta, baseline_factors, recent_start, recent_end
    )
    recent_policy = subset_metrics(prior, meta, factors, recent_start, recent_end)

    seed_rows: list[dict[str, Any]] = []
    seeds = [
        int(prior_contract["model"]["primary_seed"]),
        *[int(value) for value in prior_contract["model"]["diagnostic_seeds"]],
    ]
    for seed in seeds:
        decisions = (
            primary
            if seed == int(prior_contract["model"]["primary_seed"])
            else prior.walkforward(X, full_meta, prior_contract, seed)
            .loc[scored]
            .reset_index(drop=True)
        )
        seed_factors, seed_audit = policy_factors(
            decisions, meta, config, demo_config, topup, prior
        )
        seed_closed, _, seed_yearly = prior.closed_metrics(meta, seed_factors)
        seed_delta = meta[PNL].to_numpy(dtype=float) * (seed_factors - 1.0)
        seed_bootstrap = prior.moving_week_block_bootstrap(meta, seed_delta)
        seed_rows.append(
            {
                "seed": seed,
                "proposed_topups": int(seed_audit["proposed_topups"]),
                "accepted_topups": int(seed_audit["accepted_topups"]),
                "delta_pnl_usd": float(
                    seed_closed["net_pnl_usd"] - baseline_closed["net_pnl_usd"]
                ),
                "profit_factor": float(seed_closed["profit_factor"]),
                "nonnegative_delta_years": int(
                    seed_yearly["delta_pnl_usd"].ge(0.0).sum()
                ),
                "weekly_block_lower_95_usd": float(
                    seed_bootstrap["lower_95_one_sided_usd"]
                ),
            }
        )

    gates_config = config["gates"]
    minimum_ratio = baseline_floating["net_to_floating_drawdown"] * (
        1.0
        + float(
            gates_config[
                "minimum_net_to_floating_drawdown_improvement_fraction"
            ]
        )
    )
    seed_frame = pd.DataFrame(seed_rows)
    gates = {
        "all_features_available_at_entry": (
            feature_audit["selected_bar_unavailable_at_entry_rows"] == 0
        ),
        "feed_specific_features_excluded": not bool(
            set(config["excluded_feed_specific_features"]) & set(features.columns)
        ),
        "every_baseline_trade_retained": bool(np.all(factors >= 1.0)),
        "no_missing_risk_topup": (
            risk_audit["accepted_missing_risk_topups"] == 0
        ),
        "net_not_below_baseline": (
            policy_closed["net_pnl_usd"] >= baseline_closed["net_pnl_usd"]
        ),
        "profit_factor_within_one_percent": (
            policy_closed["profit_factor"]
            >= baseline_closed["profit_factor"]
            * (1.0 - float(gates_config["maximum_profit_factor_decline_fraction"]))
        ),
        "floating_drawdown_not_above_baseline": (
            policy_floating["maximum_floating_drawdown_usd"]
            <= baseline_floating["maximum_floating_drawdown_usd"]
        ),
        "net_to_floating_drawdown_improves_five_percent": (
            policy_floating["net_to_floating_drawdown"] >= minimum_ratio
        ),
        "all_mature_years_nonnegative": bool(
            policy_yearly.loc[
                policy_yearly["entry_year"].ge(
                    int(config["policy"]["maturity_entry_year"])
                ),
                "delta_pnl_usd",
            ].ge(0.0).all()
        ),
        "topup_profit_factor_at_least_1_2": (
            topup_pf >= float(gates_config["minimum_topup_profit_factor"])
        ),
        "weekly_block_lower_bound_above_zero": (
            bootstrap["lower_95_one_sided_usd"] > 0.0
        ),
        "recent_net_not_below_baseline": (
            recent_policy["net_pnl_usd"] >= recent_baseline["net_pnl_usd"]
        ),
        "at_least_four_seeds_positive": (
            int(seed_frame["delta_pnl_usd"].gt(0.0).sum())
            >= int(gates_config["minimum_seed_positive_delta_count"])
        ),
        "at_least_four_seeds_stable_by_year": (
            int(
                seed_frame["nonnegative_delta_years"]
                .ge(int(gates_config["minimum_seed_nonnegative_year_count"]))
                .sum()
            )
            >= int(gates_config["minimum_seed_positive_delta_count"])
        ),
    }
    passed = bool(all(gates.values()))
    result = {
        "schema_version": config["schema_version"] + "_result",
        "decision": (
            "HISTORICAL_PORTABILITY_GATES_PASS_PROSPECTIVE_DEMO_NOMINATION_ONLY"
            if passed
            else "PORTABLE_MATURE_TOPUP_FAILS_KEEP_ML_OFF_DEMO"
        ),
        "historical_gates_passed": passed,
        "runtime_changed": False,
        "population_audit": population_audit,
        "feature_audit": feature_audit,
        "market_data_audit": market_audit,
        "feature_columns": list(features.columns),
        "baseline": {
            "closed": baseline_closed,
            "floating": baseline_floating,
        },
        "policy": {
            "closed": policy_closed,
            "floating": policy_floating,
            "delta_pnl_usd": float(
                policy_closed["net_pnl_usd"] - baseline_closed["net_pnl_usd"]
            ),
            "topup_profit_factor": topup_pf,
            "risk_audit": risk_audit,
            "weekly_block_bootstrap": bootstrap,
        },
        "recent_window": {
            "start_utc": recent_start.isoformat(),
            "end_utc_exclusive": recent_end.isoformat(),
            "baseline": recent_baseline,
            "policy": recent_policy,
        },
        "yearly": {
            "baseline": baseline_yearly.to_dict(orient="records"),
            "policy": policy_yearly.to_dict(orient="records"),
        },
        "seed_sensitivity": seed_rows,
        "gates": gates,
        "limitations": [
            "All historical V60 outcomes were exposed before this experiment.",
            "A pass nominates prospective demo validation only.",
            "Cross-feed feature parity must pass before any broker-affecting use.",
            "No live authorization is granted.",
        ],
    }
    audit_features = features.rename(columns={"is_core": "feature_is_core"})
    decisions = pd.concat([meta, audit_features, primary], axis=1)
    if decisions.columns.duplicated().any():
        raise ValueError("Decision audit contains duplicate columns")
    decisions["topup_proposed"] = (
        meta["entry_time"].dt.year.ge(int(config["policy"]["maturity_entry_year"]))
        & primary["rank"].gt(float(config["policy"]["minimum_rank_exclusive"]))
    )
    decisions["topup_accepted"] = factors == 2.0
    decisions["lot"] = factors * float(config["policy"]["base_lot"])
    decisions["baseline_pnl_usd"] = decisions[PNL]
    decisions["policy_pnl_usd"] = decisions[PNL] * factors
    return prior.json_ready(result), decisions, seed_frame


def write_outputs(
    result: dict[str, Any], decisions: pd.DataFrame, seeds: pd.DataFrame
) -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    decisions.to_parquet(OUTPUTS / "PRIMARY_DECISIONS.parquet", index=False)
    seeds.to_csv(OUTPUTS / "SEED_SENSITIVITY.csv", index=False)
    (OUTPUTS / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    baseline = result["baseline"]
    policy = result["policy"]
    lines = [
        "# V60 Portable Mature Top-Up V2 Result",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "| policy | trades | net | PF | win rate | closed DD | floating DD | net/floating DD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, item in (("V60 baseline", baseline), ("Portable ML top-up", policy)):
        closed = item["closed"]
        floating = item["floating"]
        lines.append(
            f"| {label} | {closed['trade_rows']} | ${closed['net_pnl_usd']:.2f} | "
            f"{closed['profit_factor']:.3f} | {100 * closed['win_rate']:.2f}% | "
            f"${closed['closed_trade_drawdown_usd']:.2f} | "
            f"${floating['maximum_floating_drawdown_usd']:.2f} | "
            f"{floating['net_to_floating_drawdown']:.2f} |"
        )
    lines.extend(
        [
            "",
            f"- Delta: `${policy['delta_pnl_usd']:.2f}`.",
            f"- Proposed / accepted top-ups: "
            f"`{policy['risk_audit']['proposed_topups']} / "
            f"{policy['risk_audit']['accepted_topups']}`.",
            f"- Top-up PF: `{policy['topup_profit_factor']:.3f}`.",
            f"- Weekly-block lower 95% bound: "
            f"`${policy['weekly_block_bootstrap']['lower_95_one_sided_usd']:.2f}`.",
            "",
            "## Gates",
            "",
        ]
    )
    lines.extend(
        f"- {'PASS' if value else 'FAIL'}: `{name}`."
        for name, value in result["gates"].items()
    )
    lines.extend(
        [
            "",
            "Historical development evidence only. No runtime or broker authority "
            "is granted by this result.",
            "",
        ]
    )
    (OUTPUTS / "RESULT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    result, decisions, seeds = run()
    write_outputs(result, decisions, seeds)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
