from __future__ import annotations

from capture_prospective_neutral_gdelt_relative_tone import (
    load_and_verify_preregistration,
)
from run_prospective_neutral_gdelt_relative_tone import compute_signal


def _document(
    side: str,
    source: str,
    tone: float,
    suffix: str,
) -> dict[str, object]:
    return {
        "entry_date_utc": "2026-07-29",
        "batch_timestamp_utc": "20260728230000",
        "record_id": f"{side}-{suffix}",
        "side": side,
        "source_common_name": source,
        "document_identifier": f"https://{source}/{suffix}",
        "tone": tone,
    }


def test_signal_rule_matches_frozen_long_mapping() -> None:
    config, _ = load_and_verify_preregistration()
    documents = [
        _document("ECB", "ecb-one.example", 3.0, "one"),
        _document("ECB", "ecb-two.example", 3.0, "two"),
        _document("FED", "fed-one.example", -1.0, "one"),
        _document("FED", "fed-two.example", -1.0, "two"),
    ]
    result = compute_signal(config, documents)
    assert result["status"] == "SIGNAL"
    assert result["side"] == "LONG"
    assert result["relative_tone"] == 4.0


def test_signal_rule_matches_frozen_short_mapping() -> None:
    config, _ = load_and_verify_preregistration()
    documents = [
        _document("ECB", "ecb-one.example", -2.0, "one"),
        _document("ECB", "ecb-two.example", -2.0, "two"),
        _document("FED", "fed-one.example", 2.0, "one"),
        _document("FED", "fed-two.example", 2.0, "two"),
    ]
    result = compute_signal(config, documents)
    assert result["status"] == "SIGNAL"
    assert result["side"] == "SHORT"


def test_signal_rule_requires_source_quorum() -> None:
    config, _ = load_and_verify_preregistration()
    documents = [
        _document("ECB", "one.example", 3.0, "one"),
        _document("FED", "two.example", -3.0, "two"),
    ]
    result = compute_signal(config, documents)
    assert result["status"] == "CASH_SOURCE_QUORUM_FAILED"
    assert result["side"] is None


def test_signal_rule_rejects_subthreshold_and_nonfinite_tone() -> None:
    config, _ = load_and_verify_preregistration()
    base = [
        _document("ECB", "ecb-one.example", 0.1, "one"),
        _document("ECB", "ecb-two.example", 0.1, "two"),
        _document("FED", "fed-one.example", 0.0, "one"),
        _document("FED", "fed-two.example", 0.0, "two"),
    ]
    result = compute_signal(config, base)
    assert result["status"] == "CASH_SUBTHRESHOLD_RELATIVE_TONE"
    base[0]["tone"] = None
    invalid = compute_signal(config, base)
    assert invalid["status"] == "CASH_NONFINITE_TONE"
