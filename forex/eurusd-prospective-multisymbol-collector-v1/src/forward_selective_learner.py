from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Iterable


TIME_FORMAT = "%Y.%m.%d %H:%M:%S"
PIP = 0.0001


@dataclass(frozen=True)
class Bar:
    interval_open: datetime
    symbol: str
    status: str
    copied_ticks: int
    first_bid: float
    first_ask: float
    last_bid: float
    last_ask: float
    bid_high: float
    bid_low: float
    ask_high: float
    ask_low: float
    spread_mean_points: float
    point: float

    @property
    def first_mid(self) -> float:
        return (self.first_bid + self.first_ask) / 2.0

    @property
    def last_mid(self) -> float:
        return (self.last_bid + self.last_ask) / 2.0


@dataclass(frozen=True)
class SideOutcome:
    side: str
    outcome: str
    result_r: float
    exit_time: datetime


def clip(value: float, limit: float) -> float:
    return max(-limit, min(limit, value))


def sigmoid(value: float) -> float:
    bounded = clip(value, 35.0)
    return 1.0 / (1.0 + math.exp(-bounded))


def sign(value: float) -> float:
    if value > 0.0:
        return 1.0
    if value < 0.0:
        return -1.0
    return 0.0


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    return float(value) if value not in ("", None) else 0.0


def _int(row: dict[str, str], key: str) -> int:
    value = row.get(key, "")
    return int(value) if value not in ("", None) else 0


def load_forward_bars(
    feature_csv: Path,
    config: dict[str, Any],
) -> dict[datetime, dict[str, Bar]]:
    required_scope = config["evidence_scope_required"]
    floor = datetime.strptime(config["forward_floor_utc"], TIME_FORMAT)
    grouped: dict[datetime, dict[str, Bar]] = defaultdict(dict)
    if not feature_csv.exists():
        return {}

    with feature_csv.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("evidence_scope") != required_scope:
                raise ValueError("non-prospective evidence scope refused")
            interval_open = datetime.strptime(
                row["interval_open_configured_utc"], TIME_FORMAT
            )
            if interval_open < floor:
                raise ValueError("pre-floor feature row refused")
            if interval_open.minute % 5 != 0 or interval_open.second != 0:
                raise ValueError("non-native-M5 interval refused")
            symbol = row["source_symbol"]
            if symbol in grouped[interval_open]:
                raise ValueError("duplicate symbol/interval row refused")
            grouped[interval_open][symbol] = Bar(
                interval_open=interval_open,
                symbol=symbol,
                status=row["source_status"],
                copied_ticks=_int(row, "copied_tick_count"),
                first_bid=_float(row, "first_bid"),
                first_ask=_float(row, "first_ask"),
                last_bid=_float(row, "last_bid"),
                last_ask=_float(row, "last_ask"),
                bid_high=_float(row, "bid_high"),
                bid_low=_float(row, "bid_low"),
                ask_high=_float(row, "ask_high"),
                ask_low=_float(row, "ask_low"),
                spread_mean_points=_float(row, "spread_mean_points"),
                point=_float(row, "symbol_point"),
            )
    return dict(grouped)


def exact_opens(end_exclusive: datetime, minutes: int) -> list[datetime]:
    count = minutes // 5
    return [
        end_exclusive - timedelta(minutes=5 * offset)
        for offset in range(count, 0, -1)
    ]


def require_bars(
    grouped: dict[datetime, dict[str, Bar]],
    opens: Iterable[datetime],
    symbols: Iterable[str],
) -> dict[str, list[Bar]] | None:
    result = {symbol: [] for symbol in symbols}
    for interval_open in opens:
        interval = grouped.get(interval_open)
        if interval is None:
            return None
        for symbol in symbols:
            bar = interval.get(symbol)
            if (
                bar is None
                or bar.status != "OK"
                or bar.copied_ticks <= 0
                or bar.first_bid <= 0.0
                or bar.first_ask <= 0.0
                or bar.last_bid <= 0.0
                or bar.last_ask <= 0.0
            ):
                return None
            result[symbol].append(bar)
    return result


def oriented_returns(
    bars: dict[str, list[Bar]],
    config: dict[str, Any],
) -> dict[str, float]:
    signs = config["oriented_return_signs"]
    values: dict[str, float] = {}
    for symbol, symbol_bars in bars.items():
        start = symbol_bars[0].first_mid
        end = symbol_bars[-1].last_mid
        if start <= 0.0 or end <= 0.0:
            raise ValueError("invalid mid price")
        values[symbol] = float(signs[symbol]) * math.log(end / start)
    return values


def build_context(
    grouped: dict[datetime, dict[str, Bar]],
    decision_time: datetime,
    config: dict[str, Any],
) -> dict[str, float] | None:
    predictor_symbols = list(config["predictor_symbols"])
    horizons = config["features"]["return_horizons_minutes"]
    scales = config["features"]["fixed_return_scales"]
    feature_clip = float(config["features"]["feature_clip"])
    context: dict[str, float] = {}

    for horizon in horizons:
        bars = require_bars(
            grouped,
            exact_opens(decision_time, int(horizon)),
            predictor_symbols,
        )
        if bars is None:
            return None
        returns = oriented_returns(bars, config)
        context[f"strength_{horizon}"] = clip(
            sum(returns.values()) / len(returns) / float(scales[str(horizon)]),
            feature_clip,
        )
        context[f"agreement_{horizon}"] = (
            sum(sign(value) for value in returns.values()) / len(returns)
        )

    current_opens = exact_opens(
        decision_time,
        int(config["features"]["activity_current_minutes"]),
    )
    prior_end = current_opens[0]
    prior_opens = exact_opens(
        prior_end,
        int(config["features"]["activity_prior_minutes"]),
    )
    current = require_bars(grouped, current_opens, predictor_symbols)
    prior = require_bars(grouped, prior_opens, predictor_symbols)
    if current is None or prior is None:
        return None
    current_returns = oriented_returns(current, config)
    activity_terms = []
    for symbol in predictor_symbols:
        current_ticks = sum(bar.copied_ticks for bar in current[symbol])
        prior_ticks = sum(bar.copied_ticks for bar in prior[symbol])
        if prior_ticks <= 0:
            return None
        activity_change = clip(current_ticks / prior_ticks - 1.0, 2.0)
        activity_terms.append(sign(current_returns[symbol]) * activity_change)
    context["signed_activity_60"] = clip(
        sum(activity_terms) / len(activity_terms),
        feature_clip,
    )

    eurusd = require_bars(
        grouped,
        exact_opens(decision_time, 60),
        [config["execution_symbol"]],
    )
    if eurusd is None:
        return None
    spread_pips = [
        bar.spread_mean_points * bar.point / PIP
        for bar in eurusd[config["execution_symbol"]]
    ]
    spread_reference = float(
        config["features"]["eurusd_spread_reference_pips"]
    )
    context["cost_pressure"] = clip(
        sum(spread_pips) / len(spread_pips) / spread_reference - 1.0,
        2.0,
    )
    return context


def side_features(
    context: dict[str, float],
    side: str,
) -> list[float]:
    side_sign = 1.0 if side == "LONG" else -1.0
    return [
        1.0,
        context["cost_pressure"],
        side_sign * context["strength_15"],
        side_sign * context["strength_60"],
        side_sign * context["strength_240"],
        side_sign * context["agreement_15"],
        side_sign * context["agreement_60"],
        side_sign * context["agreement_240"],
        side_sign * context["signed_activity_60"],
    ]


def weights_hash(weights: list[float]) -> str:
    payload = json.dumps(
        [round(value, 12) for value in weights],
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def predict_probability(weights: list[float], features: list[float]) -> float:
    return sigmoid(sum(weight * value for weight, value in zip(weights, features)))


def update_weights(
    weights: list[float],
    long_features: list[float],
    short_features: list[float],
    long_label: int,
    short_label: int,
    resolved_days_before: int,
    config: dict[str, Any],
) -> list[float]:
    learner = config["learner"]
    learning_rate = float(learner["learning_rate"]) / math.sqrt(
        1.0 + resolved_days_before / float(learner["learning_rate_decay_days"])
    )
    l2 = float(learner["l2_penalty"])
    limit = float(learner["weight_clip"])
    long_probability = predict_probability(weights, long_features)
    short_probability = predict_probability(weights, short_features)
    updated = []
    for index, weight in enumerate(weights):
        gradient = (
            (long_probability - long_label) * long_features[index]
            + (short_probability - short_label) * short_features[index]
        ) / 2.0
        if index > 0:
            gradient += l2 * weight
        updated.append(clip(weight - learning_rate * gradient, limit))
    return updated


def resolve_side(
    grouped: dict[datetime, dict[str, Bar]],
    decision_time: datetime,
    side: str,
    config: dict[str, Any],
) -> SideOutcome | None:
    execution = config["execution"]
    symbol = config["execution_symbol"]
    opens = [
        decision_time + timedelta(minutes=5 * index)
        for index in range(int(execution["maximum_hold_minutes"]) // 5)
    ]
    path = require_bars(grouped, opens, [symbol])
    if path is None:
        return None
    bars = path[symbol]
    entry_slippage = float(execution["entry_slippage_pips_each_side"]) * PIP
    exit_slippage = float(execution["exit_slippage_pips_each_side"]) * PIP
    stop_distance = float(execution["stop_pips"]) * PIP
    target_distance = float(execution["target_pips"]) * PIP

    if side == "LONG":
        entry = bars[0].first_ask + entry_slippage
        stop = entry - stop_distance
        target = entry + target_distance
        for bar in bars:
            stop_hit = bar.bid_low <= stop
            target_hit = bar.bid_high >= target
            if stop_hit:
                return SideOutcome(
                    side,
                    "STOP",
                    (-stop_distance - exit_slippage) / stop_distance,
                    bar.interval_open,
                )
            if target_hit:
                return SideOutcome(
                    side,
                    "TARGET",
                    (target_distance - exit_slippage) / stop_distance,
                    bar.interval_open,
                )
        exit_price = bars[-1].last_bid - exit_slippage
        result_r = (exit_price - entry) / stop_distance
    else:
        entry = bars[0].first_bid - entry_slippage
        stop = entry + stop_distance
        target = entry - target_distance
        for bar in bars:
            stop_hit = bar.ask_high >= stop
            target_hit = bar.ask_low <= target
            if stop_hit:
                return SideOutcome(
                    side,
                    "STOP",
                    (-stop_distance - exit_slippage) / stop_distance,
                    bar.interval_open,
                )
            if target_hit:
                return SideOutcome(
                    side,
                    "TARGET",
                    (target_distance - exit_slippage) / stop_distance,
                    bar.interval_open,
                )
        exit_price = bars[-1].last_ask + exit_slippage
        result_r = (entry - exit_price) / stop_distance
    return SideOutcome(side, "TIME", result_r, bars[-1].interval_open)


def decision_datetime(day: date, config: dict[str, Any]) -> datetime:
    parsed = time.fromisoformat(config["decision_clock_utc"])
    return datetime.combine(day, parsed)


def available_weekdays(
    grouped: dict[datetime, dict[str, Bar]],
) -> list[date]:
    return sorted(
        {
            interval_open.date()
            for interval_open in grouped
            if interval_open.weekday() < 5
        }
    )


def profit_factor(values: list[float]) -> float | None:
    gross_profit = sum(value for value in values if value > 0.0)
    gross_loss = -sum(value for value in values if value < 0.0)
    if gross_loss <= 0.0:
        return None
    return gross_profit / gross_loss


def payoff_ratio(values: list[float]) -> float | None:
    wins = [value for value in values if value > 0.0]
    losses = [-value for value in values if value < 0.0]
    if not wins or not losses:
        return None
    return (sum(wins) / len(wins)) / (sum(losses) / len(losses))


def admission_metrics(
    eligible: list[dict[str, Any]],
    resolved_days: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    results = [float(record["eligible_result_r"]) for record in eligible]
    wins = [value for value in results if value > 0.0]
    stress_pips = float(
        config["admission"]["additional_round_trip_stress_pips"]
    )
    stress_r = stress_pips / float(config["execution"]["stop_pips"])
    stressed = [value - stress_r for value in results]

    best_five_indexes = sorted(
        range(len(results)),
        key=lambda index: results[index],
        reverse=True,
    )[:5]
    removed = {
        index for index in best_five_indexes if results[index] > 0.0
    }
    best_five_removed = [
        value for index, value in enumerate(results) if index not in removed
    ]

    month_net: dict[str, float] = defaultdict(float)
    for record, result in zip(eligible, results):
        month_net[str(record["decision_date"])[:7]] += result
    total_net = sum(results)
    maximum_month_profit_share: float | None = None
    if total_net > 0.0 and month_net:
        maximum_month_profit_share = max(month_net.values()) / total_net

    pf = profit_factor(results)
    payoff = payoff_ratio(results)
    stressed_pf = profit_factor(stressed)
    best_five_removed_pf = profit_factor(best_five_removed)
    admission = config["admission"]
    checks = {
        "minimum_eligible_trades": (
            len(results) >= int(admission["minimum_eligible_trades"])
        ),
        "minimum_active_validation_days": (
            len({record["decision_date"] for record in eligible})
            >= int(admission["minimum_active_validation_days"])
        ),
        "positive_net_expectancy": total_net > 0.0,
        "minimum_profit_factor": (
            pf is not None and pf >= float(admission["minimum_profit_factor"])
        ),
        "minimum_payoff_ratio": (
            payoff is not None
            and payoff >= float(admission["minimum_payoff_ratio"])
        ),
        "minimum_stressed_profit_factor": (
            stressed_pf is not None
            and stressed_pf
            >= float(admission["minimum_stressed_profit_factor"])
        ),
        "minimum_best_five_removed_profit_factor": (
            best_five_removed_pf is not None
            and best_five_removed_pf
            >= float(admission["minimum_best_five_removed_profit_factor"])
        ),
        "maximum_single_month_profit_share": (
            maximum_month_profit_share is not None
            and maximum_month_profit_share
            <= float(admission["maximum_single_month_profit_share"])
        ),
    }
    enough_evidence = (
        checks["minimum_eligible_trades"]
        and checks["minimum_active_validation_days"]
    )
    return {
        "eligible_trades": len(results),
        "eligible_frequency_per_resolved_day": (
            len(results) / resolved_days if resolved_days else 0.0
        ),
        "eligible_win_rate": len(wins) / len(results) if results else 0.0,
        "eligible_payoff": payoff,
        "eligible_profit_factor": pf,
        "eligible_net_r": total_net,
        "stress_r_per_trade": stress_r,
        "stressed_profit_factor": stressed_pf,
        "stressed_net_r": sum(stressed),
        "best_five_removed_profit_factor": best_five_removed_pf,
        "best_five_removed_net_r": sum(best_five_removed),
        "monthly_net_r": dict(sorted(month_net.items())),
        "maximum_single_month_profit_share": maximum_month_profit_share,
        "checks": checks,
        "research_economic_gates_pass": enough_evidence and all(checks.values()),
        "mt5_parity_complete": False,
        "shadow_demo_soak_complete": False,
        "demo_order_authorized": False,
        "status": (
            "WAITING_MINIMUM_EVIDENCE"
            if not enough_evidence
            else (
                "RESEARCH_ECONOMIC_GATES_PASS_MT5_PENDING"
                if all(checks.values())
                else "REJECT"
            )
        ),
    }


def select_side(
    probability_long: float,
    probability_short: float,
    context: dict[str, float],
) -> str:
    if probability_long > probability_short:
        return "LONG"
    if probability_short > probability_long:
        return "SHORT"
    return "LONG" if context["strength_60"] >= 0.0 else "SHORT"


def process(
    grouped: dict[datetime, dict[str, Bar]],
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    weights = [0.0] * 9
    resolved_days = 0
    records: list[dict[str, Any]] = []
    latest_interval = max(grouped) if grouped else None
    for day in available_weekdays(grouped):
        decision_time = decision_datetime(day, config)
        if (
            latest_interval is None
            or latest_interval < decision_time - timedelta(minutes=5)
        ):
            continue
        context = build_context(grouped, decision_time, config)
        if context is None:
            records.append(
                {
                    "decision_date": day.isoformat(),
                    "decision_time_utc": decision_time.strftime(TIME_FORMAT),
                    "status": "MISSING_CONTEXT",
                    "eligible_side": "CASH",
                    "training_days_before": resolved_days,
                }
            )
            continue

        long_features = side_features(context, "LONG")
        short_features = side_features(context, "SHORT")
        probability_long = predict_probability(weights, long_features)
        probability_short = predict_probability(weights, short_features)
        shadow_side = select_side(
            probability_long,
            probability_short,
            context,
        )
        learner = config["learner"]
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

        long_outcome = resolve_side(grouped, decision_time, "LONG", config)
        short_outcome = resolve_side(grouped, decision_time, "SHORT", config)
        resolved = long_outcome is not None and short_outcome is not None
        record: dict[str, Any] = {
            "decision_date": day.isoformat(),
            "decision_time_utc": decision_time.strftime(TIME_FORMAT),
            "status": "RESOLVED" if resolved else "PENDING_OUTCOME",
            "weights_hash_before": weights_hash(weights),
            "training_days_before": resolved_days,
            "probability_long": probability_long,
            "probability_short": probability_short,
            "probability_margin": margin,
            "shadow_side": shadow_side,
            "eligible_side": eligible_side,
            "eligibility_reason": eligibility_reason,
            "context": context,
        }
        if resolved:
            assert long_outcome is not None
            assert short_outcome is not None
            record["long_outcome"] = asdict(long_outcome)
            record["short_outcome"] = asdict(short_outcome)
            selected = (
                long_outcome if shadow_side == "LONG" else short_outcome
            )
            record["shadow_result_r"] = selected.result_r
            record["eligible_result_r"] = (
                selected.result_r if eligible_side != "CASH" else None
            )
            weights = update_weights(
                weights,
                long_features,
                short_features,
                int(long_outcome.outcome == "TARGET"),
                int(short_outcome.outcome == "TARGET"),
                resolved_days,
                config,
            )
            resolved_days += 1
            record["weights_hash_after"] = weights_hash(weights)
            record["training_days_after"] = resolved_days
        records.append(record)

    eligible = [
        record
        for record in records
        if record.get("eligible_side") in ("LONG", "SHORT")
        and record.get("eligible_result_r") is not None
    ]
    admission = admission_metrics(eligible, resolved_days, config)
    summary = {
        "campaign_id": config["campaign_id"],
        "status": "WAITING_FORWARD_DATA" if not records else "FORWARD_ONLY_SHADOW",
        "calendar_decisions": sum(
            record.get("status") != "MISSING_CONTEXT" for record in records
        ),
        "resolved_training_days": resolved_days,
        "shadow_frequency_per_resolved_day": (
            sum(
                record.get("status") == "RESOLVED"
                for record in records
            )
            / resolved_days
            if resolved_days
            else 0.0
        ),
        "admission": admission,
        "final_weights": weights,
        "final_weights_hash": weights_hash(weights),
        "prohibitions": config["prohibitions"],
    }
    return records, summary


def json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.strftime(TIME_FORMAT)
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def validate_append_only(
    existing_records: list[dict[str, Any]],
    new_records: list[dict[str, Any]],
) -> None:
    safe_new = json_safe(new_records)
    if len(safe_new) < len(existing_records):
        raise ValueError("forward decision ledger shrank")
    for index, existing in enumerate(existing_records):
        if existing != safe_new[index]:
            raise ValueError(
                "forward decision ledger mutation refused "
                f"at index={index} date={existing.get('decision_date')}"
            )


def load_existing_decisions(output_dir: Path) -> list[dict[str, Any]]:
    path = output_dir / "FORWARD_DECISIONS.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("existing forward decision ledger is not a list")
    return payload


def atomic_write_text(path: Path, value: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value)
    temporary.replace(path)


def write_outputs(
    records: list[dict[str, Any]],
    summary: dict[str, Any],
    output_dir: Path,
    enforce_append_only: bool = False,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if enforce_append_only:
        validate_append_only(load_existing_decisions(output_dir), records)
    atomic_write_text(
        output_dir / "FORWARD_DECISIONS.json",
        json.dumps(json_safe(records), indent=2, sort_keys=True) + "\n",
    )
    atomic_write_text(
        output_dir / "FORWARD_SUMMARY.json",
        json.dumps(json_safe(summary), indent=2, sort_keys=True) + "\n",
    )

    lines = [
        "# EURUSD forward-only selective learner",
        "",
        f"Status: `{summary['status']}`",
        "",
        f"- Calendar decisions: {summary['calendar_decisions']}",
        f"- Resolved training days: {summary['resolved_training_days']}",
        f"- Eligible trades: {summary['admission']['eligible_trades']}",
        (
            "- Eligible frequency/resolved day: "
            f"{summary['admission']['eligible_frequency_per_resolved_day']:.4f}"
        ),
        f"- Eligible win rate: {summary['admission']['eligible_win_rate']:.4f}",
        f"- Eligible payoff: {summary['admission']['eligible_payoff']}",
        f"- Eligible PF: {summary['admission']['eligible_profit_factor']}",
        f"- Eligible net: {summary['admission']['eligible_net_r']:.4f}R",
        f"- Admission: `{summary['admission']['status']}`",
        "",
        (
            "This is a forward-only shadow report. It authorizes no orders and "
            "does not alter the protected H4 sleeve."
        ),
    ]
    atomic_write_text(
        output_dir / "FORWARD_SUMMARY.md",
        "\n".join(lines) + "\n",
    )
