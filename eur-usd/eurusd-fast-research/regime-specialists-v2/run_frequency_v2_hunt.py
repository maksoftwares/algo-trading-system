from __future__ import annotations

from dataclasses import asdict
import hashlib
import itertools
import json
from pathlib import Path

import pandas as pd

from src.frequency_v2 import (
    FrequencyCandidate,
    load_capital_m15,
    metrics,
    route_portfolio,
    simulate,
)

ROOT = Path(__file__).resolve().parent
SOURCE = Path(
    "C:/MT5A1M5MomentumBacktest/Tester/Agent-127.0.0.1-3000/"
    "MQL5/Files/EURUSD_M15_CAPITAL_BROKER_201607_202607.csv"
)
EXPECTED_SHA256 = "eacc532a5f0001ea66c80a558bd4cffe7ced5704bf9d9d4770cb2f783269bea0"
WINDOWS = {
    "development": (pd.Timestamp("2016-07-01", tz="UTC"), pd.Timestamp("2022-07-01", tz="UTC")),
    "validation": (pd.Timestamp("2022-07-01", tz="UTC"), pd.Timestamp("2024-07-01", tz="UTC")),
}


def candidates() -> list[FrequencyCandidate]:
    rows: list[FrequencyCandidate] = []
    counter = itertools.count(1)

    def add(**kwargs):
        rows.append(FrequencyCandidate(candidate_id=f"EURF2_{next(counter):04d}", **kwargs))

    for family, regimes, thresholds in (
        ("rsi_fade", ("chop", "compression", "transition"), (25.0, 30.0, 35.0)),
        ("bb_fade", ("chop", "compression", "transition"), (1.5, 2.0, 2.5)),
        ("bb_reclaim", ("chop", "compression", "transition"), (1.5, 2.0, 2.5)),
    ):
        for regime, direction, threshold, stop, target, session in itertools.product(
            regimes,
            ("long", "short"),
            thresholds,
            (1.0, 1.4, 1.8),
            (0.7, 0.8, 1.0),
            ("all", "liquid"),
        ):
            add(
                family=family,
                regime=regime,
                direction=direction,
                threshold=threshold,
                stop_atr=stop,
                target_r=target,
                max_hold_bars=32,
                session=session,
            )
    for family, regime_direction in (
        ("trend_break", (("trend_up", "long"), ("trend_down", "short"))),
        ("trend_pullback", (("trend_up", "long"), ("trend_down", "short"))),
    ):
        for (regime, direction), lookback, body, stop, target, session in itertools.product(
            regime_direction,
            (4, 8, 16),
            (0.25, 0.50),
            (1.0, 1.5),
            (1.0, 1.5),
            ("all", "liquid"),
        ):
            add(
                family=family,
                regime=regime,
                direction=direction,
                threshold=0.0,
                stop_atr=stop,
                target_r=target,
                max_hold_bars=40,
                lookback=lookback,
                body_min=body,
                session=session,
            )
    for regime, direction, lookback, body, stop, target, session in itertools.product(
        ("compression",),
        ("long", "short"),
        (4, 8, 16),
        (0.25, 0.50),
        (1.0, 1.5),
        (1.0, 1.5),
        ("all", "liquid"),
    ):
        add(
            family="compression_break",
            regime=regime,
            direction=direction,
            threshold=0.0,
            stop_atr=stop,
            target_r=target,
            max_hold_bars=40,
            lookback=lookback,
            body_min=body,
            session=session,
        )
    return rows


def active_days(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> int:
    mask = (frame["timestamp"] >= start) & (frame["timestamp"] < end)
    return int(frame.loc[mask, "active_date"].nunique())


def main() -> None:
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != EXPECTED_SHA256:
        raise RuntimeError("Capital.com M15 source checksum mismatch")
    contract = json.loads((ROOT / "config" / "eurusd_regime_specialists_v2.json").read_text())
    frame, h4 = load_capital_m15(SOURCE, contract["regime_classifier"])
    output = ROOT / "outputs" / "frequency_v2_hunt"
    output.mkdir(parents=True, exist_ok=True)
    universe = candidates()
    stage_days = {name: active_days(frame, *window) for name, window in WINDOWS.items()}
    metric_rows = []
    development_trades: dict[str, list[dict]] = {}
    development_pass: list[FrequencyCandidate] = []

    for index, candidate in enumerate(universe, 1):
        trades = simulate(frame, candidate, *WINDOWS["development"])
        row = {**asdict(candidate), **metrics(trades, stage_days["development"])}
        row["parameter_sha256"] = candidate.parameter_sha256
        row["stage"] = "development"
        row["gate_pass"] = bool(
            row["trades"] >= 180
            and row["profit_factor"] >= 1.08
            and row["average_r"] > 0
            and row["top_5pct_removed_profit_factor"] >= 0.90
        )
        metric_rows.append(row)
        if row["gate_pass"]:
            development_trades[candidate.candidate_id] = trades
            development_pass.append(candidate)
        if index % 100 == 0:
            print(f"screened {index}/{len(universe)}; development passes={len(development_pass)}")

    validation_trades: dict[str, list[dict]] = {}
    validation_pass: list[tuple[FrequencyCandidate, dict]] = []
    for candidate in development_pass:
        trades = simulate(frame, candidate, *WINDOWS["validation"])
        row = {**asdict(candidate), **metrics(trades, stage_days["validation"])}
        row["parameter_sha256"] = candidate.parameter_sha256
        row["stage"] = "validation"
        row["gate_pass"] = bool(
            row["trades"] >= 60
            and row["profit_factor"] >= 1.05
            and row["average_r"] > 0
            and row["top_5pct_removed_profit_factor"] >= 0.85
        )
        metric_rows.append(row)
        if row["gate_pass"]:
            validation_trades[candidate.candidate_id] = trades
            validation_pass.append((candidate, row))

    # Keep only the most robust parameterization for each independent sleeve.
    validation_pass.sort(
        key=lambda item: (
            min(item[1]["profit_factor"], item[1]["top_5pct_removed_profit_factor"]),
            item[1]["trades"],
        ),
        reverse=True,
    )
    sleeves: list[tuple[FrequencyCandidate, dict]] = []
    sleeve_keys: set[tuple[str, str, str]] = set()
    for candidate, row in validation_pass:
        key = (candidate.family, candidate.regime, candidate.direction)
        if key in sleeve_keys:
            continue
        sleeve_keys.add(key)
        sleeves.append((candidate, row))

    # Greedily add independent sleeves while preserving quality. Frequency is
    # rewarded only after PF and positive expectancy remain above the floor.
    priority: list[str] = []
    remaining = sleeves.copy()
    portfolio_rows = []
    while remaining:
        best = None
        for candidate, row in remaining:
            trial_priority = priority + [candidate.candidate_id]
            trial = route_portfolio(validation_trades, trial_priority)
            trial_metrics = metrics(trial, stage_days["validation"])
            quality_ok = (
                trial_metrics["profit_factor"] >= 1.20
                and trial_metrics["win_rate"] >= 0.50
                and trial_metrics["average_r"] > 0
            )
            score = (
                (1 if quality_ok else 0),
                min(trial_metrics["trades_per_active_day"], 1.0),
                trial_metrics["profit_factor"],
                trial_metrics["net_r"],
            )
            if best is None or score > best[0]:
                best = (score, candidate, trial_metrics)
        assert best is not None
        _, selected, selected_metrics = best
        if selected_metrics["profit_factor"] < 1.20 or selected_metrics["average_r"] <= 0:
            break
        priority.append(selected.candidate_id)
        remaining = [item for item in remaining if item[0].candidate_id != selected.candidate_id]
        portfolio_rows.append(
            {
                "selection_order": len(priority),
                "candidate_id": selected.candidate_id,
                **selected_metrics,
            }
        )
        if selected_metrics["trades_per_active_day"] >= 1.0 and len(priority) >= 3:
            break

    portfolio = route_portfolio(validation_trades, priority)
    portfolio_metrics = metrics(portfolio, stage_days["validation"])
    selected_specs = [asdict(next(c for c in universe if c.candidate_id == candidate_id)) for candidate_id in priority]
    distinct_regimes = len({spec["regime"] for spec in selected_specs})
    portfolio_pass = bool(
        portfolio_metrics["trades_per_active_day"] >= 1.0
        and portfolio_metrics["profit_factor"] >= 1.30
        and portfolio_metrics["win_rate"] >= 0.52
        and portfolio_metrics["maximum_drawdown_r"] <= 25.0
        and portfolio_metrics["positive_active_month_share"] >= 0.55
        and portfolio_metrics["top_5pct_removed_profit_factor"] >= 1.0
        and distinct_regimes >= 3
    )
    pd.DataFrame(metric_rows).to_csv(output / "CANDIDATE_METRICS.csv", index=False)
    pd.DataFrame(portfolio_rows).to_csv(output / "PORTFOLIO_SELECTION_PATH.csv", index=False)
    pd.DataFrame(portfolio).to_csv(output / "VALIDATION_PORTFOLIO_TRADES.csv", index=False)
    verdict = {
        "schema_version": "eurusd_frequency_v2_hunt_v1",
        "source": str(SOURCE),
        "source_sha256": EXPECTED_SHA256,
        "source_rows": len(frame),
        "history_quality_pct": 99,
        "active_days": stage_days,
        "candidate_count": len(universe),
        "development_pass_count": len(development_pass),
        "validation_pass_count": len(validation_pass),
        "selected_priority": priority,
        "selected_specialists": selected_specs,
        "distinct_regimes": distinct_regimes,
        "validation_portfolio_metrics": portfolio_metrics,
        "validation_gate_pass": portfolio_pass,
        "exam_opened": False,
        "verdict": (
            "FREEZE_PORTFOLIO_AND_OPEN_ADAPTIVE_DEMO_EXAM"
            if portfolio_pass
            else "FREQUENCY_OR_QUALITY_GATE_FAILED_CONTINUE_RESEARCH"
        ),
    }
    (output / "VERDICT.json").write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
