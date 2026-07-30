from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mt5" / "Experts" / "XauProspectiveTelemetryCollector.mq5"
PRESET = ROOT / "mt5" / "Presets" / "XauProspectiveTelemetryCollector.passive_xauusd.set"


def test_collector_has_no_broker_action_surface() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    forbidden = (
        "OrderSend(",
        "OrderSendAsync(",
        "CTrade",
        "<Trade/Trade.mqh>",
        "PositionClose(",
        "PositionModify(",
        "OrderDelete(",
        "TRADE_ACTION_DEAL",
        "TRADE_ACTION_PENDING",
        "TRADE_ACTION_SLTP",
        "TRADE_ACTION_REMOVE",
    )
    for token in forbidden:
        assert token not in text
    assert "const bool BROKER_ACTION_ALLOWED = false;" in text
    assert "const bool TRADE_PERMISSION = false;" in text
    assert "const bool PYTHON_EXECUTION_AUTHORIZED = false;" in text


def test_collector_captures_required_prospective_telemetry() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    assert "void OnTick()" in text
    assert "void OnBookEvent(" in text
    assert "void OnTradeTransaction(" in text
    assert "MarketBookAdd(_Symbol)" in text
    assert "MarketBookGet(_Symbol,book)" in text
    assert "MarketBookRelease(_Symbol)" in text
    assert "tick_time_msc" in text
    assert "spread_points" in text
    assert "request_deviation" in text
    assert "result_retcode" in text
    assert "result_bid" in text
    assert "result_ask" in text
    assert "book_subscription_error" in text
    assert "terminal_trade_allowed" in text
    assert "mql_trade_allowed" in text
    assert "SYMBOL_TICKS_BOOKDEPTH" in text


def test_tick_ledger_rotates_from_the_tick_timestamp() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    assert "datetime tick_seconds=(datetime)(tick.time_msc / 1000);" in text
    assert "EnsureDailyLedgers(DateToken(tick_seconds))" in text
    assert 'base += "_" + DateToken(TimeGMT());' not in text


def test_collector_refuses_unsafe_startup() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    assert "if(!InpDryRunOnly)" in text
    assert "attached symbol does not match InpTargetSymbol" in text
    assert "server marker mismatch" in text
    assert "account login not whitelisted" in text
    assert "EA-level trading permission must remain disabled" in text
    assert "MQLInfoInteger(MQL_TRADE_ALLOWED)" in text
    assert text.count("return INIT_FAILED;") >= 6


def test_collector_preset_is_passive_and_demo_locked() -> None:
    text = PRESET.read_text(encoding="utf-8")

    assert "InpDryRunOnly=true" in text
    assert "InpTargetSymbol=XAUUSD" in text
    assert "InpExpectedServerMarker=Demo" in text
    assert "InpAllowedAccountLoginsCsv=1025742,1033030,1033669" in text
    assert "InpCollectTicks=true" in text
    assert "InpCollectMarketDepth=true" in text
    assert "InpCollectTradeTransactions=true" in text


def test_deployment_uses_separate_locked_terminal(tmp_path: Path) -> None:
    module = _load_module()
    chart = module._render_chart(ROOT)
    config = module._write_startup_config(tmp_path, "1033669", "Capital.ComMena-Demo")
    config_text = config.read_text(encoding="utf-8")

    assert module.DEFAULT_TARGET_ROOT.as_posix().endswith("MT5PortableProspectiveCollector")
    assert chart.count("<expert>") == 1
    assert "path=Experts\\XauProspectiveTelemetryCollector.ex5" in chart
    assert "expertmode=0" in chart
    assert "expertmode=1" not in chart
    assert "InpDryRunOnly=true" in chart
    assert "AllowLiveTrading=0" in config_text
    assert "AllowDllImport=0" in config_text


def test_deployment_refuses_existing_runtime_roots() -> None:
    module = _load_module()

    with pytest.raises(RuntimeError, match="credential source"):
        module._guard_target_root(module.DEFAULT_SOURCE_TERMINAL_ROOT, module.DEFAULT_SOURCE_TERMINAL_ROOT)
    with pytest.raises(RuntimeError, match="credential source"):
        module._guard_target_root(
            module.DEFAULT_SOURCE_TERMINAL_ROOT,
            module.DEFAULT_SOURCE_TERMINAL_ROOT / "collector-child",
        )
    with pytest.raises(RuntimeError, match="protected MT5 runtime"):
        module._guard_target_root(module.DEFAULT_SOURCE_TERMINAL_ROOT, Path("C:/MT5PortableGoldMission"))
    with pytest.raises(RuntimeError, match="protected MT5 runtime"):
        module._guard_target_root(
            module.DEFAULT_SOURCE_TERMINAL_ROOT,
            Path("C:/MT5PortableGoldMission/collector-child"),
        )


def test_deployment_archives_existing_ledgers_without_deleting_them(tmp_path: Path) -> None:
    module = _load_module()
    files = tmp_path / "MQL5" / "Files"
    files.mkdir(parents=True)
    old = files / "xau_prospective_test_ticks_20260717.csv"
    unrelated = files / "other.csv"
    old.write_text("header\nrow\n", encoding="utf-8")
    unrelated.write_text("keep\n", encoding="utf-8")

    backup = module._archive_existing_logs(tmp_path)

    assert backup is not None
    assert not old.exists()
    assert (backup / old.name).read_text(encoding="utf-8") == "header\nrow\n"
    assert unrelated.exists()


def test_health_distinguishes_empty_depth_from_real_depth(tmp_path: Path) -> None:
    module = _load_module()
    files = tmp_path / "MQL5" / "Files"
    files.mkdir(parents=True)
    (files / "xau_prospective_1033669_demo_XAUUSD_startup.csv").write_text(
        "status,account_login,account_server,book_subscribed,book_subscription_error\n"
        "ACTIVE,1033669,Capital.ComMena-Demo,true,0\n",
        encoding="utf-8",
    )
    (files / "xau_prospective_1033669_demo_XAUUSD_ticks_20260717.csv").write_text(
        "schema_version,bid,ask\nv1,3300.00,3300.20\n",
        encoding="utf-8",
    )
    (files / "xau_prospective_1033669_demo_XAUUSD_heartbeat_20260717.csv").write_text(
        "schema_version,terminal_connected\nv1,true\n",
        encoding="utf-8",
    )
    book = files / "xau_prospective_1033669_demo_XAUUSD_book_20260717.csv"
    book.write_text("schema_version,book_type\nv1,EMPTY\n", encoding="utf-8")

    empty = module.inspect_collection_health(tmp_path)
    assert empty["status"] == "ACTIVE_TICKS_DEPTH_EMPTY"
    assert empty["real_depth_observed"] is False

    book.write_text("schema_version,book_type\nv1,BOOK_TYPE_BUY\n", encoding="utf-8")
    real = module.inspect_collection_health(tmp_path)
    assert real["status"] == "ACTIVE_TICKS_AND_DEPTH"
    assert real["real_depth_observed"] is True


def _load_module():
    path = ROOT / "scripts" / "deploy_xau_prospective_telemetry_collector.py"
    spec = importlib.util.spec_from_file_location("deploy_xau_prospective_telemetry_collector", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
