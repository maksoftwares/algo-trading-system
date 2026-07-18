from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
V51_ROOT = RESEARCH_ROOT / "m5-passive-regime-campaign-v5-1"
sys.path.insert(0, str(ROOT / "src"))

from streaming import PolicyBlockCache, load_config  # noqa: E402


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE_RUNNER = load_module("m5_passive_v52_base_runner", V51_ROOT / "run_screen.py")


def _correct_decision(value: str) -> str:
    return value.replace("V5_1", "V5_2")


def main() -> int:
    config = load_config(ROOT)
    block_cache = PolicyBlockCache(int(config["streaming"]["cache_block_policies"]))
    original_simulate = BASE_RUNNER.PASSIVE.simulate_variant
    original_write_json = BASE_RUNNER.write_json
    original_render = BASE_RUNNER._render
    original_artifact_manifest = BASE_RUNNER._artifact_manifest

    def bounded_simulate(*args: Any, **kwargs: Any) -> Any:
        cache = args[-1] if args else kwargs["outcome_cache"]
        block_cache.before_policy(cache)
        return original_simulate(*args, **kwargs)

    def corrected_write_json(path: Path, payload: Any) -> None:
        if isinstance(payload, dict) and "decision" in payload:
            payload = dict(payload)
            payload["decision"] = _correct_decision(str(payload["decision"]))
            payload["cache_policy"] = {
                "block_size_policies": block_cache.block_size,
                "blocks_cleared": block_cache.clear_count,
                "policies_scored": block_cache.policy_count,
                "reuse_across_blocks": False,
            }
        original_write_json(path, payload)

    def corrected_render(result: dict[str, Any], shortlist: Any) -> str:
        corrected = dict(result)
        corrected["decision"] = _correct_decision(str(result["decision"]))
        return original_render(corrected, shortlist).replace(
            "Campaign V5.1 Result", "Campaign V5.2 Result"
        )

    def corrected_artifact_manifest(directory: Path, names: list[str]) -> dict[str, Any]:
        payload = original_artifact_manifest(directory, names)
        payload["schema_version"] = "xauusd_m5_passive_regime_v5_2_artifacts"
        return payload

    BASE_RUNNER.ROOT = ROOT
    BASE_RUNNER.load_config = load_config
    BASE_RUNNER.PASSIVE.simulate_variant = bounded_simulate
    BASE_RUNNER.write_json = corrected_write_json
    BASE_RUNNER._render = corrected_render
    BASE_RUNNER._artifact_manifest = corrected_artifact_manifest
    result = int(BASE_RUNNER.main())
    result_path = ROOT / config["outputs"]["directory"] / config["outputs"]["result_json"]
    if result_path.is_file():
        print(json.dumps(json.loads(result_path.read_text(encoding="utf-8")), sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
