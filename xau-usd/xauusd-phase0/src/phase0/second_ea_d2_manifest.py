from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from phase0.constants import SECOND_EA_LANE_A_CANDIDATES, SECOND_EA_LANE_B_CANDIDATES


D2_MANIFEST_RELATIVE_PATH = Path("outputs/reports/SECOND_EA_D2_UNIVERSE_MANIFEST.csv")
FAMILY_ASSIGNMENTS_RELATIVE_PATH = Path("outputs/reports/PHASE0_REALITY_CHECK_FAMILY_ASSIGNMENTS.csv")


@dataclass(frozen=True)
class D2ManifestRow:
    candidate_id: str
    lane: str
    matrix_ledger_path: str
    matrix_ledger_status: str
    d2_included: str
    reason: str
    family: str
    family_cluster_representative: str
    hypothesis_path: str
    hypothesis_lock_status: str


def write_second_ea_d2_universe_manifest(root: Path) -> list[D2ManifestRow]:
    rows = build_second_ea_d2_universe_rows(root)
    manifest = root / D2_MANIFEST_RELATIVE_PATH
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(D2ManifestRow.__dataclass_fields__))
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)
    return rows


def build_second_ea_d2_universe_rows(root: Path) -> list[D2ManifestRow]:
    family_assignments = _load_family_assignments(root / FAMILY_ASSIGNMENTS_RELATIVE_PATH)
    rows_by_candidate: dict[str, D2ManifestRow] = {}

    for path in sorted((root / "outputs" / "reports").glob("*_matrix_metrics.csv")):
        candidate = path.name.removesuffix("_matrix_metrics.csv")
        status = _ledger_status(path)
        rows_by_candidate[candidate] = _row_for_candidate(
            root=root,
            candidate=candidate,
            ledger_path=path,
            ledger_status=status,
            family_assignments=family_assignments,
        )

    for path in sorted((root / "outputs" / "matrix").glob("matrix_*.csv")):
        candidate = path.name.removeprefix("matrix_").removesuffix(".csv")
        if candidate in rows_by_candidate:
            continue
        status = _ledger_status(path)
        rows_by_candidate[candidate] = _row_for_candidate(
            root=root,
            candidate=candidate,
            ledger_path=path,
            ledger_status=status,
            family_assignments=family_assignments,
        )

    return sorted(rows_by_candidate.values(), key=lambda row: (row.d2_included != "true", row.candidate_id))


def _row_for_candidate(
    *,
    root: Path,
    candidate: str,
    ledger_path: Path,
    ledger_status: str,
    family_assignments: dict[str, dict[str, str]],
) -> D2ManifestRow:
    family = family_assignments.get(candidate, {}).get("family", "")
    representative = family_assignments.get(candidate, {}).get("representative", "")
    hypothesis_path = root / "docs" / f"hypothesis_{candidate}.md"
    lock_path = root / "docs" / f"hypothesis_{candidate}.sha256.json"
    lock_status = _hypothesis_lock_status(hypothesis_path, lock_path)
    included = ledger_status == "NON_EMPTY_RESULT_LEDGER"
    reason = "NON_EMPTY_RESULT_LEDGER_INCLUDED_FOR_D2_UNIVERSE" if included else f"{ledger_status}_NO_RESULT_LEDGER"
    return D2ManifestRow(
        candidate_id=candidate,
        lane=_lane(candidate),
        matrix_ledger_path=_relative_posix(root, ledger_path),
        matrix_ledger_status=ledger_status,
        d2_included=str(included).lower(),
        reason=reason,
        family=family or candidate,
        family_cluster_representative=representative or candidate,
        hypothesis_path=_relative_posix(root, hypothesis_path) if hypothesis_path.exists() else "",
        hypothesis_lock_status=lock_status,
    )


def _ledger_status(path: Path) -> str:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return "EMPTY"
    statuses = {str(row.get("status", "")).upper() for row in rows}
    if statuses == {"NOT_RUN"}:
        return "NOT_RUN"
    return "NON_EMPTY_RESULT_LEDGER"


def _hypothesis_lock_status(hypothesis_path: Path, lock_path: Path) -> str:
    if lock_path.exists():
        return "SHA_LOCK_FILE_PRESENT"
    if hypothesis_path.exists():
        return "LEGACY_HYPOTHESIS_DOC_PRESENT_NO_SHA_LOCK"
    return "NO_HYPOTHESIS_DOC"


def _load_family_assignments(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["expert"]: row for row in csv.DictReader(handle)}


def _lane(candidate: str) -> str:
    if candidate in SECOND_EA_LANE_A_CANDIDATES:
        return "A"
    if candidate in SECOND_EA_LANE_B_CANDIDATES:
        return "B"
    return "PRIOR_PHASE0_OR_0R"


def _relative_posix(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
