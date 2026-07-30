from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from . import forward_residual_regime_specialist as strategy
from . import forward_selective_learner as base

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = (
    ROOT / "config" / "frozen_forward_residual_live_signal_publisher_v1.json"
)
LOCK_PATH = (
    ROOT
    / "EURUSD_FORWARD_RESIDUAL_LIVE_SIGNAL_PUBLISHER_LOCK_2026_07_30.sha256.json"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_lock() -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    required = {
        "locked_before_forward_floor": True,
        "locked_with_zero_forward_feature_rows": True,
        "locked_with_zero_live_decisions": True,
        "historical_backfill_allowed": False,
        "demo_order_authorized": False,
    }
    if any(lock.get(key) is not value for key, value in required.items()):
        raise RuntimeError("residual live-publisher lock boundary is incomplete")
    for relative, expected in lock["files"].items():
        if sha256(ROOT / relative) != expected:
            raise RuntimeError(f"residual live-publisher drift: {relative}")
    return lock


def load_publisher_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("campaign_id") != "EURUSD_FORWARD_RESIDUAL_LIVE_SIGNAL_V1":
        raise ValueError("unexpected residual live-publisher campaign")
    if config.get("demo_order_authorized"):
        raise ValueError("live-publisher config unexpectedly authorizes orders")
    return config


def load_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise TypeError(f"{path.name} is not a JSON list")
    return value


def _utc_text(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def publication_window(
    day: date,
    strategy_config: dict[str, Any],
    publisher_config: dict[str, Any],
) -> tuple[datetime, datetime]:
    decision = strategy.decision_datetime(day, strategy_config).replace(
        tzinfo=UTC
    )
    start = decision + timedelta(
        seconds=int(publisher_config["publication_not_before_seconds"])
    )
    deadline = decision + timedelta(
        seconds=int(publisher_config["publication_deadline_seconds"])
    )
    return start, deadline


def reconstruct_histories(
    prior_records: list[dict[str, Any]],
    current_day: date,
    strategy_config: dict[str, Any],
) -> tuple[dict[str, dict[str, list[float]]], int]:
    regimes = strategy_config["causal_regimes"]["ordered_rules"]
    histories: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"LONG": [], "SHORT": []}
    )
    seen_dates: set[str] = set()
    resolved_days = 0
    previous_date = ""
    for record in prior_records:
        day_text = str(record.get("decision_date", ""))
        if not day_text:
            raise ValueError("residual training record lacks decision_date")
        if day_text < previous_date:
            raise ValueError("residual training ledger is not chronological")
        previous_date = day_text
        if day_text in seen_dates:
            raise ValueError(f"duplicate residual training date: {day_text}")
        seen_dates.add(day_text)
        record_day = date.fromisoformat(day_text)
        if record_day >= current_day:
            raise ValueError("current or future outcome leaked into live decision")
        if record.get("status") != "RESOLVED":
            continue
        regime = str(record.get("regime", ""))
        if regime not in regimes:
            raise ValueError(f"unknown residual training regime: {regime}")
        for side, key in (
            ("LONG", "long_outcome"),
            ("SHORT", "short_outcome"),
        ):
            outcome = record.get(key)
            if not isinstance(outcome, dict) or outcome.get("side") != side:
                raise ValueError("residual training outcome is incomplete")
            histories[regime][side].append(float(outcome["result_r"]))
        resolved_days += 1
    for regime in regimes:
        histories[regime]
    return histories, resolved_days


def _base_decision(
    day: date,
    now: datetime,
    strategy_config: dict[str, Any],
    publisher_config: dict[str, Any],
) -> dict[str, Any]:
    decision_time = strategy.decision_datetime(day, strategy_config).replace(
        tzinfo=UTC
    )
    return {
        "decision_id": f"{publisher_config['campaign_id']}|{day.isoformat()}",
        "campaign_id": publisher_config["campaign_id"],
        "strategy_campaign_id": strategy_config["campaign_id"],
        "decision_date": day.isoformat(),
        "decision_time_utc": _utc_text(decision_time),
        "published_at_utc": _utc_text(now),
        "eligible_side": "CASH",
        "regime": None,
        "demo_order_authorized": False,
    }


def validate_existing(
    existing: list[dict[str, Any]],
    publisher_config: dict[str, Any],
) -> None:
    seen_ids: set[str] = set()
    seen_dates: set[str] = set()
    previous = ""
    for record in existing:
        if record.get("campaign_id") != publisher_config["campaign_id"]:
            raise ValueError("live decision ledger campaign mismatch")
        decision_id = str(record.get("decision_id", ""))
        day_text = str(record.get("decision_date", ""))
        if not decision_id or decision_id in seen_ids:
            raise ValueError("missing or duplicate live decision id")
        if not day_text or day_text in seen_dates or day_text < previous:
            raise ValueError("live decision dates are duplicate or unordered")
        if record.get("demo_order_authorized") is not False:
            raise ValueError("live decision ledger contains order authorization")
        seen_ids.add(decision_id)
        seen_dates.add(day_text)
        previous = day_text


def process_once(
    grouped: dict[datetime, dict[str, base.Bar]],
    prior_records: list[dict[str, Any]],
    upstream_owned_dates: set[str],
    existing: list[dict[str, Any]],
    now: datetime,
    strategy_config: dict[str, Any],
    publisher_config: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if now.tzinfo is None:
        raise ValueError("live publication clock must be timezone-aware")
    now = now.astimezone(UTC)
    validate_existing(existing, publisher_config)
    floor = datetime.strptime(
        str(publisher_config["forward_floor_utc"]),
        base.TIME_FORMAT,
    ).replace(tzinfo=UTC)
    day = now.date()
    day_text = day.isoformat()
    existing_today = [
        record for record in existing if record["decision_date"] == day_text
    ]
    if existing_today:
        return list(existing), build_summary(existing, "ALREADY_PUBLISHED")
    if now < floor:
        return list(existing), build_summary(existing, "WAITING_FORWARD_FLOOR")
    if day.weekday() >= 5:
        return list(existing), build_summary(existing, "WEEKEND_NO_DECISION")
    start, deadline = publication_window(
        day,
        strategy_config,
        publisher_config,
    )
    if now < start:
        return list(existing), build_summary(existing, "WAITING_DECISION_CLOCK")

    record = _base_decision(
        day,
        now,
        strategy_config,
        publisher_config,
    )
    if now > deadline:
        record.update(
            {
                "status": "CASH_MISSED_PUBLICATION_DEADLINE",
                "eligibility_reason": "NO_LATE_SIGNAL_RECOVERY",
                "training_days_before": None,
            }
        )
    elif day_text in upstream_owned_dates:
        record.update(
            {
                "status": "CASH_UPSTREAM_OWNED",
                "eligibility_reason": "DUPLICATE_OPPORTUNITY_VETO",
                "training_days_before": None,
            }
        )
    else:
        decision_time = strategy.decision_datetime(day, strategy_config)
        context = base.build_context(grouped, decision_time, strategy_config)
        if context is None:
            record.update(
                {
                    "status": "CASH_MISSING_CONTEXT",
                    "eligibility_reason": "MISSING_CONTEXT_AT_PUBLICATION",
                    "training_days_before": None,
                }
            )
        else:
            histories, resolved_days = reconstruct_histories(
                prior_records,
                day,
                strategy_config,
            )
            regime = strategy.classify_regime(context, strategy_config)
            side, reason, statistics = strategy.select_side(
                histories,
                regime,
                resolved_days,
                context,
                strategy_config,
            )
            record.update(
                {
                    "status": (
                        "PUBLISHED_SIGNAL"
                        if side in ("LONG", "SHORT")
                        else "PUBLISHED_CASH"
                    ),
                    "regime": regime,
                    "eligible_side": side,
                    "eligibility_reason": reason,
                    "training_days_before": resolved_days,
                    "context": context,
                    "side_statistics_before": statistics,
                }
            )
    updated = [*existing, base.json_safe(record)]
    return updated, build_summary(updated, str(record["status"]))


def build_summary(
    records: list[dict[str, Any]],
    status: str,
) -> dict[str, Any]:
    return {
        "schema_version": "eurusd_forward_residual_live_signal_summary_v1",
        "campaign_id": "EURUSD_FORWARD_RESIDUAL_LIVE_SIGNAL_V1",
        "status": status,
        "published_decisions": len(records),
        "eligible_signals": sum(
            record.get("eligible_side") in ("LONG", "SHORT")
            for record in records
        ),
        "cash_decisions": sum(
            record.get("eligible_side") == "CASH" for record in records
        ),
        "last_decision_date": (
            records[-1]["decision_date"] if records else None
        ),
        "demo_order_authorized": False,
    }


def write_outputs(
    records: list[dict[str, Any]],
    summary: dict[str, Any],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    decisions_path = output_dir / "FORWARD_RESIDUAL_LIVE_SIGNALS.json"
    if decisions_path.is_file():
        existing = load_json_list(decisions_path)
        if len(records) < len(existing) or records[: len(existing)] != existing:
            raise ValueError("live decision ledger mutation refused")
    base.atomic_write_text(
        decisions_path,
        json.dumps(records, indent=2, sort_keys=True) + "\n",
    )
    base.atomic_write_text(
        output_dir / "FORWARD_RESIDUAL_LIVE_SIGNAL_SUMMARY.json",
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
    )
    base.atomic_write_text(
        output_dir / "FORWARD_RESIDUAL_LIVE_SIGNAL_SUMMARY.md",
        "\n".join(
            [
                "# EURUSD residual live signal publisher",
                "",
                f"Status: **{summary['status']}**",
                "",
                f"- Published decisions: {summary['published_decisions']}",
                f"- Eligible signals: {summary['eligible_signals']}",
                f"- Cash decisions: {summary['cash_decisions']}",
                "- Demo-order authorization: false",
                "",
            ]
        ),
    )
