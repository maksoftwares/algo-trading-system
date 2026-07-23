import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.research import add_h4_regimes, profit_factor


def config():
    return json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2.json").read_text(encoding="utf-8")
    )


def test_profit_factor():
    assert profit_factor([2.0, -1.0, 1.0]) == 3.0
    assert profit_factor([]) == 0.0


def test_classifier_is_mutually_exclusive_and_causal():
    timestamps = pd.date_range("2010-01-01", periods=2800, freq="h", tz="UTC")
    base = 1.10 + np.linspace(0, 0.08, len(timestamps))
    frame = pd.DataFrame({"timestamp": timestamps})
    for side, offset in (("bid", 0.0), ("ask", 0.0001)):
        frame[f"{side}_open"] = base + offset
        frame[f"{side}_high"] = base + offset + 0.0004
        frame[f"{side}_low"] = base + offset - 0.0004
        frame[f"{side}_close"] = base + offset + 0.0002
    classified, _ = add_h4_regimes(frame, config()["regime_classifier"])
    allowed = {"unsafe", "trend_up", "trend_down", "compression", "chop", "transition"}
    assert set(classified["regime"]).issubset(allowed)
    assert classified["regime"].notna().all()


def test_windows_are_strictly_sequential():
    windows = config()["windows"]
    assert pd.Timestamp(windows["train"][1]) == pd.Timestamp(windows["validation"][0])
    assert pd.Timestamp(windows["validation"][1]) == pd.Timestamp(windows["internal"][0])
    assert pd.Timestamp(windows["internal"][1]) == pd.Timestamp(windows["exam"][0])


def test_specialist_ownership_and_unsafe_no_trade():
    specialists = config()["specialists"]
    assert len({row["specialist_id"] for row in specialists}) == len(specialists)
    assert all(row["owned_regime"] not in {"unsafe", "transition"} for row in specialists)
