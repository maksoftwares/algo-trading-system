"""Future review-gated NP1-G2 runner with report preflight and automatic stop packets.

NP1-G2A is repository-only. This module cannot execute unless a later exact G2-B
review artifact activates the reserved budget.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Sequence

import build_a1_xau_r6_native_spread_provenance_probe as B
import run_a1_xau_r6_native_spread_provenance_probe as G1


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_REPORTS_ROOT = ROOT / "outputs" / "reports"
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
CANONICAL_REPORTS_RELATIVE = "xau-usd/xauusd-phase1/outputs/reports"
WARMUP_ASSERTIONS = {"environment", "run_id", "zero_files", "positions_zero", "orders_zero", "warmup_only"}
OFFICIAL_ASSERTIONS = {"environment", "run_id", "zero_files", "positions_zero", "orders_zero", "h1_export", "h4_export", "d1_export", "interfaces_export", "ticks_20250618", "ticks_20250929", "ticks_20251117", "ticks_20260414"}
G2_README = "# NP1-G2 Native Spread Provenance Probe\n\nStatus: `NP1_G2_DIAGNOSTIC_COMPLETE`. Diagnostic only.\n"
G2_VALIDATION = "# NP1-G2 Validation\n\nLocked G2 implementation and evidence verification passed.\n"
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
    if set(receipt) != {"mode", "copied"} or receipt.get("mode") not in {"COPIED_ALLOWLIST", "ZERO_COPY"} or not isinstance(receipt.get("copied"), list):
        raise RuntimeError("metadata receipt closed schema mismatch")
    copied = receipt.get("copied", [])
    if (receipt["mode"] == "ZERO_COPY") != (not copied):
        raise RuntimeError("metadata receipt mode/content mismatch")
    row_fields={"source_path","source_relative","destination_relative","size_bytes","sha256"}
    if any(not isinstance(row,dict) or set(row)!=row_fields for row in copied):
        raise RuntimeError("metadata receipt row closed schema mismatch")
    paths = {row.get("destination_relative") for row in copied}
    if len(paths) != len(copied): raise RuntimeError("duplicate metadata receipt entry")
    sources = {row.get("source_path") for row in copied}
    if len(sources) != len(copied): raise RuntimeError("duplicate metadata receipt source")
    if not paths <= set(ALLOWED_METADATA):
        raise RuntimeError("unexpected copied Config file")
    for row in copied:
        relative = row["destination_relative"]
        destination = root / relative
        source = Path(row["source_path"])
        if row["source_relative"] != relative: raise RuntimeError("metadata source/destination relative identity mismatch")
        if any(p.is_symlink() or (getattr(p.stat(),"st_file_attributes",0)&0x400) or p.stat().st_nlink != 1 for p in (source,destination)):
            raise RuntimeError("metadata symlink/reparse/hard-link rejected")
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
    if any(p.is_dir() or p.is_symlink() for p in config.rglob("*")): raise RuntimeError("nested Config or reparse point rejected")
    actual = {p.relative_to(root).as_posix() for p in config.rglob("*") if p.is_file()} if config.is_dir() else set()
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


def collect_exact_outputs(root: Path, run_id: str, destination: Path, not_before_ns: int, parser: Callable[[Path], Any]) -> list[dict[str, Any]]:
    destination.mkdir(parents=True, exist_ok=False)
    ini=root / "Config" / f"np1_g2_{run_id}.ini"
    if not ini.is_file() or ini.read_text(encoding="utf-8") != render_ini(run_id): raise RuntimeError("executed G2 INI missing or not exact")
    shutil.copyfile(ini,destination/"tester.ini"); selected=[{"kind":"tester_ini","source":str(ini),"sha256":sha256_file(ini),"size_bytes":ini.stat().st_size}]
    report = expected_report(root, run_id)
    validate_fresh_report(report, not_before_ns, parser)
    shutil.copyfile(report, destination / "native_report.htm")
    selected.append({"kind":"native_report","source":str(report),"sha256":sha256_file(report),"size_bytes":report.stat().st_size,"fresh_not_before_ns":not_before_ns})
    names = G1.WARMUP_NAMES if run_id == "warmup" else G1.OFFICIAL_NAMES
    for name in names:
        matches = list((root / "Tester").glob(f"Agent-*/MQL5/Files/np1_g2_{run_id}_{name}"))
        if len(matches) != 1:
            raise RuntimeError(f"expected exactly one {run_id} output {name}; found {len(matches)}")
        shutil.copyfile(matches[0], destination / name)
        selected.append({"kind":name,"source":str(matches[0]),"sha256":sha256_file(matches[0]),"size_bytes":matches[0].stat().st_size})
    return selected


def changed_logs(root: Path, preflight: dict[str, Any]) -> list[Path]:
    prior={row["relative_path"]:(row.get("size_bytes"),row.get("sha256")) for row in preflight.get("entries",[]) if row.get("kind")=="file"}
    candidates=[*(root/"Logs").glob("*.log"),*(root/"Tester"/"logs").glob("*.log"),*(root/"Tester").glob("Agent-*/logs/*.log")]
    return [p for p in candidates if prior.get(p.relative_to(root).as_posix())!=(p.stat().st_size,sha256_file(p))]


def write_g2_wrapper(packet: Path, result: dict[str, Any]) -> None:
    import analyze_a1_xau_r6_native_spread_provenance_probe as A
    wrapped=dict(result); wrapped.update(status="NP1_G2_DIAGNOSTIC_COMPLETE",pnl_authorized=False,target_exit_mfe_mae_authorized=False,demo_live_attach_authorized=False,preset_profile_arming_authorized=False,profitability_authorized=False,deployment_authorized=False); A.write_json(packet/"result.json",wrapped)
    (packet/"README.md").write_text(G2_README,encoding="utf-8",newline="\n")
    (packet/"test_validation.md").write_text(G2_VALIDATION,encoding="utf-8",newline="\n")


def assert_exact_assertions(packet: Path) -> None:
    for run_id in RUN_IDS:
        with (packet/"runs"/run_id/"assertions.tsv").open(encoding="utf-8-sig",newline="") as handle:
            rows=list(csv.DictReader(handle,delimiter="\t"))
        expected=WARMUP_ASSERTIONS if run_id=="warmup" else OFFICIAL_ASSERTIONS
        ids=[row.get("assertion_id") for row in rows]
        if set(ids)!=expected or len(ids)!=len(expected) or any(row.get("passed")!="true" for row in rows):
            raise RuntimeError(f"exact {run_id} assertion set mismatch")


def validate_packet_attestations(packet: Path, context: dict[str, Any]) -> list[str]:
    checks=[]
    def load(name: str) -> Any: return json.loads((packet/name).read_text(encoding="utf-8"))
    if load("authorization_attestation.json")!=context["authorization_attestation"]: raise RuntimeError("authorization attestation mismatch")
    checks.append("authorization_and_reviewed_executor")
    if load("metadata_receipt.json")!=context["metadata_receipt"]: raise RuntimeError("metadata receipt packet mismatch")
    receipt=load("metadata_receipt.json")
    if set(receipt)!={"mode","copied"} or receipt["mode"] not in {"COPIED_ALLOWLIST","ZERO_COPY"}: raise RuntimeError("metadata receipt packet schema mismatch")
    checks.append("metadata_receipt")
    ledger=load("invocation_ledger.json")
    if ledger!={"metaeditor_compilations":1,"tester_runs":list(RUN_IDS),"last_authorized_command_reached":"probe2"}: raise RuntimeError("invocation ledger mismatch")
    commands=load("commands.json")
    if len(commands)!=4 or any(int(row.get("exit_code",1))!=0 for row in commands): raise RuntimeError("command budget/result mismatch")
    if Path(commands[0].get("command",[""])[0]).name.lower()!="metaeditor64.exe": raise RuntimeError("compile command identity mismatch")
    for run_id,row in zip(RUN_IDS,commands[1:]):
        command=row.get("command",[])
        if not command or Path(command[0]).name.lower()!="terminal64.exe" or f"np1_g2_{run_id}.ini" not in " ".join(command): raise RuntimeError("tester command order/identity mismatch")
    checks.append("one_compile_three_ordered_runs")
    compiled=load("compile_attestation.json"); source=packet/"compiled"/B.PROBE_NAME; ex5=packet/"compiled"/Path(compiled["ex5_name"]).name; log=packet/"compiled"/"compile.log"
    B.verify_source(source)
    source_manifest=load("compiled/source_manifest.json")
    expected_source_manifest={"schema_version":"a1_xau_r6_native_spread_probe_source_manifest_v1","source":B.PROBE_NAME,"source_sha256":sha256_file(source),"zero_action":True,"interfaces":["CopyRates.spread","CopySpread","iSpread","CopyTicksRange.bid_ask"]}
    if source_manifest!=expected_source_manifest: raise RuntimeError("source manifest mismatch")
    if compiled!={"source_name":B.PROBE_NAME,"source_sha256":sha256_file(source),"ex5_name":ex5.name,"ex5_sha256":sha256_file(ex5),"metaeditor_version":G1.EXPECTED_VERSION,"compile_log_sha256":sha256_file(log)}: raise RuntimeError("compiled identity mismatch")
    text=log.read_text(encoding="utf-8",errors="replace")
    if re.search(r"\b0\s+errors?\b",text,re.I) is None or re.search(r"\b0\s+warnings?\b",text,re.I) is None: raise RuntimeError("compile log is not zero-error/zero-warning")
    ex5_checks=load("ex5_identity_attestation.json")
    if [row["stage"] for row in ex5_checks] != ["before_warmup","before_probe1","before_probe2","after_probe2"] or any(row["sha256"]!=compiled["ex5_sha256"] for row in ex5_checks): raise RuntimeError("EX5 continuity mismatch")
    checks.append("deterministic_source_build5833_ex5_continuity")
    selected=load("searched_location_inventory.json")["selected_sources"]
    expected_count=sum(2+len(G1.WARMUP_NAMES if rid=="warmup" else G1.OFFICIAL_NAMES) for rid in RUN_IDS)
    if len(selected)!=expected_count: raise RuntimeError("selected source count mismatch")
    for run_id in RUN_IDS:
        expected_names={"tester_ini","native_report",*(G1.WARMUP_NAMES if run_id=="warmup" else G1.OFFICIAL_NAMES)}
        rows=[row for row in selected if f"np1_g2_{run_id}" in row["source"]]
        if {row["kind"] for row in rows}!=expected_names or len(rows)!=len(expected_names): raise RuntimeError(f"selected source identity mismatch: {run_id}")
        for row in rows:
            name={"tester_ini":"tester.ini","native_report":"native_report.htm"}.get(row["kind"],row["kind"])
            target=packet/"runs"/run_id/name
            if target.stat().st_size!=row["size_bytes"] or sha256_file(target)!=row["sha256"]: raise RuntimeError("selected source-to-packet mismatch")
        if (packet/"runs"/run_id/"tester.ini").read_text(encoding="utf-8")!=render_ini(run_id): raise RuntimeError("packet INI mismatch")
    checks.append("exact_inis_and_selected_sources")
    preflight={row["relative_path"]:(row.get("size_bytes"),row.get("sha256")) for row in load("preflight_root_inventory.json").get("entries",[]) if row.get("kind")=="file"}
    log_rows=load("logs/log_inventory.json")["logs"]
    if {p.relative_to(packet/"logs").as_posix() for p in (packet/"logs").rglob("*") if p.is_file() and p.name!="log_inventory.json"}!={row["source_relative"] for row in log_rows}: raise RuntimeError("log file-set mismatch")
    for row in log_rows:
        copied=packet/"logs"/row["source_relative"]
        if not copied.is_file() or copied.stat().st_size!=row["size_bytes"] or sha256_file(copied)!=row["sha256"] or preflight.get(row["source_relative"])==(row["size_bytes"],row["sha256"]): raise RuntimeError("fresh log reconciliation mismatch")
    checks.append("fresh_logs")
    report_att=load("reports_directory_attestation.json")
    if report_att.get("reports_path")!=str(context["root"]/"Reports") or not all(report_att.get(k) for k in ("created_by_runner","sentinel_read_back","sentinel_deleted","writable")): raise RuntimeError("Reports attestation mismatch")
    if load("preflight_root_inventory.json").get("root")!=str(context["root"].resolve()) or load("post_reports_creation_inventory.json").get("root")!=str(context["root"].resolve()) or load("post_run_root_inventory.json").get("root")!=str(context["root"].resolve()): raise RuntimeError("root inventory identity mismatch")
    checks.append("root_and_reports_inventories")
    assert_exact_assertions(packet); checks.append("exact_zero_action_assertion_sets")
    return checks


def semantic_verify_packet(packet: Path, scratch: Path, context: dict[str, Any]) -> dict[str, Any]:
    import analyze_a1_xau_r6_native_spread_provenance_probe as A
    original={p.relative_to(packet).as_posix():sha256_file(p) for p in packet.rglob("*") if p.is_file()}
    if scratch.exists(): raise RuntimeError("semantic verification scratch exists")
    scratch.mkdir()
    try:
        shutil.copytree(packet/"compiled",scratch/"compiled"); shutil.copytree(packet/"runs",scratch/"runs")
        recomputed=A.build_packet(scratch); write_g2_wrapper(scratch,recomputed)
        compared=[]
        for name in ("analysis/prior_vs_clean_bar_fingerprints.json","analysis/reviewed_negative_bar_comparison.csv","analysis/bar_interface_comparison.csv","analysis/raw_tick_spread_summary.csv","analysis/raw_tick_negative_rows.csv","analysis/provenance_classification.json","result.json","README.md","test_validation.md"):
            a=packet/name; b=scratch/name
            if a.read_bytes()!=b.read_bytes(): raise RuntimeError(f"semantic recomputation mismatch: {name}")
            compared.append({"path":name,"sha256":sha256_file(a)})
        attestation_checks=validate_packet_attestations(packet,context)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    after={p.relative_to(packet).as_posix():sha256_file(p) for p in packet.rglob("*") if p.is_file()}
    if original!=after: raise RuntimeError("semantic verifier mutated original packet")
    return {"verifier":"full_packet_temporary_copy_recompute_v2","scientific_checks":["full_normalized_result","deterministic_g2_wrapper","tick_windows","bar_interfaces","negative_rows","classification"],"attestation_checks":attestation_checks,"compared":compared,"original_packet_mutated":False}


def _manifest(root: Path, schema: str = "a1_xau_r6_np1_g2_stop_manifest_v1") -> None:
    artifacts = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.relative_to(root).as_posix() not in {"manifest.json", "manifest.sha256"}:
            artifacts.append({"relative_path": path.relative_to(root).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)})
    write_json(root / "manifest.json", {"schema_version": schema, "artifacts": artifacts})
    (root / "manifest.sha256").write_text(sha256_file(root / "manifest.json") + "\n", encoding="ascii", newline="\n")


def preserve_stop_packet(
    *, stop: Path, root: Path, ledger: Path, preflight: dict[str, Any], reports_attestation: dict[str, Any],
    commands: list[dict[str, Any]], run_ids: list[str], error: BaseException, compile_workspace: Path | None = None,
    metadata_receipt: Path | None = None, partial_staging: Path | None = None,
    authorization_attestation: dict[str, Any] | None = None, post_reports_inventory: dict[str, Any] | None = None,
) -> Path:
    stop.mkdir(parents=True, exist_ok=False)
    write_json(stop / "result.json", {"status": "NP1_G2_EVIDENCE_INVALID", "error": str(error), "last_authorized_command_reached": json.loads(ledger.read_text(encoding="utf-8"))["last_authorized_command_reached"], "probe1_invoked": "probe1" in run_ids, "probe2_invoked": "probe2" in run_ids, "canonical_np1c_authorized": False, "census_authorized": False, "profitability_authorized": False, "deployment_authorized": False, "broker_action_authorized": False})
    (stop / "README.md").write_text("# NP1-G2 Automatic Stop Packet\n\nStatus: `NP1_G2_EVIDENCE_INVALID`. No automatic retry is authorized.\n", encoding="utf-8", newline="\n")
    shutil.copyfile(ledger, stop / "invocation_ledger.json")
    write_json(stop / "preflight_root_inventory.json", preflight)
    write_json(stop / "post_stop_root_inventory.json", inventory(root))
    write_json(stop / "reports_directory_attestation.json", reports_attestation)
    write_json(stop / "post_reports_creation_inventory.json", post_reports_inventory or {})
    write_json(stop / "authorization_attestation.json", authorization_attestation or {})
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
    for path in changed_logs(root, preflight):
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
    if path.name != "A1_XAU_NP1G2A5_EXECUTION_AUTHORIZATION_D8699D6E_2026_07_13.md" or not path.is_file() or sha256_file(path) != artifact_sha256:
        raise PermissionError("exact external G2-B review artifact identity required")
    text = path.read_text(encoding="utf-8")
    begin, end = "NP1_G2B_AUTHORIZATION_BLOCK_BEGIN", "NP1_G2B_AUTHORIZATION_BLOCK_END"
    if text.count(begin) != 1 or text.count(end) != 1 or text.index(begin) >= text.index(end):
        raise PermissionError("later exact G2-B authorization required")
    fields = {}
    for raw in text.split(begin, 1)[1].split(end, 1)[0].splitlines():
        if ":" in raw:
            key, value = (part.strip().strip("`") for part in raw.split(":", 1))
            if key in fields: raise PermissionError(f"duplicate authorization field: {key}")
            fields[key] = value
    expected = {"NP1_G2B_AUTHORIZATION_STATUS":"AUTHORIZED","REVIEW_VERDICT":"PASS","REVIEWED_EXECUTOR_COMMIT":commit,"REVIEWED_EXECUTOR_TREE":tree,"NEW_ROOT_PATH":str(NEW_ROOT),"MARKER_BYTES":"NP1 SPREAD PROBE G2 ONLY\\n","CANONICAL_REPORTS_ROOT":CANONICAL_REPORTS_RELATIVE,"COMPLETE_OUTPUT_ROOT":f"{CANONICAL_REPORTS_RELATIVE}/{COMPLETE_NAME}","STOP_OUTPUT_ROOT":f"{CANONICAL_REPORTS_RELATIVE}/{STOP_NAME}","METADATA_RECEIPT_MODES":"COPIED_ALLOWLIST,ZERO_COPY","METADATA_ALLOWLIST":"Config/accounts.dat,Config/servers.dat","METAEDITOR_COMPILATIONS_MAX":"1","STRATEGY_TESTER_RUNS_MAX":"3","STRATEGY_TESTER_ORDER":"warmup,probe1,probe2","MT5_EXECUTION_AUTHORIZED":"true","CANONICAL_NP1C_RESULT_AUTHORIZED":"false","R6_CENSUS_AUTHORIZED":"false","PNL_AUTHORIZED":"false","TARGET_EXIT_MFE_MAE_AUTHORIZED":"false","DEMO_LIVE_ATTACH_AUTHORIZED":"false","PRESET_PROFILE_ARMING_AUTHORIZED":"false","BROKER_ACTION_AUTHORIZED":"false","DEPLOYMENT_AUTHORIZED":"false"}
    outside = text.split(begin,1)[0] + text.split(end,1)[1]
    if fields != expected or outside.strip():
        raise PermissionError("G2-B authorization identity/fields mismatch")
    return fields


def execute_future(*, authorization: str, review_artifact: Path, review_sha256: str, reviewed_commit: str, reviewed_tree: str, root: Path, reports_root: Path, metadata_receipt: Path, command_runner: CommandRunner = G1.command_runner, compile_runner: CommandRunner = G1.command_runner, version_reader: Callable[[Path], str] = G1.executable_version) -> Path:
    if authorization != ACTIVATION:
        raise PermissionError("NP1-G2A is repo-only; future execution is not authorized")
    commit = G1.git("rev-parse", "HEAD"); tree = G1.git("show", "-s", "--format=%T", "HEAD")
    if commit != reviewed_commit or tree != reviewed_tree or G1.git("status", "--porcelain=v1", "--untracked-files=all"):
        raise PermissionError("clean reviewed G2-A commit/tree required")
    if reports_root.resolve()!=CANONICAL_REPORTS_ROOT.resolve(): raise PermissionError("exact canonical repository reports root required")
    auth_fields = parse_future_authorization(review_artifact, review_sha256, commit, tree)
    authority_attestation = {"artifact":review_artifact.name,"sha256":review_sha256,"parsed_fields":auth_fields,"reviewed_executor_commit":commit,"reviewed_executor_tree":tree,"canonical_reports_root":CANONICAL_REPORTS_RELATIVE,"complete_output_root":f"{CANONICAL_REPORTS_RELATIVE}/{COMPLETE_NAME}","stop_output_root":f"{CANONICAL_REPORTS_RELATIVE}/{STOP_NAME}"}
    complete, stop = assert_mutually_exclusive(reports_root)
    terminal, editor = validate_exact_root(root, initial=True)
    receipt = json.loads(metadata_receipt.read_text(encoding="utf-8")); validate_metadata_receipt(root, receipt)
    ledger_path = root / ".np1_g2_invocation_ledger.json"
    commands: list[dict[str, Any]] = []; invoked: list[str] = []; preflight: dict[str, Any] = {}; post_reports: dict[str, Any] = {}; report_attestation: dict[str, Any] = {}
    workspace = root / "np1_g2_compile_workspace"
    staging = reports_root / ".A1_XAU_R6_NATIVE_SPREAD_PROVENANCE_PROBE_G2_20260712.staging"
    if staging.exists(): raise RuntimeError("noncanonical staging path already exists")
    try:
        preflight, post_reports, report_attestation = prepare_reports_directory(root)
        ledger = Ledger(ledger_path); ledger.compilation()
        compiled = G1.compile_once(root, editor, runner=compile_runner, version_reader=version_reader)
        workspace.mkdir(); copy_if_present(compiled.source, workspace / B.PROBE_NAME); copy_if_present(compiled.ex5, workspace / compiled.ex5.name); copy_if_present(compiled.log, workspace / "compile.log")
        B.build_probe(workspace / B.PROBE_NAME, workspace / "source_manifest.json")
        commands.append(compiled.command_record)
        staging.mkdir()
        shutil.copytree(workspace, staging / "compiled")
        selected_sources=[]; ex5_checks=[]
        for run_id in RUN_IDS:
            if sha256_file(compiled.ex5) != compiled.ex5_sha256: raise RuntimeError("EX5 drift")
            ex5_checks.append({"stage":f"before_{run_id}","sha256":sha256_file(compiled.ex5)})
            ini = root / "Config" / f"np1_g2_{run_id}.ini"; ini.write_text(render_ini(run_id), encoding="utf-8", newline="\n")
            if expected_report(root, run_id).exists(): raise RuntimeError("stale report before invocation")
            ledger.run(run_id); invoked.append(run_id)
            command = [str(terminal), "/portable", f"/config:{ini}"]; started = time.time_ns(); done = command_runner(command, root, 7200); commands.append(G1.record(command, done))
            if int(getattr(done, "returncode", 1)) != 0: raise RuntimeError(f"tester {run_id} failed")
            import analyze_a1_xau_r6_native_spread_provenance_probe as A
            selected_sources.extend(collect_exact_outputs(root, run_id, staging / "runs" / run_id, started, A.parse_report))
        if sha256_file(compiled.ex5) != compiled.ex5_sha256: raise RuntimeError("final post-probe2 EX5 drift")
        ex5_checks.append({"stage":"after_probe2","sha256":sha256_file(compiled.ex5)})
        write_json(staging / "metadata_receipt.json", receipt); write_json(staging / "authorization_attestation.json", authority_attestation); write_json(staging / "preflight_root_inventory.json", preflight); write_json(staging/"post_reports_creation_inventory.json",post_reports); write_json(staging / "post_run_root_inventory.json", inventory(root)); write_json(staging / "reports_directory_attestation.json", report_attestation); write_json(staging / "invocation_ledger.json", ledger.data); write_json(staging / "commands.json", commands)
        write_json(staging/"compile_attestation.json",{"source_name":B.PROBE_NAME,"source_sha256":sha256_file(staging/"compiled"/B.PROBE_NAME),"ex5_name":compiled.ex5.name,"ex5_sha256":sha256_file(staging/"compiled"/compiled.ex5.name),"metaeditor_version":compiled.version,"compile_log_sha256":sha256_file(staging/"compiled"/"compile.log")}); write_json(staging/"ex5_identity_attestation.json",ex5_checks)
        write_json(staging/"searched_location_inventory.json",{"selected_sources":selected_sources})
        log_rows=[]
        for path in changed_logs(root,preflight):
            rel=path.relative_to(root).as_posix();copy_if_present(path,staging/"logs"/rel);log_rows.append({"source_relative":rel,"size_bytes":path.stat().st_size,"sha256":sha256_file(path)})
        write_json(staging/"logs"/"log_inventory.json",{"logs":log_rows})
        import analyze_a1_xau_r6_native_spread_provenance_probe as A
        result = A.build_packet(staging); write_g2_wrapper(staging,result)
        verification_context={"authorization_attestation":authority_attestation,"metadata_receipt":receipt,"root":root}
        write_json(staging/"packet_verification.json",semantic_verify_packet(staging,reports_root/".np1_g2_semantic_verify",verification_context))
        _manifest(staging,"a1_xau_r6_np1_g2_complete_manifest_v1"); before={p.relative_to(staging).as_posix():sha256_file(p) for p in staging.rglob("*") if p.is_file()}; verify_manifest(staging); after={p.relative_to(staging).as_posix():sha256_file(p) for p in staging.rglob("*") if p.is_file()};
        if before!=after: raise RuntimeError("read-only semantic verification mutated packet")
        staging.rename(complete)
        return complete
    except BaseException as exc:
        if not ledger_path.exists(): write_json(ledger_path, {"metaeditor_compilations":0,"tester_runs":[],"last_authorized_command_reached":"preflight"})
        preserve_stop_packet(stop=stop, root=root, ledger=ledger_path, preflight=preflight, reports_attestation=report_attestation, commands=commands, run_ids=invoked, error=exc, compile_workspace=workspace, metadata_receipt=metadata_receipt, partial_staging=staging, authorization_attestation=authority_attestation, post_reports_inventory=post_reports)
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
