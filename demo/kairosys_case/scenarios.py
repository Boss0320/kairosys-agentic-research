"""Fixed clean-room inputs for the auditable research demonstration."""

from __future__ import annotations

from decimal import Decimal
from types import MappingProxyType
from typing import Mapping

from demo.kairosys_case.model import (
    CaseInput,
    EvidenceStatus,
    FinancialQuarter,
    MetricObservation,
    ResearchDimension,
    ToolResult,
)
from demo.kairosys_case.quality_governance import ALL_DIMENSIONS


SCENARIO_NAMES = (
    "ready_report",
    "spoofed_provenance",
    "incomplete_financials",
    "contradictory_financials",
    "rendered_math_conflict",
    "shallow_but_sound",
)

_ISSUER = "Northstar Circuits"
_SYMBOL = "SYNTH-KAI-01"

_READY_DRAFT = """# Northstar Circuits — Synthetic research draft
**Claimed metric:** forward_eps
**Synthetic target:** 120
**Forward EPS:** 5.00
**Displayed P/E:** 24.0x
"""

_SPOOFED_DRAFT = """# Northstar Circuits — Synthetic research draft
**Claimed metric:** market_share
The draft asserts a market-share figure that exists only in model-supplied provenance.
"""

_INCOMPLETE_DRAFT = """# Northstar Circuits — Synthetic research draft
**Claimed metric:** revenue
**Synthetic target:** 120
**Forward EPS:** 5.00
**Displayed P/E:** 24.0x
Operating context remains useful, but the four-quarter window is incomplete.
"""

_MATH_CONFLICT_DRAFT = """# Northstar Circuits — Synthetic research draft
**Claimed metric:** forward_eps
**Synthetic target:** 120
**Forward EPS:** 5.00
**Displayed P/E:** 20.0x
"""

_SHALLOW_DRAFT = """# Northstar Circuits — Synthetic research draft
**Claimed metric:** revenue
The available facts are consistent, but valuation, catalysts, falsifiers, and analyst next steps are absent.
"""


def _quarter(period: str, revenue: str, eps: str) -> FinancialQuarter:
    return FinancialQuarter(period, Decimal(revenue), Decimal(eps))


def _observation(
    metric_id: str,
    value: str,
    period: str,
    unit: str,
    source_record: str,
) -> MetricObservation:
    return MetricObservation(
        metric_id=metric_id,
        value=Decimal(value),
        period=period,
        unit=unit,
        source_record=source_record,
        status=EvidenceStatus.VALID,
    )


_PROFITABLE_QUARTERS = (
    _quarter("2026Q2", "145", "1.35"),
    _quarter("2026Q1", "136", "1.22"),
    _quarter("2025Q4", "128", "1.10"),
    _quarter("2025Q3", "120", "1.00"),
)

_PROFITABLE_OBSERVATIONS = (
    _observation("revenue", "145", "2026Q2", "TWD_million", "SYNTH-REC-01"),
    _observation("eps", "1.35", "2026Q2", "TWD_per_share", "SYNTH-REC-02"),
    _observation("revenue", "136", "2026Q1", "TWD_million", "SYNTH-REC-03"),
    _observation("eps", "1.22", "2026Q1", "TWD_per_share", "SYNTH-REC-04"),
    _observation("revenue", "128", "2025Q4", "TWD_million", "SYNTH-REC-05"),
    _observation("eps", "1.10", "2025Q4", "TWD_per_share", "SYNTH-REC-06"),
    _observation("revenue", "120", "2025Q3", "TWD_million", "SYNTH-REC-07"),
    _observation("eps", "1.00", "2025Q3", "TWD_per_share", "SYNTH-REC-08"),
)


def _tool_result(*observations: MetricObservation) -> tuple[ToolResult, ...]:
    return (ToolResult("synthetic-statement", observations),)


_CASES: Mapping[str, CaseInput] = MappingProxyType(
    {
        "ready_report": CaseInput(
            scenario="ready_report",
            issuer=_ISSUER,
            symbol=_SYMBOL,
            tool_results=_tool_result(
                *_PROFITABLE_OBSERVATIONS,
                _observation("forward_eps", "5.00", "2026Q2", "TWD_per_share", "SYNTH-REC-09"),
            ),
            model_claimed_provenance=(),
            quarters=_PROFITABLE_QUARTERS,
            completed_dimensions=ALL_DIMENSIONS,
            draft_markdown=_READY_DRAFT,
        ),
        "spoofed_provenance": CaseInput(
            scenario="spoofed_provenance",
            issuer=_ISSUER,
            symbol=_SYMBOL,
            tool_results=_tool_result(*_PROFITABLE_OBSERVATIONS),
            model_claimed_provenance=(
                MappingProxyType({"metric_id": "market_share", "value": "42"}),
            ),
            quarters=_PROFITABLE_QUARTERS,
            completed_dimensions=ALL_DIMENSIONS,
            draft_markdown=_SPOOFED_DRAFT,
        ),
        "incomplete_financials": CaseInput(
            scenario="incomplete_financials",
            issuer=_ISSUER,
            symbol=_SYMBOL,
            tool_results=_tool_result(
                _observation("revenue", "145", "2026Q2", "TWD_million", "SYNTH-REC-10"),
            ),
            model_claimed_provenance=(),
            quarters=_PROFITABLE_QUARTERS[:3],
            completed_dimensions=ALL_DIMENSIONS,
            draft_markdown=_INCOMPLETE_DRAFT,
        ),
        "contradictory_financials": CaseInput(
            scenario="contradictory_financials",
            issuer=_ISSUER,
            symbol=_SYMBOL,
            tool_results=_tool_result(
                _observation("revenue", "0", "2026Q2", "TWD_million", "SYNTH-REC-11"),
                _observation("eps", "0.80", "2026Q2", "TWD_per_share", "SYNTH-REC-12"),
            ),
            model_claimed_provenance=(),
            quarters=(
                _quarter("2026Q2", "0", "0.80"),
                _quarter("2026Q1", "0", "0.75"),
                _quarter("2025Q4", "0", "0.70"),
                _quarter("2025Q3", "0", "0.65"),
            ),
            completed_dimensions=ALL_DIMENSIONS,
            draft_markdown="",
        ),
        "rendered_math_conflict": CaseInput(
            scenario="rendered_math_conflict",
            issuer=_ISSUER,
            symbol=_SYMBOL,
            tool_results=_tool_result(
                *_PROFITABLE_OBSERVATIONS,
                _observation("forward_eps", "5.00", "2026Q2", "TWD_per_share", "SYNTH-REC-13"),
            ),
            model_claimed_provenance=(),
            quarters=_PROFITABLE_QUARTERS,
            completed_dimensions=ALL_DIMENSIONS,
            draft_markdown=_MATH_CONFLICT_DRAFT,
        ),
        "shallow_but_sound": CaseInput(
            scenario="shallow_but_sound",
            issuer=_ISSUER,
            symbol=_SYMBOL,
            tool_results=_tool_result(_PROFITABLE_OBSERVATIONS[0]),
            model_claimed_provenance=(),
            quarters=_PROFITABLE_QUARTERS,
            completed_dimensions=(
                ResearchDimension.FUNDAMENTALS,
                ResearchDimension.INDUSTRY_SUPPLY_CHAIN,
            ),
            draft_markdown=_SHALLOW_DRAFT,
        ),
    }
)


def load_scenario(name: str) -> CaseInput:
    """Return one immutable approved case or reject an unknown name."""
    try:
        return _CASES[name]
    except KeyError as error:
        raise KeyError(f"unknown scenario: {name}") from error
