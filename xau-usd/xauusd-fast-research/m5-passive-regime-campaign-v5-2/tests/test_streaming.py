from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from streaming import PolicyBlockCache, load_config, sha256_file  # noqa: E402


def _load_passive():
    path = RESEARCH_ROOT / "m5-passive-regime-campaign-v5" / "src" / "passive.py"
    spec = importlib.util.spec_from_file_location("m5_passive_v52_test_base", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _evaluate(values: list[int], block_size: int | None) -> tuple[list[int], int]:
    cache: dict[int, int] = {}
    policy_cache = PolicyBlockCache(block_size) if block_size is not None else None
    results: list[int] = []
    for value in values:
        if policy_cache is not None:
            policy_cache.before_policy(cache)
        if value not in cache:
            cache[value] = value * value + 3
        results.append(cache[value])
    clears = policy_cache.clear_count if policy_cache is not None else 0
    return results, clears


def test_streaming_cache_preserves_policy_outputs() -> None:
    policies = [index % 11 for index in range(100)]
    persistent, _ = _evaluate(policies, None)
    streaming, clears = _evaluate(policies, 25)
    assert streaming == persistent
    assert clears == 4


def test_cache_clears_at_exact_boundaries() -> None:
    cache: dict[int, int] = {99: 1}
    policy_cache = PolicyBlockCache(25)
    clear_before: list[int] = []
    for policy in range(51):
        previous = policy_cache.clear_count
        policy_cache.before_policy(cache)
        if policy_cache.clear_count > previous:
            clear_before.append(policy + 1)
        cache[policy] = policy
    assert clear_before == [1, 26, 51]


def test_manifest_is_byte_identical_to_v5(tmp_path: Path) -> None:
    config = load_config(ROOT)
    passive = _load_passive()
    generated = tmp_path / "manifest.csv"
    passive.generate_manifest(config["selection"]).to_csv(
        generated, index=False, lineterminator="\n"
    )
    assert sha256_file(generated) == config["base"]["unchanged_manifest_sha256"]


def test_invalid_block_size_is_rejected() -> None:
    try:
        PolicyBlockCache(0)
    except ValueError:
        return
    raise AssertionError("Expected invalid block size to fail")
