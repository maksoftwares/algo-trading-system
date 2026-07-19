from __future__ import annotations

import hashlib
import importlib.util
import json
import lzma
from pathlib import Path
import struct
import time
from types import ModuleType
from typing import Any
import urllib.error
import urllib.request

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]


def load_config(root: Path = ROOT) -> dict[str, Any]:
    path = root / "config" / "capital_dukas_lagged_economic_test_v23.json"
    return json.loads(path.read_text(encoding="utf-8"))


def resolve(root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(payload: dict[str, Any], omitted_key: str) -> str:
    work = dict(payload)
    work.pop(omitted_key, None)
    encoded = json.dumps(
        work, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def path_record(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    try:
        shown = resolved.relative_to(REPO.resolve()).as_posix()
    except ValueError:
        shown = str(resolved)
    return {
        "path": shown,
        "bytes": int(path.stat().st_size),
        "sha256": sha256_file(path),
    }


def artifact_record(path: Path) -> dict[str, Any]:
    return {
        "path": path.resolve().relative_to(REPO.resolve()).as_posix(),
        "bytes": int(path.stat().st_size),
        "sha256": sha256_file(path),
    }


def load_locked_module(
    root: Path, raw_path: str, expected_sha256: str, module_name: str
) -> ModuleType:
    path = resolve(root, raw_path)
    if sha256_file(path) != expected_sha256:
        raise ValueError(f"V23 locked module changed: {path}")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_locked_inputs(config: dict[str, Any], root: Path = ROOT) -> None:
    development = config["development"]
    modules = config["locked_modules"]
    checks = (
        (development["paired_quotes"], development["paired_quotes_sha256"]),
        (development["opportunities"], development["opportunities_sha256"]),
        (modules["foundation_module"], modules["foundation_module_sha256"]),
        (modules["opportunity_module"], modules["opportunity_module_sha256"]),
        (
            modules["opportunity_contract"],
            modules["opportunity_contract_file_sha256"],
        ),
    )
    for raw_path, expected_hash in checks:
        path = resolve(root, str(raw_path))
        if not path.is_file():
            raise FileNotFoundError(path)
        if sha256_file(path) != str(expected_hash):
            raise ValueError(f"V23 locked input changed: {path}")


def confirmation_window(config: dict[str, Any]) -> tuple[pd.Timestamp, pd.Timestamp]:
    confirmation = config["confirmation"]
    return (
        pd.Timestamp(confirmation["start_inclusive_utc"]),
        pd.Timestamp(confirmation["end_exclusive_utc"]),
    )


def expected_capital_paths(config: dict[str, Any]) -> list[Path]:
    start, end = confirmation_window(config)
    confirmation = config["confirmation"]
    dates = pd.date_range(start.normalize(), end - pd.Timedelta(days=1), freq="D")
    directory = Path(confirmation["capital_directory"])
    prefix = str(confirmation["capital_filename_prefix"])
    return [directory / f"{prefix}{date:%Y%m%d}.csv" for date in dates]


def expected_dukascopy_hours(config: dict[str, Any]) -> list[pd.Timestamp]:
    start, end = confirmation_window(config)
    return list(
        pd.date_range(start.floor("h"), end - pd.Timedelta(hours=1), freq="h")
    )


def dukascopy_path(config: dict[str, Any], hour: pd.Timestamp) -> Path:
    root = Path(config["confirmation"]["dukascopy_directory"])
    return (
        root
        / f"year={hour.year:04d}"
        / f"month={hour.month:02d}"
        / f"{hour:%Y%m%d%H}.json"
    )


def build_capital_manifest(config: dict[str, Any]) -> dict[str, Any]:
    paths = expected_capital_paths(config)
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"V23 Capital confirmation files missing: {missing}")
    required_header = {
        "tick_time_msc",
        "seconds_since_tick",
        "tick_fresh",
        "account",
        "server",
        "symbol",
        "bid",
        "ask",
    }
    for path in paths:
        columns = set(pd.read_csv(path, nrows=0).columns)
        if not required_header.issubset(columns):
            raise ValueError(f"V23 Capital source schema changed: {path}")
    payload: dict[str, Any] = {
        "schema_version": "xauusd_v23_capital_source_manifest",
        "window": {
            "start_inclusive_utc": config["confirmation"]["start_inclusive_utc"],
            "end_exclusive_utc": config["confirmation"]["end_exclusive_utc"],
        },
        "capital_files": [path_record(path) for path in paths],
        "capital_file_count": len(paths),
    }
    payload["manifest_sha256"] = canonical_hash(payload, "manifest_sha256")
    return payload


def verify_file_manifest(
    manifest: dict[str, Any], section: str, self_hash_key: str = "manifest_sha256"
) -> None:
    if canonical_hash(manifest, self_hash_key) != manifest[self_hash_key]:
        raise ValueError("V23 source manifest self-hash mismatch")
    for record in manifest[section]:
        path = Path(record["path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        if int(record["bytes"]) != path.stat().st_size:
            raise ValueError(f"V23 source size changed: {path}")
        if sha256_file(path) != record["sha256"]:
            raise ValueError(f"V23 source hash changed: {path}")


def dukascopy_url(config: dict[str, Any], hour: pd.Timestamp) -> str:
    template = str(config["confirmation"]["free_url_template"])
    return template.format(
        year=f"{hour.year:04d}",
        zero_based_month=f"{hour.month - 1:02d}",
        day=f"{hour.day:02d}",
        hour=f"{hour.hour:02d}",
    )


def decode_bi5_hour(
    compressed: bytes, hour: pd.Timestamp, price_divisor: int
) -> dict[str, Any]:
    hour_ms = int(hour.value // 1_000_000)
    empty = {
        "timestamp": hour_ms,
        "multiplier": 1.0 / float(price_divisor),
        "ask": None,
        "bid": None,
        "times": [],
        "asks": [],
        "bids": [],
        "askVolumes": [],
        "bidVolumes": [],
    }
    if not compressed:
        return empty
    raw = lzma.decompress(compressed)
    if not raw:
        return empty
    if len(raw) % 20:
        raise ValueError("V23 Dukascopy BI5 payload length is not divisible by 20")
    records = list(struct.iter_unpack(">IIIff", raw))
    offsets = np.asarray([record[0] for record in records], dtype=np.int64)
    asks_raw = np.asarray([record[1] for record in records], dtype=np.int64)
    bids_raw = np.asarray([record[2] for record in records], dtype=np.int64)
    ask_volumes = [float(record[3]) for record in records]
    bid_volumes = [float(record[4]) for record in records]
    if np.any(np.diff(offsets) < 0) or offsets[0] < 0 or offsets[-1] >= 3_600_000:
        raise ValueError("V23 Dukascopy tick offsets escape their hour")
    if np.any(asks_raw <= 0) or np.any(bids_raw <= 0) or np.any(asks_raw < bids_raw):
        raise ValueError("V23 Dukascopy BI5 quote is invalid")
    times = np.diff(np.concatenate(([0], offsets))).astype(int).tolist()
    asks = np.diff(np.concatenate(([asks_raw[0]], asks_raw))).astype(int).tolist()
    bids = np.diff(np.concatenate(([bids_raw[0]], bids_raw))).astype(int).tolist()
    return {
        "timestamp": hour_ms,
        "multiplier": 1.0 / float(price_divisor),
        "ask": float(asks_raw[0] / price_divisor),
        "bid": float(bids_raw[0] / price_divisor),
        "times": times,
        "asks": asks,
        "bids": bids,
        "askVolumes": ask_volumes,
        "bidVolumes": bid_volumes,
    }


def _download_bytes(url: str, retries: int = 5) -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": "xauusd-research-v23/1.0"}
    )
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return b""
            last_error = exc
        except Exception as exc:  # pragma: no cover - network failures vary.
            last_error = exc
        time.sleep(float(attempt + 1))
    raise RuntimeError(f"V23 Dukascopy download failed for {url}: {last_error}")


def acquire_dukascopy_confirmation(config: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    divisor = int(config["confirmation"]["dukascopy_price_divisor"])
    for hour in expected_dukascopy_hours(config):
        path = dukascopy_path(config, hour)
        url = dukascopy_url(config, hour)
        if path.is_file():
            payload = json.loads(path.read_text(encoding="utf-8"))
        else:
            compressed = _download_bytes(url)
            payload = decode_bi5_hour(compressed, hour, divisor)
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".json.part")
            temporary.write_text(
                json.dumps(payload, separators=(",", ":"), allow_nan=False),
                encoding="utf-8",
            )
            temporary.replace(path)
            time.sleep(0.03)
        record = path_record(path)
        record.update(
            {
                "hour_utc": hour.isoformat(),
                "url": url,
                "tick_count": int(len(payload["times"])),
                "empty_hour": not bool(payload["times"]),
            }
        )
        records.append(record)
    manifest: dict[str, Any] = {
        "schema_version": "xauusd_v23_dukascopy_source_manifest",
        "source": "FREE_PUBLIC_DUKASCOPY_DATAFEED",
        "paid_source_used": False,
        "window": {
            "start_inclusive_utc": config["confirmation"]["start_inclusive_utc"],
            "end_exclusive_utc": config["confirmation"]["end_exclusive_utc"],
        },
        "dukascopy_files": records,
        "dukascopy_file_count": len(records),
        "nonempty_hour_count": int(sum(not row["empty_hour"] for row in records)),
        "tick_count": int(sum(row["tick_count"] for row in records)),
    }
    manifest["manifest_sha256"] = canonical_hash(manifest, "manifest_sha256")
    return manifest


def _foundation_config(config: dict[str, Any]) -> dict[str, Any]:
    confirmation = config["confirmation"]
    return {
        "window": {
            "start_inclusive_utc": confirmation["start_inclusive_utc"],
            "end_exclusive_utc": confirmation["end_exclusive_utc"],
        },
        "capital": {
            "account": confirmation["capital_account"],
            "server": confirmation["capital_server"],
            "symbol": confirmation["capital_symbol"],
            "maximum_seconds_since_tick": confirmation[
                "capital_maximum_seconds_since_tick"
            ],
            "require_tick_fresh": True,
        },
        "dukascopy": {
            "directory": confirmation["dukascopy_directory"],
            "price_decimals": 3,
            "maximum_backward_quote_age_ms": confirmation[
                "dukascopy_maximum_backward_quote_age_ms"
            ],
        },
    }


def build_confirmation_paired(
    config: dict[str, Any], capital_manifest: dict[str, Any], root: Path = ROOT
) -> tuple[pd.DataFrame, dict[str, Any]]:
    module_config = config["locked_modules"]
    foundation = load_locked_module(
        root,
        str(module_config["foundation_module"]),
        str(module_config["foundation_module_sha256"]),
        "v23_locked_foundation",
    )
    foundation_config = _foundation_config(config)
    capital = foundation.load_capital_quotes(capital_manifest, foundation_config)
    return foundation.build_paired_quotes(capital, foundation_config)


def load_development_paired(
    config: dict[str, Any], root: Path = ROOT
) -> pd.DataFrame:
    path = resolve(root, str(config["development"]["paired_quotes"]))
    frame = pd.read_parquet(path)
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    return frame.sort_values("capital_timestamp_ms", kind="mergesort").reset_index(
        drop=True
    )


def opportunity_runtime_config(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "data_quality": {
            **config["data_quality"],
            "calibration_full_weekdays": 1,
        },
        "feature": config["feature"],
        "frequency": {"cooldown_minutes": config["candidate"]["cooldown_minutes"]},
    }


def load_development_candidates(
    config: dict[str, Any], root: Path = ROOT
) -> pd.DataFrame:
    path = resolve(root, str(config["development"]["opportunities"]))
    frame = pd.read_parquet(path)
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    frame["evidence_partition"] = "DEVELOPMENT"
    return frame


def build_confirmation_candidates(
    paired: pd.DataFrame, config: dict[str, Any], root: Path = ROOT
) -> pd.DataFrame:
    module_config = config["locked_modules"]
    opportunity = load_locked_module(
        root,
        str(module_config["opportunity_module"]),
        str(module_config["opportunity_module_sha256"]),
        "v23_locked_opportunity",
    )
    runtime = opportunity_runtime_config(config)
    lags = [int(config["feature"]["primary_safety_lag_ms"])] + [
        int(value) for value in config["feature"]["robustness_safety_lags_ms"]
    ]
    frames: list[pd.DataFrame] = []
    for lag in lags:
        features = opportunity.build_causal_features(paired, runtime, lag)
        events = opportunity.select_candidate_episodes(
            features,
            float(config["candidate"]["z_threshold"]),
            int(config["candidate"]["cooldown_minutes"]),
        )
        events["candidate_side"] = np.where(
            events["candidate_direction"].gt(0), "LONG", "SHORT"
        )
        events["selected_z_threshold"] = float(
            config["candidate"]["z_threshold"]
        )
        events["evidence_partition"] = "SEALED_CONFIRMATION"
        frames.append(events)
    return pd.concat(frames, ignore_index=True)


def full_weekdays(paired: pd.DataFrame, config: dict[str, Any]) -> list[str]:
    timestamp = pd.to_datetime(paired["capital_timestamp_ms"], unit="ms", utc=True)
    daily = pd.DataFrame(
        {
            "date_utc": timestamp.dt.strftime("%Y-%m-%d"),
            "weekday": timestamp.dt.weekday,
        }
    ).groupby("date_utc", as_index=False).agg(
        paired_quotes=("date_utc", "size"), weekday=("weekday", "first")
    )
    minimum = int(config["data_quality"]["minimum_paired_quotes_per_full_day"])
    return daily.loc[
        daily["weekday"].lt(5) & daily["paired_quotes"].ge(minimum), "date_utc"
    ].tolist()


def simulate_trades(
    paired: pd.DataFrame,
    candidates: pd.DataFrame,
    eligible_dates: list[str],
    config: dict[str, Any],
) -> pd.DataFrame:
    simulation = config["simulation"]
    quotes = paired.sort_values("capital_timestamp_ms", kind="mergesort").reset_index(
        drop=True
    )
    timestamps = quotes["capital_timestamp_ms"].to_numpy(dtype=np.int64)
    candidate_rows = candidates.loc[candidates["date_utc"].isin(eligible_dates)]
    records: list[dict[str, Any]] = []
    hold_ms = int(simulation["hold_seconds"]) * 1000
    for _, lag_candidates in candidate_rows.groupby("safety_lag_ms", sort=True):
        lag_candidates = lag_candidates.sort_values(
            "capital_timestamp_ms", kind="mergesort"
        )
        last_exit_ms: int | None = None
        for _, candidate in lag_candidates.iterrows():
            decision_ms = int(candidate["capital_timestamp_ms"])
            if last_exit_ms is not None and decision_ms < last_exit_ms:
                continue
            entry_index = int(
                np.searchsorted(timestamps, decision_ms, side="right")
            )
            if entry_index >= len(quotes):
                continue
            entry = quotes.iloc[entry_index]
            entry_ms = int(entry["capital_timestamp_ms"])
            if entry_ms - decision_ms > int(simulation["maximum_entry_delay_ms"]):
                continue
            target_exit_ms = entry_ms + hold_ms
            exit_index = int(
                np.searchsorted(timestamps, target_exit_ms, side="left")
            )
            if exit_index >= len(quotes):
                continue
            exit_quote = quotes.iloc[exit_index]
            exit_ms = int(exit_quote["capital_timestamp_ms"])
            if exit_ms - target_exit_ms > int(simulation["maximum_exit_delay_ms"]):
                continue
            side = str(candidate["candidate_side"])
            base_slippage = float(simulation["base_slippage_per_side_price"])
            stress_slippage = float(
                simulation["stress_slippage_per_side_price"]
            )
            if side == "LONG":
                observed_entry = float(entry["capital_ask"])
                observed_exit = float(exit_quote["capital_bid"])
                observed_move = observed_exit - observed_entry
            elif side == "SHORT":
                observed_entry = float(entry["capital_bid"])
                observed_exit = float(exit_quote["capital_ask"])
                observed_move = observed_entry - observed_exit
            else:
                raise ValueError(f"Unknown V23 candidate side: {side}")
            dollars_per_unit = float(simulation["dollars_per_price_unit"])
            base_pnl = (observed_move - 2.0 * base_slippage) * dollars_per_unit
            stress_pnl = (
                observed_move - 2.0 * stress_slippage
            ) * dollars_per_unit
            records.append(
                {
                    "evidence_partition": candidate["evidence_partition"],
                    "safety_lag_ms": int(candidate["safety_lag_ms"]),
                    "date_utc": candidate["date_utc"],
                    "candidate_time_utc": candidate["timestamp_utc"],
                    "candidate_timestamp_ms": decision_ms,
                    "side": side,
                    "absolute_residual_z": float(candidate["absolute_residual_z"]),
                    "fair_value_residual": float(candidate["fair_value_residual"]),
                    "dukas_impulse": float(candidate["dukas_impulse"]),
                    "entry_time_utc": entry["timestamp_utc"],
                    "entry_timestamp_ms": entry_ms,
                    "entry_delay_ms": entry_ms - decision_ms,
                    "entry_bid": float(entry["capital_bid"]),
                    "entry_ask": float(entry["capital_ask"]),
                    "exit_time_utc": exit_quote["timestamp_utc"],
                    "exit_timestamp_ms": exit_ms,
                    "exit_delay_ms": exit_ms - target_exit_ms,
                    "exit_bid": float(exit_quote["capital_bid"]),
                    "exit_ask": float(exit_quote["capital_ask"]),
                    "observed_bidask_move": observed_move,
                    "base_pnl_dollars": base_pnl,
                    "stress_pnl_dollars": stress_pnl,
                    "reference_lot": float(simulation["reference_lot"]),
                }
            )
            last_exit_ms = exit_ms
    return pd.DataFrame(records)


def _profit_factor(values: pd.Series) -> float:
    gross_profit = float(values.loc[values.gt(0)].sum())
    gross_loss = float(-values.loc[values.lt(0)].sum())
    if gross_loss <= 0.0:
        return 999999.0 if gross_profit > 0.0 else 0.0
    return gross_profit / gross_loss


def _closed_trade_drawdown(values: pd.Series) -> float:
    equity = np.concatenate(([0.0], values.cumsum().to_numpy(dtype=float)))
    peaks = np.maximum.accumulate(equity)
    return float(np.max(peaks - equity))


def metrics_for_trades(
    trades: pd.DataFrame,
    partition: str,
    safety_lag_ms: int,
    full_dates: list[str],
    config: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    selected = trades.loc[
        trades["evidence_partition"].eq(partition)
        & trades["safety_lag_ms"].eq(int(safety_lag_ms))
    ].sort_values("entry_timestamp_ms", kind="mergesort")
    base = selected["base_pnl_dollars"].astype(float)
    stress = selected["stress_pnl_dollars"].astype(float)
    observed_daily = (
        selected.groupby("date_utc", as_index=False)
        .agg(
            trades=("date_utc", "size"),
            base_pnl_dollars=("base_pnl_dollars", "sum"),
            stress_pnl_dollars=("stress_pnl_dollars", "sum"),
        )
        .sort_values("date_utc")
    )
    daily = pd.DataFrame({"date_utc": full_dates}).merge(
        observed_daily, on="date_utc", how="left", validate="one_to_one"
    )
    for column in ("trades", "base_pnl_dollars", "stress_pnl_dollars"):
        daily[column] = daily[column].fillna(0)
    daily["trades"] = daily["trades"].astype(int)
    full_day_count = len(full_dates)
    base_net = float(base.sum())
    drawdown = _closed_trade_drawdown(base) if len(base) else 0.0
    recovery = base_net / drawdown if drawdown > 0.0 else (999999.0 if base_net > 0 else 0.0)
    metrics = {
        "evidence_partition": partition,
        "safety_lag_ms": int(safety_lag_ms),
        "full_weekdays": int(full_day_count),
        "trades": int(len(selected)),
        "trades_per_full_weekday": float(len(selected) / full_day_count)
        if full_day_count
        else 0.0,
        "long_trades": int(selected["side"].eq("LONG").sum()),
        "short_trades": int(selected["side"].eq("SHORT").sum()),
        "base_net_pnl_dollars": base_net,
        "base_profit_factor": _profit_factor(base),
        "base_win_rate": float(base.gt(0).mean()) if len(base) else 0.0,
        "base_mean_pnl_dollars": float(base.mean()) if len(base) else 0.0,
        "stress_net_pnl_dollars": float(stress.sum()),
        "stress_profit_factor": _profit_factor(stress),
        "closed_trade_drawdown_dollars": drawdown,
        "recovery_factor": float(recovery),
        "profitable_day_share": float(daily["base_pnl_dollars"].gt(0).mean())
        if len(daily)
        else 0.0,
    }
    if partition == "SEALED_CONFIRMATION" and int(safety_lag_ms) == int(
        config["feature"]["primary_safety_lag_ms"]
    ):
        values_by_full_day = daily["base_pnl_dollars"].to_numpy(dtype=float)
        rng = np.random.default_rng(int(config["gates"]["daily_bootstrap_seed"]))
        samples = rng.choice(
            values_by_full_day,
            size=(int(config["gates"]["daily_bootstrap_samples"]), full_day_count),
            replace=True,
        ).mean(axis=1)
        metrics["daily_bootstrap_mean_lower_bound_dollars"] = float(
            np.quantile(samples, float(config["gates"]["daily_bootstrap_lower_quantile"]))
        )
    else:
        metrics["daily_bootstrap_mean_lower_bound_dollars"] = None
    daily.insert(0, "safety_lag_ms", int(safety_lag_ms))
    daily.insert(0, "evidence_partition", partition)
    return metrics, daily


def evaluate_economic_test(
    development_paired: pd.DataFrame,
    confirmation_paired: pd.DataFrame,
    development_candidates: pd.DataFrame,
    confirmation_candidates: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
]:
    dev_dates = full_weekdays(development_paired, config)
    confirmation_dates = full_weekdays(confirmation_paired, config)
    dev_trades = simulate_trades(
        development_paired, development_candidates, dev_dates, config
    )
    confirmation_trades = simulate_trades(
        confirmation_paired, confirmation_candidates, confirmation_dates, config
    )
    trades = pd.concat([dev_trades, confirmation_trades], ignore_index=True)
    lags = [int(config["feature"]["primary_safety_lag_ms"])] + [
        int(value) for value in config["feature"]["robustness_safety_lags_ms"]
    ]
    metric_rows: list[dict[str, Any]] = []
    daily_rows: list[pd.DataFrame] = []
    for partition, dates in (
        ("DEVELOPMENT", dev_dates),
        ("SEALED_CONFIRMATION", confirmation_dates),
    ):
        for lag in lags:
            metrics, daily = metrics_for_trades(trades, partition, lag, dates, config)
            metric_rows.append(metrics)
            daily_rows.append(daily)
    metrics_frame = pd.DataFrame(metric_rows)
    daily_pnl = pd.concat(daily_rows, ignore_index=True)
    primary = int(config["feature"]["primary_safety_lag_ms"])
    dev = next(
        row
        for row in metric_rows
        if row["evidence_partition"] == "DEVELOPMENT"
        and row["safety_lag_ms"] == primary
    )
    confirmation = next(
        row
        for row in metric_rows
        if row["evidence_partition"] == "SEALED_CONFIRMATION"
        and row["safety_lag_ms"] == primary
    )
    gates = config["gates"]
    gate_results = {
        "development_economics": bool(
            dev["base_profit_factor"] >= float(gates["development_min_profit_factor"])
            and (
                not bool(gates["development_require_positive_net"])
                or dev["base_net_pnl_dollars"] > 0.0
            )
        ),
        "confirmation_sample": bool(
            confirmation["trades"] >= int(gates["confirmation_min_trades"])
            and float(gates["confirmation_min_trades_per_full_weekday"])
            <= confirmation["trades_per_full_weekday"]
            <= float(gates["confirmation_max_trades_per_full_weekday"])
        ),
        "confirmation_economics": bool(
            confirmation["base_profit_factor"]
            >= float(gates["confirmation_min_profit_factor"])
            and confirmation["stress_profit_factor"]
            >= float(gates["confirmation_stress_min_profit_factor"])
            and (
                not bool(gates["confirmation_require_positive_net"])
                or confirmation["base_net_pnl_dollars"] > 0.0
            )
        ),
        "confirmation_daily_stability": bool(
            confirmation["profitable_day_share"]
            >= float(gates["confirmation_min_profitable_day_share"])
            and confirmation["daily_bootstrap_mean_lower_bound_dollars"] > 0.0
        ),
        "confirmation_drawdown": bool(
            confirmation["closed_trade_drawdown_dollars"]
            <= float(gates["confirmation_max_closed_trade_drawdown_dollars"])
            and confirmation["recovery_factor"]
            >= float(gates["confirmation_min_recovery_factor"])
        ),
        "clock_robustness": all(
            row["base_profit_factor"]
            >= float(gates["clock_robustness_min_profit_factor"])
            for row in metric_rows
            if row["evidence_partition"] == "SEALED_CONFIRMATION"
            and row["safety_lag_ms"] != primary
        ),
    }
    passed = all(gate_results.values())
    candidates = pd.concat(
        [development_candidates, confirmation_candidates], ignore_index=True
    )
    audit = {
        "schema_version": config["schema_version"],
        "attempt": "V23_SINGLE_PREREGISTERED_ECONOMIC_TEST",
        "development_full_weekdays": dev_dates,
        "confirmation_full_weekdays": confirmation_dates,
        "gate_results": gate_results,
        "all_economic_gates_pass": passed,
        "decision": "V23_RESEARCH_PASS" if passed else "V23_RESEARCH_FAIL",
        "primary_development_metrics": dev,
        "primary_confirmation_metrics": confirmation,
        "same_version_tuning_authorized": False,
        "strategy_admission_authorized": False,
        "model_training_authorized": False,
        "execution_authorized": False,
    }
    return candidates, trades, metrics_frame, daily_pnl, audit


def render_markdown(audit: dict[str, Any]) -> str:
    dev = audit["primary_development_metrics"]
    confirmation = audit["primary_confirmation_metrics"]
    return (
        "# Capital-Dukascopy Lagged Economic Test V23\n\n"
        f"Decision: **{audit['decision']}**.\n\n"
        f"Development: {dev['trades']} trades, ${dev['base_net_pnl_dollars']:.2f} "
        f"net, PF {dev['base_profit_factor']:.3f}, drawdown "
        f"${dev['closed_trade_drawdown_dollars']:.2f}.\n\n"
        f"Sealed confirmation: {confirmation['trades']} trades, "
        f"{confirmation['trades_per_full_weekday']:.3f}/day, "
        f"${confirmation['base_net_pnl_dollars']:.2f} net, PF "
        f"{confirmation['base_profit_factor']:.3f}, stress PF "
        f"{confirmation['stress_profit_factor']:.3f}, drawdown "
        f"${confirmation['closed_trade_drawdown_dollars']:.2f}.\n\n"
        f"Gate results: `{json.dumps(audit['gate_results'], sort_keys=True)}`.\n\n"
        "No result authorizes model training, Python execution, an EA, demo, "
        "live, account, terminal, or broker action.\n"
    )
