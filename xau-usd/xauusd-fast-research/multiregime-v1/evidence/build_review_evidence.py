from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


LANE = Path(__file__).resolve().parents[1]
REPO = LANE.parents[2]
EVIDENCE = LANE / "evidence"
RESEARCH_COMMIT = "3765751bd5589dd6f67366cb4c2194f1e31680e0"
RESULT_RELATIVE = "xau-usd/xauusd-fast-research/multiregime-v1/outputs/MULTIREGIME_FAST_DISCOVERY_RESULT.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def portable(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def item(path: Path) -> dict[str, Any]:
    return {"path": portable(path), "size_bytes": path.stat().st_size, "sha256": sha256(path)}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def committed_result() -> dict[str, Any]:
    raw = subprocess.check_output(["git", "show", f"{RESEARCH_COMMIT}:{RESULT_RELATIVE}"], cwd=REPO)
    return json.loads(raw.decode("utf-8"))


def build_reconciliation(current: dict[str, Any]) -> None:
    original = committed_result()
    family_unchanged = original["family_summaries"] == current["family_summaries"]
    portfolio_unchanged = original["portfolio_summary"] == current["portfolio_summary"]
    payload = {
        "schema_version": "xauusd_multiregime_economic_reconciliation_v1",
        "research_commit": RESEARCH_COMMIT,
        "classification_before": original["decision"],
        "classification_after": current["decision"],
        "narrative_disposition": current["narrative_disposition"],
        "family_metrics_byte_semantics_unchanged": family_unchanged,
        "portfolio_metrics_byte_semantics_unchanged": portfolio_unchanged,
        "family_summaries": current["family_summaries"],
        "portfolio_summary": current["portfolio_summary"],
        "sizing_reconciliation": {
            key: current["gate_audit"][key]
            for key in (
                "raw_strategy_opportunities", "sizing_evaluated_opportunities",
                "sizing_accepted_opportunities", "contract_granularity_rejects",
                "margin_rejects", "other_sizing_rejects", "reject_rate_denominator",
                "reject_rate_pct", "contract_granularity_reject_pct", "sizing_reconciliation_valid",
            )
        },
    }
    if not family_unchanged or not portfolio_unchanged:
        raise RuntimeError("Economic result changed during evidence correction")
    write_json(EVIDENCE / "ECONOMIC_RESULT_RECONCILIATION.json", payload)


def build_segment_account(current: dict[str, Any]) -> None:
    segment_rows = (LANE / "outputs" / "MULTIREGIME_SEGMENT_RESULTS.csv").read_text(encoding="utf-8").splitlines()
    segment_d = [line for line in segment_rows[1:] if ",D," in line]
    payload = {
        "schema_version": "xauusd_multiregime_segment_d_account_evidence_v1",
        "coverage": current["coverage"],
        "segment_d_rows_csv": segment_d,
        "locked_tail_sources": {
            timeframe: current["source_manifest"][timeframe]["locked_tail"]
            for timeframe in ("M5", "M15", "H1", "H4")
        },
        "captured_mt5_contract": current["captured_mt5_contract"],
        "account_audit": current["account_audit"],
        "account_feasibility": current["gate_audit"],
        "portfolio_admitted_families": current["portfolio_admitted_families"],
    }
    write_json(EVIDENCE / "SEGMENT_D_AND_ACCOUNT_EVIDENCE.json", payload)


def inventory(paths: list[Path]) -> list[dict[str, Any]]:
    return [item(path) for path in sorted(set(paths), key=lambda value: portable(value))]


def build_manifest(current: dict[str, Any]) -> None:
    code = [LANE / ".gitattributes", LANE / ".gitignore", LANE / "README.md", LANE / "run_multiregime_fast_discovery_v1.py"]
    code += list((LANE / "src").glob("*.py")) + list((LANE / "tests").glob("*.py")) + [Path(__file__).resolve()]
    configuration = list((LANE / "config").glob("*"))
    outputs = list((LANE / "outputs").glob("*"))
    inputs: list[Path] = []
    for timeframe in ("M5", "M15", "H1", "H4"):
        inputs.append(REPO / current["source_manifest"][timeframe]["historical"]["path"])
        inputs.append(REPO / current["source_manifest"][timeframe]["locked_tail"]["path"])
    inputs.append(REPO / current["source_manifest"]["contract_snapshot"]["path"])
    excluded = {"MULTIREGIME_RUN_MANIFEST.json", "build_review_evidence.py"}
    evidence = [path for path in EVIDENCE.glob("*") if path.is_file() and path.name not in excluded]
    payload = {
        "schema_version": "xauusd_multiregime_run_manifest_v1",
        "branch": "codex/xau-multiregime-fast-discovery-v1",
        "base_commit": "50bf9b5dbcc563a20254e9041e41ec0762c86f6e",
        "research_commit": RESEARCH_COMMIT,
        "research_tree": "d8503b12783d2e571d98fee2a8619583c6904d06",
        "research_parent": "50bf9b5dbcc563a20254e9041e41ec0762c86f6e",
        "machine_classification": current["decision"],
        "narrative_disposition": current["narrative_disposition"],
        "inventory": {
            "code_and_tests": inventory(code),
            "configuration": inventory(configuration),
            "inputs_and_sources": inventory(inputs),
            "outputs": inventory(outputs),
            "review_evidence": inventory(evidence),
        },
        "inventory_rules": {
            "paths_are_repository_relative_posix": True,
            "absolute_machine_paths_prohibited": True,
            "manifest_excludes_itself_to_avoid_recursive_hashing": True,
        },
    }
    serialized = json.dumps(payload, sort_keys=True)
    if str(REPO) in serialized or "\\" in serialized:
        raise RuntimeError("Manifest contains a machine path or non-portable separator")
    write_json(EVIDENCE / "MULTIREGIME_RUN_MANIFEST.json", payload)


def main() -> int:
    current = json.loads((LANE / "outputs" / "MULTIREGIME_FAST_DISCOVERY_RESULT.json").read_text(encoding="utf-8"))
    build_reconciliation(current)
    build_segment_account(current)
    build_manifest(current)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
