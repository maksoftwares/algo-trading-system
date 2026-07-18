from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Iterator, Mapping

import numpy as np
import pandas as pd
from scipy import stats


PACKAGE = Path(__file__).resolve().parents[1]
FAST_RESEARCH = PACKAGE.parent


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


R1 = _load_module(
    "out_of_era_v2_r1_exact",
    FAST_RESEARCH / "mt5-r1-uptrend-portability-v1" / "src" / "portability.py",
)
COMPRESSION = _load_module(
    "out_of_era_v2_compression_exact",
    FAST_RESEARCH / "mt5-compression-portability-v1" / "src" / "portability.py",
)
EVENT = _load_module(
    "out_of_era_v2_corrected_event",
    FAST_RESEARCH
    / "macro-event-reaction-replication-v2"
    / "src"
    / "event_reaction.py",
)
DATA = _load_module(
    "out_of_era_v2_canonical_bar_data",
    FAST_RESEARCH / "independent-specialists-v1" / "src" / "data.py",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_side_specific_m5(replay_root: Path, months: Iterable[str]) -> pd.DataFrame:
    month_list = list(months)
    sides: dict[str, pd.DataFrame] = {}
    for side in ("bid", "ask", "mid"):
        frames: list[pd.DataFrame] = []
        for month in month_list:
            year, number = month.split("-")
            path = (
                replay_root
                / "bars"
                / "XAUUSD"
                / side
                / "M5"
                / f"year={year}"
                / f"month={number}"
                / "bars.parquet"
            )
            if not path.is_file():
                raise FileNotFoundError(path)
            frame = pd.read_parquet(path)
            frame["timestamp_utc"] = pd.to_datetime(
                frame["timestamp_utc"], utc=True, errors="raise"
            )
            frames.append(frame)
        combined = pd.concat(frames, ignore_index=True).sort_values(
            "timestamp_utc", kind="mergesort"
        )
        if combined["timestamp_utc"].duplicated().any():
            raise ValueError(f"Duplicate {side} M5 timestamps")
        rename = {
            value: f"{side}_{value}" for value in ("open", "high", "low", "close")
        }
        sides[side] = combined[
            ["timestamp_utc", "timestamp_ms", "tick_count", *rename]
        ].rename(columns=rename)
    counts = {side: len(frame) for side, frame in sides.items()}
    if len(set(counts.values())) != 1:
        raise ValueError(f"Side-specific M5 row counts differ: {counts}")
    merged = sides["bid"].rename(columns={"tick_count": "tick_count_bid"})
    merged = merged.merge(
        sides["ask"].drop(columns=["timestamp_ms"]).rename(
            columns={"tick_count": "tick_count_ask"}
        ),
        on="timestamp_utc",
        how="inner",
        validate="one_to_one",
    )
    merged = merged.merge(
        sides["mid"].drop(columns=["timestamp_ms"]).rename(
            columns={"tick_count": "tick_count_mid"}
        ),
        on="timestamp_utc",
        how="inner",
        validate="one_to_one",
    )
    if len(merged) != counts["bid"]:
        raise ValueError("Bid/Ask/Mid M5 timestamps are not exactly aligned")
    prices = [
        f"{side}_{field}"
        for side in ("bid", "ask", "mid")
        for field in ("open", "high", "low", "close")
    ]
    if (~np.isfinite(merged[prices]) | (merged[prices] <= 0.0)).any().any():
        raise ValueError("Invalid side-specific M5 price")
    if (merged["ask_open"] < merged["bid_open"]).any():
        raise ValueError("Crossed M5 opening quote")
    merged["bar_start_utc"] = merged["timestamp_utc"]
    merged["bar_end_utc"] = merged["bar_start_utc"] + pd.Timedelta(minutes=5)
    merged["timestamp_utc"] = merged["bar_end_utc"]
    merged["timeframe"] = "M5"
    merged["tick_count"] = merged["tick_count_mid"]
    previous = merged["mid_close"].shift(1)
    true_range = pd.concat(
        [
            merged["mid_high"] - merged["mid_low"],
            (merged["mid_high"] - previous).abs(),
            (merged["mid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    merged["atr"] = true_range.ewm(
        alpha=1.0 / 14.0, adjust=False, min_periods=14
    ).mean()
    return merged.sort_values("bar_start_utc", kind="mergesort").reset_index(
        drop=True
    )


def run_r1_variant(
    m5: pd.DataFrame,
    source_config: Mapping[str, Any],
    candidate_id: str,
) -> pd.DataFrame:
    d1, h4 = R1.BASE.prepare_signal_bars(m5, source_config["signal"])
    enriched, _ = R1.attach_r1_regime(
        m5,
        d1,
        h4,
        source_config["signal"],
        source_config["regime"],
    )
    candidates = R1.generate_r1_candidates(enriched, source_config["signal"])
    _, all_trades = R1.BASE.simulate_candidates(
        m5, candidates, source_config["execution"]
    )
    settings = source_config["policies"]["PORTFOLIO_CONSTRAINED_PRIMARY"]
    trades = R1.BASE.apply_policy(
        all_trades, "PORTFOLIO_CONSTRAINED_PRIMARY", settings
    )
    if trades.empty:
        return pd.DataFrame()
    result = trades.copy()
    if "candidate_id" in result:
        result["source_candidate_id"] = result["candidate_id"].astype(str)
    result["candidate_id"] = candidate_id
    result["source_policy_id"] = "PORTFOLIO_CONSTRAINED_PRIMARY"
    return result


def run_compression(
    m5: pd.DataFrame,
    source_config: Mapping[str, Any],
    candidate_id: str,
) -> pd.DataFrame:
    _, h4 = COMPRESSION.prepare_signal_bars(m5, source_config["signal"])
    candidates = COMPRESSION.generate_candidates(h4, source_config["signal"])
    _, all_trades = COMPRESSION.simulate_candidates(
        m5, candidates, source_config["execution"]
    )
    settings = source_config["policies"]["PORTFOLIO_CONSTRAINED_PRIMARY"]
    trades = COMPRESSION.apply_policy(
        all_trades, "PORTFOLIO_CONSTRAINED_PRIMARY", settings
    )
    if trades.empty:
        return pd.DataFrame()
    result = trades.copy()
    if "candidate_id" in result:
        result["source_candidate_id"] = result["candidate_id"].astype(str)
    result["candidate_id"] = candidate_id
    result["source_policy_id"] = "PORTFOLIO_CONSTRAINED_PRIMARY"
    return result


def run_price_candidate(
    m5: pd.DataFrame,
    candidate: Mapping[str, Any],
    source_config: Mapping[str, Any],
) -> pd.DataFrame:
    engine = str(candidate["engine"])
    candidate_id = str(candidate["candidate_id"])
    if engine == "R1_REGIME_BREAKOUT":
        return run_r1_variant(m5, source_config, candidate_id)
    if engine == "COMPRESSION_BREAKOUT":
        return run_compression(m5, source_config, candidate_id)
    raise KeyError(engine)


@dataclass(frozen=True)
class Tick:
    timestamp_ms: int
    bid: float
    ask: float


class VerifiedNormalizedTickStore:
    def __init__(self, replay_root: Path, symbol: str) -> None:
        self.replay_root = replay_root.resolve()
        self.symbol = symbol

    @lru_cache(maxsize=6)
    def _load_month(self, year: int, month: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        path = (
            self.replay_root
            / "normalized"
            / self.symbol
            / f"year={year:04d}"
            / f"month={month:02d}"
            / "ticks.parquet"
        )
        if not path.is_file():
            raise FileNotFoundError(path)
        frame = pd.read_parquet(path, columns=["timestamp_ms", "bid", "ask"])
        times = frame["timestamp_ms"].to_numpy(dtype=np.int64)
        bids = frame["bid"].to_numpy(dtype=float)
        asks = frame["ask"].to_numpy(dtype=float)
        if len(times) and np.any(np.diff(times) < 0):
            raise ValueError(f"Tick partition is not sorted: {path}")
        if np.any(~np.isfinite(bids)) or np.any(~np.isfinite(asks)):
            raise ValueError(f"Non-finite tick quote: {path}")
        if np.any(asks < bids):
            raise ValueError(f"Crossed tick quote: {path}")
        return times, bids, asks

    def ticks_between(
        self, start_timestamp_ms: int, end_timestamp_ms: int
    ) -> Iterator[Tick]:
        if end_timestamp_ms < start_timestamp_ms:
            return
        start = pd.Timestamp(start_timestamp_ms, unit="ms", tz="UTC")
        end = pd.Timestamp(end_timestamp_ms, unit="ms", tz="UTC")
        months = pd.period_range(
            start.tz_localize(None).to_period("M"),
            end.tz_localize(None).to_period("M"),
            freq="M",
        )
        for period in months:
            times, bids, asks = self._load_month(period.year, period.month)
            left = int(np.searchsorted(times, start_timestamp_ms, side="left"))
            right = int(np.searchsorted(times, end_timestamp_ms, side="right"))
            for index in range(left, right):
                yield Tick(int(times[index]), float(bids[index]), float(asks[index]))


def _first_quote_after(
    tick_store: VerifiedNormalizedTickStore,
    decision_ms: int,
    maximum_delay_ms: int,
) -> Tick | None:
    return next(
        (
            tick
            for tick in tick_store.ticks_between(
                decision_ms, decision_ms + maximum_delay_ms
            )
            if tick.timestamp_ms > decision_ms
        ),
        None,
    )


def label_event_candidates(
    candidates: pd.DataFrame,
    m5: pd.DataFrame,
    tick_store: VerifiedNormalizedTickStore,
    source: Mapping[str, Any],
    execution: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if m5.empty:
        raise ValueError("Cannot label event candidates against empty M5 bars")
    starts_ms = EVENT._timestamp_series_ms(m5["bar_start_utc"])
    ends_ms = EVENT._timestamp_series_ms(m5["bar_end_utc"])
    if np.any(np.diff(starts_ms) < 0) or np.any(ends_ms <= starts_ms):
        raise ValueError("M5 bar timestamps are not ordered valid intervals")
    if not candidates.empty:
        decisions = EVENT._timestamp_series_ms(candidates["feature_time_utc"])
        if bool(((decisions < starts_ms[0]) | (decisions >= ends_ms[-1])).any()):
            raise ValueError("Candidate decisions fall outside the M5 range")
    rows: list[dict[str, Any]] = []
    rejections: dict[str, int] = {}

    def reject(reason: str) -> None:
        rejections[reason] = rejections.get(reason, 0) + 1

    for candidate in candidates.itertuples(index=False):
        decision_ms = EVENT._timestamp_ms(candidate.feature_time_utc)
        entry_tick = _first_quote_after(
            tick_store, decision_ms, int(source["maximum_entry_delay_ms"])
        )
        if entry_tick is None:
            reject("NO_TIMELY_ENTRY_QUOTE")
            continue
        direction = str(candidate.direction)
        spread = float(entry_tick.ask - entry_tick.bid)
        if spread < 0.0:
            raise ValueError("Crossed quote found at event entry")
        stop_distance = max(
            float(candidate.raw_stop_distance),
            float(execution["minimum_stop_distance_usd"]),
        )
        if stop_distance > float(execution["maximum_stop_distance_usd"]):
            reject("STOP_CEILING_EXCEEDED")
            continue
        if spread > float(execution["maximum_entry_spread_usd"]):
            reject("SPREAD_CEILING_EXCEEDED")
            continue
        if spread / stop_distance > float(execution["maximum_entry_spread_r"]):
            reject("SPREAD_R_EXCEEDED")
            continue
        entry = float(entry_tick.ask if direction == "LONG" else entry_tick.bid)
        stop = entry - stop_distance if direction == "LONG" else entry + stop_distance
        target = (
            entry + float(candidate.target_r) * stop_distance
            if direction == "LONG"
            else entry - float(candidate.target_r) * stop_distance
        )
        entry_ms = int(entry_tick.timestamp_ms)
        deadline_ms = entry_ms + int(execution["maximum_hold_hours"]) * 3_600_000
        start_index = max(
            0, int(np.searchsorted(starts_ms, entry_ms, side="right") - 1)
        )
        end_index = min(
            len(m5), int(np.searchsorted(starts_ms, deadline_ms, side="right"))
        )
        hit: tuple[Any, float, str] | None = None
        for index in range(start_index, end_index):
            bar = m5.iloc[index]
            if not EVENT._potential_hit(bar, direction, stop, target):
                continue
            scan_start = max(entry_ms, int(starts_ms[index]))
            scan_end = min(deadline_ms, int(ends_ms[index]))
            hit = EVENT.first_threshold_hit(
                tick_store.ticks_between(scan_start, scan_end),
                direction,
                stop,
                target,
                scan_start,
                scan_end,
            )
            if hit is not None:
                break
        if hit is None:
            grace = int(source["exit_tick_grace_ms"])
            exit_tick = next(
                tick_store.ticks_between(deadline_ms, deadline_ms + grace), None
            )
            if exit_tick is None:
                reject("NO_TIMEOUT_QUOTE")
                continue
            exit_price = float(
                exit_tick.bid if direction == "LONG" else exit_tick.ask
            )
            exit_reason = "MAX_HOLD"
        else:
            exit_tick, exit_price, exit_reason = hit
        sign = 1.0 if direction == "LONG" else -1.0
        ounces = float(execution["ounces"])
        risk_usd = stop_distance * ounces
        gross_pnl = sign * (float(exit_price) - entry) * ounces
        holding_days = max(
            0.0, (int(exit_tick.timestamp_ms) - entry_ms) / 86_400_000.0
        )
        holding_cost = holding_days * float(execution["holding_cost_per_24h_usd"])
        baseline_net = gross_pnl - float(execution["ticket_cost_usd"]) - holding_cost
        stress_net = baseline_net - risk_usd * float(execution["stress_slippage_r"])
        rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "policy_id": candidate.policy_id,
                "event_id": candidate.event_id,
                "event_type": candidate.event_type,
                "mode": candidate.mode,
                "regime": candidate.regime,
                "direction": direction,
                "signal_time": candidate.feature_time_utc,
                "entry_time": pd.Timestamp(entry_ms, unit="ms", tz="UTC"),
                "exit_time": pd.Timestamp(
                    int(exit_tick.timestamp_ms), unit="ms", tz="UTC"
                ),
                "entry_price": entry,
                "exit_price": float(exit_price),
                "stop": stop,
                "target": target,
                "risk_usd": risk_usd,
                "entry_spread_usd": spread,
                "entry_spread_r": spread / stop_distance,
                "gross_r": gross_pnl / risk_usd,
                "baseline_net_r": baseline_net / risk_usd,
                "stress_net_r": stress_net / risk_usd,
                "holding_minutes": (
                    int(exit_tick.timestamp_ms) - entry_ms
                )
                / 60_000.0,
                "exit_reason": exit_reason,
            }
        )
    outcomes = pd.DataFrame(rows)
    if not outcomes.empty:
        outcomes = outcomes.sort_values("entry_time", kind="mergesort").reset_index(
            drop=True
        )
    audit = {
        "candidate_rows": int(len(candidates)),
        "outcome_rows": int(len(outcomes)),
        "rejection_rows": int(len(candidates) - len(outcomes)),
        "rejection_counts": dict(sorted(rejections.items())),
        "stop_outcomes": int(
            outcomes["exit_reason"].eq("STOP").sum() if not outcomes.empty else 0
        ),
        "target_outcomes": int(
            outcomes["exit_reason"].eq("TARGET").sum() if not outcomes.empty else 0
        ),
        "max_hold_outcomes": int(
            outcomes["exit_reason"].eq("MAX_HOLD").sum()
            if not outcomes.empty
            else 0
        ),
        "normalized_exact_tick_threshold_ordering": True,
    }
    return outcomes, audit


def build_fomc_regime_candidates(
    m5: pd.DataFrame,
    calendar: pd.DataFrame,
    candidate: Mapping[str, Any],
    base_regime_config: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    h4 = build_regime_h4(m5)
    policy = dict(candidate["policy"])
    if "required_regime" in policy:
        required_regimes = [str(policy.pop("required_regime"))]
    else:
        required_regimes = [str(value) for value in policy.pop("required_regimes")]
    if not required_regimes or len(required_regimes) != len(set(required_regimes)):
        raise ValueError("FOMC required regimes are empty or duplicated")
    generated = EVENT.build_candidates(
        m5, h4, base_regime_config, calendar, [policy]
    )
    future_rows = int(
        (
            generated["regime_feature_time_utc"].notna()
            & generated["regime_feature_time_utc"].gt(generated["feature_time_utc"])
        ).sum()
    )
    if future_rows:
        raise ValueError("Future regime timestamp in FOMC candidate ledger")
    selected = generated.loc[generated["regime"].isin(required_regimes)].copy()
    prohibited = {
        column
        for column in selected.columns
        if any(
            token in column.lower()
            for token in ("pnl", "profit", "exit_", "stress_", "winner")
        )
    }
    if prohibited:
        raise ValueError(f"Outcome-like FOMC candidate columns: {sorted(prohibited)}")
    manifest = {
        "official_event_rows": int(len(calendar)),
        "all_impulse_candidate_rows": int(len(generated)),
        "required_regimes": required_regimes,
        "selected_regime_candidate_rows": int(len(selected)),
        "rows_by_regime": {
            str(key): int(value)
            for key, value in generated["regime"].value_counts().sort_index().items()
        },
        "future_regime_feature_rows": future_rows,
        "candidate_sha256": candidate_digest(selected),
        "contains_outcomes": False,
    }
    return selected.reset_index(drop=True), manifest


def build_regime_h4(m5: pd.DataFrame) -> pd.DataFrame:
    return DATA.aggregate_complete_bars(m5, 240, "H4")


def run_fomc_regime(
    m5: pd.DataFrame,
    replay_root: Path,
    calendar: pd.DataFrame,
    candidate: Mapping[str, Any],
    base_regime_config: Mapping[str, Any],
    source: Mapping[str, Any],
    execution: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    candidates, manifest = build_fomc_regime_candidates(
        m5, calendar, candidate, base_regime_config
    )
    store = VerifiedNormalizedTickStore(replay_root, str(source["symbol"]))
    outcomes, audit = label_event_candidates(
        candidates, m5, store, source, execution
    )
    if not outcomes.empty:
        outcomes = outcomes.copy()
        outcomes["source_candidate_id"] = outcomes["candidate_id"].astype(str)
        outcomes["candidate_id"] = str(candidate["candidate_id"])
        outcomes["source_policy_id"] = str(candidate["policy"]["policy_id"])
    return outcomes, manifest, audit


def standardize_trades(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if result.empty:
        return result
    for column in ("entry_time", "exit_time", "signal_time"):
        if column in result:
            result[column] = pd.to_datetime(result[column], utc=True, errors="raise")
    return result.sort_values("entry_time", kind="mergesort").reset_index(drop=True)


def profit_factor(values: pd.Series) -> float:
    gains = float(values.loc[values > 0.0].sum())
    losses = float(-values.loc[values < 0.0].sum())
    if losses == 0.0:
        return float("inf") if gains > 0.0 else 0.0
    return gains / losses


def closed_drawdown(values: pd.Series) -> float:
    equity = np.concatenate(
        ([0.0], values.fillna(0.0).to_numpy(dtype=float).cumsum())
    )
    peaks = np.maximum.accumulate(equity)
    return float(np.max(peaks - equity)) if len(equity) else 0.0


def daily_values(trades: pd.DataFrame, source_days: pd.DatetimeIndex) -> pd.Series:
    if trades.empty:
        return pd.Series(0.0, index=source_days, dtype=float)
    observed = trades.assign(
        source_day=pd.to_datetime(trades["entry_time"], utc=True).dt.floor("D")
    ).groupby("source_day", sort=True)["stress_net_r"].sum()
    return observed.reindex(source_days, fill_value=0.0).astype(float)


def one_sided_daily_pvalue(
    trades: pd.DataFrame, source_days: pd.DatetimeIndex
) -> float:
    values = daily_values(trades, source_days).to_numpy(dtype=float)
    if len(values) < 2 or float(values.mean()) <= 0.0:
        return 1.0
    standard = float(values.std(ddof=1))
    if standard == 0.0:
        return 0.0
    result = stats.ttest_1samp(values, 0.0, alternative="greater")
    return float(result.pvalue) if np.isfinite(result.pvalue) else 1.0


def holm_adjust(pvalues: Mapping[str, float]) -> dict[str, float]:
    ordered = sorted(pvalues, key=lambda key: (float(pvalues[key]), key))
    count = len(ordered)
    running = 0.0
    adjusted: dict[str, float] = {}
    for rank, key in enumerate(ordered):
        running = max(running, (count - rank) * float(pvalues[key]))
        adjusted[key] = min(1.0, running)
    return adjusted


def summarize(
    candidate_id: str,
    trades: pd.DataFrame,
    gate: Mapping[str, Any],
    source_days: pd.DatetimeIndex,
    event_count: int | None = None,
) -> dict[str, Any]:
    values = (
        trades["stress_net_r"].astype(float)
        if not trades.empty
        else pd.Series(dtype=float)
    )
    dated = (
        trades.assign(entry_time=pd.to_datetime(trades["entry_time"], utc=True))
        if not trades.empty
        else trades
    )
    yearly = (
        dated.assign(year=dated["entry_time"].dt.year)
        .groupby("year", sort=True)["stress_net_r"]
        .sum()
        if not trades.empty
        else pd.Series(dtype=float)
    )
    monthly = (
        dated.assign(month=dated["entry_time"].dt.to_period("M"))
        .groupby("month", sort=True)["stress_net_r"]
        .sum()
        if not trades.empty
        else pd.Series(dtype=float)
    )
    remove_count = min(int(gate["top_winners_removed"]), len(values))
    removed = values.drop(values.nlargest(remove_count).index)
    result = {
        "candidate_id": candidate_id,
        "trades": int(len(trades)),
        "source_days": int(len(source_days)),
        "trades_per_source_day": len(trades) / len(source_days)
        if len(source_days)
        else 0.0,
        "stress_net_r": float(values.sum()),
        "stress_pf": profit_factor(values),
        "average_stress_r": float(values.mean()) if len(values) else 0.0,
        "closed_drawdown_r": closed_drawdown(values),
        "positive_active_month_share": float((monthly > 0.0).mean())
        if len(monthly)
        else 0.0,
        "positive_active_year_share": float((yearly > 0.0).mean())
        if len(yearly)
        else 0.0,
        "top_winners_removed_stress_net_r": float(removed.sum()),
        "daily_pvalue": one_sided_daily_pvalue(trades, source_days),
    }
    if event_count is not None:
        result["event_count"] = int(event_count)
        result["event_participation"] = (
            len(trades) / event_count if event_count else 0.0
        )
    return result


def gate_checks(
    metrics: Mapping[str, Any], gate: Mapping[str, Any], holm_pvalue: float
) -> dict[str, bool]:
    checks = {
        "minimum_trades": int(metrics["trades"]) >= int(gate["minimum_trades"]),
        "minimum_stress_pf": float(metrics["stress_pf"])
        >= float(gate["minimum_stress_pf"]),
        "minimum_average_stress_r": float(metrics["average_stress_r"])
        >= float(gate["minimum_average_stress_r"]),
        "maximum_closed_drawdown_r": float(metrics["closed_drawdown_r"])
        <= float(gate["maximum_closed_drawdown_r"]),
        "minimum_positive_active_year_share": float(
            metrics["positive_active_year_share"]
        )
        >= float(gate["minimum_positive_active_year_share"]),
        "top_winners_removed_positive": float(
            metrics["top_winners_removed_stress_net_r"]
        )
        > 0.0,
        "maximum_holm_pvalue": float(holm_pvalue)
        <= float(gate["maximum_holm_pvalue"]),
    }
    if "minimum_positive_active_month_share" in gate:
        checks["minimum_positive_active_month_share"] = float(
            metrics["positive_active_month_share"]
        ) >= float(gate["minimum_positive_active_month_share"])
    if "minimum_event_participation" in gate:
        checks["minimum_event_participation"] = float(
            metrics.get("event_participation", 0.0)
        ) >= float(gate["minimum_event_participation"])
    return checks


def entry_overlap_fraction(
    first: pd.DataFrame, second: pd.DataFrame, window_minutes: float
) -> float:
    if first.empty or second.empty:
        return 0.0
    left, right = (first, second) if len(first) <= len(second) else (second, first)
    right_times = {
        direction: np.sort(
            pd.to_datetime(group["entry_time"], utc=True)
            .dt.tz_localize(None)
            .to_numpy(dtype="datetime64[ns]")
        )
        for direction, group in right.groupby("direction", sort=False)
    }
    window = np.timedelta64(int(round(window_minutes * 60.0)), "s")
    matches = 0
    for row in left.itertuples(index=False):
        candidates = right_times.get(str(row.direction))
        if candidates is None or len(candidates) == 0:
            continue
        value = np.datetime64(pd.Timestamp(row.entry_time).tz_convert(None))
        index = int(np.searchsorted(candidates, value, side="left"))
        neighbors = candidates[max(0, index - 1) : min(len(candidates), index + 1)]
        if len(neighbors) and np.min(np.abs(neighbors - value)) <= window:
            matches += 1
    return matches / len(left)


def daily_pnl_correlation(
    first: pd.DataFrame,
    second: pd.DataFrame,
    source_days: pd.DatetimeIndex,
) -> float:
    left = daily_values(first, source_days)
    right = daily_values(second, source_days)
    if float(left.std(ddof=0)) == 0.0 or float(right.std(ddof=0)) == 0.0:
        return 0.0
    value = float(left.corr(right))
    return value if np.isfinite(value) else 0.0


def pairwise_independence(
    ledgers: Mapping[str, pd.DataFrame],
    economic_survivors: list[str],
    source_days: pd.DatetimeIndex,
    settings: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for first_index, first in enumerate(economic_survivors):
        for second in economic_survivors[first_index + 1 :]:
            overlap = entry_overlap_fraction(
                ledgers[first],
                ledgers[second],
                float(settings["entry_overlap_window_minutes"]),
            )
            correlation = daily_pnl_correlation(
                ledgers[first], ledgers[second], source_days
            )
            checks = {
                "maximum_entry_overlap_fraction": overlap
                <= float(settings["maximum_entry_overlap_fraction"]),
                "maximum_absolute_daily_pnl_correlation": abs(correlation)
                <= float(settings["maximum_absolute_daily_pnl_correlation"]),
            }
            rows.append(
                {
                    "first_candidate_id": first,
                    "second_candidate_id": second,
                    "entry_overlap_fraction": overlap,
                    "daily_pnl_correlation": correlation,
                    "checks": checks,
                    "independence_pass": all(checks.values()),
                }
            )
    return rows


def select_distinct_survivors(
    economic_survivors: list[str],
    pairwise: list[dict[str, Any]],
    fixed_order: list[str],
    mechanism_families: Mapping[str, str] | None = None,
) -> list[str]:
    lookup = {
        frozenset((row["first_candidate_id"], row["second_candidate_id"])): bool(
            row["independence_pass"]
        )
        for row in pairwise
    }
    survivors = set(economic_survivors)
    selected: list[str] = []
    selected_families: set[str] = set()
    for candidate_id in fixed_order:
        if candidate_id not in survivors:
            continue
        family = (
            str(mechanism_families[candidate_id])
            if mechanism_families is not None
            else candidate_id
        )
        if family in selected_families:
            continue
        if all(lookup.get(frozenset((candidate_id, prior)), False) for prior in selected):
            selected.append(candidate_id)
            selected_families.add(family)
    return selected


def candidate_digest(frame: pd.DataFrame) -> str:
    if frame.empty:
        return hashlib.sha256(b"").hexdigest()
    columns = [
        column
        for column in (
            "candidate_id",
            "event_id",
            "feature_time_utc",
            "direction",
            "regime",
        )
        if column in frame
    ]
    text = frame[columns].astype(str).to_csv(index=False, lineterminator="\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
