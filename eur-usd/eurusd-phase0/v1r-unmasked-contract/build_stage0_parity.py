from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
OLD_ROOT = REPO / "eur-usd" / "eurusd-phase0" / "unmasked-audit-v1"
NEW_MT5 = ROOT / "outputs" / "mt5"
AUDIT = ROOT / "outputs" / "audit"
LOCKED = ROOT / "outputs" / "locked"
SOURCE_CHAIN = LOCKED / "SOURCE_EX5_CHAIN.json"
ARTIFACT_MANIFEST = LOCKED / "ARTIFACT_MANIFEST.json"
OLD_LEDGER = OLD_ROOT / "outputs" / "audit" / "UNMASKED_TRADE_LEDGER_ENRICHED.csv"
NEW_LEDGER = NEW_MT5 / "EURUSD_V1R_TRADE_LEDGER.csv"
NEW_SUMMARY = NEW_MT5 / "EURUSD_V1R_EXACT_MT5_RESULT.json"
DT_FORMAT = "%Y.%m.%d %H:%M:%S"

SIGNAL_FIELDS = [
    "timestamp_broker",
    "account",
    "symbol",
    "direction",
    "reason",
    "open",
    "high",
    "low",
    "close",
    "atr",
    "band_upper",
    "band_mid",
    "band_lower",
    "rsi",
    "body_fraction",
    "band_distance_atr",
    "spread_points",
    "signal_mode",
    "extra",
]
ORDER_FIELDS = [
    "timestamp_broker",
    "account",
    "symbol",
    "action",
    "direction",
    "lots",
    "bid",
    "ask",
    "spread_points",
    "sl",
    "tp",
    "stop_points",
    "retcode",
    "retcode_description",
]
TRADE_FIELDS = [
    "entry_time",
    "direction",
    "volume",
    "entry_price",
    "exit_time",
    "exit_price",
    "price_profit",
    "commission",
    "swap",
    "net",
    "exit_comment",
]
REQUIRED_ENVIRONMENT_KEYS = {
    "account_server",
    "account_currency",
    "account_leverage",
    "account_margin_mode",
    "terminal_build",
    "mql_program_path",
    "tester_model_annotation",
    "server_time",
    "gmt_time",
    "gmt_offset_seconds",
    "daylight_savings_seconds",
    "symbol_digits",
    "symbol_point",
    "contract_size",
    "tick_size",
    "tick_value_profit",
    "tick_value_loss",
    "volume_min",
    "volume_max",
    "volume_step",
    "stops_level_points",
    "freeze_level_points",
    "spread_float",
    "trade_mode",
    "margin_calc_mode",
    "swap_mode",
    "swap_long",
    "currency_base",
    "currency_profit",
    "currency_margin",
}


def one(root: Path, pattern: str) -> Path:
    matches = sorted(root.rglob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {pattern} under {root}, found {len(matches)}")
    return matches[0]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def order_detail(value: str) -> dict[str, str]:
    deal, remainder = value.split("|result_price=", 1)
    result_price, reason = remainder.split("|reason=", 1)
    return {"deal": deal, "result_price": result_price, "reason": reason}


def compare_rows(
    artifact_type: str,
    old_rows: list[dict[str, str]],
    new_rows: list[dict[str, str]],
    fields: list[str],
) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    if len(old_rows) != len(new_rows):
        mismatches.append(
            {
                "artifact_type": artifact_type,
                "row_index": "",
                "field": "__row_count__",
                "old_value": len(old_rows),
                "new_value": len(new_rows),
            }
        )
    for index, (old, new) in enumerate(zip(old_rows, new_rows)):
        for field in fields:
            if old[field] != new[field]:
                mismatches.append(
                    {
                        "artifact_type": artifact_type,
                        "row_index": index,
                        "field": field,
                        "old_value": old[field],
                        "new_value": new[field],
                    }
                )
    return mismatches


def compare_orders(
    old_rows: list[dict[str, str]], new_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    mismatches = compare_rows("decision", old_rows, new_rows, ORDER_FIELDS)
    for index, (old, new) in enumerate(zip(old_rows, new_rows)):
        old_detail = order_detail(old["deal_and_reason"])
        new_detail = order_detail(new["deal_and_reason"])
        for field in ("result_price", "reason"):
            if old_detail[field] != new_detail[field]:
                mismatches.append(
                    {
                        "artifact_type": "decision",
                        "row_index": index,
                        "field": field,
                        "old_value": old_detail[field],
                        "new_value": new_detail[field],
                    }
                )
    return mismatches


def metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    values = [float(row["net"]) for row in rows]
    wins = [value for value in values if value > 0]
    losses = [value for value in values if value < 0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    return {
        "trades": len(rows),
        "wins": len(wins),
        "losses": len(losses),
        "net_usd": round(sum(values), 2),
        "gross_profit_usd": round(gross_profit, 2),
        "gross_loss_usd": round(gross_loss, 2),
        "profit_factor_unrounded": gross_profit / gross_loss if gross_loss else None,
    }


def grouped_metrics(
    rows: list[dict[str, str]], key
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[str(key(row))].append(row)
    return [{"bucket": bucket, **metrics(grouped[bucket])} for bucket in sorted(grouped)]


def reason(row: dict[str, str]) -> str:
    return order_detail(row["deal_and_reason"])["reason"]


def validate_source_ex5_chain(
    chain: dict[str, Any], manifest: dict[str, Any]
) -> dict[str, Any]:
    manifest_by_path = {
        artifact["path"]: artifact for artifact in manifest.get("artifacts", [])
    }
    compile_proof = chain["compile_proof"]
    source_hashes = {
        "compile_source_after_copy": compile_proof["source_hash_after_copy"],
        "tester_source": chain["tester_source"]["sha256"],
        "frozen_source": chain["frozen_source"]["sha256"],
        "repository_source": chain["repository_source"]["sha256"],
    }
    source_hashes_equal = len(set(source_hashes.values())) == 1
    ex5_hashes_equal = (
        compile_proof["ex5_hash_after_compile"] == chain["frozen_ex5"]["sha256"]
    )

    chain_artifacts = [
        ("repository_source", chain["repository_source"]),
        ("frozen_source", chain["frozen_source"]),
        ("frozen_ex5", chain["frozen_ex5"]),
        ("frozen_compile_log", chain["frozen_compile_log"]),
        *[
            (f"include_{index}", include["frozen"])
            for index, include in enumerate(chain["includes"], start=1)
        ],
    ]
    comparisons = []
    for label, artifact in chain_artifacts:
        manifest_artifact = manifest_by_path.get(artifact["path"])
        comparisons.append(
            {
                "label": label,
                "path": artifact["path"],
                "present_in_manifest": manifest_artifact is not None,
                "chain_bytes": artifact["bytes"],
                "manifest_bytes": (
                    manifest_artifact["bytes"] if manifest_artifact else None
                ),
                "bytes_equal": (
                    manifest_artifact is not None
                    and artifact["bytes"] == manifest_artifact["bytes"]
                ),
                "chain_sha256": artifact["sha256"],
                "manifest_sha256": (
                    manifest_artifact["sha256"] if manifest_artifact else None
                ),
                "sha256_equal": (
                    manifest_artifact is not None
                    and artifact["sha256"] == manifest_artifact["sha256"]
                ),
            }
        )

    all_chain_artifacts_match_manifest = bool(comparisons) and all(
        comparison["present_in_manifest"]
        and comparison["bytes_equal"]
        and comparison["sha256_equal"]
        for comparison in comparisons
    )
    return {
        "passed": (
            bool(chain["includes"])
            and source_hashes_equal
            and ex5_hashes_equal
            and all_chain_artifacts_match_manifest
        ),
        "source_hashes": source_hashes,
        "source_hashes_equal": source_hashes_equal,
        "compile_ex5_sha256": compile_proof["ex5_hash_after_compile"],
        "frozen_ex5_sha256": chain["frozen_ex5"]["sha256"],
        "ex5_hashes_equal": ex5_hashes_equal,
        "all_chain_artifacts_match_manifest": all_chain_artifacts_match_manifest,
        "artifact_comparisons": comparisons,
    }


def main() -> int:
    AUDIT.mkdir(parents=True, exist_ok=True)
    old_signals = read_csv(one(OLD_ROOT / "outputs" / "mt5", "*_signal_log.csv"))
    new_signals = read_csv(NEW_MT5 / "eurusd_v1r_signal_log.csv")
    old_orders = read_csv(one(OLD_ROOT / "outputs" / "mt5", "*_order_log.csv"))
    new_orders = read_csv(NEW_MT5 / "eurusd_v1r_order_log.csv")
    old_trades = read_csv(OLD_LEDGER)
    new_trades = read_csv(NEW_LEDGER)
    execution = read_csv(NEW_MT5 / "eurusd_v1r_execution_log.csv")
    transactions = read_csv(NEW_MT5 / "eurusd_v1r_transaction_log.csv")
    startup = read_csv(NEW_MT5 / "eurusd_v1r_startup_log.csv")
    state = read_csv(NEW_MT5 / "eurusd_v1r_state_log.csv")
    environment_rows = read_csv(NEW_MT5 / "eurusd_v1r_environment_log.csv")
    environment = {row["key"]: row["value"] for row in environment_rows}
    summary = json.loads(NEW_SUMMARY.read_text(encoding="utf-8"))
    source_chain = json.loads(SOURCE_CHAIN.read_text(encoding="utf-8"))
    artifact_manifest = json.loads(ARTIFACT_MANIFEST.read_text(encoding="utf-8"))
    source_chain_validation = validate_source_ex5_chain(
        source_chain, artifact_manifest
    )

    mismatches = []
    mismatches.extend(compare_rows("signal", old_signals, new_signals, SIGNAL_FIELDS))
    mismatches.extend(compare_orders(old_orders, new_orders))
    mismatches.extend(compare_rows("trade", old_trades, new_trades, TRADE_FIELDS))
    mismatch_path = AUDIT / "CANONICAL_MISMATCHES.csv"
    write_csv(
        mismatch_path,
        mismatches,
        ["artifact_type", "row_index", "field", "old_value", "new_value"],
    )

    request_results = [row for row in execution if row["event"] == "REQUEST_RESULT"]
    confirmed = [row for row in request_results if row["fill_confirmed"] == "true"]
    geometry = [row for row in execution if row["event"] == "STOP_GEOMETRY"]
    geometry_complete = [
        row
        for row in confirmed
        if float(row["actual_position_price"]) > 0
        and float(row["actual_sl"]) > 0
        and float(row["actual_tp"]) > 0
    ]
    requested_actual_sl_match = sum(
        row["requested_sl"] == row["actual_sl"] for row in confirmed
    )
    requested_actual_tp_match = sum(
        row["requested_tp"] == row["actual_tp"] for row in confirmed
    )
    ledger_deals = {
        row["entry_deal"] for row in new_trades
    } | {row["exit_deal"] for row in new_trades}
    transaction_deals = {
        row["deal_ticket"]
        for row in transactions
        if row["deal_ticket"] not in {"", "0"}
    }
    stop_ceiling_rows = [row for row in new_orders if reason(row) == "stop_ceiling_exceeded"]
    order_actions = Counter(row["action"] for row in new_orders)
    order_reasons = Counter(reason(row) for row in new_orders)
    stop_components = Counter(row["selected_stop_component"] for row in geometry)

    startup_gate = (
        len(startup) == 1
        and startup[0]["status"] == "INIT_OK_LATCH_ARMED"
        and len(state) >= 3
        and state[0]["event"] == "INIT_LATCH_ARMED"
        and state[1]["event"] == "STARTUP_TRANSITION_SKIPPED"
        and state[2]["event"] == "NATIVE_BAR_TRANSITION"
        and state[1]["processed_bar_open"] == startup[0]["latch_bar_open"]
    )
    environment_missing = sorted(REQUIRED_ENVIRONMENT_KEYS - set(environment))
    new_metrics = metrics(new_trades)
    expected_metrics = {
        "trades": 1145,
        "wins": 659,
        "losses": 486,
        "net_usd": 77.26,
        "gross_profit_usd": 779.61,
        "gross_loss_usd": 702.35,
    }
    metric_parity = all(new_metrics[key] == value for key, value in expected_metrics.items())
    report_metrics = summary["mt5_report_metrics"]

    gates = {
        "candidate_specific_identity": summary["candidate_id"]
        == "EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1R_UNMASKED_CONTRACT",
        "compile_zero_errors_zero_warnings": summary["clean_run"]["compile"][
            "compile_zero_errors_zero_warnings"
        ],
        "source_copy_hash_exact": summary["clean_run"]["compile"]["source_hash_before_copy"]
        == summary["clean_run"]["compile"]["source_hash_after_copy"],
        "source_ex5_chain_frozen": summary["source_chain"] == source_chain
        and source_chain_validation["passed"],
        "input_schema_exact": summary["input_contract"]["declared_input_count"] == 34
        and not summary["input_contract"]["unknown_ini_keys"]
        and not summary["input_contract"]["missing_ini_keys"],
        "ini_leverage_1_50": summary["input_contract"]["ini_leverage"] == "1:50",
        "report_leverage_1_50": summary["input_contract"]["report_leverage"] == "1:50",
        "environment_leverage_50": environment.get("account_leverage") == "50",
        "symbol_specification_complete": not environment_missing,
        "startup_fail_closed": startup_gate,
        "signal_count_2957": len(new_signals) == 2957,
        "decision_count_2957": len(new_orders) == 2957,
        "trade_count_1145": len(new_trades) == 1145,
        "aggregate_metric_parity": metric_parity,
        "canonical_signal_decision_trade_parity": len(mismatches) == 0,
        "order_action_parity": order_actions
        == Counter({"GUARD_BLOCK": 1809, "ORDER_SEND_OK": 1145, "ORDER_SEND_FAIL": 3}),
        "failed_attempts_preserved": order_reasons["order_send_failed"] == 3,
        "fill_defined_by_entry_deal": len(confirmed) == 1145,
        "requested_actual_geometry_complete": len(geometry_complete) == 1145,
        "requested_actual_sl_exact": requested_actual_sl_match == 1145,
        "requested_actual_tp_exact": requested_actual_tp_match == 1145,
        "all_entry_exit_deals_in_transaction_log": ledger_deals <= transaction_deals
        and len(ledger_deals) == 2290,
        "stop_component_attribution_complete": len(geometry) == 1148
        and all(row["selected_stop_component"] for row in geometry),
        "stop_ceiling_inventory_complete": len(stop_ceiling_rows) == 0,
        "positive_free_margin": min(float(row["free_margin"]) for row in execution) > 0,
        "mt5_net_exact": report_metrics["Total Net Profit"] == "77.26",
        "mt5_gross_exact": report_metrics["Gross Profit"] == "779.61"
        and report_metrics["Gross Loss"] == "-702.35",
        "mt5_equity_drawdown_exact": report_metrics["Equity Drawdown Maximal"]
        == "27.56 (2.68%)",
        "reclaim_not_implemented_or_run": not summary["boundary"]["reclaim_implemented"]
        and not summary["boundary"]["reclaim_run"],
        "tester_only_boundary": summary["boundary"]["strategy_tester_only"]
        and not summary["boundary"]["chart_demo_live_touched"],
    }
    passed = all(gates.values())

    years = grouped_metrics(
        new_trades,
        lambda row: datetime.strptime(row["exit_time"], DT_FORMAT).year,
    )
    months = grouped_metrics(
        new_trades,
        lambda row: datetime.strptime(row["exit_time"], DT_FORMAT).strftime("%Y-%m"),
    )
    sessions = grouped_metrics(
        new_trades,
        lambda row: f"{(datetime.strptime(row['entry_time'], DT_FORMAT).hour // 6) * 6:02d}:00-"
        f"{(datetime.strptime(row['entry_time'], DT_FORMAT).hour // 6) * 6 + 5:02d}:59",
    )
    write_csv(AUDIT / "EXIT_TIME_YEAR_METRICS.csv", years, list(years[0]))
    write_csv(AUDIT / "EXIT_TIME_MONTH_METRICS.csv", months, list(months[0]))
    write_csv(AUDIT / "ENTRY_SESSION_METRICS.csv", sessions, list(sessions[0]))
    stop_rows = [
        {"component": component, "count": count}
        for component, count in sorted(stop_components.items())
    ]
    write_csv(AUDIT / "STOP_COMPONENT_COUNTS.csv", stop_rows, ["component", "count"])

    reconciliation = {
        "schema_version": "eurusd_v1r_execution_reconciliation_v1",
        "request_results": len(request_results),
        "confirmed_entry_deals": len(confirmed),
        "failed_requests": len(request_results) - len(confirmed),
        "geometry_rows": len(geometry),
        "actual_entry_sl_tp_complete": len(geometry_complete),
        "requested_actual_sl_exact": requested_actual_sl_match,
        "requested_actual_tp_exact": requested_actual_tp_match,
        "ledger_entry_exit_deals": len(ledger_deals),
        "transaction_log_deals": len(transaction_deals),
        "missing_ledger_deals_in_transactions": sorted(
            ledger_deals - transaction_deals, key=int
        ),
        "stop_ceiling_rejections": len(stop_ceiling_rows),
        "order_actions": dict(order_actions),
        "order_reasons": dict(order_reasons),
        "minimum_free_margin_usd": min(float(row["free_margin"]) for row in execution),
        "minimum_positive_margin_level_pct": min(
            float(row["margin_level"])
            for row in execution
            if float(row["margin_level"]) > 0
        ),
    }
    (AUDIT / "EXECUTION_RECONCILIATION.json").write_text(
        json.dumps(reconciliation, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    (AUDIT / "SYMBOL_SPECIFICATION.json").write_text(
        json.dumps(
            {
                "schema_version": "eurusd_v1r_symbol_specification_v1",
                "captured_at_broker_time": environment_rows[0]["timestamp_broker"],
                "values": environment,
                "missing_required_keys": environment_missing,
                "server_utc_mapping_boundary": (
                    "MT5 tester-reported TimeGMT/offset snapshot only; portability and "
                    "native-real-tick coverage are not established."
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    result = {
        "schema_version": "eurusd_v1r_stage0_parity_v1",
        "candidate_id": "EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1R_UNMASKED_CONTRACT",
        "status": "STAGE0_PARITY_PASS_RECLAIM_NOT_RUN"
        if passed
        else "STOP_REPAIR_STAGE0_PARITY_FAIL",
        "all_gates_pass": passed,
        "gates": gates,
        "canonical_mismatches": len(mismatches),
        "benchmark": metrics(old_trades),
        "v1r": new_metrics,
        "report_metrics": report_metrics,
        "startup": {
            "startup_row": startup[0],
            "first_three_state_events": state[:3],
        },
        "execution_reconciliation": reconciliation,
        "source_ex5_chain_validation": source_chain_validation,
        "environment_missing_keys": environment_missing,
        "corrected_exit_time_years": years,
        "corrected_entry_sessions": sessions,
        "boundary": {
            "retrospective_development_only": True,
            "reclaim_source_created": False,
            "reclaim_run": False,
            "demo_live_chart_touched": False,
            "dsr_status": "NOT_ASSESSABLE",
            "native_real_tick_coverage": "NOT_ESTABLISHED_MODEL0_MAY_GENERATE_TICKS",
        },
    }
    result_path = AUDIT / "STAGE0_PARITY_RESULT.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    md = [
        "# EURUSD V1R Stage 0 Parity Result",
        "",
        f"Status: `{result['status']}`",
        "",
        "The corrected candidate reproduces the exact unmasked benchmark while",
        "closing the startup, source/EX5, input-schema, leverage, symbol, fill,",
        "SL/TP, stop-component, and order/deal evidence gaps.",
        "",
        "| Gate | Pass |",
        "|---|---:|",
        *[
            f"| {name.replace('_', ' ')} | {'PASS' if value else 'FAIL'} |"
            for name, value in gates.items()
        ],
        "",
        "## Canonical parity",
        "",
        f"- Signal rows: {len(new_signals):,}; mismatches: "
        f"{sum(row['artifact_type'] == 'signal' for row in mismatches):,}.",
        f"- Decision rows: {len(new_orders):,}; mismatches: "
        f"{sum(row['artifact_type'] == 'decision' for row in mismatches):,}.",
        f"- Trade rows: {len(new_trades):,}; mismatches: "
        f"{sum(row['artifact_type'] == 'trade' for row in mismatches):,}.",
        f"- Net: USD {new_metrics['net_usd']:.2f}.",
        f"- Gross profit/loss: USD {new_metrics['gross_profit_usd']:.2f} / "
        f"USD {new_metrics['gross_loss_usd']:.2f}.",
        f"- Unrounded PF: {new_metrics['profit_factor_unrounded']:.12f}.",
        f"- MT5 maximal equity drawdown: {report_metrics['Equity Drawdown Maximal']}.",
        "",
        "## Boundary",
        "",
        "This is a repaired retrospective research baseline only. No reclaim",
        "source was created or run. No chart, demo, live, shadow, or broker-runtime",
        "action was authorized or performed. Model 0 may contain generated ticks,",
        "and DSR remains not assessable.",
        "",
    ]
    (AUDIT / "STAGE0_PARITY_RESULT.md").write_text(
        "\n".join(md), encoding="utf-8", newline="\n"
    )
    print(json.dumps({"status": result["status"], "gates": len(gates), "mismatches": len(mismatches)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
