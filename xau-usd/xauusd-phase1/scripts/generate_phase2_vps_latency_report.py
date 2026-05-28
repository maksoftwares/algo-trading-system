from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_REPORT = Path("outputs") / "reports" / "PHASE2_VPS_LATENCY_REPORT.md"
DEFAULT_LOCAL_BASELINE = Path("outputs") / "reports" / "PHASE2_LOCAL_MT5_NETWORK_BASELINE.md"
PREFERRED_LATENCY_MS = 50.0
MAX_ACCEPTABLE_LATENCY_MS = 100.0
MIN_PING_SAMPLES = 10
MATERIAL_IMPROVEMENT_RATIO = 0.90


@dataclass(frozen=True)
class PingStats:
    sent: int | None
    received: int | None
    loss_pct: float | None
    average_ms: float | None


@dataclass(frozen=True)
class LocalBaselineStats:
    status: str | None
    median_ms: float | None
    sample_count: int | None


@dataclass(frozen=True)
class LatencyCheck:
    name: str
    status: str
    evidence: str


@dataclass(frozen=True)
class VpsLatencyReportOutput:
    status: str
    report_path: Path
    checks: tuple[LatencyCheck, ...]


def generate_phase2_vps_latency_report(
    root: Path,
    report_path: Path | None = None,
    provider: str = "",
    region: str = "",
    endpoint: str = "",
    ping_output_path: Path | None = None,
    tracert_output_path: Path | None = None,
    test_net_output_path: Path | None = None,
    local_baseline_path: Path | None = None,
) -> VpsLatencyReportOutput:
    root = root.resolve()
    report_path = (root / DEFAULT_REPORT if report_path is None else report_path).resolve()
    local_baseline_path = root / DEFAULT_LOCAL_BASELINE if local_baseline_path is None else local_baseline_path
    ping_text = _read_optional_text(ping_output_path)
    tracert_text = _read_optional_text(tracert_output_path)
    test_net_text = _read_optional_text(test_net_output_path)
    baseline_text = _read_optional_text(local_baseline_path)
    ping_stats = parse_ping_output(ping_text) if ping_text else None
    baseline_stats = parse_local_baseline_report(baseline_text) if baseline_text else None

    checks = [
        _selection_check(provider, region, endpoint),
        _ping_evidence_check(ping_output_path, ping_text, ping_stats),
        _packet_loss_check(ping_stats),
        _latency_threshold_check(ping_stats),
        _local_baseline_check(local_baseline_path, baseline_stats, ping_stats),
        _tracert_check(tracert_output_path, tracert_text),
        _test_net_check(test_net_output_path, test_net_text),
    ]
    status = _overall_status(checks)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _render_report(
            status=status,
            root=root,
            provider=provider,
            region=region,
            endpoint=endpoint,
            checks=checks,
            ping_stats=ping_stats,
            baseline_stats=baseline_stats,
            ping_output_path=ping_output_path,
            tracert_output_path=tracert_output_path,
            test_net_output_path=test_net_output_path,
            local_baseline_path=local_baseline_path,
        ),
        encoding="utf-8",
    )
    return VpsLatencyReportOutput(status, report_path, tuple(checks))


def parse_ping_output(text: str) -> PingStats:
    sent = received = None
    loss_pct = average_ms = None

    packets_match = re.search(
        r"Sent\s*=\s*(?P<sent>\d+),\s*Received\s*=\s*(?P<received>\d+),\s*Lost\s*=\s*\d+\s*\((?P<loss>[\d.]+)%\s*loss\)",
        text,
        flags=re.IGNORECASE,
    )
    if packets_match:
        sent = int(packets_match.group("sent"))
        received = int(packets_match.group("received"))
        loss_pct = float(packets_match.group("loss"))

    average_match = re.search(r"Average\s*=\s*(?P<avg>[\d.]+)\s*ms", text, flags=re.IGNORECASE)
    if average_match:
        average_ms = float(average_match.group("avg"))

    linux_packets = re.search(
        r"(?P<sent>\d+)\s+packets transmitted,\s+(?P<received>\d+)\s+(?:packets )?received,\s+(?P<loss>[\d.]+)%\s+packet loss",
        text,
        flags=re.IGNORECASE,
    )
    if linux_packets:
        sent = int(linux_packets.group("sent"))
        received = int(linux_packets.group("received"))
        loss_pct = float(linux_packets.group("loss"))

    linux_rtt = re.search(
        r"(?:rtt|round-trip).*?=\s*[\d.]+/(?P<avg>[\d.]+)/[\d.]+",
        text,
        flags=re.IGNORECASE,
    )
    if linux_rtt:
        average_ms = float(linux_rtt.group("avg"))

    return PingStats(sent=sent, received=received, loss_pct=loss_pct, average_ms=average_ms)


def parse_local_baseline_report(text: str) -> LocalBaselineStats:
    status_match = re.search(r"^Overall status:\s*(?P<status>\w+)\s*$", text, flags=re.IGNORECASE | re.MULTILINE)
    status = status_match.group("status").upper() if status_match else None

    sample_count = None
    samples_match = re.search(
        r"^\|\s*(?P<samples>\d+)\s*\|\s*[^|\n]+\|\s*(?P<median>[\d.]+)\s*ms\s*\|",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    median_ms = None
    if samples_match:
        sample_count = int(samples_match.group("samples"))
        median_ms = float(samples_match.group("median"))
    else:
        median_match = re.search(r"\|\s*Median Ping\s*\|.*?\n\|.*?\n\|[^|\n]*\|[^|\n]*\|\s*(?P<median>[\d.]+)\s*ms", text, flags=re.IGNORECASE | re.DOTALL)
        if median_match:
            median_ms = float(median_match.group("median"))

    return LocalBaselineStats(status=status, median_ms=median_ms, sample_count=sample_count)


def _selection_check(provider: str, region: str, endpoint: str) -> LatencyCheck:
    missing = [
        name
        for name, value in (("provider", provider), ("region", region), ("endpoint", endpoint))
        if not value.strip()
    ]
    if missing:
        return LatencyCheck(
            "selection_fields",
            "PENDING",
            "Missing field(s): " + ", ".join(missing) + ".",
        )
    return LatencyCheck(
        "selection_fields",
        "PASS",
        f"provider={provider}; region={region}; endpoint={endpoint}.",
    )


def _ping_evidence_check(path: Path | None, text: str, stats: PingStats | None) -> LatencyCheck:
    if path is None or not text:
        return LatencyCheck("ping_evidence", "PENDING", "No ping evidence file provided.")
    if stats is None or stats.average_ms is None or stats.loss_pct is None:
        return LatencyCheck("ping_evidence", "FAIL", f"Ping evidence could not be parsed: `{path}`.")
    if stats.sent is None or stats.sent < MIN_PING_SAMPLES:
        return LatencyCheck(
            "ping_evidence",
            "PENDING",
            f"Ping evidence has {stats.sent or 0} sample(s); at least {MIN_PING_SAMPLES} are required.",
        )
    return LatencyCheck(
        "ping_evidence",
        "PASS",
        f"Parsed ping evidence from `{path}`: {stats.sent} sample(s), average {stats.average_ms:.2f} ms, loss {stats.loss_pct:.2f}%.",
    )


def _packet_loss_check(stats: PingStats | None) -> LatencyCheck:
    if stats is None or stats.loss_pct is None:
        return LatencyCheck("packet_loss", "PENDING", "Packet loss evidence is not available yet.")
    if stats.loss_pct == 0:
        return LatencyCheck("packet_loss", "PASS", "Packet loss is 0%.")
    return LatencyCheck("packet_loss", "FAIL", f"Packet loss is {stats.loss_pct:.2f}%; retest or reject the region.")


def _latency_threshold_check(stats: PingStats | None) -> LatencyCheck:
    if stats is None or stats.average_ms is None:
        return LatencyCheck("latency_threshold", "PENDING", "Average latency evidence is not available yet.")
    if stats.average_ms <= PREFERRED_LATENCY_MS:
        return LatencyCheck(
            "latency_threshold",
            "PASS",
            f"Average latency {stats.average_ms:.2f} ms is preferred (<= {PREFERRED_LATENCY_MS:.0f} ms).",
        )
    if stats.average_ms <= MAX_ACCEPTABLE_LATENCY_MS:
        return LatencyCheck(
            "latency_threshold",
            "PASS",
            f"Average latency {stats.average_ms:.2f} ms is acceptable for Phase 2 paper measurement.",
        )
    return LatencyCheck(
        "latency_threshold",
        "FAIL",
        f"Average latency {stats.average_ms:.2f} ms exceeds {MAX_ACCEPTABLE_LATENCY_MS:.0f} ms; owner review required.",
    )


def _local_baseline_check(
    path: Path | None,
    baseline: LocalBaselineStats | None,
    stats: PingStats | None,
) -> LatencyCheck:
    if path is None or not path.exists():
        return LatencyCheck("local_baseline_comparison", "PENDING", "Local MT5 network baseline report is missing.")
    if baseline is None or baseline.status != "PASS" or baseline.median_ms is None:
        return LatencyCheck(
            "local_baseline_comparison",
            "PENDING",
            f"Local MT5 network baseline is incomplete or not PASS: `{path}`.",
        )
    if stats is None or stats.average_ms is None:
        return LatencyCheck(
            "local_baseline_comparison",
            "PENDING",
            "VPS average latency is not available for local-baseline comparison.",
        )

    target_ms = baseline.median_ms * MATERIAL_IMPROVEMENT_RATIO
    improvement_pct = ((baseline.median_ms - stats.average_ms) / baseline.median_ms) * 100.0
    if stats.average_ms <= target_ms:
        return LatencyCheck(
            "local_baseline_comparison",
            "PASS",
            f"VPS average latency {stats.average_ms:.2f} ms improves on local median {baseline.median_ms:.2f} ms by {improvement_pct:.1f}% (required >= 10.0%).",
        )
    if stats.average_ms < baseline.median_ms:
        return LatencyCheck(
            "local_baseline_comparison",
            "WARN",
            f"VPS average latency {stats.average_ms:.2f} ms beats local median {baseline.median_ms:.2f} ms by only {improvement_pct:.1f}%; owner review required.",
        )
    return LatencyCheck(
        "local_baseline_comparison",
        "FAIL",
        f"VPS average latency {stats.average_ms:.2f} ms does not beat local median {baseline.median_ms:.2f} ms; choose another region/provider or require owner exception.",
    )


def _tracert_check(path: Path | None, text: str) -> LatencyCheck:
    if path is None or not text:
        return LatencyCheck("traceroute_evidence", "PENDING", "No traceroute evidence file provided.")
    return LatencyCheck("traceroute_evidence", "PASS", f"Traceroute evidence captured in `{path}`.")


def _test_net_check(path: Path | None, text: str) -> LatencyCheck:
    if path is None or not text:
        return LatencyCheck("port_reachability_evidence", "PENDING", "No Test-NetConnection evidence file provided.")
    if re.search(r"TcpTestSucceeded\s*:\s*True", text, flags=re.IGNORECASE):
        return LatencyCheck("port_reachability_evidence", "PASS", f"Port reachability evidence passed in `{path}`.")
    if "TcpTestSucceeded" in text:
        return LatencyCheck("port_reachability_evidence", "FAIL", f"Port reachability did not pass in `{path}`.")
    return LatencyCheck(
        "port_reachability_evidence",
        "WARN",
        f"`{path}` exists but does not contain TcpTestSucceeded; review manually.",
    )


def _read_optional_text(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _overall_status(checks: list[LatencyCheck]) -> str:
    if any(check.status == "FAIL" for check in checks):
        return "FAIL"
    if any(check.status in {"PENDING", "WARN"} for check in checks):
        return "PENDING"
    return "PASS"


def _render_report(
    status: str,
    root: Path,
    provider: str,
    region: str,
    endpoint: str,
    checks: list[LatencyCheck],
    ping_stats: PingStats | None,
    baseline_stats: LocalBaselineStats | None,
    ping_output_path: Path | None,
    tracert_output_path: Path | None,
    test_net_output_path: Path | None,
    local_baseline_path: Path | None,
) -> str:
    improvement = _fmt_improvement(ping_stats, baseline_stats)
    return "\n".join(
        [
            "# Phase 2 VPS Latency Report",
            "",
            f"Overall status: {status}",
            "",
            "## Decision",
            "",
            _decision_text(status),
            "",
            "## Candidate",
            "",
            _markdown_table(
                [
                    {
                        "Provider": provider or "Pending",
                        "Region": region or "Pending",
                        "Endpoint": endpoint or "Pending",
                        "Average Ping": "" if ping_stats is None or ping_stats.average_ms is None else f"{ping_stats.average_ms:.2f} ms",
                        "Packet Loss": "" if ping_stats is None or ping_stats.loss_pct is None else f"{ping_stats.loss_pct:.2f}%",
                        "Local Median": "" if baseline_stats is None or baseline_stats.median_ms is None else f"{baseline_stats.median_ms:.2f} ms",
                        "Improvement": improvement,
                    }
                ],
                ["Provider", "Region", "Endpoint", "Average Ping", "Packet Loss", "Local Median", "Improvement"],
            ),
            "",
            "## Checks",
            "",
            _markdown_table(
                [{"Check": check.name, "Status": check.status, "Evidence": check.evidence} for check in checks],
                ["Check", "Status", "Evidence"],
            ),
            "",
            "## Evidence Paths",
            "",
            f"- Ping output: `{ping_output_path or 'pending'}`",
            f"- Traceroute output: `{tracert_output_path or 'pending'}`",
            f"- Test-NetConnection output: `{test_net_output_path or 'pending'}`",
            f"- Local MT5 baseline: `{local_baseline_path or 'pending'}`",
            "",
            "## Capture Commands",
            "",
            "Run these commands on the candidate VPS after it is provisioned:",
            "",
            "```powershell",
            ".\\scripts\\capture_phase2_vps_latency_evidence.ps1 -Provider \"<provider>\" -Region \"<region>\" -Endpoint \"<broker_or_mt5_endpoint>\" -SampleCount 20",
            "```",
            "",
            "Manual fallback:",
            "",
            "```powershell",
            "$endpoint = \"<broker_or_mt5_endpoint>\"",
            "ping -n 20 $endpoint | Tee-Object -FilePath outputs\\reports\\vps_ping.txt",
            "tracert $endpoint | Tee-Object -FilePath outputs\\reports\\vps_tracert.txt",
            "Test-NetConnection $endpoint -Port 443 | Tee-Object -FilePath outputs\\reports\\vps_test_net.txt",
            "python scripts\\generate_phase2_vps_latency_report.py --provider \"<provider>\" --region \"<region>\" --endpoint $endpoint --ping-output outputs\\reports\\vps_ping.txt --tracert-output outputs\\reports\\vps_tracert.txt --test-net-output outputs\\reports\\vps_test_net.txt",
            "```",
            "",
            "## Boundary",
            "",
            "- This report is evidence-only and does not authorize Phase 2 paper-mode implementation.",
            "- Passing latency evidence does not authorize live capital or broker-side execution.",
            "- A VPS latency PASS requires a PASS local MT5 baseline and at least 10% better average ping than the local median.",
            "- Keep `dry_run=true` and `trade_permission=false` until all Phase 2 readiness gates pass and the owner signs approval.",
            f"- Workspace root: `{root}`",
            "",
        ]
    )


def _decision_text(status: str) -> str:
    if status == "PASS":
        return "The VPS candidate has enough latency evidence and beats the local MT5 baseline for owner review."
    if status == "FAIL":
        return "The VPS candidate failed latency or reachability checks. Retest another region/provider before selection."
    return "VPS latency evidence is not complete yet. Keep VPS selection and Phase 2 readiness pending."


def _fmt_improvement(stats: PingStats | None, baseline: LocalBaselineStats | None) -> str:
    if stats is None or stats.average_ms is None or baseline is None or baseline.median_ms is None:
        return ""
    return f"{((baseline.median_ms - stats.average_ms) / baseline.median_ms) * 100.0:.1f}%"


def _markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_escape(str(row.get(column, ""))) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Phase 2 VPS latency evidence report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--provider", default="")
    parser.add_argument("--region", default="")
    parser.add_argument("--endpoint", default="")
    parser.add_argument("--ping-output", type=Path, default=None)
    parser.add_argument("--tracert-output", type=Path, default=None)
    parser.add_argument("--test-net-output", type=Path, default=None)
    parser.add_argument("--local-baseline", type=Path, default=None)
    args = parser.parse_args(argv)

    output = generate_phase2_vps_latency_report(
        root=args.root,
        report_path=args.report,
        provider=args.provider,
        region=args.region,
        endpoint=args.endpoint,
        ping_output_path=args.ping_output,
        tracert_output_path=args.tracert_output,
        test_net_output_path=args.test_net_output,
        local_baseline_path=args.local_baseline,
    )
    print(f"Phase 2 VPS latency report: {output.status}")
    print(output.report_path)
    for check in output.checks:
        print(f"{check.status}: {check.name} - {check.evidence}")
    return 1 if output.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
