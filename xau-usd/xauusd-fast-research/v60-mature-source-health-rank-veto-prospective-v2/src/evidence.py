from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping, Sequence


GENESIS_HASH = "0" * 64
EVENT_ORDER = {
    "SCORE_DECISION": 0,
    "BASELINE_EXECUTION_DECISION": 1,
    "BROKER_EXECUTION": 2,
    "BROKER_OUTCOME": 3,
}


def canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def event_hash(previous_hash: str, event: Mapping[str, Any]) -> str:
    material = f"{previous_hash}\n{canonical_json(event)}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def load_chain(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    previous_hash = GENESIS_HASH
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid evidence JSONL at {path}:{line_number}") from exc
        expected_sequence = len(records) + 1
        if int(record.get("sequence", -1)) != expected_sequence:
            raise ValueError(f"Evidence sequence mismatch at {path}:{line_number}")
        if str(record.get("previous_hash")) != previous_hash:
            raise ValueError(f"Evidence previous hash mismatch at {path}:{line_number}")
        unsigned = {key: value for key, value in record.items() if key != "event_hash"}
        expected_hash = event_hash(previous_hash, unsigned)
        if str(record.get("event_hash")) != expected_hash:
            raise ValueError(f"Evidence event hash mismatch at {path}:{line_number}")
        previous_hash = expected_hash
        records.append(record)
    return records


def immutable_events(row: Mapping[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    candidate_id = str(row["candidate_id"])
    common = {
        "candidate_id": candidate_id,
        "event_id": str(row["event_id"]),
        "source_id": str(row["source_id"]),
        "entry_time_utc": str(row["entry_time_utc"]),
    }
    events: list[tuple[str, dict[str, Any]]] = []
    if row.get("causal_rank") is not None:
        events.append(
            (
                "SCORE_DECISION",
                {
                    **common,
                    "causal_score": float(row["causal_score"]),
                    "causal_rank": float(row["causal_rank"]),
                },
            )
        )
    if bool(row.get("baseline_executed")):
        events.append(
            (
                "BASELINE_EXECUTION_DECISION",
                {
                    **common,
                    "prior_source_executed_count": int(
                        row["prior_source_executed_count"]
                    ),
                    "prior_health_window_count": int(row["prior_health_window_count"]),
                    "prior_executed_profit_factor": row.get(
                        "prior_executed_profit_factor"
                    ),
                    "would_veto": bool(row["would_veto"]),
                },
            )
        )
    execution = row.get("broker_execution")
    if execution is not None:
        events.append(
            (
                "BROKER_EXECUTION",
                {
                    **common,
                    "ticket": int(execution["ticket"]),
                    "broker_entry_time_utc": str(
                        execution["broker_entry_time_utc"]
                    ),
                    "direction": str(execution["direction"]),
                    "volume_lots": float(execution["volume_lots"]),
                    "entry_price": float(execution["entry_price"]),
                    "entry_cost_usd": float(execution["entry_cost_usd"]),
                },
            )
        )
    if bool(row.get("broker_outcome_resolved")):
        exit_fills = row.get("broker_exit_fills")
        if exit_fills is None:
            raise ValueError(
                f"Resolved broker outcome lacks exit fills: {candidate_id}"
            )
        events.append(
            (
                "BROKER_OUTCOME",
                {
                    **common,
                    "broker_exit_time_utc": str(row["broker_exit_time_utc"]),
                    "broker_pnl_usd": float(row["broker_pnl_usd"]),
                    "exit_fills": list(exit_fills),
                },
            )
        )
    return events


def update_evidence_chain(
    output_directory: Path,
    rows: Sequence[Mapping[str, Any]],
    *,
    observed_at: datetime | None = None,
) -> dict[str, Any]:
    observed_at = (observed_at or datetime.now(UTC)).astimezone(UTC)
    path = output_directory / "EVIDENCE_CHAIN.jsonl"
    head_path = output_directory / "EVIDENCE_HEAD.json"
    records = load_chain(path)
    existing: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        key = (str(record["event_type"]), str(record["payload"]["candidate_id"]))
        if key in existing:
            raise ValueError(f"Duplicate immutable evidence event: {key}")
        existing[key] = dict(record["payload"])

    pending: list[tuple[str, dict[str, Any]]] = []
    for row in rows:
        for event_type, payload in immutable_events(row):
            if event_type == "BROKER_EXECUTION" and observed_at < utc_time(
                payload["broker_entry_time_utc"]
            ):
                raise ValueError("Broker execution was observed before its entry time")
            if event_type == "BROKER_OUTCOME" and observed_at < utc_time(
                payload["broker_exit_time_utc"]
            ):
                raise ValueError("Broker outcome was observed before its exit time")
            key = (event_type, str(payload["candidate_id"]))
            if key in existing:
                if canonical_json(existing[key]) != canonical_json(payload):
                    raise ValueError(
                        f"Immutable prospective evidence changed: {event_type}: "
                        f"{payload['candidate_id']}"
                    )
                continue
            pending.append((event_type, payload))
            existing[key] = payload

    pending.sort(
        key=lambda item: (
            str(item[1]["entry_time_utc"]),
            str(item[1]["candidate_id"]),
            EVENT_ORDER[item[0]],
        )
    )
    previous_hash = str(records[-1]["event_hash"]) if records else GENESIS_HASH
    for event_type, payload in pending:
        unsigned = {
            "sequence": len(records) + 1,
            "previous_hash": previous_hash,
            "observed_at_utc": observed_at.isoformat().replace("+00:00", "Z"),
            "event_type": event_type,
            "payload": payload,
        }
        digest = event_hash(previous_hash, unsigned)
        record = {**unsigned, "event_hash": digest}
        records.append(record)
        previous_hash = digest

    atomic_write(
        path,
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in records),
    )
    counts: dict[str, int] = {}
    for record in records:
        event_type = str(record["event_type"])
        counts[event_type] = counts.get(event_type, 0) + 1
    audit = {
        "schema_version": "v60_v2_prospective_evidence_chain_v1",
        "status": "VERIFIED",
        "chain_path": str(path),
        "records": len(records),
        "new_records": len(pending),
        "event_counts": dict(sorted(counts.items())),
        "head_sha256": previous_hash,
    }
    atomic_write(head_path, json.dumps(audit, indent=2, sort_keys=True) + "\n")
    return audit


def utc_time(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Prospective timestamp is not timezone-aware: {value}")
    return parsed.astimezone(UTC)


def annotate_decision_timing(
    output_directory: Path,
    rows: Sequence[dict[str, Any]],
    *,
    maximum_delay_seconds: int,
) -> dict[str, Any]:
    maximum_delay = int(maximum_delay_seconds)
    if maximum_delay <= 0:
        raise ValueError("Maximum decision recording delay must be positive")
    records = load_chain(output_directory / "EVIDENCE_CHAIN.jsonl")
    event_records: dict[tuple[str, str], Mapping[str, Any]] = {}
    for record in records:
        key = (str(record["event_type"]), str(record["payload"]["candidate_id"]))
        if key in event_records:
            raise ValueError(f"Duplicate immutable timing event: {key}")
        event_records[key] = record

    executed = 0
    valid = 0
    reasons: dict[str, int] = {}
    for row in rows:
        candidate_id = str(row["candidate_id"])
        row["prospective_score_recorded_at_utc"] = None
        row["prospective_execution_decision_recorded_at_utc"] = None
        row["prospective_decision_latest_recorded_at_utc"] = None
        row["prospective_decision_recording_delay_seconds"] = None
        row["prospective_decision_timing_valid"] = False
        row["prospective_veto_effective"] = False
        if not bool(row.get("baseline_executed")):
            reason = "BASELINE_NOT_EXECUTED"
        else:
            executed += 1
            score = event_records.get(("SCORE_DECISION", candidate_id))
            decision = event_records.get(
                ("BASELINE_EXECUTION_DECISION", candidate_id)
            )
            if row.get("causal_rank") is None:
                reason = "MISSING_CAUSAL_RANK"
            elif score is None:
                reason = "SCORE_NOT_IMMUTABLY_RECORDED"
            elif decision is None:
                reason = "EXECUTION_DECISION_NOT_IMMUTABLY_RECORDED"
            else:
                score_observed = utc_time(score["observed_at_utc"])
                decision_observed = utc_time(decision["observed_at_utc"])
                latest_observed = max(score_observed, decision_observed)
                entry = utc_time(row["entry_time_utc"])
                delay_seconds = max(
                    0.0, (latest_observed - entry).total_seconds()
                )
                row[
                    "prospective_score_recorded_at_utc"
                ] = score_observed.isoformat().replace("+00:00", "Z")
                row[
                    "prospective_execution_decision_recorded_at_utc"
                ] = decision_observed.isoformat().replace("+00:00", "Z")
                row[
                    "prospective_decision_latest_recorded_at_utc"
                ] = latest_observed.isoformat().replace("+00:00", "Z")
                row[
                    "prospective_decision_recording_delay_seconds"
                ] = delay_seconds
                if latest_observed > entry + timedelta(seconds=maximum_delay):
                    reason = "RECORDED_AFTER_MAXIMUM_DELAY"
                elif bool(
                    row.get("broker_outcome_resolved")
                ) and latest_observed >= utc_time(row["broker_exit_time_utc"]):
                    reason = "RECORDED_AFTER_OR_AT_BROKER_EXIT"
                else:
                    reason = "VALID"
                    row["prospective_decision_timing_valid"] = True
                    row["prospective_veto_effective"] = bool(row["would_veto"])
                    valid += 1
        row["prospective_decision_timing_reason"] = reason
        reasons[reason] = reasons.get(reason, 0) + 1
    return {
        "schema_version": "v60_v2_prospective_decision_timing_v1",
        "maximum_delay_seconds": maximum_delay,
        "executed_candidates": executed,
        "valid_executed_candidates": valid,
        "valid_executed_fraction": valid / executed if executed else None,
        "reason_counts": dict(sorted(reasons.items())),
    }


def object_value(value: Any, name: str) -> Any:
    return value[name] if isinstance(value, Mapping) else getattr(value, name)


def attach_execution_details(
    rows: Sequence[dict[str, Any]],
    state: Mapping[str, Any],
    deals: Sequence[Any],
    *,
    account_currency_per_usd: float,
) -> None:
    rate = float(account_currency_per_usd)
    if rate <= 0.0:
        raise ValueError("Account-currency conversion rate must be positive")
    deals_by_position: dict[int, list[Any]] = {}
    for deal in deals:
        deals_by_position.setdefault(int(object_value(deal, "position_id")), []).append(
            deal
        )
    state_positions = state.get("positions", {})
    for row in rows:
        if not bool(row.get("baseline_executed")):
            continue
        candidate_id = str(row["candidate_id"])
        state_position = state_positions.get(candidate_id)
        if state_position is None:
            raise ValueError(
                f"Executed candidate has no portfolio state: {candidate_id}"
            )
        ticket = int(state_position["ticket"])
        entries = [
            deal
            for deal in deals_by_position.get(ticket, [])
            if int(object_value(deal, "entry")) == 0
        ]
        if not entries:
            continue
        direction_types = {int(object_value(deal, "type")) for deal in entries}
        if len(direction_types) != 1 or next(iter(direction_types)) not in (0, 1):
            raise ValueError(f"Ambiguous broker entry direction: {candidate_id}")
        volume = sum(float(object_value(deal, "volume")) for deal in entries)
        if volume <= 0.0:
            raise ValueError(f"Nonpositive broker entry volume: {candidate_id}")
        weighted_price = sum(
            float(object_value(deal, "price"))
            * float(object_value(deal, "volume"))
            for deal in entries
        ) / volume
        entry_cost_account = sum(
            sum(
                float(object_value(deal, key))
                for key in ("profit", "commission", "swap", "fee")
            )
            for deal in entries
        )
        row["broker_execution"] = {
            "ticket": ticket,
            "broker_entry_time_utc": datetime.fromtimestamp(
                min(int(object_value(deal, "time_msc")) for deal in entries)
                / 1000.0,
                UTC,
            )
            .isoformat()
            .replace("+00:00", "Z"),
            "direction": "LONG" if next(iter(direction_types)) == 0 else "SHORT",
            "volume_lots": volume,
            "entry_price": weighted_price,
            "entry_cost_usd": entry_cost_account / rate,
        }
        if bool(row.get("broker_outcome_resolved")):
            exits = [
                deal
                for deal in deals_by_position.get(ticket, [])
                if int(object_value(deal, "entry")) != 0
            ]
            if not exits:
                raise ValueError(f"Resolved candidate has no exit fills: {candidate_id}")
            closed_volume = sum(float(object_value(deal, "volume")) for deal in exits)
            if abs(closed_volume - volume) > 1e-8:
                raise ValueError(
                    f"Resolved candidate volume does not reconcile: {candidate_id}: "
                    f"entry={volume}: exit={closed_volume}"
                )
            exit_fills = []
            for deal in sorted(
                exits,
                key=lambda item: (
                    int(object_value(item, "time_msc")),
                    int(object_value(item, "ticket")),
                ),
            ):
                exit_fills.append(
                    {
                        "deal_ticket": int(object_value(deal, "ticket")),
                        "exit_time_utc": datetime.fromtimestamp(
                            int(object_value(deal, "time_msc")) / 1000.0,
                            UTC,
                        )
                        .isoformat()
                        .replace("+00:00", "Z"),
                        "volume_lots": float(object_value(deal, "volume")),
                        "exit_price": float(object_value(deal, "price")),
                        "pnl_usd": sum(
                            float(object_value(deal, key))
                            for key in ("profit", "commission", "swap", "fee")
                        )
                        / rate,
                    }
                )
            lifecycle_pnl = entry_cost_account / rate + sum(
                float(fill["pnl_usd"]) for fill in exit_fills
            )
            if abs(lifecycle_pnl - float(row["broker_pnl_usd"])) > 1e-8:
                raise ValueError(
                    f"Resolved candidate P/L does not reconcile: {candidate_id}"
                )
            row["broker_exit_fills"] = exit_fills


def build_equity_mark(
    rows: Sequence[Mapping[str, Any]],
    state: Mapping[str, Any],
    deals: Sequence[Any],
    open_positions: Sequence[Any],
    *,
    account_currency_per_usd: float,
    observed_at: datetime,
) -> dict[str, Any]:
    rate = float(account_currency_per_usd)
    if rate <= 0.0:
        raise ValueError("Account-currency conversion rate must be positive")
    deals_by_position: dict[int, list[Any]] = {}
    for deal in deals:
        deals_by_position.setdefault(int(object_value(deal, "position_id")), []).append(
            deal
        )
    positions_by_ticket = {
        int(object_value(position, "ticket")): position for position in open_positions
    }
    state_positions = state.get("positions", {})
    baseline_pnl = 0.0
    challenger_pnl = 0.0
    resolved = 0
    open_count = 0
    for row in rows:
        if not bool(row.get("baseline_executed")):
            continue
        candidate_id = str(row["candidate_id"])
        if bool(row.get("broker_outcome_resolved")):
            pnl_usd = float(row["broker_pnl_usd"])
            resolved += 1
        else:
            state_position = state_positions.get(candidate_id)
            if state_position is None:
                raise ValueError(
                    f"Executed unresolved candidate has no portfolio state: {candidate_id}"
                )
            ticket = int(state_position["ticket"])
            position = positions_by_ticket.get(ticket)
            if position is None:
                raise ValueError(
                    f"Executed unresolved candidate has no open MT5 position: {candidate_id}"
                )
            realized_account = sum(
                sum(
                    float(object_value(deal, key))
                    for key in ("profit", "commission", "swap", "fee")
                )
                for deal in deals_by_position.get(ticket, [])
            )
            floating_account = float(object_value(position, "profit")) + float(
                object_value(position, "swap")
            )
            pnl_usd = (realized_account + floating_account) / rate
            open_count += 1
        baseline_pnl += pnl_usd
        if not bool(row.get("prospective_veto_effective", False)):
            challenger_pnl += pnl_usd
    return {
        "observed_at_utc": observed_at.astimezone(UTC)
        .isoformat()
        .replace("+00:00", "Z"),
        "baseline_v60_equity_pnl_usd": baseline_pnl,
        "challenger_v2_equity_pnl_usd": challenger_pnl,
        "delta_equity_pnl_usd": challenger_pnl - baseline_pnl,
        "resolved_baseline_positions": resolved,
        "open_baseline_positions": open_count,
    }


def update_equity_marks(
    output_directory: Path,
    mark: Mapping[str, Any],
    *,
    boundary: datetime,
    minimum_marks: int,
) -> dict[str, Any]:
    path = output_directory / "EQUITY_MARKS.jsonl"
    head_path = output_directory / "EQUITY_HEAD.json"
    observed_at = datetime.fromisoformat(
        str(mark["observed_at_utc"]).replace("Z", "+00:00")
    ).astimezone(UTC)
    records = load_chain(path)
    if observed_at >= boundary.astimezone(UTC):
        if records:
            last_observed = datetime.fromisoformat(
                str(records[-1]["payload"]["observed_at_utc"]).replace(
                    "Z", "+00:00"
                )
            ).astimezone(UTC)
            if observed_at <= last_observed:
                raise ValueError("Prospective equity marks are not strictly chronological")
        previous_hash = str(records[-1]["event_hash"]) if records else GENESIS_HASH
        unsigned = {
            "sequence": len(records) + 1,
            "previous_hash": previous_hash,
            "observed_at_utc": str(mark["observed_at_utc"]),
            "event_type": "PORTFOLIO_EQUITY_MARK",
            "payload": dict(mark),
        }
        digest = event_hash(previous_hash, unsigned)
        records.append({**unsigned, "event_hash": digest})

    atomic_write(
        path,
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in records),
    )
    baseline_values = [
        float(record["payload"]["baseline_v60_equity_pnl_usd"])
        for record in records
    ]
    challenger_values = [
        float(record["payload"]["challenger_v2_equity_pnl_usd"])
        for record in records
    ]
    baseline_dd = closed_drawdown_from_equity_marks(baseline_values)
    challenger_dd = closed_drawdown_from_equity_marks(challenger_values)
    audit = {
        "schema_version": "v60_v2_prospective_equity_marks_v1",
        "status": "VERIFIED",
        "chain_path": str(path),
        "marks": len(records),
        "head_sha256": (
            str(records[-1]["event_hash"]) if records else GENESIS_HASH
        ),
        "baseline_v60_sampled_equity_drawdown_usd": baseline_dd,
        "challenger_v2_sampled_equity_drawdown_usd": challenger_dd,
        "delta_sampled_equity_drawdown_usd": challenger_dd - baseline_dd,
        "minimum_marks_gate": len(records) >= int(minimum_marks),
        "challenger_drawdown_not_worse_gate": challenger_dd <= baseline_dd,
        "latest_mark": dict(records[-1]["payload"]) if records else None,
    }
    atomic_write(head_path, json.dumps(audit, indent=2, sort_keys=True) + "\n")
    return audit


def profit_factor(values: Sequence[float]) -> float:
    gross_profit = sum(value for value in values if value > 0.0)
    gross_loss = -sum(value for value in values if value < 0.0)
    if gross_loss == 0.0:
        return math.inf if gross_profit > 0.0 else 0.0
    return gross_profit / gross_loss


def closed_drawdown(values: Sequence[float]) -> float:
    equity = 0.0
    peak = 0.0
    maximum = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        maximum = max(maximum, peak - equity)
    return maximum


def closed_drawdown_from_equity_marks(values: Sequence[float]) -> float:
    peak = 0.0
    maximum = 0.0
    for value in values:
        peak = max(peak, value)
        maximum = max(maximum, peak - value)
    return maximum


def metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ordered = sorted(
        rows,
        key=lambda row: (str(row["broker_exit_time_utc"]), str(row["candidate_id"])),
    )
    values = [float(row["broker_pnl_usd"]) for row in ordered]
    pf = profit_factor(values)
    return {
        "trades": len(values),
        "wins": sum(value > 0.0 for value in values),
        "losses": sum(value < 0.0 for value in values),
        "net_pnl_usd": sum(values),
        "profit_factor": pf if math.isfinite(pf) else None,
        "profit_factor_infinite": math.isinf(pf),
        "win_rate": (
            sum(value > 0.0 for value in values) / len(values) if values else None
        ),
        "closed_drawdown_usd": closed_drawdown(values),
    }


def pf_not_worse(challenger: Mapping[str, Any], baseline: Mapping[str, Any]) -> bool:
    if bool(baseline["profit_factor_infinite"]):
        return bool(challenger["profit_factor_infinite"])
    if bool(challenger["profit_factor_infinite"]):
        return True
    return float(challenger["profit_factor"] or 0.0) >= float(
        baseline["profit_factor"] or 0.0
    )


def add_forward_comparison(
    status: dict[str, Any],
    rows: Sequence[Mapping[str, Any]],
    acceptance: Mapping[str, Any],
) -> None:
    resolved = [
        row
        for row in rows
        if bool(row.get("baseline_executed"))
        and bool(row.get("broker_outcome_resolved"))
    ]
    challenger_rows = [
        row
        for row in resolved
        if not bool(row.get("prospective_veto_effective", False))
    ]
    baseline = metrics(resolved)
    challenger = metrics(challenger_rows)
    resolved_count = int(baseline["trades"])
    retention = (
        int(challenger["trades"]) / resolved_count if resolved_count else None
    )
    scored_resolved = sum(row.get("causal_rank") is not None for row in resolved)
    rank_coverage = scored_resolved / resolved_count if resolved_count else None
    valid_timing_resolved = sum(
        bool(row.get("prospective_decision_timing_valid")) for row in resolved
    )
    timing_coverage = (
        valid_timing_resolved / resolved_count if resolved_count else None
    )
    detailed_resolved = sum(
        row.get("broker_execution") is not None for row in resolved
    )
    execution_detail_coverage = (
        detailed_resolved / resolved_count if resolved_count else None
    )
    comparison = {
        "baseline_v60": baseline,
        "challenger_v2": challenger,
        "delta_net_pnl_usd": float(challenger["net_pnl_usd"])
        - float(baseline["net_pnl_usd"]),
        "delta_closed_drawdown_usd": float(challenger["closed_drawdown_usd"])
        - float(baseline["closed_drawdown_usd"]),
        "trade_retention": retention,
        "resolved_rank_coverage": rank_coverage,
        "resolved_prospective_decision_timing_coverage": timing_coverage,
        "resolved_execution_detail_coverage": execution_detail_coverage,
    }
    executed = [row for row in rows if bool(row.get("baseline_executed"))]
    valid_scored_executed = sum(
        row.get("causal_rank") is not None
        and bool(row.get("prospective_decision_timing_valid"))
        for row in executed
    )
    raw_vetoes = [row for row in executed if bool(row.get("would_veto"))]
    effective_vetoes = [
        row for row in executed if bool(row.get("prospective_veto_effective"))
    ]
    resolved_effective_vetoes = [
        row for row in effective_vetoes if bool(row.get("broker_outcome_resolved"))
    ]
    veto_values = [
        float(row["broker_pnl_usd"]) for row in resolved_effective_vetoes
    ]
    veto_pf = profit_factor(veto_values) if veto_values else None
    avoided_pnl = -sum(veto_values)
    status["forward_comparison"] = comparison
    status["counts"]["raw_executed_scored_candidates"] = status["counts"].get(
        "executed_scored_candidates", 0
    )
    status["counts"]["executed_scored_candidates"] = valid_scored_executed
    status["counts"]["raw_veto_opportunities"] = len(raw_vetoes)
    status["counts"]["veto_opportunities"] = len(effective_vetoes)
    status["counts"]["resolved_vetoes"] = len(resolved_effective_vetoes)
    status["counts"]["resolved_baseline_executions"] = resolved_count
    status["counts"]["resolved_scored_baseline_executions"] = scored_resolved
    status["counts"][
        "resolved_prospective_timing_valid_executions"
    ] = valid_timing_resolved
    status["counts"]["resolved_detailed_baseline_executions"] = detailed_resolved
    status["veto_broker_net_pnl_usd"] = sum(veto_values)
    status["avoided_broker_pnl_usd"] = avoided_pnl
    status["veto_broker_profit_factor"] = (
        veto_pf if veto_pf is not None and math.isfinite(veto_pf) else None
    )
    status["gates"].update(
        {
            "minimum_scored_executed_candidates": valid_scored_executed
            >= int(acceptance["minimum_scored_executed_candidates"]),
            "minimum_resolved_vetoes": len(resolved_effective_vetoes)
            >= int(acceptance["minimum_resolved_vetoes"]),
            "veto_broker_profit_factor": veto_pf is not None
            and veto_pf
            < float(acceptance["maximum_veto_broker_profit_factor_exclusive"]),
            "positive_avoided_broker_pnl": avoided_pnl
            > float(acceptance["minimum_avoided_broker_pnl_usd_exclusive"]),
            "minimum_resolved_baseline_executions": resolved_count
            >= int(acceptance["minimum_resolved_baseline_executions"]),
            "complete_resolved_rank_coverage": rank_coverage is not None
            and rank_coverage >= float(acceptance["minimum_resolved_rank_coverage"]),
            "complete_resolved_prospective_decision_timing_coverage": (
                timing_coverage is not None
                and timing_coverage
                >= float(
                    acceptance["minimum_resolved_prospective_timing_coverage"]
                )
            ),
            "complete_resolved_execution_detail_coverage": (
                execution_detail_coverage is not None
                and execution_detail_coverage
                >= float(acceptance["minimum_resolved_execution_detail_coverage"])
            ),
            "minimum_trade_retention": retention is not None
            and retention >= float(acceptance["minimum_trade_retention"]),
            "challenger_net_pnl_not_worse": float(challenger["net_pnl_usd"])
            >= float(baseline["net_pnl_usd"]),
            "challenger_profit_factor_not_worse": pf_not_worse(
                challenger, baseline
            ),
            "challenger_closed_drawdown_not_worse": float(
                challenger["closed_drawdown_usd"]
            )
            <= float(baseline["closed_drawdown_usd"]),
        }
    )
    status["decision"] = (
        "PROSPECTIVE_CONFIRMATION_PASSES_REVIEW_REQUIRED"
        if all(status["gates"].values())
        else "KEEP_DEPLOYED_V60_CONTINUE_COLLECTION"
    )
