from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from decimal import Decimal
from enum import Enum
from typing import Mapping

from demo.kairosys_case.model import PipelineResult


def _to_public_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _to_public_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return [_to_public_value(item) for item in value]
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("Mapping keys must be str")
        return {key: _to_public_value(value[key]) for key in sorted(value)}
    return value


def to_public_dict(result: PipelineResult) -> dict[str, object]:
    serialized = _to_public_value(result)
    if not isinstance(serialized, dict):
        raise TypeError("PipelineResult must serialize to a dictionary")
    return serialized


def to_stable_json(result: PipelineResult) -> str:
    return json.dumps(to_public_dict(result), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
