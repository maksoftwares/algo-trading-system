from __future__ import annotations

import argparse
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
    "PHASE3_COST_MODE_COMPARISON.md",
    "PHASE3_FAMILY_DEDUP_AUDIT.md",
    "PHASE3_EXPERIMENTAL_SAFETY_REPORT.md",
    "PHASE3_EXPERIMENTAL_MANIFEST.md",
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
    if require_clean_manifest:
        errors.extend(_verify_clean_manifest(reports / "PHASE3_EXPERIMENTAL_MANIFEST.json"))
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
