from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from composite import generate_candidates  # noqa: E402


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


R2 = load_module(
    "regime_composite_candidates_r2",
    RESEARCH_ROOT / "r2-downtrend-portability-v2" / "src" / "downtrend.py",
)
DATA = load_module(
    "regime_composite_candidates_data",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "data.py",
)
REGIMES = load_module(
    "regime_composite_candidates_regimes",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "research.py",
)
ADAPTIVE = load_module(
    "regime_composite_candidates_adaptive",
    RESEARCH_ROOT / "adaptive-h4-specialists-v1" / "src" / "adaptive.py",
)
V1 = load_module(
    "regime_composite_candidates_v1",
    RESEARCH_ROOT / "regime-mechanism-campaign-v1" / "src" / "campaign.py",
)


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "regime_composite_rawtick_v1.json").read_text(
            encoding="utf-8"
        )
    )
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    candidates_path = output / config["outputs"]["candidates"]
    manifest_path = output / config["outputs"]["candidate_manifest"]
    if candidates_path.exists() or manifest_path.exists():
        raise FileExistsError("Candidate preflight already exists")
    m5, evidence = R2.load_continuous_m5(config)
    h1 = DATA.aggregate_complete_bars(m5, 60, "H1")
    h4 = DATA.aggregate_complete_bars(m5, 240, "H4")
    frame = V1.prepare_features(h1, h4, config, ADAPTIVE, REGIMES)
    v1_manifest = pd.read_csv(
        RESEARCH_ROOT
        / "regime-mechanism-campaign-v1"
        / "outputs"
        / "REGIME_MECHANISM_CAMPAIGN_V1_MANIFEST.csv"
    )
    candidates = generate_candidates(frame, v1_manifest, config, V1)
    candidates.to_parquet(candidates_path, index=False)
    by_component = [
        {
            "origin_attempt": int(attempt),
            "rows": int(len(group)),
            "first_signal_time": group["signal_time"].min().isoformat(),
            "last_signal_time": group["signal_time"].max().isoformat(),
        }
        for attempt, group in candidates.groupby("origin_attempt", sort=True)
    ]
    manifest = {
        "schema_version": "xauusd_regime_composite_rawtick_v1_candidates",
        "rows": int(len(candidates)),
        "candidate_sha256": R2.sha256_file(candidates_path),
        "first_signal_time": candidates["signal_time"].min().isoformat(),
        "last_signal_time": candidates["signal_time"].max().isoformat(),
        "first_scheduled_entry_time": candidates[
            "scheduled_entry_time"
        ].min().isoformat(),
        "last_scheduled_entry_time": candidates[
            "scheduled_entry_time"
        ].max().isoformat(),
        "components": by_component,
        "composites": config["composites"],
        "data_evidence": {
            **evidence,
            "h1_rows": int(len(h1)),
            "h4_rows": int(len(h4)),
            "feature_rows": int(len(frame)),
        },
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

