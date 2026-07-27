from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
import sklearn

from src.crossasset import (
    LANE_ROOT,
    annual_cross_asset_predictions,
    attach_cross_asset_features,
    canonical_sha256,
    coverage_audit,
    load_cross_asset_sources,
    load_module,
    resolve_path,
    sha256_file,
    validate_frozen_v4_policy,
    verify_dependency_sources,
    verify_reproduction_sources,
)


CONFIG_PATH = (
    LANE_ROOT / "config" / "v6_causal_ml_early_exit_crossasset_v5.json"
)


def records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    result = frame.copy()
    if "checks" in result:
        result["checks"] = result["checks"].map(dict)
    return result.to_dict(orient="records")


def markdown_result(
    result: dict[str, Any], annual: pd.DataFrame, windows: pd.DataFrame
) -> str:
    failed = [
        name for name, passed in result["full_history_checks"].items() if not passed
    ]
    return "\n".join(
        [
            "# V6 Causal ML Early Exit Cross-Asset V5 Result",
            "",
            f"Decision: **{result['decision']}**",
            "",
            "Historical research only. Execution is not authorized.",
            "",
            "## Cross-Asset Coverage",
            "",
            f"- DXY 1h: {100.0 * result['target_cross_asset_coverage']['dxy_1h_available_share']:.1f}%",
            f"- Treasury 1h: {100.0 * result['target_cross_asset_coverage']['treasury_1h_available_share']:.1f}%",
            f"- Common dollar 1h: {100.0 * result['target_cross_asset_coverage']['common_dollar_1h_available_share']:.1f}%",
            "",
            "## Utility Actions",
            "",
            f"- Frozen V1 selected nominations: {result['management']['selected_nominations']}",
            f"- V5 early exits: {result['management']['early_exit_nominations']}",
            f"- Early-exit share: {result['management']['early_exit_share_pct']:.1f}%",
            f"- Positive-benefit precision: {result['management']['positive_benefit_share_pct']:.1f}%",
            f"- Realized pre-routing benefit: ${result['management']['first_action_net_benefit_usd']:.2f}",
            f"- Worst early-exit benefit: ${result['management']['worst_first_action_benefit_usd']:.2f}",
            "",
            "## V6 Sleeve",
            "",
            f"- Frozen V1 net / PF / DD: ${result['v6_sleeve']['v1_stress_net_usd']:.2f} / "
            f"{result['v6_sleeve']['v1_stress_profit_factor']:.3f} / "
            f"${result['v6_sleeve']['v1_closed_drawdown_usd']:.2f}",
            f"- Cross-asset V5 net / PF / DD: ${result['v6_sleeve']['managed_stress_net_usd']:.2f} / "
            f"{result['v6_sleeve']['managed_stress_profit_factor']:.3f} / "
            f"${result['v6_sleeve']['managed_closed_drawdown_usd']:.2f}",
            "",
            "## Shared Account",
            "",
            f"- Frozen V1 combined net / PF / closed DD / floating DD: "
            f"${result['shared_account']['v1_combined_stress_net_usd']:.2f} / "
            f"{result['shared_account']['v1_combined_stress_profit_factor']:.3f} / "
            f"${result['shared_account']['v1_combined_closed_drawdown_usd']:.2f} / "
            f"${result['shared_account']['v1_combined_floating_drawdown_usd']:.2f}",
            f"- Cross-asset V5 combined net / PF / closed DD / floating DD: "
            f"${result['shared_account']['managed_combined_stress_net_usd']:.2f} / "
            f"{result['shared_account']['managed_combined_stress_profit_factor']:.3f} / "
            f"${result['shared_account']['managed_combined_closed_drawdown_usd']:.2f} / "
            f"${result['shared_account']['managed_combined_floating_drawdown_usd']:.2f}",
            "",
            "## V4 Comparison",
            "",
            f"- V4 actions / benefit: {result['v4_comparison']['early_exit_nominations']} / "
            f"${result['v4_comparison']['first_action_net_benefit_usd']:.2f}",
            f"- V4 V6 net / PF / DD: ${result['v4_comparison']['managed_v6_net_usd']:.2f} / "
            f"{result['v4_comparison']['managed_v6_profit_factor']:.3f} / "
            f"${result['v4_comparison']['managed_v6_closed_drawdown_usd']:.2f}",
            "",
            "## Annual Models",
            "",
            "```csv",
            annual.to_csv(index=False, float_format="%.4f").rstrip(),
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
            "## Failed Checks",
            "",
            ", ".join(failed) if failed else "None.",
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

    progress("verifying V4, cross-asset, and transitive locked sources")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    observed = verify_dependency_sources(config)
    outputs = LANE_ROOT / config["outputs"]["directory"]
    outputs.mkdir(parents=True, exist_ok=True)

    v4 = load_module(
        "v4_utility_dependency_for_crossasset_v5",
        resolve_path(config["sources"]["v4_implementation"]["path"]),
    )
    v4_config = json.loads(
        resolve_path(config["sources"]["v4_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    validate_frozen_v4_policy(config, v4_config)
    v4_source_hashes = verify_dependency_sources(v4_config, v4.resolve_path)
    v3 = load_module(
        "v3_early_exit_dependency_for_crossasset_v5",
        v4.resolve_path(v4_config["sources"]["v3_implementation"]["path"]),
    )
    v3_config = json.loads(
        v4.resolve_path(v4_config["sources"]["v3_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    v3_source_hashes = verify_dependency_sources(v3_config, v3.resolve_path)
    v1 = load_module(
        "v1_veto_dependency_for_crossasset_v5",
        v3.resolve_path(v3_config["sources"]["v1_implementation"]["path"]),
    )
    v1_config = json.loads(
        v3.resolve_path(v3_config["sources"]["v1_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    v1_source_hashes = verify_dependency_sources(v1_config, v1.resolve_path)
    reproduction = load_module(
        "v6_reproduction_dependency_for_crossasset_v5",
        v1.resolve_path(v1_config["sources"]["v6_implementation"]["path"]),
    )
    reproduction_config = json.loads(
        v1.resolve_path(v1_config["sources"]["v6_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    transitive_hashes = verify_reproduction_sources(
        reproduction_config, reproduction
    )
    base_feature_names = v3.validate_feature_contract(v3_config)
    feature_names = base_feature_names + list(config["cross_asset"]["features"])
    if len(feature_names) != len(set(feature_names)):
        raise ValueError("Duplicate feature name in locked V5 contract")
    contract = {
        "schema_version": "xauusd_v6_causal_ml_early_exit_crossasset_v5_contract",
        "config_sha256": sha256_file(CONFIG_PATH),
        "implementation_sha256": sha256_file(
            LANE_ROOT / "src" / "crossasset.py"
        ),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "source_hashes": observed,
        "v4_source_hashes": v4_source_hashes,
        "v3_source_hashes": v3_source_hashes,
        "v1_source_hashes": v1_source_hashes,
        "transitive_v6_source_hashes": transitive_hashes,
        "dependency_text_hash_policy": (
            "exact_bytes_or_crlf_to_lf_only_for_text_sources"
        ),
        "base_feature_names": base_feature_names,
        "cross_asset_feature_names": config["cross_asset"]["features"],
        "feature_names": feature_names,
        "cross_asset_join": {
            "bar_minutes": config["cross_asset"]["bar_minutes"],
            "maximum_staleness_minutes": config["cross_asset"][
                "maximum_staleness_minutes"
            ],
            "rule": "source_timestamp_plus_bar_duration_lte_decision_time",
            "closure_fill": "forbidden",
        },
        "model": config["model"],
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

    progress("building broad V6 corpus and frozen causal snapshots")
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

    progress("loading and causally joining locked cross-asset bars")
    cross_asset_sources, cross_asset_source_audit = load_cross_asset_sources(config)
    training_snapshots = attach_cross_asset_features(
        training_snapshots, cross_asset_sources, config
    )
    target_snapshots = attach_cross_asset_features(
        target_snapshots, cross_asset_sources, config
    )
    training_coverage = coverage_audit(training_snapshots)
    target_coverage = coverage_audit(target_snapshots)

    progress("fitting annual frozen-policy cross-asset utility models")
    snapshot_predictions, annual = annual_cross_asset_predictions(
        training_snapshots,
        target_snapshots,
        config,
        v3_config,
        v3,
        v4,
    )
    managed_candidates, management_actions = v4.apply_first_utility_signal(
        selected, snapshot_predictions, v3
    )

    progress("rerouting frozen and V5-managed nominations")
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
    managed_accepted, routing = reproduction.route_candidates(
        baseline, managed_candidates, limits
    )

    top = int(config["gates"]["top_winners_removed"])
    v1_metrics = v1.trade_metrics(frozen_accepted, top)
    managed_metrics = v1.trade_metrics(managed_accepted, top)
    v1_combined = pd.concat([baseline, frozen_accepted], ignore_index=True).sort_values(
        ["exit_time", "trade_id"], kind="mergesort"
    )
    managed_combined = pd.concat(
        [baseline, managed_accepted], ignore_index=True
    ).sort_values(["exit_time", "trade_id"], kind="mergesort")
    v1_combined_metrics = v1.trade_metrics(v1_combined, top)
    managed_combined_metrics = v1.trade_metrics(managed_combined, top)
    windows = v3.trade_comparison(
        frozen_accepted,
        managed_accepted,
        baseline,
        config["windows"],
        v1.trade_metrics,
        config,
    )

    progress("rebuilding shared-account floating equity")
    audit = load_module(
        "v60_floating_audit_for_crossasset_v5",
        v1.resolve_path(v1_config["sources"]["v60_audit"]["path"]),
    )
    v60_config = json.loads(
        v1.resolve_path(v1_config["sources"]["v60_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    bars, market_audit = audit.load_m5_bars(v60_config["market_data"])
    v1_curve = audit.floating_curve(
        bars,
        v1_combined,
        "fee_stress_pnl_usd",
        "fee_stress_open_cost_usd",
        int(v60_config["floating_equity"]["bar_minutes"]),
    )
    managed_curve = audit.floating_curve(
        bars,
        managed_combined,
        "fee_stress_pnl_usd",
        "fee_stress_open_cost_usd",
        int(v60_config["floating_equity"]["bar_minutes"]),
    )
    v1_floating = audit.envelope_drawdown(v1_curve)
    managed_floating = audit.envelope_drawdown(managed_curve)

    first_actions = (
        snapshot_predictions.loc[snapshot_predictions["utility_exit_trigger"]]
        .sort_values(["source_trade_id", "checkpoint_minutes"], kind="mergesort")
        .drop_duplicates("source_trade_id", keep="first")
    )
    early_actions = management_actions.loc[
        management_actions["management_action"].eq("EARLY_EXIT")
    ]
    if set(first_actions["source_trade_id"]) != set(early_actions["trade_id"]):
        raise ValueError("First V5 utility signals do not match managed actions")
    early_share = len(first_actions) / len(managed_candidates)
    positive_benefit_share = (
        float(first_actions["benefit_usd"].gt(0.0).mean())
        if len(first_actions)
        else 0.0
    )
    first_action_benefit = float(first_actions["benefit_usd"].sum())
    mean_spearman = float(annual["target_spearman"].mean())
    years_spearman_positive = int(annual["target_spearman"].gt(0.0).sum())
    years_action_net_positive = int(
        annual["first_action_net_benefit_usd"].gt(0.0).sum()
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
    coverage_gates = config["coverage_gates"]
    full_checks = {
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
        "minimum_mean_annual_spearman": mean_spearman
        >= float(config["gates"]["minimum_mean_annual_spearman"]),
        "minimum_years_spearman_above_zero": years_spearman_positive
        >= int(config["gates"]["minimum_years_spearman_above_zero"]),
        "minimum_years_positive_first_action_net": years_action_net_positive
        >= int(config["gates"]["minimum_years_positive_first_action_net"]),
        "minimum_first_action_positive_benefit_share": positive_benefit_share
        >= float(config["gates"]["minimum_first_action_positive_benefit_share"]),
        "minimum_total_first_action_benefit_usd": first_action_benefit
        > float(config["gates"]["minimum_total_first_action_benefit_usd"]),
        "minimum_early_exit_trade_share": early_share
        >= float(config["gates"]["minimum_early_exit_trade_share"]),
        "maximum_early_exit_trade_share": early_share
        <= float(config["gates"]["maximum_early_exit_trade_share"]),
        "all_required_windows_pass": bool(windows["passed"].all()),
        "managed_v6_net_no_worse_than_v1": managed_metrics["stress_net_usd"]
        >= v1_metrics["stress_net_usd"] - 1e-9,
        "managed_v6_pf_no_worse_than_v1": managed_metrics["stress_profit_factor"]
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
        "managed_combined_closed_drawdown_no_worse_than_v1": managed_combined_metrics[
            "stress_closed_drawdown_usd"
        ]
        <= v1_combined_metrics["stress_closed_drawdown_usd"] + 1e-9,
        "managed_combined_floating_drawdown_no_worse_than_v1": float(
            managed_floating["maximum_drawdown_usd"]
        )
        <= float(v1_floating["maximum_drawdown_usd"]) + 1e-9,
        "maximum_routed_addon_open_positions": maximum_routed_open
        <= int(limits["maximum_addon_open_positions"]),
        "maximum_routed_addon_initial_risk_usd": maximum_routed_risk
        <= float(limits["maximum_addon_concurrent_initial_risk_usd"]) + 1e-9,
        "immutable_v4_hash_preserved": sha256_file(
            resolve_path(config["sources"]["v4_result"]["path"])
        )
        == config["sources"]["v4_result"]["sha256"],
        "frozen_v4_policy_preserved": True,
    }
    passed = all(full_checks.values())
    v4_result = json.loads(
        resolve_path(config["sources"]["v4_result"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    result = {
        "schema_version": "xauusd_v6_causal_ml_early_exit_crossasset_v5_result",
        "decision": (
            "V6_CAUSAL_ML_EARLY_EXIT_CROSSASSET_V5_HISTORICAL_GATE_PASS_REQUIRES_PROSPECTIVE"
            if passed
            else "V6_CAUSAL_ML_EARLY_EXIT_CROSSASSET_V5_HISTORICAL_GATE_FAIL_QUARANTINED"
        ),
        "passed": passed,
        "contract_sha256": contract["contract_sha256"],
        "broad_training_corpus": broad_audit,
        "training_snapshots": training_snapshot_audit,
        "target_snapshots": target_snapshot_audit,
        "cross_asset_source_audit": cross_asset_source_audit,
        "training_cross_asset_coverage": training_coverage,
        "target_cross_asset_coverage": target_coverage,
        "model_quality": {
            "mean_annual_spearman": mean_spearman,
            "years_spearman_above_zero": years_spearman_positive,
            "years_positive_first_action_net": years_action_net_positive,
            "annual": records(annual),
        },
        "management": {
            "selected_nominations": int(len(managed_candidates)),
            "early_exit_nominations": int(len(first_actions)),
            "early_exit_share_pct": 100.0 * early_share,
            "positive_benefit_share_pct": 100.0 * positive_benefit_share,
            "first_action_net_benefit_usd": first_action_benefit,
            "worst_first_action_benefit_usd": (
                float(first_actions["benefit_usd"].min())
                if len(first_actions)
                else 0.0
            ),
            "accepted_managed_trades": int(len(managed_accepted)),
            "checkpoint_counts": first_actions[
                "checkpoint_minutes"
            ].value_counts().to_dict(),
        },
        "v4_comparison": {
            "early_exit_nominations": v4_result["management"][
                "early_exit_nominations"
            ],
            "first_action_net_benefit_usd": v4_result["management"][
                "first_action_net_benefit_usd"
            ],
            "positive_benefit_share_pct": v4_result["management"][
                "positive_benefit_share_pct"
            ],
            "managed_v6_net_usd": v4_result["v6_sleeve"][
                "managed_stress_net_usd"
            ],
            "managed_v6_profit_factor": v4_result["v6_sleeve"][
                "managed_stress_profit_factor"
            ],
            "managed_v6_closed_drawdown_usd": v4_result["v6_sleeve"][
                "managed_closed_drawdown_usd"
            ],
            "managed_combined_net_usd": v4_result["shared_account"][
                "managed_combined_stress_net_usd"
            ],
            "managed_combined_profit_factor": v4_result["shared_account"][
                "managed_combined_stress_profit_factor"
            ],
            "managed_combined_floating_drawdown_usd": v4_result[
                "shared_account"
            ]["managed_combined_floating_drawdown_usd"],
        },
        "v6_sleeve": {
            "v1_stress_net_usd": v1_metrics["stress_net_usd"],
            "v1_stress_profit_factor": v1_metrics["stress_profit_factor"],
            "v1_closed_drawdown_usd": v1_metrics["stress_closed_drawdown_usd"],
            "managed_stress_net_usd": managed_metrics["stress_net_usd"],
            "managed_stress_profit_factor": managed_metrics[
                "stress_profit_factor"
            ],
            "managed_closed_drawdown_usd": managed_metrics[
                "stress_closed_drawdown_usd"
            ],
            "v1_trades": v1_metrics["trades"],
            "managed_trades": managed_metrics["trades"],
        },
        "shared_account": {
            "v1_combined_stress_net_usd": v1_combined_metrics["stress_net_usd"],
            "v1_combined_stress_profit_factor": v1_combined_metrics[
                "stress_profit_factor"
            ],
            "v1_combined_closed_drawdown_usd": v1_combined_metrics[
                "stress_closed_drawdown_usd"
            ],
            "v1_combined_floating_drawdown_usd": float(
                v1_floating["maximum_drawdown_usd"]
            ),
            "managed_combined_stress_net_usd": managed_combined_metrics[
                "stress_net_usd"
            ],
            "managed_combined_stress_profit_factor": managed_combined_metrics[
                "stress_profit_factor"
            ],
            "managed_combined_closed_drawdown_usd": managed_combined_metrics[
                "stress_closed_drawdown_usd"
            ],
            "managed_combined_floating_drawdown_usd": float(
                managed_floating["maximum_drawdown_usd"]
            ),
            "maximum_routed_open_addons": maximum_routed_open,
            "maximum_routed_addon_initial_risk_usd": maximum_routed_risk,
            "managed_floating": managed_floating,
        },
        "routing_reason_counts": routing["reason"].value_counts().to_dict(),
        "required_windows": records(windows),
        "full_history_checks": full_checks,
        "market_data_audit": market_audit,
        "research_controls": config["research_controls"],
        "execution_authorized": False,
        "interpretation": (
            (
                "The locked cross-asset feature addition improved every "
                "historical model, economic, and risk gate. It remains "
                "development evidence and requires prospective proof plus MT5 "
                "parity."
            )
            if passed
            else (
                "The locked cross-asset feature addition failed one or more "
                "coverage, model, economic, window, or drawdown gates. This "
                "exact V5 is quarantined and cannot be deployed or tuned in "
                "place."
            )
        ),
    }
    serializable_result = json.loads(json.dumps(result, default=str))
    result["result_sha256"] = canonical_sha256(serializable_result)

    names = config["outputs"]
    snapshot_predictions.to_parquet(
        outputs / names["snapshot_predictions"], index=False
    )
    managed_candidates.to_parquet(
        outputs / names["managed_candidates"], index=False
    )
    managed_accepted.to_parquet(outputs / names["accepted"], index=False)
    routing.to_parquet(outputs / names["routing"], index=False)
    annual.to_csv(outputs / names["annual_models"], index=False)
    windows.assign(checks=windows["checks"].map(json.dumps)).to_csv(
        outputs / names["windows"], index=False
    )
    (outputs / names["result_json"]).write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    (outputs / names["result_markdown"]).write_text(
        markdown_result(result, annual, windows), encoding="utf-8"
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
        "schema_version": "xauusd_v6_causal_ml_early_exit_crossasset_v5_manifest",
        "artifacts": artifacts,
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    (outputs / names["manifest"]).write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    progress("experiment complete")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
