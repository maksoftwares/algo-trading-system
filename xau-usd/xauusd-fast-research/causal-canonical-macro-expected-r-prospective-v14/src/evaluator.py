from __future__ import annotations

import importlib.util
import json
import math
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
M5_MS = 300_000
HOUR_MS = 3_600_000
FINAL_ACTIONS = frozenset(("RETAIN", "VETO", "MODEL_ABSTAIN_RETAIN_ALL"))
MACRO_FEATURES = (
    "dir_inverse_dollar_return_1h",
    "dir_inverse_dollar_return_4h",
    "dir_inverse_dollar_return_24h",
    "dir_bond_return_1h",
    "dir_bond_return_4h",
    "dir_bond_return_24h",
    "crossasset_max_staleness_seconds",
    "crossasset_coverage_fraction",
)


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object: {path}")
    return value


def stable_jsonl_snapshot(path: Path) -> tuple[list[dict[str, Any]], bytes]:
    if not path.is_file():
        return [], b""
    payload = path.read_bytes()
    if payload and not payload.endswith(b"\n"):
        last_newline = payload.rfind(b"\n")
        payload = b"" if last_newline < 0 else payload[: last_newline + 1]
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(payload.splitlines(), start=1):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL {path}:{line_number}") from exc
        if not isinstance(value, dict):
            raise TypeError(f"Non-object JSONL {path}:{line_number}")
        rows.append(value)
    return rows, payload


def _load_v13(config: Mapping[str, Any]) -> ModuleType:
    path = REPO_ROOT / str(config["upstream"]["v13_evaluator_path"])
    return load_module("macro_expected_r_v14_v13", path)


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(payload: Mapping[str, Any], omitted_key: str) -> str:
    import hashlib

    value = dict(payload)
    value.pop(omitted_key, None)
    encoded = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def utc_timestamp(value: Any) -> pd.Timestamp:
    result = pd.Timestamp(value)
    if result.tzinfo is None:
        raise ValueError(f"Timezone-naive timestamp: {value}")
    return result.tz_convert("UTC")


def utc_text(value: Any) -> str:
    return utc_timestamp(value).isoformat().replace("+00:00", "Z")


def verify_config_hashes(config: Mapping[str, Any]) -> None:
    checks = (
        (config["model"]["path"], config["model"]["sha256"], "model"),
        (
            config["model"]["manifest_path"],
            config["model"]["manifest_sha256"],
            "model manifest",
        ),
        (
            config["model"]["expected_r_module_path"],
            config["model"]["expected_r_module_sha256"],
            "Expected-R module",
        ),
        (
            config["upstream"]["v13_contract_path"],
            config["upstream"]["v13_contract_file_sha256"],
            "V13 contract",
        ),
        (
            config["upstream"]["v13_evaluator_path"],
            config["upstream"]["v13_evaluator_sha256"],
            "V13 evaluator",
        ),
        (
            config["macro_source"]["source_config_path"],
            config["macro_source"]["source_config_sha256"],
            "macro source config",
        ),
        (
            config["macro_source"]["m5_module_path"],
            config["macro_source"]["m5_module_sha256"],
            "macro M5 module",
        ),
    )
    for relative, expected, label in checks:
        path = REPO_ROOT / str(relative)
        if not path.is_file() or sha256_file(path) != str(expected):
            raise ValueError(f"{label} identity changed: {path}")
    v13_contract = read_json(REPO_ROOT / str(config["upstream"]["v13_contract_path"]))
    if str(v13_contract["contract_sha256"]) != str(
        config["upstream"]["v13_contract_sha256"]
    ):
        raise ValueError("V13 contract self-identity changed")


def verify_contract(package_root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    path = (
        package_root
        / str(config["outputs"]["directory"])
        / str(config["outputs"]["contract_lock"])
    )
    if not path.is_file():
        raise FileNotFoundError("V14 contract lock is absent")
    contract = read_json(path)
    if str(contract.get("contract_sha256")) != canonical_hash(
        contract, "contract_sha256"
    ):
        raise ValueError("V14 contract self-hash changed")
    if str(contract["forward_start_inclusive_utc"]) != str(
        config["forward_start_inclusive_utc"]
    ):
        raise ValueError("V14 forward boundary changed")
    for base, key in (
        (package_root, "package_files"),
        (REPO_ROOT, "dependencies"),
    ):
        for record in contract[key]:
            source = base / str(record["path"])
            if (
                not source.is_file()
                or source.stat().st_size != int(record["bytes"])
                or sha256_file(source) != str(record["sha256"])
            ):
                raise ValueError(f"V14 locked file changed: {record['path']}")
    verify_config_hashes(config)
    return contract


def _load_expected_r(config: Mapping[str, Any]) -> None:
    path = REPO_ROOT / str(config["model"]["expected_r_module_path"])
    if "src.expected_r" not in sys.modules:
        load_module("src.expected_r", path)


def load_model(config: Mapping[str, Any]) -> dict[str, Any]:
    _load_expected_r(config)
    path = REPO_ROOT / str(config["model"]["path"])
    payload = joblib.load(path)
    if payload["schema_version"] != "xauusd_macro_expected_r_v14_final_research_model":
        raise ValueError("Unexpected V14 model schema")
    if int(payload["fit_rows"]) != int(config["model"]["actual_fit_rows"]):
        raise ValueError("V14 fit row count changed")
    if not math.isclose(
        float(payload["veto_quantile"]),
        float(config["model"]["veto_quantile"]),
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError("V14 veto quantile changed")
    if any(
        bool(payload.get(key))
        for key in (
            "python_serving_authorized",
            "ml_shadow_authorized",
            "ea_consumption_authorized",
            "broker_action_authorized",
            "demo_authorized",
            "live_authorized",
        )
    ):
        raise ValueError("V14 model unexpectedly enables authority")
    return payload


def latest_macro_snapshot(
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame | None, dict[str, Any] | None, str | None]:
    source = config["macro_source"]
    storage = Path(str(source["storage_root"]))
    manifests = sorted(storage.glob(str(source["feature_manifest_glob"])))
    if not manifests:
        return None, None, "AWAITING_MACRO_SNAPSHOT"
    candidates: list[tuple[pd.Timestamp, Path, dict[str, Any]]] = []
    for path in manifests:
        manifest = read_json(path)
        snapshot_path = Path(str(manifest["snapshot_manifest"]))
        feature_path = Path(str(manifest["feature_path"]))
        if (
            not snapshot_path.is_file()
            or sha256_file(snapshot_path) != str(manifest["snapshot_manifest_sha256"])
            or not feature_path.is_file()
            or sha256_file(feature_path) != str(manifest["feature_sha256"])
        ):
            raise ValueError(f"Macro artifact identity changed: {path}")
        snapshot = read_json(snapshot_path)
        candidates.append(
            (
                utc_timestamp(snapshot["end_exclusive_utc"]),
                path,
                manifest,
            )
        )
    _, path, manifest = max(candidates, key=lambda item: item[0])
    frame = pd.read_parquet(Path(str(manifest["feature_path"])))
    evidence = {
        "manifest_path": str(path.resolve()).replace("\\", "/"),
        "manifest_sha256": sha256_file(path),
        "feature_path": str(Path(str(manifest["feature_path"])).resolve()).replace(
            "\\", "/"
        ),
        "feature_sha256": str(manifest["feature_sha256"]),
        "snapshot_path": str(
            Path(str(manifest["snapshot_manifest"])).resolve()
        ).replace("\\", "/"),
        "snapshot_sha256": str(manifest["snapshot_manifest_sha256"]),
        "snapshot_end_exclusive_utc": read_json(
            Path(str(manifest["snapshot_manifest"]))
        )["end_exclusive_utc"],
        "historical_parity": manifest["historical_parity"],
    }
    if float(evidence["historical_parity"]["maximum_absolute_error"]) != 0.0:
        raise ValueError("Macro source no longer has exact historical parity")
    return frame, evidence, None


def _completed_close(
    frame: pd.DataFrame,
    prefix: str,
    endpoint_ms: int,
) -> tuple[int, float] | None:
    eligible = frame.loc[
        frame["timestamp_ms"].lt(endpoint_ms)
        & frame[f"{prefix}_available"].astype(bool)
        & frame[f"{prefix}_mid_close"].notna(),
        ["timestamp_ms", f"{prefix}_mid_close"],
    ]
    if eligible.empty:
        return None
    row = eligible.iloc[-1]
    return int(row["timestamp_ms"]) + M5_MS, float(row[f"{prefix}_mid_close"])


def build_macro_features(
    cutoff: pd.Timestamp,
    direction: str,
    frame: pd.DataFrame,
    evidence: Mapping[str, Any],
    config: Mapping[str, Any],
) -> tuple[dict[str, float | None], str]:
    direction_sign = 1.0 if direction == "LONG" else -1.0
    cutoff_ms = int(cutoff.timestamp() * 1000)
    endpoint_ms = cutoff_ms // HOUR_MS * HOUR_MS
    snapshot_end = utc_timestamp(evidence["snapshot_end_exclusive_utc"])
    endpoint = pd.Timestamp(endpoint_ms, unit="ms", tz="UTC")
    if snapshot_end < endpoint:
        return {name: None for name in MACRO_FEATURES}, "AWAITING_MACRO_SNAPSHOT"
    values: dict[str, float | None] = {}
    ages: list[float] = []
    available = 0
    for feature_name, prefix, sign in (
        ("inverse_dollar", "dollaridxusd", -direction_sign),
        ("bond", "ustbondtrusd", direction_sign),
    ):
        current = _completed_close(frame, prefix, endpoint_ms)
        if current is None:
            for hours in (1, 4, 24):
                values[f"dir_{feature_name}_return_{hours}h"] = None
            continue
        ages.append((cutoff_ms - current[0]) / 1000.0)
        for hours in (1, 4, 24):
            previous = _completed_close(frame, prefix, endpoint_ms - hours * HOUR_MS)
            key = f"dir_{feature_name}_return_{hours}h"
            if previous is None or previous[1] <= 0.0 or current[1] <= 0.0:
                values[key] = None
            else:
                values[key] = sign * math.log(current[1] / previous[1])
                available += 1
    values["crossasset_max_staleness_seconds"] = max(ages) if ages else None
    values["crossasset_coverage_fraction"] = available / 6.0
    if not ages:
        return values, "ABSTAIN_MISSING_MACRO"
    if max(ages) > float(config["macro_source"]["maximum_staleness_seconds"]):
        return values, "ABSTAIN_STALE_MACRO"
    if available < 6:
        return values, "ABSTAIN_INCOMPLETE_MACRO"
    return values, "PASS"


def _stable_rows(v13: ModuleType, path: Path) -> tuple[list[dict[str, Any]], bytes]:
    rows, payload = v13.stable_jsonl_snapshot(path)
    for row in rows:
        v13.validate_no_authority(row, f"V14 upstream {path.name}")
    return rows, payload


def _prefix_record(
    v13: ModuleType, path: Path, payload: bytes, old: Any
) -> dict[str, Any]:
    return v13._source_prefix_state(path, payload, old)


def _ledger_by_id(v13: ModuleType, path: Path) -> dict[str, dict[str, Any]]:
    rows, _ = stable_jsonl_snapshot(path)
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        candidate_id = str(row["candidate_id"])
        if candidate_id in result:
            raise ValueError(f"Duplicate V14 score: {candidate_id}")
        if str(row["selection_action"]) not in FINAL_ACTIONS:
            raise ValueError(f"Invalid V14 score action: {candidate_id}")
        result[candidate_id] = row
    return result


def score_upstream(
    upstream: Mapping[str, Any],
    payload: Mapping[str, Any],
    macro: pd.DataFrame,
    evidence: Mapping[str, Any],
    config: Mapping[str, Any],
    now: pd.Timestamp,
) -> tuple[dict[str, Any] | None, str | None]:
    cutoff = utc_timestamp(upstream["scheduled_entry_time_utc"])
    xau_features = dict(upstream["numeric_features"])
    if str(upstream["feature_status"]) != "PASS":
        macro_values = {name: None for name in MACRO_FEATURES}
        feature_status = f"UPSTREAM_{upstream['feature_status']}"
    else:
        macro_values, feature_status = build_macro_features(
            cutoff,
            str(upstream["direction"]),
            macro,
            evidence,
            config,
        )
        if feature_status == "AWAITING_MACRO_SNAPSHOT":
            return None, feature_status
    values = {**xau_features, **macro_values}
    missing = set(payload["numeric_features"]).difference(values)
    if missing:
        raise ValueError(f"V14 feature contract is incomplete: {sorted(missing)}")
    if feature_status == "PASS":
        frame = pd.DataFrame(
            [
                {
                    "family_id": str(upstream["family_id"]),
                    **{name: values[name] for name in payload["numeric_features"]},
                }
            ]
        )
        model_score = float(payload["model"].predict(frame)[0])
        threshold = float(payload["pooled_threshold"])
        selected = model_score >= threshold
        action = "RETAIN" if selected else "VETO"
        reason = "APPLY_FROZEN_B123_EXPECTED_R_V14"
    else:
        model_score = None
        threshold = None
        selected = True
        action = "MODEL_ABSTAIN_RETAIN_ALL"
        reason = feature_status
    row = {
        "schema_version": "xauusd_macro_expected_r_prospective_v14_score",
        "candidate_id": str(upstream["candidate_id"]),
        "candidate_fact_sha256": str(upstream["candidate_fact_sha256"]),
        "source_id": str(upstream["source_id"]),
        "specialist_id": str(upstream["specialist_id"]),
        "family_id": str(upstream["family_id"]),
        "scheduled_entry_time_utc": utc_text(cutoff),
        "direction": str(upstream["direction"]),
        "feature_status": feature_status,
        "model_score": model_score,
        "threshold": threshold,
        "selected": selected,
        "selection_action": action,
        "selection_reason": reason,
        "numeric_features": {
            name: (
                None
                if values[name] is None or pd.isna(values[name])
                else float(values[name])
            )
            for name in payload["numeric_features"]
        },
        "upstream_v13_score_fact_sha256": canonical_hash(upstream, "__absent__"),
        "macro_evidence": dict(evidence),
        "recorded_at_utc": utc_text(now),
        "research_only": True,
        "python_serving_authorized": False,
        "ml_shadow_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
    }
    return row, None


def run_cycle(
    package_root: Path,
    config_path: Path,
    *,
    now: pd.Timestamp | None = None,
) -> dict[str, Any]:
    config = read_json(config_path)
    contract = verify_contract(package_root, config)
    current = pd.Timestamp.now(tz="UTC") if now is None else utc_timestamp(now)
    runtime = Path(str(config["runtime"]["directory"]))
    runtime.mkdir(parents=True, exist_ok=True)
    boundary = utc_timestamp(config["forward_start_inclusive_utc"])
    v13 = _load_v13(config)
    score_source = Path(str(config["upstream"]["v13_score_ledger"]))
    resolution_source = Path(str(config["upstream"]["v13_resolution_ledger"]))
    upstream_scores, score_bytes = _stable_rows(v13, score_source)
    resolutions, resolution_bytes = _stable_rows(v13, resolution_source)
    state_path = runtime / str(config["runtime"]["upstream_prefix_state"])
    old_state = read_json(state_path) if state_path.is_file() else {}
    old_sources = {str(row["path"]): row for row in old_state.get("sources", [])}
    prefix = [
        _prefix_record(
            v13,
            path,
            payload_bytes,
            old_sources.get(str(path.resolve()).replace("\\", "/")),
        )
        for path, payload_bytes in (
            (score_source, score_bytes),
            (resolution_source, resolution_bytes),
        )
    ]
    local_path = runtime / str(config["runtime"]["score_ledger"])
    local = _ledger_by_id(v13, local_path)
    macro, evidence, macro_wait = latest_macro_snapshot(config)
    model = load_model(config)
    waiting: dict[str, int] = {}
    new_rows: list[dict[str, Any]] = []
    candidate_facts: dict[str, str] = {}
    for upstream in upstream_scores:
        cutoff = utc_timestamp(upstream["scheduled_entry_time_utc"])
        if cutoff < boundary:
            continue
        candidate_id = str(upstream["candidate_id"])
        fact = str(upstream["candidate_fact_sha256"])
        if candidate_id in candidate_facts and candidate_facts[candidate_id] != fact:
            raise ValueError(f"V13 candidate fact changed: {candidate_id}")
        candidate_facts[candidate_id] = fact
        if candidate_id in local:
            if str(local[candidate_id]["candidate_fact_sha256"]) != fact:
                raise ValueError(f"Consumed V14 candidate changed: {candidate_id}")
            continue
        if current < boundary:
            continue
        if macro is None or evidence is None:
            reason = str(macro_wait)
            waiting[reason] = waiting.get(reason, 0) + 1
            continue
        row, reason = score_upstream(upstream, model, macro, evidence, config, current)
        if row is None:
            waiting[str(reason)] = waiting.get(str(reason), 0) + 1
        else:
            new_rows.append(row)
    v13.append_jsonl(local_path, new_rows)
    local = _ledger_by_id(v13, local_path)
    v13.atomic_write_json(
        state_path,
        {
            "schema_version": "xauusd_macro_expected_r_v14_upstream_prefix",
            "contract_sha256": str(contract["contract_sha256"]),
            "sources": prefix,
            "updated_at_utc": utc_text(current),
        },
    )
    resolution_by_id = {
        str(row["candidate_id"]): row
        for row in resolutions
        if utc_timestamp(row["scheduled_entry_time_utc"]) >= boundary
    }
    scored_ids = set(local)
    resolved_scored = scored_ids.intersection(resolution_by_id)
    status = {
        "schema_version": "xauusd_macro_expected_r_prospective_v14_status",
        "updated_at_utc": utc_text(current),
        "status": (
            "WAIT_BOUNDARY"
            if current < boundary
            else "ACTIVE_READ_ONLY_PROSPECTIVE_CONFIRMATION"
        ),
        "definition_contract_sha256": str(contract["contract_sha256"]),
        "forward_start_inclusive_utc": str(config["forward_start_inclusive_utc"]),
        "upstream_candidate_rows": len(candidate_facts),
        "score_rows": len(local),
        "resolved_scored_rows": len(resolved_scored),
        "model_veto_rows": sum(
            str(row["selection_action"]) == "VETO" for row in local.values()
        ),
        "model_abstain_rows": sum(
            str(row["selection_action"]) == "MODEL_ABSTAIN_RETAIN_ALL"
            for row in local.values()
        ),
        "waiting_reasons": waiting,
        "model_refit_after_boundary": False,
        "same_version_tuning_authorized": False,
        "prospective_research_scoring_authorized": True,
        "python_serving_authorized": False,
        "ml_shadow_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
    }
    v13.atomic_write_json(runtime / str(config["runtime"]["status"]), status)
    return status


def verify_score_replay(
    rows: Sequence[Mapping[str, Any]],
    payload: Mapping[str, Any],
) -> None:
    for row in rows:
        if str(row["selection_action"]) == "MODEL_ABSTAIN_RETAIN_ALL":
            if row.get("model_score") is not None or not bool(row["selected"]):
                raise ValueError(f"V14 abstention changed: {row['candidate_id']}")
            continue
        frame = pd.DataFrame(
            [
                {
                    "family_id": str(row["family_id"]),
                    **{
                        name: row["numeric_features"][name]
                        for name in payload["numeric_features"]
                    },
                }
            ]
        )
        score = float(payload["model"].predict(frame)[0])
        if not math.isclose(
            score, float(row["model_score"]), rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValueError(f"V14 score replay changed: {row['candidate_id']}")
        selected = score >= float(payload["pooled_threshold"])
        if selected != bool(row["selected"]):
            raise ValueError(f"V14 selection replay changed: {row['candidate_id']}")
