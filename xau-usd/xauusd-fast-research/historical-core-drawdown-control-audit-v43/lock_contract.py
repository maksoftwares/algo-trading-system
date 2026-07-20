from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from audit import canonical_sha256, sha256_file  # noqa: E402


PACKAGE_FILES = (
    ".gitattributes",
    ".gitignore",
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/historical_core_drawdown_control_audit_v43.json",
    "lock_contract.py",
    "run_audit.py",
    "src/__init__.py",
    "src/audit.py",
    "tests/test_audit.py",
)


def record(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return {
        "path": str(path.resolve()),
        "bytes": int(path.stat().st_size),
        "sha256": sha256_file(path),
    }


def main() -> int:
    config_path = ROOT / "config/historical_core_drawdown_control_audit_v43.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    payload = {
        "schema_version": config["schema_version"],
        "package_files": {
            relative: record(ROOT / relative) for relative in PACKAGE_FILES
        },
        "repository_sources": {
            name: record(REPO_ROOT / source["path"])
            for name, source in config["sources"].items()
        },
        "external_sources": {
            name: record(Path(source["path"]))
            for name, source in config["external_sources"].items()
        },
        "frozen_control": config["frozen_control"],
        "account_reference": config["account_reference"],
        "parameter_search_count": 0,
        "execution_authorized": False,
    }
    payload["contract_sha256"] = canonical_sha256(payload)
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    path = output / config["outputs"]["contract_lock"]
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
