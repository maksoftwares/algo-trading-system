from __future__ import annotations

import json
import subprocess
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from phase0.config import ProjectConfig
from phase0.manifests import generate_result_manifest


@dataclass(frozen=True)
class ReviewBundleOutput:
    bundle_path: Path
    included_files: tuple[str, ...]


def generate_review_bundle(config: ProjectConfig) -> ReviewBundleOutput:
    output_dir = config.root / "outputs" / "review_bundles"
    output_dir.mkdir(parents=True, exist_ok=True)
    generate_result_manifest(config)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bundle_path = output_dir / f"PHASE0_REVIEW_BUNDLE_{stamp}.zip"

    files = _review_bundle_files(config)
    included: list[str] = []
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            if not path.exists() or not path.is_file():
                continue
            arcname = path.relative_to(config.root).as_posix()
            archive.write(path, arcname)
            included.append(arcname)

        manifest = {
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "git_commit": _git_commit(config.root) or "unavailable",
            "git_status": _git_status(config.root) or "unavailable",
            "raw_data_included": False,
            "included_files": sorted(included),
        }
        archive.writestr("review_bundle_manifest.json", json.dumps(manifest, indent=2))
        included.append("review_bundle_manifest.json")

    return ReviewBundleOutput(bundle_path=bundle_path, included_files=tuple(sorted(included)))


def _review_bundle_files(config: ProjectConfig) -> list[Path]:
    roots = [
        config.root / "docs",
        config.root / "outputs" / "hashes",
        config.root / "outputs" / "manifests",
        config.root / "outputs" / "reports",
        config.root / "outputs" / "matrix_results",
        config.root / "outputs" / "decile_results",
        config.root / "outputs" / "multisymbol_results",
        config.root / "outputs" / "adversarial_review",
    ]
    files: list[Path] = []
    for root in roots:
        if root.exists():
            files.extend(_iter_files(root))

    for path in (
        config.root / "config" / "phase0.yaml",
        config.root / "config" / "cost_models.yaml",
        config.root / "config" / "true_holdout_period.yaml",
        config.root / "README.md",
    ):
        files.append(path)
    return _deduplicate(files)


def _iter_files(root: Path) -> list[Path]:
    ignored_parts = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv"}
    ignored_suffixes = {".pyc", ".pyo"}
    return [
        path
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and not any(part in ignored_parts for part in path.parts)
        and path.suffix not in ignored_suffixes
    ]


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
    return result.stdout.strip()


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
