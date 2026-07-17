from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "comex_futures_foundation_v1.json"


class AcquisitionRefused(RuntimeError):
    """Raised when an acquisition request fails a locked safety control."""


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_api_key(config: Mapping[str, Any], environment: Mapping[str, str] | None = None) -> str:
    environment = os.environ if environment is None else environment
    variable = config["acquisition_controls"]["require_api_key_environment_variable"]
    api_key = environment.get(variable, "").strip()
    if not api_key:
        raise AcquisitionRefused(
            f"{variable} is required. Set it in the environment; do not store it in the repository."
        )
    return api_key


def create_client(api_key: str) -> Any:
    try:
        import databento as db
    except ImportError as exc:
        raise AcquisitionRefused(
            "The databento package is required. Install this campaign's requirements first."
        ) from exc
    return db.Historical(api_key)


def _source(config: Mapping[str, Any]) -> Mapping[str, Any]:
    return config["source"]


def cost_request(config: Mapping[str, Any], schema: str) -> dict[str, Any]:
    source = _source(config)
    if schema not in source["estimate_schemas"]:
        raise AcquisitionRefused(f"Schema {schema!r} is not in the frozen estimate set.")
    return {
        "dataset": source["dataset"],
        "symbols": source["symbol"],
        "schema": schema,
        "start": source["start"],
        "end": source["end"],
        "stype_in": source["stype_in"],
    }


def batch_request(config: Mapping[str, Any], schema: str) -> dict[str, Any]:
    source = _source(config)
    request = cost_request(config, schema)
    request.update(
        {
            "encoding": source["encoding"],
            "compression": source["compression"],
            "split_duration": source["split_duration"],
        }
    )
    return request


def estimate_costs(client: Any, config: Mapping[str, Any]) -> dict[str, Any]:
    estimates: list[dict[str, Any]] = []
    for schema in _source(config)["estimate_schemas"]:
        request = cost_request(config, schema)
        estimated_cost = float(client.metadata.get_cost(**request))
        estimates.append({"schema": schema, "estimated_cost_usd": estimated_cost})
    return {
        "status": "ESTIMATE_ONLY",
        "campaign_id": config["campaign_id"],
        "estimated_utc": datetime.now(timezone.utc).isoformat(),
        "request": {
            key: value
            for key, value in cost_request(config, _source(config)["preferred_first_schema"]).items()
            if key != "schema"
        },
        "estimates": estimates,
        "submitted": False,
    }


def _serializable(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    return str(value)


def inspect_batch_job(client: Any, job_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", job_id):
        raise AcquisitionRefused("The Databento job ID contains unsupported path characters.")
    jobs = client.batch.list_jobs()
    job = next((item for item in jobs if str(item.get("id")) == job_id), None)
    if job is None:
        raise AcquisitionRefused(f"Databento job {job_id!r} was not found in the account.")
    state = str(job.get("state", "unknown")).lower()
    files = client.batch.list_files(job_id) if state == "done" else []
    return {
        "status": "JOB_INSPECTION",
        "job_id": job_id,
        "state": state,
        "job": _serializable(job),
        "files": [_serializable(item) for item in files],
        "downloaded": False,
    }


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_completed_job(
    client: Any,
    config: Mapping[str, Any],
    *,
    job_id: str,
    execute_download: bool,
) -> dict[str, Any]:
    inspection = inspect_batch_job(client, job_id)
    if not execute_download:
        return inspection
    if inspection["state"] != "done":
        raise AcquisitionRefused(
            f"Databento job {job_id!r} is {inspection['state']!r}; only completed jobs can download."
        )

    storage = config["storage"]
    root = Path(storage["root"]).resolve()
    destination = (root / storage["download_directory"] / job_id).resolve()
    if root != destination and root not in destination.parents:
        raise AcquisitionRefused("Resolved download path is outside the frozen storage root.")
    if destination.exists() and any(destination.iterdir()):
        raise AcquisitionRefused(f"Download directory is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    downloaded = [Path(path).resolve() for path in client.batch.download(job_id, output_dir=destination)]
    file_records: list[dict[str, Any]] = []
    for path in downloaded:
        if destination != path and destination not in path.parents:
            raise AcquisitionRefused(f"Vendor returned a path outside the job directory: {path}")
        if not path.is_file():
            raise AcquisitionRefused(f"Downloaded path is not a file: {path}")
        file_records.append(
            {
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )
    if not file_records:
        raise AcquisitionRefused("The completed job returned no downloaded files.")

    inspection.update(
        {
            "status": "DOWNLOADED_AND_HASHED",
            "downloaded_utc": datetime.now(timezone.utc).isoformat(),
            "download_directory": str(destination),
            "downloaded_files": file_records,
            "downloaded": True,
        }
    )
    return inspection


def submit_authorized(
    client: Any,
    config: Mapping[str, Any],
    *,
    schema: str,
    max_cost_usd: float,
    execute: bool,
    verified_free_credit_usd: float | None = None,
) -> dict[str, Any]:
    controls = config["acquisition_controls"]
    if controls["require_explicit_execute"] and not execute:
        raise AcquisitionRefused("Acquisition requires the explicit --execute flag.")
    if max_cost_usd <= 0:
        raise AcquisitionRefused("Acquisition requires an explicit positive --max-cost-usd cap.")
    payment_authorized = bool(controls.get("payment_authorized", True))
    if not payment_authorized:
        if not controls.get("free_credit_balance_must_be_verified", False):
            raise AcquisitionRefused("Zero-payment acquisition requires locked free-credit verification.")
        if verified_free_credit_usd is None or verified_free_credit_usd <= 0:
            raise AcquisitionRefused(
                "Zero-payment acquisition requires --verified-free-credit-usd from the current billing page."
            )
        free_credit_cap = float(controls["maximum_free_credit_consumption_usd"])
        if max_cost_usd > verified_free_credit_usd or max_cost_usd > free_credit_cap:
            raise AcquisitionRefused(
                "The authorized cost cap exceeds the verified or campaign-limited free credit."
            )

    request = cost_request(config, schema)
    estimated_cost = float(client.metadata.get_cost(**request))
    if controls["reject_above_cost_cap"] and estimated_cost > max_cost_usd:
        raise AcquisitionRefused(
            f"Estimated cost ${estimated_cost:.2f} exceeds the authorized ${max_cost_usd:.2f} cap."
        )

    job = client.batch.submit_job(**batch_request(config, schema))
    return {
        "status": "SUBMITTED_NOT_DOWNLOADED",
        "campaign_id": config["campaign_id"],
        "submitted_utc": datetime.now(timezone.utc).isoformat(),
        "schema": schema,
        "estimated_cost_usd": estimated_cost,
        "authorized_cost_cap_usd": max_cost_usd,
        "payment_authorized": payment_authorized,
        "verified_free_credit_usd": verified_free_credit_usd,
        "job": _serializable(job),
        "submitted": True,
        "automatic_download": controls["automatic_download"],
    }


def write_manifest(config: Mapping[str, Any], payload: Mapping[str, Any], output: Path | None = None) -> Path:
    if output is None:
        storage = config["storage"]
        directory = Path(storage["root"]) / storage["manifest_directory"]
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output = directory / f"{payload['status'].lower()}_{stamp}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output
