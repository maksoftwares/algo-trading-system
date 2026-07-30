from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import forward_selective_learner as base

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = (
    ROOT / "config" / "frozen_forward_residual_mt5_shadow_bridge_v1.json"
)
LOCK_PATH = (
    ROOT
    / "EURUSD_FORWARD_RESIDUAL_MT5_SHADOW_BRIDGE_LOCK_2026_07_30.sha256.json"
)
QuoteProvider = Callable[[], dict[str, Any]]


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
        "locked_with_zero_live_signals": True,
        "locked_with_zero_mt5_receipts": True,
        "historical_backfill_allowed": False,
        "demo_order_authorized": False,
    }
    if any(lock.get(key) is not value for key, value in required.items()):
        raise RuntimeError("residual MT5 bridge lock boundary is incomplete")
    for relative, expected in lock["files"].items():
        if sha256(ROOT / relative) != expected:
            raise RuntimeError(f"residual MT5 bridge drift: {relative}")
    return lock


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("campaign_id") != "EURUSD_FORWARD_RESIDUAL_MT5_SHADOW_BRIDGE_V1":
        raise ValueError("unexpected residual MT5 bridge campaign")
    if config.get("demo_order_authorized"):
        raise ValueError("MT5 bridge config unexpectedly authorizes orders")
    return config


def load_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise TypeError(f"{path.name} is not a JSON list")
    return value


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("MT5 bridge timestamp lacks timezone")
    return parsed.astimezone(UTC)


def validate_signals(
    signals: list[dict[str, Any]],
    config: dict[str, Any],
) -> None:
    seen: set[str] = set()
    previous = ""
    for signal in signals:
        if signal.get("campaign_id") != config["publisher_campaign_id"]:
            raise ValueError("MT5 bridge signal campaign mismatch")
        decision_id = str(signal.get("decision_id", ""))
        if not decision_id or decision_id in seen:
            raise ValueError("missing or duplicate MT5 bridge decision id")
        if decision_id < previous:
            raise ValueError("MT5 bridge input ledger is not ordered")
        if signal.get("demo_order_authorized") is not False:
            raise ValueError("publisher signal unexpectedly authorizes orders")
        seen.add(decision_id)
        previous = decision_id


def validate_existing(
    receipts: list[dict[str, Any]],
    config: dict[str, Any],
) -> None:
    seen: set[str] = set()
    for receipt in receipts:
        if receipt.get("campaign_id") != config["campaign_id"]:
            raise ValueError("MT5 receipt campaign mismatch")
        decision_id = str(receipt.get("decision_id", ""))
        if not decision_id or decision_id in seen:
            raise ValueError("missing or duplicate MT5 receipt decision id")
        if receipt.get("demo_order_authorized") is not False:
            raise ValueError("MT5 receipt unexpectedly authorizes orders")
        seen.add(decision_id)


def _base_receipt(
    signal: dict[str, Any],
    now: datetime,
    config: dict[str, Any],
) -> dict[str, Any]:
    return {
        "receipt_id": f"{config['campaign_id']}|{signal['decision_id']}",
        "campaign_id": config["campaign_id"],
        "publisher_campaign_id": config["publisher_campaign_id"],
        "decision_id": signal["decision_id"],
        "decision_date": signal["decision_date"],
        "publisher_status": signal["status"],
        "published_at_utc": signal["published_at_utc"],
        "received_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "eligible_side": signal["eligible_side"],
        "regime": signal.get("regime"),
        "demo_order_authorized": False,
        "order_api_called": False,
        "position_mutation_attempted": False,
    }


def _validate_account_and_tick(
    quote: dict[str, Any],
    now: datetime,
    config: dict[str, Any],
) -> tuple[datetime, float, float, float]:
    if int(quote.get("account_login", -1)) != int(
        config["required_account_login"]
    ):
        raise ValueError("MT5 bridge account login mismatch")
    if str(quote.get("account_server", "")) != str(
        config["required_account_server"]
    ):
        raise ValueError("MT5 bridge account server mismatch")
    if int(quote.get("account_trade_mode", -1)) != int(
        config["required_account_trade_mode"]
    ):
        raise ValueError("MT5 bridge account is not the required demo mode")
    if str(quote.get("symbol", "")) != str(config["symbol"]):
        raise ValueError("MT5 bridge symbol mismatch")
    tick_time = parse_time(str(quote["tick_time_utc"]))
    age = (now - tick_time).total_seconds()
    if age < -1.0 or age > float(config["maximum_tick_age_seconds"]):
        raise ValueError(f"MT5 bridge tick is stale or future: age={age}")
    bid = float(quote["bid"])
    ask = float(quote["ask"])
    if bid <= 0.0 or ask <= bid:
        raise ValueError("MT5 bridge quote is invalid")
    spread_pips = (ask - bid) / float(config["pip_size"])
    return tick_time, bid, ask, spread_pips


def process(
    signals: list[dict[str, Any]],
    existing: list[dict[str, Any]],
    now: datetime,
    quote_provider: QuoteProvider,
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if now.tzinfo is None:
        raise ValueError("MT5 bridge clock must be timezone-aware")
    now = now.astimezone(UTC)
    validate_signals(signals, config)
    validate_existing(existing, config)
    existing_ids = {str(receipt["decision_id"]) for receipt in existing}
    updated = list(existing)
    for signal in signals:
        decision_id = str(signal["decision_id"])
        if decision_id in existing_ids:
            continue
        receipt = _base_receipt(signal, now, config)
        published = parse_time(str(signal["published_at_utc"]))
        floor = datetime.strptime(
            str(config["forward_floor_utc"]),
            base.TIME_FORMAT,
        ).replace(tzinfo=UTC)
        if published < floor:
            raise ValueError("MT5 bridge refused pre-floor signal")
        if signal.get("status") != config["eligible_publisher_status"]:
            receipt.update(
                {
                    "status": "CASH_MIRRORED",
                    "shadow_action": "NO_ENTRY",
                    "receipt_delay_seconds": (
                        now - published
                    ).total_seconds(),
                }
            )
        else:
            delay = (now - published).total_seconds()
            receipt["receipt_delay_seconds"] = delay
            if delay < 0.0 or delay > float(
                config["maximum_receipt_delay_seconds"]
            ):
                receipt.update(
                    {
                        "status": "CASH_LATE_RECEIPT",
                        "shadow_action": "NO_LATE_ENTRY",
                    }
                )
            else:
                quote = quote_provider()
                tick_time, bid, ask, spread_pips = _validate_account_and_tick(
                    quote,
                    now,
                    config,
                )
                if spread_pips > float(config["maximum_spread_pips"]):
                    receipt.update(
                        {
                            "status": "CASH_SPREAD_REJECTED",
                            "shadow_action": "NO_ENTRY",
                            "tick_time_utc": tick_time.strftime(
                                "%Y-%m-%dT%H:%M:%SZ"
                            ),
                            "bid": bid,
                            "ask": ask,
                            "spread_pips": spread_pips,
                        }
                    )
                else:
                    side = str(signal["eligible_side"])
                    if side not in ("LONG", "SHORT"):
                        raise ValueError("eligible publisher signal has no side")
                    pip = float(config["pip_size"])
                    entry = ask if side == "LONG" else bid
                    stop_distance = float(config["stop_pips"]) * pip
                    target_distance = float(config["target_pips"]) * pip
                    receipt.update(
                        {
                            "status": "SHADOW_ENTRY_CAPTURED",
                            "shadow_action": f"WOULD_ENTER_{side}",
                            "tick_time_utc": tick_time.strftime(
                                "%Y-%m-%dT%H:%M:%SZ"
                            ),
                            "bid": bid,
                            "ask": ask,
                            "spread_pips": spread_pips,
                            "lots": float(config["lots"]),
                            "entry": entry,
                            "stop": (
                                entry - stop_distance
                                if side == "LONG"
                                else entry + stop_distance
                            ),
                            "target": (
                                entry + target_distance
                                if side == "LONG"
                                else entry - target_distance
                            ),
                            "maximum_hold_minutes": int(
                                config["maximum_hold_minutes"]
                            ),
                        }
                    )
        updated.append(base.json_safe(receipt))
        existing_ids.add(decision_id)
    return updated, build_summary(signals, updated)


def build_summary(
    signals: list[dict[str, Any]],
    receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    captured = sum(
        receipt.get("status") == "SHADOW_ENTRY_CAPTURED"
        for receipt in receipts
    )
    return {
        "schema_version": "eurusd_forward_residual_mt5_shadow_bridge_summary_v1",
        "campaign_id": "EURUSD_FORWARD_RESIDUAL_MT5_SHADOW_BRIDGE_V1",
        "status": (
            "WAITING_SIGNALS"
            if not signals
            else "SHADOW_RECEIPTS_ACTIVE"
        ),
        "published_decisions": len(signals),
        "receipts": len(receipts),
        "shadow_entries_captured": captured,
        "cash_receipts": len(receipts) - captured,
        "pending_receipts": len(signals) - len(receipts),
        "order_api_calls": 0,
        "position_mutation_attempts": 0,
        "demo_order_authorized": False,
    }


def write_outputs(
    receipts: list[dict[str, Any]],
    summary: dict[str, Any],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = output_dir / "FORWARD_RESIDUAL_MT5_SHADOW_RECEIPTS.json"
    if receipt_path.is_file():
        existing = load_json_list(receipt_path)
        if len(receipts) < len(existing) or receipts[: len(existing)] != existing:
            raise ValueError("MT5 shadow receipt ledger mutation refused")
    base.atomic_write_text(
        receipt_path,
        json.dumps(receipts, indent=2, sort_keys=True) + "\n",
    )
    base.atomic_write_text(
        output_dir / "FORWARD_RESIDUAL_MT5_SHADOW_SUMMARY.json",
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
    )
    base.atomic_write_text(
        output_dir / "FORWARD_RESIDUAL_MT5_SHADOW_SUMMARY.md",
        "\n".join(
            [
                "# EURUSD residual MT5 shadow bridge",
                "",
                f"Status: **{summary['status']}**",
                "",
                f"- Published decisions: {summary['published_decisions']}",
                f"- Receipts: {summary['receipts']}",
                (
                    "- Shadow entries captured: "
                    f"{summary['shadow_entries_captured']}"
                ),
                f"- Cash receipts: {summary['cash_receipts']}",
                "- Order API calls: 0",
                "- Demo-order authorization: false",
                "",
            ]
        ),
    )
