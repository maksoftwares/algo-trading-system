from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from executor import (  # noqa: E402
    RETRYABLE_RETCODES,
    SUCCESS_RETCODES,
    PositionOriginPnl,
    append_event,
    atomic_write_json,
    candidate_comment,
    candidate_prices,
    close_deadline,
    daily_key,
    due_candidates,
    effective_risk_threshold_usd,
    floating_drawdown,
    load_state,
    mark_seen,
    own_positions,
    parse_utc,
    position_origin_pnl,
    refresh_drawdown_state,
    source_positions,
    utc_now,
    utc_text,
)
from ml_topup import (  # noqa: E402
    evaluate_candidate as evaluate_ml_topup_candidate,
    prepare_runtime as prepare_ml_topup_runtime,
    status_snapshot as ml_topup_status_snapshot,
    topup_comment,
)


CONFIG_PATH = ROOT / "config" / "v60_canonical_demo_portfolio_v2.json"
ML_OVERLAY_PATH = ROOT / "config" / "v60_portable_ml_topup_v4_overlay.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_deployment_parity(config: Mapping[str, Any]) -> dict[str, Any]:
    if not bool(config["authorization"].get("full_v59_v60_forward_parity_required")):
        raise RuntimeError("Full V59/V60 deployment parity must remain required")
    settings = config.get("deployment_parity")
    if not isinstance(settings, Mapping):
        raise RuntimeError("Deployment parity settings are absent")
    path = REPO_ROOT / str(settings["artifact_path"])
    if not path.is_file() or sha256_file(path) != str(settings["artifact_sha256"]):
        raise RuntimeError("Deployment parity artifact identity changed")
    artifact = json.loads(path.read_text(encoding="utf-8"))
    observed_sources = sorted(str(row["source_id"]) for row in config["sources"])
    if artifact.get("schema_version") != "xauusd_v60_deployment_parity_v1":
        raise RuntimeError("Deployment parity artifact schema changed")
    if artifact.get("status") != "PASS":
        raise RuntimeError("Deployment parity artifact does not pass")
    if list(artifact.get("executable_source_ids", [])) != observed_sources:
        raise RuntimeError("Deployment parity source registry changed")
    if int(artifact.get("historical_trade_rows", 0)) <= 0:
        raise RuntimeError("Deployment parity has no historical trades")
    probation_sources = set(artifact.get("probation_source_ids", []))
    ml_settings = config.get("ml_topup")
    if isinstance(ml_settings, Mapping):
        eligible_sources = set(ml_settings.get("eligible_source_ids", []))
        if overlap := sorted(probation_sources & eligible_sources):
            raise RuntimeError(f"ML top-up includes probation sources: {overlap}")
    return artifact


def apply_ml_overlay(
    config: dict[str, Any], base_path: Path, overlay_path: Path
) -> dict[str, Any]:
    overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
    if overlay.get("schema_version") != "xauusd_v60_portable_ml_topup_v4_overlay":
        raise RuntimeError("Unexpected portable ML overlay schema")
    expected_base = overlay["base_config"]
    expected_path = REPO_ROOT / str(expected_base["path"])
    if expected_path.resolve() != base_path.resolve():
        raise RuntimeError("Portable ML overlay is bound to a different base config")
    if sha256_file(base_path) != str(expected_base["sha256"]):
        raise RuntimeError("Portable ML base config identity changed")
    config["authorization"].update(overlay["authorization"])
    config["ml_topup"] = overlay["ml_topup"]
    config["_ml_overlay_path"] = str(overlay_path)
    return config


def load_config(
    path: Path = CONFIG_PATH, ml_overlay_path: Path | None = None
) -> dict[str, Any]:
    path = path.resolve()
    config = json.loads(path.read_text(encoding="utf-8"))
    if ml_overlay_path is not None:
        config = apply_ml_overlay(config, path, ml_overlay_path.resolve())
    auth = config["authorization"]
    if not auth.get("demo_authorized") or not auth.get("broker_action_authorized"):
        raise RuntimeError("V60 demo broker action is not authorized")
    if auth.get("live_authorized"):
        raise RuntimeError("V60 demo executor must never have live authorization")
    if auth.get("minimum_balance_requirement_enabled"):
        raise RuntimeError("Canonical demo executor must not enforce a minimum balance")
    if not auth.get("demo_balance_eligibility_waived"):
        raise RuntimeError("Demo balance eligibility waiver is absent")
    configured_equity_scaling = config["risk"].get("equity_fraction_limits_enabled")
    if configured_equity_scaling is not True:
        raise RuntimeError(
            "Canonical demo risk limits must use activation-equity scaling"
        )
    if auth.get("ml_shadow_authorized"):
        raise RuntimeError("ML shadow must remain unauthorized")
    if auth.get("ml_runtime_authorized"):
        settings = config.get("ml_topup", {})
        if not auth.get("demo_ml_topup_authorized"):
            raise RuntimeError("Portable ML demo top-up owner authorization is absent")
        if not bool(settings.get("enabled")):
            raise RuntimeError("Authorized portable ML top-up is not enabled")
        if settings.get("failure_policy") != "BASELINE_ONLY":
            raise RuntimeError("Portable ML must fail to the deterministic baseline")
        if settings.get("execution_mode") != "PROSPECTIVE_DEMO_ONLY":
            raise RuntimeError("Portable ML execution mode is not demo-only")
        if float(settings.get("topup_lot", 0.0)) != float(
            config["account"]["fixed_lot"]
        ):
            raise RuntimeError("Portable ML top-up must equal one fixed-lot unit")
    elif config.get("ml_topup", {}).get("enabled"):
        raise RuntimeError("Portable ML top-up is enabled without runtime authority")
    expected = {
        "R1_BOX",
        "R1_PULLBACK",
        "R2_DOWNTREND",
        "R3_COMPRESSION",
        "R4_CHOP",
        "V7_SWING_HEALTH",
        "V8_RETEST_HEALTH",
        "V25_CHOP",
        "V57_BREAK_SWING_H4ADX_HIGH",
    }
    observed = {str(source["source_id"]) for source in config["sources"]}
    if observed != expected:
        raise RuntimeError(f"Canonical source set changed: {sorted(observed)}")
    cooldowns = {
        str(source["source_id"]): int(
            source.get("same_direction_post_loss_cooldown_minutes", 0)
        )
        for source in config["sources"]
        if int(source.get("same_direction_post_loss_cooldown_minutes", 0)) != 0
    }
    if cooldowns != {"V57_BREAK_SWING_H4ADX_HIGH": 120}:
        raise RuntimeError(f"Canonical post-loss cooldowns changed: {cooldowns}")
    verify_deployment_parity(config)
    return config


def load_mt5() -> Any:
    import MetaTrader5 as mt5

    return mt5


def _read_chart_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")) or b"\x00" in raw[:100]:
        return raw.decode("utf-16", errors="replace")
    return raw.decode("utf-8", errors="replace")


def _chart_settings(path: Path) -> dict[str, Any]:
    values: dict[str, str] = {}
    for raw_line in _read_chart_text(path).splitlines():
        line = raw_line.strip()
        if line == "name=Main":
            break
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key == "name" and "expert" not in values:
            values["expert"] = value
        elif key.startswith("Inp"):
            values[key] = value
    return {"path": str(path), "settings": values}


def audit_chart_profile(config: Mapping[str, Any], *, require_ready: bool) -> dict[str, Any]:
    settings = config["preflight"]
    root = Path(settings["chart_profile_directory"])
    charts = sorted(root.glob("*.chr"))
    chart_rows = [_chart_settings(path) for path in charts]
    combined = "\n".join(_read_chart_text(path) for path in charts)
    forbidden = [term for term in settings["forbidden_chart_terms"] if term in combined]
    expectations: dict[str, dict[str, Any]] = {}
    for expected in settings["expected_charts"]:
        expected_inputs = {
            str(key): str(value) for key, value in expected.get("inputs", {}).items()
        }
        expert = str(expected["expert"])
        exact = [
            row
            for row in chart_rows
            if row["settings"].get("expert") == expert
            and all(
                row["settings"].get(key) == value
                for key, value in expected_inputs.items()
            )
        ]
        expectations[str(expected["id"])] = {
            "expert": expert,
            "required_inputs": expected_inputs,
            "matching_chart_paths": [row["path"] for row in exact],
            "ready": len(exact) == 1,
        }
    if forbidden:
        raise RuntimeError(f"Forbidden legacy/ML chart attachment found: {forbidden}")
    ready = bool(charts) and bool(expectations) and all(
        row["ready"] for row in expectations.values()
    )
    if require_ready and not ready:
        failed = [key for key, value in expectations.items() if not value["ready"]]
        raise RuntimeError(
            f"Canonical deterministic MT5 chart profile is incomplete: {failed}"
        )
    return {
        "chart_count": len(charts),
        "forbidden_terms": forbidden,
        "expected_charts": expectations,
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
    cycle_age_seconds = 0.0
    cycle_within_deadline = True
    if bool(status.get("cycle_in_progress")):
        cycle_started = parse_utc(str(status["cycle_started_at_utc"]))
        cycle_age_seconds = max(0.0, (utc_now() - cycle_started).total_seconds())
        cycle_within_deadline = cycle_age_seconds <= int(
            config["runtime"]["maximum_feed_cycle_seconds"]
        )
    required = {
        "R1_BOX",
        "R1_PULLBACK",
        "R2_R3",
        "R4",
        "CORE_OUTCOMES",
        "R5_COMPONENTS",
        "R5_RESOLVER",
        "R5_ROUTER",
        "ADDONS",
    }
    observed = set(status.get("feeds", {}))
    ready = (
        required.issubset(observed)
        and bool(status.get("all_requested_feeds_ok"))
        and age_seconds
        <= int(config["runtime"]["maximum_feed_status_age_seconds"])
        and cycle_within_deadline
    )
    if require_ready and not ready:
        raise RuntimeError(
            f"Canonical feeds are not ready: age={age_seconds:.1f}s "
            f"all_ok={status.get('all_requested_feeds_ok')} "
            f"cycle_age={cycle_age_seconds:.1f}s"
        )
    return {
        "ready": ready,
        "age_seconds": age_seconds,
        "cycle_age_seconds": cycle_age_seconds,
        "cycle_in_progress": bool(status.get("cycle_in_progress")),
        "cycle_within_deadline": cycle_within_deadline,
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
    if str(expected["required_trade_mode"]) != "DEMO" or int(account.trade_mode) != 0:
        raise RuntimeError("Non-demo account trade mode refused")
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
) -> PositionOriginPnl:
    start = parse_utc(state["activated_at_utc"]) - timedelta(minutes=1)
    deals = mt5.history_deals_get(start, utc_now())
    if deals is None:
        raise RuntimeError("MT5 deal history is unavailable for V60 P/L accounting")
    snapshot = position_origin_pnl(
        deals,
        magics,
        symbol,
        entry_in=int(getattr(mt5, "DEAL_ENTRY_IN", 0)),
        entry_inout=int(getattr(mt5, "DEAL_ENTRY_INOUT", 2)),
    )
    return snapshot.scaled(float(config["account"]["usd_to_account_currency"]))


def recent_same_direction_losses(
    mt5: Any,
    config: Mapping[str, Any],
    state: Mapping[str, Any],
    positions: list[Any],
    now: datetime,
) -> tuple[dict[tuple[str, str], datetime], bool]:
    cooldown_sources = {
        int(source["magic"]): str(source["source_id"])
        for source in config["sources"]
        if int(source.get("same_direction_post_loss_cooldown_minutes", 0)) > 0
    }
    if not cooldown_sources:
        return {}, True
    start = parse_utc(state["activated_at_utc"]) - timedelta(minutes=1)
    deals = mt5.history_deals_get(start, now)
    if deals is None:
        return {}, False

    symbol = str(config["account"]["symbol"])
    entry_in = int(getattr(mt5, "DEAL_ENTRY_IN", 0))
    entry_out_values = {
        int(getattr(mt5, "DEAL_ENTRY_OUT", 1)),
        int(getattr(mt5, "DEAL_ENTRY_OUT_BY", 3)),
    }
    buy_type = int(getattr(mt5, "DEAL_TYPE_BUY", 0))
    active_position_ids = {
        int(getattr(position, "identifier", getattr(position, "ticket", -1)))
        for position in positions
    }
    origins: dict[int, tuple[str, str]] = {}
    deal_rows: dict[int, list[Any]] = {}
    for deal in deals:
        if str(getattr(deal, "symbol", "")) != symbol:
            continue
        position_id = int(getattr(deal, "position_id", 0) or 0)
        if position_id <= 0:
            continue
        deal_rows.setdefault(position_id, []).append(deal)
        magic = int(getattr(deal, "magic", -1))
        if (
            magic in cooldown_sources
            and int(getattr(deal, "entry", -1)) == entry_in
        ):
            direction = (
                "LONG"
                if int(getattr(deal, "type", -1)) == buy_type
                else "SHORT"
            )
            origins[position_id] = (cooldown_sources[magic], direction)

    recent: dict[tuple[str, str], datetime] = {}
    for position_id, key in origins.items():
        if position_id in active_position_ids:
            continue
        lifecycle = deal_rows.get(position_id, [])
        exits = [
            deal
            for deal in lifecycle
            if int(getattr(deal, "entry", -1)) in entry_out_values
        ]
        if not exits:
            continue
        net_pnl = sum(
            float(getattr(deal, "profit", 0.0))
            + float(getattr(deal, "commission", 0.0))
            + float(getattr(deal, "swap", 0.0))
            + float(getattr(deal, "fee", 0.0))
            for deal in lifecycle
        )
        if net_pnl >= 0.0:
            continue
        closed_at = max(
            datetime.fromtimestamp(
                int(
                    getattr(
                        deal,
                        "time_msc",
                        int(getattr(deal, "time", 0)) * 1000,
                    )
                )
                / 1000.0,
                tz=UTC,
            )
            for deal in exits
        )
        if key not in recent or closed_at > recent[key]:
            recent[key] = closed_at
    return recent, True


def post_loss_cooldown_active(
    candidate: Any,
    recent_losses: Mapping[tuple[str, str], datetime],
    now: datetime,
) -> bool:
    minutes = int(candidate.same_direction_post_loss_cooldown_minutes)
    if minutes <= 0:
        return False
    closed_at = recent_losses.get((candidate.source_id, candidate.direction))
    return closed_at is not None and now < closed_at + timedelta(minutes=minutes)


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


def locate_position(
    mt5: Any,
    symbol: str,
    magic: int,
    comment: str,
    *,
    before_tickets: set[int] | None = None,
) -> Any | None:
    candidates = [
        position
        for position in (mt5.positions_get(symbol=symbol) or [])
        if int(getattr(position, "magic", -1)) == magic
    ]
    exact = [p for p in candidates if str(getattr(p, "comment", "")) == comment]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        return None
    if before_tickets is None:
        return None
    newly_opened = [
        position
        for position in candidates
        if int(getattr(position, "ticket", -1)) not in before_tickets
    ]
    return newly_opened[0] if len(newly_opened) == 1 else None


def locate_position_from_deal(
    mt5: Any, result: Any, symbol: str, magic: int
) -> Any | None:
    deal_ticket = int(getattr(result, "deal", 0) or 0)
    if deal_ticket <= 0:
        return None
    now = utc_now()
    deals = mt5.history_deals_get(now - timedelta(minutes=5), now) or []
    matching = [
        deal
        for deal in deals
        if int(getattr(deal, "ticket", 0)) == deal_ticket
        and int(getattr(deal, "magic", -1)) == magic
        and str(getattr(deal, "symbol", "")) == symbol
    ]
    if len(matching) != 1:
        return None
    position_id = int(getattr(matching[0], "position_id", 0) or 0)
    if position_id <= 0:
        return None
    positions = mt5.positions_get(ticket=position_id) or []
    return positions[0] if len(positions) == 1 else None


def open_candidate(
    mt5: Any,
    candidate: Any,
    config: Mapping[str, Any],
    symbol_info: Any,
    tick: Any,
    *,
    volume: float | None = None,
    comment_override: str | None = None,
) -> tuple[Any, str, str | None, Any | None]:
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
    comment = (
        candidate_comment(candidate)
        if comment_override is None
        else str(comment_override)[:31]
    )
    before_tickets = {
        int(position.ticket)
        for position in (mt5.positions_get(symbol=config["account"]["symbol"]) or [])
    }
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": config["account"]["symbol"],
        "volume": float(
            config["account"]["fixed_lot"] if volume is None else volume
        ),
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
    position = None
    if result is not None and int(result.retcode) in SUCCESS_RETCODES:
        for _ in range(10):
            position = locate_position(
                mt5,
                config["account"]["symbol"],
                candidate.magic,
                comment,
                before_tickets=before_tickets,
            )
            if position is not None:
                break
            time.sleep(0.1)
        if position is None:
            position = locate_position_from_deal(
                mt5, result, config["account"]["symbol"], candidate.magic
            )
    return result, comment, close_deadline(candidate, utc_now()), position


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
        raw_ticket = metadata.get("ticket")
        if raw_ticket is None:
            position = locate_position(
                mt5,
                config["account"]["symbol"],
                int(metadata["magic"]),
                str(metadata["comment"]),
            )
            if position is None:
                metadata["status"] = "POSITION_IDENTITY_UNRESOLVED"
                metadata["last_reconciliation_at_utc"] = utc_text(now)
                continue
            raw_ticket = int(position.ticket)
            metadata["ticket"] = raw_ticket
            metadata["status"] = "OPEN"
            current[raw_ticket] = position
        ticket = int(raw_ticket)
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


def active_initial_risk(
    positions: list[Any],
    state: Mapping[str, Any],
    symbol_info: Any,
    mt5: Any,
) -> tuple[float, dict[str, float]]:
    metadata_by_ticket = {
        int(metadata["ticket"]): metadata
        for metadata in state.get("positions", {}).values()
        if metadata.get("ticket") is not None
    }
    by_direction = {"LONG": 0.0, "SHORT": 0.0}
    total = 0.0
    for position in positions:
        ticket = int(position.ticket)
        metadata = metadata_by_ticket.get(ticket, {})
        risk = float(metadata.get("initial_risk_usd", 0.0))
        if risk <= 0.0:
            stop = float(getattr(position, "sl", 0.0) or 0.0)
            opened = float(getattr(position, "price_open", 0.0) or 0.0)
            if stop > 0.0 and opened > 0.0:
                ounces = float(symbol_info.trade_contract_size) * float(position.volume)
                risk = abs(opened - stop) * ounces
        direction = (
            "LONG"
            if int(position.type) == int(mt5.POSITION_TYPE_BUY)
            else "SHORT"
        )
        total += risk
        by_direction[direction] += risk
    return total, by_direction


def ml_topup_risk_reason(
    candidate: Any,
    config: Mapping[str, Any],
    state: Mapping[str, Any],
    positions: list[Any],
    *,
    active_initial_risk_usd: float,
    active_direction_risk_usd: Mapping[str, float],
    active_addon_risk_usd: float,
    effective_risk_limits: Mapping[str, float],
) -> str | None:
    settings = config["ml_topup"]
    source = next(
        (
            value
            for value in config["sources"]
            if str(value["source_id"]) == candidate.source_id
        ),
        None,
    )
    if source is None:
        return "ML_TOPUP_UNKNOWN_SOURCE"
    additional_risk = float(candidate.initial_risk_usd)
    maximum_source_risk = source.get("maximum_risk_usd")
    if maximum_source_risk is None:
        return "ML_TOPUP_SOURCE_RISK_LIMIT_UNAVAILABLE"
    if additional_risk * 2.0 > float(maximum_source_risk):
        return "ML_TOPUP_SOURCE_RISK_LIMIT"

    metadata_by_ticket = {
        int(metadata["ticket"]): metadata
        for metadata in state.get("positions", {}).values()
        if metadata.get("ticket") is not None
    }
    unknown_sources = set(settings["historically_unknown_risk_source_ids"])
    for position in positions:
        metadata = metadata_by_ticket.get(int(position.ticket), {})
        if metadata.get("source_id") in unknown_sources:
            return "ML_TOPUP_ACTIVE_HISTORICALLY_UNKNOWN_RISK"

    if (
        active_initial_risk_usd + additional_risk
        > float(effective_risk_limits["maximum_account_concurrent_initial_risk_usd"])
    ):
        return "ML_TOPUP_MAXIMUM_ACCOUNT_CONCURRENT_INITIAL_RISK"
    if (
        float(active_direction_risk_usd[candidate.direction]) + additional_risk
        > float(
            effective_risk_limits[
                "maximum_directional_concurrent_initial_risk_usd"
            ]
        )
    ):
        return "ML_TOPUP_MAXIMUM_DIRECTIONAL_CONCURRENT_INITIAL_RISK"
    if candidate.sleeve_type == "ADDON" and (
        active_addon_risk_usd + additional_risk
        > float(config["risk"]["maximum_addon_concurrent_initial_risk_usd"])
    ):
        return "ML_TOPUP_MAXIMUM_ADDON_CONCURRENT_INITIAL_RISK"
    if len(positions) >= int(config["risk"]["maximum_account_xau_positions"]):
        return "ML_TOPUP_MAXIMUM_ACCOUNT_XAU_POSITIONS"

    current_tickets = {int(position.ticket) for position in positions}
    open_ml_topups = sum(
        bool(metadata.get("ml_topup"))
        and metadata.get("ticket") is not None
        and int(metadata["ticket"]) in current_tickets
        for metadata in state.get("positions", {}).values()
    )
    if open_ml_topups >= int(settings["maximum_open_ml_topups"]):
        return "ML_TOPUP_MAXIMUM_OPEN_TOPUPS"
    ml_state = state.get("ml_topup", {})
    if candidate.candidate_id in ml_state.get("orders", {}):
        return "ML_TOPUP_DUPLICATE_EVENT"
    date_key = candidate.scheduled_at.date().isoformat()
    if int(ml_state.get("daily_topups", {}).get(date_key, 0)) >= int(
        settings["maximum_ml_topups_per_utc_day"]
    ):
        return "ML_TOPUP_MAXIMUM_DAILY_TOPUPS"
    return None


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
    ml_authorized = bool(config["authorization"].get("ml_runtime_authorized"))
    ml_runtime = (
        prepare_ml_topup_runtime(mt5, REPO_ROOT, config, symbol_info)
        if ml_authorized
        else {"ready": False, "reason": "ML_RUNTIME_UNAUTHORIZED"}
    )
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
        state,
        equity=equity_usd,
        closed_pnl=pnl.closed_pnl,
        reconstructed_peak_closed_pnl=pnl.peak_closed_pnl,
        risk=config["risk"],
    )
    state["closed_pnl_attribution"] = {
        "mode": "POSITION_ORIGIN",
        "attributed_positions": pnl.attributed_positions,
        "attributed_deals": pnl.attributed_deals,
    }
    if execution_enabled:
        manage_horizon_exits(mt5, config, state, events_path, now)

    positions = list(mt5.positions_get(symbol=symbol) or [])
    recent_losses, loss_history_available = recent_same_direction_losses(
        mt5, config, state, positions, now
    )
    ours = own_positions(positions, magics, symbol)
    core_positions = own_positions(positions, core_magics, symbol)
    addon_positions = own_positions(positions, addon_magics, symbol)
    active_initial_risk_usd, active_direction_risk_usd = active_initial_risk(
        ours, state, symbol_info, mt5
    )
    active_addon_risk, _ = active_initial_risk(
        addon_positions, state, symbol_info, mt5
    )
    risk = config["risk"]
    effective_risk_limits = {
        key: effective_risk_threshold_usd(state, risk, key)
        for key in (
            "closed_drawdown_suspend_usd",
            "closed_drawdown_resume_usd",
            "combined_closed_drawdown_hard_stop_usd",
            "floating_drawdown_hard_stop_usd",
            "maximum_account_concurrent_initial_risk_usd",
            "maximum_directional_concurrent_initial_risk_usd",
        )
    }
    hard_floating_stop = floating_drawdown(state, equity_usd) >= float(
        effective_risk_limits["floating_drawdown_hard_stop_usd"]
    )
    combined_closed_stop = float(state["closed_drawdown_usd"]) >= float(
        effective_risk_limits["combined_closed_drawdown_hard_stop_usd"]
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
        active_initial_risk_usd, active_direction_risk_usd = active_initial_risk(
            ours, state, symbol_info, mt5
        )
        active_addon_risk, _ = active_initial_risk(
            addon_positions, state, symbol_info, mt5
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
        elif (
            active_initial_risk_usd + candidate.initial_risk_usd
            > float(
                effective_risk_limits[
                    "maximum_account_concurrent_initial_risk_usd"
                ]
            )
        ):
            reason = "MAXIMUM_ACCOUNT_CONCURRENT_INITIAL_RISK"
        elif (
            active_direction_risk_usd[candidate.direction]
            + candidate.initial_risk_usd
            > float(
                effective_risk_limits[
                    "maximum_directional_concurrent_initial_risk_usd"
                ]
            )
        ):
            reason = "MAXIMUM_DIRECTIONAL_CONCURRENT_INITIAL_RISK"
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
            candidate.same_direction_post_loss_cooldown_minutes > 0
            and not loss_history_available
        ):
            reason = "POST_LOSS_COOLDOWN_HISTORY_UNAVAILABLE"
        elif post_loss_cooldown_active(candidate, recent_losses, now):
            reason = "SAME_DIRECTION_POST_LOSS_COOLDOWN"
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
            and str(item.get("status", "")).startswith("ORDER_FILLED")
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
            result, comment, deadline, position = open_candidate(
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

        ticket = None if position is None else int(position.ticket)
        fill_status = (
            "ORDER_FILLED"
            if ticket is not None
            else "ORDER_FILLED_POSITION_UNRESOLVED"
        )
        mark_seen(
            state,
            candidate,
            fill_status,
            now,
            retcode=retcode,
            ticket=ticket,
            broker_order=int(getattr(result, "order", 0) or 0),
            broker_deal=int(getattr(result, "deal", 0) or 0),
        )
        state["positions"][candidate.candidate_id] = {
            "ticket": ticket,
            "magic": candidate.magic,
            "comment": comment,
            "source_id": candidate.source_id,
            "sleeve_type": candidate.sleeve_type,
            "direction": candidate.direction,
            "initial_risk_usd": candidate.initial_risk_usd,
            "event_id": candidate.event_id,
            "opened_at_utc": utc_text(now),
            "close_at_utc": deadline,
            "status": (
                "OPEN" if ticket is not None else "POSITION_IDENTITY_UNRESOLVED"
            ),
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
        active_initial_risk_usd, active_direction_risk_usd = active_initial_risk(
            ours, state, symbol_info, mt5
        )
        active_addon_risk, _ = active_initial_risk(
            addon_positions, state, symbol_info, mt5
        )
        # The deterministic fill is durable before any optional model work.
        atomic_write_json(state_path, state)
        if ml_authorized:
            ml_decision = evaluate_ml_topup_candidate(
                ml_runtime, config, state, candidate, now
            )
            if bool(ml_decision.get("topup")):
                topup_reason = (
                    "ML_TOPUP_BASELINE_POSITION_IDENTITY_UNRESOLVED"
                    if ticket is None
                    else ml_topup_risk_reason(
                        candidate,
                        config,
                        state,
                        positions,
                        active_initial_risk_usd=active_initial_risk_usd,
                        active_direction_risk_usd=active_direction_risk_usd,
                        active_addon_risk_usd=active_addon_risk,
                        effective_risk_limits=effective_risk_limits,
                    )
                )
                topup_tick = mt5.symbol_info_tick(symbol)
                if topup_reason is None and topup_tick is None:
                    topup_reason = "ML_TOPUP_NO_BROKER_TICK"
                if topup_reason is None:
                    topup_tick_time = datetime.fromtimestamp(
                        int(topup_tick.time_msc) / 1000.0, tz=UTC
                    )
                    if (utc_now() - topup_tick_time).total_seconds() > int(
                        config["runtime"]["maximum_tick_age_seconds"]
                    ):
                        topup_reason = "ML_TOPUP_STALE_BROKER_TICK"

                ml_state = state["ml_topup"]
                order_record = {
                    "candidate_id": candidate.candidate_id,
                    "source_id": candidate.source_id,
                    "decision_score": float(ml_decision["score"]),
                    "decision_rank": float(ml_decision["rank"]),
                    "requested_at_utc": utc_text(utc_now()),
                    "status": "TOPUP_REJECTED",
                    "reason": topup_reason,
                }
                if topup_reason is None:
                    try:
                        (
                            topup_result,
                            topup_order_comment,
                            topup_deadline,
                            topup_position,
                        ) = open_candidate(
                            mt5,
                            candidate,
                            config,
                            symbol_info,
                            topup_tick,
                            volume=float(config["ml_topup"]["topup_lot"]),
                            comment_override=topup_comment(candidate),
                        )
                        topup_retcode = (
                            None
                            if topup_result is None
                            else int(topup_result.retcode)
                        )
                        order_record.update(
                            {
                                "retcode": topup_retcode,
                                "broker_comment": (
                                    None
                                    if topup_result is None
                                    else str(topup_result.comment)
                                ),
                            }
                        )
                        if topup_retcode in SUCCESS_RETCODES:
                            topup_ticket = (
                                None
                                if topup_position is None
                                else int(topup_position.ticket)
                            )
                            order_record.update(
                                {
                                    "status": (
                                        "ORDER_FILLED"
                                        if topup_ticket is not None
                                        else "ORDER_FILLED_POSITION_UNRESOLVED"
                                    ),
                                    "reason": None,
                                    "ticket": topup_ticket,
                                    "broker_order": int(
                                        getattr(topup_result, "order", 0) or 0
                                    ),
                                    "broker_deal": int(
                                        getattr(topup_result, "deal", 0) or 0
                                    ),
                                }
                            )
                            position_key = f"{candidate.candidate_id}:ML3"
                            state["positions"][position_key] = {
                                "ticket": topup_ticket,
                                "magic": candidate.magic,
                                "comment": topup_order_comment,
                                "source_id": candidate.source_id,
                                "sleeve_type": candidate.sleeve_type,
                                "direction": candidate.direction,
                                "initial_risk_usd": candidate.initial_risk_usd,
                                "event_id": candidate.event_id,
                                "ml_topup": True,
                                "ml_parent_candidate_id": candidate.candidate_id,
                                "ml_score": float(ml_decision["score"]),
                                "ml_rank": float(ml_decision["rank"]),
                                "opened_at_utc": utc_text(utc_now()),
                                "close_at_utc": topup_deadline,
                                "status": (
                                    "OPEN"
                                    if topup_ticket is not None
                                    else "POSITION_IDENTITY_UNRESOLVED"
                                ),
                            }
                            date_key = candidate.scheduled_at.date().isoformat()
                            ml_state["daily_topups"][date_key] = (
                                int(ml_state["daily_topups"].get(date_key, 0)) + 1
                            )
                        else:
                            order_record["reason"] = "ML_TOPUP_ORDER_NOT_FILLED"
                    except Exception as exc:
                        order_record.update(
                            {
                                "status": "TOPUP_REJECTED",
                                "reason": "ML_TOPUP_ORDER_EXCEPTION",
                                "detail": f"{type(exc).__name__}: {exc}",
                            }
                        )
                ml_state["orders"][candidate.candidate_id] = order_record
                append_event(
                    events_path,
                    order_record | {"event": "ML_TOPUP_ORDER_RESULT"},
                )
                positions = list(mt5.positions_get(symbol=symbol) or [])
                ours = own_positions(positions, magics, symbol)
                core_positions = own_positions(positions, core_magics, symbol)
                addon_positions = own_positions(positions, addon_magics, symbol)
                (
                    active_initial_risk_usd,
                    active_direction_risk_usd,
                ) = active_initial_risk(ours, state, symbol_info, mt5)
                active_addon_risk, _ = active_initial_risk(
                    addon_positions, state, symbol_info, mt5
                )
                atomic_write_json(state_path, state)
        processed += 1

    atomic_write_json(state_path, state)
    emergency_close_failures = sum(
        record["retcode"] not in SUCCESS_RETCODES
        for record in emergency_close_results
    )
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
        "closed_pnl_attribution": dict(state["closed_pnl_attribution"]),
        "closed_drawdown_usd": float(state["closed_drawdown_usd"]),
        "floating_drawdown_usd": floating_drawdown(state, equity_usd),
        "drawdown_suspended": bool(state["drawdown_suspended"]),
        "hard_floating_stop": hard_floating_stop,
        "combined_closed_drawdown_hard_stop": combined_closed_stop,
        "active_entry_halt_files": entry_halts,
        "emergency_close_results": emergency_close_results,
        "emergency_close_failures": emergency_close_failures,
        "effective_risk_limits_usd": effective_risk_limits,
        "risk_limit_mode": "ACTIVATION_EQUITY_SCALED",
        "equity_fraction_limits_enabled": bool(
            config["risk"]["equity_fraction_limits_enabled"]
        ),
        "core_open_positions": len(core_positions),
        "addon_open_positions": len(addon_positions),
        "addon_active_initial_risk_usd": active_addon_risk,
        "account_active_initial_risk_usd": active_initial_risk_usd,
        "direction_active_initial_risk_usd": active_direction_risk_usd,
        "account_xau_positions": len(positions),
        "seen_candidates": len(state["seen"]),
        "processed_this_cycle": processed,
        "post_loss_cooldown_history_available": loss_history_available,
        "recent_same_direction_losses": {
            f"{source_id}:{direction}": utc_text(closed_at)
            for (source_id, direction), closed_at in sorted(recent_losses.items())
        },
        "demo_authorized": True,
        "minimum_balance_requirement_enabled": False,
        "demo_balance_eligibility_waived": True,
        "broker_action_authorized": True,
        "execution_enabled": execution_enabled,
        "live_authorized": False,
        "ml_runtime_authorized": ml_authorized,
        "ml_shadow_authorized": False,
        "ml_topup": ml_topup_status_snapshot(ml_runtime, state),
        "chart_profile_preflight": profile,
        "feed_preflight": feeds,
        "broker_geometry_preflight": broker_geometry,
        "canonical_sources": sorted(source["source_id"] for source in config["sources"]),
    }
    atomic_write_json(status_path, status)
    return status


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the V59/V60 canonical demo portfolio"
    )
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--ml-overlay", type=Path)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    config = load_config(
        args.config.resolve(),
        None if args.ml_overlay is None else args.ml_overlay.resolve(),
    )
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
                    "ml_runtime_authorized": bool(
                        config["authorization"].get("ml_runtime_authorized")
                    ),
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
