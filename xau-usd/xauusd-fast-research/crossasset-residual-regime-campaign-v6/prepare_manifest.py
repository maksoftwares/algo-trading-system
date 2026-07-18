from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
MACRO_ROOT = RESEARCH_ROOT / "macro-regime-routing-v1"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


load_module("campaign", MACRO_ROOT / "src" / "campaign.py")
FOUNDATION = load_module(
    "crossasset_residual_manifest_foundation",
    MACRO_ROOT / "src" / "foundation.py",
)
CAMPAIGN = load_module(
    "crossasset_residual_manifest_campaign", ROOT / "src" / "campaign.py"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "crossasset_residual_regime_campaign_v6.json").read_text(
            encoding="utf-8"
        )
    )
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / config["outputs"]["manifest"]
    evidence_path = output / "CROSSASSET_RESIDUAL_V6_MANIFEST_EVIDENCE.json"
    if manifest_path.exists() or evidence_path.exists():
        raise FileExistsError("V6 manifest preflight already exists")
    foundation = FOUNDATION.load_foundation(config)
    frame = CAMPAIGN.enrich_residual_features(foundation.decisions, config)
    manifest = CAMPAIGN.generate_manifest(frame, config)
    manifest.to_csv(manifest_path, index=False, lineterminator="\n")
    evidence = {
        "schema_version": "xauusd_crossasset_residual_v6_manifest_evidence",
        "manifest_rows": int(len(manifest)),
        "manifest_sha256": sha256_file(manifest_path),
        "attempt_first": int(manifest["attempt_no"].iat[0]),
        "attempt_last": int(manifest["attempt_no"].iat[-1]),
        "owner_counts": {
            str(key): int(value)
            for key, value in manifest.groupby("regime_owner").size().items()
        },
        "mechanic_counts": {
            str(key): int(value)
            for key, value in manifest.groupby("mechanic").size().items()
        },
        "minimum_raw_signal_count": int(manifest["raw_signal_count"].min()),
        "minimum_era_raw_signal_count": int(
            manifest["minimum_era_raw_signal_count"].min()
        ),
        "foundation_evidence": foundation.evidence,
        "outcomes_opened": False,
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

