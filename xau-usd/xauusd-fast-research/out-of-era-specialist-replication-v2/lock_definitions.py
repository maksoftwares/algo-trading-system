from __future__ import annotations

import json
import os

from src.contract import DEFINITION_LOCK_PATH, build_definition_lock, load_config


def main() -> int:
    lock = build_definition_lock(load_config())
    DEFINITION_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = DEFINITION_LOCK_PATH.with_suffix(DEFINITION_LOCK_PATH.suffix + ".part")
    temporary.write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, DEFINITION_LOCK_PATH)
    print(json.dumps(lock, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

