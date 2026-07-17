from __future__ import annotations

from dataclasses import dataclass

import pytest

from foundation import (
    AcquisitionRefused,
    batch_request,
    cost_request,
    estimate_costs,
    load_config,
    require_api_key,
    submit_authorized,
)


@dataclass
class FakeJob:
    id: str


class FakeMetadata:
    def __init__(self, costs: dict[str, float]) -> None:
        self.costs = costs
        self.requests: list[dict] = []

    def get_cost(self, **request: object) -> float:
        self.requests.append(request)
        return self.costs[str(request["schema"])]


class FakeBatch:
    def __init__(self) -> None:
        self.requests: list[dict] = []

    def submit_job(self, **request: object) -> FakeJob:
        self.requests.append(request)
        return FakeJob(id="job-123")


class FakeClient:
    def __init__(self, costs: dict[str, float]) -> None:
        self.metadata = FakeMetadata(costs)
        self.batch = FakeBatch()


def config() -> dict:
    return load_config()


def client(cost: float = 12.5) -> FakeClient:
    return FakeClient({schema: cost for schema in config()["source"]["estimate_schemas"]})


def test_estimate_is_read_only_and_covers_frozen_schemas() -> None:
    fake = client()
    result = estimate_costs(fake, config())
    assert [row["schema"] for row in result["estimates"]] == config()["source"]["estimate_schemas"]
    assert len(fake.metadata.requests) == 5
    assert fake.batch.requests == []
    assert result["submitted"] is False


def test_missing_api_key_is_refused() -> None:
    with pytest.raises(AcquisitionRefused, match="DATABENTO_API_KEY"):
        require_api_key(config(), {})


def test_execute_requires_positive_explicit_cap() -> None:
    fake = client()
    with pytest.raises(AcquisitionRefused, match="positive"):
        submit_authorized(fake, config(), schema="tbbo", max_cost_usd=0.0, execute=True)
    assert fake.metadata.requests == []
    assert fake.batch.requests == []


def test_execute_requires_explicit_flag() -> None:
    fake = client()
    with pytest.raises(AcquisitionRefused, match="explicit"):
        submit_authorized(fake, config(), schema="tbbo", max_cost_usd=20.0, execute=False)
    assert fake.batch.requests == []


def test_estimate_above_cap_cannot_submit() -> None:
    fake = client(25.01)
    with pytest.raises(AcquisitionRefused, match="exceeds"):
        submit_authorized(fake, config(), schema="tbbo", max_cost_usd=25.0, execute=True)
    assert len(fake.metadata.requests) == 1
    assert fake.batch.requests == []


def test_authorized_submit_uses_exact_frozen_request() -> None:
    fake = client(24.99)
    result = submit_authorized(fake, config(), schema="tbbo", max_cost_usd=25.0, execute=True)
    assert fake.metadata.requests == [cost_request(config(), "tbbo")]
    assert fake.batch.requests == [batch_request(config(), "tbbo")]
    assert result["job"] == {"id": "job-123"}
    assert result["submitted"] is True
    assert result["automatic_download"] is False


def test_unfrozen_schema_is_refused_before_vendor_call() -> None:
    fake = client()
    with pytest.raises(AcquisitionRefused, match="not in the frozen"):
        submit_authorized(fake, config(), schema="mbo", max_cost_usd=25.0, execute=True)
    assert fake.metadata.requests == []
    assert fake.batch.requests == []


def test_research_result_cannot_authorize_execution() -> None:
    controls = config()["research_controls"]
    assert controls["research_only"] is True
    assert controls["python_predictions_authorized"] is False
    assert controls["ea_consumption_authorized"] is False
    assert controls["broker_action_authorized"] is False
