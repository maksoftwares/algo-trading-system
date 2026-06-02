from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_FIELDS = (
    "Expert candidate ID",
    "Version",
    "Status",
    "Mechanic family",
    "Entry / decision timeframe",
    "Reference timeframe",
    "Expected median hold bars M5-equivalent",
    "Expected median hold hours",
    "Expected decisions per week",
    "Expected trades per year",
    "Timeframe diversification qualifies",
    "Same-family as breakout_retest",
    "Expected median stop distance points",
    "Expected median cost_R under measured P95 spread",
    "Expected PF after measured cost",
    "Expected average net R",
    "Expected win rate range",
    "Expected worst month R",
    "Expected losing-month percentage",
    "Expected max zero-trade months",
    "Why this behavior should exist on XAUUSD",
    "What would falsify this hypothesis",
    "Forbidden changes after lock",
    "Allowed bug fixes after lock",
)

ALLOWED_HYPOTHESIS_STATUSES = {"DRAFT", "LOCKED", "REJECTED", "OBSERVER_ONLY", "PHASE0R_PASS"}
MANIFEST_FIELDS = (
    "candidate_id",
    "version",
    "status",
    "hypothesis_path",
    "sha256",
    "registered_at_utc",
    "registered_by",
    "notes",
)


@dataclass(frozen=True)
class HypothesisValidation:
    path: Path
    fields: dict[str, str]
    missing_fields: tuple[str, ...]
    placeholder_fields: tuple[str, ...]

    @property
    def status(self) -> str:
        return "PASS" if not self.missing_fields and not self.placeholder_fields else "FAIL"


def hypothesis_paths(root: Path) -> list[Path]:
    return sorted((root / "hypotheses").glob("hypothesis_*.md"))


def parse_hypothesis_fields(path: Path) -> dict[str, str]:
    fields: dict[str, str] = {}
    in_code_block = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key in REQUIRED_FIELDS:
            fields[key] = value.strip()
    return fields


def validate_hypothesis_file(path: Path) -> HypothesisValidation:
    fields = parse_hypothesis_fields(path)
    missing = tuple(field for field in REQUIRED_FIELDS if field not in fields or fields[field] == "")
    placeholders = tuple(
        field
        for field, value in fields.items()
        if value.strip().upper() in {"TBD", "TODO", "PLACEHOLDER", "UNKNOWN"}
    )
    status = fields.get("Status")
    if status and status not in ALLOWED_HYPOTHESIS_STATUSES:
        placeholders = (*placeholders, "Status")
    return HypothesisValidation(path, fields, missing, placeholders)


def validate_hypotheses_complete(root: Path) -> list[HypothesisValidation]:
    return [validate_hypothesis_file(path) for path in hypothesis_paths(root)]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def register_hypotheses(
    root: Path,
    registered_by: str = "codex",
    notes: str = "draft separate Phase 0R lane registration",
) -> Path:
    manifest_path = root / "outputs" / "hypothesis_hash_manifest.csv"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    registered_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    rows = []
    for path in hypothesis_paths(root):
        validation = validate_hypothesis_file(path)
        fields = validation.fields
        rows.append(
            {
                "candidate_id": fields.get("Expert candidate ID", ""),
                "version": fields.get("Version", ""),
                "status": fields.get("Status", ""),
                "hypothesis_path": str(path.relative_to(root)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "registered_at_utc": registered_at,
                "registered_by": registered_by,
                "notes": notes,
            }
        )
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return manifest_path


def locked_hypotheses_match_manifest(root: Path, manifest_path: Path | None = None) -> list[str]:
    manifest_path = manifest_path or root / "outputs" / "hypothesis_hash_manifest.csv"
    if not manifest_path.exists():
        return ["Hypothesis hash manifest is missing."]

    errors: list[str] = []
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("status") != "LOCKED":
                continue
            hypothesis_path = root / str(row.get("hypothesis_path", ""))
            if not hypothesis_path.exists():
                errors.append(f"{row.get('candidate_id')}: locked hypothesis file is missing.")
                continue
            current_hash = sha256_file(hypothesis_path)
            if current_hash != row.get("sha256"):
                errors.append(f"{row.get('candidate_id')}: locked hypothesis hash changed without version bump.")
    return errors
