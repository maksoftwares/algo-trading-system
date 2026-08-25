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


def verify_ranker(config: dict) -> None:
    actual = hashlib.sha256(RANKER.read_bytes()).hexdigest()
    if actual != str(config["lock"]["observer_ranker_sha256"]):
        raise ValueError("All-source observer ranker changed")


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
        ranker = load_ranker()
        runtime = ranker.prepare_runtime(mt5, REPO_ROOT, config)
        candidates, _ = load_candidate_rows(config["read_only_inputs"])
        decisions, rank_audit = ranker.score_candidates(
            runtime, candidates, config["observer_ranker"]
        )
        return list(deals), decisions, rank_audit
    finally:
        mt5.shutdown()


def run_once(config_path: Path) -> dict:
    config = load_locked_config(config_path)
    verify_shared_observer(config)
    verify_ranker(config)
    deals, rank_decisions, rank_audit = read_mt5_observation(config)
    status, rows = build_snapshot(
        config, deals, rank_decisions=rank_decisions
    )
    status["observer_ranker"] = rank_audit
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
