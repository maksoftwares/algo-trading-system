from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_experimental_demo_terminal_quarantines_active_chart_experts(tmp_path: Path):
    module = _load_module()
    terminal = _terminal_with_log(
        tmp_path,
        [
            "OO\t0\t01:07:47.100\tTerminal\tMetaTrader 5 x64 build 5833 started for MetaQuotes Ltd.",
            "PS\t0\t01:07:47.801\tExperts\texpert GoldMissionEAv5 (XAUUSD,M15) loaded successfully",
            "RM\t0\t01:07:49.131\tNetwork\t'1025742': authorized on Capital.ComMena-Demo through Access Point 2 (ping: 134.13 ms, build 5800)",
            "KS\t0\t01:07:49.987\tNetwork\t'1025742': terminal synchronized with Capital Com Mena Securities Trading L.L.C: 0 positions, 0 orders, 232 symbols, 0 spreads",
            "HS\t0\t01:07:49.987\tNetwork\t'1025742': trading has been enabled - hedging mode",
        ],
    )
    terminal_exe = _terminal_exe(tmp_path)

    output = module.generate_phase2_experimental_demo_terminal_report(
        root=tmp_path / "xauusd-phase1",
        terminal_data_dir=terminal,
        terminal_exe=terminal_exe,
    )

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    markdown = output.markdown_path.read_text(encoding="utf-8")
    assert output.status == "DEMO_TERMINAL_VERIFIED_QUARANTINE_REQUIRED"
    assert payload["clean_demo_setup_ready"] is False
    assert payload["can_start_demo_broker_rehearsal"] is False
    assert payload["terminal"]["latest_authorization_server"] == "Capital.ComMena-Demo"
    assert payload["active_experts"][0]["expert"] == "GoldMissionEAv5"
    assert any(check.name == "active_chart_experts" and check.status == "WARN" for check in output.checks)
    assert "Overall status: DEMO_TERMINAL_VERIFIED_QUARANTINE_REQUIRED" in markdown
    assert "1025742" not in markdown


def test_experimental_demo_terminal_is_ready_when_clean_demo_context(tmp_path: Path):
    module = _load_module()
    terminal = _terminal_with_log(
        tmp_path,
        [
            "OO\t0\t01:07:58.100\tTerminal\tMetaTrader 5 x64 build 5833 started for MetaQuotes Ltd.",
            "RM\t0\t01:07:59.258\tNetwork\t'1025742': authorized on Capital.ComMena-Demo through Access Point 1 (ping: 169.89 ms, build 5800)",
            "CI\t0\t01:07:59.601\tNetwork\t'1025742': terminal synchronized with Capital Com Mena Securities Trading L.L.C: 0 positions, 0 orders, 232 symbols, 0 spreads",
            "PI\t0\t01:07:59.601\tNetwork\t'1025742': trading has been enabled - hedging mode",
        ],
    )

    output = module.generate_phase2_experimental_demo_terminal_report(
        root=tmp_path / "xauusd-phase1",
        terminal_data_dir=terminal,
        terminal_exe=_terminal_exe(tmp_path),
    )

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    assert output.status == "DEMO_TERMINAL_VERIFIED_READY_FOR_SAFE_SETUP"
    assert payload["clean_demo_setup_ready"] is True
    assert payload["can_start_experimental_demo_setup"] is True
    assert payload["canonical_phase2_authorized"] is False
    assert payload["live_trading_authorized"] is False


def test_experimental_demo_terminal_fails_when_latest_authorization_is_live(tmp_path: Path):
    module = _load_module()
    terminal = _terminal_with_log(
        tmp_path,
        [
            "OO\t0\t01:07:48.100\tTerminal\tMetaTrader 5 x64 build 5833 started for MetaQuotes Ltd.",
            "RM\t0\t01:07:49.131\tNetwork\t'1025742': authorized on Capital.ComMena-Demo through Access Point 2 (ping: 134.13 ms, build 5800)",
            "NE\t0\t01:08:23.426\tNetwork\t'1025742': authorized on Capital.ComMena-Live through Access Point 1 (ping: 172.80 ms, build 5800)",
            "CI\t0\t01:08:23.601\tNetwork\t'1025742': terminal synchronized with Capital Com Mena Securities Trading L.L.C: 0 positions, 0 orders, 232 symbols, 0 spreads",
            "PI\t0\t01:08:23.601\tNetwork\t'1025742': trading has been enabled - hedging mode",
        ],
    )

    output = module.generate_phase2_experimental_demo_terminal_report(
        root=tmp_path / "xauusd-phase1",
        terminal_data_dir=terminal,
        terminal_exe=_terminal_exe(tmp_path),
    )

    assert output.status == "FAIL"
    assert any(check.name == "demo_server" and check.status == "FAIL" for check in output.checks)


def test_experimental_demo_terminal_fails_when_positions_or_orders_exist(tmp_path: Path):
    module = _load_module()
    terminal = _terminal_with_log(
        tmp_path,
        [
            "OO\t0\t01:07:58.100\tTerminal\tMetaTrader 5 x64 build 5833 started for MetaQuotes Ltd.",
            "RM\t0\t01:07:59.258\tNetwork\t'1025742': authorized on Capital.ComMena-Demo through Access Point 1 (ping: 169.89 ms, build 5800)",
            "CI\t0\t01:07:59.601\tNetwork\t'1025742': terminal synchronized with Capital Com Mena Securities Trading L.L.C: 1 positions, 2 orders, 232 symbols, 0 spreads",
            "PI\t0\t01:07:59.601\tNetwork\t'1025742': trading has been enabled - hedging mode",
        ],
    )

    output = module.generate_phase2_experimental_demo_terminal_report(
        root=tmp_path / "xauusd-phase1",
        terminal_data_dir=terminal,
        terminal_exe=_terminal_exe(tmp_path),
    )

    assert output.status == "FAIL"
    assert any(check.name == "zero_positions_orders" and check.status == "FAIL" for check in output.checks)


def test_experimental_demo_terminal_ignores_experts_removed_before_latest_session(tmp_path: Path):
    module = _load_module()
    terminal = _terminal_with_log(
        tmp_path,
        [
            "PS\t0\t01:07:47.801\tExperts\texpert GoldMissionEAv5 (XAUUSD,M15) loaded successfully",
            "PR\t0\t01:19:56.606\tExperts\texpert GoldMissionEAv5 (XAUUSD,M15) removed",
            "OO\t0\t01:21:23.061\tTerminal\tMetaTrader 5 x64 build 5833 started for MetaQuotes Ltd.",
            "LE\t0\t01:21:25.137\tNetwork\t'1025742': authorized on Capital.ComMena-Demo through Access Point 1 (ping: 169.89 ms, build 5800)",
            "CI\t0\t01:21:25.601\tNetwork\t'1025742': terminal synchronized with Capital Com Mena Securities Trading L.L.C: 0 positions, 0 orders, 232 symbols, 0 spreads",
            "PI\t0\t01:21:25.601\tNetwork\t'1025742': trading has been enabled - hedging mode",
        ],
    )

    output = module.generate_phase2_experimental_demo_terminal_report(
        root=tmp_path / "xauusd-phase1",
        terminal_data_dir=terminal,
        terminal_exe=_terminal_exe(tmp_path),
    )

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    assert output.status == "DEMO_TERMINAL_VERIFIED_READY_FOR_SAFE_SETUP"
    assert payload["active_experts"] == []
    assert payload["terminal"]["latest_session_start"] == "2026-05-29 01:21:23.061000"


def test_experimental_demo_terminal_script_is_evidence_only():
    script = (ROOT / "scripts" / "generate_phase2_experimental_demo_terminal_report.py").read_text(encoding="utf-8")

    assert "OrderSend" not in script
    assert "CTrade" not in script
    assert "trade.Buy" not in script
    assert "trade.Sell" not in script


def _terminal_with_log(tmp_path: Path, lines: list[str]) -> Path:
    terminal = tmp_path / "terminal"
    logs = terminal / "logs"
    logs.mkdir(parents=True)
    (logs / "20260529.log").write_text("\n".join(lines), encoding="utf-8")
    return terminal


def _terminal_exe(tmp_path: Path) -> Path:
    exe = tmp_path / "MetaTrader 5" / "terminal64.exe"
    exe.parent.mkdir(parents=True, exist_ok=True)
    exe.write_text("", encoding="utf-8")
    return exe


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase2_experimental_demo_terminal_report.py"
    spec = importlib.util.spec_from_file_location("generate_phase2_experimental_demo_terminal_report", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase2_experimental_demo_terminal_report"] = module
    spec.loader.exec_module(module)
    return module
