from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.foundation import (
    DEFAULT_CONFIG,
    AcquisitionRefused,
    create_client,
    estimate_costs,
    load_config,
    require_api_key,
    submit_authorized,
    write_manifest,
)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        description="Estimate or explicitly authorize COMEX gold futures data acquisition."
    )
    command.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    command.add_argument("--output", type=Path)
    command.add_argument("--execute", action="store_true")
    command.add_argument("--schema")
    command.add_argument("--max-cost-usd", type=float)
    return command


def main() -> int:
    args = parser().parse_args()
    config = load_config(args.config)
    try:
        api_key = require_api_key(config)
        client = create_client(api_key)
        if args.execute:
            schema = args.schema or config["source"]["preferred_first_schema"]
            max_cost = (
                config["acquisition_controls"]["default_max_cost_usd"]
                if args.max_cost_usd is None
                else args.max_cost_usd
            )
            payload = submit_authorized(
                client,
                config,
                schema=schema,
                max_cost_usd=max_cost,
                execute=True,
            )
        else:
            if args.max_cost_usd is not None or args.schema is not None:
                raise AcquisitionRefused("--schema and --max-cost-usd are only valid with --execute.")
            payload = estimate_costs(client, config)
        manifest = write_manifest(config, payload, args.output)
    except AcquisitionRefused as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc)}, indent=2))
        return 2

    print(json.dumps({"status": payload["status"], "manifest": str(manifest)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
