from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from proxy_data import sha256_file  # noqa: E402
from replication import (  # noqa: E402
    load_foundation,
    pooled_gate_checks,
    proxy_gate_checks,
    simulate_proxy,
    summarize,
    unique_pooled_trades,
)


def self_hash(payload: dict[str, Any]) -> str:
    work = dict(payload)
    work.pop("contract_sha256", None)
    encoded = json.dumps(
        work, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def verify_record(record: Mapping[str, Any], base: Path, label: str) -> None:
    path = (base / str(record["path"])).resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} path escaped its root") from exc
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size != int(record["bytes"]):
        raise ValueError(f"{label} size mismatch: {record['path']}")
    if sha256_file(path) != str(record["sha256"]):
        raise ValueError(f"{label} SHA-256 mismatch: {record['path']}")


def verify_lock(config: Mapping[str, Any]) -> dict[str, Any]:
    output = ROOT / str(config["outputs"]["directory"])
    lock_path = output / str(config["outputs"]["contract_lock"])
    if not lock_path.is_file():
        raise FileNotFoundError("Run lock_contract.py before opening replication outcomes")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if self_hash(lock) != str(lock["contract_sha256"]):
        raise ValueError("Contract self-hash mismatch")
    for item in lock["package_files"] + lock["dependency_files"]:
        verify_record(item, REPO, "repository")
    source = config["source"]
    storage = Path(
        os.environ.get(source["storage_environment_variable"], source["default_storage_root"])
    ).resolve()
    for item in lock["external_files"]:
        verify_record(item, storage, "external")
    if int(lock["candidate_count"]) != 2 or int(lock["parameter_sets_per_candidate"]) != 1:
        raise ValueError("Replication cardinality differs from the preregistered contract")
    return lock


def json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
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
    path.write_text(
        json.dumps(json_value(payload), indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def render(result: Mapping[str, Any]) -> str:
    lines = [
        "# XAUUSD Macro Transition Proxy Replication V2 Result",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "| Proxy | Raw signals | Trades | Net R | PF | Avg R | Drawdown R | Pass |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in result["proxy_results"]:
        summary = item["summary"]
        lines.append(
            f"| {item['proxy_symbol']} | {item['raw_signals']} | {summary['trades']} | "
            f"{summary['stress_net_r']:.3f} | {summary['stress_profit_factor']:.3f} | "
            f"{summary['average_stress_r']:.3f} | {summary['closed_drawdown_r']:.3f} | "
            f"{str(item['pass']).lower()} |"
        )
    pooled = result["pooled_unique_summary"]
    lines.extend(
        [
            "",
            "## Unique Pooled Evidence",
            "",
            f"Trades: **{pooled['trades']}**",
            f"Duplicate proxy events removed: **{result['duplicate_proxy_events_removed']}**",
            f"Stress net: **{pooled['stress_net_r']:.3f}R**",
            f"Stress PF: **{pooled['stress_profit_factor']:.3f}**",
            f"Average stress return: **{pooled['average_stress_r']:.3f}R**",
            f"Closed drawdown: **{pooled['closed_drawdown_r']:.3f}R**",
            "",
            "This is supporting historical replication evidence only. It does not authorize training or execution.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify the sealed contract without loading data or opening outcomes.",
    )
    args = parser.parse_args()
    config = json.loads(
        (ROOT / "config" / "macro_transition_proxy_replication_v2.json").read_text(
            encoding="utf-8"
        )
    )
    lock = verify_lock(config)
    if args.verify_only:
        print(
            json.dumps(
                {
                    "verified": True,
                    "contract_sha256": lock["contract_sha256"],
                    "outcomes_opened": False,
                },
                sort_keys=True,
            )
        )
        return 0

    output = ROOT / config["outputs"]["directory"]
    result_path = output / config["outputs"]["result_json"]
    if result_path.exists():
        raise FileExistsError("V2 outcomes already exist; same-version reruns are forbidden")
    foundation = load_foundation(config)
    outcome_cache: dict[tuple[int, int, str], dict[str, Any] | None] = {}
    proxy_results = []
    trade_frames = []
    for proxy_symbol in sorted(foundation.decisions):
        trades, raw_signals = simulate_proxy(
            foundation.decisions[proxy_symbol],
            foundation.arrays,
            config,
            outcome_cache,
        )
        trades = trades.assign(proxy_symbol=proxy_symbol)
        trade_frames.append(trades)
        summary = summarize(trades, int(config["gates"]["proxy_top_winners_removed"]))
        checks = proxy_gate_checks(summary, config["gates"])
        proxy_results.append(
            {
                "proxy_symbol": proxy_symbol,
                "raw_signals": raw_signals,
                "summary": summary,
                "gate_checks": checks,
                "pass": bool(all(checks.values())),
            }
        )
    all_trades = (
        pd.concat(trade_frames, ignore_index=True)
        if trade_frames
        else pd.DataFrame(columns=["proxy_symbol", "stress_net_r"])
    )
    unique, overlap = unique_pooled_trades(all_trades)
    pooled_summary = summarize(
        unique, int(config["gates"]["pooled_top_winners_removed"])
    )
    pooled_checks = pooled_gate_checks(pooled_summary, config["gates"])
    passed = all(item["pass"] for item in proxy_results) and all(pooled_checks.values())
    decision = (
        "OUT_OF_ERA_PROXY_REPLICATION_SUPPORTED"
        if passed
        else "OUT_OF_ERA_PROXY_REPLICATION_NOT_SUPPORTED"
    )
    result = {
        "schema_version": config["schema_version"],
        "contract_sha256": lock["contract_sha256"],
        "decision": decision,
        "source_candidate": lock["fixed_candidate"],
        "proxy_results": proxy_results,
        "pooled_unique_summary": pooled_summary,
        "pooled_gate_checks": pooled_checks,
        "duplicate_proxy_events_removed": overlap,
        "data_evidence": foundation.evidence,
        "execution_evidence": {
            "native_dukascopy_gold_bid_ask": True,
            "same_bar_priority": config["execution"]["same_bar_priority"],
            "unique_cached_outcomes": len(outcome_cache),
        },
        "authorization": {
            "supporting_replication_only": True,
            "exact_source_confirmation_required": True,
            "prospective_shadow_required": True,
            "shock_is_abstain": True,
            "training_authorized": False,
            "execution_authorized": False,
            "research_only": True,
        },
    }
    trades_path = output / config["outputs"]["trades"]
    markdown_path = output / config["outputs"]["result_markdown"]
    artifact_path = output / config["outputs"]["artifact_manifest"]
    all_trades.sort_values(
        ["proxy_symbol", "entry_time"], kind="mergesort"
    ).to_csv(trades_path, index=False, lineterminator="\n")
    write_json(result_path, result)
    markdown_path.write_text(render(result), encoding="utf-8")
    artifact_names = [
        config["outputs"]["contract_lock"],
        config["outputs"]["result_json"],
        config["outputs"]["result_markdown"],
        config["outputs"]["trades"],
    ]
    write_json(
        artifact_path,
        {
            "schema_version": "xauusd_macro_transition_proxy_replication_v2_artifacts",
            "files": {
                name: {
                    "bytes": int((output / name).stat().st_size),
                    "sha256": sha256_file(output / name),
                }
                for name in artifact_names
            },
        },
    )
    print(json.dumps(json_value(result), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
