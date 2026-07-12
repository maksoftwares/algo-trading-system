"""Future review-gated NP1-G2 runner with report preflight and automatic stop packets.

NP1-G2A is repository-only. This module cannot execute unless a later exact G2-B
review artifact activates the reserved budget.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Sequence

import build_a1_xau_r6_native_spread_provenance_probe as B
import run_a1_xau_r6_native_spread_provenance_probe as G1


ROOT = Path(__file__).resolve().parents[1]
NEW_ROOT = Path(r"C:\MT5A1NP1SpreadProvenanceCleanG2")
QUARANTINED_ROOTS = (Path(r"C:\MT5A1NP1SpreadProvenanceClean"), Path(r"C:\MT5A1M5MomentumBacktest"))
MARKER = ".a1_xau_np1_spread_probe_g2_only"
MARKER_BYTES = b"NP1 SPREAD PROBE G2 ONLY\n"
RUN_IDS = ("warmup", "probe1", "probe2")
ACTIVATION = "NP1-G2B_EXACT_COMMIT_REVIEWED_AUTHORIZATION"
COMPLETE_NAME = "A1_XAU_R6_NATIVE_SPREAD_PROVENANCE_PROBE_G2_20260712"
STOP_NAME = "A1_XAU_R6_NATIVE_SPREAD_PROVENANCE_PROBE_G2_STOP_20260712"
REPORT_SENTINEL = ".np1_g2_reports_write_test"
ALLOWED_METADATA = ("Config/accounts.dat", "Config/servers.dat")
FORBIDDEN_ROOT_SURFACES = (
    "Bases", "bases", "history", "Tester/bases", "Tester/cache", "MQL5/Files",
    "Logs", "Reports", "Profiles",
)
CommandRunner = Callable[[Sequence[str], Path, int], object]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def inventory(root: Path) -> dict[str, Any]:
    if not root.exists():
        return {"root": str(root), "exists": False, "entries": []}
    rows = []
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        row: dict[str, Any] = {"relative_path": relative, "kind": "directory" if path.is_dir() else "file"}
        if path.is_file():
            row.update(size_bytes=path.stat().st_size, sha256=sha256_file(path), mtime_ns=path.stat().st_mtime_ns)
        rows.append(row)
    return {"root": str(root.resolve()), "exists": True, "entries": rows}


def validate_exact_root(root: Path, *, initial: bool) -> tuple[Path, Path]:
    root = root.resolve()
    if root != NEW_ROOT.resolve() or any(root == old.resolve() for old in QUARANTINED_ROOTS):
        raise RuntimeError("G2 exact new root required; quarantined roots rejected")
    if not (root / MARKER).is_file() or (root / MARKER).read_bytes() != MARKER_BYTES:
        raise RuntimeError("G2 marker mismatch")
    terminal, editor = root / "terminal64.exe", root / "MetaEditor64.exe"
    if not terminal.is_file() or not editor.is_file():
        raise RuntimeError("G2 terminal/editor missing")
    if initial:
        forbidden = [root / value for value in FORBIDDEN_ROOT_SURFACES]
        forbidden.extend((root / "Tester").glob("Agent-*"))
        present = [p.relative_to(root).as_posix() for p in forbidden if p.exists()]
        if present:
            raise RuntimeError(f"forbidden initial history/runtime surface: {present}")
    return terminal, editor


def validate_metadata_receipt(root: Path, receipt: dict[str, Any]) -> None:
    copied = receipt.get("copied", [])
    paths = {row.get("destination_relative") for row in copied}
    if not paths <= set(ALLOWED_METADATA):
        raise RuntimeError("unexpected copied Config file")
    for row in copied:
        relative = row["destination_relative"]
        destination = root / relative
        source = Path(row["source_path"])
        if source.resolve().parent.parent not in tuple(old.resolve() for old in QUARANTINED_ROOTS):
            raise RuntimeError("metadata source is not a quarantined approved root")
        if relative not in ALLOWED_METADATA or not destination.is_file():
            raise RuntimeError("metadata receipt destination mismatch")
        if destination.stat().st_size != row["size_bytes"] or sha256_file(destination) != row["sha256"]:
            raise RuntimeError("metadata receipt hash/size mismatch")


def prepare_reports_directory(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    reports = root / "Reports"
    before = inventory(root)
    if reports.exists():
        raise RuntimeError("Reports must be absent at initial G2 preflight")
    reports.mkdir()
    sentinel = reports / REPORT_SENTINEL
    content = f"NP1-G2 REPORT WRITE TEST {time.time_ns()}\n"
    sentinel.write_text(content, encoding="utf-8", newline="\n")
    if sentinel.read_text(encoding="utf-8") != content:
        raise RuntimeError("Reports sentinel read-back mismatch")
    sentinel_hash = sha256_file(sentinel)
    sentinel.unlink()
    if sentinel.exists():
        raise RuntimeError("Reports sentinel delete failed")
    if list(reports.glob("np1_g2_*")):
        raise RuntimeError("stale G2 report exists before first invocation")
    attestation = {"reports_path": str(reports), "created_by_runner": True, "sentinel_sha256": sentinel_hash, "sentinel_read_back": True, "sentinel_deleted": True, "writable": os.access(reports, os.W_OK)}
    if not attestation["writable"]:
        raise RuntimeError("Reports directory is not writable")
    return before, inventory(root), attestation


def render_ini(run_id: str) -> str:
    if run_id not in RUN_IDS:
        raise ValueError(run_id)
    warmup = "true" if run_id == "warmup" else "false"
    prefix = f"np1_g2_{run_id}_"
    return G1.render_ini(run_id).replace("np1_g1_", "np1_g2_").replace(f"InpWarmup={warmup}", f"InpWarmup={warmup}").replace(f"{run_id}_", f"{run_id}_")


def expected_report(root: Path, run_id: str) -> Path:
    return root / "Reports" / f"np1_g2_{run_id}.htm"


def validate_fresh_report(path: Path, not_before_ns: int, parser: Callable[[Path], Any]) -> Any:
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError("fresh nonempty report missing")
    if path.stat().st_mtime_ns + 2_000_000_000 < not_before_ns:
        raise RuntimeError("stale report rejected")
    return parser(path)


class Ledger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data: dict[str, Any] = {"metaeditor_compilations": 0, "tester_runs": [], "last_authorized_command_reached": None}
        self.persist()

    def persist(self) -> None:
        write_json(self.path, self.data)

    def compilation(self) -> None:
        if self.data["metaeditor_compilations"] >= 1:
            raise RuntimeError("second compilation forbidden")
        self.data["metaeditor_compilations"] += 1; self.data["last_authorized_command_reached"] = "compile"; self.persist()

    def run(self, run_id: str) -> None:
        expected = RUN_IDS[len(self.data["tester_runs"])] if len(self.data["tester_runs"]) < 3 else None
        if run_id != expected:
            raise RuntimeError("adaptive, out-of-order, or fourth run forbidden")
        self.data["tester_runs"].append(run_id); self.data["last_authorized_command_reached"] = run_id; self.persist()


def assert_mutually_exclusive(reports_root: Path) -> tuple[Path, Path]:
    complete, stop = reports_root / COMPLETE_NAME, reports_root / STOP_NAME
    if complete.exists() or stop.exists():
        raise RuntimeError("fixed complete/stop output root already exists")
    return complete, stop


def copy_if_present(source: Path, destination: Path) -> None:
    if source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, destination)


def _manifest(root: Path) -> None:
    artifacts = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name not in {"manifest.json", "manifest.sha256"}:
            artifacts.append({"relative_path": path.relative_to(root).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)})
    write_json(root / "manifest.json", {"schema_version": "a1_xau_r6_np1_g2_stop_manifest_v1", "artifacts": artifacts})
    (root / "manifest.sha256").write_text(sha256_file(root / "manifest.json") + "\n", encoding="ascii", newline="\n")


def preserve_stop_packet(
    *, stop: Path, root: Path, ledger: Path, preflight: dict[str, Any], reports_attestation: dict[str, Any],
    commands: list[dict[str, Any]], run_ids: list[str], error: BaseException, compile_workspace: Path | None = None,
) -> Path:
    stop.mkdir(parents=True, exist_ok=False)
    write_json(stop / "result.json", {"status": "NP1_G2_EVIDENCE_INVALID", "error": str(error), "last_authorized_command_reached": json.loads(ledger.read_text(encoding="utf-8"))["last_authorized_command_reached"], "probe1_invoked": "probe1" in run_ids, "probe2_invoked": "probe2" in run_ids, "canonical_np1c_authorized": False, "census_authorized": False, "profitability_authorized": False, "deployment_authorized": False, "broker_action_authorized": False})
    (stop / "README.md").write_text("# NP1-G2 Automatic Stop Packet\n\nStatus: `NP1_G2_EVIDENCE_INVALID`. No automatic retry is authorized.\n", encoding="utf-8", newline="\n")
    shutil.copyfile(ledger, stop / "invocation_ledger.json")
    write_json(stop / "preflight_root_inventory.json", preflight)
    write_json(stop / "post_stop_root_inventory.json", inventory(root))
    write_json(stop / "reports_directory_attestation.json", reports_attestation)
    write_json(stop / "commands.json", commands)
    for run_id in run_ids:
        run_dir = stop / "runs" / run_id
        copy_if_present(root / "Config" / f"np1_g2_{run_id}.ini", run_dir / "tester.ini")
        copy_if_present(expected_report(root, run_id), run_dir / "native_report.htm")
        for files_dir in (root / "Tester").glob("Agent-*/MQL5/Files"):
            for path in files_dir.glob(f"np1_g2_{run_id}_*"):
                copy_if_present(path, run_dir / path.name.removeprefix(f"np1_g2_{run_id}_"))
    log_rows = []
    for path in [*(root / "Tester" / "logs").glob("*.log"), *(root / "Tester").glob("Agent-*/logs/*.log")]:
        relative = path.relative_to(root).as_posix(); destination = stop / "logs" / relative
        copy_if_present(path, destination)
        log_rows.append({"source_relative": relative, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)})
    write_json(stop / "logs" / "log_inventory.json", {"logs": log_rows})
    if compile_workspace is not None and compile_workspace.exists():
        for path in compile_workspace.glob("*"):
            if path.is_file(): copy_if_present(path, stop / "compiled" / path.name)
    _manifest(stop)
    return stop


def parse_future_authorization(path: Path, commit: str, tree: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count("NP1_G2B_AUTHORIZATION_BLOCK_BEGIN") != 1 or text.count("NP1_G2B_AUTHORIZATION_BLOCK_END") != 1:
        raise PermissionError("later exact G2-B authorization required")
    required = ("NP1_G2B_AUTHORIZATION_STATUS: AUTHORIZED", "REVIEW_VERDICT: PASS", f"REVIEWED_G2A_COMMIT: {commit}", f"REVIEWED_G2A_TREE: {tree}", "MT5_EXECUTION_AUTHORIZED: true")
    if any(value not in text for value in required):
        raise PermissionError("G2-B authorization identity/fields mismatch")


def execute_future(*, authorization: str, review_artifact: Path, root: Path, reports_root: Path) -> None:
    if authorization != ACTIVATION:
        raise PermissionError("NP1-G2A is repo-only; future execution is not authorized")
    commit = G1.git("rev-parse", "HEAD"); tree = G1.git("show", "-s", "--format=%T", "HEAD")
    parse_future_authorization(review_artifact, commit, tree)
    raise RuntimeError("future G2-B executor remains review-gated at this commit")


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", default="")
    parser.add_argument("--review-artifact", type=Path)
    parser.add_argument("--root", type=Path, default=NEW_ROOT)
    parser.add_argument("--reports-root", type=Path, default=ROOT / "outputs" / "reports")
    args = parser.parse_args()
    if args.review_artifact is None:
        raise SystemExit("NP1-G2A is repository-only; no MT5 execution authorized")
    execute_future(authorization=args.authorization, review_artifact=args.review_artifact, root=args.root, reports_root=args.reports_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
