from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn

from src.veto import (
    LANE_ROOT,
    annual_walk_forward_predictions,
    attach_candidate_regimes,
    build_training_corpus,
    canonical_sha256,
    closed_drawdown,
    load_module,
    profit_factor,
    resolve_path,
    sha256_file,
    trade_metrics,
    validate_feature_contract,
    verify_sources,
    window_comparison,
)


CONFIG_PATH = LANE_ROOT / "config" / "v6_causal_ml_veto_v1.json"


def serializable_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    result = frame.copy()
    if "checks" in result:
        result["checks"] = result["checks"].map(dict)
    return result.to_dict(orient="records")


def markdown_result(
    result: dict[str, Any], annual: pd.DataFrame, windows: pd.DataFrame
) -> str:
    annual_csv = annual.to_csv(index=False, float_format="%.4f").rstrip()
    visible = windows.drop(columns=["checks"]).to_csv(
        index=False, float_format="%.3f"
    ).rstrip()
    return "\n".join(
        [
            "# V6 Causal ML Veto V1 Result",
            "",
            f"Decision: **{result['decision']}**",
            "",
            "Historical research only. Execution is not authorized.",
            "",
            "## Veto Behavior",
            "",
            f"- Frozen V6 nominations: {result['veto_behavior']['candidate_trades']}",
            f"- ML-selected nominations: {result['veto_behavior']['selected_trades']}",
            f"- Accepted beside V60: {result['veto_behavior']['accepted_trades']}",
            f"- Winning trades retained: {result['veto_behavior']['winning_trade_retention_pct']:.1f}%",
            f"- Rejected trades that were losses: {result['veto_behavior']['rejected_trade_loss_pct']:.1f}%",
            "",
            "## Shared Account",
            "",
            f"- V60 stress net: ${result['shared_account']['v60_stress_net_usd']:.2f}",
            f"- V60 plus ML stress net: ${result['shared_account']['ml_combined_stress_net_usd']:.2f}",
            f"- V60 PF: {result['shared_account']['v60_stress_profit_factor']:.3f}",
            f"- V60 plus ML PF: {result['shared_account']['ml_combined_stress_profit_factor']:.3f}",
            f"- V60 closed drawdown: ${result['shared_account']['v60_closed_drawdown_usd']:.2f}",
            f"- V60 plus ML closed drawdown: ${result['shared_account']['ml_combined_closed_drawdown_usd']:.2f}",
            f"- V60 floating drawdown: ${result['shared_account']['v60_floating_drawdown_usd']:.2f}",
            f"- V60 plus ML floating drawdown: ${result['shared_account']['ml_combined_floating_drawdown_usd']:.2f}",
            "",
            "## Annual Models",
            "",
            "```csv",
            annual_csv,
            "```",
            "",
            "## Required Windows",
            "",
            "```csv",
            visible,
            "```",
            "",
            "## Interpretation",
            "",
            result["interpretation"],
            "",
        ]
    )


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    observed = verify_sources(config)
    feature_names = validate_feature_contract(config)
    outputs = LANE_ROOT / config["outputs"]["directory"]
    outputs.mkdir(parents=True, exist_ok=True)

    previous = load_module(
        "v6_causal_replication_dependency",
        resolve_path(config["sources"]["v6_implementation"]["path"]),
    )
    previous_config = json.loads(
        resolve_path(config["sources"]["v6_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    transitive_hashes = previous.verify_sources(previous_config)
    contract = {
        "schema_version": "xauusd_v6_causal_ml_veto_v1_contract",
        "config_sha256": sha256_file(CONFIG_PATH),
        "source_hashes": observed,
        "transitive_v6_source_hashes": transitive_hashes,
        "feature_names": feature_names,
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

    corpus, corpus_audit = build_training_corpus(
        previous, previous_config, config
    )
    external_modules = previous.load_external_modules(previous_config)
    context = external_modules["specialist"].load_context()
    candidates = pd.read_parquet(
        resolve_path(config["sources"]["v6_candidates"]["path"])
    )
    candidates = attach_candidate_regimes(candidates, context)
    predictions, annual = annual_walk_forward_predictions(
        corpus, candidates, config
    )
    selected = predictions.loc[predictions["ml_selected"]].copy()

    baseline = pd.read_parquet(resolve_path(config["sources"]["v60_ledger"]["path"]))
    for column in ("signal_time", "entry_time", "exit_time"):
        baseline[column] = pd.to_datetime(baseline[column], utc=True)
    raw_accepted_source = pd.read_parquet(
        resolve_path(config["sources"]["v6_accepted"]["path"])
    )
    raw_accepted_source["entry_time"] = pd.to_datetime(
        raw_accepted_source["entry_time"], utc=True
    )
    raw_accepted_source["exit_time"] = pd.to_datetime(
        raw_accepted_source["exit_time"], utc=True
    )
    limits = previous_config["shared_account_limits"]
    raw_accepted, _ = previous.route_candidates(baseline, predictions, limits)
    if set(raw_accepted["trade_id"]) != set(raw_accepted_source["trade_id"]):
        raise ValueError("Raw V6 routing no longer reproduces the frozen accepted ledger")
    ml_accepted, routing = previous.route_candidates(baseline, selected, limits)

    windows = window_comparison(
        baseline,
        raw_accepted,
        ml_accepted,
        config["windows"],
        config,
    )
    top = int(config["gates"]["top_winners_removed"])
    v60_metrics = trade_metrics(baseline, top)
    raw_metrics = trade_metrics(raw_accepted, top)
    ml_metrics = trade_metrics(ml_accepted, top)
    ml_combined = pd.concat([baseline, ml_accepted], ignore_index=True).sort_values(
        ["exit_time", "trade_id"], kind="mergesort"
    )
    ml_combined_metrics = trade_metrics(ml_combined, top)

    audit_module = load_module(
        "v60_floating_audit_for_ml_veto",
        resolve_path(config["sources"]["v60_audit"]["path"]),
    )
    v60_config = json.loads(
        resolve_path(config["sources"]["v60_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    v60_result = json.loads(
        resolve_path(config["sources"]["v60_result"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    bars, market_audit = audit_module.load_m5_bars(v60_config["market_data"])
    curve = audit_module.floating_curve(
        bars,
        ml_combined,
        "fee_stress_pnl_usd",
        "fee_stress_open_cost_usd",
        int(v60_config["floating_equity"]["bar_minutes"]),
    )
    floating = audit_module.envelope_drawdown(curve)
    ml_floating_dd = float(floating["maximum_drawdown_usd"])
    v60_floating_dd = float(
        v60_result["fee_stress_floating"]["maximum_drawdown_usd"]
    )
    maximum_open_addons = int(curve["open_addons"].max())
    maximum_addon_risk = float(curve["addon_initial_risk_usd"].max())

    annual_aucs = annual["target_auc"].to_numpy(dtype=float)
    mean_auc = float(annual_aucs.mean())
    years_above_random = int((annual_aucs > 0.5).sum())
    full_checks = {
        "all_required_windows_pass": bool(windows["passed"].all()),
        "minimum_mean_annual_target_auc": mean_auc
        >= float(config["gates"]["minimum_mean_annual_target_auc"]),
        "minimum_years_auc_above_random": years_above_random
        >= int(config["gates"]["minimum_years_auc_above_random"]),
        "full_history_incremental_net_positive": ml_combined_metrics[
            "stress_net_usd"
        ]
        > v60_metrics["stress_net_usd"],
        "full_history_pf_no_worse_than_v60": ml_combined_metrics[
            "stress_profit_factor"
        ]
        >= v60_metrics["stress_profit_factor"],
        "full_history_closed_drawdown_no_worse_than_v60": ml_combined_metrics[
            "stress_closed_drawdown_usd"
        ]
        <= v60_metrics["stress_closed_drawdown_usd"] + 1e-9,
        "full_history_floating_drawdown_no_worse_than_v60": ml_floating_dd
        <= v60_floating_dd + 1e-9,
        "maximum_addon_open_positions": maximum_open_addons
        <= int(limits["maximum_addon_open_positions"]),
        "maximum_addon_concurrent_initial_risk_usd": maximum_addon_risk
        <= float(limits["maximum_addon_concurrent_initial_risk_usd"]) + 1e-9,
        "immutable_v60_ledger_hash_preserved": sha256_file(
            resolve_path(config["sources"]["v60_ledger"]["path"])
        )
        == config["sources"]["v60_ledger"]["sha256"],
    }
    passed = all(full_checks.values())

    selected_predictions = predictions.loc[predictions["ml_selected"]]
    rejected_predictions = predictions.loc[~predictions["ml_selected"]]
    all_winners = int(predictions["label"].sum())
    retained_winners = int(selected_predictions["label"].sum())
    rejected_losses = int((rejected_predictions["label"] == 0).sum())
    result = {
        "schema_version": "xauusd_v6_causal_ml_veto_v1_result",
        "decision": (
            "V6_CAUSAL_ML_VETO_HISTORICAL_GATE_PASS_REQUIRES_PROSPECTIVE"
            if passed
            else "V6_CAUSAL_ML_VETO_HISTORICAL_GATE_FAIL_QUARANTINED"
        ),
        "passed": passed,
        "contract_sha256": contract["contract_sha256"],
        "training_corpus": corpus_audit,
        "model_quality": {
            "mean_annual_target_auc": mean_auc,
            "years_auc_above_random": years_above_random,
            "annual": serializable_records(annual),
        },
        "veto_behavior": {
            "candidate_trades": len(predictions),
            "selected_trades": len(selected_predictions),
            "accepted_trades": len(ml_accepted),
            "raw_accepted_trades": len(raw_accepted),
            "winning_trade_retention_pct": (
                100.0 * retained_winners / all_winners if all_winners else 0.0
            ),
            "rejected_trade_loss_pct": (
                100.0 * rejected_losses / len(rejected_predictions)
                if len(rejected_predictions)
                else 0.0
            ),
        },
        "raw_v6": raw_metrics,
        "ml_v6": ml_metrics,
        "shared_account": {
            "v60_stress_net_usd": v60_metrics["stress_net_usd"],
            "v60_stress_profit_factor": v60_metrics["stress_profit_factor"],
            "v60_closed_drawdown_usd": v60_metrics[
                "stress_closed_drawdown_usd"
            ],
            "v60_floating_drawdown_usd": v60_floating_dd,
            "ml_combined_stress_net_usd": ml_combined_metrics["stress_net_usd"],
            "ml_combined_stress_profit_factor": ml_combined_metrics[
                "stress_profit_factor"
            ],
            "ml_combined_closed_drawdown_usd": ml_combined_metrics[
                "stress_closed_drawdown_usd"
            ],
            "ml_combined_floating_drawdown_usd": ml_floating_dd,
            "maximum_open_addons": maximum_open_addons,
            "maximum_addon_initial_risk_usd": maximum_addon_risk,
            "floating": floating,
        },
        "routing_reason_counts": routing["reason"].value_counts().to_dict(),
        "required_windows": serializable_records(windows),
        "full_history_checks": full_checks,
        "market_data_audit": market_audit,
        "research_controls": config["research_controls"],
        "execution_authorized": False,
        "interpretation": (
            (
                "The causal ML veto passed historical improvement gates, but all "
                "history remains development evidence. A new prospective shadow "
                "period and MT5 parity are required before any execution decision."
            )
            if passed
            else (
                "This exact ML veto is quarantined because it did not improve the "
                "frozen V6/V60 system across every preregistered quality and risk "
                "gate. It must not be deployed or tuned in place."
            )
        ),
    }
    result["result_sha256"] = canonical_sha256(result)

    names = config["outputs"]
    predictions.to_parquet(outputs / names["predictions"], index=False)
    ml_accepted.to_parquet(outputs / names["accepted"], index=False)
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
    artifacts = {}
    for path in sorted(outputs.iterdir()):
        if path.name == names["manifest"]:
            continue
        artifacts[path.name] = {
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
    manifest = {
        "schema_version": "xauusd_v6_causal_ml_veto_v1_manifest",
        "artifacts": artifacts,
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    (outputs / names["manifest"]).write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
