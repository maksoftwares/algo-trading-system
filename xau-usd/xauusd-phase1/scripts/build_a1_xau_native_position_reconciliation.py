from __future__ import annotations

"""Deterministic native-position repair for the frozen A1 XAU R1+R2 ledger.

The historical ``*_trades.csv`` files were produced by pairing MT5 HTML deals
FIFO-by-direction.  This module does not repair those immutable files.  It resolves
each frozen baseline row to its recorded upstream row, takes only that row's entry
deal, and then joins the entry to the raw MT5 deal log by the native position
namespace.  Profit, exit time, exit deal, month, and router data are not admitted to
the identity join.

This is an identity/reconciliation layer, not the router audit classifier.  In
particular, raw historical deal logs do not contain ``DEAL_FEE``; the output exposes
that evidence gap instead of claiming full Commit-3 path validity.
"""

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
FROZEN_BASELINE = REPORTS_DIR / (
    "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_"
    "current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv"
)
FROZEN_BASELINE_SHA256 = "47cbe6a562ba2874d93a97255affbde613566ed06340a149ed2795d69a5dae52"
FROZEN_TRADE_COUNT = 678
FROZEN_LEGACY_EXIT_MISMATCH_COUNT = 388
FROZEN_LEGACY_PNL_MISMATCH_COUNT = 387
FROZEN_AGGREGATE_PNL = Decimal("9640.05")

INVALID_STATUS = "ROUTER_PATH_INVALID_EVIDENCE"
VALID_RECONCILIATION_STATUS = "NATIVE_POSITION_RECONCILIATION_VALID"

SOURCE_CONTROLS: tuple[tuple[str, int, Decimal, str], ...] = (
    ("h4_d1_long_best_box2_atr80", 145, Decimal("7050.42"), "LONG"),
    ("r1_h1_pullback_long_v1", 413, Decimal("1665.94"), "LONG"),
    ("r2_continuation_short_v1", 57, Decimal("589.46"), "SHORT"),
    ("r2_pullback_rejection_short_v1", 63, Decimal("334.23"), "SHORT"),
)

BASELINE_REQUIRED_FIELDS = {
    "component",
    "source_id",
    "direction",
    "entry_time",
    "exit_time",
    "pnl_usd",
    "source_csv",
    "source_row",
}
LEGACY_REQUIRED_FIELDS = {
    "entry_time",
    "direction",
    "entry_deal",
    "volume",
    "entry_price",
    "exit_time",
    "exit_deal",
    "exit_price",
    "profit_aed",
}
DEAL_REQUIRED_FIELDS = {
    "timestamp_broker",
    "run_id",
    "account",
    "symbol",
    "magic",
    "deal_ticket",
    "position_id",
    "entry_code",
    "direction",
    "volume",
    "price",
    "profit",
    "commission",
    "swap",
    "order_ticket",
    "reason_code",
}

# These are the only fields that select a native position.  Keeping the list public
# lets the audit verifier enforce the outcome-blind join boundary.
IDENTITY_JOIN_FIELDS: tuple[str, ...] = (
    "source_csv",
    "source_row",
    "entry_deal",
    "run_id",
    "account",
    "symbol",
    "magic",
    "position_id",
)
PROHIBITED_IDENTITY_JOIN_FIELDS: tuple[str, ...] = (
    "exit_time",
    "exit_deal",
    "profit_aed",
    "pnl_usd",
    "profit",
    "month",
    "router_state",
    "primary_class",
)

RECONCILIATION_FIELDNAMES: tuple[str, ...] = (
    "source_id",
    "component",
    "source_csv",
    "source_row",
    "trade_id",
    "direction",
    "baseline_entry_time",
    "baseline_exit_time",
    "baseline_pnl_usd",
    "legacy_entry_time",
    "legacy_entry_deal",
    "legacy_entry_price",
    "legacy_entry_volume",
    "legacy_entry_comment",
    "legacy_exit_time",
    "legacy_exit_deal",
    "legacy_exit_price",
    "legacy_exit_comment",
    "legacy_pnl_usd",
    "native_run_id",
    "native_account",
    "native_symbol",
    "native_magic",
    "native_position_id",
    "native_entry_time",
    "native_entry_deal",
    "native_entry_order",
    "native_entry_price",
    "native_entry_volume",
    "native_entry_comment",
    "native_exit_time",
    "native_exit_deal",
    "native_exit_order",
    "native_exit_price",
    "native_exit_volume",
    "native_exit_reason_code",
    "native_exit_comment",
    "native_deal_profit_usd",
    "native_commission_usd",
    "native_swap_usd",
    "native_fee_usd",
    "native_fee_evidence_complete",
    "native_pnl_usd",
    "native_deal_count",
    "native_entry_count",
    "native_exit_count",
    "entry_volume_equals_exit_volume",
    "legacy_exit_deal_mismatch",
    "legacy_pnl_mismatch",
    "evidence_status",
)


class NativePositionReconciliationError(ValueError):
    """Fail-closed evidence error; callers must not fall back to FIFO pairing."""

    status = INVALID_STATUS

    def __init__(self, message: str, *, context: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.context = dict(context or {})


@dataclass(frozen=True)
class ReconciliationResult:
    rows: tuple[dict[str, str], ...]
    summary: dict[str, Any]


@dataclass(frozen=True)
class _SourceEvidence:
    trades_path: Path
    deals_path: Path
    trade_rows: tuple[dict[str, str], ...]
    deals: tuple[dict[str, str], ...]
    deals_by_ticket: Mapping[str, tuple[dict[str, str], ...]]
    deals_by_position: Mapping[tuple[str, str, str, str, str], tuple[dict[str, str], ...]]
    fee_column_present: bool


@dataclass(frozen=True)
class _IdentityMapping:
    baseline: dict[str, str]
    legacy: dict[str, str]
    evidence: _SourceEvidence
    entry: dict[str, str]
    exit: dict[str, str]
    position_deals: tuple[dict[str, str], ...]
    trade_id: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fail(message: str, **context: Any) -> None:
    raise NativePositionReconciliationError(message, context=context)


def _read_delimited(path: Path) -> tuple[list[dict[str, str]], tuple[str, ...]]:
    if not path.is_file():
        _fail("required reconciliation source does not exist", path=str(path))
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        first_line = handle.readline()
        handle.seek(0)
        delimiter = "\t" if first_line.count("\t") > first_line.count(",") else ","
        reader = csv.DictReader(handle, delimiter=delimiter)
        if reader.fieldnames is None:
            _fail("source has no header", path=str(path))
        fieldnames = tuple(str(name).strip() for name in reader.fieldnames)
        rows = [
            {str(key).strip(): "" if value is None else str(value).strip() for key, value in row.items()}
            for row in reader
        ]
    return rows, fieldnames


def _require_fields(actual: Iterable[str], required: set[str], *, path: Path) -> None:
    missing = sorted(required - set(actual))
    if missing:
        _fail("source is missing required columns", path=str(path), missing=missing)


def _decimal(value: Any, *, field: str, context: str) -> Decimal:
    text = str(value).strip().replace(" ", "")
    if not text:
        _fail("empty decimal evidence", field=field, context=context)
    try:
        parsed = Decimal(text)
    except InvalidOperation:
        _fail("invalid decimal evidence", field=field, value=text, context=context)
    if not parsed.is_finite():
        _fail("nonfinite decimal evidence", field=field, value=text, context=context)
    return parsed


def _cent(value: Decimal, *, field: str, context: str) -> Decimal:
    cents = value.quantize(Decimal("0.01"))
    if cents != value:
        _fail("money evidence is not cent precise", field=field, value=str(value), context=context)
    return cents


def _money_text(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), ".2f")


def _timestamp(value: Any, *, field: str, context: str) -> datetime:
    text = str(value).strip()
    if not text:
        _fail("empty timestamp evidence", field=field, context=context)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    _fail("invalid timestamp evidence", field=field, value=text, context=context)


def _timestamp_text(value: Any, *, field: str, context: str) -> str:
    return _timestamp(value, field=field, context=context).strftime("%Y-%m-%d %H:%M:%S")


def _require_namespace_component(value: Any, *, field: str, context: str, numeric: bool = False) -> str:
    text = str(value).strip()
    if not text or "::" in text:
        _fail("invalid namespace component", field=field, value=text, context=context)
    if numeric and (not re.fullmatch(r"[0-9]+", text) or int(text) <= 0):
        _fail("native numeric identifier must be a positive integer", field=field, value=text, context=context)
    return text


def _entry_code(row: Mapping[str, str], *, context: str) -> int:
    text = str(row.get("entry_code", "")).strip()
    if text not in {"0", "1"}:
        _fail("position contains an unsupported entry code", entry_code=text, context=context)
    return int(text)


def _resolve_recorded_source(recorded: str, *, raw_root: Path | None) -> Path:
    recorded_path = Path(recorded)
    candidates: list[Path] = []

    def add(candidate: Path) -> None:
        if candidate.is_file():
            resolved = candidate.resolve()
            if resolved not in candidates:
                candidates.append(resolved)

    # An explicit raw root is an authority override for portable immutable evidence.
    if raw_root is not None:
        root = raw_root.resolve()
        lowered = [part.lower() for part in recorded_path.parts]
        try:
            marker = lowered.index("xau-usd")
        except ValueError:
            marker = -1
        if marker >= 0:
            suffix = Path(*recorded_path.parts[marker:])
            add(root / suffix)
            if root.name.lower() == "xauusd-phase1":
                add(root / Path(*recorded_path.parts[marker + 2 :]))
        add(root / recorded_path.name)
        for candidate in sorted(root.rglob(recorded_path.name), key=lambda item: str(item).lower()):
            add(candidate)
    else:
        add(recorded_path)
        lowered = [part.lower() for part in recorded_path.parts]
        try:
            marker = lowered.index("xauusd-phase1")
        except ValueError:
            marker = -1
        if marker >= 0:
            add(PHASE1_ROOT / Path(*recorded_path.parts[marker + 1 :]))

    if not candidates:
        _fail("recorded source_csv cannot be resolved", source_csv=recorded, raw_root=str(raw_root or ""))
    if len(candidates) != 1:
        _fail(
            "recorded source_csv resolution is ambiguous",
            source_csv=recorded,
            candidates=[str(path) for path in candidates],
        )
    return candidates[0]


def _deals_path_for(trades_path: Path) -> Path:
    suffix = "_trades.csv"
    if not trades_path.name.lower().endswith(suffix):
        _fail("upstream source filename is not a *_trades.csv artifact", path=str(trades_path))
    return trades_path.with_name(trades_path.name[: -len(suffix)] + "_deals.csv")


def _load_source_evidence(trades_path: Path) -> _SourceEvidence:
    trade_rows, trade_fields = _read_delimited(trades_path)
    _require_fields(trade_fields, LEGACY_REQUIRED_FIELDS, path=trades_path)
    deals_path = _deals_path_for(trades_path)
    deals, deal_fields = _read_delimited(deals_path)
    _require_fields(deal_fields, DEAL_REQUIRED_FIELDS, path=deals_path)
    if not deals:
        _fail("deal log is empty", path=str(deals_path))

    by_ticket: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    by_position: defaultdict[tuple[str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    full_deal_keys: set[tuple[str, str, str, str, str]] = set()
    for ordinal, deal in enumerate(deals, start=2):
        context = f"{deals_path}:{ordinal}"
        run_id = _require_namespace_component(deal["run_id"], field="run_id", context=context)
        account = _require_namespace_component(deal["account"], field="account", context=context, numeric=True)
        symbol = _require_namespace_component(deal["symbol"], field="symbol", context=context)
        magic = _require_namespace_component(deal["magic"], field="magic", context=context, numeric=True)
        ticket = _require_namespace_component(
            deal["deal_ticket"], field="deal_ticket", context=context, numeric=True
        )
        position_id = _require_namespace_component(
            deal["position_id"], field="position_id", context=context, numeric=True
        )
        _entry_code(deal, context=context)
        _timestamp(deal["timestamp_broker"], field="timestamp_broker", context=context)
        _decimal(deal["volume"], field="volume", context=context)
        full_deal_key = (run_id, account, symbol, magic, ticket)
        if full_deal_key in full_deal_keys:
            _fail("duplicate namespaced native deal", deal_key="::".join(full_deal_key), context=context)
        full_deal_keys.add(full_deal_key)
        by_ticket[ticket].append(deal)
        by_position[(run_id, account, symbol, magic, position_id)].append(deal)

    return _SourceEvidence(
        trades_path=trades_path,
        deals_path=deals_path,
        trade_rows=tuple(trade_rows),
        deals=tuple(deals),
        deals_by_ticket={key: tuple(value) for key, value in by_ticket.items()},
        deals_by_position={key: tuple(value) for key, value in by_position.items()},
        fee_column_present="fee" in set(deal_fields),
    )


def _source_row(evidence: _SourceEvidence, source_row: str) -> dict[str, str]:
    text = str(source_row).strip()
    if not re.fullmatch(r"[0-9]+", text):
        _fail("source_row is not an integer CSV line number", source_row=text, path=str(evidence.trades_path))
    line_number = int(text)
    index = line_number - 2
    if line_number < 2 or index >= len(evidence.trade_rows):
        _fail(
            "source_row is outside the upstream trade artifact",
            source_row=line_number,
            path=str(evidence.trades_path),
            data_rows=len(evidence.trade_rows),
        )
    return dict(evidence.trade_rows[index])


def _map_identity(
    baseline: dict[str, str],
    evidence: _SourceEvidence,
    *,
    baseline_ordinal: int,
) -> _IdentityMapping:
    context = f"baseline row {baseline_ordinal}"
    source_id = _require_namespace_component(baseline["source_id"], field="source_id", context=context)
    legacy = _source_row(evidence, baseline["source_row"])
    entry_ticket = _require_namespace_component(
        legacy["entry_deal"], field="entry_deal", context=context, numeric=True
    )

    # No exit or outcome field participates in these two selections.
    entry_candidates = evidence.deals_by_ticket.get(entry_ticket, ())
    if len(entry_candidates) != 1:
        _fail(
            "entry deal does not identify exactly one namespaced native deal",
            entry_deal=entry_ticket,
            candidate_count=len(entry_candidates),
            context=context,
        )
    entry = dict(entry_candidates[0])
    if _entry_code(entry, context=context) != 0:
        _fail("legacy entry_deal resolves to a non-entry native deal", entry_deal=entry_ticket, context=context)
    position_key = (
        entry["run_id"],
        entry["account"],
        entry["symbol"],
        entry["magic"],
        entry["position_id"],
    )
    position_deals = evidence.deals_by_position.get(position_key, ())
    entries = [dict(deal) for deal in position_deals if _entry_code(deal, context=context) == 0]
    exits = [dict(deal) for deal in position_deals if _entry_code(deal, context=context) == 1]
    if len(position_deals) != 2 or len(entries) != 1 or len(exits) != 1:
        _fail(
            "native position is not exactly one entry plus one exit",
            position_key="::".join(position_key),
            deal_count=len(position_deals),
            entry_count=len(entries),
            exit_count=len(exits),
            context=context,
        )
    native_entry = entries[0]
    native_exit = exits[0]
    if native_entry["deal_ticket"] != entry_ticket:
        _fail("resolved position entry is not the baseline entry deal", context=context)

    entry_volume = _decimal(native_entry["volume"], field="entry volume", context=context)
    exit_volume = _decimal(native_exit["volume"], field="exit volume", context=context)
    if entry_volume <= 0 or exit_volume <= 0 or entry_volume != exit_volume:
        _fail(
            "native position does not exit the full positive entry volume",
            entry_volume=str(entry_volume),
            exit_volume=str(exit_volume),
            context=context,
        )
    entry_time = _timestamp(native_entry["timestamp_broker"], field="native entry time", context=context)
    exit_time = _timestamp(native_exit["timestamp_broker"], field="native exit time", context=context)
    if exit_time <= entry_time:
        _fail("native position has a nonpositive holding interval", context=context)

    direction = str(baseline["direction"]).strip().upper()
    if direction not in {"LONG", "SHORT"}:
        _fail("baseline direction is invalid", direction=direction, context=context)
    if str(legacy["direction"]).strip().upper() != direction:
        _fail("baseline and upstream directions disagree", context=context)
    if any(str(deal["direction"]).strip().upper() != direction for deal in position_deals):
        _fail("native deal direction disagrees with the baseline", context=context)

    trade_id = "::".join((source_id, *position_key))
    if any(not part or "::" in part for part in (source_id, *position_key)):
        _fail("trade ID contains an invalid namespace component", trade_id=trade_id, context=context)

    return _IdentityMapping(
        baseline=dict(baseline),
        legacy=legacy,
        evidence=evidence,
        entry=native_entry,
        exit=native_exit,
        position_deals=tuple(dict(deal) for deal in position_deals),
        trade_id=trade_id,
    )


def _materialize(mapping: _IdentityMapping, *, baseline_ordinal: int) -> dict[str, str]:
    baseline = mapping.baseline
    legacy = mapping.legacy
    entry = mapping.entry
    exit_deal = mapping.exit
    context = f"baseline row {baseline_ordinal}"

    baseline_entry = _timestamp_text(baseline["entry_time"], field="baseline entry_time", context=context)
    baseline_exit = _timestamp_text(baseline["exit_time"], field="baseline exit_time", context=context)
    legacy_entry = _timestamp_text(legacy["entry_time"], field="legacy entry_time", context=context)
    legacy_exit = _timestamp_text(legacy["exit_time"], field="legacy exit_time", context=context)
    if baseline_entry != legacy_entry or baseline_exit != legacy_exit:
        _fail("baseline row does not reproduce its exact upstream timestamps", context=context)

    baseline_pnl = _cent(_decimal(baseline["pnl_usd"], field="pnl_usd", context=context), field="pnl_usd", context=context)
    legacy_pnl = _cent(
        _decimal(legacy["profit_aed"], field="profit_aed", context=context),
        field="profit_aed",
        context=context,
    )
    if baseline_pnl != legacy_pnl:
        _fail("baseline P/L does not equal the exact upstream legacy P/L", context=context)

    deal_profit = sum(
        (_decimal(deal["profit"], field="profit", context=context) for deal in mapping.position_deals),
        Decimal("0"),
    )
    commission = sum(
        (_decimal(deal["commission"], field="commission", context=context) for deal in mapping.position_deals),
        Decimal("0"),
    )
    swap = sum(
        (_decimal(deal["swap"], field="swap", context=context) for deal in mapping.position_deals),
        Decimal("0"),
    )
    fee: Decimal | None = None
    if mapping.evidence.fee_column_present:
        fee = sum(
            (_decimal(deal.get("fee", ""), field="fee", context=context) for deal in mapping.position_deals),
            Decimal("0"),
        )
    native_pnl = deal_profit + commission + swap + (fee or Decimal("0"))
    for field, value in (
        ("native deal profit", deal_profit),
        ("native commission", commission),
        ("native swap", swap),
        ("native P/L", native_pnl),
    ):
        _cent(value, field=field, context=context)
    if fee is not None:
        _cent(fee, field="native fee", context=context)

    native_exit_ticket = exit_deal["deal_ticket"]
    legacy_exit_ticket = str(legacy["exit_deal"]).strip()
    legacy_exit_mismatch = legacy_exit_ticket != native_exit_ticket
    legacy_pnl_mismatch = legacy_pnl != native_pnl

    row = {
        "source_id": baseline["source_id"],
        "component": baseline["component"],
        "source_csv": baseline["source_csv"],
        "source_row": baseline["source_row"],
        "trade_id": mapping.trade_id,
        "direction": str(baseline["direction"]).upper(),
        "baseline_entry_time": baseline["entry_time"],
        "baseline_exit_time": baseline["exit_time"],
        "baseline_pnl_usd": baseline["pnl_usd"],
        "legacy_entry_time": legacy["entry_time"],
        "legacy_entry_deal": legacy["entry_deal"],
        "legacy_entry_price": legacy["entry_price"],
        "legacy_entry_volume": legacy["volume"],
        "legacy_entry_comment": legacy.get("entry_comment", ""),
        "legacy_exit_time": legacy["exit_time"],
        "legacy_exit_deal": legacy["exit_deal"],
        "legacy_exit_price": legacy["exit_price"],
        "legacy_exit_comment": legacy.get("exit_comment", ""),
        "legacy_pnl_usd": legacy["profit_aed"],
        "native_run_id": entry["run_id"],
        "native_account": entry["account"],
        "native_symbol": entry["symbol"],
        "native_magic": entry["magic"],
        "native_position_id": entry["position_id"],
        "native_entry_time": entry["timestamp_broker"],
        "native_entry_deal": entry["deal_ticket"],
        "native_entry_order": entry["order_ticket"],
        "native_entry_price": entry["price"],
        "native_entry_volume": entry["volume"],
        "native_entry_comment": entry.get("comment", ""),
        "native_exit_time": exit_deal["timestamp_broker"],
        "native_exit_deal": native_exit_ticket,
        "native_exit_order": exit_deal["order_ticket"],
        "native_exit_price": exit_deal["price"],
        "native_exit_volume": exit_deal["volume"],
        "native_exit_reason_code": exit_deal["reason_code"],
        "native_exit_comment": exit_deal.get("comment", ""),
        "native_deal_profit_usd": _money_text(deal_profit),
        "native_commission_usd": _money_text(commission),
        "native_swap_usd": _money_text(swap),
        "native_fee_usd": "" if fee is None else _money_text(fee),
        "native_fee_evidence_complete": str(fee is not None).lower(),
        "native_pnl_usd": _money_text(native_pnl),
        "native_deal_count": str(len(mapping.position_deals)),
        "native_entry_count": "1",
        "native_exit_count": "1",
        "entry_volume_equals_exit_volume": "true",
        "legacy_exit_deal_mismatch": str(legacy_exit_mismatch).lower(),
        "legacy_pnl_mismatch": str(legacy_pnl_mismatch).lower(),
        "evidence_status": VALID_RECONCILIATION_STATUS,
    }
    missing = [field for field in RECONCILIATION_FIELDNAMES if field not in row]
    if missing:
        _fail("internal reconciliation schema error", missing=missing, context=context)
    return row


def _event_pnl_multiset(rows: Sequence[Mapping[str, str]], *, native: bool) -> Counter[tuple[str, ...]]:
    values: list[tuple[str, ...]] = []
    for row in rows:
        prefix = (
            row["source_id"],
            row["native_run_id"],
            row["native_account"],
            row["native_symbol"],
            row["native_magic"],
        )
        if native:
            event = (
                _timestamp_text(row["native_exit_time"], field="native_exit_time", context=row["trade_id"]),
                row["native_exit_deal"],
                _money_text(_decimal(row["native_pnl_usd"], field="native_pnl_usd", context=row["trade_id"])),
            )
        else:
            event = (
                _timestamp_text(row["legacy_exit_time"], field="legacy_exit_time", context=row["trade_id"]),
                row["legacy_exit_deal"],
                _money_text(_decimal(row["legacy_pnl_usd"], field="legacy_pnl_usd", context=row["trade_id"])),
            )
        values.append(prefix + event)
    return Counter(values)


def _summary(
    rows: Sequence[dict[str, str]],
    *,
    baseline_path: Path,
    baseline_sha256: str,
    enforce_frozen_controls: bool,
    source_evidence: Mapping[Path, _SourceEvidence],
) -> dict[str, Any]:
    counts = Counter(row["source_id"] for row in rows)
    pnl_by_source: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    directions_by_source: defaultdict[str, set[str]] = defaultdict(set)
    for row in rows:
        pnl_by_source[row["source_id"]] += _decimal(
            row["native_pnl_usd"], field="native_pnl_usd", context=row["trade_id"]
        )
        directions_by_source[row["source_id"]].add(row["direction"])

    expected_counts = {source_id: count for source_id, count, _pnl, _direction in SOURCE_CONTROLS}
    expected_pnl = {source_id: pnl for source_id, _count, pnl, _direction in SOURCE_CONTROLS}
    expected_directions = {source_id: direction for source_id, _count, _pnl, direction in SOURCE_CONTROLS}
    actual_pnl = {source_id: pnl_by_source[source_id] for source_id in sorted(pnl_by_source)}
    aggregate_pnl = sum(actual_pnl.values(), Decimal("0"))
    exit_mismatches = sum(row["legacy_exit_deal_mismatch"] == "true" for row in rows)
    pnl_mismatches = sum(row["legacy_pnl_mismatch"] == "true" for row in rows)
    trade_ids = [row["trade_id"] for row in rows]
    entry_keys = [
        (
            row["native_run_id"],
            row["native_account"],
            row["native_symbol"],
            row["native_magic"],
            row["native_entry_deal"],
        )
        for row in rows
    ]
    position_keys = [
        (
            row["native_run_id"],
            row["native_account"],
            row["native_symbol"],
            row["native_magic"],
            row["native_position_id"],
        )
        for row in rows
    ]

    internal_checks = {
        "unique_entry_to_position": len(set(entry_keys)) == len(rows) == len(set(position_keys)),
        "one_entry_one_exit": all(
            row["native_deal_count"] == "2"
            and row["native_entry_count"] == "1"
            and row["native_exit_count"] == "1"
            for row in rows
        ),
        "full_volume_exit": all(row["entry_volume_equals_exit_volume"] == "true" for row in rows),
        "unique_trade_ids": len(trade_ids) == len(set(trade_ids)) and all(trade_ids),
        "chronological_multiset_match": _event_pnl_multiset(rows, native=False)
        == _event_pnl_multiset(rows, native=True),
        "no_missing_ids_or_times": all(
            row[field]
            for row in rows
            for field in (
                "source_id",
                "trade_id",
                "baseline_entry_time",
                "baseline_exit_time",
                "native_entry_time",
                "native_exit_time",
                "native_entry_deal",
                "native_exit_deal",
                "native_position_id",
            )
        ),
    }
    if enforce_frozen_controls:
        frozen_checks = {
            "baseline_sha256": baseline_sha256 == FROZEN_BASELINE_SHA256,
            "trade_count_678": len(rows) == FROZEN_TRADE_COUNT,
            "legacy_exit_mismatch_388": exit_mismatches == FROZEN_LEGACY_EXIT_MISMATCH_COUNT,
            "legacy_pnl_mismatch_387": pnl_mismatches == FROZEN_LEGACY_PNL_MISMATCH_COUNT,
            "source_counts_match": dict(counts) == expected_counts,
            "source_pnl_match": all(pnl_by_source[source_id] == expected for source_id, expected in expected_pnl.items())
            and set(pnl_by_source) == set(expected_pnl),
            "aggregate_pnl_match": aggregate_pnl == FROZEN_AGGREGATE_PNL,
        }
    else:
        frozen_checks = {
            "baseline_sha256": True,
            "trade_count_678": True,
            "legacy_exit_mismatch_388": True,
            "legacy_pnl_mismatch_387": True,
            "source_counts_match": True,
            "source_pnl_match": True,
            "aggregate_pnl_match": True,
        }
    checks = {**frozen_checks, **internal_checks}
    all_valid = all(checks.values())
    if enforce_frozen_controls and not all_valid:
        failed = sorted(key for key, value in checks.items() if not value)
        _fail("frozen native-position reconciliation control failed", failed_checks=failed)

    source_summary = []
    all_source_ids = sorted(set(counts) | set(expected_counts))
    for source_id in all_source_ids:
        source_summary.append(
            {
                "source_id": source_id,
                "actual_count": counts.get(source_id, 0),
                "expected_count": expected_counts.get(source_id),
                "actual_pnl_usd": _money_text(pnl_by_source[source_id]),
                "expected_pnl_usd": (
                    _money_text(expected_pnl[source_id]) if source_id in expected_pnl else None
                ),
                "actual_directions": sorted(directions_by_source[source_id]),
                "expected_direction": expected_directions.get(source_id),
            }
        )

    raw_sources = []
    for path, evidence in sorted(source_evidence.items(), key=lambda item: str(item[0]).lower()):
        raw_sources.append(
            {
                "trades_path": str(path),
                "trades_sha256": sha256_file(path),
                "deals_path": str(evidence.deals_path),
                "deals_sha256": sha256_file(evidence.deals_path),
                "trade_rows": len(evidence.trade_rows),
                "deal_rows": len(evidence.deals),
                "fee_column_present": evidence.fee_column_present,
            }
        )

    return {
        "schema_version": "a1_xau_native_position_reconciliation_v1",
        "status": VALID_RECONCILIATION_STATUS if all_valid else INVALID_STATUS,
        "all_valid": all_valid,
        "contract_enforced": enforce_frozen_controls,
        "fifo_fallback_used": False,
        "classification_status_assigned": False,
        "identity_join_fields": list(IDENTITY_JOIN_FIELDS),
        "prohibited_identity_join_fields": list(PROHIBITED_IDENTITY_JOIN_FIELDS),
        "baseline_path": str(baseline_path),
        "baseline_sha256": baseline_sha256,
        "trade_count": len(rows),
        "unique_trade_id_count": len(set(trade_ids)),
        "unique_native_entry_count": len(set(entry_keys)),
        "unique_native_position_count": len(set(position_keys)),
        "legacy_exit_deal_mismatch_count": exit_mismatches,
        "legacy_pnl_mismatch_count": pnl_mismatches,
        "aggregate_native_pnl_usd": _money_text(aggregate_pnl),
        "fee_evidence_complete_for_all_rows": all(
            row["native_fee_evidence_complete"] == "true" for row in rows
        ),
        "checks": checks,
        "source_summary": source_summary,
        "raw_sources": raw_sources,
    }


def build_native_position_reconciliation(
    baseline_csv: Path = FROZEN_BASELINE,
    *,
    raw_root: Path | None = None,
    enforce_frozen_controls: bool = True,
) -> ReconciliationResult:
    """Build the outcome-blind native identity repair and exact controls.

    ``raw_root`` may point at an immutable evidence copy when the absolute
    ``source_csv`` values recorded in the frozen ledger no longer exist.  Ambiguous
    filename resolution fails closed.  ``enforce_frozen_controls=False`` exists only
    for small regression fixtures; production callers must retain the default.
    """

    baseline_path = Path(baseline_csv).resolve()
    baseline_sha = sha256_file(baseline_path)
    if enforce_frozen_controls and baseline_sha != FROZEN_BASELINE_SHA256:
        _fail(
            "frozen baseline SHA256 mismatch",
            expected=FROZEN_BASELINE_SHA256,
            actual=baseline_sha,
            path=str(baseline_path),
        )
    baseline_rows, baseline_fields = _read_delimited(baseline_path)
    _require_fields(baseline_fields, BASELINE_REQUIRED_FIELDS, path=baseline_path)
    if enforce_frozen_controls and len(baseline_rows) != FROZEN_TRADE_COUNT:
        _fail(
            "frozen baseline row count mismatch",
            expected=FROZEN_TRADE_COUNT,
            actual=len(baseline_rows),
        )

    source_cache: dict[Path, _SourceEvidence] = {}
    source_id_paths: defaultdict[str, set[Path]] = defaultdict(set)
    mapped: list[_IdentityMapping] = []
    source_row_owners: set[tuple[Path, str]] = set()
    entry_owners: set[tuple[str, str, str, str, str]] = set()
    position_owners: set[tuple[str, str, str, str, str]] = set()
    trade_ids: set[str] = set()

    # Pass 1 performs identity mapping only.  P/L and legacy exit values are not
    # inspected until every entry-deal-to-position mapping has been locked.
    for ordinal, baseline in enumerate(baseline_rows, start=2):
        path = _resolve_recorded_source(baseline["source_csv"], raw_root=raw_root)
        evidence = source_cache.get(path)
        if evidence is None:
            evidence = _load_source_evidence(path)
            source_cache[path] = evidence
        source_id_paths[baseline["source_id"]].add(path)
        row_owner = (path, baseline["source_row"])
        if row_owner in source_row_owners:
            _fail("two baseline rows own the same upstream source row", path=str(path), source_row=baseline["source_row"])
        source_row_owners.add(row_owner)
        identity = _map_identity(baseline, evidence, baseline_ordinal=ordinal)
        entry_key = (
            identity.entry["run_id"],
            identity.entry["account"],
            identity.entry["symbol"],
            identity.entry["magic"],
            identity.entry["deal_ticket"],
        )
        position_key = (
            identity.entry["run_id"],
            identity.entry["account"],
            identity.entry["symbol"],
            identity.entry["magic"],
            identity.entry["position_id"],
        )
        if entry_key in entry_owners:
            _fail("native entry deal has more than one baseline owner", entry_key="::".join(entry_key))
        if position_key in position_owners:
            _fail("native position has more than one baseline owner", position_key="::".join(position_key))
        if identity.trade_id in trade_ids:
            _fail("duplicate namespaced audit trade ID", trade_id=identity.trade_id)
        entry_owners.add(entry_key)
        position_owners.add(position_key)
        trade_ids.add(identity.trade_id)
        mapped.append(identity)

    ambiguous_source_ids = {
        source_id: sorted(str(path) for path in paths)
        for source_id, paths in source_id_paths.items()
        if len(paths) != 1
    }
    if ambiguous_source_ids:
        _fail("a source_id resolves to more than one upstream trade artifact", sources=ambiguous_source_ids)

    # Pass 2 opens legacy exits and monetary values only for reconciliation.
    rows = tuple(_materialize(identity, baseline_ordinal=ordinal) for ordinal, identity in enumerate(mapped, start=2))
    summary = _summary(
        rows,
        baseline_path=baseline_path,
        baseline_sha256=baseline_sha,
        enforce_frozen_controls=enforce_frozen_controls,
        source_evidence=source_cache,
    )
    return ReconciliationResult(rows=rows, summary=summary)


def write_reconciliation_csv(path: Path, rows: Sequence[Mapping[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RECONCILIATION_FIELDNAMES, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_reconciliation_summary(path: Path, summary: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=FROZEN_BASELINE)
    parser.add_argument("--raw-root", type=Path)
    parser.add_argument("--output-csv", type=Path)
    parser.add_argument("--summary-json", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = build_native_position_reconciliation(args.baseline, raw_root=args.raw_root)
    except NativePositionReconciliationError as exc:
        payload = {"status": exc.status, "error": str(exc), "context": exc.context}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2
    if args.output_csv:
        write_reconciliation_csv(args.output_csv, result.rows)
    if args.summary_json:
        write_reconciliation_summary(args.summary_json, result.summary)
    print(json.dumps(result.summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
