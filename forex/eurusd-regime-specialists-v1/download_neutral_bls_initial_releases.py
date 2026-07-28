from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd
from pypdf import PdfReader


EVENT_SOURCE = Path(
    "D:/AlgoTradingData/research/"
    "eurusd-neutral-dukascopy-event-timing-v1/"
    "DUKASCOPY_ECONOMIC_EVENTS.parquet"
)
DEFAULT_OUTPUT_ROOT = Path(
    "D:/AlgoTradingData/research/"
    "eurusd-neutral-bls-initial-release-v1"
)
BASE_URL = "https://www.bls.gov/news.release/archives"
USER_AGENT = (
    "Mozilla/5.0 compatible; causal-market-research/1.0; "
    "public-data-only"
)
SCHEMA_VERSION = "eurusd_neutral_bls_initial_release_v1"
FAMILIES = {
    "CPI": {
        "event_title": "Consumer Price Index",
        "slug": "cpi",
        "metric": "headline_cpi_monthly_percent_change",
        "unit": "percent",
    },
    "PPI": {
        "event_title": "Producer Price Index",
        "slug": "ppi",
        "metric": "final_demand_ppi_monthly_percent_change",
        "unit": "percent",
    },
    "NFP": {
        "event_title": "Nonfarm Payrolls",
        "slug": "empsit",
        "metric": "total_nonfarm_payroll_monthly_change",
        "unit": "persons",
    },
}
UP_VERBS = (
    "increased",
    "rose",
    "advanced",
    "moved up",
    "edged up",
    "inched up",
    "grew",
    "gained",
    "added",
)
DOWN_VERBS = (
    "decreased",
    "declined",
    "fell",
    "moved down",
    "edged down",
    "inched down",
    "dropped",
    "lost",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def expected_releases(events: pd.DataFrame) -> pd.DataFrame:
    frame = events.copy()
    frame["event_time_utc"] = pd.to_datetime(
        frame["event_time_utc"], utc=True
    )
    pieces: list[pd.DataFrame] = []
    for family, spec in FAMILIES.items():
        selected = frame[
            frame["currency"].eq("USD")
            & frame["title"].eq(spec["event_title"])
        ].copy()
        selected["release_date"] = selected[
            "event_time_utc"
        ].dt.strftime("%Y-%m-%d")
        grouped = (
            selected.sort_values(["event_time_utc", "event_id"])
            .groupby("release_date", as_index=False)
            .agg(
                event_time_utc=("event_time_utc", "min"),
                event_ids=(
                    "event_id",
                    lambda values: "|".join(
                        sorted(values.astype(str).unique())
                    ),
                ),
            )
        )
        grouped["family"] = family
        grouped["source_url"] = grouped["release_date"].map(
            lambda value: (
                f"{BASE_URL}/{spec['slug']}_"
                f"{pd.Timestamp(value).strftime('%m%d%Y')}.pdf"
            )
        )
        pieces.append(grouped)
    result = pd.concat(pieces, ignore_index=True)
    return result.sort_values(
        ["event_time_utc", "family"]
    ).reset_index(drop=True)


def _download(url: str, path: Path, attempts: int = 4) -> None:
    if path.exists() and path.stat().st_size > 10_000:
        if path.read_bytes()[:4] == b"%PDF":
            return
    path.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/pdf",
                },
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read()
            if len(payload) <= 10_000 or payload[:4] != b"%PDF":
                raise RuntimeError(
                    f"Non-PDF or undersized response ({len(payload)} bytes)"
                )
            path.write_bytes(payload)
            return
        except (
            OSError,
            RuntimeError,
            urllib.error.URLError,
        ) as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Could not download {url}: {last_error}")


def download_archive(
    expected: pd.DataFrame,
    output_root: Path,
    workers: int,
) -> dict[str, str]:
    targets: dict[str, Path] = {}
    for row in expected.itertuples(index=False):
        target = (
            output_root
            / "raw"
            / str(row.family)
            / f"{row.release_date}.pdf"
        )
        targets[str(row.source_url)] = target
    errors: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_download, url, path): (url, path)
            for url, path in targets.items()
        }
        for future in as_completed(futures):
            url, _ = futures[future]
            try:
                future.result()
            except Exception as exc:  # noqa: BLE001
                errors[url] = str(exc)
    return errors


def extract_first_pages(path: Path, pages: int = 3) -> str:
    reader = PdfReader(path)
    text = " ".join(
        page.extract_text() or "" for page in reader.pages[:pages]
    )
    return " ".join(text.replace("\u2212", "-").split())


def _signed_number(
    verb: str,
    raw_value: str,
    scale: str | None = None,
) -> float:
    value = float(raw_value.replace(",", ""))
    if scale is not None:
        normalized_scale = scale.lower()
        if normalized_scale == "million":
            value *= 1_000_000.0
        elif normalized_scale == "thousand":
            value *= 1_000.0
        else:
            raise ValueError(f"Unknown numeric scale: {scale!r}")
    normalized = verb.lower()
    if normalized in DOWN_VERBS:
        return -value
    if normalized in UP_VERBS:
        return value
    raise ValueError(f"Unknown directional verb: {verb!r}")


def parse_release_metric(
    family: str,
    text: str,
) -> tuple[float, str]:
    verbs = "|".join(
        re.escape(value) for value in (*UP_VERBS, *DOWN_VERBS)
    )
    if family == "CPI":
        pattern = (
            r"\(CPI-U\)\s+"
            rf"(?P<verb>{verbs})\s+"
            r"(?P<value>[0-9]+(?:\.[0-9]+)?) percent"
        )
        unchanged = r"\(CPI-U\)\s+was unchanged"
    elif family == "PPI":
        pattern = (
            r"Producer Price Index for final demand\s+"
            rf"(?P<verb>{verbs})\s+"
            r"(?P<value>[0-9]+(?:\.[0-9]+)?) percent"
        )
        unchanged = (
            r"Producer Price Index for final demand\s+"
            r"(?:was\s+)?(?:essentially\s+)?unchanged"
        )
    elif family == "NFP":
        pattern = (
            r"(?:[Tt]otal\s+)?nonfarm payroll employment\s+"
            rf"(?P<verb>{verbs})\s+(?:by\s+)?"
            r"(?P<value>[0-9][0-9,]*(?:\.[0-9]+)?)"
            r"\s*(?P<scale>million|thousand)?"
        )
        unchanged = (
            r"(?:[Tt]otal\s+)?nonfarm payroll employment\s+"
            r"(?:was\s+)?(?:essentially\s+)?"
            r"(?:changed little|unchanged|edged up)"
            r".{0,80}?\((?P<signed>[+-][0-9][0-9,]*)\)"
        )
    else:
        raise ValueError(f"Unknown family: {family}")
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match is None:
        match = re.search(unchanged, text, flags=re.IGNORECASE)
        if match is None:
            raise ValueError(f"Headline metric not found for {family}")
        if family == "NFP":
            value = float(match.group("signed").replace(",", ""))
        else:
            value = 0.0
    else:
        value = _signed_number(
            match.group("verb"),
            match.group("value"),
            match.groupdict().get("scale"),
        )
    sentence_start = max(
        text.rfind(".", 0, match.start()) + 1,
        text.rfind("\n", 0, match.start()) + 1,
    )
    sentence_end = text.find(".", match.end())
    if sentence_end < 0:
        sentence_end = min(len(text), match.end() + 240)
    evidence = text[sentence_start : sentence_end + 1].strip()
    return value, evidence


def build_source(
    expected: pd.DataFrame,
    output_root: Path,
    download_errors: dict[str, str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    parse_errors: dict[str, str] = {}
    source_digest = hashlib.sha256()
    for release in expected.itertuples(index=False):
        path = (
            output_root
            / "raw"
            / str(release.family)
            / f"{release.release_date}.pdf"
        )
        if not path.exists():
            continue
        pdf_hash = sha256_file(path)
        relative = path.relative_to(output_root).as_posix()
        source_digest.update(relative.encode("utf-8"))
        source_digest.update(bytes.fromhex(pdf_hash))
        try:
            text = extract_first_pages(path)
            value, evidence = parse_release_metric(
                str(release.family), text
            )
        except Exception as exc:  # noqa: BLE001
            parse_errors[str(release.source_url)] = str(exc)
            continue
        spec = FAMILIES[str(release.family)]
        rows.append(
            {
                "family": str(release.family),
                "release_date": str(release.release_date),
                "event_time_utc": pd.Timestamp(
                    release.event_time_utc
                ),
                "event_ids": str(release.event_ids),
                "metric": spec["metric"],
                "initial_value": value,
                "unit": spec["unit"],
                "source_url": str(release.source_url),
                "source_pdf_relative_path": relative,
                "source_pdf_sha256": pdf_hash,
                "evidence_sentence": evidence,
            }
        )
    frame = pd.DataFrame(rows).sort_values(
        ["event_time_utc", "family"]
    )
    output_root.mkdir(parents=True, exist_ok=True)
    source_path = output_root / "BLS_INITIAL_RELEASES.parquet"
    frame.to_parquet(source_path, index=False, compression="zstd")
    expected_by_family = {
        family: int(expected["family"].eq(family).sum())
        for family in FAMILIES
    }
    parsed_by_family = {
        family: int(frame["family"].eq(family).sum())
        for family in FAMILIES
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "provider": "U.S. Bureau of Labor Statistics",
        "authentication_required": False,
        "source_archive": BASE_URL,
        "event_clock_source": str(EVENT_SOURCE),
        "event_clock_source_sha256": sha256_file(EVENT_SOURCE),
        "raw_pdf_chain_sha256": source_digest.hexdigest(),
        "expected_releases_by_family": expected_by_family,
        "parsed_releases_by_family": parsed_by_family,
        "coverage_by_family": {
            family: (
                parsed_by_family[family] / expected_by_family[family]
                if expected_by_family[family]
                else 0.0
            )
            for family in FAMILIES
        },
        "download_errors": download_errors,
        "parse_errors": parse_errors,
        "normalized_path": str(source_path),
        "normalized_rows": int(len(frame)),
        "first_event_utc": frame["event_time_utc"].min().isoformat(),
        "last_event_utc": frame["event_time_utc"].max().isoformat(),
        "normalized_sha256": sha256_file(source_path),
        "point_in_time_semantics": (
            "Each value is parsed from the archived PDF published at "
            "the corresponding release timestamp; later database "
            "revisions are not used."
        ),
    }
    manifest_path = output_root / "MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return frame, manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("rebuild", "resume"))
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Rebuild the normalized source from the existing PDF archive.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "rebuild" and args.output_root.exists():
        raise RuntimeError(
            "Refusing destructive rebuild over an existing source; "
            "use resume or choose a new output root"
        )
    events = pd.read_parquet(EVENT_SOURCE)
    expected = expected_releases(events)
    if args.skip_download:
        manifest_path = args.output_root / "MANIFEST.json"
        if not manifest_path.exists():
            raise RuntimeError(
                "--skip-download requires an existing source manifest"
            )
        errors = json.loads(
            manifest_path.read_text(encoding="utf-8")
        ).get("download_errors", {})
    else:
        errors = download_archive(
            expected, args.output_root, max(1, int(args.workers))
        )
    frame, manifest = build_source(
        expected, args.output_root, errors
    )
    print(
        json.dumps(
            {
                "rows": int(len(frame)),
                "coverage": manifest["coverage_by_family"],
                "download_errors": len(errors),
                "parse_errors": len(manifest["parse_errors"]),
                "normalized_sha256": manifest["normalized_sha256"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
