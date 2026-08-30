from __future__ import annotations

from decimal import Decimal
from collections.abc import Iterator, Mapping
import unittest

from demo.kairosys_case.model import EvidenceStatus, MetricObservation, ToolResult
from demo.kairosys_case.provenance import build_provenance_index


class _ExplodingModelClaim(Mapping[str, object]):
    def __getitem__(self, key: str) -> object:
        raise AssertionError(f"model claim was accessed through {key}")

    def __iter__(self) -> Iterator[str]:
        raise AssertionError("model claim was iterated")

    def __len__(self) -> int:
        return 2


class ProvenanceIndexTests(unittest.TestCase):
    def test_model_cannot_promote_its_own_source_claim(self) -> None:
        index = build_provenance_index(
            tool_results=(),
            model_claimed_provenance=({"metric_id": "market_share", "value": "42"},),
        )

        self.assertEqual(index.entries, ())
        self.assertEqual(index.discarded_model_claims, 1)

    def test_model_claim_contents_are_never_accessed(self) -> None:
        index = build_provenance_index(
            tool_results=(),
            model_claimed_provenance=(_ExplodingModelClaim(),),
        )

        self.assertEqual(index.entries, ())
        self.assertEqual(index.discarded_model_claims, 1)

    def test_only_valid_deterministic_observations_enter_index(self) -> None:
        valid = MetricObservation(
            metric_id="revenue",
            value=Decimal("125.0"),
            period="2026Q2",
            unit="TWD_million",
            source_record="SYNTH-RECORD-01",
            status=EvidenceStatus.VALID,
        )
        missing = MetricObservation(
            metric_id="eps",
            value=None,
            period="2026Q2",
            unit="TWD_per_share",
            source_record="SYNTH-RECORD-02",
            status=EvidenceStatus.MISSING,
        )

        index = build_provenance_index(
            tool_results=(ToolResult("statement_reader", (valid, missing)),),
            model_claimed_provenance=(),
        )

        self.assertEqual(tuple(item.metric_id for item in index.entries), ("revenue",))

    def test_invalid_statuses_and_missing_values_are_excluded(self) -> None:
        observations = (
            MetricObservation(
                "valid_value", Decimal("1"), "2026Q2", "TWD_million", "SYNTH-RECORD-10", EvidenceStatus.VALID
            ),
            MetricObservation(
                "valid_missing", None, "2026Q2", "TWD_million", "SYNTH-RECORD-11", EvidenceStatus.VALID
            ),
            MetricObservation(
                "missing_value", None, "2026Q2", "TWD_million", "SYNTH-RECORD-12", EvidenceStatus.MISSING
            ),
            MetricObservation(
                "invalid_value", Decimal("2"), "2026Q2", "TWD_million", "SYNTH-RECORD-13", EvidenceStatus.INVALID
            ),
            MetricObservation(
                "conflict_value", Decimal("3"), "2026Q2", "TWD_million", "SYNTH-RECORD-14", EvidenceStatus.CONFLICT
            ),
        )

        index = build_provenance_index(
            tool_results=(ToolResult("statement_reader", observations),),
            model_claimed_provenance=(),
        )

        self.assertEqual(tuple(item.metric_id for item in index.entries), ("valid_value",))

    def test_duplicate_metric_with_conflicting_values_is_not_flattened(self) -> None:
        first = MetricObservation(
            "revenue",
            Decimal("125.0"),
            "2026Q2",
            "TWD_million",
            "SYNTH-RECORD-01",
            EvidenceStatus.VALID,
        )
        second = MetricObservation(
            "revenue",
            Decimal("131.0"),
            "2026Q2",
            "TWD_million",
            "SYNTH-RECORD-02",
            EvidenceStatus.VALID,
        )

        index = build_provenance_index(
            tool_results=(
                ToolResult("statement_reader", (first,)),
                ToolResult("filing_reader", (second,)),
            ),
            model_claimed_provenance=(),
        )

        self.assertEqual(
            tuple(item.value for item in index.entries),
            (Decimal("131.0"), Decimal("125.0")),
        )

    def test_equal_sort_keys_preserve_input_order_without_value_tiebreaking(self) -> None:
        first = MetricObservation(
            "revenue", Decimal("131.0"), "2026Q2", "TWD_million", "SYNTH-RECORD-20", EvidenceStatus.VALID
        )
        second = MetricObservation(
            "revenue", Decimal("125.0"), "2026Q2", "TWD_million", "SYNTH-RECORD-20", EvidenceStatus.VALID
        )

        index = build_provenance_index(
            tool_results=(ToolResult("statement_reader", (first, second)),),
            model_claimed_provenance=(),
        )

        self.assertEqual(tuple(item.value for item in index.entries), (Decimal("131.0"), Decimal("125.0")))

    def test_entries_sort_by_the_full_trusted_identity(self) -> None:
        observations = (
            MetricObservation(
                "eps", Decimal("4.0"), "2026Q2", "TWD_per_share", "SYNTH-RECORD-03", EvidenceStatus.VALID
            ),
            MetricObservation(
                "eps", Decimal("3.0"), "2026Q1", "TWD_per_share", "SYNTH-RECORD-02", EvidenceStatus.VALID
            ),
            MetricObservation(
                "revenue", Decimal("120.0"), "2026Q2", "TWD_million", "SYNTH-RECORD-01", EvidenceStatus.VALID
            ),
        )

        index = build_provenance_index(
            tool_results=(ToolResult("statement_reader", observations),),
            model_claimed_provenance=(),
        )

        self.assertEqual(
            tuple((item.metric_id, item.period, item.unit, item.source_tool, item.source_record) for item in index.entries),
            (
                ("eps", "2026Q1", "TWD_per_share", "statement_reader", "SYNTH-RECORD-02"),
                ("eps", "2026Q2", "TWD_per_share", "statement_reader", "SYNTH-RECORD-03"),
                ("revenue", "2026Q2", "TWD_million", "statement_reader", "SYNTH-RECORD-01"),
            ),
        )


if __name__ == "__main__":
    unittest.main()
