from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "comex_auction_profile_specialists_v1.json"
FILES = {
    "PREREGISTRATION.md": ROOT / "PREREGISTRATION.md",
    "config/comex_auction_profile_specialists_v1.json": CONFIG,
    "src/auction.py": ROOT / "src" / "auction.py",
    "tests/test_auction.py": ROOT / "tests" / "test_auction.py",
    "run_research.py": ROOT / "run_research.py",
    "requirements.txt": ROOT / "requirements.txt",
    "../ml-candidate-rankers-v1/src/engine.py": (
        ROOT.parent / "ml-candidate-rankers-v1" / "src" / "engine.py"
    ),
    "../independent-specialists-v1/src/data.py": (
        ROOT.parent / "independent-specialists-v1" / "src" / "data.py"
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    files = {name: sha256(path) for name, path in FILES.items()}
    combined = hashlib.sha256(
        "\n".join(f"{name}:{digest}" for name, digest in sorted(files.items())).encode("ascii")
    ).hexdigest()
    payload = {
        "schema_version": "comex_auction_profile_contract_lock_v1",
        "locked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "combined_sha256": combined,
        "files": files,
        "windows": config["windows"],
        "families": config["families"],
        "exam_sealed_until_prior_pass": True,
        "same_version_post_outcome_tuning_authorized": False,
        "python_predictions_authorized": False,
        "broker_action_authorized": False,
    }
    output = ROOT / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
