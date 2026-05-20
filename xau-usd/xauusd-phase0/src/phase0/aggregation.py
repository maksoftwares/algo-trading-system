from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from phase0.config import ConfigError, ProjectConfig
from phase0.gates import evaluate_matrix_gates, gate_results_to_dataframe
from phase0.metrics import add_cost_sensitivity_ratios
from phase0.strategies.registry import enabled_strategy_names


@dataclass(frozen=True)
class AggregationOutput:
    expert: str
    metrics_path: Path
    gates_path: Path


def aggregate_matrix_results(config: ProjectConfig, expert: str) -> list[AggregationOutput]:
    outputs: list[AggregationOutput] = []
    for expert_name in enabled_strategy_names(expert):
        matrix = load_matrix_metrics(config, expert_name)
        matrix = add_cost_sensitivity_ratios(matrix)
        gate_results = evaluate_matrix_gates(matrix, config.phase0["gates"])
        reports_dir = config.root / "outputs" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        metrics_path = reports_dir / f"{expert_name}_matrix_metrics.csv"
        gates_path = reports_dir / f"{expert_name}_gate_results.csv"
        matrix.to_csv(metrics_path, index=False)
        gate_results_to_dataframe(gate_results).to_csv(gates_path, index=False)
        outputs.append(AggregationOutput(expert_name, metrics_path, gates_path))
    return outputs


def load_matrix_metrics(config: ProjectConfig, expert: str) -> pd.DataFrame:
    directory = config.root / "outputs" / "matrix_results" / expert
    if not directory.exists():
        raise ConfigError(f"Matrix results directory not found: {directory}. Run run-matrix first.")

    summary_files = [
        path
        for path in sorted(directory.glob("cell_*.csv"))
        if not path.stem.endswith("_trades") and not path.stem.endswith("_equity")
    ]
    if not summary_files:
        raise ConfigError(f"No matrix summary CSV files found in {directory}. Run run-matrix first.")

    frames = [pd.read_csv(path) for path in summary_files]
    matrix = pd.concat(frames, ignore_index=True)
    if "cell_id" not in matrix.columns:
        raise ConfigError(f"Matrix summaries in {directory} are missing cell_id.")
    return matrix.sort_values("cell_id").reset_index(drop=True)
