from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = (
    Path("xau-usd")
    / "xauusd-phase1"
    / "outputs"
    / "reports"
    / "A3_NET_COST_FALSIFICATION_MANIFEST_2026_06_19.json"
)


@dataclass(frozen=True)
class ManifestVerification:
    status: str
    manifest_path: str
    manifest_sha256: str
    git_ref: str | None
    checked_files: int
    mismatches: tuple[str, ...]


def verify_manifest(
    repo_root: Path,
    manifest_path: Path | None = None,
    *,
    git_ref: str | None = None,
) -> ManifestVerification:
    repo_root = repo_root.resolve()
    manifest_rel = manifest_path or DEFAULT_MANIFEST
    manifest_rel = Path(manifest_rel)
    if manifest_rel.is_absolute():
        manifest_abs = manifest_rel
        manifest_rel_posix = manifest_abs.relative_to(repo_root).as_posix()
    else:
        manifest_abs = repo_root / manifest_rel
        manifest_rel_posix = manifest_rel.as_posix()

    manifest_bytes = _read_bytes(repo_root, manifest_rel_posix, git_ref=git_ref)
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    mismatches: list[str] = []
    for artifact in manifest.get("source_artifacts", []):
        path = str(artifact.get("path", "")).strip()
        expected = str(artifact.get("sha256", "")).strip().upper()
        if not path or not expected:
            mismatches.append(f"{path or '<missing path>'}: missing path or sha256")
            continue
        try:
            actual = hashlib.sha256(_read_bytes(repo_root, path, git_ref=git_ref)).hexdigest().upper()
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            mismatches.append(f"{path}: missing ({exc})")
            continue
        if actual != expected:
            mismatches.append(f"{path}: expected {expected}, actual {actual}")

    return ManifestVerification(
        status="PASS" if not mismatches else "FAIL",
        manifest_path=manifest_rel_posix,
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest().upper(),
        git_ref=git_ref,
        checked_files=len(manifest.get("source_artifacts", [])),
        mismatches=tuple(mismatches),
    )


def _read_bytes(repo_root: Path, rel_path: str, *, git_ref: str | None) -> bytes:
    if git_ref:
        return subprocess.check_output(
            ["git", "show", f"{git_ref}:{rel_path}"],
            cwd=repo_root,
        )
    return (repo_root / rel_path).read_bytes()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the A3 net-cost falsification manifest hashes.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--git-ref", default="HEAD", help="Git ref to verify committed bytes; defaults to HEAD.")
    args = parser.parse_args(argv)

    result = verify_manifest(args.repo_root, args.manifest, git_ref=args.git_ref)
    print(json.dumps(_as_json(result), indent=2))
    return 0 if result.status == "PASS" else 1


def _as_json(result: ManifestVerification) -> dict[str, Any]:
    return {
        "status": result.status,
        "manifest_path": result.manifest_path,
        "manifest_sha256": result.manifest_sha256,
        "git_ref": result.git_ref,
        "checked_files": result.checked_files,
        "mismatches": list(result.mismatches),
    }


if __name__ == "__main__":
    raise SystemExit(main())
