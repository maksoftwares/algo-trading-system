from __future__ import annotations

from pathlib import Path

import pandas as pd

import validate_prospective_neutral_inventory_formal_inference as formal


def _counts(total: int = 90) -> dict:
    return {
        "closed_trades": total,
        "by_clock": {"0005": 30, "0605": 30, "1205": 30},
        "by_side": {"LONG": 45, "SHORT": 45},
    }


def _closed(values: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "entry_time_utc": pd.date_range(
                "2027-01-01T00:05:00Z",
                periods=len(values),
                freq="D",
            ),
            "r": values,
            "extra_half_pip_stress_r": [
                value - 0.5 / 6.0 for value in values
            ],
        }
    )


def test_exact_full_year_boundary_does_not_open_early() -> None:
    early = formal.formal_readiness(
        "2027-07-01T00:00:00Z",
        _counts(),
        pending_paths=0,
    )
    exact = formal.formal_readiness(
        "2027-07-30T00:00:00Z",
        _counts(),
        pending_paths=0,
    )
    assert early["exact_full_year_time_boundary"] is False
    assert all(exact.values())


def test_sample_counts_cannot_be_relaxed_after_time_boundary() -> None:
    readiness = formal.formal_readiness(
        "2027-08-01T00:00:00Z",
        {
            "closed_trades": 89,
            "by_clock": {"0005": 29, "0605": 30, "1205": 30},
            "by_side": {"LONG": 44, "SHORT": 45},
        },
        pending_paths=0,
    )
    assert readiness["exact_full_year_time_boundary"] is True
    assert readiness["minimum_closed_trades"] is False
    assert readiness["minimum_0005_trades"] is False


def test_day_block_inference_is_deterministic_and_keeps_day_unit() -> None:
    frame = _closed([1.5, -1.0] * 50)
    first = formal.day_block_inference(
        frame,
        simulations=200,
        block_length_days=5,
        seed=11,
        lower_quantile=0.05,
    )
    second = formal.day_block_inference(
        frame,
        simulations=200,
        block_length_days=5,
        seed=11,
        lower_quantile=0.05,
    )
    assert first == second
    assert first["active_days"] == 100
    assert first["resampling_unit"] == "UTC_ACTIVE_TRADING_DAY"


def test_same_day_clock_trades_remain_one_resampling_unit() -> None:
    frame = _closed([1.5, -1.0, 1.5, -1.0, 1.5, -1.0])
    frame["entry_time_utc"] = pd.to_datetime(
        [
            "2027-01-01T00:05:00Z",
            "2027-01-01T06:05:00Z",
            "2027-01-01T12:05:00Z",
            "2027-01-02T00:05:00Z",
            "2027-01-02T06:05:00Z",
            "2027-01-02T12:05:00Z",
        ],
        utc=True,
    )
    result = formal.day_block_inference(
        frame,
        simulations=20,
        block_length_days=1,
        seed=3,
        lower_quantile=0.05,
    )
    assert result["active_days"] == 2


def test_inference_gates_require_positive_lower_bounds() -> None:
    cfg = formal.load_config()
    inference = {
        "results": {
            "base": {
                "one_sided_lower_bounds": {
                    "profit_factor": 1.1,
                    "expectancy_r": 0.01,
                }
            },
            "extra_half_pip": {
                "one_sided_lower_bounds": {
                    "profit_factor": 1.01,
                    "expectancy_r": 0.001,
                }
            },
        }
    }
    assert all(formal.inference_gates(inference, cfg).values())
    inference["results"]["extra_half_pip"]["one_sided_lower_bounds"][
        "expectancy_r"
    ] = 0.0
    assert (
        formal.inference_gates(inference, cfg)[
            "stressed_expectancy_lower_bound"
        ]
        is False
    )


def test_blinded_status_has_no_economic_output() -> None:
    status = formal.build_blinded_status(
        evaluated_at_utc="2026-07-29T12:30:00Z",
        verify_lock=False,
    )
    serialized = str(status).lower()
    assert status["status"] == "WAITING_FOR_EXACT_FULL_YEAR_BOUNDARY"
    assert status["economic_outcomes_exposed"] is False
    for forbidden in ("profit_factor", "expectancy", "drawdown", "net_r"):
        assert forbidden not in serialized


def test_formal_result_is_immutable_and_first_result_wins(
    tmp_path: Path,
) -> None:
    first = formal.write_formal_result(
        tmp_path,
        {"status": "REJECTED_WITHOUT_RETUNING", "value": 1},
    )
    second = formal.write_formal_result(
        tmp_path,
        {"status": "INDEPENDENT_RESEARCH_REVIEW_REQUIRED", "value": 2},
    )
    assert second == first
    assert second["status"] == "REJECTED_WITHOUT_RETUNING"
    assert len(list((tmp_path / "manifests").glob("*.json"))) == 1


def test_evidence_chain_is_path_and_content_sensitive(tmp_path: Path) -> None:
    root = tmp_path / "ledger"
    root.mkdir()
    (root / "a.json").write_text("one", encoding="utf-8")
    first = formal.evidence_chain({"ledger": root})
    (root / "a.json").write_text("two", encoding="utf-8")
    second = formal.evidence_chain({"ledger": root})
    assert first["files"] == 1
    assert first["sha256"] != second["sha256"]


def test_formal_inference_lock_verifies() -> None:
    lock = formal.verify_preregistration()
    assert lock["locked_before_first_portfolio_observation"] is True
    assert lock["economic_output_before_formal_readiness_allowed"] is False
    assert lock["repeated_formal_evaluation_allowed"] is False
