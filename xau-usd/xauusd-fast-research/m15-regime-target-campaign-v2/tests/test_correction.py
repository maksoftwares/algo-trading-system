from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from correction import execution_arrays, load_config, verify_next_bar_gap  # noqa: E402


def _load_v1():
    path = RESEARCH_ROOT / "m15-regime-target-campaign-v1" / "src" / "campaign.py"
    spec = importlib.util.spec_from_file_location("m15_v2_test_v1", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["m15_v2_test_v1"] = module
    spec.loader.exec_module(module)
    return module


V1 = _load_v1()


def _mixed_unit_frame() -> pd.DataFrame:
    starts = pd.Series(
        pd.array(
            ["2024-01-02T00:00:00Z", "2024-01-02T00:15:00Z", "2024-01-02T00:30:00Z"],
            dtype="datetime64[ms, UTC]",
        )
    )
    ends = pd.Series(
        pd.array(
            ["2024-01-02T00:15:00Z", "2024-01-02T00:30:00Z", "2024-01-02T00:45:00Z"],
            dtype="datetime64[us, UTC]",
        )
    )
    return pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": ends,
            "timestamp_utc": ends,
            "bid_open": [99.9, 99.9, 100.0],
            "bid_high": [100.1, 101.2, 100.2],
            "bid_low": [99.8, 99.8, 99.8],
            "bid_close": [100.0, 100.8, 100.0],
            "ask_open": [100.0, 100.0, 100.1],
            "ask_high": [100.2, 101.3, 100.3],
            "ask_low": [99.9, 99.9, 99.9],
            "ask_close": [100.1, 100.9, 100.1],
            "atr14": 1.0,
        }
    )


def test_v2_manifest_is_new_and_unchanged_in_definition() -> None:
    config = load_config(ROOT)
    manifest = V1.generate_manifest(config["selection"])
    assert len(manifest) == 1000
    assert manifest["attempt_no"].tolist() == list(range(18120, 19120))
    assert manifest["variant_id"].is_unique


def test_mixed_clock_units_normalize_to_zero_next_bar_gap() -> None:
    arrays = execution_arrays(_mixed_unit_frame())
    assert verify_next_bar_gap(arrays, 0) == 0.0
    assert arrays["starts"][1] == arrays["signals"][0]
    assert arrays["starts"][0] == pd.Timestamp("2024-01-02T00:00:00Z").value


def test_mixed_clock_candidate_executes() -> None:
    arrays = execution_arrays(_mixed_unit_frame())
    execution = load_config(ROOT)["execution"]
    outcome = V1.simulate_trade(arrays, 0, 1, 101.0, 1.0, 1.0, execution)
    assert outcome is not None
    assert outcome["exit_reason"] == "TARGET"
    assert np.isfinite(outcome["stress_net_r"])


def test_signal_must_equal_completed_bar_end() -> None:
    frame = _mixed_unit_frame()
    frame["timestamp_utc"] = pd.Series(
        pd.array(
            [
                "2024-01-02T00:15:00Z",
                "2024-01-02T00:15:00Z",
                "2024-01-02T00:45:00Z",
            ],
            dtype="datetime64[ns, UTC]",
        )
    )
    try:
        execution_arrays(frame)
    except ValueError as exc:
        assert "completed bar end" in str(exc)
    else:
        raise AssertionError("Clock mismatch was accepted")
