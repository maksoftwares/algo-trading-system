from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
PACKAGE_FILES = (
    ".gitattributes",
    ".gitignore",
    "PREREGISTRATION.md",
    "README.md",
    "requirements.txt",
    "config/histdata_xauusd_independent_feed_audit_v47.json",
    "lock_contract.py",
    "run_audit.py",
    "src/__init__.py",
    "src/audit.py",
    "tests/test_audit.py",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_contract() -> dict[str, object]:
    config_path = ROOT / "config" / "histdata_xauusd_independent_feed_audit_v47.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    package = {
        relative: {
            "bytes": (ROOT / relative).stat().st_size,
            "sha256": sha256_file(ROOT / relative),
        }
        for relative in PACKAGE_FILES
    }
    external = {}
    for name, path_key, hash_key in (
        ("histdata_archive", "archive_path", "archive_sha256"),
        ("histdata_csv", "csv_path", "csv_sha256"),
        ("histdata_status", "status_path", "status_sha256"),
    ):
        path = Path(config["histdata"][path_key])
        actual = sha256_file(path)
        expected = config["histdata"][hash_key]
        if actual != expected:
            raise ValueError(f"Source hash mismatch for {path}")
        external[name] = {
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": actual,
        }
    dukas_path = Path(config["dukascopy"]["m5_path"])
    dukas_hash = sha256_file(dukas_path)
    if dukas_hash != config["dukascopy"]["m5_sha256"]:
        raise ValueError(f"Source hash mismatch for {dukas_path}")
    external["dukascopy_m5"] = {
        "path": str(dukas_path),
        "bytes": dukas_path.stat().st_size,
        "sha256": dukas_hash,
    }
    payload: dict[str, object] = {
        "schema_version": config["schema_version"],
        "package_files": package,
        "external_sources": external,
        "window": config["window"],
        "gates": config["gates"],
        "research_controls": config["research_controls"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["contract_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    output = ROOT / "outputs" / "HISTDATA_XAUUSD_V47_CONTRACT_LOCK.json"
    contract = build_contract()
    if args.write:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    if args.verify:
        if not output.is_file():
            raise FileNotFoundError(output)
        locked = json.loads(output.read_text(encoding="utf-8"))
        if locked != contract:
            raise ValueError("V47 contract lock does not match current sources")
    json.dump(contract, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
