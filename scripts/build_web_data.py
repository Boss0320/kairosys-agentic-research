"""Build the static browser payload from the approved synthetic scenarios."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from demo.kairosys_case.pipeline import run_scenario
from demo.kairosys_case.scenarios import SCENARIO_NAMES
from demo.kairosys_case.serialization import to_public_dict


PREFIX = "window.KAIROSYS_CASE_DATA="


def build_payload() -> dict[str, object]:
    """Return every approved scenario as its stable public pipeline value."""
    return {name: to_public_dict(run_scenario(name)) for name in SCENARIO_NAMES}


def render_javascript(payload: Mapping[str, object]) -> str:
    """Render a compact, sorted assignment suitable for an offline browser."""
    return PREFIX + json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + ";\n"


def main(arguments: tuple[str, ...] | None = None) -> int:
    """Write only the explicit data-file destination supplied by the caller."""
    arguments = tuple(sys.argv[1:] if arguments is None else arguments)
    if len(arguments) != 1:
        raise SystemExit("usage: build_web_data.py DESTINATION")
    destination = Path(arguments[0])
    destination.write_text(render_javascript(build_payload()), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
