from __future__ import annotations

import ast
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
AUDIT_PATH = (
    REPO_ROOT
    / "xau-usd/xauusd-fast-research/v60-challenger-goal-20260825/EXPOSED_BROKER_AUDIT.csv"
)
STATE_PATH = Path("C:/MT5PortableTier1BestEA/MQL5/Files/v60_canonical_demo_v2/state.json")
TICK_ROOT = Path("C:/MT5PortableTier1BestEA/MQL5/Files")
INPUTS = ROOT / "inputs"
POLL_MS = 5_000
DAY_MS = 86_400_000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def utc_text(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000.0, UTC).isoformat().replace(
        "+00:00", "Z"
    )


def merged_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[list[int]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1] + POLL_MS:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def load_trade_snapshot() -> pd.DataFrame:
    audit = pd.read_csv(AUDIT_PATH)
    audit = audit.loc[
        audit["entry_time_utc"].astype(str).str.startswith("2026-08-")
        & audit["baseline_executed"].astype(str).str.lower().eq("true")
        & audit["broker_outcome_resolved"].astype(str).str.lower().eq("true")
    ].copy()
    if len(audit) != 24 or audit["candidate_id"].duplicated().any():
        raise ValueError("Expected 24 unique resolved August broker trades")

    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    positions = state.get("positions", {})
    rows: list[dict[str, object]] = []
    for row in audit.to_dict("records"):
        candidate_id = str(row["candidate_id"])
        if candidate_id not in positions:
            raise ValueError(f"Missing runtime position state: {candidate_id}")
        position = positions[candidate_id]
        execution = ast.literal_eval(str(row["broker_execution"]))
        entry = pd.Timestamp(execution["broker_entry_time_utc"])
        exit_time = pd.Timestamp(row["broker_exit_time_utc"])
        if entry.tzinfo is None:
            entry = entry.tz_localize("UTC")
        else:
            entry = entry.tz_convert("UTC")
        if exit_time.tzinfo is None:
            exit_time = exit_time.tz_localize("UTC")
        else:
            exit_time = exit_time.tz_convert("UTC")
        rows.append(
            {
                "candidate_id": candidate_id,
                "source_id": str(row["source_id"]),
                "scheduled_entry_time_utc": str(row["entry_time_utc"]),
                "broker_entry_time_utc": entry.isoformat(),
                "broker_entry_ms": int(entry.timestamp() * 1000),
                "broker_exit_time_utc": exit_time.isoformat(),
                "broker_exit_ms": int(exit_time.timestamp() * 1000),
                "direction": str(execution["direction"]).upper(),
                "entry_price": float(execution["entry_price"]),
                "entry_cost_usd": float(execution.get("entry_cost_usd", 0.0)),
                "initial_risk_usd": float(position["initial_risk_usd"]),
                "volume_lots": float(execution["volume_lots"]),
                "broker_pnl_usd": float(row["broker_pnl_usd"]),
                "v2_baseline_path_proposal": str(row["would_veto"]).lower()
                == "true",
            }
        )
    result = pd.DataFrame(rows).sort_values(
        ["broker_entry_ms", "candidate_id"], kind="stable"
    )
    numeric = result[
        [
            "entry_price",
            "entry_cost_usd",
            "initial_risk_usd",
            "volume_lots",
            "broker_pnl_usd",
        ]
    ].to_numpy(dtype=float)
    if not np.isfinite(numeric).all() or (result["initial_risk_usd"] <= 0.0).any():
        raise ValueError("Trade snapshot contains invalid numeric values")
    return result.reset_index(drop=True)


def relevant_intervals_by_day(trades: pd.DataFrame) -> dict[int, list[tuple[int, int]]]:
    result: dict[int, list[tuple[int, int]]] = {}
    for row in trades.itertuples(index=False):
        first_day = int(row.broker_entry_ms) // DAY_MS
        last_day = int(row.broker_exit_ms) // DAY_MS
        for day in range(first_day, last_day + 1):
            day_start = day * DAY_MS
            start = max(int(row.broker_entry_ms), day_start)
            end = min(int(row.broker_exit_ms), day_start + DAY_MS - 1)
            result.setdefault(day, []).append((start, end))
    return {day: merged_intervals(intervals) for day, intervals in result.items()}


def quote_snapshot(
    intervals_by_day: dict[int, list[tuple[int, int]]]
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    quote_parts: list[pd.DataFrame] = []
    source_manifest: list[dict[str, object]] = []
    for day, intervals in sorted(intervals_by_day.items()):
        date = datetime.fromtimestamp(day * DAY_MS / 1000.0, UTC).strftime("%Y%m%d")
        path = TICK_ROOT / (
            "xau_prospective_1033030_Capital_ComMena_Demo_XAUUSD_ticks_"
            f"{date}.csv"
        )
        if not path.is_file():
            raise FileNotFoundError(path)
        source_manifest.append(
            {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
        ticks = pd.read_csv(
            path,
            usecols=["tick_time_msc", "bid", "ask"],
            dtype={"tick_time_msc": "int64", "bid": "float64", "ask": "float64"},
        ).sort_values("tick_time_msc", kind="stable")
        tick_ms = ticks["tick_time_msc"].to_numpy(dtype=np.int64)
        bid = ticks["bid"].to_numpy(dtype=float)
        ask = ticks["ask"].to_numpy(dtype=float)
        if not len(tick_ms):
            raise ValueError(f"No ticks in required source: {path}")
        for start, end in intervals:
            first_cycle = ((start + POLL_MS - 1) // POLL_MS) * POLL_MS
            cycles = np.arange(first_cycle, end + 1, POLL_MS, dtype=np.int64)
            indexes = np.searchsorted(tick_ms, cycles, side="right") - 1
            valid = indexes >= 0
            if valid.any():
                quote_parts.append(
                    pd.DataFrame(
                        {
                            "cycle_ms": cycles[valid],
                            "tick_ms": tick_ms[indexes[valid]],
                            "bid": bid[indexes[valid]],
                            "ask": ask[indexes[valid]],
                        }
                    )
                )
    quotes = pd.concat(quote_parts, ignore_index=True)
    quotes = quotes.drop_duplicates("cycle_ms", keep="last").sort_values("cycle_ms")
    if quotes[["bid", "ask"]].isna().any().any() or (quotes["ask"] < quotes["bid"]).any():
        raise ValueError("Quote snapshot contains invalid prices")
    return quotes.reset_index(drop=True), source_manifest


def main() -> int:
    INPUTS.mkdir(parents=True, exist_ok=True)
    trades = load_trade_snapshot()
    quotes, sources = quote_snapshot(relevant_intervals_by_day(trades))
    trade_path = INPUTS / "AUGUST_BROKER_TRADES.parquet"
    quote_path = INPUTS / "AUGUST_BROKER_5S_QUOTES.parquet"
    trades.to_parquet(trade_path, index=False)
    quotes.to_parquet(quote_path, index=False)
    manifest = {
        "schema_version": "xauusd_v13_august_broker_input_snapshot_v1",
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "policy_evaluated": False,
        "poll_seconds": POLL_MS // 1000,
        "trade_rows": int(len(trades)),
        "quote_rows": int(len(quotes)),
        "first_cycle_utc": utc_text(int(quotes["cycle_ms"].min())),
        "last_cycle_utc": utc_text(int(quotes["cycle_ms"].max())),
        "inputs": {
            "broker_audit": {
                "path": str(AUDIT_PATH),
                "sha256": sha256_file(AUDIT_PATH),
            },
            "runtime_state": {
                "path": str(STATE_PATH),
                "sha256_at_snapshot": sha256_file(STATE_PATH),
            },
            "source_tick_files": sources,
        },
        "outputs": {
            "trades": {"path": str(trade_path), "sha256": sha256_file(trade_path)},
            "quotes": {"path": str(quote_path), "sha256": sha256_file(quote_path)},
        },
    }
    (INPUTS / "AUGUST_INPUT_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "trade_rows": len(trades),
                "quote_rows": len(quotes),
                "first_cycle_utc": manifest["first_cycle_utc"],
                "last_cycle_utc": manifest["last_cycle_utc"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
