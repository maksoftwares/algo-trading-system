from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    config_path = ROOT / "config" / "two_trade_per_day_locked_router_v62.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    verified: dict[str, str] = {}
    for source_id, source in config["sources"].items():
        path = REPO_ROOT / source["path"]
        actual = sha256_file(path)
        if actual != source["sha256"]:
            raise ValueError(f"Source hash mismatch for {source_id}: {actual}")
        verified[source_id] = actual
    payload = {
        "schema_version": config["schema_version"],
        "config_path": config_path.relative_to(REPO_ROOT).as_posix(),
        "config_sha256": sha256_file(config_path),
        "verified_sources": verified,
        "locked_policy": config["locked_policy"],
        "locked_development_evidence": config["locked_development_evidence"],
        "research_controls": config["research_controls"],
    }
    output_dir = ROOT / config["outputs"]["directory"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / config["outputs"]["contract_lock"]
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    print(sha256_file(output_path))


if __name__ == "__main__":
    main()
