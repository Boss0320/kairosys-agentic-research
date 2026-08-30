"""Classify synthetic financial history before authorizing draft context."""

from __future__ import annotations

from decimal import Decimal
import re
from typing import Sequence

from .model import FinancialQuarter, FinancialState, FinancialStateResult, ValuationDecision


_QUARTER = re.compile(r"(?P<year>\d{4})Q(?P<quarter>[1-4])")

AUTHORIZATION = {
    FinancialState.STABLE_PROFIT: (("earnings_context",), True),
    FinancialState.REVENUE_WITHOUT_PROFIT: (("revenue_context",), False),
    FinancialState.PRE_REVENUE: (("milestone_context",), False),
    FinancialState.INSUFFICIENT_DATA: ((), False),
}


def _quarter_index(period: str) -> int | None:
    match = _QUARTER.fullmatch(period)
    if match is None:
        return None
    return int(match["year"]) * 4 + int(match["quarter"]) - 1


def _validate_amount(value: Decimal | None) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, Decimal):
        raise TypeError("financial values must be Decimal or None")


def _insufficient(reason: str) -> FinancialStateResult:
    return FinancialStateResult(FinancialState.INSUFFICIENT_DATA, reason)


def classify_financial_state(quarters: Sequence[FinancialQuarter]) -> FinancialStateResult:
    """Classify exactly four newest-first synthetic financial quarters."""
    if len(quarters) != 4:
        return _insufficient("insufficient_periods")

    periods = tuple(quarter.period for quarter in quarters)
    if len(set(periods)) != 4:
        return _insufficient("duplicate_period")

    indices = tuple(_quarter_index(period) for period in periods)
    if any(index is None for index in indices):
        return _insufficient("invalid_period")
    if any(current != following + 1 for current, following in zip(indices, indices[1:])):
        return _insufficient("non_consecutive_periods")

    for quarter in quarters:
        _validate_amount(quarter.revenue)
        _validate_amount(quarter.eps)
    if any(quarter.revenue is None for quarter in quarters):
        return _insufficient("missing_revenue")
    if any(quarter.eps is None for quarter in quarters):
        return _insufficient("missing_eps")

    revenues = tuple(quarter.revenue for quarter in quarters)
    eps_values = tuple(quarter.eps for quarter in quarters)
    total_eps = sum(eps_values, Decimal("0"))
    if all(revenue == Decimal("0") for revenue in revenues):
        if total_eps > Decimal("0"):
            return _insufficient("revenue_eps_conflict")
        return FinancialStateResult(
            FinancialState.PRE_REVENUE,
            "zero_revenue_without_positive_eps",
        )
    if total_eps > Decimal("0"):
        return FinancialStateResult(FinancialState.STABLE_PROFIT, "positive_four_quarter_eps")
    return FinancialStateResult(
        FinancialState.REVENUE_WITHOUT_PROFIT,
        "revenue_present_without_positive_eps",
    )


def authorize_valuation(state: FinancialStateResult) -> ValuationDecision:
    """Authorize synthetic draft context; this demo never calculates a valuation."""
    authorized_methods, allows_target = AUTHORIZATION[state.state]
    return ValuationDecision(
        state=state.state,
        reason=state.reason,
        authorized_methods=authorized_methods,
        allows_target=allows_target,
    )
