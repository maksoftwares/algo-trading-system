from __future__ import annotations

import argparse
from pathlib import Path

from ml.a3_meta_v1.a2_intraday_context_ranker import run_a2_intraday_context_ranker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--contract", type=Path)
    arguments = parser.parse_args()
    report = run_a2_intraday_context_ranker(arguments.root, arguments.contract)
    print(report)


if __name__ == "__main__":
    main()
