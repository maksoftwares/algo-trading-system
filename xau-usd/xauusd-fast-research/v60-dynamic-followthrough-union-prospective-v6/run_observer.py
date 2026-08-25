from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG = ROOT / "config" / "prospective.json"
RANKER = ROOT.parent / "v60-mature-source-health-rank-veto-prospective-v2" / "src" / "ranker.py"
BASE_EVIDENCE = ROOT.parent / "v60-mature-source-health-rank-veto-prospective-v2" / "src" / "evidence.py"
BASE_TICK_REPLAY = ROOT.parent / "v60-mature-source-health-rank-veto-prospective-v2" / "src" / "tick_replay.py"
EVIDENCE = ROOT / "src" / "evidence.py"
POLICY = ROOT / "src" / "policy.py"
SHARED_ROOT = ROOT.parent / "v60-v57-executed-health-rank-veto-prospective-v1"
sys.path.insert(0, str(SHARED_ROOT))

from src.observer import (
    broker_outcomes,
    build_snapshot,
    load_candidate_rows,
    utc_time,
    write_snapshot,
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_config(path: Path) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))
    authorization = config["authorization"]
    if not bool(authorization.get("read_only_mt5")):
        raise ValueError("MT5 observer must be explicitly read-only")
    if any(
        bool(authorization.get(key))
        for key in ("broker_actions", "runtime_changes", "demo_deployment", "live_deployment")
    ):
        raise ValueError("Prospective observer has forbidden authorization")
    locks = config["lock"]
    checks = (
        (Path(__file__), "observer_runner_sha256"),
        (POLICY, "policy_source_sha256"),
        (RANKER, "observer_ranker_sha256"),
        (BASE_EVIDENCE, "base_evidence_recorder_sha256"),
        (EVIDENCE, "evidence_recorder_sha256"),
        (BASE_TICK_REPLAY, "base_tick_replay_sha256"),
        (REPO_ROOT / locks["shared_observer"], "shared_observer_sha256"),
        (REPO_ROOT / locks["research_config"], "research_config_sha256"),
    )
    for source, key in checks:
        actual = sha256_file(source)
        if actual != str(locks[key]):
            raise ValueError(f"Locked observer input changed: {key}: {actual}")
    warm = REPO_ROOT / config["read_only_inputs"]["warm_start"]
    if sha256_file(warm) != locks["warm_start_sha256"]:
        raise ValueError("Locked prospective warm start changed")
    sources = REPO_ROOT / config["read_only_inputs"]["candidate_source_config"]
    if sha256_file(sources) != locks["candidate_source_config_sha256"]:
        raise ValueError("Locked candidate source config changed")
    return config


def read_mt5_observation(config: dict):
    import MetaTrader5 as mt5

    account = config["account"]
    if not mt5.initialize(path=str(account["terminal_exe"]), portable=True):
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    try:
        info = mt5.account_info()
        terminal = mt5.terminal_info()
        if info is None or terminal is None or not bool(terminal.connected):
            raise RuntimeError("MT5 read-only account state is unavailable")
        if int(info.login) != int(account["expected_login"]):
            raise RuntimeError(f"Wrong account: {info.login}")
        if str(info.server) != str(account["expected_server"]):
            raise RuntimeError(f"Wrong server: {info.server}")
        if int(info.trade_mode) != int(account["expected_trade_mode"]):
            raise RuntimeError("Observer terminal is not a demo account")
        deals = mt5.history_deals_get(
            utc_time(account["history_start_utc"]), datetime.now(UTC)
        )
        positions = mt5.positions_get(symbol=str(account["symbol"]))
        if deals is None or positions is None:
            raise RuntimeError(f"MT5 history read failed: {mt5.last_error()}")
        ranker = load_module("v60_dynamic_v6_ranker", RANKER)
        runtime = ranker.prepare_runtime(mt5, REPO_ROOT, config)
        candidates, _ = load_candidate_rows(config["read_only_inputs"])
        decisions, rank_audit = ranker.score_candidates(
            runtime, candidates, config["observer_ranker"]
        )
        policy = load_module("v60_dynamic_v6_feature_policy", POLICY)
        feature_audit = policy.attach_causal_features(
            runtime,
            candidates,
            decisions,
            maximum_bar_age_minutes=int(
                config["observer_ranker"]["maximum_feature_bar_age_minutes"]
            ),
        )
        return list(deals), list(positions), decisions, rank_audit, feature_audit
    finally:
        mt5.shutdown()


def run_once(config_path: Path) -> dict:
    config = load_config(config_path)
    prospective_contract_sha256 = sha256_file(config_path)
    cycle_started_at = datetime.now(UTC)
    deals, open_positions, decisions, rank_audit, feature_audit = read_mt5_observation(config)
    observed_at = datetime.now(UTC)
    status, rows = build_snapshot(config, deals, now=observed_at, rank_decisions=decisions)
    state = json.loads(
        Path(config["read_only_inputs"]["portfolio_state"]).read_text(encoding="utf-8")
    )
    account = config["account"]
    actual_outcomes = broker_outcomes(
        state,
        deals,
        source_id="*",
        magic={key: int(value) for key, value in account["source_magics"].items()},
        account_currency_per_usd=float(account["account_currency_per_usd"]),
    )
    warm_start = json.loads(
        (REPO_ROOT / config["read_only_inputs"]["warm_start"]).read_text(encoding="utf-8")
    )
    policy = load_module("v60_dynamic_v6_policy_apply", POLICY)
    policy_audit = policy.apply_dynamic_union(
        rows,
        decisions,
        warm_start=warm_start,
        broker_outcomes=actual_outcomes,
        boundary=utc_time(config["lock"]["evidence_start_inclusive_utc"]),
        v2_policy=config["lock"]["policy"],
        anti_rule=config["lock"]["anti_chase"],
    )
    for row in rows:
        row["prospective_contract_sha256"] = prospective_contract_sha256
    status["prospective_contract_sha256"] = prospective_contract_sha256
    status["policy_audit"] = policy_audit
    status["observer_ranker"] = rank_audit
    status["causal_feature_audit"] = feature_audit
    status["observation_timing"] = {
        "cycle_started_at_utc": cycle_started_at.isoformat().replace("+00:00", "Z"),
        "decision_completed_at_utc": observed_at.isoformat().replace("+00:00", "Z"),
        "decision_cycle_seconds": (observed_at - cycle_started_at).total_seconds(),
        "cycle_within_recording_delay_budget": (
            observed_at - cycle_started_at
        ).total_seconds()
        < float(config["acceptance"]["maximum_decision_recording_delay_seconds"]),
    }
    evidence = load_module("v60_dynamic_v6_evidence", EVIDENCE)
    evidence.attach_execution_details(
        rows,
        state,
        deals,
        account_currency_per_usd=float(account["account_currency_per_usd"]),
    )
    runtime = Path(config["outputs"]["runtime_directory"])
    status["evidence_chain"] = evidence.update_evidence_chain(
        runtime, rows, observed_at=observed_at
    )
    status["decision_timing"] = evidence.annotate_decision_timing(
        runtime,
        rows,
        maximum_delay_seconds=int(
            config["acceptance"]["maximum_decision_recording_delay_seconds"]
        ),
    )
    policy.refresh_status(status, rows, config["acceptance"])
    evidence.add_forward_comparison(status, rows, config["acceptance"])
    resolved = [
        row for row in rows if row["baseline_executed"] and row["broker_outcome_resolved"]
    ]
    feature_coverage = (
        sum(bool(row.get("causal_policy_features_complete")) for row in resolved)
        / len(resolved)
        if resolved
        else None
    )
    status["forward_comparison"]["resolved_causal_feature_coverage"] = feature_coverage
    status["gates"]["complete_resolved_causal_feature_coverage"] = (
        feature_coverage is not None
        and feature_coverage
        >= float(config["acceptance"]["minimum_resolved_causal_feature_coverage"])
    )
    equity_mark = evidence.build_equity_mark(
        rows,
        state,
        deals,
        open_positions,
        account_currency_per_usd=float(account["account_currency_per_usd"]),
        observed_at=datetime.now(UTC),
    )
    equity_audit = evidence.update_equity_marks(
        runtime,
        equity_mark,
        boundary=utc_time(config["lock"]["evidence_start_inclusive_utc"]),
        minimum_marks=int(config["acceptance"]["minimum_equity_marks"]),
    )
    status["forward_comparison"]["sampled_equity"] = equity_audit
    status["gates"]["minimum_equity_marks"] = bool(equity_audit["minimum_marks_gate"])
    status["gates"]["challenger_sampled_equity_drawdown_not_worse"] = bool(
        equity_audit["challenger_drawdown_not_worse_gate"]
    )
    status["decision"] = (
        "PROSPECTIVE_CONFIRMATION_PASSES_REVIEW_REQUIRED"
        if all(status["gates"].values())
        else "KEEP_DEPLOYED_V60_CONTINUE_COLLECTION"
    )
    write_snapshot(config, status, rows)
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description="Run read-only V60 dynamic union observer")
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=30)
    args = parser.parse_args()
    while True:
        try:
            status = run_once(args.config.resolve())
            print(json.dumps(status, sort_keys=True), flush=True)
        except Exception as exc:
            print(
                json.dumps(
                    {
                        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                        "status": "FAILED_CLOSED",
                        "error": f"{type(exc).__name__}: {exc}",
                        "broker_action_authorized": False,
                        "deployment_authorized": False,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            if args.once:
                return 1
        if args.once:
            return 0
        time.sleep(max(30, int(args.poll_seconds)))


if __name__ == "__main__":
    raise SystemExit(main())
