from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from foundation import AcquisitionRefused, ROOT


DEFAULT_FEATURE_CONFIG = ROOT / "config" / "futures_flow_feature_contract_v1.json"
DEFAULT_TRADE_FEATURE_CONFIG = ROOT / "config" / "futures_trade_feature_contract_v1.json"
TRADE_REQUIRED_COLUMNS = {
    "ts_event",
    "publisher_id",
    "instrument_id",
    "sequence",
    "side",
    "price",
    "size",
}
BOOK_REQUIRED_COLUMNS = {
    "bid_px_00",
    "ask_px_00",
    "bid_sz_00",
    "ask_sz_00",
}
EVENT_KEY = [
    "ts_event",
    "publisher_id",
    "instrument_id",
    "sequence",
    "side",
    "price",
    "size",
]


def load_feature_config(path: Path = DEFAULT_FEATURE_CONFIG) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_trade_feature_config(path: Path = DEFAULT_TRADE_FEATURE_CONFIG) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_tbbo_dbn(path: Path) -> pd.DataFrame:
    try:
        import databento as db
    except ImportError as exc:
        raise AcquisitionRefused("The databento package is required to decode DBN files.") from exc
    frame = db.DBNStore.from_file(path).to_df(
        price_type="float",
        pretty_ts=True,
        map_symbols=True,
        schema="tbbo",
    )
    if isinstance(frame, pd.DataFrame):
        return frame
    return pd.concat(frame, ignore_index=False)


def load_trades_dbn(path: Path) -> pd.DataFrame:
    try:
        import databento as db
    except ImportError as exc:
        raise AcquisitionRefused("The databento package is required to decode DBN files.") from exc
    frame = db.DBNStore.from_file(path).to_df(
        price_type="float",
        pretty_ts=True,
        map_symbols=True,
        schema="trades",
    )
    if isinstance(frame, pd.DataFrame):
        return frame
    return pd.concat(frame, ignore_index=False)


def normalize_trades(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    if "ts_event" not in normalized.columns and normalized.index.name == "ts_event":
        normalized = normalized.reset_index()
    missing = sorted(TRADE_REQUIRED_COLUMNS - set(normalized.columns))
    if missing:
        raise ValueError(f"Trade input is missing required columns: {missing}")

    normalized["ts_event"] = pd.to_datetime(normalized["ts_event"], utc=True)
    normalized["side"] = normalized["side"].astype(str).str.upper().str[0]
    if not normalized["side"].isin(["A", "B", "N"]).all():
        invalid = sorted(normalized.loc[~normalized["side"].isin(["A", "B", "N"]), "side"].unique())
        raise ValueError(f"Unsupported trade side values: {invalid}")

    numeric = ["publisher_id", "instrument_id", "sequence", "price", "size"]
    for column in numeric:
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    if (normalized["size"] <= 0).any():
        raise ValueError("Trade size must be positive.")
    if normalized.duplicated(EVENT_KEY).any():
        raise ValueError("Input contains duplicate trade events.")

    normalized = normalized.sort_values(
        ["ts_event", "publisher_id", "instrument_id", "sequence"], kind="stable"
    ).reset_index(drop=True)
    normalized["aggressor_sign"] = normalized["side"].map({"B": 1.0, "A": -1.0, "N": 0.0})
    normalized["buy_volume"] = np.where(normalized["aggressor_sign"] > 0, normalized["size"], 0.0)
    normalized["sell_volume"] = np.where(normalized["aggressor_sign"] < 0, normalized["size"], 0.0)
    normalized["unknown_volume"] = np.where(normalized["aggressor_sign"] == 0, normalized["size"], 0.0)
    normalized["signed_volume"] = normalized["size"] * normalized["aggressor_sign"]
    normalized["notional"] = normalized["price"] * normalized["size"]
    normalized["feature_time_utc"] = normalized["ts_event"].dt.floor("s") + pd.Timedelta(seconds=1)
    return normalized


def normalize_tbbo(frame: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(BOOK_REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"TBBO input is missing required book columns: {missing}")
    normalized = normalize_trades(frame)
    for column in BOOK_REQUIRED_COLUMNS:
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    if (normalized["bid_sz_00"] < 0).any() or (normalized["ask_sz_00"] < 0).any():
        raise ValueError("TBBO top-of-book sizes cannot be negative.")
    if (normalized["ask_px_00"] < normalized["bid_px_00"]).any():
        raise ValueError("TBBO input contains a crossed top of book.")
    return normalized


def aggregate_trade_seconds(events: pd.DataFrame, *, tick_size: float) -> pd.DataFrame:
    if tick_size <= 0:
        raise ValueError("tick_size must be positive.")
    frame = normalize_trades(events)
    grouped = frame.groupby(["instrument_id", "feature_time_utc"], sort=True, observed=True)
    seconds = grouped.agg(
        publisher_id=("publisher_id", "last"),
        event_time_last_utc=("ts_event", "last"),
        sequence_last=("sequence", "last"),
        trade_count=("size", "size"),
        contract_volume=("size", "sum"),
        buy_volume=("buy_volume", "sum"),
        sell_volume=("sell_volume", "sum"),
        unknown_volume=("unknown_volume", "sum"),
        signed_volume=("signed_volume", "sum"),
        notional=("notional", "sum"),
        trade_price_open=("price", "first"),
        trade_price_last=("price", "last"),
    ).reset_index()
    seconds["trade_vwap"] = seconds["notional"] / seconds["contract_volume"]
    seconds["mid_px"] = seconds["trade_price_last"]
    seconds["flow_imbalance_1s"] = seconds["signed_volume"] / seconds["contract_volume"]
    seconds["unknown_volume_share_1s"] = seconds["unknown_volume"] / seconds["contract_volume"]
    if "symbol" in frame.columns:
        symbols = grouped["symbol"].last().rename("symbol").reset_index()
        seconds = seconds.merge(symbols, on=["instrument_id", "feature_time_utc"], validate="one_to_one")
    return seconds.sort_values(["feature_time_utc", "instrument_id"], kind="stable").reset_index(drop=True)


def aggregate_tbbo_seconds(events: pd.DataFrame, *, tick_size: float) -> pd.DataFrame:
    if tick_size <= 0:
        raise ValueError("tick_size must be positive.")
    frame = normalize_tbbo(events)
    grouped = frame.groupby(["instrument_id", "feature_time_utc"], sort=True, observed=True)
    seconds = grouped.agg(
        publisher_id=("publisher_id", "last"),
        event_time_last_utc=("ts_event", "last"),
        sequence_last=("sequence", "last"),
        trade_count=("size", "size"),
        contract_volume=("size", "sum"),
        buy_volume=("buy_volume", "sum"),
        sell_volume=("sell_volume", "sum"),
        unknown_volume=("unknown_volume", "sum"),
        signed_volume=("signed_volume", "sum"),
        notional=("notional", "sum"),
        trade_price_open=("price", "first"),
        trade_price_last=("price", "last"),
        bid_px=("bid_px_00", "last"),
        ask_px=("ask_px_00", "last"),
        bid_size=("bid_sz_00", "last"),
        ask_size=("ask_sz_00", "last"),
    ).reset_index()
    seconds["trade_vwap"] = seconds["notional"] / seconds["contract_volume"]
    seconds["mid_px"] = (seconds["bid_px"] + seconds["ask_px"]) / 2.0
    seconds["spread_ticks"] = (seconds["ask_px"] - seconds["bid_px"]) / tick_size
    quote_total = seconds["bid_size"] + seconds["ask_size"]
    seconds["quote_imbalance"] = np.where(
        quote_total > 0,
        (seconds["bid_size"] - seconds["ask_size"]) / quote_total,
        0.0,
    )
    seconds["flow_imbalance_1s"] = seconds["signed_volume"] / seconds["contract_volume"]
    seconds["unknown_volume_share_1s"] = seconds["unknown_volume"] / seconds["contract_volume"]
    if "symbol" in frame.columns:
        symbols = grouped["symbol"].last().rename("symbol").reset_index()
        seconds = seconds.merge(symbols, on=["instrument_id", "feature_time_utc"], validate="one_to_one")
    return seconds.sort_values(["feature_time_utc", "instrument_id"], kind="stable").reset_index(drop=True)


def _price_at_or_before_horizon(group: pd.DataFrame, horizon_seconds: int) -> np.ndarray:
    times = group["feature_time_utc"].astype("int64").to_numpy()
    prices = group["mid_px"].to_numpy(dtype=float)
    targets = times - horizon_seconds * 1_000_000_000
    indices = np.searchsorted(times, targets, side="right") - 1
    baseline = np.full(len(group), np.nan, dtype=float)
    valid = indices >= 0
    baseline[valid] = prices[indices[valid]]
    return baseline


def add_flow_features(seconds: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    tick_size = float(config["tick_size"])
    required = {
        "instrument_id",
        "feature_time_utc",
        "contract_volume",
        "signed_volume",
        "trade_count",
        "mid_px",
    }
    missing = sorted(required - set(seconds.columns))
    if missing:
        raise ValueError(f"Second bars are missing required columns: {missing}")

    enriched_groups: list[pd.DataFrame] = []
    for _, raw_group in seconds.groupby("instrument_id", sort=False, observed=True):
        group = raw_group.sort_values("feature_time_utc", kind="stable").copy()
        group["feature_time_utc"] = pd.to_datetime(group["feature_time_utc"], utc=True)
        indexed = group.set_index("feature_time_utc")
        for horizon in config["feature_windows_seconds"]:
            window = f"{int(horizon)}s"
            volume = indexed["contract_volume"].rolling(window, closed="right").sum().to_numpy()
            signed = indexed["signed_volume"].rolling(window, closed="right").sum().to_numpy()
            count = indexed["trade_count"].rolling(window, closed="right").sum().to_numpy()
            group[f"contract_volume_{horizon}s"] = volume
            group[f"signed_volume_{horizon}s"] = signed
            group[f"trade_count_{horizon}s"] = count
            group[f"flow_imbalance_{horizon}s"] = np.divide(
                signed,
                volume,
                out=np.zeros_like(signed, dtype=float),
                where=volume > 0,
            )
            baseline = _price_at_or_before_horizon(group, int(horizon))
            group[f"price_impulse_ticks_{horizon}s"] = (group["mid_px"].to_numpy() - baseline) / tick_size
        first_time = group["feature_time_utc"].iloc[0]
        group["instrument_age_seconds"] = (
            group["feature_time_utc"] - first_time
        ).dt.total_seconds()
        enriched_groups.append(group)

    result = pd.concat(enriched_groups, ignore_index=True)
    result["volume_share_5s_of_60s"] = np.divide(
        result["contract_volume_5s"],
        result["contract_volume_60s"],
        out=np.zeros(len(result), dtype=float),
        where=result["contract_volume_60s"].to_numpy() > 0,
    )
    return result.sort_values(["feature_time_utc", "instrument_id"], kind="stable").reset_index(drop=True)


def _session_mask(frame: pd.DataFrame, session: Mapping[str, str]) -> pd.Series:
    local = frame["feature_time_utc"].dt.tz_convert(session["timezone"])
    minutes = local.dt.hour * 60 + local.dt.minute
    start_hour, start_minute = (int(part) for part in session["start"].split(":"))
    end_hour, end_minute = (int(part) for part in session["end"].split(":"))
    start = start_hour * 60 + start_minute
    end = end_hour * 60 + end_minute
    return (minutes >= start) & (minutes < end)


def _apply_cooldown(candidates: pd.DataFrame, cooldown_seconds: int) -> pd.DataFrame:
    if candidates.empty:
        return candidates
    accepted: list[int] = []
    last_time: dict[int, pd.Timestamp] = {}
    for index, row in candidates.sort_values("feature_time_utc", kind="stable").iterrows():
        instrument = int(row["instrument_id"])
        previous = last_time.get(instrument)
        if previous is None or (row["feature_time_utc"] - previous).total_seconds() >= cooldown_seconds:
            accepted.append(index)
            last_time[instrument] = row["feature_time_utc"]
    return candidates.loc[accepted]


def generate_candidates(features: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    frame = features.copy()
    frame["feature_time_utc"] = pd.to_datetime(frame["feature_time_utc"], utc=True)
    base = _session_mask(frame, config["session"])
    base &= frame["instrument_age_seconds"] >= config["instrument_warmup_seconds"]
    rules = config["candidate_rules"]
    candidates: list[pd.DataFrame] = []

    continuation = rules["flow_continuation"]
    flow_sign = np.sign(frame["flow_imbalance_5s"])
    continuation_mask = base.copy()
    continuation_mask &= frame["contract_volume_5s"] >= continuation["minimum_contract_volume_5s"]
    continuation_mask &= frame["flow_imbalance_5s"].abs() >= continuation["minimum_absolute_flow_imbalance_5s"]
    continuation_mask &= frame["flow_imbalance_30s"].abs() >= continuation["minimum_absolute_flow_imbalance_30s"]
    continuation_mask &= np.sign(frame["flow_imbalance_30s"]) == flow_sign
    continuation_mask &= frame["volume_share_5s_of_60s"] >= continuation["minimum_volume_share_5s_of_60s"]
    continuation_mask &= frame["price_impulse_ticks_5s"] * flow_sign >= continuation["minimum_directional_impulse_ticks_5s"]
    continuation_mask &= frame["quote_imbalance"] * flow_sign >= continuation["minimum_directional_quote_imbalance"]
    continuation_mask &= frame["spread_ticks"] <= continuation["maximum_spread_ticks"]
    selected = frame.loc[continuation_mask].copy()
    selected["family"] = "flow_continuation"
    selected["direction"] = np.where(selected["flow_imbalance_5s"] > 0, "LONG", "SHORT")
    candidates.append(_apply_cooldown(selected, int(continuation["cooldown_seconds"])))

    absorption = rules["absorption_reversal"]
    absorption_sign = np.sign(frame["flow_imbalance_5s"])
    absorption_mask = base.copy()
    absorption_mask &= frame["contract_volume_5s"] >= absorption["minimum_contract_volume_5s"]
    absorption_mask &= frame["flow_imbalance_5s"].abs() >= absorption["minimum_absolute_flow_imbalance_5s"]
    absorption_mask &= frame["volume_share_5s_of_60s"] >= absorption["minimum_volume_share_5s_of_60s"]
    absorption_mask &= frame["price_impulse_ticks_5s"].abs() <= absorption["maximum_absolute_impulse_ticks_5s"]
    absorption_mask &= frame["quote_imbalance"] * absorption_sign <= -absorption["minimum_opposing_quote_imbalance"]
    absorption_mask &= frame["spread_ticks"] <= absorption["maximum_spread_ticks"]
    selected = frame.loc[absorption_mask].copy()
    selected["family"] = "absorption_reversal"
    selected["direction"] = np.where(selected["flow_imbalance_5s"] < 0, "LONG", "SHORT")
    candidates.append(_apply_cooldown(selected, int(absorption["cooldown_seconds"])))

    result = pd.concat(candidates, ignore_index=True)
    if result.empty:
        return result
    columns = [
        "feature_time_utc",
        "instrument_id",
        "family",
        "direction",
        "contract_volume_5s",
        "flow_imbalance_5s",
        "flow_imbalance_30s",
        "volume_share_5s_of_60s",
        "price_impulse_ticks_5s",
        "quote_imbalance",
        "spread_ticks",
    ]
    return result[columns].sort_values(["feature_time_utc", "family"], kind="stable").reset_index(drop=True)


def generate_trade_candidates(features: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    frame = features.copy()
    frame["feature_time_utc"] = pd.to_datetime(frame["feature_time_utc"], utc=True)
    base = _session_mask(frame, config["session"])
    base &= frame["instrument_age_seconds"] >= config["instrument_warmup_seconds"]
    rules = config["candidate_rules"]
    candidates: list[pd.DataFrame] = []

    continuation = rules["flow_continuation"]
    flow_sign = np.sign(frame["flow_imbalance_5s"])
    continuation_mask = base.copy()
    continuation_mask &= frame["contract_volume_5s"] >= continuation["minimum_contract_volume_5s"]
    continuation_mask &= frame["flow_imbalance_5s"].abs() >= continuation["minimum_absolute_flow_imbalance_5s"]
    continuation_mask &= frame["flow_imbalance_30s"].abs() >= continuation["minimum_absolute_flow_imbalance_30s"]
    continuation_mask &= np.sign(frame["flow_imbalance_30s"]) == flow_sign
    continuation_mask &= frame["volume_share_5s_of_60s"] >= continuation["minimum_volume_share_5s_of_60s"]
    continuation_mask &= frame["price_impulse_ticks_5s"] * flow_sign >= continuation["minimum_directional_impulse_ticks_5s"]
    selected = frame.loc[continuation_mask].copy()
    selected["family"] = "flow_continuation"
    selected["direction"] = np.where(selected["flow_imbalance_5s"] > 0, "LONG", "SHORT")
    candidates.append(_apply_cooldown(selected, int(continuation["cooldown_seconds"])))

    absorption = rules["absorption_reversal"]
    absorption_mask = base.copy()
    absorption_mask &= frame["contract_volume_5s"] >= absorption["minimum_contract_volume_5s"]
    absorption_mask &= frame["flow_imbalance_5s"].abs() >= absorption["minimum_absolute_flow_imbalance_5s"]
    absorption_mask &= frame["volume_share_5s_of_60s"] >= absorption["minimum_volume_share_5s_of_60s"]
    absorption_mask &= frame["price_impulse_ticks_5s"].abs() <= absorption["maximum_absolute_impulse_ticks_5s"]
    selected = frame.loc[absorption_mask].copy()
    selected["family"] = "absorption_reversal"
    selected["direction"] = np.where(selected["flow_imbalance_5s"] < 0, "LONG", "SHORT")
    candidates.append(_apply_cooldown(selected, int(absorption["cooldown_seconds"])))

    result = pd.concat(candidates, ignore_index=True)
    if result.empty:
        return result
    columns = [
        "feature_time_utc",
        "instrument_id",
        "family",
        "direction",
        "contract_volume_5s",
        "flow_imbalance_5s",
        "flow_imbalance_30s",
        "volume_share_5s_of_60s",
        "price_impulse_ticks_5s",
    ]
    return result[columns].sort_values(["feature_time_utc", "family"], kind="stable").reset_index(drop=True)
