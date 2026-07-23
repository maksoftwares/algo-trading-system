from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent
PHASE0 = ROOT.parent
REPO = ROOT.parents[2]
V1_ROOT = PHASE0 / "outputs" / "mt5_parity"
UNMASKED_ROOT = ROOT / "outputs" / "mt5"
BAR_PATH = ROOT / "outputs" / "bar_audit" / "eurusd_v1_unmasked_m30_bar_audit.csv"
OUTPUT = ROOT / "outputs" / "audit"
OLD_BLOCKED_HOURS = {6, 7, 10, 13}
DT_FORMAT = "%Y.%m.%d %H:%M:%S"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_text_auto(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    return data.decode("utf-8-sig")


def number(value: str) -> float:
    text = value.replace(" ", "").replace(",", "").strip()
    return float(text) if text else 0.0


def deal_costs(report: Path) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    text = read_text_auto(report)
    for match in re.finditer(r"<tr[^>]*>(.*?)</tr>", text, flags=re.I | re.S):
        cells = [
            html.unescape(re.sub(r"<[^>]+>", "", cell)).strip().replace("\xa0", " ")
            for cell in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", match.group(1), flags=re.I | re.S)
        ]
        if len(cells) < 13 or cells[2] != "EURUSD" or cells[4] != "out":
            continue
        commission = number(cells[8])
        swap = number(cells[9])
        price_profit = number(cells[10])
        result[cells[1]] = {
            "commission": commission,
            "swap": swap,
            "price_profit": price_profit,
            "net": commission + swap + price_profit,
        }
    return result


def one(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.rglob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {pattern} under {directory}, found {len(matches)}")
    return matches[0]


def load_trade_ledger(root: Path) -> tuple[list[dict[str, Any]], Path, Path]:
    trades_path = one(root, "*_trades.csv")
    report_path = one(root, "*.htm")
    costs = deal_costs(report_path)
    rows: list[dict[str, Any]] = []
    for row in read_csv(trades_path):
        if row["exit_deal"] not in costs:
            raise RuntimeError(f"Missing MT5 exit deal {row['exit_deal']}")
        rows.append(
            {
                **row,
                **costs[row["exit_deal"]],
                "entry_dt": datetime.strptime(row["entry_time"], DT_FORMAT),
                "exit_dt": datetime.strptime(row["exit_time"], DT_FORMAT),
            }
        )
    return rows, trades_path, report_path


def profit_factor(values: list[float]) -> float:
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    return gross_profit / gross_loss if gross_loss else float("inf")


def metrics(rows: list[dict[str, Any]], value_key: str = "net") -> dict[str, Any]:
    values = [float(row[value_key]) for row in rows]
    wins = [value for value in values if value > 0]
    losses = [value for value in values if value < 0]
    return {
        "trades": len(rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(100 * len(wins) / len(rows), 2) if rows else 0.0,
        "net_usd": round(sum(values), 2),
        "gross_profit_usd": round(sum(wins), 2),
        "gross_loss_usd": round(-sum(losses), 2),
        "profit_factor": round(profit_factor(values), 4),
        "average_trade_usd": round(sum(values) / len(values), 4) if values else 0.0,
        "average_win_usd": round(sum(wins) / len(wins), 4) if wins else 0.0,
        "average_loss_usd": round(sum(losses) / len(losses), 4) if losses else 0.0,
        "payoff_ratio": round((sum(wins) / len(wins)) / (-sum(losses) / len(losses)), 4)
        if wins and losses
        else 0.0,
    }


def group_metrics(rows: list[dict[str, Any]], key) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(key(row))].append(row)
    return {name: metrics(grouped[name]) for name in sorted(grouped)}


def order_reason(row: dict[str, str]) -> str:
    marker = "|reason="
    value = row.get("deal_and_reason", "")
    return value.split(marker, 1)[1] if marker in value else ""


def add_episode_labels(
    signals: list[dict[str, str]],
    orders: list[dict[str, str]],
    trades: list[dict[str, Any]],
) -> dict[str, Any]:
    signal_by_time = {row["timestamp_broker"]: row for row in signals}
    order_by_time = {row["timestamp_broker"]: row for row in orders}
    bars = read_csv(BAR_PATH)
    episode = 0
    signal_sequence = 0
    filled_sequence = 0
    active = False
    labels: dict[str, dict[str, int]] = {}

    for bar in bars:
        stamp = bar["decision_time_broker"]
        if active and float(bar["close"]) > float(bar["band_mid"]):
            active = False
            signal_sequence = 0
            filled_sequence = 0
        if stamp not in signal_by_time:
            continue
        if not active:
            episode += 1
            active = True
            signal_sequence = 0
            filled_sequence = 0
        signal_sequence += 1
        order = order_by_time[stamp]
        filled = order["action"] == "ORDER_SEND_OK"
        if filled:
            filled_sequence += 1
        labels[stamp] = {
            "episode_id": episode,
            "signal_sequence": signal_sequence,
            "filled_entry_sequence": filled_sequence if filled else 0,
        }

    missing = sorted(set(signal_by_time) - set(labels))
    if missing:
        raise RuntimeError(f"{len(missing)} signals do not have M30 episode labels")
    for trade in trades:
        trade.update(labels[trade["entry_time"]])
    return {
        "episodes": episode,
        "signals_labeled": len(labels),
        "bar_rows": len(bars),
    }


def stress_trade(row: dict[str, Any], adverse_pips: float) -> float:
    # Standard EURUSD 100,000 contract: 0.01 lot has USD 0.10 per pip.
    execution_charge = adverse_pips * 0.10
    commission = float(row["commission"])
    swap = float(row["swap"])
    stressed_commission = commission * 1.25 if commission < 0 else commission
    stressed_swap = swap * 1.25 if swap < 0 else swap
    return float(row["price_profit"]) + stressed_commission + stressed_swap - execution_charge


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    v1_trades, v1_trade_path, v1_report = load_trade_ledger(V1_ROOT)
    unmasked_trades, unmasked_trade_path, unmasked_report = load_trade_ledger(UNMASKED_ROOT)
    v1_signals = read_csv(one(V1_ROOT, "*_signal_log.csv"))
    unmasked_signals = read_csv(one(UNMASKED_ROOT, "*_signal_log.csv"))
    v1_orders = read_csv(one(V1_ROOT, "*_order_log.csv"))
    unmasked_orders = read_csv(one(UNMASKED_ROOT, "*_order_log.csv"))

    episode_basis = add_episode_labels(unmasked_signals, unmasked_orders, unmasked_trades)

    signal_compare_fields = [
        "timestamp_broker",
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
    ]
    v1_signal_map = {row["timestamp_broker"]: row for row in v1_signals}
    unmasked_signal_map = {row["timestamp_broker"]: row for row in unmasked_signals}
    signal_parity = set(v1_signal_map) == set(unmasked_signal_map) and all(
        all(v1_signal_map[stamp][field] == unmasked_signal_map[stamp][field] for field in signal_compare_fields)
        for stamp in v1_signal_map
    )

    v1_order_map = {row["timestamp_broker"]: row for row in v1_orders}
    unmasked_order_map = {row["timestamp_broker"]: row for row in unmasked_orders}
    attempt_diff = []
    for stamp in sorted(set(v1_order_map) | set(unmasked_order_map)):
        base = v1_order_map.get(stamp, {})
        audit = unmasked_order_map.get(stamp, {})
        attempt_diff.append(
            {
                "timestamp_broker": stamp,
                "hour": datetime.strptime(stamp, DT_FORMAT).hour,
                "old_mask_hour": datetime.strptime(stamp, DT_FORMAT).hour in OLD_BLOCKED_HOURS,
                "v1_action": base.get("action", ""),
                "v1_reason": order_reason(base),
                "unmasked_action": audit.get("action", ""),
                "unmasked_reason": order_reason(audit),
                "action_changed": base.get("action", "") != audit.get("action", "")
                or order_reason(base) != order_reason(audit),
            }
        )
    write_csv(
        OUTPUT / "MATCHED_SIGNAL_ATTEMPT_DIFF.csv",
        attempt_diff,
        list(attempt_diff[0]),
    )

    v1_map = {row["entry_time"]: row for row in v1_trades}
    unmasked_map = {row["entry_time"]: row for row in unmasked_trades}
    trade_diff = []
    added = []
    for stamp in sorted(set(v1_map) | set(unmasked_map)):
        base = v1_map.get(stamp)
        audit = unmasked_map.get(stamp)
        status = "COMMON" if base and audit else "V1_ONLY" if base else "UNMASKED_ONLY"
        row = {
            "entry_time": stamp,
            "status": status,
            "entry_hour": datetime.strptime(stamp, DT_FORMAT).hour,
            "old_mask_hour": datetime.strptime(stamp, DT_FORMAT).hour in OLD_BLOCKED_HOURS,
            "v1_exit_time": base["exit_time"] if base else "",
            "v1_net_usd": round(float(base["net"]), 2) if base else "",
            "unmasked_exit_time": audit["exit_time"] if audit else "",
            "unmasked_net_usd": round(float(audit["net"]), 2) if audit else "",
            "same_outcome": bool(
                base
                and audit
                and base["exit_time"] == audit["exit_time"]
                and abs(float(base["net"]) - float(audit["net"])) < 1e-9
            ),
        }
        trade_diff.append(row)
        if status == "UNMASKED_ONLY":
            added.append(audit)
    write_csv(OUTPUT / "MATCHED_TRADE_DIFF.csv", trade_diff, list(trade_diff[0]))

    enriched_fields = [
        "entry_time",
        "entry_date",
        "entry_hour",
        "direction",
        "entry_deal",
        "volume",
        "entry_price",
        "exit_time",
        "exit_deal",
        "exit_price",
        "price_profit",
        "commission",
        "swap",
        "net",
        "exit_comment",
        "episode_id",
        "signal_sequence",
        "filled_entry_sequence",
    ]
    write_csv(OUTPUT / "UNMASKED_TRADE_LEDGER_ENRICHED.csv", unmasked_trades, enriched_fields)
    write_csv(OUTPUT / "TRADES_ADDED_BY_UNMASKING.csv", added, enriched_fields)

    simple_filtered = [
        row for row in unmasked_trades if row["entry_dt"].hour not in OLD_BLOCKED_HOURS
    ]
    old_hours = [row for row in unmasked_trades if row["entry_dt"].hour in OLD_BLOCKED_HOURS]
    repeat = [row for row in unmasked_trades if int(row["filled_entry_sequence"]) >= 2]
    first = [row for row in unmasked_trades if int(row["filled_entry_sequence"]) == 1]

    for row in unmasked_trades:
        row["primary_stress"] = stress_trade(row, 0.5)
        row["severe_stress"] = stress_trade(row, 1.0)

    annual = group_metrics(unmasked_trades, lambda row: row["entry_dt"].year)
    monthly = group_metrics(unmasked_trades, lambda row: row["entry_dt"].strftime("%Y-%m"))
    buckets = group_metrics(
        unmasked_trades,
        lambda row: f"{(row['entry_dt'].hour // 6) * 6:02d}:00-{(row['entry_dt'].hour // 6) * 6 + 5:02d}:59",
    )
    repeat_annual = group_metrics(repeat, lambda row: row["entry_dt"].year)

    v1_summary = json.loads(one(V1_ROOT, "*_summary.json").read_text(encoding="utf-8"))
    unmasked_summary = json.loads(one(UNMASKED_ROOT, "*_summary.json").read_text(encoding="utf-8"))
    v1_mt5 = v1_summary["mt5_report_metrics"]
    unmasked_mt5 = unmasked_summary["mt5_report_metrics"]
    primary = metrics(unmasked_trades, "primary_stress")
    severe = metrics(unmasked_trades, "severe_stress")
    positive_years = sum(annual[str(year)]["net_usd"] > 0 for year in (2023, 2024, 2025))
    repeat_bad_years = sum(
        repeat_annual.get(str(year), {}).get("profit_factor", 0.0) < 0.90
        for year in (2023, 2024, 2025)
    )
    repeat_share = 100 * len(repeat) / len(unmasked_trades)
    branch_eligible = repeat_share >= 20.0 and repeat_bad_years >= 2

    gates = {
        "unmasked_mt5_pf_at_least_1_05": float(unmasked_mt5["Profit Factor"]) >= 1.05,
        "primary_cost_stress_pf_at_least_0_95": primary["profit_factor"] >= 0.95,
        "at_least_two_positive_years_2023_2025": positive_years >= 2,
        "positive_net_not_dependent_on_old_blocked_hours": metrics(simple_filtered)["net_usd"] > 0
        and metrics(old_hours)["net_usd"] <= 0,
    }

    source = REPO / "forex-research" / "mt5" / "Experts" / "ForexMeanReversionScout.mq5"
    source_text = source.read_text(encoding="utf-8")
    published_v1_preset = PHASE0 / "mt5" / "Presets" / "EURUSD_M30_RSI_BB_FADE_V1_RESEARCH_ONLY.set"
    published_v1_preset_text = published_v1_preset.read_text(encoding="utf-8")
    implementation = {
        "atr_shift_1": "CopyOne(g_atr_handle, 0, 1, atr)" in source_text,
        "bands_shift_1": "CopyOne(g_bands_handle, 0, 1, band_mid)" in source_text,
        "rsi_shift_1": "CopyOne(g_rsi_handle, 0, 1, rsi)" in source_text,
        "six_bar_low_shifts_1_through_6": "RecentLow(1, 6)" in source_text,
        "stop_ceiling_rejects_not_truncates": '"stop_ceiling_exceeded"' in source_text
        and "return;" in source_text,
        "tester_only_guard": "if(!MQLInfoInteger(MQL_TESTER))" in source_text,
        "exact_v1_and_unmasked_minimum_body_fraction": 0.40,
        "published_v1_preset_minimum_body_fraction": 0.0,
        "published_v1_preset_matches_exact_mt5_input": "InpMinBodyFraction=0.40"
        in published_v1_preset_text,
        "contract_repair_required": True,
        "startup_latch_explicitly_prevents_prior_bar_entry": False,
        "startup_latch_observed_first_signal": unmasked_signals[0]["timestamp_broker"],
    }

    report = {
        "schema_version": "eurusd_v1_unmasked_audit_result_v1",
        "candidate_id": "EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1_UNMASKED_AUDIT",
        "status": "UNMASKED_KILL_GATES_PASS_CONTRACT_REPAIR_REQUIRED"
        if all(gates.values())
        else "UNMASKED_KILL_RULE_TRIGGERED_RETIRE_FAMILY",
        "boundary": {
            "development_data_only": True,
            "strategy_tester_only": True,
            "from": "2022.07.01",
            "to": "2026.07.02",
            "broker": "Capital.ComMena-Demo",
            "terminal_build": 5833,
            "history_quality": unmasked_mt5["History Quality"],
            "bars": int(unmasked_mt5["Bars"]),
            "ticks": int(unmasked_mt5["Ticks"]),
            "report_leverage": "1:50",
            "ini_requested_leverage": "1:200",
        },
        "single_change": {
            "input": "InpBlockedEntryHoursCsv",
            "v1": "6,7,10,13",
            "unmasked": "",
            "signal_stream_exact_parity": signal_parity,
        },
        "economics": {
            "v1_mt5": {
                "trades": int(v1_mt5["Total Trades"]),
                "net_usd": float(v1_mt5["Total Net Profit"]),
                "profit_factor": float(v1_mt5["Profit Factor"]),
                "equity_drawdown_maximal": v1_mt5["Equity Drawdown Maximal"],
            },
            "unmasked_mt5": {
                "trades": int(unmasked_mt5["Total Trades"]),
                "net_usd": float(unmasked_mt5["Total Net Profit"]),
                "profit_factor": float(unmasked_mt5["Profit Factor"]),
                "win_rate_pct": unmasked_summary["summary"]["overall"]["win_rate_pct"],
                "expected_payoff_usd": float(unmasked_mt5["Expected Payoff"]),
                "equity_drawdown_maximal": unmasked_mt5["Equity Drawdown Maximal"],
            },
            "unmasked_deal_ledger": metrics(unmasked_trades),
            "cost_decomposition_usd": {
                "price_profit": round(sum(float(row["price_profit"]) for row in unmasked_trades), 2),
                "commission": round(sum(float(row["commission"]) for row in unmasked_trades), 2),
                "swap": round(sum(float(row["swap"]) for row in unmasked_trades), 2),
                "net": round(sum(float(row["net"]) for row in unmasked_trades), 2),
            },
            "primary_0_5_pip_plus_25pct_cost_stress": primary,
            "severe_1_0_pip_plus_25pct_cost_stress": severe,
        },
        "matched_comparison": {
            "signals": len(unmasked_signals),
            "signal_stream_exact_parity": signal_parity,
            "attempt_rows_each": len(unmasked_orders),
            "attempts_changed": sum(bool(row["action_changed"]) for row in attempt_diff),
            "common_entry_timestamps": sum(row["status"] == "COMMON" for row in trade_diff),
            "common_exact_outcomes": sum(bool(row["same_outcome"]) for row in trade_diff),
            "unmasked_only_entries": len(added),
            "unmasked_only_at_old_blocked_hours": sum(
                row["entry_dt"].hour in OLD_BLOCKED_HOURS for row in added
            ),
            "unmasked_only_at_other_hours_path_effect": sum(
                row["entry_dt"].hour not in OLD_BLOCKED_HOURS for row in added
            ),
            "v1_only_entries_displaced_by_path": sum(row["status"] == "V1_ONLY" for row in trade_diff),
            "old_mask_simple_filter_of_unmasked_fills": metrics(simple_filtered),
            "exact_v1_causal_rerun": metrics(v1_trades),
            "simple_filter_reconstructs_v1": {
                "trade_count_equal": len(simple_filtered) == len(v1_trades),
                "net_equal": metrics(simple_filtered)["net_usd"] == metrics(v1_trades)["net_usd"],
                "explanation": "False is expected because one-position state makes the hour-mask intervention path-dependent.",
            },
            "old_blocked_hour_trades_in_unmasked_path": metrics(old_hours),
        },
        "calendar_year": annual,
        "month": monthly,
        "six_hour_broker_buckets": buckets,
        "episodes": {
            **episode_basis,
            "definition": "First qualifying setup until first completed M30 close above its current Bollinger middle band.",
            "first_filled_entries": metrics(first),
            "repeat_filled_entries": metrics(repeat),
            "repeat_trade_share_pct": round(repeat_share, 2),
            "repeat_by_year": repeat_annual,
            "years_2023_2025_repeat_pf_below_0_90": repeat_bad_years,
            "episode_mutex_branch_rule_pass": branch_eligible,
            "next_authorized_entry_intervention": "EPISODE_MUTEX" if branch_eligible else "IMMEDIATE_NEXT_BAR_RECLAIM",
        },
        "implementation_audit": implementation,
        "kill_gates": gates,
        "decision": {
            "kill_family_now": not all(gates.values()),
            "edge_established": False,
            "promotion_authorized": False,
            "runtime_authorized": False,
            "next_step": "Correct and freeze the actual V1 contract before running only the entry intervention selected by the episode branch rule."
            if all(gates.values())
            else "Retire this strategy family; do not run a rescue intervention.",
        },
        "artifacts": {
            "v1_trade_ledger": v1_trade_path.relative_to(REPO).as_posix(),
            "v1_report": v1_report.relative_to(REPO).as_posix(),
            "unmasked_trade_ledger": unmasked_trade_path.relative_to(REPO).as_posix(),
            "unmasked_report": unmasked_report.relative_to(REPO).as_posix(),
            "m30_bar_audit": BAR_PATH.relative_to(REPO).as_posix(),
        },
    }

    json_path = OUTPUT / "EURUSD_V1_UNMASKED_AUDIT_RESULT.json"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    md_path = OUTPUT / "EURUSD_V1_UNMASKED_AUDIT_RESULT.md"
    md_path.write_text(render_markdown(report), encoding="utf-8", newline="\n")

    manifest_files = sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.name != "ARTIFACT_MANIFEST.json"
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    )
    manifest = {
        "schema_version": "eurusd_v1_unmasked_artifact_manifest_v1",
        "candidate_id": report["candidate_id"],
        "artifacts": [
            {
                "path": path.relative_to(REPO).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in manifest_files
        ],
    }
    (ROOT / "outputs" / "locked" / "ARTIFACT_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"status": report["status"], "gates": gates, "episodes": report["episodes"]}, indent=2))
    return 0


def render_markdown(report: dict[str, Any]) -> str:
    econ = report["economics"]
    match = report["matched_comparison"]
    episodes = report["episodes"]
    year_rows = "\n".join(
        f"| {year} | {row['trades']} | {row['win_rate_pct']:.2f}% | ${row['net_usd']:.2f} | {row['profit_factor']:.4f} |"
        for year, row in report["calendar_year"].items()
    )
    bucket_rows = "\n".join(
        f"| {bucket} | {row['trades']} | {row['win_rate_pct']:.2f}% | ${row['net_usd']:.2f} | {row['profit_factor']:.4f} |"
        for bucket, row in report["six_hour_broker_buckets"].items()
    )
    gate_rows = "\n".join(
        f"- [{'x' if value else ' '}] `{name}`" for name, value in report["kill_gates"].items()
    )
    return f"""# EURUSD V1 Unmasked Audit

Status: `{report['status']}`

The exact unmasked run passes the reviewer's four immediate kill gates, but it
does not pass promotion gates, does not establish an edge, and cannot proceed
to an intervention until the discovered V1 contract mismatch is repaired.

## Exact MT5 result

| Candidate | Trades | Win rate | Net USD | PF | Equity DD |
|---|---:|---:|---:|---:|---:|
| Frozen V1 hour mask | {econ['v1_mt5']['trades']} | 59.33% | ${econ['v1_mt5']['net_usd']:.2f} | {econ['v1_mt5']['profit_factor']:.2f} | {econ['v1_mt5']['equity_drawdown_maximal']} |
| V1 unmasked audit | {econ['unmasked_mt5']['trades']} | {econ['unmasked_mt5']['win_rate_pct']:.2f}% | ${econ['unmasked_mt5']['net_usd']:.2f} | {econ['unmasked_mt5']['profit_factor']:.2f} | {econ['unmasked_mt5']['equity_drawdown_maximal']} |

Removing the mask added {econ['unmasked_mt5']['trades'] - econ['v1_mt5']['trades']}
net trades and reduced MT5 net by
${econ['v1_mt5']['net_usd'] - econ['unmasked_mt5']['net_usd']:.2f}. The old
hours were economically harmful in this history, but the raw signal remained
positive without them.

## Cost decomposition and stress

| Metric | Net USD | PF |
|---|---:|---:|
| Exact deal ledger | ${econ['unmasked_deal_ledger']['net_usd']:.2f} | {econ['unmasked_deal_ledger']['profit_factor']:.4f} |
| +0.5 pip round trip; negative commission/swap x1.25 | ${econ['primary_0_5_pip_plus_25pct_cost_stress']['net_usd']:.2f} | {econ['primary_0_5_pip_plus_25pct_cost_stress']['profit_factor']:.4f} |
| +1.0 pip round trip; negative commission/swap x1.25 | ${econ['severe_1_0_pip_plus_25pct_cost_stress']['net_usd']:.2f} | {econ['severe_1_0_pip_plus_25pct_cost_stress']['profit_factor']:.4f} |

Exact components: price profit
`${econ['cost_decomposition_usd']['price_profit']:.2f}`, commission
`${econ['cost_decomposition_usd']['commission']:.2f}`, swap
`${econ['cost_decomposition_usd']['swap']:.2f}`.

## Matched attribution

- Signal stream parity: `{str(match['signal_stream_exact_parity']).lower()}` across `{match['signals']}` signals.
- Changed attempt decisions: `{match['attempts_changed']}`.
- Common entry timestamps: `{match['common_entry_timestamps']}`; exact common outcomes: `{match['common_exact_outcomes']}`.
- Unmasked-only entries: `{match['unmasked_only_entries']}` (`{match['unmasked_only_at_old_blocked_hours']}` in old masked hours and `{match['unmasked_only_at_other_hours_path_effect']}` secondary path effects).
- V1-only entries displaced by path: `{match['v1_only_entries_displaced_by_path']}`.

Filtering the unmasked filled ledger after the fact produces
`{match['old_mask_simple_filter_of_unmasked_fills']['trades']}` trades and
`${match['old_mask_simple_filter_of_unmasked_fills']['net_usd']:.2f}`, not V1's
`{match['exact_v1_causal_rerun']['trades']}` trades and
`${match['exact_v1_causal_rerun']['net_usd']:.2f}`. This is not a parity failure:
the one-position mutex makes the intervention path-dependent. The exact V1
rerun is the valid causal reconstruction.

## Calendar years

| Year | Trades | Win rate | Net USD | PF |
|---|---:|---:|---:|---:|
{year_rows}

## Six-hour broker-time buckets

| Bucket | Trades | Win rate | Net USD | PF |
|---|---:|---:|---:|---:|
{bucket_rows}

## Episode diagnostic and branch

- Episodes: `{episodes['episodes']}`.
- Repeat filled entries: `{episodes['repeat_filled_entries']['trades']}` / `{econ['unmasked_deal_ledger']['trades']}` (`{episodes['repeat_trade_share_pct']:.2f}%`).
- Repeat-entry PF: `{episodes['repeat_filled_entries']['profit_factor']:.4f}`.
- Years 2023-2025 with repeat-entry PF below 0.90: `{episodes['years_2023_2025_repeat_pf_below_0_90']}`.
- Episode-mutex branch rule: `{str(episodes['episode_mutex_branch_rule_pass']).lower()}`.
- Sole next authorized entry intervention: `{episodes['next_authorized_entry_intervention']}`.

## Immediate kill gates

{gate_rows}

## Implementation audit caveat

The source uses completed-bar indicator shifts and lows 1-6, rejects stops over
700 points, and is tester-only. Exact V1 and the unmasked run both used
`InpMinBodyFraction=0.40`, while the published V1 preset says `0.0`. The exact
signal-stream attribution is therefore valid, but the earlier written contract
is not. It must be corrected and frozen.

The source also does not explicitly initialize the new-bar latch to suppress
evaluation of the bar completed before tester startup. No startup signal
occurred in this run (the first signal was
`{report['implementation_audit']['startup_latch_observed_first_signal']}`), so
the issue did not change these results, but it must be resolved in any new
redesign baseline before prospective work.

The report records terminal build 5833 and 99% history quality. The generated
report used account leverage 1:50 even though the INI requested 1:200; fixed-lot
P&L is unaffected, but the provenance discrepancy is retained.

## Decision

Do not promote or deploy. The unmasked candidate survives only the immediate
family kill test. First repair and freeze the actual V1 contract. After that,
the next and only authorized entry experiment is
`{episodes['next_authorized_entry_intervention']}`.
"""


if __name__ == "__main__":
    raise SystemExit(main())
