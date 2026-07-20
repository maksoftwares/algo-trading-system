from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any, Mapping, Sequence

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "capital_r5_causal_router_v39.json"


@dataclass(frozen=True)
class FrozenRouter:
    v38: Any
    router: Any
    v38_config: dict[str, Any]
    v11_config: dict[str, Any]
    policy: Any
    base_weights: dict[int, float]


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _repo_path(repo_root: Path, relative: str) -> Path:
    root = repo_root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"V39 dependency escaped repository: {relative}") from exc
    return path


def verify_contract(
    config: Mapping[str, Any], repo_root: Path = REPO_ROOT, package_root: Path = ROOT
) -> dict[str, Any]:
    path = (
        package_root
        / str(config["outputs"]["directory"])
        / str(config["outputs"]["contract_lock"])
    )
    if not path.is_file():
        raise FileNotFoundError("V39 contract lock is absent")
    lock = json.loads(path.read_text(encoding="utf-8"))
    work = {key: value for key, value in lock.items() if key != "contract_sha256"}
    if canonical_sha256(work) != str(lock.get("contract_sha256")):
        raise ValueError("V39 contract self-hash mismatch")
    for relative, record in lock["package_files"].items():
        file_path = package_root / relative
        if int(file_path.stat().st_size) != int(record["bytes"]):
            raise ValueError(f"V39 package size changed: {relative}")
        if sha256_file(file_path) != str(record["sha256"]):
            raise ValueError(f"V39 package hash changed: {relative}")
    for relative, record in lock["dependencies"].items():
        file_path = _repo_path(repo_root, relative)
        if int(file_path.stat().st_size) != int(record["bytes"]):
            raise ValueError(f"V39 dependency size changed: {relative}")
        if sha256_file(file_path) != str(record["sha256"]):
            raise ValueError(f"V39 dependency hash changed: {relative}")
    return lock


def load_frozen(config: Mapping[str, Any], repo_root: Path = REPO_ROOT) -> FrozenRouter:
    source = config["source"]
    identity = config["frozen_identity"]
    v38 = load_module(
        "capital_r5_v39_v38_resolver",
        _repo_path(repo_root, str(source["v38_resolver_module"])),
    )
    router = load_module(
        "capital_r5_v39_v11_router",
        _repo_path(repo_root, str(source["v11_router_module"])),
    )
    v38_config = json.loads(
        _repo_path(repo_root, str(source["v38_config"])).read_text(encoding="utf-8")
    )
    v11_config = json.loads(
        _repo_path(repo_root, str(source["v11_config"])).read_text(encoding="utf-8")
    )
    v35_lock = json.loads(
        _repo_path(repo_root, str(source["v35_contract_lock"])).read_text(
            encoding="utf-8"
        )
    )
    v38_lock = json.loads(
        _repo_path(repo_root, str(source["v38_contract_lock"])).read_text(
            encoding="utf-8"
        )
    )
    if str(v35_lock["contract_sha256"]) != str(identity["v35_contract_sha256"]):
        raise ValueError("V39 V35 contract identity changed")
    if str(v35_lock["rule_dependency_sha256"]) != str(
        identity["v35_rule_dependency_sha256"]
    ):
        raise ValueError("V39 V35 rule dependency changed")
    if str(v38_lock["contract_sha256"]) != str(identity["v38_contract_sha256"]):
        raise ValueError("V39 V38 contract identity changed")

    manifest = pd.read_csv(_repo_path(repo_root, str(source["v11_manifest"])))
    selected = manifest.loc[manifest["attempt_no"].eq(int(identity["router_attempt"]))]
    if len(selected) != 1:
        raise ValueError("V39 frozen router policy is not unique")
    row = selected.iloc[0]
    if str(row["router_id"]) != str(identity["router_id"]):
        raise ValueError("V39 frozen router ID changed")
    if str(row["mechanic"]) != str(identity["router_mechanic"]):
        raise ValueError("V39 frozen router mechanic changed")
    actual_params = json.dumps(
        json.loads(str(row["parameters_json"])),
        sort_keys=True,
        separators=(",", ":"),
    )
    if actual_params != str(identity["router_parameters_json"]):
        raise ValueError("V39 frozen router parameters changed")
    if str(v11_config["portfolio"]["tie_priority"]) != str(identity["tie_priority"]):
        raise ValueError("V39 frozen tie priority changed")
    base_weights = {
        int(key): float(value) for key, value in identity["base_weights"].items()
    }
    if base_weights != {
        int(key): float(value)
        for key, value in v11_config["portfolio"]["base_weights"].items()
    }:
        raise ValueError("V39 frozen base weights changed")
    policy = SimpleNamespace(
        attempt_no=int(row["attempt_no"]),
        router_id=str(row["router_id"]),
        mechanic=str(row["mechanic"]),
        parameters_json=actual_params,
        tie_priority=str(identity["tie_priority"]),
    )
    return FrozenRouter(v38, router, v38_config, v11_config, policy, base_weights)


def validate_resolution_rows(
    rows: Sequence[Mapping[str, Any]], config: Mapping[str, Any]
) -> list[dict[str, Any]]:
    attempts = {int(value) for value in config["frozen_identity"]["component_attempts"]}
    result: list[dict[str, Any]] = []
    for row in rows:
        status = str(row.get("resolution_status"))
        if status not in {"EXECUTED", "REJECTED"}:
            raise ValueError("V39 resolution has invalid status")
        attempt = int(row.get("origin_attempt", -1))
        if attempt not in attempts:
            raise ValueError("V39 resolution has unexpected component")
        if bool(row.get("broker_action_authorized")):
            raise ValueError("V39 resolution has broker authority")
        value = dict(row)
        if status == "EXECUTED":
            for field in (
                "entry_time_utc",
                "exit_time_utc",
                "knowledge_time_utc",
                "stress_net_r",
            ):
                if field not in value:
                    raise ValueError(f"V39 executed resolution lacks {field}")
            value["entry_time"] = pd.Timestamp(value["entry_time_utc"])
            value["exit_time"] = pd.Timestamp(value["exit_time_utc"])
            value["knowledge_time"] = pd.Timestamp(value["knowledge_time_utc"])
            if value["entry_time"].tzinfo is None or value["exit_time"].tzinfo is None:
                raise ValueError("V39 resolution time is timezone-naive")
            value["entry_time"] = value["entry_time"].tz_convert("UTC")
            value["exit_time"] = value["exit_time"].tz_convert("UTC")
            value["knowledge_time"] = value["knowledge_time"].tz_convert("UTC")
            if value["knowledge_time"] < value["exit_time"]:
                raise ValueError("V39 outcome was known before its exit")
            stress = float(value["stress_net_r"])
            if not math.isfinite(stress):
                raise ValueError("V39 resolution has non-finite stress outcome")
            value["stress_net_r"] = stress
        result.append(value)
    return result


def route_stats(
    component: int,
    entry: pd.Timestamp,
    historical: pd.DataFrame,
    resolutions: Sequence[Mapping[str, Any]],
    frozen: FrozenRouter,
) -> tuple[float, str, Any, int, int]:
    entry = pd.Timestamp(entry)
    if entry.tzinfo is None:
        raise ValueError("V39 candidate entry is timezone-naive")
    entry = entry.tz_convert("UTC")
    params = json.loads(str(frozen.policy.parameters_json))
    lookback = int(params["lookback_days"])
    start = entry - pd.Timedelta(days=lookback)
    history = historical.copy()
    history["exit_time"] = pd.to_datetime(history["exit_time"], utc=True)
    history = history.loc[
        history["exit_time"].lt(entry) & history["exit_time"].ge(start),
        ["attempt_no", "exit_time", "stress_net_r"],
    ]
    prospective_rows = [
        {
            "attempt_no": int(row["origin_attempt"]),
            "exit_time": row["exit_time"],
            "stress_net_r": float(row["stress_net_r"]),
        }
        for row in resolutions
        if str(row["resolution_status"]) == "EXECUTED"
        and pd.Timestamp(row["exit_time"]) < entry
        and pd.Timestamp(row["knowledge_time"]) < entry
        and pd.Timestamp(row["exit_time"]) >= start
    ]
    prospective = pd.DataFrame(
        prospective_rows, columns=["attempt_no", "exit_time", "stress_net_r"]
    )
    combined = pd.concat([history, prospective], ignore_index=True)
    if not combined.empty:
        combined = combined.sort_values(
            ["exit_time", "attempt_no"], kind="mergesort"
        ).reset_index(drop=True)
    entry_ns = int(entry.value)
    components = sorted(frozen.base_weights)
    cache = {}
    for attempt in components:
        values = combined.loc[
            combined["attempt_no"].eq(attempt), "stress_net_r"
        ].to_numpy(dtype=float)
        cache[(entry_ns, attempt, lookback)] = frozen.router._stats(values)  # noqa: SLF001
    multiplier, reason, stats = frozen.router.route_multiplier(
        int(component),
        entry_ns,
        str(frozen.policy.mechanic),
        params,
        components,
        cache,
    )
    return (
        float(multiplier),
        str(reason),
        stats,
        int(len(history)),
        int(len(prospective)),
    )


def route_candidate(
    candidate: Mapping[str, Any],
    historical: pd.DataFrame,
    resolutions: Sequence[Mapping[str, Any]],
    frozen: FrozenRouter,
    contract_sha256: str,
) -> dict[str, Any]:
    component = int(candidate["origin_attempt"])
    entry = pd.Timestamp(candidate["scheduled_entry_time"])
    multiplier, reason, stats, historical_rows, prospective_rows = route_stats(
        component, entry, historical, resolutions, frozen
    )
    profit_factor = float(stats.profit_factor)
    return {
        "schema_version": "xauusd_capital_r5_causal_route_v39",
        "candidate_id": str(candidate["candidate_id"]),
        "candidate_fact_sha256": str(candidate["candidate_fact_sha256"]),
        "origin_attempt": component,
        "signal_time_utc": str(candidate["signal_time_utc"]),
        "scheduled_entry_time_utc": str(candidate["scheduled_entry_time_utc"]),
        "direction": str(candidate["direction"]),
        "direction_sign": int(candidate["direction_sign"]),
        "router_attempt": int(frozen.policy.attempt_no),
        "router_id": str(frozen.policy.router_id),
        "router_mechanic": str(frozen.policy.mechanic),
        "shadow_count": int(stats.count),
        "shadow_mean_r": float(stats.mean_r),
        "shadow_profit_factor": profit_factor if math.isfinite(profit_factor) else None,
        "shadow_drawdown_r": float(stats.drawdown_r),
        "route_multiplier": multiplier,
        "route_reason": reason,
        "base_weight": float(frozen.base_weights[component]),
        "risk_weight": float(frozen.base_weights[component]) * multiplier,
        "historical_history_rows_available": historical_rows,
        "prospective_history_rows_available": prospective_rows,
        "history_cutoff": "EXIT_AND_CAUSAL_KNOWLEDGE_STRICTLY_BEFORE_CANDIDATE_ENTRY",
        "candidate_outcome_attached": False,
        "aggregate_economics_opened": False,
        "contract_sha256": str(contract_sha256),
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
    }


def read_routed_ledger(path: Path, v38: Any) -> list[dict[str, Any]]:
    snapshot = v38.stable_line_prefix(path)
    if path.is_file() and int(path.stat().st_size) != len(snapshot):
        raise ValueError("V39 routed ledger has a partial trailing record")
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(snapshot.splitlines(), start=1):
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError(f"V39 route line {line_number} is not an object")
        if str(value.get("schema_version")) != "xauusd_capital_r5_causal_route_v39":
            raise ValueError("V39 route schema changed")
        if bool(value.get("broker_action_authorized")):
            raise ValueError("V39 route has broker authority")
        rows.append(value)
    ids = [str(row.get("candidate_id")) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("V39 routed ledger contains duplicate candidate IDs")
    return rows


def verify_named_prefix(
    snapshot: bytes, state: Mapping[str, Any] | None, name: str
) -> None:
    if not state:
        return
    byte_key = f"{name}_prefix_bytes"
    hash_key = f"{name}_prefix_sha256"
    previous_bytes = int(state.get(byte_key, 0))
    previous_sha = str(state.get(hash_key, hashlib.sha256(b"").hexdigest()))
    if len(snapshot) < previous_bytes:
        raise ValueError(f"V39 {name} ledger was truncated")
    if hashlib.sha256(snapshot[:previous_bytes]).hexdigest() != previous_sha:
        raise ValueError(f"V39 {name} consumed prefix was mutated")


def validate_existing_routes(
    routes: Sequence[Mapping[str, Any]],
    candidates: Sequence[Mapping[str, Any]],
    contract: str,
) -> None:
    by_id = {str(row["candidate_id"]): row for row in candidates}
    unknown = sorted({str(row["candidate_id"]) for row in routes}.difference(by_id))
    if unknown:
        raise ValueError(f"V39 route contains unknown candidates: {unknown[:3]}")
    for route in routes:
        candidate = by_id[str(route["candidate_id"])]
        if str(route.get("candidate_fact_sha256")) != str(
            candidate["candidate_fact_sha256"]
        ):
            raise ValueError("V39 route candidate fact hash changed")
        if str(route.get("contract_sha256")) != str(contract):
            raise ValueError("V39 route belongs to another contract")
