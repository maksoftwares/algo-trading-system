from __future__ import annotations

import zipfile
from pathlib import Path

from capture_prospective_neutral_gdelt_relative_tone import (
    capture,
    capture_window,
    load_and_verify_preregistration,
    source_targets,
    status,
)


def _gkg_payload(timestamp: str, side: str) -> bytes:
    values = [""] * 27
    values[0] = f"{side}-record"
    values[1] = timestamp
    values[3] = f"{side.lower()}.example"
    values[4] = f"https://{side.lower()}.example/article"
    values[8] = "ECON_CENTRALBANK,1"
    values[13] = (
        "European Central Bank" if side == "ECB" else "Federal Reserve"
    )
    values[15] = "1.5,2.0,0.5"
    return ("\t".join(values) + "\n").encode()


def test_source_targets_and_capture_window_are_frozen() -> None:
    config, _ = load_and_verify_preregistration()
    targets = source_targets(config, "2026-07-29")
    assert [row["batch_timestamp_utc"] for row in targets] == [
        "20260728230000",
        "20260728231500",
        "20260728233000",
        "20260728234500",
    ]
    earliest, deadline = capture_window(config, "2026-07-29")
    assert earliest.isoformat() == "2026-07-29T00:01:00+00:00"
    assert deadline.isoformat() == "2026-07-29T00:15:00+00:00"


def test_status_waits_without_network_or_signal(tmp_path: Path) -> None:
    result = status(
        "2026-07-29",
        tmp_path,
        now_utc="2026-07-28T23:59:00Z",
    )
    assert result["status"] == "WAITING_FOR_CAPTURE_WINDOW"
    assert result["signal_generated"] is False
    assert result["broker_action_allowed"] is False


def test_complete_capture_is_immutable_and_source_only(
    tmp_path: Path,
) -> None:
    call_count = 0

    def fetcher(
        url: str,
        target_path: Path,
        *,
        timeout_seconds: float,
    ) -> dict[str, object]:
        nonlocal call_count
        del url, timeout_seconds
        timestamp = target_path.name.split(".", 1)[0]
        side = "ECB" if call_count % 2 == 0 else "FED"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(
            target_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            archive.writestr(
                f"{timestamp}.gkg.csv",
                _gkg_payload(timestamp, side),
            )
        call_count += 1
        return {
            "network_request_attempts": 1,
            "archive_reused": False,
            "attempts": [{"status": "DOWNLOADED"}],
        }

    result = capture(
        "2026-07-29",
        tmp_path,
        now_utc="2026-07-29T00:02:00Z",
        fetcher=fetcher,
    )
    assert result["status"] == "COMPLETE_ON_TIME"
    assert result["network_request_attempts"] == 4
    assert result["normalized"]["strict_document_occurrences"] == 4
    assert result["historical_eurusd_prices_loaded"] is False
    assert result["historical_eurusd_pnl_loaded"] is False
    assert result["oracle_rows_loaded"] is False
    assert result["signal_generated"] is False
    assert result["broker_action_allowed"] is False
    repeated = capture(
        "2026-07-29",
        tmp_path,
        now_utc="2026-07-29T00:03:00Z",
        fetcher=fetcher,
    )
    assert repeated["status"] == "COMPLETE_ON_TIME"
    assert call_count == 4


def test_late_complete_capture_cannot_create_signal(tmp_path: Path) -> None:
    def fetcher(
        url: str,
        target_path: Path,
        *,
        timeout_seconds: float,
    ) -> dict[str, object]:
        del url, timeout_seconds
        timestamp = target_path.name.split(".", 1)[0]
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target_path, "w") as archive:
            archive.writestr(
                f"{timestamp}.gkg.csv",
                _gkg_payload(timestamp, "FED"),
            )
        return {
            "network_request_attempts": 1,
            "archive_reused": False,
            "attempts": [{"status": "DOWNLOADED"}],
        }

    result = capture(
        "2026-07-29",
        tmp_path,
        now_utc="2026-07-29T00:16:00Z",
        fetcher=fetcher,
    )
    assert result["status"] == "COMPLETE_LATE_NO_SIGNAL"
    assert result["signal_generated"] is False
