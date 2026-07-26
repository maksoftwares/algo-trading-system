from __future__ import annotations

import json
import math
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping


SUCCESS_RETCODES = {10008, 10009, 10010}
RETRYABLE_RETCODES = {10004, 10012, 10020, 10021, 10024}


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    source_id: str
    specialist_id: str
    sleeve_type: str
    magic: int
    scheduled_at: datetime
    direction: str
    stop_distance: float
    target_r: float | None
    hold_hours: float | None
    maximum_entry_gap_minutes: int
    maximum_spread_r: float
    maximum_open_positions: int
    maximum_entries_per_utc_day: int
    same_direction_post_loss_cooldown_minutes: int
    initial_risk_usd: float
    event_id: str | None
    raw: Mapping[str, Any]


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_text(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def parse_utc(value: Any) -> datetime:
    text = str(value).strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{number} is not a JSON object")
        rows.append(value)
    return rows


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def append_event(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def initial_state(now: datetime, equity: float) -> dict[str, Any]:
    return {
        "schema_version": "xauusd_v60_canonical_demo_state_v2",
        "activated_at_utc": utc_text(now),
        "activation_equity_usd": float(equity),
        "peak_equity_usd": float(equity),
        "closed_pnl_usd": 0.0,
        "peak_closed_pnl_usd": 0.0,
        "closed_drawdown_usd": 0.0,
        "drawdown_suspended": False,
        "seen": {},
        "positions": {},
        "daily_entries": {},
    }


def load_state(path: Path, now: datetime, equity: float) -> dict[str, Any]:
    if not path.is_file():
        return initial_state(now, equity)
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("schema_version") != "xauusd_v60_canonical_demo_state_v2":
        raise ValueError("Unexpected V60 demo state schema")
    return state


def _finite_positive(value: Any, field: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{field} must be finite and positive")
    return number


def normalize_candidate(
    row: Mapping[str, Any], source: Mapping[str, Any], point: float
) -> Candidate | None:
    source_specialist = str(source["specialist_id"])
    row_specialist = str(row.get("specialist_id", source_specialist))
    if row_specialist != source_specialist:
        return None

    allowed = source.get("allowed_origin_attempts")
    if allowed is not None and int(row.get("origin_attempt", -1)) not in {
        int(value) for value in allowed
    }:
        return None
    required_weight = source.get("required_risk_weight")
    if required_weight is not None and not math.isclose(
        float(row.get("risk_weight", float("nan"))),
        float(required_weight),
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        return None

    candidate_id = str(row.get("candidate_id", "")).strip()
    if not candidate_id:
        raise ValueError("Candidate lacks candidate_id")
    scheduled = parse_utc(row[source["time_field"]])
    direction = str(row.get("direction", "")).upper()
    if direction not in {"LONG", "SHORT"}:
        sign = int(row.get("direction_sign", 0))
        direction = "LONG" if sign > 0 else "SHORT" if sign < 0 else ""
    if direction not in {"LONG", "SHORT"}:
        raise ValueError(f"Candidate {candidate_id} has invalid direction")

    mode = str(source["stop_mode"])
    if mode == "DISTANCE":
        stop_distance = _finite_positive(row["stop_distance"], "stop_distance")
    elif mode == "POINTS":
        stop_distance = _finite_positive(row["stop_points"], "stop_points") * point
    elif mode == "ATR":
        stop_distance = _finite_positive(
            row["signal_atr"], "signal_atr"
        ) * _finite_positive(row["stop_atr"], "stop_atr")
    else:
        raise ValueError(f"Unsupported stop mode: {mode}")

    target_value = row.get("target_r", source.get("target_r_default"))
    target_r = (
        None if target_value is None else _finite_positive(target_value, "target_r")
    )
    hold_value = row.get("hold_hours")
    hold_hours = (
        None if hold_value in (None, "") else _finite_positive(hold_value, "hold_hours")
    )
    sleeve_type = str(source.get("sleeve_type", "CORE")).upper()
    if sleeve_type not in {"CORE", "ADDON"}:
        raise ValueError(f"Unsupported sleeve type: {sleeve_type}")
    initial_risk_usd = stop_distance * float(source.get("ounces_at_lot_size", 1.0))
    maximum_risk = source.get("maximum_risk_usd")
    if maximum_risk is not None and initial_risk_usd > float(maximum_risk):
        return None
    return Candidate(
        candidate_id=candidate_id,
        source_id=str(source["source_id"]),
        specialist_id=source_specialist,
        sleeve_type=sleeve_type,
        magic=int(source["magic"]),
        scheduled_at=scheduled,
        direction=direction,
        stop_distance=stop_distance,
        target_r=target_r,
        hold_hours=hold_hours,
        maximum_entry_gap_minutes=int(source["maximum_entry_gap_minutes"]),
        maximum_spread_r=float(source["maximum_spread_r"]),
        maximum_open_positions=int(source["maximum_open_positions"]),
        maximum_entries_per_utc_day=int(source["maximum_entries_per_utc_day"]),
        same_direction_post_loss_cooldown_minutes=int(
            source.get("same_direction_post_loss_cooldown_minutes", 0)
        ),
        initial_risk_usd=initial_risk_usd,
        event_id=(None if row.get("event_id") in (None, "") else str(row["event_id"])),
        raw=row,
    )


def candidate_prices(
    candidate: Candidate,
    *,
    bid: float,
    ask: float,
    digits: int,
    minimum_stop_distance: float,
) -> tuple[float, float, float]:
    spread = ask - bid
    if spread <= 0.0:
        raise ValueError("Broker spread is not positive")
    if spread / candidate.stop_distance > candidate.maximum_spread_r:
        raise ValueError("SPREAD_R_EXCEEDED")
    if candidate.stop_distance < minimum_stop_distance:
        raise ValueError("BROKER_MINIMUM_STOP_EXCEEDED")
    entry = ask if candidate.direction == "LONG" else bid
    sign = 1.0 if candidate.direction == "LONG" else -1.0
    stop = entry - sign * candidate.stop_distance
    target = 0.0
    if candidate.target_r is not None:
        target = entry + sign * candidate.target_r * candidate.stop_distance
    return round(entry, digits), round(stop, digits), round(target, digits)


def source_positions(positions: Iterable[Any], magic: int, symbol: str) -> list[Any]:
    return [
        position
        for position in positions
        if int(getattr(position, "magic", -1)) == magic
        and str(getattr(position, "symbol", "")) == symbol
    ]


def own_positions(positions: Iterable[Any], magics: set[int], symbol: str) -> list[Any]:
    return [
        position
        for position in positions
        if int(getattr(position, "magic", -1)) in magics
        and str(getattr(position, "symbol", "")) == symbol
    ]


def refresh_drawdown_state(
    state: dict[str, Any], *, equity: float, closed_pnl: float, risk: Mapping[str, Any]
) -> None:
    state["peak_equity_usd"] = max(float(state["peak_equity_usd"]), float(equity))
    state["closed_pnl_usd"] = float(closed_pnl)
    state["peak_closed_pnl_usd"] = max(
        float(state["peak_closed_pnl_usd"]), float(closed_pnl)
    )
    drawdown = float(state["peak_closed_pnl_usd"]) - float(closed_pnl)
    state["closed_drawdown_usd"] = drawdown
    suspend = effective_risk_threshold_usd(
        state, risk, "closed_drawdown_suspend_usd"
    )
    resume = effective_risk_threshold_usd(
        state, risk, "closed_drawdown_resume_usd"
    )
    if not bool(state["drawdown_suspended"]) and drawdown >= suspend:
        state["drawdown_suspended"] = True
    elif bool(state["drawdown_suspended"]) and drawdown <= resume:
        state["drawdown_suspended"] = False


def effective_risk_threshold_usd(
    state: Mapping[str, Any], risk: Mapping[str, Any], absolute_key: str
) -> float:
    absolute = _finite_positive(risk[absolute_key], absolute_key)
    fraction_key = absolute_key.removesuffix("_usd") + "_fraction"
    fraction = _finite_positive(risk[fraction_key], fraction_key)
    activation_equity = _finite_positive(
        state["activation_equity_usd"], "activation_equity_usd"
    )
    return min(absolute, activation_equity * fraction)


def floating_drawdown(state: Mapping[str, Any], equity: float) -> float:
    return float(state["peak_equity_usd"]) - float(equity)


def daily_key(candidate: Candidate) -> str:
    return f"{candidate.source_id}:{candidate.scheduled_at.date().isoformat()}"


def candidate_comment(candidate: Candidate) -> str:
    tags = {
        "R1_BOX": "R1B",
        "R1_PULLBACK": "R1P",
        "R2_DOWNTREND": "R2",
        "R3_COMPRESSION": "R3",
        "R4_CHOP": "R4",
        "R5_TRANSITION": "R5",
        "V7_SWING_HEALTH": "V7",
        "V8_RETEST_HEALTH": "V8",
        "V25_CHOP": "V25",
        "V57_BREAK_SWING_H4ADX_HIGH": "V57",
    }
    return f"V60{tags[candidate.source_id]}:{candidate.candidate_id[:16]}"[:31]


def due_candidates(
    config: Mapping[str, Any], state: Mapping[str, Any], point: float, now: datetime
) -> list[Candidate]:
    activated = parse_utc(state["activated_at_utc"])
    seen = state.get("seen", {})
    pending: dict[str, Candidate] = {}
    for source in config["sources"]:
        for row in read_jsonl(Path(source["path"])):
            candidate = normalize_candidate(row, source, point)
            if candidate is None or candidate.candidate_id in seen:
                continue
            if candidate.scheduled_at < activated:
                continue
            if candidate.scheduled_at <= now:
                existing = pending.get(candidate.candidate_id)
                if existing is not None:
                    if (
                        existing.source_id != candidate.source_id
                        or existing.scheduled_at != candidate.scheduled_at
                        or existing.direction != candidate.direction
                    ):
                        raise ValueError(
                            f"Conflicting duplicate candidate ID: {candidate.candidate_id}"
                        )
                    continue
                pending[candidate.candidate_id] = candidate
    return sorted(
        pending.values(),
        key=lambda item: (item.scheduled_at, item.source_id, item.candidate_id),
    )


def mark_seen(
    state: dict[str, Any],
    candidate: Candidate,
    status: str,
    now: datetime,
    **details: Any,
) -> None:
    state.setdefault("seen", {})[candidate.candidate_id] = {
        "source_id": candidate.source_id,
        "specialist_id": candidate.specialist_id,
        "sleeve_type": candidate.sleeve_type,
        "event_id": candidate.event_id,
        "scheduled_at_utc": utc_text(candidate.scheduled_at),
        "processed_at_utc": utc_text(now),
        "status": status,
        **details,
    }


def close_deadline(candidate: Candidate, opened_at: datetime) -> str | None:
    if candidate.hold_hours is None:
        return None
    return utc_text(opened_at + timedelta(hours=candidate.hold_hours))
