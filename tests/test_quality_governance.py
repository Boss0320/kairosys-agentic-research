from __future__ import annotations

from decimal import Decimal
import unittest

from demo.kairosys_case.model import (
    AuditFinding,
    AuditResult,
    FinancialState,
    FindingSeverity,
    IntegrityGateState,
    ResearchDimension,
)
from demo.kairosys_case.quality_governance import (
    ALL_DIMENSIONS,
    UTILITY_WEIGHTS,
    assess_quality,
)


def audit_with(*findings: tuple[str, FindingSeverity]) -> AuditResult:
    return AuditResult(
        findings=tuple(
            AuditFinding(code=code, severity=severity, message=code, evidence=())
            for code, severity in findings
        ),
        confidence_cap=None,
    )


class QualityGovernanceTests(unittest.TestCase):
    def test_fixed_utility_weights_cannot_be_mutated_by_a_caller(self) -> None:
        original = UTILITY_WEIGHTS[ResearchDimension.FUNDAMENTALS]
        try:
            with self.assertRaises(TypeError):
                UTILITY_WEIGHTS[ResearchDimension.FUNDAMENTALS] = Decimal("0.99")  # type: ignore[index]
        finally:
            if isinstance(UTILITY_WEIGHTS, dict):
                UTILITY_WEIGHTS[ResearchDimension.FUNDAMENTALS] = original

        self.assertEqual(sum(UTILITY_WEIGHTS.values(), start=Decimal("0.00")), Decimal("1.00"))

    def test_complete_clean_research_passes_with_full_utility(self) -> None:
        result = assess_quality(audit_with(), FinancialState.STABLE_PROFIT, ALL_DIMENSIONS)

        self.assertEqual(result.integrity_gate, IntegrityGateState.PASS)
        self.assertEqual(result.gate_reasons, ())
        self.assertEqual(result.utility_score, Decimal("1.00"))
        self.assertEqual(result.effective_score, Decimal("1.00"))
        self.assertEqual(result.completed_dimensions, ALL_DIMENSIONS)
        self.assertEqual(result.missing_dimensions, ())

    def test_block_finding_caps_complete_research_at_point_four(self) -> None:
        result = assess_quality(
            audit_with(("RPT-MATH", FindingSeverity.BLOCK)),
            FinancialState.STABLE_PROFIT,
            ALL_DIMENSIONS,
        )

        self.assertEqual(result.integrity_gate, IntegrityGateState.FAIL)
        self.assertEqual(result.gate_reasons, ("RPT-MATH",))
        self.assertEqual(result.utility_score, Decimal("1.00"))
        self.assertEqual(result.effective_score, Decimal("0.40"))

    def test_clean_shallow_research_keeps_integrity_pass_but_low_utility(self) -> None:
        completed = (
            ResearchDimension.FUNDAMENTALS,
            ResearchDimension.INDUSTRY_SUPPLY_CHAIN,
        )

        result = assess_quality(audit_with(), FinancialState.STABLE_PROFIT, completed)

        self.assertEqual(result.integrity_gate, IntegrityGateState.PASS)
        self.assertEqual(result.utility_score, Decimal("0.35"))
        self.assertEqual(result.effective_score, Decimal("0.35"))
        self.assertEqual(result.completed_dimensions, completed)
        self.assertEqual(result.missing_dimensions, ALL_DIMENSIONS[2:])

    def test_duplicate_dimensions_do_not_inflate_utility(self) -> None:
        result = assess_quality(
            audit_with(),
            FinancialState.STABLE_PROFIT,
            (
                ResearchDimension.FUNDAMENTALS,
                ResearchDimension.FUNDAMENTALS,
                ResearchDimension.MARKET_TECHNICAL,
            ),
        )

        self.assertEqual(
            result.completed_dimensions,
            (ResearchDimension.FUNDAMENTALS, ResearchDimension.MARKET_TECHNICAL),
        )
        self.assertEqual(result.utility_score, Decimal("0.30"))

    def test_insufficient_financial_state_fails_closed_without_a_block_finding(self) -> None:
        result = assess_quality(
            audit_with(),
            FinancialState.INSUFFICIENT_DATA,
            ALL_DIMENSIONS,
        )

        self.assertEqual(result.integrity_gate, IntegrityGateState.FAIL)
        self.assertEqual(result.gate_reasons, ("FINANCIAL-STATE",))
        self.assertEqual(result.utility_score, Decimal("1.00"))
        self.assertEqual(result.effective_score, Decimal("0.40"))

    def test_review_finding_routes_review_without_failing_integrity(self) -> None:
        result = assess_quality(
            audit_with(("RPT-SOURCE", FindingSeverity.REVIEW)),
            FinancialState.STABLE_PROFIT,
            ALL_DIMENSIONS,
        )

        self.assertEqual(result.integrity_gate, IntegrityGateState.PASS)
        self.assertEqual(result.gate_reasons, ())
        self.assertEqual(result.utility_score, Decimal("1.00"))
        self.assertEqual(result.effective_score, Decimal("1.00"))


if __name__ == "__main__":
    unittest.main()
