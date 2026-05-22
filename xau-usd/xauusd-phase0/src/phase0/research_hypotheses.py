from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from phase0.config import ConfigError, ProjectConfig
from phase0.hashing import (
    HASH_MANIFEST_COLUMNS,
    HypothesisHash,
    current_git_commit,
    row_to_dict,
    sha256_file,
    validate_hypothesis_file_complete,
)


@dataclass(frozen=True)
class ResearchHypothesisRegistration:
    status: str
    report_path: Path
    manifest_path: Path
    expert: str
    sha256: str
    phase0_result_run_allowed: bool


@dataclass(frozen=True)
class ResearchHypothesisValidation:
    status: str
    expert: str
    hypothesis_file: Path
    sha256: str
    message: str


def register_research_hypothesis(
    config: ProjectConfig,
    expert: str,
    hypothesis_file: str,
    force: bool = False,
) -> ResearchHypothesisRegistration:
    if not expert.strip():
        raise ConfigError("Research hypothesis expert name cannot be empty.")
    relative_path = Path(hypothesis_file)
    if relative_path.is_absolute():
        raise ConfigError("Research hypothesis file must be relative to the Phase 0 root.")
    hypothesis_path = config.root / relative_path
    validate_hypothesis_file_complete(expert, hypothesis_path, raise_on_error=True)

    manifest_path = config.root / "outputs" / "hashes" / "research_hypothesis_hash_manifest.csv"
    report_path = config.root / "outputs" / "reports" / f"{expert}_research_hypothesis_registration.md"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    existing = _load_existing_rows(manifest_path)
    if expert in existing and existing[expert].sha256 != sha256_file(hypothesis_path) and not force:
        raise ConfigError(
            f"Research hypothesis {expert!r} is already registered with a different hash. "
            "Use --force only before any result-producing run exists for this version."
        )

    registered_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    row = HypothesisHash(
        expert=expert,
        hypothesis_file=relative_path.as_posix(),
        sha256=sha256_file(hypothesis_path),
        registered_at_utc=registered_at,
        file_size_bytes=hypothesis_path.stat().st_size,
        git_commit_if_available=current_git_commit(config.root),
    )
    existing[expert] = row
    _write_manifest(manifest_path, existing)
    report_path.write_text(_render_report(row, manifest_path), encoding="utf-8")
    return ResearchHypothesisRegistration(
        status="REGISTERED",
        report_path=report_path,
        manifest_path=manifest_path,
        expert=expert,
        sha256=row.sha256,
        phase0_result_run_allowed=False,
    )


def validate_research_hypothesis(
    config: ProjectConfig,
    expert: str,
    hypothesis_file: str,
) -> ResearchHypothesisValidation:
    relative_path = Path(hypothesis_file)
    if relative_path.is_absolute():
        raise ConfigError("Research hypothesis file must be relative to the Phase 0 root.")
    hypothesis_path = config.root / relative_path
    validate_hypothesis_file_complete(expert, hypothesis_path, raise_on_error=True)
    manifest_path = config.root / "outputs" / "hashes" / "research_hypothesis_hash_manifest.csv"
    existing = _load_existing_rows(manifest_path)
    if expert not in existing:
        raise ConfigError(f"Research hypothesis {expert!r} is not registered in {manifest_path}.")
    current_hash = sha256_file(hypothesis_path)
    registered = existing[expert]
    if registered.hypothesis_file != relative_path.as_posix():
        raise ConfigError(
            f"Research hypothesis {expert!r} is registered to {registered.hypothesis_file}, "
            f"not {relative_path.as_posix()}."
        )
    if registered.sha256 != current_hash:
        raise ConfigError(
            f"Research hypothesis {expert!r} changed after registration. "
            "Create a new version before testing."
        )
    return ResearchHypothesisValidation(
        status="PASS",
        expert=expert,
        hypothesis_file=hypothesis_path,
        sha256=current_hash,
        message="Research hypothesis is complete and hash-locked.",
    )


def _load_existing_rows(path: Path) -> dict[str, HypothesisHash]:
    if not path.exists():
        return {}
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != HASH_MANIFEST_COLUMNS:
            raise ConfigError(
                f"Research hash manifest {path} has invalid columns. "
                f"Expected: {', '.join(HASH_MANIFEST_COLUMNS)}."
            )
        rows = {}
        for row in reader:
            rows[row["expert"]] = HypothesisHash(
                expert=row["expert"],
                hypothesis_file=row["hypothesis_file"],
                sha256=row["sha256"],
                registered_at_utc=row["registered_at_utc"],
                file_size_bytes=int(row["file_size_bytes"]),
                git_commit_if_available=row["git_commit_if_available"],
            )
        return rows


def _write_manifest(path: Path, rows: dict[str, HypothesisHash]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HASH_MANIFEST_COLUMNS)
        writer.writeheader()
        for expert in sorted(rows):
            writer.writerow(row_to_dict(rows[expert]))


def _render_report(row: HypothesisHash, manifest_path: Path) -> str:
    return "\n".join(
        [
            "# Research Hypothesis Registration",
            "",
            "Status: REGISTERED",
            f"Generated at UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}",
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| Expert | `{row.expert}` |",
            f"| Hypothesis file | `{row.hypothesis_file}` |",
            f"| SHA256 | `{row.sha256}` |",
            f"| Registered at UTC | `{row.registered_at_utc}` |",
            f"| Manifest | `{manifest_path.as_posix()}` |",
            "",
            "## Result-Producing Run Status",
            "",
            "Current status: `BLOCKED_BY_MISSING_STRATEGY_IMPLEMENTATION`",
            "",
            (
                "The research hypothesis is locked, but no matrix, decile, multisymbol, or adversarial "
                "result run is authorized until a matching versioned strategy implementation exists and "
                "is explicitly enabled for a fresh Phase 0 pass."
            ),
            "",
        ]
    )
