from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn

from src.early_exit import (
    LANE_ROOT,
    annual_walk_forward_predictions,
    apply_first_exit_signal,
    build_snapshots,
    canonical_sha256,
    load_module,
    resolve_path,
    sha256_file,
    trade_comparison,
    validate_feature_contract,
    verify_sources,
)


CONFIG_PATH = LANE_ROOT / "config" / "v6_causal_ml_early_exit_v3.json"


def records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    result = frame.copy()
    if "checks" in result:
        result["checks"] = result["checks"].map(dict)
    return result.to_dict(orient="records")


def markdown_result(
    result: dict[str, Any], annual: pd.DataFrame, windows: pd.DataFrame
) -> str:
    return "\n".join(
        [
            "# V6 Causal ML Early Exit V3 Result",
            "",
            f"Decision: **{result['decision']}**",
            "",
            "Historical research only. Execution is not authorized.",
            "",
            "## Management Behavior",
            "",
            f"- Frozen V1 selected nominations: {result['management']['selected_nominations']}",
            f"- Early exits before routing: {result['management']['early_exit_nominations']}",
            f"- Early-exit share: {result['management']['early_exit_share_pct']:.1f}%",
            f"- Trigger precision: {result['management']['trigger_precision_pct']:.1f}%",
            f"- Accepted managed trades: {result['management']['accepted_managed_trades']}",
            f"- Net dollars saved before routing: ${result['management']['nomination_net_improvement_usd']:.2f}",
            "",
            "## V6 Sleeve",
            "",
            f"- Frozen V1 net / PF / DD: ${result['v6_sleeve']['v1_stress_net_usd']:.2f} / "
            f"{result['v6_sleeve']['v1_stress_profit_factor']:.3f} / "
            f"${result['v6_sleeve']['v1_closed_drawdown_usd']:.2f}",
            f"- Managed V3 net / PF / DD: ${result['v6_sleeve']['managed_stress_net_usd']:.2f} / "
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
            f"- Managed V3 combined net / PF / closed DD / floating DD: "
            f"${result['shared_account']['managed_combined_stress_net_usd']:.2f} / "
            f"{result['shared_account']['managed_combined_stress_profit_factor']:.3f} / "
            f"${result['shared_account']['managed_combined_closed_drawdown_usd']:.2f} / "
            f"${result['shared_account']['managed_combined_floating_drawdown_usd']:.2f}",
            "",
            "## Annual Model Audit",
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
            "## Interpretation",
            "",
            result["interpretation"],
            "",
        ]
    )


def main() -> None:
    started = time.perf_counter()

    def progress(message: str) -> None:
        elapsed = time.perf_counter() - started
        print(f"[{elapsed:8.1f}s] {message}", flush=True)

    progress("verifying locked sources")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    observed = verify_sources(config)
    feature_names = validate_feature_contract(config)
    outputs = LANE_ROOT / config["outputs"]["directory"]
    outputs.mkdir(parents=True, exist_ok=True)

    v1 = load_module(
        "v6_veto_v1_dependency_for_early_exit",
        resolve_path(config["sources"]["v1_implementation"]["path"]),
    )
    v1_config = json.loads(
        resolve_path(config["sources"]["v1_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    v1_source_hashes = v1.verify_sources(v1_config)
    reproduction = load_module(
        "v6_reproduction_dependency_for_early_exit",
        v1.resolve_path(v1_config["sources"]["v6_implementation"]["path"]),
    )
    reproduction_config = json.loads(
        v1.resolve_path(v1_config["sources"]["v6_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    transitive_hashes = reproduction.verify_sources(reproduction_config)
    contract = {
        "schema_version": "xauusd_v6_causal_ml_early_exit_v3_contract",
        "config_sha256": sha256_file(CONFIG_PATH),
        "implementation_sha256": sha256_file(
            LANE_ROOT / "src" / "early_exit.py"
        ),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "source_hashes": observed,
        "v1_source_hashes": v1_source_hashes,
        "transitive_v6_source_hashes": transitive_hashes,
        "feature_names": feature_names,
        "snapshots": config["snapshots"],
        "model": config["model"],
        "walk_forward": config["walk_forward"],
        "windows": config["windows"],
        "gates": config["gates"],
        "sklearn_version": sklearn.__version__,
        "research_controls": config["research_controls"],
    }
    contract["contract_sha256"] = canonical_sha256(contract)
    (outputs / config["outputs"]["contract_lock"]).write_text(
        json.dumps(contract, indent=2, sort_keys=True), encoding="utf-8"
    )

    progress("building broad V6 outcome corpus")
    broad_corpus, broad_audit = v1.build_training_corpus(
        reproduction, reproduction_config, v1_config
    )
    external_modules = reproduction.load_external_modules(reproduction_config)
    context = external_modules["specialist"].load_context()
    progress("building broad post-entry snapshots")
    training_snapshots, training_snapshot_audit = build_snapshots(
        broad_corpus,
        context,
        config,
        reproduction_config["execution_stress"],
    )

    v1_predictions = pd.read_parquet(
        resolve_path(config["sources"]["v1_predictions"]["path"])
    )
    for column in ("scan_time", "entry_time", "exit_time"):
        v1_predictions[column] = pd.to_datetime(v1_predictions[column], utc=True)
    selected = v1_predictions.loc[v1_predictions["ml_selected"]].copy()
    progress("building frozen V1 target snapshots")
    target_snapshots, target_snapshot_audit = build_snapshots(
        selected,
        context,
        config,
        reproduction_config["execution_stress"],
    )
    progress("fitting annual walk-forward classifiers")
    snapshot_predictions, annual = annual_walk_forward_predictions(
        training_snapshots, target_snapshots, config
    )
    progress("applying first-signal management and rerouting")
    managed_candidates, management_actions = apply_first_exit_signal(
        selected, snapshot_predictions
    )

    baseline = pd.read_parquet(
        v1.resolve_path(v1_config["sources"]["v60_ledger"]["path"])
    )
    for column in ("signal_time", "entry_time", "exit_time"):
        baseline[column] = pd.to_datetime(baseline[column], utc=True)
    frozen_source = pd.read_parquet(
        resolve_path(config["sources"]["v1_accepted"]["path"])
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
    windows = trade_comparison(
        frozen_accepted,
        managed_accepted,
        baseline,
        config["windows"],
        v1.trade_metrics,
        config,
    )

    progress("rebuilding frozen and managed floating equity curves")
    audit = load_module(
        "v60_floating_audit_for_early_exit",
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
    v1_result = json.loads(
        resolve_path(config["sources"]["v1_result"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    recorded_v1_floating = float(
        v1_result["shared_account"]["ml_combined_floating_drawdown_usd"]
    )
    if not np.isclose(
        float(v1_floating["maximum_drawdown_usd"]),
        recorded_v1_floating,
        atol=1e-9,
    ):
        raise ValueError("Frozen V1 floating drawdown no longer reproduces")

    early_actions = management_actions.loc[
        management_actions["management_action"].eq("EARLY_EXIT")
    ].copy()
    first_triggers = (
        snapshot_predictions.loc[snapshot_predictions["exit_trigger"]]
        .sort_values(["source_trade_id", "checkpoint_minutes"], kind="mergesort")
        .drop_duplicates("source_trade_id", keep="first")
    )
    trigger_precision = (
        float(first_triggers["label"].mean()) if len(first_triggers) else 0.0
    )
    early_share = len(early_actions) / len(managed_candidates)
    annual_aucs = annual["target_auc"].to_numpy(dtype=float)
    mean_auc = float(annual_aucs.mean())
    years_above_random = int((annual_aucs > 0.5).sum())
    maximum_open_addons = int(managed_curve["open_addons"].max())
    maximum_addon_risk = float(
        managed_curve["addon_initial_risk_usd"].max()
    )
    full_checks = {
        "minimum_mean_annual_target_auc": mean_auc
        >= float(config["gates"]["minimum_mean_annual_target_auc"]),
        "minimum_years_auc_above_random": years_above_random
        >= int(config["gates"]["minimum_years_auc_above_random"]),
        "minimum_trigger_precision": trigger_precision
        >= float(config["gates"]["minimum_trigger_precision"]),
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
        "maximum_addon_open_positions": maximum_open_addons
        <= int(limits["maximum_addon_open_positions"]),
        "maximum_addon_concurrent_initial_risk_usd": maximum_addon_risk
        <= float(limits["maximum_addon_concurrent_initial_risk_usd"]) + 1e-9,
        "immutable_v1_predictions_hash_preserved": sha256_file(
            resolve_path(config["sources"]["v1_predictions"]["path"])
        )
        == config["sources"]["v1_predictions"]["sha256"],
    }
    passed = all(full_checks.values())
    nomination_improvement = float(
        (
            managed_candidates["fee_stress_pnl_usd"]
            - managed_candidates["original_fee_stress_pnl_usd"]
        ).sum()
    )
    result = {
        "schema_version": "xauusd_v6_causal_ml_early_exit_v3_result",
        "decision": (
            "V6_CAUSAL_ML_EARLY_EXIT_V3_HISTORICAL_GATE_PASS_REQUIRES_PROSPECTIVE"
            if passed
            else "V6_CAUSAL_ML_EARLY_EXIT_V3_HISTORICAL_GATE_FAIL_QUARANTINED"
        ),
        "passed": passed,
        "contract_sha256": contract["contract_sha256"],
        "broad_training_corpus": broad_audit,
        "training_snapshots": training_snapshot_audit,
        "target_snapshots": target_snapshot_audit,
        "model_quality": {
            "mean_annual_target_auc": mean_auc,
            "years_auc_above_random": years_above_random,
            "annual": records(annual),
        },
        "management": {
            "selected_nominations": int(len(managed_candidates)),
            "early_exit_nominations": int(len(early_actions)),
            "early_exit_share_pct": 100.0 * early_share,
            "trigger_precision_pct": 100.0 * trigger_precision,
            "accepted_managed_trades": int(len(managed_accepted)),
            "nomination_net_improvement_usd": nomination_improvement,
            "beneficial_early_exits": int(first_triggers["label"].sum()),
            "harmful_or_small_early_exits": int(
                len(first_triggers) - first_triggers["label"].sum()
            ),
            "checkpoint_counts": early_actions[
                "management_checkpoint_minutes"
            ].value_counts().to_dict(),
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
            "maximum_open_addons": maximum_open_addons,
            "maximum_addon_initial_risk_usd": maximum_addon_risk,
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
                "The locked post-entry classifier improved the frozen historical "
                "system across all gates. It remains research-only and requires "
                "prospective evidence plus MT5 parity before authorization."
            )
            if passed
            else (
                "This exact post-entry classifier is quarantined because it did "
                "not improve every preregistered discrimination, P&L, drawdown, "
                "window, and shared-risk gate. It must not be deployed or tuned "
                "in place."
            )
        ),
    }
    result["result_sha256"] = canonical_sha256(result)

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
        "schema_version": "xauusd_v6_causal_ml_early_exit_v3_manifest",
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
