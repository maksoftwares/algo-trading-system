from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "capital_shared_account_forward_evaluator_v42.json"
AUTHORITY_FIELDS = (
    "trade_permission",
    "broker_action_allowed",
    "broker_action_authorized",
    "python_execution_authorized",
    "python_predictions_authorized",
    "ea_consumption_authorized",
    "demo_authorized",
    "live_authorized",
)
FINAL_STATUSES = frozenset(("EXECUTED", "REJECTED"))
DATE_PATTERN = re.compile(r"_ticks_(\d{8})\.csv$")

TRADE_COLUMNS = (
    "trade_id",
    "stage_date_utc",
    "specialist_id",
    "source_lane",
    "candidate_id",
    "origin_attempt",
    "direction",
    "direction_sign",
    "entry_time_utc",
    "exit_time_utc",
    "entry_time_msc",
    "exit_time_msc",
    "entry_price",
    "exit_price",
    "dollars_per_price_unit",
    "reference_lot",
    "risk_weight",
    "effective_lot",
    "base_cost_dollars",
    "stress_cost_dollars",
    "base_pnl_dollars",
    "stress_pnl_dollars",
    "broker_lot_exact",
)


class StageNotReady(RuntimeError):
    """A sealed stage exists, but its causal inputs are incomplete."""


@dataclass(frozen=True)
class JsonlSnapshot:
    rows: list[dict[str, Any]]
    payload: bytes
    bytes: int
    sha256: str


@dataclass(frozen=True)
class SourceBundle:
    v40_candidates: dict[str, list[dict[str, Any]]]
    v40_resolutions: dict[str, list[dict[str, Any]]]
    v41_candidates: list[dict[str, Any]]
    v41_resolutions: list[dict[str, Any]]
    v38_candidates: list[dict[str, Any]]
    v38_resolutions: list[dict[str, Any]]
    v39_routes: list[dict[str, Any]]
    seals: dict[str, dict[str, Any]]


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(payload: Mapping[str, Any], omitted_key: str) -> str:
    work = dict(payload)
    work.pop(omitted_key, None)
    encoded = json.dumps(
        work,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return sha256_bytes(encoded)


def utc_timestamp(value: Any) -> pd.Timestamp:
    result = pd.Timestamp(value)
    if result.tzinfo is None:
        raise ValueError(f"V42 timezone-naive timestamp: {value}")
    return result.tz_convert("UTC")


def utc_text(value: Any) -> str:
    return utc_timestamp(value).isoformat().replace("+00:00", "Z")


def _repo_path(relative: str, repo_root: Path = REPO_ROOT) -> Path:
    root = repo_root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"V42 path escaped repository: {relative}") from exc
    return path


def verify_source_contracts(
    config: Mapping[str, Any], repo_root: Path = REPO_ROOT
) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for name in ("v27", "v40", "v41", "v38", "v39"):
        source = config["sources"][name]
        path = _repo_path(str(source["contract_path"]), repo_root)
        actual_file_hash = sha256_file(path)
        if actual_file_hash != str(source["contract_file_sha256"]):
            raise ValueError(f"V42 {name} contract file changed")
        contract = json.loads(path.read_text(encoding="utf-8"))
        if str(contract.get("contract_sha256")) != str(source["contract_sha256"]):
            raise ValueError(f"V42 {name} contract identity changed")
        records[name] = {
            "path": path.relative_to(repo_root.resolve()).as_posix(),
            "bytes": int(path.stat().st_size),
            "sha256": actual_file_hash,
            "contract_sha256": str(contract["contract_sha256"]),
        }
    return records


def stable_jsonl_snapshot(
    path: Path, *, schema_version: str | None = None
) -> JsonlSnapshot:
    if not path.exists():
        return JsonlSnapshot([], b"", 0, sha256_bytes(b""))
    payload = path.read_bytes()
    if payload and not payload.endswith(b"\n"):
        last = payload.rfind(b"\n")
        payload = b"" if last < 0 else payload[: last + 1]
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(payload.splitlines(), start=1):
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"V42 invalid JSONL {path}:{line_number}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"V42 non-object JSONL {path}:{line_number}")
        if (
            schema_version is not None
            and str(row.get("schema_version")) != schema_version
        ):
            raise ValueError(f"V42 schema changed in {path}:{line_number}")
        rows.append(row)
    ids = [str(row.get("candidate_id")) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"V42 duplicate candidate ID in {path}")
    return JsonlSnapshot(rows, payload, len(payload), sha256_bytes(payload))


def _validate_authority(row: Mapping[str, Any], label: str) -> None:
    for field in AUTHORITY_FIELDS:
        if field in row and bool(row[field]):
            raise ValueError(f"V42 {label} enables {field}")


def _validate_status(
    path: Path,
    *,
    expected_contract: str,
    expected_status: str,
    label: str,
) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"V42 {label} status is absent")
    status = json.loads(path.read_text(encoding="utf-8"))
    if str(status.get("contract_sha256")) != expected_contract:
        raise ValueError(f"V42 {label} status contract changed")
    if str(status.get("status")) != expected_status:
        raise ValueError(f"V42 {label} is not active")
    _validate_authority(status, f"{label} status")
    if bool(status.get("aggregate_economics_opened", True)):
        raise ValueError(f"V42 {label} opened aggregate economics")
    return status


def _validate_candidates(rows: Sequence[Mapping[str, Any]], label: str) -> None:
    for row in rows:
        candidate_id = str(row.get("candidate_id", ""))
        if not candidate_id:
            raise ValueError(f"V42 {label} candidate lacks ID")
        _validate_authority(row, f"{label} candidate")


def _validate_resolutions(
    rows: Sequence[Mapping[str, Any]],
    candidates: Sequence[Mapping[str, Any]],
    *,
    schema_version: str,
    label: str,
) -> None:
    by_id = {str(row["candidate_id"]): row for row in candidates}
    for row in rows:
        if str(row.get("schema_version")) != schema_version:
            raise ValueError(f"V42 {label} resolution schema changed")
        candidate_id = str(row.get("candidate_id", ""))
        if candidate_id not in by_id:
            raise ValueError(f"V42 {label} resolution has unknown candidate")
        if str(row.get("resolution_status")) not in FINAL_STATUSES:
            raise ValueError(f"V42 {label} resolution status changed")
        if "candidate_fact_sha256" in row:
            candidate_hash = canonical_hash(by_id[candidate_id], "__absent__")
            if str(row["candidate_fact_sha256"]) != candidate_hash:
                raise ValueError(f"V42 {label} candidate fact mismatch")
        _validate_authority(row, f"{label} resolution")
        if str(row["resolution_status"]) == "EXECUTED":
            for field in (
                "entry_time_utc",
                "exit_time_utc",
                "entry_price",
                "exit_price",
                "risk_usd",
                "gross_r",
                "stress_net_r",
            ):
                if field not in row or row[field] is None:
                    raise ValueError(f"V42 {label} executed outcome lacks {field}")
            entry = utc_timestamp(row["entry_time_utc"])
            exit_time = utc_timestamp(row["exit_time_utc"])
            if exit_time < entry:
                raise ValueError(f"V42 {label} exit precedes entry")
            values = np.asarray(
                [
                    row["entry_price"],
                    row["exit_price"],
                    row["risk_usd"],
                    row["gross_r"],
                    row["stress_net_r"],
                ],
                dtype=float,
            )
            if not np.isfinite(values).all() or float(row["risk_usd"]) <= 0.0:
                raise ValueError(f"V42 {label} has invalid economics")


def _seal(name: str, snapshot: JsonlSnapshot) -> dict[str, Any]:
    return {
        "name": name,
        "bytes": snapshot.bytes,
        "sha256": snapshot.sha256,
        "rows": len(snapshot.rows),
    }


def _verify_consumed_prefix(
    snapshot: JsonlSnapshot,
    state_path: Path,
    *,
    bytes_field: str,
    sha_field: str,
    expected_contract: str,
    label: str,
) -> None:
    if not state_path.is_file():
        raise FileNotFoundError(f"V42 {label} prefix state is absent")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if str(state.get("contract_sha256")) != expected_contract:
        raise ValueError(f"V42 {label} prefix contract changed")
    consumed_bytes = int(state.get(bytes_field, -1))
    if consumed_bytes < 0 or snapshot.bytes < consumed_bytes:
        raise ValueError(f"V42 {label} prefix was truncated")
    consumed_sha = sha256_bytes(snapshot.payload[:consumed_bytes])
    if consumed_sha != str(state.get(sha_field, "")):
        raise ValueError(f"V42 {label} consumed prefix was mutated")


def load_source_bundle(config: Mapping[str, Any]) -> SourceBundle:
    sources = config["sources"]
    verify_source_contracts(config)
    seals: dict[str, dict[str, Any]] = {}

    v40 = sources["v40"]
    v40_runtime = Path(v40["runtime_directory"])
    v40_status = _validate_status(
        v40_runtime / v40["status"],
        expected_contract=str(v40["contract_sha256"]),
        expected_status="ACTIVE_READ_ONLY_CAUSAL_RESOLVER",
        label="V40",
    )
    v40_candidates: dict[str, list[dict[str, Any]]] = {}
    v40_resolutions: dict[str, list[dict[str, Any]]] = {}
    for stream, source in v40["candidate_sources"].items():
        candidate_snapshot = stable_jsonl_snapshot(
            Path(source["directory"]) / source["filename"]
        )
        resolution_snapshot = stable_jsonl_snapshot(
            v40_runtime / str(v40["resolution_pattern"]).format(stream=stream),
            schema_version="xauusd_capital_core_candidate_resolution_v40",
        )
        state_path = v40_runtime / str(v40["prefix_state_pattern"]).format(
            stream=stream
        )
        _verify_consumed_prefix(
            candidate_snapshot,
            state_path,
            bytes_field="source_prefix_bytes",
            sha_field="source_prefix_sha256",
            expected_contract=str(v40["contract_sha256"]),
            label=f"V40 {stream} candidate",
        )
        _verify_consumed_prefix(
            resolution_snapshot,
            state_path,
            bytes_field="resolution_prefix_bytes",
            sha_field="resolution_prefix_sha256",
            expected_contract=str(v40["contract_sha256"]),
            label=f"V40 {stream} resolution",
        )
        _validate_candidates(candidate_snapshot.rows, f"V40 {stream}")
        _validate_resolutions(
            resolution_snapshot.rows,
            candidate_snapshot.rows,
            schema_version="xauusd_capital_core_candidate_resolution_v40",
            label=f"V40 {stream}",
        )
        status_count = int(v40_status["streams"][stream]["candidate_rows"])
        if len(candidate_snapshot.rows) < status_count:
            raise ValueError(f"V42 V40 {stream} candidate snapshot trails status")
        v40_candidates[stream] = candidate_snapshot.rows
        v40_resolutions[stream] = resolution_snapshot.rows
        seals[f"v40_{stream}_candidates"] = _seal(
            f"v40_{stream}_candidates", candidate_snapshot
        )
        seals[f"v40_{stream}_resolutions"] = _seal(
            f"v40_{stream}_resolutions", resolution_snapshot
        )

    v41 = sources["v41"]
    v41_status = _validate_status(
        Path(v41["runtime_directory"]) / v41["status"],
        expected_contract=str(v41["contract_sha256"]),
        expected_status="ACTIVE_READ_ONLY_CAUSAL_RESOLVER",
        label="V41",
    )
    v41_candidates_snapshot = stable_jsonl_snapshot(
        Path(v41["candidate_directory"]) / v41["candidate_filename"]
    )
    v41_resolutions_snapshot = stable_jsonl_snapshot(
        Path(v41["runtime_directory"]) / v41["resolution_filename"],
        schema_version="xauusd_capital_r1_box_candidate_resolution_v41",
    )
    v41_state = Path(v41["runtime_directory"]) / v41["prefix_state"]
    _verify_consumed_prefix(
        v41_candidates_snapshot,
        v41_state,
        bytes_field="source_prefix_bytes",
        sha_field="source_prefix_sha256",
        expected_contract=str(v41["contract_sha256"]),
        label="V41 candidate",
    )
    _verify_consumed_prefix(
        v41_resolutions_snapshot,
        v41_state,
        bytes_field="resolution_prefix_bytes",
        sha_field="resolution_prefix_sha256",
        expected_contract=str(v41["contract_sha256"]),
        label="V41 resolution",
    )
    _validate_candidates(v41_candidates_snapshot.rows, "V41")
    _validate_resolutions(
        v41_resolutions_snapshot.rows,
        v41_candidates_snapshot.rows,
        schema_version="xauusd_capital_r1_box_candidate_resolution_v41",
        label="V41",
    )
    if len(v41_candidates_snapshot.rows) < int(v41_status["candidate_rows"]):
        raise ValueError("V42 V41 candidate snapshot trails status")
    seals["v41_candidates"] = _seal("v41_candidates", v41_candidates_snapshot)
    seals["v41_resolutions"] = _seal("v41_resolutions", v41_resolutions_snapshot)

    v38 = sources["v38"]
    v38_status = _validate_status(
        Path(v38["runtime_directory"]) / v38["status"],
        expected_contract=str(v38["contract_sha256"]),
        expected_status="ACTIVE_READ_ONLY_CAUSAL_RESOLVER",
        label="V38",
    )
    v38_candidates_snapshot = stable_jsonl_snapshot(
        Path(v38["candidate_directory"]) / v38["candidate_filename"]
    )
    v38_resolutions_snapshot = stable_jsonl_snapshot(
        Path(v38["runtime_directory"]) / v38["resolution_filename"],
        schema_version="xauusd_capital_r5_component_resolution_v38",
    )
    v38_state = Path(v38["runtime_directory"]) / v38["prefix_state"]
    _verify_consumed_prefix(
        v38_candidates_snapshot,
        v38_state,
        bytes_field="source_prefix_bytes",
        sha_field="source_prefix_sha256",
        expected_contract=str(v38["contract_sha256"]),
        label="V38 candidate",
    )
    _verify_consumed_prefix(
        v38_resolutions_snapshot,
        v38_state,
        bytes_field="resolution_prefix_bytes",
        sha_field="resolution_prefix_sha256",
        expected_contract=str(v38["contract_sha256"]),
        label="V38 resolution",
    )
    _validate_candidates(v38_candidates_snapshot.rows, "V38")
    _validate_resolutions(
        v38_resolutions_snapshot.rows,
        v38_candidates_snapshot.rows,
        schema_version="xauusd_capital_r5_component_resolution_v38",
        label="V38",
    )
    if len(v38_candidates_snapshot.rows) < int(v38_status["candidate_rows"]):
        raise ValueError("V42 V38 candidate snapshot trails status")
    seals["v38_candidates"] = _seal("v38_candidates", v38_candidates_snapshot)
    seals["v38_resolutions"] = _seal("v38_resolutions", v38_resolutions_snapshot)

    v39 = sources["v39"]
    v39_status = _validate_status(
        Path(v39["runtime_directory"]) / v39["status"],
        expected_contract=str(v39["contract_sha256"]),
        expected_status="ACTIVE_READ_ONLY_CAUSAL_ROUTER",
        label="V39",
    )
    if not bool(v39_status.get("v38_synchronized")):
        raise ValueError("V42 V39 is not synchronized with V38")
    routes_snapshot = stable_jsonl_snapshot(
        Path(v39["runtime_directory"]) / v39["route_filename"],
        schema_version="xauusd_capital_r5_causal_route_v39",
    )
    _verify_consumed_prefix(
        routes_snapshot,
        Path(v39["runtime_directory"]) / v39["prefix_state"],
        bytes_field="route_prefix_bytes",
        sha_field="route_prefix_sha256",
        expected_contract=str(v39["contract_sha256"]),
        label="V39 route",
    )
    candidate_ids = {str(row["candidate_id"]) for row in v38_candidates_snapshot.rows}
    for route in routes_snapshot.rows:
        if str(route["candidate_id"]) not in candidate_ids:
            raise ValueError("V42 V39 route has unknown candidate")
        _validate_authority(route, "V39 route")
        values = np.asarray(
            [
                route.get("route_multiplier"),
                route.get("base_weight"),
                route.get("risk_weight"),
            ],
            dtype=float,
        )
        if not np.isfinite(values).all() or float(route["risk_weight"]) < 0.0:
            raise ValueError("V42 V39 route has invalid risk weight")
    if len(routes_snapshot.rows) < int(v39_status["routed_candidate_rows"]):
        raise ValueError("V42 V39 route snapshot trails status")
    seals["v39_routes"] = _seal("v39_routes", routes_snapshot)

    return SourceBundle(
        v40_candidates,
        v40_resolutions,
        v41_candidates_snapshot.rows,
        v41_resolutions_snapshot.rows,
        v38_candidates_snapshot.rows,
        v38_resolutions_snapshot.rows,
        routes_snapshot.rows,
        seals,
    )


def _candidate_date(row: Mapping[str, Any], field: str) -> str:
    return utc_timestamp(row[field]).strftime("%Y-%m-%d")


def _require_stage_resolutions(
    candidates: Sequence[Mapping[str, Any]],
    resolutions: Sequence[Mapping[str, Any]],
    dates: set[str],
    time_field: str,
    label: str,
    routes: Sequence[Mapping[str, Any]] | None = None,
) -> None:
    required = {
        str(row["candidate_id"])
        for row in candidates
        if _candidate_date(row, time_field) in dates
    }
    resolved = {str(row["candidate_id"]) for row in resolutions}
    if missing := sorted(required.difference(resolved)):
        raise StageNotReady(f"{label} has {len(missing)} unresolved stage candidates")
    if routes is not None:
        routed = {str(row["candidate_id"]) for row in routes}
        if missing := sorted(required.difference(routed)):
            raise StageNotReady(f"{label} has {len(missing)} unrouted stage candidates")


def _direction_sign(candidate: Mapping[str, Any]) -> int:
    if "direction_sign" in candidate:
        value = int(candidate["direction_sign"])
    else:
        value = 1 if str(candidate.get("direction", "")).upper() == "LONG" else -1
    if value not in (-1, 1):
        raise ValueError("V42 invalid direction")
    return value


def _broker_lot_exact(lot: float, account: Mapping[str, Any]) -> bool:
    minimum = float(account["minimum_lot"])
    step = float(account["lot_step"])
    if lot + 1e-12 < minimum:
        return False
    steps = round((lot - minimum) / step)
    return abs(lot - (minimum + steps * step)) <= 1e-10


def _core_trade(
    candidate: Mapping[str, Any],
    resolution: Mapping[str, Any],
    *,
    specialist_id: str,
    source_lane: str,
    stage_time_field: str,
    config: Mapping[str, Any],
    risk_weight: float = 1.0,
) -> dict[str, Any]:
    portfolio = config["portfolio"]
    account = config["account_reference"]
    sign = _direction_sign(candidate)
    risk_usd = float(resolution["risk_usd"])
    gross_r = float(resolution["gross_r"])
    stress_r = float(resolution["stress_net_r"])
    base_r = stress_r + float(portfolio["core_stress_slippage_r"])
    base_pnl = base_r * risk_usd * risk_weight
    stress_pnl = stress_r * risk_usd * risk_weight
    gross_pnl = gross_r * risk_usd * risk_weight
    lot = float(portfolio["reference_lot"]) * risk_weight
    entry = utc_timestamp(resolution["entry_time_utc"])
    exit_time = utc_timestamp(resolution["exit_time_utc"])
    candidate_id = str(candidate["candidate_id"])
    return {
        "trade_id": sha256_bytes(f"{source_lane}|{candidate_id}".encode("ascii"))[:24],
        "stage_date_utc": _candidate_date(candidate, stage_time_field),
        "specialist_id": specialist_id,
        "source_lane": source_lane,
        "candidate_id": candidate_id,
        "origin_attempt": int(
            candidate.get("origin_attempt", resolution.get("origin_attempt", -1))
        ),
        "direction": "LONG" if sign > 0 else "SHORT",
        "direction_sign": sign,
        "entry_time_utc": utc_text(entry),
        "exit_time_utc": utc_text(exit_time),
        "entry_time_msc": int(entry.value // 1_000_000),
        "exit_time_msc": int(exit_time.value // 1_000_000),
        "entry_price": float(resolution["entry_price"]),
        "exit_price": float(resolution["exit_price"]),
        "dollars_per_price_unit": float(portfolio["ounces_at_reference_lot"])
        * risk_weight,
        "reference_lot": float(portfolio["reference_lot"]),
        "risk_weight": risk_weight,
        "effective_lot": lot,
        "base_cost_dollars": gross_pnl - base_pnl,
        "stress_cost_dollars": gross_pnl - stress_pnl,
        "base_pnl_dollars": base_pnl,
        "stress_pnl_dollars": stress_pnl,
        "broker_lot_exact": _broker_lot_exact(lot, account),
    }


def route_composite_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    position_until: pd.Timestamp | None = None
    ordered = sorted(
        rows,
        key=lambda row: (
            utc_timestamp(row["entry_time_utc"]),
            int(row["origin_attempt"]),
            str(row["candidate_id"]),
        ),
    )
    for row in ordered:
        entry = utc_timestamp(row["entry_time_utc"])
        if position_until is not None and entry < position_until:
            continue
        selected.append(dict(row))
        position_until = utc_timestamp(row["exit_time_utc"])
    return selected


def build_core_trades(
    bundle: SourceBundle,
    stage_dates: Sequence[str],
    config: Mapping[str, Any],
) -> pd.DataFrame:
    dates = set(stage_dates)
    sources = config["sources"]
    for stream in ("v28", "v29", "v34"):
        source = sources["v40"]["candidate_sources"][stream]
        _require_stage_resolutions(
            bundle.v40_candidates[stream],
            bundle.v40_resolutions[stream],
            dates,
            str(source["scheduled_time_field"]),
            f"V40 {stream}",
        )
    _require_stage_resolutions(
        bundle.v41_candidates,
        bundle.v41_resolutions,
        dates,
        str(sources["v41"]["scheduled_time_field"]),
        "V41",
    )
    _require_stage_resolutions(
        bundle.v38_candidates,
        bundle.v38_resolutions,
        dates,
        str(sources["v38"]["scheduled_time_field"]),
        "V38/V39",
        bundle.v39_routes,
    )

    records: list[dict[str, Any]] = []
    v40_by_stream = {
        stream: {str(row["candidate_id"]): row for row in rows}
        for stream, rows in bundle.v40_candidates.items()
    }
    v28_executed: list[dict[str, Any]] = []
    for resolution in bundle.v40_resolutions["v28"]:
        if str(resolution["resolution_status"]) != "EXECUTED":
            continue
        candidate = v40_by_stream["v28"][str(resolution["candidate_id"])]
        combined = dict(resolution)
        combined["origin_attempt"] = int(candidate["origin_attempt"])
        combined["candidate_id"] = str(candidate["candidate_id"])
        combined["specialist_id"] = str(candidate["specialist_id"])
        v28_executed.append(combined)
    for specialist in ("R2_DOWNTREND", "R3_COMPRESSION"):
        routed = route_composite_rows(
            [row for row in v28_executed if str(row["specialist_id"]) == specialist]
        )
        for resolution in routed:
            candidate = v40_by_stream["v28"][str(resolution["candidate_id"])]
            records.append(
                _core_trade(
                    candidate,
                    resolution,
                    specialist_id=specialist,
                    source_lane="V40_V28",
                    stage_time_field=str(
                        sources["v40"]["candidate_sources"]["v28"][
                            "scheduled_time_field"
                        ]
                    ),
                    config=config,
                )
            )

    simple_streams = (
        ("v29", "R1_UPTREND", "V40_V29"),
        ("v34", "R4_CHOP", "V40_V34"),
    )
    for stream, specialist, lane in simple_streams:
        for resolution in bundle.v40_resolutions[stream]:
            if str(resolution["resolution_status"]) != "EXECUTED":
                continue
            candidate = v40_by_stream[stream][str(resolution["candidate_id"])]
            records.append(
                _core_trade(
                    candidate,
                    resolution,
                    specialist_id=specialist,
                    source_lane=lane,
                    stage_time_field=str(
                        sources["v40"]["candidate_sources"][stream][
                            "scheduled_time_field"
                        ]
                    ),
                    config=config,
                )
            )

    v41_candidates = {str(row["candidate_id"]): row for row in bundle.v41_candidates}
    for resolution in bundle.v41_resolutions:
        if str(resolution["resolution_status"]) != "EXECUTED":
            continue
        candidate = v41_candidates[str(resolution["candidate_id"])]
        records.append(
            _core_trade(
                candidate,
                resolution,
                specialist_id="R1_UPTREND",
                source_lane="V41_R1_BOX",
                stage_time_field=str(sources["v41"]["scheduled_time_field"]),
                config=config,
            )
        )

    v38_candidates = {str(row["candidate_id"]): row for row in bundle.v38_candidates}
    v38_resolutions = {str(row["candidate_id"]): row for row in bundle.v38_resolutions}
    for route in bundle.v39_routes:
        weight = float(route["risk_weight"])
        if weight <= 0.0:
            continue
        candidate_id = str(route["candidate_id"])
        candidate = v38_candidates[candidate_id]
        if (
            _candidate_date(candidate, str(sources["v38"]["scheduled_time_field"]))
            not in dates
        ):
            continue
        resolution = v38_resolutions[candidate_id]
        if str(resolution["resolution_status"]) != "EXECUTED":
            continue
        records.append(
            _core_trade(
                candidate,
                resolution,
                specialist_id="R5_TRANSITION",
                source_lane="V38_V39_R5",
                stage_time_field=str(sources["v38"]["scheduled_time_field"]),
                config=config,
                risk_weight=weight,
            )
        )

    frame = pd.DataFrame(records, columns=TRADE_COLUMNS)
    if len(frame):
        frame = frame.loc[frame["stage_date_utc"].isin(dates)].sort_values(
            ["entry_time_msc", "source_lane", "trade_id"], kind="mergesort"
        )
        if frame["trade_id"].duplicated().any():
            raise ValueError("V42 duplicate Core trade ID")
    return frame.reset_index(drop=True)


def normalize_satellite_trades(
    trades: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=TRADE_COLUMNS)
    required = {
        "source_lane",
        "date_utc",
        "candidate_time_msc",
        "side",
        "entry_time_msc",
        "exit_time_msc",
        "entry_bid",
        "entry_ask",
        "exit_bid",
        "exit_ask",
        "observed_bidask_move",
        "base_pnl_dollars",
        "stress_pnl_dollars",
        "reference_lot",
    }
    if missing := required.difference(trades.columns):
        raise ValueError(f"V42 satellite trades lack columns: {sorted(missing)}")
    account = config["account_reference"]
    records: list[dict[str, Any]] = []
    for row in trades.to_dict("records"):
        sign = 1 if str(row["side"]) == "LONG" else -1
        if str(row["side"]) not in {"LONG", "SHORT"}:
            raise ValueError("V42 satellite direction changed")
        entry_price = float(row["entry_ask"] if sign > 0 else row["entry_bid"])
        exit_price = float(row["exit_bid"] if sign > 0 else row["exit_ask"])
        gross = float(row["observed_bidask_move"])
        lot = float(row["reference_lot"])
        candidate_id = f"{row['source_lane']}:{int(row['candidate_time_msc'])}"
        records.append(
            {
                "trade_id": sha256_bytes(candidate_id.encode("ascii"))[:24],
                "stage_date_utc": str(row["date_utc"]),
                "specialist_id": "SATELLITE_EXPANSION",
                "source_lane": str(row["source_lane"]),
                "candidate_id": candidate_id,
                "origin_attempt": -1,
                "direction": str(row["side"]),
                "direction_sign": sign,
                "entry_time_utc": utc_text(
                    pd.Timestamp(int(row["entry_time_msc"]), unit="ms", tz="UTC")
                ),
                "exit_time_utc": utc_text(
                    pd.Timestamp(int(row["exit_time_msc"]), unit="ms", tz="UTC")
                ),
                "entry_time_msc": int(row["entry_time_msc"]),
                "exit_time_msc": int(row["exit_time_msc"]),
                "entry_price": entry_price,
                "exit_price": exit_price,
                "dollars_per_price_unit": 1.0,
                "reference_lot": lot,
                "risk_weight": 1.0,
                "effective_lot": lot,
                "base_cost_dollars": gross - float(row["base_pnl_dollars"]),
                "stress_cost_dollars": gross - float(row["stress_pnl_dollars"]),
                "base_pnl_dollars": float(row["base_pnl_dollars"]),
                "stress_pnl_dollars": float(row["stress_pnl_dollars"]),
                "broker_lot_exact": _broker_lot_exact(lot, account),
            }
        )
    frame = pd.DataFrame(records, columns=TRADE_COLUMNS).sort_values(
        ["entry_time_msc", "source_lane", "trade_id"], kind="mergesort"
    )
    if frame["trade_id"].duplicated().any():
        raise ValueError("V42 duplicate satellite trade ID")
    return frame.reset_index(drop=True)


def profit_factor(values: Sequence[float] | pd.Series | np.ndarray) -> float:
    array = np.asarray(values, dtype=float)
    gains = float(array[array > 0.0].sum())
    losses = float(-array[array < 0.0].sum())
    if losses <= 0.0:
        return 999999.0 if gains > 0.0 else 0.0
    return gains / losses


def closed_drawdown(trades: pd.DataFrame, column: str) -> float:
    if trades.empty:
        return 0.0
    frame = trades[["exit_time_msc", column]].copy()
    realized = frame.groupby("exit_time_msc", sort=True)[column].sum().to_numpy(float)
    equity = np.concatenate(([0.0], np.cumsum(realized)))
    return float(np.max(np.maximum.accumulate(equity) - equity))


def _read_ticks(path: Path, tick_config: Mapping[str, Any]) -> pd.DataFrame:
    columns = (
        "schema_version",
        "timestamp_utc",
        "tick_time_msc",
        "account_login",
        "account_server",
        "symbol",
        "bid",
        "ask",
        "spread_price",
        "dry_run",
        "trade_permission",
        "broker_action_allowed",
        "python_execution_authorized",
    )
    frame = pd.read_csv(path, usecols=list(columns), low_memory=False)
    if frame.empty:
        return pd.DataFrame(columns=("tick_time_msc", "bid", "ask"))
    if not frame["schema_version"].eq(str(tick_config["schema_version"])).all():
        raise ValueError(f"V42 tick schema changed: {path.name}")
    checks = (
        frame["account_login"].astype(int).eq(int(tick_config["account_login"])).all(),
        frame["account_server"].eq(str(tick_config["account_server"])).all(),
        frame["symbol"].eq(str(tick_config["symbol"])).all(),
        frame["dry_run"].astype(str).str.lower().eq("true").all(),
        frame["trade_permission"].astype(str).str.lower().eq("false").all(),
        frame["broker_action_allowed"].astype(str).str.lower().eq("false").all(),
        frame["python_execution_authorized"].astype(str).str.lower().eq("false").all(),
    )
    if not all(checks):
        raise ValueError(f"V42 tick identity or authority changed: {path.name}")
    frame["tick_time_msc"] = pd.to_numeric(
        frame["tick_time_msc"], errors="raise"
    ).astype("int64")
    frame["bid"] = pd.to_numeric(frame["bid"], errors="raise")
    frame["ask"] = pd.to_numeric(frame["ask"], errors="raise")
    frame["spread_price"] = pd.to_numeric(frame["spread_price"], errors="raise")
    if not np.isfinite(frame[["bid", "ask", "spread_price"]].to_numpy(float)).all():
        raise ValueError(f"V42 non-finite tick: {path.name}")
    if frame["ask"].lt(frame["bid"]).any():
        raise ValueError(f"V42 crossed quote: {path.name}")
    if (
        (frame["ask"] - frame["bid"] - frame["spread_price"]).abs()
        > float(tick_config["maximum_spread_field_error"])
    ).any():
        raise ValueError(f"V42 spread field mismatch: {path.name}")
    parsed = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="raise")
    parsed_ms = parsed.dt.as_unit("ns").astype("int64") // 1_000_000
    if (
        (parsed_ms - frame["tick_time_msc"]).abs()
        > int(tick_config["maximum_timestamp_disagreement_ms"])
    ).any():
        raise ValueError(f"V42 tick timestamp disagreement: {path.name}")
    frame = frame.sort_values("tick_time_msc", kind="mergesort")
    duplicate = frame["tick_time_msc"].duplicated(keep=False)
    if duplicate.any():
        conflicts = (
            frame.loc[duplicate].groupby("tick_time_msc")[["bid", "ask"]].nunique()
        )
        if conflicts.gt(1).any(axis=None):
            raise ValueError(f"V42 conflicting duplicate tick: {path.name}")
        frame = frame.drop_duplicates("tick_time_msc", keep="first")
    return frame[["tick_time_msc", "bid", "ask"]].reset_index(drop=True)


def floating_equity_metrics(
    trades: pd.DataFrame,
    tick_paths: Sequence[Path],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    if trades.empty:
        return {
            "base_floating_drawdown_dollars": 0.0,
            "stress_floating_drawdown_dollars": 0.0,
            "minimum_base_equity_change_dollars": 0.0,
            "minimum_stress_equity_change_dollars": 0.0,
            "maximum_concurrent_positions": 0,
            "maximum_gross_lots": 0.0,
            "maximum_absolute_directional_lots": 0.0,
            "maximum_margin_dollars": 0.0,
            "marked_tick_rows": 0,
        }
    minimum_ms = int(trades["entry_time_msc"].min())
    maximum_ms = int(trades["exit_time_msc"].max())
    required_events = set(trades["entry_time_msc"].astype(int)).union(
        set(trades["exit_time_msc"].astype(int))
    )
    seen_events: set[int] = set()
    base_peak = stress_peak = 0.0
    base_dd = stress_dd = 0.0
    min_base = min_stress = 0.0
    maximum_count = 0
    maximum_gross_lots = 0.0
    maximum_directional_lots = 0.0
    maximum_margin = 0.0
    marked_rows = 0
    account = config["account_reference"]
    tick_config = config["sources"]["ticks"]
    for path in sorted(tick_paths):
        ticks = _read_ticks(path, tick_config)
        if ticks.empty:
            continue
        ticks = ticks.loc[
            ticks["tick_time_msc"].ge(minimum_ms)
            & ticks["tick_time_msc"].le(maximum_ms)
        ]
        if ticks.empty:
            continue
        times = ticks["tick_time_msc"].to_numpy(np.int64)
        seen_events.update(required_events.intersection(set(times.tolist())))
        bid = ticks["bid"].to_numpy(float)
        ask = ticks["ask"].to_numpy(float)
        base_equity = np.zeros(len(ticks), dtype=float)
        stress_equity = np.zeros(len(ticks), dtype=float)
        count = np.zeros(len(ticks), dtype=np.int16)
        gross_lots = np.zeros(len(ticks), dtype=float)
        directional_lots = np.zeros(len(ticks), dtype=float)
        for row in trades.to_dict("records"):
            entry_ms = int(row["entry_time_msc"])
            exit_ms = int(row["exit_time_msc"])
            entry_index = int(np.searchsorted(times, entry_ms, side="left"))
            exit_index = int(np.searchsorted(times, exit_ms, side="left"))
            if exit_index <= 0:
                base_equity += float(row["base_pnl_dollars"])
                stress_equity += float(row["stress_pnl_dollars"])
                continue
            if entry_index >= len(times):
                continue
            if exit_index < len(times):
                base_equity[exit_index:] += float(row["base_pnl_dollars"])
                stress_equity[exit_index:] += float(row["stress_pnl_dollars"])
            active_end = min(exit_index, len(times))
            active_start = max(entry_index, 0)
            if active_start >= active_end:
                continue
            sign = int(row["direction_sign"])
            mark = (
                bid[active_start:active_end]
                if sign > 0
                else ask[active_start:active_end]
            )
            move = sign * (mark - float(row["entry_price"]))
            gross = move * float(row["dollars_per_price_unit"])
            base_equity[active_start:active_end] += gross - float(
                row["base_cost_dollars"]
            )
            stress_equity[active_start:active_end] += gross - float(
                row["stress_cost_dollars"]
            )
            lot = float(row["effective_lot"])
            count[active_start:active_end] += 1
            gross_lots[active_start:active_end] += lot
            directional_lots[active_start:active_end] += sign * lot
        base_running_peak = np.maximum.accumulate(
            np.concatenate(([base_peak], base_equity))
        )[1:]
        stress_running_peak = np.maximum.accumulate(
            np.concatenate(([stress_peak], stress_equity))
        )[1:]
        base_dd = max(base_dd, float(np.max(base_running_peak - base_equity)))
        stress_dd = max(stress_dd, float(np.max(stress_running_peak - stress_equity)))
        base_peak = max(base_peak, float(np.max(base_equity)))
        stress_peak = max(stress_peak, float(np.max(stress_equity)))
        min_base = min(min_base, float(np.min(base_equity)))
        min_stress = min(min_stress, float(np.min(stress_equity)))
        maximum_count = max(maximum_count, int(np.max(count)))
        maximum_gross_lots = max(maximum_gross_lots, float(np.max(gross_lots)))
        maximum_directional_lots = max(
            maximum_directional_lots, float(np.max(np.abs(directional_lots)))
        )
        mid = (bid + ask) / 2.0
        margin = (
            gross_lots
            * float(account["contract_size_ounces_per_lot"])
            * mid
            / float(account["leverage"])
        )
        maximum_margin = max(maximum_margin, float(np.max(margin)))
        marked_rows += len(ticks)
    if missing := sorted(required_events.difference(seen_events)):
        raise ValueError(
            f"V42 tick ledger lacks {len(missing)} exact entry/exit events"
        )
    return {
        "base_floating_drawdown_dollars": base_dd,
        "stress_floating_drawdown_dollars": stress_dd,
        "minimum_base_equity_change_dollars": min_base,
        "minimum_stress_equity_change_dollars": min_stress,
        "maximum_concurrent_positions": maximum_count,
        "maximum_gross_lots": maximum_gross_lots,
        "maximum_absolute_directional_lots": maximum_directional_lots,
        "maximum_margin_dollars": maximum_margin,
        "marked_tick_rows": marked_rows,
    }


def select_tick_paths(trades: pd.DataFrame, config: Mapping[str, Any]) -> list[Path]:
    if trades.empty:
        return []
    start = pd.Timestamp(
        int(trades["entry_time_msc"].min()), unit="ms", tz="UTC"
    ).date()
    end = pd.Timestamp(int(trades["exit_time_msc"].max()), unit="ms", tz="UTC").date()
    tick_config = config["sources"]["ticks"]
    result: list[Path] = []
    for path in Path(tick_config["directory"]).glob(tick_config["filename_glob"]):
        match = DATE_PATTERN.search(path.name)
        if match is None:
            continue
        date = pd.Timestamp(match.group(1)).date()
        if start <= date <= end:
            result.append(path)
    if not result:
        raise StageNotReady("V42 has no tick files for the stage trades")
    return sorted(result)


def stage_metrics(
    trades: pd.DataFrame,
    stage_dates: Sequence[str],
    floating: Mapping[str, Any],
) -> dict[str, Any]:
    base = trades["base_pnl_dollars"].astype(float)
    stress = trades["stress_pnl_dollars"].astype(float)
    daily = pd.DataFrame({"stage_date_utc": list(stage_dates)})
    observed = (
        trades.groupby("stage_date_utc", as_index=False).agg(
            trades=("trade_id", "size"),
            base_pnl_dollars=("base_pnl_dollars", "sum"),
            stress_pnl_dollars=("stress_pnl_dollars", "sum"),
        )
        if len(trades)
        else pd.DataFrame(
            columns=(
                "stage_date_utc",
                "trades",
                "base_pnl_dollars",
                "stress_pnl_dollars",
            )
        )
    )
    daily = daily.merge(
        observed, on="stage_date_utc", how="left", validate="one_to_one"
    ).fillna(0)
    midpoint = len(stage_dates) // 2
    first = trades.loc[trades["stage_date_utc"].isin(stage_dates[:midpoint])]
    second = trades.loc[trades["stage_date_utc"].isin(stage_dates[midpoint:])]
    worst_daily_stress_loss = max(0.0, float(-daily["stress_pnl_dollars"].min()))
    specialists: dict[str, Any] = {}
    for specialist, group in trades.groupby("specialist_id", sort=True):
        specialists[str(specialist)] = {
            "trades": int(len(group)),
            "trades_per_weekday": float(len(group) / len(stage_dates)),
            "base_net_dollars": float(group["base_pnl_dollars"].sum()),
            "stress_net_dollars": float(group["stress_pnl_dollars"].sum()),
            "base_profit_factor": profit_factor(group["base_pnl_dollars"]),
            "stress_profit_factor": profit_factor(group["stress_pnl_dollars"]),
        }
    return {
        "full_weekdays": len(stage_dates),
        "trades": int(len(trades)),
        "trades_per_weekday": float(len(trades) / len(stage_dates)),
        "base_net_dollars": float(base.sum()),
        "stress_net_dollars": float(stress.sum()),
        "base_profit_factor": profit_factor(base),
        "stress_profit_factor": profit_factor(stress),
        "base_closed_drawdown_dollars": closed_drawdown(trades, "base_pnl_dollars"),
        "stress_closed_drawdown_dollars": closed_drawdown(trades, "stress_pnl_dollars"),
        "profitable_day_share": float(daily["base_pnl_dollars"].gt(0.0).mean()),
        "worst_daily_stress_loss_dollars": worst_daily_stress_loss,
        "first_half_base_profit_factor": profit_factor(first["base_pnl_dollars"]),
        "second_half_base_profit_factor": profit_factor(second["base_pnl_dollars"]),
        "maximum_trades_on_one_day": int(daily["trades"].max()),
        "specialists": specialists,
        **dict(floating),
    }


def evaluate_gates(
    metrics: Mapping[str, Any],
    *,
    v27_gate_passed: bool,
    config: Mapping[str, Any],
) -> tuple[dict[str, bool], dict[str, bool], dict[str, Any]]:
    gates = config["research_gates"]
    research = {
        "v27_stage_passed": (not gates["require_v27_stage_pass"] or v27_gate_passed),
        "minimum_total_frequency": float(metrics["trades_per_weekday"])
        >= float(gates["minimum_total_trades_per_weekday"]),
        "maximum_total_frequency": float(metrics["trades_per_weekday"])
        <= float(gates["maximum_total_trades_per_weekday"]),
        "positive_base_net": (
            not gates["require_positive_base_net"]
            or float(metrics["base_net_dollars"]) > 0.0
        ),
        "positive_stress_net": (
            not gates["require_positive_stress_net"]
            or float(metrics["stress_net_dollars"]) > 0.0
        ),
        "minimum_base_profit_factor": float(metrics["base_profit_factor"])
        >= float(gates["minimum_base_profit_factor"]),
        "minimum_stress_profit_factor": float(metrics["stress_profit_factor"])
        >= float(gates["minimum_stress_profit_factor"]),
        "minimum_profitable_day_share": float(metrics["profitable_day_share"])
        >= float(gates["minimum_profitable_day_share"]),
        "first_half_base_profit_factor": float(metrics["first_half_base_profit_factor"])
        >= float(gates["minimum_half_base_profit_factor"]),
        "second_half_base_profit_factor": float(
            metrics["second_half_base_profit_factor"]
        )
        >= float(gates["minimum_half_base_profit_factor"]),
        "maximum_closed_drawdown": float(metrics["base_closed_drawdown_dollars"])
        <= float(gates["maximum_closed_drawdown_dollars"]),
    }
    account = config["account_reference"]
    equity = float(account["reference_equity_dollars"])
    max_dd = equity * float(account["maximum_equity_drawdown_fraction"])
    max_daily_loss = equity * float(account["maximum_daily_loss_fraction"])
    max_margin = equity * float(account["maximum_margin_fraction"])
    historical_dd = float(
        account["historical_conservative_core_equity_drawdown_dollars"]
    )
    all_lots_exact = bool(metrics.get("all_trade_lots_broker_exact", False))
    account_checks = {
        "prospective_floating_drawdown_fits": float(
            metrics["stress_floating_drawdown_dollars"]
        )
        <= max_dd,
        "prospective_daily_loss_fits": float(metrics["worst_daily_stress_loss_dollars"])
        <= max_daily_loss,
        "prospective_margin_fits": float(metrics["maximum_margin_dollars"])
        <= max_margin,
        "prospective_concurrency_fits": int(metrics["maximum_concurrent_positions"])
        <= int(account["maximum_concurrent_positions"]),
        "prospective_directional_exposure_fits": float(
            metrics["maximum_absolute_directional_lots"]
        )
        <= float(account["maximum_absolute_directional_lots"]),
        "historical_core_drawdown_fits": (
            not account["historical_risk_must_fit_reference_equity"]
            or historical_dd <= max_dd
        ),
        "all_trade_lots_broker_exact": all_lots_exact,
        "r5_broker_sizing_mapping_preregistered": bool(
            account["r5_broker_sizing_mapping_preregistered"]
        ),
    }
    required_equity = max(
        historical_dd / float(account["maximum_equity_drawdown_fraction"]),
        float(metrics["stress_floating_drawdown_dollars"])
        / float(account["maximum_equity_drawdown_fraction"]),
        float(metrics["worst_daily_stress_loss_dollars"])
        / float(account["maximum_daily_loss_fraction"]),
        float(metrics["maximum_margin_dollars"])
        / float(account["maximum_margin_fraction"]),
    )
    readiness = {
        "reference_equity_dollars": equity,
        "maximum_allowed_drawdown_dollars": max_dd,
        "maximum_allowed_daily_loss_dollars": max_daily_loss,
        "maximum_allowed_margin_dollars": max_margin,
        "minimum_equity_required_dollars": required_equity,
        "research_gate_passed": bool(all(research.values())),
        "account_gate_passed": bool(all(account_checks.values())),
        "execution_ready": False,
        "execution_ready_reason": "V42_IS_RESEARCH_ONLY_AND_HAS_NO_EXECUTION_AUTHORITY",
    }
    return research, account_checks, readiness


def evaluate_stage(
    core: pd.DataFrame,
    satellite: pd.DataFrame,
    stage_dates: Sequence[str],
    *,
    v27_gate_passed: bool,
    tick_paths: Sequence[Path],
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if len(stage_dates) != int(config["stages"]["required_full_weekdays_per_stage"]):
        raise ValueError("V42 stage does not contain exactly 20 weekdays")
    combined = pd.concat([core, satellite], ignore_index=True).sort_values(
        ["entry_time_msc", "source_lane", "trade_id"], kind="mergesort"
    )
    if combined["trade_id"].duplicated().any():
        raise ValueError("V42 duplicate combined trade ID")
    floating = floating_equity_metrics(combined, tick_paths, config)
    metrics = stage_metrics(combined, stage_dates, floating)
    metrics["core_trades"] = int(len(core))
    metrics["satellite_trades"] = int(len(satellite))
    metrics["core_trades_per_weekday"] = float(len(core) / len(stage_dates))
    metrics["satellite_trades_per_weekday"] = float(len(satellite) / len(stage_dates))
    metrics["core_trade_rejections_by_v42"] = 0
    metrics["satellite_trade_rejections_by_v42"] = 0
    metrics["all_trade_lots_broker_exact"] = bool(combined["broker_lot_exact"].all())
    research, account, readiness = evaluate_gates(
        metrics, v27_gate_passed=v27_gate_passed, config=config
    )
    result = {
        "metrics": metrics,
        "research_gate_checks": research,
        "account_gate_checks": account,
        "readiness": readiness,
    }
    return combined.reset_index(drop=True), result
