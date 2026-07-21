from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from executor import (  # noqa: E402
    RETRYABLE_RETCODES,
    SUCCESS_RETCODES,
    append_event,
    atomic_write_json,
    candidate_comment,
    candidate_prices,
    close_deadline,
    daily_key,
    due_candidates,
    floating_drawdown,
    load_state,
    mark_seen,
    own_positions,
    parse_utc,
    refresh_drawdown_state,
    source_positions,
    utc_now,
    utc_text,
)


CONFIG_PATH = ROOT / "config" / "v60_canonical_demo_portfolio_v2.json"


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    auth = config["authorization"]
    if not auth.get("demo_authorized") or not auth.get("broker_action_authorized"):
        raise RuntimeError("V60 demo broker action is not authorized")
    if auth.get("live_authorized"):
        raise RuntimeError("V60 demo executor must never have live authorization")
    if auth.get("ml_runtime_authorized") or auth.get("ml_shadow_authorized"):
        raise RuntimeError("ML runtime and ML shadow must both remain unauthorized")
    expected = {
        "R1_BOX",
        "R1_PULLBACK",
        "R2_DOWNTREND",
        "R3_COMPRESSION",
        "R4_CHOP",
        "R5_TRANSITION",
        "V7_SWING_HEALTH",
        "V8_RETEST_HEALTH",
        "V25_CHOP",
        "V57_BREAK_SWING_H4ADX_HIGH",
    }
    observed = {str(source["source_id"]) for source in config["sources"]}
    if observed != expected:
        raise RuntimeError(f"Canonical source set changed: {sorted(observed)}")
    return config


def load_mt5() -> Any:
    import MetaTrader5 as mt5

    return mt5


def _read_chart_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")) or b"\x00" in raw[:100]:
        return raw.decode("utf-16", errors="replace")
    return raw.decode("utf-8", errors="replace")


def audit_chart_profile(config: Mapping[str, Any], *, require_ready: bool) -> dict[str, Any]:
    settings = config["preflight"]
    root = Path(settings["chart_profile_directory"])
    charts = sorted(root.glob("*.chr"))
    combined = "\n".join(_read_chart_text(path) for path in charts)
    forbidden = [term for term in settings["forbidden_chart_terms"] if term in combined]
    required_experts = {
        name: f"name={name}" in combined for name in settings["required_experts"]
    }
    required_runs = {
        run_id: f"InpRunId={run_id}" in combined
        for run_id in settings["required_sensor_run_ids"]
    }
    if forbidden:
        raise RuntimeError(f"Forbidden legacy/ML chart attachment found: {forbidden}")
    ready = bool(charts) and all(required_experts.values()) and all(required_runs.values())
    if require_ready and not ready:
        raise RuntimeError("Canonical deterministic MT5 sensor profile is incomplete")
    return {
        "chart_count": len(charts),
        "forbidden_terms": forbidden,
        "required_experts": required_experts,
        "required_sensor_runs": required_runs,
        "ready": ready,
    }


def account_value_usd(value: float, config: Mapping[str, Any]) -> float:
    return float(value) / float(config["account"]["usd_to_account_currency"])


def feed_preflight(config: Mapping[str, Any], *, require_ready: bool) -> dict[str, Any]:
    runtime = Path(config["runtime"]["directory"])
    path = runtime / config["runtime"]["feed_status_filename"]
    if not path.is_file():
        if require_ready:
            raise RuntimeError("Canonical feed status is absent")
        return {"ready": False, "reason": "FEED_STATUS_ABSENT"}
    status = json.loads(path.read_text(encoding="utf-8"))
    if int(status.get("account_login", -1)) != int(config["account"]["expected_login"]):
        raise RuntimeError("Canonical feed status belongs to the wrong account")
    updated = parse_utc(str(status["updated_at_utc"]))
    age_seconds = max(0.0, (utc_now() - updated).total_seconds())
    required = {
        "R1_BOX",
        "R1_PULLBACK",
        "R2_R3",
        "R4",
        "R5_COMPONENTS",
        "R5_RESOLVER",
        "R5_ROUTER",
        "ADDONS",
    }
    observed = set(status.get("feeds", {}))
    ready = required.issubset(observed) and bool(status.get("all_requested_feeds_ok")) and age_seconds <= int(
        config["runtime"]["maximum_feed_status_age_seconds"]
    )
    if require_ready and not ready:
        raise RuntimeError(
            f"Canonical feeds are not ready: age={age_seconds:.1f}s "
            f"all_ok={status.get('all_requested_feeds_ok')}"
        )
    return {
        "ready": ready,
        "age_seconds": age_seconds,
        "all_requested_feeds_ok": bool(status.get("all_requested_feeds_ok")),
        "ml_used": bool(status.get("ml_used", True)),
        "required_feeds_present": required.issubset(observed),
    }


def assert_account(
    mt5: Any, config: Mapping[str, Any], *, require_trading: bool = True
) -> tuple[Any, Any, Any]:
    account = mt5.account_info()
    terminal = mt5.terminal_info()
    symbol = mt5.symbol_info(config["account"]["symbol"])
    if account is None or terminal is None or symbol is None:
        raise RuntimeError(
            "MT5 account, terminal, or symbol information is unavailable"
        )
    expected = config["account"]
    if int(account.login) != int(expected["expected_login"]):
        raise RuntimeError(f"Wrong account login: {account.login}")
    if str(account.server) != str(expected["expected_server"]):
        raise RuntimeError(f"Wrong account server: {account.server}")
    if (
        str(expected["required_server_marker"]).lower()
        not in str(account.server).lower()
    ):
        raise RuntimeError("Non-demo server refused")
    if str(account.currency) != str(expected["required_account_currency"]):
        raise RuntimeError(f"Unexpected account currency: {account.currency}")
    if require_trading and (not bool(account.trade_allowed) or not bool(account.trade_expert)):
        raise RuntimeError("Account does not allow algorithmic trading")
    if not bool(terminal.connected):
        raise RuntimeError("Terminal is disconnected")
    if require_trading and not bool(terminal.trade_allowed):
        raise RuntimeError("Terminal is disconnected or AutoTrading is disabled")
    if not bool(symbol.visible) and not mt5.symbol_select(expected["symbol"], True):
        raise RuntimeError("Unable to select XAUUSD")
    expected_ounces = float(expected["expected_ounces_at_fixed_lot"])
    actual_ounces = float(symbol.trade_contract_size) * float(expected["fixed_lot"])
    if abs(actual_ounces - expected_ounces) > 1e-9:
        raise RuntimeError(
            f"XAUUSD contract geometry changed: {actual_ounces} ounces at fixed lot"
        )
    if float(expected["fixed_lot"]) < float(symbol.volume_min):
        raise RuntimeError("Configured fixed lot is below the broker minimum")
    return account, terminal, symbol


def closed_pnl(
    mt5: Any,
    state: Mapping[str, Any],
    magics: set[int],
    symbol: str,
    config: Mapping[str, Any],
) -> float:
    start = parse_utc(state["activated_at_utc"]) - timedelta(minutes=1)
    deals = mt5.history_deals_get(start, utc_now()) or []
    account_currency_pnl = float(
        sum(
            float(getattr(deal, "profit", 0.0))
            + float(getattr(deal, "commission", 0.0))
            + float(getattr(deal, "swap", 0.0))
            + float(getattr(deal, "fee", 0.0))
            for deal in deals
            if int(getattr(deal, "magic", -1)) in magics
            and str(getattr(deal, "symbol", "")) == symbol
        )
    )
    return account_value_usd(account_currency_pnl, config)


def broker_geometry_preflight(
    mt5: Any, config: Mapping[str, Any], symbol_info: Any
) -> dict[str, Any]:
    tick = mt5.symbol_info_tick(config["account"]["symbol"])
    if tick is None:
        raise RuntimeError("Broker geometry preflight has no XAUUSD tick")
    checks: dict[str, Any] = {}
    for direction in ("LONG", "SHORT"):
        sign = 1.0 if direction == "LONG" else -1.0
        price = float(tick.ask if direction == "LONG" else tick.bid)
        distance = 3.5
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": config["account"]["symbol"],
            "volume": float(config["account"]["fixed_lot"]),
            "type": mt5.ORDER_TYPE_BUY if direction == "LONG" else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": round(price - sign * distance, int(symbol_info.digits)),
            "tp": round(price + sign * 2.0 * distance, int(symbol_info.digits)),
            "deviation": int(config["account"]["deviation_points"]),
            "magic": 969999,
            "comment": "V60_PREFLIGHT",
            "type_time": mt5.ORDER_TIME_GTC,
        }
        attempts = []
        accepted = False
        for filling in (
            mt5.ORDER_FILLING_IOC,
            mt5.ORDER_FILLING_RETURN,
            mt5.ORDER_FILLING_FOK,
        ):
            result = mt5.order_check(dict(request, type_filling=filling))
            retcode = None if result is None else int(result.retcode)
            attempts.append(retcode)
            if retcode in {0, *SUCCESS_RETCODES}:
                accepted = True
                break
        if not accepted:
            raise RuntimeError(
                f"Broker rejected {direction} preflight geometry: {attempts}"
            )
        checks[direction] = {"accepted": True, "retcodes": attempts}
    return checks


def active_entry_halts(config: Mapping[str, Any]) -> list[str]:
    return [
        str(path)
        for value in config["runtime"].get("entry_halt_files", [])
        if (path := Path(value)).is_file()
    ]


def send_request(mt5: Any, request: dict[str, Any]) -> Any:
    fill_modes = [
        mt5.ORDER_FILLING_IOC,
        mt5.ORDER_FILLING_RETURN,
        mt5.ORDER_FILLING_FOK,
    ]
    last = None
    for filling in fill_modes:
        attempt = dict(request, type_filling=filling)
        check = mt5.order_check(attempt)
        if check is None:
            last = None
            continue
        if int(check.retcode) not in {0, *SUCCESS_RETCODES}:
            last = check
            continue
        result = mt5.order_send(attempt)
        last = result
        if result is not None and int(result.retcode) in SUCCESS_RETCODES:
            return result
        if result is not None and int(result.retcode) not in {
            10030,
            *RETRYABLE_RETCODES,
        }:
            return result
    return last


def locate_position(mt5: Any, symbol: str, magic: int, comment: str) -> Any | None:
    candidates = [
        position
        for position in (mt5.positions_get(symbol=symbol) or [])
        if int(getattr(position, "magic", -1)) == magic
    ]
    exact = [p for p in candidates if str(getattr(p, "comment", "")) == comment]
    pool = exact or candidates
    return (
        max(pool, key=lambda item: int(getattr(item, "time_msc", 0))) if pool else None
    )


def open_candidate(
    mt5: Any,
    candidate: Any,
    config: Mapping[str, Any],
    symbol_info: Any,
    tick: Any,
) -> tuple[Any, str, str | None]:
    point = float(symbol_info.point)
    minimum_stop = max(point, float(symbol_info.trade_stops_level) * point)
    price, stop, target = candidate_prices(
        candidate,
        bid=float(tick.bid),
        ask=float(tick.ask),
        digits=int(symbol_info.digits),
        minimum_stop_distance=minimum_stop,
    )
    order_type = (
        mt5.ORDER_TYPE_BUY if candidate.direction == "LONG" else mt5.ORDER_TYPE_SELL
    )
    comment = candidate_comment(candidate)
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": config["account"]["symbol"],
        "volume": float(config["account"]["fixed_lot"]),
        "type": order_type,
        "price": price,
        "sl": stop,
        "tp": target,
        "deviation": int(config["account"]["deviation_points"]),
        "magic": candidate.magic,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
    }
    result = send_request(mt5, request)
    return result, comment, close_deadline(candidate, utc_now())


def close_position(mt5: Any, position: Any, config: Mapping[str, Any]) -> Any:
    symbol = config["account"]["symbol"]
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return None
    is_buy = int(position.type) == mt5.POSITION_TYPE_BUY
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": int(position.ticket),
        "symbol": symbol,
        "volume": float(position.volume),
        "type": mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY,
        "price": float(tick.bid if is_buy else tick.ask),
        "deviation": int(config["account"]["deviation_points"]),
        "magic": int(position.magic),
        "comment": "V60_HORIZON_EXIT",
        "type_time": mt5.ORDER_TIME_GTC,
    }
    return send_request(mt5, request)


def manage_horizon_exits(
    mt5: Any,
    config: Mapping[str, Any],
    state: dict[str, Any],
    events_path: Path,
    now: datetime,
) -> None:
    current = {
        int(p.ticket): p
        for p in (mt5.positions_get(symbol=config["account"]["symbol"]) or [])
    }
    for candidate_id, metadata in list(state.get("positions", {}).items()):
        ticket = int(metadata["ticket"])
        position = current.get(ticket)
        if position is None:
            metadata["status"] = "CLOSED_OR_MISSING"
            metadata["closed_observed_at_utc"] = utc_text(now)
            continue
        close_at = metadata.get("close_at_utc")
        if not close_at or now < parse_utc(close_at):
            continue
        result = close_position(mt5, position, config)
        retcode = None if result is None else int(result.retcode)
        event = {
            "event": "HORIZON_CLOSE",
            "at_utc": utc_text(now),
            "candidate_id": candidate_id,
            "ticket": ticket,
            "retcode": retcode,
            "comment": None if result is None else str(result.comment),
        }
        append_event(events_path, event)
        if retcode in SUCCESS_RETCODES:
            metadata["status"] = "HORIZON_CLOSE_SENT"


def run_cycle(mt5: Any, config: Mapping[str, Any]) -> dict[str, Any]:
    now = utc_now()
    runtime = Path(config["runtime"]["directory"])
    state_path = runtime / config["runtime"]["state_filename"]
    events_path = runtime / config["runtime"]["events_filename"]
    status_path = runtime / config["runtime"]["status_filename"]
    execution_enabled = bool(config["runtime"]["execution_enabled"])
    profile = audit_chart_profile(config, require_ready=execution_enabled)
    feeds = feed_preflight(config, require_ready=execution_enabled)
    if feeds.get("ml_used"):
        raise RuntimeError("Canonical feed status reports ML use")
    account, _, symbol_info = assert_account(
        mt5, config, require_trading=execution_enabled
    )
    broker_geometry = broker_geometry_preflight(mt5, config, symbol_info)
    equity_usd = account_value_usd(float(account.equity), config)
    state = load_state(state_path, now, equity_usd)
    magics = {int(source["magic"]) for source in config["sources"]}
    core_magics = {
        int(source["magic"])
        for source in config["sources"]
        if str(source.get("sleeve_type", "CORE")).upper() == "CORE"
    }
    addon_magics = magics - core_magics
    symbol = config["account"]["symbol"]
    pnl = closed_pnl(mt5, state, magics, symbol, config)
    refresh_drawdown_state(
        state, equity=equity_usd, closed_pnl=pnl, risk=config["risk"]
    )
    if execution_enabled:
        manage_horizon_exits(mt5, config, state, events_path, now)

    positions = list(mt5.positions_get(symbol=symbol) or [])
    ours = own_positions(positions, magics, symbol)
    core_positions = own_positions(positions, core_magics, symbol)
    addon_positions = own_positions(positions, addon_magics, symbol)
    active_tickets = {int(position.ticket) for position in addon_positions}
    active_addon_risk = sum(
        float(metadata.get("initial_risk_usd", 0.0))
        for metadata in state.get("positions", {}).values()
        if int(metadata.get("ticket", -1)) in active_tickets
    )
    hard_floating_stop = floating_drawdown(state, equity_usd) >= float(
        config["risk"]["floating_drawdown_hard_stop_usd"]
    )
    combined_closed_stop = float(state["closed_drawdown_usd"]) >= float(
        config["risk"]["combined_closed_drawdown_hard_stop_usd"]
    )
    entry_halts = active_entry_halts(config)
    emergency_close_results: list[dict[str, Any]] = []
    if execution_enabled and (hard_floating_stop or combined_closed_stop):
        trigger = (
            "FLOATING_DRAWDOWN_HARD_STOP"
            if hard_floating_stop
            else "COMBINED_CLOSED_DRAWDOWN_HARD_STOP"
        )
        for position in ours:
            result = close_position(mt5, position, config)
            record = {
                "event": "EMERGENCY_CLOSE",
                "at_utc": utc_text(now),
                "trigger": trigger,
                "ticket": int(position.ticket),
                "magic": int(position.magic),
                "retcode": None if result is None else int(result.retcode),
                "comment": None if result is None else str(result.comment),
            }
            emergency_close_results.append(record)
            append_event(events_path, record)
        positions = list(mt5.positions_get(symbol=symbol) or [])
        ours = own_positions(positions, magics, symbol)
        core_positions = own_positions(positions, core_magics, symbol)
        addon_positions = own_positions(positions, addon_magics, symbol)
        active_tickets = {int(position.ticket) for position in addon_positions}
        active_addon_risk = sum(
            float(metadata.get("initial_risk_usd", 0.0))
            for metadata in state.get("positions", {}).values()
            if int(metadata.get("ticket", -1)) in active_tickets
        )
    point = float(symbol_info.point)
    processed = 0

    pending = due_candidates(config, state, point, now)
    if not execution_enabled:
        pending = []
    addon_source_ids = {
        str(source["source_id"])
        for source in config["sources"]
        if str(source.get("sleeve_type", "CORE")).upper() == "ADDON"
    }
    for candidate in pending:
        age = now - candidate.scheduled_at
        reason: str | None = None
        if age > timedelta(minutes=candidate.maximum_entry_gap_minutes):
            reason = "STALE_CANDIDATE"
        elif entry_halts:
            reason = "ENTRY_HALT_FILE_ACTIVE"
        elif bool(state["drawdown_suspended"]):
            reason = "CLOSED_DRAWDOWN_SUSPENDED"
        elif hard_floating_stop:
            reason = "FLOATING_DRAWDOWN_HARD_STOP"
        elif combined_closed_stop:
            reason = "COMBINED_CLOSED_DRAWDOWN_HARD_STOP"
        elif candidate.sleeve_type == "CORE" and len(core_positions) >= int(
            config["risk"]["maximum_core_open_positions"]
        ):
            reason = "MAXIMUM_CORE_OPEN_POSITIONS"
        elif candidate.sleeve_type == "ADDON" and len(addon_positions) >= int(
            config["risk"]["maximum_addon_open_positions"]
        ):
            reason = "MAXIMUM_ADDON_OPEN_POSITIONS"
        elif candidate.sleeve_type == "ADDON" and (
            active_addon_risk + candidate.initial_risk_usd
            > float(config["risk"]["maximum_addon_concurrent_initial_risk_usd"])
        ):
            reason = "MAXIMUM_ADDON_CONCURRENT_INITIAL_RISK"
        elif len(positions) >= int(config["risk"]["maximum_account_xau_positions"]):
            reason = "MAXIMUM_ACCOUNT_XAU_POSITIONS"
        elif (
            len(source_positions(positions, candidate.magic, symbol))
            >= candidate.maximum_open_positions
        ):
            reason = "MAXIMUM_SOURCE_OPEN_POSITIONS"
        elif (
            int(state["daily_entries"].get(daily_key(candidate), 0))
            >= candidate.maximum_entries_per_utc_day
        ):
            reason = "MAXIMUM_SOURCE_DAILY_ENTRIES"
        elif sum(
            int(value)
            for key, value in state["daily_entries"].items()
            if key.endswith(candidate.scheduled_at.date().isoformat())
        ) >= int(config["risk"]["maximum_daily_entries"]):
            reason = "MAXIMUM_DAILY_ENTRIES"
        elif candidate.sleeve_type == "ADDON" and sum(
            int(value)
            for key, value in state["daily_entries"].items()
            if key.split(":", 1)[0] in addon_source_ids
            and key.endswith(candidate.scheduled_at.date().isoformat())
        ) >= int(config["risk"]["maximum_addon_entries_per_utc_day"]):
            reason = "MAXIMUM_ADDON_DAILY_ENTRIES"
        elif candidate.sleeve_type == "ADDON" and candidate.event_id and any(
            item.get("event_id") == candidate.event_id
            and item.get("sleeve_type") == "ADDON"
            and item.get("status") == "ORDER_FILLED"
            for item in state.get("seen", {}).values()
        ):
            reason = "DUPLICATE_ADDON_EVENT"

        tick = mt5.symbol_info_tick(symbol)
        if reason is None and tick is None:
            reason = "NO_BROKER_TICK"
        if reason is None:
            tick_time = datetime.fromtimestamp(int(tick.time_msc) / 1000.0, tz=UTC)
            if (now - tick_time).total_seconds() > int(
                config["runtime"]["maximum_tick_age_seconds"]
            ):
                reason = "STALE_BROKER_TICK"

        if reason is not None:
            mark_seen(state, candidate, reason, now)
            append_event(
                events_path,
                state["seen"][candidate.candidate_id] | {"event": "CANDIDATE_REJECTED"},
            )
            processed += 1
            continue

        try:
            result, comment, deadline = open_candidate(
                mt5, candidate, config, symbol_info, tick
            )
        except ValueError as exc:
            mark_seen(state, candidate, str(exc), now)
            append_event(
                events_path,
                state["seen"][candidate.candidate_id] | {"event": "CANDIDATE_REJECTED"},
            )
            processed += 1
            continue
        retcode = None if result is None else int(result.retcode)
        if retcode in RETRYABLE_RETCODES or result is None:
            append_event(
                events_path,
                {
                    "event": "ORDER_RETRY_PENDING",
                    "at_utc": utc_text(now),
                    "candidate_id": candidate.candidate_id,
                    "retcode": retcode,
                    "comment": None if result is None else str(result.comment),
                },
            )
            continue
        if retcode not in SUCCESS_RETCODES:
            mark_seen(
                state,
                candidate,
                "ORDER_REJECTED",
                now,
                retcode=retcode,
                broker_comment=str(result.comment),
            )
            append_event(
                events_path,
                state["seen"][candidate.candidate_id] | {"event": "ORDER_REJECTED"},
            )
            processed += 1
            continue

        position = locate_position(mt5, symbol, candidate.magic, comment)
        ticket = (
            int(position.ticket)
            if position is not None
            else int(result.order or result.deal)
        )
        mark_seen(state, candidate, "ORDER_FILLED", now, retcode=retcode, ticket=ticket)
        state["positions"][candidate.candidate_id] = {
            "ticket": ticket,
            "magic": candidate.magic,
            "source_id": candidate.source_id,
            "sleeve_type": candidate.sleeve_type,
            "initial_risk_usd": candidate.initial_risk_usd,
            "event_id": candidate.event_id,
            "opened_at_utc": utc_text(now),
            "close_at_utc": deadline,
            "status": "OPEN",
        }
        key = daily_key(candidate)
        state["daily_entries"][key] = int(state["daily_entries"].get(key, 0)) + 1
        append_event(
            events_path,
            state["seen"][candidate.candidate_id] | {"event": "ORDER_FILLED"},
        )
        positions = list(mt5.positions_get(symbol=symbol) or [])
        ours = own_positions(positions, magics, symbol)
        core_positions = own_positions(positions, core_magics, symbol)
        addon_positions = own_positions(positions, addon_magics, symbol)
        active_tickets = {int(position.ticket) for position in addon_positions}
        active_addon_risk = sum(
            float(metadata.get("initial_risk_usd", 0.0))
            for metadata in state.get("positions", {}).values()
            if int(metadata.get("ticket", -1)) in active_tickets
        )
        processed += 1

    atomic_write_json(state_path, state)
    status = {
        "schema_version": "xauusd_v60_canonical_demo_status_v2",
        "updated_at_utc": utc_text(now),
        "status": (
            "ACTIVE_DEMO_BROKER_ACTION"
            if execution_enabled
            else (
                "READY_EXECUTION_DISABLED"
                if profile["ready"] and feeds["ready"]
                else "PREFLIGHT_PENDING_EXECUTION_DISABLED"
            )
        ),
        "account_login": int(account.login),
        "account_server": str(account.server),
        "symbol": symbol,
        "account_currency": str(account.currency),
        "balance_account_currency": float(account.balance),
        "equity_account_currency": float(account.equity),
        "balance_usd": account_value_usd(float(account.balance), config),
        "equity_usd": equity_usd,
        "activation_equity_usd": float(state["activation_equity_usd"]),
        "closed_pnl_usd": float(state["closed_pnl_usd"]),
        "closed_drawdown_usd": float(state["closed_drawdown_usd"]),
        "floating_drawdown_usd": floating_drawdown(state, equity_usd),
        "drawdown_suspended": bool(state["drawdown_suspended"]),
        "hard_floating_stop": hard_floating_stop,
        "combined_closed_drawdown_hard_stop": combined_closed_stop,
        "active_entry_halt_files": entry_halts,
        "emergency_close_results": emergency_close_results,
        "core_open_positions": len(core_positions),
        "addon_open_positions": len(addon_positions),
        "addon_active_initial_risk_usd": active_addon_risk,
        "account_xau_positions": len(positions),
        "seen_candidates": len(state["seen"]),
        "processed_this_cycle": processed,
        "demo_authorized": True,
        "broker_action_authorized": True,
        "execution_enabled": execution_enabled,
        "live_authorized": False,
        "ml_runtime_authorized": False,
        "ml_shadow_authorized": False,
        "chart_profile_preflight": profile,
        "feed_preflight": feeds,
        "broker_geometry_preflight": broker_geometry,
        "canonical_sources": sorted(source["source_id"] for source in config["sources"]),
    }
    atomic_write_json(status_path, status)
    return status


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the deterministic V59/V60 canonical demo portfolio"
    )
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config.resolve())
    mt5 = load_mt5()
    terminal = str(Path(config["account"]["terminal_exe"]).resolve())
    if not mt5.initialize(path=terminal, portable=True):
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    try:
        while True:
            try:
                status = run_cycle(mt5, config)
                print(json.dumps(status, sort_keys=True), flush=True)
            except Exception as exc:
                runtime = Path(config["runtime"]["directory"])
                failure = {
                    "schema_version": "xauusd_v60_canonical_demo_status_v2",
                    "updated_at_utc": utc_text(datetime.now(UTC)),
                    "status": "FAILED_CLOSED",
                    "error": f"{type(exc).__name__}: {exc}",
                    "broker_action_authorized": True,
                    "execution_enabled": bool(config["runtime"]["execution_enabled"]),
                    "ml_runtime_authorized": False,
                    "ml_shadow_authorized": False,
                    "live_authorized": False,
                }
                atomic_write_json(
                    runtime / config["runtime"]["status_filename"], failure
                )
                print(json.dumps(failure, sort_keys=True), flush=True)
                if args.once:
                    return 1
            if args.once:
                return 0
            time.sleep(int(config["runtime"]["poll_seconds"]))
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
