from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PHASE2_AUTHORITY_SENTENCE = (
    "This report has no authority over Phase 2 readiness. "
    "PHASE2_READINESS_REPORT.md remains the sole real readiness authority."
)


def generate_phase3_experimental_manifest(phase3_root: Path, repo_root: Path | None = None) -> Path:
    phase3_root = phase3_root.resolve()
    repo_root = (repo_root or phase3_root.parents[1]).resolve()
    reports = phase3_root / "outputs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    simulation = _read_json(reports / "PHASE3_EXPERIMENTAL_SIMULATION.json")
    safety = _read_json(reports / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.json")
    input_csv = Path(str(simulation.get("input_csv", ""))) if simulation.get("input_csv") else None
    paths = {
        "phase3_input_would_signals": input_csv,
        "phase3_simulation_json": reports / "PHASE3_EXPERIMENTAL_SIMULATION.json",
        "phase3_safety_json": reports / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.json",
        "phase3_suspend_family_json": reports / "PHASE3_SUSPEND_FAMILY_REVIEW.json",
        "phase3_suspend_family_md": reports / "PHASE3_SUSPEND_FAMILY_REVIEW.md",
        "phase3_suspend_family_csv": reports / "PHASE3_SUSPEND_FAMILY_ROWS.csv",
        "phase3_suspend_family_decision_json": reports / "PHASE3_SUSPEND_FAMILY_DECISION.json",
        "phase3_suspend_family_decision_md": reports / "PHASE3_SUSPEND_FAMILY_DECISION.md",
        "phase3_suspend_family_decision_csv": reports / "PHASE3_SUSPEND_FAMILY_DECISION.csv",
        "phase3_cost_mode_comparison_json": reports / "PHASE3_COST_MODE_COMPARISON.json",
        "phase3_cost_mode_comparison_md": reports / "PHASE3_COST_MODE_COMPARISON.md",
        "phase3_cost_mode_comparison_csv": reports / "PHASE3_COST_MODE_COMPARISON.csv",
        "phase3_cost_gate_review_json": reports / "PHASE3_COST_GATE_REVIEW.json",
        "phase3_cost_gate_review_md": reports / "PHASE3_COST_GATE_REVIEW.md",
        "phase3_cost_gate_review_csv": reports / "PHASE3_COST_GATE_REVIEW.csv",
        "phase3_family_dedup_audit_json": reports / "PHASE3_FAMILY_DEDUP_AUDIT.json",
        "phase3_family_dedup_audit_md": reports / "PHASE3_FAMILY_DEDUP_AUDIT.md",
        "phase3_family_dedup_audit_csv": reports / "PHASE3_FAMILY_DEDUP_AUDIT.csv",
        "phase2_readiness_report": repo_root
        / "xau-usd"
        / "xauusd-phase1"
        / "outputs"
        / "reports"
        / "PHASE2_READINESS_REPORT.md",
        "phase1_status_summary": repo_root
        / "xau-usd"
        / "xauusd-phase1"
        / "outputs"
        / "reports"
        / "PHASE1_STATUS_SUMMARY.json",
        "phase3_scope_doc": phase3_root / "docs" / "PHASE3_EXPERIMENTAL_SCOPE.md",
        "phase3_design_doc": phase3_root / "docs" / "PHASE3_EXECUTION_READINESS_DESIGN.md",
        "phase3_promotion_rollback_doc": phase3_root / "docs" / "PHASE3_PROMOTION_ROLLBACK_CRITERIA.md",
        "phase3_observer_conflict_playbook": phase3_root / "docs" / "PHASE3_OBSERVER_CONFLICT_PLAYBOOK.md",
        "phase3_real_implementation_prompt": phase3_root / "docs" / "PHASE3_REAL_IMPLEMENTATION_PROMPT.md",
        "phase3_review_bundle_latest_zip": phase3_root
        / "outputs"
        / "review_bundles"
        / "PHASE3_EXPERIMENTAL_REVIEW_BUNDLE_LATEST.zip",
        "phase3_review_bundle_latest_manifest": phase3_root
        / "outputs"
        / "review_bundles"
        / "PHASE3_EXPERIMENTAL_REVIEW_BUNDLE_LATEST_manifest.json",
        "script_simulation": phase3_root / "scripts" / "simulate_phase3_from_would_signals.py",
        "script_status": phase3_root / "scripts" / "generate_phase3_experimental_status.py",
        "script_safety": phase3_root / "scripts" / "audit_phase3_experimental_safety.py",
        "script_manifest": phase3_root / "scripts" / "generate_phase3_experimental_manifest.py",
        "script_cost_mode_comparison": phase3_root / "scripts" / "generate_phase3_cost_mode_comparison.py",
        "script_cost_gate_review": phase3_root / "scripts" / "generate_phase3_cost_gate_review.py",
        "script_suspend_family_decision": phase3_root / "scripts" / "generate_phase3_suspend_family_decision.py",
        "script_family_dedup_audit": phase3_root / "scripts" / "generate_phase3_family_dedup_audit.py",
        "script_review_bundle": phase3_root / "scripts" / "generate_phase3_review_bundle.py",
        "script_artifact_verifier": phase3_root / "scripts" / "verify_phase3_experimental_artifacts.py",
        "script_status_dashboard_freshness": repo_root
        / "xau-usd"
        / "xauusd-phase1"
        / "scripts"
        / "verify_status_dashboard_freshness.py",
    }
    files = {name: _file_entry(path) for name, path in paths.items()}
    working_tree_short_status = _git_output(repo_root, "status", "--short")
    manifest = {
        "status": _manifest_status(safety, simulation, files, working_tree_short_status),
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": PHASE2_AUTHORITY_SENTENCE,
        "boundary": "repo_only_no_mt5_deployment_no_phase2_status_change",
        "commit_hash": _git_output(repo_root, "rev-parse", "HEAD"),
        "commit_short": _git_output(repo_root, "rev-parse", "--short", "HEAD"),
        "working_tree_clean": working_tree_short_status == "",
        "working_tree_short_status": working_tree_short_status,
        "simulation_status": simulation.get("status", "UNKNOWN"),
        "safety_status": safety.get("status", "UNKNOWN"),
        "manifest_scope": "phase3_review_release_snapshot",
        "files": files,
    }
    json_path = reports / "PHASE3_EXPERIMENTAL_MANIFEST.json"
    md_path = reports / "PHASE3_EXPERIMENTAL_MANIFEST.md"
    json_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(manifest), encoding="utf-8")
    return json_path


def _file_entry(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"path": "", "exists": False, "sha256": None, "bytes": 0}
    path = path.resolve()
    if not path.exists():
        return {"path": str(path), "exists": False, "sha256": None, "bytes": 0}
    return {
        "path": str(path),
        "exists": True,
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
    }


def _manifest_pass(
    safety: dict[str, Any],
    simulation: dict[str, Any],
    files: dict[str, dict[str, Any]],
) -> bool:
    return (
        safety.get("status") == "PASS"
        and bool(simulation)
        and all(entry.get("exists") is True for entry in files.values())
    )


def _manifest_status(
    safety: dict[str, Any],
    simulation: dict[str, Any],
    files: dict[str, dict[str, Any]],
    working_tree_short_status: str,
) -> str:
    if not _manifest_pass(safety, simulation, files):
        return "PENDING"
    if working_tree_short_status.strip():
        return "DIRTY_WORKTREE"
    return "PASS"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_output(repo_root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _render_markdown(manifest: dict[str, Any]) -> str:
    files = manifest.get("files", {})
    if not isinstance(files, dict):
        files = {}
    return "\n".join(
        [
            "# Phase 3 Experimental Manifest",
            "",
            PHASE2_AUTHORITY_SENTENCE,
            "",
            f"Overall status: {manifest['status']}",
            "",
            "## Snapshot",
            "",
            _table(
                [
                    ("Created at UTC", str(manifest.get("created_at_utc", ""))),
                    ("Commit", str(manifest.get("commit_short", ""))),
                    ("Simulation status", str(manifest.get("simulation_status", ""))),
                    ("Safety status", str(manifest.get("safety_status", ""))),
                    ("Working tree clean", str(manifest.get("working_tree_clean", ""))),
                    ("Boundary", str(manifest.get("boundary", ""))),
                ]
            ),
            "",
            "## Working Tree",
            "",
            _working_tree_block(str(manifest.get("working_tree_short_status", ""))),
            "",
            "## Source Hashes",
            "",
            _files_table(files),
            "",
        ]
    )


def _files_table(files: dict[str, Any]) -> str:
    rows = []
    for name, raw in sorted(files.items()):
        entry = raw if isinstance(raw, dict) else {}
        rows.append(
            "| "
            + " | ".join(
                [
                    _escape(name),
                    _escape(entry.get("exists", "")),
                    _escape(entry.get("bytes", "")),
                    _escape(entry.get("sha256", "")),
                    _escape(entry.get("path", "")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "| Name | Exists | Bytes | SHA256 | Path |",
            "| --- | --- | ---: | --- | --- |",
            *rows,
        ]
    )


def _working_tree_block(status: str) -> str:
    if not status:
        return "Clean."
    return "```text\n" + status + "\n```"


def _table(rows: list[tuple[str, str]]) -> str:
    body = [f"| {_escape(key)} | {_escape(value)} |" for key, value in rows]
    return "\n".join(["| Field | Value |", "| --- | --- |", *body])


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    phase3_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Generate Phase 3 experimental source-hash manifest.")
    parser.add_argument("--phase3-root", type=Path, default=phase3_root)
    parser.add_argument("--repo-root", type=Path, default=phase3_root.parents[1])
    args = parser.parse_args(argv)
    path = generate_phase3_experimental_manifest(args.phase3_root, args.repo_root)
    print(f"Phase 3 experimental manifest: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
