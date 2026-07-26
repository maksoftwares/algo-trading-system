from __future__ import annotations

import csv
import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


FORBIDDEN_TRUE_AUTHORITY = (
    "broker_action_allowed",
    "model_training_authorized",
    "python_prediction_authorized",
    "ea_consumption_authorized",
    "demo_execution_authorized",
    "live_execution_authorized",
)

CSV_FIELDS = (
    "schema_version",
    "timestamp_utc",
    "tick_time_msc",
    "run_id",
    "account_login",
    "account_server",
    "symbol",
    "bid",
    "ask",
    "last",
    "volume",
    "volume_real",
    "flags",
    "spread_price",
    "source",
    "broker_action_allowed",
    "model_training_authorized",
    "python_prediction_authorized",
    "ea_consumption_authorized",
    "demo_execution_authorized",
    "live_execution_authorized",
)


class CollectorError(RuntimeError):
    """Fail-closed collector error."""


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    state: Path
    health: Path


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    validate_config(config)
    return config


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != "capital_multisymbol_prospective_v1":
        raise CollectorError("unexpected schema_version")
    account = config["account"]
    if int(account["expected_login"]) != 1033030:
        raise CollectorError("collector is locked to account 1033030")
    if account["expected_server"] != "Capital.ComMena-Demo":
        raise CollectorError("unexpected server contract")
    if not config["symbols"] or len(config["symbols"]) != len(set(config["symbols"])):
        raise CollectorError("symbols must be nonempty and unique")
    for name in FORBIDDEN_TRUE_AUTHORITY:
        if config["authority"].get(name) is not False:
            raise CollectorError(f"{name} must remain false")
    boundary = parse_utc(config["information_boundary"]["start_inclusive_utc"])
    if boundary != datetime(2026, 7, 27, tzinfo=UTC):
        raise CollectorError("information boundary changed")
    root = Path(config["storage"]["root"])
    if root.drive.upper() != "D:":
        raise CollectorError("prospective tick storage must remain on D:")


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise CollectorError("UTC timestamp requires timezone")
    return parsed.astimezone(UTC)


def utc_text_from_msc(value: int) -> str:
    return (
        datetime.fromtimestamp(value / 1000.0, tz=UTC)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def runtime_paths(config: dict[str, Any]) -> RuntimePaths:
    root = Path(config["storage"]["root"])
    return RuntimePaths(
        root=root,
        state=root / config["storage"]["state_relative"],
        health=root / config["storage"]["health_relative"],
    )


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def load_state(path: Path, config: dict[str, Any]) -> dict[str, Any]:
    boundary_ms = int(
        parse_utc(
            config["information_boundary"]["start_inclusive_utc"]
        ).timestamp()
        * 1000
    )
    default = {
        "schema_version": "capital_multisymbol_prospective_state_v1",
        "run_id": config["run_id"],
        "boundary_msc": boundary_ms,
        "symbols": {
            symbol: {
                "scan_cursor_msc": boundary_ms - 1,
                "last_tick_msc": None,
                "rows_written": 0,
            }
            for symbol in config["symbols"]
        },
    }
    if not path.exists():
        return default
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("run_id") != config["run_id"]:
        raise CollectorError("state run_id mismatch")
    if int(state.get("boundary_msc", -1)) != boundary_ms:
        raise CollectorError("state boundary mismatch")
    if set(state.get("symbols", {})) != set(config["symbols"]):
        raise CollectorError("state symbol set mismatch")
    return state


def safe_token(value: str) -> str:
    cleaned = value
    for character in (" ", ".", "-", "/", "\\", ":"):
        cleaned = cleaned.replace(character, "_")
    return cleaned


def partition_path(
    config: dict[str, Any], paths: RuntimePaths, symbol: str, date_text: str
) -> Path:
    name = config["storage"]["filename_template"].format(
        symbol=safe_token(symbol), date=date_text.replace("-", "")
    )
    return paths.root / safe_token(symbol) / name


def tick_to_row(
    tick: Any, config: dict[str, Any], login: int, server: str, symbol: str
) -> dict[str, Any]:
    authority = config["authority"]
    time_msc = int(tick["time_msc"])
    bid = float(tick["bid"])
    ask = float(tick["ask"])
    return {
        "schema_version": "capital_multisymbol_tick_v1",
        "timestamp_utc": utc_text_from_msc(time_msc),
        "tick_time_msc": time_msc,
        "run_id": config["run_id"],
        "account_login": login,
        "account_server": server,
        "symbol": symbol,
        "bid": format(bid, ".10g"),
        "ask": format(ask, ".10g"),
        "last": format(float(tick["last"]), ".10g"),
        "volume": int(tick["volume"]),
        "volume_real": format(float(tick["volume_real"]), ".10g"),
        "flags": int(tick["flags"]),
        "spread_price": format(ask - bid, ".10g"),
        "source": "MT5_COPY_TICKS_ALL_READ_ONLY",
        **{name: str(authority[name]).lower() for name in FORBIDDEN_TRUE_AUTHORITY},
    }


def append_rows(
    config: dict[str, Any],
    paths: RuntimePaths,
    symbol: str,
    rows: list[dict[str, Any]],
) -> int:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["timestamp_utc"][:10], []).append(row)
    written = 0
    for date_text, date_rows in sorted(grouped.items()):
        path = partition_path(config, paths, symbol, date_text)
        path.parent.mkdir(parents=True, exist_ok=True)
        new_file = not path.exists() or path.stat().st_size == 0
        with path.open("a", encoding="ascii", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
            if new_file:
                writer.writeheader()
            writer.writerows(date_rows)
            handle.flush()
            if config["collection"]["flush_and_fsync_each_chunk"]:
                os.fsync(handle.fileno())
        written += len(date_rows)
    return written


def connect(config: dict[str, Any], mt5: Any) -> tuple[int, str]:
    terminal = Path(config["account"]["terminal_exe"])
    if not terminal.exists():
        raise CollectorError(f"terminal does not exist: {terminal}")
    if not mt5.initialize(
        path=str(terminal), portable=bool(config["account"]["portable"])
    ):
        raise CollectorError(f"MetaTrader5 initialize failed: {mt5.last_error()}")
    account = mt5.account_info()
    terminal_info = mt5.terminal_info()
    if account is None or int(account.login) != int(
        config["account"]["expected_login"]
    ):
        raise CollectorError("connected account does not match locked login")
    if account.server != config["account"]["expected_server"]:
        raise CollectorError("connected account does not match locked server")
    if config["account"]["require_connected"] and (
        terminal_info is None or not bool(terminal_info.connected)
    ):
        raise CollectorError("terminal is not connected")
    for symbol in config["symbols"]:
        if config["collection"]["select_symbols_read_only"] and not mt5.symbol_select(
            symbol, True
        ):
            raise CollectorError(f"could not select read-only symbol {symbol}")
        info = mt5.symbol_info(symbol)
        if info is None or int(info.trade_mode) == 0:
            raise CollectorError(f"symbol unavailable: {symbol}")
    return int(account.login), str(account.server)


def preflight(config: dict[str, Any], mt5: Any) -> dict[str, Any]:
    login, server = connect(config, mt5)
    symbols = []
    for symbol in config["symbols"]:
        info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        symbols.append(
            {
                "symbol": symbol,
                "selected": bool(info.select),
                "visible": bool(info.visible),
                "trade_mode": int(info.trade_mode),
                "book_depth": int(info.ticks_bookdepth),
                "tick_available": tick is not None,
                "last_tick_msc": None if tick is None else int(tick.time_msc),
            }
        )
    return {
        "decision": "CAPITAL_MULTISYMBOL_V1_PREFLIGHT_PASS",
        "account_login": login,
        "account_server": server,
        "symbols": symbols,
        "authority": config["authority"],
    }


def collect_once(
    config: dict[str, Any],
    mt5: Any,
    now: datetime | None = None,
) -> dict[str, Any]:
    paths = runtime_paths(config)
    state = load_state(paths.state, config)
    login, server = connect(config, mt5)
    now_utc = (now or datetime.now(tz=UTC)).astimezone(UTC)
    boundary = parse_utc(config["information_boundary"]["start_inclusive_utc"])
    publication_lag_ms = int(config["collection"]["publication_lag_ms"])
    latest_msc = int(now_utc.timestamp() * 1000) - publication_lag_ms
    boundary_msc = int(boundary.timestamp() * 1000)
    result: dict[str, Any] = {
        "decision": "WAIT_BOUNDARY" if latest_msc < boundary_msc else "COLLECTED",
        "observed_at_utc": now_utc.isoformat().replace("+00:00", "Z"),
        "account_login": login,
        "account_server": server,
        "symbols": {},
        "authority": config["authority"],
    }
    if latest_msc < boundary_msc:
        atomic_json(paths.health, result)
        return result

    chunk_ms = int(config["collection"]["chunk_minutes"]) * 60_000
    max_rows = int(config["collection"]["maximum_rows_per_chunk"])
    for symbol in config["symbols"]:
        symbol_state = state["symbols"][symbol]
        start_msc = max(
            boundary_msc, int(symbol_state["scan_cursor_msc"]) + 1
        )
        symbol_written = 0
        chunk_count = 0
        while start_msc <= latest_msc:
            end_exclusive_msc = min(start_msc + chunk_ms, latest_msc + 1)
            start_utc = datetime.fromtimestamp(start_msc / 1000.0, tz=UTC)
            end_utc = datetime.fromtimestamp(end_exclusive_msc / 1000.0, tz=UTC)
            ticks = mt5.copy_ticks_range(
                symbol, start_utc, end_utc, mt5.COPY_TICKS_ALL
            )
            if ticks is None:
                raise CollectorError(
                    f"tick copy failed for {symbol}: {mt5.last_error()}"
                )
            selected = ticks[
                (ticks["time_msc"] >= start_msc)
                & (ticks["time_msc"] < end_exclusive_msc)
            ]
            if len(selected) > max_rows:
                raise CollectorError(
                    f"{symbol} chunk exceeded maximum rows: {len(selected)}"
                )
            rows = [
                tick_to_row(tick, config, login, server, symbol)
                for tick in selected
            ]
            symbol_written += append_rows(config, paths, symbol, rows)
            if len(selected):
                symbol_state["last_tick_msc"] = int(selected["time_msc"][-1])
            symbol_state["scan_cursor_msc"] = end_exclusive_msc - 1
            symbol_state["rows_written"] = int(symbol_state["rows_written"]) + len(
                selected
            )
            atomic_json(paths.state, state)
            start_msc = end_exclusive_msc
            chunk_count += 1
        result["symbols"][symbol] = {
            "rows_written_this_pass": symbol_written,
            "chunks_scanned": chunk_count,
            **symbol_state,
        }
    atomic_json(paths.health, result)
    return result


def contract_fingerprint(config_path: Path, source_paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(source_paths, key=lambda item: item.as_posix()):
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    digest.update(config_path.read_bytes())
    return digest.hexdigest()


def run_forever(config: dict[str, Any], mt5: Any) -> None:
    poll_seconds = float(config["collection"]["poll_seconds"])
    last_log_at = 0.0
    last_decision = ""
    try:
        while True:
            result = collect_once(config, mt5)
            now_monotonic = time.monotonic()
            rows_written = sum(
                int(details.get("rows_written_this_pass", 0))
                for details in result["symbols"].values()
            )
            if (
                rows_written
                or result["decision"] != last_decision
                or now_monotonic - last_log_at >= 60.0
            ):
                print(json.dumps(result, sort_keys=True), flush=True)
                last_log_at = now_monotonic
                last_decision = result["decision"]
            time.sleep(poll_seconds)
    finally:
        mt5.shutdown()
