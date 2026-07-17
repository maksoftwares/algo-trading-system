from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
if str(PHASE1_ROOT) not in sys.path:
    sys.path.insert(0, str(PHASE1_ROOT))

from ml.a3_meta_v1.mt5_readonly import MT5ConnectionSpec, ReadOnlyMT5Client  # noqa: E402
from ml.specialist_shadow_v1 import (  # noqa: E402
    DEFAULT_RUNTIME,
    DEFAULT_TERMINAL,
    HISTORY_DAYS,
    POLL_SECONDS,
    SPECIALIST_ID,
    SYMBOL,
    append_jsonl_once,
    assert_demo_read_only,
    atomic_write_json,
    evaluate_r1,
    last_completed_h4,
    load_frozen_r1,
    mt5_rates_to_m5,
    resolve_all_candidates,
    summarize_outcomes,
    utc_text,
)


def run_cycle(terminal: Path, runtime: Path) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    frozen = load_frozen_r1(REPO_ROOT)
    client = ReadOnlyMT5Client.from_installed_package()
    initialized = client.initialize(MT5ConnectionSpec(str(terminal), True))
    if not initialized:
        raise RuntimeError(f"MT5 initialize failed: {client.last_error()}")
    try:
        account = client.account_info()
        terminal_info = client.terminal_info()
        assert_demo_read_only(account, terminal_info)
        symbol = client.symbol_info(SYMBOL)
        if symbol is None:
            raise RuntimeError(f"MT5 symbol is unavailable: {SYMBOL}")
        completed = last_completed_h4(now)
        rates = client.copy_rates_range(
            SYMBOL,
            client.timeframe_value("M5"),
            now - timedelta(days=HISTORY_DAYS),
            now,
        )
        m5 = mt5_rates_to_m5(rates, point_size=float(symbol.point), completed_through=completed)
        state, candidate = evaluate_r1(m5, frozen, completed_through=completed)
    finally:
        client.shutdown()

    states_path = runtime / "r1_evaluations.jsonl"
    candidates_path = runtime / "r1_candidates.jsonl"
    state_added = append_jsonl_once(states_path, state, "state_id")
    candidate_added = False
    if candidate is not None:
        candidate_added = append_jsonl_once(candidates_path, candidate, "candidate_id")

    tick_dir = terminal.parent / "MQL5" / "Files"
    outcomes = resolve_all_candidates(candidates_path, tick_dir, now_utc=now)
    atomic_write_json(runtime / "r1_outcomes_latest.json", outcomes)
    status = {
        "schema_version": "xau_specialist_shadow_runtime_v1",
        "updated_at_utc": utc_text(now),
        "status": "ACTIVE_READ_ONLY_SHADOW",
        "specialist_id": SPECIALIST_ID,
        "account_login": int(account.login),
        "account_server": str(account.server),
        "symbol": SYMBOL,
        "completed_h4_through_utc": utc_text(completed),
        "m5_history_rows": len(m5),
        "m5_history_start_utc": utc_text(m5.iloc[0]["bar_start_utc"]),
        "m5_history_end_utc": utc_text(m5.iloc[-1]["bar_end_utc"]),
        "contract_hash": frozen.contract_hash,
        "latest_decision": state["decision_reason"],
        "state_added": state_added,
        "candidate_added": candidate_added,
        "candidate_count": sum(1 for _ in candidates_path.open("r", encoding="utf-8"))
        if candidates_path.exists()
        else 0,
        "outcome_counts": summarize_outcomes(outcomes),
        "trade_permission": False,
        "broker_action_allowed": False,
        "python_execution_authorized": False,
    }
    atomic_write_json(runtime / "runtime_status.json", status)
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the read-only frozen R1 shadow observer")
    parser.add_argument("--terminal", type=Path, default=DEFAULT_TERMINAL)
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=POLL_SECONDS)
    args = parser.parse_args()

    while True:
        try:
            status = run_cycle(args.terminal.resolve(), args.runtime.resolve())
            print(json.dumps(status, sort_keys=True), flush=True)
        except Exception as exc:
            failure = {
                "schema_version": "xau_specialist_shadow_runtime_v1",
                "updated_at_utc": utc_text(datetime.now(timezone.utc)),
                "status": "FAILED_CLOSED",
                "error": f"{type(exc).__name__}: {exc}",
                "trade_permission": False,
                "broker_action_allowed": False,
                "python_execution_authorized": False,
            }
            atomic_write_json(args.runtime.resolve() / "runtime_status.json", failure)
            print(json.dumps(failure, sort_keys=True), file=sys.stderr, flush=True)
            if args.once:
                return 1
        if args.once:
            return 0
        time.sleep(max(15, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
