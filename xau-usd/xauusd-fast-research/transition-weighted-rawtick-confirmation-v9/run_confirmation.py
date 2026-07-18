from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
from types import SimpleNamespace
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from confirmation import simulate_components  # noqa: E402


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


R2 = load_module(
    "transition_weighted_rawtick_v9_r2",
    RESEARCH_ROOT / "r2-downtrend-portability-v2" / "src" / "downtrend.py",
)
TICK_EXECUTION = load_module(
    "transition_weighted_rawtick_v9_execution",
    RESEARCH_ROOT / "macro-transition-rawtick-confirmation-v3" / "src" / "transition.py",
)
PORTFOLIO = load_module(
    "transition_weighted_rawtick_v9_portfolio",
    RESEARCH_ROOT / "transition-weighted-portfolio-v8" / "src" / "portfolio.py",
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
        raise FileNotFoundError("Run lock_contract.py before opening raw outcomes")
    lock = json.loads(path.read_text(encoding="utf-8"))
    if _self_hash(lock) != str(lock["contract_sha256"]):
        raise ValueError("Contract self-hash mismatch")
    for record in (
        lock["package_files"]
        + lock["dependency_files"]
        + lock["source_campaign_files"]
    ):
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
            "# Transition Weighted Raw-Tick Confirmation V9 Result",
            "",
            f"Decision: `{result['decision']}`",
            "",
            f"Candidates: **{result['candidate_rows']}**",
            f"Component trades: **{result['component_trade_rows']}**",
            f"Portfolio trades: **{result['portfolio_trade_rows']}**",
            f"Stress net: **{float(metrics['whole_stress_net_r']):.3f} R**",
            f"Stress PF: **{float(metrics['whole_stress_pf']):.3f}**",
            f"Minimum era PF: **{float(metrics['minimum_era_stress_pf']):.3f}**",
            f"Minimum era average: **{float(metrics['minimum_era_average_stress_r']):.3f} R**",
            f"Closed drawdown: **{float(metrics['whole_closed_drawdown_r']):.3f} R**",
            f"Top five winners removed: **{float(metrics['top_winners_removed_stress_net_r']):.3f} R**",
            f"Economic pass: **{bool(metrics['economic_pass'])}**",
            "",
            "This is selected historical raw-tick evidence, not an independent holdout.",
            "It does not authorize model training or trading.",
            "",
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    config = json.loads(
        (
            ROOT
            / "config"
            / "transition_weighted_rawtick_confirmation_v9.json"
        ).read_text(encoding="utf-8")
    )
    lock = verify_lock(config)
    if args.verify_only:
        print(lock["contract_sha256"])
        return 0
    output = ROOT / config["outputs"]["directory"]
    result_path = output / config["outputs"]["result_json"]
    if result_path.exists():
        raise FileExistsError("V9 raw-tick outcomes already exist")
    candidates = pd.read_parquet(output / config["outputs"]["candidates"])
    tick_store = R2.VerifiedTickStore(R2.storage_root(config), config)
    component_trades, rejections = simulate_components(
        candidates,
        tick_store,
        R2.TickQuote,
        config["execution"],
        TICK_EXECUTION.execute_candidate,
    )
    weights_json = json.dumps(
        config["portfolio"]["weights"], sort_keys=True, separators=(",", ":")
    )
    policy = SimpleNamespace(
        attempt_no=int(config["portfolio"]["confirmation_attempt_no"]),
        portfolio_id="TRANSITION_WEIGHTED_RAWTICK_V9",
        weights_json=weights_json,
        tie_priority=str(config["portfolio"]["tie_priority"]),
    )
    portfolio_trades = PORTFOLIO.build_weighted_trades(
        component_trades,
        policy,
        int(config["execution"]["maximum_trades_per_portfolio_utc_day"]),
    )
    macro_root = (ROOT / config["macro_source_campaign"]["directory"]).resolve()
    source_config = json.loads(
        (macro_root / config["macro_source_campaign"]["config"]).read_text(
            encoding="utf-8"
        )
    )
    load_module("campaign", macro_root / "src" / "campaign.py")
    foundation_module = load_module(
        "transition_weighted_rawtick_v9_run_foundation",
        macro_root / "src" / "foundation.py",
    )
    foundation = foundation_module.load_foundation(source_config)
    score_config = dict(source_config)
    score_config["windows"] = config["windows"]
    score_config["economic_gates"] = config["economic_gates"]
    metrics = foundation_module.SCORE.score_variant(
        portfolio_trades, foundation.execution_frame, score_config
    )
    adjusted = min(
        1.0,
        float(metrics["daily_pvalue"])
        * int(config["portfolio"]["origin_selection_adjustment_count"]),
    )
    component_summary = {
        str(int(attempt)): foundation_module.SCORE.score_variant(
            group, foundation.execution_frame, score_config
        )
        for attempt, group in component_trades.groupby("attempt_no", sort=True)
    }
    decision = (
        "RAW_TICK_TRANSITION_WEIGHTED_V9_ECONOMIC_CANDIDATE_FOUND"
        if bool(metrics["economic_pass"])
        else "NO_RAW_TICK_TRANSITION_WEIGHTED_V9_ECONOMIC_CANDIDATE"
    )
    result = {
        "schema_version": config["schema_version"],
        "contract_sha256": lock["contract_sha256"],
        "decision": decision,
        "origin_attempt_no": int(config["portfolio"]["origin_attempt_no"]),
        "confirmation_attempt_no": int(
            config["portfolio"]["confirmation_attempt_no"]
        ),
        "candidate_rows": int(len(candidates)),
        "component_trade_rows": int(len(component_trades)),
        "portfolio_trade_rows": int(len(portfolio_trades)),
        "selection_adjusted_pvalue": adjusted,
        "component_summary": component_summary,
        "execution_audit": {
            "component_rejections": rejections,
            "stop_slippage_trades": int(
                component_trades["exit_reason"].eq("STOP_SLIPPAGE").sum()
            ),
            "target_trades": int(
                component_trades["exit_reason"].eq("TARGET").sum()
            ),
            "fixed_horizon_trades": int(
                component_trades["exit_reason"].eq("FIXED_HORIZON").sum()
            ),
        },
        "authorization": {
            "selected_after_v8_outcomes": True,
            "raw_tick_result_can_be_independent_holdout": False,
            "independent_replication_required": True,
            "prospective_shadow_required": True,
            "training_authorized": False,
            "execution_authorized": False,
            "research_only": True,
        },
    }
    component_path = output / config["outputs"]["component_trades"]
    portfolio_path = output / config["outputs"]["portfolio_trades"]
    metrics_path = output / config["outputs"]["metrics"]
    markdown_path = output / config["outputs"]["result_markdown"]
    component_trades.to_parquet(component_path, index=False)
    portfolio_trades.to_parquet(portfolio_path, index=False)
    pd.DataFrame(
        [{**metrics, "selection_adjusted_pvalue": adjusted}]
    ).to_csv(metrics_path, index=False, lineterminator="\n")
    write_json(result_path, result)
    markdown_path.write_text(_render(result, metrics), encoding="utf-8")
    names = [
        config["outputs"]["candidates"],
        config["outputs"]["candidate_manifest"],
        config["outputs"]["contract_lock"],
        config["outputs"]["component_trades"],
        config["outputs"]["portfolio_trades"],
        config["outputs"]["metrics"],
        config["outputs"]["result_json"],
        config["outputs"]["result_markdown"],
    ]
    write_json(
        output / config["outputs"]["artifact_manifest"],
        {
            "schema_version": "xauusd_transition_weighted_rawtick_v9_artifacts",
            "files": {
                name: {
                    "bytes": int((output / name).stat().st_size),
                    "sha256": sha256_file(output / name),
                }
                for name in names
            },
        },
    )
    print(json.dumps(_json_value({**result, "metrics": metrics}), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

