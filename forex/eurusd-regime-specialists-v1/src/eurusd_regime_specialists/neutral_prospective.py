from __future__ import annotations

import hashlib
import json
import lzma
import struct
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config
from .neutral_tick_microstructure import (
    build_microstructure_dataset,
    load_tick_microstructure,
)
from .neutral_tick_volatility import VOLATILITY_MODEL_FEATURES
from .neutral_walkforward import (
    choose_side,
    fit_predict,
    purged_training_rows,
    route_outcomes,
)
from .research import (
    PACKAGE_ROOT,
    PIP,
    active_weekday_fx_days,
    aggregate_fx_h1,
    build_state_table,
    load_context_h1,
    load_fx_m5,
    serialize,
    sha256_file,
)


SYMBOL_SCALE = {
    "EURUSD": 100_000.0,
    "GBPUSD": 100_000.0,
    "USDJPY": 1_000.0,
}


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_prospective_july.json"
        ).read_text(encoding="utf-8")
    )


def load_parent_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_tick_volatility.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_PROSPECTIVE_JULY_PREREG_2026_07_27.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if lock.get("locked_before_july_fx_tick_acquisition") is not True:
        raise RuntimeError("Prospective July contract is not locked")
    checked = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Prospective July preregistration mismatch: {relative}"
            )
        checked[relative] = actual
    return checked


def dukascopy_url(symbol: str, hour: pd.Timestamp) -> str:
    return (
        f"https://datafeed.dukascopy.com/datafeed/{symbol}/"
        f"{hour.year:04d}/{hour.month - 1:02d}/{hour.day:02d}/"
        f"{hour.hour:02d}h_ticks.bi5"
    )


def decode_bi5_payload(
    compressed: bytes, hour: pd.Timestamp, symbol: str
) -> pd.DataFrame:
    columns = [
        "timestamp_utc",
        "bid",
        "ask",
        "bid_volume",
        "ask_volume",
    ]
    if not compressed:
        return pd.DataFrame(columns=columns)
    raw = lzma.decompress(compressed)
    if len(raw) % 20:
        raise ValueError(
            f"Malformed {symbol} bi5 payload: {len(raw)} bytes"
        )
    count = len(raw) // 20
    if not count:
        return pd.DataFrame(columns=columns)
    scale = SYMBOL_SCALE[symbol]
    base = (
        hour.tz_convert("UTC")
        if hour.tzinfo is not None
        else hour.tz_localize("UTC")
    )
    timestamps = np.empty(count, dtype="datetime64[ms]")
    asks = np.empty(count, dtype=float)
    bids = np.empty(count, dtype=float)
    ask_volumes = np.empty(count, dtype=float)
    bid_volumes = np.empty(count, dtype=float)
    base_ms = int(base.timestamp() * 1000)
    for index, offset in enumerate(range(0, len(raw), 20)):
        ms, ask, bid, ask_volume, bid_volume = struct.unpack(
            ">IIIff", raw[offset : offset + 20]
        )
        timestamps[index] = np.datetime64(base_ms + int(ms), "ms")
        asks[index] = ask / scale
        bids[index] = bid / scale
        ask_volumes[index] = ask_volume
        bid_volumes[index] = bid_volume
    frame = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(timestamps, utc=True),
            "bid": bids,
            "ask": asks,
            "bid_volume": bid_volumes,
            "ask_volume": ask_volumes,
        }
    )
    valid = (
        (frame["bid"] > 0)
        & (frame["ask"] > 0)
        & (frame["ask"] >= frame["bid"])
    )
    if not valid.all():
        raise ValueError(f"Invalid decoded {symbol} bid/ask tick")
    return frame


def _download_one(
    symbol: str,
    hour: pd.Timestamp,
    cache_root: Path,
    retries: int = 4,
) -> tuple[str, pd.Timestamp, Path]:
    symbol_root = cache_root / symbol
    symbol_root.mkdir(parents=True, exist_ok=True)
    path = symbol_root / f"{hour.strftime('%Y%m%d%H')}.bi5"
    if path.exists():
        return symbol, hour, path
    request = urllib.request.Request(
        dukascopy_url(symbol, hour),
        headers={"User-Agent": "eurusd-neutral-prospective/1.0"},
    )
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(
                request, timeout=30
            ) as response:
                data = response.read()
            if data:
                lzma.decompress(data)
            path.write_bytes(data)
            return symbol, hour, path
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                path.write_bytes(b"")
                return symbol, hour, path
            last_error = exc
        except Exception as exc:
            last_error = exc
        time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(
        f"Failed to download {dukascopy_url(symbol, hour)}: {last_error}"
    )


def acquire_ticks(
    cfg: dict[str, Any],
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    start = pd.Timestamp(cfg["source"]["download_start_utc"])
    end = pd.Timestamp(cfg["source"]["download_end_utc"])
    hours = pd.date_range(start.floor("h"), end.floor("h"), freq="h")
    cache_root = (
        PACKAGE_ROOT
        / "outputs"
        / "neutral_prospective_july"
        / "raw_bi5"
    )
    jobs = [
        (symbol, hour)
        for symbol in cfg["source"]["symbols"]
        for hour in hours
    ]
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(
                _download_one, symbol, hour, cache_root
            )
            for symbol, hour in jobs
        ]
        for future in as_completed(futures):
            future.result()
    frames: dict[str, pd.DataFrame] = {}
    manifests: dict[str, Any] = {}
    for symbol in cfg["source"]["symbols"]:
        digest = hashlib.sha256()
        parts = []
        nonempty = 0
        ticks = 0
        for hour in hours:
            path = (
                cache_root
                / symbol
                / f"{hour.strftime('%Y%m%d%H')}.bi5"
            )
            data = path.read_bytes()
            digest.update(path.name.encode("utf-8"))
            digest.update(hashlib.sha256(data).digest())
            if not data:
                continue
            decoded = decode_bi5_payload(data, hour, symbol)
            if decoded.empty:
                continue
            nonempty += 1
            ticks += len(decoded)
            parts.append(decoded)
        frame = (
            pd.concat(parts, ignore_index=True)
            .drop_duplicates("timestamp_utc", keep="last")
            .sort_values("timestamp_utc")
        )
        frames[symbol] = frame
        manifests[symbol] = {
            "source": "Dukascopy public datafeed .bi5",
            "hours_requested": int(len(hours)),
            "nonempty_hours": nonempty,
            "ticks": ticks,
            "first_tick_utc": frame["timestamp_utc"].min().isoformat(),
            "last_tick_utc": frame["timestamp_utc"].max().isoformat(),
            "source_chain_sha256": digest.hexdigest(),
        }
    return frames, manifests


def ticks_to_m5(ticks: pd.DataFrame) -> pd.DataFrame:
    indexed = ticks.set_index("timestamp_utc").sort_index()
    bars = indexed.resample("5min", label="left", closed="left").agg(
        bid_open=("bid", "first"),
        bid_high=("bid", "max"),
        bid_low=("bid", "min"),
        bid_close=("bid", "last"),
        ask_open=("ask", "first"),
        ask_high=("ask", "max"),
        ask_low=("ask", "min"),
        ask_close=("ask", "last"),
        tick_count=("bid", "size"),
    )
    bars = bars.dropna()
    bars["timestamp_ms"] = (
        bars.index.astype("int64") // 1_000_000
    )
    return bars[
        [
            "timestamp_ms",
            "bid_open",
            "bid_high",
            "bid_low",
            "bid_close",
            "ask_open",
            "ask_high",
            "ask_low",
            "ask_close",
            "tick_count",
        ]
    ]


def ticks_to_microstructure(
    ticks: pd.DataFrame, parent_cfg: dict[str, Any]
) -> pd.DataFrame:
    rows = []
    late_ms = (
        int(parent_cfg["features"]["late_bar_seconds"]) * 1000
    )
    frame = ticks.sort_values("timestamp_utc").copy()
    frame["bucket"] = frame["timestamp_utc"].dt.floor("5min")
    for bucket, group in frame.groupby("bucket", sort=True):
        bid = group["bid"].to_numpy(dtype=float)
        ask = group["ask"].to_numpy(dtype=float)
        mid = (bid + ask) / 2.0
        changes = np.diff(mid) / PIP
        up = int((changes > 0).sum())
        down = int((changes < 0).sum())
        directional = up + down
        absolute_path = float(np.abs(changes).sum())
        spread = (ask - bid) / PIP
        bid_volume = group["bid_volume"].to_numpy(dtype=float)
        ask_volume = group["ask_volume"].to_numpy(dtype=float)
        volume_total = float(bid_volume.sum() + ask_volume.sum())
        timestamps_ms = (
            group["timestamp_utc"].astype("int64").to_numpy()
            // 1_000_000
        )
        bucket_ms = int(bucket.timestamp() * 1000)
        late_start = bucket_ms + 300_000 - late_ms
        late_offset = int(
            np.searchsorted(timestamps_ms, late_start, side="left")
        )
        late_mid = mid[min(late_offset, len(mid) - 1)]
        rows.append(
            {
                "timestamp_utc": bucket,
                "timestamp_ms": bucket_ms,
                "tick_count_raw": int(len(group)),
                "quote_change_imbalance": (
                    (up - down) / directional
                    if directional
                    else 0.0
                ),
                "path_efficiency": (
                    float((mid[-1] - mid[0]) / PIP)
                    / absolute_path
                    if absolute_path > 0
                    else 0.0
                ),
                "late_return_pips": float(
                    (mid[-1] - late_mid) / PIP
                ),
                "volume_imbalance": (
                    float(bid_volume.sum() - ask_volume.sum())
                    / volume_total
                    if volume_total > 0
                    else 0.0
                ),
                "spread_mean_pips": float(spread.mean()),
                "spread_std_pips": float(spread.std()),
                "spread_max_pips": float(spread.max()),
                "spread_last_pips": float(spread[-1]),
                "realized_variance_pips2": float(
                    np.square(changes).sum()
                ),
                "late_tick_share": float(
                    max(len(mid) - late_offset, 0) / len(mid)
                ),
            }
        )
    return pd.DataFrame(rows).set_index("timestamp_utc")


def _combined_inputs(
    ticks: dict[str, pd.DataFrame],
    cfg: dict[str, Any],
    parent_cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    base = load_ensemble_config()
    history_start = pd.Timestamp(base["data"]["start_utc"])
    history_end = pd.Timestamp(base["data"]["end_utc"])
    prospective_end = pd.Timestamp(cfg["source"]["download_end_utc"])
    bar_root = Path(base["data"]["fx_bar_root"])
    combined_m5 = {}
    for symbol in ("EURUSD", "GBPUSD", "USDJPY"):
        history = load_fx_m5(
            bar_root, symbol, history_start, history_end
        )
        prospective = ticks_to_m5(ticks[symbol])
        combined_m5[symbol] = (
            pd.concat([history, prospective])
            .loc[lambda frame: ~frame.index.duplicated(keep="last")]
            .sort_index()
        )
    raw_root = Path(base["data"]["dukascopy_raw_root"])
    context_cache = (
        PACKAGE_ROOT
        / "outputs"
        / "neutral_prospective_july"
        / "context_cache"
    )
    dxy, dxy_manifest = load_context_h1(
        raw_root,
        "DOLLARIDXUSD",
        history_start,
        prospective_end,
        context_cache,
    )
    bond, bond_manifest = load_context_h1(
        raw_root,
        "USTBONDTRUSD",
        history_start,
        prospective_end,
        context_cache,
    )
    fx_h1 = {
        symbol: aggregate_fx_h1(frame)
        for symbol, frame in combined_m5.items()
    }
    state = build_state_table(
        dxy, bond, fx_h1, base["classifier"]
    )
    historical_micro, historical_manifest = load_tick_microstructure(
        raw_root, history_start, history_end, parent_cfg
    )
    prospective_micro = ticks_to_microstructure(
        ticks["EURUSD"], parent_cfg
    )
    micro = (
        pd.concat([historical_micro, prospective_micro])
        .loc[lambda frame: ~frame.index.duplicated(keep="last")]
        .sort_index()
    )
    rolling = int(parent_cfg["features"]["microstructure_rolling_bars"])
    micro["three_bar_quote_change_imbalance"] = (
        micro["quote_change_imbalance"]
        .rolling(rolling, min_periods=rolling)
        .mean()
    )
    median_bars = int(parent_cfg["features"]["tick_median_bars"])
    micro["tick_count_ratio_24"] = (
        micro["tick_count_raw"]
        / micro["tick_count_raw"]
        .shift(1)
        .rolling(median_bars, min_periods=median_bars)
        .median()
        .replace(0, np.nan)
    )
    manifests = {
        "DXY": dxy_manifest,
        "BOND": bond_manifest,
        "HISTORICAL_EURUSD_TICKS": historical_manifest,
    }
    return combined_m5["EURUSD"], state, micro, manifests


def run_prospective_july() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    cfg = load_config()
    parent_cfg = load_parent_config()
    ticks, download_manifests = acquire_ticks(cfg)
    eurusd, state, micro, context_manifests = _combined_inputs(
        ticks, cfg, parent_cfg
    )
    dataset = build_microstructure_dataset(
        eurusd, state, micro, parent_cfg
    )
    cutoff = pd.Timestamp(cfg["inference"]["start_utc"])
    inference_end = pd.Timestamp(cfg["inference"]["end_utc"])
    training = purged_training_rows(dataset, cutoff)
    inference = dataset[
        (dataset["entry_time_utc"] >= cutoff)
        & (dataset["entry_time_utc"] <= inference_end)
    ].copy()
    probabilities, coefficients = fit_predict(
        training,
        inference,
        parent_cfg,
        VOLATILITY_MODEL_FEATURES,
    )
    inference["predicted_probability"] = probabilities
    selected = choose_side(
        inference, float(cfg["selected_probability_threshold"])
    )
    trades = route_outcomes(selected, parent_cfg)
    metrics = payoff_metrics(trades)
    metrics["fixed_0p01_lot_usd"] = (
        float(trades["fixed_0p01_lot_usd"].sum())
        if not trades.empty
        else 0.0
    )
    active_days = active_weekday_fx_days(
        eurusd, cutoff, inference_end
    )
    metrics["trades_per_weekday"] = (
        len(trades) / active_days if active_days else 0.0
    )
    calendar_days = (
        inference_end.date() - cutoff.date()
    ).days + 1
    gate = cfg["interpretation_gate"]
    sample_complete = (
        len(trades) >= int(gate["minimum_completed_trades"])
        and calendar_days >= int(gate["minimum_calendar_days"])
    )
    metric_pass = (
        metrics["profit_factor"] >= float(gate["minimum_profit_factor"])
        and float(gate["minimum_win_rate"])
        <= metrics["win_rate"]
        <= float(gate["maximum_win_rate"])
        and float(gate["minimum_realized_payoff_ratio"])
        <= metrics["realized_payoff_ratio"]
        <= float(gate["maximum_realized_payoff_ratio"])
        and metrics["expectancy_r"]
        > float(gate["minimum_expectancy_r"])
    )
    status = (
        "PROSPECTIVE_GATE_PASS_REQUIRES_GOVERNANCE_REVIEW"
        if sample_complete and metric_pass
        else (
            gate["minimum_status_if_sample_gate_fails"]
            if not sample_complete
            else "PROSPECTIVE_GATE_FAILED"
        )
    )
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": status,
        "research_only": True,
        "broker_action_allowed": False,
        "parent_model_status": cfg["model_status_before_prospective_run"],
        "no_retuning": {
            "threshold": cfg["selected_probability_threshold"],
            "model_specification": cfg["parent_model_contract"],
            "training_label_exit_cutoff_utc": cutoff.isoformat(),
            "parameters_changed_after_july_acquisition": False,
        },
        "coverage": {
            "download_start_utc": cfg["source"]["download_start_utc"],
            "download_end_utc": cfg["source"]["download_end_utc"],
            "inference_start_utc": cfg["inference"]["start_utc"],
            "inference_end_utc": cfg["inference"]["end_utc"],
            "calendar_days": calendar_days,
            "active_weekdays": active_days,
            "training_rows": int(len(training)),
            "inference_rows": int(len(inference)),
        },
        "download_manifests": download_manifests,
        "context_manifests": context_manifests,
        "prospective_metrics": metrics,
        "sample_gate": {
            "passed": sample_complete,
            "minimum_completed_trades": gate[
                "minimum_completed_trades"
            ],
            "minimum_calendar_days": gate["minimum_calendar_days"],
        },
        "metric_gate": {
            "passed": metric_pass,
            "evaluated_but_nonpromotional_when_sample_incomplete": True,
        },
        "verdict": (
            "The frozen prospective sample is still accumulating and cannot "
            "admit or rescue the historically rejected Neutral model."
            if not sample_complete
            else (
                "The prospective metric gate passed, subject to governance."
                if metric_pass
                else "The prospective metric gate failed."
            )
        ),
    }
    artifacts = {
        "TRADES": trades,
        "SELECTED_PREDICTIONS": selected,
        "MODEL_FEATURE_DIAGNOSTIC": coefficients,
        "EURUSD_M5": ticks_to_m5(ticks["EURUSD"]).reset_index(),
        "GBPUSD_M5": ticks_to_m5(ticks["GBPUSD"]).reset_index(),
        "USDJPY_M5": ticks_to_m5(ticks["USDJPY"]).reset_index(),
    }
    return result, artifacts


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize(payload), indent=2), encoding="utf-8"
    )
