from __future__ import annotations

"""Build the frozen, outcome-sealed Router V1 exact-replay schedule.

The schedule is generated only after the byte-exact baseline and every frozen raw
artifact pass SHA256 verification.  Native entry identity selects a unique
``ORDER_SEND_OK`` row; that order's causal broker timestamp and direction select a
unique ``WOULD_SIGNAL`` row.  No profit, exit P/L, month, router class, or other
outcome field participates in either join.

Schedule bytes are locked before native P/L is read into a physically separate
sealed-outcomes CSV.  This module launches no terminal and assigns no router-audit
class or status.
"""

import argparse
import csv
import hashlib
import json
import shutil
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import build_a1_xau_native_position_reconciliation as native  # noqa: E402


PACKAGE_STEM = "A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710"
RUNTIME_SCHEDULE_NAME = f"{PACKAGE_STEM}_RUNTIME_SCHEDULE.csv"
SEALED_OUTCOMES_NAME = f"{PACKAGE_STEM}_SEALED_OUTCOMES.csv"
RECONCILIATION_NAME = f"{PACKAGE_STEM}_NATIVE_POSITION_RECONCILIATION.csv"
MANIFEST_NAME = f"{PACKAGE_STEM}_EVIDENCE_MANIFEST.json"

INVALID_STATUS = native.INVALID_STATUS
VALID_PACKAGE_STATUS = "ROUTER_ENTRY_HOLD_SCHEDULE_PACKAGE_VALID"

BASELINE_EXPECTED_SHA256 = native.FROZEN_BASELINE_SHA256
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


@dataclass(frozen=True)
class SourceArtifactContract:
    source_id: str
    component: str
    expected_regime: str
    expected_direction: str
    hashes: Mapping[str, str]


SOURCE_CONTRACTS: tuple[SourceArtifactContract, ...] = (
    SourceArtifactContract(
        source_id="h4_d1_long_best_box2_atr80",
        component="R1",
        expected_regime="UPTREND",
        expected_direction="LONG",
        hashes={
            "trades": "6ca00153146c3f62ae1acd20dc7b9bc640c5ffcdf258d0826a00f2fb694237b5",
            "orders": "e337af7d3e5698f623db5e428f9b987edc5f25c2138cad901a4e54ba6b58b44b",
            "deals": "dbfa77504f598421e55066bc7c23eac44ad3d93ce99cf165dcd8927682921cbb",
            "signals": "b53ee54afacfae9a5dceb74a2a16b8297b9aad1c3b582fdc2d77302d344afc3c",
            "management": EMPTY_SHA256,
            "html": "e1c9ccafb773aea77d67052e86d9ec883bb192694b4a1cea9c47cdbcafdf3605",
            "config": "3d52e33afb4d7ec323c6c540b21b9f516e06d446de2f55f2a8ba5d0b39441222",
        },
    ),
    SourceArtifactContract(
        source_id="r1_h1_pullback_long_v1",
        component="R1",
        expected_regime="UPTREND",
        expected_direction="LONG",
        hashes={
            "trades": "91976d2bd3d1a373eb95b5d43efe7a4cad848e64baca69e88db2fc2240312aa6",
            "orders": "8482016a012efcbb61470b8936815e0277234612d25e1bc2e084306f8338a749",
            "deals": "f02e02508af05a2c823c422b864df92bae544629a45073091107bdf83acb0fa1",
            "signals": "2ea28ff551bc1c1c071aa3ca1862447c10c483de70ffcc981797a2b403c355bd",
            "management": EMPTY_SHA256,
            "html": "9a64333a1fd240fcb8f2ddf7786ef1f63f22a2efea804d992e012c54faeb9e77",
            "config": "ce6218537800d4dc51705f32997d3b2ff29a8217fedc3fc7a091a7109991e5f6",
        },
    ),
    SourceArtifactContract(
        source_id="r2_continuation_short_v1",
        component="R2",
        expected_regime="DOWNTREND",
        expected_direction="SHORT",
        hashes={
            "trades": "171df13b53cd682e6de531f868fbb50dd03e94aaf0667c9685a1bf3755471798",
            "orders": "2284ce7a7847d6ecda755100d4e7e2bfb58eac42bf1829922ada58bb4b3e19d7",
            "deals": "075e44185c5cf02d8042fb289b902a73021d3602656d3b7ecb72e3e4ae3961b6",
            "signals": "f21b1182a991edfde99abe03b12b3cc04bf830c342962ba9121b2d3499fb961b",
            "management": EMPTY_SHA256,
            "html": "f16a1f4aaec5f0b3818ce52c0432e1ded23492e6cb3bd06b08f90b0942439596",
            "config": "97f6cdac7ef758c2ee0b2c836b67970ceea01e525639d8b751ef7d238127dbb7",
        },
    ),
    SourceArtifactContract(
        source_id="r2_pullback_rejection_short_v1",
        component="R2",
        expected_regime="DOWNTREND",
        expected_direction="SHORT",
        hashes={
            "trades": "3b37ab94c6543286268b98ce73ce491d3be4774c8337ea4a53e0f435f586b3bb",
            "orders": "893e617218c5b923545cbd6d571a035c6892b5b050a55013e7368f7642b66b66",
            "deals": "449db6f98db7a9bd54725b095dc785a490944eafab9da6edd7872e137d49c02d",
            "signals": "a9db4cc1f0461bb7ff6e14944ea5762da019ea959aec248a489731cacda0d49c",
            "management": EMPTY_SHA256,
            "html": "61762b770864a82f7cf91fdcc7e207735751e7d3a47c58a33c7b5620c6b0bb62",
            "config": "cd911b5220915e59e4465923d56bc568b380b36909a6e56fe41c27f9598a6c9a",
        },
    ),
)

SCHEDULE_FIELDNAMES: tuple[str, ...] = (
    "trade_id",
    "source_id",
    "component",
    "expected_regime",
    "direction",
    "signal_time_broker",
    "entry_time_broker",
    "exit_time_broker",
    "native_run_id",
    "native_account",
    "native_symbol",
    "native_magic",
    "native_position_id",
    "native_entry_order",
    "native_entry_deal",
    "native_exit_order",
    "native_exit_deal",
    "executed_volume",
    "actual_entry_price",
    "original_sl",
    "original_tp",
    "order_bid",
    "order_ask",
    "spread_points",
    "estimated_cost_r",
    "signal_reason",
    "native_exit_reason_code",
)

SEALED_OUTCOME_FIELDNAMES: tuple[str, ...] = ("trade_id", "native_final_pnl_usd")

FORBIDDEN_SCHEDULE_FIELDS: frozenset[str] = frozenset(
    {
        "native_final_pnl_usd",
        "final_pnl",
        "final_pnl_usd",
        "final_r",
        "profit",
        "profit_aed",
        "pnl_usd",
        "mfe",
        "mae",
        "unrealized_r",
        "post_change_r",
        "primary_class",
        "router_state",
        "drawdown_window",
    }
)

ORDER_REQUIRED_FIELDS = {
    "timestamp_broker",
    "run_id",
    "account",
    "symbol",
    "magic",
    "action",
    "direction",
    "lots",
    "bid",
    "ask",
    "spread_points",
    "sl",
    "tp",
    "estimated_cost_r",
    "order_ticket",
    "deal_ticket",
    "result_price",
}
SIGNAL_REQUIRED_FIELDS = {
    "timestamp_broker",
    "run_id",
    "account",
    "symbol",
    "magic",
    "stage",
    "direction",
    "reason",
    "bid",
    "ask",
    "spread_points",
    "estimated_cost_r",
}


class ScheduleEvidenceError(ValueError):
    status = INVALID_STATUS

    def __init__(self, message: str, *, context: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.context = dict(context or {})


@dataclass(frozen=True)
class SourceArtifacts:
    source_id: str
    paths: Mapping[str, Path]
    hashes: Mapping[str, str]


@dataclass(frozen=True)
class ScheduleBuildResult:
    schedule_rows: tuple[dict[str, str], ...]
    schedule_bytes: bytes
    schedule_sha256: str
    sealed_outcome_rows: tuple[dict[str, str], ...]
    sealed_outcome_bytes: bytes
    sealed_outcome_sha256: str
    reconciliation: native.ReconciliationResult
    source_artifacts: Mapping[str, SourceArtifacts]
    manifest: dict[str, Any]


def _fail(message: str, **context: Any) -> None:
    raise ScheduleEvidenceError(message, context=context)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return native.sha256_file(path)


def _read_rows(path: Path) -> tuple[list[dict[str, str]], tuple[str, ...]]:
    if not path.is_file():
        _fail("required schedule source is missing", path=str(path))
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        first = handle.readline()
        handle.seek(0)
        delimiter = "\t" if first.count("\t") > first.count(",") else ","
        reader = csv.DictReader(handle, delimiter=delimiter)
        if reader.fieldnames is None:
            _fail("schedule source has no header", path=str(path))
        fields = tuple(str(field).strip() for field in reader.fieldnames)
        rows = [
            {str(key).strip(): "" if value is None else str(value).strip() for key, value in row.items()}
            for row in reader
        ]
    return rows, fields


def _require_fields(fields: Iterable[str], required: set[str], *, path: Path) -> None:
    missing = sorted(required - set(fields))
    if missing:
        _fail("schedule source is missing required fields", path=str(path), missing=missing)


def _decimal(value: Any, *, field: str, context: str) -> Decimal:
    text = str(value).strip().replace(" ", "")
    if not text:
        _fail("empty decimal in schedule evidence", field=field, context=context)
    try:
        parsed = Decimal(text)
    except InvalidOperation:
        _fail("invalid decimal in schedule evidence", field=field, value=text, context=context)
    if not parsed.is_finite():
        _fail("nonfinite decimal in schedule evidence", field=field, value=text, context=context)
    return parsed


def _timestamp_text(value: Any, *, field: str, context: str) -> str:
    return native._timestamp_text(value, field=field, context=context)  # type: ignore[attr-defined]


def _broker_time(value: Any, *, field: str, context: str) -> str:
    normalized = _timestamp_text(value, field=field, context=context)
    return normalized[:10].replace("-", ".") + normalized[10:]


def _csv_bytes(fieldnames: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    import io

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=fieldnames,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _verify_hash(path: Path, expected: str, *, source_id: str, artifact_type: str) -> str:
    actual = _sha256_file(path)
    if actual != expected:
        _fail(
            "frozen artifact SHA256 mismatch",
            source_id=source_id,
            artifact_type=artifact_type,
            path=str(path),
            expected=expected,
            actual=actual,
        )
    return actual


def _base_artifact_paths(trades_path: Path) -> dict[str, Path]:
    suffix = "_trades.csv"
    if not trades_path.name.lower().endswith(suffix):
        _fail("native reconciliation trade path is not a *_trades.csv file", path=str(trades_path))
    stem = trades_path.name[: -len(suffix)]
    return {
        "trades": trades_path,
        "orders": trades_path.with_name(stem + "_orders.csv"),
        "deals": trades_path.with_name(stem + "_deals.csv"),
        "signals": trades_path.with_name(stem + "_signals.csv"),
        "management": trades_path.with_name(stem + "_management.csv"),
        "html": trades_path.with_name(stem + ".htm"),
    }


def _resolve_config(
    trades_path: Path,
    *,
    expected_hash: str,
    raw_root: Path,
    config_root: Path | None,
) -> Path:
    basename = trades_path.name[: -len("_trades.csv")] + ".ini"
    candidates: list[Path] = []

    def add(candidate: Path) -> None:
        if candidate.is_file():
            resolved = candidate.resolve()
            if resolved not in candidates and _sha256_file(resolved) == expected_hash:
                candidates.append(resolved)

    if config_root is not None:
        add(config_root / basename)
        if not candidates:
            for candidate in sorted(config_root.rglob(basename), key=lambda item: str(item).lower()):
                add(candidate)
    else:
        add(raw_root / "configs" / basename)
        if not candidates:
            for candidate in sorted(raw_root.rglob(basename), key=lambda item: str(item).lower()):
                add(candidate)
        summary_path = trades_path.with_name(trades_path.name[: -len("_trades.csv")] + "_summary.json")
        if summary_path.is_file():
            try:
                payload = json.loads(summary_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                _fail("cannot read tester config pointer", path=str(summary_path), error=str(exc))
            pointer = str(payload.get("tester_config") or "").strip()
            if pointer:
                add(Path(pointer))

    if not candidates:
        _fail(
            "frozen tester config cannot be resolved by exact hash",
            basename=basename,
            expected_hash=expected_hash,
            config_root=str(config_root or ""),
        )
    if len(candidates) != 1:
        _fail(
            "frozen tester config resolution is ambiguous",
            basename=basename,
            candidates=[str(path) for path in candidates],
        )
    return candidates[0]


def resolve_and_verify_source_artifacts(
    reconciliation: native.ReconciliationResult,
    *,
    raw_root: Path,
    config_root: Path | None = None,
    contracts: Sequence[SourceArtifactContract] = SOURCE_CONTRACTS,
) -> dict[str, SourceArtifacts]:
    contract_by_trade_hash = {contract.hashes["trades"]: contract for contract in contracts}
    if len(contract_by_trade_hash) != len(contracts):
        _fail("source artifact contract contains duplicate trade hashes")
    raw_records = reconciliation.summary.get("raw_sources")
    if not isinstance(raw_records, list):
        _fail("native reconciliation does not expose raw source provenance")

    resolved: dict[str, SourceArtifacts] = {}
    for record in raw_records:
        trade_hash = str(record.get("trades_sha256") or "")
        contract = contract_by_trade_hash.get(trade_hash)
        if contract is None:
            _fail("native reconciliation contains an uncontracted trade artifact", trades_sha256=trade_hash)
        if contract.source_id in resolved:
            _fail("source artifact resolves more than once", source_id=contract.source_id)
        trades_path = Path(str(record["trades_path"])).resolve()
        paths = _base_artifact_paths(trades_path)
        paths["config"] = _resolve_config(
            trades_path,
            expected_hash=contract.hashes["config"],
            raw_root=raw_root,
            config_root=config_root,
        )
        actual_hashes = {}
        for artifact_type, expected in contract.hashes.items():
            path = paths[artifact_type]
            actual_hashes[artifact_type] = _verify_hash(
                path,
                expected,
                source_id=contract.source_id,
                artifact_type=artifact_type,
            )
        resolved[contract.source_id] = SourceArtifacts(
            source_id=contract.source_id,
            paths=dict(paths),
            hashes=actual_hashes,
        )

    expected_ids = {contract.source_id for contract in contracts}
    if set(resolved) != expected_ids:
        _fail(
            "resolved source artifact set differs from the frozen contract",
            expected=sorted(expected_ids),
            actual=sorted(resolved),
        )
    return resolved


def _load_order_index(path: Path) -> tuple[dict[tuple[str, ...], dict[str, str]], int]:
    rows, fields = _read_rows(path)
    _require_fields(fields, ORDER_REQUIRED_FIELDS, path=path)
    index: dict[tuple[str, ...], dict[str, str]] = {}
    count = 0
    for ordinal, row in enumerate(rows, start=2):
        if row["action"] != "ORDER_SEND_OK":
            continue
        count += 1
        key = (row["run_id"], row["account"], row["symbol"], row["magic"], row["deal_ticket"])
        if any(not value for value in key):
            _fail("ORDER_SEND_OK has an empty native identity field", path=str(path), row=ordinal)
        if key in index:
            _fail("duplicate ORDER_SEND_OK native entry identity", path=str(path), key="::".join(key))
        index[key] = row
    return index, count


def _load_signal_index(path: Path) -> tuple[dict[tuple[str, ...], dict[str, str]], int]:
    index: dict[tuple[str, ...], dict[str, str]] = {}
    count = 0
    if not path.is_file():
        _fail("required schedule source is missing", path=str(path))
    # Signal artifacts are tens of millions of bytes.  Stream and retain only the
    # causal WOULD_SIGNAL rows so evidence size cannot change join behavior.
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        first = handle.readline()
        handle.seek(0)
        delimiter = "\t" if first.count("\t") > first.count(",") else ","
        reader = csv.DictReader(handle, delimiter=delimiter)
        if reader.fieldnames is None:
            _fail("schedule source has no header", path=str(path))
        fields = tuple(str(field).strip() for field in reader.fieldnames)
        _require_fields(fields, SIGNAL_REQUIRED_FIELDS, path=path)
        for ordinal, raw in enumerate(reader, start=2):
            row = {
                str(key).strip(): "" if value is None else str(value).strip()
                for key, value in raw.items()
            }
            if row["stage"] != "WOULD_SIGNAL":
                continue
            count += 1
            timestamp = _timestamp_text(
                row["timestamp_broker"], field="signal timestamp", context=f"{path}:{ordinal}"
            )
            key = (
                row["run_id"],
                row["account"],
                row["symbol"],
                row["magic"],
                timestamp,
                row["direction"],
            )
            if any(not value for value in key):
                _fail("WOULD_SIGNAL has an empty causal identity field", path=str(path), row=ordinal)
            if key in index:
                _fail("duplicate WOULD_SIGNAL causal identity", path=str(path), key="::".join(key))
            index[key] = row
    return index, count


def _same_decimal(left: Any, right: Any, *, left_field: str, right_field: str, context: str) -> None:
    if _decimal(left, field=left_field, context=context) != _decimal(right, field=right_field, context=context):
        _fail(
            "joined numeric evidence disagrees",
            left_field=left_field,
            left=str(left),
            right_field=right_field,
            right=str(right),
            context=context,
        )


def build_outcome_free_schedule(
    reconciliation: native.ReconciliationResult,
    source_artifacts: Mapping[str, SourceArtifacts],
    *,
    contracts: Sequence[SourceArtifactContract] = SOURCE_CONTRACTS,
) -> tuple[tuple[dict[str, str], ...], dict[str, Any]]:
    contract_by_id = {contract.source_id: contract for contract in contracts}
    order_indexes: dict[str, dict[tuple[str, ...], dict[str, str]]] = {}
    signal_indexes: dict[str, dict[tuple[str, ...], dict[str, str]]] = {}
    source_activity: dict[str, dict[str, int]] = {}
    for source_id in sorted(source_artifacts):
        artifacts = source_artifacts[source_id]
        order_index, order_count = _load_order_index(artifacts.paths["orders"])
        signal_index, signal_count = _load_signal_index(artifacts.paths["signals"])
        order_indexes[source_id] = order_index
        signal_indexes[source_id] = signal_index
        source_activity[source_id] = {
            "order_send_ok_rows": order_count,
            "would_signal_rows": signal_count,
        }

    schedule: list[dict[str, str]] = []
    owned_orders: set[tuple[str, ...]] = set()
    owned_signals: set[tuple[str, ...]] = set()
    for recon in reconciliation.rows:
        trade_id = recon["trade_id"]
        source_id = recon["source_id"]
        contract = contract_by_id.get(source_id)
        if contract is None or source_id not in source_artifacts:
            _fail("reconciled trade has no frozen source contract", trade_id=trade_id, source_id=source_id)
        if recon["direction"] != contract.expected_direction:
            _fail("reconciled direction violates frozen source mapping", trade_id=trade_id)

        order_key = (
            recon["native_run_id"],
            recon["native_account"],
            recon["native_symbol"],
            recon["native_magic"],
            recon["native_entry_deal"],
        )
        order = order_indexes[source_id].get(order_key)
        if order is None:
            _fail("native entry has no unique ORDER_SEND_OK", trade_id=trade_id, order_key="::".join(order_key))
        owned_order = (source_id, *order_key)
        if owned_order in owned_orders:
            _fail("ORDER_SEND_OK has more than one schedule owner", trade_id=trade_id)
        owned_orders.add(owned_order)

        if order["order_ticket"] != recon["native_entry_order"]:
            _fail("ORDER_SEND_OK order ticket disagrees with native entry", trade_id=trade_id)
        if order["direction"] != recon["direction"]:
            _fail("ORDER_SEND_OK direction disagrees with native entry", trade_id=trade_id)
        order_time = _timestamp_text(order["timestamp_broker"], field="order timestamp", context=trade_id)
        native_entry_time = _timestamp_text(recon["native_entry_time"], field="native entry time", context=trade_id)
        if order_time != native_entry_time:
            _fail("ORDER_SEND_OK time disagrees with native entry deal", trade_id=trade_id)
        _same_decimal(order["lots"], recon["native_entry_volume"], left_field="order lots", right_field="deal volume", context=trade_id)
        _same_decimal(
            order["result_price"],
            recon["native_entry_price"],
            left_field="ORDER_SEND_OK result_price",
            right_field="native entry price",
            context=trade_id,
        )
        if _decimal(order["sl"], field="original_sl", context=trade_id) <= 0:
            _fail("ORDER_SEND_OK original SL is nonpositive", trade_id=trade_id)
        if _decimal(order["tp"], field="original_tp", context=trade_id) <= 0:
            _fail("ORDER_SEND_OK original TP is nonpositive", trade_id=trade_id)

        signal_key = (
            order["run_id"],
            order["account"],
            order["symbol"],
            order["magic"],
            order_time,
            order["direction"],
        )
        signal = signal_indexes[source_id].get(signal_key)
        if signal is None:
            _fail("ORDER_SEND_OK has no unique causal WOULD_SIGNAL", trade_id=trade_id, signal_key="::".join(signal_key))
        owned_signal = (source_id, *signal_key)
        if owned_signal in owned_signals:
            _fail("WOULD_SIGNAL has more than one schedule owner", trade_id=trade_id)
        owned_signals.add(owned_signal)
        for field in ("bid", "ask", "spread_points", "estimated_cost_r"):
            _same_decimal(
                order[field],
                signal[field],
                left_field=f"order {field}",
                right_field=f"signal {field}",
                context=trade_id,
            )

        row = {
            "trade_id": trade_id,
            "source_id": source_id,
            "component": contract.component,
            "expected_regime": contract.expected_regime,
            "direction": recon["direction"],
            "signal_time_broker": _broker_time(
                signal["timestamp_broker"], field="signal timestamp", context=trade_id
            ),
            "entry_time_broker": _broker_time(
                native_entry_time, field="native entry time", context=trade_id
            ),
            "exit_time_broker": _broker_time(
                recon["native_exit_time"], field="native exit time", context=trade_id
            ),
            "native_run_id": recon["native_run_id"],
            "native_account": recon["native_account"],
            "native_symbol": recon["native_symbol"],
            "native_magic": recon["native_magic"],
            "native_position_id": recon["native_position_id"],
            "native_entry_order": recon["native_entry_order"],
            "native_entry_deal": recon["native_entry_deal"],
            "native_exit_order": recon["native_exit_order"],
            "native_exit_deal": recon["native_exit_deal"],
            "executed_volume": recon["native_entry_volume"],
            "actual_entry_price": recon["native_entry_price"],
            "original_sl": order["sl"],
            "original_tp": order["tp"],
            "order_bid": order["bid"],
            "order_ask": order["ask"],
            "spread_points": order["spread_points"],
            "estimated_cost_r": order["estimated_cost_r"],
            "signal_reason": signal["reason"],
            "native_exit_reason_code": recon["native_exit_reason_code"],
        }
        if tuple(row) != SCHEDULE_FIELDNAMES:
            _fail("internal runtime schedule schema drift", actual=list(row), expected=list(SCHEDULE_FIELDNAMES))
        schedule.append(row)

    schedule.sort(
        key=lambda row: (
            _timestamp_text(row["entry_time_broker"], field="entry_time_broker", context=row["trade_id"]),
            row["trade_id"],
        )
    )

    if len(schedule) != len(reconciliation.rows) or len(schedule) != native.FROZEN_TRADE_COUNT:
        _fail("runtime schedule does not contain exactly 678 reconciled trades", schedule_rows=len(schedule))
    if len({row["trade_id"] for row in schedule}) != len(schedule):
        _fail("runtime schedule trade IDs are not unique")
    entry_times = [
        _timestamp_text(row["entry_time_broker"], field="entry_time_broker", context=row["trade_id"])
        for row in schedule
    ]
    if any(current <= previous for previous, current in zip(entry_times, entry_times[1:])):
        _fail("runtime schedule entry times are not strictly increasing")
    signal_times = [
        _timestamp_text(row["signal_time_broker"], field="signal_time_broker", context=row["trade_id"])
        for row in schedule
    ]
    if any(current <= previous for previous, current in zip(signal_times, signal_times[1:])):
        _fail("runtime schedule signal times are not strictly increasing")
    if any(
        _timestamp_text(row["signal_time_broker"], field="signal_time_broker", context=row["trade_id"])
        > _timestamp_text(row["entry_time_broker"], field="entry_time_broker", context=row["trade_id"])
        for row in schedule
    ):
        _fail("runtime schedule contains signal_time after entry_time")
    if set(SCHEDULE_FIELDNAMES) & FORBIDDEN_SCHEDULE_FIELDS:
        _fail("runtime schedule schema admits a sealed outcome field")
    if any(field not in row or row[field] == "" for row in schedule for field in SCHEDULE_FIELDNAMES):
        _fail("runtime schedule contains an empty required field")
    join_summary = {
        "schedule_rows": len(schedule),
        "unique_order_owners": len(owned_orders),
        "unique_signal_owners": len(owned_signals),
        "all_native_entries_joined": len(owned_orders) == len(schedule),
        "all_orders_joined_to_would_signal": len(owned_signals) == len(schedule),
        "signal_and_entry_cursors_strictly_monotone": True,
        "join_fields_exclude_outcomes": True,
        "source_activity": source_activity,
    }
    return tuple(schedule), join_summary


def _sealed_outcomes_after_schedule_lock(
    reconciliation: native.ReconciliationResult,
    *,
    schedule_trade_ids: Sequence[str],
) -> tuple[dict[str, str], ...]:
    # This function is deliberately called only after schedule bytes and hash exist.
    outcome_by_id = {row["trade_id"]: row["native_pnl_usd"] for row in reconciliation.rows}
    if len(outcome_by_id) != len(reconciliation.rows):
        _fail("sealed outcome trade IDs are not unique")
    if set(outcome_by_id) != set(schedule_trade_ids):
        _fail("sealed outcome identities differ from the locked runtime schedule")
    return tuple(
        {"trade_id": trade_id, "native_final_pnl_usd": outcome_by_id[trade_id]}
        for trade_id in schedule_trade_ids
    )


def build_schedule_package(
    *,
    baseline_csv: Path,
    raw_root: Path,
    config_root: Path | None = None,
) -> ScheduleBuildResult:
    baseline_path = Path(baseline_csv).resolve()
    _verify_hash(
        baseline_path,
        BASELINE_EXPECTED_SHA256,
        source_id="__baseline__",
        artifact_type="baseline",
    )
    reconciliation = native.build_native_position_reconciliation(
        baseline_path,
        raw_root=Path(raw_root).resolve(),
        enforce_frozen_controls=True,
    )
    if not reconciliation.summary.get("all_valid"):
        _fail("native position reconciliation is not valid")
    source_artifacts = resolve_and_verify_source_artifacts(
        reconciliation,
        raw_root=Path(raw_root).resolve(),
        config_root=Path(config_root).resolve() if config_root else None,
    )
    schedule_rows, join_summary = build_outcome_free_schedule(reconciliation, source_artifacts)
    schedule_bytes = _csv_bytes(SCHEDULE_FIELDNAMES, schedule_rows)
    schedule_hash = _sha256_bytes(schedule_bytes)

    # Outcome unsealing begins only after the outcome-free schedule is serialized and
    # cryptographically locked.
    schedule_trade_ids = [row["trade_id"] for row in schedule_rows]
    sealed_rows = _sealed_outcomes_after_schedule_lock(
        reconciliation,
        schedule_trade_ids=schedule_trade_ids,
    )
    sealed_bytes = _csv_bytes(SEALED_OUTCOME_FIELDNAMES, sealed_rows)
    sealed_hash = _sha256_bytes(sealed_bytes)

    artifact_manifest = []
    for source_id in sorted(source_artifacts):
        artifacts = source_artifacts[source_id]
        for artifact_type in sorted(artifacts.paths):
            path = artifacts.paths[artifact_type]
            artifact_manifest.append(
                {
                    "source_id": source_id,
                    "artifact_type": artifact_type,
                    "source_path": str(path),
                    "sha256": artifacts.hashes[artifact_type],
                    "bytes": path.stat().st_size,
                }
            )
    manifest = {
        "schema_version": "a1_xau_router_entry_hold_schedule_manifest_v1",
        "status": VALID_PACKAGE_STATUS,
        "router_audit_result_assigned": False,
        "mt5_launched": False,
        "baseline": {
            "path": str(baseline_path),
            "sha256": BASELINE_EXPECTED_SHA256,
            "bytes": baseline_path.stat().st_size,
        },
        "native_reconciliation": {
            "all_valid": reconciliation.summary["all_valid"],
            "checks": reconciliation.summary["checks"],
            "trade_count": reconciliation.summary["trade_count"],
            "legacy_exit_deal_mismatch_count": reconciliation.summary["legacy_exit_deal_mismatch_count"],
            "legacy_pnl_mismatch_count": reconciliation.summary["legacy_pnl_mismatch_count"],
            "fee_evidence_complete_for_all_rows": reconciliation.summary["fee_evidence_complete_for_all_rows"],
        },
        "outcome_seal": {
            "schedule_built_and_locked_before_outcome_read": True,
            "schedule_fields": list(SCHEDULE_FIELDNAMES),
            "forbidden_schedule_fields": sorted(FORBIDDEN_SCHEDULE_FIELDS),
            "schedule_sha256": schedule_hash,
            "schedule_rows": len(schedule_rows),
            "sealed_outcome_fields": list(SEALED_OUTCOME_FIELDNAMES),
            "sealed_outcomes_sha256": sealed_hash,
            "sealed_outcome_rows": len(sealed_rows),
        },
        "join_checks": join_summary,
        "frozen_artifacts": artifact_manifest,
    }
    return ScheduleBuildResult(
        schedule_rows=schedule_rows,
        schedule_bytes=schedule_bytes,
        schedule_sha256=schedule_hash,
        sealed_outcome_rows=sealed_rows,
        sealed_outcome_bytes=sealed_bytes,
        sealed_outcome_sha256=sealed_hash,
        reconciliation=reconciliation,
        source_artifacts=source_artifacts,
        manifest=manifest,
    )


def _copy_immutable(source: Path, destination: Path, *, expected_sha256: str) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        actual = _sha256_file(destination)
        if actual != expected_sha256:
            _fail(
                "immutable evidence destination already exists with different bytes",
                destination=str(destination),
                expected=expected_sha256,
                actual=actual,
            )
    else:
        shutil.copyfile(source, destination)
    copied_hash = _sha256_file(destination)
    if copied_hash != expected_sha256:
        _fail("immutable evidence copy hash mismatch", destination=str(destination))
    return {
        "copied_path": str(destination),
        "sha256": copied_hash,
        "bytes": destination.stat().st_size,
    }


def write_schedule_package(result: ScheduleBuildResult, *, output_dir: Path) -> dict[str, Path]:
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    evidence_root = output / "immutable_evidence"
    copied_artifacts = []
    baseline_source = Path(result.manifest["baseline"]["path"])
    baseline_destination = evidence_root / "baseline" / baseline_source.name
    copied = _copy_immutable(
        baseline_source,
        baseline_destination,
        expected_sha256=BASELINE_EXPECTED_SHA256,
    )
    copied_artifacts.append(
        {"source_id": "__baseline__", "artifact_type": "baseline", **copied}
    )
    extension_names = {
        "trades": "trades.csv",
        "orders": "orders.csv",
        "deals": "deals.csv",
        "signals": "signals.csv",
        "management": "management.csv",
        "html": "report.htm",
        "config": "tester.ini",
    }
    for source_id in sorted(result.source_artifacts):
        artifacts = result.source_artifacts[source_id]
        for artifact_type in sorted(artifacts.paths):
            destination = evidence_root / source_id / extension_names[artifact_type]
            copied = _copy_immutable(
                artifacts.paths[artifact_type],
                destination,
                expected_sha256=artifacts.hashes[artifact_type],
            )
            copied_artifacts.append(
                {"source_id": source_id, "artifact_type": artifact_type, **copied}
            )

    schedule_path = output / RUNTIME_SCHEDULE_NAME
    outcomes_path = output / SEALED_OUTCOMES_NAME
    reconciliation_path = output / RECONCILIATION_NAME
    manifest_path = output / MANIFEST_NAME
    schedule_path.write_bytes(result.schedule_bytes)
    outcomes_path.write_bytes(result.sealed_outcome_bytes)
    native.write_reconciliation_csv(reconciliation_path, result.reconciliation.rows)
    manifest = dict(result.manifest)
    manifest["immutable_copies"] = copied_artifacts
    manifest["generated_outputs"] = {
        "runtime_schedule": {
            "path": str(schedule_path),
            "sha256": _sha256_file(schedule_path),
            "rows": len(result.schedule_rows),
        },
        "sealed_outcomes": {
            "path": str(outcomes_path),
            "sha256": _sha256_file(outcomes_path),
            "rows": len(result.sealed_outcome_rows),
        },
        "native_reconciliation": {
            "path": str(reconciliation_path),
            "sha256": _sha256_file(reconciliation_path),
            "rows": len(result.reconciliation.rows),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "runtime_schedule": schedule_path,
        "sealed_outcomes": outcomes_path,
        "native_reconciliation": reconciliation_path,
        "manifest": manifest_path,
        "immutable_evidence": evidence_root,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--config-root", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = build_schedule_package(
            baseline_csv=args.baseline,
            raw_root=args.raw_root,
            config_root=args.config_root,
        )
        outputs = write_schedule_package(result, output_dir=args.output_dir)
    except (ScheduleEvidenceError, native.NativePositionReconciliationError) as exc:
        payload = {
            "status": getattr(exc, "status", INVALID_STATUS),
            "error": str(exc),
            "context": getattr(exc, "context", {}),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2
    print(
        json.dumps(
            {
                "status": result.manifest["status"],
                "schedule_rows": len(result.schedule_rows),
                "schedule_sha256": result.schedule_sha256,
                "sealed_outcomes_sha256": result.sealed_outcome_sha256,
                "outputs": {key: str(value) for key, value in outputs.items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
