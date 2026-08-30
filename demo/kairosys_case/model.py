from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Mapping


class EvidenceStatus(str, Enum):
    VALID = "valid"
    MISSING = "missing"
    INVALID = "invalid"
    CONFLICT = "conflict"


class FinancialState(str, Enum):
    STABLE_PROFIT = "stable_profit"
    REVENUE_WITHOUT_PROFIT = "revenue_without_profit"
    PRE_REVENUE = "pre_revenue"
    INSUFFICIENT_DATA = "insufficient_data"


class ResearchDimension(str, Enum):
    FUNDAMENTALS = "fundamentals"
    INDUSTRY_SUPPLY_CHAIN = "industry_supply_chain"
    MARKET_TECHNICAL = "market_technical"
    VALUATION_SCENARIOS = "valuation_scenarios"
    CATALYSTS_FALSIFIERS = "catalysts_falsifiers"
    ANALYST_NEXT_STEPS = "analyst_next_steps"


class IntegrityGateState(str, Enum):
    PASS = "pass"
    FAIL = "fail"


class FindingSeverity(str, Enum):
    INFO = "info"
    REVIEW = "review"
    BLOCK = "block"


class DeliveryState(str, Enum):
    EDITABLE_DRAFT = "editable_draft"
    CONTEXT_ONLY = "context_only"
    REVIEW_REQUIRED = "review_required"
    WITHHELD = "withheld"


@dataclass(frozen=True)
class MetricObservation:
    metric_id: str
    value: Decimal | None
    period: str
    unit: str
    source_record: str
    status: EvidenceStatus


@dataclass(frozen=True)
class ToolResult:
    source_tool: str
    observations: tuple[MetricObservation, ...]


@dataclass(frozen=True)
class ProvenanceEntry:
    source_tool: str
    metric_id: str
    value: Decimal
    period: str
    unit: str
    source_record: str


@dataclass(frozen=True)
class ProvenanceIndex:
    entries: tuple[ProvenanceEntry, ...]
    discarded_model_claims: int


@dataclass(frozen=True)
class FinancialQuarter:
    period: str
    revenue: Decimal | None
    eps: Decimal | None


@dataclass(frozen=True)
class FinancialStateResult:
    state: FinancialState
    reason: str


@dataclass(frozen=True)
class ValuationDecision:
    state: FinancialState
    reason: str
    authorized_methods: tuple[str, ...]
    allows_target: bool


@dataclass(frozen=True)
class AuditFinding:
    code: str
    severity: FindingSeverity
    message: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class AuditResult:
    findings: tuple[AuditFinding, ...]
    confidence_cap: Decimal | None


@dataclass(frozen=True)
class QualityGovernanceResult:
    integrity_gate: IntegrityGateState
    gate_reasons: tuple[str, ...]
    utility_score: Decimal
    effective_score: Decimal
    completed_dimensions: tuple[ResearchDimension, ...]
    missing_dimensions: tuple[ResearchDimension, ...]


@dataclass(frozen=True)
class CaseInput:
    scenario: str
    issuer: str
    symbol: str
    tool_results: tuple[ToolResult, ...]
    model_claimed_provenance: tuple[Mapping[str, object], ...]
    quarters: tuple[FinancialQuarter, ...]
    completed_dimensions: tuple[ResearchDimension, ...]
    draft_markdown: str


@dataclass(frozen=True)
class PipelineResult:
    scenario: str
    delivery: DeliveryState
    provenance: ProvenanceIndex
    valuation: ValuationDecision
    audit: AuditResult
    quality: QualityGovernanceResult
    rendered_report: str
