from __future__ import annotations

from src.contract import (
    build_definition_lock,
    definition_lock_path,
    load_config,
    outcome_marker_path,
    write_json,
)


def main() -> int:
    config = load_config()
    lock_path = definition_lock_path(config)
    if lock_path.exists():
        raise RuntimeError(f"Definition lock already exists: {lock_path}")
    if outcome_marker_path(config).exists():
        raise RuntimeError("Outcomes were already opened")
    lock = build_definition_lock(config)
    write_json(lock_path, lock)
    print(lock["definition_contract_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
