from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

import pandas as pd

from phase0.config import ConfigError, ProjectConfig, get_symbol_details, resolve_symbol
from phase0.data_contracts import Direction

PriceSide = Literal["entry", "exit"]


class CostModelError(ConfigError):
    """Raised when a cost model is missing or invalid."""


@dataclass(frozen=True)
class CostModel:
    name: str
    spread_points: float
    spread_price: float
    commission_usd_per_round_turn_lot: float
    slippage_points_entry: float
    slippage_points_exit: float
    point_size: float

    @property
    def entry_slippage_price(self) -> float:
        return self.slippage_points_entry * self.point_size

    @property
    def exit_slippage_price(self) -> float:
        return self.slippage_points_exit * self.point_size


def load_cost_model(
    config: ProjectConfig,
    symbol: str,
    broker: str,
    cost_model: str,
    timestamp_utc: datetime | None = None,
) -> CostModel:
    canonical_symbol = resolve_symbol(config, symbol)
    models = config.cost_models["cost_models"]
    if cost_model not in models:
        raise CostModelError(f"Unknown cost model {cost_model!r}. Add it to config/cost_models.yaml.")

    symbol_details = get_symbol_details(config, canonical_symbol)
    point_size = float(symbol_details["point_size"])
    spread_points = get_spread_points(config, canonical_symbol, broker, timestamp_utc, cost_model)
    model = models[cost_model]
    return CostModel(
        name=cost_model,
        spread_points=spread_points,
        spread_price=spread_points * point_size,
        commission_usd_per_round_turn_lot=float(model.get("commission_usd_per_round_turn_lot", 0.0)),
        slippage_points_entry=float(model.get("slippage_points_entry", 0.0)),
        slippage_points_exit=float(model.get("slippage_points_exit", 0.0)),
        point_size=point_size,
    )


def get_spread_points(
    config: ProjectConfig,
    symbol: str,
    broker: str,
    timestamp_utc: datetime | None,
    cost_model: str,
) -> float:
    measured = _measured_spread_points(config, symbol, broker, timestamp_utc, cost_model)
    if measured is not None:
        return measured

    canonical_symbol = resolve_symbol(config, symbol)
    model = config.cost_models["cost_models"].get(cost_model)
    if model is None:
        raise CostModelError(f"Unknown cost model {cost_model!r}.")

    spreads = model.get("spread_points", {})
    if canonical_symbol not in spreads:
        raise CostModelError(
            f"Cost model {cost_model!r} has no spread_points entry for symbol {canonical_symbol}."
        )
    spread_points = float(spreads[canonical_symbol])
    if spread_points < 0:
        raise CostModelError(f"Configured spread points must be non-negative, got {spread_points}.")
    return spread_points


def _measured_spread_points(
    config: ProjectConfig,
    symbol: str,
    broker: str,
    timestamp_utc: datetime | None,
    cost_model: str,
) -> float | None:
    if cost_model not in {"median", "p95"}:
        return None

    path = config.root / "outputs" / "reports" / "cost_model_measured.csv"
    if not path.exists():
        return None

    try:
        measured = pd.read_csv(path)
    except Exception as exc:
        raise CostModelError(f"Failed to read measured cost model {path}: {exc}") from exc

    required = {
        "scope",
        "bucket",
        "symbol",
        "median_spread_points",
        "p95_spread_points",
    }
    missing = sorted(required - set(measured.columns))
    if missing:
        raise CostModelError(
            f"Measured cost model {path} missing required column(s): {', '.join(missing)}."
        )

    canonical_symbol = resolve_symbol(config, symbol)
    candidates = _measured_lookup_order(timestamp_utc)
    value_column = "median_spread_points" if cost_model == "median" else "p95_spread_points"
    for scope, bucket in candidates:
        rows = measured[
            (measured["scope"].astype(str) == scope)
            & (measured["bucket"].astype(str) == str(bucket))
        ].copy()
        if rows.empty:
            continue
        rows = rows[rows["symbol"].astype(str).apply(lambda value: _matches_csv_value(value, canonical_symbol))]
        if rows.empty:
            continue
        if "broker" in rows.columns:
            broker_rows = rows[
                rows["broker"].astype(str).apply(lambda value: _matches_csv_value(value, broker) or value == "all")
            ]
            if not broker_rows.empty:
                rows = broker_rows
            else:
                continue

        value = pd.to_numeric(rows.iloc[0][value_column], errors="coerce")
        if pd.isna(value):
            continue
        spread_points = float(value)
        if spread_points < 0:
            raise CostModelError(
                f"Measured spread points must be non-negative in {path}, got {spread_points}."
            )
        return spread_points
    return None


def _measured_lookup_order(timestamp_utc: datetime | None) -> list[tuple[str, str | int]]:
    if timestamp_utc is None:
        return [("global", "all")]
    timestamp = pd.Timestamp(timestamp_utc)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_convert("UTC")
    return [
        ("hour_utc", int(timestamp.hour)),
        ("day_of_week_utc", timestamp.day_name()),
        ("global", "all"),
    ]


def _matches_csv_value(csv_value: str, wanted: str) -> bool:
    wanted_normalized = wanted.strip().upper()
    values = {part.strip().upper() for part in str(csv_value).split(",") if part.strip()}
    return wanted_normalized in values


def price_from_mid(mid_price: float, direction: Direction, side: PriceSide, spread_price: float) -> float:
    half_spread = spread_price / 2.0
    if direction == "LONG":
        return mid_price + half_spread if side == "entry" else mid_price - half_spread
    if direction == "SHORT":
        return mid_price - half_spread if side == "entry" else mid_price + half_spread
    raise CostModelError(f"Unknown direction {direction!r}.")


def apply_entry_slippage(entry_price: float, direction: Direction, slippage_price: float) -> float:
    if direction == "LONG":
        return entry_price + slippage_price
    if direction == "SHORT":
        return entry_price - slippage_price
    raise CostModelError(f"Unknown direction {direction!r}.")


def apply_exit_slippage(exit_price: float, direction: Direction, slippage_price: float) -> float:
    if direction == "LONG":
        return exit_price - slippage_price
    if direction == "SHORT":
        return exit_price + slippage_price
    raise CostModelError(f"Unknown direction {direction!r}.")


def commission_usd(lots: float, commission_usd_per_round_turn_lot: float) -> float:
    if lots < 0:
        raise CostModelError(f"Lots must be non-negative for commission calculation, got {lots}.")
    return lots * commission_usd_per_round_turn_lot
