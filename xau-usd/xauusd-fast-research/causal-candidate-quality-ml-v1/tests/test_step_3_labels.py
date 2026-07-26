from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from step_3_labels import label_one  # noqa: E402
from step_3_sources import SourceDataError  # noqa: E402


class FakeStore:
    def __init__(self, times: list[int], bids: list[float], asks: list[float]) -> None:
        self.values = (
            np.array(times, dtype=np.int64),
            np.array(bids, dtype=float),
            np.array(asks, dtype=float),
        )
        self.start_ms = 0
        self.end_ms = 20_000_000

    def first_quote_at_or_after(
        self, timestamp_ms: int, maximum_gap_ms: int
    ) -> tuple[int, float, float] | None:
        index = int(np.searchsorted(self.values[0], timestamp_ms, side="left"))
        if (
            index >= len(self.values[0])
            or self.values[0][index] > timestamp_ms + maximum_gap_ms
        ):
            return None
        return (
            int(self.values[0][index]),
            float(self.values[1][index]),
            float(self.values[2][index]),
        )

    def hours_between(self, start_ms: int, end_ms: int):
        del start_ms, end_ms
        yield 0

    def load_hour(self, hour_key: int):
        del hour_key
        return self.values


@pytest.fixture
def contract() -> dict:
    path = PACKAGE_ROOT / "config" / "step_2b_dataset_feature_contract_v1.json"
    return json.loads(path.read_text(encoding="utf-8"))["label_contract"]


def candidate(**changes):
    row = {
        "candidate_id": "C1",
        "action_row_id": "",
        "family_id": "R4_CHOP",
        "direction": "LONG",
        "entry_eligible_time": pd.Timestamp(1_000, unit="ms", tz="UTC"),
        "planned_stop_price": 2.0,
        "target_mode": "R_MULTIPLE",
        "target_r": 2.0,
        "maximum_hold_mode": "FIXED",
        "label_observation_cap_minutes": 1.0,
    }
    row.update(changes)
    return row


def test_long_uses_ask_entry_bid_exit_and_does_not_double_charge_spread(
    contract,
) -> None:
    store = FakeStore([1_000, 2_000], [99.0, 104.0], [100.0, 105.0])
    result = label_one(candidate(), store=store, label_contract=contract)
    assert result["label_status"] == "RESOLVED_TARGET"
    assert result["entry_price"] == 100.0
    assert result["exit_price"] == 104.0
    assert result["gross_r"] == 2.0
    expected_base_cost = (0.30 + (1_000 / 60_000) / 1440 * 0.35) / 2.0
    assert result["base_cost_r"] == pytest.approx(expected_base_cost)
    assert result["stress_net_r"] == pytest.approx(2.0 - expected_base_cost - 0.05)


def test_stop_retains_observed_gap_slippage(contract) -> None:
    store = FakeStore([1_000, 2_000], [99.5, 97.0], [100.0, 97.5])
    result = label_one(candidate(), store=store, label_contract=contract)
    assert result["label_status"] == "RESOLVED_STOP_SLIPPAGE"
    assert result["exit_price"] == 97.0
    assert result["gross_r"] == -1.5


def test_short_uses_bid_entry_and_ask_exit(contract) -> None:
    store = FakeStore([1_000, 2_000], [100.0, 95.0], [101.0, 96.0])
    row = candidate(direction="SHORT")
    result = label_one(row, store=store, label_contract=contract)
    assert result["entry_price"] == 100.0
    assert result["exit_price"] == 96.0
    assert result["gross_r"] == 2.0


def test_r1_observation_cap_censors_instead_of_forcing_exit(contract) -> None:
    store = FakeStore([1_000, 2_000], [99.9, 100.0], [100.0, 100.1])
    row = candidate(
        family_id="R1_UPTREND",
        maximum_hold_mode="BARRIER_ONLY_NO_TIME_STOP",
        label_observation_cap_minutes=0.1,
    )
    result = label_one(row, store=store, label_contract=contract)
    assert result["label_status"] == "CENSORED_R1_OBSERVATION_CAP"
    assert result["gross_r"] is None
    assert pd.isna(result["exit_price"])


def test_historical_rejection_is_not_an_input_to_label(contract) -> None:
    store = FakeStore([1_000, 2_000], [99.0, 104.0], [100.0, 105.0])
    accepted = label_one(
        candidate(historical_accept_state="ACCEPTED"),
        store=store,
        label_contract=contract,
    )
    rejected = label_one(
        candidate(historical_accept_state="REJECTED"),
        store=store,
        label_contract=contract,
    )
    assert accepted == rejected


def test_corrupt_horizon_read_is_not_reported_as_a_normal_missing_quote(
    contract,
) -> None:
    class CorruptHorizonStore(FakeStore):
        calls = 0

        def first_quote_at_or_after(self, timestamp_ms, maximum_gap_ms):
            self.calls += 1
            if self.calls == 2:
                raise SourceDataError("changed source bytes")
            return super().first_quote_at_or_after(timestamp_ms, maximum_gap_ms)

    store = CorruptHorizonStore([1_000, 2_000], [99.5, 99.5], [100.0, 100.0])
    row = candidate(target_mode="NONE", target_r=np.nan)
    result = label_one(row, store=store, label_contract=contract)
    assert result["label_status"] == "UNRESOLVED_CORRUPT_QUOTE"
