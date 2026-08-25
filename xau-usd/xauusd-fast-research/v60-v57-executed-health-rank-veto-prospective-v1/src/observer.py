from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "prospective.json"


def utc_time(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp is not timezone-aware: {value}")
    return parsed.astimezone(UTC)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_repo(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else REPO_ROOT / path


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at {path}:{number}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"Non-object JSONL row at {path}:{number}")
        rows.append(value)
    return rows


def load_candidate_rows(
    inputs: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_config_text = inputs.get("candidate_source_config")
    if not source_config_text:
        path = Path(str(inputs["candidate_ledger"]))
        rows = read_jsonl(path)
        return rows, [{"path": str(path), "exists": True, "rows": len(rows)}]

    source_config = read_json(resolve_repo(str(source_config_text)))
    sources = list(source_config["sources"])
    path_counts: dict[str, int] = {}
    for source in sources:
        key = str(Path(str(source["path"])).resolve())
        path_counts[key] = path_counts.get(key, 0) + 1

    cache: dict[str, list[dict[str, Any]]] = {}
    candidates: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    for source in sources:
        source_id = str(source["source_id"])
        specialist_id = str(source["specialist_id"])
        time_field = str(source["time_field"])
        path = Path(str(source["path"]))
        key = str(path.resolve())
        exists = path.exists()
        if key not in cache:
            cache[key] = read_jsonl(path) if exists else []
        accepted = []
        for raw in cache[key]:
            row_specialist = raw.get("specialist_id")
            if row_specialist is None and path_counts[key] > 1:
                raise ValueError(
                    f"Shared candidate ledger row has no specialist_id: {path}"
                )
            if row_specialist is not None and str(row_specialist) != specialist_id:
                continue
            if "candidate_id" not in raw or time_field not in raw:
                raise ValueError(
                    f"Candidate row for {source_id} lacks candidate_id or {time_field}"
                )
            normalized = dict(raw)
            normalized["specialist_id"] = source_id
            normalized["scheduled_entry_time_utc"] = raw[time_field]
            normalized["event_id"] = str(
                raw.get("event_id", raw["candidate_id"])
            )
            accepted.append(normalized)
        candidates.extend(accepted)
        audit.append(
            {
                "source_id": source_id,
                "path": str(path),
                "exists": exists,
                "rows": len(accepted),
            }
        )

    candidate_ids = [str(row["candidate_id"]) for row in candidates]
    if len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("Candidate ledgers contain duplicate candidate_id values")
    return candidates, audit


def profit_factor(values: Sequence[float]) -> float:
    gross_profit = sum(value for value in values if value > 0.0)
    gross_loss = -sum(value for value in values if value < 0.0)
    if gross_loss == 0.0:
        return math.inf if gross_profit > 0.0 else 0.0
    return gross_profit / gross_loss


def load_locked_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = read_json(path)
    authorization = config["authorization"]
    if not bool(authorization.get("read_only_mt5")):
        raise ValueError("MT5 observer must be explicitly read-only")
    if any(
        bool(authorization.get(key))
        for key in ("broker_actions", "runtime_changes", "demo_deployment", "live_deployment")
    ):
        raise ValueError("Prospective observer has forbidden authorization")
    challenger_path = resolve_repo(config["lock"]["challenger_config"])
    if sha256_file(challenger_path) != config["lock"]["challenger_config_sha256"]:
        raise ValueError("Locked V1 challenger config changed")
    challenger = read_json(challenger_path)
    if challenger["policy"] != config["lock"]["policy"]:
        raise ValueError("Prospective policy differs from V1")
    warm_start_text = config.get("read_only_inputs", {}).get("warm_start")
    if warm_start_text:
        warm_start_path = resolve_repo(str(warm_start_text))
        expected = str(config["lock"]["warm_start_sha256"])
        if sha256_file(warm_start_path) != expected:
            raise ValueError("Locked prospective warm start changed")
    source_config_text = config.get("read_only_inputs", {}).get(
        "candidate_source_config"
    )
    if source_config_text:
        source_config_path = resolve_repo(str(source_config_text))
        expected = str(config["lock"]["candidate_source_config_sha256"])
        if sha256_file(source_config_path) != expected:
            raise ValueError("Locked candidate source config changed")
    return config


def deal_value(deal: Any, name: str) -> Any:
    return deal[name] if isinstance(deal, Mapping) else getattr(deal, name)


def broker_outcomes(
    state: Mapping[str, Any],
    deals: Sequence[Any],
    *,
    source_id: str,
    magic: int | Mapping[str, int],
    account_currency_per_usd: float,
) -> dict[str, dict[str, Any]]:
    by_position: dict[int, list[Any]] = {}
    for deal in deals:
        position_id = int(deal_value(deal, "position_id"))
        by_position.setdefault(position_id, []).append(deal)

    outcomes: dict[str, dict[str, Any]] = {}
    for candidate_id, position in state.get("positions", {}).items():
        position_source = str(position.get("source_id"))
        if source_id != "*" and position_source != source_id:
            continue
        expected_magic = (
            int(magic[position_source]) if isinstance(magic, Mapping) else int(magic)
        )
        ticket = int(position["ticket"])
        rows = by_position.get(ticket, [])
        entries = [
            row
            for row in rows
            if int(deal_value(row, "entry")) == 0
            and int(deal_value(row, "magic")) == expected_magic
        ]
        exits = [row for row in rows if int(deal_value(row, "entry")) != 0]
        opened_volume = sum(float(deal_value(row, "volume")) for row in entries)
        closed_volume = sum(float(deal_value(row, "volume")) for row in exits)
        if not entries or not exits or closed_volume + 1e-9 < opened_volume:
            continue
        pnl_account = sum(
            sum(float(deal_value(row, key)) for key in ("profit", "commission", "swap", "fee"))
            for row in rows
        )
        outcomes[str(candidate_id)] = {
            "source_id": position_source,
            "ticket": ticket,
            "opened_at_utc": datetime.fromtimestamp(
                min(int(deal_value(row, "time_msc")) for row in entries) / 1000.0,
                UTC,
            ),
            "closed_at_utc": datetime.fromtimestamp(
                max(int(deal_value(row, "time_msc")) for row in exits) / 1000.0,
                UTC,
            ),
            "pnl_usd": pnl_account / account_currency_per_usd,
        }
    return outcomes


def build_snapshot(
    config: Mapping[str, Any],
    deals: Sequence[Any],
    *,
    now: datetime | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    now = (now or datetime.now(UTC)).astimezone(UTC)
    inputs = config["read_only_inputs"]
    candidates, candidate_ledger_audit = load_candidate_rows(inputs)
    state = read_json(Path(inputs["portfolio_state"]))
    policy = config["lock"]["policy"]
    source_id = str(policy["source_id"])
    boundary = utc_time(config["lock"]["evidence_start_inclusive_utc"])
    magic: int | Mapping[str, int] = int(config["account"].get("magic", 0))
    if source_id == "*":
        magic = {
            str(key): int(value)
            for key, value in config["account"]["source_magics"].items()
        }
    outcomes = broker_outcomes(
        state,
        deals,
        source_id=source_id,
        magic=magic,
        account_currency_per_usd=float(config["account"]["account_currency_per_usd"]),
    )
    warm_start_count = 0
    warm_start_text = inputs.get("warm_start")
    if warm_start_text:
        warm_start = read_json(resolve_repo(str(warm_start_text)))
        for row in warm_start["rows"]:
            candidate_id = str(row["candidate_id"])
            if candidate_id in outcomes:
                raise ValueError(f"Warm-start outcome collides with broker outcome: {candidate_id}")
            closed_at = utc_time(row["closed_at_utc"])
            if closed_at >= boundary:
                raise ValueError("Warm-start outcome crosses the prospective boundary")
            outcomes[candidate_id] = {
                "source_id": str(row["source_id"]),
                "closed_at_utc": closed_at,
                "pnl_usd": float(row["pnl_usd"]),
                "warm_start": True,
            }
            warm_start_count += 1
    decisions = state.get("ml_topup", {}).get("decisions", {})
    positions = state.get("positions", {})
    source_candidates = sorted(
        (
            row
            for row in candidates
            if source_id == "*" or str(row.get("specialist_id")) == source_id
        ),
        key=lambda row: (utc_time(row["scheduled_entry_time_utc"]), str(row["candidate_id"])),
    )
    vetoed: set[str] = set()
    observed: list[dict[str, Any]] = []
    for candidate in source_candidates:
        candidate_id = str(candidate["candidate_id"])
        entry = utc_time(candidate["scheduled_entry_time_utc"])
        if entry < boundary:
            continue
        baseline_executed = candidate_id in positions
        candidate_source = str(candidate["specialist_id"])
        eligible_prior = [
            (prior_id, outcome)
            for prior_id, outcome in outcomes.items()
            if outcome["closed_at_utc"] <= entry and prior_id not in vetoed
            and str(outcome["source_id"]) == candidate_source
        ]
        eligible_prior.sort(key=lambda item: (item[1]["closed_at_utc"], item[0]))
        health_prior = eligible_prior
        if str(policy.get("health_scope", "ALL_CAUSAL_OUTCOMES")) == "BROKER_OUTCOMES_ONLY":
            health_prior = [
                item for item in eligible_prior if not bool(item[1].get("warm_start"))
            ]
        prior_values = [
            float(item[1]["pnl_usd"])
            for item in health_prior[-int(policy["lookback_closed_trades"]):]
        ]
        minimum_source_history = int(
            policy.get(
                "minimum_prior_source_closed_trades",
                policy["lookback_closed_trades"],
            )
        )
        prior_pf = (
            profit_factor(prior_values)
            if len(eligible_prior) >= minimum_source_history
            and len(prior_values) >= int(policy["lookback_closed_trades"])
            else None
        )
        model = decisions.get(candidate_id, {})
        rank = (
            float(model["rank"])
            if model.get("reason") == "SCORE_COMPLETE" and model.get("rank") is not None
            else None
        )
        would_veto = bool(
            baseline_executed
            and prior_pf is not None
            and math.isfinite(prior_pf)
            and prior_pf < float(policy["maximum_prior_profit_factor_exclusive"])
            and rank is not None
            and math.isfinite(rank)
            and rank < float(policy["maximum_causal_rank_exclusive"])
        )
        if would_veto:
            vetoed.add(candidate_id)
        outcome = outcomes.get(candidate_id)
        if not baseline_executed:
            evidence_status = "BASELINE_NOT_EXECUTED"
        elif rank is None:
            evidence_status = "AWAITING_CAUSAL_RANK"
        elif prior_pf is None:
            evidence_status = "INCOMPLETE_EXECUTED_HEALTH"
        elif would_veto and outcome is None:
            evidence_status = "VETO_AWAITING_BROKER_OUTCOME"
        elif would_veto:
            evidence_status = "VETO_RESOLVED"
        else:
            evidence_status = "RETAIN"
        observed.append(
            {
                "candidate_id": candidate_id,
                "event_id": str(candidate["event_id"]),
                "source_id": candidate_source,
                "entry_time_utc": entry.isoformat().replace("+00:00", "Z"),
                "baseline_executed": baseline_executed,
                "causal_rank": rank,
                "prior_source_executed_count": len(eligible_prior),
                "prior_health_window_count": len(prior_values),
                "prior_executed_profit_factor": (
                    prior_pf if prior_pf is not None and math.isfinite(prior_pf) else None
                ),
                "would_veto": would_veto,
                "broker_outcome_resolved": outcome is not None,
                "broker_exit_time_utc": (
                    outcome["closed_at_utc"].isoformat().replace("+00:00", "Z")
                    if outcome is not None
                    else None
                ),
                "broker_pnl_usd": float(outcome["pnl_usd"]) if outcome is not None else None,
                "evidence_status": evidence_status,
            }
        )

    executed_scored = [
        row for row in observed if row["baseline_executed"] and row["causal_rank"] is not None
    ]
    vetoes = [row for row in observed if row["would_veto"]]
    resolved_vetoes = [row for row in vetoes if row["broker_outcome_resolved"]]
    veto_values = [float(row["broker_pnl_usd"]) for row in resolved_vetoes]
    veto_pf = profit_factor(veto_values) if veto_values else None
    avoided_pnl = -sum(veto_values)
    acceptance = config["acceptance"]
    elapsed_days = max(0.0, (now - boundary).total_seconds() / 86400.0)
    gates = {
        "minimum_elapsed_days": elapsed_days >= float(acceptance["minimum_elapsed_days"]),
        "minimum_scored_executed_candidates": len(executed_scored)
        >= int(acceptance["minimum_scored_executed_candidates"]),
        "minimum_resolved_vetoes": len(resolved_vetoes)
        >= int(acceptance["minimum_resolved_vetoes"]),
        "veto_broker_profit_factor": veto_pf is not None
        and veto_pf < float(acceptance["maximum_veto_broker_profit_factor_exclusive"]),
        "positive_avoided_broker_pnl": avoided_pnl
        > float(acceptance["minimum_avoided_broker_pnl_usd_exclusive"]),
    }
    status = {
        "schema_version": config["schema_version"] + "_status",
        "generated_at_utc": now.isoformat().replace("+00:00", "Z"),
        "evidence_start_inclusive_utc": boundary.isoformat().replace("+00:00", "Z"),
        "decision": (
            "PROSPECTIVE_CONFIRMATION_PASSES_REVIEW_REQUIRED"
            if all(gates.values())
            else "KEEP_DEPLOYED_V60_CONTINUE_COLLECTION"
        ),
        "deployment_authorized": False,
        "broker_action_authorized": False,
        "policy": policy,
        "counts": {
            "candidates": len(observed),
            "executed_scored_candidates": len(executed_scored),
            "veto_opportunities": len(vetoes),
            "resolved_vetoes": len(resolved_vetoes),
            "warm_start_outcomes": warm_start_count,
        },
        "candidate_ledger_audit": candidate_ledger_audit,
        "veto_broker_net_pnl_usd": sum(veto_values),
        "avoided_broker_pnl_usd": avoided_pnl,
        "veto_broker_profit_factor": (
            veto_pf if veto_pf is not None and math.isfinite(veto_pf) else None
        ),
        "elapsed_days": elapsed_days,
        "gates": gates,
        "limitations": [
            "The observer is read-only and cannot change a broker order.",
            "Only actual baseline executions can be evaluated prospectively.",
            "A passing result still requires review and explicit deployment authorization.",
        ],
    }
    return status, observed


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_snapshot(config: Mapping[str, Any], status: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> None:
    output = Path(config["outputs"]["runtime_directory"])
    atomic_write(output / "STATUS.json", json.dumps(status, indent=2, sort_keys=True) + "\n")
    atomic_write(
        output / "CANDIDATES.jsonl",
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
    )
