from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from composite import build_composite_trades, simulate_components  # noqa: E402


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


R2 = load_module(
    "regime_composite_run_r2",
    RESEARCH_ROOT / "r2-downtrend-portability-v2" / "src" / "downtrend.py",
)
DATA = load_module(
    "regime_composite_run_data",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "data.py",
)
REGIMES = load_module(
    "regime_composite_run_regimes",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "research.py",
)
ADAPTIVE = load_module(
    "regime_composite_run_adaptive",
    RESEARCH_ROOT / "adaptive-h4-specialists-v1" / "src" / "adaptive.py",
)
V1 = load_module(
    "regime_composite_run_v1",
    RESEARCH_ROOT / "regime-mechanism-campaign-v1" / "src" / "campaign.py",
)


def _self_hash(payload: dict[str, Any]) -> str:
    work = dict(payload)
    work.pop("contract_sha256", None)
    encoded = json.dumps(
        work, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _verify_record(record: dict[str, Any], base: Path, label: str) -> None:
    path = (base / str(record["path"])).resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} path escaped root: {path}") from exc
    if not path.is_file():
        raise FileNotFoundError(path)
    if int(path.stat().st_size) != int(record["bytes"]):
        raise ValueError(f"{label} size mismatch: {record['path']}")
    if R2.sha256_file(path) != str(record["sha256"]):
        raise ValueError(f"{label} hash mismatch: {record['path']}")


def verify_lock(config: dict[str, Any]) -> dict[str, Any]:
    output = ROOT / config["outputs"]["directory"]
    path = output / config["outputs"]["contract_lock"]
    if not path.is_file():
        raise FileNotFoundError("Run lock_contract.py before raw outcomes")
    lock = json.loads(path.read_text(encoding="utf-8"))
    if _self_hash(lock) != str(lock["contract_sha256"]):
        raise ValueError("Contract self-hash mismatch")
    for record in lock["package_files"] + lock["dependency_files"]:
        _verify_record(record, REPO, "repository")
    _verify_record(lock["candidate_file"], REPO, "candidate")
    _verify_record(lock["candidate_manifest"], REPO, "candidate manifest")
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
    path.write_text(
        json.dumps(
            _json_value(payload), indent=2, sort_keys=True, ensure_ascii=True
        )
        + "\n",
        encoding="utf-8",
    )


def _artifact_manifest(directory: Path, names: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "xauusd_regime_composite_rawtick_v1_artifacts",
        "files": {
            name: {
                "bytes": int((directory / name).stat().st_size),
                "sha256": R2.sha256_file(directory / name),
            }
            for name in names
        },
    }


def _render(result: dict[str, Any], metrics: pd.DataFrame) -> str:
    lines = [
        "# XAUUSD Regime Composite Raw-Tick V1 Result",
        "",
        f"Decision: `{result['decision']}`",
        "",
        f"Candidates: **{result['candidate_rows']}**",
        f"Accepted component trades: **{result['component_trade_rows']}**",
        f"Accepted composite trades: **{result['composite_trade_rows']}**",
        "",
        "This is a post-selection execution diagnostic on exposed history, not an independent holdout.",
        "No result is authorized for model training or trading.",
        "",
        "| Type | Policy | Trades | PF | Min-era PF | Avg R | DD R | Top-5 removed R | Economic pass | Adjusted p |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for row in metrics.itertuples(index=False):
        lines.append(
            f"| {row.row_type} | {row.policy_id} | {int(row.whole_trades)} | "
            f"{float(row.whole_stress_pf):.3f} | {float(row.minimum_era_stress_pf):.3f} | "
            f"{float(row.whole_average_stress_r):.3f} | {float(row.whole_closed_drawdown_r):.3f} | "
            f"{float(row.top_winners_removed_stress_net_r):.3f} | {bool(row.economic_pass)} | "
            f"{float(row.selection_adjusted_pvalue):.6f} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    config = json.loads(
        (ROOT / "config" / "regime_composite_rawtick_v1.json").read_text(
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
        raise FileExistsError("Raw V1 outcomes already exist")
    candidates = pd.read_parquet(output / config["outputs"]["candidates"])
    storage = R2.storage_root(config)
    tick_store = R2.VerifiedTickStore(storage, config)
    component_trades, rejections = simulate_components(
        candidates, tick_store, R2.TickQuote, config["execution"]
    )
    composite_trades = build_composite_trades(component_trades, config)

    m5, evidence = R2.load_continuous_m5(config)
    h1 = DATA.aggregate_complete_bars(m5, 60, "H1")
    h4 = DATA.aggregate_complete_bars(m5, 240, "H4")
    frame = V1.prepare_features(h1, h4, config, ADAPTIVE, REGIMES)
    rows: list[dict[str, Any]] = []
    for attempt, trades in component_trades.groupby("origin_attempt", sort=True):
        score = V1.score_variant(trades, frame, config)
        rows.append(
            {
                "row_type": "COMPONENT",
                "policy_id": f"ORIGIN_{int(attempt)}",
                "attempt_no": int(attempt),
                "regime_owner": str(trades["regime_owner"].iat[0]),
                "subset_search_count": 1,
                "selection_adjusted_pvalue": float(score["daily_pvalue"]),
                **score,
            }
        )
    economic_composites: list[str] = []
    for composite in config["composites"]:
        policy_id = str(composite["composite_id"])
        trades = composite_trades.loc[
            composite_trades["composite_id"].eq(policy_id)
        ]
        score = V1.score_variant(trades, frame, config)
        adjusted = min(
            1.0,
            float(score["daily_pvalue"])
            * int(composite["subset_search_count"]),
        )
        rows.append(
            {
                "row_type": "COMPOSITE",
                "policy_id": policy_id,
                "attempt_no": int(composite["attempt_no"]),
                "regime_owner": str(composite["regime_owner"]),
                "subset_search_count": int(composite["subset_search_count"]),
                "selection_adjusted_pvalue": adjusted,
                **score,
            }
        )
        if bool(score["economic_pass"]):
            economic_composites.append(policy_id)
    metrics = pd.DataFrame(rows).sort_values(
        ["row_type", "attempt_no"], kind="mergesort"
    )
    decision = (
        "RAW_TICK_ECONOMIC_COMPOSITE_FOUND"
        if economic_composites
        else "NO_RAW_TICK_ECONOMIC_COMPOSITE"
    )
    result = {
        "schema_version": config["schema_version"],
        "contract_sha256": lock["contract_sha256"],
        "decision": decision,
        "attempt_first": int(config["selection"]["attempt_first"]),
        "attempt_last": int(config["selection"]["attempt_last"]),
        "cumulative_campaign_attempts": int(
            config["selection"]["cumulative_campaign_attempts"]
        ),
        "candidate_rows": int(len(candidates)),
        "component_trade_rows": int(len(component_trades)),
        "composite_trade_rows": int(len(composite_trades)),
        "economic_composite_ids": economic_composites,
        "execution_audit": {
            "rejections": rejections,
            "stop_slippage_trades": int(
                component_trades["exit_reason"].eq("STOP_SLIPPAGE").sum()
            )
            if not component_trades.empty
            else 0,
            "exact_stop_trades": int(
                component_trades["exit_reason"].eq("STOP").sum()
            )
            if not component_trades.empty
            else 0,
            "fixed_horizon_trades": int(
                component_trades["exit_reason"].eq("FIXED_HORIZON").sum()
            )
            if not component_trades.empty
            else 0,
            "maximum_horizon_delay_minutes": float(
                component_trades["horizon_delay_minutes"].max()
            )
            if not component_trades.empty
            else 0.0,
        },
        "data_evidence": evidence,
        "authorization": {
            "selected_after_v1_outcomes": True,
            "raw_tick_result_can_be_independent_holdout": False,
            "prospective_shadow_required": True,
            "training_authorized": False,
            "execution_authorized": False,
            "research_only": True,
        },
    }

    component_path = output / config["outputs"]["component_trades"]
    composite_path = output / config["outputs"]["composite_trades"]
    metrics_path = output / config["outputs"]["metrics"]
    markdown_path = output / config["outputs"]["result_markdown"]
    component_trades.to_parquet(component_path, index=False)
    composite_trades.to_parquet(composite_path, index=False)
    metrics.to_csv(metrics_path, index=False, lineterminator="\n")
    write_json(result_path, result)
    markdown_path.write_text(_render(result, metrics), encoding="utf-8")
    names = [
        config["outputs"]["candidates"],
        config["outputs"]["candidate_manifest"],
        config["outputs"]["contract_lock"],
        config["outputs"]["component_trades"],
        config["outputs"]["composite_trades"],
        config["outputs"]["metrics"],
        config["outputs"]["result_json"],
        config["outputs"]["result_markdown"],
    ]
    write_json(
        output / config["outputs"]["artifact_manifest"],
        _artifact_manifest(output, names),
    )
    print(json.dumps(_json_value(result), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

