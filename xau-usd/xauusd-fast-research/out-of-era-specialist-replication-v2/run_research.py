from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from src.contract import (
    FINAL_LOCK_PATH,
    OUTCOME_MARKER_PATH,
    RESULT_PATH,
    expected_months,
    load_config,
    sha256_file,
    storage_root,
    validate_final_lock,
)
from src import replication


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs"
METRICS_PATH = OUTPUT / "OUT_OF_ERA_SPECIALIST_METRICS.csv"
TRADES_PATH = OUTPUT / "OUT_OF_ERA_SPECIALIST_TRADES.parquet"
PAIRWISE_PATH = OUTPUT / "OUT_OF_ERA_SPECIALIST_INDEPENDENCE.csv"
FOMC_CANDIDATE_MANIFEST_PATH = OUTPUT / "OUT_OF_ERA_FOMC_CHOP_CANDIDATE_MANIFEST.json"
FOMC_EXECUTION_AUDIT_PATH = OUTPUT / "OUT_OF_ERA_FOMC_CHOP_EXECUTION_AUDIT.json"
RESULT_MD_PATH = OUTPUT / "OUT_OF_ERA_SPECIALIST_RESULT.md"
ARTIFACT_MANIFEST_PATH = OUTPUT / "OUT_OF_ERA_SPECIALIST_ARTIFACT_MANIFEST.json"


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
        return "Infinity" if value > 0.0 else None
    return value


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(_json_ready(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    frame.to_csv(temporary, index=False, lineterminator="\n")
    os.replace(temporary, path)


def _write_parquet(path: Path, frame: pd.DataFrame) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    output = frame.copy()
    if output.empty and not len(output.columns):
        output = pd.DataFrame(
            {
                "replication_candidate_id": pd.Series(dtype="string"),
                "entry_time": pd.Series(dtype="datetime64[ns, UTC]"),
                "stress_net_r": pd.Series(dtype="float64"),
            }
        )
    output.to_parquet(temporary, index=False)
    os.replace(temporary, path)


def _candidate_source_config(
    config: Mapping[str, Any], candidate: Mapping[str, Any]
) -> dict[str, Any]:
    return replication.load_json((ROOT / str(candidate["source_config"])).resolve())


def _assert_trade_integrity(
    candidate_id: str,
    trades: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> None:
    if trades.empty:
        return
    required = {"entry_time", "exit_time", "direction", "stress_net_r"}
    missing = required.difference(trades.columns)
    if missing:
        raise ValueError(f"Missing trade fields for {candidate_id}: {sorted(missing)}")
    if trades[list(required)].isna().any().any():
        raise ValueError(f"Missing trade value for {candidate_id}")
    if (~np.isfinite(trades["stress_net_r"].to_numpy(dtype=float))).any():
        raise ValueError(f"Non-finite trade return for {candidate_id}")
    if trades["entry_time"].lt(start).any() or trades["entry_time"].ge(end).any():
        raise ValueError(f"Trade escaped replication window: {candidate_id}")
    if (trades["exit_time"] < trades["entry_time"]).any():
        raise ValueError(f"Negative holding period: {candidate_id}")
    if "source_candidate_id" in trades and trades["source_candidate_id"].duplicated().any():
        raise ValueError(f"Duplicate source candidate ID: {candidate_id}")


def _decision(distinct_count: int, economic_count: int) -> str:
    if distinct_count >= 3:
        return "THREE_DISTINCT_OUT_OF_ERA_SURVIVORS_REQUIRE_COMBINED_REVIEW"
    if distinct_count == 2:
        return "TWO_DISTINCT_OUT_OF_ERA_SURVIVORS_REQUIRE_MORE_RESEARCH"
    if distinct_count == 1:
        return "ONE_DISTINCT_OUT_OF_ERA_SURVIVOR_ONLY"
    if economic_count:
        return "ECONOMIC_RESULTS_FAILED_INDEPENDENCE"
    return "NO_OUT_OF_ERA_SPECIALIST_SURVIVOR"


def _portfolio_diagnostic(
    ledgers: Mapping[str, pd.DataFrame], distinct: list[str], source_days: pd.DatetimeIndex
) -> dict[str, Any]:
    frames = [
        ledgers[candidate_id].assign(portfolio_candidate_id=candidate_id)
        for candidate_id in distinct
        if not ledgers[candidate_id].empty
    ]
    if not frames:
        return {
            "trades": 0,
            "stress_net_r": 0.0,
            "stress_pf": 0.0,
            "average_stress_r": 0.0,
            "closed_drawdown_r": 0.0,
            "trades_per_source_day": 0.0,
        }
    combined = pd.concat(frames, ignore_index=True).sort_values(
        ["entry_time", "portfolio_candidate_id"], kind="mergesort"
    )
    values = combined["stress_net_r"].astype(float)
    return {
        "trades": int(len(combined)),
        "stress_net_r": float(values.sum()),
        "stress_pf": replication.profit_factor(values),
        "average_stress_r": float(values.mean()),
        "closed_drawdown_r": replication.closed_drawdown(values),
        "trades_per_source_day": len(combined) / len(source_days)
        if len(source_days)
        else 0.0,
        "note": "Equal-R closed-trade diagnostic; not a shared-margin equity simulation.",
    }


def _render(result: Mapping[str, Any]) -> str:
    lines = [
        "# XAUUSD Out-of-Era Specialist Replication V2",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "| Candidate | Family | Trades | PF | Avg R | Net R | DD R | Holm p | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    families = {
        item["candidate_id"]: item["mechanism_family"]
        for item in result["registered_candidates"]
    }
    for row in result["metrics"]:
        lines.append(
            f"| {row['candidate_id']} | {families[row['candidate_id']]} | "
            f"{row['trades']} | {row['stress_pf']:.3f} | "
            f"{row['average_stress_r']:.3f} | {row['stress_net_r']:.3f} | "
            f"{row['closed_drawdown_r']:.3f} | {row['holm_pvalue']:.4f} | "
            f"{'PASS' if row['economic_pass'] else 'FAIL'} |"
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


def _artifact_manifest(contract_hash: str) -> None:
    artifacts = {}
    for path in sorted(OUTPUT.iterdir()):
        if not path.is_file() or path == ARTIFACT_MANIFEST_PATH or path.suffix == ".part":
            continue
        artifacts[path.name] = {
            "bytes": int(path.stat().st_size),
            "sha256": sha256_file(path),
        }
    _write_json(
        ARTIFACT_MANIFEST_PATH,
        {
            "schema_version": "xauusd_out_of_era_specialist_artifacts_v2",
            "final_contract_sha256": contract_hash,
            "artifacts": artifacts,
            "training_authorized": False,
            "execution_authorized": False,
        },
    )


def run_research() -> dict[str, Any]:
    config = load_config()
    if not FINAL_LOCK_PATH.is_file():
        raise FileNotFoundError("Run lock_final_contract.py before opening outcomes")
    if OUTCOME_MARKER_PATH.exists() or RESULT_PATH.exists():
        raise RuntimeError("Out-of-era specialist outcomes were already opened")
    lock = json.loads(FINAL_LOCK_PATH.read_text(encoding="utf-8"))
    validate_final_lock(lock, config)
    root = storage_root(config)
    replay_root = root / config["source"]["replay_root"]
    months = expected_months(config)
    m5 = replication.load_side_specific_m5(replay_root, months)
    start = pd.Timestamp(config["source"]["start_utc"])
    end = pd.Timestamp(config["source"]["end_exclusive_utc"])
    if m5.empty or m5["bar_start_utc"].min() < start or m5["bar_start_utc"].max() >= end:
        raise ValueError("Loaded M5 data violates the sealed boundary")
    observed_months = sorted(m5["bar_start_utc"].dt.strftime("%Y-%m").unique())
    if observed_months != months:
        raise ValueError("Loaded M5 data does not cover every sealed month")
    source_days = pd.DatetimeIndex(
        sorted(pd.to_datetime(m5["bar_start_utc"], utc=True).dt.floor("D").unique())
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    _write_json(
        OUTCOME_MARKER_PATH,
        {
            "schema_version": "xauusd_out_of_era_specialist_outcomes_opened_v2",
            "opened_utc": datetime.now(UTC).isoformat(),
            "final_contract_sha256": lock["final_contract_sha256"],
            "registered_candidates": lock["registered_candidates"],
            "single_outcome_opening": True,
            "training_authorized": False,
            "execution_authorized": False,
        },
    )

    ledgers: dict[str, pd.DataFrame] = {}
    fomc_manifests: dict[str, Any] = {}
    fomc_audits: dict[str, Any] = {}
    for candidate in config["candidates"]:
        candidate_id = str(candidate["candidate_id"])
        if str(candidate["engine"]) == "CORRECTED_RAW_TICK_EVENT":
            public_root = root / config["source"]["public_input_root"]
            calendar = pd.read_csv(
                public_root / "OFFICIAL_FOMC_CALENDAR_2010_2016.csv",
                parse_dates=["event_time_utc"],
            )
            base_regime = replication.load_json(
                (ROOT / config["base_regime_config"]).resolve()
            )
            trades, fomc_manifest, fomc_audit = replication.run_fomc_regime(
                m5,
                replay_root,
                calendar,
                candidate,
                base_regime,
                config["source"],
                config["event_execution"],
            )
            fomc_manifests[candidate_id] = fomc_manifest
            fomc_audits[candidate_id] = fomc_audit
            if len(trades) and not (
                int(fomc_audit["stop_outcomes"]) + int(fomc_audit["target_outcomes"])
            ):
                raise RuntimeError("FOMC event execution produced no stop or target")
        else:
            trades = replication.run_price_candidate(
                m5, candidate, _candidate_source_config(config, candidate)
            )
        ledgers[candidate_id] = replication.standardize_trades(trades)
        _assert_trade_integrity(candidate_id, ledgers[candidate_id], start, end)

    metrics: list[dict[str, Any]] = []
    event_ids = {
        str(item["candidate_id"])
        for item in config["candidates"]
        if item["engine"] == "CORRECTED_RAW_TICK_EVENT"
    }
    event_count = int(config["official_fomc"]["expected_regular_events"])
    for candidate in config["candidates"]:
        candidate_id = str(candidate["candidate_id"])
        metrics.append(
            replication.summarize(
                candidate_id,
                ledgers[candidate_id],
                config["gates"][candidate_id],
                source_days,
                event_count if candidate_id in event_ids else None,
            )
        )
    adjusted = replication.holm_adjust(
        {row["candidate_id"]: row["daily_pvalue"] for row in metrics}
    )
    for row in metrics:
        candidate_id = str(row["candidate_id"])
        row["holm_pvalue"] = float(adjusted[candidate_id])
        row["gate_checks"] = replication.gate_checks(
            row, config["gates"][candidate_id], row["holm_pvalue"]
        )
        row["economic_pass"] = all(row["gate_checks"].values())
    order = [str(value) for value in config["independence"]["fixed_selection_order"]]
    metric_lookup = {str(row["candidate_id"]): row for row in metrics}
    economic = [candidate_id for candidate_id in order if metric_lookup[candidate_id]["economic_pass"]]
    pairwise = replication.pairwise_independence(
        ledgers, economic, source_days, config["independence"]
    )
    families = {
        str(item["candidate_id"]): str(item["mechanism_family"])
        for item in config["candidates"]
    }
    distinct = replication.select_distinct_survivors(
        economic, pairwise, order, families
    )

    metric_frame = pd.DataFrame(metrics)
    metric_frame["gate_checks_json"] = metric_frame.pop("gate_checks").map(
        lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
    )
    trade_frames = [
        frame.assign(replication_candidate_id=candidate_id)
        for candidate_id, frame in ledgers.items()
        if not frame.empty
    ]
    all_trades = pd.concat(trade_frames, ignore_index=True) if trade_frames else pd.DataFrame()
    pairwise_frame = pd.DataFrame(pairwise)
    if not pairwise_frame.empty:
        pairwise_frame["checks_json"] = pairwise_frame.pop("checks").map(
            lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
        )
    _write_csv(METRICS_PATH, metric_frame)
    _write_parquet(TRADES_PATH, all_trades)
    _write_csv(PAIRWISE_PATH, pairwise_frame)
    _write_json(FOMC_CANDIDATE_MANIFEST_PATH, fomc_manifests)
    _write_json(FOMC_EXECUTION_AUDIT_PATH, fomc_audits)

    result = {
        "schema_version": config["schema_version"],
        "completed_utc": datetime.now(UTC).isoformat(),
        "final_contract_sha256": lock["final_contract_sha256"],
        "window_start_utc": start.isoformat(),
        "window_end_exclusive_utc": end.isoformat(),
        "source_months": len(months),
        "source_days": len(source_days),
        "m5_rows": len(m5),
        "campaign_attempts_before_v2": int(config["research_controls"]["campaign_attempts_before_v2"]),
        "new_attempt_first": int(config["research_controls"]["new_attempt_first"]),
        "new_attempt_last": int(config["research_controls"]["new_attempt_last"]),
        "cumulative_campaign_attempts": int(config["research_controls"]["new_attempt_last"]),
        "registered_candidates": config["candidates"],
        "metrics": metrics,
        "economic_survivors": economic,
        "pairwise_independence": pairwise,
        "distinct_survivors": distinct,
        "distinct_mechanism_families": [families[value] for value in distinct],
        "portfolio_closed_trade_diagnostic": _portfolio_diagnostic(
            ledgers, distinct, source_days
        ),
        "fomc_candidate_manifests": fomc_manifests,
        "fomc_execution_audits": fomc_audits,
        "decision": _decision(len(distinct), len(economic)),
        "single_outcome_opening": True,
        "parameter_search_count": 0,
        "paid_data_request_made": False,
        "databento_used": False,
        "broker_action_performed": False,
        "research_only": True,
        "training_authorized": False,
        "execution_authorized": False,
    }
    _write_json(RESULT_PATH, result)
    RESULT_MD_PATH.write_text(_render(result), encoding="utf-8", newline="\n")
    _artifact_manifest(str(lock["final_contract_sha256"]))
    return result


def main() -> int:
    result = run_research()
    print(json.dumps(_json_ready(result), indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
