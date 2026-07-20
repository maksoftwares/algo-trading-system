from __future__ import annotations

import pandas as pd


def add_simulator_aliases(candidates: pd.DataFrame) -> pd.DataFrame:
    required = (
        "impulse_update_imbalance",
        "impulse_displacement_price",
    )
    missing = [column for column in required if column not in candidates.columns]
    if missing:
        raise ValueError(f"V30 simulator alias source is missing: {missing}")
    output = candidates.copy()
    output["signed_update_imbalance"] = output["impulse_update_imbalance"]
    output["displacement_price"] = output["impulse_displacement_price"]
    if len(output) != len(candidates) or not output.index.equals(candidates.index):
        raise ValueError("V30 simulator alias changed candidate row identity")
    return output
