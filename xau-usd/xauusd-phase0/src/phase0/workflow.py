from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from phase0.adversarial import AdversarialPacketOutput, create_adversarial_packets
from phase0.aggregation import AggregationOutput, aggregate_matrix_results
from phase0.config import ProjectConfig, build_cell_configs
from phase0.data_availability import assert_processed_data_available
from phase0.deciles import DecileRunOutput, run_decile_tests
from phase0.hashing import validate_hypotheses
from phase0.manifests import generate_result_manifest
from phase0.matrix import MatrixRunOutput, run_phase0_matrix
from phase0.multisymbol import MultisymbolRunOutput, run_multisymbol_checks
from phase0.reports import ReportGenerationOutput, generate_all_reports
from phase0.safety import assert_no_live_trading_calls


@dataclass(frozen=True)
class RunAllOutput:
    matrix_outputs: list[MatrixRunOutput]
    decile_outputs: list[DecileRunOutput]
    multisymbol_outputs: list[MultisymbolRunOutput]
    adversarial_outputs: list[AdversarialPacketOutput]
    aggregation_outputs: list[AggregationOutput]
    report_output: ReportGenerationOutput
    result_manifest_path: Path


def run_all_phase0(
    config: ProjectConfig,
    synthetic_sample: bool = False,
    unlock_true_holdout: bool = False,
) -> RunAllOutput:
    build_cell_configs(config)
    assert_no_live_trading_calls(config)
    validate_hypotheses(config)
    if not synthetic_sample:
        assert_processed_data_available(config)
    matrix_outputs = run_phase0_matrix(config, "all", synthetic_sample=synthetic_sample)
    decile_outputs = run_decile_tests(
        config,
        "all",
        synthetic_sample=synthetic_sample,
        unlock_true_holdout=unlock_true_holdout,
    )
    multisymbol_outputs = run_multisymbol_checks(
        config,
        "all",
        synthetic_sample=synthetic_sample,
        unlock_true_holdout=unlock_true_holdout,
    )
    adversarial_outputs = create_adversarial_packets(config, "all")
    aggregation_outputs = aggregate_matrix_results(config, "all")
    report_output = generate_all_reports(config)
    result_manifest_path = generate_result_manifest(config)
    return RunAllOutput(
        matrix_outputs=matrix_outputs,
        decile_outputs=decile_outputs,
        multisymbol_outputs=multisymbol_outputs,
        adversarial_outputs=adversarial_outputs,
        aggregation_outputs=aggregation_outputs,
        report_output=report_output,
        result_manifest_path=result_manifest_path,
    )
