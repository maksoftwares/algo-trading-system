from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from simulate_phase3_from_would_signals import PHASE2_AUTHORITY_SENTENCE


BUNDLE_FILES = (
    "README.md",
    "docs/PHASE3_EXPERIMENTAL_SCOPE.md",
    "docs/PHASE3_EXECUTION_READINESS_DESIGN.md",
    "docs/PHASE3_PROMOTION_ROLLBACK_CRITERIA.md",
    "docs/PHASE3_OBSERVER_CONFLICT_PLAYBOOK.md",
    "docs/PHASE3_REAL_IMPLEMENTATION_PROMPT.md",
    "outputs/reports/PHASE3_EXPERIMENTAL_STATUS.md",
    "outputs/reports/PHASE3_EXPERIMENTAL_STATUS.json",
    "outputs/reports/PHASE3_EXPERIMENTAL_SIMULATION.md",
    "outputs/reports/PHASE3_EXPERIMENTAL_SIMULATION.json",
    "outputs/reports/PHASE3_EXPERIMENTAL_LEDGER.csv",
    "outputs/reports/PHASE3_SUSPEND_FAMILY_REVIEW.md",
    "outputs/reports/PHASE3_SUSPEND_FAMILY_REVIEW.json",
    "outputs/reports/PHASE3_SUSPEND_FAMILY_ROWS.csv",
    "outputs/reports/PHASE3_SUSPEND_FAMILY_DECISION.md",
    "outputs/reports/PHASE3_SUSPEND_FAMILY_DECISION.json",
    "outputs/reports/PHASE3_SUSPEND_FAMILY_DECISION.csv",
    "outputs/reports/PHASE3_COST_MODE_COMPARISON.md",
    "outputs/reports/PHASE3_COST_MODE_COMPARISON.json",
    "outputs/reports/PHASE3_COST_MODE_COMPARISON.csv",
    "outputs/reports/PHASE3_COST_GATE_REVIEW.md",
    "outputs/reports/PHASE3_COST_GATE_REVIEW.json",
    "outputs/reports/PHASE3_COST_GATE_REVIEW.csv",
    "outputs/reports/PHASE3_FAMILY_DEDUP_AUDIT.md",
    "outputs/reports/PHASE3_FAMILY_DEDUP_AUDIT.json",
    "outputs/reports/PHASE3_FAMILY_DEDUP_AUDIT.csv",
    "outputs/reports/PHASE3_PAPER_SHADOW_SUMMARY.md",
    "outputs/reports/PHASE3_PAPER_SHADOW_SUMMARY.json",
    "outputs/reports/PHASE3_PAPER_SHADOW_LEDGER.csv",
    "outputs/reports/PHASE3_SHADOW_LIFECYCLE_SUMMARY.md",
    "outputs/reports/PHASE3_SHADOW_LIFECYCLE_SUMMARY.json",
    "outputs/reports/PHASE3_SHADOW_LIFECYCLE_LEDGER.csv",
    "outputs/reports/PHASE3_LIFECYCLE_GUARD_SUMMARY.md",
    "outputs/reports/PHASE3_LIFECYCLE_GUARD_SUMMARY.json",
    "outputs/reports/PHASE3_LIFECYCLE_GUARD_LEDGER.csv",
    "outputs/reports/PHASE3_DEMO_REHEARSAL_CHECKLIST.md",
    "outputs/reports/PHASE3_DEMO_REHEARSAL_PLAN.json",
    "outputs/reports/PHASE3_DEMO_REHEARSAL_LEDGER.csv",
    "outputs/reports/PHASE3_COMPLETION_AUDIT.md",
    "outputs/reports/PHASE3_COMPLETION_AUDIT.json",
    "outputs/reports/PHASE3_EXPERIMENTAL_SAFETY_REPORT.md",
    "outputs/reports/PHASE3_EXPERIMENTAL_SAFETY_REPORT.json",
    "outputs/reports/PHASE3_EXPERIMENTAL_MANIFEST.md",
    "outputs/reports/PHASE3_EXPERIMENTAL_MANIFEST.json",
)


def generate_phase3_review_bundle(phase3_root: Path, output_dir: Path | None = None) -> Path:
    phase3_root = phase3_root.resolve()
    output_dir = (output_dir or phase3_root / "outputs" / "review_bundles").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    zip_path = output_dir / f"PHASE3_EXPERIMENTAL_REVIEW_BUNDLE_{timestamp}.zip"
    latest_zip_path = output_dir / "PHASE3_EXPERIMENTAL_REVIEW_BUNDLE_LATEST.zip"
    entries: list[dict[str, Any]] = []
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in BUNDLE_FILES:
            source = phase3_root / relative
            entry = {
                "path": relative,
                "exists": source.exists(),
                "bytes": source.stat().st_size if source.exists() else 0,
            }
            entries.append(entry)
            if source.exists():
                archive.write(source, arcname=relative)
        bundle_manifest = {
            "status": "PASS" if all(entry["exists"] for entry in entries) else "PENDING",
            "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "authority": PHASE2_AUTHORITY_SENTENCE,
            "bundle_path": str(zip_path),
            "latest_bundle_path": str(latest_zip_path),
            "files": entries,
        }
        archive.writestr("PHASE3_REVIEW_BUNDLE_MANIFEST.json", json.dumps(bundle_manifest, indent=2))
    shutil.copyfile(zip_path, latest_zip_path)
    manifest_path = output_dir / f"{zip_path.stem}_manifest.json"
    manifest_path.write_text(json.dumps(bundle_manifest, indent=2), encoding="utf-8")
    latest_bundle_manifest = dict(bundle_manifest)
    latest_bundle_manifest["bundle_path"] = str(latest_zip_path)
    latest_path = output_dir / "PHASE3_EXPERIMENTAL_REVIEW_BUNDLE_LATEST_manifest.json"
    latest_path.write_text(json.dumps(latest_bundle_manifest, indent=2), encoding="utf-8")
    return zip_path


def main(argv: list[str] | None = None) -> int:
    phase3_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Generate Phase 3 experimental review bundle.")
    parser.add_argument("--phase3-root", type=Path, default=phase3_root)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    path = generate_phase3_review_bundle(args.phase3_root, args.output_dir)
    print(f"Phase 3 review bundle: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
