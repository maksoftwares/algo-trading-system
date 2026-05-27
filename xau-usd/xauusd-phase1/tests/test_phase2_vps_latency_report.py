from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_vps_latency_report_pending_without_evidence(tmp_path):
    module = _load_module()
    root = tmp_path / "phase1"

    output = module.generate_phase2_vps_latency_report(root)

    report = output.report_path.read_text(encoding="utf-8")
    assert output.status == "PENDING"
    assert "Overall status: PENDING" in report
    assert any(check.name == "selection_fields" and check.status == "PENDING" for check in output.checks)
    assert any(check.name == "ping_evidence" and check.status == "PENDING" for check in output.checks)


def test_vps_latency_report_passes_with_clean_windows_evidence(tmp_path):
    module = _load_module()
    root = tmp_path / "phase1"
    ping = tmp_path / "ping.txt"
    tracert = tmp_path / "tracert.txt"
    test_net = tmp_path / "test_net.txt"
    ping.write_text(
        "\n".join(
            [
                "Pinging broker.example [192.0.2.10] with 32 bytes of data:",
                "Reply from 192.0.2.10: bytes=32 time=18ms TTL=57",
                "Reply from 192.0.2.10: bytes=32 time=19ms TTL=57",
                "Reply from 192.0.2.10: bytes=32 time=17ms TTL=57",
                "Reply from 192.0.2.10: bytes=32 time=18ms TTL=57",
                "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),",
                "Minimum = 17ms, Maximum = 19ms, Average = 18ms",
            ]
        ),
        encoding="utf-8",
    )
    tracert.write_text("Tracing route to broker.example\n  1  1 ms  1 ms  1 ms gateway\n", encoding="utf-8")
    test_net.write_text("TcpTestSucceeded : True\n", encoding="utf-8")

    output = module.generate_phase2_vps_latency_report(
        root=root,
        provider="FXVM",
        region="Dubai",
        endpoint="broker.example",
        ping_output_path=ping,
        tracert_output_path=tracert,
        test_net_output_path=test_net,
    )

    assert output.status == "PASS"
    assert "Average latency 18.00 ms is preferred" in output.report_path.read_text(encoding="utf-8")


def test_vps_latency_report_fails_on_packet_loss(tmp_path):
    module = _load_module()
    root = tmp_path / "phase1"
    ping = tmp_path / "ping.txt"
    tracert = tmp_path / "tracert.txt"
    test_net = tmp_path / "test_net.txt"
    ping.write_text(
        "Packets: Sent = 4, Received = 3, Lost = 1 (25% loss),\n"
        "Minimum = 17ms, Maximum = 19ms, Average = 18ms\n",
        encoding="utf-8",
    )
    tracert.write_text("Tracing route to broker.example\n", encoding="utf-8")
    test_net.write_text("TcpTestSucceeded : True\n", encoding="utf-8")

    output = module.generate_phase2_vps_latency_report(
        root=root,
        provider="FXVM",
        region="Dubai",
        endpoint="broker.example",
        ping_output_path=ping,
        tracert_output_path=tracert,
        test_net_output_path=test_net,
    )

    assert output.status == "FAIL"
    assert any(check.name == "packet_loss" and check.status == "FAIL" for check in output.checks)


def test_parse_linux_ping_output():
    module = _load_module()
    stats = module.parse_ping_output(
        "4 packets transmitted, 4 received, 0% packet loss, time 3005ms\n"
        "rtt min/avg/max/mdev = 12.112/13.456/15.789/1.000 ms\n"
    )

    assert stats.sent == 4
    assert stats.received == 4
    assert stats.loss_pct == 0
    assert stats.average_ms == 13.456


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase2_vps_latency_report.py"
    spec = importlib.util.spec_from_file_location("generate_phase2_vps_latency_report", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase2_vps_latency_report"] = module
    spec.loader.exec_module(module)
    return module
