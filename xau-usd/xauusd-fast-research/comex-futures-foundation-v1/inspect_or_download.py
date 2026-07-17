from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.foundation import (
    DEFAULT_CONFIG,
    AcquisitionRefused,
    create_client,
    download_completed_job,
    load_config,
    require_api_key,
    write_manifest,
)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Inspect or explicitly download a Databento batch job.")
    command.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    command.add_argument("--job-id", required=True)
    command.add_argument("--execute-download", action="store_true")
    command.add_argument("--output", type=Path)
    return command


def main() -> int:
    args = parser().parse_args()
    config = load_config(args.config)
    try:
        client = create_client(require_api_key(config))
        payload = download_completed_job(
            client,
            config,
            job_id=args.job_id,
            execute_download=args.execute_download,
        )
        manifest = write_manifest(config, payload, args.output)
    except AcquisitionRefused as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc)}, indent=2))
        return 2

    print(json.dumps({"status": payload["status"], "manifest": str(manifest)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
