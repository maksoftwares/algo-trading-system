from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
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

from transition import simulate_candidate_stream  # noqa: E402


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CAMPAIGN = load_module("campaign", MACRO_ROOT / "src" / "campaign.py")
FOUNDATION = load_module(
    "macro_transition_rawtick_run_foundation", MACRO_ROOT / "src" / "foundation.py"
)
R2 = load_module(
    "macro_transition_rawtick_r2",
    RESEARCH_ROOT / "r2-downtrend-portability-v2" / "src" / "downtrend.py",
)
SCORE = load_module(
    "macro_transition_rawtick_score",
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
        raise ValueError(f"{label} path escaped root: {path}") from exc
    if not path.is_file():
        raise FileNotFoundError(path)
    if int(path.stat().st_size) != int(record["bytes"]):
        raise ValueError(f"{label} size mismatch: {record['path']}")
    if sha256_file(path) != str(record["sha256"]):
        raise ValueError(f"{label} hash mismatch: {record['path']}")


def verify_lock(config: dict[str, Any]) -> dict[str, Any]:
    path = (
        ROOT
        / config["outputs"]["directory"]
        / config["outputs"]["contract_lock"]
    )
    if not path.is_file():
        raise FileNotFoundError("Run lock_contract.py before opening raw outcomes")
    lock = json.loads(path.read_text(encoding="utf-8"))
    if _self_hash(lock) != str(lock["contract_sha256"]):
        raise ValueError("Contract self-hash mismatch")
    for record in lock["package_files"] + lock["dependency_files"]:
        _verify_record(record, REPO, "repository")
    _verify_record(lock["candidate_file"], REPO, "candidate")
    _verify_record(lock["candidate_manifest"], REPO, "candidate manifest")
    source = config["source"]
    storage = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
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
    path.write_text(
        json.dumps(_json_value(payload), indent=2, sort_keys=True, ensure_ascii=True)
        + "\n",
        encoding="utf-8",
    )


def _render(result: Mapping[str, Any], metrics: Mapping[str, Any]) -> str:
    return "\n".join(
        (
            "# Macro Transition Raw-Tick Confirmation V3 Result",
            "",
            f"Decision: `{result['decision']}`",
            "",
            f"Raw signals: **{result['origin_raw_signals']}**",
            f"Sealed candidates: **{result['candidate_rows']}**",
            f"Accepted trades: **{result['trade_rows']}**",
            f"Stress net: **{float(metrics['whole_stress_net_r']):.3f} R**",
            f"Stress PF: **{float(metrics['whole_stress_pf']):.3f}**",
            f"Minimum era PF: **{float(metrics['minimum_era_stress_pf']):.3f}**",
            f"Average stress return: **{float(metrics['whole_average_stress_r']):.3f} R**",
            f"Closed drawdown: **{float(metrics['whole_closed_drawdown_r']):.3f} R**",
            f"Top five winners removed: **{float(metrics['top_winners_removed_stress_net_r']):.3f} R**",
            f"Economic pass: **{bool(metrics['economic_pass'])}**",
            "",
            "This is a post-selection raw-tick diagnostic on exposed history.",
            "It does not authorize model training or trading.",
            "",
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    config = json.loads(
        (ROOT / "config" / "macro_transition_rawtick_confirmation_v3.json").read_text(
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
        raise FileExistsError("Raw-tick outcomes already exist")
    candidates = pd.read_parquet(output / config["outputs"]["candidates"])
    tick_store = R2.VerifiedTickStore(R2.storage_root(config), config)
    trades, rejections = simulate_candidate_stream(
        candidates, tick_store, R2.TickQuote, config["execution"]
    )
    foundation = FOUNDATION.load_foundation(config)
    metrics = SCORE.score_variant(trades, foundation.execution_frame, config)
    selection_adjusted_pvalue = min(
        1.0,
        float(metrics["daily_pvalue"])
        * int(config["selection"]["origin_transition_attempts"]),
    )
    decision = (
        "RAW_TICK_ECONOMIC_TRANSITION_CANDIDATE_FOUND"
        if bool(metrics["economic_pass"])
        else "NO_RAW_TICK_ECONOMIC_TRANSITION_CANDIDATE"
    )
    result = {
        "schema_version": config["schema_version"],
        "contract_sha256": lock["contract_sha256"],
        "decision": decision,
        "origin_attempt": int(config["candidate"]["origin_attempt"]),
        "origin_raw_signals": int(config["candidate"]["expected_raw_signals"]),
        "candidate_rows": int(len(candidates)),
        "trade_rows": int(len(trades)),
        "selection_adjusted_pvalue": selection_adjusted_pvalue,
        "execution_audit": {
            "rejections": rejections,
            "stop_trades": int(trades["exit_reason"].eq("STOP").sum()) if not trades.empty else 0,
            "stop_slippage_trades": int(trades["exit_reason"].eq("STOP_SLIPPAGE").sum()) if not trades.empty else 0,
            "target_trades": int(trades["exit_reason"].eq("TARGET").sum()) if not trades.empty else 0,
            "fixed_horizon_trades": int(trades["exit_reason"].eq("FIXED_HORIZON").sum()) if not trades.empty else 0,
            "maximum_horizon_delay_minutes": float(trades["horizon_delay_minutes"].max()) if not trades.empty else 0.0,
        },
        "authorization": {
            "selected_after_origin_outcomes": True,
            "raw_tick_result_can_be_independent_holdout": False,
            "independent_proxy_replication_required": True,
            "prospective_shadow_required": True,
            "training_authorized": False,
            "execution_authorized": False,
            "research_only": True,
        },
    }
    trades_path = output / config["outputs"]["trades"]
    metrics_path = output / config["outputs"]["metrics"]
    markdown_path = output / config["outputs"]["result_markdown"]
    trades.to_parquet(trades_path, index=False)
    pd.DataFrame([{**metrics, "selection_adjusted_pvalue": selection_adjusted_pvalue}]).to_csv(
        metrics_path, index=False, lineterminator="\n"
    )
    write_json(result_path, result)
    markdown_path.write_text(_render(result, metrics), encoding="utf-8")
    names = [
        config["outputs"]["candidates"],
        config["outputs"]["candidate_manifest"],
        config["outputs"]["contract_lock"],
        config["outputs"]["trades"],
        config["outputs"]["metrics"],
        config["outputs"]["result_json"],
        config["outputs"]["result_markdown"],
    ]
    artifact = {
        "schema_version": "xauusd_macro_transition_rawtick_v3_artifacts",
        "files": {
            name: {
                "bytes": int((output / name).stat().st_size),
                "sha256": sha256_file(output / name),
            }
            for name in names
        },
    }
    write_json(output / config["outputs"]["artifact_manifest"], artifact)
    print(json.dumps(_json_value({**result, "metrics": metrics}), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

