from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, fields
from decimal import Decimal
from enum import Enum
from typing import Mapping, get_type_hints
import unittest

from demo.kairosys_case.model import (
    AuditFinding,
    AuditResult,
    CaseInput,
    DeliveryState,
    EvidenceStatus,
    FinancialQuarter,
    FinancialState,
    FinancialStateResult,
    FindingSeverity,
    IntegrityGateState,
    MetricObservation,
    PipelineResult,
    ProvenanceEntry,
    ProvenanceIndex,
    QualityGovernanceResult,
    ResearchDimension,
    ToolResult,
    ValuationDecision,
)
from demo.kairosys_case.serialization import _to_public_value, to_public_dict, to_stable_json


@dataclass(frozen=True)
class _MappingFixture:
    metadata: Mapping[str, object]


class SerializationTests(unittest.TestCase):
    def quality_fixture(self) -> QualityGovernanceResult:
        return QualityGovernanceResult(
            integrity_gate=IntegrityGateState.PASS,
            gate_reasons=(),
            utility_score=Decimal("1.00"),
            effective_score=Decimal("1.00"),
            completed_dimensions=tuple(ResearchDimension),
            missing_dimensions=(),
        )

    def test_public_json_is_byte_stable(self) -> None:
        result = PipelineResult(
            scenario="ready_report",
            delivery=DeliveryState.EDITABLE_DRAFT,
            provenance=ProvenanceIndex(entries=(), discarded_model_claims=0),
            valuation=ValuationDecision(
                state=FinancialState.STABLE_PROFIT,
                reason="positive_four_quarter_eps",
                authorized_methods=("earnings_context",),
                allows_target=True,
            ),
            audit=AuditResult(findings=(), confidence_cap=None),
            quality=self.quality_fixture(),
            rendered_report="# Synthetic report",
        )

        self.assertEqual(to_stable_json(result), to_stable_json(result))

    def test_public_dict_recursively_preserves_decimal_enum_tuple_and_mapping_contracts(self) -> None:
        result = PipelineResult(
            scenario="ready_report",
            delivery=DeliveryState.EDITABLE_DRAFT,
            provenance=ProvenanceIndex(
                entries=(
                    ProvenanceEntry(
                        source_tool="synthetic_ledger",
                        metric_id="trailing_eps",
                        value=Decimal("12.50"),
                        period="FY2025",
                        unit="currency_per_share",
                        source_record="record-01",
                    ),
                ),
                discarded_model_claims=1,
            ),
            valuation=ValuationDecision(
                state=FinancialState.STABLE_PROFIT,
                reason="positive_four_quarter_eps",
                authorized_methods=("earnings_context", "relative_context"),
                allows_target=True,
            ),
            audit=AuditResult(
                findings=(
                    AuditFinding(
                        code="synthetic_check",
                        severity=FindingSeverity.REVIEW,
                        message="review synthetic evidence",
                        evidence=("record-01",),
                    ),
                ),
                confidence_cap=Decimal("0.80"),
            ),
            quality=self.quality_fixture(),
            rendered_report="# Synthetic report",
        )

        public = to_public_dict(result)

        self.assertEqual(public["delivery"], "editable_draft")
        self.assertEqual(public["provenance"]["entries"][0]["value"], "12.50")
        self.assertEqual(public["valuation"]["authorized_methods"], ["earnings_context", "relative_context"])
        self.assertEqual(public["audit"]["findings"][0]["severity"], "review")
        self.assertEqual(public["audit"]["confidence_cap"], "0.80")
        self.assertEqual(public["quality"]["integrity_gate"], "pass")
        self.assertEqual(public["quality"]["utility_score"], "1.00")
        self.assertEqual(
            _to_public_value(_MappingFixture(metadata={"zeta": (Decimal("2.00"),), "alpha": EvidenceStatus.VALID})),
            {"metadata": {"alpha": "valid", "zeta": ["2.00"]}},
        )
        self.assertEqual(
            to_stable_json(result),
            '{"audit":{"confidence_cap":"0.80","findings":[{"code":"synthetic_check","evidence":["record-01"],"message":"review synthetic evidence","severity":"review"}]},"delivery":"editable_draft","provenance":{"discarded_model_claims":1,"entries":[{"metric_id":"trailing_eps","period":"FY2025","source_record":"record-01","source_tool":"synthetic_ledger","unit":"currency_per_share","value":"12.50"}]},"quality":{"completed_dimensions":["fundamentals","industry_supply_chain","market_technical","valuation_scenarios","catalysts_falsifiers","analyst_next_steps"],"effective_score":"1.00","gate_reasons":[],"integrity_gate":"pass","missing_dimensions":[],"utility_score":"1.00"},"rendered_report":"# Synthetic report","scenario":"ready_report","valuation":{"allows_target":true,"authorized_methods":["earnings_context","relative_context"],"reason":"positive_four_quarter_eps","state":"stable_profit"}}',
        )

    def test_domain_types_are_frozen_with_the_exact_field_surface(self) -> None:
        expected_fields = {
            MetricObservation: ("metric_id", "value", "period", "unit", "source_record", "status"),
            ToolResult: ("source_tool", "observations"),
            ProvenanceEntry: ("source_tool", "metric_id", "value", "period", "unit", "source_record"),
            ProvenanceIndex: ("entries", "discarded_model_claims"),
            FinancialQuarter: ("period", "revenue", "eps"),
            FinancialStateResult: ("state", "reason"),
            ValuationDecision: ("state", "reason", "authorized_methods", "allows_target"),
            AuditFinding: ("code", "severity", "message", "evidence"),
            AuditResult: ("findings", "confidence_cap"),
            QualityGovernanceResult: (
                "integrity_gate",
                "gate_reasons",
                "utility_score",
                "effective_score",
                "completed_dimensions",
                "missing_dimensions",
            ),
            CaseInput: (
                "scenario",
                "issuer",
                "symbol",
                "tool_results",
                "model_claimed_provenance",
                "quarters",
                "completed_dimensions",
                "draft_markdown",
            ),
            PipelineResult: (
                "scenario",
                "delivery",
                "provenance",
                "valuation",
                "audit",
                "quality",
                "rendered_report",
            ),
        }

        for domain_type, expected in expected_fields.items():
            with self.subTest(domain_type=domain_type.__name__):
                self.assertTrue(domain_type.__dataclass_params__.frozen)
                self.assertEqual(tuple(field.name for field in fields(domain_type)), expected)

        observation = MetricObservation(
            metric_id="trailing_eps",
            value=Decimal("12.50"),
            period="FY2025",
            unit="currency_per_share",
            source_record="record-01",
            status=EvidenceStatus.VALID,
        )
        with self.assertRaises(FrozenInstanceError):
            observation.period = "FY2026"  # type: ignore[misc]

    def test_domain_types_have_the_exact_annotation_surface(self) -> None:
        expected_hints = {
            MetricObservation: {
                "metric_id": str,
                "value": Decimal | None,
                "period": str,
                "unit": str,
                "source_record": str,
                "status": EvidenceStatus,
            },
            ToolResult: {"source_tool": str, "observations": tuple[MetricObservation, ...]},
            ProvenanceEntry: {
                "source_tool": str,
                "metric_id": str,
                "value": Decimal,
                "period": str,
                "unit": str,
                "source_record": str,
            },
            ProvenanceIndex: {"entries": tuple[ProvenanceEntry, ...], "discarded_model_claims": int},
            FinancialQuarter: {"period": str, "revenue": Decimal | None, "eps": Decimal | None},
            FinancialStateResult: {"state": FinancialState, "reason": str},
            ValuationDecision: {
                "state": FinancialState,
                "reason": str,
                "authorized_methods": tuple[str, ...],
                "allows_target": bool,
            },
            AuditFinding: {
                "code": str,
                "severity": FindingSeverity,
                "message": str,
                "evidence": tuple[str, ...],
            },
            AuditResult: {"findings": tuple[AuditFinding, ...], "confidence_cap": Decimal | None},
            QualityGovernanceResult: {
                "integrity_gate": IntegrityGateState,
                "gate_reasons": tuple[str, ...],
                "utility_score": Decimal,
                "effective_score": Decimal,
                "completed_dimensions": tuple[ResearchDimension, ...],
                "missing_dimensions": tuple[ResearchDimension, ...],
            },
            CaseInput: {
                "scenario": str,
                "issuer": str,
                "symbol": str,
                "tool_results": tuple[ToolResult, ...],
                "model_claimed_provenance": tuple[Mapping[str, object], ...],
                "quarters": tuple[FinancialQuarter, ...],
                "completed_dimensions": tuple[ResearchDimension, ...],
                "draft_markdown": str,
            },
            PipelineResult: {
                "scenario": str,
                "delivery": DeliveryState,
                "provenance": ProvenanceIndex,
                "valuation": ValuationDecision,
                "audit": AuditResult,
                "quality": QualityGovernanceResult,
                "rendered_report": str,
            },
        }

        for domain_type, expected in expected_hints.items():
            with self.subTest(domain_type=domain_type.__name__):
                self.assertEqual(get_type_hints(domain_type), expected)

    def test_recursive_serialization_rejects_non_string_mapping_keys(self) -> None:
        invalid_mapping = _MappingFixture(metadata={"nested": {1: "invalid"}})  # type: ignore[dict-item]

        with self.assertRaisesRegex(TypeError, "^Mapping keys must be str$"):
            _to_public_value(invalid_mapping)

    def test_frozen_enums_have_the_exact_public_values(self) -> None:
        self.assertEqual(
            {member.name: member.value for member in EvidenceStatus},
            {"VALID": "valid", "MISSING": "missing", "INVALID": "invalid", "CONFLICT": "conflict"},
        )
        self.assertEqual(
            {member.name: member.value for member in FinancialState},
            {
                "STABLE_PROFIT": "stable_profit",
                "REVENUE_WITHOUT_PROFIT": "revenue_without_profit",
                "PRE_REVENUE": "pre_revenue",
                "INSUFFICIENT_DATA": "insufficient_data",
            },
        )
        self.assertEqual(
            {member.name: member.value for member in ResearchDimension},
            {
                "FUNDAMENTALS": "fundamentals",
                "INDUSTRY_SUPPLY_CHAIN": "industry_supply_chain",
                "MARKET_TECHNICAL": "market_technical",
                "VALUATION_SCENARIOS": "valuation_scenarios",
                "CATALYSTS_FALSIFIERS": "catalysts_falsifiers",
                "ANALYST_NEXT_STEPS": "analyst_next_steps",
            },
        )
        self.assertEqual(
            {member.name: member.value for member in IntegrityGateState},
            {"PASS": "pass", "FAIL": "fail"},
        )
        self.assertEqual(
            {member.name: member.value for member in FindingSeverity},
            {"INFO": "info", "REVIEW": "review", "BLOCK": "block"},
        )
        self.assertEqual(
            {member.name: member.value for member in DeliveryState},
            {
                "EDITABLE_DRAFT": "editable_draft",
                "CONTEXT_ONLY": "context_only",
                "REVIEW_REQUIRED": "review_required",
                "WITHHELD": "withheld",
            },
        )
        self.assertTrue(issubclass(EvidenceStatus, str))
        self.assertTrue(issubclass(FinancialState, str))
        self.assertTrue(issubclass(ResearchDimension, str))
        self.assertTrue(issubclass(IntegrityGateState, str))
        self.assertTrue(issubclass(FindingSeverity, str))
        self.assertTrue(issubclass(DeliveryState, str))
        self.assertTrue(issubclass(EvidenceStatus, Enum))


if __name__ == "__main__":
    unittest.main()
