from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from economic_test import (  # noqa: E402
    canonical_hash,
    dukascopy_path,
    expected_dukascopy_hours,
    load_config,
    path_record,
    resolve,
    sha256_file,
    verify_file_manifest,
    verify_locked_inputs,
)


PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/capital_dukas_lagged_economic_test_v23.json",
    "src/__init__.py",
    "src/economic_test.py",
    "prepare_capital_manifest.py",
    "download_sealed_dukascopy.py",
    "lock_contract.py",
    "run_economic_test.py",
    "tests/test_economic_test.py",
)


def package_record(path: Path) -> dict[str, Any]:
    return {
        "path": path.resolve().relative_to(REPO.resolve()).as_posix(),
        "bytes": int(path.stat().st_size),
        "sha256": sha256_file(path),
    }


def validate_config(config: dict[str, Any]) -> None:
    confirmation = config["confirmation"]
    if (
        confirmation["start_inclusive_utc"] != "2026-07-01T00:00:00Z"
        or confirmation["end_exclusive_utc"] != "2026-07-18T00:00:00Z"
        or confirmation["free_url_template"]
        != "https://datafeed.dukascopy.com/datafeed/XAUUSD/{year}/{zero_based_month}/{day}/{hour}h_ticks.bi5"
    ):
        raise ValueError("The V23 sealed confirmation contract changed")
    if config["candidate"] != {"z_threshold": 4.0, "cooldown_minutes": 20}:
        raise ValueError("The V23 candidate contract changed")
    if config["simulation"] != {
        "hold_seconds": 300,
        "maximum_entry_delay_ms": 10000,
        "maximum_exit_delay_ms": 10000,
        "base_slippage_per_side_price": 0.05,
        "stress_slippage_per_side_price": 0.15,
        "reference_lot": 0.01,
        "dollars_per_price_unit": 1.0,
        "overlap_policy": "SKIP",
    }:
        raise ValueError("The V23 execution simulation changed")
    controls = config["research_controls"]
    required_true = (
        "single_preregistered_economic_test",
        "july_dukascopy_must_be_absent_before_lock",
    )
    if not all(bool(controls[key]) for key in required_true):
        raise ValueError("V23 research controls changed")
    forbidden = tuple(key for key in controls if key not in required_true)
    if any(bool(controls[key]) for key in forbidden):
        raise ValueError("V23 contains forbidden authorization")


def main() -> int:
    config = load_config(ROOT)
    validate_config(config)
    verify_locked_inputs(config, ROOT)
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    lock_path = output / config["outputs"]["contract_lock"]
    if lock_path.exists():
        raise FileExistsError("V23 contract is already locked")
    capital_manifest_path = resolve(
        ROOT, str(config["confirmation"]["capital_manifest"])
    )
    capital_manifest = json.loads(capital_manifest_path.read_text(encoding="utf-8"))
    verify_file_manifest(capital_manifest, "capital_files")
    if int(capital_manifest["capital_file_count"]) != 17:
        raise ValueError("V23 must lock exactly 17 Capital daily files")
    hours = expected_dukascopy_hours(config)
    existing = [str(dukascopy_path(config, hour)) for hour in hours if dukascopy_path(config, hour).exists()]
    if existing:
        raise FileExistsError(
            f"V23 July Dukascopy was not sealed before lock: {existing[:10]}"
        )
    payload: dict[str, Any] = {
        "schema_version": config["schema_version"],
        "package_files": [package_record(ROOT / name) for name in PACKAGE_FILES],
        "config_file": path_record(
            ROOT / "config" / "capital_dukas_lagged_economic_test_v23.json"
        ),
        "capital_source_manifest": path_record(capital_manifest_path),
        "capital_source_manifest_self_hash": capital_manifest["manifest_sha256"],
        "capital_file_count": capital_manifest["capital_file_count"],
        "locked_inputs": config["development"] | config["locked_modules"],
        "confirmation_window": {
            "start_inclusive_utc": config["confirmation"]["start_inclusive_utc"],
            "end_exclusive_utc": config["confirmation"]["end_exclusive_utc"],
        },
        "dukascopy_expected_file_count": len(hours),
        "july_dukascopy_absent_at_lock": True,
        "candidate": config["candidate"],
        "feature": config["feature"],
        "simulation": config["simulation"],
        "gates": config["gates"],
        "single_preregistered_economic_test": True,
        "same_version_tuning_authorized": False,
        "strategy_admission_authorized": False,
        "model_training_authorized": False,
        "execution_authorized": False,
    }
    payload["contract_sha256"] = canonical_hash(payload, "contract_sha256")
    lock_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
