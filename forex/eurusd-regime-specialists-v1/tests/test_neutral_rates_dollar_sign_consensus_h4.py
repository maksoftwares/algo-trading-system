from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_rates_dollar_sign_consensus_h4.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_RATES_DOLLAR_SIGN_CONSENSUS_H4_PREREG_"
    "2026_07_29.sha256.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_sign_consensus_contract_is_frozen_before_outcomes() -> None:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    assert lock["frozen_before_census_and_forward_outcomes"] is True
    assert lock["pnl_or_forward_path_loaded"] is False
    assert lock["oracle_decision_use_allowed"] is False
    assert lock["parameter_search_allowed"] is False
    for relative, expected in lock["files"].items():
        assert _sha256(PACKAGE_ROOT / relative) == expected


def test_sign_consensus_has_no_tunable_macro_threshold() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    strategy = config["strategy"]
    assert strategy["macro_rule"]["zero_threshold_only"] is True
    assert strategy["directions"] == ["LONG", "SHORT"]
    assert strategy["target_r"] == 1.5
    assert strategy["owned_regime_only"] is True
    assert config["decision_policy"]["no_parameter_search"] is True
