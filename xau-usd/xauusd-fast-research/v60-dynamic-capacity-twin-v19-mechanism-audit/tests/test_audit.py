from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import run_audit


def test_locked_v19_replacement_capacity_path() -> None:
    result = run_audit.run()
    assert result["decision"] == "MECHANISM_PARITY_PASS"
    assert all(result["checks"].values())
    assert result["broker_action_authorized"] is False
    assert result["deployment_authorized"] is False
    assert result["economic_evidence"] is False
