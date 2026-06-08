from __future__ import annotations

import csv
import hashlib
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


PHASE2X_STATUS_PASS = "PASS"
PHASE2X_STATUS_FAIL = "FAIL"
PHASE2X_STATUS_PENDING_OWNER = "PENDING_OWNER_ACTION"
PHASE2X_STATUS_PENDING_RUNTIME = "PENDING_RUNTIME_EVIDENCE"
PHASE2X_STATUS_PENDING_MANUAL = "PENDING_MANUAL_CONFIRMATION"
PHASE2X_STATUS_REVIEW = "OWNER_REVIEW_REQUIRED"

RUN_ID = "P2WEAKNESS_BR_V1"
TARGET_SYMBOL = "XAUUSD"
ACTIVE_MAGIC = 931000
OLD_MAGIC = 930101
FIXED_LOT = 0.01
MAX_ORDERS_PER_DAY = 3
STRICT_MAX_ORDERS_PER_DAY = 2
MAX_ACCOUNT_ORDERS_PER_DAY = 3
MAX_FAMILY_OPEN_POSITIONS = 1
MAX_ESTIMATED_COST_R = 0.15
MAX_MEASURED_SPREAD_POINTS = 75.0
AUTH_TOKEN = "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY"
COST_ACK_TOKEN = "I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT"
DEFAULT_OWNER_JSON = Path("local") / "phase2x_owner_authorization.local.json"
DEFAULT_LOCAL_PRESET = Path("local") / "Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.local.set"
OWNER_TEMPLATE_REL = Path("mt5") / "Presets" / "Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.template.set"
SAFE_PRESET_REL = Path("mt5") / "Presets" / "Phase2WeaknessBreakoutRetestExecutor.demo_xauusd.set"


STRICT_PRESET_VALUES: dict[str, str] = {
    "InpRunId": RUN_ID,
    "InpDryRunOnly": "false",
    "InpBrokerActionAllowed": "true",
    "InpTargetSymbol": TARGET_SYMBOL,
    "InpExpectedServerMarker": "Demo",
    "InpExperimentalAuthorizationToken": AUTH_TOKEN,
    "InpRequiredExperimentalAuthorizationToken": AUTH_TOKEN,
    "InpCostSuspensionAcknowledgementToken": COST_ACK_TOKEN,
    "InpRequiredCostSuspensionAcknowledgementToken": COST_ACK_TOKEN,
    "InpCandidateStatus": "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY",
    "InpFamilyLifecycleStatus": "COST_SUSPENDED_CANONICAL",
    "InpKillSwitchFileName": "p2weakness_br_v1_kill_switch.txt",
    "InpSignalLogFileName": "p2weakness_br_v1_signal_log_xauusd.csv",
    "InpStartupLogFileName": "p2weakness_br_v1_startup_xauusd.csv",
    "InpOrderLogFileName": "p2weakness_br_v1_order_log_xauusd.csv",
    "InpFixedLot": "0.01",
    "InpMagicNumber": "931000",
    "InpMaxOrdersPerDay": "2",
    "InpMaxAccountOrdersPerDay": "3",
    "InpMinSecondsBetweenOrders": "300",
    "InpMaxOpenPositionsPerInstance": "1",
    "InpMaxFamilyOpenPositions": "1",
    "InpDuplicateLockBars": "12",
    "InpDeviationPoints": "50",
    "InpMaxEstimatedCostR": "0.15",
    "InpMaxMeasuredSpreadPoints": "75.0",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def reports_dir(root: Path) -> Path:
    return root.resolve() / "outputs" / "reports"


def check(name: str, status: str, evidence: str) -> dict[str, str]:
    return {"name": name, "status": status, "evidence": evidence}


def overall_status(checks: list[dict[str, str]]) -> str:
    statuses = {item["status"] for item in checks}
    if PHASE2X_STATUS_FAIL in statuses:
        return PHASE2X_STATUS_FAIL
    if any(status.startswith("PENDING") for status in statuses):
        return "PENDING"
    if PHASE2X_STATUS_REVIEW in statuses:
        return PHASE2X_STATUS_REVIEW
    return PHASE2X_STATUS_PASS


def write_report_pair(output_json: Path, payload: dict[str, Any], markdown: str) -> tuple[Path, Path]:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md = output_json.with_suffix(".md")
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(markdown, encoding="utf-8")
    return output_json, output_md


def report_header(title: str, payload: dict[str, Any]) -> list[str]:
    return [
        f"# {title}",
        "",
        f"Overall status: {payload['status']}",
        "",
        payload["authority"],
        "",
        f"Created at UTC: `{payload['created_at_utc']}`",
        "",
    ]


def checks_table(checks: list[dict[str, str]]) -> list[str]:
    lines = ["| Check | Status | Evidence |", "|---|---|---|"]
    lines.extend(f"| {item['name']} | {item['status']} | {escape_md(item['evidence'])} |" for item in checks)
    return lines


def boundary_lines() -> list[str]:
    return [
        "## Boundary",
        "",
        "- Phase 2X can approve only quarantined experimental demo execution.",
        "- Phase 2X cannot approve canonical Phase 2.",
        "- Phase 2X cannot approve live trading or real capital.",
        "- Phase 2X cannot unsuspend the cost-suspended breakout-retest family.",
        "- Phase 2X cannot create same-family diversification claims.",
        "",
    ]


def escape_md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def parse_set_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def render_set_file(template_lines: list[str], values: dict[str, str]) -> str:
    rendered: list[str] = []
    seen: set[str] = set()
    for line in template_lines:
        if "=" not in line or line.lstrip().startswith("#"):
            rendered.append(line)
            continue
        key, _old = line.split("=", 1)
        key = key.strip()
        if key in values:
            rendered.append(f"{key}={values[key]}")
            seen.add(key)
        else:
            rendered.append(line)
    for key in values:
        if key not in seen:
            rendered.append(f"{key}={values[key]}")
    return "\n".join(rendered).rstrip() + "\n"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_status_markdown(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    text = path.read_text(encoding="utf-8", errors="replace")
    patterns = [
        r"Overall status:\s*`?([A-Z0-9_/-]+)`?",
        r"Status:\s*`?([A-Z0-9_/-]+)`?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return "UNKNOWN"


def validate_owner_authorization(data: dict[str, Any], now: datetime | None = None) -> list[dict[str, str]]:
    now = now or datetime.now(timezone.utc)
    checks = [
        check(
            "authorization_status",
            PHASE2X_STATUS_PASS if data.get("authorization_status") == "APPROVED_FOR_EXPERIMENTAL_DEMO_ONLY" else PHASE2X_STATUS_FAIL,
            f"authorization_status={data.get('authorization_status', '')!r}",
        ),
        check("authorized_account_login_present", PHASE2X_STATUS_PASS if str(data.get("authorized_account_login", "")).strip() else PHASE2X_STATUS_FAIL, "account login must be nonblank"),
        check("server_marker_demo_or_practice", PHASE2X_STATUS_PASS if _contains_demo_marker(data.get("authorized_server_marker", "")) else PHASE2X_STATUS_FAIL, f"server_marker={data.get('authorized_server_marker', '')!r}"),
        check("authorized_symbol_xauusd", PHASE2X_STATUS_PASS if data.get("authorized_symbol") == TARGET_SYMBOL else PHASE2X_STATUS_FAIL, f"authorized_symbol={data.get('authorized_symbol', '')!r}"),
        check("authorized_candidate", PHASE2X_STATUS_PASS if data.get("authorized_candidate") == RUN_ID else PHASE2X_STATUS_FAIL, f"authorized_candidate={data.get('authorized_candidate', '')!r}"),
        check("authorized_magic_931000", PHASE2X_STATUS_PASS if _to_int(data.get("authorized_magic")) == ACTIVE_MAGIC else PHASE2X_STATUS_FAIL, f"authorized_magic={data.get('authorized_magic', '')!r}"),
        check("fixed_lot_lte_0_01", PHASE2X_STATUS_PASS if _to_float(data.get("fixed_lot")) is not None and _to_float(data.get("fixed_lot")) <= FIXED_LOT else PHASE2X_STATUS_FAIL, f"fixed_lot={data.get('fixed_lot', '')!r}"),
        check("max_orders_per_day_lte_3", PHASE2X_STATUS_PASS if _to_int(data.get("max_orders_per_day")) is not None and _to_int(data.get("max_orders_per_day")) <= MAX_ORDERS_PER_DAY else PHASE2X_STATUS_FAIL, f"max_orders_per_day={data.get('max_orders_per_day', '')!r}"),
        check("max_account_orders_per_day_lte_3", PHASE2X_STATUS_PASS if _to_int(data.get("max_account_orders_per_day")) is not None and _to_int(data.get("max_account_orders_per_day")) <= MAX_ACCOUNT_ORDERS_PER_DAY else PHASE2X_STATUS_FAIL, f"max_account_orders_per_day={data.get('max_account_orders_per_day', '')!r}"),
        check("max_family_open_positions_eq_1", PHASE2X_STATUS_PASS if _to_int(data.get("max_family_open_positions")) == MAX_FAMILY_OPEN_POSITIONS else PHASE2X_STATUS_FAIL, f"max_family_open_positions={data.get('max_family_open_positions', '')!r}"),
        check("max_estimated_cost_r_lte_0_15", PHASE2X_STATUS_PASS if _to_float(data.get("max_estimated_cost_r")) is not None and _to_float(data.get("max_estimated_cost_r")) <= MAX_ESTIMATED_COST_R else PHASE2X_STATUS_FAIL, f"max_estimated_cost_r={data.get('max_estimated_cost_r', '')!r}"),
        check("max_measured_spread_points_lte_75", PHASE2X_STATUS_PASS if _to_float(data.get("max_measured_spread_points")) is not None and _to_float(data.get("max_measured_spread_points")) <= MAX_MEASURED_SPREAD_POINTS else PHASE2X_STATUS_FAIL, f"max_measured_spread_points={data.get('max_measured_spread_points', '')!r}"),
        check("experimental_authorization_token", PHASE2X_STATUS_PASS if data.get("experimental_authorization_token") == AUTH_TOKEN else PHASE2X_STATUS_FAIL, "required token must match exactly"),
        check("cost_suspension_acknowledgement_token", PHASE2X_STATUS_PASS if data.get("cost_suspension_acknowledgement_token") == COST_ACK_TOKEN else PHASE2X_STATUS_FAIL, "required acknowledgement token must match exactly"),
    ]
    expires_at = _parse_dt(data.get("expires_at_utc"))
    if expires_at is None:
        checks.append(check("expires_at_utc_present", PHASE2X_STATUS_FAIL, "expires_at_utc is missing or invalid"))
    elif expires_at <= now:
        checks.append(check("authorization_not_expired", PHASE2X_STATUS_FAIL, f"expires_at_utc={expires_at.isoformat()}"))
    else:
        checks.append(check("authorization_not_expired", PHASE2X_STATUS_PASS, f"expires_at_utc={expires_at.isoformat()}"))
    return checks


def owner_status_from_checks(checks: list[dict[str, str]], owner_json: Path) -> str:
    if not owner_json.exists():
        return PHASE2X_STATUS_PENDING_OWNER
    return PHASE2X_STATUS_PASS if all(item["status"] == PHASE2X_STATUS_PASS for item in checks) else PHASE2X_STATUS_FAIL


def strict_values_from_owner(data: dict[str, Any]) -> dict[str, str]:
    values = dict(STRICT_PRESET_VALUES)
    values["InpAllowedAccountLoginsCsv"] = str(data["authorized_account_login"]).strip()
    values["InpExpectedServerMarker"] = str(data.get("authorized_server_marker", "Demo")).strip()
    values["InpMaxOrdersPerDay"] = str(min(_to_int(data.get("max_orders_per_day")) or STRICT_MAX_ORDERS_PER_DAY, MAX_ORDERS_PER_DAY))
    values["InpMaxAccountOrdersPerDay"] = str(min(_to_int(data.get("max_account_orders_per_day")) or MAX_ACCOUNT_ORDERS_PER_DAY, MAX_ACCOUNT_ORDERS_PER_DAY))
    values["InpMaxFamilyOpenPositions"] = str(MAX_FAMILY_OPEN_POSITIONS)
    values["InpFixedLot"] = _format_float(min(_to_float(data.get("fixed_lot")) or FIXED_LOT, FIXED_LOT))
    values["InpMaxEstimatedCostR"] = _format_float(min(_to_float(data.get("max_estimated_cost_r")) or MAX_ESTIMATED_COST_R, MAX_ESTIMATED_COST_R))
    values["InpMaxMeasuredSpreadPoints"] = _format_float(min(_to_float(data.get("max_measured_spread_points")) or MAX_MEASURED_SPREAD_POINTS, MAX_MEASURED_SPREAD_POINTS))
    return values


def validate_local_output_path(root: Path, output: Path) -> None:
    root = root.resolve()
    local_root = root / "local"
    resolved = output.resolve()
    try:
        resolved.relative_to(local_root)
    except ValueError as exc:
        raise ValueError(f"Refusing to write owner-authorized preset outside local/: {resolved}") from exc
    if "mt5" in [part.lower() for part in resolved.parts] or "presets" in [part.lower() for part in resolved.parts]:
        raise ValueError(f"Refusing to overwrite committed preset path: {resolved}")


def mask_account(value: object) -> str:
    text = str(value or "")
    if len(text) <= 3:
        return "***"
    return "*" * (len(text) - 3) + text[-3:]


def sha256(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize_order_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    actions: dict[str, int] = {}
    costs: list[float] = []
    for row in rows:
        action = row.get("action", "") or "UNKNOWN"
        actions[action] = actions.get(action, 0) + 1
        cost = _to_float(row.get("estimated_cost_R"))
        if cost is not None:
            costs.append(cost)
    return {
        "rows": len(rows),
        "actions": actions,
        "order_send_ok": actions.get("ORDER_SEND_OK", 0),
        "guard_blocks": actions.get("GUARD_BLOCK", 0),
        "estimated_cost_r_min": min(costs) if costs else None,
        "estimated_cost_r_mean": round(mean(costs), 6) if costs else None,
        "estimated_cost_r_max": max(costs) if costs else None,
    }


def create_zip(zip_path: Path, members: list[tuple[Path, str]]) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for source, arcname in members:
            if source.exists():
                archive.write(source, arcname)


def _contains_demo_marker(value: object) -> bool:
    text = str(value).lower()
    return "demo" in text or "practice" in text


def _parse_dt(value: object) -> datetime | None:
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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


def _format_float(value: float) -> str:
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return text if "." in text else f"{text}.0"
