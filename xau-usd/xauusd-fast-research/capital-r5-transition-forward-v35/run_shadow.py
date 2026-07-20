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

from transition_forward import (  # noqa: E402
    acquire_macro_hours,
    build_decision_frames,
    build_macro_m15,
    generate_forward_component_candidates,
    load_frozen,
    route_forward_candidates,
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


def _json_record(row: Any, dependency_sha: str) -> dict[str, Any]:
    record = row._asdict()
    for key in ("signal_time", "scheduled_entry_time"):
        record[f"{key}_utc"] = utc_text(record.pop(key))
    for key in (
        "origin_attempt",
        "direction_sign",
        "router_attempt",
        "shadow_count",
    ):
        if key in record:
            record[key] = int(record[key])
    for key in (
        "signal_atr",
        "stop_atr",
        "target_r",
        "hold_hours",
        "shadow_mean_r",
        "shadow_profit_factor",
        "shadow_drawdown_r",
        "route_multiplier",
        "risk_weight",
    ):
        if key in record:
            value = float(record[key])
            record[key] = value if math.isfinite(value) else None
    record["rule_dependency_sha256"] = dependency_sha
    return record


def run_cycle(repo_root: Path, package_root: Path) -> dict[str, Any]:
    frozen = load_frozen(repo_root, package_root)
    config = frozen.package_config
    source = config["source"]
    outputs = config["outputs"]
    lock_path = package_root / outputs["directory"] / outputs["contract_lock"]
    if not lock_path.is_file():
        raise FileNotFoundError("V35 contract lock is absent")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock["rule_dependency_sha256"] != frozen.dependency_sha256:
        raise ValueError("V35 rule dependencies changed after lock")

    now = datetime.now(timezone.utc)
    completed_hour = now.replace(minute=0, second=0, microsecond=0)
    extension_start = datetime.fromisoformat(
        source["macro_extension_start_utc"].replace("Z", "+00:00")
    )
    acquired = acquire_macro_hours(
        frozen,
        start=extension_start,
        end_exclusive=now,
        concurrency=int(config["official_macro"]["maximum_concurrency"]),
        missing_only=True,
    )
    macro_m15 = build_macro_m15(
        frozen,
        extension_start=pd.Timestamp(extension_start),
        end_exclusive=pd.Timestamp(completed_hour),
    )

    completed_m15 = pd.Timestamp(now).floor("15min")
    client = ReadOnlyMT5Client.from_installed_package()
    if not client.initialize(MT5ConnectionSpec(source["terminal_exe"], True)):
        raise RuntimeError(f"MT5 initialize failed: {client.last_error()}")
    try:
        account = client.account_info()
        terminal_info = client.terminal_info()
        assert_demo_read_only(account, terminal_info)
        if int(account.login) != int(source["account_login"]):
            raise RuntimeError("V35 account login changed")
        if str(account.server) != str(source["account_server"]):
            raise RuntimeError("V35 account server changed")
        symbol = client.symbol_info(str(source["symbol"]))
        if symbol is None:
            raise RuntimeError("V35 XAUUSD symbol is unavailable")
        rates = client.copy_rates_range(
            str(source["symbol"]),
            client.timeframe_value("M5"),
            now - timedelta(days=int(source["history_days"])),
            now,
        )
        gold_m5 = mt5_rates_to_m5(
            rates,
            point_size=float(symbol.point),
            completed_through=completed_m15,
        )
        gold_m5["tick_count"] = 1.0
        history_age = assert_market_history_fresh(
            gold_m5,
            now_utc=now,
            maximum_staleness_hours=int(source["maximum_m5_staleness_hours"]),
        )
    finally:
        client.shutdown()

    _, macro_decisions, residual_decisions = build_decision_frames(
        gold_m5, macro_m15, frozen
    )
    components = generate_forward_component_candidates(
        macro_decisions,
        residual_decisions,
        frozen,
        start_inclusive=pd.Timestamp(config["forward"]["start_inclusive_utc"]),
        end_inclusive=completed_m15,
    )
    component_history = pd.read_parquet(repo_root / source["v9_component_trades"])
    routed = route_forward_candidates(components, component_history, frozen)

    runtime = Path(source["runtime_directory"])
    component_path = runtime / outputs["component_candidates"]
    routed_path = runtime / outputs["routed_candidates"]
    component_added = 0
    for row in components.itertuples(index=False):
        component_added += int(
            append_jsonl_once(
                component_path,
                _json_record(row, frozen.dependency_sha256),
                "candidate_id",
            )
        )
    routed_added = 0
    for row in routed.itertuples(index=False):
        routed_added += int(
            append_jsonl_once(
                routed_path,
                _json_record(row, frozen.dependency_sha256),
                "candidate_id",
            )
        )
    all_components = read_jsonl(component_path)
    all_routed = read_jsonl(routed_path)
    status = {
        "schema_version": "xauusd_capital_r5_transition_runtime_v35",
        "updated_at_utc": utc_text(now),
        "status": "ACTIVE_READ_ONLY_CANDIDATE_SHADOW",
        "account_login": int(account.login),
        "account_server": str(account.server),
        "symbol": str(source["symbol"]),
        "completed_m15_through_utc": utc_text(completed_m15),
        "gold_m5_rows": int(len(gold_m5)),
        "gold_m5_age_hours": float(history_age),
        "macro_m15_rows": int(len(macro_m15)),
        "macro_latest_utc": (
            None
            if macro_m15.empty
            else utc_text(macro_m15["timestamp_utc"].max())
        ),
        "macro_files_downloaded_this_cycle": int(
            sum(row["status"] == "DOWNLOADED_VALID" for row in acquired)
        ),
        "component_candidates_this_cycle": int(len(components)),
        "component_candidates_added_this_cycle": int(component_added),
        "total_component_candidates": int(len(all_components)),
        "routed_candidates_this_cycle": int(len(routed)),
        "routed_candidates_added_this_cycle": int(routed_added),
        "total_routed_candidates": int(len(all_routed)),
        "rule_dependency_sha256": frozen.dependency_sha256,
        "prospective_component_outcome_updates_authorized": False,
        "economic_outcomes_opened": False,
        "trade_permission": False,
        "broker_action_allowed": False,
        "python_execution_authorized": False,
    }
    atomic_write_json(runtime / outputs["runtime_status"], status)
    return status


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run frozen R5 transition rules on current read-only inputs"
    )
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=300)
    args = parser.parse_args()
    while True:
        try:
            status = run_cycle(REPO_ROOT, ROOT)
            print(json.dumps(status, sort_keys=True), flush=True)
        except Exception as exc:
            failure = {
                "schema_version": "xauusd_capital_r5_transition_runtime_v35",
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
                    ROOT / "config" / "capital_r5_transition_forward_v35.json"
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
        time.sleep(max(60, int(args.poll_seconds)))


if __name__ == "__main__":
    raise SystemExit(main())
