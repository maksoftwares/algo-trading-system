from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
import sklearn

from src.campaign import (
    ARM_KEYS,
    LANE_ROOT,
    annual_four_arm_predictions,
    apply_arm_first_signal,
    arm_score_column,
    arm_trigger_column,
    attach_path_sequence_features,
    canonical_sha256,
    load_module,
    resolve_path,
    sequence_feature_names,
    sha256_file,
)


CONFIG_PATH = (
    LANE_ROOT / "config" / "v6_causal_ml_early_exit_four_approach_v6.json"
)


def records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    result = frame.copy()
    if "checks" in result:
        result["checks"] = result["checks"].map(dict)
    return result.to_dict(orient="records")


def markdown_result(
    result: dict[str, Any],
    comparison: pd.DataFrame,
    annual: pd.DataFrame,
    windows: pd.DataFrame,
) -> str:
    return "\n".join(
        [
            "# V6 Causal ML Early Exit Four-Approach Result",
            "",
            f"Decision: **{result['decision']}**",
            "",
            "Historical research only. Execution is not authorized.",
            "",
            "## Arm Comparison",
            "",
            "```csv",
            comparison.to_csv(index=False, float_format="%.4f").rstrip(),
            "```",
            "",
            "## Frozen Baseline",
            "",
            f"- V1 V6 net / PF / DD: "
            f"${result['frozen_v1']['v6_net_usd']:.2f} / "
            f"{result['frozen_v1']['v6_profit_factor']:.3f} / "
            f"${result['frozen_v1']['v6_closed_drawdown_usd']:.2f}",
            f"- V1 shared net / PF / floating DD: "
            f"${result['frozen_v1']['combined_net_usd']:.2f} / "
            f"{result['frozen_v1']['combined_profit_factor']:.3f} / "
            f"${result['frozen_v1']['combined_floating_drawdown_usd']:.2f}",
            "",
            "## Annual Models",
            "",
            "```csv",
            annual.drop(columns=["model_detail"])
            .to_csv(index=False, float_format="%.4f")
            .rstrip(),
            "```",
            "",
            "## Required Windows",
            "",
            "```csv",
            windows.drop(columns=["checks"])
            .to_csv(index=False, float_format="%.3f")
            .rstrip(),
            "```",
            "",
            "## Interpretation",
            "",
            result["interpretation"],
            "",
        ]
    )


def main() -> None:
    started = time.perf_counter()

    def progress(message: str) -> None:
        print(f"[{time.perf_counter() - started:8.1f}s] {message}", flush=True)

    progress("verifying V5 and all transitive locked sources")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    outputs = LANE_ROOT / config["outputs"]["directory"]
    outputs.mkdir(parents=True, exist_ok=True)
    v5 = load_module(
        "v5_crossasset_dependency_for_four_approach_v6",
        resolve_path(config["sources"]["v5_implementation"]["path"]),
    )
    observed = v5.verify_dependency_sources(config)
    v5_config = json.loads(
        resolve_path(config["sources"]["v5_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    for section in ("action_policy", "walk_forward", "windows", "gates"):
        if config[section] != v5_config[section]:
            raise ValueError(f"Campaign changed frozen V5 section: {section}")
    v5_source_hashes = v5.verify_dependency_sources(v5_config)
    v4 = load_module(
        "v4_utility_dependency_for_four_approach_v6",
        v5.resolve_path(v5_config["sources"]["v4_implementation"]["path"]),
    )
    v4_config = json.loads(
        v5.resolve_path(v5_config["sources"]["v4_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    v4_source_hashes = v5.verify_dependency_sources(v4_config, v4.resolve_path)
    v3 = load_module(
        "v3_early_exit_dependency_for_four_approach_v6",
        v4.resolve_path(v4_config["sources"]["v3_implementation"]["path"]),
    )
    v3_config = json.loads(
        v4.resolve_path(v4_config["sources"]["v3_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    v3_source_hashes = v5.verify_dependency_sources(v3_config, v3.resolve_path)
    v1 = load_module(
        "v1_veto_dependency_for_four_approach_v6",
        v3.resolve_path(v3_config["sources"]["v1_implementation"]["path"]),
    )
    v1_config = json.loads(
        v3.resolve_path(v3_config["sources"]["v1_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    v1_source_hashes = v5.verify_dependency_sources(v1_config, v1.resolve_path)
    reproduction = load_module(
        "v6_reproduction_dependency_for_four_approach_v6",
        v1.resolve_path(v1_config["sources"]["v6_implementation"]["path"]),
    )
    reproduction_config = json.loads(
        v1.resolve_path(v1_config["sources"]["v6_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    transitive_hashes = v5.verify_reproduction_sources(
        reproduction_config, reproduction
    )
    base_feature_names = (
        v3.validate_feature_contract(v3_config)
        + list(v5_config["cross_asset"]["features"])
    )
    sequence_names = sequence_feature_names(config)
    contract = {
        "schema_version": "xauusd_v6_four_approach_contract",
        "config_sha256": sha256_file(CONFIG_PATH),
        "preregistration_sha256": sha256_file(LANE_ROOT / "PREREGISTRATION.md"),
        "implementation_sha256": sha256_file(LANE_ROOT / "src" / "campaign.py"),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "source_hashes": observed,
        "v5_source_hashes": v5_source_hashes,
        "v4_source_hashes": v4_source_hashes,
        "v3_source_hashes": v3_source_hashes,
        "v1_source_hashes": v1_source_hashes,
        "transitive_v6_source_hashes": transitive_hashes,
        "base_feature_names": base_feature_names,
        "sequence_feature_names": sequence_names,
        "arms": config["arms"],
        "model_parameters": config["model_parameters"],
        "action_policy": config["action_policy"],
        "walk_forward": config["walk_forward"],
        "windows": config["windows"],
        "gates": config["gates"],
        "coverage_gates": config["coverage_gates"],
        "sklearn_version": sklearn.__version__,
        "research_controls": config["research_controls"],
    }
    contract["contract_sha256"] = canonical_sha256(contract)
    (outputs / config["outputs"]["contract_lock"]).write_text(
        json.dumps(contract, indent=2, sort_keys=True), encoding="utf-8"
    )

    progress("building frozen broad corpus and target snapshots")
    broad_corpus, broad_audit = v1.build_training_corpus(
        reproduction, reproduction_config, v1_config
    )
    external_modules = reproduction.load_external_modules(reproduction_config)
    context = external_modules["specialist"].load_context()
    training_snapshots, training_snapshot_audit = v3.build_snapshots(
        broad_corpus,
        context,
        v3_config,
        reproduction_config["execution_stress"],
    )
    v1_predictions = pd.read_parquet(
        v3.resolve_path(v3_config["sources"]["v1_predictions"]["path"])
    )
    for column in ("scan_time", "entry_time", "exit_time"):
        v1_predictions[column] = pd.to_datetime(v1_predictions[column], utc=True)
    selected = v1_predictions.loc[v1_predictions["ml_selected"]].copy()
    target_snapshots, target_snapshot_audit = v3.build_snapshots(
        selected,
        context,
        v3_config,
        reproduction_config["execution_stress"],
    )

    progress("joining frozen cross-asset and causal path features")
    cross_asset_sources, cross_asset_source_audit = v5.load_cross_asset_sources(
        v5_config
    )
    training_snapshots = v5.attach_cross_asset_features(
        training_snapshots, cross_asset_sources, v5_config
    )
    target_snapshots = v5.attach_cross_asset_features(
        target_snapshots, cross_asset_sources, v5_config
    )
    training_coverage = v5.coverage_audit(training_snapshots)
    target_coverage = v5.coverage_audit(target_snapshots)
    training_snapshots = attach_path_sequence_features(
        training_snapshots, context, config
    )
    target_snapshots = attach_path_sequence_features(
        target_snapshots, context, config
    )

    progress("fitting all four locked annual approaches")
    snapshot_predictions, annual = annual_four_arm_predictions(
        training_snapshots,
        target_snapshots,
        config,
        v5_config,
        v3_config,
        v3,
        v4,
        v5,
    )

    progress("loading frozen account baseline and floating-equity bars")
    baseline = pd.read_parquet(
        v1.resolve_path(v1_config["sources"]["v60_ledger"]["path"])
    )
    for column in ("signal_time", "entry_time", "exit_time"):
        baseline[column] = pd.to_datetime(baseline[column], utc=True)
    frozen_source = pd.read_parquet(
        v3.resolve_path(v3_config["sources"]["v1_accepted"]["path"])
    )
    for column in ("entry_time", "exit_time"):
        frozen_source[column] = pd.to_datetime(frozen_source[column], utc=True)
    limits = reproduction_config["shared_account_limits"]
    frozen_accepted, _ = reproduction.route_candidates(baseline, selected, limits)
    if set(frozen_accepted["trade_id"]) != set(frozen_source["trade_id"]):
        raise ValueError("Frozen V1 routing no longer reproduces its accepted ledger")
    top = int(config["gates"]["top_winners_removed"])
    v1_metrics = v1.trade_metrics(frozen_accepted, top)
    v1_combined = pd.concat([baseline, frozen_accepted], ignore_index=True).sort_values(
        ["exit_time", "trade_id"], kind="mergesort"
    )
    v1_combined_metrics = v1.trade_metrics(v1_combined, top)
    floating_audit = load_module(
        "v60_floating_audit_for_four_approach_v6",
        v1.resolve_path(v1_config["sources"]["v60_audit"]["path"]),
    )
    v60_config = json.loads(
        v1.resolve_path(v1_config["sources"]["v60_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    bars, market_audit = floating_audit.load_m5_bars(v60_config["market_data"])
    v1_curve = floating_audit.floating_curve(
        bars,
        v1_combined,
        "fee_stress_pnl_usd",
        "fee_stress_open_cost_usd",
        int(v60_config["floating_equity"]["bar_minutes"]),
    )
    v1_floating = floating_audit.envelope_drawdown(v1_curve)
    coverage_gates = config["coverage_gates"]
    coverage_checks = {
        "minimum_dxy_1h_available_share": target_coverage[
            "dxy_1h_available_share"
        ]
        >= float(coverage_gates["minimum_dxy_1h_available_share"]),
        "minimum_treasury_1h_available_share": target_coverage[
            "treasury_1h_available_share"
        ]
        >= float(coverage_gates["minimum_treasury_1h_available_share"]),
        "minimum_common_dollar_1h_available_share": target_coverage[
            "common_dollar_1h_available_share"
        ]
        >= float(coverage_gates["minimum_common_dollar_1h_available_share"]),
    }

    progress("routing and replaying every arm")
    arm_results: dict[str, Any] = {}
    comparison_rows: list[dict[str, Any]] = []
    window_frames: list[pd.DataFrame] = []
    for arm in ARM_KEYS:
        managed_candidates, management_actions = apply_arm_first_signal(
            selected, snapshot_predictions, arm, v3, v4
        )
        managed_accepted, routing = reproduction.route_candidates(
            baseline, managed_candidates, limits
        )
        managed_metrics = v1.trade_metrics(managed_accepted, top)
        managed_combined = pd.concat(
            [baseline, managed_accepted], ignore_index=True
        ).sort_values(["exit_time", "trade_id"], kind="mergesort")
        managed_combined_metrics = v1.trade_metrics(managed_combined, top)
        arm_windows = v3.trade_comparison(
            frozen_accepted,
            managed_accepted,
            baseline,
            config["windows"],
            v1.trade_metrics,
            config,
        )
        arm_windows.insert(0, "arm", arm)
        window_frames.append(arm_windows)
        managed_curve = floating_audit.floating_curve(
            bars,
            managed_combined,
            "fee_stress_pnl_usd",
            "fee_stress_open_cost_usd",
            int(v60_config["floating_equity"]["bar_minutes"]),
        )
        managed_floating = floating_audit.envelope_drawdown(managed_curve)
        trigger_column = arm_trigger_column(arm)
        first_actions = (
            snapshot_predictions.loc[snapshot_predictions[trigger_column]]
            .sort_values(
                ["source_trade_id", "checkpoint_minutes"], kind="mergesort"
            )
            .drop_duplicates("source_trade_id", keep="first")
        )
        early_actions = management_actions.loc[
            management_actions["management_action"].eq("EARLY_EXIT")
        ]
        if set(first_actions["source_trade_id"]) != set(early_actions["trade_id"]):
            raise ValueError(f"{arm} first signals do not match managed actions")
        early_share = len(first_actions) / len(managed_candidates)
        positive_benefit_share = (
            float(first_actions["benefit_usd"].gt(0.0).mean())
            if len(first_actions)
            else 0.0
        )
        action_benefit = float(first_actions["benefit_usd"].sum())
        arm_annual = annual.loc[annual["arm"].eq(arm)].copy()
        mean_spearman = float(arm_annual["target_spearman"].mean())
        years_spearman_positive = int(
            arm_annual["target_spearman"].gt(0.0).sum()
        )
        years_action_net_positive = int(
            arm_annual["first_action_net_benefit_usd"].gt(0.0).sum()
        )
        accepted_routing = routing.loc[routing["accepted"]]
        maximum_routed_open = (
            int((accepted_routing["active_addons_before"] + 1).max())
            if len(accepted_routing)
            else 0
        )
        maximum_routed_risk = (
            float(
                (
                    accepted_routing["active_addon_risk_before_usd"]
                    + accepted_routing["candidate_risk_usd"]
                ).max()
            )
            if len(accepted_routing)
            else 0.0
        )
        checks = {
            **coverage_checks,
            "minimum_mean_annual_spearman": mean_spearman
            >= float(config["gates"]["minimum_mean_annual_spearman"]),
            "minimum_years_spearman_above_zero": years_spearman_positive
            >= int(config["gates"]["minimum_years_spearman_above_zero"]),
            "minimum_years_positive_first_action_net": years_action_net_positive
            >= int(config["gates"]["minimum_years_positive_first_action_net"]),
            "minimum_first_action_positive_benefit_share": positive_benefit_share
            >= float(
                config["gates"]["minimum_first_action_positive_benefit_share"]
            ),
            "minimum_total_first_action_benefit_usd": action_benefit
            > float(config["gates"]["minimum_total_first_action_benefit_usd"]),
            "minimum_early_exit_trade_share": early_share
            >= float(config["gates"]["minimum_early_exit_trade_share"]),
            "maximum_early_exit_trade_share": early_share
            <= float(config["gates"]["maximum_early_exit_trade_share"]),
            "all_required_windows_pass": bool(arm_windows["passed"].all()),
            "managed_v6_net_no_worse_than_v1": managed_metrics["stress_net_usd"]
            >= v1_metrics["stress_net_usd"] - 1e-9,
            "managed_v6_pf_no_worse_than_v1": managed_metrics[
                "stress_profit_factor"
            ]
            >= v1_metrics["stress_profit_factor"] - 1e-9,
            "managed_v6_closed_drawdown_no_worse_than_v1": managed_metrics[
                "stress_closed_drawdown_usd"
            ]
            <= v1_metrics["stress_closed_drawdown_usd"] + 1e-9,
            "managed_combined_net_no_worse_than_v1": managed_combined_metrics[
                "stress_net_usd"
            ]
            >= v1_combined_metrics["stress_net_usd"] - 1e-9,
            "managed_combined_pf_no_worse_than_v1": managed_combined_metrics[
                "stress_profit_factor"
            ]
            >= v1_combined_metrics["stress_profit_factor"] - 1e-9,
            "managed_combined_closed_drawdown_no_worse_than_v1": (
                managed_combined_metrics["stress_closed_drawdown_usd"]
                <= v1_combined_metrics["stress_closed_drawdown_usd"] + 1e-9
            ),
            "managed_combined_floating_drawdown_no_worse_than_v1": float(
                managed_floating["maximum_drawdown_usd"]
            )
            <= float(v1_floating["maximum_drawdown_usd"]) + 1e-9,
            "maximum_routed_addon_open_positions": maximum_routed_open
            <= int(limits["maximum_addon_open_positions"]),
            "maximum_routed_addon_initial_risk_usd": maximum_routed_risk
            <= float(limits["maximum_addon_concurrent_initial_risk_usd"])
            + 1e-9,
            "immutable_v5_hash_preserved": sha256_file(
                resolve_path(config["sources"]["v5_result"]["path"])
            )
            == config["sources"]["v5_result"]["sha256"],
            "frozen_v5_policy_preserved": True,
        }
        passed = all(checks.values())
        arm_result = {
            "passed": passed,
            "management": {
                "selected_nominations": int(len(managed_candidates)),
                "early_exit_nominations": int(len(first_actions)),
                "early_exit_share_pct": 100.0 * early_share,
                "positive_benefit_share_pct": 100.0 * positive_benefit_share,
                "first_action_net_benefit_usd": action_benefit,
                "worst_first_action_benefit_usd": (
                    float(first_actions["benefit_usd"].min())
                    if len(first_actions)
                    else 0.0
                ),
                "accepted_managed_trades": int(len(managed_accepted)),
                "checkpoint_counts": {
                    str(key): int(value)
                    for key, value in first_actions[
                        "checkpoint_minutes"
                    ].value_counts().to_dict().items()
                },
            },
            "model_quality": {
                "mean_annual_spearman": mean_spearman,
                "years_spearman_above_zero": years_spearman_positive,
                "years_positive_first_action_net": years_action_net_positive,
            },
            "v6_sleeve": managed_metrics,
            "shared_account": {
                **{
                    f"combined_{key}": value
                    for key, value in managed_combined_metrics.items()
                },
                "combined_floating_drawdown_usd": float(
                    managed_floating["maximum_drawdown_usd"]
                ),
                "maximum_routed_open_addons": maximum_routed_open,
                "maximum_routed_addon_initial_risk_usd": maximum_routed_risk,
                "floating": managed_floating,
            },
            "routing_reason_counts": {
                str(key): int(value)
                for key, value in routing["reason"].value_counts().to_dict().items()
            },
            "full_history_checks": checks,
            "failed_checks": [name for name, value in checks.items() if not value],
        }
        arm_results[arm] = arm_result
        comparison_rows.append(
            {
                "arm": arm,
                "passed": passed,
                "early_exits": len(first_actions),
                "early_exit_share_pct": 100.0 * early_share,
                "beneficial_exit_pct": 100.0 * positive_benefit_share,
                "action_benefit_usd": action_benefit,
                "mean_annual_spearman": mean_spearman,
                "positive_action_years": years_action_net_positive,
                "v6_trades": managed_metrics["trades"],
                "v6_win_rate_pct": managed_metrics["win_rate_pct"],
                "v6_net_usd": managed_metrics["stress_net_usd"],
                "v6_profit_factor": managed_metrics["stress_profit_factor"],
                "v6_closed_drawdown_usd": managed_metrics[
                    "stress_closed_drawdown_usd"
                ],
                "combined_win_rate_pct": managed_combined_metrics["win_rate_pct"],
                "combined_net_usd": managed_combined_metrics["stress_net_usd"],
                "combined_profit_factor": managed_combined_metrics[
                    "stress_profit_factor"
                ],
                "combined_closed_drawdown_usd": managed_combined_metrics[
                    "stress_closed_drawdown_usd"
                ],
                "combined_floating_drawdown_usd": float(
                    managed_floating["maximum_drawdown_usd"]
                ),
                "failed_check_count": len(arm_result["failed_checks"]),
            }
        )
        prefix = f"V6_FOUR_APPROACH_{arm}"
        managed_candidates.to_parquet(
            outputs / f"{prefix}_MANAGED_CANDIDATES.parquet", index=False
        )
        managed_accepted.to_parquet(
            outputs / f"{prefix}_ACCEPTED.parquet", index=False
        )
        routing.to_parquet(outputs / f"{prefix}_ROUTING.parquet", index=False)

    windows = pd.concat(window_frames, ignore_index=True)
    comparison = pd.DataFrame(comparison_rows)
    qualified = comparison.loc[comparison["passed"], "arm"].tolist()
    v5_result = json.loads(
        resolve_path(config["sources"]["v5_result"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    v4_result = json.loads(
        v5.resolve_path(v5_config["sources"]["v4_result"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    result = {
        "schema_version": "xauusd_v6_causal_ml_early_exit_four_approach_result",
        "decision": (
            "V6_FOUR_APPROACH_HAS_HISTORICAL_PASS_REQUIRES_PROSPECTIVE"
            if qualified
            else "V6_FOUR_APPROACH_ALL_HISTORICAL_GATES_FAIL_QUARANTINED"
        ),
        "passed_any_arm": bool(qualified),
        "qualified_arms": qualified,
        "contract_sha256": contract["contract_sha256"],
        "broad_training_corpus": broad_audit,
        "training_snapshots": training_snapshot_audit,
        "target_snapshots": target_snapshot_audit,
        "cross_asset_source_audit": cross_asset_source_audit,
        "training_cross_asset_coverage": training_coverage,
        "target_cross_asset_coverage": target_coverage,
        "frozen_v1": {
            "v6_trades": v1_metrics["trades"],
            "v6_win_rate_pct": v1_metrics["win_rate_pct"],
            "v6_net_usd": v1_metrics["stress_net_usd"],
            "v6_profit_factor": v1_metrics["stress_profit_factor"],
            "v6_closed_drawdown_usd": v1_metrics[
                "stress_closed_drawdown_usd"
            ],
            "combined_trades": v1_combined_metrics["trades"],
            "combined_win_rate_pct": v1_combined_metrics["win_rate_pct"],
            "combined_net_usd": v1_combined_metrics["stress_net_usd"],
            "combined_profit_factor": v1_combined_metrics[
                "stress_profit_factor"
            ],
            "combined_closed_drawdown_usd": v1_combined_metrics[
                "stress_closed_drawdown_usd"
            ],
            "combined_floating_drawdown_usd": float(
                v1_floating["maximum_drawdown_usd"]
            ),
        },
        "prior_research": {
            "v4_action_benefit_usd": v4_result["management"][
                "first_action_net_benefit_usd"
            ],
            "v4_v6_net_usd": v4_result["v6_sleeve"]["managed_stress_net_usd"],
            "v5_action_benefit_usd": v5_result["management"][
                "first_action_net_benefit_usd"
            ],
            "v5_v6_net_usd": v5_result["v6_sleeve"]["managed_stress_net_usd"],
        },
        "arms": arm_results,
        "annual_models": records(annual),
        "required_windows": records(windows),
        "market_data_audit": market_audit,
        "research_controls": config["research_controls"],
        "execution_authorized": False,
        "interpretation": (
            (
                "At least one locked arm passed every historical gate. It is "
                "still development evidence and requires a separately locked "
                "prospective period plus MT5 parity."
            )
            if qualified
            else (
                "None of the four locked approaches improved the frozen V1 "
                "policy across all model, economic, window, and drawdown gates. "
                "All four exact arms are quarantined."
            )
        ),
    }
    serializable_result = json.loads(json.dumps(result, default=str))
    result["result_sha256"] = canonical_sha256(serializable_result)

    names = config["outputs"]
    snapshot_predictions.to_parquet(
        outputs / names["snapshot_predictions"], index=False
    )
    annual.to_csv(outputs / names["annual_models"], index=False)
    comparison.to_csv(outputs / names["arm_comparison"], index=False)
    windows.assign(checks=windows["checks"].map(json.dumps)).to_csv(
        outputs / names["windows"], index=False
    )
    (outputs / names["result_json"]).write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    (outputs / names["result_markdown"]).write_text(
        markdown_result(result, comparison, annual, windows), encoding="utf-8"
    )
    artifacts: dict[str, Any] = {}
    for path in sorted(outputs.iterdir()):
        if path.name == names["manifest"]:
            continue
        artifacts[path.name] = {
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
    manifest = {
        "schema_version": "xauusd_v6_four_approach_manifest",
        "artifacts": artifacts,
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    (outputs / names["manifest"]).write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    progress("campaign complete")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
