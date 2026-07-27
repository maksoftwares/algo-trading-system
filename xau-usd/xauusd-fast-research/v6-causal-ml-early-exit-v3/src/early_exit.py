from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss, roc_auc_score


REPO_ROOT = Path(__file__).resolve().parents[4]
LANE_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_FEATURE_TOKENS = (
    "exit",
    "pnl",
    "label",
    "target",
    "future",
    "winner",
    "original",
    "benefit",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def resolve_path(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def verify_sources(config: Mapping[str, Any]) -> dict[str, str]:
    observed: dict[str, str] = {}
    for name, source in config["sources"].items():
        path = resolve_path(source["path"])
        if not path.is_file():
            raise FileNotFoundError(f"Missing locked source {name}: {path}")
        actual = sha256_file(path)
        if actual != source["sha256"]:
            raise ValueError(
                f"Locked source drift for {name}: "
                f"expected {source['sha256']}, got {actual}"
            )
        observed[name] = actual
    return observed


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def validate_feature_contract(config: Mapping[str, Any]) -> list[str]:
    names = (
        list(config["features"]["numeric"])
        + list(config["features"]["derived"])
        + [
            f"entry_regime_{regime}"
            for regime in config["features"]["regimes"]
        ]
        + [
            f"current_regime_{regime}"
            for regime in config["features"]["regimes"]
        ]
    )
    invalid = [
        name
        for name in names
        if any(token in name.lower() for token in FORBIDDEN_FEATURE_TOKENS)
    ]
    if invalid:
        raise ValueError(f"Outcome-derived feature names are forbidden: {invalid}")
    if len(names) != len(set(names)):
        raise ValueError("Duplicate ML feature names")
    return names


def build_feature_matrix(
    snapshots: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    required = {
        "long",
        "entry_regime",
        "current_regime",
        *config["features"]["numeric"],
    }
    missing = sorted(required.difference(snapshots.columns))
    if missing:
        raise ValueError(f"Snapshot input is missing columns: {missing}")
    frame = pd.DataFrame(index=snapshots.index)
    for name in config["features"]["numeric"]:
        frame[name] = pd.to_numeric(snapshots[name], errors="raise").astype(float)
    frame["direction_long"] = snapshots["long"].astype(bool).astype(float)
    regimes = set(config["features"]["regimes"])
    for column in ("entry_regime", "current_regime"):
        observed = set(snapshots[column].astype(str))
        unknown = sorted(observed.difference(regimes))
        if unknown:
            raise ValueError(f"Unexpected {column} classes: {unknown}")
        for regime in config["features"]["regimes"]:
            frame[f"{column}_{regime}"] = (
                snapshots[column].astype(str).eq(regime).astype(float)
            )
    frame = frame.loc[:, validate_feature_contract(config)]
    if not np.isfinite(frame.to_numpy(dtype=float)).all():
        raise ValueError("ML feature matrix contains non-finite values")
    return frame


def safe_auc(labels: pd.Series | np.ndarray, probabilities: np.ndarray) -> float:
    target = np.asarray(labels, dtype=int)
    if len(np.unique(target)) < 2:
        return 0.5
    return float(roc_auc_score(target, probabilities))


def decision_day_equal_weights(snapshots: pd.DataFrame) -> np.ndarray:
    days = pd.to_datetime(snapshots["decision_time"], utc=True).dt.floor("D")
    counts = days.map(days.value_counts()).to_numpy(dtype=float)
    weights = 1.0 / counts
    return weights / weights.mean()


def annual_training_split(
    snapshots: pd.DataFrame, target_year: int, purge_hours: float
) -> pd.DataFrame:
    cutoff = pd.Timestamp(f"{target_year}-01-01", tz="UTC")
    purge = pd.Timedelta(hours=purge_hours)
    return snapshots.loc[
        pd.to_datetime(snapshots["original_exit_time"], utc=True).lt(cutoff - purge)
    ].copy()


def build_snapshots(
    trades: pd.DataFrame,
    context: Mapping[str, Any],
    config: Mapping[str, Any],
    stress: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = trades.reset_index(drop=True).copy()
    cap = context["cap"]
    cap_t = np.asarray(context["cap_t"], dtype="datetime64[ns]")
    bid_open = cap["bid_open"].to_numpy(dtype=float)
    bid_low = cap["bid_low"].to_numpy(dtype=float)
    bid_close = cap["bid_close"].to_numpy(dtype=float)
    ask_open = cap["ask_open"].to_numpy(dtype=float)
    ask_high = cap["ask_high"].to_numpy(dtype=float)
    ask_close = cap["ask_close"].to_numpy(dtype=float)

    duka_t = pd.to_datetime(context["t"], utc=True).dt.tz_localize(None).to_numpy()
    duka_regime = np.asarray(context["reg"], dtype=str)
    csm = np.asarray(context["csm"], dtype=float)
    cbi = np.asarray(context["cbi"], dtype=float)
    ctc = np.asarray(context["ctc"], dtype=float)
    cts = np.asarray(context["cts"], dtype=float)
    cpe = np.asarray(context["cpe"], dtype=float)
    slope = np.nan_to_num(np.asarray(context["slope"], dtype=float))

    checkpoints = [int(value) for value in config["snapshots"]["checkpoint_minutes"]]
    bar_minutes = int(config["snapshots"]["bar_minutes"])
    material_r = float(config["snapshots"]["material_benefit_r"])
    base_fee = float(stress["base_fee_usd"])
    additional = float(stress["additional_fixed_cost_usd"])
    holding_per_day = float(stress["holding_cost_usd_per_24h"])
    slippage_r = float(stress["slippage_r"])
    entry_time = pd.to_datetime(frame["entry_time"], utc=True)
    original_exit_time = pd.to_datetime(frame["exit_time"], utc=True)
    entry_np = entry_time.dt.tz_localize(None).to_numpy()
    original_exit_np = original_exit_time.dt.tz_localize(None).to_numpy()
    entry_index = np.searchsorted(cap_t, entry_np)
    safe_entry_index = np.clip(entry_index, 0, len(cap_t) - 1)
    entry_match = (entry_index < len(cap_t)) & (
        cap_t[safe_entry_index] == entry_np
    )
    long = frame["long"].astype(bool).to_numpy()
    sign = np.where(long, 1.0, -1.0)
    entry_price_column = (
        "entry_price" if "entry_price" in frame else "cap_entry_price"
    )
    risk_column = "risk_usd" if "risk_usd" in frame else "stop_usd"
    entry_price = pd.to_numeric(
        frame[entry_price_column], errors="raise"
    ).to_numpy(dtype=float)
    risk = pd.to_numeric(frame[risk_column], errors="raise").to_numpy(dtype=float)
    if (risk <= 0.0).any():
        raise ValueError("Snapshot trade has non-positive initial risk")
    original_stress = pd.to_numeric(
        frame["fee_stress_pnl_usd"], errors="raise"
    ).to_numpy(dtype=float)
    entry_regime = frame["regime"].astype(str).to_numpy()
    if "trade_id" in frame:
        source_trade_id = frame["trade_id"].astype(str).to_numpy()
    else:
        source_trade_id = np.asarray(
            [
                f"BROAD_{int(i)}_{'L' if is_long else 'S'}"
                for i, is_long in zip(frame["i"], long)
            ]
        )
    i_values = pd.to_numeric(frame["i"], errors="raise").to_numpy(dtype=int)
    snapshot_frames: list[pd.DataFrame] = []

    for checkpoint in checkpoints:
        bars = checkpoint // bar_minutes
        decision_index = entry_index + bars - 1
        execution_index = decision_index + 1
        safe_decision = np.clip(decision_index, 0, len(cap_t) - 1)
        safe_execution = np.clip(execution_index, 0, len(cap_t) - 1)
        duka_index = (
            np.searchsorted(duka_t, cap_t[safe_decision], side="right") - 1
        )
        valid = (
            entry_match
            & (execution_index < len(cap_t))
            & (cap_t[safe_execution] < original_exit_np)
            & (duka_index >= 0)
        )
        take = np.flatnonzero(valid)
        if not len(take):
            continue
        selected_entry = entry_index[take]
        selected_decision = decision_index[take]
        selected_execution = execution_index[take]
        selected_duka = duka_index[take]
        selected_long = long[take]
        selected_sign = sign[take]
        selected_entry_price = entry_price[take]
        selected_risk = risk[take]
        selected_original_stress = original_stress[take]
        path_index = selected_entry[:, None] + np.arange(bars)[None, :]
        path_marks = np.where(
            selected_long[:, None],
            bid_close[path_index],
            ask_close[path_index],
        )
        path_r = (
            selected_sign[:, None]
            * (path_marks - selected_entry_price[:, None])
            / selected_risk[:, None]
        )
        current_mark = path_marks[:, -1]
        current_r = path_r[:, -1]
        close_min_r = path_r.min(axis=1)
        close_max_r = path_r.max(axis=1)
        prior_15 = (
            path_marks[:, bars - 1 - 3]
            if bars - 1 - 3 >= 0
            else selected_entry_price
        )
        prior_30 = (
            path_marks[:, bars - 1 - 6]
            if bars - 1 - 6 >= 0
            else selected_entry_price
        )
        long_adverse = (
            selected_entry_price - bid_low[path_index].min(axis=1)
        ) / selected_risk
        short_adverse = (
            ask_high[path_index].max(axis=1) - selected_entry_price
        ) / selected_risk
        max_adverse_r = np.maximum(
            0.0, np.where(selected_long, long_adverse, short_adverse)
        )
        early_price = np.where(
            selected_long,
            bid_open[selected_execution],
            ask_open[selected_execution],
        )
        duka_end = selected_duka + 1
        duka_begin = np.maximum(0, duka_end - 6)
        duka_count = duka_end - duka_begin
        current_regime = duka_regime[selected_duka]
        early_open_cost = (
            base_fee
            + additional
            + holding_per_day * (checkpoint / 1440.0)
            + slippage_r * selected_risk
        )
        early_base_pnl = (
            selected_sign * (early_price - selected_entry_price) - base_fee
        )
        early_stress_pnl = (
            selected_sign * (early_price - selected_entry_price)
            - early_open_cost
        )
        benefit = early_stress_pnl - selected_original_stress
        material_benefit = material_r * selected_risk
        labels = (
            (selected_original_stress < 0.0) & (benefit >= material_benefit)
        ).astype(int)
        checkpoint_ids = source_trade_id[take]
        snapshot_frames.append(
            pd.DataFrame(
                {
                    "snapshot_id": np.char.add(
                        np.char.add(checkpoint_ids.astype(str), "_"),
                        str(checkpoint),
                    ),
                    "source_trade_id": checkpoint_ids,
                    "i": i_values[take],
                    "long": selected_long,
                    "direction": np.where(selected_long, "LONG", "SHORT"),
                    "entry_time": entry_time.iloc[take].reset_index(drop=True),
                    "original_exit_time": original_exit_time.iloc[take].reset_index(
                        drop=True
                    ),
                    "decision_time": pd.to_datetime(
                        cap_t[selected_decision], utc=True
                    )
                    + pd.Timedelta(minutes=bar_minutes),
                    "early_exit_time": pd.to_datetime(
                        cap_t[selected_execution], utc=True
                    ),
                    "checkpoint_minutes": checkpoint,
                    "elapsed_hours": checkpoint / 60.0,
                    "entry_price": selected_entry_price,
                    "early_exit_price": early_price,
                    "risk_usd": selected_risk,
                    "original_stress_pnl_usd": selected_original_stress,
                    "early_base_pnl_usd": early_base_pnl,
                    "early_stress_open_cost_usd": early_open_cost,
                    "early_stress_pnl_usd": early_stress_pnl,
                    "benefit_usd": benefit,
                    "material_benefit_usd": material_benefit,
                    "label": labels,
                    "current_r": current_r,
                    "recent_15m_r": selected_sign
                    * (current_mark - prior_15)
                    / selected_risk,
                    "recent_30m_r": selected_sign
                    * (current_mark - prior_30)
                    / selected_risk,
                    "close_min_r": close_min_r,
                    "close_max_r": close_max_r,
                    "max_adverse_r": max_adverse_r,
                    "giveback_r": close_max_r - current_r,
                    "recovery_r": current_r - close_min_r,
                    "duka_flow_30m": selected_sign
                    * (csm[duka_end] - csm[duka_begin]),
                    "duka_imbalance_30m": selected_sign
                    * (cbi[duka_end] - cbi[duka_begin])
                    / duka_count,
                    "duka_activity_30m": (
                        ctc[duka_end] - ctc[duka_begin]
                    )
                    / duka_count,
                    "duka_spread_per_risk_30m": (
                        (cts[duka_end] - cts[duka_begin]) / duka_count
                    )
                    / selected_risk,
                    "duka_efficiency_30m": (
                        cpe[duka_end] - cpe[duka_begin]
                    )
                    / duka_count,
                    "duka_slope": slope[selected_duka],
                    "regime_changed": (
                        current_regime != entry_regime[take]
                    ).astype(float),
                    "entry_regime": entry_regime[take],
                    "current_regime": current_regime,
                }
            )
        )
    snapshots = (
        pd.concat(snapshot_frames, ignore_index=True)
        if snapshot_frames
        else pd.DataFrame()
    )
    if snapshots.empty:
        raise ValueError("No causal post-entry snapshots were built")
    if snapshots.duplicated("snapshot_id").any():
        raise ValueError("Duplicate snapshot IDs")
    if snapshots["early_exit_time"].ge(snapshots["original_exit_time"]).any():
        raise ValueError("Snapshot execution is not strictly before original exit")
    build_feature_matrix(snapshots, config)
    audit = {
        "input_trades": int(len(trades)),
        "snapshots": int(len(snapshots)),
        "unique_trades_with_snapshots": int(snapshots["source_trade_id"].nunique()),
        "positive_label_share": float(snapshots["label"].mean()),
        "skipped_missing_capital_entry": int((~entry_match).sum()),
        "first_decision_time": snapshots["decision_time"].min().isoformat(),
        "last_decision_time": snapshots["decision_time"].max().isoformat(),
    }
    return snapshots.sort_values(
        ["entry_time", "source_trade_id", "checkpoint_minutes"],
        kind="mergesort",
    ).reset_index(drop=True), audit


def make_model(config: Mapping[str, Any]) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(**dict(config["model"]["parameters"]))


def annual_walk_forward_predictions(
    training_snapshots: pd.DataFrame,
    target_snapshots: pd.DataFrame,
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    settings = config["walk_forward"]
    threshold = float(config["snapshots"]["probability_threshold"])
    predictions: list[pd.DataFrame] = []
    logs: list[dict[str, Any]] = []
    for year in settings["target_years"]:
        year = int(year)
        train = annual_training_split(
            training_snapshots, year, float(settings["purge_hours"])
        )
        target = target_snapshots.loc[
            pd.to_datetime(target_snapshots["entry_time"], utc=True).dt.year.eq(year)
        ].copy()
        if len(train) < int(settings["minimum_training_rows"]):
            raise ValueError(f"Insufficient training snapshots for {year}: {len(train)}")
        if target.empty:
            raise ValueError(f"No frozen V1 target snapshots for {year}")
        model = make_model(config)
        model.fit(
            build_feature_matrix(train, config),
            train["label"].astype(int),
            sample_weight=decision_day_equal_weights(train),
        )
        probability = model.predict_proba(build_feature_matrix(target, config))[:, 1]
        target["exit_probability"] = probability
        target["exit_trigger"] = target["exit_probability"].ge(threshold)
        predictions.append(target)
        triggered = target.loc[target["exit_trigger"]]
        logs.append(
            {
                "target_year": year,
                "training_rows": int(len(train)),
                "training_positive_share": float(train["label"].mean()),
                "training_last_original_exit_time": train[
                    "original_exit_time"
                ].max(),
                "target_rows": int(len(target)),
                "target_positive_share": float(target["label"].mean()),
                "target_auc": safe_auc(target["label"], probability),
                "target_brier": float(brier_score_loss(target["label"], probability)),
                "triggered_snapshots": int(len(triggered)),
                "trigger_precision": (
                    float(triggered["label"].mean()) if len(triggered) else 0.0
                ),
            }
        )
    result = pd.concat(predictions, ignore_index=True).sort_values(
        ["entry_time", "source_trade_id", "checkpoint_minutes"],
        kind="mergesort",
    )
    return result.reset_index(drop=True), pd.DataFrame(logs)


def apply_first_exit_signal(
    selected_trades: pd.DataFrame, predictions: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    triggered = predictions.loc[predictions["exit_trigger"]].sort_values(
        ["source_trade_id", "checkpoint_minutes"], kind="mergesort"
    )
    first = triggered.drop_duplicates("source_trade_id", keep="first").set_index(
        "source_trade_id"
    )
    managed_rows: list[pd.Series] = []
    actions: list[dict[str, Any]] = []
    for _, source in selected_trades.iterrows():
        row = source.copy()
        trade_id = str(row["trade_id"])
        row["original_exit_time"] = row["exit_time"]
        row["original_exit_price"] = row["exit_price"]
        row["original_pnl_usd"] = row["pnl_usd"]
        row["original_fee_stress_pnl_usd"] = row["fee_stress_pnl_usd"]
        row["managed_by_ml"] = trade_id in first.index
        row["management_action"] = "HOLD_ORIGINAL"
        row["management_probability"] = np.nan
        row["management_checkpoint_minutes"] = np.nan
        if trade_id in first.index:
            signal = first.loc[trade_id]
            risk = float(row["risk_usd"])
            row["exit_time"] = signal["early_exit_time"]
            row["exit_price"] = float(signal["early_exit_price"])
            row["pnl_usd"] = float(signal["early_base_pnl_usd"])
            row["fee_stress_pnl_usd"] = float(signal["early_stress_pnl_usd"])
            row["open_cost_usd"] = float(row["pnl_usd"]) - (
                (1.0 if bool(row["long"]) else -1.0)
                * (float(row["exit_price"]) - float(row["entry_price"]))
            )
            row["open_cost_usd"] = abs(float(row["open_cost_usd"]))
            row["fee_stress_open_cost_usd"] = float(
                signal["early_stress_open_cost_usd"]
            )
            row["net_r"] = float(row["pnl_usd"]) / risk
            row["stress_net_r"] = float(row["fee_stress_pnl_usd"]) / risk
            row["managed_by_ml"] = True
            row["management_action"] = "EARLY_EXIT"
            row["management_probability"] = float(signal["exit_probability"])
            row["management_checkpoint_minutes"] = int(
                signal["checkpoint_minutes"]
            )
        managed_rows.append(row)
        actions.append(
            {
                "trade_id": trade_id,
                "management_action": row["management_action"],
                "management_probability": row["management_probability"],
                "management_checkpoint_minutes": row[
                    "management_checkpoint_minutes"
                ],
                "original_exit_time": row["original_exit_time"],
                "managed_exit_time": row["exit_time"],
                "original_fee_stress_pnl_usd": row[
                    "original_fee_stress_pnl_usd"
                ],
                "managed_fee_stress_pnl_usd": row["fee_stress_pnl_usd"],
            }
        )
    managed = pd.DataFrame(managed_rows).reset_index(drop=True)
    sign = np.where(managed["direction"].eq("LONG"), 1.0, -1.0)
    reconciled = (
        sign * (managed["exit_price"] - managed["entry_price"])
        - managed["fee_stress_open_cost_usd"]
    )
    if not np.allclose(
        reconciled.to_numpy(dtype=float),
        managed["fee_stress_pnl_usd"].to_numpy(dtype=float),
        atol=1e-9,
    ):
        raise ValueError("Managed price/P&L reconciliation failed")
    return managed, pd.DataFrame(actions)


def trade_comparison(
    frozen: pd.DataFrame,
    managed: pd.DataFrame,
    baseline: pd.DataFrame,
    windows: Mapping[str, list[str]],
    trade_metrics: Any,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    top = int(config["gates"]["top_winners_removed"])
    minimum = int(config["gates"]["minimum_managed_accepted_trades_per_window"])
    for name, bounds in windows.items():
        start, end = map(pd.Timestamp, bounds)

        def select(frame: pd.DataFrame) -> pd.DataFrame:
            return frame.loc[
                frame["entry_time"].ge(start) & frame["entry_time"].lt(end)
            ].copy()

        base = select(baseline)
        old = select(frozen)
        new = select(managed)
        old_combined = pd.concat([base, old], ignore_index=True)
        new_combined = pd.concat([base, new], ignore_index=True)
        old_m = trade_metrics(old, top)
        new_m = trade_metrics(new, top)
        old_c = trade_metrics(old_combined, top)
        new_c = trade_metrics(new_combined, top)
        checks = {
            "minimum_managed_accepted_trades": new_m["trades"] >= minimum,
            "managed_v6_net_no_worse_than_v1": new_m["stress_net_usd"]
            >= old_m["stress_net_usd"] - 1e-9,
            "managed_v6_pf_no_worse_than_v1": new_m["stress_profit_factor"]
            >= old_m["stress_profit_factor"] - 1e-9,
            "managed_v6_drawdown_no_worse_than_v1": new_m[
                "stress_closed_drawdown_usd"
            ]
            <= old_m["stress_closed_drawdown_usd"] + 1e-9,
            "managed_combined_net_no_worse_than_v1": new_c["stress_net_usd"]
            >= old_c["stress_net_usd"] - 1e-9,
            "managed_combined_pf_no_worse_than_v1": new_c["stress_profit_factor"]
            >= old_c["stress_profit_factor"] - 1e-9,
            "managed_combined_drawdown_no_worse_than_v1": new_c[
                "stress_closed_drawdown_usd"
            ]
            <= old_c["stress_closed_drawdown_usd"] + 1e-9,
        }
        rows.append(
            {
                "window": name,
                **{f"v1_v6_{key}": value for key, value in old_m.items()},
                **{f"managed_v6_{key}": value for key, value in new_m.items()},
                **{f"v1_combined_{key}": value for key, value in old_c.items()},
                **{f"managed_combined_{key}": value for key, value in new_c.items()},
                "checks": checks,
                "passed": all(checks.values()),
            }
        )
    return pd.DataFrame(rows)
