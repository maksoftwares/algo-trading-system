from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

from phase0.config import ProjectConfig, parse_utc_datetime


@dataclass(frozen=True)
class TrueHoldoutStatus:
    true_holdout_period_start: str
    true_holdout_period_end: str
    true_holdout_unlocked: bool
    true_holdout_unlock_file: str
    true_holdout_unlock_file_present: bool
    true_holdout_overlap_detected: bool
    normal_workflows_policy: str


def true_holdout_status(
    config: ProjectConfig,
    *,
    true_holdout_unlocked: bool = False,
    requested_start: datetime | None = None,
    requested_end: datetime | None = None,
) -> TrueHoldoutStatus:
    holdout = config.true_holdout["true_holdout"]
    holdout_start = parse_utc_datetime(holdout["start"], "true_holdout_period.yaml true_holdout.start")
    holdout_end = parse_utc_datetime(holdout["end"], "true_holdout_period.yaml true_holdout.end")
    unlock_file = config.root / str(holdout["unlock_requires_file"])

    if requested_start is not None and requested_end is not None:
        overlap = _overlaps(requested_start, requested_end, holdout_start, holdout_end)
    else:
        overlap = _configured_periods_overlap(config, holdout_start, holdout_end)

    return TrueHoldoutStatus(
        true_holdout_period_start=holdout_start.isoformat(),
        true_holdout_period_end=holdout_end.isoformat(),
        true_holdout_unlocked=bool(true_holdout_unlocked),
        true_holdout_unlock_file=str(unlock_file.relative_to(config.root).as_posix()),
        true_holdout_unlock_file_present=unlock_file.exists(),
        true_holdout_overlap_detected=overlap,
        normal_workflows_policy=(
            "blocked_or_trimmed_unless_unlock_file_and_cli_flag_are_present"
            if config.phase0.get("true_holdout", {}).get("enabled", False)
            else "disabled"
        ),
    )


def write_run_context_manifest(
    config: ProjectConfig,
    *,
    true_holdout_unlocked: bool = False,
    requested_start: datetime | None = None,
    requested_end: datetime | None = None,
) -> Path:
    output_dir = config.root / "outputs" / "manifests"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "PHASE0_RUN_CONTEXT.json"
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        **asdict(
            true_holdout_status(
                config,
                true_holdout_unlocked=true_holdout_unlocked,
                requested_start=requested_start,
                requested_end=requested_end,
            )
        ),
    }
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path


def _configured_periods_overlap(
    config: ProjectConfig,
    holdout_start: datetime,
    holdout_end: datetime,
) -> bool:
    periods = config.phase0.get("periods", {})
    period_pairs = (
        ("cell_1_3_start", "cell_1_3_end"),
        ("cell_4_6_start", "cell_4_6_end"),
        ("cell_7_9_start", "cell_7_9_end"),
        ("decile_start", "decile_end"),
        ("multisymbol_start", "multisymbol_end"),
    )
    for start_key, end_key in period_pairs:
        if start_key not in periods or end_key not in periods:
            continue
        start = parse_utc_datetime(periods[start_key], f"phase0.yaml periods.{start_key}")
        end = parse_utc_datetime(periods[end_key], f"phase0.yaml periods.{end_key}")
        if _overlaps(start, end, holdout_start, holdout_end):
            return True
    return False


def _overlaps(
    requested_start: datetime,
    requested_end: datetime,
    holdout_start: datetime,
    holdout_end: datetime,
) -> bool:
    return requested_start <= holdout_end and requested_end >= holdout_start
