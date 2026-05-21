from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from phase0.config import ConfigError, ProjectConfig

HASH_MANIFEST_COLUMNS = (
    "expert",
    "hypothesis_file",
    "sha256",
    "registered_at_utc",
    "file_size_bytes",
    "git_commit_if_available",
)

REQUIRED_HYPOTHESIS_SECTIONS = (
    "Mechanical Definition",
    "Expected Behavior",
    "Why This Hypothesis Should Exist",
    "What Would Falsify It",
)
REQUIRED_HYPOTHESIS_FIELDS = (
    "Hypothesis date:",
    "Hypothesis version:",
    "Author / owner:",
    "Expected trade count per year:",
    "Expected cost-adjusted PF:",
    "Expected losing-month percentage:",
    "Expected worst single month:",
    "Expected max consecutive zero months:",
    "Expected R-multiple distribution:",
)
PLACEHOLDER_PATTERNS = (
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bPLACEHOLDER\b", re.IGNORECASE),
    re.compile(r"before any result-producing backtest", re.IGNORECASE),
    re.compile(r"before hash registration", re.IGNORECASE),
)


class HashingError(ConfigError):
    """Raised when hypothesis hash registration or validation fails."""


@dataclass(frozen=True)
class HypothesisHash:
    expert: str
    hypothesis_file: str
    sha256: str
    registered_at_utc: str
    file_size_bytes: int
    git_commit_if_available: str


def hash_manifest_path(config: ProjectConfig) -> Path:
    return config.root / "outputs" / "hashes" / "hypothesis_hash_manifest.csv"


def sha256_file(path: str | Path) -> str:
    resolved = Path(path)
    if not resolved.exists():
        raise HashingError(f"Hypothesis file not found: {resolved}. Create it before registering.")
    if not resolved.is_file():
        raise HashingError(f"Hypothesis path is not a file: {resolved}.")

    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_enabled_hypotheses(config: ProjectConfig) -> list[tuple[str, Path]]:
    hypotheses: list[tuple[str, Path]] = []
    for expert, details in config.phase0["experts"].items():
        if not details.get("enabled", False):
            continue
        relative_path = Path(str(details["hypothesis_file"]))
        hypotheses.append((expert, config.root / relative_path))
    return hypotheses


def register_hypotheses(config: ProjectConfig, force: bool = False) -> list[HypothesisHash]:
    manifest_path = hash_manifest_path(config)
    if manifest_path.exists() and not force:
        existing = load_hash_manifest(manifest_path)
        if existing and validate_hypotheses(config, raise_on_mismatch=False):
            return existing
        raise HashingError(
            f"Hash manifest already exists at {manifest_path}. "
            "Use --force only if no result-producing backtests have been run, or create new hypothesis versions."
        )

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    registered_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    git_commit = current_git_commit(config.root)
    rows: list[HypothesisHash] = []
    for expert, hypothesis_path in iter_enabled_hypotheses(config):
        rows.append(
            HypothesisHash(
                expert=expert,
                hypothesis_file=str(hypothesis_path.relative_to(config.root).as_posix()),
                sha256=sha256_file(hypothesis_path),
                registered_at_utc=registered_at,
                file_size_bytes=hypothesis_path.stat().st_size,
                git_commit_if_available=git_commit,
            )
        )

    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HASH_MANIFEST_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row_to_dict(row))
    return rows


def validate_hypotheses(config: ProjectConfig, raise_on_mismatch: bool = True) -> bool:
    manifest_path = hash_manifest_path(config)
    registered = {row.expert: row for row in load_hash_manifest(manifest_path)}
    errors: list[str] = []

    for expert, hypothesis_path in iter_enabled_hypotheses(config):
        row = registered.get(expert)
        if row is None:
            errors.append(f"{expert}: no registered hash found in {manifest_path}")
            continue
        current_hash = sha256_file(hypothesis_path)
        if current_hash != row.sha256:
            errors.append(
                f"{expert}: Hypothesis file has changed after registration. "
                "Re-register only if no results have been produced, or create a new hypothesis version."
            )

    if errors and raise_on_mismatch:
        raise HashingError("\n".join(errors))
    return not errors


def validate_hypotheses_complete(config: ProjectConfig, raise_on_error: bool = True) -> bool:
    errors: list[str] = []
    for expert, hypothesis_path in iter_enabled_hypotheses(config):
        errors.extend(_hypothesis_completeness_errors(expert, hypothesis_path))

    if errors and raise_on_error:
        raise HashingError(
            "Hypothesis pre-registration is incomplete. "
            "Real-data Phase 0 runs are invalid until every enabled hypothesis is fully specified:\n"
            + "\n".join(errors)
        )
    return not errors


def validate_hypothesis_file_complete(
    expert: str,
    hypothesis_path: str | Path,
    raise_on_error: bool = True,
) -> bool:
    path = Path(hypothesis_path)
    errors = _hypothesis_completeness_errors(expert, path)
    if errors and raise_on_error:
        raise HashingError(
            f"Hypothesis pre-registration is incomplete for {expert}:\n" + "\n".join(errors)
        )
    return not errors


def load_hash_manifest(path: str | Path) -> list[HypothesisHash]:
    resolved = Path(path)
    if not resolved.exists():
        raise HashingError(
            f"Hash manifest not found: {resolved}. Run `python -m phase0 hash-hypotheses --register`."
        )

    with resolved.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != HASH_MANIFEST_COLUMNS:
            raise HashingError(
                f"Hash manifest {resolved} has invalid columns. "
                f"Expected: {', '.join(HASH_MANIFEST_COLUMNS)}."
            )
        return [
            HypothesisHash(
                expert=row["expert"],
                hypothesis_file=row["hypothesis_file"],
                sha256=row["sha256"],
                registered_at_utc=row["registered_at_utc"],
                file_size_bytes=int(row["file_size_bytes"]),
                git_commit_if_available=row["git_commit_if_available"],
            )
            for row in reader
        ]


def _hypothesis_completeness_errors(expert: str, path: Path) -> list[str]:
    if not path.exists():
        return [f"{expert}: hypothesis file not found: {path}"]
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.search(text):
            errors.append(f"{expert}: placeholder text remains in {path.name}: {pattern.pattern}")

    for section in REQUIRED_HYPOTHESIS_SECTIONS:
        if f"## {section}" not in text:
            errors.append(f"{expert}: missing section '## {section}' in {path.name}")

    for field in REQUIRED_HYPOTHESIS_FIELDS:
        value = _field_value(text, field)
        if value is None:
            errors.append(f"{expert}: missing required field '{field}' in {path.name}")
        elif not value.strip():
            errors.append(f"{expert}: required field '{field}' is empty in {path.name}")

    for section in REQUIRED_HYPOTHESIS_SECTIONS:
        body = _section_body(text, section)
        if body is None:
            continue
        meaningful_lines = [
            line.strip()
            for line in body.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if not meaningful_lines:
            errors.append(f"{expert}: section '## {section}' has no content in {path.name}")

    return errors


def _field_value(text: str, field: str) -> str | None:
    for line in text.splitlines():
        if line.strip().lower().startswith(field.lower()):
            return line.split(":", 1)[1].strip()
    return None


def _section_body(text: str, section: str) -> str | None:
    marker = f"## {section}"
    start = text.find(marker)
    if start < 0:
        return None
    body_start = text.find("\n", start)
    if body_start < 0:
        return ""
    next_section = text.find("\n## ", body_start + 1)
    if next_section < 0:
        return text[body_start:].strip()
    return text[body_start:next_section].strip()


def current_git_commit(root: Path) -> str:
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


def row_to_dict(row: HypothesisHash) -> dict[str, str | int]:
    return {
        "expert": row.expert,
        "hypothesis_file": row.hypothesis_file,
        "sha256": row.sha256,
        "registered_at_utc": row.registered_at_utc,
        "file_size_bytes": row.file_size_bytes,
        "git_commit_if_available": row.git_commit_if_available,
    }
