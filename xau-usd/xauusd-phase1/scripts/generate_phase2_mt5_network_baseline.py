from __future__ import annotations

import argparse
import re
import statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_REPORT = Path("outputs") / "reports" / "PHASE2_LOCAL_MT5_NETWORK_BASELINE.md"
AUTH_RE = re.compile(
    r"(?P<time>\d{2}:\d{2}:\d{2}\.\d{3}).*?authorized on (?P<server>.+?) "
    r"through Access Point (?P<access_point>\d+) \(ping: (?P<ping>[\d.]+) ms",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class AccessPointPing:
    timestamp: datetime
    server: str
    access_point: str
    ping_ms: float
    source_file: Path


@dataclass(frozen=True)
class NetworkBaselineOutput:
    status: str
    report_path: Path
    sample_count: int
    latest_ping_ms: float | None
    median_ping_ms: float | None
    best_ping_ms: float | None
    worst_ping_ms: float | None


def generate_phase2_mt5_network_baseline(
    logs_dir: Path,
    report_path: Path,
) -> NetworkBaselineOutput:
    logs_dir = logs_dir.resolve()
    report_path = report_path.resolve()
    samples = parse_mt5_access_point_pings(logs_dir)
    status = "PASS" if samples else "PENDING"
    pings = [sample.ping_ms for sample in samples]
    latest_ping = samples[-1].ping_ms if samples else None
    median_ping = statistics.median(pings) if pings else None
    best_ping = min(pings) if pings else None
    worst_ping = max(pings) if pings else None

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _render_report(
            status=status,
            logs_dir=logs_dir,
            samples=samples,
            latest_ping=latest_ping,
            median_ping=median_ping,
            best_ping=best_ping,
            worst_ping=worst_ping,
        ),
        encoding="utf-8",
    )
    return NetworkBaselineOutput(
        status=status,
        report_path=report_path,
        sample_count=len(samples),
        latest_ping_ms=latest_ping,
        median_ping_ms=median_ping,
        best_ping_ms=best_ping,
        worst_ping_ms=worst_ping,
    )


def parse_mt5_access_point_pings(logs_dir: Path) -> list[AccessPointPing]:
    if not logs_dir.exists():
        return []
    samples: list[AccessPointPing] = []
    for path in sorted(logs_dir.glob("*.log")):
        log_date = _date_from_log_name(path)
        if log_date is None:
            continue
        for line in _read_log_text(path).splitlines():
            match = AUTH_RE.search(line)
            if not match:
                continue
            timestamp = datetime.strptime(
                f"{log_date} {match.group('time')}",
                "%Y%m%d %H:%M:%S.%f",
            )
            samples.append(
                AccessPointPing(
                    timestamp=timestamp,
                    server=match.group("server").strip(),
                    access_point=match.group("access_point"),
                    ping_ms=float(match.group("ping")),
                    source_file=path,
                )
            )
    return sorted(samples, key=lambda sample: sample.timestamp)


def _read_log_text(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        return data.decode("utf-16", errors="replace")
    return data.decode("utf-8", errors="replace")


def _date_from_log_name(path: Path) -> str | None:
    match = re.fullmatch(r"(\d{8})", path.stem)
    return match.group(1) if match else None


def _render_report(
    status: str,
    logs_dir: Path,
    samples: list[AccessPointPing],
    latest_ping: float | None,
    median_ping: float | None,
    best_ping: float | None,
    worst_ping: float | None,
) -> str:
    latest = samples[-1] if samples else None
    rows = _access_point_rows(samples)
    recent_rows = [
        {
            "Timestamp": sample.timestamp.isoformat(sep=" "),
            "Server": sample.server,
            "Access Point": sample.access_point,
            "Ping": f"{sample.ping_ms:.2f} ms",
        }
        for sample in samples[-10:]
    ]
    return "\n".join(
        [
            "# Phase 2 Local MT5 Network Baseline",
            "",
            f"Overall status: {status}",
            "",
            "## Purpose",
            "",
            "This report gives a sanitized local MT5 broker-access baseline before VPS selection. It is evidence-only and does not authorize Phase 2, paper trading, demo trading, broker execution, or live capital.",
            "",
            "## Summary",
            "",
            _markdown_table(
                [
                    {
                        "Samples": str(len(samples)),
                        "Latest Ping": _fmt_ms(latest_ping),
                        "Median Ping": _fmt_ms(median_ping),
                        "Best Ping": _fmt_ms(best_ping),
                        "Worst Ping": _fmt_ms(worst_ping),
                        "Latest Access Point": latest.access_point if latest else "pending",
                    }
                ],
                ["Samples", "Latest Ping", "Median Ping", "Best Ping", "Worst Ping", "Latest Access Point"],
            ),
            "",
            "## Access Point Breakdown",
            "",
            _markdown_table(rows, ["Access Point", "Samples", "Median Ping", "Best Ping", "Worst Ping"]),
            "",
            "## Recent Authorization Pings",
            "",
            _markdown_table(recent_rows, ["Timestamp", "Server", "Access Point", "Ping"]),
            "",
            "## VPS Selection Use",
            "",
            "- A candidate VPS should be compared against this local baseline using `PHASE2_VPS_LATENCY_REPORT.md`.",
            "- Prefer a VPS/region that materially improves on local median ping and has 0% packet loss.",
            "- If a VPS cannot beat this local baseline, owner review is required before treating it as an operational improvement.",
            "- MT5 terminal logs do not expose a stable broker DNS endpoint here, so the VPS latency packet still needs broker endpoint evidence from the selected VPS or MT5 connection UI/logs.",
            "",
            "## Privacy Boundary",
            "",
            "- Account identifiers and previous authorization IP addresses are intentionally excluded.",
            "- Source log lines are not copied into this report.",
            "- No credentials, tokens, or server-cache files are included.",
            "",
            "## Source",
            "",
            f"- Logs directory: `{logs_dir}`",
            "",
        ]
    )


def _access_point_rows(samples: list[AccessPointPing]) -> list[dict[str, str]]:
    grouped: dict[str, list[float]] = {}
    for sample in samples:
        grouped.setdefault(sample.access_point, []).append(sample.ping_ms)
    return [
        {
            "Access Point": access_point,
            "Samples": str(len(values)),
            "Median Ping": _fmt_ms(statistics.median(values)),
            "Best Ping": _fmt_ms(min(values)),
            "Worst Ping": _fmt_ms(max(values)),
        }
        for access_point, values in sorted(grouped.items(), key=lambda item: item[0])
    ]


def _fmt_ms(value: float | None) -> str:
    return "pending" if value is None else f"{value:.2f} ms"


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
    parser = argparse.ArgumentParser(description="Generate a sanitized local MT5 network baseline for Phase 2 VPS selection.")
    parser.add_argument("--logs-dir", type=Path, default=Path("C:/MT5PortableGoldMission/logs"))
    parser.add_argument("--report", type=Path, default=Path(__file__).resolve().parents[1] / DEFAULT_REPORT)
    args = parser.parse_args(argv)

    output = generate_phase2_mt5_network_baseline(args.logs_dir, args.report)
    print(f"Phase 2 local MT5 network baseline: {output.status}")
    print(output.report_path)
    print(f"samples={output.sample_count}")
    if output.latest_ping_ms is not None:
        print(f"latest_ping_ms={output.latest_ping_ms:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
