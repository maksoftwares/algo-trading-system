from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from composite import generate_manifest  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "transition_composite_discovery_v7.json").read_text(
            encoding="utf-8"
        )
    )
    source_root = (ROOT / config["source_campaign"]["directory"]).resolve()
    metrics = pd.read_csv(source_root / config["source_campaign"]["metrics"])
    trades_path = source_root / config["source_campaign"]["selected_trades"]
    trades = pd.read_parquet(trades_path)
    identity: list[dict[str, Any]] = []
    for component in config["component_pool"]:
        attempt = int(component["attempt_no"])
        row = metrics.loc[metrics["attempt_no"].eq(attempt)]
        if len(row) != 1:
            raise ValueError(f"Source component is not unique: {attempt}")
        source = row.iloc[0]
        checks = {
            "mechanic": str(source["mechanic"]) == str(component["mechanic"]),
            "geometry_id": str(source["geometry_id"])
            == str(component["geometry_id"]),
            "trade_rows": int(trades["attempt_no"].eq(attempt).sum())
            == int(source["whole_trades"]),
        }
        if not all(checks.values()):
            raise ValueError(f"Source component changed: {attempt}: {checks}")
        identity.append(
            {
                "attempt_no": attempt,
                "checks": checks,
                "whole_trades": int(source["whole_trades"]),
                "whole_stress_net_r": float(source["whole_stress_net_r"]),
                "whole_stress_pf": float(source["whole_stress_pf"]),
                "minimum_era_stress_pf": float(source["minimum_era_stress_pf"]),
            }
        )
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / config["outputs"]["manifest"]
    evidence_path = output / config["outputs"]["manifest_evidence"]
    if manifest_path.exists() or evidence_path.exists():
        raise FileExistsError("V7 manifest preflight already exists")
    manifest = generate_manifest(config)
    manifest.to_csv(manifest_path, index=False, lineterminator="\n")
    evidence = {
        "schema_version": "xauusd_transition_composite_v7_manifest_evidence",
        "manifest_rows": int(len(manifest)),
        "manifest_sha256": sha256_file(manifest_path),
        "component_trade_file_sha256": sha256_file(trades_path),
        "component_identity": identity,
        "components_selected_after_outcomes": True,
        "composite_outcomes_opened": False,
        "training_authorized": False,
        "execution_authorized": False,
    }
    evidence_path.write_text(
        json.dumps(evidence, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
