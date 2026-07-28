from __future__ import annotations

import hashlib
import heapq
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
CONTRACT_PATH = ROOT / "config" / "CAUSAL_RETEST_CONTRACT.json"
OUTPUTS = ROOT / "outputs"
PNL = "fee_stress_pnl_usd"
BAR_WIDTH = pd.Timedelta(minutes=5)
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_BLOCK_WEEKS = 4
BOOTSTRAP_SEED = 20_260_728

FEATURES_PATH = (
    REPO_ROOT
    / "xau-usd/xauusd-fast-research/claude-v60-portfolio-state-ml-v1"
    / "src/features.py"
)
COOLDOWN_PATH = (
    REPO_ROOT
    / "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2"
    / "build_v57_post_loss_cooldown_impact.py"
)
FLOATING_AUDIT_PATH = (
    REPO_ROOT
    / "xau-usd/xauusd-fast-research/one-trade-per-day-floating-equity-v60"
    / "src/audit.py"
)
FLOATING_CONFIG_PATH = (
    REPO_ROOT
    / "xau-usd/xauusd-fast-research/one-trade-per-day-floating-equity-v60"
    / "config/one_trade_per_day_floating_equity_v60.json"
)
DEMO_STATUS_PATH = Path(
    "C:/MT5PortableTier1BestEA/MQL5/Files/v60_canonical_demo_v2/status.json"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def utc_ns(values: pd.Series | np.ndarray) -> np.ndarray:
    return pd.DatetimeIndex(pd.to_datetime(values, utc=True)).as_unit("ns").asi8


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_contract() -> dict[str, Any]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    for source in contract["inputs"].values():
        path = Path(str(source["path"]))
        if not path.is_absolute():
            path = REPO_ROOT / path
        actual = sha256_file(path)
        if actual != str(source["sha256"]):
            raise ValueError(f"Input hash mismatch for {path}: {actual}")
    return contract


def completed_bar_indices(
    bar_open: pd.Series | np.ndarray,
    entry_time: pd.Series | np.ndarray,
    bar_width: pd.Timedelta = BAR_WIDTH,
) -> np.ndarray:
    opens = utc_ns(bar_open)
    entries = utc_ns(entry_time)
    available = opens + int(bar_width.value)
    return np.searchsorted(available, entries, side="right") - 1


def execution_source(row: pd.Series) -> str:
    specialist = row.get("specialist_id")
    if specialist is not None and not pd.isna(specialist):
        return str(specialist)
    return str(row["sleeve_id"])


def load_current_population(
    contract: dict[str, Any], cooldown_module: ModuleType
) -> tuple[pd.DataFrame, dict[str, Any]]:
    ledger_path = REPO_ROOT / contract["inputs"]["v60_price_ledger"]["path"]
    ledger = pd.read_parquet(ledger_path)
    for column in ("entry_time", "exit_time", "signal_time"):
        ledger[column] = pd.to_datetime(ledger[column], utc=True)
    excluded = set(contract["population"]["exclude_specialist_ids"])
    baseline = ledger.loc[~ledger["specialist_id"].isin(excluded)].copy()
    cooldowns = contract["population"]["post_loss_cooldowns_minutes"]
    audited = cooldown_module.apply_post_loss_cooldowns(baseline, cooldowns)
    accepted = audited.loc[audited["post_loss_cooldown_accepted"]].copy()
    feed_start = pd.Timestamp(contract["population"]["feed_start_utc"])
    accepted = accepted.loc[accepted["entry_time"].ge(feed_start)].copy()
    accepted["execution_source_id"] = accepted.apply(execution_source, axis=1)
    accepted = accepted.sort_values(
        ["entry_time", "trade_id"], kind="mergesort"
    ).reset_index(drop=True)
    audit = {
        "raw_ledger_rows": int(len(ledger)),
        "r5_excluded_rows": int(len(ledger) - len(baseline)),
        "pre_feed_or_cooldown_excluded_rows": int(len(baseline) - len(accepted)),
        "current_population_rows": int(len(accepted)),
        "current_population_start_utc": accepted["entry_time"].min().isoformat(),
        "current_population_end_utc": accepted["entry_time"].max().isoformat(),
    }
    return accepted, audit


def build_corrected_features(
    ledger: pd.DataFrame, feature_module: ModuleType
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    market = feature_module.load_market()
    opens = market["t"].copy()
    selected = completed_bar_indices(opens, ledger["entry_time"])
    if (selected < 0).any():
        raise ValueError("Market history does not cover every entry")
    selected_open = opens.iloc[selected].reset_index(drop=True)
    selected_available = selected_open + BAR_WIDTH
    entries = ledger["entry_time"].reset_index(drop=True)
    causal = selected_available.le(entries)
    if not bool(causal.all()):
        raise ValueError("An incomplete M5 bar reached the corrected features")

    available_market = market.copy()
    available_market["t"] = available_market["t"] + BAR_WIDTH
    market_features = feature_module.market_features(ledger, available_market)
    X = market_features[feature_module.MARKET].copy()
    X["is_long"] = (ledger["direction_sign"].to_numpy() > 0).astype(float)
    X["is_core"] = ledger["is_core"].astype(float).to_numpy()
    X = X.replace([np.inf, -np.inf], np.nan)
    keep = market_features["_bar_ok"].to_numpy(dtype=bool) & X.notna().all(axis=1)

    meta_columns = [
        "trade_id",
        "entry_time",
        "exit_time",
        "source_id",
        "specialist_id",
        "sleeve_id",
        "execution_source_id",
        "direction",
        "direction_sign",
        "is_core",
        "entry_price",
        "exit_price",
        "fee_stress_open_cost_usd",
        PNL,
        "risk_usd",
    ]
    meta = ledger[meta_columns].copy()
    X = X.loc[keep].reset_index(drop=True)
    meta = meta.loc[keep].reset_index(drop=True)
    audit = {
        "input_rows": int(len(ledger)),
        "feature_complete_rows": int(keep.sum()),
        "dropped_rows": int((~keep).sum()),
        "selected_bar_available_at_entry_rows": int(causal.sum()),
        "selected_bar_unavailable_at_entry_rows": int((~causal).sum()),
        "selected_bar_max_age_seconds": float(
            (entries - selected_available).dt.total_seconds().max()
        ),
        "selected_bar_min_age_seconds": float(
            (entries - selected_available).dt.total_seconds().min()
        ),
        "feature_columns": list(X.columns),
    }
    return X, meta, audit


def expanding_rank(
    values: np.ndarray,
    training_reference: np.ndarray,
    history: list[float],
    minimum_history: int,
) -> np.ndarray:
    ranks = np.empty(len(values), dtype=float)
    reference = np.sort(np.asarray(training_reference, dtype=float))
    for index, value in enumerate(values):
        source = (
            np.sort(np.asarray(history, dtype=float))
            if len(history) >= minimum_history
            else reference
        )
        ranks[index] = np.searchsorted(source, value, side="right") / len(source)
        history.append(float(value))
    return ranks


def walkforward(
    X: pd.DataFrame,
    meta: pd.DataFrame,
    contract: dict[str, Any],
    seed: int,
) -> pd.DataFrame:
    model_config = contract["model"]
    sizing = contract["sizing"]
    scores = np.full(len(X), np.nan)
    ranks = np.full(len(X), np.nan)
    multipliers = np.full(len(X), np.nan)
    history: list[float] = []
    rng = np.random.default_rng(seed)
    purge = pd.Timedelta(hours=int(model_config["purge_hours"]))
    parameters = dict(model_config["parameters"])

    for year in contract["population"]["test_entry_years"]:
        cutoff = pd.Timestamp(f"{year}-01-01", tz="UTC") - purge
        train = meta["exit_time"].lt(cutoff).to_numpy()
        test = meta["entry_time"].dt.year.eq(year).to_numpy()
        if (
            int(train.sum()) < int(model_config["minimum_train_rows"])
            or int(test.sum()) < 5
        ):
            continue
        X_train = X.loc[train]
        X_test = X.loc[test]
        pnl = meta.loc[train, PNL].to_numpy(dtype=float)
        target = np.clip(
            pnl,
            np.quantile(pnl, model_config["winsor_quantiles"][0]),
            np.quantile(pnl, model_config["winsor_quantiles"][1]),
        )
        test_score = np.zeros(int(test.sum()), dtype=float)
        train_score = np.zeros(int(train.sum()), dtype=float)
        for _ in range(int(model_config["bags"])):
            sample = rng.integers(0, len(X_train), len(X_train))
            model = HistGradientBoostingRegressor(**parameters).fit(
                X_train.iloc[sample], target[sample]
            )
            test_score += model.predict(X_test)
            train_score += model.predict(X_train)
        test_score /= int(model_config["bags"])
        train_score /= int(model_config["bags"])
        rank = expanding_rank(
            test_score,
            train_score,
            history,
            int(sizing["minimum_oos_history"]),
        )
        low, high = map(float, sizing["continuous_band"])
        raw = (low + rank * (high - low)) / float(
            sizing["continuous_constant_normalizer"]
        )
        shrink = min(
            1.0,
            np.sqrt(int(train.sum()) / float(sizing["training_size_reference"])),
        )
        multiplier = 1.0 + (raw - 1.0) * shrink
        scores[test] = test_score
        ranks[test] = rank
        multipliers[test] = multiplier

    return pd.DataFrame(
        {
            "score": scores,
            "rank": ranks,
            "continuous_multiplier": multipliers,
        }
    )


def closed_metrics(
    meta: pd.DataFrame, factors: np.ndarray
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    factor = np.asarray(factors, dtype=float)
    pnl = meta[PNL].to_numpy(dtype=float)
    active = factor > 0.0
    realized = pnl * factor
    order = np.argsort(meta["exit_time"].to_numpy())
    equity = np.concatenate(([0.0], np.cumsum(realized[order])))
    drawdown = float(np.max(np.maximum.accumulate(equity) - equity))
    active_pnl = realized[active]
    gross_profit = float(np.clip(active_pnl, 0.0, None).sum())
    gross_loss = float(np.clip(-active_pnl, 0.0, None).sum())
    month = meta["exit_time"].dt.strftime("%Y-%m")
    monthly = pd.DataFrame(
        {
            "month": month,
            "baseline_pnl_usd": pnl,
            "policy_pnl_usd": realized,
        }
    ).groupby("month", as_index=False).sum()
    monthly["delta_pnl_usd"] = (
        monthly["policy_pnl_usd"] - monthly["baseline_pnl_usd"]
    )
    year = meta["entry_time"].dt.year
    yearly = pd.DataFrame(
        {
            "entry_year": year,
            "baseline_pnl_usd": pnl,
            "policy_pnl_usd": realized,
        }
    ).groupby("entry_year", as_index=False).sum()
    yearly["delta_pnl_usd"] = yearly["policy_pnl_usd"] - yearly["baseline_pnl_usd"]
    metrics = {
        "trade_rows": int(active.sum()),
        "baseline_rows": int(len(meta)),
        "net_pnl_usd": float(realized.sum()),
        "profit_factor": float(gross_profit / gross_loss) if gross_loss else None,
        "win_rate": float((active_pnl > 0.0).mean()) if len(active_pnl) else None,
        "closed_trade_drawdown_usd": drawdown,
        "green_months": int(monthly["policy_pnl_usd"].gt(0.0).sum()),
        "months": int(len(monthly)),
        "green_month_percentage": float(
            100.0 * monthly["policy_pnl_usd"].gt(0.0).mean()
        ),
        "nonnegative_entry_years": int(yearly["delta_pnl_usd"].ge(0.0).sum()),
        "evaluated_entry_years": int(len(yearly)),
        "mean_factor": float(factor.mean()),
    }
    return metrics, monthly, yearly


def moving_week_block_bootstrap(
    meta: pd.DataFrame,
    delta: np.ndarray,
    repetitions: int = BOOTSTRAP_REPS,
    block_weeks: int = BOOTSTRAP_BLOCK_WEEKS,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    frame = pd.DataFrame(
        {
            "entry_time": meta["entry_time"],
            "delta": np.asarray(delta, dtype=float),
        }
    )
    naive = frame["entry_time"].dt.tz_localize(None)
    frame["week"] = naive.dt.to_period("W-SUN").dt.start_time
    frame["year"] = frame["entry_time"].dt.year
    series: list[np.ndarray] = []
    for _, group in frame.groupby("year"):
        weekly = group.groupby("week")["delta"].sum().sort_index()
        complete = pd.date_range(weekly.index.min(), weekly.index.max(), freq="7D")
        series.append(weekly.reindex(complete, fill_value=0.0).to_numpy(dtype=float))

    rng = np.random.default_rng(seed)
    samples = np.zeros(repetitions, dtype=float)
    for repetition in range(repetitions):
        total = 0.0
        for values in series:
            count = len(values)
            sampled: list[float] = []
            while len(sampled) < count:
                start = int(rng.integers(0, count))
                sampled.extend(
                    values[(start + np.arange(block_weeks)) % count].tolist()
                )
            total += float(np.sum(sampled[:count]))
        samples[repetition] = total
    return {
        "observed_delta_usd": float(np.sum(delta)),
        "repetitions": int(repetitions),
        "block_weeks": int(block_weeks),
        "lower_95_one_sided_usd": float(np.quantile(samples, 0.05)),
        "lower_95_two_sided_usd": float(np.quantile(samples, 0.025)),
        "upper_95_two_sided_usd": float(np.quantile(samples, 0.975)),
        "probability_nonpositive": float(np.mean(samples <= 0.0)),
    }


def demo_limits(config: dict[str, Any]) -> dict[str, float]:
    status = (
        json.loads(DEMO_STATUS_PATH.read_text(encoding="utf-8"))
        if DEMO_STATUS_PATH.exists()
        else {}
    )
    risk = config["risk"]
    activation = float(status.get("activation_equity_usd", 0.0))

    def effective(absolute_key: str, fraction_key: str) -> float:
        absolute = float(risk[absolute_key])
        fractional = activation * float(risk[fraction_key]) if activation else absolute
        return min(absolute, fractional)

    return {
        "activation_equity_usd": activation,
        "account_initial_risk_usd": effective(
            "maximum_account_concurrent_initial_risk_usd",
            "maximum_account_concurrent_initial_risk_fraction",
        ),
        "directional_initial_risk_usd": effective(
            "maximum_directional_concurrent_initial_risk_usd",
            "maximum_directional_concurrent_initial_risk_fraction",
        ),
        "addon_initial_risk_usd": float(
            risk["maximum_addon_concurrent_initial_risk_usd"]
        ),
        "maximum_account_positions": float(risk["maximum_account_xau_positions"]),
        "maximum_core_positions": float(risk["maximum_core_open_positions"]),
        "maximum_addon_positions": float(risk["maximum_addon_open_positions"]),
        "floating_drawdown_hard_stop_usd": effective(
            "floating_drawdown_hard_stop_usd",
            "floating_drawdown_hard_stop_fraction",
        ),
    }


def source_risk_limits(config: dict[str, Any]) -> dict[str, float]:
    result = {
        "R1_UPTREND": 45.0,
        "R2_DOWNTREND": 45.0,
        "R3_COMPRESSION": 45.0,
        "R4_CHOP": 45.0,
    }
    for source in config["sources"]:
        source_id = str(source["source_id"])
        if source_id in {
            "V7_SWING_HEALTH",
            "V8_RETEST_HEALTH",
            "V25_CHOP",
            "V57_BREAK_SWING_H4ADX_HIGH",
        }:
            result[source_id] = float(source["maximum_risk_usd"])
    return result


def broker_factors(
    meta: pd.DataFrame,
    multipliers: np.ndarray,
    config: dict[str, Any],
    limits: dict[str, float],
    contract: dict[str, Any],
) -> tuple[np.ndarray, dict[str, Any]]:
    policy = contract["sizing"]["broker_policy"]
    low = float(policy["skip_below_multiplier"])
    high = float(policy["double_above_multiplier"])
    factors = np.ones(len(meta), dtype=float)
    factors[np.asarray(multipliers) < low] = 0.0
    proposed_double = np.asarray(multipliers) > high
    risk_limits = source_risk_limits(config)
    active: list[tuple[int, int, float, str, bool, bool]] = []
    sequence = 0
    known_account_risk = 0.0
    known_direction_risk = {"LONG": 0.0, "SHORT": 0.0}
    known_addon_risk = 0.0
    unknown_active = 0
    core_positions = 0
    addon_positions = 0
    doubled = 0
    double_rejections: dict[str, int] = {}

    def reject(reason: str) -> None:
        double_rejections[reason] = double_rejections.get(reason, 0) + 1

    for index, row in meta.iterrows():
        entry_ns = int(row["entry_time"].value)
        while active and active[0][0] <= entry_ns:
            _, _, risk, direction, addon, unknown = heapq.heappop(active)
            if unknown:
                unknown_active -= 1
            else:
                known_account_risk -= risk
                known_direction_risk[direction] -= risk
                if addon:
                    known_addon_risk -= risk
            if addon:
                addon_positions -= 1
            else:
                core_positions -= 1

        factor = factors[index]
        risk_value = row["risk_usd"]
        known = pd.notna(risk_value)
        risk = float(risk_value) if known else 0.0
        direction = str(row["direction"]).upper()
        addon = not bool(row["is_core"])
        source = str(row["execution_source_id"])

        if factor > 0.0 and proposed_double[index]:
            proposed_risk = risk * 2.0
            reason = None
            if not known:
                reason = "MISSING_INITIAL_RISK"
            elif source not in risk_limits:
                reason = "UNKNOWN_SOURCE_RISK_LIMIT"
            elif proposed_risk > risk_limits[source]:
                reason = "SOURCE_RISK_LIMIT"
            elif unknown_active > 0:
                reason = "ACTIVE_UNKNOWN_RISK"
            elif (
                known_account_risk + proposed_risk
                > limits["account_initial_risk_usd"]
            ):
                reason = "ACCOUNT_RISK_LIMIT"
            elif (
                known_direction_risk[direction] + proposed_risk
                > limits["directional_initial_risk_usd"]
            ):
                reason = "DIRECTIONAL_RISK_LIMIT"
            elif addon and (
                known_addon_risk + proposed_risk
                > limits["addon_initial_risk_usd"]
            ):
                reason = "ADDON_RISK_LIMIT"
            if reason is None:
                factor = 2.0
                doubled += 1
            else:
                factor = 1.0
                reject(reason)
            factors[index] = factor

        if factor <= 0.0:
            continue
        scaled_risk = risk * factor
        unknown = not known
        if unknown:
            unknown_active += 1
        else:
            known_account_risk += scaled_risk
            known_direction_risk[direction] += scaled_risk
            if addon:
                known_addon_risk += scaled_risk
        if addon:
            addon_positions += 1
        else:
            core_positions += 1
        heapq.heappush(
            active,
            (
                int(row["exit_time"].value),
                sequence,
                scaled_risk,
                direction,
                addon,
                unknown,
            ),
        )
        sequence += 1

    audit = {
        "skipped_rows": int(np.sum(factors == 0.0)),
        "one_lot_unit_rows": int(np.sum(factors == 1.0)),
        "two_lot_unit_rows": int(np.sum(factors == 2.0)),
        "proposed_double_rows": int(proposed_double.sum()),
        "accepted_double_rows": int(doubled),
        "accepted_double_missing_risk_rows": int(
            np.sum((factors == 2.0) & meta["risk_usd"].isna().to_numpy())
        ),
        "double_rejections": double_rejections,
        "lot_values": sorted((factors * 0.01)[factors > 0.0].tolist())
        if len(factors)
        else [],
    }
    if audit["lot_values"]:
        audit["lot_values"] = sorted(set(audit["lot_values"]))
    return factors, audit


def weighted_floating_metrics(
    bars: pd.DataFrame, meta: pd.DataFrame, factors: np.ndarray
) -> dict[str, Any]:
    factor = np.asarray(factors, dtype=float)
    bar_ns = utc_ns(bars["timestamp_utc"])
    duration_ns = int(BAR_WIDTH.value)
    bar_end_ns = bar_ns + duration_ns
    n = len(bars)
    long_weight = np.zeros(n + 1)
    short_weight = np.zeros(n + 1)
    open_constant = np.zeros(n + 1)
    close_long_weight = np.zeros(n + 1)
    close_short_weight = np.zeros(n + 1)
    close_constant = np.zeros(n + 1)
    position_count = np.zeros(n + 1)
    core_count = np.zeros(n + 1)
    addon_count = np.zeros(n + 1)
    known_risk = np.zeros(n + 1)
    unknown_risk_positions = np.zeros(n + 1)

    def add(target: np.ndarray, start: int, end: int, value: float) -> None:
        if start < end:
            target[start] += value
            target[end] -= value

    for index, row in meta.iterrows():
        size = float(factor[index])
        if size <= 0.0:
            continue
        entry = int(row["entry_time"].value)
        exit_time = int(row["exit_time"].value)
        start = int(np.searchsorted(bar_end_ns, entry, side="right"))
        end = int(np.searchsorted(bar_ns, exit_time, side="left"))
        close_start = start
        close_end = int(np.searchsorted(bar_end_ns, exit_time, side="left"))
        sign = 1.0 if str(row["direction"]).upper() == "LONG" else -1.0
        constant = size * (
            -sign * float(row["entry_price"])
            - float(row["fee_stress_open_cost_usd"])
        )
        if sign > 0:
            add(long_weight, start, end, size)
            add(close_long_weight, close_start, close_end, size)
        else:
            add(short_weight, start, end, size)
            add(close_short_weight, close_start, close_end, size)
        add(open_constant, start, end, constant)
        add(close_constant, close_start, close_end, constant)
        add(position_count, start, end, 1.0)
        add(
            addon_count if not bool(row["is_core"]) else core_count,
            start,
            end,
            1.0,
        )
        if pd.notna(row["risk_usd"]):
            add(known_risk, start, end, size * float(row["risk_usd"]))
        else:
            add(unknown_risk_positions, start, end, 1.0)

    long_active = np.cumsum(long_weight[:-1])
    short_active = np.cumsum(short_weight[:-1])
    constant_active = np.cumsum(open_constant[:-1])
    close_long = np.cumsum(close_long_weight[:-1])
    close_short = np.cumsum(close_short_weight[:-1])
    close_const = np.cumsum(close_constant[:-1])

    ordered = meta.assign(_factor=factor).sort_values(
        ["exit_time", "trade_id"], kind="mergesort"
    )
    exit_ns = utc_ns(ordered["exit_time"])
    exit_pnl = (
        ordered[PNL].to_numpy(dtype=float)
        * ordered["_factor"].to_numpy(dtype=float)
    )
    cumulative = np.concatenate(([0.0], np.cumsum(exit_pnl)))
    realized_before = cumulative[np.searchsorted(exit_ns, bar_ns, side="right")]
    realized_at_close = cumulative[
        np.searchsorted(exit_ns, bar_end_ns, side="right")
    ]
    low = (
        realized_before
        + long_active * bars["bid_low"].to_numpy(dtype=float)
        - short_active * bars["ask_high"].to_numpy(dtype=float)
        + constant_active
    )
    high = (
        realized_before
        + long_active * bars["bid_high"].to_numpy(dtype=float)
        - short_active * bars["ask_low"].to_numpy(dtype=float)
        + constant_active
    )
    close = (
        realized_at_close
        + close_long * bars["bid_close"].to_numpy(dtype=float)
        - close_short * bars["ask_close"].to_numpy(dtype=float)
        + close_const
    )
    running_peak = np.maximum.accumulate(np.maximum(high, 0.0))
    drawdowns = running_peak - low
    trough = int(np.argmax(drawdowns))
    positions = np.cumsum(position_count[:-1])
    core = np.cumsum(core_count[:-1])
    addon = np.cumsum(addon_count[:-1])
    known = np.cumsum(known_risk[:-1])
    unknown = np.cumsum(unknown_risk_positions[:-1])
    return {
        "net_pnl_usd": float(exit_pnl.sum()),
        "maximum_floating_drawdown_usd": float(drawdowns[trough]),
        "net_to_floating_drawdown": float(
            exit_pnl.sum() / max(drawdowns[trough], 1e-9)
        ),
        "peak_before_trough_usd": float(running_peak[trough]),
        "trough_low_equity_pnl_usd": float(low[trough]),
        "trough_time_utc": bars["timestamp_utc"].iloc[trough].isoformat(),
        "maximum_open_positions": int(np.max(positions)),
        "maximum_open_core_positions": int(np.max(core)),
        "maximum_open_addon_positions": int(np.max(addon)),
        "maximum_known_initial_risk_usd": float(np.max(known)),
        "maximum_unknown_risk_positions": int(np.max(unknown)),
        "final_close_equity_pnl_usd": float(close[-1]),
    }


def load_floating_bars(
    floating_module: ModuleType, meta: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, Any]]:
    config = json.loads(FLOATING_CONFIG_PATH.read_text(encoding="utf-8"))
    bars, audit = floating_module.load_m5_bars(config["market_data"])
    start = meta["entry_time"].min().floor("5min") - BAR_WIDTH
    end = meta["exit_time"].max().ceil("5min")
    bars = bars.loc[
        bars["timestamp_utc"].ge(start) & bars["timestamp_utc"].le(end)
    ].reset_index(drop=True)
    return bars, audit


def gates_for_policy(
    baseline_closed: dict[str, Any],
    policy_closed: dict[str, Any],
    baseline_floating: dict[str, Any],
    policy_floating: dict[str, Any],
    bootstrap: dict[str, Any],
    leverage_adjusted_delta: float,
) -> dict[str, bool]:
    minimum_ratio = baseline_floating["net_to_floating_drawdown"] * 1.05
    return {
        "net_pnl_not_below_baseline": (
            policy_closed["net_pnl_usd"] >= baseline_closed["net_pnl_usd"]
        ),
        "floating_drawdown_not_above_baseline": (
            policy_floating["maximum_floating_drawdown_usd"]
            <= baseline_floating["maximum_floating_drawdown_usd"]
        ),
        "net_to_floating_drawdown_improves_at_least_5pct": (
            policy_floating["net_to_floating_drawdown"] >= minimum_ratio
        ),
        "green_month_within_2_points": (
            policy_closed["green_month_percentage"]
            >= baseline_closed["green_month_percentage"] - 2.0
        ),
        "at_least_5_of_6_entry_years_nonnegative": (
            policy_closed["nonnegative_entry_years"] >= 5
        ),
        "weekly_block_bootstrap_lower_bound_above_zero": (
            bootstrap["lower_95_one_sided_usd"] > 0.0
        ),
        "leverage_adjusted_delta_above_zero": leverage_adjusted_delta > 0.0,
    }


def risk_gates(
    floating: dict[str, Any], limits: dict[str, float], broker_audit: dict[str, Any]
) -> dict[str, bool]:
    return {
        "lot_values_broker_expressible": set(broker_audit["lot_values"]).issubset(
            {0.01, 0.02}
        ),
        "no_missing_risk_trade_doubled": (
            broker_audit["accepted_double_missing_risk_rows"] == 0
        ),
        "maximum_account_positions_respected": (
            floating["maximum_open_positions"] <= limits["maximum_account_positions"]
        ),
        "maximum_core_positions_respected": (
            floating["maximum_open_core_positions"]
            <= limits["maximum_core_positions"]
        ),
        "maximum_addon_positions_respected": (
            floating["maximum_open_addon_positions"]
            <= limits["maximum_addon_positions"]
        ),
        "known_initial_risk_respected": (
            floating["maximum_known_initial_risk_usd"]
            <= limits["account_initial_risk_usd"] + 1e-9
        ),
        "floating_hard_stop_respected": (
            floating["maximum_floating_drawdown_usd"]
            <= limits["floating_drawdown_hard_stop_usd"]
        ),
    }


def policy_evaluation(
    name: str,
    meta: pd.DataFrame,
    factors: np.ndarray,
    baseline_closed: dict[str, Any],
    baseline_floating: dict[str, Any],
    bars: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    closed, monthly, yearly = closed_metrics(meta, factors)
    floating = weighted_floating_metrics(bars, meta, factors)
    delta = meta[PNL].to_numpy(dtype=float) * (np.asarray(factors) - 1.0)
    bootstrap = moving_week_block_bootstrap(meta, delta)
    naive_leveraged_net = baseline_closed["net_pnl_usd"] * closed["mean_factor"]
    leverage_adjusted_delta = closed["net_pnl_usd"] - naive_leveraged_net
    result = {
        "name": name,
        "closed": closed,
        "floating": floating,
        "delta_pnl_usd": float(
            closed["net_pnl_usd"] - baseline_closed["net_pnl_usd"]
        ),
        "naive_mean_leverage_net_usd": float(naive_leveraged_net),
        "leverage_adjusted_delta_usd": float(leverage_adjusted_delta),
        "weekly_block_bootstrap": bootstrap,
        "gates": gates_for_policy(
            baseline_closed,
            closed,
            baseline_floating,
            floating,
            bootstrap,
            leverage_adjusted_delta,
        ),
    }
    result["historical_gates_passed"] = bool(all(result["gates"].values()))
    return result, monthly, yearly


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def write_markdown(result: dict[str, Any]) -> None:
    base = result["baseline"]
    continuous = result["continuous_policy"]
    broker = result["broker_policy"]
    lines = [
        "# V60 ML Sizing Causal Retest V1 Result",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "Historical research only. No MT5 or runtime authorization is granted.",
        "",
        "## Feature audit",
        "",
        f"- Current V60 population after R5 exclusion and V57 cooldown: "
        f"{result['population_audit']['current_population_rows']} rows.",
        f"- Feature-complete rows: {result['feature_audit']['feature_complete_rows']}.",
        f"- Incomplete bars used: "
        f"{result['feature_audit']['selected_bar_unavailable_at_entry_rows']}.",
        "",
        "## Corrected result",
        "",
        "| policy | trades | net | PF | win rate | closed DD | floating DD | net/floating DD | delta years >= 0 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, item in (
        ("V60 baseline", base),
        ("Continuous ML", continuous),
        ("Broker ML", broker),
    ):
        closed = item["closed"]
        floating = item["floating"]
        lines.append(
            f"| {label} | {closed['trade_rows']} | ${closed['net_pnl_usd']:.2f} | "
            f"{closed['profit_factor']:.3f} | "
            f"{100.0 * closed['win_rate']:.2f}% | "
            f"${closed['closed_trade_drawdown_usd']:.2f} | "
            f"${floating['maximum_floating_drawdown_usd']:.2f} | "
            f"{floating['net_to_floating_drawdown']:.2f} | "
            f"{closed['nonnegative_entry_years']}/{closed['evaluated_entry_years']} |"
        )
    lines.extend(
        [
            "",
            "## Gates",
            "",
            f"- Continuous historical gates: "
            f"{'PASS' if continuous['historical_gates_passed'] else 'FAIL'}.",
            f"- Broker historical gates: "
            f"{'PASS' if broker['historical_gates_passed'] else 'FAIL'}.",
            f"- Broker risk gates: "
            f"{'PASS' if broker['risk_gates_passed'] else 'FAIL'}.",
            f"- Continuous delta versus baseline: "
            f"${continuous['delta_pnl_usd']:.2f}; mean multiplier "
            f"{continuous['closed']['mean_factor']:.4f}.",
            f"- Broker delta versus baseline: ${broker['delta_pnl_usd']:.2f}; "
            f"{broker['broker_audit']['skipped_rows']} trades skipped and "
            f"{broker['broker_audit']['accepted_double_rows']} trades doubled.",
            f"- Continuous weekly-block lower bound: "
            f"${continuous['weekly_block_bootstrap']['lower_95_one_sided_usd']:.2f}.",
            f"- Broker weekly-block lower bound: "
            f"${broker['weekly_block_bootstrap']['lower_95_one_sided_usd']:.2f}.",
            "",
            "## Demo verdict",
            "",
            result["demo_verdict"],
            "",
        ]
    )
    (OUTPUTS / "RESULT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    contract = load_contract()
    feature_module = load_module("codex_claude_features", FEATURES_PATH)
    cooldown_module = load_module("codex_v60_cooldown", COOLDOWN_PATH)
    floating_module = load_module("codex_v60_floating", FLOATING_AUDIT_PATH)
    demo_config_path = REPO_ROOT / contract["inputs"]["current_demo_config"]["path"]
    demo_config = json.loads(demo_config_path.read_text(encoding="utf-8"))

    ledger, population_audit = load_current_population(contract, cooldown_module)
    X, meta, feature_audit = build_corrected_features(ledger, feature_module)
    primary = walkforward(
        X, meta, contract, int(contract["model"]["primary_seed"])
    )
    scored = primary["continuous_multiplier"].notna().to_numpy()
    X_scored = X.loc[scored].reset_index(drop=True)
    meta_scored = meta.loc[scored].reset_index(drop=True)
    primary = primary.loc[scored].reset_index(drop=True)
    if len(meta_scored) == 0:
        raise ValueError("No corrected out-of-time trades were scored")

    sensitivity = []
    for seed in contract["model"]["diagnostic_seeds"]:
        diagnostic = walkforward(X, meta, contract, int(seed)).loc[scored]
        sensitivity.append(
            {
                "seed": int(seed),
                "mean_multiplier": float(
                    diagnostic["continuous_multiplier"].mean()
                ),
                "net_pnl_usd": float(
                    (
                        meta_scored[PNL].to_numpy()
                        * diagnostic["continuous_multiplier"].to_numpy()
                    ).sum()
                ),
            }
        )

    bars, market_audit = load_floating_bars(floating_module, meta_scored)
    baseline_factors = np.ones(len(meta_scored), dtype=float)
    baseline_closed, baseline_monthly, baseline_yearly = closed_metrics(
        meta_scored, baseline_factors
    )
    baseline_floating = weighted_floating_metrics(
        bars, meta_scored, baseline_factors
    )
    baseline = {
        "name": "V60 baseline",
        "closed": baseline_closed,
        "floating": baseline_floating,
    }

    continuous_factors = primary["continuous_multiplier"].to_numpy(dtype=float)
    continuous, continuous_monthly, continuous_yearly = policy_evaluation(
        "Continuous causal ML sizing",
        meta_scored,
        continuous_factors,
        baseline_closed,
        baseline_floating,
        bars,
    )

    limits = demo_limits(demo_config)
    executable_factors, broker_audit = broker_factors(
        meta_scored,
        continuous_factors,
        demo_config,
        limits,
        contract,
    )
    broker, broker_monthly, broker_yearly = policy_evaluation(
        "Broker-expressible causal ML sizing",
        meta_scored,
        executable_factors,
        baseline_closed,
        baseline_floating,
        bars,
    )
    broker["broker_audit"] = broker_audit
    broker["risk_limits"] = limits
    broker["risk_gates"] = risk_gates(
        broker["floating"], limits, broker_audit
    )
    broker["risk_gates_passed"] = bool(all(broker["risk_gates"].values()))

    feature_gate = (
        feature_audit["selected_bar_unavailable_at_entry_rows"] == 0
    )
    deployable = bool(
        feature_gate
        and continuous["historical_gates_passed"]
        and broker["historical_gates_passed"]
        and broker["risk_gates_passed"]
    )
    decision = (
        "HISTORICAL_GATES_PASS_PROSPECTIVE_DEMO_SHADOW_CANDIDATE_ONLY"
        if deployable
        else "HISTORICAL_OR_EXECUTION_GATES_FAIL_KEEP_ML_OFF_DEMO"
    )
    demo_verdict = (
        "The corrected evidence is sufficient only to prepare a fail-closed "
        "prospective demo-shadow candidate. It does not authorize broker sizing."
        if deployable
        else "Do not apply this ML overlay to demo orders. Keep deterministic "
        "V60 unchanged while a different prospective ML candidate is evaluated."
    )

    decision_rows = meta_scored.copy()
    decision_rows = pd.concat([decision_rows, primary], axis=1)
    decision_rows["broker_factor"] = executable_factors
    decision_rows["broker_lot"] = executable_factors * 0.01
    decision_rows["baseline_pnl_usd"] = decision_rows[PNL]
    decision_rows["continuous_pnl_usd"] = (
        decision_rows[PNL] * decision_rows["continuous_multiplier"]
    )
    decision_rows["broker_pnl_usd"] = (
        decision_rows[PNL] * decision_rows["broker_factor"]
    )

    result = {
        "schema_version": "codex_v60_ml_sizing_causal_retest_result_v1",
        "decision": decision,
        "demo_verdict": demo_verdict,
        "runtime_changed": False,
        "contract_sha256": sha256_file(CONTRACT_PATH),
        "population_audit": population_audit,
        "feature_audit": feature_audit,
        "scored_rows": int(len(meta_scored)),
        "test_entry_years": sorted(
            int(value) for value in meta_scored["entry_time"].dt.year.unique()
        ),
        "market_data_audit": market_audit,
        "baseline": baseline,
        "continuous_policy": continuous,
        "broker_policy": broker,
        "diagnostic_seed_sensitivity": sensitivity,
        "limitations": [
            "The architecture was selected after historical outcomes were exposed.",
            "Weekly moving-block bootstrap is diagnostic and not a new holdout.",
            "R1 historical initial risk is missing; no R1 trade may be doubled.",
            "The broker policy changes frequency and is not the continuous policy.",
            "Prospective evidence is required before any broker-affecting ML use.",
            "M5 bar extremes cannot order an intrabar entry against the bar high or low.",
            "The historical paths do not simulate stop-and-restart behavior after a current-account hard stop.",
        ],
    }
    result = json_ready(result)

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    X_scored.to_parquet(OUTPUTS / "CORRECTED_FEATURES.parquet", index=False)
    meta_scored.to_parquet(OUTPUTS / "CORRECTED_META.parquet", index=False)
    decision_rows.to_parquet(OUTPUTS / "PRIMARY_DECISIONS.parquet", index=False)
    baseline_monthly.rename(
        columns={"policy_pnl_usd": "baseline_policy_pnl_usd"}
    ).to_csv(OUTPUTS / "BASELINE_MONTHLY.csv", index=False)
    continuous_monthly.to_csv(OUTPUTS / "CONTINUOUS_MONTHLY.csv", index=False)
    broker_monthly.to_csv(OUTPUTS / "BROKER_MONTHLY.csv", index=False)
    baseline_yearly.rename(
        columns={"policy_pnl_usd": "baseline_policy_pnl_usd"}
    ).to_csv(OUTPUTS / "BASELINE_YEARLY.csv", index=False)
    continuous_yearly.to_csv(OUTPUTS / "CONTINUOUS_YEARLY.csv", index=False)
    broker_yearly.to_csv(OUTPUTS / "BROKER_YEARLY.csv", index=False)
    (OUTPUTS / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(result)

    integrity_files = [
        path
        for path in sorted(OUTPUTS.iterdir())
        if path.name != "INTEGRITY.json" and path.is_file()
    ]
    integrity = {
        "schema_version": "codex_v60_ml_sizing_causal_retest_integrity_v1",
        "contract_sha256": sha256_file(CONTRACT_PATH),
        "files": {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in integrity_files
        },
    }
    integrity["integrity_sha256"] = canonical_sha256(integrity)
    (OUTPUTS / "INTEGRITY.json").write_text(
        json.dumps(integrity, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0
