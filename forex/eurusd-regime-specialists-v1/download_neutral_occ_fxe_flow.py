from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_ROOT = Path(
    "D:/AlgoTradingData/research/eurusd-neutral-occ-fxe-flow-v1"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_payload(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    text = payload.decode("utf-8-sig").strip()
    report_date = pd.to_datetime(path.stem, format="%Y%m%d")
    if text == "No record(s) found":
        return {
            "trade_date": report_date,
            "call_volume": 0,
            "put_volume": 0,
            "total_customer_volume": 0,
            "source_has_records": False,
            "raw_sha256": hashlib.sha256(payload).hexdigest(),
        }
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or rows[0][:7] != [
        "quantity",
        "underlying",
        "symbol",
        "actype",
        "porc",
        "exchange",
        "actdate",
    ]:
        raise RuntimeError(f"Unexpected OCC schema: {path}")
    call_volume = 0
    put_volume = 0
    for fields in rows[1:]:
        if not fields:
            continue
        if len(fields) < 7:
            raise RuntimeError(f"Short OCC row: {path}: {fields!r}")
        quantity, underlying, _, account, put_call, _, date_text = (
            fields[:7]
        )
        if underlying != "FXE" or account != "C":
            raise RuntimeError(
                f"Unexpected OCC classification: {path}: {fields!r}"
            )
        row_date = pd.to_datetime(date_text, format="%m/%d/%Y")
        if row_date != report_date:
            raise RuntimeError(
                f"OCC date mismatch: {path}: {date_text}"
            )
        if put_call == "C":
            call_volume += int(quantity)
        elif put_call == "P":
            put_volume += int(quantity)
        else:
            raise RuntimeError(
                f"Unexpected OCC put/call value: {put_call!r}"
            )
    return {
        "trade_date": report_date,
        "call_volume": call_volume,
        "put_volume": put_volume,
        "total_customer_volume": call_volume + put_volume,
        "source_has_records": True,
        "raw_sha256": hashlib.sha256(payload).hexdigest(),
    }


def normalize(output_root: Path) -> dict[str, Any]:
    raw_paths = sorted((output_root / "raw").glob("*.csv"))
    if not raw_paths:
        raise RuntimeError("No OCC raw files found")
    records = [parse_payload(path) for path in raw_paths]
    frame = pd.DataFrame(records).sort_values("trade_date")
    frame["customer_net_call_volume"] = (
        frame["call_volume"] - frame["put_volume"]
    )
    frame["customer_put_call_ratio"] = (
        frame["put_volume"]
        / frame["call_volume"].replace(0, pd.NA)
    )
    frame["available_time_utc"] = (
        frame["trade_date"] + pd.Timedelta(days=1)
    ).dt.tz_localize("UTC")
    normalized_path = output_root / "OCC_FXE_CUSTOMER_FLOW.parquet"
    frame.to_parquet(normalized_path, index=False)

    chain = hashlib.sha256()
    for path in raw_paths:
        chain.update(path.name.encode("ascii"))
        chain.update(bytes.fromhex(sha256_file(path)))
    manifest = {
        "campaign": "eurusd-neutral-occ-fxe-flow-v1",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "OCC official Volume Query Batch Processing",
        "source_documentation": (
            "https://www.theocc.com/market-data/market-data-reports/"
            "other-market-data-info/batch-processing/"
            "volume-query-batch-processing"
        ),
        "query": {
            "volumeQueryType": "O",
            "symbolType": "U",
            "symbol": "FXE",
            "reportType": "D",
            "accountType": "C",
            "productKind": "OSTK",
            "porc": "BOTH",
        },
        "credentials_used": False,
        "cost_usd": 0.0,
        "raw_files": len(raw_paths),
        "raw_chain_sha256": chain.hexdigest(),
        "normalized_path": str(normalized_path),
        "normalized_sha256": sha256_file(normalized_path),
        "rows": int(len(frame)),
        "rows_with_records": int(frame["source_has_records"].sum()),
        "first_trade_date": frame["trade_date"].min().date().isoformat(),
        "last_trade_date": frame["trade_date"].max().date().isoformat(),
        "total_calls": int(frame["call_volume"].sum()),
        "total_puts": int(frame["put_volume"].sum()),
    }
    manifest_path = output_root / "MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    manifest["manifest_path"] = str(manifest_path)
    manifest["manifest_sha256"] = sha256_file(manifest_path)
    return manifest


def acquire(
    output_root: Path, start_date: str, end_date: str
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    helper = (
        Path(__file__).resolve().parent
        / "download_occ_fxe_flow_raw.ps1"
    )
    command = [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(helper),
        "-OutputRoot",
        str(output_root),
        "-StartDate",
        start_date,
        "-EndDate",
        end_date,
    ]
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"OCC raw acquisition failed: {completed.returncode}"
        )
    return normalize(output_root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root", type=Path, default=DEFAULT_ROOT
    )
    parser.add_argument("--start-date", default="2024-07-29")
    parser.add_argument("--end-date", default="2026-06-30")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = acquire(
        args.output_root, args.start_date, args.end_date
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
