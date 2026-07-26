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
from step_5_1_account_currency import (  # noqa: E402
    account_policy_contract,
    build_account_economics,
    floating_account_curve,
    run_account_policy,
)
from step_5_1_runner import (  # noqa: E402
    _acceptance,
    _account_metric_inputs,
    _rename_metric_units,
)
from step_5_metrics import window_metrics  # noqa: E402
from step_5_portfolio import load_m5_bars  # noqa: E402


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    config_path = (
        PACKAGE / "config" / "step_5_1_account_currency_correction_v1.json"
    )
    correction = load_json(config_path)
    output_dir = PACKAGE / str(correction["outputs"]["directory"])
    outputs = correction["outputs"]
    lock_path = output_dir / str(outputs["contract_lock"])
    lock = load_json(lock_path)
    if lock["definition"]["config_sha256"] != sha256_file(config_path):
        raise ValueError("Step 5.1 config differs from lock")
    snapshot_path = output_dir / str(outputs["broker_snapshot"])
    if lock["definition"]["broker_snapshot_sha256"] != sha256_file(snapshot_path):
        raise ValueError("Step 5.1 broker snapshot differs from lock")
    for relative, expected in lock["definition"]["implementation_sha256"].items():
        if sha256_file(PACKAGE / relative) != expected:
            raise ValueError(f"Locked implementation changed: {relative}")
    bound = {
        name: verify_bound_file(REPO, spec, name)
        for name, spec in correction["bound_inputs"].items()
    }

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
    expected_artifacts = {
        str(value)
        for key, value in outputs.items()
        if key not in {"directory", "artifact_manifest"}
    }
    if set(manifest["artifacts"]) != expected_artifacts:
        raise ValueError("Step 5.1 artifact set is incomplete or unexpected")

    result = load_json(output_dir / str(outputs["result_json"]))
    acceptance = load_json(output_dir / str(outputs["acceptance_gates"]))
    snapshot = load_json(snapshot_path)
    if result["decision"] != "STEP_5_1_AED_PORTFOLIO_GATE_FAIL":
        raise ValueError("Unexpected Step 5.1 evidence decision")
    required_false = (
        "ml_used",
        "comex_used",
        "databento_api_accessed",
        "broker_action_performed",
        "runtime_changed",
        "shadow_demo_or_live_activated",
    )
    if any(bool(result[name]) for name in required_false):
        raise ValueError("Step 5.1 control state is not offline")
    if not result["research_only"] or not result["step_5_superseded_for_aed_account_claims"]:
        raise ValueError("Step 5.1 evidence boundary is invalid")
    if int(result["account_login"]) != int(snapshot["account"]["login"]):
        raise ValueError("Step 5.1 account login mismatch")
    if result["account_currency"] != snapshot["account"]["currency"]:
        raise ValueError("Step 5.1 account currency mismatch")

    step_5_contract = load_json(bound["step_5_config"])
    step_5_lock = load_json(bound["step_5_lock"])
    dataset = pd.read_parquet(bound["step_3_dataset"])
    economics, conversion = build_account_economics(
        dataset,
        step_5_contract=step_5_contract,
        broker_snapshot=snapshot,
    )
    account_contract = account_policy_contract(
        step_5_contract, snapshot, correction["policy_mapping"]
    )
    stored_decisions = pd.read_parquet(output_dir / str(outputs["decision_ledger"]))
    stored_trades = pd.read_parquet(output_dir / str(outputs["accepted_trades"]))
    states = result["policy_states"]
    primary_id = str(correction["acceptance"]["primary_policy_id"])
    primary_ledger: pd.DataFrame | None = None
    for spec in account_contract["policies"]:
        policy_id = str(spec["policy_id"])
        decisions, ledger, state = run_account_policy(
            economics, spec=spec, contract=account_contract
        )
        observed = stored_decisions.loc[
            stored_decisions["policy_id"].eq(policy_id)
        ].sort_values(["entry_time", "candidate_id"], kind="stable")
        expected = decisions.sort_values(
            ["entry_time", "candidate_id"], kind="stable"
        )
        for column in ("candidate_id", "accepted", "decision_reason"):
            if observed[column].tolist() != expected[column].tolist():
                raise ValueError(f"Decision {column} mismatch: {policy_id}")
        trade_ids = stored_trades.loc[
            stored_trades["policy_id"].eq(policy_id), "candidate_id"
        ].tolist()
        if trade_ids != ledger["candidate_id"].tolist():
            raise ValueError(f"Accepted ledger mismatch: {policy_id}")
        if int(states[policy_id]["accepted_trades"]) != len(ledger):
            raise ValueError(f"Accepted trade count mismatch: {policy_id}")
        if spec["account_governor"]:
            if state["risk_invariants"] != states[policy_id]["risk_invariants"]:
                raise ValueError(f"Risk invariants mismatch: {policy_id}")
            if state["hard_stop_triggered"] != states[policy_id]["hard_stop_triggered"]:
                raise ValueError(f"Hard stop mismatch: {policy_id}")
        if policy_id == primary_id:
            primary_ledger = ledger
    if primary_ledger is None:
        raise ValueError("Corrected primary portfolio is absent")

    endpoint = (
        primary_ledger["gross_endpoint_pnl_account"]
        - primary_ledger["implied_cost_account"]
        - primary_ledger["pnl_account"]
    )
    if float(endpoint.abs().max()) > 1e-8:
        raise ValueError("Primary account-currency P&L does not reconcile")
    if not np.allclose(
        economics["initial_risk_usd"],
        economics["source_initial_risk_usd"]
        * float(conversion["loss_account_per_source_usd"]),
    ):
        raise ValueError("Initial risk currency conversion does not reproduce")

    bars, market_audit = load_m5_bars(
        step_5_contract["market_data"],
        step_5_lock["definition"]["market_source_manifest"],
    )
    curve = floating_account_curve(
        bars,
        primary_ledger,
        starting_equity_account=float(conversion["starting_equity_account"]),
        bar_minutes=int(step_5_contract["market_data"]["bar_minutes"]),
        profit_rate=float(conversion["profit_account_per_source_usd"]),
        loss_rate=float(conversion["loss_account_per_source_usd"]),
    )
    observed_curve = pd.read_parquet(
        output_dir / str(outputs["primary_equity_curve"])
    )
    if not observed_curve["timestamp_utc"].equals(curve["timestamp_utc"]):
        raise ValueError("Primary account curve timestamps differ")
    numeric = [column for column in curve.columns if column != "timestamp_utc"]
    if not np.allclose(
        observed_curve[numeric].to_numpy(float),
        curve[numeric].to_numpy(float),
        rtol=1e-12,
        atol=1e-9,
    ):
        raise ValueError("Primary account curve does not reproduce")

    metric_ledger, metric_curve = _account_metric_inputs(primary_ledger, curve)
    expected_windows = _rename_metric_units(
        window_metrics(
            metric_ledger,
            metric_curve,
            policy_id=primary_id,
            windows=step_5_contract["evaluation"]["windows"],
            starting_equity_usd=float(conversion["starting_equity_account"]),
            top_winners_removed=int(
                step_5_contract["evaluation"]["top_winners_removed"]
            ),
        )
    ).sort_values("window", kind="stable")
    windows = pd.read_parquet(output_dir / str(outputs["window_metrics"]))
    observed_windows = windows.loc[
        windows["policy_id"].eq(primary_id)
    ].sort_values("window", kind="stable")
    compare_numeric = [
        "entries",
        "exits",
        "entries_per_weekday",
        "net_account",
        "profit_factor",
        "closed_drawdown_account",
        "floating_drawdown_account",
        "maximum_open_positions",
        "maximum_open_initial_risk_account",
        "top_winners_removed_net_account",
    ]
    if not np.allclose(
        observed_windows[compare_numeric].to_numpy(float),
        expected_windows[compare_numeric].to_numpy(float),
        rtol=1e-12,
        atol=1e-9,
        equal_nan=True,
    ):
        raise ValueError("Primary account window metrics do not reproduce")

    stability = pd.read_parquet(
        output_dir / str(outputs["six_month_stability"])
    )
    reproduced_acceptance = _acceptance(
        windows,
        stability,
        states[primary_id],
        step_5_contract=step_5_contract,
        correction_contract=correction,
    )
    if reproduced_acceptance["checks"] != acceptance["checks"]:
        raise ValueError("Step 5.1 acceptance checks do not reproduce")
    if reproduced_acceptance["decision"] != result["decision"]:
        raise ValueError("Step 5.1 decision does not reproduce")

    expected_policy_ids = {
        str(spec["policy_id"]) for spec in account_contract["policies"]
    }
    for output_name, label in (
        ("daily_metrics", "daily"),
        ("attribution", "attribution"),
        ("six_month_stability", "stability"),
    ):
        frame = pd.read_parquet(output_dir / str(outputs[output_name]))
        if set(frame["policy_id"].unique()) != expected_policy_ids:
            raise ValueError(f"Policy coverage mismatch in {label}")

    first_suspension = stored_decisions.loc[
        stored_decisions["policy_id"].eq(primary_id)
        & stored_decisions["decision_reason"].eq("REJECT_DRAWDOWN_SUSPENDED")
    ].sort_values("entry_time", kind="stable").iloc[0]
    print(
        json.dumps(
            {
                "decision": "STEP_5_1_VERIFIED",
                "evidence_decision": result["decision"],
                "artifact_manifest_sha256": sha256_file(manifest_path),
                "artifacts_verified": len(manifest["artifacts"]),
                "policies_verified": len(expected_policy_ids),
                "primary_trades": len(primary_ledger),
                "primary_full_net_account": result["policies"][primary_id][
                    "full_net_account"
                ],
                "primary_full_profit_factor": result["policies"][primary_id][
                    "full_profit_factor"
                ],
                "primary_full_floating_drawdown_account": result["policies"][
                    primary_id
                ]["full_floating_drawdown_account"],
                "first_drawdown_suspension_entry_utc": first_suspension[
                    "entry_time"
                ].isoformat(),
                "m5_rows_replayed": market_audit["rows"],
                "passed_acceptance_checks": acceptance["passed_checks"],
                "required_acceptance_checks": acceptance["required_checks"],
                "broker_action_performed": False,
                "runtime_changed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
