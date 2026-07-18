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
MACRO_ROOT = RESEARCH_ROOT / "macro-regime-routing-v1"
sys.path.insert(0, str(ROOT / "src"))

from transition import generate_candidates  # noqa: E402


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CAMPAIGN = load_module("campaign", MACRO_ROOT / "src" / "campaign.py")
FOUNDATION = load_module(
    "macro_transition_rawtick_foundation", MACRO_ROOT / "src" / "foundation.py"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "macro_transition_rawtick_confirmation_v3.json").read_text(
            encoding="utf-8"
        )
    )
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    candidates_path = output / config["outputs"]["candidates"]
    manifest_path = output / config["outputs"]["candidate_manifest"]
    if candidates_path.exists() or manifest_path.exists():
        raise FileExistsError("Candidate preflight already exists")
    origin_manifest = pd.read_csv(
        MACRO_ROOT / "outputs" / "MACRO_REGIME_ROUTING_V1_MANIFEST.csv"
    )
    definition = config["candidate"]
    selected = origin_manifest.loc[
        origin_manifest["attempt_no"].eq(int(definition["origin_attempt"]))
    ]
    if len(selected) != 1:
        raise ValueError("Frozen origin attempt is not unique")
    source = selected.iloc[0]
    expected_params = json.dumps(
        definition["parameters"], sort_keys=True, separators=(",", ":")
    )
    identity = {
        "variant_id": str(source["variant_id"]) == str(definition["origin_variant_id"]),
        "regime_owner": str(source["regime_owner"]) == str(definition["regime_owner"]),
        "mechanic": str(source["mechanic"]) == str(definition["mechanic"]),
        "geometry_id": str(source["geometry_id"]) == str(definition["geometry_id"]),
        "parameters_json": str(source["parameters_json"]) == expected_params,
        "raw_signal_count": int(source["raw_signal_count"])
        == int(definition["expected_raw_signals"]),
    }
    if not all(identity.values()):
        raise ValueError(f"Origin identity changed: {identity}")
    foundation = FOUNDATION.load_foundation(config)
    candidates = generate_candidates(
        foundation.decisions, foundation.execution_frame, CAMPAIGN, config
    )
    candidates.to_parquet(candidates_path, index=False)
    manifest = {
        "schema_version": "xauusd_macro_transition_rawtick_v3_candidates",
        "rows": int(len(candidates)),
        "origin_raw_signals": int(definition["expected_raw_signals"]),
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
        "candidate_definition": definition,
        "data_evidence": foundation.evidence,
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

