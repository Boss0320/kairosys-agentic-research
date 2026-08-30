"""Apply deterministic integrity and utility layers to a synthetic research draft."""

from __future__ import annotations

from decimal import Decimal
from types import MappingProxyType

from .model import (
    AuditResult,
    FinancialState,
    FindingSeverity,
    IntegrityGateState,
    QualityGovernanceResult,
    ResearchDimension,
)


ALL_DIMENSIONS = tuple(ResearchDimension)
UTILITY_WEIGHTS = MappingProxyType({
    ResearchDimension.FUNDAMENTALS: Decimal("0.20"),
    ResearchDimension.INDUSTRY_SUPPLY_CHAIN: Decimal("0.15"),
    ResearchDimension.MARKET_TECHNICAL: Decimal("0.10"),
    ResearchDimension.VALUATION_SCENARIOS: Decimal("0.20"),
    ResearchDimension.CATALYSTS_FALSIFIERS: Decimal("0.20"),
    ResearchDimension.ANALYST_NEXT_STEPS: Decimal("0.15"),
})
INTEGRITY_SCORE_CAP = Decimal("0.40")


def assess_quality(
    audit: AuditResult,
    financial_state: FinancialState,
    completed_dimensions: tuple[ResearchDimension, ...],
) -> QualityGovernanceResult:
    """Return a stable two-layer quality decision without external I/O."""
    provided = tuple(completed_dimensions)
    if any(not isinstance(dimension, ResearchDimension) for dimension in provided):
        raise TypeError("completed_dimensions must contain ResearchDimension values")

    provided_set = set(provided)
    completed = tuple(dimension for dimension in ALL_DIMENSIONS if dimension in provided_set)
    missing = tuple(dimension for dimension in ALL_DIMENSIONS if dimension not in provided_set)
    utility_score = sum(
        (UTILITY_WEIGHTS[dimension] for dimension in completed),
        start=Decimal("0.00"),
    )

    reasons = {
        finding.code
        for finding in audit.findings
        if finding.severity is FindingSeverity.BLOCK
    }
    if financial_state is FinancialState.INSUFFICIENT_DATA:
        reasons.add("FINANCIAL-STATE")
    gate_reasons = tuple(sorted(reasons))
    integrity_gate = IntegrityGateState.FAIL if gate_reasons else IntegrityGateState.PASS
    effective_score = (
        min(utility_score, INTEGRITY_SCORE_CAP)
        if integrity_gate is IntegrityGateState.FAIL
        else utility_score
    )

    return QualityGovernanceResult(
        integrity_gate=integrity_gate,
        gate_reasons=gate_reasons,
        utility_score=utility_score,
        effective_score=effective_score,
        completed_dimensions=completed,
        missing_dimensions=missing,
    )
