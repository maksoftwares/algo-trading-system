from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from contract import (  # noqa: E402
    expected_months,
    load_config,
    sha256_file,
    storage_root,
    validate_final_lock,
)


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(_json_ready(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


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
        if math.isnan(value):
            return None
        return "Infinity" if value > 0 else "-Infinity"
    return value


def _write_parquet(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    output = frame.copy()
    if output.empty and not len(output.columns):
        output = pd.DataFrame(
            {
                "candidate_id": pd.Series(dtype="string"),
                "entry_time": pd.Series(dtype="datetime64[ns, UTC]"),
                "stress_net_r": pd.Series(dtype="float64"),
            }
        )
    output.to_parquet(temporary, index=False)
    os.replace(temporary, path)


def _load_source_config(
    config: Mapping[str, Any], candidate_id: str
) -> dict[str, Any]:
    candidate = next(
        item for item in config["candidates"] if item["candidate_id"] == candidate_id
    )
    path = (ROOT / candidate["source_config"]).resolve()
    return json.loads(path.read_text(encoding="utf-8"))


def _standardize_trades(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if result.empty:
        return result
    for column in ("entry_time", "exit_time", "signal_time"):
        if column in result:
            result[column] = pd.to_datetime(result[column], utc=True, errors="raise")
    if "risk_usd" in result and "stress_net_usd" not in result:
        result["stress_net_usd"] = (
            pd.to_numeric(result["stress_net_r"], errors="raise")
            * pd.to_numeric(result["risk_usd"], errors="raise")
        )
    result = result.sort_values("entry_time", kind="mergesort").reset_index(drop=True)
    return result


def _assert_trade_integrity(
    candidate_id: str, trades: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> None:
    if trades.empty:
        return
    if trades["entry_time"].isna().any() or trades["stress_net_r"].isna().any():
        raise ValueError(f"Missing trade fields for {candidate_id}")
    if (~np.isfinite(trades["stress_net_r"].to_numpy(dtype=float))).any():
        raise ValueError(f"Non-finite trade return for {candidate_id}")
    if trades["entry_time"].lt(start).any() or trades["entry_time"].ge(end).any():
        raise ValueError(f"Trade escaped replication window: {candidate_id}")
    if (trades["exit_time"] < trades["entry_time"]).any():
        raise ValueError(f"Negative holding period: {candidate_id}")
    if "source_candidate_id" in trades and trades["source_candidate_id"].duplicated().any():
        raise ValueError(f"Duplicate source candidate IDs: {candidate_id}")


def _format_number(value: Any, digits: int = 3) -> str:
    number = float(value)
    if math.isinf(number):
        return "inf"
    return f"{number:.{digits}f}"


def _render(result: Mapping[str, Any]) -> str:
    lines = [
        "# XAUUSD Out-of-Era Replication V1",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "| Candidate | Role | Trades | Stress PF | Avg R | Net R | DD R | Holm p | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    roles = {item["candidate_id"]: item["role"] for item in result["candidates"]}
    for candidate_id, metrics in result["metrics"].items():
        lines.append(
            "| "
            + " | ".join(
                [
                    candidate_id,
                    roles[candidate_id],
                    str(metrics["trades"]),
                    _format_number(metrics["stress_pf"]),
                    _format_number(metrics["average_stress_r"]),
                    _format_number(metrics["stress_net_r"]),
                    _format_number(metrics["closed_drawdown_r"]),
                    _format_number(metrics["holm_pvalue"], 4),
                    "PASS" if metrics["replication_gate_pass"] else "FAIL",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "This is research evidence only. It does not authorize training, Python",
            "prediction serving, EA consumption, demo trading, or live trading.",
            "",
        ]
    )
    return "\n".join(lines)


def _trade_id(candidate_id: str, signal_time: Any, direction: str) -> str:
    raw = f"{candidate_id}|{pd.Timestamp(signal_time).isoformat()}|{direction}"
    return hashlib.sha256(raw.encode("ascii")).hexdigest()


def main() -> int:
    config = load_config()
    output = ROOT / "outputs"
    final_lock_path = output / "OUT_OF_ERA_FINAL_CONTRACT_LOCK.json"
    if not final_lock_path.is_file():
        raise FileNotFoundError("Final contract is not locked")
    final_lock = json.loads(final_lock_path.read_text(encoding="utf-8"))
    validate_final_lock(final_lock, config)
    marker_path = output / "OUT_OF_ERA_OUTCOMES_OPENED.json"
    result_path = output / "OUT_OF_ERA_REPLICATION_RESULT.json"
    if marker_path.exists() or result_path.exists():
        raise RuntimeError("V1 outcomes were already opened; create a new version")

    root = storage_root(config)
    replay_root = root / config["source"]["replay_root"]
    months = expected_months(config)
    replication = importlib.import_module("replication")
    m5 = replication.load_side_specific_m5(replay_root, months)
    start = pd.Timestamp(config["source"]["start_utc"])
    end = pd.Timestamp(config["source"]["end_exclusive_utc"])
    if m5.empty or m5["bar_start_utc"].min() < start or m5["bar_start_utc"].max() >= end:
        raise ValueError("Loaded M5 frame violates the sealed date boundary")
    observed_months = sorted(m5["bar_start_utc"].dt.strftime("%Y-%m").unique())
    if observed_months != months:
        raise ValueError("Loaded M5 frame does not cover every sealed month")

    opened = {
        "schema_version": "xauusd_out_of_era_outcomes_opened_v1",
        "opened_utc": datetime.now(UTC).isoformat(),
        "final_contract_sha256": final_lock["final_contract_sha256"],
        "registered_candidates": final_lock["registered_candidates"],
        "outcomes_opened": True,
        "parameter_search_count": 0,
        "training_authorized": False,
        "execution_authorized": False,
    }
    _atomic_json(marker_path, opened)

    r1 = replication.run_r1(
        m5, _load_source_config(config, "R1_UPTREND_PORTABILITY_EXACT")
    )
    nfp, event_count, nfp_audit = replication.run_nfp(
        m5,
        replay_root,
        root / config["source"]["public_input_root"] / "bls-nfp-2010-2016.json",
        _load_source_config(config, "NFP_FADE_RR2_EXACT"),
    )
    gld = replication.run_gld(
        m5,
        root / config["source"]["public_input_root"] / "gld-daily-2008-2016.csv",
        config["execution"],
    )
    if not gld.empty:
        gld = gld.copy()
        gld["source_candidate_id"] = [
            _trade_id("GLD_FLOW_REVERSAL_V0_EXACT", row.signal_time, row.direction)
            for row in gld.itertuples(index=False)
        ]
    trades = {
        "R1_UPTREND_PORTABILITY_EXACT": _standardize_trades(r1),
        "NFP_FADE_RR2_EXACT": _standardize_trades(nfp),
        "GLD_FLOW_REVERSAL_V0_EXACT": _standardize_trades(gld),
    }
    for candidate_id, frame in trades.items():
        _assert_trade_integrity(candidate_id, frame, start, end)

    metrics: dict[str, dict[str, Any]] = {}
    for candidate_id, frame in trades.items():
        metrics[candidate_id] = replication.summarize(
            candidate_id,
            frame,
            config["gates"][candidate_id],
            event_count if candidate_id == "NFP_FADE_RR2_EXACT" else None,
        )
        if "stress_net_usd" in frame:
            metrics[candidate_id]["stress_net_usd"] = float(
                frame["stress_net_usd"].sum()
            )
        metrics[candidate_id]["long_trades"] = int(
            frame["direction"].eq("LONG").sum()
        ) if not frame.empty else 0
        metrics[candidate_id]["short_trades"] = int(
            frame["direction"].eq("SHORT").sum()
        ) if not frame.empty else 0
        metrics[candidate_id]["win_rate"] = float(
            frame["stress_net_r"].gt(0.0).mean()
        ) if not frame.empty else 0.0
    holm = replication.holm_adjust(
        {candidate_id: row["daily_pvalue"] for candidate_id, row in metrics.items()}
    )
    for candidate_id, row in metrics.items():
        row["holm_pvalue"] = float(holm[candidate_id])
        row["gate_checks"] = replication.gate_checks(
            row, config["gates"][candidate_id], row["holm_pvalue"]
        )
        row["replication_gate_pass"] = all(row["gate_checks"].values())
        row["eligible_for_combined_review"] = bool(
            row["replication_gate_pass"]
            and candidate_id != "GLD_FLOW_REVERSAL_V0_EXACT"
        )

    advancing = [
        candidate_id
        for candidate_id, row in metrics.items()
        if row["eligible_for_combined_review"]
    ]
    decision = (
        "OUT_OF_ERA_REPLICATION_SURVIVOR_REQUIRES_COMBINED_REVIEW"
        if advancing
        else "NO_OUT_OF_ERA_REPLICATION_SURVIVOR"
    )
    result: dict[str, Any] = {
        "schema_version": "xauusd_out_of_era_replication_result_v1",
        "completed_utc": datetime.now(UTC).isoformat(),
        "decision": decision,
        "final_contract_sha256": final_lock["final_contract_sha256"],
        "replication_window": [start.isoformat(), end.isoformat()],
        "campaign_attempts_before_this_replication": int(
            config["research_controls"]["campaign_attempts_before_this_replication"]
        ),
        "registered_attempts_this_replication": 3,
        "candidates": config["candidates"],
        "metrics": metrics,
        "eligible_for_combined_review": advancing,
        "nfp_execution_audit": nfp_audit,
        "research_only": True,
        "training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "demo_trading_authorized": False,
        "live_trading_authorized": False,
    }

    output.mkdir(parents=True, exist_ok=True)
    trade_paths: list[Path] = []
    for candidate_id, frame in trades.items():
        path = output / f"{candidate_id}_TRADES.parquet"
        _write_parquet(path, frame)
        trade_paths.append(path)
    metrics_path = output / "OUT_OF_ERA_REPLICATION_METRICS.csv"
    flat_metrics = pd.DataFrame(
        [
            {
                key: value
                for key, value in row.items()
                if key != "gate_checks"
            }
            for row in metrics.values()
        ]
    )
    flat_metrics.to_csv(metrics_path, index=False)
    audit_path = output / "OUT_OF_ERA_NFP_EXECUTION_AUDIT.json"
    _atomic_json(audit_path, nfp_audit)
    _atomic_json(result_path, result)
    markdown_path = output / "OUT_OF_ERA_REPLICATION_RESULT.md"
    _atomic_text(markdown_path, _render(result))
    artifacts = [
        marker_path,
        *trade_paths,
        metrics_path,
        audit_path,
        result_path,
        markdown_path,
    ]
    manifest = {
        "schema_version": "xauusd_out_of_era_replication_artifacts_v1",
        "created_utc": datetime.now(UTC).isoformat(),
        "final_contract_sha256": final_lock["final_contract_sha256"],
        "artifacts": {
            path.name: {
                "bytes": int(path.stat().st_size),
                "sha256": sha256_file(path),
            }
            for path in artifacts
        },
        "research_only": True,
        "training_authorized": False,
        "execution_authorized": False,
    }
    _atomic_json(output / "OUT_OF_ERA_REPLICATION_ARTIFACT_MANIFEST.json", manifest)
    print(json.dumps(_json_ready(result), indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
