from __future__ import annotations

import hashlib
import importlib.util
from itertools import product
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT.parent


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE = _load_module(
    "calendar_session_execution_base",
    RESEARCH_ROOT / "cftc-options-positioning-mechanics-v1" / "src" / "campaign.py",
)

MECHANICS = (
    "UTC_HOUR_DIRECTIONAL_CARRY",
    "WEEKDAY_HOUR_DIRECTIONAL_CARRY",
    "PRIOR_SESSION_CONTINUATION",
    "PRIOR_SESSION_REVERSAL",
    "SESSION_RANGE_EXTREME_REVERSION",
)
WEEKDAY_SETS = ("ALL", "MWF", "TUTH")
SESSION_BOUNDARIES = (0, 6, 12, 18)
_MISSING = object()


def _space(**values: Iterable[Any]) -> list[dict[str, Any]]:
    names = tuple(values)
    return [
        dict(zip(names, combination, strict=True))
        for combination in product(*(values[name] for name in names))
    ]


def _execution_geometry() -> dict[str, tuple[Any, ...]]:
    return {
        "stop_atr": (0.75, 1.0, 1.5, 2.0),
        "target_r": (1.0, 1.5, 2.0, 3.0),
        "hold_hours": (2, 4, 8, 12),
    }


def parameter_space(mechanic: str) -> list[dict[str, Any]]:
    execution = _execution_geometry()
    if mechanic == "UTC_HOUR_DIRECTIONAL_CARRY":
        return _space(
            decision_hour=tuple(range(24)),
            fixed_direction=(-1, 1),
            weekday_set=WEEKDAY_SETS,
            **execution,
        )
    if mechanic == "WEEKDAY_HOUR_DIRECTIONAL_CARRY":
        return _space(
            decision_hour=tuple(range(0, 24, 2)),
            fixed_direction=(-1, 1),
            weekday=(0, 1, 2, 3, 4),
            **execution,
        )
    if mechanic in {"PRIOR_SESSION_CONTINUATION", "PRIOR_SESSION_REVERSAL"}:
        return _space(
            decision_hour=SESSION_BOUNDARIES,
            impulse_hours=(3, 6, 12, 24),
            impulse_min_atr=(0.25, 0.5, 0.75, 1.0),
            weekday_set=WEEKDAY_SETS,
            **execution,
        )
    if mechanic == "SESSION_RANGE_EXTREME_REVERSION":
        return _space(
            decision_hour=SESSION_BOUNDARIES,
            range_hours=(6, 12, 24, 48),
            edge_fraction=(0.10, 0.20, 0.30),
            range_min_atr=(0.5, 1.0, 1.5, 2.0),
            weekday_set=WEEKDAY_SETS,
            **execution,
        )
    raise KeyError(mechanic)


def prepare_features(h1: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    required = {
        "bar_start_utc",
        "bar_end_utc",
        "mid_open",
        "mid_high",
        "mid_low",
        "mid_close",
    }
    missing = sorted(required.difference(h1.columns))
    if missing:
        raise ValueError(f"H1 source is missing columns: {missing}")
    frame = h1.copy().sort_values("bar_end_utc", kind="mergesort").reset_index(drop=True)
    for column in ("bar_start_utc", "bar_end_utc"):
        frame[column] = pd.to_datetime(frame[column], utc=True, errors="raise")
    if frame["bar_end_utc"].duplicated().any():
        raise ValueError("Duplicate H1 decision timestamps")
    frame["atr14"] = BASE._atr(frame, int(config["features"]["h1_atr_period"]))
    scale = frame["atr14"].replace(0.0, np.nan)
    frame["body_atr"] = (frame["mid_close"] - frame["mid_open"]) / scale
    frame["hour_utc"] = frame["bar_end_utc"].dt.hour
    frame["weekday"] = frame["bar_end_utc"].dt.weekday
    frame["report_date"] = frame["bar_end_utc"].dt.floor("D")
    frame["available_utc"] = frame["bar_end_utc"]
    for hours in (3, 6, 12, 24):
        frame[f"impulse_{hours}_atr"] = (
            frame["mid_close"] - frame["mid_close"].shift(hours)
        ) / scale
    for hours in (6, 12, 24, 48):
        rolling_high = frame["mid_high"].rolling(hours, min_periods=hours).max()
        rolling_low = frame["mid_low"].rolling(hours, min_periods=hours).min()
        width = (rolling_high - rolling_low).replace(0.0, np.nan)
        frame[f"range_position_{hours}"] = (
            frame["mid_close"] - rolling_low
        ) / width
        frame[f"range_span_atr_{hours}"] = width / scale
    return frame


def _weekday_mask(frame: pd.DataFrame, value: str) -> pd.Series:
    if value == "ALL":
        return pd.Series(True, index=frame.index)
    if value == "MWF":
        return frame["weekday"].isin((0, 2, 4))
    if value == "TUTH":
        return frame["weekday"].isin((1, 3))
    raise KeyError(value)


def signal_mask_direction(
    frame: pd.DataFrame,
    mechanic: str,
    params: Mapping[str, Any],
) -> tuple[pd.Series, pd.Series]:
    decision = frame["hour_utc"].eq(int(params["decision_hour"]))
    if mechanic == "UTC_HOUR_DIRECTIONAL_CARRY":
        direction = pd.Series(int(params["fixed_direction"]), index=frame.index)
        mask = decision & _weekday_mask(frame, str(params["weekday_set"]))
    elif mechanic == "WEEKDAY_HOUR_DIRECTIONAL_CARRY":
        direction = pd.Series(int(params["fixed_direction"]), index=frame.index)
        mask = decision & frame["weekday"].eq(int(params["weekday"]))
    elif mechanic in {"PRIOR_SESSION_CONTINUATION", "PRIOR_SESSION_REVERSAL"}:
        impulse = frame[f"impulse_{int(params['impulse_hours'])}_atr"]
        sign = pd.Series(np.sign(impulse.fillna(0.0)).astype(int), index=frame.index)
        direction = -sign if mechanic == "PRIOR_SESSION_REVERSAL" else sign
        mask = (
            decision
            & _weekday_mask(frame, str(params["weekday_set"]))
            & impulse.abs().ge(float(params["impulse_min_atr"]))
            & direction.ne(0)
        )
    elif mechanic == "SESSION_RANGE_EXTREME_REVERSION":
        hours = int(params["range_hours"])
        position = frame[f"range_position_{hours}"]
        edge = float(params["edge_fraction"])
        direction = pd.Series(
            np.select(
                [position.le(edge), position.ge(1.0 - edge)],
                [1, -1],
                default=0,
            ).astype(int),
            index=frame.index,
        )
        mask = (
            decision
            & _weekday_mask(frame, str(params["weekday_set"]))
            & frame[f"range_span_atr_{hours}"].ge(float(params["range_min_atr"]))
            & direction.ne(0)
        )
    else:
        raise KeyError(mechanic)
    return mask.fillna(False), direction


def generate_manifest(
    frame: pd.DataFrame,
    discovery_start: pd.Timestamp,
    discovery_end: pd.Timestamp,
    attempts_before: int = 10093,
    policies_per_mechanic: int = 200,
    minimum_raw_signals: int = 180,
) -> pd.DataFrame:
    stage = frame["bar_end_utc"].ge(discovery_start) & frame["bar_end_utc"].lt(
        discovery_end
    )
    rows: list[dict[str, Any]] = []
    attempt = attempts_before
    for mechanic in MECHANICS:
        ranked = sorted(
            parameter_space(mechanic),
            key=lambda params: hashlib.sha256(
                f"{mechanic}|{json.dumps(params, sort_keys=True)}".encode("ascii")
            ).hexdigest(),
        )
        admitted = 0
        for params in ranked:
            mask, _ = signal_mask_direction(frame, mechanic, params)
            raw_signals = int((mask & stage).sum())
            if raw_signals < minimum_raw_signals:
                continue
            attempt += 1
            canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
            rows.append(
                {
                    "attempt_no": attempt,
                    "policy_id": hashlib.sha256(
                        f"{mechanic}|{canonical}".encode("ascii")
                    ).hexdigest()[:16],
                    "mechanic": mechanic,
                    "raw_discovery_signal_count": raw_signals,
                    "parameters_json": canonical,
                }
            )
            admitted += 1
            if admitted == policies_per_mechanic:
                break
        if admitted != policies_per_mechanic:
            raise ValueError(
                f"Only {admitted} coverage-eligible policies for {mechanic}; "
                f"required {policies_per_mechanic}"
            )
    manifest = pd.DataFrame(rows)
    expected = len(MECHANICS) * policies_per_mechanic
    if len(manifest) != expected:
        raise ValueError("Invalid calendar/session policy count")
    if manifest["policy_id"].duplicated().any():
        raise ValueError("Duplicate calendar/session policy IDs")
    return manifest


def select_policy_trades(
    frame: pd.DataFrame,
    arrays: Mapping[str, Any],
    policy: Any,
    config: Mapping[str, Any],
    stage_start: pd.Timestamp,
    stage_end: pd.Timestamp,
    outcome_cache: dict[tuple[Any, ...], Any],
) -> pd.DataFrame:
    params = json.loads(policy.parameters_json)
    mechanic = str(policy.mechanic)
    mask, direction = signal_mask_direction(frame, mechanic, params)
    stage = frame["bar_end_utc"].ge(stage_start) & frame["bar_end_utc"].lt(stage_end)
    indices = np.flatnonzero((mask & stage).to_numpy())
    selected: list[dict[str, Any]] = []
    position_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    execution = config["execution"]
    for index in indices:
        row = frame.iloc[int(index)]
        signal_time = pd.Timestamp(row["bar_end_utc"])
        signal_direction = int(direction.iat[int(index)])
        key = (
            int(signal_time.value),
            signal_direction,
            float(params["stop_atr"]),
            float(params["target_r"]),
            int(params["hold_hours"]),
        )
        outcome = outcome_cache.get(key, _MISSING)
        if outcome is _MISSING:
            outcome = BASE.simulate_trade(
                arrays,
                signal_time,
                float(row["atr14"]),
                signal_direction,
                params,
                execution,
                stage_end,
            )
            outcome_cache[key] = outcome
        if outcome is None:
            continue
        entry_time = outcome["entry_time"]
        if entry_time < position_until:
            continue
        day = entry_time.date()
        if daily_count.get(day, 0) >= int(
            execution["maximum_trades_per_policy_utc_day"]
        ):
            continue
        selected.append(
            {
                "attempt_no": int(policy.attempt_no),
                "policy_id": str(policy.policy_id),
                "mechanic": mechanic,
                "report_date": pd.Timestamp(row["report_date"]),
                "signal_time": signal_time,
                **outcome,
            }
        )
        position_until = outcome["exit_time"]
        daily_count[day] = daily_count.get(day, 0) + 1
    if not selected:
        return pd.DataFrame()
    return pd.DataFrame(selected).sort_values("entry_time", kind="mergesort").reset_index(
        drop=True
    )


def evaluate_policies(
    frame: pd.DataFrame,
    m5: pd.DataFrame,
    manifest: pd.DataFrame,
    config: Mapping[str, Any],
    stage: str,
) -> tuple[pd.DataFrame, dict[tuple[Any, ...], Any]]:
    start, end = map(pd.Timestamp, config["windows"][stage])
    arrays = BASE.execution_arrays(m5)
    cache: dict[tuple[Any, ...], Any] = {}
    rows: list[dict[str, Any]] = []
    for policy in manifest.itertuples(index=False):
        trades = select_policy_trades(frame, arrays, policy, config, start, end, cache)
        values = BASE.summarize(
            trades,
            frame,
            start,
            end,
            config["segments"][stage],
            int(config["gates"][stage]["top_winners_removed"]),
        )
        rows.append(
            {
                "attempt_no": int(policy.attempt_no),
                "policy_id": str(policy.policy_id),
                "mechanic": str(policy.mechanic),
                "raw_discovery_signal_count": int(policy.raw_discovery_signal_count),
                "parameters_json": str(policy.parameters_json),
                **values,
            }
        )
    metrics = pd.DataFrame(rows)
    metrics["fdr_qvalue"] = BASE.benjamini_hochberg(metrics["block_pvalue"])
    checks_list: list[dict[str, bool]] = []
    passes: list[bool] = []
    for row in metrics.to_dict(orient="records"):
        checks = BASE.gate_checks(row, config["gates"][stage])
        checks_list.append(checks)
        passes.append(all(checks.values()))
    metrics["gate_checks_json"] = [
        json.dumps(checks, sort_keys=True, separators=(",", ":"))
        for checks in checks_list
    ]
    metrics["gate_pass"] = passes
    return metrics, cache


def select_advancers(metrics: pd.DataFrame, gate: Mapping[str, Any]) -> pd.DataFrame:
    return BASE.select_advancers(metrics, gate)


def selected_trade_ledger(
    frame: pd.DataFrame,
    m5: pd.DataFrame,
    selected_manifest: pd.DataFrame,
    config: Mapping[str, Any],
    stage: str,
    cache: dict[tuple[Any, ...], Any] | None = None,
) -> pd.DataFrame:
    if selected_manifest.empty:
        return pd.DataFrame()
    start, end = map(pd.Timestamp, config["windows"][stage])
    arrays = BASE.execution_arrays(m5)
    outcome_cache = cache if cache is not None else {}
    frames: list[pd.DataFrame] = []
    for policy in selected_manifest.itertuples(index=False):
        trades = select_policy_trades(
            frame, arrays, policy, config, start, end, outcome_cache
        )
        if not trades.empty:
            frames.append(trades.assign(stage=stage))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
