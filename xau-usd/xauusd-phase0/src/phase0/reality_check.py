from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError, ProjectConfig


@dataclass(frozen=True)
class RealityCheckOutput:
    status: str
    report_path: Path
    summary_path: Path
    manifest_path: Path
    winner: str
    white_reality_check_pvalue: float
    max_pairwise_spa_pvalue: float


def run_reality_check(
    config: ProjectConfig,
    approved_expert: str = "breakout_retest",
    iterations: int = 5000,
    block_months: int = 3,
    max_pvalue: float = 0.10,
    seed: int = 20260521,
) -> RealityCheckOutput:
    if iterations < 100:
        raise ConfigError("Reality check requires at least 100 bootstrap iterations.")
    if block_months < 1:
        raise ConfigError("Reality check block_months must be positive.")
    if not 0.0 < max_pvalue < 1.0:
        raise ConfigError("Reality check max_pvalue must be between 0 and 1.")

    panel = _load_monthly_panel(config)
    if approved_expert not in panel.columns:
        raise ConfigError(f"Approved expert {approved_expert!r} is missing from matrix trade ledgers.")
    if len(panel.columns) < 2:
        raise ConfigError("Reality check requires at least two expert candidates.")
    if len(panel) < block_months * 2:
        raise ConfigError("Reality check monthly panel is too short for the requested block size.")

    observed = panel.mean(axis=0)
    winner = str(observed.idxmax())
    white_pvalue, white_bootstrap_quantiles = _white_reality_check_pvalue(
        panel=panel,
        iterations=iterations,
        block_months=block_months,
        seed=seed,
    )
    pairwise_rows = _pairwise_spa_rows(
        panel=panel,
        approved_expert=approved_expert,
        iterations=iterations,
        block_months=block_months,
        seed=seed + 17,
        max_pvalue=max_pvalue,
    )
    max_pairwise_pvalue = max(float(row["spa_pvalue"]) for row in pairwise_rows)
    status = (
        "PASS"
        if winner == approved_expert
        and float(observed[approved_expert]) > 0
        and white_pvalue <= max_pvalue
        and all(row["status"] == "PASS" for row in pairwise_rows)
        else "FAIL"
    )

    reports_dir = config.root / "outputs" / "reports"
    manifests_dir = config.root / "outputs" / "manifests"
    reports_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "PHASE0_REALITY_CHECK.md"
    summary_path = reports_dir / "PHASE0_REALITY_CHECK_SUMMARY.csv"
    manifest_path = manifests_dir / "PHASE0_REALITY_CHECK_MANIFEST.json"

    summary_rows = _summary_rows(panel, observed, approved_expert, pairwise_rows)
    pd.DataFrame(summary_rows).to_csv(summary_path, index=False)
    report_path.write_text(
        _render_report(
            status=status,
            approved_expert=approved_expert,
            winner=winner,
            iterations=iterations,
            block_months=block_months,
            max_pvalue=max_pvalue,
            observed=observed,
            white_pvalue=white_pvalue,
            white_bootstrap_quantiles=white_bootstrap_quantiles,
            pairwise_rows=pairwise_rows,
            panel=panel,
        ),
        encoding="utf-8",
    )
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "approved_expert": approved_expert,
        "winner": winner,
        "method": "white_reality_check_and_spa_style_block_bootstrap_on_monthly_trade_ledger_returns",
        "iterations": iterations,
        "block_months": block_months,
        "max_pvalue": max_pvalue,
        "white_reality_check_pvalue": white_pvalue,
        "white_bootstrap_quantiles": white_bootstrap_quantiles,
        "max_pairwise_spa_pvalue": max_pairwise_pvalue,
        "month_count": int(len(panel)),
        "experts": list(panel.columns),
        "observed_mean_monthly_pnl_usd": {str(key): float(value) for key, value in observed.items()},
        "pairwise_spa": pairwise_rows,
        "report_path": str(report_path.relative_to(config.root)),
        "summary_path": str(summary_path.relative_to(config.root)),
        "report_sha256": _sha256(report_path),
        "summary_sha256": _sha256(summary_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return RealityCheckOutput(
        status=status,
        report_path=report_path,
        summary_path=summary_path,
        manifest_path=manifest_path,
        winner=winner,
        white_reality_check_pvalue=white_pvalue,
        max_pairwise_spa_pvalue=max_pairwise_pvalue,
    )


def _load_monthly_panel(config: ProjectConfig) -> pd.DataFrame:
    root = config.root / "outputs" / "matrix_results"
    if not root.exists():
        raise ConfigError(f"Missing matrix results directory: {root}")
    expert_series: dict[str, pd.Series] = {}
    for expert_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        series = _expert_monthly_series(expert_dir)
        if not series.empty:
            expert_series[expert_dir.name] = series
    if not expert_series:
        raise ConfigError(f"No expert trade ledgers found under {root}")
    return pd.DataFrame(expert_series).fillna(0.0).sort_index()


def _expert_monthly_series(expert_dir: Path) -> pd.Series:
    ledger_series: list[pd.Series] = []
    for trade_file in sorted(expert_dir.glob("*_trades.csv")):
        frame = pd.read_csv(trade_file, usecols=["entry_time_utc", "net_pnl_usd"])
        frame["entry_time_utc"] = pd.to_datetime(frame["entry_time_utc"], utc=True, errors="coerce")
        frame["net_pnl_usd"] = pd.to_numeric(frame["net_pnl_usd"], errors="coerce")
        frame = frame.dropna(subset=["entry_time_utc", "net_pnl_usd"])
        if frame.empty:
            continue
        frame["month"] = frame["entry_time_utc"].dt.strftime("%Y-%m")
        ledger_series.append(frame.groupby("month")["net_pnl_usd"].sum())
    if not ledger_series:
        return pd.Series(dtype="float64")
    return pd.concat(ledger_series, axis=1).fillna(0.0).mean(axis=1)


def _white_reality_check_pvalue(
    panel: pd.DataFrame,
    iterations: int,
    block_months: int,
    seed: int,
) -> tuple[float, dict[str, float]]:
    observed_means = panel.mean(axis=0)
    observed_max = float(observed_means.max())
    centered = panel - observed_means
    values = centered.to_numpy(dtype="float64")
    rng = np.random.default_rng(seed)
    bootstrap_stats = np.empty(iterations, dtype="float64")
    for index in range(iterations):
        sampled = values[_block_bootstrap_indices(len(values), block_months, rng)]
        bootstrap_stats[index] = float(sampled.mean(axis=0).max())
    pvalue = float((np.count_nonzero(bootstrap_stats >= observed_max) + 1) / (iterations + 1))
    quantiles = {
        "q90": float(np.quantile(bootstrap_stats, 0.90)),
        "q95": float(np.quantile(bootstrap_stats, 0.95)),
        "q99": float(np.quantile(bootstrap_stats, 0.99)),
    }
    return pvalue, quantiles


def _pairwise_spa_rows(
    panel: pd.DataFrame,
    approved_expert: str,
    iterations: int,
    block_months: int,
    seed: int,
    max_pvalue: float,
) -> list[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for alternative in panel.columns:
        if alternative == approved_expert:
            continue
        diff = (panel[approved_expert] - panel[alternative]).to_numpy(dtype="float64")
        observed_diff = float(np.mean(diff))
        centered = diff - observed_diff
        bootstrap_stats = np.empty(iterations, dtype="float64")
        for index in range(iterations):
            sampled = centered[_block_bootstrap_indices(len(centered), block_months, rng)]
            bootstrap_stats[index] = float(np.mean(sampled))
        pvalue = float((np.count_nonzero(bootstrap_stats >= observed_diff) + 1) / (iterations + 1))
        rows.append(
            {
                "status": "PASS" if observed_diff > 0 and pvalue <= max_pvalue else "FAIL",
                "approved_expert": approved_expert,
                "alternative": str(alternative),
                "mean_monthly_edge_usd": observed_diff,
                "spa_pvalue": pvalue,
                "bootstrap_q95": float(np.quantile(bootstrap_stats, 0.95)),
            }
        )
    return rows


def _block_bootstrap_indices(length: int, block_months: int, rng: np.random.Generator) -> np.ndarray:
    indices: list[int] = []
    while len(indices) < length:
        start = int(rng.integers(0, length))
        for offset in range(block_months):
            indices.append((start + offset) % length)
            if len(indices) == length:
                break
    return np.array(indices, dtype=int)


def _summary_rows(
    panel: pd.DataFrame,
    observed: pd.Series,
    approved_expert: str,
    pairwise_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = [
        {
            "row_type": "expert_monthly_mean",
            "expert": str(expert),
            "comparison": "",
            "mean_monthly_pnl_usd": float(value),
            "total_pnl_usd": float(panel[expert].sum()),
            "pvalue": "",
            "status": "APPROVED_EXPERT" if expert == approved_expert else "ALTERNATIVE",
        }
        for expert, value in observed.items()
    ]
    for row in pairwise_rows:
        rows.append(
            {
                "row_type": "pairwise_spa",
                "expert": row["approved_expert"],
                "comparison": row["alternative"],
                "mean_monthly_pnl_usd": row["mean_monthly_edge_usd"],
                "total_pnl_usd": "",
                "pvalue": row["spa_pvalue"],
                "status": row["status"],
            }
        )
    return rows


def _render_report(
    status: str,
    approved_expert: str,
    winner: str,
    iterations: int,
    block_months: int,
    max_pvalue: float,
    observed: pd.Series,
    white_pvalue: float,
    white_bootstrap_quantiles: dict[str, float],
    pairwise_rows: list[dict[str, Any]],
    panel: pd.DataFrame,
) -> str:
    expert_table = _markdown_table(
        [
            {
                "Expert": str(expert),
                "Mean Monthly PnL": _money(value),
                "Total PnL": _money(panel[expert].sum()),
                "Role": "approved" if expert == approved_expert else "alternative",
            }
            for expert, value in observed.items()
        ],
        ["Expert", "Mean Monthly PnL", "Total PnL", "Role"],
    )
    pairwise_table = _markdown_table(
        [
            {
                "Alternative": str(row["alternative"]),
                "Status": str(row["status"]),
                "Mean Edge": _money(row["mean_monthly_edge_usd"]),
                "SPA p": _fmt(row["spa_pvalue"], 4),
                "Bootstrap q95": _money(row["bootstrap_q95"]),
            }
            for row in pairwise_rows
        ],
        ["Alternative", "Status", "Mean Edge", "SPA p", "Bootstrap q95"],
    )
    return "\n".join(
        [
            "# PHASE0 REALITY CHECK",
            "",
            f"Status: {status}",
            f"Generated at UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}",
            f"Approved expert under test: {approved_expert}",
            "",
            "## Method",
            "",
            (
                "This report applies a White Reality Check and SPA-style pairwise bootstrap to monthly "
                "trade-ledger returns for the Phase 0 expert family. Each expert's monthly value is the "
                "average monthly PnL across its matrix trade ledgers, which keeps cost/broker cells from "
                "turning into separate optimized candidates."
            ),
            "",
            f"- Bootstrap iterations: {iterations}",
            f"- Circular block length: {block_months} month(s)",
            f"- Maximum accepted p-value: {max_pvalue}",
            f"- Months in panel: {len(panel)}",
            "",
            "## White Reality Check",
            "",
            _markdown_table(
                [
                    {
                        "Winner": winner,
                        "White p": _fmt(white_pvalue, 4),
                        "q90": _money(white_bootstrap_quantiles["q90"]),
                        "q95": _money(white_bootstrap_quantiles["q95"]),
                        "q99": _money(white_bootstrap_quantiles["q99"]),
                    }
                ],
                ["Winner", "White p", "q90", "q95", "q99"],
            ),
            "",
            "## Expert Means",
            "",
            expert_table,
            "",
            "## SPA-Style Pairwise Checks",
            "",
            pairwise_table,
            "",
            "## Interpretation",
            "",
            (
                "A PASS means breakout_retest remains the family winner after a block-bootstrap adjustment "
                "for multiple tested expert candidates. This is statistical support only; it does not remove "
                "the need for Phase 1 soak completion, Phase 2 paper trading, or live drift monitoring."
            ),
            "",
            "Summary rows are written to `outputs/reports/PHASE0_REALITY_CHECK_SUMMARY.csv`.",
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


def _fmt(value: object, places: int = 3) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if math.isinf(number):
        return "inf"
    return f"{number:.{places}f}"


def _money(value: object) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value)


def _sha256(path: Path) -> str:
    digest = __import__("hashlib").sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
