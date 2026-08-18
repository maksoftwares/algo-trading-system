from __future__ import annotations

import argparse
import hashlib
import json
import os
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
PROTECTION_OVERLAY_PATH = ROOT / "config" / "v60_drawdown_protection_v1_overlay.json"
ML_TOPUP_SEND_ATTEMPTS = 3
ML_TOPUP_SEND_RETRY_SECONDS = 1.0
SAFE_ORDER_SEND_RETRY_RETCODES = RETRYABLE_RETCODES - {10012}
MT5_IPC_SEND_FAILED = -10001


class SingleInstanceLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.handle: Any | None = None

    def __enter__(self) -> SingleInstanceLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        if handle.seek(0, os.SEEK_END) == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            handle.close()
            raise RuntimeError("Another V60 portfolio executor is already running") from exc
        self.handle = handle
        return self

    def __exit__(self, *_args: Any) -> None:
        if self.handle is None:
            return
        try:
            self.handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        finally:
            self.handle.close()
            self.handle = None


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


def apply_protection_overlay(
    config: dict[str, Any], base_path: Path, overlay_path: Path
) -> dict[str, Any]:
    overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
    if overlay.get("schema_version") != "xauusd_v60_drawdown_protection_v1_overlay":
        raise RuntimeError("Unexpected drawdown-protection overlay schema")
    expected_base = overlay["base_config"]
    expected_path = REPO_ROOT / str(expected_base["path"])
    if expected_path.resolve() != base_path.resolve():
        raise RuntimeError("Drawdown-protection overlay is bound to another config")
    if sha256_file(base_path) != str(expected_base["sha256"]):
        raise RuntimeError("Drawdown-protection base config identity changed")
    settings = overlay["portfolio_protection"]
    expected = {
        "enabled": True,
        "open_profit_arm_r": 1.5,
        "open_profit_retain_r": 0.5,
        "same_direction_source_families": [["R4_CHOP", "V25_CHOP"]],
        "soft_addon_block_drawdown_fraction": 0.20,
        "soft_core_concurrency_drawdown_fraction": 0.22,
        "soft_core_maximum_open_positions": 1,
        "soft_ml_topup_block_drawdown_fraction": 0.10,
    }
    if settings != expected:
        raise RuntimeError("Drawdown-protection policy differs from the locked candidate")
    config["portfolio_protection"] = settings
    config["_protection_overlay_path"] = str(overlay_path)
    return config


def load_config(
    path: Path = CONFIG_PATH,
    ml_overlay_path: Path | None = None,
    protection_overlay_path: Path | None = None,
) -> dict[str, Any]:
    path = path.resolve()
    config = json.loads(path.read_text(encoding="utf-8"))
    if protection_overlay_path is not None:
        config = apply_protection_overlay(
            config, path, protection_overlay_path.resolve()
        )
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
            "Canonical demo entry-risk limits must use activation-equity scaling"
        )
    if config["risk"].get("drawdown_equity_fraction_limits_enabled") is not False:
        raise RuntimeError(
            "Canonical fixed-lot drawdown limits must use explicit USD thresholds"
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
    parity = verify_deployment_parity(config)
    historical_drawdown = float(parity["all_history"]["closed_trade_drawdown_usd"])
    hard_closed_limit = float(
        config["risk"]["combined_closed_drawdown_hard_stop_usd"]
    )
    hard_floating_limit = float(config["risk"]["floating_drawdown_hard_stop_usd"])
    if min(hard_closed_limit, hard_floating_limit) < historical_drawdown * 1.5:
        raise RuntimeError(
            "Canonical hard drawdown limits lack 1.5x historical headroom"
        )
    recovery = config["risk"].get("closed_drawdown_recovery")
    if not isinstance(recovery, Mapping) or recovery.get("enabled") is not True:
        raise RuntimeError("Canonical closed-drawdown recovery mode is not enabled")
    source_sleeves = {
        str(source["source_id"]): str(source.get("sleeve_type", "CORE")).upper()
        for source in config["sources"]
    }
    recovery_sources = {str(value) for value in recovery["eligible_source_ids"]}
    if not recovery_sources or any(
        source_sleeves.get(source_id) != "CORE" for source_id in recovery_sources
    ):
        raise RuntimeError("Closed-drawdown recovery sources must be known CORE sleeves")
    return config


def load_mt5() -> Any:
    import MetaTrader5 as mt5

    return mt5


def mt5_session_problem(mt5: Any, config: Mapping[str, Any]) -> str | None:
    terminal = mt5.terminal_info()
    if terminal is None:
        return "terminal information is unavailable"
    if not bool(getattr(terminal, "connected", False)):
        return "terminal is disconnected"
    account = mt5.account_info()
    if account is None:
        return "account information is unavailable"
    if int(getattr(account, "login", 0)) != int(config["account"]["expected_login"]):
        return "terminal is connected to the wrong account"
    if str(getattr(account, "server", "")) != str(config["account"]["expected_server"]):
        return "terminal is connected to the wrong server"
    symbol = mt5.symbol_info(str(config["account"]["symbol"]))
    if symbol is None:
        return "symbol information is unavailable"
    return None


def initialize_mt5_session(mt5: Any, config: Mapping[str, Any]) -> None:
    terminal = str(Path(config["account"]["terminal_exe"]).resolve())
    attempts = max(1, int(config["runtime"].get("mt5_initialize_attempts", 3)))
    delay = max(0.0, float(config["runtime"].get("mt5_reconnect_delay_seconds", 2)))
    problems: list[str] = []
    for attempt in range(1, attempts + 1):
        try:
            mt5.shutdown()
        except Exception:
            pass
        if not mt5.initialize(path=terminal, portable=True):
            problems.append(f"attempt {attempt}: initialize failed: {mt5.last_error()}")
        else:
            problem = mt5_session_problem(mt5, config)
            if problem is None:
                return
            problems.append(f"attempt {attempt}: {problem}")
        if attempt < attempts and delay > 0.0:
            time.sleep(delay)
    raise RuntimeError("MT5 session recovery failed; " + "; ".join(problems))


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
        "ADDONS",
    }
    feed_rows = status.get("feeds", {})
    observed = set(feed_rows)
    execution_feeds_ok = required.issubset(observed) and all(
        bool(feed_rows[name].get("ok")) for name in required
    )
    if "execution_feeds_ok" in status:
        execution_feeds_ok = execution_feeds_ok and bool(
            status["execution_feeds_ok"]
        )
    ready = (
        execution_feeds_ok
        and age_seconds
        <= int(config["runtime"]["maximum_feed_status_age_seconds"])
        and cycle_within_deadline
    )
    if require_ready and not ready:
        raise RuntimeError(
            f"Canonical feeds are not ready: age={age_seconds:.1f}s "
            f"execution_ok={execution_feeds_ok} "
            f"cycle_age={cycle_age_seconds:.1f}s"
        )
    return {
        "ready": ready,
        "age_seconds": age_seconds,
        "cycle_age_seconds": cycle_age_seconds,
        "cycle_in_progress": bool(status.get("cycle_in_progress")),
        "cycle_within_deadline": cycle_within_deadline,
        "execution_feeds_ok": execution_feeds_ok,
        "all_requested_feeds_ok": execution_feeds_ok,
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


def mt5_last_error_snapshot(mt5: Any) -> dict[str, Any] | None:
    try:
        value = mt5.last_error()
    except Exception as exc:
        return {"exception": f"{type(exc).__name__}: {exc}"}
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        code = value[0] if value else None
        message = value[1] if len(value) > 1 else ""
        try:
            code = None if code is None else int(code)
        except (TypeError, ValueError):
            code = str(code)
        return {"code": code, "message": str(message)}
    return {"value": str(value)}


def send_request(
    mt5: Any,
    request: dict[str, Any],
    *,
    maximum_attempts: int = 1,
    retry_delay_seconds: float = 0.0,
    diagnostics: dict[str, Any] | None = None,
) -> Any:
    fill_modes = [
        mt5.ORDER_FILLING_IOC,
        mt5.ORDER_FILLING_RETURN,
        mt5.ORDER_FILLING_FOK,
    ]
    maximum_attempts = max(1, int(maximum_attempts))
    request_records: list[dict[str, Any]] = []
    last = None
    attempts_used = 0

    def finish() -> None:
        if diagnostics is None:
            return
        diagnostics.clear()
        diagnostics.update(
            {
                "maximum_attempts": maximum_attempts,
                "attempts_used": attempts_used,
                "requests": request_records,
                "last_error": mt5_last_error_snapshot(mt5),
            }
        )

    for request_attempt in range(1, maximum_attempts + 1):
        attempts_used = request_attempt
        retryable_round = False
        for filling in fill_modes:
            attempt = dict(request, type_filling=filling)
            record: dict[str, Any] = {
                "attempt": request_attempt,
                "fill_mode": int(filling),
            }
            check = mt5.order_check(attempt)
            if check is None:
                retryable_round = True
                record.update(
                    {
                        "order_check": "NONE",
                        "last_error": mt5_last_error_snapshot(mt5),
                    }
                )
                request_records.append(record)
                continue
            last = check
            check_retcode = int(check.retcode)
            record.update(
                {
                    "check_retcode": check_retcode,
                    "check_comment": str(getattr(check, "comment", "")),
                }
            )
            if check_retcode not in {0, *SUCCESS_RETCODES}:
                retryable_round = retryable_round or check_retcode in {
                    10030,
                    *RETRYABLE_RETCODES,
                }
                request_records.append(record)
                continue
            result = mt5.order_send(attempt)
            if result is None:
                last_error = mt5_last_error_snapshot(mt5)
                record.update(
                    {
                        "order_send": "NONE",
                        "last_error": last_error,
                    }
                )
                request_records.append(record)
                if (
                    last_error is not None
                    and last_error.get("code") == MT5_IPC_SEND_FAILED
                ):
                    retryable_round = True
                    break
                finish()
                return last
            last = result
            result_retcode = int(result.retcode)
            record.update(
                {
                    "send_retcode": result_retcode,
                    "send_comment": str(getattr(result, "comment", "")),
                }
            )
            request_records.append(record)
            if result_retcode in SUCCESS_RETCODES:
                finish()
                return result
            if result_retcode == 10030:
                retryable_round = True
                continue
            if result_retcode in SAFE_ORDER_SEND_RETRY_RETCODES:
                retryable_round = True
                break
            finish()
            return result
        if request_attempt < maximum_attempts and retryable_round:
            time.sleep(max(0.0, float(retry_delay_seconds)))
        else:
            break
    finish()
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
    send_attempts: int = 1,
    send_retry_delay_seconds: float = 0.0,
    request_diagnostics: dict[str, Any] | None = None,
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
    result = send_request(
        mt5,
        request,
        maximum_attempts=send_attempts,
        retry_delay_seconds=send_retry_delay_seconds,
        diagnostics=request_diagnostics,
    )
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


def close_position(
    mt5: Any,
    position: Any,
    config: Mapping[str, Any],
    *,
    comment: str = "V60_HORIZON_EXIT",
) -> Any:
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
        "comment": comment[:31],
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


def position_source_id(
    position: Any, config: Mapping[str, Any], state: Mapping[str, Any]
) -> str | None:
    ticket = int(getattr(position, "ticket", 0) or 0)
    for metadata in state.get("positions", {}).values():
        if int(metadata.get("ticket", 0) or 0) == ticket:
            return str(metadata.get("source_id", "")) or None
    magic = int(getattr(position, "magic", -1))
    for source in config["sources"]:
        if int(source["magic"]) == magic:
            return str(source["source_id"])
    return None


def protection_drawdown_fraction(
    state: Mapping[str, Any], equity_usd: float
) -> float:
    activation = float(state["activation_equity_usd"])
    if activation <= 0.0:
        raise ValueError("Activation equity must be positive")
    return max(
        float(state["closed_drawdown_usd"]),
        floating_drawdown(state, equity_usd),
    ) / activation


def protection_entry_reason(
    candidate: Any,
    config: Mapping[str, Any],
    state: Mapping[str, Any],
    positions: list[Any],
    mt5: Any,
    equity_usd: float,
) -> str | None:
    settings = config.get("portfolio_protection")
    if not isinstance(settings, Mapping) or not bool(settings.get("enabled")):
        return None
    drawdown_fraction = protection_drawdown_fraction(state, equity_usd)
    if candidate.sleeve_type == "ADDON" and drawdown_fraction >= float(
        settings["soft_addon_block_drawdown_fraction"]
    ):
        return "SOFT_DRAWDOWN_ADDON_BLOCK"
    if candidate.sleeve_type == "CORE" and drawdown_fraction >= float(
        settings["soft_core_concurrency_drawdown_fraction"]
    ):
        core_magics = {
            int(source["magic"])
            for source in config["sources"]
            if str(source.get("sleeve_type", "CORE")).upper() == "CORE"
        }
        core_count = sum(
            int(getattr(position, "magic", -1)) in core_magics
            for position in positions
        )
        if core_count >= int(settings["soft_core_maximum_open_positions"]):
            return "SOFT_DRAWDOWN_CORE_CONCURRENCY"
    for family in settings["same_direction_source_families"]:
        if candidate.source_id not in family:
            continue
        for position in positions:
            source_id = position_source_id(position, config, state)
            if source_id not in family or source_id == candidate.source_id:
                continue
            direction = (
                "LONG"
                if int(position.type) == int(mt5.POSITION_TYPE_BUY)
                else "SHORT"
            )
            if direction == candidate.direction:
                return "SAME_DIRECTION_PROTECTION_FAMILY"
    return None


def closed_drawdown_recovery_entry_reason(
    candidate: Any,
    config: Mapping[str, Any],
    state: Mapping[str, Any],
    positions: list[Any],
    equity_usd: float,
    effective_risk_limits: Mapping[str, float],
) -> str | None:
    if not bool(state.get("drawdown_suspended")):
        return None
    settings = config["risk"]["closed_drawdown_recovery"]
    if not bool(settings.get("enabled")):
        return "CLOSED_DRAWDOWN_SUSPENDED"
    if candidate.sleeve_type != "CORE":
        return "DRAWDOWN_RECOVERY_CORE_ONLY"
    if candidate.source_id not in set(settings["eligible_source_ids"]):
        return "DRAWDOWN_RECOVERY_SOURCE_NOT_ELIGIBLE"
    if len(positions) >= int(settings["maximum_open_positions"]):
        return "DRAWDOWN_RECOVERY_MAXIMUM_OPEN_POSITIONS"
    candidate_risk = float(candidate.initial_risk_usd)
    if candidate_risk > float(settings["maximum_initial_risk_usd"]):
        return "DRAWDOWN_RECOVERY_MAXIMUM_INITIAL_RISK"
    current_drawdown = max(
        float(state["closed_drawdown_usd"]),
        floating_drawdown(state, equity_usd),
    )
    hard_limit = min(
        float(effective_risk_limits["combined_closed_drawdown_hard_stop_usd"]),
        float(effective_risk_limits["floating_drawdown_hard_stop_usd"]),
    )
    required_headroom = candidate_risk * float(
        settings["minimum_hard_stop_headroom_multiple"]
    )
    if hard_limit - current_drawdown < required_headroom:
        return "DRAWDOWN_RECOVERY_INSUFFICIENT_HARD_STOP_HEADROOM"
    date_key = candidate.scheduled_at.date().isoformat()
    entries = state.get("drawdown_recovery_daily_entries", {})
    if int(entries.get(date_key, 0)) >= int(
        settings["maximum_entries_per_utc_day"]
    ):
        return "DRAWDOWN_RECOVERY_MAXIMUM_DAILY_ENTRIES"
    return None


def append_runtime_heartbeat(
    state: dict[str, Any],
    events_path: Path,
    config: Mapping[str, Any],
    now: datetime,
    *,
    positions: int,
    processed_candidates: int,
) -> bool:
    interval = max(1, int(config["runtime"]["event_heartbeat_seconds"]))
    previous = state.get("last_event_heartbeat_at_utc")
    if previous is not None and (now - parse_utc(previous)).total_seconds() < interval:
        return False
    append_event(
        events_path,
        {
            "event": "EXECUTOR_HEARTBEAT",
            "at_utc": utc_text(now),
            "process_id": os.getpid(),
            "drawdown_suspended": bool(state.get("drawdown_suspended")),
            "closed_drawdown_usd": float(state.get("closed_drawdown_usd", 0.0)),
            "open_positions": int(positions),
            "processed_candidates": int(processed_candidates),
        },
    )
    state["last_event_heartbeat_at_utc"] = utc_text(now)
    return True


def open_position_pnl_usd(
    positions: list[Any], config: Mapping[str, Any]
) -> float:
    account_value = sum(
        float(getattr(position, "profit", 0.0) or 0.0)
        + float(getattr(position, "swap", 0.0) or 0.0)
        for position in positions
    )
    return account_value_usd(account_value, config)


def strategy_drawdown_equity_usd(
    state: Mapping[str, Any],
    closed_pnl_usd: float,
    positions: list[Any],
    config: Mapping[str, Any],
) -> float:
    """Build an equity curve from V60-owned P/L only."""
    return (
        float(state["activation_equity_usd"])
        + float(closed_pnl_usd)
        + open_position_pnl_usd(positions, config)
    )


def ensure_strategy_drawdown_scope(
    state: dict[str, Any],
    strategy_equity_usd: float,
    reconstructed_peak_closed_pnl_usd: float,
) -> None:
    if state.get("drawdown_equity_scope") == "STRATEGY_ONLY":
        return
    state["peak_equity_usd"] = max(
        float(strategy_equity_usd),
        float(state["activation_equity_usd"])
        + float(reconstructed_peak_closed_pnl_usd),
    )
    state["drawdown_equity_scope"] = "STRATEGY_ONLY"


def manage_open_profit_giveback(
    mt5: Any,
    config: Mapping[str, Any],
    state: dict[str, Any],
    positions: list[Any],
    active_risk_usd: float,
    events_path: Path,
    now: datetime,
) -> dict[str, Any]:
    settings = config.get("portfolio_protection")
    result: dict[str, Any] = {
        "enabled": bool(isinstance(settings, Mapping) and settings.get("enabled")),
        "policy": None if not isinstance(settings, Mapping) else dict(settings),
        "armed": False,
        "open_pnl_usd": 0.0,
        "active_initial_risk_usd": float(active_risk_usd),
        "triggered": False,
        "close_results": [],
    }
    if not result["enabled"]:
        return result
    protection = state.setdefault(
        "open_profit_protection",
        {"armed": False, "peak_open_pnl_usd": 0.0, "tickets": []},
    )
    tickets = sorted(int(position.ticket) for position in positions)
    prior_tickets = {int(value) for value in protection.get("tickets", [])}
    if not positions or active_risk_usd <= 0.0:
        protection.update(
            {"armed": False, "peak_open_pnl_usd": 0.0, "tickets": []}
        )
        return result
    if prior_tickets and not prior_tickets.intersection(tickets):
        protection.update({"armed": False, "peak_open_pnl_usd": 0.0})
    protection["tickets"] = tickets
    open_pnl = open_position_pnl_usd(positions, config)
    protection["peak_open_pnl_usd"] = max(
        float(protection.get("peak_open_pnl_usd", 0.0)), open_pnl
    )
    arm_threshold = float(settings["open_profit_arm_r"]) * active_risk_usd
    retain_threshold = float(settings["open_profit_retain_r"]) * active_risk_usd
    if not bool(protection.get("armed")) and open_pnl >= arm_threshold:
        protection["armed"] = True
        append_event(
            events_path,
            {
                "event": "OPEN_PROFIT_PROTECTION_ARMED",
                "at_utc": utc_text(now),
                "open_pnl_usd": open_pnl,
                "active_initial_risk_usd": active_risk_usd,
                "arm_threshold_usd": arm_threshold,
                "tickets": tickets,
            },
        )
    elif bool(protection.get("armed")) and open_pnl <= retain_threshold:
        result["triggered"] = True
        for position in positions:
            close_result = close_position(
                mt5,
                position,
                config,
                comment="V60_PROFIT_GIVEBACK_EXIT",
            )
            record = {
                "event": "OPEN_PROFIT_GIVEBACK_CLOSE",
                "at_utc": utc_text(now),
                "ticket": int(position.ticket),
                "magic": int(position.magic),
                "open_pnl_usd": open_pnl,
                "active_initial_risk_usd": active_risk_usd,
                "retain_threshold_usd": retain_threshold,
                "retcode": (
                    None if close_result is None else int(close_result.retcode)
                ),
                "comment": (
                    None if close_result is None else str(close_result.comment)
                ),
            }
            result["close_results"].append(record)
            append_event(events_path, record)
    result.update(
        {
            "armed": bool(protection.get("armed")),
            "open_pnl_usd": open_pnl,
            "peak_open_pnl_usd": float(protection["peak_open_pnl_usd"]),
            "arm_threshold_usd": arm_threshold,
            "retain_threshold_usd": retain_threshold,
        }
    )
    return result


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
    equity_usd: float | None = None,
) -> str | None:
    settings = config["ml_topup"]
    if bool(state.get("drawdown_suspended")):
        return "ML_TOPUP_DRAWDOWN_RECOVERY_BLOCK"
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
    protection = config.get("portfolio_protection")
    if (
        isinstance(protection, Mapping)
        and bool(protection.get("enabled"))
        and equity_usd is not None
        and protection_drawdown_fraction(state, equity_usd)
        >= float(protection["soft_ml_topup_block_drawdown_fraction"])
    ):
        return "ML_TOPUP_SOFT_DRAWDOWN_BLOCK"
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
    account_equity_usd = account_value_usd(float(account.equity), config)
    state = load_state(state_path, now, account_equity_usd)
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
    drawdown_positions = own_positions(
        list(mt5.positions_get(symbol=symbol) or []), magics, symbol
    )
    drawdown_equity_usd = strategy_drawdown_equity_usd(
        state, pnl.closed_pnl, drawdown_positions, config
    )
    ensure_strategy_drawdown_scope(
        state, drawdown_equity_usd, pnl.peak_closed_pnl
    )
    refresh_drawdown_state(
        state,
        equity=drawdown_equity_usd,
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
    profit_protection = manage_open_profit_giveback(
        mt5,
        config,
        state,
        ours,
        active_initial_risk_usd,
        events_path,
        now,
    )
    if profit_protection["triggered"]:
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
    hard_floating_stop = floating_drawdown(state, drawdown_equity_usd) >= float(
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
        recovery_mode = bool(state["drawdown_suspended"])
        recovery_reason = closed_drawdown_recovery_entry_reason(
            candidate,
            config,
            state,
            ours,
            drawdown_equity_usd,
            effective_risk_limits,
        )
        protection_reason = protection_entry_reason(
            candidate, config, state, ours, mt5, drawdown_equity_usd
        )
        if age > timedelta(minutes=candidate.maximum_entry_gap_minutes):
            reason = "STALE_CANDIDATE"
        elif profit_protection["triggered"]:
            reason = "OPEN_PROFIT_GIVEBACK_CYCLE_LOCK"
        elif entry_halts:
            reason = "ENTRY_HALT_FILE_ACTIVE"
        elif hard_floating_stop:
            reason = "FLOATING_DRAWDOWN_HARD_STOP"
        elif combined_closed_stop:
            reason = "COMBINED_CLOSED_DRAWDOWN_HARD_STOP"
        elif recovery_mode and recovery_reason is not None:
            reason = recovery_reason
        elif protection_reason is not None:
            reason = protection_reason
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
            "drawdown_recovery_entry": recovery_mode,
        }
        key = daily_key(candidate)
        state["daily_entries"][key] = int(state["daily_entries"].get(key, 0)) + 1
        if recovery_mode:
            recovery_date = candidate.scheduled_at.date().isoformat()
            recovery_entries = state.setdefault(
                "drawdown_recovery_daily_entries", {}
            )
            recovery_entries[recovery_date] = int(
                recovery_entries.get(recovery_date, 0)
            ) + 1
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
        if ml_authorized and not recovery_mode:
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
                        equity_usd=drawdown_equity_usd,
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
                    topup_request_diagnostics: dict[str, Any] = {}
                    order_record["request_diagnostics"] = topup_request_diagnostics
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
                            send_attempts=ML_TOPUP_SEND_ATTEMPTS,
                            send_retry_delay_seconds=ML_TOPUP_SEND_RETRY_SECONDS,
                            request_diagnostics=topup_request_diagnostics,
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

    heartbeat_written = append_runtime_heartbeat(
        state,
        events_path,
        config,
        now,
        positions=len(ours),
        processed_candidates=processed,
    )
    atomic_write_json(state_path, state)
    emergency_close_failures = sum(
        record["retcode"] not in SUCCESS_RETCODES
        for record in emergency_close_results
    )
    profit_protection_close_failures = sum(
        record["retcode"] not in SUCCESS_RETCODES
        for record in profit_protection["close_results"]
    )
    status = {
        "schema_version": "xauusd_v60_canonical_demo_status_v2",
        "updated_at_utc": utc_text(now),
        "status": (
            "FAILED_CLOSED"
            if profit_protection_close_failures
            else (
                "ACTIVE_DEMO_BROKER_ACTION"
                if execution_enabled
                else (
                    "READY_EXECUTION_DISABLED"
                    if profile["ready"] and feeds["ready"]
                    else "PREFLIGHT_PENDING_EXECUTION_DISABLED"
                )
            )
        ),
        "account_login": int(account.login),
        "account_server": str(account.server),
        "symbol": symbol,
        "account_currency": str(account.currency),
        "balance_account_currency": float(account.balance),
        "equity_account_currency": float(account.equity),
        "balance_usd": account_value_usd(float(account.balance), config),
        "equity_usd": account_equity_usd,
        "strategy_equity_usd": drawdown_equity_usd,
        "drawdown_equity_scope": str(state["drawdown_equity_scope"]),
        "activation_equity_usd": float(state["activation_equity_usd"]),
        "closed_pnl_usd": float(state["closed_pnl_usd"]),
        "closed_pnl_attribution": dict(state["closed_pnl_attribution"]),
        "closed_drawdown_usd": float(state["closed_drawdown_usd"]),
        "floating_drawdown_usd": floating_drawdown(state, drawdown_equity_usd),
        "drawdown_suspended": bool(state["drawdown_suspended"]),
        "drawdown_recovery_mode": bool(state["drawdown_suspended"]),
        "drawdown_recovery_policy": dict(
            config["risk"]["closed_drawdown_recovery"]
        ),
        "hard_floating_stop": hard_floating_stop,
        "combined_closed_drawdown_hard_stop": combined_closed_stop,
        "active_entry_halt_files": entry_halts,
        "emergency_close_results": emergency_close_results,
        "emergency_close_failures": emergency_close_failures,
        "profit_protection_close_failures": profit_protection_close_failures,
        "effective_risk_limits_usd": effective_risk_limits,
        "risk_limit_mode": "MIXED_ENTRY_EQUITY_SCALED_DRAWDOWN_ABSOLUTE_USD",
        "equity_fraction_limits_enabled": bool(
            config["risk"]["equity_fraction_limits_enabled"]
        ),
        "drawdown_equity_fraction_limits_enabled": bool(
            config["risk"]["drawdown_equity_fraction_limits_enabled"]
        ),
        "event_heartbeat_written_this_cycle": heartbeat_written,
        "last_event_heartbeat_at_utc": state.get("last_event_heartbeat_at_utc"),
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
        "portfolio_protection": profit_protection,
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
    parser.add_argument("--protection-overlay", type=Path)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    config = load_config(
        args.config.resolve(),
        None if args.ml_overlay is None else args.ml_overlay.resolve(),
        (
            None
            if args.protection_overlay is None
            else args.protection_overlay.resolve()
        ),
    )
    mt5 = load_mt5()
    runtime = Path(config["runtime"]["directory"])
    lock_path = runtime / str(
        config["runtime"].get("single_instance_lock_filename", "portfolio.lock")
    )
    maximum_failures = max(
        1, int(config["runtime"].get("maximum_consecutive_cycle_failures", 3))
    )
    with SingleInstanceLock(lock_path):
        initialize_mt5_session(mt5, config)
        consecutive_failures = 0
        try:
            while True:
                try:
                    problem = mt5_session_problem(mt5, config)
                    if problem is not None:
                        initialize_mt5_session(mt5, config)
                    status = run_cycle(mt5, config)
                    consecutive_failures = 0
                    print(json.dumps(status, sort_keys=True), flush=True)
                except Exception as exc:
                    consecutive_failures += 1
                    failure = {
                        "schema_version": "xauusd_v60_canonical_demo_status_v2",
                        "updated_at_utc": utc_text(datetime.now(UTC)),
                        "status": "FAILED_CLOSED",
                        "error": f"{type(exc).__name__}: {exc}",
                        "consecutive_cycle_failures": consecutive_failures,
                        "broker_action_authorized": True,
                        "execution_enabled": bool(
                            config["runtime"]["execution_enabled"]
                        ),
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
                    try:
                        initialize_mt5_session(mt5, config)
                    except Exception:
                        pass
                    if consecutive_failures >= maximum_failures:
                        return 1
                if args.once:
                    return 0
                time.sleep(int(config["runtime"]["poll_seconds"]))
        finally:
            mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
