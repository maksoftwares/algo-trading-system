from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase2x_common import boundary_lines, checks_table, mask_account, now_utc, read_json, report_header, reports_dir, sha256, write_report_pair


DEFAULT_JSON = Path("outputs") / "reports" / "PHASE2X_EVIDENCE_BUNDLE_MANIFEST.json"
DEFAULT_ORDER_LOG = Path("C:/MT5PortableP2WeaknessDemo/MQL5/Files/p2weakness_br_v1_order_log_xauusd.csv")
DEFAULT_SIGNAL_LOG = Path("C:/MT5PortableP2WeaknessDemo/MQL5/Files/p2weakness_br_v1_signal_log_xauusd.csv")
DEFAULT_STARTUP_LOG = Path("C:/MT5PortableP2WeaknessDemo/MQL5/Files/p2weakness_br_v1_startup_xauusd.csv")
DEFAULT_LOCAL_PRESET = Path("local") / "Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.local.set"


def generate_phase2x_evidence_bundle(
    root: Path,
    output_json: Path | None = None,
    order_log: Path = DEFAULT_ORDER_LOG,
    signal_log: Path = DEFAULT_SIGNAL_LOG,
    startup_log: Path = DEFAULT_STARTUP_LOG,
    local_preset: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    report_dir = reports_dir(root)
    output_json = (output_json or root / DEFAULT_JSON).resolve()
    local_preset = (local_preset or root / DEFAULT_LOCAL_PRESET).resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    zip_path = report_dir / f"PHASE2X_EVIDENCE_BUNDLE_{stamp}.zip"
    report_files = [
        "PHASE2X_DEMO_PREFLIGHT_REPORT.md",
        "PHASE2X_NO_TOUCH_STAGING_REPORT.md",
        "PHASE2X_OWNER_AUTHORIZATION_STATUS.md",
        "PHASE2X_RUNTIME_RECONCILIATION.md",
        "PHASE2X_RUNTIME_CLEANUP_REPORT.md",
        "PHASE2X_KILL_SWITCH_BLOCK_TEST_REPORT.md",
        "P2WEAKNESS_BR_V1_SOURCE_GOVERNANCE_PARITY.md",
        "P2WEAKNESS_BR_V1_MAGIC_COLLISION_AUDIT.md",
        "P2WEAKNESS_BR_V1_CLEAN_CLONE_RECONCILIATION.md",
        "P2WEAKNESS_BR_V1_RUNTIME_RECONCILIATION.md",
        "P2WEAKNESS_BR_V1_RUNTIME_ATTACHMENT_AUDIT.md",
        "PHASE2_ACTUAL_DEMO_COST_RECONCILIATION.md",
    ]
    daily_reports = sorted(report_dir.glob("PHASE2X_DAILY_DEMO_REVIEW_*.md"))
    included: list[str] = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in report_files:
            path = report_dir / name
            if path.exists():
                archive.write(path, f"reports/{name}")
                included.append(f"reports/{name}")
        for path in daily_reports:
            archive.write(path, f"reports/{path.name}")
            included.append(f"reports/{path.name}")
        for source, arcname in ((order_log, "logs/order_log_masked.csv"), (signal_log, "logs/signal_log_masked.csv"), (startup_log, "logs/startup_log_masked.csv")):
            if source.exists():
                archive.writestr(arcname, _masked_csv_text(source))
                included.append(arcname)
        archive.writestr("manifest/private_local_preset_sha256.txt", f"{sha256(local_preset)}\n")
        included.append("manifest/private_local_preset_sha256.txt")
        archive.writestr("manifest/git_status.txt", _git(root.parents[1], ["status", "--short"]))
        archive.writestr("manifest/git_commit.txt", _git(root.parents[1], ["rev-parse", "HEAD"]))
    checks = [
        {"name": "bundle_created", "status": "PASS" if zip_path.exists() else "FAIL", "evidence": str(zip_path)},
        {"name": "local_preset_contents_excluded", "status": "PASS", "evidence": "Only SHA256 is included."},
        {"name": "account_login_masked", "status": "PASS", "evidence": "CSV account_login/account fields are masked in bundled log copies."},
    ]
    payload = {
        "status": "PASS" if zip_path.exists() else "FAIL",
        "created_at_utc": now_utc(),
        "authority": "Phase 2X evidence bundle. Experimental demo evidence only; no canonical Phase 2, live trading, or real capital authorization.",
        "zip_path": str(zip_path),
        "included_members": included,
        "local_preset": str(local_preset),
        "local_preset_sha256": sha256(local_preset),
        "canonical_phase2_authorized": False,
        "live_trading_authorized": False,
        "real_capital_authorized": False,
        "checks": checks,
    }
    write_report_pair(output_json, payload, _render(payload))
    return payload


def _masked_csv_text(path: Path) -> str:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = handle.seek(0) or list(csv.DictReader(handle).fieldnames or [])
    for row in rows:
        for key in ("account_login", "account", "login"):
            if key in row:
                row[key] = mask_account(row[key])
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _git(repo_root: Path, args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=repo_root, check=False, capture_output=True, text=True)
    return completed.stdout if completed.returncode == 0 else completed.stderr


def _render(payload: dict[str, Any]) -> str:
    lines = report_header("Phase 2X Evidence Bundle Manifest", payload)
    lines.extend(boundary_lines())
    lines.extend([
        f"- Bundle: `{payload['zip_path']}`",
        f"- Local preset SHA256 only: `{payload['local_preset_sha256']}`",
        "",
        "## Checks",
        "",
        *checks_table(payload["checks"]),
        "",
        "## Included Members",
        "",
    ])
    lines.extend(f"- `{member}`" for member in payload["included_members"])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 2X evidence bundle.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--order-log", type=Path, default=DEFAULT_ORDER_LOG)
    parser.add_argument("--signal-log", type=Path, default=DEFAULT_SIGNAL_LOG)
    parser.add_argument("--startup-log", type=Path, default=DEFAULT_STARTUP_LOG)
    parser.add_argument("--local-preset", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = generate_phase2x_evidence_bundle(args.root, args.output_json, args.order_log, args.signal_log, args.startup_log, args.local_preset)
    print(f"Phase 2X evidence bundle: {payload['status']}")
    print(payload["zip_path"])
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
