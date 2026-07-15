from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.dukascopy_label_ranker import _sha256_file  # noqa: E402
from ml.a3_meta_v1.dukascopy_m5_nonlinear_ranker import (  # noqa: E402
    _fit_model,
    _validate_contract,
)


def _contract() -> dict:
    return json.loads(
        (
            ROOT
            / "config"
            / "ml"
            / "a3_ml_dukascopy_m5_nonlinear_ranker.json"
        ).read_text(encoding="utf-8")
    )


def test_contract_binds_linear_base_contract() -> None:
    contract = _contract()
    _validate_contract(contract)
    base = ROOT / contract["base_contract_path"]
    assert _sha256_file(base) == contract["base_contract_sha256"]


def test_contract_rejects_complexity_change() -> None:
    changed = copy.deepcopy(_contract())
    changed["model"]["max_depth"] = 4
    with pytest.raises(ValueError, match="model configuration changed"):
        _validate_contract(changed)


def test_contract_rejects_broker_authorization() -> None:
    changed = copy.deepcopy(_contract())
    changed["authorization"]["broker_action_authorized"] = True
    with pytest.raises(ValueError, match="requires broker_action_authorized=false"):
        _validate_contract(changed)


def test_fixed_seed_produces_identical_probabilities() -> None:
    rng = np.random.default_rng(7)
    matrix = rng.normal(size=(600, 8))
    labels = (matrix[:, 0] * matrix[:, 1] + 0.2 * matrix[:, 2] > 0.0).astype(int)
    first = _fit_model(_contract()["model"]).fit(matrix, labels)
    second = _fit_model(_contract()["model"]).fit(matrix, labels)
    np.testing.assert_array_equal(
        first.predict_proba(matrix)[:, 1], second.predict_proba(matrix)[:, 1]
    )
