from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_JSON = Path("outputs") / "reports" / "EXPERIMENTAL_DEMO_EXECUTOR_CLEAN_CLONE_RECONCILIATION.json"
DEFAULT_MD = Path("outputs") / "reports" / "EXPERIMENTAL_DEMO_EXECUTOR_CLEAN_CLONE_RECONCILIATION.md"
SOURCE_REL = Path("xau-usd") / "xauusd-phase1" / "mt5" / "Experts" / "Phase2ExperimentalDemoExecutor.mq5"
GOVERNANCE_REL = Path("xau-usd") / "xauusd-phase1" / "docs" / "EXPERIMENTAL_DEMO_EXECUTOR_GOVERNANCE.md"
PARITY_REL = Path("xau-usd") / "xauusd-phase1" / "outputs" / "reports" / "EXPERIMENTAL_DEMO_EXECUTOR_SOURCE_GOVERNANCE_PARITY.md"
DEPLOY_REL = Path("xau-usd") / "xauusd-phase1" / "scripts" / "deploy_phase1_mt5.py"
REQUIRED_SOURCE_TOKENS = (
    "InpAllowedAccountLoginsCsv",
    "InpExperimentalAuthorizationToken",
    "InpCostSuspensionAcknowledgementToken",
    "InpCandidateStatus",
    "InpFamilyLifecycleStatus",
    "InpAuthorizedCandidatesCsv",
    "InpMaxAccountOrdersPerDay",
    "InpKillSwitchFileName",
    "InpMaxEstimatedCostR",
    "InpMaxMeasuredSpreadPoints",
    "Order" + "Send",
)


@dataclass(frozen=True)
class CleanCloneReconciliationOutput:
    status: str
    json_path: Path
    markdown_path: Path
    clone_commit_hash: str


def generate_clean_clone_reconciliation(
    phase1_root: Path,
    repo_url: str,
    branch: str = "main",
    output_json: Path | None = None,
) -> CleanCloneReconciliationOutput:
    phase1_root = phase1_root.resolve()
    repo_root = phase1_root.parents[1]
    output_json = (output_json or phase1_root / DEFAULT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_JSON.name else phase1_root / DEFAULT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="ats-clean-clone-") as temp_dir:
        clone_root = Path(temp_dir) / "clean-review-clone"
        _run(["git", "clone", "--depth", "1", "--branch", branch, repo_url, str(clone_root)], cwd=Path(temp_dir))
        commit_hash = _run(["git", "rev-parse", "HEAD"], cwd=clone_root).strip()
        source_path = clone_root / SOURCE_REL
        governance_path = clone_root / GOVERNANCE_REL
        parity_path = clone_root / PARITY_REL
        deploy_path = clone_root / DEPLOY_REL
        source_text = _read(source_path)
        governance_text = _read(governance_path)
        parity_text = _read(parity_path)
        deploy_text = _read(deploy_path)
        token_rows = [
            {
                "token": token,
                "status": "PASS" if token in source_text else "FAIL",
                "line": _line_number(source_text, token),
            }
            for token in REQUIRED_SOURCE_TOKENS
        ]
        packaging_rows = [
            {
                "check": "canonical_deploy_excludes_experimental_executor",
                "status": "PASS"
                if "EXPERT_NAME = \"Phase1DryRunShell.mq5\"" in deploy_text
                and "Phase2ExperimentalDemoExecutor" not in deploy_text
                else "FAIL",
                "evidence": DEPLOY_REL.as_posix(),
            },
            {
                "check": "parity_report_committed",
                "status": "PASS" if parity_path.exists() else "FAIL",
                "evidence": PARITY_REL.as_posix(),
            },
            {
                "check": "governance_doc_committed",
                "status": "PASS" if governance_path.exists() and "InpAllowedAccountLoginsCsv" in governance_text else "FAIL",
                "evidence": GOVERNANCE_REL.as_posix(),
            },
        ]
        status = "PASS" if all(row["status"] == "PASS" for row in token_rows + packaging_rows) else "FAIL"
        payload = {
            "status": status,
            "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "repo_url": repo_url,
            "branch": branch,
            "clone_commit_hash": commit_hash,
            "source_path": SOURCE_REL.as_posix(),
            "source_file_sha256": _sha256(source_path),
            "governance_doc_sha256": _sha256(governance_path),
            "parity_report_sha256": _sha256(parity_path),
            "source_input_declaration_block": _input_declaration_block(source_text),
            "required_token_rows": token_rows,
            "packaging_rows": packaging_rows,
            "authority": (
                "This clean-clone reconciliation proves the public GitHub source at the recorded commit. "
                "It does not authorize canonical Phase 2, demo execution, broker execution, or live capital."
            ),
        }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return CleanCloneReconciliationOutput(status, output_json, output_md, payload["clone_commit_hash"])


def _run(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"{' '.join(command)} failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _sha256(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _line_number(text: str, token: str) -> str:
    for index, line in enumerate(text.splitlines(), start=1):
        if token in line:
            return str(index)
    return ""


def _input_declaration_block(source: str) -> str:
    lines = source.splitlines()
    input_lines = [f"{index}: {line}" for index, line in enumerate(lines, start=1) if line.strip().startswith("input ")]
    if input_lines:
        return "\n".join(input_lines[:80])
    return "\n".join(f"{index}: {line}" for index, line in enumerate(lines[:80], start=1))


def _render_markdown(payload: dict[str, object]) -> str:
    token_rows = payload["required_token_rows"]
    packaging_rows = payload["packaging_rows"]
    assert isinstance(token_rows, list)
    assert isinstance(packaging_rows, list)
    lines = [
        "# Experimental Demo Executor Clean-Clone Reconciliation",
        "",
        f"Overall status: {payload['status']}",
        "",
        str(payload["authority"]),
        "",
        f"Repo URL: `{payload['repo_url']}`",
        f"Branch: `{payload['branch']}`",
        f"Clean-clone commit hash: `{payload['clone_commit_hash']}`",
        f"Source path: `{payload['source_path']}`",
        f"Source SHA256: `{payload['source_file_sha256']}`",
        f"Governance doc SHA256: `{payload['governance_doc_sha256']}`",
        f"Parity report SHA256: `{payload['parity_report_sha256']}`",
        "",
        "## Required Source Tokens",
        "",
        "| Token | Status | Line |",
        "| --- | --- | --- |",
    ]
    for row in token_rows:
        assert isinstance(row, dict)
        lines.append(f"| {row['token']} | {row['status']} | {row['line']} |")
    lines.extend(["", "## Packaging Proof", "", "| Check | Status | Evidence |", "| --- | --- | --- |"])
    for row in packaging_rows:
        assert isinstance(row, dict)
        lines.append(f"| {row['check']} | {row['status']} | {row['evidence']} |")
    lines.extend(
        [
            "",
            "## Input Declaration Block",
            "",
            "```mql5",
            str(payload["source_input_declaration_block"]).rstrip(),
            "```",
            "",
            "## Boundary",
            "",
            "Experimental demo executor lane remains QUARANTINE / NO DEPLOYMENT / REVIEW ONLY.",
            "",
        ]
    )
    return "\n".join(lines)


def _default_repo_url(phase1_root: Path) -> str:
    try:
        return _run(["git", "config", "--get", "remote.origin.url"], cwd=phase1_root.parents[1])
    except RuntimeError:
        return "https://github.com/maksoftwares/algo-trading-system.git"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate clean-clone reconciliation for experimental demo executor source.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--repo-url", default=None)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    repo_url = args.repo_url or _default_repo_url(args.root.resolve())
    output = generate_clean_clone_reconciliation(args.root, repo_url, args.branch, args.output_json)
    print(f"Experimental demo clean-clone reconciliation: {output.status}")
    print(f"Commit: {output.clone_commit_hash}")
    print(output.markdown_path)
    return 0 if output.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
