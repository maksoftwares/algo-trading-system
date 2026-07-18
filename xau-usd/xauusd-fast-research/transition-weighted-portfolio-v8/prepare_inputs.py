from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from portfolio import generate_manifest  # noqa: E402


def load_module(name: str, path: Path) -> Any:
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
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _metric_checks(score: dict[str, Any], source: pd.Series) -> dict[str, bool]:
    return {
        "whole_trades": int(score["whole_trades"]) == int(source["whole_trades"]),
        "whole_stress_net_r": bool(
            np.isclose(
                float(score["whole_stress_net_r"]),
                float(source["whole_stress_net_r"]),
                rtol=0.0,
                atol=1e-12,
            )
        ),
        "whole_stress_pf": bool(
            np.isclose(
                float(score["whole_stress_pf"]),
                float(source["whole_stress_pf"]),
                rtol=0.0,
                atol=1e-12,
            )
        ),
        "minimum_era_stress_pf": bool(
            np.isclose(
                float(score["minimum_era_stress_pf"]),
                float(source["minimum_era_stress_pf"]),
                rtol=0.0,
                atol=1e-12,
            )
        ),
    }


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "transition_weighted_portfolio_v8.json").read_text(
            encoding="utf-8"
        )
    )
    macro_root = (ROOT / config["macro_source_campaign"]["directory"]).resolve()
    macro_config = json.loads(
        (macro_root / config["macro_source_campaign"]["config"]).read_text(
            encoding="utf-8"
        )
    )
    campaign = load_module("campaign", macro_root / "src" / "campaign.py")
    foundation_module = load_module(
        "transition_weighted_v8_foundation", macro_root / "src" / "foundation.py"
    )
    foundation = foundation_module.load_foundation(macro_config)
    macro_manifest = pd.read_csv(
        macro_root / config["macro_source_campaign"]["manifest"]
    )
    macro_metrics = pd.read_csv(
        macro_root / config["macro_source_campaign"]["metrics"]
    )
    source_manifest = macro_manifest.loc[macro_manifest["attempt_no"].eq(23925)]
    source_metrics = macro_metrics.loc[macro_metrics["attempt_no"].eq(23925)]
    if len(source_manifest) != 1 or len(source_metrics) != 1:
        raise ValueError("Macro component 23925 is not unique")
    item = next(source_manifest.itertuples(index=False))
    macro_trades = campaign.simulate_variant(
        foundation.decisions,
        foundation.arrays,
        item,
        macro_config,
        {},
        foundation_module.ROUTER.simulate_fixed_trade,
    )
    macro_trades["attempt_no"] = 23925
    macro_trades["variant_id"] = str(item.variant_id)
    score = foundation_module.SCORE.score_variant(
        macro_trades, foundation.execution_frame, macro_config
    )
    checks = _metric_checks(score, source_metrics.iloc[0])
    if not all(checks.values()):
        raise ValueError(f"Macro component reproduction failed: {checks}")

    residual_root = (
        ROOT / config["residual_source_campaign"]["directory"]
    ).resolve()
    residual_metrics = pd.read_csv(
        residual_root / config["residual_source_campaign"]["metrics"]
    )
    residual_trades = pd.read_parquet(
        residual_root / config["residual_source_campaign"]["selected_trades"]
    )
    residual_attempts = {24877, 24995, 25048}
    residual_trades = residual_trades.loc[
        residual_trades["attempt_no"].isin(residual_attempts)
    ].copy()
    identity: list[dict[str, Any]] = [
        {
            "attempt_no": 23925,
            "source": "MACRO_REGIME_ROUTING_V1",
            "metric_reproduction_checks": checks,
            "trade_rows": int(len(macro_trades)),
        }
    ]
    for component in config["components"]:
        attempt = int(component["attempt_no"])
        if attempt == 23925:
            continue
        row = residual_metrics.loc[residual_metrics["attempt_no"].eq(attempt)]
        if len(row) != 1:
            raise ValueError(f"Residual component is not unique: {attempt}")
        source = row.iloc[0]
        component_checks = {
            "mechanic": str(source["mechanic"]) == str(component["mechanic"]),
            "geometry_id": str(source["geometry_id"])
            == str(component["geometry_id"]),
            "trade_rows": int(residual_trades["attempt_no"].eq(attempt).sum())
            == int(source["whole_trades"]),
        }
        if not all(component_checks.values()):
            raise ValueError(f"Residual component changed: {attempt}")
        identity.append(
            {
                "attempt_no": attempt,
                "source": "CROSSASSET_RESIDUAL_V6",
                "checks": component_checks,
                "trade_rows": int(source["whole_trades"]),
            }
        )
    components = pd.concat((macro_trades, residual_trades), ignore_index=True)
    components = components.sort_values(
        ["entry_time", "attempt_no"], kind="mergesort"
    ).reset_index(drop=True)
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    component_path = output / config["outputs"]["component_trades"]
    manifest_path = output / config["outputs"]["manifest"]
    evidence_path = output / config["outputs"]["input_evidence"]
    if component_path.exists() or manifest_path.exists() or evidence_path.exists():
        raise FileExistsError("V8 input preflight already exists")
    components.to_parquet(component_path, index=False)
    manifest = generate_manifest(config)
    manifest.to_csv(manifest_path, index=False, lineterminator="\n")
    evidence = {
        "schema_version": "xauusd_transition_weighted_v8_input_evidence",
        "component_rows": int(len(components)),
        "component_trade_sha256": sha256_file(component_path),
        "component_identity": identity,
        "manifest_rows": int(len(manifest)),
        "manifest_sha256": sha256_file(manifest_path),
        "components_selected_after_outcomes": True,
        "portfolio_outcomes_opened": False,
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

