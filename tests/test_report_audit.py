from __future__ import annotations

from decimal import Decimal
import unittest

from demo.kairosys_case.model import (
    AuditResult,
    DeliveryState,
    FinancialState,
    FindingSeverity,
    IntegrityGateState,
    ProvenanceEntry,
    ProvenanceIndex,
    ResearchDimension,
    ValuationDecision,
)
from demo.kairosys_case.quality_governance import ALL_DIMENSIONS, assess_quality
from demo.kairosys_case.report_audit import audit_rendered_report, apply_delivery_policy


def get_finding(result: AuditResult, code: str):
    return next(item for item in result.findings if item.code == code)


def empty_index() -> ProvenanceIndex:
    return ProvenanceIndex(entries=(), discarded_model_claims=0)


def target_allowed() -> ValuationDecision:
    return ValuationDecision(
        state=FinancialState.STABLE_PROFIT,
        reason="positive_four_quarter_eps",
        authorized_methods=("earnings_context",),
        allows_target=True,
    )


def target_denied() -> ValuationDecision:
    return ValuationDecision(
        state=FinancialState.REVENUE_WITHOUT_PROFIT,
        reason="revenue_present_without_positive_eps",
        authorized_methods=("revenue_context",),
        allows_target=False,
    )


def insufficient_data() -> ValuationDecision:
    return ValuationDecision(
        state=FinancialState.INSUFFICIENT_DATA,
        reason="missing_evidence",
        authorized_methods=(),
        allows_target=False,
    )


def valid_index() -> ProvenanceIndex:
    entry = ProvenanceEntry(
        source_tool="statement_reader",
        metric_id="forward_eps",
        value=Decimal("5.00"),
        period="2026F",
        unit="TWD/share",
        source_record="SYNTH-RECORD-01",
    )
    return ProvenanceIndex(entries=(entry,), discarded_model_claims=0)


class RenderedReportAuditTests(unittest.TestCase):
    def test_report_metric_without_trusted_evidence_requires_review(self) -> None:
        result = audit_rendered_report(
            markdown="**Claimed metric:** market_share\n",
            provenance=empty_index(),
            valuation=target_allowed(),
        )

        finding = get_finding(result, "RPT-SOURCE")
        self.assertEqual(finding.severity, FindingSeverity.REVIEW)
        self.assertEqual(finding.evidence, ("**Claimed metric:** market_share",))

    def test_unauthorized_target_is_blocking(self) -> None:
        result = audit_rendered_report(
            markdown="**Synthetic target:** 120\n",
            provenance=valid_index(),
            valuation=target_denied(),
        )

        finding = get_finding(result, "RPT-AUTH")
        self.assertEqual(finding.severity, FindingSeverity.BLOCK)
        self.assertEqual(finding.evidence, ("**Synthetic target:** 120",))

    def test_conflicting_forward_eps_is_blocking(self) -> None:
        markdown = "**Forward EPS:** 5.00\n**Forward EPS:** 6.00\n"
        result = audit_rendered_report(markdown, valid_index(), target_allowed())

        finding = get_finding(result, "RPT-DUP")
        self.assertEqual(finding.severity, FindingSeverity.BLOCK)
        self.assertEqual(
            finding.evidence,
            ("**Forward EPS:** 5.00", "**Forward EPS:** 6.00"),
        )

    def test_target_pe_relationship_is_recomputed(self) -> None:
        markdown = (
            "**Synthetic target:** 120\n"
            "**Forward EPS:** 5.00\n"
            "**Displayed P/E:** 20.0x\n"
        )
        result = audit_rendered_report(markdown, valid_index(), target_allowed())

        finding = get_finding(result, "RPT-MATH")
        self.assertEqual(finding.severity, FindingSeverity.BLOCK)
        self.assertEqual(
            finding.evidence,
            (
                "**Synthetic target:** 120",
                "**Forward EPS:** 5.00",
                "**Displayed P/E:** 20.0x",
            ),
        )

    def test_malformed_numeric_representation_blocks_math_check(self) -> None:
        markdown = (
            "**Synthetic target:** 120\n"
            "**Forward EPS:** 5.00\n"
            "**Displayed P/E:** NaN\n"
        )

        result = audit_rendered_report(markdown, valid_index(), target_allowed())

        finding = get_finding(result, "RPT-MATH")
        self.assertEqual(finding.severity, FindingSeverity.BLOCK)
        self.assertEqual(finding.evidence[-1], "**Displayed P/E:** NaN")

    def test_numeric_label_with_malformed_suffix_is_not_ignored(self) -> None:
        markdown = "  **Synthetic target:** 120 trailing-token  \n"

        result = audit_rendered_report(markdown, valid_index(), target_allowed())

        finding = get_finding(result, "RPT-MATH")
        self.assertEqual(finding.severity, FindingSeverity.BLOCK)
        self.assertEqual(finding.evidence, ("  **Synthetic target:** 120 trailing-token  ",))

    def test_non_finite_numeric_label_is_not_ignored(self) -> None:
        markdown = "**Forward EPS:** Infinity\n"

        result = audit_rendered_report(markdown, valid_index(), target_allowed())

        finding = get_finding(result, "RPT-MATH")
        self.assertEqual(finding.severity, FindingSeverity.BLOCK)
        self.assertEqual(finding.evidence, ("**Forward EPS:** Infinity",))

    def test_blank_numeric_suffix_is_not_ignored(self) -> None:
        markdown = "**Displayed P/E:**   \n"

        result = audit_rendered_report(markdown, valid_index(), target_allowed())

        finding = get_finding(result, "RPT-MATH")
        self.assertEqual(finding.severity, FindingSeverity.BLOCK)
        self.assertEqual(finding.evidence, ("**Displayed P/E:**   ",))

    def test_identical_forward_eps_duplicates_still_recompute_math(self) -> None:
        markdown = (
            "**Synthetic target:** 120\n"
            "**Forward EPS:** 5.00\n"
            "**Forward EPS:** 5.00\n"
            "**Displayed P/E:** 20.0x\n"
        )

        result = audit_rendered_report(markdown, valid_index(), target_allowed())

        self.assertFalse(any(finding.code == "RPT-DUP" for finding in result.findings))
        finding = get_finding(result, "RPT-MATH")
        self.assertEqual(finding.severity, FindingSeverity.BLOCK)
        self.assertEqual(
            finding.evidence,
            (
                "**Synthetic target:** 120",
                "**Forward EPS:** 5.00",
                "**Forward EPS:** 5.00",
                "**Displayed P/E:** 20.0x",
            ),
        )

    def test_renderer_rounding_accepts_half_up_value_at_displayed_scale(self) -> None:
        markdown = (
            "**Synthetic target:** 100\n"
            "**Forward EPS:** 3\n"
            "**Displayed P/E:** 33.3x\n"
        )

        result = audit_rendered_report(markdown, valid_index(), target_allowed())

        self.assertFalse(any(finding.code == "RPT-MATH" for finding in result.findings))

    def test_renderer_rounding_rejects_adjacent_value_outside_boundary(self) -> None:
        markdown = (
            "**Synthetic target:** 100\n"
            "**Forward EPS:** 3\n"
            "**Displayed P/E:** 33.2x\n"
        )

        result = audit_rendered_report(markdown, valid_index(), target_allowed())

        self.assertEqual(get_finding(result, "RPT-MATH").severity, FindingSeverity.BLOCK)

    def test_mixed_findings_have_exact_deterministic_order_and_evidence(self) -> None:
        markdown = (
            "**Claimed metric:** market_share\n"
            "**Synthetic target:** 120\n"
            "**Forward EPS:** 5.00\n"
            "**Forward EPS:** 6.00\n"
            "**Displayed P/E:** NaN\n"
        )

        result = audit_rendered_report(markdown, valid_index(), target_denied())

        self.assertEqual(
            tuple(finding.code for finding in result.findings),
            ("RPT-SOURCE", "RPT-AUTH", "RPT-DUP", "RPT-MATH"),
        )
        self.assertEqual(
            tuple(finding.evidence for finding in result.findings),
            (
                ("**Claimed metric:** market_share",),
                ("**Synthetic target:** 120",),
                ("**Forward EPS:** 5.00", "**Forward EPS:** 6.00"),
                ("**Displayed P/E:** NaN",),
            ),
        )


class DeliveryPolicyTests(unittest.TestCase):
    def test_math_block_retains_visibly_labeled_draft_with_confidence_cap(self) -> None:
        markdown = (
            "# Synthetic research draft\n"
            "**Synthetic target:** 120\n"
            "**Forward EPS:** 5.00\n"
            "**Displayed P/E:** 20.0x\n"
        )
        audit = audit_rendered_report(markdown, valid_index(), target_allowed())

        delivery, rendered, confidence_cap = apply_delivery_policy(
            markdown,
            target_allowed(),
            audit,
            assess_quality(audit, FinancialState.STABLE_PROFIT, ALL_DIMENSIONS),
        )

        self.assertEqual(delivery, DeliveryState.REVIEW_REQUIRED)
        self.assertEqual(rendered, "REVIEW REQUIRED\n\n" + markdown.strip())
        self.assertEqual(confidence_cap, Decimal("0.40"))

    def test_unauthorized_target_becomes_context_only_and_preserves_context(self) -> None:
        markdown = (
            "# Synthetic research draft\n"
            "Operating context remains useful.\n"
            "**Synthetic target:** 120\n"
            "**Forward EPS:** 5.00\n"
            "**Displayed P/E:** 24.0x\n"
        )
        audit = audit_rendered_report(markdown, valid_index(), target_denied())

        delivery, rendered, confidence_cap = apply_delivery_policy(
            markdown,
            target_denied(),
            audit,
            assess_quality(
                audit,
                FinancialState.REVENUE_WITHOUT_PROFIT,
                ALL_DIMENSIONS,
            ),
        )

        self.assertEqual(delivery, DeliveryState.CONTEXT_ONLY)
        self.assertEqual(
            rendered,
            "# Synthetic research draft\nOperating context remains useful.\n**Forward EPS:** 5.00",
        )
        self.assertIsNone(confidence_cap)

    def test_empty_insufficient_report_is_withheld(self) -> None:
        audit = audit_rendered_report("   \n", empty_index(), insufficient_data())

        delivery, rendered, confidence_cap = apply_delivery_policy(
            "   \n",
            insufficient_data(),
            audit,
            assess_quality(
                audit,
                FinancialState.INSUFFICIENT_DATA,
                ALL_DIMENSIONS,
            ),
        )

        self.assertEqual(delivery, DeliveryState.WITHHELD)
        self.assertEqual(rendered, "")
        self.assertIsNone(confidence_cap)

    def test_empty_report_is_withheld_even_when_financial_state_is_stable(self) -> None:
        audit = audit_rendered_report("   \n", valid_index(), target_allowed())

        delivery, rendered, confidence_cap = apply_delivery_policy(
            "   \n",
            target_allowed(),
            audit,
            assess_quality(audit, FinancialState.STABLE_PROFIT, ALL_DIMENSIONS),
        )

        self.assertEqual(delivery, DeliveryState.WITHHELD)
        self.assertEqual(rendered, "")
        self.assertIsNone(confidence_cap)

    def test_blocking_audit_fails_closed_when_supplied_quality_is_inconsistent(self) -> None:
        markdown = (
            "# Synthetic research draft\n"
            "**Synthetic target:** 120\n"
            "**Forward EPS:** 5.00\n"
            "**Displayed P/E:** 20.0x\n"
        )
        blocking_audit = audit_rendered_report(markdown, valid_index(), target_allowed())
        clean_quality = assess_quality(
            AuditResult(findings=(), confidence_cap=None),
            FinancialState.STABLE_PROFIT,
            ALL_DIMENSIONS,
        )

        delivery, rendered, confidence_cap = apply_delivery_policy(
            markdown,
            target_allowed(),
            blocking_audit,
            clean_quality,
        )

        self.assertEqual(delivery, DeliveryState.REVIEW_REQUIRED)
        self.assertEqual(rendered, "REVIEW REQUIRED\n\n" + markdown.strip())
        self.assertEqual(confidence_cap, Decimal("0.40"))

    def test_clean_report_remains_editable_draft(self) -> None:
        markdown = "# Synthetic research draft\n**Claimed metric:** forward_eps\n"
        audit = audit_rendered_report(markdown, valid_index(), target_allowed())

        delivery, rendered, confidence_cap = apply_delivery_policy(
            markdown,
            target_allowed(),
            audit,
            assess_quality(audit, FinancialState.STABLE_PROFIT, ALL_DIMENSIONS),
        )

        self.assertEqual(delivery, DeliveryState.EDITABLE_DRAFT)
        self.assertEqual(rendered, markdown.strip())
        self.assertIsNone(confidence_cap)

    def test_clean_low_utility_report_requires_review_with_point_six_cap(self) -> None:
        markdown = "# Synthetic research draft\n**Claimed metric:** forward_eps\n"
        audit = audit_rendered_report(markdown, valid_index(), target_allowed())
        quality = assess_quality(
            audit,
            FinancialState.STABLE_PROFIT,
            (
                ResearchDimension.FUNDAMENTALS,
                ResearchDimension.INDUSTRY_SUPPLY_CHAIN,
            ),
        )

        delivery, rendered, confidence_cap = apply_delivery_policy(
            markdown,
            target_allowed(),
            audit,
            quality,
        )

        self.assertEqual(quality.integrity_gate, IntegrityGateState.PASS)
        self.assertEqual(quality.utility_score, Decimal("0.35"))
        self.assertEqual(delivery, DeliveryState.REVIEW_REQUIRED)
        self.assertEqual(rendered, "REVIEW REQUIRED\n\n" + markdown.strip())
        self.assertEqual(confidence_cap, Decimal("0.60"))

    def test_authorization_finding_overrides_other_blocks_for_delivery(self) -> None:
        markdown = (
            "# Synthetic research draft\n"
            "Operating context remains useful.\n"
            "**Synthetic target:** 120\n"
            "**Forward EPS:** 5.00\n"
            "**Forward EPS:** 6.00\n"
            "**Displayed P/E:** NaN\n"
        )
        audit = audit_rendered_report(markdown, valid_index(), target_denied())

        delivery, rendered, confidence_cap = apply_delivery_policy(
            markdown,
            target_denied(),
            audit,
            assess_quality(
                audit,
                FinancialState.REVENUE_WITHOUT_PROFIT,
                ALL_DIMENSIONS,
            ),
        )

        self.assertEqual(delivery, DeliveryState.CONTEXT_ONLY)
        self.assertEqual(
            rendered,
            "# Synthetic research draft\nOperating context remains useful.\n**Forward EPS:** 5.00\n**Forward EPS:** 6.00",
        )
        self.assertIsNone(confidence_cap)


if __name__ == "__main__":
    unittest.main()
