from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


MISSING_INPUTS_RELATIVE_PATH = Path("outputs/reports/SECOND_EA_RESEARCH_MISSING_INPUTS.md")
REQUIRED_SOURCE_DOCUMENTS = (
    "CODEX_BRIEF_SECOND_EA_RESEARCH_LANES_2026_06_10.md",
    "SECOND_EA_RESEARCH_LANES_DOC_REVIEW_2026_06_10.md",
    "TRUE_HOLDOUT_POLICY.md",
    "HYPOTHESIS_LOCKING.md",
    "NO_TUNING_RULES.md",
    "HYPOTHESIS_TEMPLATE.md",
    "CANDIDATE_RESEARCH_BACKLOG.md",
    "PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.md",
    "PHASE0_CONCENTRATION_FREQUENCY_NORMALIZED_AUDIT.md",
    "PHASE0_REALITY_CHECK.md",
    "MEASURED_COST_MODEL.md",
    "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md",
    "COST_SUSPENDED_LIFECYCLE_REPORT.md",
)
NEAR_NAME_CONTEXT = (
    "PHASE0_REALITY_CHECK_INTERPRETATION.md",
    "MEASURED_COST_REVALIDATION_DECISION.md",
    "MEASURED_COST_REVALIDATION_SANITY_CHECK.md",
)


@dataclass(frozen=True)
class MissingInputsReport:
    status: str
    generated_at_utc: str
    report_path: Path
    found_paths: tuple[Path, ...]
    missing_documents: tuple[str, ...]
    near_name_paths: tuple[Path, ...]


def generate_missing_inputs_report(
    phase0_root: Path,
    repo_root: Path | None = None,
    downloads_root: Path | None = None,
) -> MissingInputsReport:
    repo = repo_root or phase0_root.parents[1]
    downloads = downloads_root or phase0_root.parents[2]
    found_by_name = find_required_source_documents(repo, downloads)
    near_paths = find_near_name_context(repo)
    missing = tuple(name for name in REQUIRED_SOURCE_DOCUMENTS if name not in found_by_name)
    found_paths = tuple(found_by_name[name] for name in REQUIRED_SOURCE_DOCUMENTS if name in found_by_name)
    report = MissingInputsReport(
        status="PASS" if not missing else "MISSING",
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        report_path=phase0_root / MISSING_INPUTS_RELATIVE_PATH,
        found_paths=found_paths,
        missing_documents=missing,
        near_name_paths=near_paths,
    )
    report.report_path.parent.mkdir(parents=True, exist_ok=True)
    report.report_path.write_text(render_missing_inputs_report(report, phase0_root), encoding="utf-8")
    return report


def find_required_source_documents(repo_root: Path, downloads_root: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    required = set(REQUIRED_SOURCE_DOCUMENTS)
    for path in sorted((p for p in repo_root.rglob("*") if p.is_file() and p.name in required), key=_sort_key):
        found.setdefault(path.name, path)
    for path in sorted((p for p in downloads_root.glob("*") if p.is_file() and p.name in required), key=_sort_key):
        found.setdefault(path.name, path)
    return found


def find_near_name_context(repo_root: Path) -> tuple[Path, ...]:
    near = set(NEAR_NAME_CONTEXT)
    return tuple(sorted((p for p in repo_root.rglob("*") if p.is_file() and p.name in near), key=_sort_key))


def render_missing_inputs_report(report: MissingInputsReport, phase0_root: Path) -> str:
    missing_label = "file name was" if len(report.missing_documents) == 1 else "file names were"
    lines = [
        "# Second EA Research Missing Inputs",
        "",
        f"Generated at UTC: {report.generated_at_utc}",
        "",
        (
            "The goal requires exact source documents to be read before coding. "
            f"The following exact {missing_label} not found in the repository or top-level Downloads folder "
            "and must not be inferred from similarly named files:"
        ),
        "",
        "| Required document | Status |",
        "| --- | --- |",
    ]
    if report.missing_documents:
        lines.extend(f"| `{name}` | MISSING |" for name in report.missing_documents)
    else:
        lines.append("| none | PASS |")
    lines.extend(["", "Found exact-name inputs:", ""])
    lines.extend(f"- `{_display_path(path, phase0_root)}`" for path in report.found_paths)
    lines.extend(["", "Near-name context observed but not treated as exact substitutes:", ""])
    if report.near_name_paths:
        lines.extend(f"- `{_display_path(path, phase0_root)}`" for path in report.near_name_paths)
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _display_path(path: Path, phase0_root: Path) -> str:
    try:
        return path.relative_to(phase0_root).as_posix()
    except ValueError:
        try:
            return path.relative_to(phase0_root.parents[1]).as_posix()
        except ValueError:
            return path.as_posix()


def _sort_key(path: Path) -> str:
    return path.as_posix().lower()
