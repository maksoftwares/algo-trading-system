from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from router import generate_manifest  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "transition_online_component_router_v10.json").read_text(
            encoding="utf-8"
        )
    )
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / config["outputs"]["manifest"]
    evidence_path = output / config["outputs"]["manifest_evidence"]
    if manifest_path.exists() or evidence_path.exists():
        raise FileExistsError("V10 manifest preflight already exists")
    manifest = generate_manifest(config)
    with manifest_path.open("w", encoding="utf-8", newline="\n") as handle:
        manifest.to_csv(handle, index=False, lineterminator="\n")
    evidence = {
        "schema_version": "xauusd_transition_online_router_v10_manifest_evidence",
        "manifest_rows": int(len(manifest)),
        "manifest_sha256": sha256_file(manifest_path),
        "attempt_first": int(manifest["attempt_no"].iat[0]),
        "attempt_last": int(manifest["attempt_no"].iat[-1]),
        "mechanic_counts": {
            str(key): int(value)
            for key, value in manifest.groupby("mechanic", sort=True).size().items()
        },
        "policy_outcomes_opened": False,
        "manifest_membership_uses_no_policy_outcomes": True,
        "training_authorized": False,
        "execution_authorized": False
    }
    with evidence_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(
            json.dumps(evidence, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        )
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
