from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
REPO = ROOT.parents[2]
MACRO_ROOT = RESEARCH_ROOT / "macro-regime-routing-v1"
sys.path.insert(0, str(ROOT / "src"))

from composite import build_composite_trades  # noqa: E402


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


load_module("campaign", MACRO_ROOT / "src" / "campaign.py")
FOUNDATION = load_module(
    "transition_composite_v7_foundation", MACRO_ROOT / "src" / "foundation.py"
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
        raise FileNotFoundError("Run lock_contract.py before opening composite outcomes")
    lock = json.loads(path.read_text(encoding="utf-8"))
    if _self_hash(lock) != str(lock["contract_sha256"]):
        raise ValueError("Contract self-hash mismatch")
    for record in (
        lock["package_files"]
        + lock["dependency_files"]
        + lock["source_campaign_files"]
    ):
        _verify_record(record, REPO, "repository")
    _verify_record(lock["manifest_file"], REPO, "manifest")
    _verify_record(lock["manifest_evidence"], REPO, "manifest evidence")
    storage = Path(lock["external_storage_root"]).resolve()
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
    path.write_text(
        json.dumps(_json_value(payload), indent=2, sort_keys=True, ensure_ascii=True)
        + "\n",
        encoding="utf-8",
    )


def _render(result: Mapping[str, Any], best: Mapping[str, Any]) -> str:
    return "\n".join(
        (
            "# Transition Composite Discovery V7 Result",
            "",
            f"Decision: `{result['decision']}`",
            "",
            f"Policies tested: **{result['attempts_completed']}**",
            f"Economic finalists: **{result['economic_finalist_count']}**",
            f"Adjusted-p finalists: **{result['statistical_finalist_count']}**",
            "",
            f"Best policy: **{int(best['attempt_no'])}**",
            f"Components: `{best['component_attempts_json']}`",
            f"Tie priority: `{best['tie_priority']}`",
            f"Trades: **{int(best['whole_trades'])}**",
            f"Stress net: **{float(best['whole_stress_net_r']):.3f} R**",
            f"Stress PF: **{float(best['whole_stress_pf']):.3f}**",
            f"Minimum era PF: **{float(best['minimum_era_stress_pf']):.3f}**",
            f"Average stress return: **{float(best['whole_average_stress_r']):.3f} R**",
            f"Closed drawdown: **{float(best['whole_closed_drawdown_r']):.3f} R**",
            "",
            "This is post-selection discovery on exposed component outcomes.",
            "It does not authorize model training or trading.",
            "",
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    config = json.loads(
        (ROOT / "config" / "transition_composite_discovery_v7.json").read_text(
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
        raise FileExistsError("V7 outcomes already exist")
    source_root = (ROOT / config["source_campaign"]["directory"]).resolve()
    source_config = json.loads(
        (source_root / config["source_campaign"]["config"]).read_text(
            encoding="utf-8"
        )
    )
    component_trades = pd.read_parquet(
        source_root / config["source_campaign"]["selected_trades"]
    )
    manifest = pd.read_csv(output / config["outputs"]["manifest"])
    foundation = FOUNDATION.load_foundation(source_config)
    score_config = dict(source_config)
    score_config["windows"] = config["windows"]
    score_config["economic_gates"] = config["economic_gates"]
    rows: list[dict[str, Any]] = []
    trade_frames: list[pd.DataFrame] = []
    maximum_daily = int(config["execution"]["maximum_trades_per_composite_utc_day"])
    search_count = int(config["selection"]["subset_search_count"])
    for policy in manifest.itertuples(index=False):
        trades = build_composite_trades(component_trades, policy, maximum_daily)
        score = FOUNDATION.SCORE.score_variant(
            trades, foundation.execution_frame, score_config
        )
        adjusted = min(1.0, float(score["daily_pvalue"]) * search_count)
        statistical = adjusted <= float(config["selection"]["false_discovery_rate"])
        rows.append(
            {
                **policy._asdict(),
                **score,
                "selection_adjusted_pvalue": adjusted,
                "statistical_pass": statistical,
            }
        )
        trade_frames.append(trades)
    metrics = pd.DataFrame(rows)
    economic = metrics.loc[metrics["economic_pass"]]
    statistical = economic.loc[economic["statistical_pass"]]
    ranked = metrics.sort_values(
        [
            "economic_pass",
            "minimum_era_stress_pf",
            "whole_stress_pf",
            "whole_trades",
            "attempt_no",
        ],
        ascending=[False, False, False, False, True],
        kind="mergesort",
    )
    best = ranked.iloc[0].to_dict()
    decision = (
        "TRANSITION_COMPOSITE_V7_STATISTICAL_FINALIST_FOUND"
        if not statistical.empty
        else (
            "TRANSITION_COMPOSITE_V7_ECONOMIC_FINALIST_FOUND"
            if not economic.empty
            else "NO_TRANSITION_COMPOSITE_V7_ECONOMIC_FINALIST"
        )
    )
    result = {
        "schema_version": config["schema_version"],
        "contract_sha256": lock["contract_sha256"],
        "decision": decision,
        "attempt_first": int(config["selection"]["attempt_first"]),
        "attempt_last": int(config["selection"]["attempt_last"]),
        "attempts_completed": int(len(metrics)),
        "cumulative_campaign_attempts": int(config["selection"]["attempt_last"]),
        "economic_finalist_count": int(len(economic)),
        "statistical_finalist_count": int(len(statistical)),
        "economic_finalist_attempts": [int(value) for value in economic["attempt_no"]],
        "statistical_finalist_attempts": [
            int(value) for value in statistical["attempt_no"]
        ],
        "best_policy": _json_value(best),
        "authorization": {
            "post_selection_discovery": True,
            "exact_raw_tick_confirmation_required": True,
            "independent_replication_required": True,
            "prospective_shadow_required": True,
            "training_authorized": False,
            "execution_authorized": False,
            "research_only": True,
        },
    }
    all_trades = pd.concat(trade_frames, ignore_index=True)
    metrics_path = output / config["outputs"]["metrics"]
    trades_path = output / config["outputs"]["trades"]
    markdown_path = output / config["outputs"]["result_markdown"]
    metrics.to_csv(metrics_path, index=False, lineterminator="\n")
    all_trades.to_parquet(trades_path, index=False)
    write_json(result_path, result)
    markdown_path.write_text(_render(result, best), encoding="utf-8")
    names = [
        config["outputs"]["manifest"],
        config["outputs"]["manifest_evidence"],
        config["outputs"]["contract_lock"],
        config["outputs"]["metrics"],
        config["outputs"]["trades"],
        config["outputs"]["result_json"],
        config["outputs"]["result_markdown"],
    ]
    write_json(
        output / config["outputs"]["artifact_manifest"],
        {
            "schema_version": "xauusd_transition_composite_v7_artifacts",
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
