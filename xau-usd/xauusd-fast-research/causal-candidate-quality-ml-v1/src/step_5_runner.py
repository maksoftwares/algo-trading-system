from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from step_3_common import sha256_file, stable_parquet, verify_bound_file, write_json
from step_5_metrics import (
    attribution_metrics,
    daily_metrics,
    six_month_stability,
    window_metrics,
)
from step_5_portfolio import (
    floating_equity_curve,
    load_m5_bars,
    prepare_candidate_economics,
    run_policy,
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _acceptance(
    windows: pd.DataFrame,
    stability: pd.DataFrame,
    state: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    gates = contract["acceptance_gates"]
    primary_id = str(gates["primary_policy_id"])
    primary = windows.loc[windows["policy_id"].eq(primary_id)].set_index("window")
    checks: dict[str, bool] = {}
    for window, minimum in gates["minimum_profit_factor_by_window"].items():
        value = primary.at[window, "profit_factor"]
        checks[f"profit_factor_{window}"] = pd.notna(value) and float(value) >= float(
            minimum
        )
    for window, minimum in gates["minimum_net_usd_by_window"].items():
        checks[f"net_usd_{window}"] = float(primary.at[window, "net_usd"]) > float(
            minimum
        )
    for window, minimum in gates["minimum_entries_per_weekday_by_window"].items():
        checks[f"entries_per_weekday_{window}"] = float(
            primary.at[window, "entries_per_weekday"]
        ) >= float(minimum)
    checks["floating_drawdown_FULL"] = float(
        primary.at["FULL", "floating_drawdown_fraction_of_start"]
    ) <= float(gates["maximum_floating_drawdown_fraction"])
    primary_stability = stability.loc[stability["policy_id"].eq(primary_id)]
    positive_fraction = float(primary_stability["positive"].mean())
    checks["positive_six_month_blocks"] = positive_fraction >= float(
        gates["minimum_positive_six_month_block_fraction"]
    )
    for window, minimum in gates[
        "minimum_top_winners_removed_net_usd_by_window"
    ].items():
        checks[f"top_winners_removed_net_{window}"] = float(
            primary.at[window, "top_winners_removed_net_usd"]
        ) > float(minimum)
    checks["family_concentration_5Y"] = float(
        primary.at["5Y", "maximum_single_family_entry_fraction"]
    ) <= float(gates["maximum_single_family_entry_fraction_5Y"])
    checks["risk_invariants"] = bool(state["risk_invariants_pass"])
    checks["hard_stop_not_triggered"] = not bool(state["hard_stop_triggered"])
    passed = all(checks.values())
    return {
        "schema_version": "xauusd_step_5_acceptance_gates_v1",
        "primary_policy_id": primary_id,
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "required_checks": len(checks),
        "positive_six_month_block_fraction": positive_fraction,
        "decision": contract["decision_policy"]["pass"]
        if passed
        else contract["decision_policy"]["fail"],
        "research_only": True,
        "runtime_authorized": False,
    }


def _artifact_manifest(
    output_dir: Path,
    repo_root: Path,
    *,
    decision: str,
    lock_sha256: str,
) -> dict[str, Any]:
    artifacts: dict[str, Any] = {}
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.name == "STEP_5_ARTIFACT_MANIFEST.json":
            continue
        artifacts[path.relative_to(output_dir).as_posix()] = {
            "path": path.relative_to(repo_root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    return {
        "schema_version": "xauusd_step_5_artifact_manifest_v1",
        "decision": decision,
        "contract_lock_sha256": lock_sha256,
        "runtime_changed": False,
        "artifacts": artifacts,
    }


def _window_attribution(
    ledger: pd.DataFrame,
    *,
    policy_id: str,
    windows: Mapping[str, list[str]],
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for window, bounds in windows.items():
        start, end = (pd.Timestamp(value) for value in bounds)
        local = ledger.loc[
            ledger["label_end_time"].ge(start) & ledger["label_end_time"].lt(end)
        ]
        attribution = attribution_metrics(local, policy_id=policy_id)
        if len(attribution):
            attribution.insert(1, "window", window)
            frames.append(attribution)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _markdown_result(
    result: Mapping[str, Any],
    windows: pd.DataFrame,
    acceptance: Mapping[str, Any],
) -> str:
    primary_id = str(acceptance["primary_policy_id"])
    primary = windows.loc[
        windows["policy_id"].eq(primary_id)
        & windows["window"].isin(["3M", "6M", "1Y", "2Y", "5Y", "10Y", "FULL"])
    ]
    lines = [
        "# Step 5 Locked Shared-Account Portfolio Evaluation",
        "",
        f"Decision: `{result['decision']}`",
        "",
        f"Primary policy: `{primary_id}`",
        "",
        "| Window | Entries | Entries/weekday | Net USD | PF | Floating DD USD |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in primary.itertuples(index=False):
        pf = "n/a" if pd.isna(row.profit_factor) else f"{float(row.profit_factor):.3f}"
        lines.append(
            f"| {row.window} | {int(row.entries):,} | "
            f"{float(row.entries_per_weekday):.3f} | "
            f"{float(row.net_usd):,.2f} | {pf} | "
            f"{float(row.floating_drawdown_usd):,.2f} |"
        )
    failed = [name for name, passed in acceptance["checks"].items() if not passed]
    lines.extend(
        [
            "",
            f"Acceptance checks: `{acceptance['passed_checks']}` / "
            f"`{acceptance['required_checks']}` passed.",
            f"Failed checks: `{', '.join(failed) if failed else 'none'}`.",
            "",
            "This is exposed-history research only. ML, Databento, COMEX, MT5, "
            "shadow, demo, live, and runtime actions were not used or changed.",
            "",
        ]
    )
    return "\n".join(lines)


def run_step_5(
    repo_root: Path, package_root: Path, config_path: Path
) -> dict[str, Any]:
    contract = load_json(config_path)
    bound = {
        name: verify_bound_file(repo_root, spec, name)
        for name, spec in contract["bound_inputs"].items()
    }
    output_dir = package_root / str(contract["outputs"]["directory"])
    lock_path = output_dir / str(contract["outputs"]["contract_lock"])
    if not lock_path.is_file():
        raise ValueError("Step 5 contract must be locked before portfolio evaluation")
    lock = load_json(lock_path)
    if lock["definition"]["config_sha256"] != sha256_file(config_path):
        raise ValueError("Step 5 configuration changed after lock")
    for relative, expected in lock["definition"]["implementation_sha256"].items():
        if sha256_file(package_root / relative) != expected:
            raise ValueError(f"Step 5 implementation changed after lock: {relative}")
    lock_sha = sha256_file(lock_path)

    step3 = load_json(bound["step_3_result"])
    step4 = load_json(bound["step_4_result"])
    acceptance4 = load_json(bound["step_4_acceptance"])
    if step3["decision"] != "STEP_3_COUNTERFACTUAL_LABEL_AND_CAUSAL_FEATURE_BUILD_COMPLETE":
        raise ValueError("Step 3 evidence is not complete")
    if step4["decision"] != "MODEL_EVIDENCE_GATE_FAIL":
        raise ValueError("Step 5 requires the frozen Step 4 ML failure state")
    if acceptance4["runtime_authorized"]:
        raise ValueError("Step 4 unexpectedly authorized runtime")

    dataset = pd.read_parquet(bound["step_3_dataset"])
    economics = prepare_candidate_economics(dataset, contract["account"])
    bars, market_audit = load_m5_bars(
        contract["market_data"], lock["definition"]["market_source_manifest"]
    )
    outputs = contract["outputs"]
    evaluation = contract["evaluation"]
    start = pd.Timestamp(evaluation["data_start_inclusive_utc"])
    end = pd.Timestamp(evaluation["cutoff_exclusive_utc"])
    starting_equity = float(contract["account"]["starting_equity_usd"])

    decision_frames: list[pd.DataFrame] = []
    trade_frames: list[pd.DataFrame] = []
    window_frames: list[pd.DataFrame] = []
    daily_frames: list[pd.DataFrame] = []
    attribution_frames: list[pd.DataFrame] = []
    stability_frames: list[pd.DataFrame] = []
    policy_states: dict[str, Any] = {}
    primary_curve: pd.DataFrame | None = None
    primary_id = str(contract["acceptance_gates"]["primary_policy_id"])

    for spec in contract["policies"]:
        policy_id = str(spec["policy_id"])
        decisions, ledger, state = run_policy(
            economics, spec=spec, contract=contract
        )
        curve = floating_equity_curve(
            bars,
            ledger,
            starting_equity_usd=starting_equity,
            bar_minutes=int(contract["market_data"]["bar_minutes"]),
        )
        state["maximum_curve_open_positions"] = int(curve["open_positions"].max())
        state["maximum_curve_open_initial_risk_usd"] = float(
            curve["open_initial_risk_usd"].max()
        )
        state["maximum_curve_open_margin_usd"] = float(curve["open_margin_usd"].max())
        policy_states[policy_id] = state
        decision_frames.append(decisions)
        trade_frames.append(ledger)
        window_frames.append(
            window_metrics(
                ledger,
                curve,
                policy_id=policy_id,
                windows=evaluation["windows"],
                starting_equity_usd=starting_equity,
                top_winners_removed=int(evaluation["top_winners_removed"]),
            )
        )
        daily_frames.append(
            daily_metrics(
                ledger,
                policy_id=policy_id,
                start=start,
                end=end,
                starting_equity_usd=starting_equity,
            )
        )
        attribution_frames.append(
            _window_attribution(
                ledger, policy_id=policy_id, windows=evaluation["windows"]
            )
        )
        stability_frames.append(
            six_month_stability(
                ledger,
                policy_id=policy_id,
                start=pd.Timestamp(evaluation["six_month_stability_start_utc"]),
                end=end,
            )
        )
        if policy_id == primary_id:
            primary_curve = curve

    if primary_curve is None:
        raise ValueError("Primary policy did not run")
    decisions = pd.concat(decision_frames, ignore_index=True).sort_values(
        ["policy_id", "entry_time", "candidate_id"], kind="stable"
    )
    trades = pd.concat(trade_frames, ignore_index=True).sort_values(
        ["policy_id", "entry_time", "candidate_id"], kind="stable"
    )
    windows = pd.concat(window_frames, ignore_index=True).sort_values(
        ["policy_id", "window_start_utc"], kind="stable"
    )
    daily = pd.concat(daily_frames, ignore_index=True).sort_values(
        ["policy_id", "date_utc"], kind="stable"
    )
    attribution = pd.concat(attribution_frames, ignore_index=True).sort_values(
        ["policy_id", "window", "dimension", "value"], kind="stable"
    )
    stability = pd.concat(stability_frames, ignore_index=True).sort_values(
        ["policy_id", "block_start_utc"], kind="stable"
    )

    stable_parquet(decisions, output_dir / str(outputs["decision_ledger"]))
    stable_parquet(trades, output_dir / str(outputs["accepted_trades"]))
    stable_parquet(windows, output_dir / str(outputs["window_metrics"]))
    stable_parquet(daily, output_dir / str(outputs["daily_metrics"]))
    stable_parquet(attribution, output_dir / str(outputs["attribution"]))
    stable_parquet(stability, output_dir / str(outputs["six_month_stability"]))
    stable_parquet(primary_curve, output_dir / str(outputs["primary_equity_curve"]))

    acceptance = _acceptance(
        windows, stability, policy_states[primary_id], contract
    )
    write_json(output_dir / str(outputs["acceptance"]), acceptance)
    policy_summaries = {}
    for policy_id, group in windows.groupby("policy_id", sort=True):
        full = group.loc[group["window"].eq("FULL")].iloc[0]
        policy_summaries[policy_id] = {
            "accepted_trades": int(policy_states[policy_id]["accepted_trades"]),
            "full_net_usd": float(full["net_usd"]),
            "full_profit_factor": full["profit_factor"],
            "full_entries_per_weekday": float(full["entries_per_weekday"]),
            "full_floating_drawdown_usd": float(full["floating_drawdown_usd"]),
            "full_floating_drawdown_fraction_of_start": float(
                full["floating_drawdown_fraction_of_start"]
            ),
        }
    result = {
        "schema_version": "xauusd_step_5_result_v1",
        "decision": acceptance["decision"],
        "contract_lock_sha256": lock_sha,
        "primary_policy_id": primary_id,
        "canonical_candidate_rows": len(economics),
        "policies": policy_summaries,
        "policy_states": policy_states,
        "primary_window_metrics": windows.loc[
            windows["policy_id"].eq(primary_id)
        ].to_dict("records"),
        "acceptance_checks": acceptance["checks"],
        "market_data_audit": market_audit,
        "historical_outcomes_already_exposed": True,
        "research_only": True,
        "ml_predictions_used": False,
        "ml_thresholds_used": False,
        "journey_rows_used": 0,
        "comex_used": False,
        "databento_api_accessed": False,
        "new_data_acquired": False,
        "runtime_changed": False,
        "shadow_demo_or_live_activated": False,
    }
    write_json(output_dir / str(outputs["result_json"]), result)
    (output_dir / str(outputs["result_markdown"])).write_text(
        _markdown_result(result, windows, acceptance), encoding="utf-8"
    )
    manifest = _artifact_manifest(
        output_dir, repo_root, decision=result["decision"], lock_sha256=lock_sha
    )
    write_json(output_dir / str(outputs["artifact_manifest"]), manifest)
    result["artifact_manifest_sha256"] = sha256_file(
        output_dir / str(outputs["artifact_manifest"])
    )
    return result
