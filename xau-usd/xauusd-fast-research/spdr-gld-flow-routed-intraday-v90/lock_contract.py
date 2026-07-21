from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs"
CONFIG_PATH = ROOT / "config" / "spdr_gld_flow_routed_intraday_v90.json"
PREFIX = "SPDR_GLD_FLOW_ROUTED_INTRADAY_V90"
LOCK_PATH = OUTPUT / f"{PREFIX}_CONTRACT_LOCK.json"
MANIFEST_PATH = OUTPUT / f"{PREFIX}_POLICY_MANIFEST.csv"
CENSUS_PATH = OUTPUT / f"{PREFIX}_SIGNAL_CENSUS.json"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return _json_ready(value.item())
    return value


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(_json_ready(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def contract_paths(config: Mapping[str, Any]) -> dict[str, Path]:
    source = config["source"]
    storage = Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    ).resolve()
    return {
        "config/spdr_gld_flow_routed_intraday_v90.json": CONFIG_PATH,
        "PREREGISTRATION.md": ROOT / "PREREGISTRATION.md",
        "SHARED_PORTFOLIO_PRECOMMITMENT.md": ROOT
        / "SHARED_PORTFOLIO_PRECOMMITMENT.md",
        "requirements.txt": ROOT / "requirements.txt",
        "src/campaign.py": ROOT / "src" / "campaign.py",
        "lock_contract.py": ROOT / "lock_contract.py",
        "run_research.py": ROOT / "run_research.py",
        "upstream/dukascopy_data_source.py": (ROOT / source["data_source"]).resolve(),
        "upstream/base_simulator.py": (
            ROOT / config["base_simulator"]["path"]
        ).resolve(),
        "external/dukascopy_feature_cache": storage / source["feature_cache"],
        "external/dukascopy_feature_manifest": storage / source["feature_manifest"],
        "external/spdr_gld_historical_archive": Path(
            config["gld_source"]["path"]
        ).resolve(),
    }


def verify_sources(config: Mapping[str, Any], paths: Mapping[str, Path]) -> dict[str, Any]:
    for name, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"Missing contract input {name}: {path}")
    source = config["source"]
    if sha256_file(paths["external/dukascopy_feature_cache"]) != source["feature_sha256"]:
        raise ValueError("Dukascopy feature cache hash mismatch")
    if sha256_file(paths["upstream/dukascopy_data_source.py"]) != source[
        "data_source_sha256"
    ]:
        raise ValueError("Dukascopy loader hash mismatch")
    if sha256_file(paths["upstream/base_simulator.py"]) != config["base_simulator"][
        "sha256"
    ]:
        raise ValueError("Base simulator hash mismatch")
    gld_config = config["gld_source"]
    gld_path = paths["external/spdr_gld_historical_archive"]
    if sha256_file(gld_path) != gld_config["sha256"]:
        raise ValueError("SPDR GLD archive hash mismatch")
    raw = pd.read_excel(gld_path, sheet_name=gld_config["sheet_name"])
    if len(raw) + 1 != int(gld_config["expected_workbook_rows"]):
        raise ValueError("Unexpected SPDR GLD workbook row count")
    dates = pd.to_datetime(raw["Date"], format="%d-%b-%Y", errors="raise")
    ounces = pd.to_numeric(
        raw["Total Ounces of Gold in the Trust"], errors="coerce"
    )
    valid_dates = dates.loc[ounces.notna()]
    if len(valid_dates) != int(gld_config["expected_valid_rows"]):
        raise ValueError("Unexpected SPDR GLD valid row count")
    if valid_dates.min().date().isoformat() != gld_config["first_date"]:
        raise ValueError("Unexpected first SPDR GLD date")
    if valid_dates.max().date().isoformat() != gld_config["downloaded_through"]:
        raise ValueError("Unexpected last SPDR GLD date")
    if valid_dates.duplicated().any():
        raise ValueError("Duplicate SPDR GLD observation")
    return {
        "gld_workbook_rows": int(len(raw) + 1),
        "gld_valid_rows": int(len(valid_dates)),
        "gld_first_date": valid_dates.min().date().isoformat(),
        "gld_last_date": valid_dates.max().date().isoformat(),
        "paid_data_request_made": False,
        "databento_used": False,
        "same_day_gld_holdings_use": False,
        "raw_archive_committed": False,
    }


def main() -> int:
    if LOCK_PATH.exists() or MANIFEST_PATH.exists() or CENSUS_PATH.exists():
        raise RuntimeError("V90 is already locked")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    paths = contract_paths(config)
    source_evidence = verify_sources(config, paths)
    campaign = _load_module("spdr_gld_v90_lock_campaign", ROOT / "src" / "campaign.py")
    data = _load_module(
        "spdr_gld_v90_lock_data", (ROOT / config["source"]["data_source"]).resolve()
    )
    bundle = data.load_bundle(config)
    gld = campaign.load_gld(
        paths["external/spdr_gld_historical_archive"],
        str(config["gld_source"]["sheet_name"]),
        int(config["gld_source"]["availability_lag_days"]),
    )
    frame = campaign.prepare_features(bundle.bars["H1"], gld, config)
    start, end = map(pd.Timestamp, config["windows"]["discovery"])
    controls = config["research_controls"]
    manifest = campaign.generate_manifest(
        frame,
        start,
        end,
        int(controls["attempt_first"]),
        int(controls["policies_per_mechanic"]),
        int(controls["minimum_raw_discovery_signals"]),
    )
    if len(manifest) != int(controls["registered_policy_count"]):
        raise ValueError("V90 policy count mismatch")
    if int(manifest["attempt_no"].min()) != int(controls["attempt_first"]):
        raise ValueError("V90 first attempt mismatch")
    if int(manifest["attempt_no"].max()) != int(controls["attempt_last"]):
        raise ValueError("V90 last attempt mismatch")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    temporary = MANIFEST_PATH.with_suffix(".csv.part")
    manifest.to_csv(temporary, index=False)
    os.replace(temporary, MANIFEST_PATH)
    grouped = manifest.groupby("mechanic", sort=True)["raw_discovery_signal_count"]
    census = {
        "schema_version": "xauusd_spdr_gld_flow_v90_signal_census",
        "created_utc": datetime.now(UTC).isoformat(),
        "discovery_start": start.isoformat(),
        "discovery_end": end.isoformat(),
        "policy_count": int(len(manifest)),
        "attempt_first": int(manifest["attempt_no"].min()),
        "attempt_last": int(manifest["attempt_no"].max()),
        "mechanics": {
            mechanic: {
                "policies": int(len(values)),
                "minimum_raw_signals": int(values.min()),
                "median_raw_signals": float(values.median()),
                "maximum_raw_signals": int(values.max()),
            }
            for mechanic, values in grouped
        },
        "coverage_selection_used_trade_outcomes": False,
        "post_entry_quotes_opened": False,
        "strategy_scoring_performed": False,
        "paid_data_request_made": False,
        "databento_used": False,
    }
    write_json(CENSUS_PATH, census)
    body = {
        "schema_version": "xauusd_spdr_gld_flow_v90_contract_lock",
        "created_utc": datetime.now(UTC).isoformat(),
        "files": {name: sha256_file(path) for name, path in sorted(paths.items())},
        "policy_manifest_sha256": sha256_file(MANIFEST_PATH),
        "signal_census_sha256": sha256_file(CENSUS_PATH),
        "attempt_first": int(manifest["attempt_no"].min()),
        "attempt_last": int(manifest["attempt_no"].max()),
        "registered_policy_count": int(len(manifest)),
        "source_evidence": source_evidence,
        "outcomes_opened": False,
        "training_authorized": False,
        "execution_authorized": False,
        "paid_data_authorized": False,
        "databento_use_authorized": False,
        "v59_v60_modification_authorized": False,
    }
    body["contract_sha256"] = canonical_hash(body)
    write_json(LOCK_PATH, body)
    print(json.dumps(_json_ready(body), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
