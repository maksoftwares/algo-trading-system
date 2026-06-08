from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any


EA_REL = Path("mt5") / "Experts" / "Phase2WeaknessBreakoutRetestExecutor.mq5"
SAFE_PRESET_REL = Path("mt5") / "Presets" / "Phase2WeaknessBreakoutRetestExecutor.demo_xauusd.set"
OWNER_PRESET_REL = Path("mt5") / "Presets" / "Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.set"
RUNTIME_NOTES_REL = Path("docs") / "P2WEAKNESS_BR_V1_RUNTIME_NOTES.md"
REGISTRY_REL = Path("docs") / "MAGIC_NUMBER_EXTERNAL_REGISTRY.md"
DEFAULT_ORDER_LOG = Path("C:/MT5PortableP2WeaknessDemo/MQL5/Files/p2weakness_br_v1_order_log_xauusd.csv")
DEFAULT_STARTUP_LOG = Path("C:/MT5PortableP2WeaknessDemo/MQL5/Files/p2weakness_br_v1_startup_xauusd.csv")
REPORTS_DIR = Path("outputs") / "reports"
P2_MAGIC_START = 931000
P2_MAGIC_END = 931099
P2_ACTIVE_MAGIC = 931000
WR50_RANGES = ((930000, 930099), (930100, 930199), (930200, 930299))


@dataclass(frozen=True)
class ReportOutput:
    status: str
    paths: tuple[Path, ...]


def generate_p2weakness_governance_reports(
    phase1_root: Path,
    output_dir: Path | None = None,
    order_log: Path = DEFAULT_ORDER_LOG,
    startup_log: Path = DEFAULT_STARTUP_LOG,
) -> ReportOutput:
    phase1_root = phase1_root.resolve()
    output_dir = (output_dir or phase1_root / REPORTS_DIR).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    source = _read(phase1_root / EA_REL)
    safe_preset = _preset(phase1_root / SAFE_PRESET_REL)
    owner_preset = _preset(phase1_root / OWNER_PRESET_REL)
    runtime_notes = _read(phase1_root / RUNTIME_NOTES_REL)
    registry = _read(phase1_root / REGISTRY_REL)
    source_inputs = _source_inputs(source)
    created_at = _utc_now()

    parity = _parity_payload(phase1_root, source, source_inputs, safe_preset, owner_preset, runtime_notes, registry, created_at)
    magic = _magic_payload(source_inputs, safe_preset, owner_preset, registry, order_log, created_at)
    deployment = _deployment_payload(phase1_root, safe_preset, owner_preset, created_at)
    clean_clone = _clean_clone_payload(phase1_root, parity, magic, created_at)
    daily_risk = _daily_risk_payload(order_log, startup_log, magic, created_at)

    outputs = (
        _write_pair(output_dir, "P2WEAKNESS_BR_V1_SOURCE_GOVERNANCE_PARITY", parity, _render_parity),
        _write_pair(output_dir, "P2WEAKNESS_BR_V1_MAGIC_COLLISION_AUDIT", magic, _render_magic),
        _write_pair(output_dir, "P2WEAKNESS_BR_V1_DEPLOYMENT", deployment, _render_deployment),
        _write_pair(output_dir, "P2WEAKNESS_BR_V1_CLEAN_CLONE_RECONCILIATION", clean_clone, _render_clean_clone),
        _write_pair(output_dir, "EXPERIMENTAL_DEMO_DAILY_RISK_REPORT", daily_risk, _render_daily_risk),
    )
    flat_paths = tuple(path for pair in outputs for path in pair)
    status = "PASS" if parity["status"] == "PASS" and magic["status"] == "PASS" else "FAIL"
    return ReportOutput(status=status, paths=flat_paths)


def _parity_payload(
    phase1_root: Path,
    source: str,
    source_inputs: dict[str, str],
    safe_preset: dict[str, str],
    owner_preset: dict[str, str],
    runtime_notes: str,
    registry: str,
    created_at: str,
) -> dict[str, Any]:
    checks = [
        _token_check("non_canonical_banner", source, "NON_CANONICAL / EXPERIMENTAL DEMO ONLY / DO NOT DEPLOY AS PHASE2"),
        _input_check(source_inputs, "InpDryRunOnly", "true"),
        _input_check(source_inputs, "InpBrokerActionAllowed", "false"),
        _input_check(source_inputs, "InpAllowedAccountLoginsCsv", ""),
        _input_check(source_inputs, "InpExperimentalAuthorizationToken", ""),
        _input_check(source_inputs, "InpCostSuspensionAcknowledgementToken", ""),
        _input_check(source_inputs, "InpCandidateStatus", "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY"),
        _input_check(source_inputs, "InpFamilyLifecycleStatus", "COST_SUSPENDED_CANONICAL"),
        _input_check(source_inputs, "InpMagicNumber", str(P2_ACTIVE_MAGIC)),
        _preset_check(safe_preset, "safe_preset_dry_run", "InpDryRunOnly", "true"),
        _preset_check(safe_preset, "safe_preset_broker_action_disabled", "InpBrokerActionAllowed", "false"),
        _preset_check(owner_preset, "owner_preset_magic", "InpMagicNumber", str(P2_ACTIVE_MAGIC)),
        _token_check("cost_suspension_ack_guard", source, "CostSuspensionAcknowledgementTokenValid", "cost_suspension_acknowledgement_token_missing_or_invalid"),
        _token_check("kill_switch_present", source, "KillSwitchActive", "InpKillSwitchFileName"),
        _token_check("demo_server_refusal", source, 'ContainsText(server, "live")', 'ContainsText(server, "real")'),
        _token_check("cost_r_guard", source, "InpMaxEstimatedCostR", "estimated_cost_r_exceeds_threshold"),
        _token_check("spread_guard", source, "InpMaxMeasuredSpreadPoints", "measured_spread_points_exceeds_threshold"),
        _token_check("market_proxy_logged", source, "MARKET_PROXY", "order_mode"),
        _token_check("duplicate_family_suppression", source, "SameDirectionFamilyExposureExists", "DuplicateFamilyLockActive"),
        _token_check("startup_safe_default_flags", source, "source_default_safe", "owner_authorized_set_used", "cost_suspension_acknowledged"),
        _token_check("runtime_notes_updated", runtime_notes, "931000-931099", "owner_authorized_demo_xauusd.set"),
        _token_check("registry_updated", registry, "P2WEAKNESS_BR_V1", "931000-931099"),
        _fixed_lot_check(source_inputs),
    ]
    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    return {
        "status": status,
        "created_at_utc": created_at,
        "source": str(phase1_root / EA_REL),
        "safe_preset": str(phase1_root / SAFE_PRESET_REL),
        "owner_authorized_preset": str(phase1_root / OWNER_PRESET_REL),
        "source_sha256": _sha256(phase1_root / EA_REL),
        "safe_preset_sha256": _sha256(phase1_root / SAFE_PRESET_REL),
        "owner_authorized_preset_sha256": _sha256(phase1_root / OWNER_PRESET_REL),
        "authority": "P2WEAKNESS_BR_V1 governance parity only; no canonical Phase 2, paper-mode, live, or real-capital authorization.",
        "checks": checks,
        "failed_count": sum(1 for check in checks if check["status"] != "PASS"),
        "input_declaration_block": _input_declaration_block(source),
    }


def _magic_payload(
    source_inputs: dict[str, str],
    safe_preset: dict[str, str],
    owner_preset: dict[str, str],
    registry: str,
    order_log: Path,
    created_at: str,
) -> dict[str, Any]:
    source_magic = _to_int(source_inputs.get("InpMagicNumber"))
    safe_magic = _to_int(safe_preset.get("InpMagicNumber"))
    owner_magic = _to_int(owner_preset.get("InpMagicNumber"))
    runtime_magics = sorted(_runtime_magics(order_log))
    active = {
        "WR50_BreakoutEvening_v0": 930000,
        "WR50_BreakoutQuality_v0": 930100,
        "WR50_BreakoutExit1R_v0": 930200,
        "P2WEAKNESS_BR_V1": P2_ACTIVE_MAGIC,
    }
    duplicate_values = _duplicates(active)
    checks = [
        _range_check("source_magic_in_p2weakness_namespace", source_magic, P2_MAGIC_START, P2_MAGIC_END),
        _range_check("safe_preset_magic_in_p2weakness_namespace", safe_magic, P2_MAGIC_START, P2_MAGIC_END),
        _range_check("owner_preset_magic_in_p2weakness_namespace", owner_magic, P2_MAGIC_START, P2_MAGIC_END),
        _equality_check("active_magic_is_931000", source_magic, P2_ACTIVE_MAGIC),
        _bool_check("p2weakness_not_inside_wr50_namespace", not _range_overlaps((P2_MAGIC_START, P2_MAGIC_END), (930000, 930999)), "P2WEAKNESS=931000-931099; WR50=930000-930999"),
        _bool_check("active_magic_values_unique", not duplicate_values, f"duplicates={duplicate_values or 'none'}"),
        _bool_check("registry_mentions_p2weakness_namespace", "931000-931099" in registry and "P2WEAKNESS_BR_V1" in registry, "registry updated"),
    ]
    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    return {
        "status": status,
        "created_at_utc": created_at,
        "authority": "Magic collision audit for experimental namespaces. PASS does not authorize deployment or trading.",
        "p2weakness_namespace": f"{P2_MAGIC_START}-{P2_MAGIC_END}",
        "p2weakness_active_magic": P2_ACTIVE_MAGIC,
        "source_magic": source_magic,
        "safe_preset_magic": safe_magic,
        "owner_preset_magic": owner_magic,
        "known_active_assignments": active,
        "runtime_log_magics_observed": runtime_magics,
        "runtime_previous_magic_warning": 930101 in runtime_magics,
        "checks": checks,
        "failed_count": sum(1 for check in checks if check["status"] != "PASS"),
    }


def _deployment_payload(phase1_root: Path, safe_preset: dict[str, str], owner_preset: dict[str, str], created_at: str) -> dict[str, Any]:
    return {
        "status": "REPORT_ONLY_NO_NEW_DEPLOYMENT",
        "created_at_utc": created_at,
        "authority": "Reviewer-requested deployment-boundary summary. No MT5 terminal was closed, restarted, attached, detached, or redeployed by this report generator.",
        "source": str(phase1_root / EA_REL),
        "safe_preset": str(phase1_root / SAFE_PRESET_REL),
        "owner_authorized_preset": str(phase1_root / OWNER_PRESET_REL),
        "source_sha256": _sha256(phase1_root / EA_REL),
        "safe_preset_sha256": _sha256(phase1_root / SAFE_PRESET_REL),
        "owner_authorized_preset_sha256": _sha256(phase1_root / OWNER_PRESET_REL),
        "safe_preset_broker_action_allowed": safe_preset.get("InpBrokerActionAllowed", ""),
        "owner_preset_broker_action_allowed": owner_preset.get("InpBrokerActionAllowed", ""),
        "terminal_closed_or_restarted": False,
        "charts_attached_or_modified": False,
        "profiles_modified": False,
        "canonical_phase2_authorized": False,
        "live_trading_authorized": False,
    }


def _clean_clone_payload(phase1_root: Path, parity: dict[str, Any], magic: dict[str, Any], created_at: str) -> dict[str, Any]:
    dirty = _git_status(phase1_root)
    status = "PENDING_AFTER_COMMIT_AND_PUSH" if dirty else "READY_FOR_CLEAN_CLONE_RECHECK"
    return {
        "status": status,
        "created_at_utc": created_at,
        "authority": "Clean-clone reconciliation marker for P2WEAKNESS_BR_V1. A true remote clean-clone proof should be regenerated after commit/push.",
        "repo_head": _git_head(phase1_root),
        "working_tree_has_pending_changes": bool(dirty),
        "pending_paths": dirty,
        "local_parity_status": parity["status"],
        "local_magic_collision_status": magic["status"],
        "required_post_push_action": "Clone origin/main after push, rerun this generator, and expect source/magic parity to remain PASS.",
    }


def _daily_risk_payload(order_log: Path, startup_log: Path, magic: dict[str, Any], created_at: str) -> dict[str, Any]:
    rows = _csv_rows(order_log)
    startup_rows = _csv_rows(startup_log)
    executed = [row for row in rows if row.get("action") == "ORDER_SEND_OK"]
    guard_blocks = [row for row in rows if row.get("action") == "GUARD_BLOCK"]
    costs = [_to_float(row.get("estimated_cost_R")) for row in rows if _to_float(row.get("estimated_cost_R")) is not None]
    costs_clean = [value for value in costs if value is not None]
    latest = rows[-1] if rows else {}
    magics = sorted({row.get("magic", "") for row in rows if row.get("magic")})
    return {
        "status": "REVIEW_ONLY",
        "created_at_utc": created_at,
        "authority": "Experimental demo daily risk report. It does not authorize canonical Phase 2, deployment, live trading, or real capital.",
        "order_log": str(order_log),
        "startup_log": str(startup_log),
        "order_log_exists": order_log.exists(),
        "startup_log_exists": startup_log.exists(),
        "rows": len(rows),
        "executed_orders": len(executed),
        "guard_blocks": len(guard_blocks),
        "open_positions_from_log": _last_int(rows, "family_open_exposure"),
        "account_orders_today_from_log": _last_int(rows, "account_orders_today"),
        "cost_r_min": round(min(costs_clean), 4) if costs_clean else None,
        "cost_r_median": round(median(costs_clean), 4) if costs_clean else None,
        "cost_r_max": round(max(costs_clean), 4) if costs_clean else None,
        "latest_timestamp_broker": latest.get("timestamp_broker", ""),
        "latest_guard_reason": latest.get("guard_reason", ""),
        "latest_action": latest.get("action", ""),
        "magics_observed": magics,
        "runtime_previous_magic_warning": magic.get("runtime_previous_magic_warning", False),
        "startup_rows": len(startup_rows),
        "latest_startup_status": startup_rows[-1].get("startup_status", "") if startup_rows else "",
        "kill_switch_status": "NOT_CHECKED_BY_REPORT_GENERATOR",
        "owner_notes": "New deployments are paused until reviewer-requested governance fixes are reviewed.",
    }


def _write_pair(output_dir: Path, stem: str, payload: dict[str, Any], renderer) -> tuple[Path, Path]:
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(renderer(payload), encoding="utf-8")
    return json_path, md_path


def _render_parity(payload: dict[str, Any]) -> str:
    lines = _report_header("P2WEAKNESS BR V1 Source Governance Parity", payload)
    lines.extend([
        f"- Source: `{payload['source']}`",
        f"- Safe preset: `{payload['safe_preset']}`",
        f"- Owner-authorized preset: `{payload['owner_authorized_preset']}`",
        f"- Failed checks: `{payload['failed_count']}`",
        "",
        "| Check | Status | Evidence |",
        "|---|---|---|",
    ])
    for check in payload["checks"]:
        lines.append(f"| {check['name']} | {check['status']} | {_escape(check['evidence'])} |")
    lines.extend(["", "## Input Declaration Block", "", "```mql5", payload["input_declaration_block"].rstrip(), "```", ""])
    return "\n".join(lines)


def _render_magic(payload: dict[str, Any]) -> str:
    lines = _report_header("P2WEAKNESS BR V1 Magic Collision Audit", payload)
    lines.extend([
        f"- P2WEAKNESS namespace: `{payload['p2weakness_namespace']}`",
        f"- Active magic: `{payload['p2weakness_active_magic']}`",
        f"- Runtime previous-magic warning: `{payload['runtime_previous_magic_warning']}`",
        "",
        "| Check | Status | Evidence |",
        "|---|---|---|",
    ])
    for check in payload["checks"]:
        lines.append(f"| {check['name']} | {check['status']} | {_escape(check['evidence'])} |")
    lines.extend(["", "## Active Assignments", "", "| EA | Magic |", "|---|---:|"])
    for name, magic in payload["known_active_assignments"].items():
        lines.append(f"| {name} | {magic} |")
    lines.append("")
    return "\n".join(lines)


def _render_deployment(payload: dict[str, Any]) -> str:
    lines = _report_header("P2WEAKNESS BR V1 Deployment Boundary", payload)
    lines.extend([
        f"- Source SHA256: `{payload['source_sha256']}`",
        f"- Safe preset SHA256: `{payload['safe_preset_sha256']}`",
        f"- Owner-authorized preset SHA256: `{payload['owner_authorized_preset_sha256']}`",
        f"- Terminal closed/restarted: `{payload['terminal_closed_or_restarted']}`",
        f"- Charts attached/modified: `{payload['charts_attached_or_modified']}`",
        f"- Profiles modified: `{payload['profiles_modified']}`",
        f"- Canonical Phase 2 authorized: `{payload['canonical_phase2_authorized']}`",
        f"- Live trading authorized: `{payload['live_trading_authorized']}`",
        "",
    ])
    return "\n".join(lines)


def _render_clean_clone(payload: dict[str, Any]) -> str:
    lines = _report_header("P2WEAKNESS BR V1 Clean-Clone Reconciliation", payload)
    lines.extend([
        f"- Repo HEAD: `{payload['repo_head']}`",
        f"- Working tree has pending changes: `{payload['working_tree_has_pending_changes']}`",
        f"- Local parity status: `{payload['local_parity_status']}`",
        f"- Local magic collision status: `{payload['local_magic_collision_status']}`",
        f"- Required post-push action: {payload['required_post_push_action']}",
        "",
        "## Pending Paths",
        "",
    ])
    for path in payload["pending_paths"]:
        lines.append(f"- `{path}`")
    lines.append("")
    return "\n".join(lines)


def _render_daily_risk(payload: dict[str, Any]) -> str:
    lines = _report_header("Experimental Demo Daily Risk Report", payload)
    lines.extend([
        f"- Order log exists: `{payload['order_log_exists']}`",
        f"- Startup log exists: `{payload['startup_log_exists']}`",
        f"- Rows: `{payload['rows']}`",
        f"- Executed orders: `{payload['executed_orders']}`",
        f"- Guard blocks: `{payload['guard_blocks']}`",
        f"- Cost R min/median/max: `{payload['cost_r_min']}` / `{payload['cost_r_median']}` / `{payload['cost_r_max']}`",
        f"- Latest action: `{payload['latest_action']}`",
        f"- Latest guard reason: `{payload['latest_guard_reason']}`",
        f"- Runtime previous-magic warning: `{payload['runtime_previous_magic_warning']}`",
        f"- Latest startup status: `{payload['latest_startup_status']}`",
        f"- Owner notes: {payload['owner_notes']}",
        "",
    ])
    return "\n".join(lines)


def _report_header(title: str, payload: dict[str, Any]) -> list[str]:
    return [
        f"# {title}",
        "",
        f"Status: {payload['status']}",
        "",
        payload["authority"],
        "",
        f"Created at UTC: `{payload['created_at_utc']}`",
        "",
    ]


def _token_check(name: str, text: str, *tokens: str) -> dict[str, str]:
    missing = [token for token in tokens if token not in text]
    return {"name": name, "status": "PASS" if not missing else "FAIL", "evidence": "all required tokens present" if not missing else "missing: " + ", ".join(missing)}


def _input_check(inputs: dict[str, str], name: str, expected: str) -> dict[str, str]:
    actual = inputs.get(name)
    return _bool_check(f"{name}_default", actual == expected, f"actual={actual!r}; expected={expected!r}")


def _preset_check(preset: dict[str, str], check_name: str, key: str, expected: str) -> dict[str, str]:
    actual = preset.get(key)
    return _bool_check(check_name, actual == expected, f"{key}={actual!r}; expected={expected!r}")


def _fixed_lot_check(inputs: dict[str, str]) -> dict[str, str]:
    value = _to_float(inputs.get("InpFixedLot"))
    return _bool_check("fixed_lot_lte_0_01", value is not None and value <= 0.01, f"InpFixedLot={value}")


def _range_check(name: str, value: int | None, low: int, high: int) -> dict[str, str]:
    return _bool_check(name, value is not None and low <= value <= high, f"value={value}; allowed={low}-{high}")


def _equality_check(name: str, value: int | None, expected: int) -> dict[str, str]:
    return _bool_check(name, value == expected, f"value={value}; expected={expected}")


def _bool_check(name: str, ok: bool, evidence: str) -> dict[str, str]:
    return {"name": name, "status": "PASS" if ok else "FAIL", "evidence": evidence}


def _source_inputs(source: str) -> dict[str, str]:
    values: dict[str, str] = {}
    pattern = re.compile(r"^\s*input\s+\w+\s+(\w+)\s*=\s*(.+?);\s*$")
    for line in source.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        raw = match.group(2).strip()
        if raw.startswith('"') and raw.endswith('"'):
            raw = raw[1:-1]
        values[match.group(1)] = raw
    return values


def _preset(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip() or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _input_declaration_block(source: str) -> str:
    return "\n".join(f"{index}: {line}" for index, line in enumerate(source.splitlines(), start=1) if line.strip().startswith("input "))


def _runtime_magics(order_log: Path) -> set[int]:
    values: set[int] = set()
    for row in _csv_rows(order_log):
        magic = _to_int(row.get("magic"))
        if magic is not None:
            values.add(magic)
    return values


def _csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _last_int(rows: list[dict[str, str]], key: str) -> int | None:
    for row in reversed(rows):
        value = _to_int(row.get(key))
        if value is not None:
            return value
    return None


def _to_int(value: object) -> int | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(float(str(value)))
    except ValueError:
        return None


def _to_float(value: object) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(str(value))
    except ValueError:
        return None


def _duplicates(values: dict[str, int]) -> dict[int, list[str]]:
    seen: dict[int, list[str]] = {}
    for name, magic in values.items():
        seen.setdefault(magic, []).append(name)
    return {magic: names for magic, names in seen.items() if len(names) > 1}


def _range_overlaps(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return left[0] <= right[1] and right[0] <= left[1]


def _git_head(phase1_root: Path) -> str:
    return _run_git(phase1_root.parents[1], ["rev-parse", "HEAD"]) or "UNKNOWN"


def _git_status(phase1_root: Path) -> list[str]:
    status = _run_git(phase1_root.parents[1], ["status", "--short"])
    return [line.strip() for line in status.splitlines() if line.strip()]


def _run_git(repo_root: Path, args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=repo_root, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _sha256(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate P2WEAKNESS_BR_V1 governance and daily risk reports.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--order-log", type=Path, default=DEFAULT_ORDER_LOG)
    parser.add_argument("--startup-log", type=Path, default=DEFAULT_STARTUP_LOG)
    args = parser.parse_args(argv)
    output = generate_p2weakness_governance_reports(
        args.phase1_root,
        output_dir=args.output_dir,
        order_log=args.order_log,
        startup_log=args.startup_log,
    )
    print(f"P2WEAKNESS governance reports: {output.status}")
    for path in output.paths:
        print(path)
    return 0 if output.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
