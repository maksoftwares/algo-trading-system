from __future__ import annotations

import argparse
import csv
import shutil
from datetime import datetime, timezone
from pathlib import Path

from verify_phase1_logs import DECISION_REQUIRED_COLUMNS, DECISION_SCHEMA_VERSION, EXPECTED_DECISION_SCHEMA_HASH


def migrate_decision_log_schema(
    archived_decision_log: Path,
    current_decision_log: Path,
    output_path: Path | None = None,
) -> Path:
    archived_decision_log = archived_decision_log.resolve()
    current_decision_log = current_decision_log.resolve()
    output_path = (output_path or current_decision_log).resolve()
    if not archived_decision_log.exists():
        raise FileNotFoundError(archived_decision_log)
    if not current_decision_log.exists():
        raise FileNotFoundError(current_decision_log)

    current_rows, current_columns = _read_rows(current_decision_log)
    archived_rows, _ = _read_rows(archived_decision_log)
    if not current_columns:
        raise ValueError(f"Current decision log has no header: {current_decision_log}")

    migrated_rows = [_migrate_row(row, current_columns) for row in archived_rows]
    combined_rows = [*migrated_rows, *current_rows]
    backup_path = _backup_path(current_decision_log)
    shutil.copy2(current_decision_log, backup_path)
    _write_rows(output_path, current_columns, combined_rows)
    return backup_path


def _migrate_row(row: dict[str, str], columns: tuple[str, ...]) -> dict[str, str]:
    migrated = {column: row.get(column, "") for column in columns}
    migrated["decision_schema_version"] = DECISION_SCHEMA_VERSION
    migrated["decision_schema_hash"] = EXPECTED_DECISION_SCHEMA_HASH
    legacy_lifecycle = row.get("expert_lifecycle_state") or "DRY_RUN_ONLY"
    migrated["br_lifecycle_state"] = row.get("br_lifecycle_state") or legacy_lifecycle
    migrated["sbr_lifecycle_state"] = row.get("sbr_lifecycle_state") or legacy_lifecycle
    migrated["router_version"] = row.get("router_version", migrated.get("router_version", ""))
    for required in DECISION_REQUIRED_COLUMNS:
        migrated.setdefault(required, "")
    return migrated


def _read_rows(path: Path) -> tuple[list[dict[str, str]], tuple[str, ...]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), tuple(reader.fieldnames or ())


def _write_rows(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _backup_path(path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return path.with_name(f"{path.stem}_pre_migration_{stamp}{path.suffix}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate archived Phase 1 decision-log rows into the v2 schema.")
    parser.add_argument("--archived-decision-log", type=Path, required=True)
    parser.add_argument("--current-decision-log", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    backup = migrate_decision_log_schema(args.archived_decision_log, args.current_decision_log, args.output)
    print(f"Backed up current decision log to: {backup}")
    print(f"Migrated decision log written to: {args.output or args.current_decision_log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
