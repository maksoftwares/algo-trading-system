from __future__ import annotations

import hashlib
import json
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_ROOT.parents[2]
OUTPUT = PACKAGE_ROOT / "recovery" / "recovery_manifest.json"

CRITICAL_FILES = [
    "multi-asset/data-foundation/dukascopy-ticks-v1/src/dukascopy_tick_foundation/foundation.py",
    "xau-usd/operations/v60-prospective-supervisor-v1/config/runtime_supervisor_v1.json",
    "xau-usd/operations/v60-prospective-supervisor-v1/deployed_specialist_monitor.py",
    "xau-usd/operations/v60-prospective-supervisor-v1/README.md",
    "xau-usd/operations/v60-prospective-supervisor-v1/runtime_status.py",
    "xau-usd/operations/v60-prospective-supervisor-v1/runtime_supervisor.ps1",
    "xau-usd/operations/v60-prospective-supervisor-v1/start_supervisor.ps1",
    "xau-usd/operations/v60-prospective-supervisor-v1/stop_supervisor.ps1",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/apply_safety_repair.ps1",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/build_drawdown_protection_comparison.py",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/config/v60_canonical_demo_portfolio_v2.json",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/config/v60_drawdown_protection_v1_overlay.json",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/config/v60_portable_ml_topup_v4_overlay.json",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/evidence/V60_CANONICAL_DEMO_DEPLOYMENT_PARITY_V1.json",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/evidence/V60_DRAWDOWN_PROTECTION_V1_COMPARISON_20260802.json",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/evidence/V60_DRAWDOWN_PROTECTION_V1_COMPARISON_20260802.md",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/evidence/V60_DRAWDOWN_RECOVERY_V2_REPLAY_20260806.json",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/evidence/V60_DRAWDOWN_RECOVERY_V2_REPLAY_20260806.md",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/evidence/V60_DRAWDOWN_RECOVERY_V2_FULL_REPLAY_RESULT_20260806.json",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/evidence/V60_SAFETY_REPAIR_AFTER_REPLAY_RESULT_20260730.json",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/evidence/V60_SAFETY_REPAIR_BEFORE_AFTER_20260730.json",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/evidence/V60_SAFETY_REPAIR_BEFORE_REPLAY_RESULT_20260730.json",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/requirements-runtime.txt",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/requirements-runtime.lock.txt",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/RECOVERY_RUNBOOK.md",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/README.md",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/recovery/build_recovery_manifest.py",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/recovery/verify_recovery.py",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/restore_mt5_profile.ps1",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/restore_v60_demo.ps1",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/run_feeds.py",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/run_portfolio.py",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/run_research_feeds.py",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/set_terminal_algo_trading.ps1",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/src/addons.py",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/src/executor.py",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/src/feeds.py",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/src/ml_topup.py",
    "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/start_portfolio.ps1",
    "xau-usd/xauusd-fast-research/codex-v60-tick-runtime-replay-v1/config/SAFETY_REPAIR_REPLAY_CONTRACT.json",
    "xau-usd/xauusd-fast-research/codex-v60-tick-runtime-replay-v1/config/DRAWDOWN_PROTECTION_V1_REPLAY_CONTRACT.json",
    "xau-usd/xauusd-fast-research/codex-v60-tick-runtime-replay-v1/evidence/GUARDIAN_EXIT_MAGIC_OBSERVATION.json",
    "xau-usd/xauusd-fast-research/codex-v60-tick-runtime-replay-v1/run_replay.py",
    "xau-usd/xauusd-fast-research/codex-v60-tick-runtime-replay-v1/src/replay.py",
    "xau-usd/xauusd-fast-research/codex-v60-portable-mature-topup-prospective-v3/config/IMPLEMENTATION_LOCK.json",
    "xau-usd/xauusd-fast-research/codex-v60-portable-mature-topup-prospective-v3/outputs/MODEL_BUNDLE.joblib",
    "xau-usd/xauusd-fast-research/codex-v60-portable-mature-topup-prospective-v3/outputs/PARITY_RESULT.json",
    "xau-usd/xauusd-fast-research/codex-v60-portable-mature-topup-prospective-v3/src/serving.py",
    "xau-usd/xauusd-fast-research/high-frequency-expansion-v1/outputs/HIGH_FREQUENCY_EXPANSION_ACTION_LABELS.parquet",
    "xau-usd/xauusd-fast-research/high-frequency-expansion-v1/src/dataset.py",
    "xau-usd/xauusd-fast-research/independent-specialists-v1/src/research.py",
    "xau-usd/xauusd-fast-research/pullback-swing-replication-v7/outputs/PULLBACK_SWING_REPLICATION_V7_TRADES.parquet",
    "xau-usd/xauusd-fast-research/one-trade-per-day-floating-equity-v60/outputs/ONE_TRADE_PER_DAY_FLOATING_EQUITY_V60_PRICE_LEDGER.parquet",
    "xau-usd/xauusd-fast-research/chop-failed-reversion-rawtick-v25/config/chop_failed_reversion_rawtick_v25.json",
    "xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5",
    "xau-usd/xauusd-phase1/mt5/Experts/Account1DailyProfitFloorGuardian.mq5",
    "xau-usd/xauusd-phase1/mt5/Experts/AccountEquityGuardianShadow.mq5",
    "xau-usd/xauusd-phase1/mt5/Experts/XauProspectiveTelemetryCollector.mq5",
    "xau-usd/xauusd-phase1/scripts/run_xau_specialist_shadow.py",
    "xau-usd/xauusd-phase1/outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_INPUTS_20260710/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710_NATIVE_POSITION_RECONCILIATION.csv",
]

DEPENDENCY_TREES = [
    "xau-usd/xauusd-fast-research/capital-core-causal-outcome-resolver-v40",
    "xau-usd/xauusd-fast-research/capital-core-same-period-shadow-v28",
    "xau-usd/xauusd-fast-research/capital-r1-pullback-forward-v29",
    "xau-usd/xauusd-fast-research/capital-r4-chop-forward-v34",
    "xau-usd/xauusd-fast-research/capital-r5-causal-outcome-resolver-v38",
    "xau-usd/xauusd-fast-research/capital-r5-causal-router-v39",
    "xau-usd/xauusd-fast-research/capital-r5-transition-forward-v35",
]

EXCLUDED_PARTS = {".git", ".pytest_cache", ".venv", "__pycache__"}
EXCLUDED_SUFFIXES = {".log", ".pyc"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def included(path: Path) -> bool:
    return not EXCLUDED_PARTS.intersection(path.parts) and (
        path.suffix.lower() not in EXCLUDED_SUFFIXES
    )


def manifest_paths() -> list[str]:
    paths = set(CRITICAL_FILES)
    for chart in sorted((PACKAGE_ROOT / "recovery" / "mt5-profile" / "Default").glob("chart*.chr")):
        paths.add(chart.relative_to(REPO_ROOT).as_posix())
    for relative in DEPENDENCY_TREES:
        root = REPO_ROOT / relative
        for path in root.rglob("*"):
            if path.is_file() and included(path):
                paths.add(path.relative_to(REPO_ROOT).as_posix())
    return sorted(paths)


def main() -> int:
    rows = []
    missing = []
    for relative in manifest_paths():
        path = REPO_ROOT / relative
        if not path.is_file():
            missing.append(relative)
            continue
        rows.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    if missing:
        raise FileNotFoundError(f"Missing recovery inputs: {missing}")
    payload = {
        "schema_version": "xauusd_v60_demo_recovery_manifest_v1",
        "recovery_tag": "v60-demo-recovery-20260818-runtime-isolation",
        "recovery_variant": "runtime-feed-isolation-v3-20260818",
        "account_login": 1033030,
        "account_server": "Capital.ComMena-Demo",
        "terminal_root": "C:/MT5PortableTier1BestEA",
        "python_version": "3.14.4",
        "files": rows,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "WRITTEN", "path": str(OUTPUT), "files": len(rows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
