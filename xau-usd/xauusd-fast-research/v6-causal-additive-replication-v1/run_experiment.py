from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.reproduction import (
    LANE_ROOT,
    REPO_ROOT,
    annual_metrics,
    build_annual_candidates,
    build_variant_pool,
    canonical_sha256,
    closed_drawdown,
    evaluate_windows,
    load_external_modules,
    prepare_candidate_ledger,
    profit_factor,
    resolve_repo_path,
    route_candidates,
    sha256_file,
    verify_sources,
)


CONFIG_PATH = LANE_ROOT / "config" / "v6_causal_additive_replication_v1.json"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def serializable_frame(frame: pd.DataFrame) -> list[dict[str, Any]]:
    result = frame.copy()
    if "checks" in result:
        result["checks"] = result["checks"].map(dict)
    return result.to_dict(orient="records")


def write_markdown(result: dict[str, Any], windows: pd.DataFrame, annual: pd.DataFrame) -> str:
    window_text = windows.drop(columns=["checks"]).to_csv(index=False, float_format="%.3f")
    annual_text = annual.to_csv(index=False, float_format="%.3f")
    lines = [
        "# V6 Causal Additive Replication V1 Result",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "Historical research only. No trading execution is authorized.",
        "",
        "## Standalone Accepted Candidate",
        "",
        f"- Trades: {result['standalone']['trades']}",
        f"- Stress net: ${result['standalone']['stress_net_usd']:.2f}",
        f"- Stress PF: {result['standalone']['stress_profit_factor']:.3f}",
        f"- Win rate: {result['standalone']['win_rate_pct']:.1f}%",
        f"- Closed drawdown: ${result['standalone']['stress_closed_drawdown_usd']:.2f}",
        "",
        "## Shared Account",
        "",
        f"- V60 trades: {result['shared_account']['baseline_trades']}",
        f"- Accepted V6 trades: {result['shared_account']['accepted_candidate_trades']}",
        f"- Combined stress net: ${result['shared_account']['combined_stress_net_usd']:.2f}",
        f"- Combined stress PF: {result['shared_account']['combined_stress_profit_factor']:.3f}",
        f"- Buffered floating drawdown: ${result['shared_account']['buffered_floating_drawdown_usd']:.2f}",
        f"- Maximum open add-ons: {result['shared_account']['maximum_open_addons']}",
        f"- Maximum concurrent add-on risk: ${result['shared_account']['maximum_addon_initial_risk_usd']:.2f}",
        "",
        "## Required Windows",
        "",
        "```csv",
        window_text.rstrip(),
        "```",
        "",
        "## Candidate By Entry Year",
        "",
        "```csv",
        annual_text.rstrip(),
        "```",
        "",
        "## Interpretation",
        "",
        result["interpretation"],
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    observed = verify_sources(config)
    outputs = LANE_ROOT / config["outputs"]["directory"]
    outputs.mkdir(parents=True, exist_ok=True)

    contract = {
        "schema_version": "xauusd_v6_causal_additive_replication_v1_contract",
        "config_sha256": sha256_file(CONFIG_PATH),
        "observed_source_hashes": observed,
        "selection": config["selection"],
        "execution_stress": config["execution_stress"],
        "shared_account_limits": config["shared_account_limits"],
        "windows": config["windows"],
        "gates": config["gates"],
        "research_controls": config["research_controls"],
    }
    contract["contract_sha256"] = canonical_sha256(contract)
    (outputs / config["outputs"]["contract_lock"]).write_text(
        json.dumps(contract, indent=2, sort_keys=True), encoding="utf-8"
    )

    modules = load_external_modules(config)
    pool = build_variant_pool(modules)
    executed, selection_log = build_annual_candidates(
        pool, config["selection"]
    )
    candidates = prepare_candidate_ledger(
        executed, config["execution_stress"]
    )

    v60_ledger_path = resolve_repo_path(config["canonical_v60"]["ledger"]["path"])
    baseline = pd.read_parquet(v60_ledger_path)
    for column in ("signal_time", "entry_time", "exit_time"):
        baseline[column] = pd.to_datetime(baseline[column], utc=True)
    accepted, routing = route_candidates(
        baseline, candidates, config["shared_account_limits"]
    )
    windows = evaluate_windows(
        baseline,
        accepted,
        config["windows"],
        config["gates"],
        config["shared_account_limits"],
    )
    annual = annual_metrics(accepted)
    combined = pd.concat([baseline, accepted], ignore_index=True).sort_values(
        ["exit_time", "trade_id"], kind="mergesort"
    )

    audit_path = resolve_repo_path(config["canonical_v60"]["audit_module"]["path"])
    v60_audit = load_module("v60_floating_audit_for_v6", audit_path)
    v60_config = json.loads(
        resolve_repo_path(config["canonical_v60"]["config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    v60_result = json.loads(
        resolve_repo_path(config["canonical_v60"]["result"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    bars, market_audit = v60_audit.load_m5_bars(v60_config["market_data"])
    curve = v60_audit.floating_curve(
        bars,
        combined,
        "fee_stress_pnl_usd",
        "fee_stress_open_cost_usd",
        int(v60_config["floating_equity"]["bar_minutes"]),
    )
    floating = v60_audit.envelope_drawdown(curve)
    floating_dd = float(floating["maximum_drawdown_usd"])
    maximum_open_addons = int(curve["open_addons"].max())
    maximum_addon_risk = float(curve["addon_initial_risk_usd"].max())

    limits = config["shared_account_limits"]
    baseline_values = baseline["fee_stress_pnl_usd"].astype(float)
    baseline_pf = profit_factor(baseline_values)
    baseline_closed_dd = closed_drawdown(baseline_values)
    baseline_floating_dd = float(
        v60_result["fee_stress_floating"]["maximum_drawdown_usd"]
    )
    full_history_checks = {
        "all_required_windows_pass": bool(windows["passed"].all()),
        "canonical_v60_passed": bool(v60_result["passed"]),
        "maximum_addon_open_positions": maximum_open_addons
        <= int(limits["maximum_addon_open_positions"]),
        "maximum_addon_concurrent_initial_risk_usd": maximum_addon_risk
        <= float(limits["maximum_addon_concurrent_initial_risk_usd"]) + 1e-9,
        "maximum_combined_closed_drawdown_usd": closed_drawdown(
            combined["fee_stress_pnl_usd"]
        )
        <= float(limits["maximum_combined_closed_drawdown_usd"]),
        "maximum_buffered_floating_drawdown_usd": floating_dd
        <= float(limits["maximum_buffered_floating_drawdown_usd"]),
        "immutable_v60_ledger_hash_preserved": sha256_file(v60_ledger_path)
        == config["canonical_v60"]["ledger"]["sha256"],
    }
    passed = all(full_history_checks.values())
    accepted_values = accepted["fee_stress_pnl_usd"].astype(float)
    combined_values = combined["fee_stress_pnl_usd"].astype(float)
    result = {
        "schema_version": "xauusd_v6_causal_additive_replication_v1_result",
        "decision": (
            "V6_CAUSAL_ADDITIVE_HISTORICAL_GATE_PASS_REQUIRES_PROSPECTIVE"
            if passed
            else "V6_CAUSAL_ADDITIVE_HISTORICAL_GATE_FAIL_QUARANTINED"
        ),
        "passed": passed,
        "contract_sha256": contract["contract_sha256"],
        "pool_members": len(pool),
        "pre_route_candidate_trades": len(candidates),
        "standalone": {
            "trades": len(accepted),
            "win_rate_pct": 100.0 * float(accepted_values.gt(0.0).mean()),
            "stress_net_usd": float(accepted_values.sum()),
            "stress_profit_factor": profit_factor(accepted_values),
            "stress_closed_drawdown_usd": closed_drawdown(accepted_values),
        },
        "shared_account": {
            "baseline_trades": len(baseline),
            "accepted_candidate_trades": len(accepted),
            "combined_trades": len(combined),
            "baseline_stress_net_usd": float(
                baseline["fee_stress_pnl_usd"].sum()
            ),
            "baseline_stress_profit_factor": baseline_pf,
            "baseline_closed_drawdown_usd": baseline_closed_dd,
            "baseline_buffered_floating_drawdown_usd": baseline_floating_dd,
            "combined_stress_net_usd": float(combined_values.sum()),
            "combined_stress_profit_factor": profit_factor(combined_values),
            "combined_closed_drawdown_usd": closed_drawdown(combined_values),
            "buffered_floating_drawdown_usd": floating_dd,
            "maximum_open_addons": maximum_open_addons,
            "maximum_addon_initial_risk_usd": maximum_addon_risk,
            "floating": floating,
        },
        "comparison_to_v60": {
            "stress_net_delta_usd": float(combined_values.sum() - baseline_values.sum()),
            "stress_profit_factor_delta": profit_factor(combined_values) - baseline_pf,
            "closed_drawdown_delta_usd": closed_drawdown(combined_values)
            - baseline_closed_dd,
            "buffered_floating_drawdown_delta_usd": floating_dd
            - baseline_floating_dd,
        },
        "routing_reason_counts": routing["reason"].value_counts().to_dict(),
        "required_windows": serializable_frame(windows),
        "annual_candidate_metrics": serializable_frame(annual),
        "full_history_checks": full_history_checks,
        "market_data_audit": market_audit,
        "research_controls": config["research_controls"],
        "execution_authorized": False,
        "interpretation": (
            (
                "This historical result may nominate a new prospective research "
                "lane, but it cannot validate the candidate because all history "
                "through 2026-06-30 is development evidence. MT5 parity and "
                "genuinely new prospective observations are still required."
            )
            if passed
            else (
                "This exact candidate is quarantined. It added historical net "
                "profit, but it failed preregistered robustness and shared-account "
                "risk gates. It must not be translated to MT5 or deployed."
            )
        ),
    }
    result["result_sha256"] = canonical_sha256(result)

    output_map = config["outputs"]
    (outputs / output_map["selection_log"]).write_text(
        json.dumps(selection_log, indent=2, default=str), encoding="utf-8"
    )
    candidates.to_parquet(outputs / output_map["candidates"], index=False)
    accepted.to_parquet(outputs / output_map["accepted"], index=False)
    routing.to_parquet(outputs / output_map["routing"], index=False)
    annual.to_csv(outputs / output_map["annual"], index=False)
    windows.assign(checks=windows["checks"].map(json.dumps)).to_csv(
        outputs / output_map["windows"], index=False
    )
    (outputs / output_map["result_json"]).write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    (outputs / output_map["result_markdown"]).write_text(
        write_markdown(result, windows, annual), encoding="utf-8"
    )

    artifacts = {}
    for path in sorted(outputs.iterdir()):
        if path.name == output_map["manifest"]:
            continue
        artifacts[path.name] = {
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
    manifest = {
        "schema_version": "xauusd_v6_causal_additive_replication_v1_manifest",
        "artifacts": artifacts,
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    (outputs / output_map["manifest"]).write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
