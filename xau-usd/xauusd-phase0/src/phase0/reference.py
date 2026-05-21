from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from phase0.config import ConfigError, ProjectConfig


EXPECTED_REFERENCE_FILES = (
    "xauusd_phase0_codex_implementation_spec.md",
    "PHASE0_STATISTICAL_STUDY_SPEC.md",
    "PATH_TO_10.md",
    "PLAN_V01_REVIEW_FINDINGS.md",
    "xauusd_master_ea_plan_v0_3_phase0_first_review_ready.md",
)


@dataclass(frozen=True)
class ReferenceValidationOutput:
    status: str
    reference_dir: Path
    existing_files: tuple[str, ...]
    missing_files: tuple[str, ...]
    readme_path: Path


def validate_reference_files(
    config: ProjectConfig,
    *,
    raise_on_error: bool = True,
) -> ReferenceValidationOutput:
    reference_dir = config.root / "reference"
    readme_path = reference_dir / "README.md"
    errors: list[str] = []

    if not reference_dir.exists():
        errors.append(f"Missing reference directory: {reference_dir}")
        output = ReferenceValidationOutput("FAIL", reference_dir, (), EXPECTED_REFERENCE_FILES, readme_path)
        return _raise_or_return(output, errors, raise_on_error)

    existing = tuple(name for name in EXPECTED_REFERENCE_FILES if (reference_dir / name).is_file())
    missing = tuple(name for name in EXPECTED_REFERENCE_FILES if name not in existing)
    readme_documents_missing = _readme_documents_missing(readme_path, missing)

    if missing and not readme_documents_missing:
        errors.append(
            "Reference specs are missing and reference/README.md does not explicitly document the gap: "
            + ", ".join(missing)
        )
        status = "FAIL"
    elif missing:
        status = "DOCUMENTED_MISSING"
    else:
        status = "PASS"

    output = ReferenceValidationOutput(status, reference_dir, existing, missing, readme_path)
    return _raise_or_return(output, errors, raise_on_error)


def _readme_documents_missing(readme_path: Path, missing: tuple[str, ...]) -> bool:
    if not missing or not readme_path.exists():
        return False
    text = readme_path.read_text(encoding="utf-8").lower()
    return "missing reference" in text and all(name.lower() in text for name in missing)


def _raise_or_return(
    output: ReferenceValidationOutput,
    errors: list[str],
    raise_on_error: bool,
) -> ReferenceValidationOutput:
    if errors and raise_on_error:
        raise ConfigError("\n".join(errors))
    return output
