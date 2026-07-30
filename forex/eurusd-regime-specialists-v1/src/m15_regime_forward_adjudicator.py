from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


TIME_FORMAT = "%Y.%m.%d %H:%M:%S"
AUDIT_FIELDS = (
    "recorded_at_broker",
    "recorded_at_utc",
    "run_id",
    "event",
    "detail",
    "account",
    "server",
    "symbol",
    "magic",
    "regime",
    "side",
    "lots",
    "entry",
    "stop",
    "target",
    "shadow",
    "orders_enabled",
    "emergency_stop",
)


@dataclass(frozen=True)
class Signal:
    signal_id: str
    entry_time: datetime
    regime: str
    lots: float
    entry: float
    stop: float
    target: float


@dataclass(frozen=True)
class Bar:
    interval_open: datetime
    status: str
    first_ask: float | None
    ask_high: float | None
    ask_low: float | None
    last_ask: float | None


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, TIME_FORMAT).replace(tzinfo=UTC)


def _audit_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-16", newline="") as handle:
        raw = list(csv.reader(handle))
    if not raw:
        return []
    header_present = tuple(raw[0]) == AUDIT_FIELDS
    data = raw[1:] if header_present else raw
    if any(len(row) != len(AUDIT_FIELDS) for row in data):
        raise ValueError("M15 shadow audit contains malformed rows")
    return [dict(zip(AUDIT_FIELDS, row, strict=True)) for row in data]


def load_signals(path: Path, config: dict[str, Any]) -> list[Signal]:
    rows = _audit_rows(path)
    floor = parse_time(config["forward_floor_utc"])
    required_run = config["campaign_id"]
    required_account = config["required_account_login"]
    required_server = config["required_account_server"]
    required_symbol = config["execution_symbol"]
    for row in rows:
        if (
            row["run_id"] != required_run
            or row["account"] != required_account
            or row["server"] != required_server
            or row["symbol"] != required_symbol
            or row["shadow"] != "true"
            or row["orders_enabled"] != "false"
            or row["emergency_stop"] != "true"
        ):
            raise ValueError("M15 shadow audit identity or safety mismatch")
        if row["event"] in ("ORDER_SEND_OK", "ORDER_SEND_FAILED", "TIME_EXIT_OK"):
            raise ValueError("M15 shadow audit contains a forbidden order action")

    signal_rows = [row for row in rows if row["event"] == "SIGNAL"]
    blocked_rows = [row for row in rows if row["event"] == "ORDER_BLOCKED"]
    blocked_keys = {
        (row["recorded_at_utc"], row["regime"], row["magic"])
        for row in blocked_rows
        if row["detail"]
        == config["signal_contract"]["matching_order_block_detail"]
    }
    signals: list[Signal] = []
    seen_ids: set[str] = set()
    seen_regime_dates: set[tuple[str, str]] = set()
    allowed_regimes = set(config["allowed_regimes"])
    for row in signal_rows:
        timestamp = parse_time(row["recorded_at_utc"])
        if timestamp < floor:
            raise ValueError("pre-floor M15 signal refused")
        key = (row["recorded_at_utc"], row["regime"], row["magic"])
        if key not in blocked_keys:
            raise ValueError("M15 shadow signal lacks matching blocked-order row")
        if row["side"] != config["signal_contract"]["side"]:
            raise ValueError("M15 shadow signal side mismatch")
        if row["regime"] not in allowed_regimes:
            raise ValueError("M15 shadow signal regime mismatch")
        if (
            timestamp.minute
            not in config["signal_contract"]["clock_minutes"]
            or timestamp.second != 0
            or timestamp.hour
            < int(config["signal_contract"]["minimum_hour_utc"])
            or timestamp.hour
            > int(config["signal_contract"]["maximum_hour_utc"])
        ):
            raise ValueError("M15 shadow signal clock mismatch")
        expected_lots = float(
            config["signal_contract"][
                "chop_lots"
                if row["regime"] == "CHOP"
                else "compression_lots"
            ]
        )
        lots = float(row["lots"])
        if not math.isclose(lots, expected_lots, abs_tol=1e-12):
            raise ValueError("M15 shadow signal lot allocation mismatch")
        signal_id = "|".join(key)
        if signal_id in seen_ids:
            raise ValueError("duplicate M15 shadow signal")
        regime_date = (row["regime"], timestamp.date().isoformat())
        if regime_date in seen_regime_dates:
            raise ValueError("more than one signal for a regime UTC date")
        seen_ids.add(signal_id)
        seen_regime_dates.add(regime_date)
        entry = float(row["entry"])
        stop = float(row["stop"])
        target = float(row["target"])
        if not target < entry < stop:
            raise ValueError("M15 shadow short geometry is invalid")
        signals.append(
            Signal(
                signal_id=signal_id,
                entry_time=timestamp,
                regime=row["regime"],
                lots=lots,
                entry=entry,
                stop=stop,
                target=target,
            )
        )
    return sorted(signals, key=lambda item: (item.entry_time, item.regime))


def _optional_float(row: dict[str, str], name: str) -> float | None:
    value = row.get(name, "")
    return float(value) if value not in ("", None) else None


def load_eurusd_bars(
    path: Path, config: dict[str, Any]
) -> dict[datetime, Bar]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required_scope = config["required_evidence_scope"]
    floor = parse_time(config["forward_floor_utc"])
    bars: dict[datetime, Bar] = {}
    for row in rows:
        if row["evidence_scope"] != required_scope:
            raise ValueError("non-prospective feature row refused")
        timestamp = parse_time(row["interval_open_configured_utc"])
        if timestamp < floor:
            raise ValueError("pre-floor feature row refused")
        if row["source_symbol"] != config["execution_symbol"]:
            continue
        if timestamp in bars:
            raise ValueError("duplicate EURUSD feature interval")
        status = row["source_status"]
        valid_quotes = int(row["valid_two_sided_quote_count"])
        valid = status == "OK" and valid_quotes > 0
        bars[timestamp] = Bar(
            interval_open=timestamp,
            status=status if valid else "INVALID",
            first_ask=_optional_float(row, "first_ask") if valid else None,
            ask_high=_optional_float(row, "ask_high") if valid else None,
            ask_low=_optional_float(row, "ask_low") if valid else None,
            last_ask=_optional_float(row, "last_ask") if valid else None,
        )
    return bars


def _base_record(signal: Signal) -> dict[str, Any]:
    return {
        "signal_id": signal.signal_id,
        "entry_time_utc": signal.entry_time.isoformat(),
        "regime": signal.regime,
        "side": "SHORT",
        "lots": signal.lots,
        "entry": signal.entry,
        "stop": signal.stop,
        "target": signal.target,
    }


def resolve_signal(
    signal: Signal,
    bars: dict[datetime, Bar],
    config: dict[str, Any],
) -> dict[str, Any] | None:
    outcome = config["outcome_contract"]
    step = timedelta(minutes=int(outcome["path_timeframe_minutes"]))
    required = int(outcome["required_path_bars_for_time_exit"])
    latest = max(bars) if bars else None
    pip = float(outcome["pip_size"])
    stop_pips = (signal.stop - signal.entry) / pip
    if stop_pips <= 0.0:
        raise ValueError("M15 shadow signal has nonpositive stop")

    path: list[Bar] = []
    for index in range(required):
        expected = signal.entry_time + index * step
        bar = bars.get(expected)
        if bar is None:
            if latest is None or latest < expected:
                return None
            return {
                **_base_record(signal),
                "status": "INVALID",
                "invalid_reason": f"MISSING_INTERVAL_{expected.isoformat()}",
            }
        if bar.status != "OK" or any(
            value is None
            for value in (bar.first_ask, bar.ask_high, bar.ask_low, bar.last_ask)
        ):
            return {
                **_base_record(signal),
                "status": "INVALID",
                "invalid_reason": (
                    f"INVALID_INTERVAL_{bar.interval_open.isoformat()}"
                ),
            }
        path.append(bar)
        assert bar.first_ask is not None
        assert bar.ask_high is not None
        assert bar.ask_low is not None
        exit_price: float | None = None
        exit_reason: str | None = None
        if bar.first_ask >= signal.stop:
            exit_price = bar.first_ask
            exit_reason = "STOP_GAP"
        elif bar.ask_high >= signal.stop:
            exit_price = signal.stop
            exit_reason = "STOP"
        elif bar.first_ask <= signal.target:
            exit_price = bar.first_ask
            exit_reason = "TARGET_GAP"
        elif bar.ask_low <= signal.target:
            exit_price = signal.target
            exit_reason = "TARGET"
        if exit_price is not None:
            return _resolved_record(
                signal,
                bar.interval_open,
                exit_price,
                exit_reason or "UNKNOWN",
                stop_pips,
                len(path),
                config,
            )

    final = path[-1]
    assert final.last_ask is not None
    return _resolved_record(
        signal,
        final.interval_open + step,
        final.last_ask,
        "TIME",
        stop_pips,
        len(path),
        config,
    )


def _resolved_record(
    signal: Signal,
    exit_time: datetime,
    exit_price: float,
    exit_reason: str,
    stop_pips: float,
    path_bars: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    outcome = config["outcome_contract"]
    pip = float(outcome["pip_size"])
    net_pips = (signal.entry - exit_price) / pip
    pip_value = float(outcome["pip_value_usd_per_standard_lot"])
    stress_pips = float(outcome["additional_round_trip_stress_pips"])
    return {
        **_base_record(signal),
        "status": "RESOLVED",
        "exit_time_utc": exit_time.isoformat(),
        "exit": exit_price,
        "exit_reason": exit_reason,
        "path_bars": path_bars,
        "stop_pips": stop_pips,
        "net_pips": net_pips,
        "result_r": net_pips / stop_pips,
        "pnl_usd": net_pips * pip_value * signal.lots,
        "stressed_pnl_usd": (net_pips - stress_pips)
        * pip_value
        * signal.lots,
    }


def profit_factor(values: list[float]) -> float:
    gains = sum(value for value in values if value > 0.0)
    losses = -sum(value for value in values if value < 0.0)
    return gains / losses if losses else math.inf if gains else 0.0


def admission_metrics(
    records: list[dict[str, Any]],
    pending: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    resolved = [row for row in records if row["status"] == "RESOLVED"]
    invalid = [row for row in records if row["status"] == "INVALID"]
    values = [float(row["pnl_usd"]) for row in resolved]
    stressed = [float(row["stressed_pnl_usd"]) for row in resolved]
    base_pf = profit_factor(values)
    stressed_pf = profit_factor(stressed)
    remove_count = max(1, math.ceil(len(resolved) * 0.05)) if resolved else 0
    best_indices = {
        index
        for index, _ in sorted(
            enumerate(values), key=lambda item: item[1], reverse=True
        )[:remove_count]
    }
    removed_pf = profit_factor(
        [value for index, value in enumerate(values) if index not in best_indices]
    )
    midpoint = len(values) // 2
    half_pfs = (
        [
            profit_factor(values[:midpoint]),
            profit_factor(values[midpoint:]),
        ]
        if len(values) >= 2
        else [0.0, 0.0]
    )
    regime_values = {
        regime: [
            float(row["pnl_usd"])
            for row in resolved
            if row["regime"] == regime
        ]
        for regime in config["allowed_regimes"]
    }
    regime_pfs = {
        regime: profit_factor(items)
        for regime, items in regime_values.items()
    }
    months = {
        str(row["entry_time_utc"])[:7] for row in resolved
    }
    monthly_gross: dict[str, float] = defaultdict(float)
    for row in resolved:
        monthly_gross[str(row["entry_time_utc"])[:7]] += max(
            0.0, float(row["pnl_usd"])
        )
    gross = sum(monthly_gross.values())
    maximum_month_share = (
        max(monthly_gross.values(), default=0.0) / gross if gross > 0.0 else 1.0
    )
    observation_days = 0
    if resolved:
        first = datetime.fromisoformat(resolved[0]["entry_time_utc"])
        last = datetime.fromisoformat(resolved[-1]["exit_time_utc"])
        observation_days = (last.date() - first.date()).days + 1
    gates = config["admission"]
    checks = {
        "minimum_resolved_trades": len(resolved)
        >= int(gates["minimum_resolved_trades"]),
        "minimum_observation_calendar_days": observation_days
        >= int(gates["minimum_observation_calendar_days"]),
        "minimum_active_calendar_months": len(months)
        >= int(gates["minimum_active_calendar_months"]),
        "minimum_profit_factor": base_pf
        >= float(gates["minimum_profit_factor"]),
        "minimum_stressed_profit_factor": stressed_pf
        >= float(gates["minimum_stressed_profit_factor"]),
        "minimum_best_5pct_removed_profit_factor": removed_pf
        >= float(gates["minimum_best_5pct_removed_profit_factor"]),
        "minimum_each_trade_sequence_half_profit_factor": all(
            value
            > float(
                gates[
                    "minimum_each_trade_sequence_half_profit_factor_exclusive"
                ]
            )
            for value in half_pfs
        ),
        "minimum_trades_per_regime": all(
            len(items) >= int(gates["minimum_trades_per_regime"])
            for items in regime_values.values()
        ),
        "minimum_component_profit_factor": all(
            value >= float(gates["minimum_component_profit_factor"])
            for value in regime_pfs.values()
        ),
        "maximum_single_month_gross_profit_share": maximum_month_share
        <= float(gates["maximum_single_month_gross_profit_share"]),
        "zero_invalid_outcomes": not invalid,
        "mt5_signal_parity": False,
        "shadow_soak": False,
    }
    automated_names = [
        name
        for name in checks
        if name not in ("mt5_signal_parity", "shadow_soak")
    ]
    if (
        len(resolved) < int(gates["minimum_resolved_trades"])
        or observation_days < int(gates["minimum_observation_calendar_days"])
    ):
        status = "WAITING_MINIMUM_EVIDENCE"
    elif not all(checks[name] for name in automated_names):
        status = "REJECTED_FORWARD_EVIDENCE"
    else:
        status = "WAITING_EXTERNAL_PARITY_AND_SOAK"
    return {
        "status": status,
        "resolved_trades": len(resolved),
        "invalid_outcomes": len(invalid),
        "pending_signals": pending,
        "observation_calendar_days": observation_days,
        "active_calendar_months": len(months),
        "profit_factor": base_pf,
        "stressed_profit_factor": stressed_pf,
        "best_5pct_removed_profit_factor": removed_pf,
        "trade_sequence_half_profit_factors": half_pfs,
        "regime_trade_counts": {
            regime: len(items) for regime, items in regime_values.items()
        },
        "regime_profit_factors": regime_pfs,
        "maximum_single_month_gross_profit_share": maximum_month_share,
        "checks": checks,
        "demo_order_authorized": False,
    }


def process(
    signals: list[Signal],
    bars: dict[datetime, Bar],
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    outcomes = [
        resolve_signal(signal, bars, config)
        for signal in signals
    ]
    first_pending = next(
        (
            index
            for index, record in enumerate(outcomes)
            if record is None
        ),
        len(outcomes),
    )
    # Only publish a chronological terminal prefix. A later short-duration
    # signal can otherwise resolve before an older 12-hour signal and would
    # have to be inserted into the append-only ledger retroactively.
    records = [
        record
        for record in outcomes[:first_pending]
        if record is not None
    ]
    pending = len(signals) - len(records)
    unresolved = sum(record is None for record in outcomes)
    withheld = sum(
        record is not None for record in outcomes[first_pending:]
    )
    earliest_pending = (
        signals[first_pending].entry_time.isoformat()
        if first_pending < len(signals)
        else None
    )
    summary = {
        "schema_version": "eurusd_m15_regime_forward_summary_v1",
        "campaign_id": config["campaign_id"],
        "signals": len(signals),
        "terminal_outcomes": len(records),
        "pending_signals": pending,
        "unresolved_signals": unresolved,
        "causally_withheld_signals": withheld,
        "earliest_pending_signal_entry_time_utc": earliest_pending,
        "admission": admission_metrics(records, pending, config),
        "demo_order_authorized": False,
    }
    return records, summary


def json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    return value


def load_existing(output_dir: Path) -> list[dict[str, Any]]:
    path = output_dir / "FORWARD_OUTCOMES.json"
    if not path.exists():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("existing M15 forward outcome ledger is not a list")
    return value


def validate_append_only(
    existing: list[dict[str, Any]], new: list[dict[str, Any]]
) -> None:
    safe = json_safe(new)
    if len(safe) < len(existing):
        raise ValueError("M15 forward outcome ledger shrank")
    for index, prior in enumerate(existing):
        if prior != safe[index]:
            raise ValueError(
                "M15 forward outcome mutation refused "
                f"at index={index} signal_id={prior.get('signal_id')}"
            )


def atomic_write(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)


def write_outputs(
    records: list[dict[str, Any]],
    summary: dict[str, Any],
    output_dir: Path,
    *,
    enforce_append_only: bool,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if enforce_append_only:
        validate_append_only(load_existing(output_dir), records)
    atomic_write(
        output_dir / "FORWARD_OUTCOMES.json",
        json.dumps(json_safe(records), indent=2, sort_keys=True) + "\n",
    )
    atomic_write(
        output_dir / "FORWARD_SUMMARY.json",
        json.dumps(json_safe(summary), indent=2, sort_keys=True) + "\n",
    )
    admission = summary["admission"]
    atomic_write(
        output_dir / "FORWARD_SUMMARY.md",
        "\n".join(
            [
                "# EURUSD M15 regime forward adjudication",
                "",
                f"Status: **{admission['status']}**",
                "",
                f"- Signals: `{summary['signals']}`",
                f"- Resolved trades: `{admission['resolved_trades']}`",
                f"- Invalid outcomes: `{admission['invalid_outcomes']}`",
                f"- Pending signals: `{admission['pending_signals']}`",
                f"- Profit factor: `{admission['profit_factor']}`",
                f"- Stressed profit factor: `{admission['stressed_profit_factor']}`",
                "- Demo-order authorization: `false`",
                "",
            ]
        ),
    )
