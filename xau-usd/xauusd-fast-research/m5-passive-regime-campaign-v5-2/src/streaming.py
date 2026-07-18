from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, MutableMapping


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_config(root: Path) -> dict[str, Any]:
    overlay = json.loads(
        (root / "config" / "m5_passive_regime_campaign_v5_2.json").read_text(
            encoding="utf-8"
        )
    )
    base_path = (root / str(overlay["base"]["config_path"])).resolve()
    invalidation_path = (root / str(overlay["base"]["invalidation_path"])).resolve()
    unchanged_manifest = (
        root / str(overlay["base"]["unchanged_manifest_path"])
    ).resolve()
    if sha256_file(base_path) != str(overlay["base"]["config_sha256"]):
        raise ValueError("V5.1 base config hash mismatch")
    if sha256_file(invalidation_path) != str(overlay["base"]["invalidation_sha256"]):
        raise ValueError("V5.1 invalidation hash mismatch")
    if sha256_file(unchanged_manifest) != str(
        overlay["base"]["unchanged_manifest_sha256"]
    ):
        raise ValueError("V5.1 manifest hash mismatch")
    v51_root = base_path.parent.parent
    v51_clock = _load_module(
        "m5_passive_v52_config_base", v51_root / "src" / "clock.py"
    )
    config = v51_clock.load_config(v51_root)
    for key in ("schema_version", "outputs", "research_controls"):
        config[key] = overlay[key]
    config["base"] = overlay["base"]
    config["streaming"] = overlay["streaming"]
    return config


class PolicyBlockCache:
    def __init__(self, block_size: int) -> None:
        if block_size <= 0:
            raise ValueError("block_size must be positive")
        self.block_size = int(block_size)
        self.policy_count = 0
        self.clear_count = 0

    def before_policy(self, cache: MutableMapping[Any, Any]) -> None:
        if self.policy_count % self.block_size == 0:
            cache.clear()
            self.clear_count += 1
        self.policy_count += 1
