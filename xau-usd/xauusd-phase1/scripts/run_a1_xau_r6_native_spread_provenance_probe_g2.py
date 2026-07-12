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
        if source.name != destination.name or source.parent.name != "Config":
            raise RuntimeError("metadata source/destination identity mismatch")
        if not source.is_file() or source.stat().st_size != row["size_bytes"] or sha256_file(source) != row["sha256"]:
            raise RuntimeError("metadata source receipt hash/size mismatch")
        if destination.stat().st_size != row["size_bytes"] or sha256_file(destination) != row["sha256"] or source.read_bytes() != destination.read_bytes():
            raise RuntimeError("metadata receipt hash/size mismatch")
    config = root / "Config"
    actual = {f"Config/{p.name}" for p in config.iterdir() if p.is_file()} if config.is_dir() else set()
    if actual != paths:
        raise RuntimeError(f"actual Config file set differs from receipt: {sorted(actual)}")


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


def collect_exact_outputs(root: Path, run_id: str, destination: Path, not_before_ns: int, parser: Callable[[Path], Any]) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    copy_if_present(root / "Config" / f"np1_g2_{run_id}.ini", destination / "tester.ini")
    report = expected_report(root, run_id)
    validate_fresh_report(report, not_before_ns, parser)
    shutil.copyfile(report, destination / "native_report.htm")
    names = G1.WARMUP_NAMES if run_id == "warmup" else G1.OFFICIAL_NAMES
    for name in names:
        matches = list((root / "Tester").glob(f"Agent-*/MQL5/Files/np1_g2_{run_id}_{name}"))
        if len(matches) != 1:
            raise RuntimeError(f"expected exactly one {run_id} output {name}; found {len(matches)}")
        shutil.copyfile(matches[0], destination / name)


def _manifest(root: Path, schema: str = "a1_xau_r6_np1_g2_stop_manifest_v1") -> None:
    artifacts = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name not in {"manifest.json", "manifest.sha256"}:
            artifacts.append({"relative_path": path.relative_to(root).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)})
    write_json(root / "manifest.json", {"schema_version": schema, "artifacts": artifacts})
    (root / "manifest.sha256").write_text(sha256_file(root / "manifest.json") + "\n", encoding="ascii", newline="\n")


def preserve_stop_packet(
    *, stop: Path, root: Path, ledger: Path, preflight: dict[str, Any], reports_attestation: dict[str, Any],
    commands: list[dict[str, Any]], run_ids: list[str], error: BaseException, compile_workspace: Path | None = None,
    metadata_receipt: Path | None = None, partial_staging: Path | None = None,
) -> Path:
    stop.mkdir(parents=True, exist_ok=False)
    write_json(stop / "result.json", {"status": "NP1_G2_EVIDENCE_INVALID", "error": str(error), "last_authorized_command_reached": json.loads(ledger.read_text(encoding="utf-8"))["last_authorized_command_reached"], "probe1_invoked": "probe1" in run_ids, "probe2_invoked": "probe2" in run_ids, "canonical_np1c_authorized": False, "census_authorized": False, "profitability_authorized": False, "deployment_authorized": False, "broker_action_authorized": False})
    (stop / "README.md").write_text("# NP1-G2 Automatic Stop Packet\n\nStatus: `NP1_G2_EVIDENCE_INVALID`. No automatic retry is authorized.\n", encoding="utf-8", newline="\n")
    shutil.copyfile(ledger, stop / "invocation_ledger.json")
    write_json(stop / "preflight_root_inventory.json", preflight)
    write_json(stop / "post_stop_root_inventory.json", inventory(root))
    write_json(stop / "reports_directory_attestation.json", reports_attestation)
    write_json(stop / "commands.json", commands)
    if metadata_receipt is not None: copy_if_present(metadata_receipt, stop / "metadata_receipt.json")
    searched: list[dict[str, Any]] = []
    for run_id in run_ids:
        run_dir = stop / "runs" / run_id
        copy_if_present(root / "Config" / f"np1_g2_{run_id}.ini", run_dir / "tester.ini")
        copy_if_present(expected_report(root, run_id), run_dir / "native_report.htm")
        for files_dir in (root / "Tester").glob("Agent-*/MQL5/Files"):
            for path in files_dir.glob(f"np1_g2_{run_id}_*"):
                relative = path.relative_to(root).as_posix(); searched.append({"run_id":run_id,"source_relative":relative,"size_bytes":path.stat().st_size,"sha256":sha256_file(path)})
                copy_if_present(path, run_dir / "searched_outputs" / relative)
    write_json(stop / "searched_location_inventory.json", {"matches": searched})
    log_rows = []
    for path in [*(root / "Logs").glob("*.log"), *(root / "Tester" / "logs").glob("*.log"), *(root / "Tester").glob("Agent-*/logs/*.log")]:
        relative = path.relative_to(root).as_posix(); destination = stop / "logs" / relative
        copy_if_present(path, destination)
        log_rows.append({"source_relative": relative, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)})
    write_json(stop / "logs" / "log_inventory.json", {"logs": log_rows})
    if compile_workspace is not None and compile_workspace.exists():
        for path in compile_workspace.glob("*"):
            if path.is_file(): copy_if_present(path, stop / "compiled" / path.name)
    if partial_staging is not None and partial_staging.exists():
        shutil.move(str(partial_staging), str(stop / "partial_staging"))
    _manifest(stop)
    verify_manifest(stop)
    return stop


def verify_manifest(root: Path) -> None:
    payload = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if (root / "manifest.sha256").read_text(encoding="ascii").strip() != sha256_file(root / "manifest.json"):
        raise RuntimeError("manifest sidecar mismatch")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()} - {"manifest.json", "manifest.sha256"}
    listed = {row["relative_path"] for row in payload["artifacts"]}
    if actual != listed:
        raise RuntimeError("manifest tree mismatch")
    for row in payload["artifacts"]:
        path = root / row["relative_path"]
        if path.stat().st_size != row["size_bytes"] or sha256_file(path) != row["sha256"]:
            raise RuntimeError("manifest artifact mismatch")


def parse_future_authorization(path: Path, artifact_sha256: str, commit: str, tree: str) -> dict[str, str]:
    if path.name != "A1_XAU_NP1G2A1_EXECUTION_AUTHORIZATION_195B5831_2026_07_12.md" or not path.is_file() or sha256_file(path) != artifact_sha256:
        raise PermissionError("exact external G2-B review artifact identity required")
    text = path.read_text(encoding="utf-8")
    begin, end = "NP1_G2B_AUTHORIZATION_BLOCK_BEGIN", "NP1_G2B_AUTHORIZATION_BLOCK_END"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise PermissionError("later exact G2-B authorization required")
    fields = {}
    for raw in text.split(begin, 1)[1].split(end, 1)[0].splitlines():
        if ":" in raw:
            key, value = (part.strip().strip("`") for part in raw.split(":", 1))
            if key in fields: raise PermissionError(f"duplicate authorization field: {key}")
            fields[key] = value
    expected = {"NP1_G2B_AUTHORIZATION_STATUS":"AUTHORIZED","REVIEW_VERDICT":"PASS","REVIEWED_G2A_COMMIT":commit,"REVIEWED_G2A_TREE":tree,"NEW_ROOT_PATH":str(NEW_ROOT),"MARKER_BYTES":"NP1 SPREAD PROBE G2 ONLY\\n","METADATA_ALLOWLIST":"Config/accounts.dat,Config/servers.dat","METAEDITOR_COMPILATIONS_MAX":"1","STRATEGY_TESTER_RUNS_MAX":"3","STRATEGY_TESTER_ORDER":"warmup,probe1,probe2","MT5_EXECUTION_AUTHORIZED":"true","CANONICAL_NP1C_RESULT_AUTHORIZED":"false","R6_CENSUS_AUTHORIZED":"false","BROKER_ACTION_AUTHORIZED":"false"}
    outside = (text.split(begin,1)[0] + text.split(end,1)[1]).upper()
    if fields != expected or "FAIL" in outside or "NO-GO" in outside:
        raise PermissionError("G2-B authorization identity/fields mismatch")
    return fields


def execute_future(*, authorization: str, review_artifact: Path, review_sha256: str, reviewed_commit: str, reviewed_tree: str, root: Path, reports_root: Path, metadata_receipt: Path, command_runner: CommandRunner = G1.command_runner, compile_runner: CommandRunner = G1.command_runner, version_reader: Callable[[Path], str] = G1.executable_version) -> Path:
    if authorization != ACTIVATION:
        raise PermissionError("NP1-G2A is repo-only; future execution is not authorized")
    commit = G1.git("rev-parse", "HEAD"); tree = G1.git("show", "-s", "--format=%T", "HEAD")
    if commit != reviewed_commit or tree != reviewed_tree or G1.git("status", "--porcelain=v1", "--untracked-files=all"):
        raise PermissionError("clean reviewed G2-A commit/tree required")
    parse_future_authorization(review_artifact, review_sha256, commit, tree)
    complete, stop = assert_mutually_exclusive(reports_root)
    ledger_path = root / ".np1_g2_invocation_ledger.json"
    commands: list[dict[str, Any]] = []; invoked: list[str] = []; preflight: dict[str, Any] = {}; report_attestation: dict[str, Any] = {}
    workspace = root / "np1_g2_compile_workspace"
    staging = reports_root / ".A1_XAU_R6_NATIVE_SPREAD_PROVENANCE_PROBE_G2_20260712.staging"
    if staging.exists(): raise RuntimeError("noncanonical staging path already exists")
    try:
        terminal, editor = validate_exact_root(root, initial=True)
        receipt = json.loads(metadata_receipt.read_text(encoding="utf-8")); validate_metadata_receipt(root, receipt)
        preflight, _, report_attestation = prepare_reports_directory(root)
        ledger = Ledger(ledger_path); ledger.compilation()
        compiled = G1.compile_once(root, editor, runner=compile_runner, version_reader=version_reader)
        workspace.mkdir(); copy_if_present(compiled.source, workspace / B.PROBE_NAME); copy_if_present(compiled.ex5, workspace / compiled.ex5.name); copy_if_present(compiled.log, workspace / "compile.log")
        B.build_probe(workspace / B.PROBE_NAME, workspace / "source_manifest.json")
        commands.append(compiled.command_record)
        staging.mkdir()
        shutil.copytree(workspace, staging / "compiled")
        for run_id in RUN_IDS:
            if sha256_file(compiled.ex5) != compiled.ex5_sha256: raise RuntimeError("EX5 drift")
            ini = root / "Config" / f"np1_g2_{run_id}.ini"; ini.write_text(render_ini(run_id), encoding="utf-8", newline="\n")
            if expected_report(root, run_id).exists(): raise RuntimeError("stale report before invocation")
            ledger.run(run_id); invoked.append(run_id)
            command = [str(terminal), "/portable", f"/config:{ini}"]; started = time.time_ns(); done = command_runner(command, root, 7200); commands.append(G1.record(command, done))
            if int(getattr(done, "returncode", 1)) != 0: raise RuntimeError(f"tester {run_id} failed")
            import analyze_a1_xau_r6_native_spread_provenance_probe as A
            collect_exact_outputs(root, run_id, staging / "runs" / run_id, started, A.parse_report)
        if sha256_file(compiled.ex5) != compiled.ex5_sha256: raise RuntimeError("final post-probe2 EX5 drift")
        write_json(staging / "metadata_receipt.json", receipt); write_json(staging / "preflight_root_inventory.json", preflight); write_json(staging / "post_run_root_inventory.json", inventory(root)); write_json(staging / "reports_directory_attestation.json", report_attestation); write_json(staging / "invocation_ledger.json", ledger.data); write_json(staging / "commands.json", commands)
        import analyze_a1_xau_r6_native_spread_provenance_probe as A
        result = A.build_packet(staging); result["status"] = "NP1_G2_DIAGNOSTIC_COMPLETE"; A.write_json(staging / "result.json", result)
        (staging/"README.md").write_text("# NP1-G2 Native Spread Provenance Probe\n\nStatus: `NP1_G2_DIAGNOSTIC_COMPLETE`. Diagnostic only.\n",encoding="utf-8",newline="\n")
        (staging/"test_validation.md").write_text("# NP1-G2 Validation\n\nLocked G2 implementation and evidence verification passed.\n",encoding="utf-8",newline="\n")
        _manifest(staging,"a1_xau_r6_np1_g2_complete_manifest_v1"); verify_manifest(staging)
        staging.rename(complete)
        return complete
    except BaseException as exc:
        if not ledger_path.exists(): write_json(ledger_path, {"metaeditor_compilations":0,"tester_runs":[],"last_authorized_command_reached":"preflight"})
        preserve_stop_packet(stop=stop, root=root, ledger=ledger_path, preflight=preflight, reports_attestation=report_attestation, commands=commands, run_ids=invoked, error=exc, compile_workspace=workspace, metadata_receipt=metadata_receipt, partial_staging=staging)
        raise


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", default="")
    parser.add_argument("--review-artifact", type=Path)
    parser.add_argument("--review-sha256", default="")
    parser.add_argument("--reviewed-commit", default="")
    parser.add_argument("--reviewed-tree", default="")
    parser.add_argument("--metadata-receipt", type=Path)
    parser.add_argument("--root", type=Path, default=NEW_ROOT)
    parser.add_argument("--reports-root", type=Path, default=ROOT / "outputs" / "reports")
    args = parser.parse_args()
    if args.review_artifact is None:
        raise SystemExit("NP1-G2A is repository-only; no MT5 execution authorized")
    if args.metadata_receipt is None: raise SystemExit("--metadata-receipt required")
    execute_future(authorization=args.authorization, review_artifact=args.review_artifact, review_sha256=args.review_sha256, reviewed_commit=args.reviewed_commit, reviewed_tree=args.reviewed_tree, root=args.root, reports_root=args.reports_root, metadata_receipt=args.metadata_receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
