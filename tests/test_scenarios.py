from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal
import re
import unittest

from demo.kairosys_case.model import EvidenceStatus, ResearchDimension
from demo.kairosys_case.quality_governance import ALL_DIMENSIONS
from demo.kairosys_case.scenarios import SCENARIO_NAMES, load_scenario


EXPECTED = {
    "ready_report",
    "spoofed_provenance",
    "incomplete_financials",
    "contradictory_financials",
    "rendered_math_conflict",
    "shallow_but_sound",
}
_ENVIRONMENT_SHAPED_NAME = re.compile(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+){2,}\b")
_URL = re.compile(r"https?://|www\.", re.IGNORECASE)


class ScenarioCatalogTests(unittest.TestCase):
    def test_catalog_has_exactly_the_six_approved_names(self) -> None:
        self.assertEqual(set(SCENARIO_NAMES), EXPECTED)
        self.assertEqual(len(SCENARIO_NAMES), len(EXPECTED))

    def test_each_case_is_synthetic_and_uses_only_safe_identifiers(self) -> None:
        for name in SCENARIO_NAMES:
            with self.subTest(name=name):
                case = load_scenario(name)
                source_identifiers = tuple(
                    value
                    for result in case.tool_results
                    for value in (result.source_tool, *(item.source_record for item in result.observations))
                )
                text_values = (case.issuer, case.symbol, case.draft_markdown, *source_identifiers)

                self.assertEqual(case.scenario, name)
                self.assertEqual(case.issuer, "Northstar Circuits")
                self.assertEqual(case.symbol, "SYNTH-KAI-01")
                self.assertLessEqual(len(case.quarters), 4)
                self.assertTrue(all(not _URL.search(value) for value in text_values))
                self.assertTrue(all(not _ENVIRONMENT_SHAPED_NAME.search(value) for value in text_values))
                self.assertTrue(all("production" not in value.lower() for value in text_values))

    def test_case_inputs_and_model_claims_are_immutable(self) -> None:
        case = load_scenario("spoofed_provenance")

        with self.assertRaises(FrozenInstanceError):
            case.issuer = "Changed issuer"  # type: ignore[misc]
        with self.assertRaises(TypeError):
            case.model_claimed_provenance[0]["metric_id"] = "changed"  # type: ignore[index]

    def test_ready_case_has_profitable_four_quarter_history_and_forward_eps_evidence(self) -> None:
        case = load_scenario("ready_report")
        observations = tuple(item for result in case.tool_results for item in result.observations)

        self.assertEqual(len(case.quarters), 4)
        self.assertTrue(all(quarter.revenue is not None and quarter.revenue > 0 for quarter in case.quarters))
        self.assertTrue(all(quarter.eps is not None and quarter.eps > 0 for quarter in case.quarters))
        self.assertIn(
            ("forward_eps", Decimal("5.00"), EvidenceStatus.VALID),
            tuple((item.metric_id, item.value, item.status) for item in observations),
        )

    def test_spoofed_case_uses_only_a_model_market_share_claim(self) -> None:
        case = load_scenario("spoofed_provenance")
        deterministic_metrics = {
            item.metric_id for result in case.tool_results for item in result.observations
        }

        self.assertIn("market_share", {claim["metric_id"] for claim in case.model_claimed_provenance})
        self.assertNotIn("market_share", deterministic_metrics)

    def test_shallow_case_has_only_two_completed_research_dimensions(self) -> None:
        case = load_scenario("shallow_but_sound")

        self.assertEqual(
            case.completed_dimensions,
            (
                ResearchDimension.FUNDAMENTALS,
                ResearchDimension.INDUSTRY_SUPPLY_CHAIN,
            ),
        )
        self.assertTrue(all(isinstance(item, ResearchDimension) for item in case.completed_dimensions))

    def test_all_other_cases_model_complete_utility_coverage(self) -> None:
        for name in SCENARIO_NAMES:
            if name == "shallow_but_sound":
                continue
            with self.subTest(name=name):
                self.assertEqual(load_scenario(name).completed_dimensions, ALL_DIMENSIONS)

    def test_incomplete_case_has_three_quarters_and_deterministic_revenue(self) -> None:
        case = load_scenario("incomplete_financials")
        observations = tuple(item for result in case.tool_results for item in result.observations)

        self.assertEqual(len(case.quarters), 3)
        self.assertIn(
            ("revenue", EvidenceStatus.VALID),
            tuple((item.metric_id, item.status) for item in observations),
        )

    def test_contradictory_case_has_zero_revenue_positive_eps_and_no_draft(self) -> None:
        case = load_scenario("contradictory_financials")

        self.assertEqual(case.draft_markdown, "")
        self.assertTrue(any(quarter.revenue == Decimal("0") for quarter in case.quarters))
        self.assertTrue(any(quarter.eps is not None and quarter.eps > 0 for quarter in case.quarters))

    def test_all_drafts_exactly_match_the_approved_shapes(self) -> None:
        expected_drafts = {
            "ready_report": """# Northstar Circuits — Synthetic research draft
**Claimed metric:** forward_eps
**Synthetic target:** 120
**Forward EPS:** 5.00
**Displayed P/E:** 24.0x
""",
            "spoofed_provenance": """# Northstar Circuits — Synthetic research draft
**Claimed metric:** market_share
The draft asserts a market-share figure that exists only in model-supplied provenance.
""",
            "incomplete_financials": """# Northstar Circuits — Synthetic research draft
**Claimed metric:** revenue
**Synthetic target:** 120
**Forward EPS:** 5.00
**Displayed P/E:** 24.0x
Operating context remains useful, but the four-quarter window is incomplete.
""",
            "contradictory_financials": "",
            "rendered_math_conflict": """# Northstar Circuits — Synthetic research draft
**Claimed metric:** forward_eps
**Synthetic target:** 120
**Forward EPS:** 5.00
**Displayed P/E:** 20.0x
""",
            "shallow_but_sound": """# Northstar Circuits — Synthetic research draft
**Claimed metric:** revenue
The available facts are consistent, but valuation, catalysts, falsifiers, and analyst next steps are absent.
""",
        }

        self.assertEqual(
            {name: load_scenario(name).draft_markdown for name in SCENARIO_NAMES},
            expected_drafts,
        )

    def test_every_case_has_its_exact_approved_quarter_sequence(self) -> None:
        expected_periods = {
            "ready_report": ("2026Q2", "2026Q1", "2025Q4", "2025Q3"),
            "spoofed_provenance": ("2026Q2", "2026Q1", "2025Q4", "2025Q3"),
            "incomplete_financials": ("2026Q2", "2026Q1", "2025Q4"),
            "contradictory_financials": ("2026Q2", "2026Q1", "2025Q4", "2025Q3"),
            "rendered_math_conflict": ("2026Q2", "2026Q1", "2025Q4", "2025Q3"),
            "shallow_but_sound": ("2026Q2", "2026Q1", "2025Q4", "2025Q3"),
        }

        self.assertEqual(
            {name: tuple(quarter.period for quarter in load_scenario(name).quarters) for name in SCENARIO_NAMES},
            expected_periods,
        )

    def test_unknown_scenario_fails_closed(self) -> None:
        with self.assertRaisesRegex(KeyError, "unknown scenario"):
            load_scenario("unapproved_case")


if __name__ == "__main__":
    unittest.main()
