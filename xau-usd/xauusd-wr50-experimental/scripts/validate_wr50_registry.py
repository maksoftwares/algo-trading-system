from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


WR50_MIN_MAGIC = 930000
WR50_MAX_MAGIC = 930999
VALID_EXPERIMENT_STATUSES = {
    "DEMO_EXPERIMENT_ONLY",
    "DISABLED",
    "REJECTED_EXPERIMENTAL",
    "CANDIDATE_FOR_PHASE0R_REVALIDATION",
}


@dataclass
class RegistryValidation:
    rows: list[dict[str, str]]
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def _split_markdown_row(row: str) -> list[str]:
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in row:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "|":
            cells.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    cells.append("".join(current).strip())
    return cells


def parse_registry_markdown(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = _split_markdown_row(stripped)
        if not cells:
            continue
        if all(set(cell.replace(":", "").strip()) <= {"-"} for cell in cells):
            continue
        if header is None and "ea_id" in cells:
            header = [cell.strip() for cell in cells]
            continue
        if header is not None and len(cells) == len(header):
            row = {key: value.strip().strip("`") for key, value in zip(header, cells)}
            if row.get("ea_id") and row["ea_id"] != "---":
                rows.append(row)
    return rows


def _int_field(row: dict[str, str], field: str, errors: list[str]) -> int | None:
    try:
        return int(str(row.get(field, "")).strip())
    except ValueError:
        errors.append(f"{row.get('ea_id', '<unknown>')}: {field} is not an integer")
        return None


def _float_field(row: dict[str, str], field: str, errors: list[str]) -> float | None:
    try:
        return float(str(row.get(field, "")).strip())
    except ValueError:
        errors.append(f"{row.get('ea_id', '<unknown>')}: {field} is not numeric")
        return None


def _is_true(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "1"}


def validate_rows(rows: Iterable[dict[str, str]]) -> RegistryValidation:
    parsed_rows = list(rows)
    errors: list[str] = []
    warnings: list[str] = []
    ids: set[str] = set()
    names: set[str] = set()
    short_codes: set[str] = set()
    active_magics: set[int] = set()

    if not parsed_rows:
        errors.append("registry contains no EA rows")

    required_fields = {
        "ea_id",
        "ea_name",
        "version",
        "magic_start",
        "magic_end",
        "active_magic",
        "strategy_family",
        "experiment_status",
        "allowed_account",
        "symbol",
        "entry_timeframe",
        "risk_profile",
        "comment_prefix",
        "owner_authorized",
        "live_authorized",
        "canonical_phase2_authorized",
        "max_fixed_lot",
    }

    for row in parsed_rows:
        ea_id = row.get("ea_id", "").strip()
        missing = sorted(field for field in required_fields if field not in row or row[field] == "")
        if missing:
            errors.append(f"{ea_id or '<unknown>'}: missing fields {', '.join(missing)}")
            continue

        if ea_id in ids:
            errors.append(f"{ea_id}: duplicate ea_id")
        ids.add(ea_id)

        ea_name = row["ea_name"].strip()
        if ea_name in names:
            errors.append(f"{ea_id}: duplicate ea_name {ea_name}")
        names.add(ea_name)

        comment_prefix = row["comment_prefix"].strip()
        if not comment_prefix.startswith("WR50|"):
            errors.append(f"{ea_id}: comment_prefix must start with WR50|")
        short_code = comment_prefix.split("|", 2)[1] if "|" in comment_prefix else ""
        if not short_code:
            errors.append(f"{ea_id}: missing short code in comment_prefix")
        elif short_code in short_codes:
            errors.append(f"{ea_id}: duplicate short code {short_code}")
        short_codes.add(short_code)

        magic_start = _int_field(row, "magic_start", errors)
        magic_end = _int_field(row, "magic_end", errors)
        active_magic = _int_field(row, "active_magic", errors)
        max_fixed_lot = _float_field(row, "max_fixed_lot", errors)
        if magic_start is None or magic_end is None or active_magic is None:
            continue

        if not (WR50_MIN_MAGIC <= magic_start <= WR50_MAX_MAGIC):
            errors.append(f"{ea_id}: magic_start {magic_start} outside WR50 namespace")
        if not (WR50_MIN_MAGIC <= magic_end <= WR50_MAX_MAGIC):
            errors.append(f"{ea_id}: magic_end {magic_end} outside WR50 namespace")
        if magic_start > magic_end:
            errors.append(f"{ea_id}: magic_start greater than magic_end")
        if not (magic_start <= active_magic <= magic_end):
            errors.append(f"{ea_id}: active_magic {active_magic} outside assigned range")
        if active_magic in active_magics:
            errors.append(f"{ea_id}: duplicate active_magic {active_magic}")
        active_magics.add(active_magic)

        status = row["experiment_status"].strip()
        if status not in VALID_EXPERIMENT_STATUSES:
            errors.append(f"{ea_id}: unsupported experiment_status {status}")
        if _is_true(row["live_authorized"]):
            errors.append(f"{ea_id}: live_authorized must remain false")
        if _is_true(row["canonical_phase2_authorized"]):
            errors.append(f"{ea_id}: canonical_phase2_authorized must remain false")
        if "owner_authorized" not in row:
            errors.append(f"{ea_id}: owner_authorized field is required")
        if max_fixed_lot is not None and max_fixed_lot <= 0:
            warnings.append(f"{ea_id}: max_fixed_lot is {max_fixed_lot}; runtime minimum-lot mode must still be capped by owner authorization")

    return RegistryValidation(parsed_rows, errors, warnings)


def validate_registry_file(path: Path) -> RegistryValidation:
    return validate_rows(parse_registry_markdown(path))


def build_short_comment(short_code: str, run_id: str) -> str:
    return f"WR50|{short_code}|{run_id}"


def validate_short_comment(comment: str, short_code: str, run_id: str) -> list[str]:
    errors: list[str] = []
    if len(comment) > 31:
        errors.append("comment length exceeds 31 chars")
    if not comment.startswith("WR50|"):
        errors.append("comment must start with WR50|")
    if short_code not in comment.split("|"):
        errors.append("comment missing short EA code")
    if run_id not in comment.split("|"):
        errors.append("comment missing run id")
    return errors


def write_report(result: RegistryValidation, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    status = "PASS" if result.ok else "FAIL"
    lines = [
        "# WR50 Registry Validation",
        "",
        f"Overall status: {status}",
        "",
        f"Rows checked: {len(result.rows)}",
        "",
        "## Errors",
        "",
    ]
    lines.extend([f"- {error}" for error in result.errors] or ["- None"])
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- {warning}" for warning in result.warnings] or ["- None"])
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This validation does not authorize canonical Phase 2 or live trading.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def default_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    root = default_root()
    parser = argparse.ArgumentParser(description="Validate WR50 EA registry.")
    parser.add_argument("--registry", type=Path, default=root / "docs" / "WR50_EA_REGISTRY.md")
    parser.add_argument("--report", type=Path, default=root / "outputs" / "reports" / "WR50_REGISTRY_VALIDATION.md")
    args = parser.parse_args(argv)

    result = validate_registry_file(args.registry)
    write_report(result, args.report)
    print(f"WR50 registry validation: {'PASS' if result.ok else 'FAIL'}")
    print(f"Report: {args.report}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

