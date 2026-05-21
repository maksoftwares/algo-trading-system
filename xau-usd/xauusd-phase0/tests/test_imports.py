from __future__ import annotations

import importlib


def test_required_modules_import():
    module_names = [
        "phase0",
        "phase0.adversarial",
        "phase0.aggregation",
        "phase0.backtester",
        "phase0.bar_builder",
        "phase0.candles",
        "phase0.cli",
        "phase0.config",
        "phase0.constants",
        "phase0.costs",
        "phase0.data_contracts",
        "phase0.data_availability",
        "phase0.data_import",
        "phase0.data_loader",
        "phase0.data_validator",
        "phase0.deciles",
        "phase0.execution",
        "phase0.gates",
        "phase0.hashing",
        "phase0.indicators",
        "phase0.levels",
        "phase0.manifests",
        "phase0.metrics",
        "phase0.matrix",
        "phase0.multisymbol",
        "phase0.mt5_presets",
        "phase0.normalizer",
        "phase0.reports",
        "phase0.run_context",
        "phase0.safety",
        "phase0.sizing",
        "phase0.snapshot",
        "phase0.spread_analysis",
        "phase0.trades",
        "phase0.utils",
        "phase0.workflow",
        "phase0.strategies.base",
        "phase0.strategies.trend_pullback",
        "phase0.strategies.breakout_retest",
        "phase0.strategies.range_mr",
        "phase0.strategies.registry",
        "phase0.synthetic",
    ]

    for module_name in module_names:
        importlib.import_module(module_name)
