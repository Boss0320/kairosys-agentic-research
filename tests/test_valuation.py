from __future__ import annotations

from decimal import Decimal
import unittest

from demo.kairosys_case.model import (
    FinancialQuarter,
    FinancialState,
    FinancialStateResult,
)
from demo.kairosys_case.valuation import authorize_valuation, classify_financial_state


def fq(*rows: tuple[str, str | None, str | None]) -> tuple[FinancialQuarter, ...]:
    return tuple(
        FinancialQuarter(
            period=period,
            revenue=None if revenue is None else Decimal(revenue),
            eps=None if eps is None else Decimal(eps),
        )
        for period, revenue, eps in rows
    )


CASES = (
    (
        fq(("2026Q2", "125", "1.2"), ("2026Q1", "118", "1.0"),
           ("2025Q4", "111", "0.9"), ("2025Q3", "105", "0.8")),
        "stable_profit", "positive_four_quarter_eps",
    ),
    (
        fq(("2026Q2", "125", "-1.2"), ("2026Q1", "118", "-1.0"),
           ("2025Q4", "111", "-0.9"), ("2025Q3", "105", "-0.8")),
        "revenue_without_profit", "revenue_present_without_positive_eps",
    ),
    (
        fq(("2026Q2", "0", "0"), ("2026Q1", "0", "0"),
           ("2025Q4", "0", "0"), ("2025Q3", "0", "0")),
        "pre_revenue", "zero_revenue_without_positive_eps",
    ),
    (
        fq(("2026Q2", "125", "1.2"), ("2026Q1", "118", "1.0"),
           ("2025Q4", "111", "0.9")),
        "insufficient_data", "insufficient_periods",
    ),
    (
        fq(("2026Q2", "125", "1.2"), ("2026Q2", "118", "1.0"),
           ("2025Q4", "111", "0.9"), ("2025Q3", "105", "0.8")),
        "insufficient_data", "duplicate_period",
    ),
    (
        fq(("2026Q2", "125", "1.2"), ("2025Q4", "118", "1.0"),
           ("2025Q3", "111", "0.9"), ("2025Q2", "105", "0.8")),
        "insufficient_data", "non_consecutive_periods",
    ),
    (
        fq(("2026Q2", None, "1.2"), ("2026Q1", "118", "1.0"),
           ("2025Q4", "111", "0.9"), ("2025Q3", "105", "0.8")),
        "insufficient_data", "missing_revenue",
    ),
    (
        fq(("2026Q2", "0", "1.2"), ("2026Q1", "0", "1.0"),
           ("2025Q4", "0", "0.9"), ("2025Q3", "0", "0.8")),
        "insufficient_data", "revenue_eps_conflict",
    ),
)


class FinancialStateTests(unittest.TestCase):
    def test_classifies_the_approved_eight_row_matrix(self) -> None:
        for quarters, state, reason in CASES:
            with self.subTest(state=state, reason=reason):
                self.assertEqual(
                    classify_financial_state(quarters),
                    FinancialStateResult(FinancialState(state), reason),
                )

    def test_requires_newest_first_quarter_order(self) -> None:
        quarters = fq(
            ("2025Q3", "105", "0.8"),
            ("2025Q4", "111", "0.9"),
            ("2026Q1", "118", "1.0"),
            ("2026Q2", "125", "1.2"),
        )

        self.assertEqual(
            classify_financial_state(quarters),
            FinancialStateResult(FinancialState.INSUFFICIENT_DATA, "non_consecutive_periods"),
        )

    def test_rejects_malformed_period_with_an_explicit_reason(self) -> None:
        quarters = fq(
            ("2026Q5", "125", "1.2"),
            ("2026Q1", "118", "1.0"),
            ("2025Q4", "111", "0.9"),
            ("2025Q3", "105", "0.8"),
        )

        self.assertEqual(
            classify_financial_state(quarters),
            FinancialStateResult(FinancialState.INSUFFICIENT_DATA, "invalid_period"),
        )

    def test_rejects_missing_eps_with_an_explicit_reason(self) -> None:
        quarters = fq(
            ("2026Q2", "125", None),
            ("2026Q1", "118", "1.0"),
            ("2025Q4", "111", "0.9"),
            ("2025Q3", "105", "0.8"),
        )

        self.assertEqual(
            classify_financial_state(quarters),
            FinancialStateResult(FinancialState.INSUFFICIENT_DATA, "missing_eps"),
        )

    def test_rejects_boolean_financial_values(self) -> None:
        quarters = (
            FinancialQuarter("2026Q2", True, Decimal("1.2")),
            FinancialQuarter("2026Q1", Decimal("118"), Decimal("1.0")),
            FinancialQuarter("2025Q4", Decimal("111"), Decimal("0.9")),
            FinancialQuarter("2025Q3", Decimal("105"), Decimal("0.8")),
        )

        with self.assertRaises(TypeError):
            classify_financial_state(quarters)

    def test_rejects_boolean_eps(self) -> None:
        quarters = (
            FinancialQuarter("2026Q2", Decimal("125"), True),
            FinancialQuarter("2026Q1", Decimal("118"), Decimal("1.0")),
            FinancialQuarter("2025Q4", Decimal("111"), Decimal("0.9")),
            FinancialQuarter("2025Q3", Decimal("105"), Decimal("0.8")),
        )

        with self.assertRaises(TypeError):
            classify_financial_state(quarters)

    def test_rejects_integer_revenue(self) -> None:
        quarters = (
            FinancialQuarter("2026Q2", 125, Decimal("1.2")),
            FinancialQuarter("2026Q1", Decimal("118"), Decimal("1.0")),
            FinancialQuarter("2025Q4", Decimal("111"), Decimal("0.9")),
            FinancialQuarter("2025Q3", Decimal("105"), Decimal("0.8")),
        )

        with self.assertRaises(TypeError):
            classify_financial_state(quarters)

    def test_rejects_float_eps(self) -> None:
        quarters = (
            FinancialQuarter("2026Q2", Decimal("125"), 1.2),
            FinancialQuarter("2026Q1", Decimal("118"), Decimal("1.0")),
            FinancialQuarter("2025Q4", Decimal("111"), Decimal("0.9")),
            FinancialQuarter("2025Q3", Decimal("105"), Decimal("0.8")),
        )

        with self.assertRaises(TypeError):
            classify_financial_state(quarters)

    def test_classifies_mixed_sign_eps_by_decimal_sum(self) -> None:
        cases = (
            (
                fq(
                    ("2026Q2", "125", "2"),
                    ("2026Q1", "118", "-1"),
                    ("2025Q4", "111", "0"),
                    ("2025Q3", "105", "0"),
                ),
                FinancialState.STABLE_PROFIT,
                "positive_four_quarter_eps",
            ),
            (
                fq(
                    ("2026Q2", "125", "1"),
                    ("2026Q1", "118", "-2"),
                    ("2025Q4", "111", "0"),
                    ("2025Q3", "105", "0"),
                ),
                FinancialState.REVENUE_WITHOUT_PROFIT,
                "revenue_present_without_positive_eps",
            ),
        )
        for quarters, state, reason in cases:
            with self.subTest(state=state):
                self.assertEqual(
                    classify_financial_state(quarters),
                    FinancialStateResult(state, reason),
                )


class ValuationAuthorizationTests(unittest.TestCase):
    def test_authorizes_exactly_the_public_state_table(self) -> None:
        cases = (
            (FinancialState.STABLE_PROFIT, ("earnings_context",), True),
            (FinancialState.REVENUE_WITHOUT_PROFIT, ("revenue_context",), False),
            (FinancialState.PRE_REVENUE, ("milestone_context",), False),
            (FinancialState.INSUFFICIENT_DATA, (), False),
        )
        for state, authorized_methods, allows_target in cases:
            with self.subTest(state=state):
                result = authorize_valuation(FinancialStateResult(state, "state_reason"))
                self.assertEqual(result.state, state)
                self.assertEqual(result.reason, "state_reason")
                self.assertEqual(result.authorized_methods, authorized_methods)
                self.assertEqual(result.allows_target, allows_target)


if __name__ == "__main__":
    unittest.main()
