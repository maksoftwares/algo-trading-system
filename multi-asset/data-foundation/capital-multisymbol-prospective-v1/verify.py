from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "capital_multisymbol_prospective_v1.json"
LOCK = ROOT / "outputs" / "CAPITAL_MULTISYMBOL_PROSPECTIVE_V1_CONTRACT_LOCK.json"
FORBIDDEN_SOURCE_TOKENS = (
    "order_send",
    "trade_action_",
    "position_close",
    "history_deal_get",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    checks: dict[str, bool] = {}
    checks["exact_account"] = config["account"]["expected_login"] == 1033030
    checks["exact_server"] = (
        config["account"]["expected_server"] == "Capital.ComMena-Demo"
    )
    checks["future_boundary"] = (
        config["information_boundary"]["start_inclusive_utc"]
        == "2026-07-27T00:00:00Z"
    )
    checks["d_drive_storage"] = Path(config["storage"]["root"]).drive.upper() == "D:"
    checks["all_authority_false"] = all(
        value is False for value in config["authority"].values()
    )
    source = (ROOT / "src" / "collector.py").read_text(encoding="utf-8").lower()
    checks["no_broker_action_api"] = not any(
        token in source for token in FORBIDDEN_SOURCE_TOKENS
    )
    checks["bound_files_unchanged"] = all(
        sha256(ROOT / relative) == expected
        for relative, expected in lock["files"].items()
    )
    decision = (
        "CAPITAL_MULTISYMBOL_PROSPECTIVE_V1_VERIFICATION_PASS"
        if all(checks.values())
        else "CAPITAL_MULTISYMBOL_PROSPECTIVE_V1_VERIFICATION_FAIL"
    )
    print(json.dumps({"decision": decision, "checks": checks}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

