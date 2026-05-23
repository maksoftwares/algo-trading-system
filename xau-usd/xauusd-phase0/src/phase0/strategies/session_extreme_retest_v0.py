from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.indicators import atr
from phase0.strategies.base import copy_context, require_frame
from phase0.strategies.breakout_retest import BreakoutRetestStrategy


class SessionExtremeRetestV0Strategy(BreakoutRetestStrategy):
    """Disabled research strategy for the locked session-extreme retest v0 hypothesis."""

    name = "session_extreme_retest_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], 14)

        bar_starts = _bar_start_times(m5)
        day_key = bar_starts.dt.strftime("%Y-%m-%d")
        start_minutes = bar_starts.dt.hour * 60 + bar_starts.dt.minute
        highs = pd.to_numeric(m5["high"], errors="coerce")
        lows = pd.to_numeric(m5["low"], errors="coerce")

        asia_mask = (start_minutes >= 0) & (start_minutes < 6 * 60)
        london_mask = (start_minutes >= 7 * 60) & (start_minutes < 11 * 60)
        m5["session_retest_day"] = day_key
        m5["bar_start_minute_utc"] = start_minutes
        m5["asia_high"] = day_key.map(highs.loc[asia_mask].groupby(day_key[asia_mask]).max())
        m5["asia_low"] = day_key.map(lows.loc[asia_mask].groupby(day_key[asia_mask]).min())
        m5["london_high"] = day_key.map(highs.loc[london_mask].groupby(day_key[london_mask]).max())
        m5["london_low"] = day_key.map(lows.loc[london_mask].groupby(day_key[london_mask]).min())
        context["M5"] = m5
        return context

    def _bar_arrays(self, m5: pd.DataFrame) -> dict[str, Any]:
        return {
            "timestamp": m5["timestamp_utc"].to_numpy(),
            "open": m5["open"].to_numpy(),
            "high": m5["high"].to_numpy(),
            "low": m5["low"].to_numpy(),
            "close": m5["close"].to_numpy(),
            "atr14": m5["atr14"].to_numpy(),
            "bar_start_minute_utc": m5["bar_start_minute_utc"].to_numpy(),
            "asia_high": m5["asia_high"].to_numpy(),
            "asia_low": m5["asia_low"].to_numpy(),
            "london_high": m5["london_high"].to_numpy(),
            "london_low": m5["london_low"].to_numpy(),
        }

    def _candidate_levels_from_arrays(
        self,
        arrays: dict[str, Any],
        position: int,
        direction: str,
        point_size: float,
    ) -> list[dict[str, Any]]:
        del point_size
        timestamp = arrays["timestamp"][position]
        start_minute = int(arrays["bar_start_minute_utc"][position])
        raw: list[tuple[str, Any, Any]] = []
        if direction == "LONG":
            if start_minute >= 7 * 60:
                raw.append(("asia_high", arrays["asia_high"][position], timestamp))
            if start_minute >= 13 * 60 + 30:
                raw.append(("london_high", arrays["london_high"][position], timestamp))
        else:
            if start_minute >= 7 * 60:
                raw.append(("asia_low", arrays["asia_low"][position], timestamp))
            if start_minute >= 13 * 60 + 30:
                raw.append(("london_low", arrays["london_low"][position], timestamp))
        return [
            {"level_kind": kind, "level_price": float(price), "level_time_utc": level_time}
            for kind, price, level_time in raw
            if pd.notna(price) and pd.notna(level_time)
        ]


def _bar_start_times(frame: pd.DataFrame) -> pd.Series:
    if "bar_start_utc" in frame:
        starts = pd.to_datetime(frame["bar_start_utc"], utc=True, errors="coerce")
        if not starts.isna().all():
            return starts
    return pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce") - pd.Timedelta(minutes=5)
