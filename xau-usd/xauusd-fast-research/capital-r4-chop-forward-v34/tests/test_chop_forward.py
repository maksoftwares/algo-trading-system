from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chop_forward import (  # noqa: E402
    BAR_WIDTH_MS,
    aggregate_capital_quotes,
    dependency_sha256,
    generate_forward_candidates,
    overlay_quote_bars,
)


QUALITY = {
    "minimum_unique_quotes_per_m5": 2,
    "maximum_first_quote_delay_ms": 1000,
    "maximum_last_quote_age_ms": 1000,
    "maximum_internal_quote_gap_ms": 300000,
}


def test_tick_imbalance_resets_cross_bucket_move() -> None:
    base = int(pd.Timestamp("2026-07-20T00:00:00Z").value // 1_000_000)
    offsets = np.array(
        [
            0,
            299000,
            BAR_WIDTH_MS,
            BAR_WIDTH_MS + 299000,
            2 * BAR_WIDTH_MS,
            2 * BAR_WIDTH_MS + 299000,
        ],
        dtype=np.int64,
    )
    mid = np.array([100.0, 101.0, 110.0, 109.0, 109.0, 110.0])
    ticks = pd.DataFrame(
        {
            "tick_time_msc": base + offsets,
            "bid": mid - 0.1,
            "ask": mid + 0.1,
            "spread_price": 0.2,
        }
    )

    bars = aggregate_capital_quotes(
        ticks,
        completed_through=pd.Timestamp("2026-07-20T00:15:00Z"),
        quality=QUALITY,
    )

    assert bars["tick_signed_move"].tolist() == [1.0, -1.0, 1.0]
    assert bars["tick_move_count"].tolist() == [1, 1, 1]
    assert bars["quote_quality_passed"].all()
    assert bars["quote_contiguous_15m"].tolist() == [False, False, True]
    assert bars["tick_imbalance_15m"].iloc[2] == 1.0 / 3.0


def test_incomplete_bar_and_bad_quote_bar_are_not_used() -> None:
    start = pd.Timestamp("2026-07-20T00:00:00Z")
    historical = pd.DataFrame(
        {
            "bar_start_utc": [start],
            "mid_close": [100.0],
            "quote_quality_passed": [False],
            "quote_contiguous_15m": [False],
        }
    )
    bad_quote = pd.DataFrame(
        {
            "bar_start_utc": [start],
            "mid_close": [999.0],
            "quote_quality_passed": [False],
            "quote_contiguous_15m": [False],
        }
    )
    combined = overlay_quote_bars(historical, bad_quote)
    assert combined["mid_close"].tolist() == [100.0]


class _Confirmation:
    @staticmethod
    def independent_signal_mask_direction(
        frame: pd.DataFrame, mechanic: str, params: dict[str, Any]
    ) -> tuple[pd.Series, pd.Series]:
        del mechanic, params
        return (
            pd.Series(True, index=frame.index),
            pd.Series(1, index=frame.index),
        )


@dataclass
class _Frozen:
    r4_config: dict[str, Any]
    confirmation_module: Any = _Confirmation()


def test_forward_candidates_require_three_quality_bars_and_deduplicate() -> None:
    times = pd.date_range("2026-07-20T00:05:00Z", periods=2, freq="5min")
    frame = pd.DataFrame(
        {
            "bar_end_utc": times,
            "quote_quality_passed": [True, True],
            "quote_contiguous_15m": [False, True],
            "risk_atr": [10.0, 11.0],
        }
    )
    components = []
    for priority, attempt in ((1, 10), (2, 20)):
        components.append(
            {
                "priority": priority,
                "origin_attempt": attempt,
                "origin_variant_id": f"variant-{attempt}",
                "mechanic": f"mechanic-{attempt}",
                "geometry_id": "EXTENDED",
                "parameters": {},
            }
        )
    frozen = _Frozen(
        {
            "components": components,
            "geometry": {
                "stop_atr": 1.0,
                "target_r": 2.0,
                "maximum_hold_hours": 12.0,
            },
        }
    )

    candidates = generate_forward_candidates(
        frame,
        frozen,  # type: ignore[arg-type]
        start_inclusive=times[0],
        end_inclusive=times[-1],
    )

    assert len(candidates) == 1
    assert candidates.iloc[0]["origin_attempt"] == 10
    assert candidates.iloc[0]["signal_time_utc"] == times[-1]
    assert not bool(candidates.iloc[0]["economic_outcome_opened"])


def test_package_has_no_broker_action_path() -> None:
    prohibited = ("order_send", "order_check", "TRADE_ACTION", "positions_get")
    for path in [ROOT / "run_shadow.py", ROOT / "src" / "chop_forward.py"]:
        source = path.read_text(encoding="utf-8")
        for token in prohibited:
            assert token not in source


def test_dependency_hash_is_independent_of_text_line_endings(tmp_path: Path) -> None:
    dependency = tmp_path / "rule.py"
    dependency.write_bytes(b"first\nsecond\n")
    lf_hash = dependency_sha256(tmp_path, ["rule.py"])
    dependency.write_bytes(b"first\r\nsecond\r\n")
    crlf_hash = dependency_sha256(tmp_path, ["rule.py"])
    assert crlf_hash == lf_hash
