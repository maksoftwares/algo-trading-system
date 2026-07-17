from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from foundation import AcquisitionRefused, download_completed_job, inspect_batch_job, load_config


class FakeBatch:
    def __init__(self, root: Path, state: str = "done") -> None:
        self.root = root
        self.state = state
        self.download_calls: list[tuple[str, Path]] = []

    def list_jobs(self) -> list[dict]:
        return [{"id": "job-123", "state": self.state, "schema": "tbbo"}]

    def list_files(self, job_id: str) -> list[dict]:
        assert job_id == "job-123"
        return [{"filename": "part-000.dbn.zst", "size": 4}]

    def download(self, job_id: str, output_dir: Path) -> list[Path]:
        destination = Path(output_dir)
        self.download_calls.append((job_id, destination))
        path = destination / "part-000.dbn.zst"
        path.write_bytes(b"dbn1")
        return [path]


class FakeClient:
    def __init__(self, root: Path, state: str = "done") -> None:
        self.batch = FakeBatch(root, state)


def temp_config(tmp_path: Path) -> dict:
    config = deepcopy(load_config())
    config["storage"]["root"] = str(tmp_path)
    return config


def test_inspection_never_downloads() -> None:
    client = FakeClient(Path("unused"))
    result = inspect_batch_job(client, "job-123")
    assert result["state"] == "done"
    assert result["files"] == [{"filename": "part-000.dbn.zst", "size": 4}]
    assert result["downloaded"] is False
    assert client.batch.download_calls == []


def test_path_like_job_id_is_refused_before_vendor_call() -> None:
    client = FakeClient(Path("unused"))
    with pytest.raises(AcquisitionRefused, match="path characters"):
        inspect_batch_job(client, "../job-123")
    assert client.batch.download_calls == []


def test_unfinished_job_cannot_download(tmp_path: Path) -> None:
    client = FakeClient(tmp_path, state="processing")
    with pytest.raises(AcquisitionRefused, match="only completed"):
        download_completed_job(
            client,
            temp_config(tmp_path),
            job_id="job-123",
            execute_download=True,
        )
    assert client.batch.download_calls == []


def test_explicit_download_hashes_files(tmp_path: Path) -> None:
    client = FakeClient(tmp_path)
    result = download_completed_job(
        client,
        temp_config(tmp_path),
        job_id="job-123",
        execute_download=True,
    )
    assert result["status"] == "DOWNLOADED_AND_HASHED"
    assert result["downloaded"] is True
    assert result["downloaded_files"] == [
        {
            "path": str((tmp_path / "raw" / "job-123" / "part-000.dbn.zst").resolve()),
            "size_bytes": 4,
            "sha256": "8a21367fe3959953ab7738ab621cc33af0c6245051fba9b1d9bad5dd13a466c3",
        }
    ]


def test_nonempty_download_directory_is_refused(tmp_path: Path) -> None:
    destination = tmp_path / "raw" / "job-123"
    destination.mkdir(parents=True)
    (destination / "existing.txt").write_text("keep", encoding="utf-8")
    client = FakeClient(tmp_path)
    with pytest.raises(AcquisitionRefused, match="not empty"):
        download_completed_job(
            client,
            temp_config(tmp_path),
            job_id="job-123",
            execute_download=True,
        )
    assert client.batch.download_calls == []
