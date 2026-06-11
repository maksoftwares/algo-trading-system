from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase0.hashing import sha256_file


REPORT_RELATIVE_PATH = Path("outputs/reports/LANE_A_RULE_RECONSTRUCTION_NOTES.md")
JSON_RELATIVE_PATH = Path("outputs/reports/LANE_A_RULE_RECONSTRUCTION_NOTES.json")
LANE_A_RECONSTRUCTION_ROWS = (
    (
        "d1_momentum_h4_pullback_v1_fullhist",
        "d1_momentum_h4_pullback_v0",
        "docs/hypothesis_d1_momentum_h4_pullback_v0.md",
        "src/phase0/strategies/d1_momentum_h4_pullback_v0.py",
    ),
    (
        "w1_d1_momentum_continuation_v1_fullhist",
        "w1_d1_momentum_continuation_v0",
        "docs/hypothesis_w1_d1_momentum_continuation_v0.md",
        "src/phase0/strategies/w1_d1_momentum_continuation_v0.py",
    ),
    (
        "h4_inside_bar_d1_momentum_breakout_v1_fullhist",
        "h4_inside_bar_d1_momentum_breakout_v0",
        "docs/hypothesis_h4_inside_bar_d1_momentum_breakout_v0.md",
        "src/phase0/strategies/h4_inside_bar_d1_momentum_breakout_v0.py",
    ),
)


@dataclass(frozen=True)
class LaneAReconstructionRow:
    candidate_id: str
    source_candidate_id: str
    source_hypothesis_path: str
    source_hypothesis_sha256: str
    source_strategy_path: str
    source_strategy_sha256: str
    source_status: str
    v1_hypothesis_path: str
    v1_strategy_path: str
    reconstruction_status: str
    notes: str


@dataclass(frozen=True)
class LaneAReconstructionNotes:
    status: str
    generated_at_utc: str
    report_path: Path
    json_path: Path
    rows: tuple[LaneAReconstructionRow, ...]


def generate_lane_a_reconstruction_notes(root: Path) -> LaneAReconstructionNotes:
    rows = tuple(_row(root, *details) for details in LANE_A_RECONSTRUCTION_ROWS)
    source_ok = all(row.source_status == "PASS" for row in rows)
    reconstructed = all(row.reconstruction_status == "COMPLETE_BYTE_IDENTICAL_ALIAS" for row in rows)
    if not source_ok:
        status = "FAIL_MISSING_SOURCE_BASELINE"
    elif reconstructed:
        status = "PASS_RECONSTRUCTED_FOR_PARTIAL_PASS"
    else:
        status = "BLOCKED_M1_PRE_RECONSTRUCTION"
    notes = LaneAReconstructionNotes(
        status=status,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        report_path=root / REPORT_RELATIVE_PATH,
        json_path=root / JSON_RELATIVE_PATH,
        rows=rows,
    )
    notes.report_path.parent.mkdir(parents=True, exist_ok=True)
    notes.report_path.write_text(render_lane_a_reconstruction_notes(notes), encoding="utf-8")
    notes.json_path.write_text(
        json.dumps(
            {
                "status": notes.status,
                "generated_at_utc": notes.generated_at_utc,
                "rows": [asdict(row) for row in notes.rows],
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return notes


def render_lane_a_reconstruction_notes(notes: LaneAReconstructionNotes) -> str:
    rows = [
        {
            "Candidate": row.candidate_id,
            "Source v0": row.source_candidate_id,
            "Source status": row.source_status,
            "Hypothesis SHA256": row.source_hypothesis_sha256,
            "Strategy SHA256": row.source_strategy_sha256,
            "Reconstruction status": row.reconstruction_status,
            "Notes": row.notes,
        }
        for row in notes.rows
    ]
    return "\n".join(
        [
            "# Lane A Rule Reconstruction Notes",
            "",
            f"Status: {notes.status}",
            f"Generated at UTC: {notes.generated_at_utc}",
            "",
            "## Boundary",
            "",
            "This report captures v0 rule baselines and Lane A v1 full-history reconstruction status. It does not authorize MT5 runtime, broker, demo, live, or observer activity.",
            "",
            "## Rule Baselines",
            "",
            _markdown_table(
                rows,
                [
                    "Candidate",
                    "Source v0",
                    "Source status",
                    "Hypothesis SHA256",
                    "Strategy SHA256",
                    "Reconstruction status",
                    "Notes",
                ],
            ),
            "",
            "Lane A v1 full-history candidates preserve the referenced v0 mechanics byte-identically where possible by subclass alias. If any future version requires a rule difference, document it here before a result-producing run.",
            "",
        ]
    )


def _row(
    root: Path,
    candidate_id: str,
    source_candidate_id: str,
    source_hypothesis_relative: str,
    source_strategy_relative: str,
) -> LaneAReconstructionRow:
    source_hypothesis = root / source_hypothesis_relative
    source_strategy = root / source_strategy_relative
    missing = [
        str(path)
        for path in (source_hypothesis, source_strategy)
        if not path.exists()
    ]
    source_status = "PASS" if not missing else "FAIL"
    v1_hypothesis = root / "docs" / f"hypothesis_{candidate_id}.md"
    v1_strategy = root / "src" / "phase0" / "strategies" / f"{candidate_id}.py"
    v1_hypothesis_exists = v1_hypothesis.exists()
    v1_strategy_exists = v1_strategy.exists()
    if v1_hypothesis_exists and v1_strategy_exists:
        reconstruction_status = "COMPLETE_BYTE_IDENTICAL_ALIAS"
        notes = "v1 hypothesis and strategy alias exist; source v0 mechanics are preserved by subclass alias."
    elif not v1_hypothesis_exists:
        reconstruction_status = "NOT_STARTED_BLOCKED_BY_M1"
        notes = "Source baseline captured; v1 reconstruction deferred until M1 preflight is unblocked."
    else:
        reconstruction_status = "REVIEW_REQUIRED"
        notes = "v1 hypothesis exists, but strategy alias is missing or requires review."

    return LaneAReconstructionRow(
        candidate_id=candidate_id,
        source_candidate_id=source_candidate_id,
        source_hypothesis_path=source_hypothesis_relative,
        source_hypothesis_sha256=sha256_file(source_hypothesis) if source_hypothesis.exists() else "",
        source_strategy_path=source_strategy_relative,
        source_strategy_sha256=sha256_file(source_strategy) if source_strategy.exists() else "",
        source_status=source_status,
        v1_hypothesis_path=str(v1_hypothesis.relative_to(root).as_posix()),
        v1_strategy_path=str(v1_strategy.relative_to(root).as_posix()),
        reconstruction_status=reconstruction_status,
        notes=notes if not missing else f"Missing source baseline file(s): {', '.join(missing)}",
    )


def _markdown_table(rows: list[dict[str, Any]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)
