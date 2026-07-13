from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


TIMEFRAME_MINUTES = {"M5": 5, "M15": 15, "H1": 60, "H4": 240}
PRICE_COLUMNS = tuple(f"{side}_{field}" for side in ("mid", "bid", "ask") for field in ("open", "high", "low", "close"))
SPREAD_COLUMNS = ("spread_open_points", "spread_close_points", "spread_median_points", "spread_p95_points")


@dataclass(frozen=True)
class DataBundle:
    bars: dict[str, pd.DataFrame]
    coverage: dict[str, Any]
    source_manifest: dict[str, Any]
    contract: dict[str, Any]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _one_csv(directory: Path) -> Path:
    paths = sorted(directory.glob("*.csv"))
    if len(paths) != 1:
        raise FileNotFoundError(f"Expected exactly one CSV in {directory}, found {len(paths)}")
    return paths[0]


def _read_processed(path: Path) -> pd.DataFrame:
    usecols = [
        "timestamp_utc", "bar_start_utc", "bar_end_utc", "broker", "symbol", "timeframe",
        *PRICE_COLUMNS, *SPREAD_COLUMNS, "tick_count", "volume_sum",
    ]
    frame = pd.read_csv(path, usecols=usecols, low_memory=False)
    for column in ("timestamp_utc", "bar_start_utc", "bar_end_utc"):
        frame[column] = pd.to_datetime(frame[column], utc=True, errors="coerce")
    for column in (*PRICE_COLUMNS, *SPREAD_COLUMNS, "tick_count", "volume_sum"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["source_partition"] = "CAPITAL_COM_PROCESSED_2016_2025"
    return frame


def _month_boundaries(start: pd.Timestamp, end: pd.Timestamp) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    boundaries = list(pd.date_range(start, end, freq="MS", tz="UTC"))
    if not boundaries or boundaries[0] != start:
        boundaries.insert(0, start)
    if boundaries[-1] != end:
        boundaries.append(end)
    return list(zip(boundaries[:-1], boundaries[1:], strict=True))


def _acquire_mt5_tail(cache_dir: Path, symbol: str, start: pd.Timestamp, end: pd.Timestamp) -> tuple[dict[str, Path], dict[str, Any]]:
    import MetaTrader5 as mt5

    cache_dir.mkdir(parents=True, exist_ok=True)
    timeframe_ids = {"M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15, "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4}
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialization failed: {mt5.last_error()}")
    try:
        info = mt5.symbol_info(symbol)
        account = mt5.account_info()
        terminal = mt5.terminal_info()
        if info is None or account is None or terminal is None or not terminal.connected:
            raise RuntimeError("Connected MT5 symbol/account/terminal metadata is unavailable")
        point = float(info.point)
        paths: dict[str, Path] = {}
        for timeframe, mt5_id in timeframe_ids.items():
            path = cache_dir / f"{symbol}_{timeframe}_{start:%Y%m%d}_{end:%Y%m%d}_mt5.csv"
            paths[timeframe] = path
            if path.exists():
                continue
            pieces = []
            for left, right in _month_boundaries(start, end):
                rates = mt5.copy_rates_range(symbol, mt5_id, left.to_pydatetime(), right.to_pydatetime())
                if rates is None:
                    raise RuntimeError(f"CopyRates failed for {timeframe} {left}..{right}: {mt5.last_error()}")
                if len(rates):
                    pieces.append(pd.DataFrame(rates))
            if not pieces:
                raise RuntimeError(f"No MT5 rates returned for {timeframe}")
            raw = pd.concat(pieces, ignore_index=True).drop_duplicates("time", keep="last")
            raw["bar_start_utc"] = pd.to_datetime(raw["time"], unit="s", utc=True)
            raw = raw.loc[(raw["bar_start_utc"] >= start) & (raw["bar_start_utc"] < end)].copy()
            spread_price = raw["spread"].astype(float) * point
            output = pd.DataFrame({
                "bar_start_utc": raw["bar_start_utc"],
                "bar_end_utc": raw["bar_start_utc"] + pd.Timedelta(minutes=TIMEFRAME_MINUTES[timeframe]),
                "timestamp_utc": raw["bar_start_utc"] + pd.Timedelta(minutes=TIMEFRAME_MINUTES[timeframe]),
                "broker": "capital_com_mt5", "symbol": symbol, "timeframe": timeframe,
            })
            for field in ("open", "high", "low", "close"):
                output[f"bid_{field}"] = raw[field].astype(float).to_numpy()
                output[f"ask_{field}"] = raw[field].astype(float).to_numpy() + spread_price.to_numpy()
                output[f"mid_{field}"] = raw[field].astype(float).to_numpy() + 0.5 * spread_price.to_numpy()
            output["spread_open_points"] = raw["spread"].astype(float).to_numpy()
            output["spread_close_points"] = raw["spread"].astype(float).to_numpy()
            output["spread_median_points"] = raw["spread"].astype(float).to_numpy()
            output["spread_p95_points"] = raw["spread"].astype(float).to_numpy()
            output["tick_count"] = raw["tick_volume"].astype(float).to_numpy()
            output["volume_sum"] = raw["real_volume"].astype(float).to_numpy()
            output["source_partition"] = "CAPITAL_COM_MT5_LOCKED_TAIL_2025_2026"
            output.to_csv(path, index=False, lineterminator="\n")
        contract = {
            "captured_server": str(account.server), "captured_account_currency": str(account.currency),
            "captured_account_leverage": int(account.leverage), "terminal_build": int(terminal.build),
            "point": point, "digits": int(info.digits), "volume_min": float(info.volume_min),
            "volume_step": float(info.volume_step), "volume_max": float(info.volume_max),
            "contract_size": float(info.trade_contract_size), "tick_size": float(info.trade_tick_size),
            "swap_mode": int(info.swap_mode), "swap_long": float(info.swap_long), "swap_short": float(info.swap_short),
            "swap_rollover3days": int(info.swap_rollover3days),
            "bar_bid_ask_method": "MT5 BID OHLC PLUS NATIVE COPYRATES BAR SPREAD",
            "zero_trade_action": True,
        }
        minimum_volume = float(info.volume_min)
        anchor_price = float(info.ask)
        native_profit_one_usd_move = mt5.order_calc_profit(mt5.ORDER_TYPE_BUY, symbol, minimum_volume, anchor_price, anchor_price + 1.0)
        native_margin = mt5.order_calc_margin(mt5.ORDER_TYPE_BUY, symbol, minimum_volume, anchor_price)
        if native_profit_one_usd_move is None or native_margin is None or native_profit_one_usd_move <= 0:
            raise RuntimeError(f"OrderCalcProfit/OrderCalcMargin capture failed: {mt5.last_error()}")
        account_units_per_usd = float(native_profit_one_usd_move) / (float(info.trade_contract_size) * minimum_volume)
        margin_usd = float(native_margin) / account_units_per_usd
        contract.update({
            "order_calc_anchor_price": anchor_price,
            "order_calc_profit_account_currency_for_one_usd_move_min_volume": float(native_profit_one_usd_move),
            "order_calc_margin_account_currency_min_volume": float(native_margin),
            "account_units_per_usd": account_units_per_usd,
            "order_calc_margin_usd_min_volume": margin_usd,
            "order_calc_margin_rate": margin_usd / (anchor_price * float(info.trade_contract_size) * minimum_volume),
            "order_calc_capture_zero_trade_action": True,
        })
        return paths, contract
    finally:
        mt5.shutdown()


def _quality(frame: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    expected = pd.Timedelta(minutes=TIMEFRAME_MINUTES[timeframe])
    gaps = frame["bar_start_utc"].diff().dropna()
    invalid = (~np.isfinite(frame[list(PRICE_COLUMNS)]) | (frame[list(PRICE_COLUMNS)] <= 0)).any(axis=1)
    invalid |= frame[["timestamp_utc", "bar_start_utc", "bar_end_utc"]].isna().any(axis=1)
    invalid |= (frame["ask_open"] < frame["bid_open"]) | (frame["ask_close"] < frame["bid_close"])
    return {
        "rows": int(len(frame)), "start": frame["bar_start_utc"].min().isoformat(),
        "end_exclusive": frame["bar_end_utc"].max().isoformat(), "duplicate_starts": int(frame["bar_start_utc"].duplicated().sum()),
        "invalid_rows": int(invalid.sum()), "gaps_over_3_bars": int((gaps > expected * 3).sum()),
        "maximum_gap_hours": float(gaps.max().total_seconds() / 3600.0) if len(gaps) else 0.0,
        "source_partition_counts": frame["source_partition"].value_counts().sort_index().astype(int).to_dict(),
    }


def load_bundle(repo_root: Path, config: dict[str, Any]) -> DataBundle:
    start, end = pd.Timestamp(config["requested_start"]), pd.Timestamp(config["requested_end_exclusive"])
    tail_start = pd.Timestamp(config["mt5_tail_start"])
    historical_root = repo_root / config["historical_source_root"]
    cache_dir = repo_root / config["cache_dir"]
    tail_paths, _live_contract = _acquire_mt5_tail(cache_dir, config["symbol"], tail_start, end)
    contract_path = repo_root / config["contract_snapshot_path"]
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    bars: dict[str, pd.DataFrame] = {}
    sources: dict[str, Any] = {}
    for timeframe in TIMEFRAME_MINUTES:
        historical_path = _one_csv(historical_root / timeframe)
        historical = _read_processed(historical_path)
        historical = historical.loc[(historical["bar_start_utc"] >= start) & (historical["bar_start_utc"] < tail_start)]
        tail = _read_processed(tail_paths[timeframe])
        tail["source_partition"] = "CAPITAL_COM_MT5_LOCKED_TAIL_2025_2026"
        frame = pd.concat([historical, tail], ignore_index=True).sort_values("bar_start_utc", kind="mergesort")
        frame = frame.drop_duplicates("bar_start_utc", keep="last").reset_index(drop=True)
        frame = frame.loc[(frame["bar_start_utc"] >= start) & (frame["bar_start_utc"] < end)].reset_index(drop=True)
        development = frame.loc[frame["bar_start_utc"] < tail_start, "spread_open_points"].dropna()
        stress_p95 = float(development.quantile(0.95))
        frame["stress_spread_points"] = stress_p95
        frame["data_valid"] = np.isfinite(frame[list(PRICE_COLUMNS)]).all(axis=1) & (frame[list(PRICE_COLUMNS)] > 0).all(axis=1)
        frame["data_valid"] &= frame[["timestamp_utc", "bar_start_utc", "bar_end_utc"]].notna().all(axis=1)
        frame["data_valid"] &= (frame["ask_open"] >= frame["bid_open"]) & (frame["ask_close"] >= frame["bid_close"])
        bars[timeframe] = frame
        sources[timeframe] = {
            "historical": {"path": historical_path.relative_to(repo_root).as_posix(), "sha256": sha256_file(historical_path)},
            "locked_tail": {"path": tail_paths[timeframe].relative_to(repo_root).as_posix(), "sha256": sha256_file(tail_paths[timeframe])},
            "development_spread_p95_points": stress_p95,
        }
    quality = {timeframe: _quality(frame, timeframe) for timeframe, frame in bars.items()}
    sources["contract_snapshot"] = {
        "path": contract_path.relative_to(repo_root).as_posix(),
        "sha256": sha256_file(contract_path),
        "capture_method": "READ_ONLY_ORDERCALCPROFIT_AND_ORDERCALCMARGIN_ZERO_TRADE_ACTION",
    }
    complete = all(
        pd.Timestamp(item["start"]) <= start and pd.Timestamp(item["end_exclusive"]) >= end
        and item["duplicate_starts"] == 0 and item["invalid_rows"] == 0
        for item in quality.values()
    )
    coverage = {
        "requested_start": start.isoformat(), "requested_end_exclusive": end.isoformat(),
        "segment_d_start": tail_start.isoformat(), "segment_d_complete": bool(complete),
        "status": "COMPLETE_EXACT_PERIOD" if complete else "MULTIREGIME_V1_DATA_INCOMPLETE_NO_ADVANCEMENT",
        "timeframes": quality,
        "source_boundary": "processed Capital.com before 2025-07-01; same-broker Capital.com MT5 at and after 2025-07-01",
    }
    return DataBundle(bars=bars, coverage=coverage, source_manifest=sources, contract=contract)
