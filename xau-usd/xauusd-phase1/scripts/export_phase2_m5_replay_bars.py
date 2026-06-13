from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TERMINAL_EXE = Path("C:/Program Files/MetaTrader 5/terminal64.exe")
DEFAULT_OUTPUT_DIR = Path("outputs") / "reports" / "m5_replay_bars"
DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "PHASE2_M5_REPLAY_BAR_EXPORT_REPORT.json"
DEFAULT_REPORT_MD = Path("outputs") / "reports" / "PHASE2_M5_REPLAY_BAR_EXPORT_REPORT.md"
DEFAULT_SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]
DEFAULT_TIMEFRAMES = ["M5"]
DEFAULT_START = "2026-06-01 00:00:00"

BAR_FIELDS = [
    "bar_start_utc",
    "bar_end_utc",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "real_volume",
    "symbol",
    "timeframe",
    "source_terminal",
]


def export_phase2_m5_replay_bars(
    phase1_root: Path,
    terminal_exe: Path = DEFAULT_TERMINAL_EXE,
    symbols: list[str] | None = None,
    timeframes: list[str] | None = None,
    start_text: str = DEFAULT_START,
    end_text: str | None = None,
    output_dir: Path | None = None,
    report_json: Path | None = None,
) -> Path:
    phase1_root = phase1_root.resolve()
    terminal_exe = terminal_exe.resolve()
    symbols = [symbol.upper() for symbol in (symbols or DEFAULT_SYMBOLS)]
    timeframes = [timeframe.upper() for timeframe in (timeframes or DEFAULT_TIMEFRAMES)]
    output_dir = (output_dir or phase1_root / DEFAULT_OUTPUT_DIR).resolve()
    report_json = (report_json or phase1_root / DEFAULT_REPORT_JSON).resolve()
    report_md = report_json.with_suffix(".md") if report_json.name != DEFAULT_REPORT_JSON.name else phase1_root / DEFAULT_REPORT_MD
    output_dir.mkdir(parents=True, exist_ok=True)
    report_json.parent.mkdir(parents=True, exist_ok=True)

    start = _parse_utc(start_text)
    end = _parse_utc(end_text) if end_text else datetime.now(timezone.utc)
    if end <= start:
        raise ValueError("end must be after start")

    rows_by_key: dict[tuple[str, str], list[dict[str, str]]] = {}
    source: dict[str, Any] = {
        "terminal_exe": str(terminal_exe),
        "mode": "read_only_history_copy_rates_range",
        "symbol_select_used": False,
        "chart_or_order_changes": False,
    }
    try:
        import MetaTrader5 as mt5  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - local bridge dependency
        raise RuntimeError(f"MetaTrader5 import failed: {type(exc).__name__}: {exc}") from exc

    if not terminal_exe.exists():
        raise FileNotFoundError(f"MT5 terminal not found: {terminal_exe}")

    if not mt5.initialize(path=str(terminal_exe)):  # pragma: no cover - local terminal dependency
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    try:  # pragma: no cover - exercised against the user's local terminal
        terminal_info = mt5.terminal_info()
        account = mt5.account_info()
        source.update(
            {
                "terminal_data_path": getattr(terminal_info, "data_path", ""),
                "account_login_masked": _mask(str(getattr(account, "login", ""))),
                "account_server": getattr(account, "server", ""),
            }
        )
        timeframe_map = _timeframe_map(mt5)
        for symbol in symbols:
            for timeframe in timeframes:
                if timeframe not in timeframe_map:
                    raise ValueError(f"Unsupported timeframe: {timeframe}")
                mt5_timeframe, seconds = timeframe_map[timeframe]
                rates = mt5.copy_rates_range(symbol, mt5_timeframe, start, end)
                rows = _rate_rows(rates, symbol=symbol, timeframe=timeframe, seconds=seconds, terminal_exe=terminal_exe)
                rows_by_key[(symbol, timeframe)] = rows
                _write_csv(output_dir / f"{symbol}_{timeframe}_20260601_to_latest.csv", rows, BAR_FIELDS)
    finally:
        mt5.shutdown()

    report_rows = [
        _continuity(symbol=symbol, timeframe=timeframe, rows=rows, requested_start=start, requested_end=end)
        for (symbol, timeframe), rows in rows_by_key.items()
    ]
    payload = {
        "status": "PASS" if report_rows and all(row["status"] != "FAIL_NO_ROWS" for row in report_rows) else "FAIL",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Read-only M5 replay-bar export for observer outcome scoring. It copies history rates only and does not "
            "touch MT5 charts, profiles, orders, positions, or EA settings."
        ),
        "requested_start_utc": start.strftime("%Y-%m-%d %H:%M:%S"),
        "requested_end_utc": end.strftime("%Y-%m-%d %H:%M:%S"),
        "output_dir": str(output_dir),
        "source": source,
        "timeframes": timeframes,
        "symbols": report_rows,
    }
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(_render_markdown(payload), encoding="utf-8")
    return report_json


def _timeframe_map(mt5: Any) -> dict[str, tuple[Any, int]]:
    return {
        "M5": (mt5.TIMEFRAME_M5, 300),
        "H1": (mt5.TIMEFRAME_H1, 3600),
        "H4": (mt5.TIMEFRAME_H4, 14400),
        "D1": (mt5.TIMEFRAME_D1, 86400),
    }


def _rate_rows(rates: Any, *, symbol: str, timeframe: str, seconds: int, terminal_exe: Path) -> list[dict[str, str]]:
    if rates is None:
        return []
    rows: list[dict[str, str]] = []
    for item in rates:
        start = datetime.fromtimestamp(int(item["time"]), tz=timezone.utc)
        end = datetime.fromtimestamp(int(item["time"]) + seconds, tz=timezone.utc)
        rows.append(
            {
                "bar_start_utc": start.strftime("%Y-%m-%d %H:%M:%S"),
                "bar_end_utc": end.strftime("%Y-%m-%d %H:%M:%S"),
                "open": _fmt(item["open"]),
                "high": _fmt(item["high"]),
                "low": _fmt(item["low"]),
                "close": _fmt(item["close"]),
                "tick_volume": str(int(item["tick_volume"])),
                "spread": str(int(item["spread"])),
                "real_volume": str(int(item["real_volume"])),
                "symbol": symbol,
                "timeframe": timeframe,
                "source_terminal": str(terminal_exe),
            }
        )
    return rows


def _continuity(
    *,
    symbol: str,
    timeframe: str = "M5",
    rows: list[dict[str, str]],
    requested_start: datetime,
    requested_end: datetime,
) -> dict[str, Any]:
    times = sorted(_parse_utc(row["bar_start_utc"]) for row in rows if row.get("bar_start_utc"))
    if not times:
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "status": "FAIL_NO_ROWS",
            "rows": 0,
            "first_bar_utc": "",
            "last_bar_utc": "",
            "requested_start_utc": requested_start.strftime("%Y-%m-%d %H:%M:%S"),
            "requested_end_utc": requested_end.strftime("%Y-%m-%d %H:%M:%S"),
            "gap_count_gt_5m": 0,
            "max_gap_minutes": "0.0",
            "duplicate_bar_times": 0,
            "continuity_pct_from_first_to_last": "0.00",
        }

    unique_times = sorted(set(times))
    duplicate_times = len(times) - len(unique_times)
    gap_count = 0
    max_gap_minutes = 0.0
    for left, right in zip(unique_times, unique_times[1:]):
        gap_minutes = (right - left).total_seconds() / 60.0
        if gap_minutes > 5.0:
            gap_count += 1
            max_gap_minutes = max(max_gap_minutes, gap_minutes)
    span_minutes = (unique_times[-1] - unique_times[0]).total_seconds() / 60.0
    expected_rows = int(span_minutes / 5.0) + 1 if span_minutes >= 0 else 0
    continuity_pct = (len(unique_times) / expected_rows * 100.0) if expected_rows else 0.0
    status = "PASS"
    if duplicate_times or gap_count:
        status = "WARN_GAPS_OR_DUPLICATES"
    if unique_times[0] > requested_start:
        status = "WARN_START_AFTER_REQUEST"
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "status": status,
        "rows": len(rows),
        "first_bar_utc": unique_times[0].strftime("%Y-%m-%d %H:%M:%S"),
        "last_bar_utc": unique_times[-1].strftime("%Y-%m-%d %H:%M:%S"),
        "requested_start_utc": requested_start.strftime("%Y-%m-%d %H:%M:%S"),
        "requested_end_utc": requested_end.strftime("%Y-%m-%d %H:%M:%S"),
        "gap_count_gt_5m": gap_count,
        "max_gap_minutes": f"{max_gap_minutes:.1f}",
        "duplicate_bar_times": duplicate_times,
        "continuity_pct_from_first_to_last": f"{continuity_pct:.2f}",
    }


def _parse_utc(value: str) -> datetime:
    text = str(value).strip().replace("T", " ").replace("Z", "")
    parsed = datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
    return parsed.replace(tzinfo=timezone.utc)


def _fmt(value: Any) -> str:
    return f"{float(value):.5f}".rstrip("0").rstrip(".")


def _mask(value: str) -> str:
    text = str(value or "")
    if len(text) <= 4:
        return "***"
    return f"{text[:2]}***{text[-2:]}"


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 2 M5 Replay Bar Export",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["authority"],
        "",
        f"Requested window UTC: `{payload['requested_start_utc']}` to `{payload['requested_end_utc']}`",
        f"Output dir: `{payload['output_dir']}`",
        "",
        "## Continuity",
        "",
        "| Symbol | Timeframe | Status | Rows | First bar UTC | Last bar UTC | Gaps >5m | Max gap min | Duplicates | Continuity % |",
        "| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["symbols"]:
        lines.append(
            f"| {row['symbol']} | {row['timeframe']} | {row['status']} | {row['rows']} | {row['first_bar_utc']} | "
            f"{row['last_bar_utc']} | {row['gap_count_gt_5m']} | {row['max_gap_minutes']} | "
            f"{row['duplicate_bar_times']} | {row['continuity_pct_from_first_to_last']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Read-only history export.",
            "- No chart attachments, order placement, position changes, profile changes, or EA setting changes.",
            "- Gaps are reported explicitly so partial exports cannot silently drive replay conclusions.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export read-only M5 bars for Phase 2 observer replay scoring.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--terminal-exe", type=Path, default=DEFAULT_TERMINAL_EXE)
    parser.add_argument("--symbols", nargs="+", default=DEFAULT_SYMBOLS)
    parser.add_argument("--timeframes", nargs="+", default=DEFAULT_TIMEFRAMES)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--report-json", type=Path, default=None)
    args = parser.parse_args()
    output = export_phase2_m5_replay_bars(
        args.phase1_root,
        terminal_exe=args.terminal_exe,
        symbols=args.symbols,
        timeframes=args.timeframes,
        start_text=args.start,
        end_text=args.end,
        output_dir=args.output_dir,
        report_json=args.report_json,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
