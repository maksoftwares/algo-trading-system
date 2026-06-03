from __future__ import annotations

from dataclasses import dataclass


ALLOWED_STATUSES = {
    "DRAFT",
    "LOCKED",
    "REJECTED",
    "OBSERVER_ONLY",
    "PHASE0R_PASS",
    "PAPER_APPROVED",
}

PASSIVE_DEFAULT_FLAGS = {
    "dry_run": True,
    "trade_permission": False,
    "broker_action_allowed": False,
    "phase2_execution_authorized": False,
}


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    version: str
    status: str
    mechanic_family: str
    decision_timeframe: str
    entry_timeframe: str
    expected_median_hold_hours: str
    expected_decisions_per_week: str
    expected_trades_per_year: str
    expected_median_stop_points: float
    same_family_as_breakout_retest: bool
    timeframe_diversification_qualifies: bool
    hypothesis_filename: str
    phase2_execution_authorized: bool = False
    trade_permission: bool = False
    broker_action_allowed: bool = False
    dry_run: bool = True

    @property
    def hypothesis_path(self) -> str:
        return f"hypotheses/{self.hypothesis_filename}"


CANDIDATES: tuple[Candidate, ...] = (
    Candidate(
        candidate_id="d1_compression_h4_expansion_v0",
        version="v0",
        status="DRAFT",
        mechanic_family="volatility expansion / compression-release",
        decision_timeframe="D1/H4",
        entry_timeframe="H4",
        expected_median_hold_hours="24-96",
        expected_decisions_per_week="0-2",
        expected_trades_per_year="<100",
        expected_median_stop_points=500.0,
        same_family_as_breakout_retest=False,
        timeframe_diversification_qualifies=True,
        hypothesis_filename="hypothesis_d1_compression_h4_expansion_v0.md",
    ),
    Candidate(
        candidate_id="h4_trend_pullback_d1_bias_v0",
        version="v0",
        status="DRAFT",
        mechanic_family="trend continuation / pullback",
        decision_timeframe="D1/H4",
        entry_timeframe="H4",
        expected_median_hold_hours="12-72",
        expected_decisions_per_week="2-6",
        expected_trades_per_year="100-300 maximum",
        expected_median_stop_points=375.0,
        same_family_as_breakout_retest=False,
        timeframe_diversification_qualifies=True,
        hypothesis_filename="hypothesis_h4_trend_pullback_d1_bias_v0.md",
    ),
    Candidate(
        candidate_id="weekly_level_h4_rejection_v0",
        version="v0",
        status="DRAFT",
        mechanic_family="higher-timeframe rejection / mean reversion",
        decision_timeframe="W1/D1/H4",
        entry_timeframe="H4",
        expected_median_hold_hours="24-120",
        expected_decisions_per_week="0-3",
        expected_trades_per_year="<150",
        expected_median_stop_points=425.0,
        same_family_as_breakout_retest=False,
        timeframe_diversification_qualifies=True,
        hypothesis_filename="hypothesis_weekly_level_h4_rejection_v0.md",
    ),
    Candidate(
        candidate_id="session_extreme_retest_v1_htf_confirmed",
        version="v1",
        status="DRAFT",
        mechanic_family="session extreme rejection / higher-timeframe confirmed retest",
        decision_timeframe="D1/H4/M15",
        entry_timeframe="M15",
        expected_median_hold_hours="6-48",
        expected_decisions_per_week="1-5",
        expected_trades_per_year="<120",
        expected_median_stop_points=500.0,
        same_family_as_breakout_retest=True,
        timeframe_diversification_qualifies=False,
        hypothesis_filename="hypothesis_session_extreme_retest_v1_htf_confirmed.md",
    ),
)


def candidate_ids() -> list[str]:
    return [candidate.candidate_id for candidate in CANDIDATES]


def candidate_map() -> dict[str, Candidate]:
    return {candidate.candidate_id: candidate for candidate in CANDIDATES}


def get_candidate(candidate_id: str) -> Candidate:
    candidates = candidate_map()
    if candidate_id not in candidates:
        available = ", ".join(sorted(candidates))
        raise KeyError(f"Unknown Phase 0R candidate {candidate_id!r}. Available: {available}")
    return candidates[candidate_id]


def selected_candidates(candidate_id: str) -> list[Candidate]:
    if candidate_id == "all":
        return list(CANDIDATES)
    return [get_candidate(candidate_id)]


def validate_candidate_registry() -> list[str]:
    errors: list[str] = []
    ids = candidate_ids()
    if len(ids) != len(set(ids)):
        errors.append("Candidate IDs must be unique.")
    for candidate in CANDIDATES:
        if candidate.status not in ALLOWED_STATUSES:
            errors.append(f"{candidate.candidate_id}: unsupported status {candidate.status}.")
        if not candidate.mechanic_family.strip():
            errors.append(f"{candidate.candidate_id}: mechanic family is required.")
        if candidate.same_family_as_breakout_retest is None:
            errors.append(f"{candidate.candidate_id}: same-family classification is required.")
        if candidate.phase2_execution_authorized:
            errors.append(f"{candidate.candidate_id}: Phase 2 execution cannot default to authorized.")
        if candidate.trade_permission:
            errors.append(f"{candidate.candidate_id}: trade permission cannot default to true.")
        if candidate.broker_action_allowed:
            errors.append(f"{candidate.candidate_id}: broker action cannot default to allowed.")
        if not candidate.dry_run:
            errors.append(f"{candidate.candidate_id}: dry-run must default to true.")
    return errors


def validate_status_transition(old_status: str, new_status: str) -> bool:
    if old_status not in ALLOWED_STATUSES or new_status not in ALLOWED_STATUSES:
        return False
    if old_status == "DRAFT" and new_status == "PAPER_APPROVED":
        return False
    if new_status == "PAPER_APPROVED" and old_status != "PHASE0R_PASS":
        return False
    return True
