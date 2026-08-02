from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_ROOT.parents[2]
MANIFEST = PACKAGE_ROOT / "recovery" / "recovery_manifest.json"
CONFIG = PACKAGE_ROOT / "config" / "v60_canonical_demo_portfolio_v2.json"
OVERLAY = PACKAGE_ROOT / "config" / "v60_portable_ml_topup_v4_overlay.json"
PROTECTION_OVERLAY = (
    PACKAGE_ROOT / "config" / "v60_drawdown_protection_v1_overlay.json"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def verify_repo(errors: list[str]) -> int:
    manifest = read_json(MANIFEST)
    require(
        manifest.get("schema_version") == "xauusd_v60_demo_recovery_manifest_v1",
        "Unexpected recovery manifest schema",
        errors,
    )
    for item in manifest.get("files", []):
        path = REPO_ROOT / str(item["path"])
        require(path.is_file(), f"Missing recovery file: {path}", errors)
        if path.is_file():
            require(
                sha256_file(path) == str(item["sha256"]),
                f"Recovery hash mismatch: {path}",
                errors,
            )

    config = read_json(CONFIG)
    overlay = read_json(OVERLAY)
    protection_overlay = read_json(PROTECTION_OVERLAY)
    require(
        int(config["account"]["expected_login"]) == 1033030,
        "Wrong recovery account login",
        errors,
    )
    require(
        config["account"]["expected_server"] == "Capital.ComMena-Demo",
        "Wrong recovery account server",
        errors,
    )
    require(
        config["authorization"]["live_authorized"] is False,
        "Live authorization must remain false",
        errors,
    )
    require(
        config["authorization"]["minimum_balance_requirement_enabled"] is False,
        "Minimum-balance gate must remain disabled",
        errors,
    )
    require(
        config["risk"]["equity_fraction_limits_enabled"] is True,
        "Equity-scaled risk limits must remain enabled",
        errors,
    )
    require(
        sha256_file(CONFIG) == overlay["base_config"]["sha256"],
        "ML overlay is not bound to the current base config",
        errors,
    )
    require(
        sha256_file(CONFIG) == protection_overlay["base_config"]["sha256"],
        "Protection overlay is not bound to the current base config",
        errors,
    )
    require(
        protection_overlay.get("portfolio_protection", {}).get("enabled") is True,
        "Drawdown protection is not enabled",
        errors,
    )
    parity = config["deployment_parity"]
    parity_path = REPO_ROOT / parity["artifact_path"]
    require(
        sha256_file(parity_path) == parity["artifact_sha256"],
        "Deployment parity identity changed",
        errors,
    )
    for key in ("serving_source", "implementation_lock", "model_bundle", "parity_result"):
        item = overlay["ml_topup"][key]
        path = REPO_ROOT / item["path"]
        require(
            path.is_file() and sha256_file(path) == item["sha256"],
            f"ML recovery artifact changed: {key}",
            errors,
        )
    return len(manifest.get("files", []))


def verify_terminal(terminal_root: Path, errors: list[str]) -> None:
    require(
        (terminal_root / "terminal64.exe").is_file(),
        f"MT5 terminal is missing: {terminal_root}",
        errors,
    )
    source_root = REPO_ROOT / "xau-usd" / "xauusd-phase1" / "mt5" / "Experts"
    deployed_root = terminal_root / "MQL5" / "Experts"
    for name in (
        "A1XauM5MomentumContinuationExecutor.mq5",
        "Account1DailyProfitFloorGuardian.mq5",
        "AccountEquityGuardianShadow.mq5",
        "XauProspectiveTelemetryCollector.mq5",
    ):
        source = source_root / name
        deployed = deployed_root / name
        require(
            deployed.is_file() and sha256_file(source) == sha256_file(deployed),
            f"Deployed EA source differs: {name}",
            errors,
        )
    profile_root = terminal_root / "MQL5" / "Profiles" / "Charts" / "Default"
    try:
        spec = importlib.util.spec_from_file_location(
            "v60_recovery_runtime",
            PACKAGE_ROOT / "run_portfolio.py",
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("Cannot load portfolio runtime")
        runtime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runtime)
        config = read_json(CONFIG)
        config["preflight"]["chart_profile_directory"] = str(profile_root)
        profile = runtime.audit_chart_profile(config, require_ready=True)
        require(profile["chart_count"] == 6, "Deployed profile must have six charts", errors)
    except Exception as exc:
        errors.append(f"Deployed chart profile failed semantic audit: {type(exc).__name__}: {exc}")
    status_path = terminal_root / "MQL5" / "Files" / "v60_canonical_demo_v2" / "status.json"
    if status_path.is_file():
        status = read_json(status_path)
        require(status.get("account_login") == 1033030, "Live status has wrong account", errors)
        require(
            status.get("status") == "ACTIVE_DEMO_BROKER_ACTION",
            "V60 runtime is not active",
            errors,
        )
        require(status.get("live_authorized") is False, "Live account is authorized", errors)
        require(
            status.get("portfolio_protection", {}).get("enabled") is True,
            "Drawdown protection is not active",
            errors,
        )
        require(
            status.get("profit_protection_close_failures") == 0,
            "Drawdown-protection close failure is active",
            errors,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the reproducible V60 demo package")
    parser.add_argument("--terminal-root", type=Path)
    args = parser.parse_args()
    errors: list[str] = []
    file_count = verify_repo(errors)
    if args.terminal_root is not None:
        verify_terminal(args.terminal_root.resolve(), errors)
    result = {
        "schema_version": "xauusd_v60_demo_recovery_verification_v1",
        "status": "PASS" if not errors else "FAIL",
        "manifest_files": file_count,
        "terminal_checked": args.terminal_root is not None,
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
