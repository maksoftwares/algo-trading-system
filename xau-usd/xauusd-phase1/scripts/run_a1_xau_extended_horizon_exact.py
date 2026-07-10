from __future__ import annotations

"""Run the frozen R1+R2 sources over five- and ten-year exact-MT5 windows."""

import argparse
import csv
import html
import json
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Sequence

import build_a1_xau_fee_evidence_source as fee_source
import run_a1_xau_fee_native_replays_exact as fee
import run_a1_xau_router_entry_hold_path_exact as exact


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
SCHEMA_VERSION = "a1_xau_extended_horizon_exact_v1"
SOURCE_PRIORITY = {
    "r1_h1_pullback_long_v1": 71,
    "h4_d1_long_best_box2_atr80": 80,
    "r2_pullback_rejection_short_v1": 92,
    "r2_continuation_short_v1": 123,
}
DEDUPE_SECONDS = 5 * 60


@dataclass(frozen=True)
class Horizon:
    name: str
    from_date: str
    to_date: str


HORIZONS = (
    Horizon("five_year", "2021.07.01", "2026.06.30"),
    Horizon("ten_year", "2016.07.01", "2026.06.30"),
)


def render_ini(sections: dict[str, dict[str, str]]) -> str:
    lines: list[str] = []
    for section_name in ("Tester", "TesterInputs"):
        lines.append(f"[{section_name}]")
        lines.extend(f"{key}={value}" for key, value in sections[section_name].items())
        lines.append("")
    return "\n".join(lines)


def derive_horizon_config(original_text: str, spec: fee.SourceSpec, horizon: Horizon) -> tuple[str, dict[str, str]]:
    base_text, _ = fee.derive_replay_config(original_text, spec)
    sections = exact.parse_ini(base_text)
    tester = sections["Tester"]
    inputs = sections["TesterInputs"]
    stem = f"{fee.safe_name(spec.source_id)}_{horizon.name}"
    tester["FromDate"] = horizon.from_date
    tester["ToDate"] = horizon.to_date
    tester["Report"] = f"Reports\\A1_XAU_EXTENDED_{stem.upper()}"
    log_names = {key: f"a1_xau_extended_{stem}_{suffix}" for key, suffix in fee.LOG_INPUTS.items()}
    inputs.update(log_names)
    text = render_ini(sections)
    parsed = exact.parse_ini(text)
    if set(parsed) != {"Tester", "TesterInputs"} or "[Common]" in text:
        raise RuntimeError("Extended tester config contains an account/session section")
    if parsed["Tester"]["UseRemote"] != "0" or parsed["Tester"]["UseCloud"] != "0":
        raise RuntimeError("Extended tester config enables nonlocal agents")
    return text, log_names


def decimal_value(value: Any, label: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise RuntimeError(f"Invalid decimal {label}: {value!r}") from exc
    if not result.is_finite():
        raise RuntimeError(f"Nonfinite decimal {label}")
    return result


def build_native_trades(source_id: str, deal_log: Path) -> list[dict[str, Any]]:
    fields, rows = fee.read_tsv(deal_log)
    required = {
        "timestamp_broker", "run_id", "account", "symbol", "magic", "deal_ticket", "position_id",
        "entry_code", "type_code", "reason_code", "direction", "volume", "price", "profit",
        "commission", "swap", "fee", "order_ticket", "comment",
    }
    if not required.issubset(fields):
        raise RuntimeError(f"Deal schema incomplete for {source_id}")
    grouped: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if decimal_value(row["fee"], "fee") != 0:
            raise RuntimeError(f"Nonzero DEAL_FEE in {source_id}")
        grouped[row["position_id"]].append(row)
    trades: list[dict[str, Any]] = []
    for position_id, deals in grouped.items():
        entries = [row for row in deals if row["entry_code"] == "0"]
        exits = [row for row in deals if row["entry_code"] in {"1", "3"}]
        if len(entries) != 1 or len(exits) != 1 or len(deals) != 2:
            raise RuntimeError(f"Native position is not one-entry/one-exit: {source_id}/{position_id}")
        entry, exit_row = entries[0], exits[0]
        if decimal_value(entry["volume"], "entry volume") != decimal_value(exit_row["volume"], "exit volume"):
            raise RuntimeError(f"Native position volume mismatch: {source_id}/{position_id}")
        pnl = sum(
            (
                decimal_value(row["profit"], "profit")
                + decimal_value(row["commission"], "commission")
                + decimal_value(row["swap"], "swap")
                + decimal_value(row["fee"], "fee")
                for row in deals
            ),
            Decimal("0"),
        )
        trades.append(
            {
                "source_id": source_id,
                "source_priority": SOURCE_PRIORITY[source_id],
                "trade_id": "::".join(
                    [source_id, entry["run_id"], entry["account"], entry["symbol"], entry["magic"], position_id]
                ),
                "run_id": entry["run_id"],
                "account": entry["account"],
                "symbol": entry["symbol"],
                "magic": entry["magic"],
                "position_id": position_id,
                "entry_deal": entry["deal_ticket"],
                "exit_deal": exit_row["deal_ticket"],
                "entry_order": entry["order_ticket"],
                "exit_order": exit_row["order_ticket"],
                "entry_time": entry["timestamp_broker"].replace(".", "-", 2),
                "exit_time": exit_row["timestamp_broker"].replace(".", "-", 2),
                "direction": entry["direction"],
                "volume": entry["volume"],
                "entry_price": entry["price"],
                "exit_price": exit_row["price"],
                "exit_reason_code": exit_row["reason_code"],
                "pnl_usd": str(pnl),
                "tickets": 1,
            }
        )
    return sorted(trades, key=lambda row: (row["entry_time"], row["source_priority"], row["source_id"], int(row["position_id"])))


def dedupe_portfolio(trades: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ordered = sorted(
        trades,
        key=lambda row: (row["entry_time"], row["source_priority"], row["source_id"], row["direction"], int(row["position_id"])),
    )
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for row in ordered:
        entry = datetime.fromisoformat(row["entry_time"])
        duplicate = None
        for previous in reversed(kept[-50:]):
            delta = (entry - datetime.fromisoformat(previous["entry_time"])).total_seconds()
            if delta > DEDUPE_SECONDS:
                break
            if abs(delta) <= DEDUPE_SECONDS and row["direction"] == previous["direction"] and row["source_id"] != previous["source_id"]:
                duplicate = previous
                break
        if duplicate is None:
            kept.append(row)
        else:
            dropped.append(
                {
                    **row,
                    "drop_reason": "same_direction_overlap_5m",
                    "duplicate_of_trade_id": duplicate["trade_id"],
                }
            )
    return kept, dropped


def metrics(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    pnls = [decimal_value(row["pnl_usd"], "pnl") for row in rows]
    wins = [value for value in pnls if value > 0]
    losses = [value for value in pnls if value < 0]
    gross_win = sum(wins, Decimal("0"))
    gross_loss = abs(sum(losses, Decimal("0")))
    avg_win = gross_win / len(wins) if wins else Decimal("0")
    avg_loss = gross_loss / len(losses) if losses else Decimal("0")
    stressed = [value - Decimal("0.30") * int(row.get("tickets", 1)) for value, row in zip(pnls, rows)]
    stress_win = sum((value for value in stressed if value > 0), Decimal("0"))
    stress_loss = abs(sum((value for value in stressed if value < 0), Decimal("0")))
    equity = Decimal("0")
    peak = Decimal("0")
    max_dd = Decimal("0")
    for row in sorted(rows, key=lambda item: (item["exit_time"], item["entry_time"], item["source_priority"], item["source_id"], int(item["position_id"]))):
        equity += decimal_value(row["pnl_usd"], "pnl")
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return {
        "trades": len(rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(100 * len(wins) / len(rows), 2) if rows else 0.0,
        "avg_win_loss": float(round(avg_win / avg_loss, 4)) if avg_loss else None,
        "profit_factor": float(round(gross_win / gross_loss, 4)) if gross_loss else None,
        "net_usd": float(round(sum(pnls, Decimal("0")), 2)),
        "stress_net_030_usd": float(round(sum(stressed, Decimal("0")), 2)),
        "stress_profit_factor": float(round(stress_win / stress_loss, 4)) if stress_loss else None,
        "max_closed_drawdown_usd": float(round(max_dd, 2)),
    }


def grouped_rows(rows: Sequence[dict[str, Any]], period: str) -> list[dict[str, Any]]:
    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        timestamp = datetime.fromisoformat(row["entry_time"])
        key = timestamp.strftime("%Y") if period == "year" else timestamp.strftime("%Y-%m")
        groups[key].append(row)
    return [{period: key, **metrics(group)} for key, group in sorted(groups.items())]


def rolling_months(monthly: Sequence[dict[str, Any]], horizon: int) -> list[dict[str, Any]]:
    if not monthly:
        return []
    values = {row["month"]: Decimal(str(row["net_usd"])) for row in monthly}
    start = datetime.strptime(monthly[0]["month"], "%Y-%m")
    end = datetime.strptime(monthly[-1]["month"], "%Y-%m")
    months: list[str] = []
    cursor = start
    while cursor <= end:
        months.append(cursor.strftime("%Y-%m"))
        cursor = datetime(cursor.year + (cursor.month == 12), 1 if cursor.month == 12 else cursor.month + 1, 1)
    output: list[dict[str, Any]] = []
    for index in range(horizon - 1, len(months)):
        window = months[index - horizon + 1 : index + 1]
        output.append(
            {
                "months": horizon,
                "start_month": window[0],
                "end_month": window[-1],
                "net_usd": float(round(sum((values.get(month, Decimal("0")) for month in window), Decimal("0")), 2)),
            }
        )
    return output


def parse_report_metrics(path: Path) -> dict[str, str]:
    text = exact.read_text(path)
    rows: list[list[str]] = []
    for match in re.finditer(r"<tr[^>]*>(.*?)</tr>", text, flags=re.I | re.S):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", match.group(1), flags=re.I | re.S)
        cleaned = [html.unescape(re.sub(r"<[^>]+>", "", cell)).strip().replace("\xa0", " ") for cell in cells]
        if cleaned:
            rows.append(cleaned)
    flat = [cell for row in rows for cell in row]
    labels = (
        "History Quality:", "Bars:", "Ticks:", "Total Trades:", "Total Deals:", "Total Net Profit:",
        "Balance Drawdown Maximal:", "Equity Drawdown Maximal:", "Profit Factor:",
    )
    output: dict[str, str] = {}
    for label in labels:
        for index, cell in enumerate(flat[:-1]):
            if cell == label:
                output[label.rstrip(":")] = flat[index + 1]
                break
    exact.require_build(text, path.name)
    return output


def write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run_one(
    *, spec: fee.SourceSpec, horizon: Horizon, package_dir: Path, sandbox: Path, terminal: Path,
    output_dir: Path, timeout_seconds: int,
) -> dict[str, Any]:
    frozen_dir = package_dir / "immutable_evidence" / spec.source_id
    config_text, log_names = derive_horizon_config(exact.read_text(frozen_dir / "tester.ini"), spec, horizon)
    config = sandbox / "Config" / f"A1_XAU_EXTENDED_{fee.safe_name(spec.source_id)}_{horizon.name}.ini"
    config.write_text(config_text, encoding="utf-8", newline="\n")
    parsed = exact.parse_ini(config_text)
    report_name = parsed["Tester"]["Report"].replace("\\", "/").split("/")[-1] + ".htm"
    report = sandbox / "Reports" / report_name
    if report.exists():
        report.unlink()
    files_dir = sandbox / "Tester" / "Agent-127.0.0.1-3000" / "MQL5" / "Files"
    for name in log_names.values():
        path = files_dir / name
        if path.exists():
            path.unlink()
    exact.run_checked(
        [str(terminal), "/portable", f"/config:{config}"], cwd=sandbox, timeout_seconds=timeout_seconds,
        command_runner=exact.default_command_runner, label=f"MT5 {horizon.name} {spec.source_id}",
    )
    run_dir = output_dir / "runs" / horizon.name / spec.source_id
    run_dir.mkdir(parents=True, exist_ok=True)
    copied_config = fee.copy_required(config, run_dir / "tester.ini")
    copied_report = fee.copy_required(report, run_dir / report.name)
    logs: dict[str, Path] = {}
    for input_name, name in log_names.items():
        source = files_dir / name
        destination = run_dir / name
        if input_name == "InpManagementLogFileName" and not source.exists():
            destination.write_bytes(b"")
        else:
            fee.copy_required(source, destination)
        logs[input_name] = destination
    trades = build_native_trades(spec.source_id, logs["InpDealLogFileName"])
    order_fields, order_rows = fee.read_tsv(logs["InpOrderLogFileName"])
    if "action" not in order_fields:
        raise RuntimeError("Order log schema missing action")
    actions = Counter(row["action"] for row in order_rows)
    failed_actions = {"ORDER_SEND_FAIL", "SPLIT_TP1_ORDER_SEND_FAIL", "SPLIT_RUNNER_ORDER_SEND_FAIL"}
    order_failures = [
        {
            key: row.get(key, "")
            for key in (
                "timestamp_broker", "action", "direction", "lots", "bid", "ask", "sl", "tp",
                "retcode", "retcode_description", "reason",
            )
        }
        for row in order_rows
        if row.get("action") in failed_actions
    ]
    report_metrics = parse_report_metrics(copied_report)
    if report_metrics.get("History Quality") != exact.EXPECTED_HISTORY_QUALITY:
        raise RuntimeError(f"Unexpected history quality in {horizon.name}/{spec.source_id}")
    if exact.metric_int(report_metrics, "Bars") <= 0 or exact.metric_int(report_metrics, "Ticks") <= 0:
        raise RuntimeError(f"Missing MT5 history in {horizon.name}/{spec.source_id}")
    return {
        "source_id": spec.source_id,
        "horizon": horizon.name,
        "source_commit": spec.source_commit,
        "source_sha256": spec.source_sha256,
        "config_sha256": exact.sha256_file(copied_config),
        "report_sha256": exact.sha256_file(copied_report),
        "report_metrics": report_metrics,
        "trade_metrics": metrics(trades),
        "order_actions": dict(actions),
        "order_failures": order_failures,
        "trades": trades,
        "artifacts": {key: value.relative_to(output_dir).as_posix() for key, value in logs.items()},
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAUUSD Extended-Horizon Exact-MT5 Development Backtests", "",
        f"Generated UTC: `{payload['generated_at_utc']}`", "",
        "These are development-data diagnostics. They are not an untouched holdout and authorize no broker action.", "",
        "| Window | Trades | WR% | W/L | PF | Net USD | Stress net | Max closed DD | +6M rolls | +12M rolls |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["horizons"]:
        shape = row["portfolio_metrics"]
        lines.append(
            f"| `{row['name']}` | {shape['trades']} | {shape['win_rate_pct']:.2f} | "
            f"{shape['avg_win_loss'] or 0:.4f} | {shape['profit_factor'] or 0:.4f} | "
            f"{shape['net_usd']:.2f} | {shape['stress_net_030_usd']:.2f} | "
            f"{shape['max_closed_drawdown_usd']:.2f} | {row['rolling_summary']['positive_6m']}/{row['rolling_summary']['total_6m']} | "
            f"{row['rolling_summary']['positive_12m']}/{row['rolling_summary']['total_12m']} |"
        )
    lines.extend(["", "## Source Attribution", "", "| Window | Source | Trades | PF | Net | Closed DD | MT5 equity DD |", "| --- | --- | ---: | ---: | ---: | ---: | --- |"])
    for horizon in payload["horizons"]:
        for source in horizon["sources"]:
            metric = source["trade_metrics"]
            lines.append(
                f"| `{horizon['name']}` | `{source['source_id']}` | {metric['trades']} | "
                f"{metric['profit_factor'] or 0:.4f} | {metric['net_usd']:.2f} | {metric['max_closed_drawdown_usd']:.2f} | "
                f"{source['report_metrics'].get('Equity Drawdown Maximal', 'n/a')} |"
            )
    lines.extend(["", "## Execution defects", ""])
    failures = [
        (horizon["name"], source["source_id"], failure)
        for horizon in payload["horizons"]
        for source in horizon["sources"]
        for failure in source["order_failures"]
    ]
    if failures:
        lines.extend(["| Window | Source | Time | Retcode | Description |", "| --- | --- | --- | ---: | --- |"])
        for horizon_name, source_id, failure in failures:
            lines.append(
                f"| `{horizon_name}` | `{source_id}` | {failure['timestamp_broker']} | "
                f"{failure['retcode']} | {failure['retcode_description']} |"
            )
    else:
        lines.append("No order-send failures.")
    lines.extend(["", "## Interpretation boundary", "", "Any recorded order-send failure is a hard NO-GO and is not removed from the evidence. Portfolio drawdown above is closed-equity drawdown after the frozen five-minute ownership rule. Source-level MT5 equity drawdown is retained from each native report. A true integrated portfolio equity-DD result still requires the separately governed integrated MT5 harness.", ""])
    return "\n".join(lines)


def run_extended(
    *, tester_sandbox: Path, metaeditor: Path, package_dir: Path, baseline_fee_manifest: Path,
    output_dir: Path, timeout_seconds: int = 3600,
) -> Path:
    fee_payload = json.loads(baseline_fee_manifest.read_text(encoding="utf-8"))
    if fee_payload.get("status") != "FEE_NATIVE_REPLAY_VALID":
        raise RuntimeError("Four-year source-identity/fee replay is not valid; extended testing is blocked")
    sandbox = tester_sandbox.resolve()
    terminal = exact.validate_strategy_tester_sandbox(sandbox)
    editor = exact.validate_metaeditor(metaeditor)
    package_dir = package_dir.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError(f"Extended output directory must be new or empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    expert_dir = sandbox / "MQL5" / "Experts" / "A1Audit"
    expert_dir.mkdir(parents=True, exist_ok=True)
    for spec in fee.SOURCE_SPECS:
        source = expert_dir / f"{spec.expert_name}.mq5"
        manifest = output_dir / "compiled" / f"{fee.safe_name(spec.source_id)}_source_manifest.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        fee_source.build_fee_evidence_source(
            REPO_ROOT, source, manifest, source_commit=spec.source_commit,
            source_sha256=spec.source_sha256, generated_expert_name=spec.expert_name,
        )
        compile_log = sandbox / "Logs" / f"compile_A1_XAU_EXTENDED_{fee.safe_name(spec.source_id)}.log"
        ex5 = exact.compile_program(
            source, editor, sandbox, compile_log, timeout_seconds=timeout_seconds,
            command_runner=exact.default_command_runner,
        )
        for path in (source, ex5, compile_log):
            fee.copy_required(path, output_dir / "compiled" / fee.safe_name(spec.source_id) / path.name)

    horizon_results: list[dict[str, Any]] = []
    for horizon in HORIZONS:
        source_results = [
            run_one(
                spec=spec, horizon=horizon, package_dir=package_dir, sandbox=sandbox, terminal=terminal,
                output_dir=output_dir, timeout_seconds=timeout_seconds,
            )
            for spec in fee.SOURCE_SPECS
        ]
        all_trades = [trade for source in source_results for trade in source.pop("trades")]
        kept, dropped = dedupe_portfolio(all_trades)
        monthly = grouped_rows(kept, "month")
        yearly = grouped_rows(kept, "year")
        rolling6 = rolling_months(monthly, 6)
        rolling12 = rolling_months(monthly, 12)
        base = output_dir / f"A1_XAU_EXTENDED_{horizon.name.upper()}_20260711"
        write_csv(base.with_name(base.name + "_KEPT.csv"), kept)
        write_csv(base.with_name(base.name + "_DROPPED.csv"), dropped)
        write_csv(base.with_name(base.name + "_MONTHLY.csv"), monthly)
        write_csv(base.with_name(base.name + "_YEARLY.csv"), yearly)
        write_csv(base.with_name(base.name + "_ROLLING.csv"), [*rolling6, *rolling12])
        horizon_results.append(
            {
                "name": horizon.name,
                "from_date": horizon.from_date,
                "to_date": horizon.to_date,
                "sources": source_results,
                "raw_source_trades": len(all_trades),
                "dropped_overlaps": len(dropped),
                "portfolio_metrics": metrics(kept),
                "monthly": monthly,
                "yearly": yearly,
                "rolling_summary": {
                    "total_6m": len(rolling6),
                    "positive_6m": sum(row["net_usd"] > 0 for row in rolling6),
                    "worst_6m_usd": min((row["net_usd"] for row in rolling6), default=0),
                    "total_12m": len(rolling12),
                    "positive_12m": sum(row["net_usd"] > 0 for row in rolling12),
                    "worst_12m_usd": min((row["net_usd"] for row in rolling12), default=0),
                },
            }
        )
    five_bars = {exact.metric_int(source["report_metrics"], "Bars") for source in horizon_results[0]["sources"]}
    ten_bars = {exact.metric_int(source["report_metrics"], "Bars") for source in horizon_results[1]["sources"]}
    five_ticks = {exact.metric_int(source["report_metrics"], "Ticks") for source in horizon_results[0]["sources"]}
    ten_ticks = {exact.metric_int(source["report_metrics"], "Ticks") for source in horizon_results[1]["sources"]}
    if len(five_bars) != 1 or len(ten_bars) != 1 or len(five_ticks) != 1 or len(ten_ticks) != 1:
        raise RuntimeError("Source runs do not share identical MT5 history coverage inside a horizon")
    if min(five_bars) <= exact.EXPECTED_BARS or min(five_ticks) <= exact.EXPECTED_TICKS:
        raise RuntimeError("Five-year run did not extend beyond the frozen four-year history")
    if min(ten_bars) <= min(five_bars) or min(ten_ticks) <= min(five_ticks):
        raise RuntimeError("Ten-year run did not extend beyond the five-year history")
    order_failure_count = sum(
        len(source["order_failures"])
        for horizon in horizon_results
        for source in horizon["sources"]
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": (
            "EXTENDED_HORIZON_NO_GO_ORDER_FAILURES"
            if order_failure_count
            else "EXTENDED_HORIZON_DEVELOPMENT_EVIDENCE_GENERATED"
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": {
            "strategy_tester_only": True,
            "development_data_not_holdout": True,
            "broker_action_authorized": False,
            "integrated_portfolio_equity_dd_claimed": False,
        },
        "baseline_fee_manifest_sha256": exact.sha256_file(baseline_fee_manifest),
        "order_failure_count": order_failure_count,
        "horizons": horizon_results,
    }
    json_path = output_dir / "A1_XAU_EXTENDED_HORIZON_EXACT_MT5_20260711.json"
    md_path = output_dir / "A1_XAU_EXTENDED_HORIZON_EXACT_MT5_20260711.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    manifest = output_dir / "manifest.json"
    manifest.write_text(
        json.dumps({"status": payload["status"], "artifacts": exact.manifest_artifacts(output_dir)}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return json_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tester-sandbox", type=Path, required=True)
    parser.add_argument("--metaeditor", type=Path, required=True)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--baseline-fee-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(
        run_extended(
            tester_sandbox=args.tester_sandbox, metaeditor=args.metaeditor,
            package_dir=args.package_dir, baseline_fee_manifest=args.baseline_fee_manifest,
            output_dir=args.output_dir, timeout_seconds=args.timeout_seconds,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
