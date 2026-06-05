from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from validate_wr50_registry import parse_registry_markdown


@dataclass
class LogValidation:
    rows_checked: int
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def _read_csv_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                row["_source_file"] = str(path)
                rows.append(row)
    return rows


def _as_float(value: str) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except ValueError:
        return None


def _build_registry(registry_path: Path) -> dict[int, dict[str, str]]:
    rows = parse_registry_markdown(registry_path)
    registry: dict[int, dict[str, str]] = {}
    for row in rows:
        registry[int(row["active_magic"])] = row
    return registry


def validate_ledger_rows(rows: list[dict[str, str]], registry: dict[int, dict[str, str]]) -> LogValidation:
    errors: list[str] = []
    warnings: list[str] = []
    seen_order_tickets: dict[str, str] = {}

    for idx, row in enumerate(rows, start=1):
        source = row.get("_source_file", "<memory>")
        row_id = f"{source}:row{idx}"
        magic_text = row.get("magic", "").strip()
        comment = row.get("comment", "").strip()
        if not magic_text:
            errors.append(f"{row_id}: missing magic")
            continue
        try:
            magic = int(magic_text)
        except ValueError:
            errors.append(f"{row_id}: magic is not an integer")
            continue
        registry_row = registry.get(magic)
        if registry_row is None:
            errors.append(f"{row_id}: unknown WR50 magic {magic}")
            continue

        if not comment:
            errors.append(f"{row_id}: missing comment")
        elif not comment.startswith(registry_row["comment_prefix"]):
            errors.append(f"{row_id}: comment {comment!r} does not match {registry_row['comment_prefix']!r}")

        for field in ("experiment_id", "run_id"):
            if not row.get(field, "").strip():
                errors.append(f"{row_id}: missing {field}")

        sl_price = _as_float(row.get("sl_price", ""))
        tp_price = _as_float(row.get("tp_price", ""))
        if sl_price is None or sl_price <= 0:
            errors.append(f"{row_id}: hard SL not recorded")
        if tp_price is None or tp_price <= 0:
            errors.append(f"{row_id}: hard TP not recorded")

        lot = _as_float(row.get("lot", ""))
        max_lot = _as_float(registry_row.get("max_fixed_lot", ""))
        if lot is None:
            errors.append(f"{row_id}: lot missing or invalid")
        elif max_lot is not None and lot > max_lot + 1e-9:
            errors.append(f"{row_id}: lot {lot} exceeds registry max_fixed_lot {max_lot}")

        server = row.get("server", "").strip().lower()
        if server:
            if "live" in server or "real" in server or "contest" in server:
                errors.append(f"{row_id}: non-demo server marker found in {server!r}")
            elif "demo" not in server and "practice" not in server:
                errors.append(f"{row_id}: server does not contain a demo marker: {server!r}")

        order_ticket = row.get("order_ticket", "").strip()
        if order_ticket:
            prior_ea = seen_order_tickets.get(order_ticket)
            current_ea = registry_row["ea_id"]
            if prior_ea is not None and prior_ea != current_ea:
                errors.append(f"{row_id}: order_ticket {order_ticket} reused across {prior_ea} and {current_ea}")
            seen_order_tickets[order_ticket] = current_ea

    if not rows:
        warnings.append("no WR50 ledger rows found")
    return LogValidation(len(rows), errors, warnings)


def validate_logs(registry_path: Path, ledger_paths: list[Path]) -> LogValidation:
    registry = _build_registry(registry_path)
    rows = _read_csv_rows(ledger_paths)
    return validate_ledger_rows(rows, registry)


def write_report(result: LogValidation, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    status = "PASS" if result.ok else "FAIL"
    lines = [
        "# WR50 Log Validation",
        "",
        f"Overall status: {status}",
        "",
        f"Rows checked: {result.rows_checked}",
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
            "Valid WR50 logs remain demo-only research evidence and do not authorize canonical Phase 2 or live trading.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def default_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    root = default_root()
    parser = argparse.ArgumentParser(description="Validate WR50 trade logs.")
    parser.add_argument("--registry", type=Path, default=root / "docs" / "WR50_EA_REGISTRY.md")
    parser.add_argument("--ledger", type=Path, action="append")
    parser.add_argument("--report", type=Path, default=root / "outputs" / "reports" / "WR50_LOG_VALIDATION.md")
    args = parser.parse_args(argv)

    ledgers = args.ledger or [
        *(root / "outputs" / "ledgers").glob("*.csv"),
        root / "outputs" / "logs" / "wr50_trade_ledger.csv",
    ]
    result = validate_logs(args.registry, list(ledgers))
    write_report(result, args.report)
    print(f"WR50 log validation: {'PASS' if result.ok else 'FAIL'}")
    print(f"Report: {args.report}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

