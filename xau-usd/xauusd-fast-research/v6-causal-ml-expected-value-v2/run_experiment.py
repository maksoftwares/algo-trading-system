from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import sklearn

from src.expected_value import (
    LANE_ROOT,
    annual_expected_value_predictions,
    canonical_sha256,
    load_module,
    resolve_path,
    sha256_file,
    verify_sources,
)


CONFIG_PATH = LANE_ROOT / "config" / "v6_causal_ml_expected_value_v2.json"


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
            "# V6 Causal ML Expected Value V2 Result",
            "",
            f"Decision: **{result['decision']}**",
            "",
            "Historical research only. Execution is not authorized.",
            "",
            "## Selection",
            "",
            f"- Frozen nominations: {result['selection']['candidate_trades']}",
            f"- Selected nominations: {result['selection']['selected_trades']}",
            f"- Accepted beside V60: {result['selection']['accepted_trades']}",
            "",
            "## V6 Comparison",
            "",
            f"- Raw V6 net/PF/DD: ${result['raw_v6']['stress_net_usd']:.2f} / "
            f"{result['raw_v6']['stress_profit_factor']:.3f} / "
            f"${result['raw_v6']['stress_closed_drawdown_usd']:.2f}",
            f"- V2 V6 net/PF/DD: ${result['ml_v6']['stress_net_usd']:.2f} / "
            f"{result['ml_v6']['stress_profit_factor']:.3f} / "
            f"${result['ml_v6']['stress_closed_drawdown_usd']:.2f}",
            "",
            "## Shared Account",
            "",
            f"- V60 net/PF/DD: ${result['shared_account']['v60_stress_net_usd']:.2f} / "
            f"{result['shared_account']['v60_stress_profit_factor']:.3f} / "
            f"${result['shared_account']['v60_closed_drawdown_usd']:.2f}",
            f"- V60 plus V2 net/PF/DD: "
            f"${result['shared_account']['ml_combined_stress_net_usd']:.2f} / "
            f"{result['shared_account']['ml_combined_stress_profit_factor']:.3f} / "
            f"${result['shared_account']['ml_combined_closed_drawdown_usd']:.2f}",
            f"- Floating drawdown: ${result['shared_account']['ml_combined_floating_drawdown_usd']:.2f}",
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
            windows.drop(columns=["checks"]).to_csv(
                index=False, float_format="%.3f"
            ).rstrip(),
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
    outputs = LANE_ROOT / config["outputs"]["directory"]
    outputs.mkdir(parents=True, exist_ok=True)
    v1 = load_module(
        "v6_ml_v1_dependency",
        resolve_path(config["sources"]["v1_implementation"]["path"]),
    )
    v1_config = json.loads(
        resolve_path(config["sources"]["v1_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    v1_hashes = v1.verify_sources(v1_config)
    contract = {
        "schema_version": "xauusd_v6_causal_ml_expected_value_v2_contract",
        "config_sha256": sha256_file(CONFIG_PATH),
        "source_hashes": observed,
        "transitive_v1_source_hashes": v1_hashes,
        "feature_names": v1.validate_feature_contract(v1_config),
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

    previous = v1.load_module(
        "v6_replication_dependency_for_ev",
        v1.resolve_path(v1_config["sources"]["v6_implementation"]["path"]),
    )
    previous_config = json.loads(
        v1.resolve_path(v1_config["sources"]["v6_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    corpus, corpus_audit = v1.build_training_corpus(
        previous, previous_config, v1_config
    )
    external = previous.load_external_modules(previous_config)
    candidates = pd.read_parquet(
        v1.resolve_path(v1_config["sources"]["v6_candidates"]["path"])
    )
    candidates = v1.attach_candidate_regimes(
        candidates, external["specialist"].load_context()
    )
    predictions, annual = annual_expected_value_predictions(
        corpus, candidates, config, v1_config, v1
    )
    selected = predictions.loc[predictions["ml_selected"]].copy()

    baseline = pd.read_parquet(
        v1.resolve_path(v1_config["sources"]["v60_ledger"]["path"])
    )
    for column in ("signal_time", "entry_time", "exit_time"):
        baseline[column] = pd.to_datetime(baseline[column], utc=True)
    raw_source = pd.read_parquet(
        v1.resolve_path(v1_config["sources"]["v6_accepted"]["path"])
    )
    for column in ("entry_time", "exit_time"):
        raw_source[column] = pd.to_datetime(raw_source[column], utc=True)
    limits = previous_config["shared_account_limits"]
    raw_accepted, _ = previous.route_candidates(baseline, predictions, limits)
    if set(raw_accepted["trade_id"]) != set(raw_source["trade_id"]):
        raise ValueError("Raw V6 routing no longer reproduces its frozen ledger")
    ml_accepted, routing = previous.route_candidates(baseline, selected, limits)

    windows = v1.window_comparison(
        baseline, raw_accepted, ml_accepted, config["windows"], config
    )
    top = int(config["gates"]["top_winners_removed"])
    v60_metrics = v1.trade_metrics(baseline, top)
    raw_metrics = v1.trade_metrics(raw_accepted, top)
    ml_metrics = v1.trade_metrics(ml_accepted, top)
    combined = pd.concat([baseline, ml_accepted], ignore_index=True).sort_values(
        ["exit_time", "trade_id"], kind="mergesort"
    )
    combined_metrics = v1.trade_metrics(combined, top)

    audit = v1.load_module(
        "v60_floating_audit_for_ev",
        v1.resolve_path(v1_config["sources"]["v60_audit"]["path"]),
    )
    v60_config = json.loads(
        v1.resolve_path(v1_config["sources"]["v60_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    v60_result = json.loads(
        v1.resolve_path(v1_config["sources"]["v60_result"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    bars, market_audit = audit.load_m5_bars(v60_config["market_data"])
    curve = audit.floating_curve(
        bars,
        combined,
        "fee_stress_pnl_usd",
        "fee_stress_open_cost_usd",
        int(v60_config["floating_equity"]["bar_minutes"]),
    )
    floating = audit.envelope_drawdown(curve)
    floating_dd = float(floating["maximum_drawdown_usd"])
    v60_floating_dd = float(
        v60_result["fee_stress_floating"]["maximum_drawdown_usd"]
    )
    maximum_open_addons = int(curve["open_addons"].max())
    maximum_addon_risk = float(curve["addon_initial_risk_usd"].max())

    mean_auc = float(annual["target_auc"].mean())
    mean_spearman = float(annual["target_spearman"].mean())
    positive_spearman_years = int(annual["target_spearman"].gt(0.0).sum())
    checks = {
        "all_required_windows_pass": bool(windows["passed"].all()),
        "minimum_mean_annual_target_auc": mean_auc
        >= float(config["gates"]["minimum_mean_annual_target_auc"]),
        "minimum_mean_annual_spearman": mean_spearman
        >= float(config["gates"]["minimum_mean_annual_spearman"]),
        "minimum_years_spearman_above_zero": positive_spearman_years
        >= int(config["gates"]["minimum_years_spearman_above_zero"]),
        "full_history_incremental_net_positive": combined_metrics[
            "stress_net_usd"
        ]
        > v60_metrics["stress_net_usd"],
        "full_history_pf_no_worse_than_v60": combined_metrics[
            "stress_profit_factor"
        ]
        >= v60_metrics["stress_profit_factor"],
        "full_history_closed_drawdown_no_worse_than_v60": combined_metrics[
            "stress_closed_drawdown_usd"
        ]
        <= v60_metrics["stress_closed_drawdown_usd"] + 1e-9,
        "full_history_floating_drawdown_no_worse_than_v60": floating_dd
        <= v60_floating_dd + 1e-9,
        "maximum_addon_open_positions": maximum_open_addons
        <= int(limits["maximum_addon_open_positions"]),
        "maximum_addon_concurrent_initial_risk_usd": maximum_addon_risk
        <= float(limits["maximum_addon_concurrent_initial_risk_usd"]) + 1e-9,
    }
    passed = all(checks.values())
    result = {
        "schema_version": "xauusd_v6_causal_ml_expected_value_v2_result",
        "decision": (
            "V6_CAUSAL_ML_EXPECTED_VALUE_V2_HISTORICAL_GATE_PASS_REQUIRES_PROSPECTIVE"
            if passed
            else "V6_CAUSAL_ML_EXPECTED_VALUE_V2_HISTORICAL_GATE_FAIL_QUARANTINED"
        ),
        "passed": passed,
        "contract_sha256": contract["contract_sha256"],
        "training_corpus": corpus_audit,
        "model_quality": {
            "mean_annual_target_auc": mean_auc,
            "mean_annual_target_spearman": mean_spearman,
            "years_spearman_above_zero": positive_spearman_years,
            "annual": records(annual),
        },
        "selection": {
            "candidate_trades": len(predictions),
            "selected_trades": int(predictions["ml_selected"].sum()),
            "accepted_trades": len(ml_accepted),
            "raw_accepted_trades": len(raw_accepted),
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
            "ml_combined_stress_net_usd": combined_metrics["stress_net_usd"],
            "ml_combined_stress_profit_factor": combined_metrics[
                "stress_profit_factor"
            ],
            "ml_combined_closed_drawdown_usd": combined_metrics[
                "stress_closed_drawdown_usd"
            ],
            "ml_combined_floating_drawdown_usd": floating_dd,
            "maximum_open_addons": maximum_open_addons,
            "maximum_addon_initial_risk_usd": maximum_addon_risk,
            "floating": floating,
        },
        "routing_reason_counts": routing["reason"].value_counts().to_dict(),
        "required_windows": records(windows),
        "full_history_checks": checks,
        "market_data_audit": market_audit,
        "research_controls": config["research_controls"],
        "execution_authorized": False,
        "interpretation": (
            (
                "V2 passed historical improvement gates, but all history remains "
                "development evidence. Prospective shadow observation and MT5 "
                "parity are required before any execution decision."
            )
            if passed
            else (
                "This exact expected-value model is quarantined because it did "
                "not improve V6 and V60 across every locked quality and risk gate. "
                "It must not be deployed or tuned in place."
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
        "schema_version": "xauusd_v6_causal_ml_expected_value_v2_manifest",
        "artifacts": artifacts,
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    (outputs / names["manifest"]).write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
