from __future__ import annotations

import itertools
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from phase0.config import ConfigError, ProjectConfig


@dataclass(frozen=True)
class CpcvOutput:
    status: str
    report_path: Path
    paths_path: Path
    manifest_path: Path
    expert: str
    path_count: int
    pass_rate: float
    median_oos_profit_factor: float
    min_oos_profit_factor: float


def run_cpcv_validation(
    config: ProjectConfig,
    expert: str = "breakout_retest",
    folds: int = 6,
    test_fold_count: int = 2,
    purge_days: float = 1.0,
    min_oos_profit_factor: float = 1.0,
    min_median_oos_profit_factor: float = 1.10,
    min_oos_trades: int = 40,
) -> CpcvOutput:
    if folds < 3:
        raise ConfigError("CPCV requires at least 3 folds.")
    if test_fold_count < 1 or test_fold_count >= folds:
        raise ConfigError("CPCV test_fold_count must be at least 1 and lower than folds.")
    if purge_days < 0:
        raise ConfigError("CPCV purge_days must be non-negative.")

    trade_files = _matrix_trade_files(config, expert)
    if not trade_files:
        raise ConfigError(f"No matrix trade ledgers found for expert {expert!r}.")

    path_rows: list[dict[str, Any]] = []
    cell_rows: list[dict[str, Any]] = []
    for trade_file in trade_files:
        trades = _load_trade_ledger(trade_file)
        if len(trades) < folds * min_oos_trades:
            raise ConfigError(
                f"Trade ledger {trade_file} has {len(trades)} trades; "
                f"CPCV needs at least {folds * min_oos_trades}."
            )
        metadata = _load_matrix_metadata(trade_file)
        rows = _run_cell_cpcv(
            trades=trades,
            trade_file=trade_file,
            metadata=metadata,
            folds=folds,
            test_fold_count=test_fold_count,
            purge_days=purge_days,
            min_oos_profit_factor=min_oos_profit_factor,
            min_oos_trades=min_oos_trades,
        )
        path_rows.extend(rows)
        cell_rows.append(_summarize_cell(rows))

    summary = _summarize_all(path_rows, cell_rows, min_median_oos_profit_factor)
    status = (
        "PASS"
        if summary["failing_paths"] == 0
        and summary["failing_cells"] == 0
        and summary["median_oos_profit_factor"] >= min_median_oos_profit_factor
        else "FAIL"
    )

    reports_dir = config.root / "outputs" / "reports"
    manifests_dir = config.root / "outputs" / "manifests"
    reports_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "PHASE0_CPCV_VALIDATION.md"
    paths_path = reports_dir / "PHASE0_CPCV_PATHS.csv"
    manifest_path = manifests_dir / "PHASE0_CPCV_MANIFEST.json"

    pd.DataFrame(path_rows).to_csv(paths_path, index=False)
    report_path.write_text(
        _render_report(
            status=status,
            expert=expert,
            folds=folds,
            test_fold_count=test_fold_count,
            purge_days=purge_days,
            min_oos_profit_factor=min_oos_profit_factor,
            min_median_oos_profit_factor=min_median_oos_profit_factor,
            min_oos_trades=min_oos_trades,
            summary=summary,
            cell_rows=cell_rows,
        ),
        encoding="utf-8",
    )
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "expert": expert,
        "method": "combinatorial_purged_cross_validation_on_fixed_trade_ledgers",
        "folds": folds,
        "test_fold_count": test_fold_count,
        "purge_days": purge_days,
        "min_oos_profit_factor": min_oos_profit_factor,
        "min_median_oos_profit_factor": min_median_oos_profit_factor,
        "min_oos_trades": min_oos_trades,
        "report_path": str(report_path.relative_to(config.root)),
        "paths_path": str(paths_path.relative_to(config.root)),
        "summary": summary,
        "cells": cell_rows,
        "source_files": [
            {
                "path": str(path.relative_to(config.root)),
                "sha256": _sha256(path),
            }
            for path in trade_files
        ],
        "report_sha256": _sha256(report_path),
        "paths_sha256": _sha256(paths_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return CpcvOutput(
        status=status,
        report_path=report_path,
        paths_path=paths_path,
        manifest_path=manifest_path,
        expert=expert,
        path_count=int(summary["path_count"]),
        pass_rate=float(summary["path_pass_rate"]),
        median_oos_profit_factor=float(summary["median_oos_profit_factor"]),
        min_oos_profit_factor=float(summary["min_oos_profit_factor"]),
    )


def _matrix_trade_files(config: ProjectConfig, expert: str) -> list[Path]:
    root = config.root / "outputs" / "matrix_results" / expert
    return sorted(root.glob("*_trades.csv")) if root.exists() else []


def _load_trade_ledger(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"entry_time_utc", "exit_time_utc", "net_pnl_usd"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ConfigError(f"Trade ledger {path} is missing required columns: {', '.join(missing)}")
    frame["entry_time_utc"] = pd.to_datetime(frame["entry_time_utc"], utc=True, errors="coerce")
    frame["exit_time_utc"] = pd.to_datetime(frame["exit_time_utc"], utc=True, errors="coerce")
    frame["net_pnl_usd"] = pd.to_numeric(frame["net_pnl_usd"], errors="coerce")
    frame = frame.dropna(subset=["entry_time_utc", "exit_time_utc", "net_pnl_usd"])
    if frame.empty:
        raise ConfigError(f"Trade ledger {path} contains no valid trade rows.")
    return frame.sort_values("entry_time_utc").reset_index(drop=True)


def _load_matrix_metadata(trade_file: Path) -> dict[str, Any]:
    summary_path = trade_file.with_name(trade_file.name.replace("_trades.csv", ".csv"))
    if not summary_path.exists():
        return {
            "cell_id": "",
            "broker": "",
            "cost_model": "",
            "symbol": "",
            "summary_path": "",
        }
    row = pd.read_csv(summary_path).iloc[0].to_dict()
    return {
        "cell_id": row.get("cell_id", ""),
        "broker": row.get("broker", ""),
        "cost_model": row.get("cost_model", ""),
        "symbol": row.get("symbol", ""),
        "summary_path": str(summary_path),
    }


def _run_cell_cpcv(
    trades: pd.DataFrame,
    trade_file: Path,
    metadata: dict[str, Any],
    folds: int,
    test_fold_count: int,
    purge_days: float,
    min_oos_profit_factor: float,
    min_oos_trades: int,
) -> list[dict[str, Any]]:
    trades = trades.copy()
    trades["cpcv_fold"] = _assign_chronological_folds(len(trades), folds)
    rows: list[dict[str, Any]] = []
    for path_index, test_folds in enumerate(itertools.combinations(range(folds), test_fold_count), start=1):
        test_mask = trades["cpcv_fold"].isin(test_folds)
        test = trades[test_mask].copy()
        train = _purged_training_rows(trades, test_mask, tuple(test_folds), purge_days)
        train_stats = _trade_stats(train)
        test_stats = _trade_stats(test)
        path_status = (
            "PASS"
            if test_stats["profit_factor"] >= min_oos_profit_factor
            and test_stats["trade_count"] >= min_oos_trades
            else "FAIL"
        )
        rows.append(
            {
                "status": path_status,
                "cell_id": metadata["cell_id"],
                "broker": metadata["broker"],
                "cost_model": metadata["cost_model"],
                "symbol": metadata["symbol"],
                "path_index": path_index,
                "test_folds": "+".join(str(fold) for fold in test_folds),
                "purge_days": purge_days,
                "train_trade_count": train_stats["trade_count"],
                "train_profit_factor": train_stats["profit_factor"],
                "train_total_pnl_usd": train_stats["total_pnl_usd"],
                "oos_trade_count": test_stats["trade_count"],
                "oos_profit_factor": test_stats["profit_factor"],
                "oos_total_pnl_usd": test_stats["total_pnl_usd"],
                "oos_win_rate": test_stats["win_rate"],
                "source_trade_file": trade_file.name,
            }
        )
    return rows


def _assign_chronological_folds(row_count: int, folds: int) -> list[int]:
    if row_count <= 0:
        return []
    return [min(folds - 1, (position * folds) // row_count) for position in range(row_count)]


def _purged_training_rows(
    trades: pd.DataFrame,
    test_mask: pd.Series,
    test_folds: tuple[int, ...],
    purge_days: float,
) -> pd.DataFrame:
    train_mask = ~test_mask
    purge_delta = pd.Timedelta(days=purge_days)
    for fold in test_folds:
        fold_rows = trades[trades["cpcv_fold"] == fold]
        if fold_rows.empty:
            continue
        start = fold_rows["entry_time_utc"].min() - purge_delta
        end = fold_rows["exit_time_utc"].max() + purge_delta
        near_fold = (trades["entry_time_utc"] >= start) & (trades["entry_time_utc"] <= end)
        train_mask &= ~near_fold
    return trades[train_mask].copy()


def _trade_stats(rows: pd.DataFrame) -> dict[str, float | int]:
    pnl = pd.to_numeric(rows["net_pnl_usd"], errors="coerce").dropna()
    wins = float(pnl[pnl > 0].sum())
    losses = float(-pnl[pnl < 0].sum())
    return {
        "trade_count": int(len(pnl)),
        "profit_factor": _profit_factor(wins, losses),
        "total_pnl_usd": float(pnl.sum()),
        "win_rate": float((pnl > 0).mean()) if len(pnl) else 0.0,
    }


def _profit_factor(wins: float, losses: float) -> float:
    if losses == 0:
        return math.inf if wins > 0 else 0.0
    return wins / losses


def _summarize_cell(rows: list[dict[str, Any]]) -> dict[str, Any]:
    frame = pd.DataFrame(rows)
    failing_paths = int((frame["status"] != "PASS").sum())
    return {
        "status": "PASS" if failing_paths == 0 else "FAIL",
        "cell_id": rows[0]["cell_id"],
        "broker": rows[0]["broker"],
        "cost_model": rows[0]["cost_model"],
        "path_count": int(len(frame)),
        "failing_paths": failing_paths,
        "path_pass_rate": float((frame["status"] == "PASS").mean()),
        "min_oos_profit_factor": float(frame["oos_profit_factor"].min()),
        "median_oos_profit_factor": float(frame["oos_profit_factor"].median()),
        "min_oos_trade_count": int(frame["oos_trade_count"].min()),
    }


def _summarize_all(
    path_rows: list[dict[str, Any]],
    cell_rows: list[dict[str, Any]],
    min_median_oos_profit_factor: float,
) -> dict[str, Any]:
    paths = pd.DataFrame(path_rows)
    cells = pd.DataFrame(cell_rows)
    median_pf = float(paths["oos_profit_factor"].median())
    return {
        "status": "PASS"
        if int((paths["status"] != "PASS").sum()) == 0
        and int((cells["status"] != "PASS").sum()) == 0
        and median_pf >= min_median_oos_profit_factor
        else "FAIL",
        "path_count": int(len(paths)),
        "failing_paths": int((paths["status"] != "PASS").sum()),
        "cell_count": int(len(cells)),
        "failing_cells": int((cells["status"] != "PASS").sum()),
        "path_pass_rate": float((paths["status"] == "PASS").mean()),
        "min_oos_profit_factor": float(paths["oos_profit_factor"].min()),
        "median_oos_profit_factor": median_pf,
        "min_oos_trade_count": int(paths["oos_trade_count"].min()),
    }


def _render_report(
    status: str,
    expert: str,
    folds: int,
    test_fold_count: int,
    purge_days: float,
    min_oos_profit_factor: float,
    min_median_oos_profit_factor: float,
    min_oos_trades: int,
    summary: dict[str, Any],
    cell_rows: list[dict[str, Any]],
) -> str:
    cell_table = _markdown_table(
        [
            {
                "Cell": str(row["cell_id"]),
                "Broker": str(row["broker"]),
                "Cost": str(row["cost_model"]),
                "Status": str(row["status"]),
                "Paths": str(row["path_count"]),
                "Failing": str(row["failing_paths"]),
                "Min OOS PF": _fmt(row["min_oos_profit_factor"]),
                "Median OOS PF": _fmt(row["median_oos_profit_factor"]),
                "Min OOS Trades": str(row["min_oos_trade_count"]),
            }
            for row in cell_rows
        ],
        ["Cell", "Broker", "Cost", "Status", "Paths", "Failing", "Min OOS PF", "Median OOS PF", "Min OOS Trades"],
    )
    return "\n".join(
        [
            "# PHASE0 CPCV VALIDATION",
            "",
            f"Status: {status}",
            f"Generated at UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}",
            f"Expert: {expert}",
            "",
            "## Method",
            "",
            (
                "Combinatorial purged cross-validation was run on the fixed Phase 0 matrix trade ledgers. "
                "No parameters are selected inside this step; the test only checks whether the already-approved "
                "mechanical expert remains profitable when chronological fold combinations are held out."
            ),
            "",
            f"- Folds: {folds}",
            f"- Held-out folds per path: {test_fold_count}",
            f"- Purge window around held-out folds: {purge_days} day(s)",
            f"- Path gate: OOS PF >= {min_oos_profit_factor} and OOS trades >= {min_oos_trades}",
            f"- Aggregate gate: median OOS PF >= {min_median_oos_profit_factor}",
            "",
            "## Summary",
            "",
            _markdown_table(
                [
                    {
                        "Status": status,
                        "Paths": str(summary["path_count"]),
                        "Failing Paths": str(summary["failing_paths"]),
                        "Cells": str(summary["cell_count"]),
                        "Failing Cells": str(summary["failing_cells"]),
                        "Pass Rate": _pct(summary["path_pass_rate"]),
                        "Min OOS PF": _fmt(summary["min_oos_profit_factor"]),
                        "Median OOS PF": _fmt(summary["median_oos_profit_factor"]),
                        "Min OOS Trades": str(summary["min_oos_trade_count"]),
                    }
                ],
                [
                    "Status",
                    "Paths",
                    "Failing Paths",
                    "Cells",
                    "Failing Cells",
                    "Pass Rate",
                    "Min OOS PF",
                    "Median OOS PF",
                    "Min OOS Trades",
                ],
            ),
            "",
            "## Cell Results",
            "",
            cell_table,
            "",
            "## Interpretation",
            "",
            (
                "A PASS here supports robustness of the fixed breakout_retest definition across purged "
                "chronological partitions. It does not replace the five-trading-day Phase 1 soak or the "
                "future paper-trading drift monitor."
            ),
            "",
            "Path-level rows are written to `outputs/reports/PHASE0_CPCV_PATHS.csv`.",
            "",
        ]
    )


def _markdown_table(rows: list[dict[str, str]], headers: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def _fmt(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if math.isinf(number):
        return "inf"
    return f"{number:.3f}"


def _pct(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return str(value)


def _sha256(path: Path) -> str:
    digest = __import__("hashlib").sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
