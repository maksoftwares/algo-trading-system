from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from . import forward_selective_learner as base

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = (
    ROOT
    / "config"
    / "frozen_forward_residual_live_outcome_adjudicator_v1.json"
)
LOCK_PATH = (
    ROOT
    / "EURUSD_FORWARD_RESIDUAL_LIVE_OUTCOME_ADJUDICATOR_LOCK_2026_07_30.sha256.json"
)
TickProvider = Callable[[datetime, datetime], list[dict[str, Any]]]
SELF_TERMINAL_PUBLISHER_STATUSES = {"CASH_MARKET_CLOSURE"}


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
        "locked_with_zero_live_signals": True,
        "locked_with_zero_mt5_receipts": True,
        "locked_with_zero_live_outcomes": True,
        "historical_backfill_allowed": False,
        "demo_order_authorized": False,
    }
    if any(lock.get(key) is not value for key, value in required.items()):
        raise RuntimeError("live outcome lock boundary is incomplete")
    for relative, expected in lock["files"].items():
        if sha256(ROOT / relative) != expected:
            raise RuntimeError(f"live outcome implementation drift: {relative}")
    return lock


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("campaign_id") != "EURUSD_FORWARD_RESIDUAL_LIVE_OUTCOME_V1":
        raise ValueError("unexpected live outcome campaign")
    if config.get("demo_order_authorized"):
        raise ValueError("live outcome config unexpectedly authorizes orders")
    return config


def load_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise TypeError(f"{path.name} is not a JSON list")
    return value


def parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        parsed = datetime.strptime(value, base.TIME_FORMAT).replace(tzinfo=UTC)
    if parsed.tzinfo is None:
        raise ValueError("live outcome timestamp lacks timezone")
    return parsed.astimezone(UTC)


def canonical_ticks(ticks: list[dict[str, Any]]) -> bytes:
    return (
        json.dumps(ticks, separators=(",", ":"), sort_keys=True) + "\n"
    ).encode()


def validate_inputs(
    signals: list[dict[str, Any]],
    receipts: list[dict[str, Any]],
    outcomes: list[dict[str, Any]],
    config: dict[str, Any],
) -> None:
    signal_ids: set[str] = set()
    for signal in signals:
        if signal.get("campaign_id") != config["publisher_campaign_id"]:
            raise ValueError("live outcome publisher campaign mismatch")
        decision_id = str(signal.get("decision_id", ""))
        if not decision_id or decision_id in signal_ids:
            raise ValueError("missing or duplicate live outcome signal")
        signal_ids.add(decision_id)
    receipt_ids: set[str] = set()
    for receipt in receipts:
        if receipt.get("campaign_id") != config["bridge_campaign_id"]:
            raise ValueError("live outcome bridge campaign mismatch")
        decision_id = str(receipt.get("decision_id", ""))
        if decision_id not in signal_ids or decision_id in receipt_ids:
            raise ValueError("orphan or duplicate live outcome receipt")
        receipt_ids.add(decision_id)
    outcome_ids: set[str] = set()
    for outcome in outcomes:
        if outcome.get("campaign_id") != config["campaign_id"]:
            raise ValueError("live outcome ledger campaign mismatch")
        decision_id = str(outcome.get("decision_id", ""))
        if decision_id not in receipt_ids or decision_id in outcome_ids:
            raise ValueError("orphan or duplicate live outcome")
        if outcome.get("demo_order_authorized") is not False:
            raise ValueError("live outcome unexpectedly authorizes orders")
        outcome_ids.add(decision_id)


def _find_entry_index(
    ticks: list[dict[str, Any]],
    receipt: dict[str, Any],
    config: dict[str, Any],
) -> tuple[int | None, int]:
    start = parse_time(str(receipt["tick_time_utc"]))
    start_ms = int(start.timestamp() * 1000)
    end_ms = start_ms + int(
        config["entry_tick_match_window_milliseconds"]
    )
    bid = float(receipt["bid"])
    ask = float(receipt["ask"])
    matches = [
        index
        for index, tick in enumerate(ticks)
        if start_ms <= int(tick["time_msc"]) < end_ms
        and math.isclose(float(tick["bid"]), bid, abs_tol=1e-12)
        and math.isclose(float(tick["ask"]), ask, abs_tol=1e-12)
    ]
    return (matches[0] if len(matches) == 1 else None), len(matches)


def _invalid_outcome(
    receipt: dict[str, Any],
    status: str,
    detail: str,
    ticks: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    tick_bytes = canonical_ticks(ticks)
    return {
        "outcome_id": f"{config['campaign_id']}|{receipt['decision_id']}",
        "campaign_id": config["campaign_id"],
        "decision_id": receipt["decision_id"],
        "decision_date": receipt["decision_date"],
        "status": status,
        "detail": detail,
        "eligible_side": receipt["eligible_side"],
        "raw_tick_count": len(ticks),
        "raw_tick_sha256": hashlib.sha256(tick_bytes).hexdigest(),
        "result_pips": None,
        "result_r": None,
        "pnl_usd": None,
        "stressed_pnl_usd": None,
        "demo_order_authorized": False,
    }


def resolve_receipt(
    receipt: dict[str, Any],
    ticks: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    if receipt.get("status") != "SHADOW_ENTRY_CAPTURED":
        raise ValueError("non-entry receipt cannot be economically resolved")
    if not ticks:
        return _invalid_outcome(
            receipt,
            "INVALID_EMPTY_TICK_PATH",
            "broker returned no ticks",
            ticks,
            config,
        )
    ordered = sorted(ticks, key=lambda tick: int(tick["time_msc"]))
    if ordered != ticks:
        raise ValueError("raw tick path is not chronological")
    entry_index, match_count = _find_entry_index(ordered, receipt, config)
    if entry_index is None:
        return _invalid_outcome(
            receipt,
            "INVALID_ENTRY_TICK_MATCH",
            f"matching entry ticks={match_count}",
            ordered,
            config,
        )
    entry_tick = ordered[entry_index]
    entry_time = datetime.fromtimestamp(
        int(entry_tick["time_msc"]) / 1000.0,
        tz=UTC,
    )
    hold_end = entry_time + timedelta(
        minutes=int(config["maximum_hold_minutes"])
    )
    hold_end_ms = int(hold_end.timestamp() * 1000)
    path = [
        tick
        for tick in ordered[entry_index + 1 :]
        if int(tick["time_msc"]) <= hold_end_ms
    ]
    if not path:
        return _invalid_outcome(
            receipt,
            "INVALID_EMPTY_POST_ENTRY_PATH",
            "no broker tick followed the captured entry",
            ordered,
            config,
        )
    side = str(receipt["eligible_side"])
    entry = float(receipt["entry"])
    stop = float(receipt["stop"])
    target = float(receipt["target"])
    exit_price: float | None = None
    exit_time: datetime | None = None
    exit_reason = ""
    for tick in path:
        tick_time = datetime.fromtimestamp(
            int(tick["time_msc"]) / 1000.0,
            tz=UTC,
        )
        if side == "LONG":
            quote = float(tick["bid"])
            if quote <= stop:
                exit_price = quote
                exit_time = tick_time
                exit_reason = "STOP"
                break
            if quote >= target:
                exit_price = target
                exit_time = tick_time
                exit_reason = "TARGET"
                break
        elif side == "SHORT":
            quote = float(tick["ask"])
            if quote >= stop:
                exit_price = quote
                exit_time = tick_time
                exit_reason = "STOP"
                break
            if quote <= target:
                exit_price = target
                exit_time = tick_time
                exit_reason = "TARGET"
                break
        else:
            raise ValueError(f"unknown live outcome side: {side}")
    if exit_price is None:
        final_tick = path[-1]
        final_time = datetime.fromtimestamp(
            int(final_tick["time_msc"]) / 1000.0,
            tz=UTC,
        )
        age = (hold_end - final_time).total_seconds()
        if age < 0.0 or age > float(
            config["maximum_time_exit_tick_age_seconds"]
        ):
            return _invalid_outcome(
                receipt,
                "INVALID_TIME_EXIT_TICK",
                f"time-exit tick age={age}",
                ordered,
                config,
            )
        exit_price = (
            float(final_tick["bid"])
            if side == "LONG"
            else float(final_tick["ask"])
        )
        exit_time = final_time
        exit_reason = "TIME"
    pip = float(config["pip_size"])
    result_pips = (
        (exit_price - entry) / pip
        if side == "LONG"
        else (entry - exit_price) / pip
    )
    stop_pips = float(config["stop_pips"])
    result_r = result_pips / stop_pips
    pnl_usd = (
        result_pips
        * float(config["pip_value_usd_per_standard_lot"])
        * float(config["lots"])
    )
    stressed_pnl_usd = (
        result_pips - float(config["additional_round_trip_stress_pips"])
    ) * float(config["pip_value_usd_per_standard_lot"]) * float(
        config["lots"]
    )
    tick_bytes = canonical_ticks(ordered)
    return {
        "outcome_id": f"{config['campaign_id']}|{receipt['decision_id']}",
        "campaign_id": config["campaign_id"],
        "decision_id": receipt["decision_id"],
        "decision_date": receipt["decision_date"],
        "status": "RESOLVED",
        "eligible_side": side,
        "regime": receipt.get("regime"),
        "entry_time_utc": entry_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "exit_time_utc": exit_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "exit_reason": exit_reason,
        "entry": entry,
        "exit": exit_price,
        "stop": stop,
        "target": target,
        "lots": float(config["lots"]),
        "result_pips": result_pips,
        "result_r": result_r,
        "pnl_usd": pnl_usd,
        "stressed_pnl_usd": stressed_pnl_usd,
        "entry_tick_match_count": match_count,
        "raw_tick_count": len(ordered),
        "raw_tick_first_time_msc": int(ordered[0]["time_msc"]),
        "raw_tick_last_time_msc": int(ordered[-1]["time_msc"]),
        "raw_tick_sha256": hashlib.sha256(tick_bytes).hexdigest(),
        "demo_order_authorized": False,
    }


def selection_parity(
    signal: dict[str, Any],
    terminal: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    status = str(signal["status"])
    comparisons: dict[str, bool]
    if status in ("PUBLISHED_SIGNAL", "PUBLISHED_CASH"):
        comparisons = {
            "terminal_status": terminal.get("status") == "RESOLVED",
            "decision_time": parse_time(
                str(signal["decision_time_utc"])
            ).replace(microsecond=0)
            == parse_time(str(terminal["decision_time_utc"])).replace(
                microsecond=0
            ),
            "regime": signal.get("regime") == terminal.get("regime"),
            "eligible_side": signal.get("eligible_side")
            == terminal.get("eligible_side"),
            "eligibility_reason": signal.get("eligibility_reason")
            == terminal.get("eligibility_reason"),
            "training_days_before": signal.get("training_days_before")
            == terminal.get("training_days_before"),
            "context": signal.get("context") == terminal.get("context"),
            "side_statistics_before": signal.get("side_statistics_before")
            == terminal.get("side_statistics_before"),
        }
    elif status == "CASH_UPSTREAM_OWNED":
        comparisons = {
            "terminal_status": terminal.get("status") == "UPSTREAM_OWNED"
        }
    elif status == "CASH_MISSING_CONTEXT":
        comparisons = {
            "terminal_status": terminal.get("status") == "MISSING_CONTEXT"
        }
    else:
        comparisons = {"operational_cash_not_comparable": True}
    passed = all(comparisons.values())
    return {
        "parity_id": f"{config['campaign_id']}|{signal['decision_id']}",
        "campaign_id": config["campaign_id"],
        "decision_id": signal["decision_id"],
        "decision_date": signal["decision_date"],
        "publisher_status": status,
        "terminal_status": terminal.get("status"),
        "comparisons": comparisons,
        "parity_pass": passed,
        "demo_order_authorized": False,
    }


def process(
    signals: list[dict[str, Any]],
    receipts: list[dict[str, Any]],
    terminal_records: list[dict[str, Any]],
    existing_outcomes: list[dict[str, Any]],
    existing_parity: list[dict[str, Any]],
    now: datetime,
    tick_provider: TickProvider,
    config: dict[str, Any],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, bytes],
]:
    if now.tzinfo is None:
        raise ValueError("live outcome clock must be timezone-aware")
    now = now.astimezone(UTC)
    validate_inputs(signals, receipts, existing_outcomes, config)
    signals_by_id = {str(item["decision_id"]): item for item in signals}
    terminal_by_date = {
        str(item["decision_date"]): item for item in terminal_records
    }
    if len(terminal_by_date) != len(terminal_records):
        raise ValueError("duplicate terminal residual date")
    parity_ids = {str(item["decision_id"]) for item in existing_parity}
    parity_rows = list(existing_parity)
    for signal in signals:
        decision_id = str(signal["decision_id"])
        if decision_id in parity_ids:
            continue
        terminal = terminal_by_date.get(str(signal["decision_date"]))
        if (
            terminal is None
            and signal.get("status") not in SELF_TERMINAL_PUBLISHER_STATUSES
        ):
            continue
        parity_rows.append(selection_parity(signal, terminal or {}, config))
        parity_ids.add(decision_id)

    outcome_ids = {str(item["decision_id"]) for item in existing_outcomes}
    outcomes = list(existing_outcomes)
    raw_artifacts: dict[str, bytes] = {}
    for receipt in receipts:
        decision_id = str(receipt["decision_id"])
        if decision_id in outcome_ids:
            continue
        signal = signals_by_id[decision_id]
        day = datetime.fromisoformat(str(receipt["decision_date"])).date()
        if day.weekday() == 4 and not config["friday_utc_entry_allowed"]:
            outcome = {
                "outcome_id": f"{config['campaign_id']}|{decision_id}",
                "campaign_id": config["campaign_id"],
                "decision_id": decision_id,
                "decision_date": receipt["decision_date"],
                "status": "CASH_MARKET_CLOSURE",
                "detail": config["friday_action"],
                "eligible_side": receipt["eligible_side"],
                "result_pips": None,
                "result_r": None,
                "pnl_usd": None,
                "stressed_pnl_usd": None,
                "demo_order_authorized": False,
            }
        elif receipt.get("status") != "SHADOW_ENTRY_CAPTURED":
            outcome = {
                "outcome_id": f"{config['campaign_id']}|{decision_id}",
                "campaign_id": config["campaign_id"],
                "decision_id": decision_id,
                "decision_date": receipt["decision_date"],
                "status": "CASH_NO_SHADOW_ENTRY",
                "detail": receipt.get("status"),
                "eligible_side": receipt["eligible_side"],
                "result_pips": None,
                "result_r": None,
                "pnl_usd": None,
                "stressed_pnl_usd": None,
                "demo_order_authorized": False,
            }
        else:
            tick_time = parse_time(str(receipt["tick_time_utc"]))
            hold_end = tick_time + timedelta(
                minutes=int(config["maximum_hold_minutes"])
            )
            if now < hold_end + timedelta(seconds=1):
                continue
            ticks = tick_provider(
                tick_time,
                hold_end + timedelta(seconds=1),
            )
            outcome = resolve_receipt(receipt, ticks, config)
            raw_name = f"{outcome['raw_tick_sha256']}.json"
            raw_artifacts[raw_name] = canonical_ticks(
                sorted(ticks, key=lambda tick: int(tick["time_msc"]))
            )
            outcome["raw_tick_file"] = raw_name
        outcomes.append(base.json_safe(outcome))
        outcome_ids.add(decision_id)
    return (
        outcomes,
        parity_rows,
        build_summary(
            signals,
            receipts,
            outcomes,
            parity_rows,
            config,
        ),
        raw_artifacts,
    )


def _profit_factor(values: list[float]) -> float:
    gross_profit = sum(value for value in values if value > 0.0)
    gross_loss = -sum(value for value in values if value < 0.0)
    return (
        gross_profit / gross_loss
        if gross_loss
        else math.inf
        if gross_profit
        else 0.0
    )


def _payoff(values: list[float]) -> float | None:
    wins = [value for value in values if value > 0.0]
    losses = [-value for value in values if value < 0.0]
    if not wins or not losses:
        return None
    return (sum(wins) / len(wins)) / (sum(losses) / len(losses))


def _best_removed(values: list[float]) -> float:
    if not values:
        return 0.0
    remove = max(1, math.ceil(len(values) * 0.05))
    indexes = set(
        sorted(
            range(len(values)),
            key=lambda index: values[index],
            reverse=True,
        )[:remove]
    )
    return _profit_factor(
        [value for index, value in enumerate(values) if index not in indexes]
    )


def _halves(values: list[float]) -> list[float]:
    if len(values) < 2:
        return [0.0, 0.0]
    midpoint = len(values) // 2
    return [
        _profit_factor(values[:midpoint]),
        _profit_factor(values[midpoint:]),
    ]


def build_summary(
    signals: list[dict[str, Any]],
    receipts: list[dict[str, Any]],
    outcomes: list[dict[str, Any]],
    parity_rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    resolved = [item for item in outcomes if item["status"] == "RESOLVED"]
    invalid = [
        item for item in outcomes if str(item["status"]).startswith("INVALID_")
    ]
    values = [float(item["pnl_usd"]) for item in resolved]
    stressed = [float(item["stressed_pnl_usd"]) for item in resolved]
    payoff = _payoff(values)
    win_rate = sum(value > 0.0 for value in values) / len(values) if values else 0.0
    halves = _halves(values)
    mismatches = sum(not item["parity_pass"] for item in parity_rows)
    gates = config["admission"]
    checks = {
        "minimum_matched_live_selection_decisions": len(parity_rows)
        >= int(gates["minimum_matched_live_selection_decisions"]),
        "maximum_selection_mismatches": mismatches
        <= int(gates["maximum_selection_mismatches"]),
        "minimum_live_executable_outcomes": len(resolved)
        >= int(gates["minimum_live_executable_outcomes"]),
        "maximum_invalid_outcomes": len(invalid)
        <= int(gates["maximum_invalid_outcomes"]),
        "minimum_win_rate": win_rate >= float(gates["minimum_win_rate"]),
        "maximum_win_rate": win_rate <= float(gates["maximum_win_rate"]),
        "minimum_payoff_ratio": payoff is not None
        and payoff >= float(gates["minimum_payoff_ratio"]),
        "minimum_profit_factor": _profit_factor(values)
        >= float(gates["minimum_profit_factor"]),
        "minimum_stressed_profit_factor": _profit_factor(stressed)
        >= float(gates["minimum_stressed_profit_factor"]),
        "minimum_best_5pct_removed_profit_factor": _best_removed(values)
        >= float(gates["minimum_best_5pct_removed_profit_factor"]),
        "minimum_each_trade_sequence_half_profit_factor": all(
            value
            > float(
                gates[
                    "minimum_each_trade_sequence_half_profit_factor_exclusive"
                ]
            )
            for value in halves
        ),
        "minimum_net_pnl_usd": sum(values)
        > float(gates["minimum_net_pnl_usd_exclusive"]),
        "mt5_ordering_parity": False,
        "shadow_demo_soak": False,
    }
    external = {"mt5_ordering_parity", "shadow_demo_soak"}
    enough = (
        checks["minimum_matched_live_selection_decisions"]
        and checks["minimum_live_executable_outcomes"]
    )
    if not enough:
        status = "WAITING_MINIMUM_LIVE_EVIDENCE"
    elif not all(value for key, value in checks.items() if key not in external):
        status = "REJECTED_LIVE_EXECUTION"
    elif not all(checks[key] for key in external):
        status = "WAITING_MT5_PARITY_AND_SOAK"
    else:
        status = "READY_FOR_COMBINED_LIVE_ADMISSION"
    return {
        "schema_version": "eurusd_forward_residual_live_outcome_summary_v1",
        "campaign_id": config["campaign_id"],
        "status": status,
        "published_decisions": len(signals),
        "mt5_receipts": len(receipts),
        "terminal_outcomes": len(outcomes),
        "resolved_live_outcomes": len(resolved),
        "invalid_outcomes": len(invalid),
        "selection_parity_rows": len(parity_rows),
        "selection_mismatches": mismatches,
        "pending_selection_parity": len(signals) - len(parity_rows),
        "win_rate": win_rate,
        "payoff_ratio": payoff,
        "profit_factor": _profit_factor(values),
        "stressed_profit_factor": _profit_factor(stressed),
        "best_5pct_removed_profit_factor": _best_removed(values),
        "trade_sequence_half_profit_factors": halves,
        "net_pnl_usd": sum(values),
        "checks": checks,
        "order_api_calls": 0,
        "position_mutation_attempts": 0,
        "demo_order_authorized": False,
    }


def write_outputs(
    outcomes: list[dict[str, Any]],
    parity_rows: list[dict[str, Any]],
    summary: dict[str, Any],
    raw_artifacts: dict[str, bytes],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    outcomes_path = output_dir / "FORWARD_RESIDUAL_LIVE_OUTCOMES.json"
    parity_path = output_dir / "FORWARD_RESIDUAL_SELECTION_PARITY.json"
    for path, records, label in (
        (outcomes_path, outcomes, "live outcome"),
        (parity_path, parity_rows, "selection parity"),
    ):
        if path.is_file():
            existing = load_json_list(path)
            if len(records) < len(existing) or records[: len(existing)] != existing:
                raise ValueError(f"{label} ledger mutation refused")
        base.atomic_write_text(
            path,
            json.dumps(base.json_safe(records), indent=2, sort_keys=True)
            + "\n",
        )
    raw_root = output_dir / "raw_ticks"
    raw_root.mkdir(parents=True, exist_ok=True)
    for name, payload in raw_artifacts.items():
        path = raw_root / name
        if path.is_file() and path.read_bytes() != payload:
            raise ValueError(f"raw tick artifact mutation refused: {name}")
        if not path.is_file():
            temporary = path.with_name(path.name + ".tmp")
            temporary.write_bytes(payload)
            temporary.replace(path)
    base.atomic_write_text(
        output_dir / "FORWARD_RESIDUAL_LIVE_OUTCOME_SUMMARY.json",
        json.dumps(base.json_safe(summary), indent=2, sort_keys=True) + "\n",
    )
    base.atomic_write_text(
        output_dir / "FORWARD_RESIDUAL_LIVE_OUTCOME_SUMMARY.md",
        "\n".join(
            [
                "# EURUSD residual live outcome adjudicator",
                "",
                f"Status: **{summary['status']}**",
                "",
                f"- Live outcomes: {summary['resolved_live_outcomes']}",
                f"- Invalid outcomes: {summary['invalid_outcomes']}",
                (
                    "- Selection parity mismatches: "
                    f"{summary['selection_mismatches']}"
                ),
                f"- Profit factor: {summary['profit_factor']}",
                (
                    "- Stressed profit factor: "
                    f"{summary['stressed_profit_factor']}"
                ),
                f"- Net P&L: ${summary['net_pnl_usd']:.2f}",
                "- Order API calls: 0",
                "- Demo-order authorization: false",
                "",
            ]
        ),
    )
