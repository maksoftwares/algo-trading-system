from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import Any

from .market_data_export import _sha256_file, _table, _utc_now, _write_json_atomic


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_REVIEWER_HANDOFF_PACKAGE_STATUS.json"
SCHEMA_VERSION = "a3_ml_reviewer_handoff_package_status_v1"
STATUS_READY = "READY_TO_SEND_REVIEWER_HANDOFF_PACKAGE"
STATUS_MISSING = "MISSING_REVIEWER_HANDOFF_INPUTS"
C45_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_REVIEWER_SUBMISSION_BUNDLE_STATUS.json"


def package_reviewer_handoff(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    c45_path = root / C45_STATUS_JSON
    c45 = _read_json(c45_path)
    dataset_version = str(c45.get("dataset_version") or _read_json(reports / "C02_DATASET_POINTER.json").get("dataset_version", "UNKNOWN_DATASET"))
    package_dir = reports / "reviewer_handoff" / dataset_version
    package_zip = reports / "reviewer_handoff" / f"{dataset_version}_reviewer_handoff.zip"
    sources = _sources(c45_path, c45)
    missing = [item for item in sources if not item["source"].exists()]
    copied: list[dict[str, Any]] = []
    readme_path = package_dir / "README_REVIEWER_HANDOFF.md"

    if not missing:
        package_dir.mkdir(parents=True, exist_ok=True)
        for item in sources:
            target = package_dir / item["target_name"]
            shutil.copy2(item["source"], target)
            copied.append(
                {
                    "name": item["name"],
                    "source_path": str(item["source"]),
                    "package_path": str(target),
                    "sha256": _sha256_file(target),
                }
            )
        readme_path.write_text(_readme(c45, copied), encoding="utf-8")
        copied.append(
            {
                "name": "README reviewer handoff",
                "source_path": "",
                "package_path": str(readme_path),
                "sha256": _sha256_file(readme_path),
            }
        )
        _write_zip(package_zip, package_dir)

    status = STATUS_READY if not missing else STATUS_MISSING
    payload = {
        "status": status,
        "stage": "C49-REVIEWER-HANDOFF-PACKAGE",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": dataset_version,
        "inputs": {
            "c45_reviewer_submission_bundle": str(c45_path),
        },
        "missing_inputs": [
            {"name": item["name"], "path": str(item["source"])}
            for item in missing
        ],
        "included_artifacts": copied,
        "package": {
            "directory": str(package_dir),
            "zip": str(package_zip) if not missing else "",
            "zip_exists": package_zip.exists() if not missing else False,
            "zip_sha256": _sha256_file(package_zip) if package_zip.exists() and not missing else "",
            "readme": str(readme_path) if not missing else "",
        },
        "authorization": {
            "package_authorizes_training": False,
            "package_authorizes_python_demo_predictions": False,
            "package_authorizes_ea_consumption": False,
            "package_authorizes_broker_action": False,
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "config_write_attempted": False,
            "terminal_runtime_change_authorized": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(reports / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_reviewer_handoff_package_md(payload: dict[str, Any]) -> str:
    included_rows = [
        {
            "Artifact": item.get("name", ""),
            "Packaged path": item.get("package_path", ""),
            "SHA256": item.get("sha256", ""),
        }
        for item in payload.get("included_artifacts", [])
    ]
    missing_rows = [
        {"Artifact": item.get("name", ""), "Path": item.get("path", "")}
        for item in payload.get("missing_inputs", [])
    ]
    package = payload.get("package", {})
    return "\n".join(
        [
            "# A3 ML Reviewer Handoff Package",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Package",
            "",
            f"- Directory: {package.get('directory', '')}",
            f"- Zip: {package.get('zip', '')}",
            f"- Zip SHA256: {package.get('zip_sha256', '')}",
            f"- README: {package.get('readme', '')}",
            "",
            "## Included Artifacts",
            "",
            _table(included_rows, ["Artifact", "Packaged path", "SHA256"]) if included_rows else "No artifacts packaged.",
            "",
            "## Missing Inputs",
            "",
            _table(missing_rows, ["Artifact", "Path"]) if missing_rows else "- none",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Config write attempted: false.",
            "- Model training authorized: false.",
            "- Python demo predictions authorized: false.",
            "- EA consumption authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _sources(c45_path: Path, c45: dict[str, Any]) -> list[dict[str, Any]]:
    sources = [
        {
            "name": "C45 reviewer submission bundle JSON",
            "source": c45_path,
            "target_name": c45_path.name,
        },
        {
            "name": "C45 reviewer submission bundle Markdown",
            "source": c45_path.with_suffix(".md"),
            "target_name": c45_path.with_suffix(".md").name,
        },
    ]
    seen = {str(c45_path.resolve()), str(c45_path.with_suffix(".md").resolve())}
    for artifact in c45.get("artifact_manifest", []):
        path = Path(str(artifact.get("path", "")))
        if not path:
            continue
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "name": str(artifact.get("name", path.name)),
                "source": path,
                "target_name": path.name,
            }
        )
    return sources


def _readme(c45: dict[str, Any], copied: list[dict[str, Any]]) -> str:
    lines = [
        "# A3 ML Reviewer Handoff",
        "",
        f"Dataset: {c45.get('dataset_version', '')}",
        f"C45 status: {c45.get('status', '')}",
        "",
        "## Message To Reviewer",
        "",
        c45.get("reviewer_submission_text", ""),
        "",
        "## Commands After Reviewer Returns",
        "",
    ]
    for key, value in c45.get("commands_after_reviewer_returns", {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Included Files",
            "",
            *[f"- {Path(item['package_path']).name} ({item['name']})" for item in copied],
            "",
            "## Boundary",
            "",
            "- This package is evidence-only.",
            "- It does not authorize training, Python demo predictions, EA consumption, or broker action.",
            "- Broker action remains false.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_zip(zip_path: Path, package_dir: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(package_dir.iterdir()):
            if path.is_file():
                archive.write(path, arcname=path.name)


def _next_allowed_stage(status: str) -> str:
    if status == STATUS_READY:
        return "Send the reviewer handoff zip to the reviewer, then validate the returned C44 template through C42."
    return "Regenerate C45 and required reviewer artifacts, then rerun C49."


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_reviewer_handoff_package_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c49_reviewer_handoff_package_report"] = payload["outputs"]["status_report_json"]
    pointer["c49_reviewer_handoff_package_status"] = payload["status"]
    pointer["c49_reviewer_handoff_package_zip"] = payload["package"]["zip"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
