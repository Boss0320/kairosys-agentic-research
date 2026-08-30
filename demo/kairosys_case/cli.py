"""Command-line adapter for deterministic synthetic case evaluation."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from .pipeline import run_scenario
from .scenarios import SCENARIO_NAMES
from .serialization import to_stable_json


def main(argv: Sequence[str] | None = None) -> int:
    """Print one stable JSON result for a pre-approved scenario."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=SCENARIO_NAMES, required=True)
    arguments = parser.parse_args(argv)
    print(to_stable_json(run_scenario(arguments.scenario)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
