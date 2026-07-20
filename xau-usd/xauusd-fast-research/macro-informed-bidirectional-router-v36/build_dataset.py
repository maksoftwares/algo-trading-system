from __future__ import annotations

import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from contract import (  # noqa: E402
    load_config,
    resolve_relative,
    sha256_file,
    verify_contract_lock,
)
from macro_features import (  # noqa: E402
    align_macro_features,
    build_macro_features,
    load_macro_m15,
    model_macro_feature_columns,
)


def ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [ready(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return ready(value.item())
    return value


def main() -> int:
    config = load_config()
    verify_contract_lock()
    base_path = resolve_relative(str(config["sources"]["base_actions"]))
    base_evidence_path = resolve_relative(str(config["sources"]["base_evidence"]))
    if sha256_file(base_path) != config["sources"]["base_actions_sha256"]:
        raise ValueError("Base action dataset hash mismatch")
    if sha256_file(base_evidence_path) != config["sources"]["base_evidence_sha256"]:
        raise ValueError("Base evidence hash mismatch")
    base_evidence = json.loads(base_evidence_path.read_text(encoding="utf-8"))
    actions = pd.read_parquet(base_path)
    macro_m15, macro_source_evidence = load_macro_m15(config)
    macro = build_macro_features(macro_m15, config)
    merged, alignment_evidence = align_macro_features(actions, macro, config)
    base_features = list(base_evidence["router_features"])
    added_features = model_macro_feature_columns(config)
    features = [*base_features, *added_features]
    if len(features) != len(set(features)):
        raise ValueError("Duplicate model feature")
    if any(column.startswith("future_") for column in features):
        raise ValueError("Future feature reached V36 feature set")
    if np.isinf(merged[features]).any(axis=None):
        raise ValueError("Infinite V36 model feature")
    required = list(config["macro_features"]["required_finite_features"])
    if required and not np.isfinite(merged[required]).all(axis=None):
        raise ValueError("Required V36 model feature is non-finite")
    evidence = {
        "schema_version": config["schema_version"],
        **alignment_evidence,
        "base_dataset_sha256": sha256_file(base_path),
        "base_evidence_sha256": sha256_file(base_evidence_path),
        "base_feature_count": len(base_features),
        "added_feature_count": len(added_features),
        "model_feature_count": len(features),
        "base_features": base_features,
        "added_features": added_features,
        "model_features": features,
        "required_finite_features": required,
        "macro_source": macro_source_evidence,
        "long_rows": int(merged["direction"].eq("LONG").sum()),
        "short_rows": int(merged["direction"].eq("SHORT").sum()),
        "authorization": config["authorization"],
    }
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    dataset_path = output / config["outputs"]["merged_actions"]
    evidence_path = output / config["outputs"]["dataset_evidence"]
    merged.to_parquet(dataset_path, index=False)
    evidence["dataset_sha256"] = sha256_file(dataset_path)
    evidence_path.write_text(
        json.dumps(ready(evidence), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(ready(evidence), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
