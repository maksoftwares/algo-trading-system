from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESEARCH_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from router import build_routed_trades, build_shadow_cache  # noqa: E402


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SCORE = load_module(
    "transition_online_router_v11_score",
    RESEARCH_ROOT / "regime-mechanism-campaign-v1" / "src" / "campaign.py",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _self_hash(payload: Mapping[str, Any]) -> str:
    work = {key: value for key, value in payload.items() if key != "contract_sha256"}
    encoded = json.dumps(
        work, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _verify_record(record: Mapping[str, Any], base: Path, label: str) -> None:
    path = (base / str(record["path"])).resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} path escaped root") from exc
    if not path.is_file():
        raise FileNotFoundError(path)
    if int(path.stat().st_size) != int(record["bytes"]):
        raise ValueError(f"{label} size mismatch: {record['path']}")
    if sha256_file(path) != str(record["sha256"]):
        raise ValueError(f"{label} hash mismatch: {record['path']}")


def verify_lock(config: dict[str, Any]) -> dict[str, Any]:
    output = ROOT / config["outputs"]["directory"]
    path = output / config["outputs"]["contract_lock"]
    if not path.is_file():
        raise FileNotFoundError("Run lock_contract.py before opening policy outcomes")
    lock = json.loads(path.read_text(encoding="utf-8"))
    if _self_hash(lock) != str(lock["contract_sha256"]):
        raise ValueError("Contract self-hash mismatch")
    for record in lock["package_files"] + lock["dependency_files"] + lock["source_files"]:
        _verify_record(record, REPO, "repository")
    _verify_record(lock["manifest_file"], REPO, "manifest")
    _verify_record(lock["manifest_evidence"], REPO, "manifest evidence")
    storage = Path(
        os.environ.get(
            str(config["source"]["storage_environment_variable"]),
            str(config["source"]["default_storage_root"]),
        )
    ).resolve()
    for record in lock["external_files"]:
        _verify_record(record, storage, "external")
    return lock


def _json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if math.isnan(number):
            return None
        if math.isinf(number):
            return "Infinity" if number > 0 else "-Infinity"
        return number
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(
            json.dumps(
                _json_value(payload), indent=2, sort_keys=True, ensure_ascii=True
            )
            + "\n"
        )


def _source_frame(config: Mapping[str, Any]) -> pd.DataFrame:
    source = config["source"]
    storage = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()
    timestamps = pd.read_parquet(
        storage / str(source["feature_cache"]), columns=["timestamp_ms"]
    )["timestamp_ms"]
    return pd.DataFrame(
        {"bar_start_utc": pd.to_datetime(timestamps, unit="ms", utc=True)}
    )


def _shortlist(metrics: pd.DataFrame, maximum: int) -> pd.DataFrame:
    ranked = metrics.assign(
        gate_count=metrics["gate_checks_json"].map(
            lambda raw: sum(json.loads(str(raw)).values())
        )
    ).sort_values(
        [
            "economic_pass",
            "gate_count",
            "minimum_era_stress_pf",
            "whole_stress_pf",
            "whole_trades",
            "attempt_no",
        ],
        ascending=[False, False, False, False, False, True],
        kind="mergesort",
    )
    return (
        ranked.groupby("mechanic", sort=False, group_keys=False)
        .head(maximum)
        .drop(columns="gate_count")
        .reset_index(drop=True)
    )


def _render(result: Mapping[str, Any], shortlist: pd.DataFrame) -> str:
    lines = [
        "# Transition Online Component Router V11 Result",
        "",
        f"Decision: `{result['decision']}`",
        "",
        f"Attempts completed: **{result['attempts_completed']}**",
        f"Economic finalists: **{result['economic_finalist_count']}**",
        f"FDR-supported finalists: **{result['fdr_finalist_count']}**",
        "",
        "| Attempt | Mechanic | Trades | Net R | PF | Min-era PF | Min-era avg R | DD R | Pass |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in shortlist.itertuples(index=False):
        lines.append(
            f"| {int(row.attempt_no)} | {row.mechanic} | {int(row.whole_trades)} | "
            f"{float(row.whole_stress_net_r):.3f} | {float(row.whole_stress_pf):.3f} | "
            f"{float(row.minimum_era_stress_pf):.3f} | "
            f"{float(row.minimum_era_average_stress_r):.3f} | "
            f"{float(row.whole_closed_drawdown_r):.3f} | {bool(row.economic_pass)} |"
        )
    lines.extend(
        (
            "",
            "All routing decisions use completed prior shadow trades only.",
            "This is selected historical discovery evidence, not authorization to trade.",
        )
    )
    return "\n".join(lines) + "\n"


def _assert_baseline_reproduces(
    config: Mapping[str, Any], source_frame: pd.DataFrame
) -> dict[str, Any]:
    baseline = pd.read_parquet(ROOT / config["source"]["baseline_portfolio_trades"])
    expected = pd.read_csv(ROOT / config["source"]["baseline_metrics"]).iloc[0]
    observed = SCORE.score_variant(baseline, source_frame, config)
    keys = (
        "whole_trades",
        "whole_stress_net_r",
        "whole_stress_pf",
        "minimum_era_stress_pf",
        "minimum_era_average_stress_r",
        "whole_closed_drawdown_r",
        "top_winners_removed_stress_net_r",
    )
    for key in keys:
        if not np.isclose(float(observed[key]), float(expected[key]), rtol=0.0, atol=1e-10):
            raise ValueError(
                f"Baseline score mismatch for {key}: {observed[key]} != {expected[key]}"
            )
    return {key: observed[key] for key in keys}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    config = json.loads(
        (ROOT / "config" / "transition_online_component_router_v11.json").read_text(
            encoding="utf-8"
        )
    )
    lock = verify_lock(config)
    if args.verify_only:
        print(lock["contract_sha256"])
        return 0
    output = ROOT / config["outputs"]["directory"]
    result_path = output / config["outputs"]["result_json"]
    if result_path.exists():
        raise FileExistsError("V11 policy outcomes already exist")
    manifest = pd.read_csv(output / config["outputs"]["manifest"])
    components = pd.read_parquet(ROOT / config["source"]["component_trades"])
    source_frame = _source_frame(config)
    baseline_audit = _assert_baseline_reproduces(config, source_frame)
    base_weights = {
        int(key): float(value)
        for key, value in config["portfolio"]["base_weights"].items()
    }
    lookbacks = sorted(
        {
            int(json.loads(raw)["lookback_days"])
            for raw in manifest["parameters_json"]
        }
    )
    cache = build_shadow_cache(components, lookbacks, sorted(base_weights))
    rows: list[dict[str, Any]] = []
    for item in manifest.itertuples(index=False):
        policy = SimpleNamespace(
            **item._asdict(), tie_priority=config["portfolio"]["tie_priority"]
        )
        trades = build_routed_trades(
            components,
            policy,
            base_weights,
            int(config["portfolio"]["maximum_trades_per_utc_day"]),
            cache,
        )
        score = SCORE.score_variant(trades, source_frame, config)
        rows.append({**item._asdict(), **score})
    metrics = pd.DataFrame(rows)
    metrics["daily_fdr_qvalue"] = SCORE.bh_adjust(metrics["daily_pvalue"])
    metrics["statistical_pass"] = metrics["daily_fdr_qvalue"].le(
        float(config["selection"]["false_discovery_rate"])
    )
    shortlist = _shortlist(
        metrics, int(config["selection"]["maximum_finalists_per_mechanic"])
    )
    selected_frames: list[pd.DataFrame] = []
    by_attempt = manifest.set_index("attempt_no")
    for attempt in shortlist["attempt_no"]:
        item = by_attempt.loc[int(attempt)]
        policy = SimpleNamespace(
            attempt_no=int(attempt),
            router_id=str(item["router_id"]),
            mechanic=str(item["mechanic"]),
            parameters_json=str(item["parameters_json"]),
            tie_priority=config["portfolio"]["tie_priority"],
        )
        selected_frames.append(
            build_routed_trades(
                components,
                policy,
                base_weights,
                int(config["portfolio"]["maximum_trades_per_utc_day"]),
                cache,
            )
        )
    selected_trades = pd.concat(selected_frames, ignore_index=True)
    economic = metrics.loc[metrics["economic_pass"]]
    fdr = economic.loc[economic["statistical_pass"]]
    decision = (
        "TRANSITION_ONLINE_ROUTER_V11_FDR_FINALIST_FOUND"
        if not fdr.empty
        else (
            "TRANSITION_ONLINE_ROUTER_V11_ECONOMIC_FINALIST_FOUND"
            if not economic.empty
            else "NO_TRANSITION_ONLINE_ROUTER_V11_ECONOMIC_FINALIST"
        )
    )
    mechanic_summary = {
        mechanic: {
            "attempts": int(len(group)),
            "economic_passes": int(group["economic_pass"].sum()),
            "fdr_passes": int((group["economic_pass"] & group["statistical_pass"]).sum()),
            "best_minimum_era_pf": float(group["minimum_era_stress_pf"].max()),
            "best_whole_pf": float(group["whole_stress_pf"].replace(np.inf, np.nan).max()),
        }
        for mechanic, group in metrics.groupby("mechanic", sort=True)
    }
    result = {
        "schema_version": config["schema_version"],
        "contract_sha256": lock["contract_sha256"],
        "decision": decision,
        "attempt_first": int(config["selection"]["attempt_first"]),
        "attempt_last": int(config["selection"]["attempt_last"]),
        "attempts_completed": int(len(metrics)),
        "cumulative_campaign_attempts": int(config["selection"]["attempt_last"]),
        "economic_finalist_count": int(len(economic)),
        "fdr_finalist_count": int(len(fdr)),
        "economic_finalist_attempts": [int(value) for value in economic["attempt_no"]],
        "fdr_finalist_attempts": [int(value) for value in fdr["attempt_no"]],
        "baseline_reproduction": baseline_audit,
        "mechanic_summary": mechanic_summary,
        "authorization": {
            "historical_discovery_only": True,
            "raw_tick_source_is_independent_holdout": False,
            "independent_replication_required": True,
            "prospective_shadow_required": True,
            "training_authorized": False,
            "execution_authorized": False,
            "research_only": True,
        },
    }
    with (output / config["outputs"]["metrics"]).open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        metrics.to_csv(handle, index=False, lineterminator="\n")
    with (output / config["outputs"]["shortlist"]).open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        shortlist.to_csv(handle, index=False, lineterminator="\n")
    selected_trades.to_parquet(output / config["outputs"]["selected_trades"], index=False)
    write_json(result_path, result)
    with (output / config["outputs"]["result_markdown"]).open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        handle.write(_render(result, shortlist))
    names = [
        config["outputs"]["contract_lock"],
        config["outputs"]["manifest"],
        config["outputs"]["manifest_evidence"],
        config["outputs"]["metrics"],
        config["outputs"]["shortlist"],
        config["outputs"]["selected_trades"],
        config["outputs"]["result_json"],
        config["outputs"]["result_markdown"],
    ]
    write_json(
        output / config["outputs"]["artifact_manifest"],
        {
            "schema_version": "xauusd_transition_online_router_v11_artifacts",
            "files": {
                name: {
                    "bytes": int((output / name).stat().st_size),
                    "sha256": sha256_file(output / name),
                }
                for name in names
            },
        },
    )
    print(json.dumps(_json_value(result), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
