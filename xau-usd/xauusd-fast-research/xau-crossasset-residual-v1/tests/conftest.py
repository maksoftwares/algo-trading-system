import sys
from pathlib import Path

import numpy as np
import pandas as pd

LANE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE / "src"))

BASE_TS = 1_704_067_200_000  # 2024-01-01T00:00:00Z
UTC_DATE = "2024-01-01"


def bars(times, base=100.0):
    return pd.DataFrame({"timestamp_ms": times, "close": [base + i for i in range(len(times))]})


def synthetic_returns(n=3100):
    rng = np.random.default_rng(689988)
    xag = rng.normal(0, .001, n)
    eur = rng.normal(0, .001, n)
    jpy = rng.normal(0, .001, n)
    noise = rng.normal(0, .0001, n)
    xau = .00001 + .7 * xag + .2 * eur - .1 * jpy + noise
    return pd.DataFrame({"timestamp_ms": BASE_TS + np.arange(n, dtype=np.int64) * 300_000, "r_xau": xau, "r_xag": xag, "r_eurusd": eur, "r_usdjpy": jpy})


def model_rows(zs):
    return pd.DataFrame([{"timestamp_ms": BASE_TS + i * 300_000, "chronological_segment": "DEVELOPMENT", "residual_z": z, "r_xau": 0.0, "predicted_r_xau": 0.0, "residual": 0.0, "beta_xag": 0.0, "beta_eurusd": 0.0, "beta_usdjpy": 0.0, "condition_number": 1.0} for i, z in enumerate(zs)])


def tick_frame(rows):
    return pd.DataFrame([{"timestamp_msc": BASE_TS + int(offset), "bid": float(bid), "ask": float(ask), "spread": float(ask) - float(bid), "source_sequence": sequence} for offset, sequence, bid, ask in rows])


def exit_parameters(**overrides):
    values = {"direction": "LONG", "entry_price": 100.0, "risk": 1.0, "stop": 99.0, "target": 101.5, "convergence_ms": 2**63 - 1, "convergence_z": float("nan"), "expiry_ms": 2**63 - 1, "force_ms": 2**63 - 1, "utc_date": UTC_DATE}
    values.update(overrides)
    return values
