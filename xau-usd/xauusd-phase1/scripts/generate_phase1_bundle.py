from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from analyze_phase1_soak import analyze_phase1_soak
from append_phase1_soak_history import append_phase1_soak_history
from generate_phase1_acceptance_report import generate_phase1_acceptance_report
from generate_phase1_observer_parity_report import generate_phase1_observer_parity_report
from generate_phase1_review_index import generate_phase1_review_index
from generate_phase1_runtime_health_report import generate_phase1_runtime_health_report
from generate_phase1_soak_history_report import generate_phase1_soak_history_report
from generate_phase1_status_summary import generate_phase1_status_summary
from generate_phase1_would_signal_report import generate_phase1_would_signal_report
from generate_phase2_paper_ledger_schema_report import generate_phase2_paper_ledger_schema_report
from generate_phase2_readiness_report import generate_phase2_readiness_report
from verify_phase1_logs import verify_phase1_logs


DEFAULT_RUNTIME_FILES = (
    "decision_log.csv",
    "startup_log.csv",
    "shutdown_log.csv",
)

REPO_PATTERNS = (
    "README.md",
    "docs/*.md",
    "mt5/README.md",
    "mt5/Config/*.ini",
    "mt5/Experts/*.mq5",
    "mt5/Include/Phase1/*.mqh",
    "mt5/Presets/*.set",
    "scripts/*.py",
    "tests/*.py",
    "outputs/reports/*.md",
    "outputs/reports/*.csv",
    "outputs/reports/*.json",
)


@dataclass(frozen=True)
class BundleOutput:
    bundle_path: Path
    manifest_path: Path
    included_count: int
    log_status: str
    soak_status: str
    would_signal_status: str
    acceptance_status: str
    runtime_health_status: str
    runtime_health_report_path: Path
    review_index_status: str
    review_index_path: Path
    phase2_readiness_status: str
    phase2_readiness_path: Path
    soak_history_path: Path
    soak_history_rows: int
    soak_history_report_status: str


def generate_phase1_bundle(
    root: Path,
    files_dir: Path,
    output_dir: Path | None = None,
    compile_log: Path | None = None,
    now: datetime | None = None,
) -> BundleOutput:
    root = root.resolve()
    files_dir = files_dir.resolve()
    if output_dir is None:
        output_dir = root / "outputs" / "review_bundles"
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = root / "outputs" / "reports" / "PHASE1_DRY_RUN_LOG_REPORT.md"
    verification = verify_phase1_logs(files_dir, report_path)
    soak_report_path = root / "outputs" / "reports" / "PHASE1_SOAK_DRIFT_REPORT.md"
    soak_analysis = analyze_phase1_soak(files_dir, soak_report_path, now=now)
    runtime_health_report_path = root / "outputs" / "reports" / "PHASE1_RUNTIME_HEALTH_REPORT.md"
    runtime_health = generate_phase1_runtime_health_report(files_dir, runtime_health_report_path, now=now)
    would_signal_report_path = root / "outputs" / "reports" / "PHASE1_WOULD_SIGNAL_REPORT.md"
    would_signal_report = generate_phase1_would_signal_report(files_dir, would_signal_report_path)
    acceptance_report_path = root / "outputs" / "reports" / "PHASE1_ACCEPTANCE_REPORT.md"
    acceptance = generate_phase1_acceptance_report(files_dir, acceptance_report_path, compile_log, root, now=now)
    status_summary_path = generate_phase1_status_summary(
        files_dir,
        root / "outputs" / "reports" / "PHASE1_STATUS_SUMMARY.json",
        compile_log,
        root,
        now=now,
    )
    soak_history = append_phase1_soak_history(
        summary_path=status_summary_path,
        history_path=root / "outputs" / "reports" / "PHASE1_SOAK_HISTORY.csv",
    )
    soak_history_report = generate_phase1_soak_history_report(
        soak_history.history_path,
        root / "outputs" / "reports" / "PHASE1_SOAK_HISTORY_REPORT.md",
    )
    acceptance = generate_phase1_acceptance_report(
        files_dir,
        acceptance_report_path,
        compile_log,
        root,
        soak_history_report.report_path,
        runtime_health.report_path,
        now=now,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bundle_path = output_dir / f"PHASE1_DRY_RUN_BUNDLE_{stamp}.zip"
    manifest_path = output_dir / f"PHASE1_DRY_RUN_BUNDLE_{stamp}_manifest.json"
    review_index = generate_phase1_review_index(
        root,
        root / "outputs" / "reports" / "PHASE1_REVIEW_INDEX.md",
        bundle_path,
        manifest_path,
        include_phase2_readiness=False,
    )
    generate_phase2_paper_ledger_schema_report(
        root,
        root / "outputs" / "reports" / "PHASE2_PAPER_LEDGER_SCHEMA_REPORT.md",
        root / "outputs" / "reports" / "PHASE2_PAPER_LEDGER_COLUMNS.csv",
    )
    observer_parity = generate_phase1_observer_parity_report(
        root,
        root / "outputs" / "reports" / "PHASE1_OBSERVER_PARITY_REPORT.md",
    )
    phase2_readiness = generate_phase2_readiness_report(
        root,
        root / "outputs" / "reports" / "PHASE2_READINESS_REPORT.md",
    )
    review_index = generate_phase1_review_index(
        root,
        root / "outputs" / "reports" / "PHASE1_REVIEW_INDEX.md",
        bundle_path,
        manifest_path,
    )

    entries: list[dict[str, object]] = []
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in _repo_files(root):
            _write_file(archive, path, path.relative_to(root).as_posix(), entries)

        for name in DEFAULT_RUNTIME_FILES:
            path = files_dir / name
            if path.exists():
                _write_file(archive, path, f"mt5_runtime/{name}", entries)

        if compile_log is not None and compile_log.exists():
            _write_file(archive, compile_log.resolve(), f"mt5_runtime/{compile_log.name}", entries)

        manifest = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "workspace_root": str(root),
            "mt5_files_dir": str(files_dir),
            "log_verification_status": verification.status,
            "log_report_path": str(verification.report_path),
            "soak_analysis_status": soak_analysis.status,
            "soak_report_path": str(soak_analysis.report_path),
            "runtime_health_status": runtime_health.status,
            "runtime_health_report_path": str(runtime_health.report_path),
            "would_signal_status": would_signal_report.status,
            "would_signal_report_path": str(would_signal_report.report_path),
            "would_signal_csv_path": str(would_signal_report.csv_path),
            "would_signal_count": would_signal_report.signal_count,
            "would_signal_cluster_count": would_signal_report.cluster_count,
            "acceptance_status": acceptance.status,
            "acceptance_report_path": str(acceptance.report_path),
            "review_index_status": review_index.status,
            "review_index_path": str(review_index.report_path),
            "observer_parity_status": observer_parity.status,
            "observer_parity_report_path": str(observer_parity.report_path),
            "phase2_readiness_status": phase2_readiness.status,
            "phase2_readiness_path": str(phase2_readiness.report_path),
            "status_summary_path": str(status_summary_path),
            "soak_history_path": str(soak_history.history_path),
            "soak_history_rows": soak_history.row_count,
            "soak_history_appended": soak_history.appended,
            "soak_history_report_status": soak_history_report.status,
            "soak_history_report_path": str(soak_history_report.report_path),
            "included_count": len(entries),
            "files": entries,
        }
        manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
        archive.writestr("phase1_bundle_manifest.json", manifest_bytes)

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return BundleOutput(
        bundle_path,
        manifest_path,
        len(entries),
        verification.status,
        soak_analysis.status,
        would_signal_report.status,
        acceptance.status,
        runtime_health.status,
        runtime_health.report_path,
        review_index.status,
        review_index.report_path,
        phase2_readiness.status,
        phase2_readiness.report_path,
        soak_history.history_path,
        soak_history.row_count,
        soak_history_report.status,
    )


def _repo_files(root: Path) -> list[Path]:
    paths: set[Path] = set()
    for pattern in REPO_PATTERNS:
        paths.update(path for path in root.glob(pattern) if path.is_file())
    return sorted(paths)


def _write_file(
    archive: zipfile.ZipFile,
    path: Path,
    archive_path: str,
    entries: list[dict[str, object]],
) -> None:
    archive.write(path, archive_path)
    entries.append(
        {
            "archive_path": archive_path,
            "source_path": str(path),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a Phase 1 dry-run review bundle.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Phase 1 workspace root.",
    )
    parser.add_argument("--files-dir", type=Path, required=True, help="MT5 MQL5/Files directory.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Bundle output directory. Defaults to outputs/review_bundles.",
    )
    parser.add_argument(
        "--compile-log",
        type=Path,
        default=Path("C:/MT5PortableGoldMission/compile_Phase1DryRunShell.log"),
        help="Optional MetaEditor compile log path.",
    )
    args = parser.parse_args(argv)

    output = generate_phase1_bundle(args.root, args.files_dir, args.output_dir, args.compile_log)
    print(f"Phase 1 review bundle created: {output.bundle_path}")
    print(f"Manifest: {output.manifest_path}")
    print(f"Included files: {output.included_count}")
    print(f"Log verification status: {output.log_status}")
    print(f"Soak analysis status: {output.soak_status}")
    print(f"Would-signal status: {output.would_signal_status}")
    print(f"Acceptance status: {output.acceptance_status}")
    print(f"Runtime health status: {output.runtime_health_status}")
    print(f"Runtime health report: {output.runtime_health_report_path}")
    print(f"Review index status: {output.review_index_status}")
    print(f"Review index: {output.review_index_path}")
    print(f"Phase 2 readiness status: {output.phase2_readiness_status}")
    print(f"Phase 2 readiness: {output.phase2_readiness_path}")
    print(f"Soak history: {output.soak_history_path}")
    print(f"Soak history rows: {output.soak_history_rows}")
    print(f"Soak history report status: {output.soak_history_report_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
