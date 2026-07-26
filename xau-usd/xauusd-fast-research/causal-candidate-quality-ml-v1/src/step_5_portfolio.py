from __future__ import annotations

import heapq
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from step_3_common import canonical_json_sha256, sha256_file


REQUIRED_COLUMNS = {
    "candidate_id",
    "family_id",
    "broad_mechanic",
    "direction",
    "structural_episode_id",
    "entry_time",
    "label_end_time",
    "entry_price",
    "exit_price",
    "initial_risk_usd_0p01",
    "stress_net_r",
    "label_status",
    "broker_executable",
    "historical_portfolio_accepted",
    "log1p_observation_cap_minutes",
    "planned_stop_price",
}


def build_market_manifest(market: Mapping[str, Any]) -> dict[str, Any]:
    records: dict[str, Any] = {}
    modern = Path(str(market["modern_m5"]["path"])).resolve()
    if not modern.is_file():
        raise FileNotFoundError(modern)
    records["modern_m5"] = {
        "path": modern.as_posix(),
        "bytes": modern.stat().st_size,
        "sha256": sha256_file(modern),
    }
    for side in ("bid", "ask"):
        spec = market[f"legacy_{side}_m5"]
        root = Path(str(spec["root"])).resolve()
        files = sorted(root.glob(str(spec["pattern"])))
        if len(files) != int(spec["expected_files"]):
            raise ValueError(f"Unexpected legacy {side} file count: {len(files)}")
        records[f"legacy_{side}_m5"] = [
            {
                "path": path.resolve().as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ]
    return {
        "schema_version": "xauusd_step_5_m5_source_manifest_v1",
        "records": records,
        "manifest_sha256": canonical_json_sha256(records),
    }


def verify_market_manifest(manifest: Mapping[str, Any]) -> None:
    records = manifest["records"]
    flattened = [records["modern_m5"]]
    flattened.extend(records["legacy_bid_m5"])
    flattened.extend(records["legacy_ask_m5"])
    for row in flattened:
        path = Path(str(row["path"]))
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.stat().st_size != int(row["bytes"]):
            raise ValueError(f"M5 byte-size mismatch: {path}")
        if sha256_file(path) != str(row["sha256"]):
            raise ValueError(f"M5 hash mismatch: {path}")
    if canonical_json_sha256(records) != str(manifest["manifest_sha256"]):
        raise ValueError("M5 manifest digest mismatch")


def load_m5_bars(
    market: Mapping[str, Any], locked_manifest: Mapping[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    verify_market_manifest(locked_manifest)
    modern_spec = market["modern_m5"]
    modern_path = Path(str(modern_spec["path"]))
    if sha256_file(modern_path) != str(modern_spec["sha256"]):
        raise ValueError("Modern M5 configuration hash mismatch")
    columns = [
        "timestamp_ms",
        "bid_open",
        "bid_high",
        "bid_low",
        "bid_close",
        "ask_open",
        "ask_high",
        "ask_low",
        "ask_close",
    ]
    modern = pd.read_parquet(modern_path, columns=columns)
    if len(modern) != int(modern_spec["expected_rows"]):
        raise ValueError("Unexpected modern M5 row count")

    legacy: dict[str, pd.DataFrame] = {}
    for side in ("bid", "ask"):
        source = market[f"legacy_{side}_m5"]
        file_rows = locked_manifest["records"][f"legacy_{side}_m5"]
        frames = [pd.read_parquet(str(row["path"])) for row in file_rows]
        frame = pd.concat(frames, ignore_index=True)
        if len(frame) != int(source["expected_rows"]):
            raise ValueError(f"Unexpected legacy {side} M5 row count")
        legacy[side] = frame[["timestamp_ms", "open", "high", "low", "close"]].rename(
            columns={name: f"{side}_{name}" for name in ("open", "high", "low", "close")}
        )
    old = legacy["bid"].merge(
        legacy["ask"], on="timestamp_ms", how="outer", validate="one_to_one"
    )
    if old.isna().any().any():
        raise ValueError("Legacy bid and ask M5 timestamps differ")
    bars = pd.concat([old, modern], ignore_index=True)
    bars = bars.sort_values("timestamp_ms", kind="stable").reset_index(drop=True)
    if bars["timestamp_ms"].duplicated().any():
        raise ValueError("Duplicate M5 timestamps")
    quote_columns = [column for column in bars.columns if column != "timestamp_ms"]
    if not np.isfinite(bars[quote_columns].to_numpy(dtype=float)).all():
        raise ValueError("Nonfinite M5 quote")
    bars["timestamp_utc"] = pd.to_datetime(bars["timestamp_ms"], unit="ms", utc=True)
    return bars, {
        "rows": len(bars),
        "first_bar_utc": bars["timestamp_utc"].iloc[0].isoformat(),
        "last_bar_utc": bars["timestamp_utc"].iloc[-1].isoformat(),
        "manifest_sha256": locked_manifest["manifest_sha256"],
    }


def prepare_candidate_economics(
    frame: pd.DataFrame, account: Mapping[str, Any]
) -> pd.DataFrame:
    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing Step 5 columns: {missing}")
    if frame["candidate_id"].duplicated().any():
        raise ValueError("Candidate IDs must be unique")
    result = frame.copy()
    for column in ("entry_time", "label_end_time", "decision_time"):
        result[column] = pd.to_datetime(result[column], utc=True)
    result["initial_risk_usd"] = pd.to_numeric(
        result["initial_risk_usd_0p01"], errors="raise"
    )
    result["pnl_usd"] = (
        pd.to_numeric(result["stress_net_r"], errors="raise")
        * result["initial_risk_usd"]
    )
    result["direction_sign"] = np.where(result["direction"].eq("LONG"), 1.0, -1.0)
    ounces = float(account["xau_ounces_per_reference_lot"])
    result["gross_endpoint_pnl_usd"] = (
        result["direction_sign"]
        * (result["exit_price"] - result["entry_price"])
        * ounces
    )
    result["implied_cost_usd"] = result["gross_endpoint_pnl_usd"] - result["pnl_usd"]
    if result["implied_cost_usd"].lt(-1e-6).any():
        raise ValueError("Negative implied execution cost")
    result["open_cost_usd"] = result["implied_cost_usd"].clip(lower=0.0)
    result["margin_usd"] = (
        result["entry_price"]
        * ounces
        / float(account["conservative_leverage"])
    )
    finite = [
        "entry_price",
        "exit_price",
        "initial_risk_usd",
        "pnl_usd",
        "gross_endpoint_pnl_usd",
        "implied_cost_usd",
        "margin_usd",
    ]
    if not np.isfinite(result[finite].to_numpy(dtype=float)).all():
        raise ValueError("Nonfinite candidate economics")
    if result["initial_risk_usd"].le(0.0).any():
        raise ValueError("Nonpositive initial risk")
    if result["label_end_time"].lt(result["entry_time"]).any():
        raise ValueError("Exit precedes entry")
    endpoint_error = (
        result["gross_endpoint_pnl_usd"]
        - result["implied_cost_usd"]
        - result["pnl_usd"]
    ).abs()
    if float(endpoint_error.max()) > 1e-8:
        raise ValueError("Endpoint P&L reconciliation failed")
    return result


def _family_scope(contract: Mapping[str, Any], scope: str) -> list[str]:
    population = contract["population"]
    if scope == "FIVE":
        return list(population["five_regime_families"])
    if scope == "EXPANDED":
        return list(population["expanded_families"])
    raise ValueError(f"Unknown family scope: {scope}")


def _eligible(frame: pd.DataFrame, contract: Mapping[str, Any]) -> pd.Series:
    prefix = str(contract["population"]["resolved_status_prefix"])
    return frame["broker_executable"].astype(bool) & frame["label_status"].str.startswith(
        prefix
    )


def _episode_candidates(
    frame: pd.DataFrame, contract: Mapping[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    priority = {
        family: index
        for index, family in enumerate(contract["population"]["family_priority"])
    }
    ordered = frame.copy()
    ordered["family_priority"] = ordered["family_id"].map(priority)
    if ordered["family_priority"].isna().any():
        raise ValueError("Family is absent from the frozen priority")
    ordered["horizon_priority"] = pd.to_numeric(
        ordered["log1p_observation_cap_minutes"], errors="coerce"
    ).fillna(np.inf)
    ordered["stop_priority"] = pd.to_numeric(
        ordered["planned_stop_price"], errors="coerce"
    ).fillna(np.inf)
    ordered = ordered.sort_values(
        [
            "structural_episode_id",
            "family_priority",
            "horizon_priority",
            "stop_priority",
            "candidate_id",
        ],
        kind="stable",
    )
    rank = ordered.groupby("structural_episode_id", sort=False).cumcount()
    selected = ordered.loc[rank.eq(0)].drop(
        columns=["family_priority", "horizon_priority", "stop_priority"]
    )
    duplicates = ordered.loc[rank.gt(0)].drop(
        columns=["family_priority", "horizon_priority", "stop_priority"]
    )
    return selected, duplicates


def _decision_row(
    row: Any,
    *,
    policy_id: str,
    accepted: bool,
    reason: str,
    state: Mapping[str, float | int] | None = None,
) -> dict[str, Any]:
    state = state or {}
    return {
        "policy_id": policy_id,
        "candidate_id": str(row.candidate_id),
        "family_id": str(row.family_id),
        "broad_mechanic": str(row.broad_mechanic),
        "direction": str(row.direction),
        "structural_episode_id": str(row.structural_episode_id),
        "entry_time": row.entry_time,
        "label_end_time": row.label_end_time,
        "accepted": bool(accepted),
        "decision_reason": reason,
        "initial_risk_usd": float(row.initial_risk_usd),
        "pnl_usd": float(row.pnl_usd),
        "open_positions_before": state.get("open_positions"),
        "open_initial_risk_before_usd": state.get("open_initial_risk_usd"),
        "open_directional_risk_before_usd": state.get("open_directional_risk_usd"),
        "open_margin_before_usd": state.get("open_margin_usd"),
        "closed_balance_before_usd": state.get("balance_usd"),
        "closed_drawdown_before_usd": state.get("closed_drawdown_usd"),
    }


def _govern_candidates(
    candidates: pd.DataFrame,
    *,
    policy_id: str,
    account: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    starting = float(account["starting_equity_usd"])
    limits = {
        "single_risk": starting
        * float(account["maximum_single_trade_initial_risk_fraction"]),
        "aggregate_risk": starting
        * float(account["maximum_aggregate_initial_risk_fraction"]),
        "directional_risk": starting
        * float(account["maximum_directional_initial_risk_fraction"]),
        "margin": starting * float(account["maximum_margin_fraction"]),
        "daily_loss": starting * float(account["daily_closed_loss_breaker_fraction"]),
        "suspend": starting * float(account["closed_drawdown_suspend_fraction"]),
        "resume": starting * float(account["closed_drawdown_resume_fraction"]),
        "hard_stop": starting * float(account["closed_drawdown_hard_stop_fraction"]),
    }
    ordered = candidates.sort_values(
        ["entry_time", "family_id", "candidate_id"], kind="stable"
    )
    open_positions: dict[str, dict[str, Any]] = {}
    exit_heap: list[tuple[int, str, dict[str, Any]]] = []
    daily_realized: dict[str, float] = {}
    daily_entries: dict[str, int] = {}
    balance = starting
    peak_balance = starting
    suspended = False
    hard_stopped = False
    hard_stop_time: str | None = None
    max_open = 0
    max_risk = 0.0
    max_directional_risk = 0.0
    max_margin = 0.0
    decisions: list[dict[str, Any]] = []

    def close_through(cutoff_ns: int) -> None:
        nonlocal balance, peak_balance, suspended, hard_stopped, hard_stop_time
        while exit_heap and exit_heap[0][0] <= cutoff_ns:
            timestamp_ns = exit_heap[0][0]
            batch: list[dict[str, Any]] = []
            while exit_heap and exit_heap[0][0] == timestamp_ns:
                _, candidate_id, position = heapq.heappop(exit_heap)
                open_positions.pop(candidate_id, None)
                batch.append(position)
            pnl = float(sum(float(position["pnl_usd"]) for position in batch))
            balance += pnl
            exit_time = pd.Timestamp(timestamp_ns, unit="ns", tz="UTC")
            day = exit_time.date().isoformat()
            daily_realized[day] = daily_realized.get(day, 0.0) + pnl
            peak_balance = max(peak_balance, balance)
            drawdown = peak_balance - balance
            if drawdown >= limits["hard_stop"] - 1e-9:
                hard_stopped = True
                if hard_stop_time is None:
                    hard_stop_time = exit_time.isoformat()
            if suspended and drawdown <= limits["resume"] + 1e-9:
                suspended = False
            if drawdown >= limits["suspend"] - 1e-9:
                suspended = True

    for row in ordered.itertuples(index=False):
        entry_ns = int(row.entry_time.value)
        close_through(entry_ns)
        values = list(open_positions.values())
        open_risk = float(sum(float(item["initial_risk_usd"]) for item in values))
        directional_risk = float(
            sum(
                float(item["initial_risk_usd"])
                for item in values
                if item["direction"] == row.direction
            )
        )
        open_margin = float(sum(float(item["margin_usd"]) for item in values))
        drawdown = peak_balance - balance
        state = {
            "open_positions": len(values),
            "open_initial_risk_usd": open_risk,
            "open_directional_risk_usd": directional_risk,
            "open_margin_usd": open_margin,
            "balance_usd": balance,
            "closed_drawdown_usd": drawdown,
        }
        day = row.entry_time.date().isoformat()
        family_open = sum(item["family_id"] == row.family_id for item in values)
        mechanic_open = sum(
            item["broad_mechanic"] == row.broad_mechanic for item in values
        )
        direction_open = sum(item["direction"] == row.direction for item in values)
        reason = "ACCEPTED"
        if hard_stopped:
            reason = "REJECT_HARD_DRAWDOWN_STOP"
        elif suspended:
            reason = "REJECT_DRAWDOWN_SUSPENDED"
        elif daily_realized.get(day, 0.0) <= -limits["daily_loss"] + 1e-9:
            reason = "REJECT_DAILY_CLOSED_LOSS_BREAKER"
        elif float(row.initial_risk_usd) > limits["single_risk"] + 1e-9:
            reason = "REJECT_SINGLE_TRADE_RISK"
        elif daily_entries.get(day, 0) >= int(account["maximum_entries_per_utc_date"]):
            reason = "REJECT_DAILY_ENTRY_CAP"
        elif family_open >= int(account["maximum_positions_per_family"]):
            reason = "REJECT_FAMILY_POSITION_CAP"
        elif mechanic_open >= int(account["maximum_positions_per_broad_mechanic"]):
            reason = "REJECT_MECHANIC_POSITION_CAP"
        elif len(values) >= int(account["maximum_positions"]):
            reason = "REJECT_ACCOUNT_POSITION_CAP"
        elif direction_open >= int(account["maximum_positions_per_direction"]):
            reason = "REJECT_DIRECTION_POSITION_CAP"
        elif open_risk + float(row.initial_risk_usd) > limits["aggregate_risk"] + 1e-9:
            reason = "REJECT_AGGREGATE_INITIAL_RISK"
        elif directional_risk + float(row.initial_risk_usd) > limits["directional_risk"] + 1e-9:
            reason = "REJECT_DIRECTIONAL_INITIAL_RISK"
        elif open_margin + float(row.margin_usd) > limits["margin"] + 1e-9:
            reason = "REJECT_MARGIN_CAP"
        accepted = reason == "ACCEPTED"
        decisions.append(
            _decision_row(
                row,
                policy_id=policy_id,
                accepted=accepted,
                reason=reason,
                state=state,
            )
        )
        if not accepted:
            continue
        position = {
            "candidate_id": str(row.candidate_id),
            "family_id": str(row.family_id),
            "broad_mechanic": str(row.broad_mechanic),
            "direction": str(row.direction),
            "initial_risk_usd": float(row.initial_risk_usd),
            "margin_usd": float(row.margin_usd),
            "pnl_usd": float(row.pnl_usd),
        }
        open_positions[position["candidate_id"]] = position
        heapq.heappush(
            exit_heap,
            (int(row.label_end_time.value), position["candidate_id"], position),
        )
        daily_entries[day] = daily_entries.get(day, 0) + 1
        accepted_values = list(open_positions.values())
        accepted_risk = float(
            sum(float(item["initial_risk_usd"]) for item in accepted_values)
        )
        accepted_margin = float(sum(float(item["margin_usd"]) for item in accepted_values))
        by_direction = [
            sum(
                float(item["initial_risk_usd"])
                for item in accepted_values
                if item["direction"] == direction
            )
            for direction in ("LONG", "SHORT")
        ]
        max_open = max(max_open, len(accepted_values))
        max_risk = max(max_risk, accepted_risk)
        max_margin = max(max_margin, accepted_margin)
        max_directional_risk = max(max_directional_risk, *by_direction)

    close_through(np.iinfo(np.int64).max)
    decision_frame = pd.DataFrame(decisions)
    risk_invariants = {
        "maximum_positions": max_open <= int(account["maximum_positions"]),
        "maximum_aggregate_initial_risk": max_risk <= limits["aggregate_risk"] + 1e-9,
        "maximum_directional_initial_risk": max_directional_risk
        <= limits["directional_risk"] + 1e-9,
        "maximum_margin": max_margin <= limits["margin"] + 1e-9,
    }
    return decision_frame, {
        "accepted_trades": int(decision_frame["accepted"].sum()),
        "ending_closed_balance_usd": balance,
        "maximum_open_positions": max_open,
        "maximum_open_initial_risk_usd": max_risk,
        "maximum_open_directional_risk_usd": max_directional_risk,
        "maximum_open_margin_usd": max_margin,
        "hard_stop_triggered": hard_stopped,
        "hard_stop_time_utc": hard_stop_time,
        "risk_invariants": risk_invariants,
        "risk_invariants_pass": all(risk_invariants.values()),
        "limits_usd": limits,
    }


def _frozen_decisions(
    scope: pd.DataFrame,
    *,
    policy_id: str,
    eligible: pd.Series,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(scope.itertuples(index=False)):
        is_eligible = bool(eligible.iloc[index])
        accepted = is_eligible and bool(row.historical_portfolio_accepted)
        if not is_eligible:
            reason = (
                "REJECT_BROKER_INELIGIBLE"
                if not bool(row.broker_executable)
                else "REJECT_UNRESOLVED_LABEL"
            )
        elif accepted:
            reason = "HISTORICAL_POLICY_ACCEPTED"
        else:
            reason = "HISTORICAL_POLICY_REJECTED"
        rows.append(
            _decision_row(
                row,
                policy_id=policy_id,
                accepted=accepted,
                reason=reason,
            )
        )
    return pd.DataFrame(rows)


def run_policy(
    frame: pd.DataFrame,
    *,
    spec: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    policy_id = str(spec["policy_id"])
    families = _family_scope(contract, str(spec["family_scope"]))
    scope = frame.loc[frame["family_id"].isin(families)].copy()
    eligible = _eligible(scope, contract)
    if str(spec["mode"]) == "HISTORICAL_POLICY_AS_RECORDED":
        decisions = _frozen_decisions(scope, policy_id=policy_id, eligible=eligible)
        state = {
            "accepted_trades": int(decisions["accepted"].sum()),
            "historical_policy_as_recorded": True,
            "risk_invariants": None,
            "risk_invariants_pass": None,
            "hard_stop_triggered": False,
        }
    else:
        valid = scope.loc[eligible].copy()
        selected, duplicates = _episode_candidates(valid, contract)
        governed, state = _govern_candidates(
            selected, policy_id=policy_id, account=contract["account"]
        )
        extras: list[dict[str, Any]] = []
        for row in scope.loc[~eligible].itertuples(index=False):
            reason = (
                "REJECT_BROKER_INELIGIBLE"
                if not bool(row.broker_executable)
                else "REJECT_UNRESOLVED_LABEL"
            )
            extras.append(
                _decision_row(
                    row,
                    policy_id=policy_id,
                    accepted=False,
                    reason=reason,
                )
            )
        for row in duplicates.itertuples(index=False):
            extras.append(
                _decision_row(
                    row,
                    policy_id=policy_id,
                    accepted=False,
                    reason="REJECT_STRUCTURAL_EPISODE_DUPLICATE",
                )
            )
        decisions = pd.DataFrame(governed.to_dict("records") + extras)
    decisions = decisions.sort_values(
        ["entry_time", "candidate_id"], kind="stable"
    ).reset_index(drop=True)
    if len(decisions) != len(scope) or decisions["candidate_id"].duplicated().any():
        raise ValueError(f"Decision population mismatch for {policy_id}")
    accepted_ids = decisions.loc[decisions["accepted"], "candidate_id"]
    ledger = scope.loc[scope["candidate_id"].isin(accepted_ids)].copy()
    ledger["policy_id"] = policy_id
    ledger = ledger.sort_values(["entry_time", "candidate_id"], kind="stable")
    if len(ledger) != len(accepted_ids):
        raise ValueError(f"Accepted ledger mismatch for {policy_id}")
    return decisions, ledger.reset_index(drop=True), state


def _range_add(diff: np.ndarray, start: int, end: int, value: float) -> None:
    if start < end:
        diff[start] += value
        diff[end] -= value


def _utc_ns(values: pd.Series) -> np.ndarray:
    return (
        pd.to_datetime(values, utc=True)
        .astype("datetime64[ns, UTC]")
        .astype("int64")
        .to_numpy()
    )


def floating_equity_curve(
    bars: pd.DataFrame,
    ledger: pd.DataFrame,
    *,
    starting_equity_usd: float,
    bar_minutes: int,
) -> pd.DataFrame:
    n = len(bars)
    if n == 0:
        raise ValueError("M5 bars are empty")
    bar_ns = _utc_ns(bars["timestamp_utc"])
    bar_end_ns = bar_ns + int(pd.Timedelta(minutes=bar_minutes).value)
    long_count = np.zeros(n + 1)
    short_count = np.zeros(n + 1)
    open_constant = np.zeros(n + 1)
    close_long_count = np.zeros(n + 1)
    close_short_count = np.zeros(n + 1)
    close_constant = np.zeros(n + 1)
    risk = np.zeros(n + 1)
    margin = np.zeros(n + 1)
    positions = np.zeros(n + 1)

    if len(ledger):
        entry_ns = _utc_ns(ledger["entry_time"])
        exit_ns = _utc_ns(ledger["label_end_time"])
        if entry_ns.min() < bar_ns.min() or exit_ns.max() > bar_end_ns.max():
            raise ValueError("M5 history does not contain every accepted trade")
        for row in ledger.itertuples(index=False):
            entry = int(row.entry_time.value)
            exit_ = int(row.label_end_time.value)
            start = int(np.searchsorted(bar_end_ns, entry, side="right"))
            end = int(np.searchsorted(bar_ns, exit_, side="left"))
            close_start = start
            close_end = int(np.searchsorted(bar_end_ns, exit_, side="left"))
            sign = 1.0 if row.direction == "LONG" else -1.0
            constant = -sign * float(row.entry_price) - float(row.open_cost_usd)
            if sign > 0:
                _range_add(long_count, start, end, 1.0)
                _range_add(close_long_count, close_start, close_end, 1.0)
            else:
                _range_add(short_count, start, end, 1.0)
                _range_add(close_short_count, close_start, close_end, 1.0)
            _range_add(open_constant, start, end, constant)
            _range_add(close_constant, close_start, close_end, constant)
            _range_add(risk, start, end, float(row.initial_risk_usd))
            _range_add(margin, start, end, float(row.margin_usd))
            _range_add(positions, start, end, 1.0)

        exits = ledger.sort_values(["label_end_time", "candidate_id"], kind="stable")
        ordered_exit_ns = _utc_ns(exits["label_end_time"])
        cumulative = np.concatenate(([0.0], np.cumsum(exits["pnl_usd"].to_numpy(float))))
        realized_before = cumulative[
            np.searchsorted(ordered_exit_ns, bar_ns, side="right")
        ]
        realized_close = cumulative[
            np.searchsorted(ordered_exit_ns, bar_end_ns, side="right")
        ]
    else:
        realized_before = np.zeros(n)
        realized_close = np.zeros(n)

    active_long = np.cumsum(long_count[:-1])
    active_short = np.cumsum(short_count[:-1])
    active_constant = np.cumsum(open_constant[:-1])
    close_long = np.cumsum(close_long_count[:-1])
    close_short = np.cumsum(close_short_count[:-1])
    close_const = np.cumsum(close_constant[:-1])
    low = (
        starting_equity_usd
        + realized_before
        + active_long * bars["bid_low"].to_numpy(float)
        - active_short * bars["ask_high"].to_numpy(float)
        + active_constant
    )
    high = (
        starting_equity_usd
        + realized_before
        + active_long * bars["bid_high"].to_numpy(float)
        - active_short * bars["ask_low"].to_numpy(float)
        + active_constant
    )
    close = (
        starting_equity_usd
        + realized_close
        + close_long * bars["bid_close"].to_numpy(float)
        - close_short * bars["ask_close"].to_numpy(float)
        + close_const
    )
    return pd.DataFrame(
        {
            "timestamp_utc": bars["timestamp_utc"],
            "low_equity_usd": low,
            "high_equity_usd": high,
            "close_equity_usd": close,
            "open_positions": np.rint(np.cumsum(positions[:-1])).astype(int),
            "open_initial_risk_usd": np.cumsum(risk[:-1]),
            "open_margin_usd": np.cumsum(margin[:-1]),
        }
    )
