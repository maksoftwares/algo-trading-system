from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import math
from statistics import mean, median
from typing import Iterable


BAR_MS = 300_000


def tick_identity(tick: dict) -> tuple:
    return tuple(tick.get(name) for name in ("time", "time_msc", "bid", "ask", "last", "volume", "flags"))


def normalize_ticks(ticks: Iterable[dict]) -> tuple[list[dict], dict]:
    rows = list(ticks)
    decreasing = sum(rows[i]["time_msc"] < rows[i - 1]["time_msc"] for i in range(1, len(rows)))
    duplicate_count = len(rows) - len({tick_identity(row) for row in rows})
    crossed = sum(row["ask"] < row["bid"] for row in rows)
    zero = sum(row["bid"] <= 0 or row["ask"] <= 0 for row in rows)
    missing = sum(not math.isfinite(row["bid"]) or not math.isfinite(row["ask"]) for row in rows)
    ordered = sorted(rows, key=lambda row: row["time_msc"])
    return ordered, {"decreasing": decreasing, "duplicates": duplicate_count, "crossed": crossed, "zero_bid_ask": zero, "missing_bid_ask": missing}


def interval_start(time_msc: int) -> int:
    return time_msc // BAR_MS * BAR_MS


def aggregate_ticks(ticks: Iterable[dict], digits: int, include_last: bool = False) -> dict[int, dict]:
    ordered, integrity = normalize_ticks(ticks)
    if any(integrity[name] for name in ("decreasing", "crossed", "zero_bid_ask", "missing_bid_ask")):
        raise ValueError("invalid tick integrity")
    groups: dict[int, list[dict]] = defaultdict(list)
    for tick in ordered:
        groups[interval_start(tick["time_msc"])].append(tick)
    result = {}
    for start, rows in groups.items():
        candidates = {}
        for basis in ("BID", "ASK", "MID"):
            values = [row["bid"] if basis == "BID" else row["ask"] if basis == "ASK" else (row["bid"] + row["ask"]) / 2 for row in rows]
            candidates[basis] = tuple(round(value, digits) for value in (values[0], max(values), min(values), values[-1]))
        if include_last and all(row.get("last", 0) > 0 for row in rows):
            values = [row["last"] for row in rows]
            candidates["LAST"] = tuple(round(value, digits) for value in (values[0], max(values), min(values), values[-1]))
        spreads = [row["ask"] - row["bid"] for row in rows]
        result[start] = {"start_msc": start, "first_tick_msc": rows[0]["time_msc"], "last_tick_msc": rows[-1]["time_msc"],
                         "tick_count": len(rows), "ohlc": candidates,
                         "spreads": {"BAR_OPEN_SPREAD": spreads[0], "BAR_CLOSE_SPREAD": spreads[-1],
                                     "BAR_MINIMUM_SPREAD": min(spreads), "BAR_MAXIMUM_SPREAD": max(spreads),
                                     "BAR_MEAN_SPREAD": mean(spreads), "BAR_MEDIAN_SPREAD": median(spreads)}}
    return result


def complete_interval(bar: dict, query_start_msc: int, query_end_msc: int) -> bool:
    return bar["start_msc"] >= query_start_msc and bar["start_msc"] + BAR_MS <= query_end_msc


def difference_metrics(actual: list[float], expected: list[float], point: float) -> dict:
    errors = [abs(a - e) for a, e in zip(actual, expected)]
    ordered = sorted(errors)
    p95 = ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)] if ordered else None
    return {"count": len(errors), "exact_count": sum(a == e for a, e in zip(actual, expected)),
            "exact_rate": sum(a == e for a, e in zip(actual, expected)) / len(errors) if errors else 0,
            "mean_abs_difference": mean(errors) if errors else None, "median_abs_difference": median(errors) if errors else None,
            "p95_abs_difference": p95, "maximum_abs_difference": max(errors) if errors else None,
            "median_difference_points": median(errors) / point if errors else None}


def basis_pass(metrics: dict[str, dict]) -> bool:
    limits = {"open": .9999, "high": .995, "low": .995, "close": .9999}
    return all(metrics[field]["exact_rate"] >= limit for field, limit in limits.items())


def separated(selected: dict, alternatives: list[dict]) -> bool:
    for other in alternatives:
        rate_gap = min(selected[field]["exact_rate"] - other[field]["exact_rate"] for field in ("open", "close")) * 100
        selected_error = median([selected[field]["median_abs_difference"] for field in ("open", "close")])
        other_error = median([other[field]["median_abs_difference"] for field in ("open", "close")])
        if rate_gap < .25 and not (other_error > 0 and selected_error <= .25 * other_error):
            return False
    return True


def spread_metrics(actual: list[float], expected: list[float]) -> dict:
    errors = [abs(a - e) for a, e in zip(actual, expected)]
    ordered = sorted(errors)
    return {"count": len(errors), "exact_count": sum(error == 0 for error in errors),
            "exact_rate": sum(error == 0 for error in errors) / len(errors) if errors else 0,
            "within_one_count": sum(error <= 1 for error in errors),
            "within_one_rate": sum(error <= 1 for error in errors) / len(errors) if errors else 0,
            "mean_abs_error_points": mean(errors) if errors else None, "median_abs_error_points": median(errors) if errors else None,
            "p95_abs_error_points": ordered[max(0, math.ceil(.95 * len(ordered)) - 1)] if errors else None,
            "maximum_abs_error_points": max(errors) if errors else None}


def spread_pass(metrics: dict) -> bool:
    return metrics["exact_rate"] >= .995 or (metrics["within_one_rate"] >= .999 and metrics["median_abs_error_points"] <= .25)


def aggregate_ohlc(bars: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return bars[0][0], max(row[1] for row in bars), min(row[2] for row in bars), bars[-1][3]


def segment(timestamp_msc: int) -> str:
    value = datetime.fromtimestamp(timestamp_msc / 1000, timezone.utc)
    if value < datetime(2024, 1, 1, tzinfo=timezone.utc):
        return "DEVELOPMENT_OVERLAP"
    if value < datetime(2025, 7, 1, tzinfo=timezone.utc):
        return "VALIDATION_OVERLAP"
    return "LOCKED_EXAM_OVERLAP"


def all_three_resolved(classifications: dict[str, str]) -> bool:
    return set(classifications) == {"XAUUSD", "EURUSD", "USDJPY"} and all(value.startswith("QUOTE_CONTRACT_RESOLVED_") for value in classifications.values())


def strategy_scoring_allowed(classifications: dict[str, str]) -> bool:
    return all_three_resolved(classifications)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
