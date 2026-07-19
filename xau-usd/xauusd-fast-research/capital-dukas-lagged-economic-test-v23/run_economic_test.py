from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from economic_test import (  # noqa: E402
    artifact_record,
    build_confirmation_candidates,
    build_confirmation_paired,
    canonical_hash,
    evaluate_economic_test,
    load_config,
    load_development_candidates,
    load_development_paired,
    resolve,
    sha256_file,
    verify_file_manifest,
    verify_locked_inputs,
)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def verify_contract(config: dict) -> dict:
    path = ROOT / config["outputs"]["directory"] / config["outputs"][
        "contract_lock"
    ]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if canonical_hash(payload, "contract_sha256") != payload["contract_sha256"]:
        raise ValueError("V23 contract self-hash mismatch")
    for record in payload["package_files"]:
        package_path = REPO / record["path"]
        if sha256_file(package_path) != record["sha256"]:
            raise ValueError(f"Locked V23 file changed: {record['path']}")
    verify_locked_inputs(config, ROOT)
    return payload


def main() -> int:
    config = load_config(ROOT)
    contract = verify_contract(config)
    capital_manifest_path = resolve(
        ROOT, str(config["confirmation"]["capital_manifest"])
    )
    dukascopy_manifest_path = resolve(
        ROOT, str(config["confirmation"]["dukascopy_manifest"])
    )
    capital_manifest = json.loads(
        capital_manifest_path.read_text(encoding="utf-8")
    )
    dukascopy_manifest = json.loads(
        dukascopy_manifest_path.read_text(encoding="utf-8")
    )
    verify_file_manifest(capital_manifest, "capital_files")
    verify_file_manifest(dukascopy_manifest, "dukascopy_files")
    if int(dukascopy_manifest["dukascopy_file_count"]) != int(
        contract["dukascopy_expected_file_count"]
    ):
        raise ValueError("V23 Dukascopy confirmation inventory is incomplete")
    development_paired = load_development_paired(config, ROOT)
    development_candidates = load_development_candidates(config, ROOT)
    confirmation_paired, pairing_audit = build_confirmation_paired(
        config, capital_manifest, ROOT
    )
    confirmation_candidates = build_confirmation_candidates(
        confirmation_paired, config, ROOT
    )
    candidates, trades, metrics, daily_pnl, audit = evaluate_economic_test(
        development_paired,
        confirmation_paired,
        development_candidates,
        confirmation_candidates,
        config,
    )
    audit.update(
        {
            "contract_sha256": contract["contract_sha256"],
            "capital_source_manifest_sha256": capital_manifest[
                "manifest_sha256"
            ],
            "dukascopy_source_manifest_sha256": dukascopy_manifest[
                "manifest_sha256"
            ],
            "confirmation_pairing_audit": pairing_audit,
            "paid_source_used": bool(dukascopy_manifest["paid_source_used"]),
        }
    )
    output = ROOT / config["outputs"]["directory"]
    keys = (
        "confirmation_paired_quotes",
        "candidates",
        "trades",
        "metrics",
        "daily_pnl",
        "audit_json",
        "audit_markdown",
        "artifact_manifest",
    )
    paths = {key: output / config["outputs"][key] for key in keys}
    confirmation_paired.to_parquet(paths["confirmation_paired_quotes"], index=False)
    candidates.to_parquet(paths["candidates"], index=False)
    trades.to_parquet(paths["trades"], index=False)
    metrics.to_csv(paths["metrics"], index=False, lineterminator="\n")
    daily_pnl.to_csv(paths["daily_pnl"], index=False, lineterminator="\n")
    write_json(paths["audit_json"], audit)
    from economic_test import render_markdown

    paths["audit_markdown"].write_text(
        render_markdown(audit), encoding="utf-8"
    )
    artifact_keys = (
        "confirmation_paired_quotes",
        "candidates",
        "trades",
        "metrics",
        "daily_pnl",
        "audit_json",
        "audit_markdown",
    )
    manifest = {
        "schema_version": config["schema_version"],
        "contract_sha256": contract["contract_sha256"],
        "capital_source_manifest_sha256": capital_manifest["manifest_sha256"],
        "dukascopy_source_manifest_sha256": dukascopy_manifest["manifest_sha256"],
        "artifacts": [artifact_record(paths[key]) for key in artifact_keys],
        "strategy_admission_authorized": False,
        "model_training_authorized": False,
        "execution_authorized": False,
    }
    write_json(paths["artifact_manifest"], manifest)
    print(json.dumps(audit, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
