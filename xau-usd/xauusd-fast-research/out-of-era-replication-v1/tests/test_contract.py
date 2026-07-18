from __future__ import annotations

import json
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from contract import canonical_hash, expected_months  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]


def test_registered_sources_exist_and_no_authority_is_enabled() -> None:
    config = json.loads(
        (ROOT / "config" / "out_of_era_replication_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(config["candidates"]) == 3
    assert set(config["gates"]) == {
        candidate["candidate_id"] for candidate in config["candidates"]
    }
    for candidate in config["candidates"]:
        for key, value in candidate.items():
            if key.startswith("source_") and key != "source_policy_id":
                assert (ROOT / value).resolve().is_file()
    controls = config["research_controls"]
    assert controls["parameter_search_count"] == 0
    assert controls["paid_data_request_authorized"] is False
    assert controls["databento_use_authorized"] is False
    assert controls["broker_action_authorized"] is False
    assert controls["python_predictions_authorized"] is False
    assert controls["ea_consumption_authorized"] is False


def test_nfp_policy_is_exactly_present_in_source_config() -> None:
    config = json.loads(
        (ROOT / "config" / "out_of_era_replication_v1.json").read_text(
            encoding="utf-8"
        )
    )
    candidate = next(
        item
        for item in config["candidates"]
        if item["candidate_id"] == "NFP_FADE_RR2_EXACT"
    )
    source = json.loads(
        (ROOT / candidate["source_config"]).resolve().read_text(encoding="utf-8")
    )
    policy = next(
        item
        for item in source["policies"]
        if item["policy_id"] == candidate["source_policy_id"]
    )
    assert policy == {
        "policy_id": "EVENT_NFP_FADE_RR2",
        "event_type": "NFP",
        "mode": "FADE",
        "impulse_minutes": 15,
        "start_minutes": 15,
        "end_minutes": 90,
        "break_atr": 0.1,
        "stop_buffer_atr": 0.1,
        "minimum_body_fraction": 0.35,
        "target_r": 2.0,
    }
    assert source["schema_version"] == "xauusd_macro_event_reaction_replication_v3"
    assert source["source"]["exit_tick_grace_ms"] == 259_200_000


def test_contract_month_boundary_and_canonical_hash() -> None:
    config = json.loads(
        (ROOT / "config" / "out_of_era_replication_v1.json").read_text(
            encoding="utf-8"
        )
    )
    months = expected_months(config)
    assert len(months) == 78
    assert months[0] == "2010-01"
    assert months[-1] == "2016-06"
    assert canonical_hash({"b": 2, "a": 1}) == canonical_hash({"a": 1, "b": 2})
