from __future__ import annotations

import hashlib
import ast
import json
import math
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

PHASE = "XAU_CROSSASSET_RESIDUAL_V1_REVIEW_CORRECTIONS"
SOURCE_PHASE = "XAU_CROSSASSET_RESIDUAL_DIRECTIONAL_SPECIALISTS_V1"
BASE_COMMIT = "0722a66a41cf7a3d109a4bc129f8f469b80ca022"
BASE_TREE = "89dbd09a45c85e98a67b3a1487ea87730ce7d172"
BASE_PARENT = "c21c98711e21f3e2e4d705d64ac8cf1391aca228"
BRANCH = "codex/xau-crossasset-residual-v1-review-corrections"
COMMIT_MESSAGE = "fix: correct XAU residual V1 research evidence"
SOURCE_ORIGIN = "https://jetta.dukascopy.com/v1"
STORAGE_ENV = "DUKASCOPY_TICK_DATA_ROOT"
INSTRUMENTS = {"XAUUSD": "XAU-USD", "XAGUSD": "XAG-USD", "EURUSD": "EUR-USD", "USDJPY": "USD-JPY"}
LONG_ID = "XAU_NEGATIVE_RESIDUAL_LONG_SPECIALIST"
SHORT_ID = "XAU_POSITIVE_RESIDUAL_SHORT_SPECIALIST"
COMBINED_ID = "COMBINED_BIDIRECTIONAL_DIAGNOSTIC"
STAGE_A_START_MS = int(datetime(2021, 7, 1, tzinfo=UTC).timestamp() * 1000)
STAGE_A_END_MS = int(datetime(2024, 7, 1, tzinfo=UTC).timestamp() * 1000)


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iso_ms(value: int | float | None) -> str:
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return ""
    return datetime.fromtimestamp(float(value) / 1000, UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def chronological_segment(timestamp_ms: int) -> str:
    if timestamp_ms < int(datetime(2024, 7, 1, tzinfo=UTC).timestamp() * 1000):
        return "DEVELOPMENT"
    if timestamp_ms < int(datetime(2025, 7, 1, tzinfo=UTC).timestamp() * 1000):
        return "VALIDATION"
    return "LOCKED_EXAM"


def synchronize_m5(frames: Mapping[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Exact UTC intersection; absent observations are reported and never filled."""
    if set(frames) != set(INSTRUMENTS):
        raise ValueError("all four instruments are mandatory")
    sets = {symbol: set(frame["timestamp_ms"].astype("int64")) for symbol, frame in frames.items()}
    union = sorted(set().union(*sets.values()))
    common = sorted(set.intersection(*sets.values()))
    missing_rows = []
    for ts in union:
        missing = sorted(symbol for symbol, values in sets.items() if ts not in values)
        if missing:
            pos = int(np.searchsorted(common, ts))
            missing_rows.append({
                "timestamp_utc": iso_ms(ts), "timestamp_ms": ts,
                "missing_instruments": "|".join(missing), "exclusion_reason": "MISSING_COMMON_M5_BAR",
                "previous_synchronized_timestamp": iso_ms(common[pos - 1]) if pos else "",
                "next_synchronized_timestamp": iso_ms(common[pos]) if pos < len(common) else "",
            })
    result = pd.DataFrame({"timestamp_ms": common})
    for symbol in INSTRUMENTS:
        source = frames[symbol][["timestamp_ms", "close"]].drop_duplicates("timestamp_ms", keep="first")
        result = result.merge(source.rename(columns={"close": f"close_{symbol.lower()}"}), on="timestamp_ms", how="inner", validate="one_to_one")
    return result.sort_values("timestamp_ms", kind="mergesort").reset_index(drop=True), pd.DataFrame(missing_rows)


def add_log_returns(synchronized: pd.DataFrame) -> pd.DataFrame:
    out = synchronized.copy()
    consecutive = out["timestamp_ms"].diff().eq(300_000)
    for symbol in INSTRUMENTS:
        close = out[f"close_{symbol.lower()}"].astype(float)
        out[f"r_{symbol.lower().replace('usd', '') if symbol in {'XAUUSD','XAGUSD'} else symbol.lower()}"] = np.where(consecutive, np.log(close / close.shift(1)), np.nan)
    return out.rename(columns={"r_eurusd": "r_eurusd", "r_usdjpy": "r_usdjpy", "r_xau": "r_xau", "r_xag": "r_xag"})


def rolling_causal_ols(frame: pd.DataFrame, window: int = 3000, minimum: int = 2500, condition_limit: float = 1_000_000) -> pd.DataFrame:
    required = ["r_xau", "r_xag", "r_eurusd", "r_usdjpy"]
    valid = frame.dropna(subset=required).reset_index(drop=True).copy()
    n = len(valid)
    x = np.column_stack([np.ones(n), valid[["r_xag", "r_eurusd", "r_usdjpy"]].to_numpy(float)])
    y = valid["r_xau"].to_numpy(float)
    xx = np.einsum("ni,nj->nij", x, x)
    xy = x * y[:, None]
    cxx = np.concatenate([np.zeros((1, 4, 4)), np.cumsum(xx, axis=0)])
    cxy = np.concatenate([np.zeros((1, 4)), np.cumsum(xy, axis=0)])
    rows: list[dict[str, Any]] = []
    residuals: list[float] = []
    for i in range(n):
        start = max(0, i - window)
        obs = i - start
        row: dict[str, Any] = {
            "timestamp_ms": int(valid.at[i, "timestamp_ms"]), "chronological_segment": chronological_segment(int(valid.at[i, "timestamp_ms"])),
            **{name: float(valid.at[i, name]) for name in required}, "training_start": iso_ms(valid.at[start, "timestamp_ms"]) if obs else "",
            "training_end": iso_ms(valid.at[i - 1, "timestamp_ms"]) if obs else "", "training_observations": obs,
            "intercept": np.nan, "beta_xag": np.nan, "beta_eurusd": np.nan, "beta_usdjpy": np.nan,
            "condition_number": np.nan, "predicted_r_xau": np.nan, "residual": np.nan,
            "prior_residual_mean": np.nan, "prior_residual_std": np.nan, "residual_z": np.nan,
            "model_valid": False, "model_rejection_reason": "INSUFFICIENT_TRAINING_OBSERVATIONS" if obs < minimum else "",
        }
        if obs >= minimum:
            gram = cxx[i] - cxx[start]
            rhs = cxy[i] - cxy[start]
            rank = int(np.linalg.matrix_rank(gram))
            cond = float(math.sqrt(max(float(np.linalg.cond(gram)), 0.0)))
            row["condition_number"] = cond
            if rank < 4:
                row["model_rejection_reason"] = "RANK_DEFICIENT"
            elif not math.isfinite(cond) or cond > condition_limit:
                row["model_rejection_reason"] = "CONDITION_NUMBER_EXCEEDED"
            else:
                coef = np.linalg.solve(gram, rhs)
                prediction = float(x[i] @ coef)
                residual = float(y[i] - prediction)
                if np.all(np.isfinite(coef)) and math.isfinite(prediction) and math.isfinite(residual):
                    row.update(intercept=float(coef[0]), beta_xag=float(coef[1]), beta_eurusd=float(coef[2]), beta_usdjpy=float(coef[3]), predicted_r_xau=prediction, residual=residual, model_valid=True, model_rejection_reason="")
                    residuals.append(residual)
                else:
                    row["model_rejection_reason"] = "NONFINITE_MODEL_VALUE"
        prior = residuals[-500:]
        if row["model_valid"] and len(prior) >= 500:
            # residuals already includes current; remove it from its own reference.
            reference = residuals[-501:-1] if len(residuals) >= 501 else []
            if len(reference) == 500:
                mean = float(np.mean(reference))
                std = float(np.std(reference, ddof=1))
                row["prior_residual_mean"], row["prior_residual_std"] = mean, std
                if math.isfinite(std) and std > 0:
                    row["residual_z"] = (row["residual"] - mean) / std
                else:
                    row["model_valid"], row["model_rejection_reason"] = False, "ZERO_RESIDUAL_STANDARD_DEVIATION"
        rows.append(row)
    return pd.DataFrame(rows)


def construct_episodes(model: pd.DataFrame) -> list[dict[str, Any]]:
    valid = model[np.isfinite(model["residual_z"])].sort_values("timestamp_ms", kind="mergesort")
    candidates: list[dict[str, Any]] = []
    state = {"LONG": None, "SHORT": None}
    prev_z: float | None = None
    prev_ts: int | None = None
    sequence = {"LONG": 0, "SHORT": 0}
    for row in valid.to_dict("records"):
        ts, z = int(row["timestamp_ms"]), float(row["residual_z"])
        date = iso_ms(ts)[:10]
        for direction in ("LONG", "SHORT"):
            active = state[direction]
            if active is not None:
                zero = (direction == "LONG" and z >= 0) or (direction == "SHORT" and z <= 0)
                if zero or ts - active["start"] >= 6 * 3_600_000 or date != active["date"]:
                    state[direction] = None
        if prev_z is not None and prev_ts is not None and ts - prev_ts == 300_000:
            for direction, crossed, specialist in (
                ("LONG", prev_z > -2.5 and z <= -2.5, LONG_ID),
                ("SHORT", prev_z < 2.5 and z >= 2.5, SHORT_ID),
            ):
                if crossed and state[direction] is None:
                    sequence[direction] += 1
                    episode = f"{direction}-{date}-{sequence[direction]:05d}"
                    state[direction] = {"start": ts, "date": date, "traded": False}
                    candidates.append({
                        "specialist_id": specialist, "direction": direction, "excursion_episode_id": episode,
                        "UTC_date": date, "chronological_segment": row["chronological_segment"],
                        "candidate_bar_time": iso_ms(ts), "candidate_bar_ms": ts, "candidate_completed_ms": ts + 300_000,
                        "residual_z_previous": prev_z, "residual_z_current": z,
                        **{key: row.get(key) for key in ("r_xau", "predicted_r_xau", "residual", "beta_xag", "beta_eurusd", "beta_usdjpy", "condition_number")},
                    })
        prev_z, prev_ts = z, ts
    return candidates


def wilder_atr(frame: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    out = frame.sort_values("timestamp_ms", kind="mergesort").copy()
    prev = out["close"].shift(1)
    tr = pd.concat([(out.high - out.low).abs(), (out.high - prev).abs(), (out.low - prev).abs()], axis=1).max(axis=1)
    out["ATR14"] = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    return out


def prior_percentile(values: Sequence[float], current: float) -> float:
    clean = np.asarray([value for value in values if math.isfinite(float(value))], dtype=float)
    if not len(clean):
        return float("nan")
    return float(100.0 * np.count_nonzero(clean <= current) / len(clean))


def weighted_percentile(histogram: Mapping[float, int], q: float) -> float:
    total = sum(histogram.values())
    if total <= 0:
        return float("nan")
    target = int((total - 1) * q)
    cumulative = 0
    for value, count in sorted(histogram.items()):
        cumulative += count
        if cumulative > target:
            return float(value)
    return float(max(histogram))


def metrics(trades: Sequence[Mapping[str, Any]], field: str = "baseline_net_R", development_months: int = 36) -> dict[str, Any]:
    values = np.asarray([float(row[field]) for row in trades], dtype=float)
    wins = values[values > 0]
    losses = values[values < 0]
    equity = np.cumsum(values) if len(values) else np.asarray([])
    peaks = np.maximum.accumulate(np.r_[0.0, equity]) if len(values) else np.asarray([0.0])
    drawdown = peaks[1:] - equity if len(values) else np.asarray([])
    gross_positive = float(wins.sum())
    top10 = float(np.sort(wins)[-10:].sum() / gross_positive) if gross_positive > 0 else 1.0
    daily = Counter()
    for row, value in zip(trades, values):
        daily[str(row["UTC_date"])] += value
    winning_days = sorted((v for v in daily.values() if v > 0), reverse=True)
    # Frozen definition: the numerator uses positive net days, while the
    # denominator is gross positive *individual trade* R. Losses on a winning
    # day therefore reduce the numerator but never the denominator.
    top3days = float(sum(winning_days[:3]) / gross_positive) if gross_positive > 0 else 1.0
    months = {str(row["UTC_date"])[:7] for row in trades}
    return {
        "trades": int(len(values)), "wins": int(len(wins)), "losses": int(len(losses)),
        "net_R": float(values.sum()), "expectancy_R": float(values.mean()) if len(values) else 0.0,
        "profit_factor": float(wins.sum() / -losses.sum()) if len(losses) and -losses.sum() > 0 else (float("inf") if len(wins) else 0.0),
        "maximum_closed_drawdown_R": float(drawdown.max()) if len(drawdown) else 0.0,
        "top_ten_winners_fraction": top10, "top_three_winning_days_fraction": top3days,
        "active_months": len(months), "annualized_trades": float(len(values) * 12 / development_months),
        "median_monthly_trades": float(np.median(list(Counter(str(row["UTC_date"])[:7] for row in trades).values()))) if trades else 0.0,
    }


def stage_a_gate(baseline: Mapping[str, Any], stress: Mapping[str, Any], broker: Mapping[str, Any], combined: bool = False) -> tuple[bool, list[str]]:
    thresholds = {
        "trades": 180 if combined else 90, "annualized_trades": 60 if combined else 30,
        "active_months": 24 if combined else 18, "baseline_profit_factor": 1.15 if combined else 1.18,
        "baseline_expectancy_R": 0.05 if combined else 0.07, "stress_profit_factor": 1.05 if combined else 1.07,
        "stress_expectancy_R": 0.0 if combined else 0.02, "broker_profit_factor": 1.0 if combined else 1.02,
        "maximum_closed_drawdown_R": 15 if combined else 10, "top_ten_winners_fraction": 0.35,
        "top_three_winning_days_fraction": 0.25,
    }
    observed = {"trades": baseline["trades"], "annualized_trades": baseline["annualized_trades"], "active_months": baseline["active_months"],
        "baseline_profit_factor": baseline["profit_factor"], "baseline_expectancy_R": baseline["expectancy_R"],
        "stress_profit_factor": stress["profit_factor"], "stress_expectancy_R": stress["expectancy_R"],
        "broker_profit_factor": broker["profit_factor"], "maximum_closed_drawdown_R": baseline["maximum_closed_drawdown_R"],
        "top_ten_winners_fraction": baseline["top_ten_winners_fraction"], "top_three_winning_days_fraction": baseline["top_three_winning_days_fraction"]}
    failures = []
    for key, limit in thresholds.items():
        if key.startswith("maximum") or key.startswith("top_"):
            if observed[key] > limit:
                failures.append(key)
        elif observed[key] < limit:
            failures.append(key)
    for label, report in (("baseline_net_R", baseline), ("stress_net_R", stress), ("broker_net_R", broker), ("broker_expectancy_R", broker)):
        value = report["expectancy_R"] if label.endswith("expectancy_R") else report["net_R"]
        if value <= 0:
            failures.append(label)
    return not failures, failures


def stage_b_authorized(survivors: Sequence[str]) -> bool:
    return any(value in {LONG_ID, SHORT_ID} for value in survivors)


def final_direction_gate(full: Mapping[str, Any], stress: Mapping[str, Any], broker: Mapping[str, Any], validation: Mapping[str, Any], exam: Mapping[str, Any], rolling_positive_fraction: float, floating_drawdown_r: float, locked_active_months: int) -> tuple[bool, list[str]]:
    checks = {
        "full_trades": full["trades"] >= 160, "annualized_trades": full["annualized_trades"] >= 32,
        "validation_trades": validation["trades"] >= 30, "exam_trades": exam["trades"] >= 30,
        "locked_active_months": locked_active_months >= 8, "full_profit_factor": full["profit_factor"] >= 1.25,
        "full_expectancy": full["expectancy_R"] >= .08, "full_net": full["net_R"] > 0,
        "stress_profit_factor": stress["profit_factor"] >= 1.10, "stress_expectancy": stress["expectancy_R"] >= .03, "stress_net": stress["net_R"] > 0,
        "broker_profit_factor": broker["profit_factor"] >= 1.05, "broker_expectancy": broker["expectancy_R"] > 0, "broker_net": broker["net_R"] > 0,
        "validation_profit_factor": validation["profit_factor"] >= 1.05, "validation_expectancy": validation["expectancy_R"] > 0, "validation_net": validation["net_R"] > 0,
        "exam_profit_factor": exam["profit_factor"] >= 1.15, "exam_expectancy": exam["expectancy_R"] >= .05, "exam_net": exam["net_R"] > 0,
        "floating_drawdown": floating_drawdown_r <= 12, "winner_concentration": full["top_ten_winners_fraction"] <= .30,
        "winning_day_concentration": full["top_three_winning_days_fraction"] <= .20, "rolling_robustness": rolling_positive_fraction >= .70,
    }
    failures = [name for name, passed in checks.items() if not passed]
    return not failures, failures


def final_combined_gate(full: Mapping[str, Any], stress: Mapping[str, Any], broker: Mapping[str, Any], validation: Mapping[str, Any], exam: Mapping[str, Any], rolling_positive_fraction: float, floating_drawdown_r: float, locked_active_months: int, direction_positive_contribution_max: float) -> tuple[bool, list[str]]:
    checks = {
        "full_trades": full["trades"] >= 300, "annualized_trades": full["annualized_trades"] >= 60,
        "median_monthly_trades": full["median_monthly_trades"] >= 4, "validation_trades": validation["trades"] >= 55,
        "exam_trades": exam["trades"] >= 55, "locked_active_months": locked_active_months >= 10,
        "full_profit_factor": full["profit_factor"] >= 1.25, "full_expectancy": full["expectancy_R"] >= .08, "full_net": full["net_R"] > 0,
        "stress_profit_factor": stress["profit_factor"] >= 1.10, "stress_expectancy": stress["expectancy_R"] >= .03, "stress_net": stress["net_R"] > 0,
        "broker_profit_factor": broker["profit_factor"] >= 1.05, "broker_expectancy": broker["expectancy_R"] > 0, "broker_net": broker["net_R"] > 0,
        "validation_net": validation["net_R"] > 0, "exam_profit_factor": exam["profit_factor"] >= 1.15,
        "exam_expectancy": exam["expectancy_R"] >= .05, "exam_net": exam["net_R"] > 0,
        "floating_drawdown": floating_drawdown_r <= 15, "winner_concentration": full["top_ten_winners_fraction"] <= .30,
        "winning_day_concentration": full["top_three_winning_days_fraction"] <= .20, "rolling_robustness": rolling_positive_fraction >= .70,
        "direction_contribution": direction_positive_contribution_max <= .70,
    }
    failures = [name for name, passed in checks.items() if not passed]
    return not failures, failures


def capital_feasibility(account_balance: float, minimum_volume_loss: float, required_margin: float) -> tuple[bool, dict[str, float | str]]:
    """Evaluate the frozen USD 1,000-equivalent account contract.

    Leverage may affect broker margin, but it cannot enlarge the 0.50% risk
    limit or relax either of the two independent margin constraints.
    """
    risk_limit = account_balance * .005
    margin_limit = account_balance * .20
    minimum_free_margin = account_balance * .80
    post_entry_free_margin = account_balance - required_margin
    risk_pass = minimum_volume_loss <= risk_limit
    margin_pass = required_margin <= margin_limit
    free_margin_pass = post_entry_free_margin >= minimum_free_margin
    feasible = risk_pass and margin_pass and free_margin_pass
    failures = []
    if not risk_pass:
        failures.append("MINIMUM_VOLUME_TOTAL_LOSS_EXCEEDS_0_50_PERCENT")
    if not margin_pass:
        failures.append("REQUIRED_MARGIN_EXCEEDS_20_PERCENT")
    if not free_margin_pass:
        failures.append("POST_ENTRY_FREE_MARGIN_BELOW_80_PERCENT")
    return feasible, {
        "minimum_volume_loss": minimum_volume_loss,
        "required_margin": required_margin,
        "post_entry_free_margin": post_entry_free_margin,
        "risk_limit": risk_limit,
        "margin_limit": margin_limit,
        "minimum_free_margin": minimum_free_margin,
        "risk_condition_passed": risk_pass,
        "margin_condition_passed": margin_pass,
        "free_margin_condition_passed": free_margin_pass,
        "rejection_reason": "|".join(failures),
    }


def sizing_rejection_rate_passes(rejected: int, evaluated: int) -> bool:
    if evaluated <= 0 or rejected < 0 or rejected > evaluated:
        raise ValueError("rejected/evaluated counts are invalid")
    return rejected / evaluated <= .10


def classify(evidence_valid: bool, data_complete: bool, survivors: Sequence[str], final_passers: Sequence[str] = (), combined_final: bool = False) -> str:
    if not evidence_valid:
        return "XAU_CROSSASSET_RESIDUAL_V1_EVIDENCE_INVALID"
    if not data_complete:
        return "XAU_CROSSASSET_RESIDUAL_V1_DATA_INCOMPLETE"
    if not survivors:
        return "XAU_CROSSASSET_RESIDUAL_V1_NO_DIRECTIONAL_SURVIVOR"
    if set(final_passers) == {LONG_ID, SHORT_ID} and combined_final:
        return "XAU_CROSSASSET_RESIDUAL_V1_BIDIRECTIONAL_SPECIALIST_CONFIRMATION_REQUIRED"
    if final_passers == [LONG_ID]:
        return "XAU_CROSSASSET_RESIDUAL_V1_LONG_SPECIALIST_CONFIRMATION_REQUIRED"
    if final_passers == [SHORT_ID]:
        return "XAU_CROSSASSET_RESIDUAL_V1_SHORT_SPECIALIST_CONFIRMATION_REQUIRED"
    return "XAU_CROSSASSET_RESIDUAL_V1_FINAL_REJECTED"


class ExecutionOrderingError(RuntimeError):
    """Raised when tick order is unknowable and the frozen ambiguity rule does not apply."""


def _exit_side_price(row: Mapping[str, Any], direction: str) -> float:
    return float(row["bid"] if direction == "LONG" else row["ask"])


def _barrier_flags(price: float, direction: str, stop: float, target: float) -> tuple[bool, bool]:
    if direction == "LONG":
        return price <= stop, price >= target
    return price >= stop, price <= target


def _process_ordered_exit_ticks_dataframe_reference(
    ticks: pd.DataFrame,
    *,
    direction: str,
    entry_price: float,
    risk: float,
    stop: float,
    target: float,
    convergence_ms: int,
    convergence_z: float,
    expiry_ms: int,
    force_ms: int,
    utc_date: str,
) -> dict[str, Any] | None:
    """Select an exit one tick at a time in timestamp/source-sequence order.

    MFE/MAE are updated immediately before the barrier/lifecycle checks for the
    same scalar quote, so no later quote can contaminate the chosen exit.
    """
    required = {"timestamp_msc", "bid", "ask", "spread", "source_sequence"}
    if not required.issubset(ticks.columns):
        raise ValueError(f"ticks missing required columns: {sorted(required - set(ticks.columns))}")
    if direction not in {"LONG", "SHORT"} or not risk > 0:
        raise ValueError("direction and risk are invalid")

    frame = ticks.copy().reset_index(drop=False).rename(columns={"index": "_input_index"})
    frame = frame.sort_values("timestamp_msc", kind="mergesort").reset_index(drop=True)
    mfe = 0.0
    mae = 0.0
    diagnostics: Counter[str] = Counter()

    for timestamp, group in frame.groupby("timestamp_msc", sort=True):
        ts = int(timestamp)
        if iso_ms(ts)[:10] != utc_date:
            break
        group = group.copy()
        group_size = len(group)
        if group_size > 1:
            diagnostics["same_millisecond_groups_inspected"] += 1

        sequences = group["source_sequence"]
        missing_sequence = sequences.isna().any() or sequences.astype(str).str.strip().eq("").any()
        sequence_strings = sequences.astype(str).tolist() if not missing_sequence else []
        duplicated = bool(sequence_strings) and len(set(sequence_strings)) != len(sequence_strings)
        duplicate_conflict = False
        if duplicated:
            for _, repeated in group.assign(_sequence=sequences.astype(str)).groupby("_sequence", sort=False):
                if len(repeated) > 1 and len(repeated[["bid", "ask", "spread"]].drop_duplicates()) > 1:
                    duplicate_conflict = True
                    break

        if missing_sequence or duplicate_conflict:
            quality = "MISSING_SOURCE_SEQUENCE" if missing_sequence else "DUPLICATE_SOURCE_SEQUENCE_CONFLICT"
            diagnostics["unordered_groups"] += 1
            diagnostics[quality] += 1
            prices = [_exit_side_price(row, direction) for row in group.to_dict("records")]
            flags = [_barrier_flags(price, direction, stop, target) for price in prices]
            stop_hits = [index for index, (hit, _) in enumerate(flags) if hit]
            target_hits = [index for index, (_, hit) in enumerate(flags) if hit]
            if stop_hits and target_hits and group_size > 1:
                diagnostics["groups_containing_both_stop_and_target_across_quotes"] += 1
                selected_position = min(stop_hits, key=lambda index: prices[index]) if direction == "LONG" else max(stop_hits, key=lambda index: prices[index])
                selected = group.iloc[selected_position]
                price = prices[selected_position]
                excursion = (price - entry_price) / risk if direction == "LONG" else (entry_price - price) / risk
                mfe, mae = max(mfe, excursion), min(mae, excursion)
                return {
                    "exit_tick": selected,
                    "exit_price": price,
                    "exit_reason": "STOP",
                    "exit_z": float("nan"),
                    "MFE_R": float(mfe),
                    "MAE_R": float(mae),
                    "identical_timestamp_ambiguity": True,
                    "exit_source_sequence": "",
                    "exit_timestamp_group_size": group_size,
                    "exit_ordering_quality": "IDENTICAL_TIMESTAMP_STOP_FIRST",
                    "stop_gap": price != stop,
                    "target_gap": False,
                    "diagnostics": dict(diagnostics),
                }
            raise ExecutionOrderingError(quality)

        if duplicated:
            # Byte-for-byte identical transitions with the same sequence are
            # semantically one quote; collapsing them preserves the exact path.
            group = group.drop_duplicates(["source_sequence", "bid", "ask", "spread"], keep="first")
            diagnostics["identical_duplicate_source_sequences_collapsed"] += group_size - len(group)
        if len(set(group["source_sequence"].astype(str))) > 1:
            diagnostics["same_millisecond_groups_with_multiple_source_sequences"] += 1
        original_sequences = group["source_sequence"].astype(str).tolist()
        ordered_sequences = sorted(original_sequences)
        if original_sequences != ordered_sequences:
            diagnostics["NON_MONOTONIC_SOURCE_SEQUENCE"] += 1
        group = group.assign(_sequence=group["source_sequence"].astype(str)).sort_values("_sequence", kind="mergesort")

        for _, tick in group.iterrows():
            price = _exit_side_price(tick, direction)
            excursion = (price - entry_price) / risk if direction == "LONG" else (entry_price - price) / risk
            mfe, mae = max(mfe, excursion), min(mae, excursion)
            stop_hit, target_hit = _barrier_flags(price, direction, stop, target)
            if stop_hit and target_hit:
                raise AssertionError("one scalar executable quote cannot reach both frozen barriers")
            reason = ""
            exit_price = price
            exit_z = float("nan")
            if stop_hit:
                reason = "STOP"
            elif target_hit:
                reason = "TARGET"
                exit_price = target
            elif ts >= convergence_ms:
                reason = "RESIDUAL_CONVERGENCE"
                exit_z = convergence_z
            elif ts >= expiry_ms:
                reason = "NINETY_MINUTE_EXPIRY"
            elif ts >= force_ms:
                reason = "SAME_DAY_FORCE_CLOSE"
            if reason:
                return {
                    "exit_tick": tick,
                    "exit_price": float(exit_price),
                    "exit_reason": reason,
                    "exit_z": float(exit_z),
                    "MFE_R": float(mfe),
                    "MAE_R": float(mae),
                    "identical_timestamp_ambiguity": False,
                    "exit_source_sequence": str(tick["source_sequence"]),
                    "exit_timestamp_group_size": group_size,
                    "exit_ordering_quality": "SOURCE_SEQUENCE_ORDERED",
                    "stop_gap": bool(reason == "STOP" and price != stop),
                    "target_gap": bool(reason == "TARGET" and price != target),
                    "diagnostics": dict(diagnostics),
                }
    return None


def process_ordered_exit_ticks(
    ticks: pd.DataFrame,
    *,
    direction: str,
    entry_price: float,
    risk: float,
    stop: float,
    target: float,
    convergence_ms: int,
    convergence_z: float,
    expiry_ms: int,
    force_ms: int,
    utc_date: str,
) -> dict[str, Any] | None:
    """NumPy-indexed equivalent of the audited scalar tick state machine."""
    required = {"timestamp_msc", "bid", "ask", "spread", "source_sequence"}
    if not required.issubset(ticks.columns):
        raise ValueError(f"ticks missing required columns: {sorted(required - set(ticks.columns))}")
    if direction not in {"LONG", "SHORT"} or not risk > 0:
        raise ValueError("direction and risk are invalid")
    if ticks.empty:
        return None

    timestamps = ticks["timestamp_msc"].to_numpy(dtype=np.int64, copy=False)
    bids = ticks["bid"].to_numpy(dtype=float, copy=False)
    asks = ticks["ask"].to_numpy(dtype=float, copy=False)
    spreads = ticks["spread"].to_numpy(dtype=float, copy=False)
    sequences = ticks["source_sequence"].to_numpy(dtype=object, copy=False)
    if np.any(timestamps[1:] < timestamps[:-1]):
        index_order = np.argsort(timestamps, kind="stable")
        timestamps, bids, asks, spreads, sequences = (array[index_order] for array in (timestamps, bids, asks, spreads, sequences))

    prices = bids if direction == "LONG" else asks
    mfe = 0.0
    mae = 0.0
    diagnostics: Counter[str] = Counter()

    def tick_at(index: int) -> pd.Series:
        return pd.Series({"timestamp_msc": int(timestamps[index]), "bid": float(bids[index]), "ask": float(asks[index]), "spread": float(spreads[index]), "source_sequence": sequences[index]})

    i, count = 0, len(timestamps)
    while i < count:
        ts = int(timestamps[i])
        if iso_ms(ts)[:10] != utc_date:
            break
        j = int(np.searchsorted(timestamps, ts, side="right"))
        group_size = j - i
        if group_size > 1:
            diagnostics["same_millisecond_groups_inspected"] += 1
        raw_sequences = sequences[i:j]
        missing_sequence = any(value is None or (isinstance(value, float) and math.isnan(value)) or not str(value).strip() for value in raw_sequences)
        sequence_strings = [str(value) for value in raw_sequences] if not missing_sequence else []
        duplicate_conflict = False
        if sequence_strings and len(set(sequence_strings)) != len(sequence_strings):
            signatures: dict[str, tuple[float, float, float]] = {}
            for offset, sequence in enumerate(sequence_strings):
                signature = (float(bids[i + offset]), float(asks[i + offset]), float(spreads[i + offset]))
                if sequence in signatures and signatures[sequence] != signature:
                    duplicate_conflict = True
                    break
                signatures[sequence] = signature

        if missing_sequence or duplicate_conflict:
            quality = "MISSING_SOURCE_SEQUENCE" if missing_sequence else "DUPLICATE_SOURCE_SEQUENCE_CONFLICT"
            diagnostics["unordered_groups"] += 1
            diagnostics[quality] += 1
            group_prices = prices[i:j]
            if direction == "LONG":
                stop_offsets = np.flatnonzero(group_prices <= stop)
                target_offsets = np.flatnonzero(group_prices >= target)
            else:
                stop_offsets = np.flatnonzero(group_prices >= stop)
                target_offsets = np.flatnonzero(group_prices <= target)
            if len(stop_offsets) and len(target_offsets) and group_size > 1:
                diagnostics["groups_containing_both_stop_and_target_across_quotes"] += 1
                adverse_offset = int(stop_offsets[np.argmin(group_prices[stop_offsets])]) if direction == "LONG" else int(stop_offsets[np.argmax(group_prices[stop_offsets])])
                selected_index = i + adverse_offset
                price = float(prices[selected_index])
                excursion = (price - entry_price) / risk if direction == "LONG" else (entry_price - price) / risk
                mfe, mae = max(mfe, excursion), min(mae, excursion)
                return {
                    "exit_tick": tick_at(selected_index), "exit_price": price, "exit_reason": "STOP", "exit_z": float("nan"),
                    "MFE_R": float(mfe), "MAE_R": float(mae), "identical_timestamp_ambiguity": True,
                    "exit_source_sequence": "", "exit_timestamp_group_size": group_size,
                    "exit_ordering_quality": "IDENTICAL_TIMESTAMP_STOP_FIRST", "stop_gap": price != stop,
                    "target_gap": False, "diagnostics": dict(diagnostics),
                }
            raise ExecutionOrderingError(quality)

        if len(set(sequence_strings)) > 1:
            diagnostics["same_millisecond_groups_with_multiple_source_sequences"] += 1
        ordered_offsets = sorted(range(group_size), key=lambda offset: sequence_strings[offset])
        if ordered_offsets != list(range(group_size)):
            diagnostics["NON_MONOTONIC_SOURCE_SEQUENCE"] += 1
        seen: dict[str, tuple[float, float, float]] = {}
        for offset in ordered_offsets:
            index = i + offset
            sequence = sequence_strings[offset]
            signature = (float(bids[index]), float(asks[index]), float(spreads[index]))
            if sequence in seen:
                diagnostics["identical_duplicate_source_sequences_collapsed"] += 1
                continue
            seen[sequence] = signature
            price = float(prices[index])
            excursion = (price - entry_price) / risk if direction == "LONG" else (entry_price - price) / risk
            mfe, mae = max(mfe, excursion), min(mae, excursion)
            stop_hit, target_hit = _barrier_flags(price, direction, stop, target)
            if stop_hit and target_hit:
                raise AssertionError("one scalar executable quote cannot reach both frozen barriers")
            reason = ""
            exit_price = price
            exit_z = float("nan")
            if stop_hit:
                reason = "STOP"
            elif target_hit:
                reason, exit_price = "TARGET", target
            elif ts >= convergence_ms:
                reason, exit_z = "RESIDUAL_CONVERGENCE", convergence_z
            elif ts >= expiry_ms:
                reason = "NINETY_MINUTE_EXPIRY"
            elif ts >= force_ms:
                reason = "SAME_DAY_FORCE_CLOSE"
            if reason:
                return {
                    "exit_tick": tick_at(index), "exit_price": float(exit_price), "exit_reason": reason,
                    "exit_z": float(exit_z), "MFE_R": float(mfe), "MAE_R": float(mae),
                    "identical_timestamp_ambiguity": False, "exit_source_sequence": sequence,
                    "exit_timestamp_group_size": group_size, "exit_ordering_quality": "SOURCE_SEQUENCE_ORDERED",
                    "stop_gap": bool(reason == "STOP" and price != stop), "target_gap": bool(reason == "TARGET" and price != target),
                    "diagnostics": dict(diagnostics),
                }
        i = j
    return None


def trade_result_signature(result: Mapping[str, Any]) -> tuple[Any, ...]:
    """Fields that must remain invariant when post-exit ticks are modified."""
    tick = result["exit_tick"]
    return (
        int(tick["timestamp_msc"]),
        str(result["exit_reason"]),
        float(result["exit_price"]),
        float(result["MFE_R"]),
        float(result["MAE_R"]),
    )


def combine_standalone_trades(trades: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Merge directions chronologically while permitting one global XAU position."""
    combined: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    global_exit = -1
    for trade in sorted(trades, key=lambda row: (str(row["entry_time"]), str(row["specialist_id"]))):
        entry_ms = int(datetime.fromisoformat(str(trade["entry_time"]).replace("Z", "+00:00")).timestamp() * 1000)
        exit_ms = int(datetime.fromisoformat(str(trade["exit_time"]).replace("Z", "+00:00")).timestamp() * 1000)
        if entry_ms < global_exit:
            conflicts.append({"specialist_id": trade["specialist_id"], "entry_time": trade["entry_time"], "rejection_reason": "GLOBAL_XAU_POSITION_ALREADY_OPEN"})
        else:
            combined.append({**trade, "simulation_id": COMBINED_ID})
            global_exit = exit_ms
    return combined, conflicts


def no_search_tokens(source: str) -> bool:
    """Reject executable search/trading APIs without flagging documentation or this audit itself."""
    prohibited_names = {"Grid" + "SearchCV", "Randomized" + "SearchCV", "create_" + "study", "f" + "min", "order_" + "send"}
    prohibited_modules = {"op" + "tuna", "hyper" + "opt", "Meta" + "Trader5"}
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name.split(".")[0] for alias in node.names] if isinstance(node, ast.Import) else [(node.module or "").split(".")[0]]
            if any(name in prohibited_modules for name in names):
                return False
        if isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
            if name in prohibited_names:
                return False
    return True
