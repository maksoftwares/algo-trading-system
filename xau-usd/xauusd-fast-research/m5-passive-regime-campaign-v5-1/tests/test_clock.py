from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from clock import (  # noqa: E402
    activation_gaps_minutes,
    load_config,
    m5_execution_arrays,
    sha256_file,
    utc_nanoseconds,
)


def _load_passive():
    path = RESEARCH_ROOT / "m5-passive-regime-campaign-v5" / "src" / "passive.py"
    spec = importlib.util.spec_from_file_location("m5_passive_v51_test_base", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mixed_units_normalize_to_identical_nanoseconds() -> None:
    expected = 1_262_304_000_000_000_000
    for unit in ("ms", "us", "ns"):
        values = pd.Series(
            pd.to_datetime(["2010-01-01T00:00:00Z"], utc=True).astype(
                f"datetime64[{unit}, UTC]"
            )
        )
        assert int(utc_nanoseconds(values)[0]) == expected


def test_m5_arrays_have_ns_clock_and_positive_duration() -> None:
    starts = pd.Series(
        pd.to_datetime(
            ["2010-01-01T00:00:00Z", "2010-01-01T00:05:00Z"], utc=True
        ).astype("datetime64[ms, UTC]")
    )
    ends = pd.Series(
        pd.to_datetime(
            ["2010-01-01T00:05:00Z", "2010-01-01T00:10:00Z"], utc=True
        ).astype("datetime64[us, UTC]")
    )
    frame = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": ends,
            **{
                column: [100.0, 100.1]
                for column in (
                    "bid_open",
                    "bid_high",
                    "bid_low",
                    "bid_close",
                    "ask_open",
                    "ask_high",
                    "ask_low",
                    "ask_close",
                )
            },
        }
    )
    arrays = m5_execution_arrays(frame)
    assert arrays["starts"][0] == 1_262_304_000_000_000_000
    assert np.all(arrays["ends"] > arrays["starts"])


def test_mixed_unit_activation_gap_is_zero() -> None:
    arrays = {
        "starts": utc_nanoseconds(
            pd.Series(pd.to_datetime(["2010-01-01T00:15:00Z"], utc=True))
        )
    }
    decision = pd.Series(
        pd.to_datetime(["2010-01-01T00:15:00Z"], utc=True).astype(
            "datetime64[us, UTC]"
        )
    )
    gaps = activation_gaps_minutes(arrays, utc_nanoseconds(decision))
    assert gaps.tolist() == [0.0]


def test_manifest_is_byte_identical_to_v5(tmp_path: Path) -> None:
    config = load_config(ROOT)
    passive = _load_passive()
    generated = tmp_path / "manifest.csv"
    passive.generate_manifest(config["selection"]).to_csv(
        generated, index=False, lineterminator="\n"
    )
    assert sha256_file(generated) == config["base"]["unchanged_manifest_sha256"]
