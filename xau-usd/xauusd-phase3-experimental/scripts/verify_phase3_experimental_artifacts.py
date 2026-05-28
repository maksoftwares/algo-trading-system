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
    "PHASE3_TO_DEMO_HANDOFF.md",
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
    "PHASE3_TO_DEMO_HANDOFF.json",
)

SELF_REFERENTIAL_MANIFEST_FILES = {
    "PHASE3_EXPERIMENTAL_MANIFEST.md",
    "PHASE3_EXPERIMENTAL_MANIFEST.json",
}

SUMMARY_FILES_THAT_REFERENCE_MANIFEST = {
    "PHASE3_EXPERIMENTAL_STATUS.md",
    "PHASE3_EXPERIMENTAL_STATUS.json",
    "PHASE3_COMPLETION_AUDIT.md",
    "PHASE3_COMPLETION_AUDIT.json",
}

HASH_EXCLUDED_OUTPUT_PARTS = {
    "review_bundles",
}


def verify_phase3_experimental_artifacts(
    phase3_root: Path,
    repo_root: Path | None = None,
    require_git_tracked: bool = False,
    require_clean_manifest: bool = False,
    allow_dirty_working_snapshot: bool = False,
    require_clean_release_snapshot: bool = False,
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
    errors.extend(_verify_current_state_freshness(reports, repo_root))
    if require_clean_manifest or require_clean_release_snapshot:
        errors.extend(_verify_clean_manifest(reports / "PHASE3_EXPERIMENTAL_MANIFEST.json"))
    elif allow_dirty_working_snapshot:
        errors.extend(_verify_working_manifest(reports / "PHASE3_EXPERIMENTAL_MANIFEST.json"))
    return errors


def _verify_consistency(reports: Path) -> list[str]:
    errors: list[str] = []
    status = _read_json(reports / "PHASE3_EXPERIMENTAL_STATUS.json") or {}
    simulation = _read_json(reports / "PHASE3_EXPERIMENTAL_SIMULATION.json") or {}
    safety = _read_json(reports / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.json") or {}
    manifest = _read_json(reports / "PHASE3_EXPERIMENTAL_MANIFEST.json") or {}
    completion = _read_json(reports / "PHASE3_COMPLETION_AUDIT.json") or {}
    rehearsal = _read_json(reports / "PHASE3_DEMO_REHEARSAL_PLAN.json") or {}
    handoff = _read_json(reports / "PHASE3_TO_DEMO_HANDOFF.json") or {}

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
    if handoff:
        if handoff.get("can_start_demo_now") is not False or handoff.get("demo_authorized") is not False:
            errors.append("Phase 3 to demo handoff must keep can_start_demo_now=false and demo_authorized=false.")
        if handoff.get("broker_action_code_allowed") is not False:
            errors.append("Phase 3 to demo handoff must keep broker_action_code_allowed=false.")
        if handoff.get("phase2_readiness") != status.get("real_phase2_readiness"):
            errors.append(
                "Phase 3 to demo handoff phase2_readiness must match status real_phase2_readiness: "
                f"handoff={handoff.get('phase2_readiness')!r}; status={status.get('real_phase2_readiness')!r}"
            )

    audit_rows = completion.get("repo_requirement_rows", [])
    if isinstance(audit_rows, list):
        for row in audit_rows:
            item = _mapping(row)
            if item.get("key") == "manifest":
                manifest_is_dirty = (
                    manifest.get("status") == "DIRTY_WORKTREE"
                    or manifest.get("working_tree_clean") is False
                    or bool(str(manifest.get("working_tree_short_status", "")).strip())
                )
                if manifest_is_dirty and item.get("status") == "PASS":
                    errors.append("completion audit must mark a dirty Phase 3 manifest row as WARN, not PASS.")
                if not manifest_is_dirty and manifest.get("status") == "PASS" and item.get("status") != "PASS":
                    errors.append("completion audit must mark a clean PASS Phase 3 manifest row as PASS.")
            evidence = Path(str(item.get("evidence", "")))
            if str(evidence) and not evidence.exists():
                errors.append(f"completion audit references missing evidence: {evidence}")
    else:
        errors.append("completion audit repo_requirement_rows must be a list.")

    files = manifest.get("files", {})
    if isinstance(files, dict):
        indexed_manifest_paths: dict[str, Path] = {}
        for name, raw in files.items():
            entry = _mapping(raw)
            if entry.get("exists") is not True:
                errors.append(f"manifest file entry is missing: {name}")
                continue
            path = Path(str(entry.get("path", "")))
            indexed_manifest_paths[path.name] = path
            if not path.exists():
                errors.append(f"manifest path does not exist: {name}: {path}")
                continue
            if _skip_manifest_hash_check(path):
                continue
            expected_sha = str(entry.get("sha256", ""))
            if expected_sha and _sha256(path) != expected_sha:
                errors.append(f"manifest hash is stale for {name}: {path}")
            expected_bytes = entry.get("bytes")
            if expected_bytes is not None and path.stat().st_size != expected_bytes:
                errors.append(f"manifest byte count is stale for {name}: {path}")
        required_manifest_names = (
            set(REQUIRED_ARTIFACTS)
            | set(REQUIRED_JSON_ARTIFACTS)
        ) - SELF_REFERENTIAL_MANIFEST_FILES
        for required_name in sorted(required_manifest_names):
            if required_name not in indexed_manifest_paths:
                errors.append(f"manifest does not hash required Phase 3 artifact: {required_name}")
    else:
        errors.append("manifest files field must be a dict.")
    return errors


def _skip_manifest_hash_check(path: Path) -> bool:
    if path.name in SELF_REFERENTIAL_MANIFEST_FILES:
        return True
    if path.name in SUMMARY_FILES_THAT_REFERENCE_MANIFEST:
        return True
    return any(part in HASH_EXCLUDED_OUTPUT_PARTS for part in path.parts)


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


def _verify_working_manifest(path: Path) -> list[str]:
    if not path.exists():
        return [f"missing required Phase 3 manifest JSON: {path}"]
    manifest = json.loads(path.read_text(encoding="utf-8"))
    status = manifest.get("status")
    if status not in {"PASS", "DIRTY_WORKTREE"}:
        return [f"Phase 3 working manifest status must be PASS or DIRTY_WORKTREE: {status}"]
    return []


def _dirty_manifest_warnings(path: Path) -> list[str]:
    if not path.exists():
        return []
    manifest = json.loads(path.read_text(encoding="utf-8"))
    dirty = (
        manifest.get("status") == "DIRTY_WORKTREE"
        or manifest.get("working_tree_clean") is False
        or bool(str(manifest.get("working_tree_short_status", "")).strip())
    )
    if not dirty:
        return []
    return [
        "Phase 3 manifest is a dirty working snapshot; this is allowed for WIP review, "
        "but not for release snapshots."
    ]


def _verify_current_state_freshness(reports: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    status = _read_json(reports / "PHASE3_EXPERIMENTAL_STATUS.json") or {}
    if not status:
        return errors

    phase1_reports = repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase1_summary_path = phase1_reports / "PHASE1_STATUS_SUMMARY.json"
    phase1_acceptance_path = phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md"
    phase2_readiness_path = phase1_reports / "PHASE2_READINESS_REPORT.md"

    phase1_acceptance = _read_markdown_status(phase1_acceptance_path)
    if phase1_acceptance and status.get("real_phase1_acceptance") != phase1_acceptance:
        errors.append(
            "Phase 3 status real_phase1_acceptance is stale: "
            f"status={status.get('real_phase1_acceptance')!r}; current={phase1_acceptance!r}"
        )

    phase2_readiness = _read_markdown_status(phase2_readiness_path)
    if phase2_readiness and status.get("real_phase2_readiness") != phase2_readiness:
        errors.append(
            "Phase 3 status real_phase2_readiness is stale: "
            f"status={status.get('real_phase2_readiness')!r}; current={phase2_readiness!r}"
        )

    phase1_summary = _read_json(phase1_summary_path) or {}
    latest = _mapping(_mapping(phase1_summary.get("runtime")).get("latest_row"))
    comparisons = {
        "latest_phase1_bar": latest.get("bar_time"),
        "latest_phase1_dry_run": latest.get("dry_run"),
        "latest_phase1_trade_permission": latest.get("trade_permission"),
    }
    for status_key, current_value in comparisons.items():
        if current_value in {None, ""}:
            continue
        if str(status.get(status_key, "")) != str(current_value):
            errors.append(
                f"Phase 3 status {status_key} is stale: "
                f"status={status.get(status_key)!r}; current={current_value!r}"
            )
    return errors


def _read_markdown_status(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Overall status:") or line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


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
        help="Deprecated alias for --require-clean-release-snapshot.",
    )
    parser.add_argument(
        "--allow-dirty-working-snapshot",
        action="store_true",
        help="Allow a DIRTY_WORKTREE manifest for local WIP review snapshots and print a warning.",
    )
    parser.add_argument(
        "--require-clean-release-snapshot",
        action="store_true",
        help="Fail if PHASE3_EXPERIMENTAL_MANIFEST.json is not a clean PASS release snapshot.",
    )
    args = parser.parse_args(argv)
    clean_required = args.require_clean_manifest or args.require_clean_release_snapshot
    if args.allow_dirty_working_snapshot and clean_required:
        parser.error("--allow-dirty-working-snapshot cannot be combined with clean release snapshot requirements")
    errors = verify_phase3_experimental_artifacts(
        phase3_root=args.phase3_root,
        repo_root=args.repo_root,
        require_git_tracked=args.require_git_tracked,
        require_clean_manifest=args.require_clean_manifest,
        allow_dirty_working_snapshot=args.allow_dirty_working_snapshot,
        require_clean_release_snapshot=args.require_clean_release_snapshot,
    )
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    if args.allow_dirty_working_snapshot:
        for warning in _dirty_manifest_warnings(args.phase3_root / "outputs" / "reports" / "PHASE3_EXPERIMENTAL_MANIFEST.json"):
            print(f"WARN: {warning}")
    print("Phase 3 experimental artifacts: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
