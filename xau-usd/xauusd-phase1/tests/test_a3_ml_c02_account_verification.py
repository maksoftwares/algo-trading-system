from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.account_verification import render_account_verification_matrix_md, verify_account_read_only
from ml.a3_meta_v1.safety import scan_c02_python_safety
from ml.a3_meta_v1.terminal_verification import RunningProcess


REGISTRY = ROOT / "config" / "ml" / "mt5_accounts.yaml"


def test_c02_account_verifier_fails_before_mt5_when_terminal_not_running() -> None:
    def client_factory():
        raise AssertionError("client_factory should not be called without the terminal process")

    record = verify_account_read_only(
        ROOT,
        REGISTRY,
        "A2",
        process_provider=lambda: [],
        client_factory=client_factory,
        terminal_exists=lambda _: True,
    )

    assert record["status"] == "FAIL_CLOSED"
    assert record["code"] == "TERMINAL_NOT_ALREADY_RUNNING"
    assert record["mt5_initialize_attempted"] is False
    assert record["data_exported"] is False


def test_c02_account_verifier_detects_terminal_auto_launch() -> None:
    client = _FakeClient("1033030", "C:/MT5PortableTier1BestEA")
    process_provider = _ProcessProvider(
        [
            [RunningProcess(pid=10, exe="C:/MT5PortableTier1BestEA/terminal64.exe")],
            [
                RunningProcess(pid=10, exe="C:/MT5PortableTier1BestEA/terminal64.exe"),
                RunningProcess(pid=11, exe="C:/MT5PortableTier1BestEA/terminal64.exe"),
            ],
            [
                RunningProcess(pid=10, exe="C:/MT5PortableTier1BestEA/terminal64.exe"),
                RunningProcess(pid=11, exe="C:/MT5PortableTier1BestEA/terminal64.exe"),
            ],
        ]
    )

    record = verify_account_read_only(
        ROOT,
        REGISTRY,
        "A2",
        process_provider=process_provider,
        client_factory=lambda: client,
        terminal_exists=lambda _: True,
    )

    assert record["status"] == "FAIL_CLOSED"
    assert record["code"] == "UNEXPECTED_TERMINAL_LAUNCH"
    assert record["mt5_initialize_attempted"] is True
    assert client.shutdown_count == 1


def test_c02_account_verifier_passes_with_fake_readonly_client() -> None:
    client = _FakeClient("1033030", "C:/MT5PortableTier1BestEA")
    processes = [RunningProcess(pid=10, exe="C:/MT5PortableTier1BestEA/terminal64.exe")]

    record = verify_account_read_only(
        ROOT,
        REGISTRY,
        "A2",
        process_provider=lambda: processes,
        client_factory=lambda: client,
        terminal_exists=lambda _: True,
    )

    assert record["status"] == "PASS"
    assert record["code"] == "ACCOUNT_VERIFICATION_PASS"
    assert record["metadata"]["account"]["login"] == "1033030"
    assert record["runtime_audit"]["before_identity"]["position_tickets"]["tickets"] == ["100"]
    assert record["model_training_authorized"] is False
    assert client.shutdown_count == 1


def test_c02_account_verifier_failcloses_a3_runtime_drift() -> None:
    client = _FakeClient("1033669", "C:/MT5PortableRepairLane", position_sequences=[["100"], ["101"]])
    processes = [RunningProcess(pid=30, exe="C:/MT5PortableRepairLane/terminal64.exe")]

    record = verify_account_read_only(
        ROOT,
        REGISTRY,
        "A3",
        process_provider=lambda: processes,
        client_factory=lambda: client,
        terminal_exists=lambda _: True,
    )

    assert record["status"] == "FAIL_CLOSED"
    assert record["code"] == "A3_RUNTIME_ACTIVITY_DURING_VERIFICATION"
    assert record["data_exported"] is False


def test_c02_account_verification_script_has_worker_mode_and_boundary_text(tmp_path: Path) -> None:
    module = load_script("c02_verify_mt5_accounts")
    assert hasattr(module, "main")
    payload = {
        "status": "PASS",
        "boundary": {
            "mt5_connection_attempted": True,
            "data_exported": False,
            "model_training_authorized": False,
            "broker_action_authorized": False,
            "terminal_runtime_change_authorized": False,
            "worker_process_isolation": True,
        },
        "account_records": [
            {
                "account_label": "A1",
                "account_scope": "1025742",
                "status": "PASS",
                "code": "ACCOUNT_VERIFICATION_PASS",
                "detail": "ok",
            }
        ],
        "next_allowed_stage": "C02-02 bars/ticks export only if every account record is PASS",
    }

    report = render_account_verification_matrix_md(payload)

    assert "Data exported: false" in report
    assert "Model training authorized: false" in report
    assert "Worker process isolation: true" in report
    assert json.dumps(payload)


def test_c02_python_safety_scan_still_passes_with_account_verifier() -> None:
    findings = scan_c02_python_safety(ROOT / "ml" / "a3_meta_v1")

    assert findings == []


class _ProcessProvider:
    def __init__(self, sequences):
        self._sequences = sequences
        self._index = 0

    def __call__(self):
        value = self._sequences[min(self._index, len(self._sequences) - 1)]
        self._index += 1
        return value


class _FakeClient:
    def __init__(self, login: str, terminal_root: str, position_sequences=None):
        self.login = login
        self.terminal_root = terminal_root
        self.shutdown_count = 0
        self._position_sequences = position_sequences or [["100"], ["100"], ["100"]]
        self._position_index = 0

    def initialize(self, spec):
        assert spec.terminal_exe.startswith(self.terminal_root)
        return True

    def shutdown(self):
        self.shutdown_count += 1

    def version(self):
        return (500, 1, "test")

    def last_error(self):
        return (0, "ok")

    def account_info(self):
        return SimpleNamespace(login=self.login, server="Capital.ComMena-Demo", trade_mode=0, currency="USD")

    def terminal_info(self):
        return SimpleNamespace(
            path=self.terminal_root,
            data_path=self.terminal_root,
            commondata_path=self.terminal_root,
            connected=True,
            build=5000,
        )

    def symbol_info(self, symbol: str):
        assert symbol == "XAUUSD"
        return SimpleNamespace(point=0.01, digits=2, visible=True)

    def positions_get(self, symbol: str | None = None):
        assert symbol == "XAUUSD"
        tickets = self._position_sequences[min(self._position_index, len(self._position_sequences) - 1)]
        self._position_index += 1
        return [SimpleNamespace(ticket=ticket) for ticket in tickets]

    def orders_get(self, symbol: str | None = None):
        assert symbol == "XAUUSD"
        return []
