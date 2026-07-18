from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "five_specialist_window_report_v1.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_source(record: Mapping[str, Any]) -> Path:
    path = REPO / str(record["path"])
    if not path.is_file():
        raise FileNotFoundError(path)
    observed = sha256_file(path)
    if observed != str(record["sha256"]):
        raise ValueError(f"Source hash changed for {path}: {observed}")
    return path


def _close_enough(observed: float, expected: float) -> bool:
    return bool(np.isclose(observed, expected, rtol=0.0, atol=1e-9))


def _standard_columns(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "trade_id",
        "specialist_id",
        "regime",
        "source_strategy",
        "pnl_basis",
        "entry_time_utc",
        "exit_time_utc",
        "direction",
        "pnl_usd_0p01_equiv",
        "stress_net_r",
        "risk_usd",
    ]
    result = frame[columns].copy()
    result["entry_time_utc"] = pd.to_datetime(result["entry_time_utc"], utc=True)
    result["exit_time_utc"] = pd.to_datetime(result["exit_time_utc"], utc=True)
    return result


def load_r1(config: Mapping[str, Any]) -> pd.DataFrame:
    record = config["sources"]["r1_uptrend"]
    source = pd.read_csv(verify_source(record))
    frame = source.loc[source["book"].eq(str(record["book"]))].copy()
    if len(frame) != int(record["expected_trades"]):
        raise ValueError(f"R1 trade count changed: {len(frame)}")
    net = float(frame["pnl_usd"].sum())
    if not _close_enough(net, float(record["expected_net_usd"])):
        raise ValueError(f"R1 net changed: {net}")
    result = pd.DataFrame(
        {
            "trade_id": frame["dedupe_key"].astype(str),
            "specialist_id": "R1_UPTREND",
            "regime": "UPTREND",
            "source_strategy": frame["source_id"].astype(str),
            "pnl_basis": str(record["pnl_basis"]),
            "entry_time_utc": frame["entry_time"],
            "exit_time_utc": frame["exit_time"],
            "direction": frame["direction"].astype(str),
            "pnl_usd_0p01_equiv": frame["pnl_usd"].astype(float),
            "stress_net_r": np.nan,
            "risk_usd": np.nan,
        }
    )
    return _standard_columns(result)


def _raw_tick_frame(
    frame: pd.DataFrame,
    specialist_id: str,
    regime: str,
    pnl_basis: str,
    source_strategy: pd.Series,
) -> pd.DataFrame:
    result = pd.DataFrame(
        {
            "trade_id": frame["candidate_id"].astype(str),
            "specialist_id": specialist_id,
            "regime": regime,
            "source_strategy": source_strategy.astype(str),
            "pnl_basis": pnl_basis,
            "entry_time_utc": frame["entry_time"],
            "exit_time_utc": frame["exit_time"],
            "direction": frame["direction"].astype(str),
            "pnl_usd_0p01_equiv": frame["stress_net_r"].astype(float)
            * frame["risk_usd"].astype(float),
            "stress_net_r": frame["stress_net_r"].astype(float),
            "risk_usd": frame["risk_usd"].astype(float),
        }
    )
    return _standard_columns(result)


def load_regime_composites(config: Mapping[str, Any]) -> list[pd.DataFrame]:
    record = config["sources"]["regime_composites"]
    source = pd.read_parquet(verify_source(record))
    result: list[pd.DataFrame] = []
    regimes = {"R2_DOWNTREND": "DOWNTREND", "R3_COMPRESSION": "COMPRESSION"}
    for definition in record["definitions"]:
        frame = source.loc[
            source["composite_id"].eq(str(definition["composite_id"]))
        ].copy()
        if len(frame) != int(definition["expected_trades"]):
            raise ValueError(
                f"{definition['specialist_id']} trade count changed: {len(frame)}"
            )
        net_r = float(frame["stress_net_r"].sum())
        if not _close_enough(net_r, float(definition["expected_stress_net_r"])):
            raise ValueError(f"{definition['specialist_id']} stress net changed")
        specialist_id = str(definition["specialist_id"])
        result.append(
            _raw_tick_frame(
                frame,
                specialist_id,
                regimes[specialist_id],
                str(record["pnl_basis"]),
                frame["mechanic"],
            )
        )
    return result


def load_r4(config: Mapping[str, Any]) -> pd.DataFrame:
    record = config["sources"]["r4_chop"]
    frame = pd.read_parquet(verify_source(record))
    if len(frame) != int(record["expected_trades"]):
        raise ValueError(f"R4 trade count changed: {len(frame)}")
    if not _close_enough(
        float(frame["stress_net_r"].sum()),
        float(record["expected_stress_net_r"]),
    ):
        raise ValueError("R4 stress net changed")
    return _raw_tick_frame(
        frame,
        "R4_CHOP",
        "CHOP",
        str(record["pnl_basis"]),
        frame["mechanic"],
    )


def load_r5(config: Mapping[str, Any]) -> pd.DataFrame:
    record = config["sources"]["r5_transition"]
    source = pd.read_parquet(verify_source(record))
    frame = source.loc[
        source["attempt_no"].eq(int(record["router_attempt"]))
    ].copy()
    if len(frame) != int(record["expected_trades"]):
        raise ValueError(f"R5 trade count changed: {len(frame)}")
    if not _close_enough(
        float(frame["stress_net_r"].sum()),
        float(record["expected_stress_net_r"]),
    ):
        raise ValueError("R5 stress net changed")
    strategy = (
        frame["component_attempt_no"].astype(int).astype(str)
        + ":"
        + frame["mechanic"].astype(str)
    )
    return _raw_tick_frame(
        frame,
        "R5_TRANSITION",
        "TRANSITION",
        str(record["pnl_basis"]),
        strategy,
    )


def load_ledger(config: Mapping[str, Any]) -> pd.DataFrame:
    parts = [load_r1(config), *load_regime_composites(config), load_r4(config), load_r5(config)]
    result = pd.concat(parts, ignore_index=True)
    if result.duplicated(["specialist_id", "trade_id"]).any():
        raise ValueError("Normalized ledger contains duplicate specialist trade IDs")
    if result["exit_time_utc"].lt(result["entry_time_utc"]).any():
        raise ValueError("Normalized ledger contains an exit before entry")
    return result.sort_values(
        ["exit_time_utc", "specialist_id", "trade_id"], kind="mergesort"
    ).reset_index(drop=True)


def profit_factor(values: pd.Series) -> float:
    gains = float(values.loc[values > 0.0].sum())
    losses = float(-values.loc[values < 0.0].sum())
    if losses == 0.0:
        return float("inf") if gains > 0.0 else 0.0
    return gains / losses


def closed_drawdown(frame: pd.DataFrame, column: str) -> float:
    if frame.empty:
        return 0.0
    realized = frame.groupby("exit_time_utc", sort=True)[column].sum()
    equity = np.concatenate(([0.0], realized.cumsum().to_numpy(dtype=float)))
    peaks = np.maximum.accumulate(equity)
    return float(np.max(peaks - equity))


def maximum_consecutive_losses(frame: pd.DataFrame, column: str) -> int:
    streak = maximum = 0
    for value in frame.sort_values(
        ["exit_time_utc", "specialist_id", "trade_id"], kind="mergesort"
    )[column].astype(float):
        streak = streak + 1 if value < 0.0 else 0
        maximum = max(maximum, streak)
    return maximum


def summarize(frame: pd.DataFrame) -> dict[str, Any]:
    values = frame["pnl_usd_0p01_equiv"].astype(float)
    wins = int(values.gt(0.0).sum())
    losses = int(values.lt(0.0).sum())
    row: dict[str, Any] = {
        "trades": int(len(frame)),
        "wins": wins,
        "losses": losses,
        "breakeven": int(values.eq(0.0).sum()),
        "win_rate_pct": float(100.0 * wins / len(frame)) if len(frame) else 0.0,
        "gross_profit_usd": float(values.loc[values > 0.0].sum()),
        "gross_loss_usd": float(-values.loc[values < 0.0].sum()),
        "net_usd_0p01_equiv": float(values.sum()),
        "profit_factor_usd": profit_factor(values),
        "average_usd_per_trade": float(values.mean()) if len(values) else 0.0,
        "closed_drawdown_usd": closed_drawdown(frame, "pnl_usd_0p01_equiv"),
        "maximum_consecutive_losses": maximum_consecutive_losses(
            frame, "pnl_usd_0p01_equiv"
        ),
        "active_exit_days": int(frame["exit_time_utc"].dt.date.nunique()),
    }
    stress = frame["stress_net_r"].dropna().astype(float)
    raw_only = len(frame) > 0 and len(stress) == len(frame)
    row.update(
        {
            "net_stress_r": float(stress.sum()) if raw_only else np.nan,
            "profit_factor_stress_r": profit_factor(stress)
            if raw_only
            else np.nan,
            "closed_drawdown_stress_r": closed_drawdown(frame, "stress_net_r")
            if raw_only
            else np.nan,
        }
    )
    return row


def concurrency_metrics(
    ledger: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> dict[str, Any]:
    overlapping = ledger.loc[
        ledger["entry_time_utc"].lt(end) & ledger["exit_time_utc"].gt(start)
    ]
    events: list[tuple[pd.Timestamp, int]] = []
    for row in overlapping.itertuples(index=False):
        interval_start = max(pd.Timestamp(row.entry_time_utc), start)
        interval_end = min(pd.Timestamp(row.exit_time_utc), end)
        if interval_end <= interval_start:
            continue
        events.extend(((interval_start, 1), (interval_end, -1)))
    active = maximum = 0
    for _, delta in sorted(events, key=lambda item: (item[0], item[1])):
        active += delta
        maximum = max(maximum, active)

    entries = ledger.loc[
        ledger["entry_time_utc"].ge(start) & ledger["entry_time_utc"].lt(end)
    ]
    any_overlap = cross_overlap = 0
    for index, row in entries.iterrows():
        open_rows = ledger.loc[
            ledger["entry_time_utc"].le(row["entry_time_utc"])
            & ledger["exit_time_utc"].gt(row["entry_time_utc"])
            & ledger.index.to_series().ne(index)
        ]
        any_overlap += int(not open_rows.empty)
        cross_overlap += int(
            open_rows["specialist_id"].ne(row["specialist_id"]).any()
        )
    return {
        "maximum_concurrent_positions": maximum,
        "maximum_concurrent_lots_at_0p01_each": maximum * 0.01,
        "entries_while_any_position_open": any_overlap,
        "entries_while_other_specialist_open": cross_overlap,
    }


def build_summaries(
    ledger: pd.DataFrame, config: Mapping[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cutoff = pd.Timestamp(config["cutoff_utc"])
    individual: list[dict[str, Any]] = []
    combined: list[dict[str, Any]] = []
    order = [str(value) for value in config["specialist_order"]]
    for window_id, raw_start in config["windows"].items():
        start = pd.Timestamp(raw_start)
        window = ledger.loc[
            ledger["exit_time_utc"].ge(start)
            & ledger["exit_time_utc"].lt(cutoff)
        ]
        for specialist_id in order:
            frame = window.loc[window["specialist_id"].eq(specialist_id)]
            individual.append(
                {
                    "window_id": str(window_id),
                    "start_utc": start.isoformat(),
                    "end_exclusive_utc": cutoff.isoformat(),
                    "specialist_id": specialist_id,
                    **summarize(frame),
                }
            )
        combined_row = {
            "window_id": str(window_id),
            "start_utc": start.isoformat(),
            "end_exclusive_utc": cutoff.isoformat(),
            "specialists_with_realized_trades": int(
                window["specialist_id"].nunique()
            ),
            **summarize(window),
            **concurrency_metrics(ledger, start, cutoff),
        }
        combined.append(combined_row)
    individual_frame = pd.DataFrame(individual)
    combined_frame = pd.DataFrame(combined)
    for window_id in config["windows"]:
        expected = float(
            individual_frame.loc[
                individual_frame["window_id"].eq(window_id),
                "net_usd_0p01_equiv",
            ].sum()
        )
        observed = float(
            combined_frame.loc[
                combined_frame["window_id"].eq(window_id),
                "net_usd_0p01_equiv",
            ].iat[0]
        )
        if not _close_enough(expected, observed):
            raise ValueError(f"Combined additivity failed for {window_id}")
    return individual_frame, combined_frame


def _number(value: Any, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    number = float(value)
    if np.isposinf(number):
        return "Inf"
    if np.isneginf(number):
        return "-Inf"
    return f"{number:.{digits}f}"


def render_markdown(
    individual: pd.DataFrame,
    combined: pd.DataFrame,
    config: Mapping[str, Any],
) -> str:
    lines = [
        "# Five-Specialist Window Performance V1",
        "",
        "Evidence cutoff: `2026-07-01T00:00:00Z` (exclusive).",
        "Realized trades are assigned by exit time.",
        "",
        "## Individual results",
        "",
        "| Window | Specialist | Trades | Win % | Net USD | PF | Closed DD USD | Net stress R |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in individual.itertuples(index=False):
        lines.append(
            f"| {row.window_id} | {row.specialist_id} | {row.trades} | "
            f"{_number(row.win_rate_pct)} | {_number(row.net_usd_0p01_equiv)} | "
            f"{_number(row.profit_factor_usd, 3)} | "
            f"{_number(row.closed_drawdown_usd)} | "
            f"{_number(row.net_stress_r, 3)} |"
        )
    lines.extend(
        (
            "",
            "## Additive combined results",
            "",
            "| Window | Trades | Active specialists | Win % | Net USD | PF | Closed DD USD | Max concurrent | Max lots | Cross-specialist overlap entries |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        )
    )
    for row in combined.itertuples(index=False):
        lines.append(
            f"| {row.window_id} | {row.trades} | "
            f"{row.specialists_with_realized_trades} | "
            f"{_number(row.win_rate_pct)} | {_number(row.net_usd_0p01_equiv)} | "
            f"{_number(row.profit_factor_usd, 3)} | "
            f"{_number(row.closed_drawdown_usd)} | "
            f"{row.maximum_concurrent_positions} | "
            f"{_number(row.maximum_concurrent_lots_at_0p01_each)} | "
            f"{row.entries_while_other_specialist_open} |"
        )
    lines.extend(
        (
            "",
            "## Accounting notes",
            "",
            "- R1 is exact MT5 closed P&L at 0.01 lot.",
            "- R2-R5 are conservative Dukascopy raw-tick stress-dollar equivalents at 0.01 lot.",
            "- Combined results add every specialist trade and allow simultaneous positions.",
            "- Closed drawdown is based on realized exits, not floating account equity.",
            "- No shared margin, exposure, daily-loss, or liquidation engine is applied.",
            "- Net stress R is not reported for R1 because its frozen ledger does not contain a per-trade initial-risk field.",
            "- These are historical development results and do not authorize training or trading.",
            "",
        )
    )
    return "\n".join(lines)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    ledger = load_ledger(config)
    individual, combined = build_summaries(ledger, config)
    output = ROOT / str(config["outputs"]["directory"])
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "normalized_ledger": output / config["outputs"]["normalized_ledger"],
        "individual_csv": output / config["outputs"]["individual_csv"],
        "combined_csv": output / config["outputs"]["combined_csv"],
        "markdown": output / config["outputs"]["markdown"],
    }
    ledger.to_parquet(paths["normalized_ledger"], index=False)
    individual.to_csv(paths["individual_csv"], index=False, lineterminator="\n")
    combined.to_csv(paths["combined_csv"], index=False, lineterminator="\n")
    paths["markdown"].write_text(
        render_markdown(individual, combined, config),
        encoding="utf-8",
        newline="\n",
    )
    source_records = {
        name: {
            "path": str(record["path"]),
            "sha256": str(record["sha256"]),
        }
        for name, record in config["sources"].items()
    }
    manifest = {
        "schema_version": config["schema_version"],
        "cutoff_utc": config["cutoff_utc"],
        "normalized_trades": int(len(ledger)),
        "specialist_trade_counts": {
            str(key): int(value)
            for key, value in ledger.groupby("specialist_id").size().items()
        },
        "source_files": source_records,
        "output_files": {
            path.name: {
                "bytes": int(path.stat().st_size),
                "sha256": sha256_file(path),
            }
            for path in paths.values()
        },
        "research_controls": config["research_controls"],
    }
    manifest_path = output / config["outputs"]["manifest"]
    write_json(manifest_path, manifest)
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
