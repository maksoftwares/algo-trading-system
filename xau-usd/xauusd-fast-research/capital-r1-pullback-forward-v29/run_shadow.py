from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import math
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

from pullback import (  # noqa: E402
    PullbackSettings,
    canonical_sha,
    candidates_from_evaluations,
    dependency_sha256,
    evaluate_decisions,
    prepare_bars,
    rates_to_frame,
    utc_text,
)
from ml.a3_meta_v1.mt5_readonly import (  # noqa: E402
    MT5ConnectionSpec,
    ReadOnlyMT5Client,
)
from ml.specialist_shadow_v1 import (  # noqa: E402
    append_jsonl_once,
    assert_demo_read_only,
    atomic_write_json,
    read_jsonl,
)


UTC = timezone.utc


def load_config() -> dict[str, Any]:
    return json.loads(
        (ROOT / "config" / "capital_r1_pullback_forward_v29.json").read_text(
            encoding="utf-8"
        )
    )


def fetch_rates(
    client: ReadOnlyMT5Client,
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
) -> pd.DataFrame:
    rates = client.copy_rates_range(
        symbol, client.timeframe_value(timeframe), start, end
    )
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"MT5 returned no {timeframe} rates: {client.last_error()}")
    return rates_to_frame(rates)


def candidate_record(row: Any) -> dict[str, Any]:
    record = row._asdict()
    for key in ("decision_time_utc", "confirmation_bar_time_utc"):
        record[key] = utc_text(record[key])
    for key in (
        "stop_points",
        "break_distance_atr",
        "estimated_cost_r",
        "spread_points",
    ):
        record[key] = float(record[key])
    return record


def frozen_evaluation_record(row: pd.Series, observed_at: datetime) -> dict[str, Any]:
    record = {key: row[key] for key in row.index}
    record["decision_time_utc"] = utc_text(record["decision_time_utc"])
    record["observed_at_utc"] = utc_text(observed_at)
    record["raw_signal"] = bool(record["raw_signal"])
    for key in (
        "stop_points",
        "break_distance_atr",
        "estimated_cost_r",
        "spread_points",
    ):
        value = float(record[key])
        record[key] = value if math.isfinite(value) else None
    return record


def evaluation_from_record(record: dict[str, Any]) -> pd.DataFrame:
    restored = dict(record)
    restored.pop("observed_at_utc", None)
    restored["decision_time_utc"] = pd.Timestamp(restored["decision_time_utc"])
    return pd.DataFrame([restored])


def run_cycle() -> dict[str, Any]:
    config = load_config()
    source = config["source"]
    settings = PullbackSettings.from_mapping(config["settings"])
    dependency_digest = dependency_sha256(REPO_ROOT, config["contract_scope"])
    lock_path = (
        ROOT / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    )
    if not lock_path.is_file():
        raise FileNotFoundError("V29 contract lock is absent")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    signed_lock = dict(lock)
    observed_contract_sha = signed_lock.pop("contract_sha256")
    if observed_contract_sha != canonical_sha(signed_lock):
        raise ValueError("V29 contract payload hash is invalid")
    if lock["rule_dependency_sha256"] != dependency_digest:
        raise ValueError("V29 rule dependencies changed after lock")

    now = datetime.now(UTC)
    boundary = pd.Timestamp(source["forward_start_inclusive_utc"])
    runtime = Path(source["runtime_directory"])
    client = ReadOnlyMT5Client.from_installed_package()
    if not client.initialize(MT5ConnectionSpec(source["forward_terminal_exe"], True)):
        raise RuntimeError(f"MT5 initialize failed: {client.last_error()}")
    try:
        account = client.account_info()
        terminal_info = client.terminal_info()
        assert_demo_read_only(account, terminal_info)
        if int(account.login) != int(source["forward_account_login"]):
            raise RuntimeError(f"V29 account login changed: {account.login}")
        if str(account.server) != str(source["account_server"]):
            raise RuntimeError(f"V29 account server changed: {account.server}")
        symbol = client.symbol_info(source["symbol"])
        tick = client.symbol_info_tick(source["symbol"])
        if symbol is None or tick is None:
            raise RuntimeError("V29 XAUUSD symbol or tick is unavailable")
        warmup = source["forward_warmup_days"]
        m15 = fetch_rates(
            client,
            source["symbol"],
            "M15",
            now - timedelta(days=int(warmup["M15"])),
            now,
        )
        h1 = fetch_rates(
            client,
            source["symbol"],
            "H1",
            now - timedelta(days=int(warmup["H1"])),
            now,
        )
        h4 = fetch_rates(
            client,
            source["symbol"],
            "H4",
            now - timedelta(days=int(warmup["H4"])),
            now,
        )
        d1 = fetch_rates(
            client,
            source["symbol"],
            "D1",
            now - timedelta(days=int(warmup["D1"])),
            now,
        )
    finally:
        client.shutdown()

    latest_decision = pd.Timestamp(m15.iloc[-1]["time"])
    history_age_hours = (pd.Timestamp(now) - latest_decision).total_seconds() / 3600.0
    if history_age_hours < 0.0:
        raise ValueError("latest M15 bar is in the future")
    if history_age_hours > float(source["maximum_market_staleness_hours"]):
        raise ValueError(
            f"latest M15 bar is {history_age_hours:.2f} hours stale; maximum is "
            f"{source['maximum_market_staleness_hours']}"
        )
    point = float(symbol.point)
    if point <= 0.0 or abs(point - settings.point_size) > 1e-12:
        raise ValueError(f"V29 XAUUSD point changed: {point}")
    spread_points = max(0.0, (float(tick.ask) - float(tick.bid)) / point)
    prepared = prepare_bars(m15, h1, h4, d1, settings)
    evaluations = evaluate_decisions(
        prepared,
        pd.DataFrame(
            {
                "decision_time_utc": [latest_decision],
                "spread_points": [spread_points],
            }
        ),
        settings,
    )
    decision_path = runtime / config["outputs"]["decision_state_log"]
    decision_added = 0
    decision_states = read_jsonl(decision_path)
    if latest_decision >= boundary:
        decision_key = utc_text(latest_decision)
        existing = next(
            (
                record
                for record in decision_states
                if record.get("decision_time_utc") == decision_key
            ),
            None,
        )
        if existing is None:
            frozen = frozen_evaluation_record(evaluations.iloc[0], now)
            decision_added = int(
                append_jsonl_once(decision_path, frozen, "decision_time_utc")
            )
            decision_states.append(frozen)
        else:
            evaluations = evaluation_from_record(existing)
        candidates = candidates_from_evaluations(evaluations, dependency_digest)
    else:
        candidates = candidates_from_evaluations(
            evaluations.iloc[0:0], dependency_digest
        )

    candidate_path = runtime / config["outputs"]["candidate_log"]
    added = 0
    for row in candidates.itertuples(index=False):
        added += int(
            append_jsonl_once(candidate_path, candidate_record(row), "candidate_id")
        )
    all_candidates = read_jsonl(candidate_path)
    evaluation = evaluations.iloc[0]
    status = {
        "schema_version": "xauusd_capital_r1_pullback_shadow_runtime_v29",
        "updated_at_utc": utc_text(now),
        "status": (
            "ACTIVE_READ_ONLY_CANDIDATE_SHADOW"
            if pd.Timestamp(now) >= boundary
            else "WAITING_FORWARD_BOUNDARY"
        ),
        "account_login": int(account.login),
        "account_server": str(account.server),
        "symbol": source["symbol"],
        "latest_decision_time_utc": utc_text(latest_decision),
        "latest_market_history_age_hours": history_age_hours,
        "forward_warmup_days": source["forward_warmup_days"],
        "latest_raw_signal": bool(evaluation["raw_signal"]),
        "latest_regime": str(evaluation["regime"]),
        "latest_guard_action": str(evaluation["guard_action"]),
        "latest_guard_reason": str(evaluation["guard_reason"]),
        "candidates_added_this_cycle": added,
        "candidate_count": len(all_candidates),
        "decision_state_added_this_cycle": decision_added,
        "decision_state_count": len(decision_states),
        "rule_dependency_sha256": dependency_digest,
        "economic_outcomes_opened": False,
        "trade_permission": False,
        "broker_action_allowed": False,
        "python_execution_authorized": False,
    }
    atomic_write_json(runtime / config["outputs"]["runtime_status"], status)
    return status


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run locked read-only R1 pullback candidate shadow"
    )
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=10)
    args = parser.parse_args()
    while True:
        try:
            status = run_cycle()
            print(json.dumps(status, sort_keys=True), flush=True)
        except Exception as exc:
            config = load_config()
            failure = {
                "schema_version": "xauusd_capital_r1_pullback_shadow_runtime_v29",
                "updated_at_utc": utc_text(datetime.now(UTC)),
                "status": "FAILED_CLOSED",
                "error": f"{type(exc).__name__}: {exc}",
                "economic_outcomes_opened": False,
                "trade_permission": False,
                "broker_action_allowed": False,
                "python_execution_authorized": False,
            }
            atomic_write_json(
                Path(config["source"]["runtime_directory"])
                / config["outputs"]["runtime_status"],
                failure,
            )
            print(json.dumps(failure, sort_keys=True), file=sys.stderr, flush=True)
            if args.once:
                return 1
        if args.once:
            return 0
        time.sleep(max(5, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
