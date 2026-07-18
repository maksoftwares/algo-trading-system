from __future__ import annotations

from datetime import UTC, datetime
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
OUTPUT = ROOT / "outputs"
CONFIG_PATH = ROOT / "config" / "out_of_era_breakout_independence_v2.json"
FINAL_LOCK_PATH = OUTPUT / "OUT_OF_ERA_BREAKOUT_FINAL_CONTRACT_LOCK.json"
MARKER_PATH = OUTPUT / "OUT_OF_ERA_BREAKOUT_OUTCOMES_OPENED.json"
METRICS_PATH = OUTPUT / "OUT_OF_ERA_BREAKOUT_METRICS.csv"
TRADES_PATH = OUTPUT / "OUT_OF_ERA_BREAKOUT_TRADES.csv"
PAIRWISE_PATH = OUTPUT / "OUT_OF_ERA_BREAKOUT_INDEPENDENCE.csv"
RESULT_PATH = OUTPUT / "OUT_OF_ERA_BREAKOUT_RESULT.json"
RESULT_MD_PATH = OUTPUT / "OUT_OF_ERA_BREAKOUT_RESULT.md"
ARTIFACT_MANIFEST_PATH = OUTPUT / "OUT_OF_ERA_BREAKOUT_ARTIFACT_MANIFEST.json"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return _json_ready(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return "Infinity" if value > 0 else None
    return value


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(_json_ready(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def _decision(economic: list[str], distinct: list[str]) -> str:
    if not economic:
        return "NO_OUT_OF_ERA_BREAKOUT_ECONOMIC_SURVIVOR"
    if len(distinct) >= 2:
        return "OUT_OF_ERA_BREAKOUT_INDEPENDENT_SURVIVORS"
    return "ONE_OUT_OF_ERA_BREAKOUT_SURVIVOR_ONLY"


def _render(result: Mapping[str, Any]) -> str:
    lines = [
        "# Out-Of-Era Breakout Economics And Independence V2 Result",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "| Candidate | Trades | Stress PF | Average R | Drawdown R | Holm p | Economic pass |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["metrics"]:
        lines.append(
            f"| {row['candidate_id']} | {row['trades']} | {row['stress_pf']:.3f} | "
            f"{row['average_stress_r']:.3f} | {row['closed_drawdown_r']:.3f} | "
            f"{row['holm_pvalue']:.4f} | {row['economic_pass']} |"
        )
    lines.extend(
        [
            "",
            f"Economic survivors: `{', '.join(result['economic_survivors']) or 'NONE'}`",
            "",
            f"Distinct survivors: `{', '.join(result['distinct_survivors']) or 'NONE'}`",
            "",
            "Research only. No model, EA, demo, live, broker, Databento, or paid-data authority is granted.",
            "",
        ]
    )
    return "\n".join(lines)


def _update_artifact_manifest(contract_hash: str) -> None:
    artifacts = {}
    for path in sorted(OUTPUT.iterdir()):
        if (
            not path.is_file()
            or path == ARTIFACT_MANIFEST_PATH
            or path.suffix == ".part"
        ):
            continue
        artifacts[path.name] = {"bytes": path.stat().st_size, "sha256": _sha256(path)}
    _write_json(
        ARTIFACT_MANIFEST_PATH,
        {
            "final_contract_sha256": contract_hash,
            "artifacts": artifacts,
            "training_authorized": False,
            "execution_authorized": False,
        },
    )


def main() -> int:
    if any(
        path.exists()
        for path in (MARKER_PATH, METRICS_PATH, TRADES_PATH, RESULT_PATH)
    ):
        raise RuntimeError("Out-of-era breakout outcomes were already opened")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    final_contract = _load_module(
        "out_of_era_breakout_final_verify", ROOT / "lock_final_contract.py"
    )
    if not FINAL_LOCK_PATH.is_file():
        raise FileNotFoundError("Run lock_final_contract.py before opening outcomes")
    lock = json.loads(FINAL_LOCK_PATH.read_text(encoding="utf-8"))
    final_contract.validate_final_lock(lock, config)
    replication = _load_module(
        "out_of_era_breakout_research_run", ROOT / "src" / "replication.py"
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    _write_json(
        MARKER_PATH,
        {
            "schema_version": "xauusd_out_of_era_breakout_outcomes_opened_v2",
            "opened_utc": datetime.now(UTC).isoformat(),
            "final_contract_sha256": lock["final_contract_sha256"],
            "training_authorized": False,
            "execution_authorized": False,
        },
    )
    source = config["source"]
    storage_root = Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    ).resolve()
    replay_root = storage_root / source["replay_root"]
    months = final_contract.expected_months(config)
    m5 = replication.load_side_specific_m5(replay_root, months)
    source_days = pd.DatetimeIndex(
        sorted(pd.to_datetime(m5["bar_start_utc"], utc=True).dt.floor("D").unique())
    )
    ledgers: dict[str, pd.DataFrame] = {}
    metrics: list[dict[str, Any]] = []
    for candidate in config["candidates"]:
        candidate_id = str(candidate["candidate_id"])
        source_config = replication.load_json(
            (ROOT / candidate["source_config"]).resolve()
        )
        trades = replication.run_candidate(m5, candidate, source_config)
        ledgers[candidate_id] = trades
        metrics.append(
            replication.summarize(
                candidate_id,
                trades,
                config["gates"][candidate_id],
                source_days,
            )
        )
    raw_pvalues = {row["candidate_id"]: row["daily_pvalue"] for row in metrics}
    adjusted = replication.holm_adjust(raw_pvalues)
    for row in metrics:
        candidate_id = row["candidate_id"]
        row["holm_pvalue"] = adjusted[candidate_id]
        checks = replication.gate_checks(
            row, config["gates"][candidate_id], adjusted[candidate_id]
        )
        row["gate_checks"] = checks
        row["economic_pass"] = all(checks.values())
    fixed_order = [str(value) for value in config["independence"]["fixed_selection_order"]]
    metric_lookup = {row["candidate_id"]: row for row in metrics}
    economic = [
        candidate_id
        for candidate_id in fixed_order
        if bool(metric_lookup[candidate_id]["economic_pass"])
    ]
    pairwise = replication.pairwise_independence(
        ledgers, economic, source_days, config["independence"]
    )
    distinct = replication.select_distinct_survivors(
        economic, pairwise, fixed_order
    )
    metrics_frame = pd.DataFrame(metrics)
    metrics_frame["gate_checks_json"] = metrics_frame.pop("gate_checks").map(
        lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
    )
    trade_frames = [
        trades.assign(replication_candidate_id=candidate_id)
        for candidate_id, trades in ledgers.items()
        if not trades.empty
    ]
    all_trades = (
        pd.concat(trade_frames, ignore_index=True)
        if trade_frames
        else pd.DataFrame()
    )
    pairwise_frame = pd.DataFrame(pairwise)
    if not pairwise_frame.empty:
        pairwise_frame["checks_json"] = pairwise_frame.pop("checks").map(
            lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
        )
    _write_csv(METRICS_PATH, metrics_frame)
    _write_csv(TRADES_PATH, all_trades)
    _write_csv(PAIRWISE_PATH, pairwise_frame)
    result = {
        "schema_version": config["schema_version"],
        "completed_utc": datetime.now(UTC).isoformat(),
        "final_contract_sha256": lock["final_contract_sha256"],
        "attempts_before_replication": int(
            config["research_controls"]["campaign_attempts_before_replication"]
        ),
        "parameter_search_count": 0,
        "source_start_utc": source["start_utc"],
        "source_end_exclusive_utc": source["end_exclusive_utc"],
        "source_months": len(months),
        "source_days": len(source_days),
        "m5_rows": len(m5),
        "metrics": metrics,
        "economic_survivors": economic,
        "pairwise_independence": pairwise,
        "distinct_survivors": distinct,
        "additional_distinct_survivors_beyond_r1": [
            value for value in distinct if value != "R1_UPTREND_PORTABILITY_EXACT"
        ],
        "decision": _decision(economic, distinct),
        "evidence_hashes": {
            "metrics_sha256": _sha256(METRICS_PATH),
            "trades_sha256": _sha256(TRADES_PATH),
            "independence_sha256": _sha256(PAIRWISE_PATH),
        },
        "paid_data_request_made": False,
        "databento_used": False,
        "broker_action_performed": False,
        "research_only": True,
        "training_authorized": False,
        "execution_authorized": False,
    }
    _write_json(RESULT_PATH, result)
    RESULT_MD_PATH.write_text(_render(result), encoding="utf-8")
    _update_artifact_manifest(str(lock["final_contract_sha256"]))
    print(json.dumps(_json_ready(result), indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
