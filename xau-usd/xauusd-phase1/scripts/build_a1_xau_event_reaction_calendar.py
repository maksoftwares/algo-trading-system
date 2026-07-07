from __future__ import annotations

import csv
import hashlib
import json
import re
import urllib.error
import urllib.request
from datetime import date, datetime, time, timezone
from html import unescape
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
DATA_DIR = PHASE1_ROOT / "data" / "external" / "event_reaction_calendar"
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"

START_DATE = date(2022, 7, 1)
END_DATE = date(2026, 6, 30)
NY_ZONE = ZoneInfo("America/New_York")

FED_FOMC_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
BLS_YEAR_URLS = {
    2022: "https://www.bls.gov/schedule/2022/home.htm",
    2023: "https://www.bls.gov/schedule/2023/home.htm",
    2024: "https://www.bls.gov/schedule/2024/home.htm",
    2025: "https://www.bls.gov/schedule/2025/home.htm",
    2026: "https://www.bls.gov/schedule/news_release/current_year.asp",
}

OUTPUT_STEM = "A1_XAU_EVENT_REACTION_CALENDAR_202207_202606"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def fetch_url(url: str) -> tuple[bytes | None, dict[str, Any]]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 Codex A1 XAU event calendar provenance",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read()
            return data, {
                "url": url,
                "status": "FETCH_OK",
                "http_status": response.status,
                "content_type": response.headers.get("content-type", ""),
                "byte_count": len(data),
                "sha256": sha256_bytes(data),
            }
    except urllib.error.HTTPError as exc:
        return None, {
            "url": url,
            "status": "FETCH_FAILED",
            "http_status": exc.code,
            "error": str(exc),
        }
    except OSError as exc:
        return None, {
            "url": url,
            "status": "FETCH_FAILED",
            "error": type(exc).__name__,
            "message": str(exc),
        }


def parse_fomc_events(html_text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for match in re.finditer(r"monetary(?P<ymd>20(?:22|23|24|25|26)\d{4})a\.htm", html_text):
        context = html_text[max(0, match.start() - 600) : match.start()]
        if "notation vote" in context.lower() or "Statement:</strong>" not in context:
            continue
        ymd = match.group("ymd")
        decision_day = datetime.strptime(ymd, "%Y%m%d").date()
        if not (START_DATE <= decision_day <= END_DATE):
            continue
        local_dt = datetime.combine(decision_day, time(14, 0), tzinfo=NY_ZONE)
        events.append(
            event_row(
                event_type="FOMC",
                event_name="FOMC_STATEMENT",
                local_dt=local_dt,
                source_url=FED_FOMC_URL,
                provenance_tier="FED_OFFICIAL_FETCHED",
                source_rule="FOMC statement link date parsed from Federal Reserve FOMC calendar; release time fixed at 14:00 ET.",
            )
        )
    unique: dict[str, dict[str, Any]] = {}
    for row in events:
        unique[row["event_id"]] = row
    return sorted(unique.values(), key=lambda row: row["timestamp_utc"])


def parse_bls_events(html_text: str, source_url: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    pattern = re.compile(
        r'<tr[^>]*>\s*'
        r'<td class="date-cell"><p>(?P<date>.*?)</p></td>\s*'
        r'<td class="time-cell"><p>(?P<time>.*?)</p></td>\s*'
        r'<td class="desc-cell"><p><strong>(?P<title>.*?)</strong>(?P<tail>.*?)</p></td>\s*'
        r"</tr>",
        re.DOTALL | re.IGNORECASE,
    )
    for match in pattern.finditer(html_text):
        title = clean_html(match.group("title"))
        if title not in {"Employment Situation", "Consumer Price Index"}:
            continue
        date_text = clean_html(match.group("date"))
        time_text = clean_html(match.group("time"))
        if time_text != "08:30 AM":
            continue
        try:
            local_day = datetime.strptime(date_text, "%A, %B %d, %Y").date()
        except ValueError:
            continue
        if not (START_DATE <= local_day <= END_DATE):
            continue
        event_type = "NFP" if title == "Employment Situation" else "CPI"
        event_name = "EMPLOYMENT_SITUATION_OFFICIAL" if event_type == "NFP" else "CPI_OFFICIAL"
        events.append(
            event_row(
                event_type=event_type,
                event_name=event_name,
                local_dt=datetime.combine(local_day, time(8, 30), tzinfo=NY_ZONE),
                source_url=source_url,
                provenance_tier="BLS_OFFICIAL_FETCHED",
                source_rule=f"{title} release row parsed from official BLS release calendar; all BLS calendar times are Eastern Time.",
            )
        )
    return events


def clean_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", "", value)
    text = unescape(text).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def build_bls_rejection_only_events() -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    current = date(START_DATE.year, START_DATE.month, 1)
    while current <= END_DATE:
        year = current.year
        month = current.month
        nfp_day = nth_weekday(year, month, weekday=4, occurrence=1)
        cpi_day = nth_weekday(year, month, weekday=2, occurrence=2)
        for event_type, event_name, local_day, source_rule in (
            (
                "NFP",
                "NFP_FIRST_FRIDAY_APPROX",
                nfp_day,
                "Deterministic first-Friday approximation because BLS official schedule fetch returned 403 locally; rejection-only, not acceptance-grade.",
            ),
            (
                "CPI",
                "CPI_SECOND_WEDNESDAY_APPROX",
                cpi_day,
                "Deterministic second-Wednesday approximation because BLS official schedule fetch returned 403 locally; rejection-only, not acceptance-grade.",
            ),
        ):
            if START_DATE <= local_day <= END_DATE:
                events.append(
                    event_row(
                        event_type=event_type,
                        event_name=event_name,
                        local_dt=datetime.combine(local_day, time(8, 30), tzinfo=NY_ZONE),
                        source_url=BLS_YEAR_URLS[year],
                        provenance_tier="BLS_APPROX_REJECTION_ONLY",
                        source_rule=source_rule,
                    )
                )
        if month == 12:
            current = date(year + 1, 1, 1)
        else:
            current = date(year, month + 1, 1)
    return events


def event_row(
    *,
    event_type: str,
    event_name: str,
    local_dt: datetime,
    source_url: str,
    provenance_tier: str,
    source_rule: str,
) -> dict[str, Any]:
    utc_dt = local_dt.astimezone(timezone.utc)
    event_id = f"{event_type}_{local_dt.date().isoformat()}"
    return {
        "event_id": event_id,
        "event_type": event_type,
        "event_name": event_name,
        "local_date": local_dt.date().isoformat(),
        "local_time_et": local_dt.strftime("%H:%M"),
        "timezone": "America/New_York",
        "timestamp_utc": utc_dt.isoformat().replace("+00:00", "Z"),
        "provenance_tier": provenance_tier,
        "source_url": source_url,
        "source_rule": source_rule,
    }


def nth_weekday(year: int, month: int, weekday: int, occurrence: int) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return date(year, month, 1 + offset + 7 * (occurrence - 1))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "event_id",
        "event_type",
        "event_name",
        "local_date",
        "local_time_et",
        "timezone",
        "timestamp_utc",
        "provenance_tier",
        "source_url",
        "source_rule",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def render_markdown(payload: dict[str, Any]) -> str:
    rows = payload["event_counts"]
    if payload.get("acceptance_ready"):
        provenance_read = (
            "FOMC events are official-provenance because the Federal Reserve calendar was fetched and hashed locally. "
            "NFP and CPI events are official-provenance because the BLS yearly release-calendar pages were fetched, hashed, "
            "and parsed from their release tables."
        )
        blocker_read = (
            "Calendar provenance is frozen for the first exact-MT5 event-reaction implementation. "
            "This still does not approve a strategy or demo spec; it only removes the event-calendar provenance blocker."
        )
    else:
        provenance_read = (
            "FOMC events are official-provenance because the Federal Reserve calendar was fetched and hashed locally. "
            "NFP and CPI events are provisional rejection-only approximations because BLS schedule pages were not fully "
            "available to local scripted parsing."
        )
        blocker_read = (
            "Before an event-reaction candidate can be promoted beyond rejection-only smoke testing, replace the BLS "
            "approximation rows with official BLS release-date rows, freeze the raw source or manual export, and record "
            "SHA256 provenance."
        )
    lines = [
        "# A1 XAU Event-Reaction Calendar Provenance",
        "",
        "Date: 2026-07-07",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Boundary",
        "",
        "This freezes the current calendar provenance state for the event-reaction branch. It does not run MT5, does not approve a strategy, and does not make any trading result acceptance-ready.",
        "",
        provenance_read,
        "",
        "## Counts",
        "",
        "| Event type | Provenance | Count |",
        "|---|---|---:|",
    ]
    for row in rows:
        lines.append(f"| `{row['event_type']}` | `{row['provenance_tier']}` | {row['count']} |")
    lines.extend(
        [
            "",
            "## Files",
            "",
            f"- Calendar CSV: `{rel(Path(payload['outputs']['calendar_csv']))}`",
            f"- Manifest JSON: `{rel(Path(payload['outputs']['manifest_json']))}`",
            f"- Report: `{rel(Path(payload['outputs']['report_md']))}`",
            f"- Calendar CSV SHA256: `{payload['calendar_csv_sha256']}`",
            "",
            "## Source Fetches",
            "",
            "| Source | Status | Detail |",
            "|---|---|---|",
        ]
    )
    for fetch in payload["source_fetches"]:
        detail = fetch.get("sha256") or fetch.get("error") or fetch.get("message") or ""
        lines.append(f"| `{fetch['url']}` | `{fetch['status']}` | `{detail}` |")
    lines.extend(
        [
            "",
            "## Acceptance Blocker",
            "",
            blocker_read,
            "",
        ]
    )
    return "\n".join(lines)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    source_fetches: list[dict[str, Any]] = []
    fed_html, fed_fetch = fetch_url(FED_FOMC_URL)
    source_fetches.append(fed_fetch)
    if fed_html:
        raw_fed = DATA_DIR / f"{OUTPUT_STEM}_FED_FOMC_RAW.html"
        raw_fed.write_bytes(fed_html)
        fomc_events = parse_fomc_events(fed_html.decode("utf-8", errors="replace"))
    else:
        fomc_events = []

    bls_official_events: list[dict[str, Any]] = []
    bls_fetch_failed = False
    for year, url in BLS_YEAR_URLS.items():
        data, fetch = fetch_url(url)
        source_fetches.append(fetch)
        if data:
            raw_bls = DATA_DIR / f"{OUTPUT_STEM}_BLS_{year}_RAW.html"
            raw_bls.write_bytes(data)
            bls_official_events.extend(parse_bls_events(data.decode("utf-8", errors="replace"), url))
        else:
            bls_fetch_failed = True

    bls_events = bls_official_events
    if bls_fetch_failed or not bls_events:
        bls_events = build_bls_rejection_only_events()

    events = sorted([*bls_events, *fomc_events], key=lambda row: (row["timestamp_utc"], row["event_type"]))
    calendar_csv = DATA_DIR / f"{OUTPUT_STEM}.csv"
    manifest_json = DATA_DIR / f"{OUTPUT_STEM}.manifest.json"
    report_md = REPORTS_DIR / f"{OUTPUT_STEM}_PROVENANCE.md"
    write_csv(calendar_csv, events)

    counts: dict[tuple[str, str], int] = {}
    for row in events:
        key = (row["event_type"], row["provenance_tier"])
        counts[key] = counts.get(key, 0) + 1
    event_counts = [
        {"event_type": event_type, "provenance_tier": provenance_tier, "count": count}
        for (event_type, provenance_tier), count in sorted(counts.items())
    ]
    acceptance_ready = bool(fomc_events) and not bls_fetch_failed and all(
        row["provenance_tier"] in {"BLS_OFFICIAL_FETCHED", "FED_OFFICIAL_FETCHED"} for row in events
    )
    status = "EVENT_CALENDAR_OFFICIAL_PROVENANCE_FROZEN_NO_MT5_RUN" if acceptance_ready else "EVENT_CALENDAR_PARTIAL_PROVENANCE_REJECTION_ONLY"
    if not fomc_events:
        status = "EVENT_CALENDAR_PROVENANCE_INCOMPLETE_NO_OFFICIAL_EVENTS"

    payload = {
        "status": status,
        "window": {"start": START_DATE.isoformat(), "end": END_DATE.isoformat()},
        "calendar_csv_sha256": sha256_file(calendar_csv),
        "event_counts": event_counts,
        "source_fetches": source_fetches,
        "acceptance_ready": acceptance_ready,
        "acceptance_blocker": None
        if acceptance_ready
        else "BLS NFP/CPI rows are deterministic approximations; official BLS release-date provenance is required before promotion.",
        "outputs": {
            "calendar_csv": str(calendar_csv),
            "manifest_json": str(manifest_json),
            "report_md": str(report_md),
        },
    }
    manifest_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": status, "events": len(events), "calendar_csv": str(calendar_csv)}, indent=2))


if __name__ == "__main__":
    main()
