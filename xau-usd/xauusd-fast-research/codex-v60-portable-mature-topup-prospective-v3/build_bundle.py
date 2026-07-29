from __future__ import annotations

import json

from src.serving import (
    OUTPUTS,
    load_config,
    recreate_serving_bundle,
    save_bundle,
)


def main() -> int:
    config = load_config()
    bundle, audit, check = recreate_serving_bundle(config)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    save_bundle(bundle, OUTPUTS / "MODEL_BUNDLE.joblib")
    (OUTPUTS / "BUILD_AUDIT.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8"
    )
    check.to_parquet(OUTPUTS / "STORED_2026_REPRODUCTION.parquet", index=False)
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
