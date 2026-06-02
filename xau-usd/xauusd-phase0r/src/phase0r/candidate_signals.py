from __future__ import annotations

from dataclasses import dataclass

from phase0r.candidate_registry import get_candidate


@dataclass(frozen=True)
class CandidateSignalContract:
    candidate_id: str
    decision_timeframe: str
    entry_timeframe: str
    passive_only: bool
    notes: str


def signal_contract(candidate_id: str) -> CandidateSignalContract:
    candidate = get_candidate(candidate_id)
    return CandidateSignalContract(
        candidate_id=candidate.candidate_id,
        decision_timeframe=candidate.decision_timeframe,
        entry_timeframe=candidate.entry_timeframe,
        passive_only=True,
        notes="Phase 0R signal implementation is intentionally gated behind hypothesis lock.",
    )


def build_candidate_signals(*_args: object, **_kwargs: object) -> list[object]:
    raise NotImplementedError(
        "Phase 0R signal generation is not enabled until the candidate hypothesis is LOCKED."
    )
