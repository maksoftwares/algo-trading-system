from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_demo_account_isolation_passes_for_demo_terminal_evidence(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_terminal_report(reports / "PHASE2_EXPERIMENTAL_DEMO_TERMINAL.json", server="Capital.ComMena-Demo")
    _write_attachments_report(reports / "PHASE2_EXPERIMENTAL_DEMO_ATTACHMENTS.json")
    (reports / "DEMO_OBSERVER_WOULD_SIGNALS_2026_06_01.csv").write_text("symbol\nXAUUSD\n", encoding="utf-8")

    output = module.generate_phase2_demo_account_isolation_report(root)

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    markdown = output.markdown_path.read_text(encoding="utf-8")
    assert output.status == "PASS"
    assert payload["account"]["account_server"] == "Capital.ComMena-Demo"
    assert payload["account"]["account_type_or_label"] == "DEMO_OR_PRACTICE"
    assert payload["account"]["positions_count"] == 0
    assert payload["account"]["orders_count"] == 0
    assert payload["account"]["live_server_marker_present"] is False
    assert payload["paper_mode_authorized"] is False
    assert payload["demo_trading_authorized"] is False
    assert payload["canonical_phase2_authorized"] is False
    assert "Overall status: PASS" in markdown


def test_demo_account_isolation_fails_on_live_server_marker(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_terminal_report(reports / "PHASE2_EXPERIMENTAL_DEMO_TERMINAL.json", server="Capital.ComMena-Live")
    _write_attachments_report(reports / "PHASE2_EXPERIMENTAL_DEMO_ATTACHMENTS.json")

    output = module.generate_phase2_demo_account_isolation_report(root)

    assert output.status == "FAIL"
    assert any(check.name == "demo_server" and check.status == "FAIL" for check in output.checks)


def test_demo_account_isolation_stays_pending_without_terminal_report(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    (root / "outputs" / "reports").mkdir(parents=True)

    output = module.generate_phase2_demo_account_isolation_report(root)

    assert output.status == "PENDING"
    assert any(
        check.name == "experimental_demo_terminal_report" and check.status == "PENDING"
        for check in output.checks
    )


def _write_terminal_report(path: Path, server: str) -> None:
    path.write_text(
        json.dumps(
            {
                "status": "DEMO_TERMINAL_VERIFIED_EXPERIMENTAL_OBSERVERS_ATTACHED",
                "canonical_phase2_authorized": False,
                "live_trading_authorized": False,
                "can_start_demo_broker_rehearsal": False,
                "experimental_observers_attached": True,
                "experimental_observer_active_count": 3,
                "terminal": {
                    "latest_authorization_server": server,
                    "terminal_exe": "C:/Program Files/MetaTrader 5/terminal64.exe",
                    "terminal_data_dir": "C:/Users/User/AppData/Roaming/MetaQuotes/Terminal/demo",
                },
                "checks": [
                    {
                        "name": "zero_positions_orders",
                        "status": "PASS",
                        "evidence": "Latest post-authorization sync shows 0 positions and 0 orders.",
                    },
                    {
                        "name": "runtime_isolation",
                        "status": "PASS",
                        "evidence": "Terminal path is distinct from protected runtimes.",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_attachments_report(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "canonical_phase2_authorized": False,
                "live_trading_authorized": False,
                "broker_execution_authorized": False,
            }
        ),
        encoding="utf-8",
    )


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase2_demo_account_isolation_report.py"
    spec = importlib.util.spec_from_file_location("generate_phase2_demo_account_isolation_report", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase2_demo_account_isolation_report"] = module
    spec.loader.exec_module(module)
    return module
