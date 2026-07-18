from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from typing import Any
import urllib.parse
import urllib.request


NFP_LINK = re.compile(r"empsit_(\d{8})\.(?:htm|html|pdf)$", re.IGNORECASE)


@dataclass(frozen=True)
class ArchiveLink:
    href: str
    text: str


class BLSArchiveParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[ArchiveLink] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag.lower() != "a":
            return
        attributes = dict(attrs)
        href = attributes.get("href")
        if href and NFP_LINK.search(href):
            self._href = href
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            self.links.append(
                ArchiveLink(self._href, " ".join("".join(self._text).split()))
            )
            self._href = None
            self._text = []


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_bls_nfp_archive(
    html: str, base_url: str, start_date: str, end_exclusive_date: str
) -> list[dict[str, str]]:
    parser = BLSArchiveParser()
    parser.feed(html)
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_exclusive_date).date()
    by_date: dict[str, ArchiveLink] = {}
    for link in parser.links:
        match = NFP_LINK.search(link.href)
        if match is None:
            continue
        release = datetime.strptime(match.group(1), "%m%d%Y").date()
        if not start <= release < end:
            continue
        date_text = release.isoformat()
        existing = by_date.get(date_text)
        if existing is None or link.href.lower().endswith((".htm", ".html")):
            by_date[date_text] = link
    return [
        {
            "title": "Employment Situation",
            "date": date_text,
            "reference": by_date[date_text].text,
            "primaryUrl": urllib.parse.urljoin(base_url, by_date[date_text].href),
            "release_time_rule": "08:30 America/New_York",
        }
        for date_text in sorted(by_date)
    ]


def _request_bytes(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "xau-out-of-era-research/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def acquire_bls_calendar(
    url: str,
    output: Path,
    start_date: str,
    end_exclusive_date: str,
    expected_releases: int,
    snapshot_path: Path | None = None,
) -> dict[str, Any]:
    raw = snapshot_path.read_bytes() if snapshot_path is not None else _request_bytes(url)
    rows = parse_bls_nfp_archive(
        raw.decode("utf-8", errors="strict"),
        url,
        start_date,
        end_exclusive_date,
    )
    if len(rows) != expected_releases:
        raise ValueError(
            f"Expected {expected_releases} official NFP releases, found {len(rows)}"
        )
    dates = [row["date"] for row in rows]
    if len(dates) != len(set(dates)):
        raise ValueError("Duplicate official NFP release dates")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    return {
        "source_url": url,
        "source_transport": (
            "BROWSER_DOM_SNAPSHOT" if snapshot_path is not None else "DIRECT_HTTPS"
        ),
        "source_snapshot_path": str(snapshot_path) if snapshot_path is not None else "",
        "source_page_sha256": hashlib.sha256(raw).hexdigest(),
        "output_sha256": sha256_file(output),
        "rows": len(rows),
        "first_release": dates[0],
        "last_release": dates[-1],
    }


def acquire_gld_daily(
    url: str,
    symbol: str,
    output: Path,
    start_utc: str,
    end_exclusive_utc: str,
    minimum_rows: int,
) -> dict[str, Any]:
    start = datetime.fromisoformat(start_utc.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_exclusive_utc.replace("Z", "+00:00"))
    query = urllib.parse.urlencode(
        {
            "period1": int(start.timestamp()),
            "period2": int(end.timestamp()),
            "interval": "1d",
            "events": "history",
        }
    )
    request_url = f"{url}?{query}"
    raw = _request_bytes(request_url)
    payload = json.loads(raw.decode("utf-8"))
    result = payload["chart"]["result"][0]
    timestamps = result.get("timestamp") or []
    quote = result["indicators"]["quote"][0]
    rows: list[dict[str, Any]] = []
    acquired_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    for index, epoch in enumerate(timestamps):
        values = {
            field: quote[field][index]
            for field in ("open", "high", "low", "close", "volume")
        }
        if any(value is None for value in values.values()):
            continue
        timestamp = datetime.fromtimestamp(int(epoch), UTC)
        rows.append(
            {
                "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z"),
                "date_utc": timestamp.date().isoformat(),
                **values,
                "source_symbol": symbol,
                "source": "Yahoo Finance chart API; public non-primary GLD ETF OHLCV proxy",
                "acquired_at_utc": acquired_at,
            }
        )
    if len(rows) < minimum_rows:
        raise ValueError(f"Expected at least {minimum_rows} GLD rows, found {len(rows)}")
    dates = [row["date_utc"] for row in rows]
    if len(dates) != len(set(dates)):
        raise ValueError("Duplicate GLD daily dates")
    if any(float(row["volume"]) <= 0.0 for row in rows):
        raise ValueError("Nonpositive GLD volume found")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return {
        "source_url": request_url,
        "source_payload_sha256": hashlib.sha256(raw).hexdigest(),
        "output_sha256": sha256_file(output),
        "rows": len(rows),
        "first_date": dates[0],
        "last_date": dates[-1],
    }
