from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from phase0.config import load_project_config
from phase0.measured_revalidation import generate_measured_cost_revalidation


def test_measured_cost_revalidation_pending_without_measured_model(project_root, tmp_path):
    root = _copy_config(project_root, tmp_path)
    config = load_project_config(root)

    output = generate_measured_cost_revalidation(config)

    assert output.status == "PENDING"
    assert output.report_path.exists()
    assert "Overall status: PENDING" in output.report_path.read_text(encoding="utf-8")


def test_measured_cost_revalidation_passes_with_measured_p95_model(project_root, tmp_path):
    root = _copy_config(project_root, tmp_path)
    _lower_trade_threshold(root)
    _write_measured_cost_model(root)
    _write_trade_ledgers(root)
    config = load_project_config(root)

    output = generate_measured_cost_revalidation(config)

    assert output.status == "PASS"
    assert output.passing_cells == 9
    assert output.trade_count == 27
    assert "Overall status: PASS" in output.report_path.read_text(encoding="utf-8")
    reports = root / "outputs" / "reports"
    diagnostic = reports / "BREAKOUT_RETEST_COST_R_DIAGNOSTIC.md"
    delta = reports / "MEASURED_COST_ASSUMPTION_DELTA.md"
    audit = reports / "BREAKOUT_RETEST_MEASURED_COST_AUDIT.md"
    viability = reports / "BREAKOUT_RETEST_COST_VIABILITY_MAP.md"
    assert diagnostic.exists()
    assert delta.exists()
    assert audit.exists()
    assert viability.exists()
    assert "risk_price" in diagnostic.read_text(encoding="utf-8")
    assert "configured_p95_spread_points" in delta.read_text(encoding="utf-8")
    assert "measured spread replaces modeled entry spread" in audit.read_text(encoding="utf-8")
    viability_text = viability.read_text(encoding="utf-8")
    assert "## Scenario Map" in viability_text
    assert "## Spread Thresholds" in viability_text
    assert "Measured hourly P95 lookup" in viability_text


def _copy_config(project_root: Path, tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(project_root / "config", root / "config")
    return root


def _lower_trade_threshold(root: Path) -> None:
    path = root / "config" / "phase0.yaml"
    text = path.read_text(encoding="utf-8")
    text = text.replace("min_trades_every_cell: 40", "min_trades_every_cell: 3")
    path.write_text(text, encoding="utf-8")


def _write_measured_cost_model(root: Path) -> None:
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "MEASURED_COST_MODEL.md").write_text(
        "# Measured Cost Model\n\nOverall status: PASS\n",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "scope": "global",
                "bucket": "all",
                "broker": "capital_com",
                "symbol": "XAUUSD",
                "observations": 500,
                "median_spread_points": 20.0,
                "p95_spread_points": 20.0,
                "max_spread_points": 30.0,
            }
        ]
    ).to_csv(reports / "cost_model_measured.csv", index=False)


def _write_trade_ledgers(root: Path) -> None:
    trade_dir = root / "outputs" / "matrix_results" / "breakout_retest"
    trade_dir.mkdir(parents=True, exist_ok=True)
    for cell_id in range(1, 10):
        stem = f"cell_{cell_id}_breakout_retest_capital_com_p95"
        pd.DataFrame(
            [
                _trade_row("2024-01-02T08:00:00+00:00", 1.5),
                _trade_row("2024-01-02T09:00:00+00:00", 1.5),
                _trade_row("2024-01-02T10:00:00+00:00", -1.0),
            ]
        ).to_csv(trade_dir / f"{stem}_trades.csv", index=False)
        pd.DataFrame(
            [
                {
                    "cell_id": cell_id,
                    "broker": "capital_com",
                    "cost_model": "p95",
                    "symbol": "XAUUSD",
                }
            ]
        ).to_csv(trade_dir / f"{stem}.csv", index=False)


def _trade_row(entry_time: str, r_multiple: float) -> dict[str, object]:
    return {
        "entry_time_utc": entry_time,
        "entry_price": 2000.0,
        "stop_loss": 1999.0,
        "gross_pnl_usd": r_multiple * 100.0,
        "costs_usd": 0.0,
        "net_pnl_usd": r_multiple * 100.0,
        "r_multiple": r_multiple,
        "metadata_spread_points": 20.0,
        "metadata_entry_slippage_price": 0.0,
        "metadata_exit_slippage_price": 0.0,
        "metadata_actual_risk_usd": 100.0,
    }
