from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from dataclasses import asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FOREX_ROOT = ROOT.parent
LEARNER_ROOT = FOREX_ROOT / "eurusd-prospective-multisymbol-collector-v1"
LEARNER_MODULE = LEARNER_ROOT / "src" / "forward_selective_learner.py"
LEARNER_CONFIG = LEARNER_ROOT / "config" / "frozen_forward_selective_learner_v1.json"
SOURCE_CONFIG = ROOT / "config" / "frozen_crosspair_strength_daily.json"
PIP = 0.0001


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_engine():
    name = "frozen_forward_selective_learner_history_diagnostic"
    spec = importlib.util.spec_from_file_location(name, LEARNER_MODULE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen forward learner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_contracts() -> tuple[dict[str, Any], dict[str, Any]]:
    learner = json.loads(LEARNER_CONFIG.read_text(encoding="utf-8"))
    source = json.loads(SOURCE_CONFIG.read_text(encoding="utf-8"))
    if learner["campaign_id"] != "EURUSD_FORWARD_SELECTIVE_LEARNER_V1":
        raise RuntimeError("unexpected frozen learner campaign")
    if source["status"] != "LOCKED_BEFORE_EURUSD_OUTCOME_INSPECTION":
        raise RuntimeError("historical source contract is not frozen")
    return learner, source


def load_source_frames(
    source_config: dict[str, Any],
    symbols: list[str],
) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    root = Path(source_config["source_root"])
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
        "tick_count",
    ]
    frames: dict[str, pd.DataFrame] = {}
    verified: dict[str, str] = {}
    for symbol in symbols:
        filename = f"{symbol}_M5_BIDASK.parquet"
        path = root / filename
        actual_hash = sha256(path)
        expected_hash = source_config["source_sha256"][filename]
        if actual_hash != expected_hash:
            raise RuntimeError(f"historical source hash mismatch: {filename}")
        frame = pd.read_parquet(path, columns=columns)
        frame["timestamp"] = pd.to_datetime(
            frame.pop("timestamp_ms"),
            unit="ms",
            utc=True,
        )
        frame = frame.set_index("timestamp").sort_index()
        if frame.index.has_duplicates:
            raise RuntimeError(f"duplicate historical timestamps: {symbol}")
        frames[symbol] = frame
        verified[filename] = actual_hash
    return frames, verified


def _point(symbol: str) -> float:
    return 0.001 if symbol.endswith("JPY") else 0.00001


def build_day_bars(
    day: date,
    frames: dict[str, pd.DataFrame],
    learner_config: dict[str, Any],
    engine,
) -> dict[datetime, dict[str, Any]]:
    decision = engine.decision_datetime(day, learner_config)
    start = pd.Timestamp(decision - timedelta(hours=4), tz="UTC")
    end = pd.Timestamp(decision + timedelta(hours=6), tz="UTC")
    grouped: dict[datetime, dict[str, Any]] = defaultdict(dict)
    symbols = [
        learner_config["execution_symbol"],
        *learner_config["predictor_symbols"],
    ]
    for symbol in symbols:
        subset = frames[symbol].loc[start : end - pd.Timedelta(minutes=5)]
        point = _point(symbol)
        for row in subset.itertuples():
            timestamp = row.Index.to_pydatetime().replace(tzinfo=None)
            mean_spread_points = (
                (float(row.ask_open) - float(row.bid_open))
                + (float(row.ask_close) - float(row.bid_close))
            ) / (2.0 * point)
            grouped[timestamp][symbol] = engine.Bar(
                interval_open=timestamp,
                symbol=symbol,
                status="OK",
                copied_ticks=int(row.tick_count),
                first_bid=float(row.bid_open),
                first_ask=float(row.ask_open),
                last_bid=float(row.bid_close),
                last_ask=float(row.ask_close),
                bid_high=float(row.bid_high),
                bid_low=float(row.bid_low),
                ask_high=float(row.ask_high),
                ask_low=float(row.ask_low),
                spread_mean_points=mean_spread_points,
                point=point,
            )
    return dict(grouped)


def replay_day(
    day: date,
    grouped: dict[datetime, dict[str, Any]],
    weights: list[float],
    resolved_days: int,
    learner_config: dict[str, Any],
    engine,
) -> tuple[dict[str, Any], list[float], int]:
    decision_time = engine.decision_datetime(day, learner_config)
    context = engine.build_context(grouped, decision_time, learner_config)
    if context is None:
        return (
            {
                "decision_date": day.isoformat(),
                "decision_time_utc": decision_time.strftime(engine.TIME_FORMAT),
                "status": "MISSING_CONTEXT",
                "eligible_side": "CASH",
                "training_days_before": resolved_days,
            },
            weights,
            resolved_days,
        )
    long_features = engine.side_features(context, "LONG")
    short_features = engine.side_features(context, "SHORT")
    probability_long = engine.predict_probability(weights, long_features)
    probability_short = engine.predict_probability(weights, short_features)
    shadow_side = engine.select_side(
        probability_long,
        probability_short,
        context,
    )
    learner = learner_config["learner"]
    warm = resolved_days < int(learner["warmup_resolved_days"])
    probability_max = max(probability_long, probability_short)
    margin = abs(probability_long - probability_short)
    if warm:
        eligible_side = "CASH"
        eligibility_reason = "WARMUP"
    elif probability_max < float(learner["minimum_probability"]):
        eligible_side = "CASH"
        eligibility_reason = "PROBABILITY_BELOW_FLOOR"
    elif margin < float(learner["minimum_side_margin"]):
        eligible_side = "CASH"
        eligibility_reason = "SIDE_MARGIN_BELOW_FLOOR"
    else:
        eligible_side = shadow_side
        eligibility_reason = "ELIGIBLE"

    long_outcome = engine.resolve_side(
        grouped,
        decision_time,
        "LONG",
        learner_config,
    )
    short_outcome = engine.resolve_side(
        grouped,
        decision_time,
        "SHORT",
        learner_config,
    )
    resolved = long_outcome is not None and short_outcome is not None
    record: dict[str, Any] = {
        "decision_date": day.isoformat(),
        "decision_time_utc": decision_time.strftime(engine.TIME_FORMAT),
        "status": "RESOLVED" if resolved else "PENDING_OUTCOME",
        "weights_hash_before": engine.weights_hash(weights),
        "training_days_before": resolved_days,
        "probability_long": probability_long,
        "probability_short": probability_short,
        "probability_margin": margin,
        "shadow_side": shadow_side,
        "eligible_side": eligible_side,
        "eligibility_reason": eligibility_reason,
        "context": context,
    }
    if not resolved:
        return record, weights, resolved_days

    assert long_outcome is not None
    assert short_outcome is not None
    record["long_outcome"] = asdict(long_outcome)
    record["short_outcome"] = asdict(short_outcome)
    selected = long_outcome if shadow_side == "LONG" else short_outcome
    record["shadow_result_r"] = selected.result_r
    record["eligible_result_r"] = selected.result_r if eligible_side != "CASH" else None
    updated = engine.update_weights(
        weights,
        long_features,
        short_features,
        int(long_outcome.outcome == "TARGET"),
        int(short_outcome.outcome == "TARGET"),
        resolved_days,
        learner_config,
    )
    new_resolved_days = resolved_days + 1
    record["weights_hash_after"] = engine.weights_hash(updated)
    record["training_days_after"] = new_resolved_days
    return record, updated, new_resolved_days


def profit_factor(values: list[float]) -> float:
    gross_profit = sum(value for value in values if value > 0.0)
    gross_loss = -sum(value for value in values if value < 0.0)
    return (
        gross_profit / gross_loss if gross_loss else math.inf if gross_profit else 0.0
    )


def payoff_ratio(values: list[float]) -> float | None:
    wins = [value for value in values if value > 0.0]
    losses = [-value for value in values if value < 0.0]
    if not wins or not losses:
        return None
    return (sum(wins) / len(wins)) / (sum(losses) / len(losses))


def maximum_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown


def outcome_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    values = [float(record["eligible_result_r"]) for record in records]
    return {
        "trades": len(values),
        "win_rate": (
            sum(value > 0.0 for value in values) / len(values) if values else 0.0
        ),
        "payoff_ratio": payoff_ratio(values),
        "profit_factor": profit_factor(values),
        "net_r": sum(values),
        "net_usd_0_01_lot": sum(values) * 0.8,
        "maximum_drawdown_r": maximum_drawdown(values),
    }


def evaluate(
    records: list[dict[str, Any]],
    resolved_days: int,
    learner_config: dict[str, Any],
) -> dict[str, Any]:
    warmup = int(learner_config["learner"]["warmup_resolved_days"])
    validation = [
        record
        for record in records
        if record.get("status") == "RESOLVED"
        and int(record.get("training_days_before", -1)) >= warmup
    ]
    eligible = [
        record
        for record in validation
        if record.get("eligible_side") in ("LONG", "SHORT")
        and record.get("eligible_result_r") is not None
    ]
    primary = outcome_metrics(eligible)
    validation_days = len(validation)
    primary["trades_per_validation_weekday"] = (
        len(eligible) / validation_days if validation_days else 0.0
    )
    stress_r = float(
        learner_config["admission"]["additional_round_trip_stress_pips"]
    ) / float(learner_config["execution"]["stop_pips"])
    stressed_records = [
        {
            **record,
            "eligible_result_r": float(record["eligible_result_r"]) - stress_r,
        }
        for record in eligible
    ]
    stressed = outcome_metrics(stressed_records)
    blocks = {}
    for name, start, end in (
        ("B1_2016H2_2018", "2016-07-01", "2019-01-01"),
        ("B2_2019_2021", "2019-01-01", "2022-01-01"),
        ("B3_2022_2024", "2022-01-01", "2025-01-01"),
        ("B4_2025_2026H1", "2025-01-01", "2026-07-01"),
    ):
        blocks[name] = outcome_metrics(
            [
                record
                for record in eligible
                if start <= str(record["decision_date"]) < end
            ]
        )
    latest_12 = outcome_metrics(
        [
            record
            for record in eligible
            if "2025-07-01" <= str(record["decision_date"]) < "2026-07-01"
        ]
    )
    monthly: dict[str, float] = defaultdict(float)
    for record in eligible:
        monthly[str(record["decision_date"])[:7]] += float(record["eligible_result_r"])
    positive_month_share = (
        sum(value > 0.0 for value in monthly.values()) / len(monthly)
        if monthly
        else 0.0
    )
    minimum_daily_needed = 0.85 - 0.203065
    projected_frequency = primary["trades_per_validation_weekday"] + 0.203065
    return {
        "status": "RETROSPECTIVE_DIAGNOSTIC_ONLY_NO_ADMISSION",
        "resolved_training_days": resolved_days,
        "validation_weekdays_after_warmup": validation_days,
        "missing_context_days": sum(
            record.get("status") == "MISSING_CONTEXT" for record in records
        ),
        "pending_outcome_days": sum(
            record.get("status") == "PENDING_OUTCOME" for record in records
        ),
        "primary": primary,
        "stress_plus_0_5_pip": stressed,
        "chronological_blocks": blocks,
        "latest_12_months": latest_12,
        "positive_active_month_share": positive_month_share,
        "minimum_daily_frequency_needed_for_combined_0_85": minimum_daily_needed,
        "projected_m15_plus_daily_trades_per_weekday_before_overlap_caps": (
            projected_frequency
        ),
        "diagnostic_frequency_sufficient": (
            primary["trades_per_validation_weekday"] >= minimum_daily_needed
        ),
        "diagnostic_edge_sufficient": (
            primary["profit_factor"] >= 1.1
            and stressed["profit_factor"] >= 1.0
            and primary["net_r"] > 0.0
        ),
        "demo_order_authorized": False,
    }


def run() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    learner_config, source_config = load_contracts()
    engine = load_engine()
    symbols = [
        learner_config["execution_symbol"],
        *learner_config["predictor_symbols"],
    ]
    frames, verified = load_source_frames(source_config, symbols)
    start = datetime.fromisoformat(
        source_config["period"]["from_inclusive"].replace("Z", "+00:00")
    ).date()
    end = datetime.fromisoformat(
        source_config["period"]["to_exclusive"].replace("Z", "+00:00")
    ).date()
    weights = [0.0] * 9
    resolved_days = 0
    records: list[dict[str, Any]] = []
    current = start
    while current < end:
        if current.weekday() < 5:
            grouped = build_day_bars(
                current,
                frames,
                learner_config,
                engine,
            )
            record, weights, resolved_days = replay_day(
                current,
                grouped,
                weights,
                resolved_days,
                learner_config,
                engine,
            )
            records.append(record)
        current += timedelta(days=1)
    result = evaluate(records, resolved_days, learner_config)
    result.update(
        {
            "schema_version": "eurusd_forward_learner_history_diagnostic_v1",
            "campaign_id": learner_config["campaign_id"],
            "diagnostic_period": source_config["period"],
            "historical_bar_adapter": {
                "source": "hash-verified M5 bid/ask OHLC bars",
                "spread_mean_points_proxy": (
                    "mean of bar-open and bar-close bid/ask spread; "
                    "intrabar tick-mean spread was unavailable"
                ),
                "outcome_path": "native bid/ask bar highs and lows",
            },
            "learner_config_sha256": sha256(LEARNER_CONFIG),
            "learner_source_sha256": sha256(LEARNER_MODULE),
            "historical_source_sha256_verified": verified,
            "final_weights_hash": engine.weights_hash(weights),
            "prohibitions": [
                "NO_THRESHOLD_TUNING_FROM_THIS_DIAGNOSTIC",
                "NO_RETROSPECTIVE_RESULT_COUNTS_AS_FORWARD_EVIDENCE",
                "NO_ORDER_AUTHORIZATION",
            ],
        }
    )
    return engine.json_safe(records), result


def json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def write_outputs(
    records: list[dict[str, Any]],
    result: dict[str, Any],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "DECISIONS.json").write_text(
        json.dumps(json_safe(records), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "RESULT.json").write_text(
        json.dumps(json_safe(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    primary = result["primary"]
    stress = result["stress_plus_0_5_pip"]
    lines = [
        "# Frozen forward learner historical diagnostic",
        "",
        "Status: **RETROSPECTIVE DIAGNOSTIC ONLY -- NO ADMISSION**",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Validation weekdays after warmup | {result['validation_weekdays_after_warmup']:,} |",
        f"| Eligible trades | {primary['trades']:,} |",
        (
            "| Trades/validation weekday | "
            f"{primary['trades_per_validation_weekday']:.4f} |"
        ),
        f"| Win rate | {primary['win_rate']:.2%} |",
        f"| Payoff ratio | {primary['payoff_ratio']} |",
        f"| Profit factor | {primary['profit_factor']:.4f} |",
        f"| Stressed PF (+0.5 pip) | {stress['profit_factor']:.4f} |",
        f"| Net at 0.01 lot | ${primary['net_usd_0_01_lot']:.2f} |",
        (
            "| Projected M15 + daily frequency before overlap caps | "
            f"{result['projected_m15_plus_daily_trades_per_weekday_before_overlap_caps']:.4f} |"
        ),
        "",
        "The exact frozen learner was replayed causally from zero weights. No",
        "parameter was changed. These already-mined historical prices cannot",
        "count toward forward admission or demo-order authorization.",
        "",
        "The source bars contain bid/ask OHLC but not intrabar tick-mean spread.",
        "The adapter therefore uses the mean of each bar's open and close spread",
        "for the spread feature; trade outcomes use the native bid/ask highs and lows.",
        "",
    ]
    (output_dir / "RESULT.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
