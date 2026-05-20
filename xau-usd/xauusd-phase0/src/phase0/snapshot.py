from __future__ import annotations

import subprocess
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from phase0.config import ProjectConfig
from phase0.manifests import generate_result_manifest


@dataclass(frozen=True)
class SnapshotOutput:
    snapshot_path: Path
    included_files: tuple[str, ...]


def generate_snapshot(config: ProjectConfig, include_raw_data: bool = False) -> SnapshotOutput:
    snapshots_dir = config.root / "outputs" / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    generate_result_manifest(config)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    snapshot_path = snapshots_dir / f"phase0_snapshot_{stamp}.zip"
    files = _snapshot_files(config, include_raw_data)
    included: list[str] = []

    with zipfile.ZipFile(snapshot_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            if not path.exists() or not path.is_file():
                continue
            arcname = path.relative_to(config.root).as_posix()
            archive.write(path, arcname)
            included.append(arcname)
        commit = _git_commit(config.root)
        archive.writestr("git_commit.txt", commit or "unavailable")
        included.append("git_commit.txt")
        archive.writestr("git_status.txt", _git_status(config.root) or "unavailable")
        included.append("git_status.txt")
        archive.writestr("snapshot_manifest.txt", "\n".join(sorted(included)))
        included.append("snapshot_manifest.txt")

    return SnapshotOutput(snapshot_path, tuple(sorted(included)))


def _snapshot_files(config: ProjectConfig, include_raw_data: bool) -> list[Path]:
    roots = [
        config.root / "config",
        config.root / "docs",
        config.root / "scripts",
        config.root / "mt5",
        config.root / "src" / "phase0",
        config.root / "tests",
        config.root / "outputs" / "hashes",
        config.root / "outputs" / "manifests",
        config.root / "outputs" / "matrix_results",
        config.root / "outputs" / "decile_results",
        config.root / "outputs" / "multisymbol_results",
        config.root / "outputs" / "adversarial_review",
        config.root / "outputs" / "reports",
    ]
    files: list[Path] = []
    for root in roots:
        if root.exists():
            files.extend(_iter_snapshot_files(root))

    for name in ("requirements.txt", "pyproject.toml", "README.md", "CODEX_IMPLEMENTATION_SPEC.md"):
        files.append(config.root / name)
    data_readme = config.root / "data" / "README_DATA.md"
    files.append(data_readme)
    if include_raw_data:
        raw_dir = config.root / "data" / "raw"
        if raw_dir.exists():
            files.extend(_iter_snapshot_files(raw_dir))
    return _deduplicate(files)


def _iter_snapshot_files(root: Path) -> list[Path]:
    ignored_parts = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv"}
    ignored_suffixes = {".pyc", ".pyo"}
    ignored_name_suffixes = (".egg-info",)
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in ignored_parts for part in path.parts):
            continue
        if any(part.endswith(ignored_name_suffixes) for part in path.parts):
            continue
        if path.suffix in ignored_suffixes:
            continue
        files.append(path)
    return files


def _deduplicate(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    result: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        result.append(path)
    return result


def _git_commit(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return result.stdout.strip() or "clean"


def _git_status(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "status", "--short"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return result.stdout.strip() or "clean"
