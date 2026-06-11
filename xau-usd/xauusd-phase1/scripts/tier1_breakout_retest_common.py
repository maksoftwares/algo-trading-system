from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_PENDING_OWNER = "PENDING_OWNER_ACTION"
STATUS_PENDING_RUNTIME = "PENDING_RUNTIME_EVIDENCE"
STATUS_PENDING_MANUAL = "PENDING_MANUAL_CONFIRMATION"

RUN_ID = "TIER1_BREAKOUT_RETEST_SEPARATE_DEMO_2026_06_10"
EA_NAME = "Phase2ExperimentalDemoExecutor"
EA_SOURCE_REL = Path("mt5") / "Experts" / f"{EA_NAME}.mq5"
TEMPLATE_REL = Path("mt5") / "Presets" / f"{EA_NAME}.tier1_breakout_retest_demo_xauusd.template.set"
DEFAULT_OWNER_JSON = Path("local") / "tier1_breakout_retest_owner_authorization.local.json"
DEFAULT_LOCAL_PRESET = Path("local") / f"{EA_NAME}.tier1_breakout_retest.owner_authorized_demo_xauusd.local.set"
DEFAULT_PORTABLE_ROOT = Path("C:/MT5PortableTier1BestEA")
DEFAULT_SOURCE_CONFIG_ROOT = Path("C:/MT5PortableSpreadLogger/Config")
DEFAULT_INSTALL_ROOT = Path("C:/Program Files/MetaTrader 5")

TARGET_SYMBOL = "XAUUSD"
CANDIDATE = "breakout_retest"
DERIVED_MAGIC = 920101
AUTH_TOKEN = "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY"
COST_ACK_TOKEN = "I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT"
OLD_DEMO_ACCOUNT = "1025742"

TIER1_PRESET_VALUES: dict[str, str] = {
    "InpRunId": RUN_ID,
    "InpDryRunOnly": "false",
    "InpBrokerActionAllowed": "true",
    "InpCandidate": CANDIDATE,
    "InpCandidateStatus": "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY",
    "InpFamilyLifecycleStatus": "COST_SUSPENDED_CANONICAL",
    "InpTargetSymbol": TARGET_SYMBOL,
    "InpQualifiedSymbolsCsv": TARGET_SYMBOL,
    "InpExpectedServerMarker": "Demo",
    "InpExperimentalAuthorizationToken": AUTH_TOKEN,
    "InpRequiredExperimentalAuthorizationToken": AUTH_TOKEN,
    "InpCostSuspensionAcknowledgementToken": COST_ACK_TOKEN,
    "InpRequiredCostSuspensionAcknowledgementToken": COST_ACK_TOKEN,
    "InpAuthorizedCandidatesCsv": CANDIDATE,
    "InpAttachmentLogFileName": "tier1_bestea_signal_log_xauusd.csv",
    "InpStartupLogFileName": "tier1_bestea_startup_xauusd.csv",
    "InpOrderLogFileName": "tier1_bestea_order_log_xauusd.csv",
    "InpKillSwitchFileName": "tier1_bestea_kill_switch.txt",
    "InpFixedLot": "0.01",
    "InpEURUSDFixedLot": "0.01",
    "InpGBPUSDFixedLot": "0.01",
    "InpMaxOrdersPerDay": "0",
    "InpMaxAccountOrdersPerDay": "0",
    "InpMinSecondsBetweenOrders": "60",
    "InpMaxOpenPositionsPerInstance": "1",
    "InpDeviationPoints": "50",
    "InpMaxEstimatedCostR": "0.30",
    "InpMaxMeasuredSpreadPoints": "75.0",
    "InpTradeSessionGateEnabled": "true",
    "InpTradeSessionStartHour": "12",
    "InpTradeSessionEndHour": "15",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def reports_dir(root: Path) -> Path:
    return root.resolve() / "outputs" / "reports"


def check(name: str, status: str, evidence: str) -> dict[str, str]:
    return {"name": name, "status": status, "evidence": evidence}


def overall_status(checks: list[dict[str, str]]) -> str:
    statuses = {item["status"] for item in checks}
    if STATUS_FAIL in statuses:
        return STATUS_FAIL
    if any(status.startswith("PENDING") for status in statuses):
        return "PENDING"
    return STATUS_PASS


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
        "- Experimental demo lane only; canonical Phase 2 remains blocked.",
        "- One EA, one symbol, one chart: breakout_retest on XAUUSD M5.",
        "- Owner-authorized execution presets are local/private and must not be committed.",
        "- The old demo account 1025742 is not touched by this lane.",
        "",
    ]


def escape_md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def sha256(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mask_account(value: object) -> str:
    text = str(value or "")
    if len(text) <= 3:
        return "***"
    return "*" * (len(text) - 3) + text[-3:]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


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
    for key, value in values.items():
        if key not in seen:
            rendered.append(f"{key}={value}")
    return "\n".join(rendered).rstrip() + "\n"


def parse_mq5_inputs(source: Path) -> dict[str, str]:
    inputs: dict[str, str] = {}
    if not source.exists():
        return inputs
    pattern = re.compile(r"^\s*input\s+.+?\s+(Inp[A-Za-z0-9_]+)\s*=\s*(.+?);")
    for line in source.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(line)
        if match:
            inputs[match.group(1)] = match.group(2).strip()
    return inputs


def validate_local_output_path(root: Path, output: Path) -> None:
    root = root.resolve()
    local_root = root / "local"
    resolved = output.resolve()
    try:
        resolved.relative_to(local_root)
    except ValueError as exc:
        raise ValueError(f"Refusing to write owner-authorized Tier-1 preset outside local/: {resolved}") from exc
    lowered = [part.lower() for part in resolved.parts]
    if "mt5" in lowered or "presets" in lowered:
        raise ValueError(f"Refusing to write owner-authorized Tier-1 preset inside committed MT5 paths: {resolved}")


def demo_marker(value: object) -> bool:
    text = str(value).lower()
    return "demo" in text or "practice" in text


def validate_owner_authorization(data: dict[str, Any]) -> list[dict[str, str]]:
    checks = [
        check(
            "authorization_status",
            STATUS_PASS if data.get("authorization_status") == "APPROVED_FOR_EXPERIMENTAL_DEMO_ONLY" else STATUS_FAIL,
            f"authorization_status={data.get('authorization_status', '')!r}",
        ),
        check("authorized_account_login_present", STATUS_PASS if str(data.get("authorized_account_login", "")).strip() else STATUS_FAIL, "account login must be nonblank"),
        check("old_account_1025742_not_authorized", STATUS_PASS if str(data.get("authorized_account_login", "")).strip() != OLD_DEMO_ACCOUNT else STATUS_FAIL, f"authorized_account_login={mask_account(data.get('authorized_account_login', ''))}"),
        check("server_marker_demo_or_practice", STATUS_PASS if demo_marker(data.get("authorized_server_marker", "")) else STATUS_FAIL, f"server_marker={data.get('authorized_server_marker', '')!r}"),
        check("authorized_symbol_xauusd", STATUS_PASS if data.get("authorized_symbol") == TARGET_SYMBOL else STATUS_FAIL, f"authorized_symbol={data.get('authorized_symbol', '')!r}"),
        check("authorized_candidate_breakout_retest", STATUS_PASS if data.get("authorized_candidate") == CANDIDATE else STATUS_FAIL, f"authorized_candidate={data.get('authorized_candidate', '')!r}"),
        check("derived_magic_920101", STATUS_PASS if _to_int(data.get("authorized_magic")) == DERIVED_MAGIC else STATUS_FAIL, f"authorized_magic={data.get('authorized_magic', '')!r}"),
        check("fixed_lot_eq_0_01", STATUS_PASS if _to_float(data.get("fixed_lot")) == 0.01 else STATUS_FAIL, f"fixed_lot={data.get('fixed_lot', '')!r}"),
        check("max_estimated_cost_r_eq_0_30", STATUS_PASS if _to_float(data.get("max_estimated_cost_r")) == 0.30 else STATUS_FAIL, f"max_estimated_cost_r={data.get('max_estimated_cost_r', '')!r}"),
        check("max_measured_spread_points_eq_75", STATUS_PASS if _to_float(data.get("max_measured_spread_points")) == 75.0 else STATUS_FAIL, f"max_measured_spread_points={data.get('max_measured_spread_points', '')!r}"),
        check("max_open_positions_per_instance_eq_1", STATUS_PASS if _to_int(data.get("max_open_positions_per_instance")) == 1 else STATUS_FAIL, f"max_open_positions_per_instance={data.get('max_open_positions_per_instance', '')!r}"),
        check("min_seconds_between_orders_eq_60", STATUS_PASS if _to_int(data.get("min_seconds_between_orders")) == 60 else STATUS_FAIL, f"min_seconds_between_orders={data.get('min_seconds_between_orders', '')!r}"),
        check("max_orders_per_day_uncapped", STATUS_PASS if _to_int(data.get("max_orders_per_day")) == 0 else STATUS_FAIL, f"max_orders_per_day={data.get('max_orders_per_day', '')!r}"),
        check("max_account_orders_per_day_uncapped", STATUS_PASS if _to_int(data.get("max_account_orders_per_day")) == 0 else STATUS_FAIL, f"max_account_orders_per_day={data.get('max_account_orders_per_day', '')!r}"),
    ]
    return checks


def owner_payload_from_login(login: str, server_marker: str) -> dict[str, Any]:
    return {
        "authorization_status": "APPROVED_FOR_EXPERIMENTAL_DEMO_ONLY",
        "approved_at_utc": now_utc(),
        "authorized_account_login": str(login).strip(),
        "authorized_server_marker": str(server_marker).strip() or "Demo",
        "authorized_symbol": TARGET_SYMBOL,
        "authorized_candidate": CANDIDATE,
        "authorized_magic": DERIVED_MAGIC,
        "fixed_lot": 0.01,
        "max_estimated_cost_r": 0.30,
        "max_measured_spread_points": 75.0,
        "max_open_positions_per_instance": 1,
        "min_seconds_between_orders": 60,
        "max_orders_per_day": 0,
        "max_account_orders_per_day": 0,
    }


def tier1_values_from_owner(data: dict[str, Any]) -> dict[str, str]:
    values = dict(TIER1_PRESET_VALUES)
    values["InpAllowedAccountLoginsCsv"] = str(data["authorized_account_login"]).strip()
    server_marker = str(data.get("authorized_server_marker", "Demo")).strip()
    values["InpExpectedServerMarker"] = "Practice" if "practice" in server_marker.lower() else "Demo"
    return values


def compile_log_passed(path: Path) -> bool:
    text = read_text_any_encoding(path)
    lowered = text.lower()
    return (
        "0 errors, 0 warnings" in lowered
        or "0 errors, 0 warning" in lowered
        or "0 error(s), 0 warning(s)" in lowered
        or "0 error(s), 0 warning" in lowered
    )


def read_text_any_encoding(path: Path) -> str:
    if not path.exists():
        return ""
    payload = path.read_bytes()
    for encoding in ("utf-16", "utf-8-sig", "utf-8", "cp1252"):
        try:
            return payload.decode(encoding)
        except UnicodeError:
            continue
    return payload.decode("utf-8", errors="replace")


def summarize_order_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    actions: dict[str, int] = {}
    guard_reasons: dict[str, int] = {}
    costs: list[float] = []
    stop_distances: list[float] = []
    for row in rows:
        action = row.get("action", "") or "UNKNOWN"
        actions[action] = actions.get(action, 0) + 1
        if action == "GUARD_BLOCK":
            reason = row.get("guard_reason", "") or "UNKNOWN"
            guard_reasons[reason] = guard_reasons.get(reason, 0) + 1
        cost = _to_float(row.get("estimated_cost_R"))
        if cost is not None:
            costs.append(cost)
        stop_distance = _to_float(row.get("stop_distance_points"))
        if stop_distance is not None:
            stop_distances.append(stop_distance)
    return {
        "rows": len(rows),
        "actions": actions,
        "guard_reasons": guard_reasons,
        "orders_sent": actions.get("ORDER_SEND_OK", 0),
        "guard_blocks": actions.get("GUARD_BLOCK", 0),
        "cost_r_mean": round(mean(costs), 6) if costs else None,
        "cost_r_p95": percentile(costs, 95) if costs else None,
        "stop_distance_points_mean": round(mean(stop_distances), 2) if stop_distances else None,
    }


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = int(round((pct / 100.0) * (len(ordered) - 1)))
    return round(ordered[index], 6)


def session_bucket(server_timestamp: str) -> str:
    parsed = parse_mt5_datetime(server_timestamp)
    if parsed is None:
        return "UNKNOWN"
    hour = parsed.hour
    if 12 <= hour <= 15:
        return "NY_MORNING"
    if 16 <= hour <= 20:
        return "NY_AFTERNOON"
    if 23 <= hour or hour <= 6:
        return "ASIA"
    if 7 <= hour <= 11:
        return "LONDON_PRE"
    if 21 <= hour <= 22:
        return "HALT"
    return "UNKNOWN"


def bucket_dubai_equivalent(bucket: str, value_date: date) -> str:
    offset = 4 if us_dst_active(value_date) else 5
    ranges = {
        "NY_MORNING": (12, 15, 59),
        "NY_AFTERNOON": (16, 20, 59),
        "ASIA": (23, 6, 59),
        "LONDON_PRE": (7, 11, 59),
        "HALT": (21, 22, 59),
    }
    if bucket not in ranges:
        return "n/a"
    start, end, minute = ranges[bucket]
    return f"{(start + offset) % 24:02d}:00-{(end + offset) % 24:02d}:{minute:02d} Dubai"


def us_dst_active(value_date: date) -> bool:
    march = date(value_date.year, 3, 1)
    first_sunday_march = 1 + ((6 - march.weekday()) % 7)
    second_sunday_march = first_sunday_march + 7
    november = date(value_date.year, 11, 1)
    first_sunday_november = 1 + ((6 - november.weekday()) % 7)
    return date(value_date.year, 3, second_sunday_march) <= value_date < date(value_date.year, 11, first_sunday_november)


def parse_mt5_datetime(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=None)


def filter_rows_for_date(rows: list[dict[str, str]], review_date: str) -> list[dict[str, str]]:
    dotted = review_date.replace("_", ".").replace("-", ".")
    dashed = review_date.replace("_", "-").replace(".", "-")
    return [
        row
        for row in rows
        if str(row.get("timestamp_broker", "")).startswith(dotted)
        or str(row.get("timestamp_utc", "")).startswith(dotted)
        or str(row.get("timestamp_broker", "")).startswith(dashed)
        or str(row.get("timestamp_utc", "")).startswith(dashed)
    ]


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
