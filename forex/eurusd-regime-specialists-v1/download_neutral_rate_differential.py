from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

DATA_ROOT = Path(os.environ.get("ALGO_DATA_ROOT", "D:/AlgoTradingData"))
SOURCE_ROOT = (
    DATA_ROOT / "research" / "eurusd-neutral-rate-differential-v1"
)
RAW_ROOT = SOURCE_ROOT / "raw"
NORMALIZED_ROOT = SOURCE_ROOT / "normalized"
MANIFEST_PATH = SOURCE_ROOT / "SOURCE_MANIFEST.json"
AUDIT_PATH = SOURCE_ROOT / "SOURCE_AUDIT.json"

ECB_URL = (
    "https://data-api.ecb.europa.eu/service/data/YC/"
    "B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y"
    "?startPeriod=2019-01-01&endPeriod=2026-06-30&format=csvdata"
)
TREASURY_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/"
    "interest-rates/pages/xml?data=daily_treasury_yield_curve"
    "&field_tdr_date_value={year}"
)
USER_AGENT = "EURUSD-neutral-rate-source-audit/1.0"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch(url: str) -> tuple[bytes, dict[str, Any]]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/csv, application/xml, text/xml, */*",
            "User-Agent": USER_AGENT,
        },
    )
    started = datetime.now(UTC)
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = response.read()
        metadata = {
            "requested_at_utc": started.isoformat(),
            "completed_at_utc": datetime.now(UTC).isoformat(),
            "url": url,
            "status": int(response.status),
            "content_type": response.headers.get("Content-Type"),
            "provider_date": response.headers.get("Date"),
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
            "bytes": len(payload),
            "sha256": sha256_bytes(payload),
        }
    return payload, metadata


def parse_treasury_xml(payload: bytes) -> pd.DataFrame:
    root = ET.fromstring(payload)
    data_ns = "http://schemas.microsoft.com/ado/2007/08/dataservices"
    rows: list[dict[str, Any]] = []
    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        date_element = entry.find(f".//{{{data_ns}}}NEW_DATE")
        yield_element = entry.find(f".//{{{data_ns}}}BC_2YEAR")
        if (
            date_element is None
            or date_element.text is None
            or yield_element is None
            or yield_element.text is None
        ):
            continue
        rows.append(
            {
                "observation_date": pd.Timestamp(date_element.text).date(),
                "us_treasury_2y_percent": float(yield_element.text),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError("Treasury response has no two-year observations")
    return frame.sort_values("observation_date").reset_index(drop=True)


def parse_ecb_csv(payload: bytes) -> pd.DataFrame:
    rows = list(
        csv.DictReader(payload.decode("utf-8-sig").splitlines())
    )
    selected = []
    for row in rows:
        if (
            row.get("KEY")
            != "YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y"
            or not row.get("TIME_PERIOD")
            or not row.get("OBS_VALUE")
        ):
            continue
        selected.append(
            {
                "observation_date": pd.Timestamp(
                    row["TIME_PERIOD"]
                ).date(),
                "ecb_euro_area_aaa_2y_percent": float(row["OBS_VALUE"]),
                "observation_status": row.get("OBS_STATUS", ""),
            }
        )
    frame = pd.DataFrame(selected)
    if frame.empty:
        raise RuntimeError("ECB response has no two-year observations")
    return frame.sort_values("observation_date").reset_index(drop=True)


def build_audit(
    treasury: pd.DataFrame, ecb: pd.DataFrame
) -> dict[str, Any]:
    for name, frame, value in (
        ("treasury", treasury, "us_treasury_2y_percent"),
        ("ecb", ecb, "ecb_euro_area_aaa_2y_percent"),
    ):
        if frame["observation_date"].duplicated().any():
            raise RuntimeError(f"Duplicate {name} observation dates")
        if not pd.to_numeric(frame[value], errors="coerce").notna().all():
            raise RuntimeError(f"Non-numeric {name} observations")
    common = treasury.merge(ecb, on="observation_date", how="inner")
    common["spread_percent"] = (
        common["us_treasury_2y_percent"]
        - common["ecb_euro_area_aaa_2y_percent"]
    )
    common["spread_change_bps"] = common["spread_percent"].diff() * 100.0
    return {
        "schema_version": "eurusd_neutral_rate_differential_source_audit_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "eurusd_prices_loaded": False,
        "eurusd_returns_loaded": False,
        "oracle_rows_loaded": False,
        "pnl_loaded": False,
        "treasury": {
            "rows": len(treasury),
            "first_observation_date": str(
                treasury["observation_date"].min()
            ),
            "last_observation_date": str(
                treasury["observation_date"].max()
            ),
        },
        "ecb": {
            "rows": len(ecb),
            "first_observation_date": str(ecb["observation_date"].min()),
            "last_observation_date": str(ecb["observation_date"].max()),
        },
        "exact_common_observation_dates": len(common),
        "absolute_spread_changes_at_least_5bp": int(
            common["spread_change_bps"].abs().ge(5.0).sum()
        ),
        "status": "SOURCE_ACCEPTED_FOR_OUTCOME_BLIND_CENSUS",
        "broker_action_allowed": False,
    }


def rebuild() -> dict[str, Any]:
    if SOURCE_ROOT.exists():
        raise RuntimeError(
            "Refusing destructive rebuild over an existing rate source"
        )
    RAW_ROOT.mkdir(parents=True)
    NORMALIZED_ROOT.mkdir(parents=True)
    source_records: list[dict[str, Any]] = []
    treasury_frames: list[pd.DataFrame] = []

    for year in range(2019, 2027):
        url = TREASURY_URL.format(year=year)
        payload, metadata = fetch(url)
        path = RAW_ROOT / f"USTREASURY_DAILY_CURVE_{year}.xml"
        path.write_bytes(payload)
        metadata["relative_path"] = str(
            path.relative_to(SOURCE_ROOT)
        ).replace("\\", "/")
        metadata["year"] = year
        source_records.append(metadata)
        treasury_frames.append(parse_treasury_xml(payload))

    ecb_payload, ecb_metadata = fetch(ECB_URL)
    ecb_path = RAW_ROOT / "ECB_EURO_AREA_AAA_2Y_2019_2026H1.csv"
    ecb_path.write_bytes(ecb_payload)
    ecb_metadata["relative_path"] = str(
        ecb_path.relative_to(SOURCE_ROOT)
    ).replace("\\", "/")
    source_records.append(ecb_metadata)

    treasury = (
        pd.concat(treasury_frames, ignore_index=True)
        .drop_duplicates("observation_date", keep="last")
        .sort_values("observation_date")
        .reset_index(drop=True)
    )
    treasury = treasury[
        pd.to_datetime(treasury["observation_date"]).between(
            "2019-01-01", "2026-06-30"
        )
    ].copy()
    ecb = parse_ecb_csv(ecb_payload)
    ecb = ecb[
        pd.to_datetime(ecb["observation_date"]).between(
            "2019-01-01", "2026-06-30"
        )
    ].copy()

    treasury_path = NORMALIZED_ROOT / "US_TREASURY_2Y.csv"
    ecb_normalized_path = NORMALIZED_ROOT / "ECB_EURO_AREA_AAA_2Y.csv"
    treasury.to_csv(treasury_path, index=False, lineterminator="\n")
    ecb.to_csv(ecb_normalized_path, index=False, lineterminator="\n")
    audit = build_audit(treasury, ecb)
    audit["normalized_artifacts"] = {
        "normalized/US_TREASURY_2Y.csv": sha256_file(treasury_path),
        "normalized/ECB_EURO_AREA_AAA_2Y.csv": sha256_file(
            ecb_normalized_path
        ),
    }
    AUDIT_PATH.write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": "eurusd_neutral_rate_differential_source_manifest_v1",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "sources": source_records,
        "source_audit_relative_path": "SOURCE_AUDIT.json",
        "source_audit_sha256": sha256_file(AUDIT_PATH),
        "normalized_artifacts": audit["normalized_artifacts"],
        "eurusd_prices_loaded": False,
        "eurusd_returns_loaded": False,
        "oracle_rows_loaded": False,
        "pnl_loaded": False,
        "broker_action_allowed": False,
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {**audit, "manifest_sha256": sha256_file(MANIFEST_PATH)}


def status() -> dict[str, Any]:
    if not MANIFEST_PATH.exists() or not AUDIT_PATH.exists():
        return {
            "status": "SOURCE_NOT_ACQUIRED",
            "source_root": str(SOURCE_ROOT),
        }
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for source in manifest["sources"]:
        path = SOURCE_ROOT / source["relative_path"]
        if sha256_file(path) != source["sha256"]:
            raise RuntimeError(f"Raw source drift: {path}")
    for relative, expected in manifest["normalized_artifacts"].items():
        if sha256_file(SOURCE_ROOT / relative) != expected:
            raise RuntimeError(f"Normalized source drift: {relative}")
    if sha256_file(AUDIT_PATH) != manifest["source_audit_sha256"]:
        raise RuntimeError("Source audit drift")
    return {
        "status": "SOURCE_INTEGRITY_VERIFIED",
        "manifest_sha256": sha256_file(MANIFEST_PATH),
        "audit": json.loads(AUDIT_PATH.read_text(encoding="utf-8")),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("rebuild", "status"))
    args = parser.parse_args()
    result = rebuild() if args.command == "rebuild" else status()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
