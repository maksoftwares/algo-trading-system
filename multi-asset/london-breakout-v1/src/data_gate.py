from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


TIMEFRAMES = ("H1", "M15", "M5")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def portable(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def raw_schema(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "execution_source_kind": "MISSING", "promotion_grade": False}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        header = next(csv.reader(handle))
    normalized = {column.strip().upper() for column in header}
    has_bid_ask = any("BID" in column for column in normalized) and any("ASK" in column for column in normalized)
    single_spread_bar = "<SPREAD>" in normalized and {"<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>"}.issubset(normalized)
    kind = "RAW_BID_ASK" if has_bid_ask else "BAR_OHLC_PLUS_SINGLE_SPREAD_FIELD" if single_spread_bar else "UNKNOWN_BAR_SCHEMA"
    return {
        "exists": True,
        "header": header,
        "execution_source_kind": kind,
        "promotion_grade": bool(has_bid_ask),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def discover_bar_files(repo_root: Path, config: dict[str, Any], symbol: str) -> dict[str, dict[str, Any]]:
    root = repo_root / config["raw_capital_com_root"]
    result: dict[str, dict[str, Any]] = {}
    for timeframe in TIMEFRAMES:
        matches = sorted(root.glob(f"{symbol}_{timeframe}_*_capital_com.csv"))
        if len(matches) == 1:
            result[timeframe] = {"path": portable(matches[0], repo_root), **raw_schema(matches[0])}
        else:
            result[timeframe] = {"exists": False, "match_count": len(matches), "execution_source_kind": "MISSING", "promotion_grade": False}
    return result


def tick_coverage_complete(first_tick_time_msc: int | None, required_start: datetime) -> bool:
    return first_tick_time_msc is not None and first_tick_time_msc <= int(required_start.timestamp() * 1000)


def capture_mt5_snapshot(config: dict[str, Any]) -> dict[str, Any]:
    import MetaTrader5 as mt5

    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialization failed: {mt5.last_error()}")
    try:
        account = mt5.account_info()
        terminal = mt5.terminal_info()
        if account is None or terminal is None or not terminal.connected:
            raise RuntimeError("Connected MT5 account/terminal metadata unavailable")
        requested_start = datetime.fromisoformat(config["requested_start"].replace("Z", "+00:00"))
        exam_start = datetime.fromisoformat(config["locked_exam_start"].replace("Z", "+00:00"))
        symbols: dict[str, Any] = {}
        account_units_per_usd: float | None = None
        xau_info = mt5.symbol_info("XAUUSD")
        if xau_info is not None:
            anchor = float(xau_info.ask)
            native = mt5.order_calc_profit(mt5.ORDER_TYPE_BUY, "XAUUSD", float(xau_info.volume_min), anchor, anchor + 1.0)
            if native is not None and native > 0:
                account_units_per_usd = float(native) / (float(xau_info.trade_contract_size) * float(xau_info.volume_min))
        for symbol in config["symbols"]:
            info = mt5.symbol_info(symbol)
            if info is None:
                symbols[symbol] = {"available": False}
                continue
            probes = {}
            for label, probe_time in (("full_period", requested_start), ("locked_exam", exam_start)):
                ticks = mt5.copy_ticks_from(symbol, probe_time, 1, mt5.COPY_TICKS_ALL)
                first = int(ticks[0]["time_msc"]) if ticks is not None and len(ticks) else None
                probes[label] = {
                    "requested_start": probe_time.isoformat(),
                    "returned_count": None if ticks is None else int(len(ticks)),
                    "first_tick_time_msc": first,
                    "first_tick_utc": datetime.fromtimestamp(first / 1000, tz=timezone.utc).isoformat() if first else None,
                    "coverage_starts_on_time": tick_coverage_complete(first, probe_time),
                    "last_error": list(mt5.last_error()),
                }
            anchor_price = float(info.ask)
            min_volume = float(info.volume_min)
            one_point_profit = mt5.order_calc_profit(mt5.ORDER_TYPE_BUY, symbol, min_volume, anchor_price, anchor_price + float(info.point))
            margin = mt5.order_calc_margin(mt5.ORDER_TYPE_BUY, symbol, min_volume, anchor_price)
            symbols[symbol] = {
                "available": True,
                "exact_symbol_name": str(info.name),
                "point": float(info.point), "digits": int(info.digits),
                "volume_min": min_volume, "volume_step": float(info.volume_step), "volume_max": float(info.volume_max),
                "contract_size": float(info.trade_contract_size),
                "currency_base": str(info.currency_base), "currency_profit": str(info.currency_profit), "currency_margin": str(info.currency_margin),
                "swap_mode": int(info.swap_mode), "swap_long": float(info.swap_long), "swap_short": float(info.swap_short),
                "swap_rollover3days": int(info.swap_rollover3days),
                "order_calc_anchor_price": anchor_price,
                "order_calc_profit_account_currency_one_point_min_volume": None if one_point_profit is None else float(one_point_profit),
                "order_calc_margin_account_currency_min_volume": None if margin is None else float(margin),
                "order_calc_margin_usd_min_volume": None if margin is None or not account_units_per_usd else float(margin) / account_units_per_usd,
                "tick_probes": probes,
                "zero_trade_action": True,
            }
        return {
            "schema_version": "capital_com_contract_tick_probe_v1",
            "captured_at_utc": datetime.now(timezone.utc).isoformat(),
            "server": str(account.server), "account_currency": str(account.currency), "account_leverage": int(account.leverage),
            "terminal_build": int(terminal.build), "account_units_per_usd": account_units_per_usd,
            "symbols": symbols, "zero_trade_action": True,
        }
    finally:
        mt5.shutdown()


def evaluate_data_gate(repo_root: Path, config: dict[str, Any], snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for symbol in config["symbols"]:
        bars = discover_bar_files(repo_root, config, symbol)
        contract = snapshot["symbols"].get(symbol, {"available": False})
        full_tick = contract.get("tick_probes", {}).get("full_period", {})
        all_bar_files = all(item["exists"] for item in bars.values())
        all_bars_promotion_grade = all(item["promotion_grade"] for item in bars.values())
        full_tick_complete = bool(full_tick.get("coverage_starts_on_time", False))
        trustworthy_complete = bool(contract.get("available") and all_bar_files and all_bars_promotion_grade and full_tick_complete)
        rows.append({
            "symbol": symbol,
            "exact_mt5_symbol": contract.get("exact_symbol_name"),
            "contract_available": bool(contract.get("available")),
            "h1_file_present": bars["H1"]["exists"], "m15_file_present": bars["M15"]["exists"], "m5_file_present": bars["M5"]["exists"],
            "repository_execution_source": bars["M5"]["execution_source_kind"],
            "repository_bid_ask_promotion_grade": all_bars_promotion_grade,
            "first_terminal_tick_utc": full_tick.get("first_tick_utc"),
            "full_period_terminal_ticks_complete": full_tick_complete,
            "complete_trustworthy_execution_data": trustworthy_complete,
            "contract_expressibility_status": "NOT_EVALUATED_DATA_GATE_STOP",
            "data_stop_reason": "FULL_PERIOD_RAW_BID_ASK_OR_TICK_DERIVED_M5_UNAVAILABLE" if not trustworthy_complete else "",
            "bar_files": bars,
        })
    return rows
