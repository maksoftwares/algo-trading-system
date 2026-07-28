from __future__ import annotations

from eurusd_regime_specialists import prospective_neutral_validation_v1_2 as module


def _result(
    *,
    economic: bool,
    same_day: bool,
    temporal: bool,
    status: str = "REJECTED_WITHOUT_RETUNING",
) -> dict:
    return {
        "schema_version": "v1_1",
        "status": status,
        "gate_results": {
            "minimum_closed_trades": economic,
            "profit_factor": economic,
            "oracle_precision": same_day,
            "oracle_precision_lift": same_day,
            "oracle_random_side_test": same_day,
            **{key: temporal for key in module.TEMPORAL_CHECKS},
        },
        "controlled_demo_ready": False,
    }


def test_profitable_strategy_can_be_reviewed_without_imitation_claim() -> None:
    result = module.classify_validation_result(
        _result(economic=True, same_day=False, temporal=False)
    )
    assert result["status"] == "INDEPENDENT_PROFITABILITY_REVIEW_REQUIRED"
    assert result["profitability_review_allowed"] is True
    assert result["same_day_regime_review_allowed"] is False
    assert result["oracle_imitation_claim_allowed"] is False
    assert result["controlled_demo_ready"] is False


def test_same_day_and_full_temporal_claims_are_separate() -> None:
    same_day = module.classify_validation_result(
        _result(economic=True, same_day=True, temporal=False)
    )
    assert same_day["status"] == (
        "INDEPENDENT_SAME_DAY_REGIME_REVIEW_REQUIRED"
    )
    assert same_day["same_day_regime_review_allowed"] is True
    assert same_day["oracle_imitation_claim_allowed"] is False

    full = module.classify_validation_result(
        _result(economic=True, same_day=True, temporal=True)
    )
    assert full["status"] == (
        "INDEPENDENT_FULL_ORACLE_IMITATION_REVIEW_REQUIRED"
    )
    assert full["oracle_imitation_claim_allowed"] is True


def test_immature_status_stays_immature_and_never_authorizes_demo() -> None:
    result = module.classify_validation_result(
        _result(
            economic=False,
            same_day=False,
            temporal=False,
            status="ACCUMULATING_PROSPECTIVE_EVIDENCE",
        )
    )
    assert result["status"] == "ACCUMULATING_PROSPECTIVE_EVIDENCE"
    assert result["profitability_review_allowed"] is False
    assert result["controlled_demo_ready"] is False


def test_lock_verifies_after_preregistration() -> None:
    checked = module.verify_lock()
    relative = module.CONFIG_PATH.relative_to(module.PACKAGE_ROOT).as_posix()
    assert relative in checked
