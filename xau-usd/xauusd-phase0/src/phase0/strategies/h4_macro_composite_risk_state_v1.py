from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.data_contracts import Signal
from phase0.strategies.base import context_symbol, value_available
from phase0.strategies.h4_macro_composite_risk_state_v0 import (
    H4MacroCompositeRiskStateV0Strategy,
    _setup_metadata,
)


class H4MacroCompositeRiskStateV1Strategy(H4MacroCompositeRiskStateV0Strategy):
    """Research-only fixed macro composite v1 with broader cross-domain vote threshold."""

    name = "h4_macro_composite_risk_state_v1"
    version = "0.1-research-disabled"

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h4 = context["H4"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_day_direction: set[tuple[str, str]] = set()

        for position in range(100, len(h4)):
            row = h4.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            day_direction = (timestamp.strftime("%Y-%m-%d"), str(setup["direction"]))
            if day_direction in used_day_direction:
                continue
            used_day_direction.add(day_direction)

            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H4_MACRO_COMPOSITE_RISK_STATE_V1_{direction}",
                    metadata={**setup, "h4_index": int(position), "signal_day": day_direction[0]},
                )
            )
        return signals

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["close"],
            row["h4_atr14"],
            row["h4_ema40"],
            row["h4_return_6"],
            row["macro_composite_score"],
            row["macro_bull_votes"],
            row["macro_bear_votes"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_ema40 = float(row["h4_ema40"])
        h4_return_6 = float(row["h4_return_6"])
        composite_score = float(row["macro_composite_score"])
        bull_votes = float(row["macro_bull_votes"])
        bear_votes = float(row["macro_bear_votes"])
        if h4_atr <= 0:
            return None

        if (
            composite_score >= 2.0
            and bull_votes >= 3.0
            and close > h4_ema40
            and close > open_price
            and h4_return_6 > 0.0
        ):
            return _setup_metadata(row, "LONG", close)

        if (
            composite_score <= -2.0
            and bear_votes >= 3.0
            and close < h4_ema40
            and close < open_price
            and h4_return_6 < 0.0
        ):
            return _setup_metadata(row, "SHORT", close)

        return None
