from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
PHASE1_ROOT = REPO_ROOT / "xau-usd" / "xauusd-phase1"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(PHASE1_ROOT))

from core_shadow import (  # noqa: E402
    build_feature_frame,
    generate_regime_candidates,
    load_frozen,
)
from ml.a3_meta_v1.mt5_readonly import (  # noqa: E402
    MT5ConnectionSpec,
    ReadOnlyMT5Client,
)
from ml.specialist_shadow_v1 import (  # noqa: E402
    append_jsonl_once,
    assert_demo_read_only,
    assert_market_history_fresh,
    atomic_write_json,
    last_completed_h4,
    mt5_rates_to_m5,
    read_jsonl,
    utc_text,
)


def _json_record(row: Any) -> dict[str, Any]:
    record = row._asdict()
    for key in ("signal_time_utc", "scheduled_entry_time_utc"):
        record[key] = utc_text(record[key])
    record["origin_attempt"] = int(record["origin_attempt"])
    record["direction_sign"] = int(record["direction_sign"])
    for key in ("signal_atr", "stop_atr", "hold_hours"):
        record[key] = float(record[key])
    return record


def run_cycle(repo_root: Path, package_root: Path) -> dict[str, Any]:
    frozen = load_frozen(repo_root, package_root)
    config = frozen.package_config
    source = config["source"]
    forward = config["forward"]
    lock_path = (
        package_root
        / config["outputs"]["directory"]
        / config["outputs"]["contract_lock"]
    )
    if not lock_path.is_file():
        raise FileNotFoundError("V28 contract lock is absent")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock["rule_dependency_sha256"] != frozen.dependency_sha256:
        raise ValueError("V28 rule dependencies changed after lock")

    now = datetime.now(timezone.utc)
    terminal = Path(source["terminal_exe"])
    runtime = Path(source["runtime_directory"])
    client = ReadOnlyMT5Client.from_installed_package()
    if not client.initialize(MT5ConnectionSpec(str(terminal), True)):
        raise RuntimeError(f"MT5 initialize failed: {client.last_error()}")
    try:
        account = client.account_info()
        terminal_info = client.terminal_info()
        assert_demo_read_only(account, terminal_info)
        if int(account.login) != int(source["account_login"]):
            raise RuntimeError("V28 account login changed")
        if str(account.server) != str(source["account_server"]):
            raise RuntimeError("V28 account server changed")
        symbol = client.symbol_info(str(source["symbol"]))
        if symbol is None:
            raise RuntimeError("V28 XAUUSD symbol is unavailable")
        completed = last_completed_h4(now)
        rates = client.copy_rates_range(
            str(source["symbol"]),
            client.timeframe_value("M5"),
            now - timedelta(days=int(source["history_days"])),
            now,
        )
        m5 = mt5_rates_to_m5(
            rates, point_size=float(symbol.point), completed_through=completed
        )
        # The exact R2/R3 feature path aggregates this bookkeeping field but
        # never consumes it in a signal rule.
        m5["tick_count"] = 1.0
        age_hours = assert_market_history_fresh(
            m5,
            now_utc=now,
            maximum_staleness_hours=int(source["maximum_m5_staleness_hours"]),
        )
        build_frame = build_feature_frame(m5, frozen)
        candidates = generate_regime_candidates(
            build_frame,
            frozen,
            start_inclusive=pd.Timestamp(forward["start_inclusive_utc"]),
            end_exclusive=completed + pd.Timedelta(nanoseconds=1),
            require_next_bar=False,
        )
    finally:
        client.shutdown()

    candidate_path = runtime / "r2_r3_candidates.jsonl"
    added = 0
    for row in candidates.itertuples(index=False):
        added += int(
            append_jsonl_once(candidate_path, _json_record(row), "candidate_id")
        )
    all_candidates = read_jsonl(candidate_path)
    by_specialist: dict[str, int] = {}
    for row in all_candidates:
        key = str(row["specialist_id"])
        by_specialist[key] = by_specialist.get(key, 0) + 1
    boundary = pd.Timestamp(forward["start_inclusive_utc"])
    status = {
        "schema_version": "xauusd_capital_core_shadow_runtime_v28",
        "updated_at_utc": utc_text(now),
        "status": (
            "ACTIVE_READ_ONLY_CANDIDATE_SHADOW"
            if pd.Timestamp(now) >= boundary
            else "WAITING_FORWARD_BOUNDARY"
        ),
        "account_login": int(account.login),
        "account_server": str(account.server),
        "symbol": str(source["symbol"]),
        "completed_h4_through_utc": utc_text(completed),
        "m5_history_rows": int(len(m5)),
        "m5_history_age_hours": age_hours,
        "feature_rows": int(len(build_frame)),
        "candidate_rows_this_cycle": int(len(candidates)),
        "candidates_added_this_cycle": added,
        "candidate_counts": dict(sorted(by_specialist.items())),
        "rule_dependency_sha256": frozen.dependency_sha256,
        "economic_outcomes_opened": False,
        "trade_permission": False,
        "broker_action_allowed": False,
        "python_execution_authorized": False,
    }
    atomic_write_json(runtime / "runtime_status.json", status)
    return status


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run frozen read-only R2/R3 Core shadow"
    )
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=60)
    args = parser.parse_args()
    while True:
        try:
            status = run_cycle(REPO_ROOT, ROOT)
            print(json.dumps(status, sort_keys=True), flush=True)
        except Exception as exc:
            failure = {
                "schema_version": "xauusd_capital_core_shadow_runtime_v28",
                "updated_at_utc": utc_text(datetime.now(timezone.utc)),
                "status": "FAILED_CLOSED",
                "error": f"{type(exc).__name__}: {exc}",
                "economic_outcomes_opened": False,
                "trade_permission": False,
                "broker_action_allowed": False,
                "python_execution_authorized": False,
            }
            config = json.loads(
                (
                    ROOT / "config" / "capital_core_same_period_shadow_v28.json"
                ).read_text(encoding="utf-8")
            )
            atomic_write_json(
                Path(config["source"]["runtime_directory"]) / "runtime_status.json",
                failure,
            )
            print(json.dumps(failure, sort_keys=True), file=sys.stderr, flush=True)
            if args.once:
                return 1
        if args.once:
            return 0
        time.sleep(max(15, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
