from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from ml_topup import evaluate_candidate, status_snapshot


def config() -> dict:
    return {
        "ml_topup": {
            "eligible_source_ids": ["R3_COMPRESSION"],
            "maximum_feature_bar_age_minutes": 10,
        }
    }


def candidate(source_id: str = "R3_COMPRESSION") -> SimpleNamespace:
    return SimpleNamespace(
        candidate_id="candidate-1",
        source_id=source_id,
        initial_risk_usd=5.0,
        scheduled_at=datetime(2026, 7, 29, 12, tzinfo=UTC),
        direction="LONG",
        sleeve_type="CORE",
    )


def test_model_prepare_failure_is_baseline_only_and_durable() -> None:
    state: dict = {}
    result = evaluate_candidate(
        {
            "ready": False,
            "reason": "ML_RUNTIME_PREPARE_FAILED",
            "detail": "test failure",
        },
        config(),
        state,
        candidate(),
        datetime(2026, 7, 29, 12, tzinfo=UTC),
    )
    assert result["topup"] is False
    assert result["reason"] == "ML_RUNTIME_PREPARE_FAILED"
    assert state["ml_topup"]["score_history"] == []
    assert state["ml_topup"]["decisions"]["candidate-1"] == result


def test_ineligible_source_is_never_scored() -> None:
    state: dict = {}
    result = evaluate_candidate(
        {"ready": True},
        config(),
        state,
        candidate("R1_BOX"),
        datetime(2026, 7, 29, 12, tzinfo=UTC),
    )
    assert result["topup"] is False
    assert result["reason"] == "SOURCE_NOT_HISTORICALLY_RISK_ELIGIBLE"


def test_unexpected_scoring_exception_is_baseline_only() -> None:
    state: dict = {}
    result = evaluate_candidate(
        {
            "ready": True,
            "serving": SimpleNamespace(
                score_candidate=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    KeyError("broken model")
                )
            ),
            "bundle": {
                "historical_oos_score_reference": [0.0],
            },
            "feature_bars": object(),
        },
        config(),
        state,
        candidate(),
        datetime(2026, 7, 29, 12, tzinfo=UTC),
    )
    assert result["topup"] is False
    assert result["reason"] == "MODEL_SCORING_FAILED"
    assert state["ml_topup"]["score_history"] == []


def test_status_reports_baseline_only_failure_policy() -> None:
    status = status_snapshot(
        {"ready": False, "reason": "TEST"},
        {"ml_topup": {"decisions": {}, "orders": {}}},
    )
    assert status["ready"] is False
    assert status["failure_policy"] == "BASELINE_ONLY"
