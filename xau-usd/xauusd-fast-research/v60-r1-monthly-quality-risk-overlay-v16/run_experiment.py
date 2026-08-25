from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG = ROOT / "config" / "experiment.json"
OUTPUTS = ROOT / "outputs"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def rename_v14_labels(value):
    if isinstance(value, dict):
        return {
            str(key).replace("v14", "v16"): rename_v14_labels(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [rename_v14_labels(item) for item in value]
    return value


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    scenario = load_module("v16_local_scenario", ROOT / "src" / "scenario.py")
    shared = load_module(
        "v16_shared_runner", REPO_ROOT / config["inputs"]["v14_runner"]["path"]
    )
    shared.ROOT = ROOT
    shared.REPO_ROOT = REPO_ROOT
    shared.CONFIG = CONFIG
    shared.OUTPUTS = OUTPUTS
    shared.PROPOSAL_RULE = scenario.PROPOSAL_RULE
    shared.should_veto_monthly = scenario.should_veto_monthly
    shared.monthly_overlay_class = scenario.monthly_overlay_class
    shared.apply_overlay_sequence = scenario.apply_overlay_sequence
    result = int(shared.main())

    result_path = OUTPUTS / "RESULT.json"
    payload = rename_v14_labels(
        json.loads(result_path.read_text(encoding="utf-8"))
    )
    retention_vs_v60 = (
        payload["historical"]["challenger"]["trades_closed"]
        / payload["historical"]["baseline"]["trades_closed"]
    )
    retention_vs_v6 = (
        payload["historical"]["challenger"]["trades_closed"]
        / payload["frozen_v6"]["challenger"]["trades_closed"]
    )
    payload["canonical_goal_trade_retention"] = {
        "required_fraction_vs_v60": 0.99,
        "observed_fraction_vs_v60": retention_vs_v60,
        "observed_fraction_vs_v6": retention_vs_v6,
        "passes": retention_vs_v60 >= 0.99,
    }
    payload["canonical_goal_authorized"] = False
    caveat = (
        "V16 passes its preregistered 98% retention floor but not the canonical "
        "99% V60 retention goal; it cannot replace V6 without a separate decision."
    )
    if caveat not in payload["limitations"]:
        payload["limitations"].append(caveat)
    result_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    monthly_path = OUTPUTS / "MONTHLY.csv"
    monthly_path.write_text(
        monthly_path.read_text(encoding="utf-8")
        .replace("V14", "V16")
        .replace("v14_", "v16_"),
        encoding="utf-8",
    )
    markdown_path = OUTPUTS / "RESULT.md"
    markdown_path.write_text(
        markdown_path.read_text(encoding="utf-8").replace("V14", "V16")
        + "\n## Canonical Goal Caveat\n\n"
        + f"V16 retains {retention_vs_v60:.3%} of V60 trades and "
        + f"{retention_vs_v6:.3%} of V6 trades. It passes the V16 98% floor but "
        + "does not pass the original 99% V60-retention goal. V6 therefore "
        + "remains the canonical forward challenger.\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    raise SystemExit(main())
