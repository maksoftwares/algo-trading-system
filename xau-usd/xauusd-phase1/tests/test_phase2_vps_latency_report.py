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
    assert "capture_phase2_vps_latency_evidence.ps1" in report
    assert "-SampleCount 20" in report
    assert "ping -n 20 $endpoint" in report
    assert any(check.name == "selection_fields" and check.status == "PENDING" for check in output.checks)
    assert any(check.name == "ping_evidence" and check.status == "PENDING" for check in output.checks)
    assert any(check.name == "local_baseline_comparison" and check.status == "PENDING" for check in output.checks)


def test_vps_latency_report_passes_with_clean_windows_evidence(tmp_path):
    module = _load_module()
    root = tmp_path / "phase1"
    ping = tmp_path / "ping.txt"
    tracert = tmp_path / "tracert.txt"
    test_net = tmp_path / "test_net.txt"
    baseline = _write_local_baseline(root, median_ms=129.78)
    ping.write_text(
        "\n".join(
            [
                "Pinging broker.example [192.0.2.10] with 32 bytes of data:",
                "Reply from 192.0.2.10: bytes=32 time=18ms TTL=57",
                "Reply from 192.0.2.10: bytes=32 time=19ms TTL=57",
                "Reply from 192.0.2.10: bytes=32 time=17ms TTL=57",
                "Reply from 192.0.2.10: bytes=32 time=18ms TTL=57",
                "Packets: Sent = 20, Received = 20, Lost = 0 (0% loss),",
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
        local_baseline_path=baseline,
    )

    assert output.status == "PASS"
    report = output.report_path.read_text(encoding="utf-8")
    assert "Average latency 18.00 ms is preferred" in report
    assert "VPS average latency 18.00 ms improves on local median 129.78 ms" in report
    assert "Local Median" in report


def test_vps_latency_report_requires_enough_ping_samples(tmp_path):
    module = _load_module()
    root = tmp_path / "phase1"
    ping = tmp_path / "ping.txt"
    tracert = tmp_path / "tracert.txt"
    test_net = tmp_path / "test_net.txt"
    baseline = _write_local_baseline(root, median_ms=129.78)
    ping.write_text(
        "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),\n"
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
        local_baseline_path=baseline,
    )

    assert output.status == "PENDING"
    assert any(
        check.name == "ping_evidence"
        and check.status == "PENDING"
        and "at least 10" in check.evidence
        for check in output.checks
    )


def test_vps_latency_report_fails_on_packet_loss(tmp_path):
    module = _load_module()
    root = tmp_path / "phase1"
    ping = tmp_path / "ping.txt"
    tracert = tmp_path / "tracert.txt"
    test_net = tmp_path / "test_net.txt"
    baseline = _write_local_baseline(root, median_ms=129.78)
    ping.write_text(
        "Packets: Sent = 20, Received = 15, Lost = 5 (25% loss),\n"
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
        local_baseline_path=baseline,
    )

    assert output.status == "FAIL"
    assert any(check.name == "packet_loss" and check.status == "FAIL" for check in output.checks)


def test_vps_latency_report_fails_when_vps_does_not_beat_local_baseline(tmp_path):
    module = _load_module()
    root = tmp_path / "phase1"
    ping = tmp_path / "ping.txt"
    tracert = tmp_path / "tracert.txt"
    test_net = tmp_path / "test_net.txt"
    baseline = _write_local_baseline(root, median_ms=129.78)
    ping.write_text(
        "Packets: Sent = 20, Received = 20, Lost = 0 (0% loss),\n"
        "Minimum = 130ms, Maximum = 140ms, Average = 135ms\n",
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
        local_baseline_path=baseline,
    )

    assert output.status == "FAIL"
    assert any(
        check.name == "local_baseline_comparison"
        and check.status == "FAIL"
        and "does not beat local median" in check.evidence
        for check in output.checks
    )


def test_vps_latency_report_keeps_small_baseline_improvement_pending_for_owner_review(tmp_path):
    module = _load_module()
    root = tmp_path / "phase1"
    ping = tmp_path / "ping.txt"
    tracert = tmp_path / "tracert.txt"
    test_net = tmp_path / "test_net.txt"
    baseline = _write_local_baseline(root, median_ms=100.00)
    ping.write_text(
        "Packets: Sent = 20, Received = 20, Lost = 0 (0% loss),\n"
        "Minimum = 92ms, Maximum = 98ms, Average = 95ms\n",
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
        local_baseline_path=baseline,
    )

    assert output.status == "PENDING"
    assert any(
        check.name == "local_baseline_comparison"
        and check.status == "WARN"
        and "owner review required" in check.evidence
        for check in output.checks
    )


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


def test_vps_latency_capture_script_is_evidence_only():
    script = (ROOT / "scripts" / "capture_phase2_vps_latency_evidence.ps1").read_text(encoding="utf-8")

    assert "generate_phase2_vps_latency_report.py" in script
    assert "local_baseline_path=$LocalBaselinePath" in script
    assert "--local-baseline $LocalBaselinePath" in script
    assert "Test-NetConnection" in script
    assert "ping -n $SampleCount $Endpoint" in script
    assert "Tee-Object -FilePath $PingPath" in script
    assert "OrderSend" not in script
    assert "CTrade" not in script


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


def _write_local_baseline(root: Path, median_ms: float) -> Path:
    report = root / "outputs" / "reports" / "PHASE2_LOCAL_MT5_NETWORK_BASELINE.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "\n".join(
            [
                "# Phase 2 Local MT5 Network Baseline",
                "",
                "Overall status: PASS",
                "",
                "## Summary",
                "",
                "| Samples | Latest Ping | Median Ping | Best Ping | Worst Ping | Latest Access Point |",
                "| --- | --- | --- | --- | --- | --- |",
                f"| 5755 | 185.76 ms | {median_ms:.2f} ms | 121.76 ms | 312.50 ms | 1 |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report
