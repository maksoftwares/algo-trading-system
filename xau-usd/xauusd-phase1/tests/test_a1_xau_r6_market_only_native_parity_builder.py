from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


B = _load("build_a1_xau_r6_market_only_native_parity_oracle")


def test_builder_extracts_every_locked_block_byte_for_byte() -> None:
    text, equivalence = B.render_oracle()
    source = B.AUTHORITATIVE_SOURCE.read_text(encoding="utf-8")

    assert len(equivalence["blocks"]) == len(B.BLOCK_NAMES) == 16
    assert {row["signature"] for row in equivalence["blocks"]} == set(B.BLOCK_NAMES)
    for row in equivalence["blocks"]:
        source_raw = source.encode()[row["source_start_byte_offset"] : row["source_end_byte_offset"]]
        generated_raw = text.encode()[row["generated_start_byte_offset"] : row["generated_end_byte_offset"]]
        assert source_raw == generated_raw
        assert hashlib.sha256(source_raw).hexdigest() == row["source_raw_sha256"]
        assert row["source_raw_sha256"] == row["generated_raw_sha256"]
        assert row["exact_equal"] is True


def test_checked_in_oracle_is_reproducible_and_equivalence_hash_is_embedded(tmp_path: Path) -> None:
    output = tmp_path / B.ORACLE_NAME
    sidecar = tmp_path / "source_equivalence.json"
    B.build_oracle(output, sidecar)

    assert output.read_bytes() == B.OUTPUT_SOURCE.read_bytes()
    B.verify_generated_source(output)
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    canonical = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    assert hashlib.sha256(canonical).hexdigest() in output.read_text(encoding="utf-8")


def test_builder_fails_closed_on_source_or_generated_drift(tmp_path: Path) -> None:
    mutated = tmp_path / "source.mq5"
    mutated.write_bytes(B.AUTHORITATIVE_SOURCE.read_bytes() + b"\n// drift\n")
    with pytest.raises(RuntimeError, match="Git blob mismatch"):
        B.assert_pinned_source(mutated)

    generated = tmp_path / B.ORACLE_NAME
    B.build_oracle(generated)
    generated.write_text(generated.read_text(encoding="utf-8") + "\n// drift\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="stale"):
        B.verify_generated_source(generated)
