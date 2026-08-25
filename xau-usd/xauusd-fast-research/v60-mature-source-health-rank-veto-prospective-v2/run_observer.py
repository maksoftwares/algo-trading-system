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
RANKER = ROOT / "src" / "ranker.py"
EVIDENCE = ROOT / "src" / "evidence.py"
SHARED_ROOT = (
    REPO_ROOT
    / "xau-usd"
    / "xauusd-fast-research"
    / "v60-v57-executed-health-rank-veto-prospective-v1"
)
sys.path.insert(0, str(SHARED_ROOT))

from src.observer import (
    build_snapshot,
    load_candidate_rows,
    load_locked_config,
    utc_time,
    write_snapshot,
)


def verify_shared_observer(config: dict) -> None:
    path = REPO_ROOT / config["lock"]["shared_observer"]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != config["lock"]["shared_observer_sha256"]:
        raise ValueError("Shared prospective observer changed")


def load_ranker():
    spec = importlib.util.spec_from_file_location("v60_v2_all_source_ranker", RANKER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load observer ranker: {RANKER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_evidence():
    spec = importlib.util.spec_from_file_location("v60_v2_prospective_evidence", EVIDENCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load evidence recorder: {EVIDENCE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def verify_ranker(config: dict) -> None:
    actual = hashlib.sha256(RANKER.read_bytes()).hexdigest()
    if actual != str(config["lock"]["observer_ranker_sha256"]):
        raise ValueError("All-source observer ranker changed")


def verify_evidence(config: dict) -> None:
    actual = hashlib.sha256(EVIDENCE.read_bytes()).hexdigest()
    if actual != str(config["lock"]["evidence_recorder_sha256"]):
        raise ValueError("Prospective evidence recorder changed")


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
        if deals is None:
            raise RuntimeError(f"MT5 history read failed: {mt5.last_error()}")
        positions = mt5.positions_get(symbol=str(account["symbol"]))
        if positions is None:
            raise RuntimeError(f"MT5 positions read failed: {mt5.last_error()}")
        ranker = load_ranker()
        runtime = ranker.prepare_runtime(mt5, REPO_ROOT, config)
        candidates, _ = load_candidate_rows(config["read_only_inputs"])
        decisions, rank_audit = ranker.score_candidates(
            runtime, candidates, config["observer_ranker"]
        )
        return list(deals), list(positions), decisions, rank_audit
    finally:
        mt5.shutdown()


def run_once(config_path: Path) -> dict:
    config = load_locked_config(config_path)
    verify_shared_observer(config)
    verify_ranker(config)
    verify_evidence(config)
    observed_at = datetime.now(UTC)
    deals, open_positions, rank_decisions, rank_audit = read_mt5_observation(config)
    status, rows = build_snapshot(
        config, deals, now=observed_at, rank_decisions=rank_decisions
    )
    status["observer_ranker"] = rank_audit
    evidence = load_evidence()
    state = json.loads(
        Path(config["read_only_inputs"]["portfolio_state"]).read_text(
            encoding="utf-8"
        )
    )
    evidence.attach_execution_details(
        rows,
        state,
        deals,
        account_currency_per_usd=float(
            config["account"]["account_currency_per_usd"]
        ),
    )
    evidence.add_forward_comparison(status, rows, config["acceptance"])
    status["evidence_chain"] = evidence.update_evidence_chain(
        Path(config["outputs"]["runtime_directory"]),
        rows,
        observed_at=observed_at,
    )
    equity_mark = evidence.build_equity_mark(
        rows,
        state,
        deals,
        open_positions,
        account_currency_per_usd=float(
            config["account"]["account_currency_per_usd"]
        ),
        observed_at=observed_at,
    )
    equity_audit = evidence.update_equity_marks(
        Path(config["outputs"]["runtime_directory"]),
        equity_mark,
        boundary=utc_time(config["lock"]["evidence_start_inclusive_utc"]),
        minimum_marks=int(config["acceptance"]["minimum_equity_marks"]),
    )
    status["forward_comparison"]["sampled_equity"] = equity_audit
    status["gates"]["minimum_equity_marks"] = bool(
        equity_audit["minimum_marks_gate"]
    )
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
    parser = argparse.ArgumentParser(description="Run the read-only V60 V2 observer")
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=300)
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
