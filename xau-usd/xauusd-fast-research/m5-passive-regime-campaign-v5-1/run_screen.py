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
V5_ROOT = RESEARCH_ROOT / "m5-passive-regime-campaign-v5"
sys.path.insert(0, str(ROOT / "src"))

from clock import (  # noqa: E402
    activation_gaps_minutes,
    load_config,
    m5_execution_arrays,
    utc_nanoseconds,
)


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PASSIVE = load_module("m5_passive_v51_base", V5_ROOT / "src" / "passive.py")
V5RUN = load_module("m5_passive_v51_runner_base", V5_ROOT / "run_screen.py")
R2 = V5RUN.R2
DATA = V5RUN.DATA
TARGET = V5RUN.TARGET
REGIMES = V5RUN.REGIMES
ADAPTIVE = V5RUN.ADAPTIVE
BASE = V5RUN.BASE


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
        raise ValueError(f"{label} path escaped its root: {path}") from exc
    if not path.is_file():
        raise FileNotFoundError(path)
    if int(path.stat().st_size) != int(record["bytes"]):
        raise ValueError(f"{label} size mismatch: {record['path']}")
    if R2.sha256_file(path) != str(record["sha256"]):
        raise ValueError(f"{label} hash mismatch: {record['path']}")


def verify_lock(config: dict[str, Any]) -> dict[str, Any]:
    output = ROOT / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    if not lock_path.is_file():
        raise FileNotFoundError("Run lock_contract.py before opening outcomes")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if _self_hash(lock) != str(lock["contract_sha256"]):
        raise ValueError("Contract self-hash mismatch")
    for record in lock["package_files"] + lock["dependency_files"]:
        _verify_record(record, REPO, "repository")
    storage = Path(
        os.environ.get(
            str(config["source"]["storage_environment_variable"]),
            str(config["source"]["default_storage_root"]),
        )
    ).resolve()
    for record in lock["external_files"]:
        _verify_record(record, storage, "external")
    manifest_path = output / config["outputs"]["manifest"]
    if R2.sha256_file(manifest_path) != str(lock["manifest_sha256"]):
        raise ValueError("Manifest changed after lock")
    if len(pd.read_csv(manifest_path)) != int(lock["attempt_count"]):
        raise ValueError("Manifest count differs from lock")
    return lock


def _json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
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
        json.dumps(_json_value(payload), indent=2, sort_keys=True, ensure_ascii=True)
        + "\n",
        encoding="utf-8",
    )


def _render(result: dict[str, Any], shortlist: pd.DataFrame) -> str:
    lines = [
        "# XAUUSD M5 Passive Regime Campaign V5.1 Result",
        "",
        f"Decision: `{result['decision']}`",
        "",
        f"Attempts completed: **{result['attempts_completed']}**",
        f"Economic finalists: **{result['economic_finalist_rows']}**",
        f"FDR-supported finalists: **{result['statistical_finalist_rows']}**",
        "",
        "Historical outcomes are discovery evidence. No result authorizes training or execution.",
        "",
        "## Regime summary",
        "",
        "| Owner | Attempts | Economic passes | FDR passes | Best min-era PF |",
        "|---|---:|---:|---:|---:|",
    ]
    for item in result["regime_summary"]:
        lines.append(
            f"| {item['regime_owner']} | {item['attempts']} | {item['economic_passes']} | "
            f"{item['statistical_passes']} | {item['best_minimum_era_stress_pf']:.3f} |"
        )
    lines.extend(["", "## Economic finalists", ""])
    if shortlist.empty:
        lines.append("No definition passed every registered economic gate.")
    else:
        lines.extend(
            [
                "| Attempt | Owner | Mechanic | Trades | PF | Min-era PF | Min-era N | FDR q |",
                "|---:|---|---|---:|---:|---:|---:|---:|",
            ]
        )
        for row in shortlist.itertuples(index=False):
            lines.append(
                f"| {int(row.attempt_no)} | {row.regime_owner} | {row.mechanic} | "
                f"{int(row.whole_trades)} | {float(row.whole_stress_pf):.3f} | "
                f"{float(row.minimum_era_stress_pf):.3f} | {int(row.minimum_era_trades)} | "
                f"{float(row.daily_fdr_qvalue):.6f} |"
            )
    return "\n".join(lines) + "\n"


def _artifact_manifest(directory: Path, names: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "xauusd_m5_passive_regime_v5_1_artifacts",
        "files": {
            name: {
                "bytes": int((directory / name).stat().st_size),
                "sha256": R2.sha256_file(directory / name),
            }
            for name in names
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    config = load_config(ROOT)
    lock = verify_lock(config)
    if args.verify_only:
        print(lock["contract_sha256"])
        return 0
    output = ROOT / config["outputs"]["directory"]
    result_path = output / config["outputs"]["result_json"]
    if result_path.exists():
        raise FileExistsError("V5.1 outcomes already exist; same-version reruns are forbidden")

    manifest = pd.read_csv(output / config["outputs"]["manifest"])
    m5, evidence = R2.load_continuous_m5(config)
    m15 = DATA.aggregate_complete_bars(m5, 15, "M15")
    h4 = DATA.aggregate_complete_bars(m5, 240, "H4")
    frame = TARGET.prepare_features(m15, h4, config, ADAPTIVE, REGIMES)
    frame = PASSIVE.prepare_passive_features(frame)
    arrays = m5_execution_arrays(m5)
    decisions_ns = utc_nanoseconds(frame["timestamp_utc"])
    gaps = activation_gaps_minutes(arrays, decisions_ns)
    finite_gaps = gaps[np.isfinite(gaps)]
    if len(finite_gaps) == 0 or np.min(finite_gaps) < 0.0:
        raise ValueError("Invalid pending-order activation gap after normalization")

    outcome_cache: dict[tuple[Any, ...], dict[str, Any] | None] = {}
    rows: list[dict[str, Any]] = []
    for offset, manifest_row in enumerate(manifest.itertuples(index=False), 1):
        trades = PASSIVE.simulate_variant(
            frame,
            arrays,
            manifest_row,
            config["execution"],
            config["passive_execution"],
            outcome_cache,
        )
        metrics = BASE.score_variant(trades, frame, config)
        rows.append(
            {
                "attempt_no": int(manifest_row.attempt_no),
                "variant_id": str(manifest_row.variant_id),
                "regime_owner": str(manifest_row.regime_owner),
                "mechanic": str(manifest_row.mechanic),
                "parameters_json": str(manifest_row.parameters_json),
                **metrics,
            }
        )
        if offset % 25 == 0:
            print(f"scored={offset}/{len(manifest)} outcomes={len(outcome_cache)}", flush=True)

    metrics = pd.DataFrame(rows)
    metrics["daily_fdr_qvalue"] = BASE.bh_adjust(metrics["daily_pvalue"])
    metrics["statistical_pass"] = metrics["daily_fdr_qvalue"].le(
        float(config["selection"]["false_discovery_rate"])
    )
    finalists = metrics.loc[metrics["economic_pass"]].copy().sort_values(
        [
            "daily_fdr_qvalue",
            "minimum_era_stress_pf",
            "whole_stress_pf",
            "whole_trades",
            "attempt_no",
        ],
        ascending=[True, False, False, False, True],
        kind="mergesort",
    )
    maximum = int(config["selection"]["maximum_economic_finalists_per_mechanic"])
    shortlist = finalists.groupby("mechanic", sort=True).head(maximum).copy()
    regime_summary = []
    for owner, group in metrics.groupby("regime_owner", sort=True):
        regime_summary.append(
            {
                "regime_owner": owner,
                "attempts": int(len(group)),
                "economic_passes": int(group["economic_pass"].sum()),
                "statistical_passes": int(
                    (group["economic_pass"] & group["statistical_pass"]).sum()
                ),
                "best_minimum_era_stress_pf": float(
                    group["minimum_era_stress_pf"].max()
                ),
            }
        )
    statistical_finalists = int(
        (metrics["economic_pass"] & metrics["statistical_pass"]).sum()
    )
    decision = (
        "FDR_SUPPORTED_EXACT_TICK_FINALISTS_FOUND"
        if statistical_finalists > 0
        else (
            "ECONOMIC_ONLY_EXACT_TICK_FINALISTS_FOUND"
            if not shortlist.empty
            else "NO_M5_PASSIVE_REGIME_V5_1_ECONOMIC_FINALIST"
        )
    )
    result = {
        "schema_version": config["schema_version"],
        "contract_sha256": lock["contract_sha256"],
        "decision": decision,
        "attempt_first": int(manifest["attempt_no"].min()),
        "attempt_last": int(manifest["attempt_no"].max()),
        "attempts_completed": int(len(metrics)),
        "cumulative_campaign_attempts": int(manifest["attempt_no"].max()),
        "cached_pending_outcomes": int(len(outcome_cache)),
        "economic_pass_rows": int(metrics["economic_pass"].sum()),
        "economic_finalist_rows": int(len(shortlist)),
        "statistical_finalist_rows": statistical_finalists,
        "regime_summary": regime_summary,
        "clock_audit": {
            "unit": "ns",
            "finite_activation_gaps": int(len(finite_gaps)),
            "out_of_bounds_decisions": int(np.sum(~np.isfinite(gaps))),
            "negative_activation_gaps": int(np.sum(finite_gaps < 0.0)),
            "zero_activation_gaps": int(np.sum(finite_gaps == 0.0)),
            "maximum_activation_gap_minutes": float(np.max(finite_gaps)),
        },
        "fill_contract": config["passive_execution"],
        "data_evidence": {
            **evidence,
            "m5_rows": int(len(m5)),
            "m15_rows": int(len(m15)),
            "h4_rows": int(len(h4)),
            "feature_rows": int(len(frame)),
            "first_feature_time": frame["timestamp_utc"].min().isoformat(),
            "last_feature_time": frame["timestamp_utc"].max().isoformat(),
        },
        "authorization": {
            "historical_periods_are_discovery_only": True,
            "exact_tick_confirmation_required": True,
            "prospective_shadow_required": True,
            "training_authorized": False,
            "execution_authorized": False,
            "research_only": True,
        },
    }

    metrics_path = output / config["outputs"]["metrics"]
    shortlist_path = output / config["outputs"]["shortlist"]
    markdown_path = output / config["outputs"]["result_markdown"]
    metrics.to_csv(metrics_path, index=False, lineterminator="\n")
    shortlist.to_csv(shortlist_path, index=False, lineterminator="\n")
    write_json(result_path, result)
    markdown_path.write_text(_render(result, shortlist), encoding="utf-8")
    names = [
        config["outputs"]["contract_lock"],
        config["outputs"]["manifest"],
        config["outputs"]["metrics"],
        config["outputs"]["shortlist"],
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
