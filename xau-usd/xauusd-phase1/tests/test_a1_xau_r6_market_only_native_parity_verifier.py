from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


B = _load("build_a1_xau_r6_market_only_native_parity_oracle")
V = _load("verify_a1_xau_r6_market_only_native_parity")


def _write_tsv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_contracts_pin_actual_python_router_and_load_directly() -> None:
    source, schema, manifest = V.load_contracts()
    router = V.load_python_router(source)

    assert router.classify_router is not None
    assert source["python_router_authority"]["module_reimplementation_in_np1_b_forbidden"] is True
    assert source["parity_acceptance"] == schema["parity"]["acceptance"]
    assert manifest["dependencies"]["python_router_authority"]["sha256"] == source["python_router_authority"]["sha256"]


def test_source_equivalence_and_safety_fail_closed_on_tamper(tmp_path: Path) -> None:
    generated = tmp_path / B.ORACLE_NAME
    sidecar = tmp_path / "source_equivalence.json"
    B.build_oracle(generated, sidecar)
    assert V.verify_source_equivalence(sidecar, generated) == []

    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    payload["blocks"][0]["exact_equal"] = False
    sidecar.write_text(json.dumps(payload), encoding="utf-8")
    assert any("flag false" in error for error in V.verify_source_equivalence(sidecar, generated))


def test_assertion_contract_requires_open_positions_and_pending_orders(tmp_path: Path) -> None:
    _, schema, _ = V.load_contracts()
    contract = schema["native_assertions"]
    required = contract["required_assertion_ids"]
    assert "open_positions_zero" in required
    assert "pending_orders_zero" in required

    path = tmp_path / "native_assertions.tsv"
    rows = [
        {"assertion_id": item, "passed": "true", "observed": "0", "expected": "0", "detail": "ok"}
        for item in required
        if item != "pending_orders_zero"
    ]
    _write_tsv(path, contract["columns"], rows)
    errors = V.verify_assertions(path, schema)
    assert errors == ["required assertion did not pass: pending_orders_zero"]


def test_manifest_policy_is_nonrecursive_and_sidecar_hashes_manifest(tmp_path: Path) -> None:
    _, schema, _ = V.load_contracts()
    schema = {**schema, "exact_tree": ["artifact.txt", "manifest.json", "manifest.sha256"]}
    (tmp_path / "artifact.txt").write_text("locked\n", encoding="utf-8")
    manifest = {
        "artifacts": [
            {
                "relative_path": "artifact.txt",
                "size_bytes": (tmp_path / "artifact.txt").stat().st_size,
                "sha256": V.sha256_file(tmp_path / "artifact.txt"),
            }
        ]
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (tmp_path / "manifest.sha256").write_text(V.sha256_file(manifest_path) + "\n", encoding="ascii")

    assert V.verify_nonrecursive_manifest(tmp_path, schema) == []
    manifest["artifacts"].append({"relative_path": "manifest.json", "size_bytes": 0, "sha256": "0" * 64})
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert any("excluded" in error for error in V.verify_nonrecursive_manifest(tmp_path, schema))
