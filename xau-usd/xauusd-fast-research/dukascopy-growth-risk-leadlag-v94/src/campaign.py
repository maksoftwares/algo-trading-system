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
PREFIXES = ("spx", "copper", "usdcnh")
MECHANICS = (
    "M5_RISK_PULSE_CATCHUP",
    "M5_GROWTH_PULSE_CATCHUP",
    "M5_BREADTH_CONTINUATION",
    "M5_PULSE_EXHAUSTION_FADE",
    "M5_SEQUENCE_BREAKOUT",
)
SESSIONS = ("ALL", "ASIA", "LONDON", "NY")
EXECUTION_PROFILES = (
    (0.8, 1.0, 1),
    (0.8, 1.25, 1),
    (1.0, 1.25, 1),
    (1.0, 1.5, 2),
    (1.2, 1.5, 2),
    (1.2, 2.0, 2),
    (1.5, 1.5, 4),
    (1.5, 2.0, 4),
)
_MISSING = object()


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


V89 = _load_module(
    "dukascopy_growth_risk_v94_v89_metrics",
    RESEARCH_ROOT / "cboe-gvz-routed-intraday-v89" / "src" / "campaign.py",
)
BASE = V89.BASE
summarize = V89.summarize
benjamini_hochberg = V89.benjamini_hochberg
gate_checks = V89.gate_checks
select_advancers = V89.select_advancers


def _space(**values: Iterable[Any]) -> list[dict[str, Any]]:
    names = tuple(values)
    return [
        dict(zip(names, combination, strict=True))
        for combination in product(*(values[name] for name in names))
    ]


def parameter_space(mechanic: str) -> list[dict[str, Any]]:
    common = _space(
        source_horizon=(1, 3, 6, 12),
        source_lookback=(288, 576, 1152),
        source_threshold_z=(0.6, 0.9, 1.2, 1.5, 1.8),
        minimum_tick_count=(5, 20),
        maximum_source_staleness_minutes=(1, 3, 5),
        session=SESSIONS,
    )
    def combine(specific: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = []
        for base, detail, (stop, target, hold) in product(
            common, specific, EXECUTION_PROFILES
        ):
            rows.append(
                {
                    **base,
                    **detail,
                    "stop_atr": stop,
                    "target_r": target,
                    "hold_hours": hold,
                }
            )
        return rows

    if mechanic in {"M5_RISK_PULSE_CATCHUP", "M5_GROWTH_PULSE_CATCHUP"}:
        return combine(_space(
            maximum_response_atr=(0.0, 0.25, 0.50, 0.75),
            minimum_opposite_response_atr=(0.0,),
            minimum_agreeing_legs=(1,),
            sequence_multiplier=(2,),
            channel_bars=(6,),
            breakout_buffer_atr=(0.0,),
        ))
    if mechanic == "M5_BREADTH_CONTINUATION":
        return combine(_space(
            maximum_response_atr=(0.25, 0.50, 0.75, 1.0),
            minimum_opposite_response_atr=(0.0,),
            minimum_agreeing_legs=(2, 3),
            sequence_multiplier=(2,),
            channel_bars=(6,),
            breakout_buffer_atr=(0.0,),
        ))
    if mechanic == "M5_PULSE_EXHAUSTION_FADE":
        return combine(_space(
            maximum_response_atr=(10.0,),
            minimum_opposite_response_atr=(0.50, 0.75, 1.0, 1.5),
            minimum_agreeing_legs=(1,),
            sequence_multiplier=(2,),
            channel_bars=(6,),
            breakout_buffer_atr=(0.0,),
        ))
    if mechanic == "M5_SEQUENCE_BREAKOUT":
        return combine(_space(
            maximum_response_atr=(10.0,),
            minimum_opposite_response_atr=(0.0,),
            minimum_agreeing_legs=(1,),
            sequence_multiplier=(2,),
            channel_bars=(3, 6, 12),
            breakout_buffer_atr=(0.0, 0.05, 0.10),
        ))
    raise KeyError(mechanic)


def _causal_z(values: pd.Series, lookback: int) -> pd.Series:
    observed = values.dropna()
    prior = observed.shift(1).rolling(lookback, min_periods=lookback)
    scored = (observed - prior.mean()) / prior.std(ddof=0).replace(0.0, np.nan)
    return scored.reindex(values.index)


def _atr(frame: pd.DataFrame, period: int) -> pd.Series:
    previous = frame["mid_close"].shift(1)
    true_range = pd.concat(
        [
            frame["mid_high"] - frame["mid_low"],
            (frame["mid_high"] - previous).abs(),
            (frame["mid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


HORIZON_NAMES = {1: "5m", 3: "15m", 6: "30m", 12: "60m"}


def prepare_source_m5(
    source_m5: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    required = {"bar_open_timestamp_ms"}
    for prefix in PREFIXES:
        required.update(
            {
                f"{prefix}_available_timestamp_ms",
                f"{prefix}_source_last_timestamp_ms",
                f"{prefix}_tick_count",
                *(f"{prefix}_return_{name}" for name in HORIZON_NAMES.values()),
            }
        )
    missing = sorted(required.difference(source_m5.columns))
    if missing:
        raise ValueError(f"Growth-risk M5 source is missing columns: {missing}")
    result = source_m5.copy().sort_values(
        "bar_open_timestamp_ms", kind="mergesort"
    ).reset_index(drop=True)
    result["bar_open_utc"] = pd.to_datetime(
        result["bar_open_timestamp_ms"], unit="ms", utc=True
    )
    result["bar_end_utc"] = result["bar_open_utc"] + pd.Timedelta(minutes=5)
    result["hour_utc"] = result["bar_end_utc"].dt.hour
    result["session_slot"] = np.select(
        [
            result["hour_utc"].ge(1) & result["hour_utc"].lt(7),
            result["hour_utc"].ge(7) & result["hour_utc"].lt(13),
            result["hour_utc"].ge(13) & result["hour_utc"].lt(19),
        ],
        ["ASIA", "LONDON", "NY"],
        default="OUTSIDE",
    )
    for prefix in PREFIXES:
        available = pd.to_datetime(
            result[f"{prefix}_available_timestamp_ms"], unit="ms", utc=True
        )
        source_last = pd.to_datetime(
            result[f"{prefix}_source_last_timestamp_ms"], unit="ms", utc=True
        )
        result[f"{prefix}_staleness_minutes"] = (
            result["bar_end_utc"] - source_last
        ).dt.total_seconds() / 60.0
        observed = available.notna()
        if not available.loc[observed].eq(result.loc[observed, "bar_end_utc"]).all():
            raise ValueError(f"Noncausal {prefix} M5 availability boundary")
        if (source_last.loc[observed] >= available.loc[observed]).any():
            raise ValueError(f"Noncausal {prefix} source tick availability")

    lookbacks = tuple(map(int, config["features"]["source_normalization_lookbacks"]))
    for horizon, name in HORIZON_NAMES.items():
        for lookback in lookbacks:
            z_values = {}
            for prefix in PREFIXES:
                column = f"{prefix}_z_{horizon}b_{lookback}"
                result[column] = _causal_z(
                    result[f"{prefix}_return_{name}"], lookback
                )
                z_values[prefix] = result[column]
            risk_legs = pd.concat(
                [-z_values["spx"], -z_values["copper"], z_values["usdcnh"]],
                axis=1,
            )
            growth_legs = pd.concat(
                [z_values["copper"], -z_values["usdcnh"]], axis=1
            )
            risk_score = risk_legs.mean(axis=1, skipna=False)
            growth_score = growth_legs.mean(axis=1, skipna=False)
            result[f"risk_score_{horizon}b_{lookback}"] = risk_score
            result[f"growth_score_{horizon}b_{lookback}"] = growth_score
            risk_direction = np.sign(risk_score)
            growth_direction = np.sign(growth_score)
            result[f"risk_agreeing_legs_{horizon}b_{lookback}"] = (
                np.sign(risk_legs).eq(risk_direction, axis=0).sum(axis=1)
            )
            result[f"growth_agreeing_legs_{horizon}b_{lookback}"] = (
                np.sign(growth_legs).eq(growth_direction, axis=0).sum(axis=1)
            )
    return result


def prepare_features(
    m5: pd.DataFrame, source_m5: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    required = {
        "bar_start_utc",
        "bar_end_utc",
        "mid_open",
        "mid_high",
        "mid_low",
        "mid_close",
    }
    missing = sorted(required.difference(m5.columns))
    if missing:
        raise ValueError(f"XAU M5 source is missing columns: {missing}")
    frame = m5.copy().sort_values("bar_end_utc", kind="mergesort").reset_index(drop=True)
    frame["atr_m5"] = _atr(frame, int(config["features"]["m5_atr_period"]))
    scale = frame["atr_m5"].replace(0.0, np.nan)
    frame["body_atr"] = (frame["mid_close"] - frame["mid_open"]) / scale
    for bars in HORIZON_NAMES:
        contiguous = frame["bar_end_utc"].diff(bars).eq(
            pd.Timedelta(minutes=5 * bars)
        )
        frame[f"impulse_{bars}_atr"] = (
            (frame["mid_close"] - frame["mid_close"].shift(bars)) / scale
        ).where(contiguous)
    for bars in (3, 6, 12):
        contiguous = frame["bar_end_utc"].diff(bars).eq(
            pd.Timedelta(minutes=5 * bars)
        )
        frame[f"prior_high_{bars}"] = (
            frame["mid_high"].shift(1).rolling(bars, min_periods=bars).max()
        ).where(contiguous)
        frame[f"prior_low_{bars}"] = (
            frame["mid_low"].shift(1).rolling(bars, min_periods=bars).min()
        ).where(contiguous)
    prepared_source = prepare_source_m5(source_m5, config)
    return frame.merge(
        prepared_source.drop(columns=["bar_open_utc"]),
        on="bar_end_utc",
        how="left",
        validate="one_to_one",
    )


def _session_mask(frame: pd.DataFrame, session: str) -> pd.Series:
    if session == "ALL":
        return frame["session_slot"].isin(("ASIA", "LONDON", "NY"))
    if session not in {"ASIA", "LONDON", "NY"}:
        raise KeyError(session)
    return frame["session_slot"].eq(session)


def source_event_mask_direction(
    frame: pd.DataFrame, mechanic: str, params: Mapping[str, Any]
) -> tuple[pd.Series, pd.Series]:
    horizon = int(params["source_horizon"])
    lookback = int(params["source_lookback"])
    threshold = float(params["source_threshold_z"])
    score_name = (
        "growth_score" if mechanic == "M5_GROWTH_PULSE_CATCHUP" else "risk_score"
    )
    score = frame[f"{score_name}_{horizon}b_{lookback}"]
    event_strength = score.abs()
    direction = pd.Series(
        np.sign(score.fillna(0.0)).astype(int), index=frame.index
    )
    mask = event_strength.ge(threshold) & direction.ne(0)
    agreement_name = "growth_agreeing_legs" if score_name == "growth_score" else "risk_agreeing_legs"
    mask &= frame[f"{agreement_name}_{horizon}b_{lookback}"].ge(
        int(params["minimum_agreeing_legs"])
    )
    required_prefixes = (
        ("copper", "usdcnh")
        if mechanic == "M5_GROWTH_PULSE_CATCHUP"
        else PREFIXES
    )
    for prefix in required_prefixes:
        mask &= frame[f"{prefix}_tick_count"].ge(int(params["minimum_tick_count"]))
        mask &= frame[f"{prefix}_staleness_minutes"].le(
            float(params["maximum_source_staleness_minutes"])
        )
    mask &= _session_mask(frame, str(params["session"]))
    return mask.fillna(False), direction


def signal_mask_direction(
    frame: pd.DataFrame, mechanic: str, params: Mapping[str, Any]
) -> tuple[pd.Series, pd.Series]:
    mask, source_direction = source_event_mask_direction(frame, mechanic, params)
    horizon = int(params["source_horizon"])
    response = frame[f"impulse_{horizon}_atr"]
    maximum_response = float(params["maximum_response_atr"])
    if mechanic in {"M5_RISK_PULSE_CATCHUP", "M5_GROWTH_PULSE_CATCHUP"}:
        direction = source_direction
        mask &= (direction * response).le(maximum_response)
    elif mechanic == "M5_BREADTH_CONTINUATION":
        direction = source_direction
        signed_body = direction * frame["body_atr"]
        mask &= signed_body.ge(0.0) & signed_body.le(maximum_response)
    elif mechanic == "M5_PULSE_EXHAUSTION_FADE":
        direction = source_direction
        mask &= (direction * frame["body_atr"]).le(
            -float(params["minimum_opposite_response_atr"])
        )
    elif mechanic == "M5_SEQUENCE_BREAKOUT":
        bars = int(params["channel_bars"])
        buffer = float(params["breakout_buffer_atr"]) * frame["atr_m5"]
        long_break = frame["mid_close"].ge(frame[f"prior_high_{bars}"] + buffer)
        short_break = frame["mid_close"].le(frame[f"prior_low_{bars}"] - buffer)
        direction = pd.Series(
            np.select([long_break, short_break], [1, -1], default=0).astype(int),
            index=frame.index,
        )
        longer_horizon = {1: 3, 3: 6, 6: 12, 12: 12}[horizon]
        longer_score = frame[
            f"risk_score_{longer_horizon}b_{int(params['source_lookback'])}"
        ]
        longer_direction = pd.Series(
            np.sign(longer_score.fillna(0.0)).astype(int), index=frame.index
        )
        mask &= direction.eq(source_direction) & direction.eq(longer_direction)
        mask &= direction.ne(0)
    else:
        raise KeyError(mechanic)
    return mask.fillna(False), direction


def generate_manifest(
    source_m5: pd.DataFrame,
    discovery_start: pd.Timestamp,
    discovery_end: pd.Timestamp,
    attempt_first: int,
    policies_per_mechanic: int,
    minimum_raw_signals: int,
) -> pd.DataFrame:
    stage = source_m5["bar_end_utc"].ge(discovery_start) & source_m5[
        "bar_end_utc"
    ].lt(discovery_end)
    rows: list[dict[str, Any]] = []
    attempt = attempt_first - 1
    for mechanic in MECHANICS:
        ranked = sorted(
            parameter_space(mechanic),
            key=lambda params: hashlib.sha256(
                f"{mechanic}|{json.dumps(params, sort_keys=True)}".encode("ascii")
            ).hexdigest(),
        )
        admitted = 0
        for params in ranked:
            mask, direction = source_event_mask_direction(source_m5, mechanic, params)
            selected = mask & stage
            raw_signals = int(selected.sum())
            if raw_signals < minimum_raw_signals:
                continue
            long_signals = int((selected & direction.gt(0)).sum())
            short_signals = int((selected & direction.lt(0)).sum())
            if min(long_signals, short_signals) < max(30, minimum_raw_signals // 10):
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
                    "raw_discovery_long_count": long_signals,
                    "raw_discovery_short_count": short_signals,
                    "parameters_json": canonical,
                }
            )
            admitted += 1
            if admitted == policies_per_mechanic:
                break
        if admitted != policies_per_mechanic:
            raise ValueError(
                f"Only {admitted} source-eligible V94 policies for {mechanic}; "
                f"required {policies_per_mechanic}"
            )
    manifest = pd.DataFrame(rows)
    expected = len(MECHANICS) * policies_per_mechanic
    if len(manifest) != expected or manifest["policy_id"].duplicated().any():
        raise ValueError("Invalid V94 policy manifest")
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
    cooldown_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    slot_count: dict[tuple[Any, str], int] = {}
    execution = config["execution"]
    cooldown = pd.Timedelta(hours=float(execution["cooldown_hours"]))
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
                float(row["atr_m5"]),
                signal_direction,
                params,
                execution,
                stage_end,
            )
            outcome_cache[key] = outcome
        if outcome is None:
            continue
        entry_time = pd.Timestamp(outcome["entry_time"])
        if entry_time < position_until or entry_time < cooldown_until:
            continue
        day = entry_time.date()
        slot = str(row["session_slot"])
        if daily_count.get(day, 0) >= int(execution["maximum_trades_per_policy_utc_day"]):
            continue
        if slot_count.get((day, slot), 0) >= int(
            execution["maximum_trades_per_session_slot"]
        ):
            continue
        selected.append(
            {
                "attempt_no": int(policy.attempt_no),
                "policy_id": str(policy.policy_id),
                "mechanic": mechanic,
                "source_horizon": int(params["source_horizon"]),
                "source_lookback": int(params["source_lookback"]),
                "session_slot": slot,
                **outcome,
            }
        )
        position_until = pd.Timestamp(outcome["exit_time"])
        cooldown_until = position_until + cooldown
        daily_count[day] = daily_count.get(day, 0) + 1
        slot_count[(day, slot)] = slot_count.get((day, slot), 0) + 1
    if not selected:
        return pd.DataFrame()
    return pd.DataFrame(selected).sort_values("entry_time", kind="mergesort").reset_index(drop=True)


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
        rows.append(
            {
                "attempt_no": int(policy.attempt_no),
                "policy_id": str(policy.policy_id),
                "mechanic": str(policy.mechanic),
                "parameters_json": str(policy.parameters_json),
                **summarize(
                    trades,
                    start,
                    end,
                    config["segments"][stage],
                    int(config["gates"][stage]["top_winners_removed"]),
                ),
            }
        )
    metrics = pd.DataFrame(rows)
    metrics["fdr_qvalue"] = benjamini_hochberg(metrics["block_pvalue"])
    checks: list[dict[str, bool]] = []
    passes: list[bool] = []
    for row in metrics.to_dict(orient="records"):
        values = gate_checks(row, config["gates"][stage])
        checks.append(values)
        passes.append(all(values.values()))
    metrics["gate_checks_json"] = [
        json.dumps(value, sort_keys=True, separators=(",", ":")) for value in checks
    ]
    metrics["gate_pass"] = passes
    return metrics, cache


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
    frames = []
    for policy in selected_manifest.itertuples(index=False):
        trades = select_policy_trades(
            frame, arrays, policy, config, start, end, outcome_cache
        )
        if not trades.empty:
            frames.append(trades.assign(stage=stage))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
