from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from phase0.constants import CELL_COST_MODELS, CELL_WINDOWS, DEFAULT_PHASE0_CONFIG, PACKAGE_ROOT
from phase0.data_contracts import BacktestConfig, CellConfig


class ConfigError(ValueError):
    """Raised when a Phase 0 configuration file is missing or invalid."""


@dataclass(frozen=True)
class ProjectConfig:
    root: Path
    phase0: dict[str, Any]
    symbols: dict[str, Any]
    cost_models: dict[str, Any]
    broker_sources: dict[str, Any]
    true_holdout: dict[str, Any]


def load_yaml_file(path: str | Path) -> dict[str, Any]:
    resolved = Path(path)
    if not resolved.exists():
        raise ConfigError(f"Config file not found: {resolved}. Create the file or fix the path.")

    try:
        with resolved.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {resolved}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"Config file {resolved} must contain a YAML mapping at the top level.")
    return data


def load_project_config(root: str | Path | None = None) -> ProjectConfig:
    project_root = Path(root).resolve() if root is not None else PACKAGE_ROOT
    config_dir = project_root / "config"
    phase0 = load_yaml_file(config_dir / "phase0.yaml")
    config = ProjectConfig(
        root=project_root,
        phase0=phase0,
        symbols=load_yaml_file(config_dir / "symbols.yaml"),
        cost_models=load_yaml_file(config_dir / "cost_models.yaml"),
        broker_sources=load_yaml_file(config_dir / "broker_sources.yaml"),
        true_holdout=load_yaml_file(config_dir / "true_holdout_period.yaml"),
    )
    validate_project_config(config)
    return config


def validate_project_config(config: ProjectConfig) -> None:
    phase0 = config.phase0
    _require_keys(phase0, ("project", "execution", "periods", "experts", "gates", "outputs"), "phase0.yaml")
    _require_keys(config.symbols, ("symbols",), "symbols.yaml")
    _require_keys(config.cost_models, ("cost_models",), "cost_models.yaml")
    _require_keys(config.broker_sources, ("brokers",), "broker_sources.yaml")
    _require_keys(config.true_holdout, ("true_holdout",), "true_holdout_period.yaml")

    project = phase0["project"]
    _require_positive(project, "starting_equity_usd", "phase0.yaml project")
    _require_range(
        project,
        "phase0_risk_per_trade_pct",
        lower_exclusive=0.0,
        upper_inclusive=0.05,
        context="phase0.yaml project",
    )

    execution = phase0["execution"]
    if execution.get("one_trade_at_a_time") is not True:
        raise ConfigError("phase0.yaml execution.one_trade_at_a_time must be true for Phase 0.")

    for expert_name, expert in phase0["experts"].items():
        _require_keys(expert, ("enabled", "hypothesis_file"), f"phase0.yaml experts.{expert_name}")
        if expert["enabled"] and not str(expert["hypothesis_file"]).strip():
            raise ConfigError(f"phase0.yaml experts.{expert_name}.hypothesis_file cannot be empty.")

    for symbol, details in config.symbols["symbols"].items():
        for key in ("point_size", "contract_size_per_lot", "min_lot", "lot_step"):
            _require_positive(details, key, f"symbols.yaml symbols.{symbol}")

    for cost_model, details in config.cost_models["cost_models"].items():
        _require_keys(details, ("spread_points",), f"cost_models.yaml cost_models.{cost_model}")
        for symbol, spread_points in details["spread_points"].items():
            if float(spread_points) < 0:
                raise ConfigError(
                    f"cost_models.yaml cost_models.{cost_model}.spread_points.{symbol} "
                    "must be non-negative."
                )

    for key in (
        "cell_1_3_start",
        "cell_1_3_end",
        "cell_4_6_start",
        "cell_4_6_end",
        "cell_7_9_start",
        "cell_7_9_end",
    ):
        parse_utc_datetime(phase0["periods"][key], f"phase0.yaml periods.{key}")


def build_backtest_config(config: ProjectConfig) -> BacktestConfig:
    project = config.phase0["project"]
    execution = config.phase0["execution"]
    return BacktestConfig(
        starting_equity_usd=float(project["starting_equity_usd"]),
        risk_per_trade_pct=float(project["phase0_risk_per_trade_pct"]),
        one_trade_at_a_time=bool(execution["one_trade_at_a_time"]),
        ambiguous_intrabar_policy=str(execution["ambiguous_intrabar_policy"]),
    )


def build_cell_configs(config: ProjectConfig, symbol: str = "XAUUSD") -> list[CellConfig]:
    periods = config.phase0["periods"]
    cells: list[CellConfig] = []
    for cell_id in range(1, 10):
        start_key, end_key, broker = CELL_WINDOWS[cell_id]
        cells.append(
            CellConfig(
                cell_id=cell_id,
                start_utc=parse_utc_datetime(periods[start_key], f"phase0.yaml periods.{start_key}"),
                end_utc=parse_utc_datetime(periods[end_key], f"phase0.yaml periods.{end_key}"),
                broker=broker,
                cost_model=CELL_COST_MODELS[cell_id],
                symbol=symbol,
            )
        )
    return cells


def get_symbol_details(config: ProjectConfig, symbol: str) -> dict[str, Any]:
    symbols = config.symbols["symbols"]
    canonical = resolve_symbol(config, symbol)
    return symbols[canonical]


def resolve_symbol(config: ProjectConfig, symbol_or_alias: str) -> str:
    wanted = symbol_or_alias.upper()
    for canonical, details in config.symbols["symbols"].items():
        aliases = [canonical, *details.get("aliases", [])]
        if wanted in {str(alias).upper() for alias in aliases}:
            return canonical
    raise ConfigError(f"Unknown symbol {symbol_or_alias!r}. Add it to config/symbols.yaml.")


def get_broker_details(config: ProjectConfig, broker: str) -> dict[str, Any]:
    brokers = config.broker_sources["brokers"]
    if broker not in brokers:
        raise ConfigError(f"Unknown broker {broker!r}. Add it to config/broker_sources.yaml.")
    return brokers[broker]


def validate_true_holdout_access(
    config: ProjectConfig,
    requested_start: datetime,
    requested_end: datetime,
    unlock_flag: bool = False,
) -> None:
    phase0_holdout = config.phase0.get("true_holdout", {})
    holdout = config.true_holdout["true_holdout"]
    if not phase0_holdout.get("enabled", False):
        return

    holdout_start = parse_utc_datetime(holdout["start"], "true_holdout_period.yaml true_holdout.start")
    holdout_end = parse_utc_datetime(holdout["end"], "true_holdout_period.yaml true_holdout.end")
    overlaps = requested_start <= holdout_end and requested_end >= holdout_start
    if not overlaps:
        return

    approval_file = config.root / str(holdout["unlock_requires_file"])
    if unlock_flag and approval_file.exists():
        return

    raise ConfigError(
        "Requested period overlaps the reserved true holdout window "
        f"({holdout_start.isoformat()} to {holdout_end.isoformat()}). "
        f"Create {approval_file} and pass {holdout['unlock_requires_cli_flag']} only for final review."
    )


def parse_utc_datetime(value: str | datetime, context: str = "datetime value") -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = str(value).strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError as exc:
            raise ConfigError(f"{context} must be an ISO-8601 datetime, got {value!r}.") from exc

    if parsed.tzinfo is None:
        raise ConfigError(f"{context} must be timezone-aware and UTC.")
    return parsed.astimezone(timezone.utc)


def _require_keys(data: dict[str, Any], keys: tuple[str, ...], context: str) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise ConfigError(f"{context} is missing required key(s): {', '.join(missing)}.")


def _require_positive(data: dict[str, Any], key: str, context: str) -> None:
    if key not in data:
        raise ConfigError(f"{context}.{key} is required.")
    if float(data[key]) <= 0:
        raise ConfigError(f"{context}.{key} must be positive, got {data[key]!r}.")


def _require_range(
    data: dict[str, Any],
    key: str,
    lower_exclusive: float,
    upper_inclusive: float,
    context: str,
) -> None:
    if key not in data:
        raise ConfigError(f"{context}.{key} is required.")
    value = float(data[key])
    if value <= lower_exclusive or value > upper_inclusive:
        raise ConfigError(
            f"{context}.{key} must be > {lower_exclusive} and <= {upper_inclusive}, got {value}."
        )


def load_default_phase0_config() -> dict[str, Any]:
    return load_yaml_file(DEFAULT_PHASE0_CONFIG)
