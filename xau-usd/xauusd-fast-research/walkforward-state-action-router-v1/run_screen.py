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

from router import (  # noqa: E402
    decision_indices,
    label_geometry,
    select_trades,
    state_codes,
    walkforward_statistics,
)


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


R2 = load_module(
    "state_action_router_runner_r2",
    RESEARCH_ROOT / "r2-downtrend-portability-v2" / "src" / "downtrend.py",
)
DATA = load_module(
    "state_action_router_runner_data",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "data.py",
)
REGIMES = load_module(
    "state_action_router_runner_regimes",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "research.py",
)
ADAPTIVE = load_module(
    "state_action_router_runner_adaptive",
    RESEARCH_ROOT / "adaptive-h4-specialists-v1" / "src" / "adaptive.py",
)
FEATURES = load_module(
    "state_action_router_runner_features",
    RESEARCH_ROOT / "m15-regime-target-campaign-v1" / "src" / "campaign.py",
)
CLOCK = load_module(
    "state_action_router_runner_clock",
    RESEARCH_ROOT / "m15-regime-target-campaign-v2" / "src" / "correction.py",
)
SCORE = load_module(
    "state_action_router_runner_score",
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
        raise ValueError("Manifest row count differs from lock")
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


def _artifact_manifest(directory: Path, names: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "xauusd_walkforward_state_action_router_v1_artifacts",
        "files": {
            name: {
                "bytes": int((directory / name).stat().st_size),
                "sha256": R2.sha256_file(directory / name),
            }
            for name in names
        },
    }


def _render(result: dict[str, Any], shortlist: pd.DataFrame) -> str:
    lines = [
        "# XAUUSD Walk-Forward State/Action Router V1 Result",
        "",
        f"Decision: `{result['decision']}`",
        "",
        f"Attempts completed: **{result['attempts_completed']}**",
        f"Economic pass rows: **{result['economic_pass_rows']}**",
        f"Economic shortlist rows: **{result['economic_shortlist_rows']}**",
        f"FDR-supported shortlist rows: **{result['statistical_finalist_rows']}**",
        "",
        "All reported trades are purged walk-forward OOS decisions. Historical periods remain discovery evidence.",
        "No result authorizes training or execution.",
        "",
        "## Regime summary",
        "",
        "| Owner | Attempts | Economic passes | FDR passes | Best min-era PF | Best total PF |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in result["regime_summary"]:
        lines.append(
            f"| {item['regime_owner']} | {item['attempts']} | {item['economic_passes']} | "
            f"{item['fdr_economic_passes']} | {item['best_minimum_era_stress_pf']:.3f} | "
            f"{item['best_whole_stress_pf']:.3f} |"
        )
    lines.extend(["", "## Shortlist", ""])
    if shortlist.empty:
        lines.append("No policy passed every registered economic gate.")
    else:
        lines.extend(
            [
                "| Attempt | Owner | Schema | Geometry | Trades | PF | Min-era PF | FDR q |",
                "|---:|---|---|---|---:|---:|---:|---:|",
            ]
        )
        for row in shortlist.itertuples(index=False):
            lines.append(
                f"| {int(row.attempt_no)} | {row.regime_owner} | {row.schema_id} | "
                f"{row.geometry_id} | {int(row.whole_trades)} | "
                f"{float(row.whole_stress_pf):.3f} | "
                f"{float(row.minimum_era_stress_pf):.3f} | "
                f"{float(row.daily_fdr_qvalue):.6f} |"
            )
    lines.extend(
        [
            "",
            "## Authorization boundary",
            "",
            "Only an economic and FDR survivor may proceed to separately locked exact raw-tick confirmation. Shock remains abstain.",
        ]
    )
    return "\n".join(lines) + "\n"


def _policy_dict(row: Any) -> dict[str, Any]:
    return {
        "minimum_cell_rows": int(row.minimum_cell_rows),
        "prior_strength": float(row.prior_strength),
        "lcb_z": float(row.lcb_z),
        "minimum_lcb_r": float(row.minimum_lcb_r),
        "minimum_action_gap_r": float(row.minimum_action_gap_r),
        "maximum_trades_per_utc_day": int(row.maximum_trades_per_utc_day),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    config = json.loads(
        (ROOT / "config" / "walkforward_state_action_router_v1.json").read_text(
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
        raise FileExistsError(
            "V1 outcomes already exist; same-version reruns are forbidden"
        )

    manifest = pd.read_csv(output / config["outputs"]["manifest"])
    m5, evidence = R2.load_continuous_m5(config)
    m15 = DATA.aggregate_complete_bars(m5, 15, "M15")
    h4 = DATA.aggregate_complete_bars(m5, 240, "H4")
    frame = FEATURES.prepare_features(m15, h4, config, ADAPTIVE, REGIMES)
    arrays = CLOCK.execution_arrays(frame)
    next_gaps = (arrays["starts"][1:] - arrays["signals"][:-1]) / 60_000_000_000
    if np.any(next_gaps < 0.0):
        raise ValueError("Negative next-bar gap after nanosecond normalization")
    oos_start = pd.Timestamp(config["walk_forward"]["oos_start_utc"])
    oos_end = pd.Timestamp(config["walk_forward"]["oos_end_exclusive_utc"])
    frame_oos = frame.loc[
        pd.to_datetime(frame["timestamp_utc"], utc=True).ge(oos_start)
        & pd.to_datetime(frame["timestamp_utc"], utc=True).lt(oos_end)
    ].copy()

    metric_rows: list[dict[str, Any]] = []
    selected_economic: list[pd.DataFrame] = []
    diagnostic_rows: list[dict[str, Any]] = []
    label_evidence: list[dict[str, Any]] = []
    for owner in config["owners"]:
        signals = decision_indices(frame, owner, config)
        owner_manifest = manifest.loc[manifest["regime_owner"].eq(owner)]
        for geometry_id, geometry in config["geometries"][owner].items():
            geometry_manifest = owner_manifest.loc[
                owner_manifest["geometry_id"].eq(geometry_id)
            ]
            if geometry_manifest.empty:
                continue
            labels = label_geometry(
                arrays,
                signals,
                owner,
                geometry_id,
                geometry,
                config["execution"],
            )
            if labels.empty:
                raise ValueError(f"No labels for {owner}/{geometry_id}")
            label_evidence.append(
                {
                    "regime_owner": owner,
                    "geometry_id": geometry_id,
                    "decision_rows": int(len(signals)),
                    "paired_action_rows": int(len(labels)),
                    "paired_decisions": int(len(labels) // 2),
                    "first_signal_time": labels["signal_time"].min(),
                    "last_signal_time": labels["signal_time"].max(),
                }
            )
            signal_index = labels["signal_index"].to_numpy(dtype=np.int64)
            direction = labels["direction_sign"].to_numpy(dtype=np.int32)
            for schema_id in config["schemas"][owner]:
                schema_manifest = geometry_manifest.loc[
                    geometry_manifest["schema_id"].eq(schema_id)
                ]
                if schema_manifest.empty:
                    continue
                codes, state_count = state_codes(
                    frame, signal_index, direction, owner, schema_id, config
                )
                for history_mode in config["walk_forward"]["history_modes"]:
                    policies = schema_manifest.loc[
                        schema_manifest["history_mode"].eq(history_mode)
                    ]
                    if policies.empty:
                        continue
                    stats, fold_diagnostics = walkforward_statistics(
                        labels, codes, state_count, history_mode, config
                    )
                    for item in fold_diagnostics:
                        diagnostic_rows.append(
                            {
                                "regime_owner": owner,
                                "geometry_id": geometry_id,
                                "schema_id": schema_id,
                                "history_mode": history_mode,
                                "state_count": state_count,
                                **item,
                            }
                        )
                    for policy_row in policies.itertuples(index=False):
                        policy = _policy_dict(policy_row)
                        selected, diagnostics = select_trades(
                            labels, stats, policy, config
                        )
                        metrics = SCORE.score_variant(selected, frame_oos, config)
                        metric_rows.append(
                            {
                                **policy_row._asdict(),
                                "state_count": state_count,
                                **diagnostics,
                                **metrics,
                            }
                        )
                        if bool(metrics["economic_pass"]):
                            opened = selected.copy()
                            opened["attempt_no"] = int(policy_row.attempt_no)
                            opened["variant_id"] = str(policy_row.variant_id)
                            opened["schema_id"] = schema_id
                            opened["history_mode"] = history_mode
                            selected_economic.append(opened)
            print(
                f"labeled owner={owner} geometry={geometry_id} "
                f"paired_decisions={len(labels) // 2} scored={len(metric_rows)}/1000",
                flush=True,
            )

    metrics = pd.DataFrame(metric_rows).sort_values("attempt_no", kind="mergesort")
    if len(metrics) != int(config["selection"]["total_attempts"]):
        raise ValueError(f"Expected 1,000 scored policies, found {len(metrics)}")
    metrics["daily_fdr_qvalue"] = SCORE.bh_adjust(metrics["daily_pvalue"])
    metrics["statistical_pass"] = metrics["daily_fdr_qvalue"].le(
        float(config["selection"]["false_discovery_rate"])
    )
    economic = (
        metrics.loc[metrics["economic_pass"]]
        .copy()
        .sort_values(
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
    )
    maximum = int(config["selection"]["maximum_finalists_per_schema"])
    shortlist = economic.groupby(["regime_owner", "schema_id"], sort=True).head(maximum)
    fdr_shortlist = shortlist.loc[shortlist["statistical_pass"]]
    if not fdr_shortlist.empty:
        decision = "WALKFORWARD_STATE_ACTION_FDR_FINALISTS_FOUND"
    elif not shortlist.empty:
        decision = "WALKFORWARD_STATE_ACTION_ECONOMIC_ONLY_FINALISTS_FOUND"
    else:
        decision = "NO_WALKFORWARD_STATE_ACTION_ROUTER_V1_ECONOMIC_FINALIST"

    if selected_economic:
        selected = pd.concat(selected_economic, ignore_index=True)
        selected = selected.loc[
            selected["attempt_no"].isin(shortlist["attempt_no"])
        ].sort_values(["attempt_no", "entry_time"], kind="mergesort")
    else:
        selected = pd.DataFrame(
            columns=[
                "attempt_no",
                "variant_id",
                "schema_id",
                "signal_time",
                "entry_time",
                "exit_time",
                "direction",
                "stress_net_r",
            ]
        )
    diagnostics_frame = pd.DataFrame(diagnostic_rows)
    regime_summary = []
    for owner, group in metrics.groupby("regime_owner", sort=True):
        economic_mask = group["economic_pass"].astype(bool)
        regime_summary.append(
            {
                "regime_owner": owner,
                "attempts": int(len(group)),
                "economic_passes": int(economic_mask.sum()),
                "fdr_economic_passes": int(
                    (economic_mask & group["statistical_pass"].astype(bool)).sum()
                ),
                "best_minimum_era_stress_pf": float(
                    group["minimum_era_stress_pf"].max()
                ),
                "best_whole_stress_pf": float(group["whole_stress_pf"].max()),
                "maximum_oos_trades": int(group["whole_trades"].max()),
            }
        )
    result = {
        "schema_version": config["schema_version"],
        "contract_sha256": lock["contract_sha256"],
        "decision": decision,
        "attempt_first": int(metrics["attempt_no"].min()),
        "attempt_last": int(metrics["attempt_no"].max()),
        "attempts_completed": int(len(metrics)),
        "cumulative_campaign_attempts": int(metrics["attempt_no"].max()),
        "economic_pass_rows": int(metrics["economic_pass"].sum()),
        "economic_shortlist_rows": int(len(shortlist)),
        "statistical_finalist_rows": int(len(fdr_shortlist)),
        "regime_summary": regime_summary,
        "label_evidence": label_evidence,
        "clock_audit": {
            "unit": "ns",
            "negative_next_bar_gaps": int(np.sum(next_gaps < 0.0)),
            "zero_next_bar_gaps": int(np.sum(next_gaps == 0.0)),
            "minimum_next_bar_gap_minutes": float(next_gaps.min()),
            "maximum_next_bar_gap_minutes": float(next_gaps.max()),
        },
        "data_evidence": {
            **evidence,
            "m15_rows": int(len(m15)),
            "h4_rows": int(len(h4)),
            "feature_rows": int(len(frame)),
            "first_feature_time": frame["timestamp_utc"].min(),
            "last_feature_time": frame["timestamp_utc"].max(),
        },
        "authorization": {
            "historical_periods_are_discovery_only": True,
            "exact_raw_tick_confirmation_required": True,
            "implementation_parity_required": True,
            "prospective_shadow_required": True,
            "shock_is_abstain": True,
            "training_authorized": False,
            "execution_authorized": False,
            "research_only": True,
        },
    }

    metrics_path = output / config["outputs"]["metrics"]
    shortlist_path = output / config["outputs"]["shortlist"]
    selected_path = output / config["outputs"]["selected_trades"]
    diagnostics_path = output / config["outputs"]["diagnostics"]
    markdown_path = output / config["outputs"]["result_markdown"]
    metrics.to_csv(metrics_path, index=False, lineterminator="\n")
    shortlist.to_csv(shortlist_path, index=False, lineterminator="\n")
    selected.to_csv(selected_path, index=False, lineterminator="\n")
    diagnostics_frame.to_csv(diagnostics_path, index=False, lineterminator="\n")
    write_json(result_path, result)
    markdown_path.write_text(_render(result, shortlist), encoding="utf-8")
    names = [
        config["outputs"]["contract_lock"],
        config["outputs"]["manifest"],
        config["outputs"]["metrics"],
        config["outputs"]["shortlist"],
        config["outputs"]["selected_trades"],
        config["outputs"]["diagnostics"],
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
