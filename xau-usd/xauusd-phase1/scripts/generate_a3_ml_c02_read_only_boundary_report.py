from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.boundary_report import generate_c02_read_only_boundary_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the C02 read-only boundary build report.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()

    output = generate_c02_read_only_boundary_report(
        args.root,
        registry_path=args.registry,
        output_json=args.output_json,
    )
    print(f"C02 read-only boundary report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
