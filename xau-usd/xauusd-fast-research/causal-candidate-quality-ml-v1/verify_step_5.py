from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
sys.path.insert(0, str(PACKAGE / "src"))

from step_3_common import sha256_file, verify_bound_file  # noqa: E402
from step_5_metrics import window_metrics  # noqa: E402
from step_5_portfolio import (  # noqa: E402
    floating_equity_curve,
    load_m5_bars,
    prepare_candidate_economics,
    run_policy,
    verify_market_manifest,
)
from step_5_runner import _acceptance  # noqa: E402


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    config_path = (
        PACKAGE / "config" / "step_5_shared_account_portfolio_contract_v1.json"
    )
    contract = load_json(config_path)
    output_dir = PACKAGE / str(contract["outputs"]["directory"])
    outputs = contract["outputs"]
    lock_path = output_dir / str(outputs["contract_lock"])
    lock = load_json(lock_path)
    if lock["definition"]["config_sha256"] != sha256_file(config_path):
        raise ValueError("Step 5 config differs from lock")
    for relative, expected in lock["definition"]["implementation_sha256"].items():
        if sha256_file(PACKAGE / relative) != expected:
            raise ValueError(f"Locked implementation changed: {relative}")
    bound = {
        name: verify_bound_file(REPO, spec, name)
        for name, spec in contract["bound_inputs"].items()
    }
    verify_market_manifest(lock["definition"]["market_source_manifest"])

    manifest_path = output_dir / str(outputs["artifact_manifest"])
    manifest = load_json(manifest_path)
    for name, artifact in manifest["artifacts"].items():
        path = REPO / str(artifact["path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.stat().st_size != int(artifact["bytes"]):
            raise ValueError(f"Artifact size mismatch: {name}")
        if sha256_file(path) != str(artifact["sha256"]):
            raise ValueError(f"Artifact hash mismatch: {name}")

    result = load_json(output_dir / str(outputs["result_json"]))
    acceptance = load_json(output_dir / str(outputs["acceptance"]))
    if result["decision"] != "STEP_5_HISTORICAL_PORTFOLIO_GATE_PASS_RESEARCH_ONLY":
        raise ValueError("Unexpected Step 5 evidence decision")
    required_false = (
        "ml_predictions_used",
        "ml_thresholds_used",
        "comex_used",
        "databento_api_accessed",
        "new_data_acquired",
        "runtime_changed",
        "shadow_demo_or_live_activated",
    )
    if any(bool(result[name]) for name in required_false):
        raise ValueError("Step 5 control state is not offline")
    if result["journey_rows_used"] != 0 or not result["research_only"]:
        raise ValueError("Step 5 population or authorization state is invalid")

    dataset = pd.read_parquet(bound["step_3_dataset"])
    economics = prepare_candidate_economics(dataset, contract["account"])
    stored_decisions = pd.read_parquet(output_dir / str(outputs["decision_ledger"]))
    stored_trades = pd.read_parquet(output_dir / str(outputs["accepted_trades"]))
    policy_states = result["policy_states"]
    primary_id = str(contract["acceptance_gates"]["primary_policy_id"])
    primary_ledger: pd.DataFrame | None = None
    for spec in contract["policies"]:
        policy_id = str(spec["policy_id"])
        decisions, ledger, state = run_policy(
            economics, spec=spec, contract=contract
        )
        observed = stored_decisions.loc[
            stored_decisions["policy_id"].eq(policy_id)
        ].sort_values(["entry_time", "candidate_id"], kind="stable")
        expected = decisions.sort_values(["entry_time", "candidate_id"], kind="stable")
        if observed["candidate_id"].tolist() != expected["candidate_id"].tolist():
            raise ValueError(f"Decision population mismatch: {policy_id}")
        if observed["accepted"].tolist() != expected["accepted"].tolist():
            raise ValueError(f"Accepted decision mismatch: {policy_id}")
        if observed["decision_reason"].tolist() != expected["decision_reason"].tolist():
            raise ValueError(f"Decision reason mismatch: {policy_id}")
        trade_ids = stored_trades.loc[
            stored_trades["policy_id"].eq(policy_id), "candidate_id"
        ].tolist()
        if trade_ids != ledger["candidate_id"].tolist():
            raise ValueError(f"Accepted trade ledger mismatch: {policy_id}")
        if int(policy_states[policy_id]["accepted_trades"]) != len(ledger):
            raise ValueError(f"Result trade count mismatch: {policy_id}")
        if spec["account_governor"]:
            if state["risk_invariants"] != policy_states[policy_id]["risk_invariants"]:
                raise ValueError(f"Risk invariant mismatch: {policy_id}")
            if state["hard_stop_triggered"] != policy_states[policy_id]["hard_stop_triggered"]:
                raise ValueError(f"Hard-stop mismatch: {policy_id}")
        if policy_id == primary_id:
            primary_ledger = ledger

    if primary_ledger is None:
        raise ValueError("Primary portfolio is absent")
    endpoint = (
        primary_ledger["gross_endpoint_pnl_usd"]
        - primary_ledger["implied_cost_usd"]
        - primary_ledger["pnl_usd"]
    )
    if float(endpoint.abs().max()) > 1e-8:
        raise ValueError("Primary endpoint P&L does not reconcile")

    bars, market_audit = load_m5_bars(
        contract["market_data"], lock["definition"]["market_source_manifest"]
    )
    expected_curve = floating_equity_curve(
        bars,
        primary_ledger,
        starting_equity_usd=float(contract["account"]["starting_equity_usd"]),
        bar_minutes=int(contract["market_data"]["bar_minutes"]),
    )
    observed_curve = pd.read_parquet(output_dir / str(outputs["primary_equity_curve"]))
    if not observed_curve["timestamp_utc"].equals(expected_curve["timestamp_utc"]):
        raise ValueError("Primary M5 curve timestamps differ")
    numeric = [column for column in expected_curve.columns if column != "timestamp_utc"]
    if not np.allclose(
        observed_curve[numeric].to_numpy(float),
        expected_curve[numeric].to_numpy(float),
        rtol=1e-12,
        atol=1e-9,
    ):
        raise ValueError("Primary M5 curve does not reproduce")

    windows = pd.read_parquet(output_dir / str(outputs["window_metrics"]))
    primary_windows = window_metrics(
        primary_ledger,
        expected_curve,
        policy_id=primary_id,
        windows=contract["evaluation"]["windows"],
        starting_equity_usd=float(contract["account"]["starting_equity_usd"]),
        top_winners_removed=int(contract["evaluation"]["top_winners_removed"]),
    ).sort_values("window", kind="stable")
    stored_primary_windows = windows.loc[
        windows["policy_id"].eq(primary_id)
    ].sort_values("window", kind="stable")
    compare_numeric = [
        "entries",
        "exits",
        "entries_per_weekday",
        "net_usd",
        "profit_factor",
        "closed_drawdown_usd",
        "floating_drawdown_usd",
        "maximum_open_positions",
        "maximum_open_initial_risk_usd",
        "top_winners_removed_net_usd",
    ]
    if not np.allclose(
        stored_primary_windows[compare_numeric].to_numpy(float),
        primary_windows[compare_numeric].to_numpy(float),
        rtol=1e-12,
        atol=1e-9,
        equal_nan=True,
    ):
        raise ValueError("Primary window metrics do not reproduce")

    stability = pd.read_parquet(output_dir / str(outputs["six_month_stability"]))
    recomputed_acceptance = _acceptance(
        windows, stability, policy_states[primary_id], contract
    )
    if recomputed_acceptance["checks"] != acceptance["checks"]:
        raise ValueError("Acceptance gates do not reproduce")
    if recomputed_acceptance["decision"] != acceptance["decision"]:
        raise ValueError("Acceptance decision does not reproduce")

    daily = pd.read_parquet(output_dir / str(outputs["daily_metrics"]))
    attribution = pd.read_parquet(output_dir / str(outputs["attribution"]))
    expected_policy_ids = {str(spec["policy_id"]) for spec in contract["policies"]}
    for frame, name in (
        (stored_decisions, "decisions"),
        (stored_trades, "trades"),
        (windows, "windows"),
        (daily, "daily"),
        (attribution, "attribution"),
        (stability, "stability"),
    ):
        if set(frame["policy_id"].unique()) != expected_policy_ids:
            raise ValueError(f"Policy coverage mismatch in {name}")

    print(
        json.dumps(
            {
                "decision": "STEP_5_VERIFIED",
                "evidence_decision": result["decision"],
                "artifact_manifest_sha256": sha256_file(manifest_path),
                "artifacts_verified": len(manifest["artifacts"]),
                "policies_verified": len(expected_policy_ids),
                "primary_trades": len(primary_ledger),
                "primary_full_net_usd": result["policies"][primary_id]["full_net_usd"],
                "primary_full_profit_factor": result["policies"][primary_id][
                    "full_profit_factor"
                ],
                "primary_full_floating_drawdown_usd": result["policies"][primary_id][
                    "full_floating_drawdown_usd"
                ],
                "m5_rows_replayed": market_audit["rows"],
                "passed_acceptance_checks": acceptance["passed_checks"],
                "required_acceptance_checks": acceptance["required_checks"],
                "ml_used": False,
                "runtime_changed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
