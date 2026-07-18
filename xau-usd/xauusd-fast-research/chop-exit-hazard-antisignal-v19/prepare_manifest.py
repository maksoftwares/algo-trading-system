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


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


DATA = load_module(
    "chop_exit_anti_v19_manifest_data",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "data.py",
)
REGIMES = load_module(
    "chop_exit_anti_v19_manifest_regimes",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "research.py",
)
MICRO = load_module(
    "chop_exit_anti_v19_manifest_micro",
    RESEARCH_ROOT / "m5-microstructure-mechanics-v1" / "src" / "campaign.py",
)
CAMPAIGN = load_module(
    "chop_exit_anti_v19_manifest_campaign", ROOT / "src" / "campaign.py"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "chop_exit_hazard_antisignal_v19.json").read_text(
            encoding="utf-8"
        )
    )
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / config["outputs"]["manifest"]
    evidence_path = output / config["outputs"]["manifest_evidence"]
    if manifest_path.exists() or evidence_path.exists():
        raise FileExistsError("V19 manifest preflight already exists")
    bundle = DATA.load_bundle(config)
    frame = CAMPAIGN.prepare_frame(
        bundle.bars["M5"],
        bundle.bars["H1"],
        bundle.bars["H4"],
        config,
        MICRO,
        REGIMES,
    )
    frame["entry_time_key"] = frame["bar_start_utc"].shift(-1)
    manifest = CAMPAIGN.generate_manifest(frame, config)
    source_manifest_path = (
        RESEARCH_ROOT
        / "chop-exit-hazard-campaign-v18"
        / "outputs"
        / "CHOP_EXIT_HAZARD_V18_MANIFEST.csv"
    )
    source = pd.read_csv(source_manifest_path)
    paired = manifest.merge(
        source,
        left_on="paired_source_attempt_no",
        right_on="attempt_no",
        suffixes=("_v19", "_v18"),
        validate="one_to_one",
    )
    checks = (
        paired["parameters_json_v19"].eq(paired["parameters_json_v18"])
        & paired["raw_signal_count_v19"].eq(paired["raw_signal_count_v18"])
        & paired["minimum_era_raw_signal_count_v19"].eq(
            paired["minimum_era_raw_signal_count_v18"]
        )
        & paired.apply(
            lambda row: CAMPAIGN.V18_MECHANICS[str(row["mechanic_v19"])]
            == str(row["mechanic_v18"]),
            axis=1,
        )
    )
    if len(paired) != len(manifest) or not bool(checks.all()):
        raise ValueError("V19 manifest is not an exact parameter/signal pair of V18")
    with manifest_path.open("w", encoding="utf-8", newline="\n") as handle:
        manifest.to_csv(handle, index=False, lineterminator="\n")
    evidence = {
        "schema_version": "xauusd_chop_exit_hazard_antisignal_v19_manifest_evidence",
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
        "source_manifest_sha256": sha256_file(source_manifest_path),
        "paired_parameters_and_signal_counts_equal": True,
        "mechanic_counts": {
            str(key): int(value)
            for key, value in manifest.groupby("mechanic", sort=True).size().items()
        },
        "minimum_raw_signal_count": int(manifest["raw_signal_count"].min()),
        "minimum_era_raw_signal_count": int(
            manifest["minimum_era_raw_signal_count"].min()
        ),
        "data_evidence": bundle.evidence,
        "m5_feature_rows": int(len(frame)),
        "h4_chop_rows_attached": int(frame["regime"].eq("CHOP").sum()),
        "latest_completed_h1_atr_rows": int(frame["atr_h1"].notna().sum()),
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
