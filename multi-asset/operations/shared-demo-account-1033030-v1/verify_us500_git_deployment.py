from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
MANIFEST = ROOT / "config" / "frozen_us500_v41_shared_demo_deployment.json"
DEPLOYED_EX5 = Path(
    r"C:\MT5PortableTier1BestEA\MQL5\Experts\SharedAccount1033030"
    r"\US500V41CausalSharedDemoEA.ex5"
)
PACKAGE_EX5 = "mql5/US500V41CausalSharedDemoEA.ex5"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def resolve_commit(git_ref: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "--verify", f"{git_ref}^{{commit}}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def committed_bytes(commit: str, package_relative: str) -> bytes:
    repo_relative = (ROOT / package_relative).relative_to(REPO).as_posix()
    result = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{commit}:{repo_relative}"],
        check=True,
        capture_output=True,
    )
    return result.stdout


def verify(git_ref: str, deployed_ex5: Path = DEPLOYED_EX5) -> dict[str, object]:
    commit = resolve_commit(git_ref)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    artifacts: dict[str, str] = manifest["artifacts"]
    artifact_results: dict[str, dict[str, object]] = {}
    errors: list[str] = []

    for relative, expected in artifacts.items():
        payload = committed_bytes(commit, relative)
        actual = sha256_bytes(payload)
        matches = actual == expected
        artifact_results[relative] = {
            "sha256": actual,
            "manifest_match": matches,
        }
        if not matches:
            errors.append(f"committed artifact hash mismatch: {relative}")

    if not deployed_ex5.is_file():
        deployed_hash = None
        errors.append(f"deployed EX5 is missing: {deployed_ex5}")
    else:
        deployed_hash = sha256_bytes(deployed_ex5.read_bytes())
        if deployed_hash != artifacts[PACKAGE_EX5]:
            errors.append("deployed EX5 does not match the committed rollback binary")

    return {
        "status": "VERIFIED" if not errors else "FAILED",
        "requested_ref": git_ref,
        "resolved_commit": commit,
        "account_login": manifest["account_login"],
        "server": manifest["server"],
        "symbol": manifest["symbol"],
        "period": manifest["period"],
        "deployed_ex5": str(deployed_ex5),
        "deployed_ex5_sha256": deployed_hash,
        "artifacts": artifact_results,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify deployed US500 V41 against artifacts stored at a Git commit"
    )
    parser.add_argument("--git-ref", required=True, help="commit, tag, or branch to verify")
    parser.add_argument("--deployed-ex5", type=Path, default=DEPLOYED_EX5)
    args = parser.parse_args()
    report = verify(args.git_ref, args.deployed_ex5)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
