from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record(path: Path, base: Path) -> dict[str, Any]:
    resolved = path.resolve()
    resolved.relative_to(base.resolve())
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    return {
        "path": str(resolved.relative_to(base.resolve())).replace("\\", "/"),
        "bytes": int(resolved.stat().st_size),
        "sha256": sha256_file(resolved),
    }


def self_hash(payload: dict[str, Any]) -> str:
    work = dict(payload)
    work.pop("contract_sha256", None)
    encoded = json.dumps(
        work, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def source_evidence(config: dict[str, Any]) -> dict[str, Any]:
    source = REPO / "xau-usd/xauusd-fast-research/chop-v1/outputs"
    candidate = config["candidate"]
    subtype = pd.read_csv(source / "CHOP_SUBTYPE_RESULTS.csv")
    selected = subtype.loc[
        subtype["strategy_id"].eq(candidate["strategy_id"])
        & subtype["timeframe"].eq(candidate["timeframe"])
        & subtype["subtype_dimension"].eq("volatility_subtype")
        & subtype["subtype"].eq(candidate["volatility_subtype"])
    ]
    if len(selected) != 1:
        raise ValueError("Expected exactly one Capital.com source subtype row")
    trades = pd.read_csv(source / "CHOP_TRADE_LEDGER.csv")
    selected_trades = trades.loc[
        trades["strategy_id"].eq(candidate["strategy_id"])
        & trades["timeframe"].eq(candidate["timeframe"])
        & trades["volatility_subtype"].eq(candidate["volatility_subtype"])
    ]
    evidence = {
        "strategy_id": str(selected["strategy_id"].iat[0]),
        "timeframe": str(selected["timeframe"].iat[0]),
        "subtype_dimension": str(selected["subtype_dimension"].iat[0]),
        "volatility_subtype": str(selected["subtype"].iat[0]),
        "trades": int(len(selected_trades)),
        "stress_net_r": float(selected_trades["stress_net_r"].sum()),
        "source_subtype_row": selected.iloc[0].to_dict(),
    }
    checks = {
        "strategy": evidence["strategy_id"] == candidate["strategy_id"],
        "timeframe": evidence["timeframe"] == candidate["timeframe"],
        "subtype": evidence["volatility_subtype"] == candidate["volatility_subtype"],
        "trades": evidence["trades"] == int(candidate["source_trade_count"]),
        "stress_net_r": abs(
            evidence["stress_net_r"] - float(candidate["source_stress_net_r"])
        )
        < 1e-9,
    }
    if not all(checks.values()):
        raise ValueError(f"Fixed candidate differs from source evidence: {checks}")
    evidence["identity_checks"] = checks
    return evidence


def main() -> int:
    config_path = ROOT / "config" / "portability_v2.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    package_names = [
        "PREREGISTRATION.md",
        "requirements.txt",
        "config/portability_v2.json",
        "src/portability.py",
        "tests/test_portability.py",
        "lock_contract.py",
        "run_portability.py",
    ]
    dependency_names = [
        "xau-usd/xauusd-fast-research/chop-m30-dukascopy-portability-v1/src/portability.py",
        "xau-usd/xauusd-fast-research/chop-v1/config/chop_fast_discovery_v1.json",
        "xau-usd/xauusd-fast-research/chop-v1/src/backtest.py",
        "xau-usd/xauusd-fast-research/chop-v1/src/data_adapter.py",
        "xau-usd/xauusd-fast-research/chop-v1/src/regime.py",
        "xau-usd/xauusd-fast-research/chop-v1/src/strategies.py",
        "xau-usd/xauusd-fast-research/chop-v1/outputs/CHOP_FAST_DISCOVERY_RESULT.json",
        "xau-usd/xauusd-fast-research/chop-v1/outputs/CHOP_SUBTYPE_RESULTS.csv",
        "xau-usd/xauusd-fast-research/chop-v1/outputs/CHOP_TRADE_LEDGER.csv",
        "xau-usd/xauusd-fast-research/independent-specialists-v1/src/data.py",
    ]
    source = config["source"]
    storage = Path(
        os.environ.get(source["storage_environment_variable"], source["default_storage_root"])
    ).resolve()
    external_names = [
        Path(str(source["feature_cache"])),
        Path(str(source["feature_manifest"])),
    ]
    if sha256_file(storage / str(source["feature_cache"])) != str(source["feature_sha256"]):
        raise ValueError("Dukascopy feature cache hash differs from the config")
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    lock_path = output / config["outputs"]["contract_lock"]
    if lock_path.exists():
        raise FileExistsError("V2 contract lock already exists")
    payload = {
        "schema_version": "xauusd_chop_m5_highvol_portability_v2_contract",
        "contract_sha256": "",
        "package_files": [record(ROOT / name, REPO) for name in package_names],
        "dependency_files": [record(REPO / name, REPO) for name in dependency_names],
        "external_files": [record(storage / name, storage) for name in external_names],
        "source_selection_evidence": source_evidence(config),
        "candidate_count": 1,
        "parameter_search_count": 0,
        "outcomes_opened": False,
    }
    payload["contract_sha256"] = self_hash(payload)
    lock_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"lock": str(lock_path), "contract_sha256": payload["contract_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
