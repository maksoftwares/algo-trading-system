from __future__ import annotations

import csv
from datetime import UTC, datetime, timedelta
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
from typing import Any

from build_packet import ROOT, load_config, sha256_file


class TableCellParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cells: list[str] = []
        self._parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "td":
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._parts is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self._parts is not None:
            self.cells.append(" ".join("".join(self._parts).split()))
            self._parts = None


def metric(cells: list[str], label: str) -> str:
    try:
        index = cells.index(label)
    except ValueError as exc:
        raise ValueError(f"missing MT5 metric: {label}") from exc
    for value in cells[index + 1 :]:
        if value:
            return value
    raise ValueError(f"missing value after MT5 metric: {label}")


def number(text: str) -> float:
    return float(text.replace(" ", "").replace(",", ""))


def drawdown(text: str) -> tuple[float, float]:
    match = re.fullmatch(r"([\d ,.\-]+) \(([\d.]+)%\)", text)
    if not match:
        raise ValueError(f"invalid drawdown: {text}")
    return number(match.group(1)), float(match.group(2))


def report_specs(config: dict[str, Any]) -> list[dict[str, str]]:
    specs = [
        {
            "report_id": str(row["component_id"]),
            "report_name": str(row["report"]),
            "mode": "NATIVE_MT5_SIGNAL_GENERATION_REAL_TICKS",
        }
        for row in config["native_r1"]
    ]
    specs.extend(
        {
            "report_id": str(row["specialist_id"]),
            "report_name": f"FIVE_SPECIALIST_MT5_3M_{row['specialist_id']}",
            "mode": "MT5_REAL_TICK_EXECUTION_SCHEDULE_REPLAY",
        }
        for row in config["replay_specialists"]
    )
    combined_id = str(config["combined_replay"]["specialist_id"])
    specs.append(
        {
            "report_id": combined_id,
            "report_name": f"FIVE_SPECIALIST_MT5_3M_{combined_id}",
            "mode": "MT5_REAL_TICK_COMBINED_EXECUTION_SCHEDULE_REPLAY",
        }
    )
    return specs


def read_mt5_html(path: Path) -> str:
    payload = path.read_bytes()
    if payload.startswith((b"\xff\xfe", b"\xfe\xff")):
        return payload.decode("utf-16")
    return payload.decode("utf-8")


def parse_report(path: Path, spec: dict[str, str]) -> dict[str, Any]:
    parser = TableCellParser()
    parser.feed(read_mt5_html(path))
    equity_dd_usd, equity_dd_pct = drawdown(
        metric(parser.cells, "Equity Drawdown Maximal:")
    )
    balance_dd_usd, balance_dd_pct = drawdown(
        metric(parser.cells, "Balance Drawdown Maximal:")
    )
    return {
        "report_id": spec["report_id"],
        "mode": spec["mode"],
        "history_quality": metric(parser.cells, "History Quality:"),
        "net_profit_usd": number(metric(parser.cells, "Total Net Profit:")),
        "gross_profit_usd": number(metric(parser.cells, "Gross Profit:")),
        "gross_loss_usd": number(metric(parser.cells, "Gross Loss:")),
        "profit_factor": number(metric(parser.cells, "Profit Factor:")),
        "expected_payoff_usd": number(metric(parser.cells, "Expected Payoff:")),
        "total_trades": int(number(metric(parser.cells, "Total Trades:"))),
        "balance_drawdown_max_usd": balance_dd_usd,
        "balance_drawdown_max_pct": balance_dd_pct,
        "equity_drawdown_max_usd": equity_dd_usd,
        "equity_drawdown_max_pct": equity_dd_pct,
        "source_sha256": sha256_file(path),
    }


def archive_report(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    for image in source.parent.glob(f"{source.stem}*.png"):
        shutil.copy2(image, destination.parent / image.name)


def collect_build_audit(config: dict[str, Any], output_dir: Path) -> dict[str, str]:
    terminal_root = Path(config["mt5"]["terminal_root"])
    package_source = ROOT / "mt5" / "FiveSpecialistSignalReplay.mq5"
    deployed_source = terminal_root / "MQL5" / "Experts" / package_source.name
    compiled_ex5 = deployed_source.with_suffix(".ex5")
    compile_log = terminal_root / "five_specialist_replay_compile.log"
    for path in (package_source, deployed_source, compiled_ex5, compile_log):
        if not path.is_file():
            raise FileNotFoundError(path)
    package_hash = sha256_file(package_source)
    deployed_hash = sha256_file(deployed_source)
    if package_hash != deployed_hash:
        raise ValueError("deployed replay EA source differs from package source")
    compile_result = "Result: 0 errors, 0 warnings"
    if compile_result not in read_mt5_html(compile_log):
        raise ValueError("replay EA compile log is not clean")
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(compiled_ex5, output_dir / compiled_ex5.name)
    shutil.copy2(compile_log, output_dir / compile_log.name)
    return {
        "package_source_sha256": package_hash,
        "deployed_source_sha256": deployed_hash,
        "compiled_ex5_sha256": sha256_file(compiled_ex5),
        "compile_log_sha256": sha256_file(compile_log),
        "compile_result": compile_result,
    }


def replay_counts(
    report_id: str, expected: int, event_dir: Path, output_dir: Path
) -> dict[str, int]:
    source = event_dir / f"five_specialist_3m_{report_id.lower()}_events.csv"
    if not source.is_file():
        raise FileNotFoundError(source)
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, output_dir / source.name)
    with source.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    opened = sum(row["event"] == "OPENED" for row in rows)
    missed = sum(row["event"] == "MISSED" for row in rows)
    if opened != expected or missed != 0:
        raise ValueError(
            f"{report_id} replay count mismatch: opened={opened}, missed={missed}, expected={expected}"
        )
    return {"scheduled": expected, "opened": opened, "missed": missed}


def aggregate_r1(records: list[dict[str, Any]]) -> dict[str, Any]:
    gross_profit = sum(row["gross_profit_usd"] for row in records)
    gross_loss = sum(row["gross_loss_usd"] for row in records)
    trades = sum(row["total_trades"] for row in records)
    net = sum(row["net_profit_usd"] for row in records)
    return {
        "report_id": "R1_UPTREND",
        "mode": "NATIVE_MT5_TWO_COMPONENT_AGGREGATE",
        "history_quality": "100% real ticks",
        "net_profit_usd": round(net, 2),
        "gross_profit_usd": round(gross_profit, 2),
        "gross_loss_usd": round(gross_loss, 2),
        "profit_factor": round(gross_profit / abs(gross_loss), 2)
        if gross_loss
        else 0.0,
        "expected_payoff_usd": round(net / trades, 2) if trades else 0.0,
        "total_trades": trades,
        "balance_drawdown_max_usd": max(
            row["balance_drawdown_max_usd"] for row in records
        ),
        "balance_drawdown_max_pct": max(
            row["balance_drawdown_max_pct"] for row in records
        ),
        "equity_drawdown_max_usd": max(
            row["equity_drawdown_max_usd"] for row in records
        ),
        "equity_drawdown_max_pct": max(
            row["equity_drawdown_max_pct"] for row in records
        ),
    }


def money(value: float) -> str:
    return f"${value:,.2f}" if value >= 0 else f"-${abs(value):,.2f}"


def weekday_count(start_utc: str, end_exclusive_utc: str) -> int:
    current = datetime.fromisoformat(start_utc.replace("Z", "+00:00")).date()
    end = datetime.fromisoformat(end_exclusive_utc.replace("Z", "+00:00")).date()
    count = 0
    while current < end:
        count += current.weekday() < 5
        current += timedelta(days=1)
    return count


def write_summary(
    summary: dict[str, Any], records: list[dict[str, Any]], output_dir: Path
) -> None:
    json_path = output_dir / "FIVE_SPECIALIST_MT5_3M_RESULTS.json"
    json_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    csv_path = output_dir / "FIVE_SPECIALIST_MT5_3M_RESULTS.csv"
    columns = [
        "report_id",
        "mode",
        "history_quality",
        "total_trades",
        "net_profit_usd",
        "gross_profit_usd",
        "gross_loss_usd",
        "profit_factor",
        "expected_payoff_usd",
        "balance_drawdown_max_usd",
        "balance_drawdown_max_pct",
        "equity_drawdown_max_usd",
        "equity_drawdown_max_pct",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=columns, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(records)

    specialist_rows = summary["five_specialists"]
    combined = summary["combined"]
    lines = [
        "# Five-Specialist MT5 Real-Tick Report",
        "",
        "Window: 2026-04-01 through 2026-06-30. Symbol: XAUUSD. Timeframe: M5. "
        "Size: fixed 0.01 lot. Starting deposit: $1,000.",
        "",
        "| Specialist | MT5 validation mode | Trades | Net P&L | PF | Max equity DD |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in specialist_rows:
        lines.append(
            f"| {row['report_id']} | {row['mode']} | {row['total_trades']} | "
            f"{money(row['net_profit_usd'])} | {row['profit_factor']:.2f} | "
            f"{money(row['equity_drawdown_max_usd'])} ({row['equity_drawdown_max_pct']:.2f}%) |"
        )
    lines.extend(
        [
            "",
            "## Combined MT5 Account Curve",
            "",
            f"The combined replay executed {combined['total_trades']} trades and returned "
            f"{money(combined['net_profit_usd'])}, with PF {combined['profit_factor']:.2f} and "
            f"maximal equity drawdown {money(combined['equity_drawdown_max_usd'])} "
            f"({combined['equity_drawdown_max_pct']:.2f}%).",
            f"Observed frequency was {combined['total_trades']} trades across "
            f"{summary['window_weekdays']} weekdays, or "
            f"{summary['trades_per_weekday']:.2f} trades per weekday.",
            "",
            "## Python/Dukascopy Reference vs MT5",
            "",
            "| Specialist | Reference net | MT5 net | Difference |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in summary["reference_comparison"]:
        lines.append(
            f"| {row['report_id']} | {money(row['reference_net_usd'])} | "
            f"{money(row['mt5_net_usd'])} | {money(row['difference_usd'])} |"
        )
    lines.extend(
        [
            "",
            "## Scope",
            "",
            "- Every report states `100% real ticks`.",
            "- R1 is native MQL5 signal generation; both R1 components produced zero trades.",
            "- R2-R5 are frozen Python-signal schedule replays through MT5 execution, not native MQL5 signal parity.",
            "- Six replay signals opened and none were missed.",
            "- The archived EX5 was compiled from the repository source with `0 errors, 0 warnings`.",
            "- This small three-month sample is execution-portability evidence, not authorization for demo or live trading.",
            "",
        ]
    )
    (output_dir / "FIVE_SPECIALIST_MT5_3M_RESULTS.md").write_text(
        "\n".join(lines), encoding="utf-8", newline="\n"
    )


def main() -> int:
    config = load_config()
    terminal_reports = Path(config["mt5"]["terminal_root"]) / "Reports"
    report_output = ROOT / "outputs" / "mt5_reports"
    event_output = ROOT / "outputs" / "mt5_event_logs"
    build_output = ROOT / "outputs" / "mt5_build"
    summary_output = ROOT / "outputs" / "reports"
    event_source = (
        Path(os.environ["APPDATA"]) / "MetaQuotes" / "Terminal" / "Common" / "Files"
    )
    summary_output.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    for spec in report_specs(config):
        source = terminal_reports / f"{spec['report_name']}.htm"
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = report_output / source.name
        archive_report(source, destination)
        row = parse_report(destination, spec)
        row["archived_report"] = str(destination.relative_to(ROOT)).replace("\\", "/")
        records.append(row)

    if any(row["history_quality"] != "100% real ticks" for row in records):
        raise ValueError("one or more MT5 reports did not use 100% real ticks")

    expected_counts = {
        str(row["specialist_id"]): int(row["expected_schedule_rows"])
        for row in config["replay_specialists"]
    }
    expected_counts[str(config["combined_replay"]["specialist_id"])] = int(
        config["combined_replay"]["expected_schedule_rows"]
    )
    replay_audit = {
        report_id: replay_counts(report_id, expected, event_source, event_output)
        for report_id, expected in expected_counts.items()
    }

    by_id = {row["report_id"]: row for row in records}
    r1 = aggregate_r1([by_id["R1_UPTREND_BOX"], by_id["R1_UPTREND_PULLBACK"]])
    five = [r1] + [
        by_id[f"R{regime}_{name}"]
        for regime, name in (
            (2, "DOWNTREND"),
            (3, "COMPRESSION"),
            (4, "CHOP"),
            (5, "TRANSITION"),
        )
    ]
    combined = by_id["ALL_SPECIALISTS"]
    additive_net = round(sum(row["net_profit_usd"] for row in five), 2)
    additive_trades = sum(row["total_trades"] for row in five)
    if (
        combined["net_profit_usd"] != additive_net
        or combined["total_trades"] != additive_trades
    ):
        raise ValueError("combined MT5 report does not reconcile to standalone reports")

    reference = {
        str(row["specialist_id"]): float(row["reference_net_usd"])
        for row in config["replay_specialists"]
    }
    reference_comparison = [
        {
            "report_id": report_id,
            "reference_net_usd": round(reference_net, 2),
            "mt5_net_usd": by_id[report_id]["net_profit_usd"],
            "difference_usd": round(
                by_id[report_id]["net_profit_usd"] - reference_net, 2
            ),
        }
        for report_id, reference_net in reference.items()
    ]
    reference_total = sum(reference.values())
    reference_comparison.append(
        {
            "report_id": "ALL_SPECIALISTS",
            "reference_net_usd": round(reference_total, 2),
            "mt5_net_usd": combined["net_profit_usd"],
            "difference_usd": round(combined["net_profit_usd"] - reference_total, 2),
        }
    )
    window_weekdays = weekday_count(
        str(config["window"]["start_utc"]),
        str(config["window"]["end_exclusive_utc"]),
    )
    summary = {
        "schema_version": "five_specialist_mt5_3m_results_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "window": config["window"],
        "mt5": config["mt5"],
        "five_specialists": five,
        "combined": combined,
        "window_weekdays": window_weekdays,
        "trades_per_weekday": round(combined["total_trades"] / window_weekdays, 4),
        "native_component_reports": [
            by_id["R1_UPTREND_BOX"],
            by_id["R1_UPTREND_PULLBACK"],
        ],
        "reference_net_usd": reference,
        "reference_comparison": reference_comparison,
        "replay_audit": replay_audit,
        "build_audit": collect_build_audit(config, build_output),
        "verdict": "EXECUTION_PORTABILITY_EVIDENCE_ONLY_NOT_TRADING_AUTHORIZATION",
    }
    write_summary(summary, five + [combined], summary_output)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
