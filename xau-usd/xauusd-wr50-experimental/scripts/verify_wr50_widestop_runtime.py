from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TERMINAL_DATA_DIR = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
)
DEFAULT_ATTACH_JSON = Path("outputs") / "reports" / "WR50_WIDESTOP_DEMO_ATTACHMENTS_2026_06_09.json"
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "WR50_WIDESTOP_RUNTIME_VERIFICATION_2026_06_09.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "WR50_WIDESTOP_RUNTIME_VERIFICATION_2026_06_09.md"


@dataclass(frozen=True)
class ExpectedRuntime:
    ea_id: str
    short_code: str
    magic: str
    target_r: str


EXPECTED = (
    ExpectedRuntime("wr50_wst12", "WST12", "930300", "1.20"),
    ExpectedRuntime("wr50_wst15", "WST15", "930400", "1.50"),
)


def verify_runtime(
    wr50_root: Path,
    terminal_data_dir: Path = DEFAULT_TERMINAL_DATA_DIR,
    attach_json: Path | None = None,
    output_json: Path | None = None,
) -> dict[str, Any]:
    wr50_root = wr50_root.resolve()
    terminal_data_dir = terminal_data_dir.resolve()
    attach_json = (attach_json or wr50_root / DEFAULT_ATTACH_JSON).resolve()
    output_json = (output_json or wr50_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else wr50_root / DEFAULT_OUTPUT_MD

    attachment_payload = _read_json(attach_json)
    checks: list[dict[str, Any]] = []
    startup_rows = _read_csv(terminal_data_dir / "MQL5" / "Files" / "WR50" / "wr50_startup_log.csv")

    checks.append(_check_file("compiled_ex5", terminal_data_dir / "MQL5" / "Experts" / "WR50" / "WR50_BreakoutWideStop_v0.ex5"))
    checks.append(_check_file("source_mq5", terminal_data_dir / "MQL5" / "Experts" / "WR50" / "WR50_BreakoutWideStop_v0.mq5"))
    checks.append(_check_file("runtime_registry", terminal_data_dir / "MQL5" / "Files" / "WR50" / "wr50_runtime_registry.csv"))
    checks.append(_check_file("account_allowlist", terminal_data_dir / "MQL5" / "Files" / "WR50" / "wr50_account_allowlist.csv"))

    expected_by_magic = {item.magic: item for item in EXPECTED}
    attachment_rows: list[dict[str, Any]] = attachment_payload.get("attachments", [])
    for item in attachment_rows:
        magic = str(item.get("magic", ""))
        expected = expected_by_magic.get(magic)
        if expected is None:
            continue
        chart_path = Path(str(item.get("chart_file", "")))
        checks.extend(_check_chart(chart_path, expected))
        checks.append(_check_latest_init_ok(startup_rows, expected))

    attached_magics = {str(item.get("magic", "")) for item in attachment_rows}
    for expected in EXPECTED:
        checks.append(
            {
                "name": f"attachment_record_{expected.magic}",
                "status": "PASS" if expected.magic in attached_magics else "FAIL",
                "detail": "attachment report contains expected magic",
            }
        )

    status = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    payload: dict[str, Any] = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": "WR50 WideStop demo runtime verification only; not canonical Phase 2 evidence.",
        "terminal_data_dir": str(terminal_data_dir),
        "attachment_report": str(attach_json),
        "checks": checks,
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return payload


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing JSON report: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _check_file(name: str, path: Path) -> dict[str, Any]:
    return {
        "name": name,
        "status": "PASS" if path.exists() and path.stat().st_size > 0 else "FAIL",
        "detail": str(path),
    }


def _check_chart(path: Path, expected: ExpectedRuntime) -> list[dict[str, Any]]:
    if not path.exists():
        return [{"name": f"chart_exists_{expected.magic}", "status": "FAIL", "detail": str(path)}]
    text = path.read_text(encoding="utf-8", errors="replace")
    required = {
        f"chart_path_{expected.magic}": "path=Experts\\WR50\\WR50_BreakoutWideStop_v0.ex5",
        f"chart_magic_{expected.magic}": f"InpMagicNumber={expected.magic}",
        f"chart_short_code_{expected.magic}": f"InpEaShortCode={expected.short_code}",
        f"chart_target_r_{expected.magic}": f"InpTargetR={expected.target_r}",
        f"chart_demo_enabled_{expected.magic}": "InpAllowDemoTrading=true",
    }
    checks = [{"name": f"chart_exists_{expected.magic}", "status": "PASS", "detail": str(path)}]
    for name, needle in required.items():
        checks.append({"name": name, "status": "PASS" if needle in text else "FAIL", "detail": needle})
    return checks


def _check_latest_init_ok(rows: list[dict[str, str]], expected: ExpectedRuntime) -> dict[str, Any]:
    matches = [
        row
        for row in rows
        if row.get("ea_id") == expected.ea_id
        and row.get("ea_short_code") == expected.short_code
        and row.get("magic") == expected.magic
    ]
    if not matches:
        return {"name": f"latest_init_ok_{expected.magic}", "status": "FAIL", "detail": "no startup rows found"}
    latest = matches[-1]
    status_reason = latest.get("status_reason", "")
    return {
        "name": f"latest_init_ok_{expected.magic}",
        "status": "PASS" if status_reason.startswith("INIT_OK") else "FAIL",
        "detail": f"{latest.get('timestamp_broker','')} {status_reason}",
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# WR50 WideStop Runtime Verification",
        "",
        f"Status: {payload['status']}",
        "",
        payload["scope"],
        "",
        f"Terminal data dir: `{payload['terminal_data_dir']}`",
        f"Attachment report: `{payload['attachment_report']}`",
        "",
        "| Check | Status | Detail |",
        "|---|---:|---|",
    ]
    for check in payload["checks"]:
        lines.append(f"| {check['name']} | {check['status']} | `{check['detail']}` |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify WR50 WideStop demo runtime attachment evidence.")
    parser.add_argument("--wr50-root", type=Path, default=Path("."))
    parser.add_argument("--terminal-data-dir", type=Path, default=DEFAULT_TERMINAL_DATA_DIR)
    parser.add_argument("--attach-json", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args()

    payload = verify_runtime(
        wr50_root=args.wr50_root,
        terminal_data_dir=args.terminal_data_dir,
        attach_json=args.attach_json,
        output_json=args.output_json,
    )
    print(f"WR50 WideStop runtime verification: {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
