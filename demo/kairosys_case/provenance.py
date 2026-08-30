"""Rebuild trusted provenance from deterministic tool observations only."""

from __future__ import annotations

from typing import Mapping, Sequence

from demo.kairosys_case.model import (
    EvidenceStatus,
    ProvenanceEntry,
    ProvenanceIndex,
    ToolResult,
)


def build_provenance_index(
    tool_results: Sequence[ToolResult],
    model_claimed_provenance: Sequence[Mapping[str, object]],
) -> ProvenanceIndex:
    """Return valid tool observations without resolving deterministic conflicts."""
    entries = []
    for tool_result in tool_results:
        for observation in tool_result.observations:
            if observation.status is EvidenceStatus.VALID and observation.value is not None:
                entries.append(
                    ProvenanceEntry(
                        source_tool=tool_result.source_tool,
                        metric_id=observation.metric_id,
                        value=observation.value,
                        period=observation.period,
                        unit=observation.unit,
                        source_record=observation.source_record,
                    )
                )

    entries.sort(
        key=lambda entry: (
            entry.metric_id,
            entry.period,
            entry.unit,
            entry.source_tool,
            entry.source_record,
        )
    )
    return ProvenanceIndex(
        entries=tuple(entries),
        discarded_model_claims=len(model_claimed_provenance),
    )
