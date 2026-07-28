from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import Counter
from datetime import date, datetime, timezone
from datetime import time as datetime_time
from pathlib import Path
from typing import Any

import pandas as pd

from capture_prospective_neutral_gdelt_relative_tone import (
    DEFAULT_OUTPUT_ROOT as SOURCE_ROOT,
)
from capture_prospective_neutral_gdelt_relative_tone import (
    IMPLEMENTATION_LOCK_PATH,
    _entry_date,
    _utc,
    _validated_manifests,
    load_and_verify_preregistration,
)
from capture_prospective_neutral_ownership import (
    DEFAULT_OUTPUT_ROOT as OWNERSHIP_ROOT,
)
from capture_prospective_neutral_ownership import (
    _validated_existing_ownership,
    write_immutable,
)
from run_neutral_gdelt_coverage_census import sha256_file

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = (
    ROOT
    / "config"
    / "frozen_prospective_neutral_gdelt_relative_tone_v1.json"
)
DEFAULT_LEDGER_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-gdelt-relative-tone-v1/ledger"
)
SCHEMA_VERSION = "eurusd_neutral_prospective_gdelt_decision_v1"


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _deduplicate_documents(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for row in sorted(
        rows,
        key=lambda value: (
            value["batch_timestamp_utc"],
            value["record_id"],
            value["document_identifier"],
        ),
    ):
        selected.setdefault(str(row["document_identifier"]), row)
    return list(selected.values())


def _median_absolute_deviation(values: list[float]) -> float:
    center = statistics.median(values)
    return statistics.median(abs(value - center) for value in values)


def compute_signal(
    config: dict[str, Any],
    documents: list[dict[str, Any]],
) -> dict[str, Any]:
    signal_config = config["signal"]
    rows = _deduplicate_documents(documents)
    if any(
        row.get("tone") is None
        or not math.isfinite(float(row["tone"]))
        for row in rows
    ):
        return {
            "status": "CASH_NONFINITE_TONE",
            "side": None,
            "deduplicated_documents": len(rows),
        }
    side_values: dict[str, dict[str, Any]] = {}
    for side in ("ECB", "FED"):
        selected = [row for row in rows if row["side"] == side]
        source_documents = Counter(
            str(row["source_common_name"]) for row in selected
        )
        unique_sources = len(source_documents)
        largest_share = (
            max(source_documents.values()) / len(selected)
            if selected
            else 0.0
        )
        source_scores = [
            statistics.median(
                [
                    float(row["tone"])
                    for row in selected
                    if row["source_common_name"] == source
                ]
            )
            for source in sorted(source_documents)
        ]
        side_values[side] = {
            "strict_documents": len(selected),
            "unique_sources": unique_sources,
            "largest_source_share": largest_share,
            "source_scores": source_scores,
            "side_score": (
                statistics.median(source_scores)
                if source_scores
                else None
            ),
        }
        if (
            unique_sources
            < int(signal_config["minimum_unique_sources_per_side"])
            or largest_share
            > float(
                signal_config[
                    "maximum_largest_source_share_per_side"
                ]
            )
        ):
            return {
                "status": "CASH_SOURCE_QUORUM_FAILED",
                "side": None,
                "deduplicated_documents": len(rows),
                "by_side": side_values,
            }
    all_source_scores = [
        *side_values["ECB"]["source_scores"],
        *side_values["FED"]["source_scores"],
    ]
    dispersion = _median_absolute_deviation(all_source_scores)
    effective_dispersion = max(
        float(signal_config["dispersion_floor"]),
        dispersion,
    )
    relative_tone = (
        float(side_values["ECB"]["side_score"])
        - float(side_values["FED"]["side_score"])
    )
    strength = abs(relative_tone) / effective_dispersion
    minimum_strength = float(signal_config["minimum_strength"])
    if strength < minimum_strength or relative_tone == 0:
        status = "CASH_SUBTHRESHOLD_RELATIVE_TONE"
        side = None
    else:
        status = "SIGNAL"
        side = "LONG" if relative_tone > 0 else "SHORT"
    return {
        "status": status,
        "side": side,
        "deduplicated_documents": len(rows),
        "by_side": side_values,
        "relative_tone": relative_tone,
        "pooled_dispersion": dispersion,
        "effective_dispersion": effective_dispersion,
        "strength": strength,
        "minimum_strength": minimum_strength,
    }


def _decision_time(config: dict[str, Any], entry_date: date) -> datetime:
    return datetime.combine(
        entry_date,
        datetime_time.fromisoformat(
            config["decision_and_entry"]["decision_time_utc"]
        ),
        tzinfo=timezone.utc,
    )


def _validated_existing_decision(
    ledger_root: Path,
    entry_date: date,
) -> dict[str, Any] | None:
    paths = sorted(
        (ledger_root / "decisions").glob(
            f"DECISION_{entry_date.isoformat()}_*.json"
        )
    )
    if not paths:
        return None
    if len(paths) != 1:
        raise RuntimeError("Multiple GDELT decisions exist for one date")
    path = paths[0]
    payload = path.read_bytes()
    digest = _sha256_bytes(payload)
    if path.name != (
        f"DECISION_{entry_date.isoformat()}_{digest[:16]}.json"
    ):
        raise RuntimeError("GDELT decision name/hash drift")
    result = json.loads(payload)
    if result["entry_date_utc"] != entry_date.isoformat():
        raise RuntimeError("GDELT decision date drift")
    if result.get("broker_action_allowed") is not False:
        raise RuntimeError("GDELT decision broker boundary drift")
    return {
        **result,
        "decision_relative_path": path.relative_to(
            ledger_root
        ).as_posix(),
        "decision_sha256": digest,
    }


def status(
    entry_date: Any,
    *,
    source_root: Path = SOURCE_ROOT,
    ownership_root: Path = OWNERSHIP_ROOT,
    ledger_root: Path = DEFAULT_LEDGER_ROOT,
    now_utc: Any | None = None,
) -> dict[str, Any]:
    config, _ = load_and_verify_preregistration()
    day = _entry_date(entry_date)
    evaluated = (
        datetime.now(timezone.utc)
        if now_utc is None
        else _utc(now_utc)
    )
    due = _decision_time(config, day)
    existing = _validated_existing_decision(ledger_root, day)
    source_manifests = _validated_manifests(source_root, day)
    on_time_sources = [
        row
        for row in source_manifests
        if row["status"] == "COMPLETE_ON_TIME"
    ]
    ownership = _validated_existing_ownership(
        ownership_root,
        pd.Timestamp(day, tz="UTC"),
    )
    if existing is not None:
        state = "DECISION_RECORDED"
    elif evaluated < due:
        state = "WAITING_FOR_DECISION_TIME"
    else:
        state = "DECISION_DUE"
    return {
        "schema_version": SCHEMA_VERSION,
        "evaluated_at_utc": evaluated.isoformat(),
        "entry_date_utc": day.isoformat(),
        "status": state,
        "decision_due_at_utc": due.isoformat(),
        "complete_on_time_source_manifests": len(on_time_sources),
        "ownership_record_available": ownership is not None,
        "ownership_status": (
            ownership["status"] if ownership is not None else None
        ),
        "decision": existing,
        "historical_eurusd_prices_loaded": False,
        "historical_eurusd_pnl_loaded": False,
        "oracle_rows_loaded": False,
        "broker_action_allowed": False,
    }


def evaluate(
    entry_date: Any,
    *,
    source_root: Path = SOURCE_ROOT,
    ownership_root: Path = OWNERSHIP_ROOT,
    ledger_root: Path = DEFAULT_LEDGER_ROOT,
    now_utc: Any | None = None,
) -> dict[str, Any]:
    config, lock = load_and_verify_preregistration()
    day = _entry_date(entry_date)
    evaluated = (
        datetime.now(timezone.utc)
        if now_utc is None
        else _utc(now_utc)
    )
    decision_time = _decision_time(config, day)
    if evaluated < decision_time:
        return status(
            day,
            source_root=source_root,
            ownership_root=ownership_root,
            ledger_root=ledger_root,
            now_utc=evaluated,
        )
    existing = _validated_existing_decision(ledger_root, day)
    if existing is not None:
        return existing
    source_manifests = [
        row
        for row in _validated_manifests(source_root, day)
        if row["status"] == "COMPLETE_ON_TIME"
        and _utc(row["capture_completed_at_utc"]) <= decision_time
    ]
    selected_source = min(
        source_manifests,
        key=lambda row: row["capture_completed_at_utc"],
        default=None,
    )
    ownership = _validated_existing_ownership(
        ownership_root,
        pd.Timestamp(day, tz="UTC"),
    )
    signal_result: dict[str, Any]
    if selected_source is None:
        decision_status = "CASH_MISSING_ON_TIME_SOURCE"
        signal_result = {"status": decision_status, "side": None}
    elif ownership is None:
        decision_status = "CASH_MISSING_ON_TIME_OWNERSHIP"
        signal_result = {"status": decision_status, "side": None}
    else:
        record_path = ownership_root / ownership[
            "ownership_record_relative_path"
        ]
        ownership_record = json.loads(
            record_path.read_text(encoding="utf-8")
        )
        if _utc(ownership_record["ownership_observed_at_utc"]) > decision_time:
            decision_status = "CASH_LATE_OWNERSHIP"
            signal_result = {"status": decision_status, "side": None}
        elif ownership["status"] != "NEUTRAL_OWNED":
            decision_status = "CASH_DATE_NOT_NEUTRAL"
            signal_result = {"status": decision_status, "side": None}
        else:
            normalized_path = source_root / selected_source[
                "normalized"
            ]["relative_path"]
            normalized = json.loads(
                normalized_path.read_text(encoding="utf-8")
            )
            signal_result = compute_signal(
                config,
                normalized["documents"],
            )
            decision_status = str(signal_result["status"])
    decision = {
        "schema_version": SCHEMA_VERSION,
        "campaign_id": config["campaign_id"],
        "entry_date_utc": day.isoformat(),
        "evaluated_at_utc": evaluated.isoformat(),
        "decision_time_utc": decision_time.isoformat(),
        "status": decision_status,
        "side": signal_result.get("side"),
        "signal_evidence": signal_result,
        "source_manifest": (
            {
                "relative_path": selected_source[
                    "manifest_relative_path"
                ],
                "sha256": selected_source["manifest_sha256"],
            }
            if selected_source is not None
            else None
        ),
        "ownership": (
            {
                "record_relative_path": ownership[
                    "ownership_record_relative_path"
                ],
                "record_sha256": ownership["ownership_record_sha256"],
                "evidence_sha256": ownership[
                    "ownership_evidence_sha256"
                ],
                "status": ownership["status"],
            }
            if ownership is not None
            else None
        ),
        "preregistration_lock_sha256": sha256_file(
            ROOT
            / (
                "EURUSD_NEUTRAL_PROSPECTIVE_GDELT_RELATIVE_TONE_"
                "PREREG_2026_07_28.sha256.json"
            )
        ),
        "implementation_lock_sha256": sha256_file(
            IMPLEMENTATION_LOCK_PATH
        ),
        "preregistration_locked_at_utc": lock["locked_at_utc"],
        "decision_source_sha256": sha256_file(Path(__file__)),
        "historical_eurusd_prices_loaded": False,
        "historical_eurusd_pnl_loaded": False,
        "oracle_rows_loaded": False,
        "trade_created": False,
        "broker_action_allowed": False,
    }
    payload = _json_bytes(decision)
    digest = _sha256_bytes(payload)
    relative = (
        Path("decisions")
        / f"DECISION_{day.isoformat()}_{digest[:16]}.json"
    )
    write_immutable(ledger_root / relative, payload)
    return {
        **decision,
        "decision_relative_path": relative.as_posix(),
        "decision_sha256": digest,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("evaluate", "status"))
    parser.add_argument("--entry-date", required=True)
    parser.add_argument(
        "--source-root",
        type=Path,
        default=SOURCE_ROOT,
    )
    parser.add_argument(
        "--ownership-root",
        type=Path,
        default=OWNERSHIP_ROOT,
    )
    parser.add_argument(
        "--ledger-root",
        type=Path,
        default=DEFAULT_LEDGER_ROOT,
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    kwargs = {
        "source_root": args.source_root,
        "ownership_root": args.ownership_root,
        "ledger_root": args.ledger_root,
    }
    if args.command == "evaluate":
        result = evaluate(args.entry_date, **kwargs)
    else:
        result = status(args.entry_date, **kwargs)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
