from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


DATA = load_module(
    "chop_antisignal_v15_manifest_data",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "data.py",
)
REGIMES = load_module(
    "chop_antisignal_v15_manifest_regimes",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "research.py",
)
ADAPTIVE = load_module(
    "chop_antisignal_v15_manifest_adaptive",
    RESEARCH_ROOT / "adaptive-h4-specialists-v1" / "src" / "adaptive.py",
)
BASE = load_module(
    "chop_antisignal_v15_manifest_base",
    RESEARCH_ROOT / "regime-mechanism-campaign-v1" / "src" / "campaign.py",
)
CAMPAIGN = load_module(
    "chop_antisignal_v15_manifest_campaign", ROOT / "src" / "campaign.py"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "chop_antisignal_campaign_v15.json").read_text(
            encoding="utf-8"
        )
    )
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / config["outputs"]["manifest"]
    evidence_path = output / config["outputs"]["manifest_evidence"]
    if manifest_path.exists() or evidence_path.exists():
        raise FileExistsError("V15 manifest preflight already exists")
    bundle = DATA.load_bundle(config)
    frame = CAMPAIGN.prepare_frame(
        bundle.bars["M15"], bundle.bars["H4"], config, ADAPTIVE, REGIMES, BASE
    )
    frame["entry_time_key"] = frame["bar_start_utc"].shift(-1)
    manifest = CAMPAIGN.generate_manifest(frame, config)
    with manifest_path.open("w", encoding="utf-8", newline="\n") as handle:
        manifest.to_csv(handle, index=False, lineterminator="\n")
    evidence = {
        "schema_version": "xauusd_chop_antisignal_v15_manifest_evidence",
        "manifest_rows": int(len(manifest)),
        "manifest_sha256": sha256_file(manifest_path),
        "attempt_first": int(manifest["attempt_no"].iat[0]),
        "attempt_last": int(manifest["attempt_no"].iat[-1]),
        "paired_source_attempt_first": int(
            manifest["paired_source_attempt_no"].iat[0]
        ),
        "paired_source_attempt_last": int(
            manifest["paired_source_attempt_no"].iat[-1]
        ),
        "mechanic_counts": {
            str(key): int(value)
            for key, value in manifest.groupby("mechanic", sort=True).size().items()
        },
        "minimum_raw_signal_count": int(manifest["raw_signal_count"].min()),
        "minimum_era_raw_signal_count": int(
            manifest["minimum_era_raw_signal_count"].min()
        ),
        "data_evidence": bundle.evidence,
        "m15_feature_rows": int(len(frame)),
        "outcomes_opened": False,
        "manifest_membership_uses_signal_counts_only": True,
        "training_authorized": False,
        "execution_authorized": False,
    }
    with evidence_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(
            json.dumps(evidence, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        )
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
