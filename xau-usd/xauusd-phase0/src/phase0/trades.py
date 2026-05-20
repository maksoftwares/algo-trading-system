from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pandas as pd

from phase0.data_contracts import Trade


TRADE_COLUMNS = (
    "expert",
    "symbol",
    "direction",
    "entry_time_utc",
    "exit_time_utc",
    "entry_price",
    "exit_price",
    "stop_loss",
    "take_profit",
    "lots",
    "gross_pnl_usd",
    "costs_usd",
    "net_pnl_usd",
    "r_multiple",
    "exit_reason",
)


def trades_to_dataframe(trades: list[Trade]) -> pd.DataFrame:
    rows = []
    for trade in trades:
        row = asdict(trade)
        metadata = row.pop("metadata", {})
        for key, value in metadata.items():
            row[f"metadata_{key}"] = value
        rows.append(row)
    if not rows:
        return pd.DataFrame(columns=TRADE_COLUMNS)
    return pd.DataFrame(rows)


def write_trades_csv(trades: list[Trade], path: str | Path) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    trades_to_dataframe(trades).to_csv(resolved, index=False)
    return resolved
