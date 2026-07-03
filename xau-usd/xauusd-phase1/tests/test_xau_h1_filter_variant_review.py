from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_xau_h1_filter_variant_review.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_xau_h1_filter_variant_review", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_asymmetric_variant_never_allows_negative_h1_short() -> None:
    module = load_module()
    variants = {variant.variant_id: variant for variant in module.build_variants()}
    row = {"direction_norm": "SHORT", "h1": -0.01}

    assert variants["V1_current_symmetric_015"].predicate(row) is False
    assert variants["V2_asym_short_005_long_015"].predicate(row) is False
    assert variants["V2_asym_short_010_long_015"].predicate(row) is False
    assert variants["V_bad_counter_h1_shorts_allowed"].predicate(row) is True


def test_asymmetric_variant_allows_weak_positive_short_but_not_weak_long() -> None:
    module = load_module()
    variants = {variant.variant_id: variant for variant in module.build_variants()}
    weak_short = {"direction_norm": "SHORT", "h1": 0.07}
    weak_long = {"direction_norm": "LONG", "h1": 0.07}

    assert variants["V1_current_symmetric_015"].predicate(weak_short) is False
    assert variants["V2_asym_short_005_long_015"].predicate(weak_short) is True
    assert variants["V2_asym_short_005_long_015"].predicate(weak_long) is False


def test_current_variant_requires_015_for_both_directions() -> None:
    module = load_module()
    variants = {variant.variant_id: variant for variant in module.build_variants()}

    assert variants["V1_current_symmetric_015"].predicate({"direction_norm": "LONG", "h1": 0.149}) is False
    assert variants["V1_current_symmetric_015"].predicate({"direction_norm": "SHORT", "h1": 0.149}) is False
    assert variants["V1_current_symmetric_015"].predicate({"direction_norm": "LONG", "h1": 0.15}) is True
    assert variants["V1_current_symmetric_015"].predicate({"direction_norm": "SHORT", "h1": 0.15}) is True
