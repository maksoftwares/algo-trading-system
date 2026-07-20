from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_repo_sources(repo_root: Path, sources: dict[str, Any]) -> dict[str, str]:
    verified: dict[str, str] = {}
    for source_id, source in sources.items():
        path = repo_root / str(source["path"])
        actual = sha256_file(path)
        if actual != str(source["sha256"]):
            raise ValueError(f"Source hash mismatch for {source_id}: {actual}")
        verified[source_id] = actual
    return verified


def directory_manifest(source: dict[str, Any]) -> list[dict[str, Any]]:
    root = Path(str(source["root"]))
    files = sorted(root.glob(str(source["pattern"])))
    if len(files) != int(source["expected_files"]):
        raise ValueError(f"Unexpected file count for {root}: {len(files)}")
    rows: list[dict[str, Any]] = []
    for path in files:
        rows.append(
            {
                "path": path.as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return rows


def _standard_source(
    frame: pd.DataFrame,
    trade_ids: pd.Series,
    source_id: str,
    pnl: pd.Series,
) -> pd.DataFrame:
    result = pd.DataFrame(
        {
            "trade_id": trade_ids.astype(str),
            "source_id": source_id,
            "source_entry_time": pd.to_datetime(frame["entry_time"], utc=True),
            "source_exit_time": pd.to_datetime(frame["exit_time"], utc=True),
            "source_direction": frame["direction"].astype(str),
            "entry_price": pd.to_numeric(frame["entry_price"], errors="raise"),
            "exit_price": pd.to_numeric(frame["exit_price"], errors="raise"),
            "source_risk_usd": pd.to_numeric(frame["risk_usd"], errors="coerce"),
            "source_pnl_usd": pd.to_numeric(pnl, errors="raise"),
        }
    )
    if result["trade_id"].duplicated().any():
        raise ValueError(f"Duplicate trade IDs in {source_id}")
    return result


def build_price_ledger(
    trades: pd.DataFrame,
    core: pd.DataFrame,
    sources: dict[str, pd.DataFrame],
    policy: dict[str, Any],
    extra_r1_fee_usd: float,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    tolerance = float(policy["absolute_tolerance"])
    core_meta = core[["trade_id", "specialist_id", "source_strategy"]].copy()
    if core_meta["trade_id"].duplicated().any():
        raise ValueError("Duplicate V59 core trade IDs")
    ledger = trades.merge(core_meta, on="trade_id", how="left", validate="one_to_one")
    ledger["is_core"] = ledger["sleeve_id"].eq("V59_BROKER_CORE")
    if ledger.loc[ledger["is_core"], "specialist_id"].isna().any():
        raise ValueError("Core metadata did not map one-to-one")

    pieces: list[pd.DataFrame] = []
    r1 = core.loc[core["specialist_id"].eq("R1_UPTREND")].copy()
    pieces.append(
        _standard_source(r1, r1["trade_id"], "R1_NATIVE_POSITION", r1["pnl_usd"])
    )

    regime = sources["regime_rawtick"]
    for specialist in ("R2_DOWNTREND", "R3_COMPRESSION"):
        ids = set(core.loc[core["specialist_id"].eq(specialist), "trade_id"].astype(str))
        selected = regime.loc[regime["candidate_id"].astype(str).isin(ids)].copy()
        pieces.append(
            _standard_source(
                selected,
                selected["candidate_id"],
                f"{specialist}_DUKASCOPY_RAW_TICK",
                selected["stress_net_r"] * selected["risk_usd"],
            )
        )

    chop_ids = set(core.loc[core["specialist_id"].eq("R4_CHOP"), "trade_id"].astype(str))
    chop = sources["chop_rawtick"]
    chop = chop.loc[chop["candidate_id"].astype(str).isin(chop_ids)].copy()
    pieces.append(
        _standard_source(
            chop,
            chop["candidate_id"],
            "R4_CHOP_DUKASCOPY_RAW_TICK",
            chop["stress_net_r"] * chop["risk_usd"],
        )
    )

    transition_ids = set(
        core.loc[core["specialist_id"].eq("R5_TRANSITION"), "trade_id"].astype(str)
    )
    transition = sources["transition_rawtick"]
    transition = transition.loc[
        transition["attempt_no"].eq(int(policy["r5_attempt_no"]))
        & np.isclose(
            transition["risk_weight"].astype(float),
            float(policy["r5_required_risk_weight"]),
            rtol=0.0,
            atol=tolerance,
        )
        & transition["candidate_id"].astype(str).isin(transition_ids)
    ].copy()
    pieces.append(
        _standard_source(
            transition,
            transition["candidate_id"],
            "R5_TRANSITION_DUKASCOPY_RAW_TICK",
            transition["stress_net_r"] * transition["risk_usd"],
        )
    )

    v7_ids = set(ledger.loc[ledger["sleeve_id"].eq("V7_SWING_HEALTH"), "trade_id"])
    v7 = sources["v7_rawtick"]
    v7 = v7.loc[v7["v7_trade_id"].astype(str).isin(v7_ids)].copy()
    pieces.append(
        _standard_source(
            v7,
            v7["v7_trade_id"],
            "V7_DUKASCOPY_RAW_TICK",
            v7["portfolio_pnl_usd"],
        )
    )

    expansion = sources["expansion_rawtick"]
    v8_ids = set(ledger.loc[ledger["sleeve_id"].eq("V8_RETEST_HEALTH"), "trade_id"])
    v8 = expansion.loc[
        expansion["action_id"].eq(str(policy["v8_action_id"]))
        & ("V8_" + expansion["event_id"].astype(str)).isin(v8_ids)
    ].copy()
    pieces.append(
        _standard_source(
            v8,
            "V8_" + v8["event_id"].astype(str),
            "V8_DUKASCOPY_RAW_TICK",
            v8["stress_net_r"] * v8["risk_usd"],
        )
    )

    overlay_ids = set(
        ledger.loc[
            ledger["sleeve_id"].eq("V57_BREAK_SWING_H4ADX_HIGH"), "trade_id"
        ]
    )
    overlay = expansion.loc[
        expansion["action_id"].eq(str(policy["v57_action_id"]))
        & ("V9_BREAK_" + expansion["event_id"].astype(str)).isin(overlay_ids)
    ].copy()
    pieces.append(
        _standard_source(
            overlay,
            "V9_BREAK_" + overlay["event_id"].astype(str),
            "V57_OVERLAY_DUKASCOPY_RAW_TICK",
            overlay["stress_net_r"] * overlay["risk_usd"],
        )
    )

    v25_ids = set(ledger.loc[ledger["sleeve_id"].eq("V25_CHOP"), "trade_id"])
    v25 = sources["v25_rawtick"]
    v25 = v25.loc[("V25_" + v25["candidate_id"].astype(str)).isin(v25_ids)].copy()
    pieces.append(
        _standard_source(
            v25,
            "V25_" + v25["candidate_id"].astype(str),
            "V25_DUKASCOPY_RAW_TICK",
            v25["stress_net_r"] * v25["risk_usd"],
        )
    )

    prices = pd.concat(pieces, ignore_index=True)
    if prices["trade_id"].duplicated().any():
        duplicates = prices.loc[prices["trade_id"].duplicated(False), "trade_id"]
        raise ValueError(f"Price source duplication: {duplicates.head().tolist()}")
    ledger = ledger.merge(prices, on="trade_id", how="left", validate="one_to_one")
    if ledger["source_id"].isna().any():
        missing = ledger.loc[ledger["source_id"].isna(), "trade_id"].head().tolist()
        raise ValueError(f"Missing price sources: {missing}")

    for column in ("signal_time", "entry_time", "exit_time"):
        ledger[column] = pd.to_datetime(ledger[column], utc=True)
    entry_error = (ledger["entry_time"] - ledger["source_entry_time"]).abs().dt.total_seconds()
    exit_error = (ledger["exit_time"] - ledger["source_exit_time"]).abs().dt.total_seconds()
    if float(entry_error.max()) > tolerance or float(exit_error.max()) > tolerance:
        raise ValueError("Source timestamp mismatch")
    if not ledger["direction"].astype(str).eq(ledger["source_direction"]).all():
        raise ValueError("Source direction mismatch")
    pnl_error = (ledger["pnl_usd"] - ledger["source_pnl_usd"]).abs()
    if float(pnl_error.max()) > tolerance:
        raise ValueError(f"Source P&L mismatch: {float(pnl_error.max())}")
    risk_comparable = ledger["risk_usd"].notna() & ledger["source_risk_usd"].notna()
    risk_error = (
        ledger.loc[risk_comparable, "risk_usd"]
        - ledger.loc[risk_comparable, "source_risk_usd"]
    ).abs()
    if len(risk_error) and float(risk_error.max()) > tolerance:
        raise ValueError(f"Source risk mismatch: {float(risk_error.max())}")

    ledger["direction_sign"] = np.where(ledger["direction"].eq("LONG"), 1.0, -1.0)
    ounces = float(policy["xau_ounces_per_reference_lot"])
    ledger["gross_endpoint_pnl_usd"] = (
        ledger["direction_sign"]
        * (ledger["exit_price"] - ledger["entry_price"])
        * ounces
    )
    ledger["implied_cost_usd"] = ledger["gross_endpoint_pnl_usd"] - ledger["pnl_usd"]
    ledger["open_cost_usd"] = ledger["implied_cost_usd"].clip(lower=0.0)
    ledger["is_r1"] = ledger["specialist_id"].eq("R1_UPTREND")
    ledger["fee_stress_pnl_usd"] = ledger["pnl_usd"] - np.where(
        ledger["is_r1"], float(extra_r1_fee_usd), 0.0
    )
    ledger["fee_stress_implied_cost_usd"] = (
        ledger["gross_endpoint_pnl_usd"] - ledger["fee_stress_pnl_usd"]
    )
    ledger["fee_stress_open_cost_usd"] = ledger[
        "fee_stress_implied_cost_usd"
    ].clip(lower=0.0)
    ledger["endpoint_error_usd"] = (
        ledger["gross_endpoint_pnl_usd"] - ledger["implied_cost_usd"] - ledger["pnl_usd"]
    )
    if float(ledger["endpoint_error_usd"].abs().max()) > tolerance:
        raise ValueError("Endpoint reconciliation failed")

    audit = {
        "trades": int(len(ledger)),
        "source_counts": ledger["source_id"].value_counts().sort_index().to_dict(),
        "maximum_entry_time_error_seconds": float(entry_error.max()),
        "maximum_exit_time_error_seconds": float(exit_error.max()),
        "maximum_source_pnl_error_usd": float(pnl_error.max()),
        "maximum_source_risk_error_usd": float(risk_error.max()) if len(risk_error) else 0.0,
        "maximum_endpoint_error_usd": float(ledger["endpoint_error_usd"].abs().max()),
        "negative_implied_cost_trades": int(ledger["implied_cost_usd"].lt(-tolerance).sum()),
        "r1_fee_stressed_trades": int(ledger["is_r1"].sum()),
    }
    return ledger.sort_values(["entry_time", "trade_id"], kind="mergesort"), audit


def load_m5_bars(market: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    modern_path = Path(str(market["modern_m5"]["path"]))
    if sha256_file(modern_path) != str(market["modern_m5"]["sha256"]):
        raise ValueError("Modern M5 source hash mismatch")
    modern_columns = [
        "timestamp_ms",
        "bid_open",
        "bid_high",
        "bid_low",
        "bid_close",
        "ask_open",
        "ask_high",
        "ask_low",
        "ask_close",
    ]
    modern = pd.read_parquet(modern_path, columns=modern_columns)
    if len(modern) != int(market["modern_m5"]["expected_rows"]):
        raise ValueError("Unexpected modern M5 row count")

    side_frames: dict[str, pd.DataFrame] = {}
    manifests: dict[str, list[dict[str, Any]]] = {}
    for side in ("bid", "ask"):
        source = market[f"legacy_{side}_m5"]
        manifest = directory_manifest(source)
        frames = [pd.read_parquet(row["path"]) for row in manifest]
        frame = pd.concat(frames, ignore_index=True)
        if len(frame) != int(source["expected_rows"]):
            raise ValueError(f"Unexpected legacy {side} row count")
        frame = frame[["timestamp_ms", "open", "high", "low", "close"]].rename(
            columns={name: f"{side}_{name}" for name in ("open", "high", "low", "close")}
        )
        side_frames[side] = frame
        manifests[side] = manifest
    legacy = side_frames["bid"].merge(
        side_frames["ask"], on="timestamp_ms", how="outer", validate="one_to_one"
    )
    if legacy.isna().any().any():
        raise ValueError("Legacy bid/ask M5 timestamps do not match")
    bars = pd.concat([legacy, modern], ignore_index=True)
    bars = bars.sort_values("timestamp_ms", kind="mergesort").reset_index(drop=True)
    if bars["timestamp_ms"].duplicated().any():
        raise ValueError("Duplicate M5 timestamps")
    quote_columns = [column for column in bars.columns if column != "timestamp_ms"]
    if not np.isfinite(bars[quote_columns].to_numpy(dtype=float)).all():
        raise ValueError("Nonfinite M5 quote")
    bars["timestamp_utc"] = pd.to_datetime(bars["timestamp_ms"], unit="ms", utc=True)
    audit = {
        "bars": int(len(bars)),
        "first_bar_utc": bars["timestamp_utc"].iloc[0].isoformat(),
        "last_bar_utc": bars["timestamp_utc"].iloc[-1].isoformat(),
        "legacy_bid_manifest_sha256": canonical_sha256({"files": manifests["bid"]}),
        "legacy_ask_manifest_sha256": canonical_sha256({"files": manifests["ask"]}),
    }
    return bars, audit


def _range_add(diff: np.ndarray, start: int, end: int, value: float) -> None:
    if start >= end:
        return
    diff[start] += value
    diff[end] -= value


def _utc_ns(values: pd.Series) -> np.ndarray:
    return (
        pd.to_datetime(values, utc=True)
        .astype("datetime64[ns, UTC]")
        .astype("int64")
        .to_numpy()
    )


def floating_curve(
    bars: pd.DataFrame,
    ledger: pd.DataFrame,
    pnl_column: str,
    cost_column: str,
    bar_minutes: int,
) -> pd.DataFrame:
    bar_ns = _utc_ns(bars["timestamp_utc"])
    duration_ns = int(pd.Timedelta(minutes=bar_minutes).value)
    bar_end_ns = bar_ns + duration_ns
    entry_ns = _utc_ns(ledger["entry_time"])
    exit_ns = _utc_ns(ledger["exit_time"])
    if entry_ns.min() < bar_ns.min() or exit_ns.max() > bar_end_ns.max():
        raise ValueError("M5 coverage does not contain every trade")
    n = len(bars)
    long_count = np.zeros(n + 1)
    short_count = np.zeros(n + 1)
    open_constant = np.zeros(n + 1)
    close_long_count = np.zeros(n + 1)
    close_short_count = np.zeros(n + 1)
    close_constant = np.zeros(n + 1)
    risk_count = np.zeros(n + 1)
    known_risk = np.zeros(n + 1)
    addon_count = np.zeros(n + 1)
    addon_risk = np.zeros(n + 1)

    for row in ledger.itertuples(index=False):
        entry = int(row.entry_time.value)
        exit_ = int(row.exit_time.value)
        start = int(np.searchsorted(bar_end_ns, entry, side="right"))
        end = int(np.searchsorted(bar_ns, exit_, side="left"))
        close_start = int(np.searchsorted(bar_end_ns, entry, side="right"))
        close_end = int(np.searchsorted(bar_end_ns, exit_, side="left"))
        sign = 1.0 if row.direction == "LONG" else -1.0
        constant = -sign * float(row.entry_price) - float(getattr(row, cost_column))
        if sign > 0:
            _range_add(long_count, start, end, 1.0)
            _range_add(close_long_count, close_start, close_end, 1.0)
        else:
            _range_add(short_count, start, end, 1.0)
            _range_add(close_short_count, close_start, close_end, 1.0)
        _range_add(open_constant, start, end, constant)
        _range_add(close_constant, close_start, close_end, constant)
        _range_add(risk_count, start, end, 1.0)
        if pd.notna(row.risk_usd):
            _range_add(known_risk, start, end, float(row.risk_usd))
        if row.sleeve_id != "V59_BROKER_CORE":
            _range_add(addon_count, start, end, 1.0)
            _range_add(addon_risk, start, end, float(row.risk_usd))

    long_active = np.cumsum(long_count[:-1])
    short_active = np.cumsum(short_count[:-1])
    constant_active = np.cumsum(open_constant[:-1])
    close_long = np.cumsum(close_long_count[:-1])
    close_short = np.cumsum(close_short_count[:-1])
    close_const = np.cumsum(close_constant[:-1])
    ordered_exit = ledger.sort_values(["exit_time", "trade_id"], kind="mergesort")
    ordered_exit_ns = _utc_ns(ordered_exit["exit_time"])
    exit_pnl = ordered_exit[pnl_column].to_numpy(dtype=float)
    cumulative = np.concatenate(([0.0], np.cumsum(exit_pnl)))
    realized_before = cumulative[np.searchsorted(ordered_exit_ns, bar_ns, side="right")]
    realized_at_close = cumulative[
        np.searchsorted(ordered_exit_ns, bar_end_ns, side="right")
    ]
    low = (
        realized_before
        + long_active * bars["bid_low"].to_numpy(dtype=float)
        - short_active * bars["ask_high"].to_numpy(dtype=float)
        + constant_active
    )
    high = (
        realized_before
        + long_active * bars["bid_high"].to_numpy(dtype=float)
        - short_active * bars["ask_low"].to_numpy(dtype=float)
        + constant_active
    )
    close = (
        realized_at_close
        + close_long * bars["bid_close"].to_numpy(dtype=float)
        - close_short * bars["ask_close"].to_numpy(dtype=float)
        + close_const
    )
    return pd.DataFrame(
        {
            "timestamp_utc": bars["timestamp_utc"],
            "low_equity_pnl_usd": low,
            "high_equity_pnl_usd": high,
            "close_equity_pnl_usd": close,
            "open_positions": np.cumsum(risk_count[:-1]).astype(int),
            "known_initial_risk_usd": np.cumsum(known_risk[:-1]),
            "open_addons": np.cumsum(addon_count[:-1]).astype(int),
            "addon_initial_risk_usd": np.cumsum(addon_risk[:-1]),
        }
    )


def envelope_drawdown(curve: pd.DataFrame) -> dict[str, Any]:
    high = curve["high_equity_pnl_usd"].to_numpy(dtype=float)
    low = curve["low_equity_pnl_usd"].to_numpy(dtype=float)
    if len(curve) == 0:
        return {
            "maximum_drawdown_usd": 0.0,
            "peak_time_utc": None,
            "trough_time_utc": None,
            "peak_equity_pnl_usd": 0.0,
            "trough_equity_pnl_usd": 0.0,
        }
    running_peak = -np.inf
    running_peak_index = 0
    maximum = -np.inf
    peak_index = 0
    trough_index = 0
    for index in range(len(curve)):
        if high[index] > running_peak:
            running_peak = high[index]
            running_peak_index = index
        drawdown = running_peak - low[index]
        if drawdown > maximum:
            maximum = drawdown
            peak_index = running_peak_index
            trough_index = index
    timestamps = curve["timestamp_utc"]
    return {
        "maximum_drawdown_usd": float(maximum),
        "peak_time_utc": timestamps.iloc[peak_index].isoformat(),
        "trough_time_utc": timestamps.iloc[trough_index].isoformat(),
        "peak_equity_pnl_usd": float(high[peak_index]),
        "trough_equity_pnl_usd": float(low[trough_index]),
        "trough_open_positions": int(curve["open_positions"].iloc[trough_index]),
        "trough_open_addons": int(curve["open_addons"].iloc[trough_index]),
        "trough_known_initial_risk_usd": float(
            curve["known_initial_risk_usd"].iloc[trough_index]
        ),
        "trough_addon_initial_risk_usd": float(
            curve["addon_initial_risk_usd"].iloc[trough_index]
        ),
    }


def window_drawdowns(
    base_curve: pd.DataFrame,
    stress_curve: pd.DataFrame,
    windows: dict[str, list[str]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for name, bounds in windows.items():
        start, end = map(pd.Timestamp, bounds)
        mask = base_curve["timestamp_utc"].ge(start) & base_curve["timestamp_utc"].lt(end)
        base = envelope_drawdown(base_curve.loc[mask].reset_index(drop=True))
        stress = envelope_drawdown(stress_curve.loc[mask].reset_index(drop=True))
        rows.append(
            {
                "window": name,
                "window_start_utc": start.isoformat(),
                "cutoff_exclusive_utc": end.isoformat(),
                "base_floating_drawdown_usd": base["maximum_drawdown_usd"],
                "fee_stress_floating_drawdown_usd": stress["maximum_drawdown_usd"],
                "base_peak_time_utc": base["peak_time_utc"],
                "base_trough_time_utc": base["trough_time_utc"],
                "fee_stress_peak_time_utc": stress["peak_time_utc"],
                "fee_stress_trough_time_utc": stress["trough_time_utc"],
            }
        )
    return pd.DataFrame(rows)
