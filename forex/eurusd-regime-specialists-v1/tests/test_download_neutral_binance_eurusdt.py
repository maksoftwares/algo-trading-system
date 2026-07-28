from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from download_neutral_binance_eurusdt import (  # noqa: E402
    archive_name,
    expected_checksum,
    months_inclusive,
    parse_archive,
)


def test_month_range_is_inclusive() -> None:
    assert months_inclusive("2024-11", "2025-02") == [
        "2024-11",
        "2024-12",
        "2025-01",
        "2025-02",
    ]


def test_checksum_requires_matching_archive_name() -> None:
    name = archive_name("2024-01")
    digest = hashlib.sha256(b"archive").hexdigest()
    payload = f"{digest}  {name}\n".encode()
    assert expected_checksum(payload, name) == digest


def _write_archive(
    path: Path,
    *,
    timestamp_unit: str,
) -> None:
    start = pd.Timestamp("2025-01-01T00:00:00Z")
    divisor = 1_000_000 if timestamp_unit == "ms" else 1_000
    rows: list[str] = []
    for offset in (0, 5):
        opened = start + pd.Timedelta(minutes=offset)
        closed = opened + pd.Timedelta(minutes=5)
        open_raw = opened.value // divisor
        close_raw = closed.value // divisor - 1
        rows.append(
            ",".join(
                [
                    str(open_raw),
                    "1.1000",
                    "1.1010",
                    "1.0990",
                    "1.1005",
                    "100",
                    str(close_raw),
                    "110",
                    "20",
                    "60",
                    "66",
                    "0",
                ]
            )
        )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            path.stem.replace(".zip", "") + ".csv",
            "\n".join(rows),
        )


def test_parser_handles_millisecond_timestamps(tmp_path: Path) -> None:
    path = tmp_path / "sample-ms.zip"
    _write_archive(path, timestamp_unit="ms")
    frame, manifest = parse_archive(path, "2024-01")
    assert len(frame) == 2
    assert manifest["timestamp_unit"] == "ms"
    assert frame["taker_imbalance"].eq(0.2).all()


def test_parser_handles_microsecond_timestamps(tmp_path: Path) -> None:
    path = tmp_path / "sample-us.zip"
    _write_archive(path, timestamp_unit="us")
    frame, manifest = parse_archive(path, "2025-01")
    assert len(frame) == 2
    assert manifest["timestamp_unit"] == "us"
    assert frame["open_time_utc"].iloc[1] == pd.Timestamp(
        "2025-01-01T00:05:00Z"
    )
