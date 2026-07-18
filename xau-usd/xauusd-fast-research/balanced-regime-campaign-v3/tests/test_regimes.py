from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from campaign import ARCHETYPES, _direction, generate_manifest  # noqa: E402
from regimes import _prior_quantile, _stabilize_states  # noqa: E402


def test_prior_quantile_excludes_current_observation() -> None:
    values = pd.Series([1.0, 2.0, 3.0, 1000.0])
    result = _prior_quantile(values, window=3, minimum=3, quantile=0.5)
    assert np.isnan(result.iloc[2])
    assert result.iloc[3] == 2.0


def test_state_change_requires_confirmation_and_emits_one_transition() -> None:
    raw = pd.Series(
        ["CHOP", "CHOP", "TREND_UP", "TREND_UP", "TREND_UP", "CHOP"]
    )
    unsafe = pd.Series(False, index=raw.index)
    eligible = pd.Series(True, index=raw.index)
    result = _stabilize_states(raw, unsafe, eligible, confirmation_bars=2)
    assert result.tolist() == [
        "CHOP",
        "CHOP",
        "CHOP",
        "TRANSITION",
        "TREND_UP",
        "TREND_UP",
    ]


def test_config_forbids_pnl_conditioning() -> None:
    config = json.loads(
        (ROOT / "config" / "balanced_regime_campaign_v3.json").read_text(
            encoding="utf-8"
        )
    )
    controls = config["research_controls"]
    assert controls["pnl_visible_to_regime_audit"] is False
    assert controls["regime_thresholds_selected_from_returns"] is False


def test_manifest_has_one_thousand_direction_specific_attempts() -> None:
    manifest = generate_manifest()
    assert len(manifest) == 1000
    assert manifest["variant_id"].is_unique
    assert manifest.groupby(["archetype", "timeframe"]).size().eq(25).all()
    assert set(manifest["archetype"]) == set(ARCHETYPES)
    assert all(_direction(name) in {-1, 1} for name in ARCHETYPES)
