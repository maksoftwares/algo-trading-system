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


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


DATA = load_module(
    "chop_micro_anti_v17_run_data",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "data.py",
)
REGIMES = load_module(
    "chop_micro_anti_v17_run_regimes",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "research.py",
)
MICRO = load_module(
    "chop_micro_anti_v17_run_micro",
    RESEARCH_ROOT / "m5-microstructure-mechanics-v1" / "src" / "campaign.py",
)
BASE = load_module(
    "chop_micro_anti_v17_run_base",
    RESEARCH_ROOT / "regime-mechanism-campaign-v1" / "src" / "campaign.py",
)
CAMPAIGN = load_module(
    "chop_micro_anti_v17_run_campaign", ROOT / "src" / "campaign.py"
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
        raise FileNotFoundError("Run lock_contract.py before opening outcomes")
    lock = json.loads(path.read_text(encoding="utf-8"))
    if _self_hash(lock) != str(lock["contract_sha256"]):
        raise ValueError("Contract self-hash mismatch")
    for record in lock["package_files"] + lock["dependency_files"]:
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
        "# Chop Microstructure Anti-Signal Campaign V17 Result",
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
            "Every policy is paired to V16 with native M5 direction reversed.",
            "Signals, H4 chop ownership, execution, costs, and gates remain paired.",
            "Historical discovery evidence does not authorize training or trading.",
        )
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    config = json.loads(
        (
            ROOT / "config" / "chop_microstructure_antisignal_v17.json"
        ).read_text(
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
        raise FileExistsError("V17 outcomes already exist")
    manifest = pd.read_csv(output / config["outputs"]["manifest"])
    bundle = DATA.load_bundle(config)
    frame = CAMPAIGN.prepare_frame(
        bundle.bars["M5"], bundle.bars["H4"], config, MICRO, REGIMES
    )
    frame["entry_time_key"] = frame["bar_start_utc"].shift(-1)
    arrays = CAMPAIGN.execution_arrays(frame)
    cache: dict[tuple[Any, ...], dict[str, Any] | None] = {}
    rows: list[dict[str, Any]] = []
    for offset, item in enumerate(manifest.itertuples(index=False), 1):
        trades = CAMPAIGN.simulate_variant(frame, arrays, item, config, cache)
        score = BASE.score_variant(trades, frame, config)
        rows.append({**item._asdict(), **score})
        if offset % 100 == 0:
            print(f"scored={offset}/{len(manifest)} outcomes={len(cache)}", flush=True)
    metrics = pd.DataFrame(rows)
    metrics["daily_fdr_qvalue"] = BASE.bh_adjust(metrics["daily_pvalue"])
    metrics["statistical_pass"] = metrics["daily_fdr_qvalue"].le(
        float(config["selection"]["false_discovery_rate"])
    )
    shortlist = _shortlist(
        metrics, int(config["selection"]["maximum_finalists_per_mechanic"])
    )
    manifest_by_attempt = manifest.set_index("attempt_no")
    selected_frames: list[pd.DataFrame] = []
    for attempt in shortlist["attempt_no"]:
        item = manifest_by_attempt.loc[int(attempt)]
        selected_frames.append(
            CAMPAIGN.simulate_variant(
                frame,
                arrays,
                type("Policy", (), {**item.to_dict(), "attempt_no": int(attempt)})(),
                config,
                cache,
            )
        )
    selected_trades = pd.concat(selected_frames, ignore_index=True)
    economic = metrics.loc[metrics["economic_pass"]]
    fdr = economic.loc[economic["statistical_pass"]]
    decision = (
        "CHOP_MICROSTRUCTURE_ANTISIGNAL_V17_FDR_FINALIST_FOUND"
        if not fdr.empty
        else (
            "CHOP_MICROSTRUCTURE_ANTISIGNAL_V17_ECONOMIC_FINALIST_FOUND"
            if not economic.empty
            else "NO_CHOP_MICROSTRUCTURE_ANTISIGNAL_V17_ECONOMIC_FINALIST"
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
        "paired_source_attempt_first": int(
            config["selection"]["paired_source_attempt_first"]
        ),
        "paired_source_attempt_last": int(
            config["selection"]["paired_source_attempt_last"]
        ),
        "attempts_completed": int(len(metrics)),
        "cumulative_campaign_attempts": int(config["selection"]["attempt_last"]),
        "economic_finalist_count": int(len(economic)),
        "fdr_finalist_count": int(len(fdr)),
        "economic_finalist_attempts": [int(value) for value in economic["attempt_no"]],
        "fdr_finalist_attempts": [int(value) for value in fdr["attempt_no"]],
        "cached_outcomes": int(len(cache)),
        "mechanic_summary": mechanic_summary,
        "data_evidence": bundle.evidence,
        "authorization": {
            "historical_discovery_only": True,
            "raw_tick_confirmation_required": True,
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
            "schema_version": "xauusd_chop_microstructure_antisignal_v17_artifacts",
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
