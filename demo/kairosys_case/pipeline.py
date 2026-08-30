"""Orchestrate the approved synthetic case through one auditable direction."""

from __future__ import annotations

from dataclasses import replace

from .model import AuditResult, CaseInput, PipelineResult
from .provenance import build_provenance_index
from .quality_governance import assess_quality
from .report_audit import apply_delivery_policy, audit_rendered_report
from .scenarios import load_scenario
from .valuation import authorize_valuation, classify_financial_state


def evaluate_case(case: CaseInput) -> PipelineResult:
    """Evaluate an immutable synthetic case without external I/O."""
    provenance = build_provenance_index(
        case.tool_results,
        case.model_claimed_provenance,
    )
    financial_state = classify_financial_state(case.quarters)
    valuation = authorize_valuation(financial_state)
    audited = audit_rendered_report(case.draft_markdown, provenance, valuation)
    quality = assess_quality(
        audited,
        financial_state.state,
        case.completed_dimensions,
    )
    delivery, rendered_report, confidence_cap = apply_delivery_policy(
        case.draft_markdown,
        valuation,
        audited,
        quality,
    )
    audit = replace(audited, confidence_cap=confidence_cap)
    return PipelineResult(
        scenario=case.scenario,
        delivery=delivery,
        provenance=provenance,
        valuation=valuation,
        audit=audit,
        quality=quality,
        rendered_report=rendered_report,
    )


def run_scenario(name: str) -> PipelineResult:
    """Load and evaluate one approved synthetic scenario."""
    return evaluate_case(load_scenario(name))
