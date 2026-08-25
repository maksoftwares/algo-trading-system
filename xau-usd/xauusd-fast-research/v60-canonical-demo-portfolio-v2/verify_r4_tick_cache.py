from __future__ import annotations

import argparse
from datetime import UTC, datetime
import gc
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
R4_ROOT = REPO_ROOT / "xau-usd" / "xauusd-fast-research" / "capital-r4-chop-forward-v34"
sys.path.insert(0, str(ROOT / "src"))

from feeds import _load_module  # noqa: E402
from r4_bar_cache import load_quote_bars_cached  # noqa: E402
from r4_tick_cache import load_ticks_cached  # noqa: E402


def frame_sha256(frame: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    digest.update(json.dumps(list(frame.columns)).encode("utf-8"))
    digest.update(json.dumps([str(value) for value in frame.dtypes]).encode("utf-8"))
    for start in range(0, len(frame), 250_000):
        hashed = pd.util.hash_pandas_object(
            frame.iloc[start : start + 250_000], index=False, categorize=True
        )
        digest.update(hashed.to_numpy().tobytes())
    return digest.hexdigest()


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify exact R4 tick-cache parity")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "v60_canonical_demo_portfolio_v2.json",
    )
    parser.add_argument("--cache-directory", type=Path)
    parser.add_argument("--bar-cache-directory", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--exclude-recent-seconds",
        type=int,
        default=300,
        help="Exclude actively growing files modified within this interval",
    )
    args = parser.parse_args()

    config = load_config(args.config.resolve())
    runtime = Path(config["runtime"]["directory"])
    cache_directory = (
        args.cache_directory.resolve()
        if args.cache_directory
        else runtime / "feeds" / "r4" / "tick_cache_v1"
    )
    bar_cache_directory = (
        args.bar_cache_directory.resolve()
        if args.bar_cache_directory
        else runtime / "feeds" / "r4" / "bar_cache_v1"
    )
    output = (
        args.output.resolve()
        if args.output
        else ROOT / "outputs" / "R4_TICK_CACHE_PARITY.json"
    )

    runner = _load_module("v60_r4_cache_parity_runner", R4_ROOT / "run_shadow.py")
    frozen = runner.load_frozen(REPO_ROOT, R4_ROOT)
    source = frozen.package_config["source"]
    source.update(
        {
            "tick_directory": str(config["feeds"]["terminal_files_directory"]),
            "tick_filename_glob": str(config["feeds"]["tick_filename_glob"]),
            "account_login": int(config["account"]["expected_login"]),
            "account_server": str(config["account"]["expected_server"]),
        }
    )
    loader_config = runner._tick_loader_config(frozen.package_config)
    discovered_paths = sorted(
        Path(source["tick_directory"]).glob(source["tick_filename_glob"])
    )
    verification_started = time.time()
    paths = [
        path
        for path in discovered_paths
        if verification_started - path.stat().st_mtime
        >= int(args.exclude_recent_seconds)
    ]
    excluded_paths = [path for path in discovered_paths if path not in paths]
    if not paths:
        raise RuntimeError("No immutable R4 tick files are available for parity")
    source_identities = {
        str(path.resolve()): (int(path.stat().st_size), int(path.stat().st_mtime_ns))
        for path in paths
    }
    completed_through = pd.Timestamp.now(tz="UTC").floor("5min")

    started = time.perf_counter()
    reference_ticks, reference_audit, reference_daily = (
        frozen.tick_loader_module.load_ticks(paths, loader_config)
    )
    reference_load_seconds = time.perf_counter() - started
    reference_tick_sha = frame_sha256(reference_ticks)
    reference_bars = runner.aggregate_capital_quotes(
        reference_ticks,
        completed_through=completed_through,
        quality=frozen.package_config["data_quality"],
    )
    reference_bar_sha = frame_sha256(reference_bars)
    del reference_ticks
    gc.collect()

    started = time.perf_counter()
    cached_ticks, cached_audit, cached_daily = load_ticks_cached(
        paths,
        loader_config,
        cache_directory=cache_directory,
        original_loader=frozen.tick_loader_module.load_ticks,
    )
    cache_build_seconds = time.perf_counter() - started
    cached_tick_sha = frame_sha256(cached_ticks)
    cached_bars = runner.aggregate_capital_quotes(
        cached_ticks,
        completed_through=completed_through,
        quality=frozen.package_config["data_quality"],
    )
    cached_bar_sha = frame_sha256(cached_bars)

    pd.testing.assert_frame_equal(reference_daily, cached_daily, check_exact=True)
    pd.testing.assert_frame_equal(reference_bars, cached_bars, check_exact=True)
    for field in ("source_files", "raw_rows", "unique_rows", "duplicate_millisecond_rows"):
        if reference_audit[field] != cached_audit[field]:
            raise AssertionError(f"R4 cache audit mismatch: {field}")
    if reference_tick_sha != cached_tick_sha:
        raise AssertionError("R4 cached tick content differs from the original loader")
    if reference_bar_sha != cached_bar_sha:
        raise AssertionError("R4 cached quote bars differ from the original aggregation")
    del cached_ticks
    gc.collect()

    started = time.perf_counter()
    warm_ticks, warm_audit, warm_daily = load_ticks_cached(
        paths,
        loader_config,
        cache_directory=cache_directory,
        original_loader=frozen.tick_loader_module.load_ticks,
    )
    warm_load_seconds = time.perf_counter() - started
    warm_tick_sha = frame_sha256(warm_ticks)
    if warm_tick_sha != reference_tick_sha:
        raise AssertionError("Warm R4 cache content differs from the original loader")
    pd.testing.assert_frame_equal(reference_daily, warm_daily, check_exact=True)
    del warm_ticks
    gc.collect()

    started = time.perf_counter()
    bar_cached, bar_audit, bar_daily = load_quote_bars_cached(
        paths,
        loader_config,
        quality=frozen.package_config["data_quality"],
        completed_through=completed_through,
        cache_directory=bar_cache_directory,
        original_loader=frozen.tick_loader_module.load_ticks,
        original_aggregate=runner.aggregate_capital_quotes,
    )
    bar_cache_build_seconds = time.perf_counter() - started
    pd.testing.assert_frame_equal(reference_bars, bar_cached, check_exact=True)
    pd.testing.assert_frame_equal(reference_daily, bar_daily, check_exact=True)
    for field in ("source_files", "raw_rows", "unique_rows", "duplicate_millisecond_rows"):
        if reference_audit[field] != bar_audit[field]:
            raise AssertionError(f"R4 bar-cache audit mismatch: {field}")

    started = time.perf_counter()
    warm_bars, warm_bar_audit, warm_bar_daily = load_quote_bars_cached(
        paths,
        loader_config,
        quality=frozen.package_config["data_quality"],
        completed_through=completed_through,
        cache_directory=bar_cache_directory,
        original_loader=frozen.tick_loader_module.load_ticks,
        original_aggregate=runner.aggregate_capital_quotes,
    )
    warm_bar_cache_load_seconds = time.perf_counter() - started
    pd.testing.assert_frame_equal(reference_bars, warm_bars, check_exact=True)
    pd.testing.assert_frame_equal(reference_daily, warm_bar_daily, check_exact=True)
    final_identities = {
        str(path.resolve()): (int(path.stat().st_size), int(path.stat().st_mtime_ns))
        for path in paths
    }
    if final_identities != source_identities:
        raise AssertionError("An immutable R4 source file changed during parity verification")

    report = {
        "schema_version": "xauusd_v60_r4_tick_cache_parity_v1",
        "verified_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "result": "PASS_EXACT_PARITY",
        "source_files": len(paths),
        "discovered_source_files": len(discovered_paths),
        "excluded_mutable_files": [str(path.resolve()) for path in excluded_paths],
        "source_bytes": sum(path.stat().st_size for path in paths),
        "raw_tick_rows": int(reference_audit["raw_rows"]),
        "unique_tick_rows": int(reference_audit["unique_rows"]),
        "quote_m5_rows": int(len(reference_bars)),
        "tick_frame_sha256": reference_tick_sha,
        "quote_bar_frame_sha256": reference_bar_sha,
        "reference_load_seconds": reference_load_seconds,
        "cache_build_seconds": cache_build_seconds,
        "warm_cache_load_seconds": warm_load_seconds,
        "warm_cache_hits": int(warm_audit["cache"]["hits"]),
        "warm_cache_misses": int(warm_audit["cache"]["misses"]),
        "bar_cache_build_seconds": bar_cache_build_seconds,
        "warm_bar_cache_load_seconds": warm_bar_cache_load_seconds,
        "warm_bar_cache_hits": int(warm_bar_audit["bar_cache"]["hits"]),
        "warm_bar_cache_misses": int(warm_bar_audit["bar_cache"]["misses"]),
        "completed_through_utc": completed_through.isoformat(),
        "strategy_or_risk_parameters_changed": False,
        "broker_action_added": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
