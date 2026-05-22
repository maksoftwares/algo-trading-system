from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from phase0.config import ProjectConfig
from phase0.hashing import HashingError, hash_manifest_path, validate_hypotheses, validate_hypotheses_complete
from phase0.holdout import write_run_context_manifest
from phase0.reference import validate_reference_files


@dataclass(frozen=True)
class ArtifactCheck:
    name: str
    status: str
    message: str


@dataclass(frozen=True)
class RealArtifactVerificationOutput:
    status: str
    report_path: Path
    checks: tuple[ArtifactCheck, ...]


def verify_real_artifacts(config: ProjectConfig) -> RealArtifactVerificationOutput:
    write_run_context_manifest(config)
    checks = [
        _check_reference(config),
        _check_hypotheses_complete(config),
        _check_hypothesis_hashes(config),
        _check_file("result_manifest", config.root / "outputs" / "manifests" / "PHASE0_RESULT_MANIFEST.csv"),
        _check_file("run_context_manifest", config.root / "outputs" / "manifests" / "PHASE0_RUN_CONTEXT.json"),
        _check_file("data_readiness_report", config.root / "outputs" / "manifests" / "PHASE0_DATA_READINESS.md"),
        _check_file("data_manifest", config.root / "outputs" / "manifests" / "PHASE0_DATA_MANIFEST.md"),
        _check_file("consolidated_verdict", config.root / "outputs" / "reports" / "PHASE0_VERDICT.md"),
        _check_file("cost_reporting_policy", config.root / "docs" / "COST_REPORTING_POLICY.md"),
        _check_status_report(
            "fixed_notional_report",
            config.root / "outputs" / "reports" / "FIXED_NOTIONAL_REPORT.md",
            "Run generate-fixed-notional-report before Phase 2 authorization.",
        ),
        _check_holdout_manifest(config),
        _check_true_holdout_audit(config),
        _check_status_report(
            "independent_reproduction",
            config.root / "outputs" / "reports" / "PHASE0_INDEPENDENT_REPRODUCTION.md",
            "Run generate-independent-reproduction before Phase 2 authorization.",
        ),
        _check_status_report(
            "cpcv_validation",
            config.root / "outputs" / "reports" / "PHASE0_CPCV_VALIDATION.md",
            "Run run-cpcv-validation before Phase 2 authorization.",
        ),
        _check_status_report(
            "reality_check",
            config.root / "outputs" / "reports" / "PHASE0_REALITY_CHECK.md",
            "Run run-reality-check before Phase 2 authorization.",
        ),
        _check_verdict_state(config),
        _check_intrabar_reports(config),
        _check_adversarial_scores(config),
        _check_review_bundle(config),
    ]
    status = "PASS" if all(check.status in {"PASS", "WARN"} for check in checks) else "FAIL"
    report_path = config.root / "outputs" / "reports" / "PHASE0_REAL_ARTIFACT_VERIFICATION.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(status, checks), encoding="utf-8")
    return RealArtifactVerificationOutput(status, report_path, tuple(checks))


def _check_reference(config: ProjectConfig) -> ArtifactCheck:
    try:
        output = validate_reference_files(config, raise_on_error=True)
    except Exception as exc:
        return ArtifactCheck("reference_status", "FAIL", str(exc))
    if output.status == "DOCUMENTED_MISSING":
        return ArtifactCheck(
            "reference_status",
            "WARN",
            "Some original reference docs are missing, but reference/README.md documents the gap.",
        )
    return ArtifactCheck("reference_status", "PASS", "Reference status is documented.")


def _check_hypotheses_complete(config: ProjectConfig) -> ArtifactCheck:
    try:
        complete = validate_hypotheses_complete(config, raise_on_error=False)
    except Exception as exc:
        return ArtifactCheck("hypotheses_complete", "FAIL", str(exc))
    return ArtifactCheck(
        "hypotheses_complete",
        "PASS" if complete else "FAIL",
        "Enabled hypothesis files contain all required fields and no placeholders."
        if complete
        else "One or more enabled hypothesis files are incomplete.",
    )


def _check_hypothesis_hashes(config: ProjectConfig) -> ArtifactCheck:
    try:
        valid = validate_hypotheses(config, raise_on_mismatch=False)
    except HashingError as exc:
        return ArtifactCheck("hypothesis_hashes", "FAIL", str(exc))
    return ArtifactCheck(
        "hypothesis_hashes",
        "PASS" if valid else "FAIL",
        f"Hypothesis hashes match {hash_manifest_path(config)}."
        if valid
        else "Current hypothesis files do not match the registered hash manifest.",
    )


def _check_file(name: str, path: Path) -> ArtifactCheck:
    return ArtifactCheck(
        name,
        "PASS" if path.exists() else "FAIL",
        f"Found {path}" if path.exists() else f"Missing required artifact {path}",
    )


def _check_holdout_manifest(config: ProjectConfig) -> ArtifactCheck:
    path = config.root / "outputs" / "manifests" / "PHASE0_RUN_CONTEXT.json"
    if not path.exists():
        return ArtifactCheck("true_holdout_status", "FAIL", f"Missing {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    required = (
        "true_holdout_period_start",
        "true_holdout_period_end",
        "true_holdout_unlocked",
        "true_holdout_unlock_file",
        "true_holdout_overlap_detected",
    )
    missing = [field for field in required if field not in data]
    if missing:
        return ArtifactCheck("true_holdout_status", "FAIL", "Missing field(s): " + ", ".join(missing))
    if data["true_holdout_unlocked"]:
        return ArtifactCheck(
            "true_holdout_status",
            "FAIL",
            "True holdout is marked unlocked; final approval evidence must be reviewed separately.",
        )
    return ArtifactCheck(
        "true_holdout_status",
        "PASS",
        "True holdout status is explicit and remains locked.",
    )


def _check_true_holdout_audit(config: ProjectConfig) -> ArtifactCheck:
    path = config.root / "outputs" / "reports" / "PHASE0_TRUE_HOLDOUT_AUDIT.md"
    if not path.exists():
        return ArtifactCheck(
            "true_holdout_audit",
            "WARN",
            f"Missing {path}. Run audit-true-holdout before Phase 2 authorization.",
        )
    status = ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Overall status:"):
            status = line.split(":", 1)[1].strip()
            break
    if status == "PASS":
        return ArtifactCheck("true_holdout_audit", "PASS", f"Holdout audit passed: {path}.")
    return ArtifactCheck(
        "true_holdout_audit",
        "FAIL",
        f"Holdout audit status is {status or 'unknown'}: {path}.",
    )


def _check_status_report(name: str, path: Path, missing_message: str) -> ArtifactCheck:
    if not path.exists():
        return ArtifactCheck(name, "WARN", f"Missing {path}. {missing_message}")
    status = _extract_status(path)
    if status == "PASS":
        return ArtifactCheck(name, "PASS", f"{name.replace('_', ' ').title()} passed: {path}.")
    return ArtifactCheck(name, "FAIL", f"{name.replace('_', ' ').title()} status is {status or 'unknown'}: {path}.")


def _extract_status(path: Path) -> str:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Overall status:") or line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _check_verdict_state(config: ProjectConfig) -> ArtifactCheck:
    path = config.root / "outputs" / "reports" / "PHASE0_VERDICT.md"
    if not path.exists():
        return ArtifactCheck("final_verdict_state", "FAIL", f"Missing {path}")
    text = path.read_text(encoding="utf-8")
    if "INVALID_PRE_REGISTRATION" in text:
        return ArtifactCheck(
            "final_verdict_state",
            "FAIL",
            "Verdict explicitly marks pre-registration invalid.",
        )
    approved = _section_body(text, "## Experts Approved for Phase 1")
    pending_manual = _section_body(text, "## Experts Pending Manual Review")
    invalid_registration = _section_body(text, "## Invalid Pre-Registration")
    if "PENDING_MANUAL_REVIEW" in text:
        return ArtifactCheck(
            "final_verdict_state",
            "FAIL",
            "Verdict still contains a final pending-manual-review state; Phase 1 EA coding remains blocked.",
        )
    if invalid_registration and invalid_registration.strip() != "None.":
        return ArtifactCheck(
            "final_verdict_state",
            "FAIL",
            "Verdict lists invalid pre-registration entries.",
        )
    if pending_manual and pending_manual.strip() != "None.":
        return ArtifactCheck(
            "final_verdict_state",
            "FAIL",
            "Verdict lists experts still pending manual review.",
        )
    if "- " in approved:
        return ArtifactCheck("final_verdict_state", "PASS", "Verdict contains at least one final approved expert.")
    return ArtifactCheck("final_verdict_state", "FAIL", "Verdict does not list an approved Phase 1 expert.")


def _section_body(text: str, heading: str) -> str:
    if heading not in text:
        return ""
    after_heading = text.split(heading, 1)[1]
    if "\n## " in after_heading:
        after_heading = after_heading.split("\n## ", 1)[0]
    return after_heading.strip()


def _check_intrabar_reports(config: ProjectConfig) -> ArtifactCheck:
    missing = [
        expert
        for expert in _enabled_experts(config)
        if not (config.root / "outputs" / "reports" / f"{expert}_intrabar_ambiguity_report.md").exists()
    ]
    if missing:
        return ArtifactCheck(
            "intrabar_ambiguity_reports",
            "WARN",
            "Missing intrabar ambiguity reports for: " + ", ".join(missing),
        )
    return ArtifactCheck("intrabar_ambiguity_reports", "PASS", "Intrabar ambiguity reports exist.")


def _check_adversarial_scores(config: ProjectConfig) -> ArtifactCheck:
    missing = [
        expert
        for expert in _enabled_experts(config)
        if not (config.root / "outputs" / "adversarial_review" / f"{expert}_adversarial_score.md").exists()
    ]
    if missing:
        return ArtifactCheck(
            "adversarial_scores",
            "FAIL",
            "Missing scored adversarial review files for: " + ", ".join(missing),
        )
    return ArtifactCheck("adversarial_scores", "PASS", "Scored adversarial review files exist.")


def _check_review_bundle(config: ProjectConfig) -> ArtifactCheck:
    bundle_dir = config.root / "outputs" / "review_bundles"
    bundles = sorted(bundle_dir.glob("PHASE0_REVIEW_BUNDLE_*.zip")) if bundle_dir.exists() else []
    if not bundles:
        return ArtifactCheck(
            "review_bundle",
            "FAIL",
            f"Missing review bundle in {bundle_dir}. Run generate-review-bundle.",
        )
    return ArtifactCheck("review_bundle", "PASS", f"Found latest review bundle {bundles[-1]}.")


def _enabled_experts(config: ProjectConfig) -> tuple[str, ...]:
    return tuple(
        expert
        for expert, details in config.phase0["experts"].items()
        if details.get("enabled", False)
    )


def _render_report(status: str, checks: list[ArtifactCheck]) -> str:
    rows = [
        {
            "Check": check.name,
            "Status": check.status,
            "Message": check.message,
        }
        for check in checks
    ]
    return "\n".join(
        [
            "# Phase 0 Real Artifact Verification",
            "",
            f"Overall status: {status}",
            "",
            _markdown_table(rows, ["Check", "Status", "Message"]),
            "",
            "A PASS here means the artifact package is structurally reviewable. It does not approve "
            "EA coding unless the consolidated verdict also contains a final approved expert.",
            "",
        ]
    )


def _markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_escape(str(row.get(column, ""))) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")
