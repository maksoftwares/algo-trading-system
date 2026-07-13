"""Reproduce outcome-blind availability evidence for the R5 pre-downtrend short."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from bisect import bisect_right
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence


SCHEMA_VERSION = "a1_xau_r5_pre_downtrend_opportunity_v1"
WINDOW_START = datetime(2022, 7, 1)
WINDOW_END = datetime(2026, 6, 30, 23, 59, 59)
TIME_FORMAT = "%Y.%m.%d %H:%M:%S"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tsv(path: Path) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def timestamp(value: str) -> datetime:
    return datetime.strptime(value, TIME_FORMAT)


def h4_intervals(path: Path) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, list[datetime]]] = {}
    for row in read_tsv(path):
        position = row["position_id"]
        side = grouped.setdefault(position, {"entry": [], "exit": []})
        if row["entry_code"] == "0":
            side["entry"].append(timestamp(row["timestamp_broker"]))
        elif row["entry_code"] in {"1", "2", "3"}:
            side["exit"].append(timestamp(row["timestamp_broker"]))
    result = []
    for position, sides in grouped.items():
        if len(sides["entry"]) != 1 or not sides["exit"]:
            raise RuntimeError(f"incomplete H4 position interval: {position}")
        result.append({
            "position_id": position,
            "start": sides["entry"][0],
            "end": max(sides["exit"]),
        })
    return sorted(result, key=lambda row: (row["start"], row["end"], int(row["position_id"])))


def merge_intervals(rows: Sequence[dict[str, Any]]) -> list[tuple[datetime, datetime]]:
    merged: list[tuple[datetime, datetime]] = []
    for row in rows:
        start, end = row["start"], row["end"]
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        elif end > merged[-1][1]:
            merged[-1] = (merged[-1][0], end)
    return merged


def containing_episode(
    value: datetime, episodes: Sequence[tuple[datetime, datetime]], starts: Sequence[datetime],
) -> int | None:
    index = bisect_right(starts, value) - 1
    if index >= 0 and value <= episodes[index][1]:
        return index
    return None


def source_record(path: Path) -> dict[str, Any]:
    return {
        "path": path.resolve().as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def analyze(h4_deals: Path, oracle: Path, q55_orders: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    positions = h4_intervals(h4_deals)
    common_positions = [
        row for row in positions
        if row["end"] >= WINDOW_START and row["start"] <= WINDOW_END
    ]
    episodes = merge_intervals(common_positions)
    episode_starts = [row[0] for row in episodes]
    full_episodes = merge_intervals(positions)

    oracle_counts: Counter[str] = Counter()
    oracle_rows = 0
    oracle_exposed = 0
    for row in read_tsv(oracle):
        oracle_rows += 1
        when = timestamp(row["timestamp_broker"])
        if containing_episode(when, episodes, episode_starts) is None:
            continue
        oracle_exposed += 1
        oracle_counts[row["reason"].upper()] += 1

    raw_candidates: list[dict[str, Any]] = []
    for row in read_tsv(q55_orders):
        reason = row["reason"].lower()
        if reason.endswith("_state_uptrend"):
            state = "UPTREND"
        elif reason.endswith("_state_chop"):
            state = "CHOP"
        else:
            continue
        when = timestamp(row["timestamp_broker"])
        raw_candidates.append({
            "timestamp": when,
            "router_state": state,
            "spread_points": float(row["spread_points"]),
            "estimated_cost_r": float(row["estimated_cost_r"]),
            "stop_points": float(row["stop_points"]),
            "reason": row["reason"],
        })

    eligible = [
        row for row in raw_candidates
        if row["spread_points"] <= 75.0
        and row["estimated_cost_r"] <= 0.05
        and row["stop_points"] <= 1000.0
    ]
    eligible_overlap: list[dict[str, Any]] = []
    touched_positions: set[str] = set()
    touched_episodes: set[int] = set()
    for candidate in eligible:
        when = candidate["timestamp"]
        matching_positions = [
            row["position_id"] for row in common_positions
            if row["start"] <= when <= row["end"]
        ]
        episode = containing_episode(when, episodes, episode_starts)
        if not matching_positions or episode is None:
            continue
        touched_positions.update(matching_positions)
        touched_episodes.add(episode)
        eligible_overlap.append({
            **candidate,
            "h4_position_ids": ",".join(sorted(matching_positions, key=int)),
            "h4_episode": episode + 1,
        })

    raw_states = Counter(row["router_state"] for row in raw_candidates)
    eligible_states = Counter(row["router_state"] for row in eligible)
    overlap_states = Counter(row["router_state"] for row in eligible_overlap)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "boundary": {
            "development_data_not_holdout": True,
            "h4_outcomes_used_in_rule": False,
            "h4_exposure_used_only_for_posthoc_availability": True,
            "opportunities_are_not_predicted_executions": True,
        },
        "contract_filters": {
            "router_states": ["UPTREND", "CHOP"],
            "maximum_spread_points": 75.0,
            "maximum_estimated_cost_r": 0.05,
            "maximum_stop_points": 1000.0,
            "daily_and_position_caps_applied": False,
        },
        "sources": {
            "h4_deals": source_record(h4_deals),
            "router_oracle": source_record(oracle),
            "q55_orders": source_record(q55_orders),
        },
        "h4": {
            "ten_year_positions": len(positions),
            "ten_year_merged_exposure_episodes": len(full_episodes),
            "common_window_positions": len(common_positions),
            "common_window_merged_exposure_episodes": len(episodes),
            "common_window_start": WINDOW_START.isoformat(sep=" "),
            "common_window_end": WINDOW_END.isoformat(sep=" "),
        },
        "router_availability_while_h4_exposed": {
            "oracle_rows": oracle_rows,
            "exposed_rows": oracle_exposed,
            "state_counts": dict(sorted(oracle_counts.items())),
            "uptrend_plus_chop": oracle_counts["UPTREND"] + oracle_counts["CHOP"],
            "uptrend_plus_chop_pct": round(
                100.0 * (oracle_counts["UPTREND"] + oracle_counts["CHOP"]) / oracle_exposed, 4,
            ),
        },
        "q55_opportunities": {
            "raw_uptrend_chop_rows": len(raw_candidates),
            "raw_unique_broker_dates": len({row["timestamp"].date() for row in raw_candidates}),
            "raw_state_counts": dict(sorted(raw_states.items())),
            "risk_eligible_rows": len(eligible),
            "risk_eligible_unique_broker_dates": len({row["timestamp"].date() for row in eligible}),
            "risk_eligible_state_counts": dict(sorted(eligible_states.items())),
            "risk_eligible_during_h4_exposure": len(eligible_overlap),
            "overlap_unique_broker_dates": len({row["timestamp"].date() for row in eligible_overlap}),
            "overlap_state_counts": dict(sorted(overlap_states.items())),
            "h4_positions_touched": len(touched_positions),
            "h4_episodes_touched": len(touched_episodes),
        },
    }
    return payload, eligible_overlap


def render(payload: dict[str, Any]) -> str:
    h4 = payload["h4"]
    router = payload["router_availability_while_h4_exposed"]
    q55 = payload["q55_opportunities"]
    states = router["state_counts"]
    return "\n".join([
        "# A1 XAU R5 Pre-Downtrend Opportunity Evidence", "",
        "Status: `RESEARCH_AVAILABILITY_ONLY_NOT_STRATEGY_VALIDATION`", "",
        "The proposed live rule does not read H4 positions, H4 P/L, drawdown, or outcomes. "
        "H4 intervals are used only after signal construction to test contemporaneous availability.", "",
        "## Causal router availability", "",
        f"The common evidence window contains {h4['common_window_positions']} H4 positions in "
        f"{h4['common_window_merged_exposure_episodes']} merged exposure episodes.  Across "
        f"{router['exposed_rows']} causal M5 snapshots while H4 was exposed:", "",
        "| State | M5 snapshots |", "| --- | ---: |",
        *[f"| `{state}` | {count} |" for state, count in sorted(states.items())],
        f"| `UPTREND + CHOP` | {router['uptrend_plus_chop']} ({router['uptrend_plus_chop_pct']:.2f}%) |", "",
        "## Frozen q55 opportunity incidence", "",
        "| Measure | Count |", "| --- | ---: |",
        f"| Raw UPTREND/CHOP blocked-signal rows | {q55['raw_uptrend_chop_rows']} |",
        f"| Raw broker dates | {q55['raw_unique_broker_dates']} |",
        f"| Rows after spread <=75, cost <=0.05R, stop <=1000 | {q55['risk_eligible_rows']} |",
        f"| Eligible broker dates | {q55['risk_eligible_unique_broker_dates']} |",
        f"| Eligible rows during H4 exposure | {q55['risk_eligible_during_h4_exposure']} |",
        f"| H4 positions touched | {q55['h4_positions_touched']} / {h4['common_window_positions']} |",
        f"| H4 episodes touched | {q55['h4_episodes_touched']} / {h4['common_window_merged_exposure_episodes']} |", "",
        "These are pre-daily-cap and pre-own-position-cap opportunities, not predicted executions. "
        "The common window ends in June 2026; full-decade execution and overlap remain unknown until "
        "the preregistered exact MT5 run.", "",
    ])


def write_outputs(payload: dict[str, Any], overlap: Sequence[dict[str, Any]], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = "A1_XAU_R5_PRE_DOWNTREND_BREAK_RESEARCH_20260711"
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    csv_path = output_dir / f"{stem}_ELIGIBLE_H4_OVERLAP.csv"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render(payload), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "timestamp_broker", "router_state", "spread_points", "estimated_cost_r",
            "stop_points", "h4_position_ids", "h4_episode", "reason",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in overlap:
            writer.writerow({
                "timestamp_broker": row["timestamp"].strftime(TIME_FORMAT),
                "router_state": row["router_state"],
                "spread_points": row["spread_points"],
                "estimated_cost_r": row["estimated_cost_r"],
                "stop_points": row["stop_points"],
                "h4_position_ids": row["h4_position_ids"],
                "h4_episode": row["h4_episode"],
                "reason": row["reason"],
            })
    artifacts = {}
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            artifacts[path.relative_to(output_dir).as_posix()] = {
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
    (output_dir / "manifest.json").write_text(
        json.dumps({"schema_version": SCHEMA_VERSION, "artifacts": artifacts}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return json_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--h4-deals", type=Path, required=True)
    parser.add_argument("--router-oracle", type=Path, required=True)
    parser.add_argument("--q55-orders", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for path in (args.h4_deals, args.router_oracle, args.q55_orders):
        if not path.is_file():
            raise FileNotFoundError(path)
    payload, overlap = analyze(args.h4_deals, args.router_oracle, args.q55_orders)
    print(write_outputs(payload, overlap, args.output_dir.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
