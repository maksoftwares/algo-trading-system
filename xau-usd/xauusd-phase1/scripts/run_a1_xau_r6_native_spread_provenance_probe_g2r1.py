"""Future review-gated NP1-G2R1 privacy-safe runner with automatic stop packets.

NP1-G2A12 is repository-only. This module cannot execute unless a later exact
review artifact activates the reserved budget.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

import build_a1_xau_r6_native_spread_provenance_probe_g2r1 as B
import run_a1_xau_r6_native_spread_provenance_probe as G1


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_REPORTS_ROOT = ROOT / "outputs" / "reports"
NEW_ROOT = Path(r"C:\MT5A1NP1SpreadProvenanceCleanG2R1")
METADATA_SOURCE_ROOT = Path(r"C:\MT5A1NP1SpreadProvenanceClean")
QUARANTINED_ROOTS = (
    METADATA_SOURCE_ROOT,
    Path(r"C:\MT5A1M5MomentumBacktest"),
    Path(r"C:\MT5A1NP1SpreadProvenanceCleanG2"),
)
ACCOUNT_SELECTOR = Path(r"C:\MT5A1NP1Secrets\A1_XAU_NP1_G2R1_ACCOUNT_SELECTOR_V1.json")
MARKER = ".a1_xau_np1_spread_probe_g2r1_only"
MARKER_BYTES = b"NP1 SPREAD PROBE G2R1 ONLY\n"
RUN_IDS = ("warmup", "probe1", "probe2")
ACTIVATION = "NP1-G2R1_EXACT_COMMIT_REVIEWED_AUTHORIZATION"
COMPLETE_NAME = "A1_XAU_R6_NATIVE_SPREAD_PROVENANCE_PROBE_G2R1_20260713"
STOP_NAME = "A1_XAU_R6_NATIVE_SPREAD_PROVENANCE_PROBE_G2R1_STOP_20260713"
REPORT_SENTINEL = ".np1_g2r1_reports_write_test"
ALLOWED_METADATA = ("Config/accounts.dat", "Config/servers.dat")
METADATA_IDENTITIES = {
    "Config/accounts.dat": (15935, "d9b8e87ef41d4a498a34bd7ae2b37b2fea769c820311fdeef0488e0387976b8a"),
    "Config/servers.dat": (326364, "e2cda2f1548c92b168894d74f0959957839a89d8b992be1afc3b3062dfaefb66"),
}
CANONICAL_REPORTS_RELATIVE = "xau-usd/xauusd-phase1/outputs/reports"
ACCOUNT_ASSERTIONS = {"account_login_present", "account_login_matches", "account_server_present", "account_server_matches"}
WARMUP_ASSERTIONS = {"environment", "run_id", "zero_files", "positions_zero", "orders_zero", "warmup_only", *ACCOUNT_ASSERTIONS}
OFFICIAL_ASSERTIONS = {"environment", "run_id", "zero_files", "positions_zero", "orders_zero", "h1_export", "h4_export", "d1_export", "interfaces_export", "ticks_20250618", "ticks_20250929", "ticks_20251117", "ticks_20260414", *ACCOUNT_ASSERTIONS}
G2_README = "# NP1-G2R1 Native Spread Provenance Probe\n\nStatus: `NP1_G2R1_DIAGNOSTIC_COMPLETE`. Diagnostic only.\n"
G2_VALIDATION = "# NP1-G2R1 Validation\n\nLocked privacy-safe implementation and evidence verification passed.\n"
COMMAND_FIELDS = {"command","exit_code","stdout_base64","stderr_base64","stdout_sha256","stderr_sha256"}
BAR_COLUMNS = ["schema_version","timeframe","open_time_broker","open","high","low","close","tick_volume","spread","real_volume","copyrates_return","copyrates_error"]
INTERFACE_COLUMNS = ["schema_version","timeframe","open_time_broker","open","high","low","close","tick_volume","real_volume","copyrates_spread","copyspread_spread","ispread_spread","copyspread_return","copyspread_error","ibarshift","ispread_error","point","digits"]
TICK_COLUMNS = ["schema_version","broker_day","time_msc","time","bid","ask","last","volume","volume_real","flags","raw_ask_minus_bid","raw_spread_points","negative_spread_boolean","quote_sides_positive","copyticks_return","copyticks_error"]
NATIVE_REPORT_REQUIRED_FIELDS = (
    "Expert", "Symbol", "Period", "History Quality", "Company", "Currency",
    "Initial Deposit", "Leverage", "Bars", "Ticks", "Total Trades", "Total Deals",
)
TICK_DAYS = {"ticks_20250618.tsv":"2025.06.18","ticks_20250929.tsv":"2025.09.29","ticks_20251117.tsv":"2025.11.17","ticks_20260414.tsv":"2026.04.14"}
FORBIDDEN_ROOT_SURFACES = (
    "Bases", "bases", "history", "Tester/bases", "Tester/cache", "MQL5/Files",
    "Logs", "Reports", "Profiles",
)
SELECTOR_FIELDS = {"schema_version", "login", "platform_server", "expected_account_server"}
REDACTED_LOGIN = "<REDACTED_LOGIN_MATCHED>"
REDACTED_PLATFORM_SERVER = "<REDACTED_PLATFORM_SERVER>"
REDACTED_ACCOUNT_SERVER = "<REDACTED_ACCOUNT_SERVER>"
PATH_REDACTION_TOKENS = ("REDACTED_LOGIN", "REDACTED_PLATFORM_SERVER", "REDACTED_ACCOUNT_SERVER")
CommandRunner = Callable[[Sequence[str], Path, int], object]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_account_selector(path: Path, root: Path = NEW_ROOT) -> dict[str, str]:
    expected = ACCOUNT_SELECTOR.absolute()
    if path.absolute() != expected or not path.is_file():
        raise PermissionError("exact external account selector required")
    for candidate in (path, *path.parents):
        if not candidate.exists():
            continue
        stat = candidate.lstat()
        if candidate.is_symlink() or (getattr(stat, "st_file_attributes", 0) & 0x400):
            raise PermissionError("account selector or ancestor link/reparse rejected")
    if path.lstat().st_nlink != 1:
        raise PermissionError("account selector link/reparse/hard-link rejected")
    resolved = path.resolve()
    for forbidden in (ROOT.resolve(), root.resolve()):
        try:
            resolved.relative_to(forbidden)
        except ValueError:
            pass
        else:
            raise PermissionError("account selector must remain outside repo and execution root")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PermissionError("account selector is not exact UTF-8 JSON") from exc
    if not isinstance(payload, dict) or set(payload) != SELECTOR_FIELDS or any(not isinstance(value, str) for value in payload.values()):
        raise PermissionError("account selector closed schema mismatch")
    if payload["schema_version"] != "a1_xau_np1_g2r1_account_selector_v1":
        raise PermissionError("account selector schema version mismatch")
    if re.fullmatch(r"[1-9][0-9]*", payload["login"]) is None:
        raise PermissionError("account selector login must be a positive decimal string")
    for key in ("platform_server", "expected_account_server"):
        value = payload[key]
        if (
            not value.strip()
            or value != value.strip()
            or len(value) > 256
            or any(unicodedata.category(char).startswith("C") for char in value)
        ):
            raise PermissionError("account selector server value invalid")
    return payload


def selector_attestation(selector: dict[str, str]) -> dict[str, Any]:
    return {
        "schema_version": "a1_xau_np1_g2r1_account_selector_attestation_v1",
        "selector_path": str(ACCOUNT_SELECTOR),
        "selector_committed": False,
        "password_present": False,
        "login_present": True,
        "common_tester_login_equal": True,
        "platform_server_present": True,
        "expected_account_server_present": True,
        "raw_values_committed": False,
    }


def sensitive_values(selector: dict[str, str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys((selector["login"], selector["platform_server"], selector["expected_account_server"])))


def _value_tokens(selector: dict[str, str]) -> tuple[tuple[str, str, str], ...]:
    return tuple(zip(sensitive_values(selector), (REDACTED_LOGIN, REDACTED_PLATFORM_SERVER, REDACTED_ACCOUNT_SERVER), PATH_REDACTION_TOKENS))


def _encoded_variants(value: str) -> tuple[bytes, ...]:
    texts = tuple(dict.fromkeys((value, value.lower(), value.upper(), value.casefold())))
    return tuple(dict.fromkeys(text.encode(encoding) for text in texts for encoding in ("utf-8", "utf-16-le", "utf-16-be")))


def assert_bytes_redacted(raw: bytes, selector: dict[str, str], *, label: str) -> None:
    for value in sensitive_values(selector):
        if any(token and token in raw for token in _encoded_variants(value)):
            raise RuntimeError(f"sensitive selector value remains in {label}")


def sanitize_runtime_bytes(raw: bytes, selector: dict[str, str]) -> bytes:
    sanitized = raw
    for value, text_token, _ in _value_tokens(selector):
        for encoding in ("utf-8", "utf-16-le", "utf-16-be"):
            replacement = text_token.encode(encoding)
            for variant in tuple(dict.fromkeys((value, value.lower(), value.upper(), value.casefold()))):
                sanitized = sanitized.replace(variant.encode(encoding), replacement)
    assert_bytes_redacted(sanitized, selector, label="sanitized runtime bytes")
    return sanitized


def sanitize_projection(value: Any, selector: dict[str, str]) -> Any:
    if isinstance(value, str):
        return sanitize_runtime_text(value, selector)
    if isinstance(value, list):
        return [sanitize_projection(item, selector) for item in value]
    if isinstance(value, tuple):
        return [sanitize_projection(item, selector) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_projection(item, selector) for key, item in value.items()}
    return value


def assert_relative_path_redacted(relative: str, selector: dict[str, str]) -> None:
    if relative.startswith("/") or "\\" in relative or any(part in {"", ".", ".."} for part in relative.split("/")):
        raise RuntimeError("packet relative path grammar mismatch")
    if any(re.search(re.escape(value), relative, flags=re.I) for value in sensitive_values(selector)):
        raise RuntimeError("sensitive selector value remains in packet pathname")


def sanitize_relative_path(relative: str, selector: dict[str, str]) -> str:
    parts = []
    for component in relative.replace("\\", "/").split("/"):
        if component in {"", ".", ".."}:
            raise RuntimeError("unsafe runtime-derived relative path")
        for value, _, path_token in _value_tokens(selector):
            component = re.sub(re.escape(value), path_token, component, flags=re.I)
        parts.append(component)
    sanitized = "/".join(parts)
    assert_relative_path_redacted(sanitized, selector)
    return sanitized


def sanitize_command_record(record: dict[str, Any], selector: dict[str, str]) -> dict[str, Any]:
    if set(record) != COMMAND_FIELDS or any(not isinstance(part, str) for part in record.get("command", [])):
        raise RuntimeError("command record closed schema mismatch")
    if any(re.search(re.escape(value), part, flags=re.I) for part in record["command"] for value in sensitive_values(selector)):
        raise RuntimeError("sensitive selector value in command array")
    sanitized = dict(record)
    for stream in ("stdout", "stderr"):
        try:
            decoded = base64.b64decode(record[f"{stream}_base64"], validate=True)
        except Exception as exc:
            raise RuntimeError("command stream base64 mismatch") from exc
        if hashlib.sha256(decoded).hexdigest() != record[f"{stream}_sha256"]:
            raise RuntimeError("command stream hash mismatch")
        safe = sanitize_runtime_bytes(decoded, selector)
        sanitized[f"{stream}_base64"] = base64.b64encode(safe).decode("ascii")
        sanitized[f"{stream}_sha256"] = hashlib.sha256(safe).hexdigest()
    return sanitized


def sanitize_command_records(commands: list[dict[str, Any]], selector: dict[str, str]) -> list[dict[str, Any]]:
    return [sanitize_command_record(row, selector) for row in commands]


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
    if set(receipt) != {"mode", "copied"} or receipt.get("mode") != "COPIED_ALLOWLIST" or not isinstance(receipt.get("copied"), list):
        raise RuntimeError("metadata receipt closed schema mismatch")
    copied = receipt.get("copied", [])
    if len(copied) != 2: raise RuntimeError("exact two-file metadata copy required")
    row_fields={"source_path","source_relative","destination_relative","size_bytes","sha256"}
    if any(not isinstance(row,dict) or set(row)!=row_fields for row in copied):
        raise RuntimeError("metadata receipt row closed schema mismatch")
    paths = {row.get("destination_relative") for row in copied}
    if len(paths) != len(copied): raise RuntimeError("duplicate metadata receipt entry")
    sources = {row.get("source_path") for row in copied}
    if len(sources) != len(copied): raise RuntimeError("duplicate metadata receipt source")
    if paths != set(ALLOWED_METADATA):
        raise RuntimeError("unexpected copied Config file")
    for row in copied:
        relative = row["destination_relative"]
        destination = root / relative
        source = Path(row["source_path"])
        if row["source_relative"] != relative: raise RuntimeError("metadata source/destination relative identity mismatch")
        if any(p.is_symlink() or (getattr(p.stat(),"st_file_attributes",0)&0x400) or p.stat().st_nlink != 1 for p in (source,destination)):
            raise RuntimeError("metadata symlink/reparse/hard-link rejected")
        if source.resolve().parent.parent != METADATA_SOURCE_ROOT.resolve():
            raise RuntimeError("metadata source is not the exact approved G1 root")
        if relative not in ALLOWED_METADATA or not destination.is_file():
            raise RuntimeError("metadata receipt destination mismatch")
        if source.name != destination.name or source.parent.name != "Config":
            raise RuntimeError("metadata source/destination identity mismatch")
        if (row["size_bytes"], row["sha256"]) != METADATA_IDENTITIES[relative]:
            raise RuntimeError("metadata receipt does not match the approved identity")
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
    if list(reports.glob("np1_g2r1_*")):
        raise RuntimeError("stale G2 report exists before first invocation")
    attestation = {"reports_path": str(reports), "created_by_runner": True, "sentinel_sha256": sentinel_hash, "sentinel_read_back": True, "sentinel_deleted": True, "writable": os.access(reports, os.W_OK)}
    if not attestation["writable"]:
        raise RuntimeError("Reports directory is not writable")
    return before, inventory(root), attestation


def render_ini(run_id: str, selector: dict[str, str]) -> str:
    if run_id not in RUN_IDS:
        raise ValueError(run_id)
    base = G1.render_ini(run_id).replace("A1XauR6NativeSpreadProvenanceProbe.ex5", f"{Path(B.PROBE_NAME).stem}.ex5").replace("np1_g1_", "np1_g2r1_")
    base = base.replace("[Tester]\n", f"[Common]\nLogin={selector['login']}\nServer={selector['platform_server']}\n\n[Tester]\nLogin={selector['login']}\n", 1)
    base = base.replace(f"InpWarmup={'true' if run_id == 'warmup' else 'false'}\n", f"InpWarmup={'true' if run_id == 'warmup' else 'false'}\nInpExpectedLogin={selector['login']}\nInpExpectedAccountServer={selector['expected_account_server']}\n", 1)
    validate_raw_ini(base, selector)
    return base


def parse_ini(text: str) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line: continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            if current in sections: raise RuntimeError("duplicate INI section")
            sections[current] = {}
            continue
        if current is None or "=" not in line: raise RuntimeError("invalid INI grammar")
        key, value = line.split("=", 1)
        if key in sections[current]: raise RuntimeError("duplicate INI key")
        sections[current][key] = value
    return sections


def validate_raw_ini(text: str, selector: dict[str, str]) -> dict[str, dict[str, str]]:
    sections = parse_ini(text)
    if "Password" in text or "/login:" in text.lower(): raise RuntimeError("password or command-line login forbidden")
    if sections.get("Common", {}).get("Login") != selector["login"]: raise RuntimeError("missing or mismatched Common Login")
    if sections.get("Common", {}).get("Server") != selector["platform_server"]: raise RuntimeError("missing or mismatched Common Server")
    if sections.get("Tester", {}).get("Login") != selector["login"]: raise RuntimeError("missing or mismatched Tester Login")
    if "Server" in sections.get("Tester", {}): raise RuntimeError("Tester Server key forbidden")
    inputs = sections.get("TesterInputs", {})
    if inputs.get("InpExpectedLogin") != selector["login"] or inputs.get("InpExpectedAccountServer") != selector["expected_account_server"]:
        raise RuntimeError("execution-only EA account inputs mismatch")
    return sections


def render_redacted_ini(raw: str, selector: dict[str, str]) -> str:
    validate_raw_ini(raw, selector)
    redacted = raw.replace(selector["login"], REDACTED_LOGIN)
    redacted = redacted.replace(selector["platform_server"], REDACTED_PLATFORM_SERVER)
    redacted = redacted.replace(selector["expected_account_server"], REDACTED_ACCOUNT_SERVER)
    if any(value in redacted for value in sensitive_values(selector)): raise RuntimeError("INI redaction failed")
    return redacted


def expected_report(root: Path, run_id: str) -> Path:
    return root / "Reports" / f"np1_g2r1_{run_id}.htm"


def validate_fresh_report(path: Path, not_before_ns: int, parser: Callable[[Path], Any]) -> Any:
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError("fresh nonempty report missing")
    if path.stat().st_mtime_ns + 2_000_000_000 < not_before_ns:
        raise RuntimeError("stale report rejected")
    return parser(path)


def native_report_fields(path: Path) -> dict[str,str]:
    import analyze_a1_xau_r6_native_spread_provenance_probe as A
    raw=path.read_bytes(); text=raw.decode("utf-16") if raw.startswith((b"\xff\xfe",b"\xfe\xff")) else raw.decode("utf-8-sig")
    cells=A.Cells(); cells.feed(text)
    fields: dict[str,str]={}
    for index,cell in enumerate(cells.cells):
        if not cell.endswith(":"): continue
        label=cell[:-1].strip()
        if label in fields: raise RuntimeError(f"duplicate native report label: {label}")
        if index+1>=len(cells.cells): raise RuntimeError(f"native report value missing: {label}")
        fields[label]=cells.cells[index+1].strip()
    return fields


def validate_effective_report(path: Path) -> dict[str,str]:
    fields=native_report_fields(path)
    required=set(NATIVE_REPORT_REQUIRED_FIELDS)
    if not required<=set(fields): raise RuntimeError(f"native report effective-setting fields missing: {sorted(required-set(fields))}")
    if Path(fields["Expert"].split()[0]).stem!="A1XauR6NativeSpreadProvenanceProbeG2R1": raise RuntimeError("native report expert mismatch")
    if fields["Symbol"].split()[0]!="XAUUSD": raise RuntimeError("native report symbol mismatch")
    if fields["Period"]!="M5 (2015.06.01 - 2026.07.01)": raise RuntimeError("native report period/date mismatch")
    deposit=float(re.sub(r"[^0-9.]","",fields["Initial Deposit"]))
    if abs(deposit-10000.0)>1e-9 or fields["Currency"]!="USD": raise RuntimeError("native report deposit/currency mismatch")
    quality=re.fullmatch(r"([1-9][0-9]*(?:\.[0-9]+)?)%\s+real ticks",fields["History Quality"],re.I)
    if quality is None: raise RuntimeError("native report real-tick history quality mismatch")
    float(quality.group(1))
    if re.sub(r"\s","",fields["Leverage"])!="1:50": raise RuntimeError("native report leverage mismatch")
    def integer(name: str) -> int: return int(re.sub(r"[^0-9]","",fields[name]))
    if integer("Bars")<=0 or integer("Ticks")<=0 or integer("Total Trades")!=0 or integer("Total Deals")!=0: raise RuntimeError("native report bars/ticks/zero-action mismatch")
    if "Model" in fields and "real tick" not in fields["Model"].lower(): raise RuntimeError("native report model mismatch")
    if fields["Company"]!="Capital Com Mena Securities Trading L.L.C": raise RuntimeError("native report company mismatch")
    return fields


def decode_runtime_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig", errors="replace")


def sanitize_runtime_text(text: str, selector: dict[str, str]) -> str:
    for value, token, _ in _value_tokens(selector):
        text = re.sub(re.escape(value), token, text, flags=re.I)
    if any(re.search(re.escape(value), text, flags=re.I) for value in sensitive_values(selector)):
        raise RuntimeError("runtime text redaction failed")
    return text


def write_sanitized_runtime_file(source: Path, destination: Path, selector: dict[str, str]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(sanitize_runtime_text(decode_runtime_text(source), selector), encoding="utf-8", newline="\n")


def assert_packet_redacted(packet: Path, selector: dict[str, str]) -> None:
    forbidden_names = {ACCOUNT_SELECTOR.name.lower(), "accounts.dat", "servers.dat"}
    for path in sorted(packet.rglob("*"), key=lambda candidate: candidate.relative_to(packet).as_posix()):
        relative = path.relative_to(packet).as_posix()
        assert_relative_path_redacted(relative, selector)
        if not path.is_file():
            continue
        if path.name.lower() in forbidden_names or relative == "tester.ini" or relative.endswith("/tester.ini") or relative == "native_report.htm" or relative.endswith("/native_report.htm"):
            raise RuntimeError("raw account-bearing artifact committed")
        raw = path.read_bytes()
        assert_bytes_redacted(raw, selector, label="packet")
        if b"Password=" in raw or b"/login:" in raw.lower(): raise RuntimeError("credential material remains in packet")
        if path.name == "commands.json":
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, list):
                raise RuntimeError("command records must be a list")
            for row in payload:
                if not isinstance(row, dict) or set(row) != COMMAND_FIELDS:
                    raise RuntimeError("command record closed schema mismatch")
                for stream in ("stdout", "stderr"):
                    try:
                        decoded = base64.b64decode(row[f"{stream}_base64"], validate=True)
                    except Exception as exc:
                        raise RuntimeError("command stream base64 mismatch") from exc
                    if hashlib.sha256(decoded).hexdigest() != row[f"{stream}_sha256"]:
                        raise RuntimeError("command stream hash mismatch")
                    assert_bytes_redacted(decoded, selector, label=f"decoded command {stream}")
        if relative == "manifest.json":
            payload = json.loads(raw.decode("utf-8"))
            for row in payload.get("artifacts", []):
                if not isinstance(row, dict) or not isinstance(row.get("relative_path"), str):
                    raise RuntimeError("manifest artifact schema mismatch")
                assert_relative_path_redacted(row["relative_path"], selector)


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


def compile_once_g2r1(root: Path, editor: Path, *, runner: CommandRunner = G1.command_runner, version_reader: Callable[[Path], str] = G1.executable_version) -> G1.CompileResult:
    experts = root / "MQL5" / "Experts"
    experts.mkdir(parents=True, exist_ok=True)
    source = experts / B.PROBE_NAME
    B.build_probe(source)
    B.verify_source(source)
    ex5, log = source.with_suffix(".ex5"), root / "compile.log"
    if ex5.exists() or log.exists(): raise RuntimeError("clean-root compile outputs already exist")
    command = [str(editor), f"/compile:{source}", f"/log:{log}"]
    completed = runner(command, root, 180)
    if int(getattr(completed, "returncode", 1)) not in {0, 1} or not ex5.is_file() or not log.is_file():
        raise RuntimeError("single MetaEditor compilation failed")
    raw = log.read_bytes()
    text = raw.decode("utf-16") if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else raw.decode("utf-8-sig", errors="replace")
    if re.search(r"\b0\s+errors?\b", text, re.I) is None or re.search(r"\b0\s+warnings?\b", text, re.I) is None:
        raise RuntimeError("compile log is not zero-error/zero-warning")
    version = version_reader(editor)
    if version != G1.EXPECTED_VERSION: raise RuntimeError("MetaEditor version mismatch")
    log.write_text(f"MetaEditor executable version: {version}\n{text.strip()}\n", encoding="utf-8", newline="\n")
    return G1.CompileResult(source, ex5, log, sha256_file(source), sha256_file(ex5), version, G1.record(command, completed))


def assert_mutually_exclusive(reports_root: Path) -> tuple[Path, Path]:
    complete, stop = reports_root / COMPLETE_NAME, reports_root / STOP_NAME
    if complete.exists() or stop.exists():
        raise RuntimeError("fixed complete/stop output root already exists")
    return complete, stop


def copy_if_present(source: Path, destination: Path) -> None:
    if source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, destination)


def collect_exact_outputs(root: Path, run_id: str, destination: Path, not_before_ns: int, parser: Callable[[Path], Any], selector: dict[str, str]) -> list[dict[str, Any]]:
    destination.mkdir(parents=True, exist_ok=False)
    ini=root / "Config" / f"np1_g2r1_{run_id}.ini"
    raw_ini = ini.read_text(encoding="utf-8") if ini.is_file() else ""
    if raw_ini != render_ini(run_id, selector): raise RuntimeError("executed G2R1 INI missing or not exact")
    redacted_ini = destination / "tester.redacted.ini"
    redacted_ini.write_text(render_redacted_ini(raw_ini, selector), encoding="utf-8", newline="\n")
    selected=[{"kind":"tester_redacted_ini","source":sanitize_runtime_text(str(ini), selector),"sha256":sha256_file(redacted_ini),"size_bytes":redacted_ini.stat().st_size}]
    report = expected_report(root, run_id)
    validate_fresh_report(report, not_before_ns, parser)
    validate_effective_report(report)
    sanitized_report = destination / "native_report.redacted.htm"
    write_sanitized_runtime_file(report, sanitized_report, selector)
    selected.append({"kind":"native_report_redacted","source":sanitize_runtime_text(str(report), selector),"sha256":sha256_file(sanitized_report),"size_bytes":sanitized_report.stat().st_size,"fresh_not_before_ns":not_before_ns})
    names = G1.WARMUP_NAMES if run_id == "warmup" else G1.OFFICIAL_NAMES
    for name in names:
        matches = list((root / "Tester").glob(f"Agent-*/MQL5/Files/np1_g2r1_{run_id}_{name}"))
        if len(matches) != 1:
            raise RuntimeError(f"expected exactly one {run_id} output {name}; found {len(matches)}")
        shutil.copyfile(matches[0], destination / name)
        selected.append({"kind":name,"source":sanitize_runtime_text(str(matches[0]), selector),"sha256":sha256_file(matches[0]),"size_bytes":matches[0].stat().st_size})
    return selected


def changed_logs(root: Path, preflight: dict[str, Any]) -> list[Path]:
    prior={row["relative_path"]:(row.get("size_bytes"),row.get("sha256")) for row in preflight.get("entries",[]) if row.get("kind")=="file"}
    candidates=[*(root/"Logs").glob("*.log"),*(root/"Tester"/"logs").glob("*.log"),*(root/"Tester").glob("Agent-*/logs/*.log")]
    return [p for p in candidates if prior.get(p.relative_to(root).as_posix())!=(p.stat().st_size,sha256_file(p))]


def write_g2_wrapper(packet: Path, result: dict[str, Any]) -> None:
    import analyze_a1_xau_r6_native_spread_provenance_probe as A
    wrapped=dict(result); wrapped.update(status="NP1_G2R1_DIAGNOSTIC_COMPLETE",canonical_np1c_authorized=False,r6_census_authorized=False,pnl_authorized=False,profitability_authorized=False,target_exit_authorized=False,mfe_mae_authorized=False,h4_portfolio_authorized=False,demo_live_attach_authorized=False,preset_profile_arming_authorized=False,broker_action_authorized=False,btc_work_authorized=False,deployment_authorized=False); A.write_json(packet/"result.json",wrapped)
    (packet/"README.md").write_text(G2_README,encoding="utf-8",newline="\n")
    (packet/"test_validation.md").write_text(G2_VALIDATION,encoding="utf-8",newline="\n")


def read_tsv_exact(path: Path, columns: list[str]) -> list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as handle:
        reader=csv.DictReader(handle,delimiter="\t")
        if reader.fieldnames!=columns: raise RuntimeError(f"exact TSV schema mismatch: {path.name}")
        return list(reader)


def assert_exact_assertions(packet: Path) -> None:
    for run_id in RUN_IDS:
        rows=read_tsv_exact(packet/"runs"/run_id/"assertions.tsv",["assertion_id","passed","observed","expected"])
        expected=WARMUP_ASSERTIONS if run_id=="warmup" else OFFICIAL_ASSERTIONS
        ids=[row.get("assertion_id") for row in rows]
        if set(ids)!=expected or len(ids)!=len(expected) or any(row.get("passed")!="true" for row in rows):
            raise RuntimeError(f"exact {run_id} assertion set mismatch")
        expected_values={value:("pass","pass") for value in expected}; expected_values.update(positions_zero=("0","0"),orders_zero=("0","0"),run_id=(("warmup","warmup") if run_id=="warmup" else ("official","official")))
        if run_id=="warmup": expected_values["warmup_only"]=("true","true")
        if any((row["observed"],row["expected"])!=expected_values[row["assertion_id"]] for row in rows): raise RuntimeError(f"{run_id} assertion observed/expected mismatch")


def validate_command_records(commands: list[dict[str,Any]], root: Path, selector: dict[str, str]) -> None:
    if len(commands)!=4 or any(set(row)!=COMMAND_FIELDS for row in commands): raise RuntimeError("command record closed schema mismatch")
    for row in commands:
        for stream in ("stdout","stderr"):
            try: decoded=base64.b64decode(row[f"{stream}_base64"],validate=True)
            except Exception as exc: raise RuntimeError("command stream base64 mismatch") from exc
            if hashlib.sha256(decoded).hexdigest()!=row[f"{stream}_sha256"]: raise RuntimeError("command stream hash mismatch")
            assert_bytes_redacted(decoded, selector, label=f"decoded command {stream}")
    compile_expected=[str((root/"MetaEditor64.exe").resolve()),f"/compile:{(root/'MQL5'/'Experts'/B.PROBE_NAME).resolve()}",f"/log:{(root/'compile.log').resolve()}"]
    if commands[0]["command"]!=compile_expected or int(commands[0]["exit_code"]) not in {0,1}: raise RuntimeError("compile command/exit semantics mismatch")
    for run_id,row in zip(RUN_IDS,commands[1:]):
        expected=[str((root/"terminal64.exe").resolve()),"/portable",f"/config:{(root/'Config'/f'np1_g2r1_{run_id}.ini').resolve()}"]
        if row["command"]!=expected or int(row["exit_code"])!=0: raise RuntimeError("tester command/exit semantics mismatch")
        if any("/login:" in part.lower() for part in row["command"]): raise RuntimeError("command-line login forbidden")


def validate_native_exports(packet: Path) -> None:
    def iso(value: str) -> datetime:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",value) is None: raise RuntimeError("native ISO timestamp grammar mismatch")
        try: return datetime.strptime(value,"%Y-%m-%dT%H:%M:%S")
        except ValueError as exc: raise RuntimeError("invalid native ISO timestamp") from exc
    history_start=datetime(2015,6,1); history_end=datetime(2026,7,1)
    run=packet/"runs"/"probe1"
    for timeframe in ("H1","H4","D1"):
        rows=read_tsv_exact(run/f"{timeframe.lower()}_bars.tsv",BAR_COLUMNS)
        if not rows: raise RuntimeError("empty bar export")
        stamps=[iso(row["open_time_broker"]) for row in rows]
        if stamps!=sorted(set(stamps)): raise RuntimeError("bar timestamps not unique/monotonic")
        if any(row["schema_version"]!="a1_xau_np1_g1_bar_v1" or row["timeframe"]!=timeframe or int(row["copyrates_error"])!=0 or int(row["copyrates_return"])!=len(rows) for row in rows) or any(not history_start<=stamp<history_end for stamp in stamps): raise RuntimeError("bar native return/error/range mismatch")
    interfaces=read_tsv_exact(run/"bar_spread_interfaces.tsv",INTERFACE_COLUMNS)
    if not interfaces: raise RuntimeError("empty interface export")
    interface_times=[iso(row["open_time_broker"]) for row in interfaces]
    keys=[(row["timeframe"],stamp) for row,stamp in zip(interfaces,interface_times)]
    if len(keys)!=len(set(keys)) or any([stamp for row,stamp in zip(interfaces,interface_times) if row["timeframe"]==tf]!=sorted(stamp for row,stamp in zip(interfaces,interface_times) if row["timeframe"]==tf) for tf in ("H1","H4","D1")): raise RuntimeError("interface timestamps not unique/monotonic")
    if any(row["schema_version"]!="a1_xau_np1_g1_interface_v1" or row["timeframe"] not in {"H1","H4","D1"} or int(row["copyspread_return"])!=1 or int(row["copyspread_error"])!=0 or int(row["ibarshift"])<0 or int(row["ispread_error"])!=0 for row in interfaces): raise RuntimeError("interface native return/error mismatch")
    if any(re.fullmatch(r"\d+",row["digits"]) is None for row in interfaces): raise RuntimeError("invalid native digits grammar")
    points={float(row["point"]) for row in interfaces}; digits={int(row["digits"]) for row in interfaces}
    if len(points)!=1 or len(digits)!=1: raise RuntimeError("mixed native point/digits identity")
    point=next(iter(points)); digit=next(iter(digits))
    if not (math.isfinite(point) and point>0 and digit>=0 and abs(point-(10.0**-digit))<=max(1e-12,point*1e-10)): raise RuntimeError("invalid native point/digits identity")
    for filename,day in TICK_DAYS.items():
        rows=read_tsv_exact(run/filename,TICK_COLUMNS)
        if not rows: raise RuntimeError("empty tick export")
        times=[int(row["time_msc"]) for row in rows]
        if times!=sorted(times): raise RuntimeError("tick timestamps decreasing")
        if re.fullmatch(r"\d{4}\.\d{2}\.\d{2}",day) is None: raise RuntimeError("tick broker-day grammar mismatch")
        day_start=datetime.strptime(day,"%Y.%m.%d"); day_end=day_start+timedelta(days=1)
        for row in rows:
            stamp=iso(row["time"]); msc=int(row["time_msc"])
            if row["schema_version"]!="a1_xau_np1_g1_tick_v1" or row["broker_day"]!=day or not day_start<=stamp<day_end or stamp.strftime("%Y.%m.%d")!=day or msc//1000!=int(stamp.replace(tzinfo=timezone.utc).timestamp()) or int(row["copyticks_error"])!=0 or int(row["copyticks_return"])!=len(rows): raise RuntimeError("tick native return/error/day mismatch")
            bid=float(row["bid"]); ask=float(row["ask"])
            if not (math.isfinite(bid) and math.isfinite(ask)): raise RuntimeError("non-finite tick quote")
            positive=bid>0 and ask>0
            if row["quote_sides_positive"] not in {"true","false"} or (row["quote_sides_positive"]=="true")!=positive: raise RuntimeError("tick quote-side flag mismatch")
            if positive:
                if not row["raw_ask_minus_bid"] or not row["raw_spread_points"] or row["negative_spread_boolean"] not in {"true","false"}: raise RuntimeError("positive tick raw fields missing")
                raw=ask-bid; reported_raw=float(row["raw_ask_minus_bid"]); reported_points=float(row["raw_spread_points"])
                if not (math.isfinite(reported_raw) and math.isfinite(reported_points)) or abs(raw-reported_raw)>1e-8 or (row["negative_spread_boolean"]=="true")!=(raw<0): raise RuntimeError("raw tick arithmetic mismatch")
                if abs(reported_points-(raw/point))>max(1e-8,abs(raw/point)*1e-10): raise RuntimeError("raw tick native-point mismatch")
            elif not (bid<=0 or ask<=0) or any(row[name]!="" for name in ("raw_ask_minus_bid","raw_spread_points","negative_spread_boolean")): raise RuntimeError("unavailable tick raw fields must be empty")
    for run_id in ("probe1","probe2"):
        if any((packet/"runs"/run_id/name).read_bytes()!=(packet/"runs"/"probe1"/name).read_bytes() for name in G1.OFFICIAL_NAMES): raise RuntimeError("official export drift")


def validate_packet_attestations(packet: Path, context: dict[str, Any]) -> list[str]:
    checks=[]
    def load(name: str) -> Any: return json.loads((packet/name).read_text(encoding="utf-8"))
    if load("authorization_attestation.json")!=context["authorization_attestation"]: raise RuntimeError("authorization attestation mismatch")
    checks.append("authorization_and_reviewed_executor")
    if load("account_selector_attestation.json")!=selector_attestation(context["selector"]): raise RuntimeError("account selector attestation mismatch")
    checks.append("external_selector_value_free_attestation")
    if load("metadata_receipt.json")!=context["metadata_receipt"]: raise RuntimeError("metadata receipt packet mismatch")
    receipt=load("metadata_receipt.json")
    if set(receipt)!={"mode","copied"} or receipt["mode"] != "COPIED_ALLOWLIST": raise RuntimeError("metadata receipt packet schema mismatch")
    checks.append("metadata_receipt")
    ledger=load("invocation_ledger.json")
    if ledger!={"metaeditor_compilations":1,"tester_runs":list(RUN_IDS),"last_authorized_command_reached":"probe2"}: raise RuntimeError("invocation ledger mismatch")
    commands=load("commands.json"); validate_command_records(commands,context["root"],context["selector"])
    checks.append("one_compile_three_ordered_runs")
    compiled=load("compile_attestation.json"); source=packet/"compiled"/B.PROBE_NAME; ex5=packet/"compiled"/Path(compiled["ex5_name"]).name; log=packet/"compiled"/"compile.log"
    B.verify_source(source)
    source_manifest=load("compiled/source_manifest.json")
    expected_source_manifest={"schema_version":"a1_xau_r6_native_spread_probe_g2r1_source_manifest_v1","source":B.PROBE_NAME,"source_sha256":sha256_file(source),"zero_action":True,"interfaces":["CopyRates.spread","CopySpread","iSpread","CopyTicksRange.bid_ask"]}
    if source_manifest!=expected_source_manifest: raise RuntimeError("source manifest mismatch")
    source_sha=sha256_file(source); ex5_sha=sha256_file(ex5)
    if compiled!={"source_name":B.PROBE_NAME,"source_sha256":source_sha,"compiled_source_sha256":source_sha,"ex5_name":ex5.name,"ex5_sha256":ex5_sha,"compiled_ex5_sha256":ex5_sha,"metaeditor_version":G1.EXPECTED_VERSION,"compile_log_sha256":sha256_file(log)} or source_manifest["source_sha256"]!=compiled["compiled_source_sha256"]: raise RuntimeError("compiled identity mismatch")
    text=log.read_text(encoding="utf-8",errors="replace")
    if re.search(r"\b0\s+errors?\b",text,re.I) is None or re.search(r"\b0\s+warnings?\b",text,re.I) is None: raise RuntimeError("compile log is not zero-error/zero-warning")
    ex5_checks=load("ex5_identity_attestation.json")
    if [row["stage"] for row in ex5_checks] != ["before_warmup","before_probe1","before_probe2","after_probe2"] or any(row["sha256"]!=compiled["ex5_sha256"] for row in ex5_checks): raise RuntimeError("EX5 continuity mismatch")
    checks.append("deterministic_source_build5833_ex5_continuity")
    selected=load("searched_location_inventory.json")["selected_sources"]
    selector=context["selector"]
    expected_count=sum(2+len(G1.WARMUP_NAMES if rid=="warmup" else G1.OFFICIAL_NAMES) for rid in RUN_IDS)
    if len(selected)!=expected_count: raise RuntimeError("selected source count mismatch")
    for run_id in RUN_IDS:
        expected_names={"tester_redacted_ini","native_report_redacted",*(G1.WARMUP_NAMES if run_id=="warmup" else G1.OFFICIAL_NAMES)}
        rows=[row for row in selected if f"np1_g2r1_{run_id}" in row["source"]]
        if {row["kind"] for row in rows}!=expected_names or len(rows)!=len(expected_names): raise RuntimeError(f"selected source identity mismatch: {run_id}")
        for row in rows:
            expected_fields={"kind","source","sha256","size_bytes","fresh_not_before_ns"} if row["kind"]=="native_report_redacted" else {"kind","source","sha256","size_bytes"}
            if set(row)!=expected_fields: raise RuntimeError("selected source closed schema mismatch")
            name={"tester_redacted_ini":"tester.redacted.ini","native_report_redacted":"native_report.redacted.htm"}.get(row["kind"],row["kind"])
            target=packet/"runs"/run_id/name
            if target.stat().st_size!=row["size_bytes"] or sha256_file(target)!=row["sha256"]: raise RuntimeError("selected source-to-packet mismatch")
            source_text=row["source"]
            if row["kind"]=="tester_redacted_ini": expected_source=sanitize_runtime_text(str((context["root"]/"Config"/f"np1_g2r1_{run_id}.ini").resolve()),selector)
            elif row["kind"]=="native_report_redacted": expected_source=sanitize_runtime_text(str((context["root"]/"Reports"/f"np1_g2r1_{run_id}.htm").resolve()),selector)
            else:
                root_text=sanitize_runtime_text(str(context["root"].resolve()),selector).rstrip("\\/")
                normalized=source_text.replace("\\","/"); prefix=root_text.replace("\\","/")+"/"
                if not normalized.startswith(prefix): raise RuntimeError("selected output source path mismatch")
                relative=tuple(normalized[len(prefix):].split("/"))
                if len(relative)!=5 or relative[0]!="Tester" or not relative[1].startswith("Agent-") or relative!=("Tester",relative[1],"MQL5","Files",f"np1_g2r1_{run_id}_{row['kind']}"): raise RuntimeError("selected output source path mismatch")
                expected_source=source_text
            if row["kind"] in {"tester_redacted_ini","native_report_redacted"} and source_text!=expected_source: raise RuntimeError("selected source path mismatch")
        if (packet/"runs"/run_id/"tester.redacted.ini").read_text(encoding="utf-8")!=render_redacted_ini(render_ini(run_id,selector),selector): raise RuntimeError("packet redacted INI mismatch")
        validate_effective_report(packet/"runs"/run_id/"native_report.redacted.htm")
    checks.append("exact_inis_and_selected_sources")
    preflight={row["relative_path"]:(row.get("size_bytes"),row.get("sha256")) for row in load("preflight_root_inventory.json").get("entries",[]) if row.get("kind")=="file"}
    log_rows=load("logs/log_inventory.json")["logs"]
    if {p.relative_to(packet/"logs").as_posix() for p in (packet/"logs").rglob("*") if p.is_file() and p.name!="log_inventory.json"}!={row["source_relative"] for row in log_rows}: raise RuntimeError("log file-set mismatch")
    for row in log_rows:
        if set(row)!={"source_relative","size_bytes","sha256"} or re.fullmatch(r"(?:Logs/[^/]+\.log|Tester/logs/[^/]+\.log|Tester/Agent-[^/]+/logs/[^/]+\.log)",row["source_relative"]) is None: raise RuntimeError("unauthorized log path/schema")
        copied=packet/"logs"/row["source_relative"]
        if not copied.is_file() or copied.stat().st_size!=row["size_bytes"] or sha256_file(copied)!=row["sha256"] or preflight.get(row["source_relative"])==(row["size_bytes"],row["sha256"]): raise RuntimeError("fresh log reconciliation mismatch")
    checks.append("fresh_logs")
    report_att=load("reports_directory_attestation.json")
    if report_att.get("reports_path")!=str(context["root"]/"Reports") or not all(report_att.get(k) for k in ("created_by_runner","sentinel_read_back","sentinel_deleted","writable")): raise RuntimeError("Reports attestation mismatch")
    pre_obj=load("preflight_root_inventory.json"); reports_obj=load("post_reports_creation_inventory.json"); post_obj=load("post_run_root_inventory.json")
    if any(obj.get("root")!=str(context["root"].resolve()) for obj in (pre_obj,reports_obj,post_obj)): raise RuntimeError("root inventory identity mismatch")
    pre_paths={row["relative_path"] for row in pre_obj.get("entries",[])}; reports_paths={row["relative_path"] for row in reports_obj.get("entries",[])}; post_paths={row["relative_path"] for row in post_obj.get("entries",[])}
    if "Reports" in pre_paths or any(path==surface or path.startswith(surface+"/") for surface in FORBIDDEN_ROOT_SURFACES for path in pre_paths): raise RuntimeError("preflight inventory forbidden surface")
    if not {MARKER,"terminal64.exe","MetaEditor64.exe"}<=pre_paths or "Reports" not in reports_paths or any(REPORT_SENTINEL in path or path.startswith("Reports/np1_g2r1_") for path in reports_paths): raise RuntimeError("pre/post Reports inventory mismatch")
    required_post={*(f"Config/np1_g2r1_{rid}.ini" for rid in RUN_IDS),*(f"Reports/np1_g2r1_{rid}.htm" for rid in RUN_IDS)}
    if not required_post<=post_paths or not any(path.startswith("Tester/Agent-") for path in post_paths): raise RuntimeError("post-run inventory incomplete")
    checks.append("root_and_reports_inventories")
    assert_exact_assertions(packet); validate_native_exports(packet); assert_packet_redacted(packet,context["selector"]); checks.append("exact_zero_action_native_export_and_redaction_contracts")
    return checks


def semantic_verify_packet(packet: Path, scratch: Path, context: dict[str, Any]) -> dict[str, Any]:
    import analyze_a1_xau_r6_native_spread_provenance_probe as A
    original={p.relative_to(packet).as_posix():sha256_file(p) for p in packet.rglob("*") if p.is_file()}
    if scratch.exists(): raise RuntimeError("semantic verification scratch exists")
    scratch.mkdir()
    try:
        shutil.copytree(packet/"compiled",scratch/"compiled"); shutil.copytree(packet/"runs",scratch/"runs")
        for run_id in RUN_IDS:
            run = scratch / "runs" / run_id
            (run / "tester.redacted.ini").rename(run / "tester.ini")
            (run / "native_report.redacted.htm").rename(run / "native_report.htm")
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


def build_scientific_outputs_from_redacted_packet(packet: Path, scratch: Path) -> dict[str, Any]:
    import analyze_a1_xau_r6_native_spread_provenance_probe as A
    if scratch.exists(): raise RuntimeError("scientific build scratch exists")
    scratch.mkdir()
    try:
        shutil.copytree(packet/"compiled",scratch/"compiled"); shutil.copytree(packet/"runs",scratch/"runs")
        for run_id in RUN_IDS:
            run=scratch/"runs"/run_id
            (run/"tester.redacted.ini").rename(run/"tester.ini")
            (run/"native_report.redacted.htm").rename(run/"native_report.htm")
        result=A.build_packet(scratch)
        shutil.copytree(scratch/"analysis",packet/"analysis")
        return result
    finally:
        shutil.rmtree(scratch,ignore_errors=True)


def _manifest(root: Path, schema: str = "a1_xau_r6_np1_g2r1_stop_manifest_v1") -> None:
    artifacts = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.relative_to(root).as_posix() not in {"manifest.json", "manifest.sha256"}:
            artifacts.append({"relative_path": path.relative_to(root).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)})
    write_json(root / "manifest.json", {"schema_version": schema, "artifacts": artifacts})
    (root / "manifest.sha256").write_text(sha256_file(root / "manifest.json") + "\n", encoding="ascii", newline="\n")


def copy_privacy_file(source: Path, destination: Path, selector: dict[str, str]) -> None:
    stat = source.lstat()
    if source.is_symlink() or (getattr(stat, "st_file_attributes", 0) & 0x400) or stat.st_nlink != 1:
        raise RuntimeError("linked optional artifact rejected")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise RuntimeError("privacy projection path collision")
    destination.write_bytes(sanitize_runtime_bytes(source.read_bytes(), selector))


def copy_privacy_projection(source: Path, destination: Path, selector: dict[str, str], omissions: list[dict[str, str]]) -> None:
    forbidden_names = {ACCOUNT_SELECTOR.name.lower(), "accounts.dat", "servers.dat", "tester.ini", "native_report.htm"}
    for path in sorted(source.rglob("*"), key=lambda candidate: candidate.relative_to(source).as_posix()):
        if not path.is_file():
            continue
        raw_relative = path.relative_to(source).as_posix()
        safe_relative = sanitize_relative_path(raw_relative, selector)
        if path.name.lower() in forbidden_names:
            omissions.append({"artifact": safe_relative, "reason": "raw_account_artifact_omitted"})
            continue
        if path.name.lower() in {"manifest.json", "manifest.sha256"}:
            omissions.append({"artifact": safe_relative, "reason": "superseded_projection_manifest_omitted"})
            continue
        try:
            target = destination / safe_relative
            if path.name == "commands.json":
                payload = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(payload, list):
                    raise RuntimeError("command records must be a list")
                write_json(target, sanitize_command_records(payload, selector))
            else:
                copy_privacy_file(path, target, selector)
        except BaseException:
            omissions.append({"artifact": safe_relative, "reason": "unsafe_optional_artifact_omitted"})


def _finalize_stop_stage(stage: Path, stop: Path, selector: dict[str, str]) -> Path:
    assert_packet_redacted(stage, selector)
    _manifest(stage)
    assert_packet_redacted(stage, selector)
    verify_manifest(stage)
    assert_packet_redacted(stage, selector)
    stage.rename(stop)
    return stop


def preserve_stop_packet(
    *, stop: Path, root: Path, ledger: Path, preflight: dict[str, Any], reports_attestation: dict[str, Any],
    commands: list[dict[str, Any]], run_ids: list[str], error: BaseException, compile_workspace: Path | None = None,
    metadata_receipt: Path | None = None, partial_staging: Path | None = None,
    authorization_attestation: dict[str, Any] | None = None, post_reports_inventory: dict[str, Any] | None = None,
    selector: dict[str, str] | None = None,
) -> Path:
    if selector is None: raise RuntimeError("selector required for privacy-safe stop packet")
    stage = stop.with_name(f".{stop.name}.staging")
    if stop.exists() or stage.exists():
        raise RuntimeError("fixed stop or temporary stop staging already exists")
    omissions: list[dict[str, str]] = []
    try:
        try:
            ledger_payload = json.loads(ledger.read_text(encoding="utf-8"))
        except BaseException:
            ledger_payload = {"metaeditor_compilations": 0, "tester_runs": [], "last_authorized_command_reached": "unavailable"}
            omissions.append({"artifact": "invocation_ledger.json", "reason": "unsafe_optional_artifact_omitted"})
        result = {"status": "NP1_G2R1_EVIDENCE_INVALID", "error": sanitize_runtime_text(str(error), selector), "last_authorized_command_reached": ledger_payload.get("last_authorized_command_reached", "unavailable"), "probe1_invoked": "probe1" in run_ids, "probe2_invoked": "probe2" in run_ids, "canonical_np1c_authorized": False, "r6_census_authorized": False, "pnl_authorized": False, "profitability_authorized": False, "target_exit_authorized": False, "mfe_mae_authorized": False, "h4_portfolio_authorized": False, "demo_live_attach_authorized": False, "preset_profile_arming_authorized": False, "deployment_authorized": False, "broker_action_authorized": False, "btc_work_authorized": False}
        stage.mkdir(parents=True, exist_ok=False)
        write_json(stage / "result.json", result)
        (stage / "README.md").write_text("# NP1-G2R1 Automatic Stop Packet\n\nStatus: `NP1_G2R1_EVIDENCE_INVALID`. No automatic retry is authorized.\n", encoding="utf-8", newline="\n")
        write_json(stage / "invocation_ledger.json", sanitize_projection(ledger_payload, selector))
        write_json(stage / "preflight_root_inventory.json", sanitize_projection(preflight, selector))
        write_json(stage / "post_stop_root_inventory.json", sanitize_projection(inventory(root), selector))
        write_json(stage / "reports_directory_attestation.json", sanitize_projection(reports_attestation, selector))
        write_json(stage / "post_reports_creation_inventory.json", sanitize_projection(post_reports_inventory or {}, selector))
        write_json(stage / "authorization_attestation.json", sanitize_projection(authorization_attestation or {}, selector))
        write_json(stage / "account_selector_attestation.json", selector_attestation(selector))
        try:
            safe_commands = sanitize_command_records(commands, selector)
        except BaseException:
            safe_commands = []
            omissions.append({"artifact": "commands.json", "reason": "unsafe_optional_artifact_omitted"})
        write_json(stage / "commands.json", safe_commands)
        if metadata_receipt is not None and metadata_receipt.is_file():
            try:
                write_json(stage / "metadata_receipt.json", sanitize_projection(json.loads(metadata_receipt.read_text(encoding="utf-8")), selector))
            except BaseException:
                omissions.append({"artifact": "metadata_receipt.json", "reason": "unsafe_optional_artifact_omitted"})
        searched: list[dict[str, Any]] = []
        for run_id in run_ids:
            run_dir = stage / "runs" / run_id
            raw_ini = root / "Config" / f"np1_g2r1_{run_id}.ini"
            if raw_ini.is_file():
                try:
                    redacted = render_redacted_ini(raw_ini.read_text(encoding="utf-8"), selector)
                    (run_dir / "tester.redacted.ini").parent.mkdir(parents=True, exist_ok=True)
                    (run_dir / "tester.redacted.ini").write_text(redacted, encoding="utf-8", newline="\n")
                except BaseException:
                    omissions.append({"artifact": f"runs/{run_id}/tester.redacted.ini", "reason": "unsafe_optional_artifact_omitted"})
            report = expected_report(root, run_id)
            if report.is_file():
                try:
                    validate_effective_report(report)
                    write_sanitized_runtime_file(report, run_dir / "native_report.redacted.htm", selector)
                except BaseException:
                    omissions.append({"artifact": f"runs/{run_id}/native_report.redacted.htm", "reason": "unsafe_optional_artifact_omitted"})
            for files_dir in (root / "Tester").glob("Agent-*/MQL5/Files"):
                for path in files_dir.glob(f"np1_g2r1_{run_id}_*"):
                    raw_relative = path.relative_to(root).as_posix()
                    safe_relative = sanitize_relative_path(raw_relative, selector)
                    destination = run_dir / "searched_outputs" / safe_relative
                    try:
                        copy_privacy_file(path, destination, selector)
                        searched.append({"run_id":run_id,"source_relative":safe_relative,"size_bytes":destination.stat().st_size,"sha256":sha256_file(destination)})
                    except BaseException:
                        omissions.append({"artifact": f"runs/{run_id}/searched_outputs/{safe_relative}", "reason": "unsafe_optional_artifact_omitted"})
        write_json(stage / "searched_location_inventory.json", {"matches": searched})
        log_rows = []
        try:
            changed = changed_logs(root, preflight)
        except BaseException:
            changed = []
            omissions.append({"artifact": "logs", "reason": "unsafe_optional_artifact_omitted"})
        for path in changed:
            raw_relative = path.relative_to(root).as_posix()
            safe_relative = sanitize_relative_path(raw_relative, selector)
            destination = stage / "logs" / safe_relative
            try:
                write_sanitized_runtime_file(path, destination, selector)
                log_rows.append({"source_relative": safe_relative, "size_bytes": destination.stat().st_size, "sha256": sha256_file(destination)})
            except BaseException:
                omissions.append({"artifact": f"logs/{safe_relative}", "reason": "unsafe_optional_artifact_omitted"})
        write_json(stage / "logs" / "log_inventory.json", {"logs": log_rows})
        if compile_workspace is not None and compile_workspace.exists():
            copy_privacy_projection(compile_workspace, stage / "compiled", selector, omissions)
        if partial_staging is not None and partial_staging.exists():
            copy_privacy_projection(partial_staging, stage / "partial_staging", selector, omissions)
        write_json(stage / "omissions.json", {"omissions": omissions})
        try:
            completed = _finalize_stop_stage(stage, stop, selector)
        except BaseException:
            shutil.rmtree(stage, ignore_errors=True)
            stage.mkdir(parents=True, exist_ok=False)
            write_json(stage / "result.json", result)
            (stage / "README.md").write_text("# NP1-G2R1 Minimal Automatic Stop Packet\n\nStatus: `NP1_G2R1_EVIDENCE_INVALID`. Unsafe optional evidence was omitted. No automatic retry is authorized.\n", encoding="utf-8", newline="\n")
            write_json(stage / "invocation_ledger.json", sanitize_projection(ledger_payload, selector))
            write_json(stage / "account_selector_attestation.json", selector_attestation(selector))
            write_json(stage / "commands.json", [])
            write_json(stage / "omissions.json", {"omissions": [{"artifact": "extended_stop_projection", "reason": "unsafe_optional_artifact_omitted"}]})
            completed = _finalize_stop_stage(stage, stop, selector)
        if partial_staging is not None and partial_staging.exists():
            shutil.rmtree(partial_staging, ignore_errors=True)
        return completed
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


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
    expected_name=f"A1_XAU_NP1G2A12_EXECUTION_AUTHORIZATION_{commit[:8].upper()}_2026_07_13.md"
    if path.name != expected_name or not path.is_file() or sha256_file(path) != artifact_sha256:
        raise PermissionError("exact external G2R1 review artifact identity required")
    text = path.read_text(encoding="utf-8")
    begin, end = "NP1_G2R1_EXECUTION_AUTHORIZATION_BLOCK_BEGIN", "NP1_G2R1_EXECUTION_AUTHORIZATION_BLOCK_END"
    if text.count(begin) != 1 or text.count(end) != 1 or text.index(begin) >= text.index(end):
        raise PermissionError("later exact G2R1 authorization required")
    fields = {}
    for raw in text.split(begin, 1)[1].split(end, 1)[0].splitlines():
        if ":" in raw:
            key, value = (part.strip().strip("`") for part in raw.split(":", 1))
            if key in fields: raise PermissionError(f"duplicate authorization field: {key}")
            fields[key] = value
    expected = {
        "NP1_G2R1_EXECUTION_AUTHORIZATION_STATUS":"AUTHORIZED", "REVIEW_VERDICT":"PASS",
        "REVIEWED_EXECUTOR_COMMIT":commit, "REVIEWED_EXECUTOR_TREE":tree,
        "NEW_ROOT_PATH":str(NEW_ROOT), "MARKER_BYTES":"NP1 SPREAD PROBE G2R1 ONLY\\n",
        "CANONICAL_REPORTS_ROOT":CANONICAL_REPORTS_RELATIVE,
        "COMPLETE_OUTPUT_ROOT":f"{CANONICAL_REPORTS_RELATIVE}/{COMPLETE_NAME}",
        "STOP_OUTPUT_ROOT":f"{CANONICAL_REPORTS_RELATIVE}/{STOP_NAME}",
        "METADATA_RECEIPT_MODE":"COPIED_ALLOWLIST", "METADATA_SOURCE_ROOT":str(METADATA_SOURCE_ROOT),
        "METADATA_ALLOWLIST":"Config/accounts.dat,Config/servers.dat",
        "ACCOUNTS_DAT_SIZE_BYTES":"15935", "ACCOUNTS_DAT_SHA256":METADATA_IDENTITIES["Config/accounts.dat"][1],
        "SERVERS_DAT_SIZE_BYTES":"326364", "SERVERS_DAT_SHA256":METADATA_IDENTITIES["Config/servers.dat"][1],
        "ACCOUNT_SELECTOR_MODE":"EXTERNAL_RUNTIME_FILE", "ACCOUNT_SELECTOR_PATH":str(ACCOUNT_SELECTOR),
        "ACCOUNT_SELECTOR_COMMITTED":"false", "COMMON_LOGIN_REQUIRED":"true", "COMMON_SERVER_REQUIRED":"true",
        "TESTER_LOGIN_REQUIRED":"true", "TESTER_SERVER_KEY_AUTHORIZED":"false", "PASSWORD_IN_INI_AUTHORIZED":"false",
        "RAW_EXECUTION_INI_COMMITTED":"false", "RAW_ACCOUNT_LOGS_COMMITTED":"false", "RAW_NATIVE_REPORT_COMMITTED":"false",
        "REDACTED_ACCOUNT_EVIDENCE_REQUIRED":"true",
        "ACCOUNT_ASSERTIONS_REQUIRED":"account_login_present,account_login_matches,account_server_present,account_server_matches",
        "METAEDITOR_COMPILATIONS_MAX":"1", "STRATEGY_TESTER_RUNS_MAX":"3", "STRATEGY_TESTER_ORDER":"warmup,probe1,probe2",
        "AUTOMATIC_RETRY_AUTHORIZED":"false", "REUSE_G2A10_AUTHORIZATION_AUTHORIZED":"false", "REUSE_G2A11_AUTHORIZATION_AUTHORIZED":"false", "REUSE_G2_ROOT_AUTHORIZED":"false",
        "MT5_EXECUTION_AUTHORIZED":"true", "CANONICAL_NP1C_RESULT_AUTHORIZED":"false", "R6_CENSUS_AUTHORIZED":"false",
        "PNL_AUTHORIZED":"false", "PROFITABILITY_AUTHORIZED":"false", "TARGET_EXIT_AUTHORIZED":"false",
        "MFE_MAE_AUTHORIZED":"false", "H4_PORTFOLIO_AUTHORIZED":"false", "DEMO_LIVE_ATTACH_AUTHORIZED":"false",
        "PRESET_PROFILE_ARMING_AUTHORIZED":"false", "BROKER_ACTION_AUTHORIZED":"false", "BTC_WORK_AUTHORIZED":"false",
        "DEPLOYMENT_AUTHORIZED":"false",
    }
    outside = text.split(begin,1)[0] + text.split(end,1)[1]
    if fields != expected or outside.strip():
        raise PermissionError("G2R1 authorization identity/fields mismatch")
    return fields


def execute_future(*, authorization: str, review_artifact: Path, review_sha256: str, reviewed_commit: str, reviewed_tree: str, root: Path, reports_root: Path, metadata_receipt: Path, selector_path: Path = ACCOUNT_SELECTOR, command_runner: CommandRunner = G1.command_runner, compile_runner: CommandRunner = G1.command_runner, version_reader: Callable[[Path], str] = G1.executable_version) -> Path:
    if authorization != ACTIVATION:
        raise PermissionError("NP1-G2A12 is repo-only; future execution is not authorized")
    commit = G1.git("rev-parse", "HEAD"); tree = G1.git("show", "-s", "--format=%T", "HEAD")
    if commit != reviewed_commit or tree != reviewed_tree or G1.git("status", "--porcelain=v1", "--untracked-files=all"):
        raise PermissionError("clean reviewed G2-A12 commit/tree required")
    if reports_root.resolve()!=CANONICAL_REPORTS_ROOT.resolve(): raise PermissionError("exact canonical repository reports root required")
    auth_fields = parse_future_authorization(review_artifact, review_sha256, commit, tree)
    selector = load_account_selector(selector_path, root)
    authority_attestation = {"artifact":review_artifact.name,"sha256":review_sha256,"parsed_fields":auth_fields,"reviewed_executor_commit":commit,"reviewed_executor_tree":tree,"canonical_reports_root":CANONICAL_REPORTS_RELATIVE,"complete_output_root":f"{CANONICAL_REPORTS_RELATIVE}/{COMPLETE_NAME}","stop_output_root":f"{CANONICAL_REPORTS_RELATIVE}/{STOP_NAME}"}
    complete, stop = assert_mutually_exclusive(reports_root)
    terminal, editor = validate_exact_root(root, initial=True)
    receipt = json.loads(metadata_receipt.read_text(encoding="utf-8")); validate_metadata_receipt(root, receipt)
    ledger_path = root / ".np1_g2r1_invocation_ledger.json"
    commands: list[dict[str, Any]] = []; invoked: list[str] = []; preflight: dict[str, Any] = {}; post_reports: dict[str, Any] = {}; report_attestation: dict[str, Any] = {}
    workspace = root / "np1_g2r1_compile_workspace"
    staging = reports_root / ".A1_XAU_R6_NATIVE_SPREAD_PROVENANCE_PROBE_G2R1_20260713.staging"
    if staging.exists(): raise RuntimeError("noncanonical staging path already exists")
    try:
        preflight, post_reports, report_attestation = prepare_reports_directory(root)
        ledger = Ledger(ledger_path); ledger.compilation()
        compiled = compile_once_g2r1(root, editor, runner=compile_runner, version_reader=version_reader)
        workspace.mkdir(); copy_if_present(compiled.source, workspace / B.PROBE_NAME); copy_if_present(compiled.ex5, workspace / compiled.ex5.name); copy_if_present(compiled.log, workspace / "compile.log")
        B.build_probe(workspace / B.PROBE_NAME, workspace / "source_manifest.json")
        commands.append(sanitize_command_record(compiled.command_record, selector))
        staging.mkdir()
        shutil.copytree(workspace, staging / "compiled")
        selected_sources=[]; ex5_checks=[]
        for run_id in RUN_IDS:
            if sha256_file(compiled.ex5) != compiled.ex5_sha256: raise RuntimeError("EX5 drift")
            ex5_checks.append({"stage":f"before_{run_id}","sha256":sha256_file(compiled.ex5)})
            ini = root / "Config" / f"np1_g2r1_{run_id}.ini"; ini.write_text(render_ini(run_id, selector), encoding="utf-8", newline="\n")
            if expected_report(root, run_id).exists(): raise RuntimeError("stale report before invocation")
            ledger.run(run_id); invoked.append(run_id)
            command = [str(terminal), "/portable", f"/config:{ini}"]; started = time.time_ns(); done = command_runner(command, root, 7200); commands.append(sanitize_command_record(G1.record(command, done), selector))
            if int(getattr(done, "returncode", 1)) != 0: raise RuntimeError(f"tester {run_id} failed")
            import analyze_a1_xau_r6_native_spread_provenance_probe as A
            selected_sources.extend(collect_exact_outputs(root, run_id, staging / "runs" / run_id, started, A.parse_report, selector))
        if sha256_file(compiled.ex5) != compiled.ex5_sha256: raise RuntimeError("final post-probe2 EX5 drift")
        ex5_checks.append({"stage":"after_probe2","sha256":sha256_file(compiled.ex5)})
        write_json(staging / "metadata_receipt.json", sanitize_projection(receipt, selector)); write_json(staging / "authorization_attestation.json", sanitize_projection(authority_attestation, selector)); write_json(staging / "account_selector_attestation.json", selector_attestation(selector)); write_json(staging / "preflight_root_inventory.json", sanitize_projection(preflight, selector)); write_json(staging/"post_reports_creation_inventory.json",sanitize_projection(post_reports, selector)); write_json(staging / "post_run_root_inventory.json", sanitize_projection(inventory(root), selector)); write_json(staging / "reports_directory_attestation.json", sanitize_projection(report_attestation, selector)); write_json(staging / "invocation_ledger.json", sanitize_projection(ledger.data, selector)); write_json(staging / "commands.json", sanitize_command_records(commands, selector))
        packet_source_sha=sha256_file(staging/"compiled"/B.PROBE_NAME); packet_ex5_sha=sha256_file(staging/"compiled"/compiled.ex5.name)
        if compiled.source_sha256!=packet_source_sha or compiled.ex5_sha256!=packet_ex5_sha: raise RuntimeError("compiled source/EX5 packet binding mismatch")
        write_json(staging/"compile_attestation.json",{"source_name":B.PROBE_NAME,"source_sha256":packet_source_sha,"compiled_source_sha256":compiled.source_sha256,"ex5_name":compiled.ex5.name,"ex5_sha256":packet_ex5_sha,"compiled_ex5_sha256":compiled.ex5_sha256,"metaeditor_version":compiled.version,"compile_log_sha256":sha256_file(staging/"compiled"/"compile.log")}); write_json(staging/"ex5_identity_attestation.json",ex5_checks)
        write_json(staging/"searched_location_inventory.json",{"selected_sources":selected_sources})
        log_rows=[]
        for path in changed_logs(root,preflight):
            rel=sanitize_relative_path(path.relative_to(root).as_posix(),selector); destination=staging/"logs"/rel; write_sanitized_runtime_file(path,destination,selector);log_rows.append({"source_relative":rel,"size_bytes":destination.stat().st_size,"sha256":sha256_file(destination)})
        write_json(staging/"logs"/"log_inventory.json",{"logs":log_rows})
        result = build_scientific_outputs_from_redacted_packet(staging,reports_root/".np1_g2r1_scientific_build"); write_g2_wrapper(staging,result)
        verification_context={"authorization_attestation":authority_attestation,"metadata_receipt":receipt,"root":root,"selector":selector}
        write_json(staging/"packet_verification.json",semantic_verify_packet(staging,reports_root/".np1_g2r1_semantic_verify",verification_context))
        assert_packet_redacted(staging,selector); _manifest(staging,"a1_xau_r6_np1_g2r1_complete_manifest_v1"); assert_packet_redacted(staging,selector); before={p.relative_to(staging).as_posix():sha256_file(p) for p in staging.rglob("*") if p.is_file()}; verify_manifest(staging); after={p.relative_to(staging).as_posix():sha256_file(p) for p in staging.rglob("*") if p.is_file()};
        if before!=after: raise RuntimeError("read-only semantic verification mutated packet")
        staging.rename(complete)
        return complete
    except BaseException as exc:
        if not ledger_path.exists(): write_json(ledger_path, {"metaeditor_compilations":0,"tester_runs":[],"last_authorized_command_reached":"preflight"})
        preserve_stop_packet(stop=stop, root=root, ledger=ledger_path, preflight=preflight, reports_attestation=report_attestation, commands=commands, run_ids=invoked, error=exc, compile_workspace=workspace, metadata_receipt=metadata_receipt, partial_staging=staging, authorization_attestation=authority_attestation, post_reports_inventory=post_reports, selector=selector)
        raise


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", default="")
    parser.add_argument("--review-artifact", type=Path)
    parser.add_argument("--review-sha256", default="")
    parser.add_argument("--reviewed-commit", default="")
    parser.add_argument("--reviewed-tree", default="")
    parser.add_argument("--metadata-receipt", type=Path)
    parser.add_argument("--account-selector", type=Path, default=ACCOUNT_SELECTOR)
    parser.add_argument("--root", type=Path, default=NEW_ROOT)
    parser.add_argument("--reports-root", type=Path, default=ROOT / "outputs" / "reports")
    args = parser.parse_args()
    if args.review_artifact is None:
        raise SystemExit("NP1-G2A12 is repository-only; no MT5 execution authorized")
    if args.metadata_receipt is None: raise SystemExit("--metadata-receipt required")
    execute_future(authorization=args.authorization, review_artifact=args.review_artifact, review_sha256=args.review_sha256, reviewed_commit=args.reviewed_commit, reviewed_tree=args.reviewed_tree, root=args.root, reports_root=args.reports_root, metadata_receipt=args.metadata_receipt, selector_path=args.account_selector)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
