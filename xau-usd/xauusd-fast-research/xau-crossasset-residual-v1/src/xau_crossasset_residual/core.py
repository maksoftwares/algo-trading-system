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

PHASE = "XAU_CROSSASSET_RESIDUAL_DIRECTIONAL_SPECIALISTS_V1"
BASE_COMMIT = "c21c98711e21f3e2e4d705d64ac8cf1391aca228"
BASE_TREE = "1bedbc6531ab4de1d02b21984ef6003fe324f97a"
BRANCH = "codex/xau-crossasset-residual-fast-discovery-v1"
COMMIT_MESSAGE = "research: screen XAU cross-asset residual specialists"
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
    top3days = float(sum(winning_days[:3]) / sum(winning_days)) if winning_days else 1.0
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
    post_entry_free_margin = account_balance - required_margin
    feasible = minimum_volume_loss <= account_balance * .01 and post_entry_free_margin >= 2 * minimum_volume_loss
    reason = "" if feasible else "MINIMUM_VOLUME_RISK_OR_MARGIN_EXCEEDS_FROZEN_ACCOUNT_LIMIT"
    return feasible, {"minimum_volume_loss": minimum_volume_loss, "required_margin": required_margin, "post_entry_free_margin": post_entry_free_margin, "rejection_reason": reason}


def classify(evidence_valid: bool, data_complete: bool, survivors: Sequence[str], final_passers: Sequence[str] = (), combined_final: bool = False) -> str:
    if not evidence_valid:
        return "XAU_CROSSASSET_RESIDUAL_V1_EVIDENCE_INVALID"
    if not data_complete:
        return "XAU_CROSSASSET_RESIDUAL_V1_DATA_INCOMPLETE"
    if not survivors:
        return "XAU_CROSSASSET_RESIDUAL_V1_NO_DIRECTIONAL_SURVIVOR"
    if set(final_passers) == {LONG_ID, SHORT_ID} and combined_final:
        return "XAU_CROSSASSET_RESIDUAL_V1_BIDIRECTIONAL_CONFIRMATION_REQUIRED"
    if final_passers == [LONG_ID]:
        return "XAU_CROSSASSET_RESIDUAL_V1_LONG_CONFIRMATION_REQUIRED"
    if final_passers == [SHORT_ID]:
        return "XAU_CROSSASSET_RESIDUAL_V1_SHORT_CONFIRMATION_REQUIRED"
    return "XAU_CROSSASSET_RESIDUAL_V1_FINAL_REJECTED"


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
