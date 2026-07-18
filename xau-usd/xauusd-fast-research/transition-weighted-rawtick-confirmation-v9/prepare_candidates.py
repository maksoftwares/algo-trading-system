from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from confirmation import combine_candidates, component_candidates  # noqa: E402


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


def main() -> int:
    config = json.loads(
        (
            ROOT
            / "config"
            / "transition_weighted_rawtick_confirmation_v9.json"
        ).read_text(encoding="utf-8")
    )
    macro_root = (ROOT / config["macro_source_campaign"]["directory"]).resolve()
    macro_config = json.loads(
        (macro_root / config["macro_source_campaign"]["config"]).read_text(
            encoding="utf-8"
        )
    )
    macro_campaign = load_module("campaign", macro_root / "src" / "campaign.py")
    foundation_module = load_module(
        "transition_weighted_rawtick_v9_foundation",
        macro_root / "src" / "foundation.py",
    )
    foundation = foundation_module.load_foundation(macro_config)
    macro_manifest = pd.read_csv(
        macro_root / config["macro_source_campaign"]["manifest"]
    )
    macro_source = macro_manifest.loc[macro_manifest["attempt_no"].eq(23925)]
    if len(macro_source) != 1:
        raise ValueError("Macro source attempt 23925 is not unique")
    frames = [
        component_candidates(
            foundation.decisions,
            foundation.execution_frame,
            next(macro_source.itertuples(index=False)),
            macro_campaign,
            macro_config,
            config,
        )
    ]

    residual_root = (
        ROOT / config["residual_source_campaign"]["directory"]
    ).resolve()
    residual_config = json.loads(
        (residual_root / config["residual_source_campaign"]["config"]).read_text(
            encoding="utf-8"
        )
    )
    residual_campaign = load_module(
        "transition_weighted_rawtick_v9_residual_campaign",
        residual_root / "src" / "campaign.py",
    )
    residual_frame = residual_campaign.enrich_residual_features(
        foundation.decisions, residual_config
    )
    residual_manifest = pd.read_csv(
        residual_root / config["residual_source_campaign"]["manifest"]
    )
    for attempt in (24877, 24995, 25048):
        source = residual_manifest.loc[residual_manifest["attempt_no"].eq(attempt)]
        if len(source) != 1:
            raise ValueError(f"Residual source attempt is not unique: {attempt}")
        frames.append(
            component_candidates(
                residual_frame,
                foundation.execution_frame,
                next(source.itertuples(index=False)),
                residual_campaign,
                residual_config,
                config,
            )
        )

    portfolio_root = (ROOT / config["portfolio_source"]["directory"]).resolve()
    portfolio_metrics = pd.read_csv(
        portfolio_root / config["portfolio_source"]["metrics"]
    )
    origin = portfolio_metrics.loc[
        portfolio_metrics["attempt_no"].eq(
            int(config["portfolio"]["origin_attempt_no"])
        )
    ]
    if len(origin) != 1:
        raise ValueError("Origin V8 portfolio is not unique")
    source_portfolio = origin.iloc[0]
    expected_weights = json.dumps(
        config["portfolio"]["weights"], sort_keys=True, separators=(",", ":")
    )
    portfolio_checks = {
        "weights": str(source_portfolio["weights_json"]) == expected_weights,
        "tie_priority": str(source_portfolio["tie_priority"])
        == str(config["portfolio"]["tie_priority"]),
        "whole_trades": int(source_portfolio["whole_trades"]) == 330,
    }
    if not all(portfolio_checks.values()):
        raise ValueError(f"Origin V8 portfolio changed: {portfolio_checks}")
    candidates = combine_candidates(frames)
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    candidate_path = output / config["outputs"]["candidates"]
    manifest_path = output / config["outputs"]["candidate_manifest"]
    if candidate_path.exists() or manifest_path.exists():
        raise FileExistsError("V9 candidate preflight already exists")
    candidates.to_parquet(candidate_path, index=False)
    inventory = [
        {
            "origin_attempt": int(attempt),
            "candidate_rows": int(len(group)),
            "first_signal_time": group["signal_time"].min().isoformat(),
            "last_signal_time": group["signal_time"].max().isoformat(),
        }
        for attempt, group in candidates.groupby("origin_attempt", sort=True)
    ]
    manifest = {
        "schema_version": "xauusd_transition_weighted_rawtick_v9_candidates",
        "candidate_rows": int(len(candidates)),
        "candidate_sha256": sha256_file(candidate_path),
        "component_inventory": inventory,
        "portfolio_identity_checks": portfolio_checks,
        "portfolio": config["portfolio"],
        "foundation_evidence": foundation.evidence,
        "raw_outcomes_opened": False,
        "training_authorized": False,
        "execution_authorized": False,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

