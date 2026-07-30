from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
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
EX5 = ROOT / "mt5" / "Experts" / "EurUsdProspectiveMultiSymbolCollector.ex5"
COMPILE_LOG = (
    ROOT / "mt5" / "EURUSD_PROSPECTIVE_MULTISYMBOL_COLLECTOR_COMPILE.log"
)
SMOKE = ROOT / "outputs" / "smoke"
FEATURES = SMOKE / "EURUSD_PROSPECTIVE_M5_FEATURES_R2_SMOKE_ONLY.csv"
ENVIRONMENT = SMOKE / "EURUSD_PROSPECTIVE_M5_ENVIRONMENT_R2_SMOKE_ONLY.csv"
HEARTBEAT = SMOKE / "EURUSD_PROSPECTIVE_M5_HEARTBEAT_R2_SMOKE_ONLY.csv"
REPORT = SMOKE / "EURUSD_PROSPECTIVE_MULTISYMBOL_COLLECTOR_R2_SMOKE.htm"
VERIFICATION = SMOKE / "VERIFICATION.json"
MANIFEST = (
    ROOT
    / "EURUSD_PROSPECTIVE_MULTISYMBOL_COLLECTOR_MANIFEST_2026_07_30.sha256.json"
)


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
        'StringReplace(referenceSymbolsLog, ",", "|")',
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


def test_compiled_artifact_and_smoke_evidence_are_pinned() -> None:
    verification = json.loads(VERIFICATION.read_text(encoding="utf-8"))
    paths = {
        "compiled_ex5": EX5,
        "compile_log": COMPILE_LOG,
        "tester_report": REPORT,
        "feature_ledger": FEATURES,
        "environment_log": ENVIRONMENT,
        "heartbeat_log": HEARTBEAT,
    }
    for key, path in paths.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == verification[
            "sha256"
        ][key]

    assert "Result: 0 errors, 0 warnings" in COMPILE_LOG.read_text(
        encoding="utf-16"
    )
    report = REPORT.read_text(encoding="utf-16")
    assert "Total Trades:</td>" in report
    assert "Total Deals:</td>" in report
    assert verification["runtime"]["total_trades"] == 0
    assert verification["runtime"]["total_deals"] == 0
    assert verification["runtime"]["final_balance_usd"] == 10000.0


def test_smoke_ledger_has_expected_missing_data_behavior() -> None:
    with FEATURES.open(encoding="utf-8", newline="") as handle:
        feature_rows = list(csv.DictReader(handle))
    assert len(feature_rows) == 4592
    assert {row["evidence_scope"] for row in feature_rows} == {
        "TESTER_SMOKE_NOT_FORWARD"
    }
    assert Counter(row["source_status"] for row in feature_rows) == {
        "NO_TICKS": 2871,
        "SYMBOL_UNAVAILABLE": 1148,
        "OK": 573,
    }
    assert Counter(
        (row["source_symbol"], row["source_status"]) for row in feature_rows
    ) == {
        ("EURUSD", "NO_TICKS"): 1,
        ("EURUSD", "OK"): 573,
        ("EURGBP", "NO_TICKS"): 574,
        ("EURJPY", "NO_TICKS"): 574,
        ("GBPUSD", "NO_TICKS"): 574,
        ("USDJPY", "NO_TICKS"): 574,
        ("GBPJPY", "NO_TICKS"): 574,
        ("DOLLARIDXUSD", "SYMBOL_UNAVAILABLE"): 574,
        ("USTBONDTRUSD", "SYMBOL_UNAVAILABLE"): 574,
    }

    with ENVIRONMENT.open(encoding="utf-8", newline="") as handle:
        environment_rows = list(csv.DictReader(handle))
    environment = {row["key"]: row["value"] for row in environment_rows}
    assert environment["chart_period"] == "PERIOD_M5"
    assert environment["trade_permission"] == "NONE_READ_ONLY"
    assert environment["reference_symbols"] == (
        "EURUSD|EURGBP|EURJPY|GBPUSD|USDJPY|GBPJPY|"
        "DOLLARIDXUSD|USTBONDTRUSD"
    )

    with HEARTBEAT.open(encoding="utf-8", newline="") as handle:
        heartbeat_rows = list(csv.DictReader(handle))
    assert Counter(row["event"] for row in heartbeat_rows) == {
        "STARTUP_LATCH": 1,
        "INTERVAL_CAPTURED": 574,
        "HEARTBEAT": 2879,
        "BAR_GAP": 2,
        "DEINIT": 1,
    }


def test_manifest_matches_every_packaged_file() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    packaged = {
        path.relative_to(ROOT).as_posix(): path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path != MANIFEST
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    }
    assert set(manifest["files"]) == set(packaged)
    for relative, path in packaged.items():
        entry = manifest["files"][relative]
        assert entry["bytes"] == path.stat().st_size
        assert entry["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
