from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT / "mt5" / "Experts" / "EurUsdProspectiveMultiSymbolCollector.mq5"
)
PRESET = (
    ROOT
    / "mt5"
    / "Presets"
    / "EURUSD_PROSPECTIVE_MULTISYMBOL_COLLECTOR_DEMO.set"
)
PROTOCOL = ROOT / "PROSPECTIVE_DATA_PROTOCOL.md"


def _settings(path: Path) -> dict[str, str]:
    return {
        key: value
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
        for key, value in [line.split("=", 1)]
    }


def test_source_has_no_order_capability() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    forbidden = (
        "<Trade/Trade.mqh>",
        "CTrade",
        "OrderSend",
        "PositionOpen",
        ".Buy(",
        ".Sell(",
    )
    for token in forbidden:
        assert token not in source


def test_source_is_demo_or_tester_only_and_m5_only() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    required = (
        "MQL_TESTER",
        "ACCOUNT_TRADE_MODE_DEMO",
        "_Period != PERIOD_M5",
        "_Symbol != InpTargetSymbol",
        "FROZEN_FORWARD_FLOOR_UTC",
        "current_bar_latched_no_historical_backfill",
        "duplicate_instance_mutex",
    )
    for token in required:
        assert token in source


def test_tick_ranges_are_exact_and_missing_data_is_explicit() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    required = (
        "CopyTicksRange(",
        "const ulong fromMsc = (ulong)intervalOpen * 1000;",
        "const ulong toMsc = (ulong)intervalClose * 1000 - 1;",
        '"SYMBOL_UNAVAILABLE"',
        '"COPY_FAILED"',
        '"NO_TICKS"',
        '"NO_VALID_TWO_SIDED_QUOTES"',
        '"BAR_GAP"',
        '"no_catchup_gap_seconds="',
    )
    for token in required:
        assert token in source


def test_safe_preset_uses_frozen_forward_boundary() -> None:
    settings = _settings(PRESET)
    assert settings["InpTargetSymbol"] == "EURUSD"
    assert settings["InpProspectiveStartUtc"] == "2026.08.01 00:00"
    assert settings["InpBrokerUtcOffsetSeconds"] == "0"
    assert "EURGBP" in settings["InpReferenceSymbols"]
    assert "USDJPY" in settings["InpReferenceSymbols"]
    assert settings["InpFeatureLogName"].endswith("_V1.csv")


def test_protocol_separates_discovery_and_untouched_validation() -> None:
    protocol = PROTOCOL.read_text(encoding="utf-8")
    required = (
        "Tranche A",
        "Tranche B",
        "next 60 active collection days",
        "may not be reversed post-hoc",
        "additional 0.5 pip round-trip stress",
        "removing the five best trades",
        "MT5 implementation parity",
    )
    for token in required:
        assert token in protocol

