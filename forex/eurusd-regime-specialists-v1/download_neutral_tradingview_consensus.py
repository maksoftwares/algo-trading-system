from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


BLS_SOURCE = Path(
    "D:/AlgoTradingData/research/"
    "eurusd-neutral-bls-initial-release-v1/"
    "BLS_INITIAL_RELEASES.parquet"
)
DEFAULT_OUTPUT_ROOT = Path(
    "D:/AlgoTradingData/research/"
    "eurusd-neutral-tradingview-consensus-v1"
)
ENDPOINT = "https://economic-calendar.tradingview.com/events"
PROVIDER_PAGE = "https://www.tradingview.com/economic-calendar/"
START_UTC = pd.Timestamp("2019-01-01T00:00:00Z")
END_EXCLUSIVE_UTC = pd.Timestamp("2026-07-01T00:00:00Z")
USER_AGENT = (
    "Mozilla/5.0 compatible; causal-market-research/1.0; "
    "public-data-only"
)
SCHEMA_VERSION = "eurusd_neutral_tradingview_consensus_v1"
TICKERS = {
    "ECONOMICS:USIRMM": "CPI",
    "ECONOMICS:USPPIMM": "PPI",
    "ECONOMICS:USNFP": "NFP",
}
RECONCILED_COLUMNS = [
    "family",
    "event_time_utc",
    "metric",
    "unit",
    "official_initial_value",
    "official_pdf_sha256",
    "tradingview_event_id",
    "tradingview_title",
    "tradingview_ticker",
    "tradingview_actual_value",
    "forecast_value",
    "previous_value",
    "importance",
    "reference_date",
    "provider_source",
    "provider_source_url",
    "retrieval_semantics",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def month_windows() -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    boundaries = pd.date_range(
        START_UTC,
        END_EXCLUSIVE_UTC,
        freq="MS",
        inclusive="both",
    )
    return list(zip(boundaries[:-1], boundaries[1:], strict=False))


def _iso_utc(value: pd.Timestamp) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def month_url(start: pd.Timestamp, end: pd.Timestamp) -> str:
    query = urllib.parse.urlencode(
        {
            "from": _iso_utc(start),
            "to": _iso_utc(end),
            "countries": "US",
            "minImportance": 0,
        }
    )
    return f"{ENDPOINT}?{query}"


def _valid_payload(payload: bytes) -> dict[str, Any]:
    parsed = json.loads(payload)
    if parsed.get("status") != "ok":
        raise RuntimeError(
            f"TradingView response status is not ok: {parsed.get('status')!r}"
        )
    if not isinstance(parsed.get("result"), list):
        raise RuntimeError("TradingView response lacks a result list")
    return parsed


def download_month(
    start: pd.Timestamp,
    end: pd.Timestamp,
    path: Path,
    attempts: int = 4,
) -> None:
    if path.exists() and path.stat().st_size > 2:
        _valid_payload(path.read_bytes())
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        month_url(start, end),
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Origin": "https://www.tradingview.com",
            "Referer": PROVIDER_PAGE,
        },
    )
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read()
            _valid_payload(payload)
            path.write_bytes(payload)
            return
        except (
            OSError,
            RuntimeError,
            ValueError,
            urllib.error.URLError,
        ) as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Could not download {request.full_url}: {last_error}")


def download_archive(
    output_root: Path,
    delay_seconds: float,
) -> dict[str, str]:
    errors: dict[str, str] = {}
    windows = month_windows()
    for index, (start, end) in enumerate(windows):
        path = output_root / "raw" / f"{start:%Y-%m}.json"
        try:
            download_month(start, end, path)
        except Exception as exc:  # noqa: BLE001
            errors[f"{start:%Y-%m}"] = str(exc)
        if index + 1 < len(windows) and delay_seconds > 0:
            time.sleep(delay_seconds)
    return errors


def _number(event: dict[str, Any], raw_key: str, key: str) -> float | None:
    value = event.get(raw_key)
    if value is None:
        value = event.get(key)
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_calendar_candidates(
    payloads: Iterable[dict[str, Any]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for payload in payloads:
        for event in payload.get("result", []):
            ticker = str(event.get("ticker") or "")
            family = TICKERS.get(ticker)
            if family is None:
                continue
            timestamp = pd.to_datetime(event.get("date"), utc=True)
            if not (START_UTC <= timestamp < END_EXCLUSIVE_UTC):
                continue
            rows.append(
                {
                    "family": family,
                    "event_time_utc": timestamp,
                    "tradingview_event_id": str(event.get("id") or ""),
                    "title": str(event.get("title") or ""),
                    "ticker": ticker,
                    "actual_value": _number(
                        event, "actualRaw", "actual"
                    ),
                    "forecast_value": _number(
                        event, "forecastRaw", "forecast"
                    ),
                    "previous_value": _number(
                        event, "previousRaw", "previous"
                    ),
                    "importance": event.get("importance"),
                    "reference_date": event.get("referenceDate"),
                    "provider_source": event.get("source"),
                    "provider_source_url": event.get("source_url"),
                }
            )
    if not rows:
        return pd.DataFrame(
            columns=[
                "family",
                "event_time_utc",
                "tradingview_event_id",
                "title",
                "ticker",
                "actual_value",
                "forecast_value",
                "previous_value",
                "importance",
                "reference_date",
                "provider_source",
                "provider_source_url",
            ]
        )
    frame = pd.DataFrame(rows)
    frame["event_time_utc"] = pd.to_datetime(
        frame["event_time_utc"], utc=True
    ).dt.as_unit("ns")
    return frame.sort_values(
        ["event_time_utc", "family", "tradingview_event_id"]
    ).reset_index(drop=True)


def _actual_matches(
    family: str,
    provider_value: float | None,
    official_value: float,
) -> bool:
    if provider_value is None:
        return False
    tolerance = 0.5 if family == "NFP" else 1e-9
    return abs(float(provider_value) - float(official_value)) <= tolerance


def reconcile_with_bls(
    candidates: pd.DataFrame,
    bls: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    official = bls.copy()
    official["event_time_utc"] = pd.to_datetime(
        official["event_time_utc"], utc=True
    ).dt.as_unit("ns")
    records: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    for release in official.sort_values(
        ["event_time_utc", "family"]
    ).itertuples(index=False):
        same_time = candidates[
            candidates["family"].eq(str(release.family))
            & candidates["event_time_utc"].eq(
                pd.Timestamp(release.event_time_utc)
            )
        ].copy()
        exact = same_time[
            same_time["actual_value"].map(
                lambda value: _actual_matches(
                    str(release.family),
                    value,
                    float(release.initial_value),
                )
            )
        ].copy()
        key = {
            "family": str(release.family),
            "event_time_utc": pd.Timestamp(
                release.event_time_utc
            ).isoformat(),
            "official_initial_value": float(release.initial_value),
        }
        if len(exact) == 0:
            if same_time.empty:
                missing.append(key)
            else:
                mismatches.append(
                    {
                        **key,
                        "provider_actual_values": sorted(
                            value
                            for value in same_time[
                                "actual_value"
                            ].dropna().astype(float).unique().tolist()
                        ),
                    }
                )
            continue
        if len(exact) > 1:
            ambiguous.append(
                {
                    **key,
                    "matching_event_ids": sorted(
                        exact["tradingview_event_id"].astype(str).tolist()
                    ),
                }
            )
            continue
        provider = exact.iloc[0]
        records.append(
            {
                "family": str(release.family),
                "event_time_utc": pd.Timestamp(release.event_time_utc),
                "metric": str(release.metric),
                "unit": str(release.unit),
                "official_initial_value": float(release.initial_value),
                "official_pdf_sha256": str(
                    release.source_pdf_sha256
                ),
                "tradingview_event_id": str(
                    provider["tradingview_event_id"]
                ),
                "tradingview_title": str(provider["title"]),
                "tradingview_ticker": str(provider["ticker"]),
                "tradingview_actual_value": float(
                    provider["actual_value"]
                ),
                "forecast_value": (
                    float(provider["forecast_value"])
                    if pd.notna(provider["forecast_value"])
                    else None
                ),
                "previous_value": (
                    float(provider["previous_value"])
                    if pd.notna(provider["previous_value"])
                    else None
                ),
                "importance": provider["importance"],
                "reference_date": provider["reference_date"],
                "provider_source": provider["provider_source"],
                "provider_source_url": provider[
                    "provider_source_url"
                ],
                "retrieval_semantics": (
                    "POST_HOC_HISTORICAL_CALENDAR_FORECAST_FIELD"
                ),
            }
        )
    if records:
        frame = pd.DataFrame(records).sort_values(
            ["event_time_utc", "family"]
        ).reset_index(drop=True)
    else:
        frame = pd.DataFrame(columns=RECONCILED_COLUMNS)
    by_family: dict[str, Any] = {}
    for family in TICKERS.values():
        expected = int(official["family"].eq(family).sum())
        selected = frame[frame["family"].eq(family)]
        matched = int(len(selected))
        forecasts = int(selected["forecast_value"].notna().sum())
        by_family[family] = {
            "official_releases": expected,
            "exact_actual_matches": matched,
            "exact_actual_match_rate": matched / expected if expected else 0.0,
            "forecast_values": forecasts,
            "forecast_coverage_of_matches": (
                forecasts / matched if matched else 0.0
            ),
        }
    audit = {
        "calendar_candidates": int(len(candidates)),
        "official_releases": int(len(official)),
        "exact_actual_matches": int(len(frame)),
        "missing_provider_rows": missing,
        "actual_mismatches": mismatches,
        "ambiguous_exact_matches": ambiguous,
        "by_family": by_family,
    }
    return frame, audit


def raw_payloads(output_root: Path) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for path in sorted((output_root / "raw").glob("*.json")):
        payloads.append(_valid_payload(path.read_bytes()))
    return payloads


def raw_chain_sha256(output_root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((output_root / "raw").glob("*.json")):
        relative = path.relative_to(output_root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def build_source(
    output_root: Path,
    download_errors: dict[str, str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    bls = pd.read_parquet(BLS_SOURCE)
    candidates = extract_calendar_candidates(raw_payloads(output_root))
    frame, audit = reconcile_with_bls(candidates, bls)
    output_root.mkdir(parents=True, exist_ok=True)
    source_path = output_root / "TRADINGVIEW_CONSENSUS.parquet"
    frame.to_parquet(source_path, index=False, compression="zstd")
    family_checks = {
        family: (
            values["exact_actual_match_rate"] >= 0.95
            and values["forecast_coverage_of_matches"] >= 0.80
        )
        for family, values in audit["by_family"].items()
    }
    accepted = (
        not download_errors
        and not audit["ambiguous_exact_matches"]
        and all(family_checks.values())
    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "provider": "TradingView Economic Calendar",
        "authentication_required": False,
        "endpoint": ENDPOINT,
        "provider_page": PROVIDER_PAGE,
        "retrieved_window": [
            START_UTC.isoformat(),
            (END_EXCLUSIVE_UTC - pd.Timedelta(nanoseconds=1)).isoformat(),
        ],
        "raw_response_files": len(
            list((output_root / "raw").glob("*.json"))
        ),
        "raw_response_chain_sha256": raw_chain_sha256(output_root),
        "download_errors": download_errors,
        "official_bls_source": str(BLS_SOURCE),
        "official_bls_source_sha256": sha256_file(BLS_SOURCE),
        "reconciliation": audit,
        "source_acceptance_checks": family_checks,
        "accepted_for_adaptive_historical_research": accepted,
        "accepted_for_pristine_oos_claim": False,
        "normalized_path": str(source_path),
        "normalized_rows": int(len(frame)),
        "normalized_sha256": sha256_file(source_path),
        "known_corruption_check_2024_01_05_nfp": {
            "actual": 216000.0,
            "forecast": 170000.0,
            "previous": 173000.0,
            "expected_match": True,
        },
        "information_boundary": (
            "Actual values are accepted only when timestamp and value match "
            "the official archived BLS initial-release source. Forecast is "
            "the provider's historical pre-release consensus field, but the "
            "API responses were retrieved after the events and are not "
            "independent pre-release snapshots. The source is therefore "
            "adaptive historical research only; future forecasts must be "
            "captured prospectively before release."
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
    parser.add_argument("--delay-seconds", type=float, default=0.2)
    parser.add_argument("--skip-download", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "rebuild" and args.output_root.exists():
        raise RuntimeError(
            "Refusing destructive rebuild over an existing source; "
            "use resume or choose a new output root"
        )
    if args.skip_download:
        errors: dict[str, str] = {}
    else:
        errors = download_archive(
            args.output_root,
            max(0.0, float(args.delay_seconds)),
        )
    frame, manifest = build_source(args.output_root, errors)
    print(
        json.dumps(
            {
                "rows": int(len(frame)),
                "accepted": manifest[
                    "accepted_for_adaptive_historical_research"
                ],
                "download_errors": len(errors),
                "by_family": manifest["reconciliation"]["by_family"],
                "normalized_sha256": manifest["normalized_sha256"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
