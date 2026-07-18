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
ORIGIN_ROOT = RESEARCH_ROOT / "chop-failed-reversion-envelope-v24"
sys.path.insert(0, str(ROOT / "src"))

from confirmation import generate_candidates  # noqa: E402


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


DATA = load_module(
    "chop_rawtick_v25_data",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "data.py",
)
REGIMES = load_module(
    "chop_rawtick_v25_regimes",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "research.py",
)
MICRO = load_module(
    "chop_rawtick_v25_micro",
    RESEARCH_ROOT / "m5-microstructure-mechanics-v1" / "src" / "campaign.py",
)
ORIGIN = load_module(
    "chop_rawtick_v25_origin", ORIGIN_ROOT / "src" / "campaign.py"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "chop_failed_reversion_rawtick_v25.json").read_text(
            encoding="utf-8"
        )
    )
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    candidates_path = output / config["outputs"]["candidates"]
    manifest_path = output / config["outputs"]["candidate_manifest"]
    if candidates_path.exists() or manifest_path.exists():
        raise FileExistsError("V25 candidate preflight already exists")

    origin_manifest_path = (
        ORIGIN_ROOT / "outputs" / "CHOP_FAILED_REVERSION_ENVELOPE_V24_MANIFEST.csv"
    )
    origin_metrics_path = (
        ORIGIN_ROOT / "outputs" / "CHOP_FAILED_REVERSION_ENVELOPE_V24_METRICS.csv"
    )
    origin_manifest = pd.read_csv(origin_manifest_path)
    origin_metrics = pd.read_csv(origin_metrics_path)
    definition = config["candidate"]
    selected = origin_manifest.loc[
        origin_manifest["attempt_no"].eq(int(definition["origin_attempt"]))
    ]
    selected_metrics = origin_metrics.loc[
        origin_metrics["attempt_no"].eq(int(definition["origin_attempt"]))
    ]
    if len(selected) != 1 or len(selected_metrics) != 1:
        raise ValueError("Frozen V24 origin attempt is not unique")
    source = selected.iloc[0]
    metrics = selected_metrics.iloc[0]
    expected_params = json.dumps(
        definition["parameters"], sort_keys=True, separators=(",", ":")
    )
    identity = {
        "variant_id": str(source["variant_id"])
        == str(definition["origin_variant_id"]),
        "regime_owner": str(source["regime_owner"])
        == str(definition["regime_owner"]),
        "mechanic": str(source["mechanic"]) == str(definition["mechanic"]),
        "parameters_json": str(source["parameters_json"]) == expected_params,
        "raw_signal_count": int(source["raw_signal_count"])
        == int(definition["expected_raw_signals"]),
        "economic_pass": str(metrics["economic_pass"]).strip().lower() == "true",
        "m5_trade_count": int(metrics["whole_trades"])
        == int(definition["expected_m5_trades"]),
    }
    if not all(identity.values()):
        raise ValueError(f"V24 origin identity changed: {identity}")

    bundle = DATA.load_bundle(config)
    frame = ORIGIN.prepare_frame(
        bundle.bars["M5"],
        bundle.bars["M15"],
        bundle.bars["H1"],
        bundle.bars["H4"],
        config,
        MICRO,
        REGIMES,
    )
    candidates, parity = generate_candidates(frame, ORIGIN, config)
    candidates.to_parquet(candidates_path, index=False)
    manifest = {
        "schema_version": "xauusd_chop_failed_reversion_rawtick_v25_candidates",
        "rows": int(len(candidates)),
        "origin_raw_signals": int(definition["expected_raw_signals"]),
        "origin_m5_trades": int(definition["expected_m5_trades"]),
        "candidate_sha256": sha256_file(candidates_path),
        "first_signal_time": candidates["signal_time"].min().isoformat(),
        "last_signal_time": candidates["signal_time"].max().isoformat(),
        "first_scheduled_entry_time": candidates[
            "scheduled_entry_time"
        ].min().isoformat(),
        "last_scheduled_entry_time": candidates[
            "scheduled_entry_time"
        ].max().isoformat(),
        "origin_identity_checks": identity,
        "independent_signal_parity": parity,
        "candidate_definition": definition,
        "origin_manifest_sha256": sha256_file(origin_manifest_path),
        "origin_metrics_sha256": sha256_file(origin_metrics_path),
        "data_evidence": bundle.evidence,
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
