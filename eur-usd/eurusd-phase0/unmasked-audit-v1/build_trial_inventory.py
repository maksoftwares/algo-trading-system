from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=ROOT / "evidence" / "prior_trial_reports",
    )
    args = parser.parse_args()
    source = args.source_dir.resolve()
    reports = sorted(source.glob("*.json"))
    if not reports:
        raise RuntimeError(f"No prior trial JSON reports found under {source}")

    evidence_rows: list[dict[str, Any]] = []
    trial_rows: list[dict[str, Any]] = []
    for report in reports:
        payload = json.loads(report.read_text(encoding="utf-8"))
        results = payload.get("results", [])
        evidence_rows.append(
            {
                "report": report.name,
                "sha256": sha256(report),
                "bytes": report.stat().st_size,
                "schema_or_status": payload.get("schema_version", payload.get("status", "")),
                "result_rows": len(results),
            }
        )
        scope = payload.get("scope", {})
        for index, result in enumerate(results, start=1):
            overall = result.get("summary", {}).get("overall", {})
            mt5 = result.get("mt5_report_metrics", {})
            trial_rows.append(
                {
                    "source_report": report.name,
                    "source_report_sha256": sha256(report),
                    "row_index": index,
                    "generated_at_utc": payload.get("generated_at_utc", ""),
                    "tag": scope.get("tag", ""),
                    "from_date": scope.get("from_date", ""),
                    "to_date": scope.get("to_date", ""),
                    "tuning_attempted": scope.get("tuning_attempted", ""),
                    "symbol": result.get("symbol", ""),
                    "variant": result.get("variant", ""),
                    "description": result.get("description", ""),
                    "status": result.get("status", ""),
                    "trades": overall.get("trades", ""),
                    "win_rate_pct": overall.get("win_rate_pct", ""),
                    "parsed_net_usd": overall.get("pnl", ""),
                    "parsed_profit_factor": overall.get("profit_factor", ""),
                    "mt5_net_usd": mt5.get("Total Net Profit", ""),
                    "mt5_profit_factor": mt5.get("Profit Factor", ""),
                }
            )

    evidence_path = ROOT / "evidence" / "PRIOR_REPORT_INVENTORY.csv"
    trial_path = ROOT / "evidence" / "PRIOR_TRIAL_RESULT_INVENTORY.csv"
    for path, rows in ((evidence_path, evidence_rows), (trial_path, trial_rows)):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    print(f"{len(evidence_rows)} reports, {len(trial_rows)} trial-result rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
