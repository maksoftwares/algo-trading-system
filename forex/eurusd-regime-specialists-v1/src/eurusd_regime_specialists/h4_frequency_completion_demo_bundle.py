from __future__ import annotations

import hashlib
import json
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ARCHIVE_NAME = "EURUSD_H4_FREQUENCY_COMPLETION_DEMO_BUNDLE_V1.zip"
ZIP_TIMESTAMP = (2026, 7, 30, 13, 30, 0)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class BundleResult:
    status: str
    archive_path: Path
    archive_sha256: str
    manifest_path: Path
    manifest_sha256: str
    file_count: int


@dataclass(frozen=True)
class InstallPlan:
    status: str
    target_root: Path
    checks: tuple[dict[str, Any], ...]
    planned_files: tuple[dict[str, Any], ...]
    target_writes_performed: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "target_root": str(self.target_root),
            "checks": list(self.checks),
            "planned_files": list(self.planned_files),
            "target_writes_performed": self.target_writes_performed,
        }


def _load_and_verify(
    config_path: Path,
) -> tuple[dict[str, Any], Path, list[dict[str, Any]]]:
    config_path = config_path.resolve()
    root = config_path.parent.parent
    config = json.loads(config_path.read_text(encoding="utf-8"))
    files = list(config["files"])
    seen: set[str] = set()
    for item in files:
        source = (root / item["source"]).resolve()
        bundle_path = str(item["bundle_path"]).replace("\\", "/")
        if bundle_path.startswith("/") or ".." in Path(bundle_path).parts:
            raise RuntimeError(f"Unsafe bundle path: {bundle_path}")
        if bundle_path in seen:
            raise RuntimeError(f"Duplicate bundle path: {bundle_path}")
        seen.add(bundle_path)
        if not source.is_file():
            raise FileNotFoundError(source)
        if sha256_file(source) != item["sha256"]:
            raise RuntimeError(f"Frozen source hash mismatch: {source}")
    if config["deployment_authorized"] or config["demo_orders_authorized"]:
        raise RuntimeError("Bundle configuration must remain unauthorized")
    return config, root, files


def _manifest_bytes(
    config: dict[str, Any],
    files: list[dict[str, Any]],
) -> bytes:
    manifest = {
        "schema_version": (
            "eurusd_h4_frequency_completion_demo_bundle_manifest_v1"
        ),
        "package_id": config["package_id"],
        "frozen_at_utc": config["frozen_at_utc"],
        "status": "READY_FOR_PERMISSIONED_INSTALL_NOT_DEPLOYED",
        "deployment_authorized": False,
        "demo_orders_authorized": False,
        "default_install_mode": config["default_install_mode"],
        "safety_contract": config["safety_contract"],
        "files": {
            item["bundle_path"]: {
                "sha256": item["sha256"],
                "install_in_shadow_phase": bool(
                    item["install_in_shadow_phase"]
                ),
            }
            for item in sorted(files, key=lambda row: row["bundle_path"])
        },
        "decision_policy": config["decision_policy"],
    }
    return (
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")


def _write_zip_member(
    archive: zipfile.ZipFile,
    name: str,
    payload: bytes,
) -> None:
    info = zipfile.ZipInfo(name.replace("\\", "/"), ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    archive.writestr(info, payload)


def build_bundle(
    config_path: Path,
    output_dir: Path,
) -> BundleResult:
    config, root, files = _load_and_verify(config_path)
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_bytes = _manifest_bytes(config, files)
    manifest_path = output_dir / "MANIFEST.json"
    manifest_path.write_bytes(manifest_bytes)
    archive_path = output_dir / ARCHIVE_NAME
    with zipfile.ZipFile(archive_path, "w") as archive:
        for item in sorted(files, key=lambda row: row["bundle_path"]):
            _write_zip_member(
                archive,
                item["bundle_path"],
                (root / item["source"]).read_bytes(),
            )
        _write_zip_member(archive, "MANIFEST.json", manifest_bytes)
    result = {
        "schema_version": (
            "eurusd_h4_frequency_completion_demo_bundle_result_v1"
        ),
        "package_id": config["package_id"],
        "frozen_at_utc": config["frozen_at_utc"],
        "status": "BUNDLE_READY_NO_DEPLOYMENT",
        "deployment_performed": False,
        "demo_orders_authorized": False,
        "archive": {
            "path": archive_path.name,
            "sha256": sha256_file(archive_path),
        },
        "manifest": {
            "path": manifest_path.name,
            "sha256": sha256_file(manifest_path),
        },
        "file_count_excluding_manifest": len(files),
    }
    (output_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return BundleResult(
        status=result["status"],
        archive_path=archive_path,
        archive_sha256=result["archive"]["sha256"],
        manifest_path=manifest_path,
        manifest_sha256=result["manifest"]["sha256"],
        file_count=len(files),
    )


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left.resolve())) == os.path.normcase(
        str(right.resolve())
    )


def plan_shadow_install(
    config_path: Path,
    target_root: Path,
    *,
    running_terminal_executables: Iterable[Path] = (),
    process_discovery_ok: bool = True,
) -> InstallPlan:
    config, root, files = _load_and_verify(config_path)
    target_root = target_root.resolve()
    terminal = target_root / "terminal64.exe"
    mql5 = target_root / "MQL5"
    config_dir = target_root / "Config"
    known_test_roots = [
        Path(value).resolve()
        for value in config["known_strategy_tester_roots"]
    ]
    prohibited_demo_roots = [
        Path(value).resolve()
        for value in config["prohibited_existing_demo_roots"]
    ]
    running = [
        path.resolve() for path in running_terminal_executables
    ]
    checks: list[dict[str, Any]] = [
        {
            "name": "target_root_exists",
            "passed": target_root.is_dir(),
            "detail": str(target_root),
        },
        {
            "name": "terminal_exists",
            "passed": terminal.is_file(),
            "detail": str(terminal),
        },
        {
            "name": "mql5_root_exists",
            "passed": mql5.is_dir(),
            "detail": str(mql5),
        },
        {
            "name": "config_root_exists",
            "passed": config_dir.is_dir(),
            "detail": str(config_dir),
        },
        {
            "name": "not_strategy_tester_root",
            "passed": not any(
                _same_path(target_root, item) for item in known_test_roots
            ),
            "detail": ", ".join(map(str, known_test_roots)),
        },
        {
            "name": "not_existing_demo_terminal_root",
            "passed": not any(
                _same_path(target_root, item)
                for item in prohibited_demo_roots
            ),
            "detail": ", ".join(map(str, prohibited_demo_roots)),
        },
        {
            "name": "process_discovery_succeeded",
            "passed": process_discovery_ok,
            "detail": "read-only process inventory",
        },
        {
            "name": "target_terminal_stopped",
            "passed": process_discovery_ok
            and not any(_same_path(terminal, item) for item in running),
            "detail": str(terminal),
        },
        {
            "name": "deployment_not_authorized_by_bundle",
            "passed": not config["deployment_authorized"],
            "detail": "explicit new user permission remains required",
        },
    ]
    planned: list[dict[str, Any]] = []
    collision_free = True
    for item in files:
        if not item["install_in_shadow_phase"]:
            continue
        bundle_path = Path(item["bundle_path"])
        if bundle_path.parts[0] == "MQL5":
            destination = target_root.joinpath(*bundle_path.parts)
        elif bundle_path.parts[0] == "Config":
            destination = target_root.joinpath(*bundle_path.parts)
        else:
            raise RuntimeError(
                f"Unexpected install path: {item['bundle_path']}"
            )
        existing_hash = (
            sha256_file(destination) if destination.is_file() else None
        )
        state = (
            "ABSENT"
            if existing_hash is None
            else (
                "ALREADY_MATCHES"
                if existing_hash == item["sha256"]
                else "HASH_COLLISION"
            )
        )
        if state == "HASH_COLLISION":
            collision_free = False
        planned.append(
            {
                "source": str((root / item["source"]).resolve()),
                "destination": str(destination),
                "sha256": item["sha256"],
                "target_state": state,
            }
        )
    checks.append(
        {
            "name": "no_hash_collisions",
            "passed": collision_free,
            "detail": "existing matching files are allowed; drift is blocked",
        }
    )
    ready = all(bool(check["passed"]) for check in checks)
    return InstallPlan(
        status="READY_NO_WRITES" if ready else "BLOCKED_NO_WRITES",
        target_root=target_root,
        checks=tuple(checks),
        planned_files=tuple(planned),
        target_writes_performed=0,
    )
