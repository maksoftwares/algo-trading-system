import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.crossasset import (
    LANE_ROOT,
    attach_cross_asset_features,
    build_feature_matrix,
    causal_log_return,
    validate_frozen_v4_policy,
    verify_dependency_sources,
    verify_sources,
)


def source_frame(times, prices, available=None):
    if available is None:
        available = [True] * len(times)
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(times, utc=True),
            "price": prices,
            "available": available,
        }
    )


def test_causal_return_uses_only_completed_bars():
    source = source_frame(
        [
            "2026-01-01 00:20:00Z",
            "2026-01-01 00:25:00Z",
            "2026-01-01 00:30:00Z",
        ],
        [100.0, 110.0, 999.0],
    )
    decision = pd.Series(pd.to_datetime(["2026-01-01 00:30:00Z"], utc=True))
    observed = causal_log_return(decision, source, 5, 5, 10)
    assert observed.loc[0, "available"] == 1.0
    assert observed.loc[0, "return"] == pytest.approx(np.log(110.0 / 100.0))


def test_causal_return_rejects_stale_endpoint():
    source = source_frame(
        ["2026-01-01 00:00:00Z", "2026-01-01 01:00:00Z"],
        [100.0, 110.0],
    )
    decision = pd.Series(pd.to_datetime(["2026-01-01 01:30:00Z"], utc=True))
    observed = causal_log_return(decision, source, 60, 5, 10)
    assert observed.loc[0, "available"] == 0.0
    assert observed.loc[0, "return"] == 0.0


def test_common_dollar_factor_has_preregistered_signs(config):
    times = pd.date_range(
        "2026-01-01 00:05:00Z", periods=13, freq="5min", tz="UTC"
    )
    base = np.full(len(times), 100.0)
    sources = {
        "dxy": source_frame(times, base),
        "treasury": source_frame(times, base),
        "eurusd": source_frame(times, np.linspace(100.0, 101.0, len(times))),
        "gbpusd": source_frame(times, np.linspace(100.0, 102.0, len(times))),
        "usdjpy": source_frame(times, np.linspace(100.0, 103.0, len(times))),
    }
    snapshots = pd.DataFrame(
        {"decision_time": [pd.Timestamp("2026-01-01 01:10:00Z")]}
    )
    result = attach_cross_asset_features(snapshots, sources, config)
    eur = np.log(101.0 / 100.0)
    gbp = np.log(102.0 / 100.0)
    jpy = np.log(103.0 / 100.0)
    assert result.loc[0, "common_dollar_return_1h"] == pytest.approx(
        (-eur - gbp + jpy) / 3.0
    )
    assert result.loc[0, "common_dollar_1h_available"] == 1.0


def test_feature_matrix_appends_crossasset_without_changing_base(config):
    class FakeV3:
        @staticmethod
        def build_feature_matrix(snapshots, _config):
            return snapshots.loc[:, ["base"]].astype(float)

    snapshots = pd.DataFrame(
        {
            "base": [2.0],
            **{name: [0.0] for name in config["cross_asset"]["features"]},
        }
    )
    frame = build_feature_matrix(snapshots, {}, FakeV3(), config)
    assert frame.columns.tolist() == [
        "base",
        *config["cross_asset"]["features"],
    ]
    assert frame.loc[0, "base"] == 2.0
    assert np.isfinite(frame.to_numpy()).all()


def test_v4_model_policy_is_exactly_frozen(config):
    v4_config = json.loads(
        (
            LANE_ROOT.parent
            / "v6-causal-ml-early-exit-utility-v4"
            / "config"
            / "v6_causal_ml_early_exit_utility_v4.json"
        ).read_text(encoding="utf-8")
    )
    validate_frozen_v4_policy(config, v4_config)
    changed = json.loads(json.dumps(config))
    changed["action_policy"]["maximum_current_r"] = -0.11
    with pytest.raises(ValueError, match="action_policy"):
        validate_frozen_v4_policy(changed, v4_config)


def test_verify_sources_fails_closed(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("changed", encoding="utf-8")
    config = {
        "sources": {
            "source": {"path": str(source), "sha256": "0" * 64}
        }
    }
    with pytest.raises(ValueError, match="Locked source drift"):
        verify_sources(config)


def test_dependency_verifier_only_normalizes_crlf(tmp_path: Path):
    source = tmp_path / "source.json"
    source.write_bytes(b"{\n  \"value\": 1\n}\n")
    expected = __import__("hashlib").sha256(source.read_bytes()).hexdigest()
    source.write_bytes(b"{\r\n  \"value\": 1\r\n}\r\n")
    config = {
        "sources": {
            "source": {"path": str(source), "sha256": expected}
        }
    }
    observed = verify_dependency_sources(config)
    assert observed["source"]["match_mode"] == "crlf_to_lf"
    source.write_bytes(b"{\r\n  \"value\": 2\r\n}\r\n")
    with pytest.raises(ValueError, match="Locked dependency drift"):
        verify_dependency_sources(config)
