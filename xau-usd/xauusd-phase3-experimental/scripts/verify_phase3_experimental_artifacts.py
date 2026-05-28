from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


PHASE2_AUTHORITY_SENTENCE = (
    "This report has no authority over Phase 2 readiness. "
    "PHASE2_READINESS_REPORT.md remains the sole real readiness authority."
)

REQUIRED_ARTIFACTS = (
    "PHASE3_EXPERIMENTAL_STATUS.md",
    "PHASE3_EXPERIMENTAL_SIMULATION.md",
    "PHASE3_EXPERIMENTAL_LEDGER.csv",
    "PHASE3_SUSPEND_FAMILY_REVIEW.md",
    "PHASE3_SUSPEND_FAMILY_DECISION.md",
    "PHASE3_COST_MODE_COMPARISON.md",
    "PHASE3_COST_GATE_REVIEW.md",
    "PHASE3_FAMILY_DEDUP_AUDIT.md",
    "PHASE3_PAPER_SHADOW_SUMMARY.md",
    "PHASE3_PAPER_SHADOW_LEDGER.csv",
    "PHASE3_SHADOW_LIFECYCLE_SUMMARY.md",
    "PHASE3_SHADOW_LIFECYCLE_LEDGER.csv",
    "PHASE3_LIFECYCLE_GUARD_SUMMARY.md",
    "PHASE3_LIFECYCLE_GUARD_LEDGER.csv",
    "PHASE3_DEMO_REHEARSAL_CHECKLIST.md",
    "PHASE3_DEMO_REHEARSAL_LEDGER.csv",
    "PHASE3_COMPLETION_AUDIT.md",
    "PHASE3_EXPERIMENTAL_SAFETY_REPORT.md",
    "PHASE3_EXPERIMENTAL_MANIFEST.md",
)

REQUIRED_JSON_ARTIFACTS = (
    "PHASE3_EXPERIMENTAL_STATUS.json",
    "PHASE3_EXPERIMENTAL_SIMULATION.json",
    "PHASE3_COMPLETION_AUDIT.json",
    "PHASE3_EXPERIMENTAL_SAFETY_REPORT.json",
    "PHASE3_EXPERIMENTAL_MANIFEST.json",
    "PHASE3_DEMO_REHEARSAL_PLAN.json",
)


def verify_phase3_experimental_artifacts(
    phase3_root: Path,
    repo_root: Path | None = None,
    require_git_tracked: bool = False,
    require_clean_manifest: bool = False,
) -> list[str]:
    phase3_root = phase3_root.resolve()
    repo_root = (repo_root or phase3_root.parents[1]).resolve()
    reports = phase3_root / "outputs" / "reports"
    errors: list[str] = []
    for name in REQUIRED_ARTIFACTS:
        path = reports / name
        if not path.exists():
            errors.append(f"missing required Phase 3 artifact: {path}")
            continue
        if path.suffix.lower() == ".md":
            text = path.read_text(encoding="utf-8", errors="replace")
            if PHASE2_AUTHORITY_SENTENCE not in text:
                errors.append(f"missing required Phase 2 authority sentence: {path}")
        if require_git_tracked and not _is_git_tracked(repo_root, path):
            errors.append(f"required Phase 3 artifact is not git-tracked: {path}")
    for name in REQUIRED_JSON_ARTIFACTS:
        path = reports / name
        if not path.exists():
            errors.append(f"missing required Phase 3 JSON artifact: {path}")
            continue
        if _read_json(path) is None:
            errors.append(f"invalid JSON artifact: {path}")
        if require_git_tracked and not _is_git_tracked(repo_root, path):
            errors.append(f"required Phase 3 JSON artifact is not git-tracked: {path}")
    errors.extend(_verify_consistency(reports))
    if require_clean_manifest:
        errors.extend(_verify_clean_manifest(reports / "PHASE3_EXPERIMENTAL_MANIFEST.json"))
    return errors


def _verify_consistency(reports: Path) -> list[str]:
    errors: list[str] = []
    status = _read_json(reports / "PHASE3_EXPERIMENTAL_STATUS.json") or {}
    simulation = _read_json(reports / "PHASE3_EXPERIMENTAL_SIMULATION.json") or {}
    safety = _read_json(reports / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.json") or {}
    manifest = _read_json(reports / "PHASE3_EXPERIMENTAL_MANIFEST.json") or {}
    completion = _read_json(reports / "PHASE3_COMPLETION_AUDIT.json") or {}
    rehearsal = _read_json(reports / "PHASE3_DEMO_REHEARSAL_PLAN.json") or {}

    status_simulation = _mapping(status.get("simulation"))
    for key in (
        "accepted_events",
        "raw_observer_event_count",
        "family_unique_event_count",
        "observer_duplicate_count",
        "observer_conflict_count",
        "rejected_source_rows",
        "cost_mode",
    ):
        if status_simulation.get(key) != simulation.get(key):
            errors.append(
                f"status/simulation mismatch for {key}: "
                f"status={status_simulation.get(key)!r}; simulation={simulation.get(key)!r}"
            )

    if safety.get("status") != "PASS" or safety.get("findings_count") != 0:
        errors.append(
            f"Phase 3 safety must be PASS with 0 findings: status={safety.get('status')}; "
            f"findings={safety.get('findings_count')}"
        )
    if status.get("real_phase2_readiness") == "PASS":
        errors.append("Phase 3 status must not promote real_phase2_readiness to PASS.")
    for key in ("authorized_for_deployment", "mt5_runtime_touched", "broker_action_code_allowed"):
        if status.get(key) is not False:
            errors.append(f"Phase 3 status must keep {key}=false; found {status.get(key)!r}")
    if rehearsal.get("can_start_real_demo") is not False or rehearsal.get("demo_authorized") is not False:
        errors.append("Phase 3 demo rehearsal must keep can_start_real_demo=false and demo_authorized=false.")

    audit_rows = completion.get("repo_requirement_rows", [])
    if isinstance(audit_rows, list):
        for row in audit_rows:
            item = _mapping(row)
            evidence = Path(str(item.get("evidence", "")))
            if str(evidence) and not evidence.exists():
                errors.append(f"completion audit references missing evidence: {evidence}")
    else:
        errors.append("completion audit repo_requirement_rows must be a list.")

    files = manifest.get("files", {})
    if isinstance(files, dict):
        for name, raw in files.items():
            entry = _mapping(raw)
            if entry.get("exists") is not True:
                errors.append(f"manifest file entry is missing: {name}")
                continue
            path = Path(str(entry.get("path", "")))
            if not path.exists():
                errors.append(f"manifest path does not exist: {name}: {path}")
                continue
            if "outputs" in path.parts:
                continue
            expected_sha = str(entry.get("sha256", ""))
            if expected_sha and _sha256(path) != expected_sha:
                errors.append(f"manifest hash is stale for {name}: {path}")
            expected_bytes = entry.get("bytes")
            if expected_bytes is not None and path.stat().st_size != expected_bytes:
                errors.append(f"manifest byte count is stale for {name}: {path}")
    else:
        errors.append("manifest files field must be a dict.")
    return errors


def _verify_clean_manifest(path: Path) -> list[str]:
    if not path.exists():
        return [f"missing required Phase 3 manifest JSON: {path}"]
    manifest = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if manifest.get("status") != "PASS":
        errors.append(f"Phase 3 manifest status must be PASS for review release artifacts: {manifest.get('status')}")
    if manifest.get("working_tree_clean") is not True:
        errors.append("Phase 3 manifest must record working_tree_clean=true")
    if str(manifest.get("working_tree_short_status", "")).strip():
        errors.append("Phase 3 manifest must not record a dirty working_tree_short_status")
    return errors


def _read_json(path: Path) -> dict[str, object] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_git_tracked(repo_root: Path, path: Path) -> bool:
    relative = path.resolve().relative_to(repo_root)
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(relative).replace("\\", "/")],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def main(argv: list[str] | None = None) -> int:
    phase3_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Verify committed Phase 3 experimental review artifacts.")
    parser.add_argument("--phase3-root", type=Path, default=phase3_root)
    parser.add_argument("--repo-root", type=Path, default=phase3_root.parents[1])
    parser.add_argument(
        "--require-git-tracked",
        action="store_true",
        help="Fail if required artifacts exist locally but are not tracked by git.",
    )
    parser.add_argument(
        "--require-clean-manifest",
        action="store_true",
        help="Fail if PHASE3_EXPERIMENTAL_MANIFEST.json is not a clean PASS snapshot.",
    )
    args = parser.parse_args(argv)
    errors = verify_phase3_experimental_artifacts(
        phase3_root=args.phase3_root,
        repo_root=args.repo_root,
        require_git_tracked=args.require_git_tracked,
        require_clean_manifest=args.require_clean_manifest,
    )
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("Phase 3 experimental artifacts: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
