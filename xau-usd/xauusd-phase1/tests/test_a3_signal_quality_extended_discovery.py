from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta

from phase2x_test_helpers import ROOT, load_script


def test_extended_discovery_script_has_no_runtime_mt5_calls() -> None:
    text = (ROOT / "scripts" / "run_a3_signal_quality_extended_discovery.py").read_text(encoding="utf-8")

    for forbidden in (
        "MetaTrader5",
        "mt5.initialize",
        "OrderSend",
        "CTrade",
        "TRADE_ACTION",
        "PositionClose",
        "PositionModify",
        "terminal64.exe",
        "MQL5\\Profiles",
        "MQL5\\Presets",
    ):
        assert forbidden not in text


def test_soft_retest_v2_accepts_clean_completed_bar_geometry() -> None:
    module = load_script("run_a3_signal_quality_extended_discovery")
    bars = _bars(module)
    signal = _signal(module)

    assert module.soft_retest_v2(signal, bars)


def test_soft_retest_v2_blocks_weak_confirmation_body() -> None:
    module = load_script("run_a3_signal_quality_extended_discovery")
    bars = _bars(module)
    bars[20] = module.Bar(bars[20].start, bars[20].end, 101.20, 101.50, 99.50, 101.40, 0.0)

    assert not module.soft_retest_v2(_signal(module), bars)


def test_soft_retest_v2_blocks_weak_directional_close() -> None:
    module = load_script("run_a3_signal_quality_extended_discovery")
    bars = _bars(module)
    bars[20] = module.Bar(bars[20].start, bars[20].end, 100.10, 101.50, 99.50, 100.50, 0.0)

    assert not module.soft_retest_v2(_signal(module), bars)


def test_soft_retest_v2_blocks_retest_close_without_margin() -> None:
    module = load_script("run_a3_signal_quality_extended_discovery")
    bars = _bars(module)
    bars[19] = module.Bar(bars[19].start, bars[19].end, 99.90, 100.50, 99.50, 100.02, 0.0)

    assert not module.soft_retest_v2(_signal(module), bars)


def test_soft_retest_v2_atr_window_includes_completed_retest_bar() -> None:
    module = load_script("run_a3_signal_quality_extended_discovery")
    bars = _bars(module)
    bars[19] = module.Bar(bars[19].start, bars[19].end, 99.90, 110.00, 90.00, 100.10, 0.0)

    assert not module.soft_retest_v2(_signal(module), bars)


def test_soft_retest_v2_manifest_hash_matches_locked_doc() -> None:
    manifest = ROOT / "outputs" / "manifests" / "A3_SIGNAL_QUALITY_V2_SOFT_RETEST_W15_B45_C60_RCM05.sha256.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    files = {row["file"]: row["sha256"] for row in payload["files"]}

    assert payload["status"] == "LOCKED"
    expected_files = [
        "docs/A3_SIGNAL_QUALITY_V2_SOFT_RETEST_W15_B45_C60_RCM05_2026_06_18.md",
        "docs/A3_SIGNAL_QUALITY_V2_SOFT_RETEST_THRESHOLD_PROVENANCE_2026_06_18.md",
    ]
    assert sorted(files) == sorted(expected_files)
    for file_name in expected_files:
        assert files[file_name] == hashlib.sha256((ROOT / file_name).read_bytes()).hexdigest()


def test_soft_retest_v2_docs_disclose_cost_and_threshold_provenance() -> None:
    doc = (ROOT / "docs" / "A3_SIGNAL_QUALITY_V2_SOFT_RETEST_W15_B45_C60_RCM05_2026_06_18.md").read_text(encoding="utf-8")
    provenance = (ROOT / "docs" / "A3_SIGNAL_QUALITY_V2_SOFT_RETEST_THRESHOLD_PROVENANCE_2026_06_18.md").read_text(encoding="utf-8")

    assert "after subtracting `cost_r`" in doc
    assert "zero promotion evidence" in doc
    assert "ATR window includes the completed retest bar" in doc
    assert "18,000 possible combinations" in provenance
    assert "14,112 possible combinations" in provenance


def _bars(module):
    start = datetime(2025, 1, 2)
    bars = []
    for index in range(25):
        t0 = start + timedelta(minutes=5 * index)
        bars.append(module.Bar(t0, t0 + timedelta(minutes=5), 100.0, 100.5, 99.5, 100.0, 0.0))
    bars[19] = module.Bar(bars[19].start, bars[19].end, 99.90, 100.60, 99.60, 100.10, 0.0)
    bars[20] = module.Bar(bars[20].start, bars[20].end, 100.00, 101.50, 99.50, 101.40, 0.0)
    return bars


def _signal(module):
    return module.RawSignal(
        signal_id="fixture",
        direction="LONG",
        decision_time=datetime(2025, 1, 2, 1, 45),
        confirmation_index=20,
        retest_index=19,
        break_index=10,
        break_shift=11,
        level_kind="fixture",
        level_price=100.0,
        entry_price=101.40,
        stop_loss=100.40,
        take_profit=102.90,
        stop_distance_points=100.0,
        cost_r=0.0,
        session_bucket="Morning 06:00-11:59",
        h1_slope_points=1.0,
        h1_regime="RISING",
    )
