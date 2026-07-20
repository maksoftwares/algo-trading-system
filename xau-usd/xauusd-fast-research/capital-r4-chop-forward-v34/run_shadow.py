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

from chop_forward import (  # noqa: E402
    add_historical_micro_placeholders,
    aggregate_capital_quotes,
    build_feature_frame,
    generate_forward_candidates,
    load_frozen,
    overlay_quote_bars,
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
    mt5_rates_to_m5,
    read_jsonl,
    utc_text,
)


def _tick_loader_config(config: dict[str, Any]) -> dict[str, Any]:
    source = config["source"]
    quality = config["data_quality"]
    return {
        "source": {
            "schema_version": source["tick_schema_version"],
            "account_login": source["account_login"],
            "account_server": source["account_server"],
            "symbol": source["symbol"],
        },
        "data_quality": {
            "maximum_timestamp_disagreement_ms": quality[
                "maximum_timestamp_disagreement_ms"
            ],
            "maximum_spread_field_error": quality[
                "maximum_spread_field_error"
            ],
        },
    }


def _json_record(row: Any, dependency_sha: str) -> dict[str, Any]:
    record = row._asdict()
    for key in ("signal_time_utc", "scheduled_entry_time_utc"):
        record[key] = utc_text(record[key])
    for key in ("component_priority", "origin_attempt", "direction_sign"):
        record[key] = int(record[key])
    for key in ("signal_atr", "stop_atr", "target_r", "hold_hours"):
        record[key] = float(record[key])
    record["rule_dependency_sha256"] = dependency_sha
    return record


def run_cycle(repo_root: Path, package_root: Path) -> dict[str, Any]:
    frozen = load_frozen(repo_root, package_root)
    config = frozen.package_config
    source = config["source"]
    forward = config["forward"]
    output = package_root / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    if not lock_path.is_file():
        raise FileNotFoundError("V34 contract lock is absent")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock["rule_dependency_sha256"] != frozen.dependency_sha256:
        raise ValueError("V34 rule dependencies changed after lock")

    now = datetime.now(timezone.utc)
    completed_through = pd.Timestamp(now).floor("5min")
    client = ReadOnlyMT5Client.from_installed_package()
    if not client.initialize(MT5ConnectionSpec(source["terminal_exe"], True)):
        raise RuntimeError(f"MT5 initialize failed: {client.last_error()}")
    try:
        account = client.account_info()
        terminal_info = client.terminal_info()
        assert_demo_read_only(account, terminal_info)
        if int(account.login) != int(source["account_login"]):
            raise RuntimeError("V34 account login changed")
        if str(account.server) != str(source["account_server"]):
            raise RuntimeError("V34 account server changed")
        symbol = client.symbol_info(str(source["symbol"]))
        if symbol is None:
            raise RuntimeError("V34 XAUUSD symbol is unavailable")
        rates = client.copy_rates_range(
            str(source["symbol"]),
            client.timeframe_value("M5"),
            now - timedelta(days=int(source["history_days"])),
            now,
        )
        historical = mt5_rates_to_m5(
            rates,
            point_size=float(symbol.point),
            completed_through=completed_through,
        )
        history_age_hours = assert_market_history_fresh(
            historical,
            now_utc=now,
            maximum_staleness_hours=int(source["maximum_m5_staleness_hours"]),
        )
    finally:
        client.shutdown()

    tick_paths = sorted(
        Path(source["tick_directory"]).glob(source["tick_filename_glob"])
    )
    ticks, tick_audit, _ = frozen.tick_loader_module.load_ticks(
        tick_paths, _tick_loader_config(config)
    )
    quote_bars = aggregate_capital_quotes(
        ticks,
        completed_through=completed_through,
        quality=config["data_quality"],
    )
    historical = add_historical_micro_placeholders(historical)
    combined = overlay_quote_bars(historical, quote_bars)
    frame = build_feature_frame(combined, frozen)
    candidates = generate_forward_candidates(
        frame,
        frozen,
        start_inclusive=pd.Timestamp(forward["start_inclusive_utc"]),
        end_inclusive=completed_through,
    )

    runtime = Path(source["runtime_directory"])
    candidate_path = runtime / config["outputs"]["runtime_candidates"]
    added = 0
    for row in candidates.itertuples(index=False):
        added += int(
            append_jsonl_once(
                candidate_path,
                _json_record(row, frozen.dependency_sha256),
                "candidate_id",
            )
        )
    all_candidates = read_jsonl(candidate_path)
    latest_state = frame.iloc[-1] if not frame.empty else None
    status = {
        "schema_version": "xauusd_capital_r4_chop_runtime_v34",
        "updated_at_utc": utc_text(now),
        "status": "ACTIVE_READ_ONLY_CANDIDATE_SHADOW",
        "account_login": int(account.login),
        "account_server": str(account.server),
        "symbol": str(source["symbol"]),
        "completed_m5_through_utc": utc_text(completed_through),
        "historical_m5_rows": int(len(historical)),
        "historical_m5_age_hours": float(history_age_hours),
        "raw_tick_rows": int(tick_audit["raw_rows"]),
        "unique_tick_rows": int(tick_audit["unique_rows"]),
        "quote_m5_rows": int(len(quote_bars)),
        "quality_quote_m5_rows": int(
            quote_bars.get("quote_quality_passed", pd.Series(dtype=bool)).sum()
        ),
        "quality_contiguous_15m_rows": int(
            quote_bars.get("quote_contiguous_15m", pd.Series(dtype=bool)).sum()
        ),
        "feature_rows": int(len(frame)),
        "latest_regime": None if latest_state is None else str(latest_state["regime"]),
        "candidate_rows_this_cycle": int(len(candidates)),
        "candidates_added_this_cycle": int(added),
        "total_forward_candidates": int(len(all_candidates)),
        "rule_dependency_sha256": frozen.dependency_sha256,
        "economic_outcomes_opened": False,
        "trade_permission": False,
        "broker_action_allowed": False,
        "python_execution_authorized": False,
    }
    atomic_write_json(runtime / config["outputs"]["runtime_status"], status)
    return status


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run frozen R4 chop rules on read-only Capital quotes"
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
                "schema_version": "xauusd_capital_r4_chop_runtime_v34",
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
                    ROOT / "config" / "capital_r4_chop_forward_v34.json"
                ).read_text(encoding="utf-8")
            )
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
        time.sleep(max(15, int(args.poll_seconds)))


if __name__ == "__main__":
    raise SystemExit(main())
