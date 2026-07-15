from __future__ import annotations

import json
from pathlib import Path

from xau_continuation import research


def test_exact_base_identity_is_frozen(lane: Path) -> None:
    identity = research.verify_identity(lane)
    assert identity["verified_base_commit"] == research.BASE_COMMIT
    assert identity["verified_base_tree"] == research.BASE_TREE
    assert identity["verified_base_parent"] == research.BASE_PARENT


def test_branch_begins_directly_at_base(lane: Path) -> None:
    identity = research.verify_identity(lane)
    assert identity["verified_branch"] == research.BRANCH
    assert identity["new_branch_begins_directly_from_exact_base"] is True


def test_reviewed_correction_lane_is_present(lane: Path) -> None:
    identity = research.verify_identity(lane)
    assert identity["reviewed_residual_correction_lane_exists"] is True
    assert identity["base_commit_files_outside_reviewed_lane"] == []


def test_current_changes_are_confined_to_lane(lane: Path) -> None:
    assert research.verify_identity(lane)["current_files_outside_permitted_scope"] == []


def test_stage_a_has_exact_36_months() -> None:
    months = research.month_keys()
    assert len(months) == 36
    assert (months[0], months[-1]) == ("2018-07", "2021-06")


def test_stage_a_boundaries_are_half_open() -> None:
    assert research.STAGE_A_START.isoformat() == "2018-07-01T00:00:00+00:00"
    assert research.STAGE_A_END.isoformat() == "2021-07-01T00:00:00+00:00"


def test_quarantine_boundaries_are_exact() -> None:
    assert research.QUARANTINE_START == research.STAGE_A_END
    assert research.QUARANTINE_END.isoformat() == "2024-07-01T00:00:00+00:00"


def test_quarantine_months_cannot_enter_stage_a() -> None:
    assert all(month < "2021-07" for month in research.month_keys())
    assert "2021-07" not in research.month_keys()


def test_all_four_official_instruments_are_frozen() -> None:
    assert research.INSTRUMENTS == {"XAUUSD": "XAU-USD", "XAGUSD": "XAG-USD", "EURUSD": "EUR-USD", "USDJPY": "USD-JPY"}


def test_only_xau_directional_specialists_exist() -> None:
    assert research.LONG_ID == "XAU_POSITIVE_RESIDUAL_LONG_SPECIALIST"
    assert research.SHORT_ID == "XAU_NEGATIVE_RESIDUAL_SHORT_SPECIALIST"
    assert research.COMBINED_ID == "COMBINED_RESIDUAL_CONTINUATION_DIAGNOSTIC"


def test_frozen_configuration_has_zero_searches(lane: Path) -> None:
    config = json.loads((lane / "config" / "frozen_config.json").read_text())
    assert config["parameter_search_count"] == 0
    assert config["feature_search_count"] == 0
    assert config["model_search_count"] == 0
    assert config["router_training_count"] == 0


def test_frozen_configuration_prohibits_mean_reversion_direction(lane: Path) -> None:
    config = json.loads((lane / "config" / "frozen_config.json").read_text())
    assert config["episodes"]["positive_long_threshold"] == 2.5
    assert config["episodes"]["negative_short_threshold"] == -2.5


def test_required_output_contract_is_complete() -> None:
    outputs = set(research.required_outputs())
    assert len(outputs) == 31
    assert "XAU_CONTINUATION_RUN_MANIFEST.json" in outputs
    assert "XAU_CONTINUATION_TRADE_LEDGER.csv" in outputs


def test_source_code_contains_no_absolute_username(lane: Path) -> None:
    sources = "\n".join(path.read_text(encoding="utf-8") for path in (lane / "src").rglob("*.py"))
    assert "ZHAO ZHU INFORMATION" not in sources
    assert "C:\\Users\\" not in sources


def test_no_ea_or_mt5_files_in_lane(lane: Path) -> None:
    suffixes = {path.suffix.lower() for path in lane.rglob("*") if path.is_file()}
    assert not suffixes.intersection({".mq4", ".mq5", ".ex4", ".ex5", ".set"})


def test_official_source_is_dukascopy_only() -> None:
    assert research.SOURCE == "https://jetta.dukascopy.com/v1"
    assert "capital" not in research.SOURCE.lower()
