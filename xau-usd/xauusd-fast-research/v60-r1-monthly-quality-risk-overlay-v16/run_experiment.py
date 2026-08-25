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
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    if "v14" in payload["monthly"]:
        payload["monthly"]["v16"] = payload["monthly"].pop("v14")
        result_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    monthly_path = OUTPUTS / "MONTHLY.csv"
    monthly_path.write_text(
        monthly_path.read_text(encoding="utf-8").replace("V14", "V16"),
        encoding="utf-8",
    )
    markdown_path = OUTPUTS / "RESULT.md"
    markdown_path.write_text(
        markdown_path.read_text(encoding="utf-8").replace("V14", "V16"),
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    raise SystemExit(main())
