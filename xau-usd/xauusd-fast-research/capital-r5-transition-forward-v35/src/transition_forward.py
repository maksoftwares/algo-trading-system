from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import sys
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


TEXT_DEPENDENCY_SUFFIXES = {".csv", ".json", ".md", ".py", ".txt"}
OFFICIAL_INSTRUMENTS = {
    "DOLLARIDXUSD": {
        "source_code": "DOLLAR.IDX-USD",
        "pip_size": 0.01,
        "price_scale": 3,
    },
    "USTBONDTRUSD": {
        "source_code": "USTBOND.TR-USD",
        "pip_size": 0.01,
        "price_scale": 3,
    },
}
COMPONENT_ATTEMPTS = (23925, 24877, 24995, 25048)
ROUTER_ATTEMPT = 27135
CANDIDATE_COLUMNS = (
    "candidate_id",
    "origin_attempt",
    "origin_variant_id",
    "regime_owner",
    "mechanic",
    "geometry_id",
    "signal_time",
    "scheduled_entry_time",
    "direction_sign",
    "direction",
    "signal_atr",
    "stop_atr",
    "target_r",
    "hold_hours",
    "parameters_json",
)


@dataclass(frozen=True)
class FrozenR5:
    repo_root: Path
    package_config: dict[str, Any]
    macro_config: dict[str, Any]
    v9_config: dict[str, Any]
    router_config: dict[str, Any]
    dependency_sha256: str
    data_module: Any
    foundation_module: Any
    macro_campaign: Any
    residual_campaign: Any
    confirmation_module: Any
    router_module: Any
    dukascopy_foundation: Any
    component_sources: tuple[tuple[Any, Any, Mapping[str, Any]], ...]
    router_policy: Any


def _load_module(name: str, path: Path) -> Any:
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
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dependency_sha256(repo_root: Path, paths: Iterable[str]) -> str:
    rows = []
    for relative in sorted(str(value).replace("\\", "/") for value in paths):
        path = repo_root / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        content = path.read_bytes()
        if path.suffix.lower() in TEXT_DEPENDENCY_SUFFIXES:
            content = content.replace(b"\r\n", b"\n")
        rows.append(f"{relative}|{hashlib.sha256(content).hexdigest()}")
    return hashlib.sha256("\n".join(rows).encode("ascii")).hexdigest()


def _config(repo_root: Path, relative: str) -> dict[str, Any]:
    return json.loads((repo_root / relative).read_text(encoding="utf-8"))


def load_frozen(repo_root: Path, package_root: Path) -> FrozenR5:
    package_config = json.loads(
        (
            package_root
            / "config"
            / "capital_r5_transition_forward_v35.json"
        ).read_text(encoding="utf-8")
    )
    source = package_config["source"]
    macro_config = _config(repo_root, source["macro_config"])
    v9_config = _config(repo_root, source["v9_config"])
    router_config = _config(repo_root, source["router_config"])
    research_root = repo_root / "xau-usd" / "xauusd-fast-research"
    macro_root = research_root / "macro-regime-routing-v1"

    macro_campaign = _load_module(
        "campaign", macro_root / "src" / "campaign.py"
    )
    foundation_module = _load_module(
        "capital_r5_v35_foundation", macro_root / "src" / "foundation.py"
    )
    residual_campaign = _load_module(
        "capital_r5_v35_residual",
        research_root
        / "crossasset-residual-regime-campaign-v6"
        / "src"
        / "campaign.py",
    )
    confirmation_module = _load_module(
        "capital_r5_v35_confirmation",
        research_root
        / "transition-weighted-rawtick-confirmation-v9"
        / "src"
        / "confirmation.py",
    )
    router_module = _load_module(
        "capital_r5_v35_router",
        research_root
        / "transition-online-component-router-v11"
        / "src"
        / "router.py",
    )
    data_module = foundation_module.DATA
    foundation_path = (
        repo_root
        / "multi-asset"
        / "data-foundation"
        / "dukascopy-ticks-v1"
        / "src"
        / "dukascopy_tick_foundation"
        / "foundation.py"
    )
    dukascopy_foundation = _load_module(
        "capital_r5_v35_dukascopy_foundation", foundation_path
    )
    dukascopy_foundation.INSTRUMENTS.update(OFFICIAL_INSTRUMENTS)

    macro_manifest = pd.read_csv(repo_root / source["macro_manifest"])
    residual_manifest = pd.read_csv(repo_root / source["residual_manifest"])
    component_sources: list[tuple[Any, Any, Mapping[str, Any]]] = []
    for attempt in COMPONENT_ATTEMPTS:
        manifest = macro_manifest if attempt == 23925 else residual_manifest
        selected = manifest.loc[manifest["attempt_no"].eq(attempt)]
        if len(selected) != 1:
            raise ValueError(f"R5 component source is not unique: {attempt}")
        campaign = macro_campaign if attempt == 23925 else residual_campaign
        config = macro_config if attempt == 23925 else _config(
            repo_root, source["residual_config"]
        )
        component_sources.append(
            (next(selected.itertuples(index=False)), campaign, config)
        )

    router_manifest = pd.read_csv(repo_root / source["router_manifest"])
    selected_policy = router_manifest.loc[
        router_manifest["attempt_no"].eq(ROUTER_ATTEMPT)
    ]
    if len(selected_policy) != 1:
        raise ValueError("R5 router policy 27135 is not unique")
    policy_row = next(selected_policy.itertuples(index=False))
    router_policy = SimpleNamespace(
        **policy_row._asdict(),
        tie_priority=router_config["portfolio"]["tie_priority"],
    )
    return FrozenR5(
        repo_root=repo_root,
        package_config=package_config,
        macro_config=macro_config,
        v9_config=v9_config,
        router_config=router_config,
        dependency_sha256=dependency_sha256(
            repo_root, package_config["contract_scope"]
        ),
        data_module=data_module,
        foundation_module=foundation_module,
        macro_campaign=macro_campaign,
        residual_campaign=residual_campaign,
        confirmation_module=confirmation_module,
        router_module=router_module,
        dukascopy_foundation=dukascopy_foundation,
        component_sources=tuple(component_sources),
        router_policy=router_policy,
    )


def completed_hours(start: datetime, end_exclusive: datetime) -> list[datetime]:
    cursor = start.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
    end = end_exclusive.astimezone(UTC).replace(
        minute=0, second=0, microsecond=0
    )
    rows = []
    while cursor < end:
        rows.append(cursor)
        cursor += timedelta(hours=1)
    return rows


def acquire_macro_hours(
    frozen: FrozenR5,
    *,
    start: datetime,
    end_exclusive: datetime,
    concurrency: int = 4,
    missing_only: bool = False,
) -> list[dict[str, Any]]:
    if not 1 <= concurrency <= 4:
        raise ValueError("Dukascopy concurrency must be between one and four")
    root = Path(frozen.package_config["source"]["dukascopy_storage_root"])
    jobs = [
        (symbol, hour)
        for hour in completed_hours(start, end_exclusive)
        for symbol in OFFICIAL_INSTRUMENTS
        if not missing_only
        or not frozen.dukascopy_foundation.raw_hour_path(root, symbol, hour).is_file()
    ]
    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(
                frozen.dukascopy_foundation.acquire_hour,
                root,
                symbol,
                hour,
            ): (symbol, hour)
            for symbol, hour in jobs
        }
        for future in as_completed(futures):
            rows.append(future.result())
    rows.sort(key=lambda row: (row["hour_utc"], row["symbol"]))
    failures = [row for row in rows if row["status"] == "FAILED_AFTER_ONE_RETRY"]
    if failures:
        raise RuntimeError(f"Official Dukascopy macro acquisition failed: {failures}")
    return rows


def _basis_frame(
    ticks: list[Any], foundation: Any, symbol: str, basis: str
) -> pd.DataFrame:
    frame = pd.DataFrame(foundation.aggregate_bars(ticks, "M5", basis))
    if frame.empty:
        return pd.DataFrame(columns=["timestamp_ms"])
    prefix = f"{symbol.lower()}_{basis.lower()}_"
    return frame.rename(
        columns={
            column: f"{prefix}{column}"
            for column in frame.columns
            if column != "timestamp_ms"
        }
    )


def build_macro_extension_m5(
    frozen: FrozenR5,
    *,
    start_inclusive: pd.Timestamp,
    end_exclusive: pd.Timestamp,
) -> pd.DataFrame:
    storage = Path(frozen.package_config["source"]["dukascopy_storage_root"])
    symbol_frames = []
    for symbol in OFFICIAL_INSTRUMENTS:
        ticks: list[Any] = []
        first = pd.Timestamp(start_inclusive).to_pydatetime()
        final = pd.Timestamp(end_exclusive).to_pydatetime()
        first_ms = int(pd.Timestamp(start_inclusive).value // 1_000_000)
        final_ms = int(pd.Timestamp(end_exclusive).value // 1_000_000)
        cursor = datetime(first.year, first.month, 1, tzinfo=UTC)
        while cursor < final:
            for path, raw in frozen.dukascopy_foundation.iter_raw_month(
                storage, symbol, cursor.year, cursor.month
            ):
                decoded = frozen.dukascopy_foundation.decode_payload(
                    raw, symbol, path.name
                )
                ticks.extend(
                    tick
                    for tick in decoded
                    if first_ms <= tick.timestamp_ms < final_ms
                )
            cursor = datetime(
                cursor.year + int(cursor.month == 12),
                1 if cursor.month == 12 else cursor.month + 1,
                1,
                tzinfo=UTC,
            )
        ticks.sort(key=lambda tick: (tick.timestamp_ms, tick.source_file_id, tick.source_row_index))
        bases = [
            _basis_frame(ticks, frozen.dukascopy_foundation, symbol, basis)
            for basis in ("Bid", "Ask", "Mid")
        ]
        merged = bases[0]
        for basis in bases[1:]:
            merged = merged.merge(
                basis, on="timestamp_ms", how="inner", validate="one_to_one"
            )
        symbol_frames.append(merged)
    combined = symbol_frames[0].merge(
        symbol_frames[1], on="timestamp_ms", how="outer", validate="one_to_one"
    )
    combined = combined.sort_values("timestamp_ms", kind="mergesort").reset_index(
        drop=True
    )
    combined.insert(
        0,
        "timestamp_utc",
        pd.to_datetime(combined["timestamp_ms"], unit="ms", utc=True),
    )
    for symbol in OFFICIAL_INSTRUMENTS:
        combined[f"{symbol.lower()}_available"] = combined[
            f"{symbol.lower()}_mid_close"
        ].notna()
    return combined


def build_macro_m15(
    frozen: FrozenR5,
    *,
    extension_start: pd.Timestamp,
    end_exclusive: pd.Timestamp,
) -> pd.DataFrame:
    root = Path(frozen.package_config["source"]["dukascopy_storage_root"])
    cache = root / frozen.macro_config["macro_source"]["feature_cache"]
    historical = pd.read_parquet(cache)
    historical["timestamp_utc"] = pd.to_datetime(
        historical["timestamp_utc"], utc=True
    )
    extension = build_macro_extension_m5(
        frozen,
        start_inclusive=extension_start,
        end_exclusive=end_exclusive,
    )
    combined = pd.concat([historical, extension], ignore_index=True)
    combined = (
        combined.sort_values("timestamp_utc", kind="mergesort")
        .drop_duplicates("timestamp_utc", keep="last")
        .reset_index(drop=True)
    )
    dollar = frozen.foundation_module.MACRO_DATA._aggregate_symbol(  # noqa: SLF001
        combined, "DOLLARIDXUSD"
    )
    bond = frozen.foundation_module.MACRO_DATA._aggregate_symbol(  # noqa: SLF001
        combined, "USTBONDTRUSD"
    )
    return dollar.merge(
        bond, on="timestamp_utc", how="inner", validate="one_to_one"
    ).sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)


def build_decision_frames(
    gold_m5: pd.DataFrame, macro_m15: pd.DataFrame, frozen: FrozenR5
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    m15 = frozen.data_module.aggregate_complete_bars(gold_m5, 15, "M15")
    h4 = frozen.data_module.aggregate_complete_bars(gold_m5, 240, "H4")
    execution = frozen.foundation_module.FEATURES.prepare_features(
        m15,
        h4,
        frozen.macro_config,
        frozen.foundation_module.ADAPTIVE,
        frozen.foundation_module.REGIMES,
    )
    macro_decisions = frozen.macro_campaign.enrich_frame(
        execution, macro_m15, frozen.macro_config
    )
    residual_decisions = frozen.residual_campaign.enrich_residual_features(
        macro_decisions,
        _config(
            frozen.repo_root,
            frozen.package_config["source"]["residual_config"],
        ),
    )
    return execution, macro_decisions, residual_decisions


def _candidate_id(origin_attempt: int, signal_time: pd.Timestamp) -> str:
    payload = f"{origin_attempt}|{signal_time.isoformat()}".encode("ascii")
    return hashlib.sha256(payload).hexdigest()[:24]


def generate_forward_component_candidates(
    macro_decisions: pd.DataFrame,
    residual_decisions: pd.DataFrame,
    frozen: FrozenR5,
    *,
    start_inclusive: pd.Timestamp,
    end_inclusive: pd.Timestamp,
) -> pd.DataFrame:
    rows = []
    for source_row, campaign, source_config in frozen.component_sources:
        decisions = macro_decisions if int(source_row.attempt_no) == 23925 else residual_decisions
        params = json.loads(str(source_row.parameters_json))
        mask, direction = campaign.signal_mask_direction(
            decisions, str(source_row.mechanic), params
        )
        mask = (
            mask
            & decisions["timestamp_utc"].ge(start_inclusive)
            & decisions["timestamp_utc"].le(end_inclusive)
        )
        geometry = source_config["geometries"][str(source_row.regime_owner)][
            str(source_row.geometry_id)
        ]
        for index in np.flatnonzero(mask.to_numpy(dtype=bool)):
            signal = decisions.iloc[int(index)]
            signal_time = pd.Timestamp(signal["timestamp_utc"])
            sign = int(direction.iat[int(index)])
            attempt = int(source_row.attempt_no)
            rows.append(
                {
                    "candidate_id": _candidate_id(attempt, signal_time),
                    "origin_attempt": attempt,
                    "origin_variant_id": str(source_row.variant_id),
                    "regime_owner": str(source_row.regime_owner),
                    "mechanic": str(source_row.mechanic),
                    "geometry_id": str(source_row.geometry_id),
                    "signal_time": signal_time,
                    "scheduled_entry_time": signal_time,
                    "direction_sign": sign,
                    "direction": "LONG" if sign > 0 else "SHORT",
                    "signal_atr": float(signal["atr14"]),
                    "stop_atr": float(geometry["stop_atr"]),
                    "target_r": float(geometry["target_r"]),
                    "hold_hours": float(geometry["maximum_hold_hours"]),
                    "parameters_json": str(source_row.parameters_json),
                }
            )
    if not rows:
        return pd.DataFrame(columns=CANDIDATE_COLUMNS)
    result = pd.DataFrame(rows).sort_values(
        ["scheduled_entry_time", "origin_attempt"], kind="mergesort"
    )
    if result["candidate_id"].duplicated().any():
        raise ValueError("R5 forward component candidate IDs are not unique")
    return result.reset_index(drop=True)


def route_forward_candidates(
    candidates: pd.DataFrame,
    component_history: pd.DataFrame,
    frozen: FrozenR5,
) -> pd.DataFrame:
    if candidates.empty:
        return candidates.copy()
    history = component_history.copy()
    history["exit_time"] = pd.to_datetime(history["exit_time"], utc=True)
    params = json.loads(str(frozen.router_policy.parameters_json))
    lookback = int(params["lookback_days"])
    components = list(COMPONENT_ATTEMPTS)
    base_weights = {
        int(key): float(value)
        for key, value in frozen.router_config["portfolio"]["base_weights"].items()
    }
    rows = []
    for candidate in candidates.itertuples(index=False):
        entry = pd.Timestamp(candidate.scheduled_entry_time)
        entry_ns = int(entry.value)
        cache = {}
        for component in components:
            values = history.loc[
                history["attempt_no"].eq(component)
                & history["exit_time"].lt(entry)
                & history["exit_time"].ge(entry - pd.Timedelta(days=lookback)),
                "stress_net_r",
            ].to_numpy(dtype=float)
            cache[(entry_ns, component, lookback)] = frozen.router_module._stats(  # noqa: SLF001
                values
            )
        multiplier, reason, stats = frozen.router_module.route_multiplier(
            int(candidate.origin_attempt),
            entry_ns,
            str(frozen.router_policy.mechanic),
            params,
            components,
            cache,
        )
        row = candidate._asdict()
        row.update(
            {
                "router_attempt": ROUTER_ATTEMPT,
                "router_id": str(frozen.router_policy.router_id),
                "router_mechanic": str(frozen.router_policy.mechanic),
                "shadow_count": int(stats.count),
                "shadow_mean_r": float(stats.mean_r),
                "shadow_profit_factor": float(stats.profit_factor),
                "shadow_drawdown_r": float(stats.drawdown_r),
                "route_multiplier": float(multiplier),
                "route_reason": str(reason),
                "risk_weight": base_weights[int(candidate.origin_attempt)]
                * float(multiplier),
                "economic_outcome_opened": False,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _canonical_sha(frame: pd.DataFrame, columns: Iterable[str]) -> str:
    selected = frame.loc[:, list(columns)].copy()
    for column in selected.columns:
        if isinstance(selected[column].dtype, pd.DatetimeTZDtype):
            selected[column] = selected[column].map(
                lambda value: pd.Timestamp(value).isoformat()
            )
    payload = selected.to_json(orient="records", double_precision=15)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_historical_candidates(frozen: FrozenR5) -> pd.DataFrame:
    foundation = frozen.foundation_module.load_foundation(frozen.macro_config)
    frames = []
    residual_frame = frozen.residual_campaign.enrich_residual_features(
        foundation.decisions,
        _config(
            frozen.repo_root,
            frozen.package_config["source"]["residual_config"],
        ),
    )
    for source_row, campaign, source_config in frozen.component_sources:
        decisions = foundation.decisions if int(source_row.attempt_no) == 23925 else residual_frame
        frames.append(
            frozen.confirmation_module.component_candidates(
                decisions,
                foundation.execution_frame,
                source_row,
                campaign,
                source_config,
                frozen.v9_config,
            )
        )
    return frozen.confirmation_module.combine_candidates(frames)


def verify_historical_parity(frozen: FrozenR5, repo_root: Path) -> dict[str, Any]:
    generated_candidates = build_historical_candidates(frozen)
    candidate_artifact = pd.read_parquet(
        repo_root / frozen.package_config["source"]["v9_candidates"]
    )
    generated_candidate_sha = _canonical_sha(
        generated_candidates, CANDIDATE_COLUMNS
    )
    artifact_candidate_sha = _canonical_sha(candidate_artifact, CANDIDATE_COLUMNS)
    if generated_candidate_sha != artifact_candidate_sha:
        raise ValueError("R5 V9 historical candidate parity failed")

    component_trades = pd.read_parquet(
        repo_root / frozen.package_config["source"]["v9_component_trades"]
    )
    generated_selected = frozen.router_module.build_routed_trades(
        component_trades,
        frozen.router_policy,
        {
            int(key): float(value)
            for key, value in frozen.router_config["portfolio"]["base_weights"].items()
        },
        int(frozen.router_config["portfolio"]["maximum_trades_per_utc_day"]),
    )
    selected_artifact = pd.read_parquet(
        repo_root / frozen.package_config["source"]["v11_selected_trades"]
    )
    selected_artifact = selected_artifact.loc[
        selected_artifact["attempt_no"].eq(ROUTER_ATTEMPT)
    ].reset_index(drop=True)
    selected_columns = tuple(generated_selected.columns)
    generated_selected_sha = _canonical_sha(generated_selected, selected_columns)
    artifact_selected_sha = _canonical_sha(selected_artifact, selected_columns)
    if generated_selected_sha != artifact_selected_sha:
        raise ValueError("R5 V11 selected-trade parity failed")
    return {
        "component_attempts": list(COMPONENT_ATTEMPTS),
        "router_attempt": ROUTER_ATTEMPT,
        "candidate_rows": int(len(generated_candidates)),
        "candidate_canonical_sha256": generated_candidate_sha,
        "candidate_artifact_canonical_sha256": artifact_candidate_sha,
        "selected_trade_rows": int(len(generated_selected)),
        "selected_trade_canonical_sha256": generated_selected_sha,
        "selected_trade_artifact_canonical_sha256": artifact_selected_sha,
    }
