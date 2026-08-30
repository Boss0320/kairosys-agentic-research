"""Audit four explicit report labels in the synthetic rendered draft."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

from demo.kairosys_case.model import (
    AuditFinding,
    AuditResult,
    DeliveryState,
    FinancialState,
    FindingSeverity,
    IntegrityGateState,
    ProvenanceIndex,
    QualityGovernanceResult,
    ValuationDecision,
)


_CLAIMED_METRIC = re.compile(r"^\*\*Claimed metric:\*\*\s*(?P<metric>\S+)\s*$")
_SYNTHETIC_TARGET = re.compile(r"^\s*\*\*Synthetic target:\*\*(?P<suffix>.*)$")
_FORWARD_EPS = re.compile(r"^\s*\*\*Forward EPS:\*\*(?P<suffix>.*)$")
_DISPLAYED_PE = re.compile(r"^\s*\*\*Displayed P/E:\*\*(?P<suffix>.*)$")
_DECIMAL = re.compile(r"(?:0|[1-9]\d*)(?:\.\d+)?$")
UTILITY_EDITABLE_THRESHOLD = Decimal("0.75")
UTILITY_REVIEW_CAP = Decimal("0.60")


def _matched_lines(
    markdown: str,
    pattern: re.Pattern[str],
    group_name: str,
) -> tuple[tuple[str, str], ...]:
    return tuple(
        (line, match[group_name])
        for line in markdown.splitlines()
        if (match := pattern.fullmatch(line)) is not None
    )


def _parse_decimal(token: str, *, pe_multiple: bool = False) -> Decimal | None:
    normalized = token.strip()
    raw_number = normalized[:-1] if pe_multiple and normalized.endswith("x") else normalized
    if pe_multiple and raw_number == normalized:
        return None
    if _DECIMAL.fullmatch(raw_number) is None:
        return None
    try:
        value = Decimal(raw_number)
    except InvalidOperation:
        return None
    return value if value.is_finite() else None


def _finding(
    code: str,
    severity: FindingSeverity,
    message: str,
    evidence: tuple[str, ...],
) -> AuditFinding:
    return AuditFinding(code=code, severity=severity, message=message, evidence=evidence)


def audit_rendered_report(
    markdown: str,
    provenance: ProvenanceIndex,
    valuation: ValuationDecision,
) -> AuditResult:
    """Check four approved labels; this is not a general Markdown verifier."""
    claimed_metrics = _matched_lines(markdown, _CLAIMED_METRIC, "metric")
    targets = _matched_lines(markdown, _SYNTHETIC_TARGET, "suffix")
    forward_eps = _matched_lines(markdown, _FORWARD_EPS, "suffix")
    displayed_pe = _matched_lines(markdown, _DISPLAYED_PE, "suffix")
    findings: list[AuditFinding] = []

    trusted_metrics = {entry.metric_id for entry in provenance.entries}
    unsupported_claims = tuple(line for line, metric in claimed_metrics if metric not in trusted_metrics)
    if unsupported_claims:
        findings.append(
            _finding(
                "RPT-SOURCE",
                FindingSeverity.REVIEW,
                "claimed metric lacks trusted synthetic evidence",
                unsupported_claims,
            )
        )

    if targets and not valuation.allows_target:
        findings.append(
            _finding(
                "RPT-AUTH",
                FindingSeverity.BLOCK,
                "synthetic target is not authorized for this financial state",
                tuple(line for line, _ in targets),
            )
        )

    parsed_eps = tuple((line, _parse_decimal(value)) for line, value in forward_eps)
    valid_eps = {value for _, value in parsed_eps if value is not None}
    if len(valid_eps) > 1:
        findings.append(
            _finding(
                "RPT-DUP",
                FindingSeverity.BLOCK,
                "conflicting Forward EPS values appear in the rendered draft",
                tuple(line for line, value in parsed_eps if value is not None),
            )
        )

    parsed_targets = tuple((line, _parse_decimal(value)) for line, value in targets)
    parsed_pe = tuple((line, _parse_decimal(value, pe_multiple=True)) for line, value in displayed_pe)
    malformed_lines = tuple(
        line
        for values in (parsed_targets, parsed_eps, parsed_pe)
        for line, value in values
        if value is None
    )
    if malformed_lines:
        findings.append(
            _finding(
                "RPT-MATH",
                FindingSeverity.BLOCK,
                "rendered numeric label is malformed or non-finite",
                malformed_lines,
            )
        )
    elif len(parsed_targets) == len(parsed_pe) == 1 and len(valid_eps) == 1:
        target = parsed_targets[0][1]
        forward = next(iter(valid_eps))
        multiple = parsed_pe[0][1]
        numeric_evidence = tuple(line for line, _ in parsed_targets + parsed_eps + parsed_pe)
        try:
            expected = (target / forward).quantize(
                Decimal(1).scaleb(multiple.as_tuple().exponent),
                rounding=ROUND_HALF_UP,
            )
        except (InvalidOperation, ZeroDivisionError):
            expected = None
        if forward == Decimal("0") or expected is None or expected != multiple:
            findings.append(
                _finding(
                    "RPT-MATH",
                    FindingSeverity.BLOCK,
                    "Displayed P/E does not match rounded Synthetic target divided by Forward EPS",
                    numeric_evidence,
                )
            )

    return AuditResult(findings=tuple(findings), confidence_cap=None)


def _strip_target_lines(markdown: str) -> str:
    return "\n".join(
        line
        for line in markdown.splitlines()
        if _SYNTHETIC_TARGET.fullmatch(line) is None and _DISPLAYED_PE.fullmatch(line) is None
    ).strip()


def apply_delivery_policy(
    markdown: str,
    valuation: ValuationDecision,
    audit: AuditResult,
    quality: QualityGovernanceResult,
) -> tuple[DeliveryState, str, Decimal | None]:
    """Return the approved delivery meaning for the rendered synthetic draft."""
    if not markdown.strip():
        return DeliveryState.WITHHELD, "", None
    if any(finding.code == "RPT-AUTH" for finding in audit.findings):
        return DeliveryState.CONTEXT_ONLY, _strip_target_lines(markdown), None
    if (
        quality.integrity_gate is IntegrityGateState.FAIL
        or valuation.state is FinancialState.INSUFFICIENT_DATA
        or any(finding.severity is FindingSeverity.BLOCK for finding in audit.findings)
    ):
        return DeliveryState.REVIEW_REQUIRED, "REVIEW REQUIRED\n\n" + markdown.strip(), Decimal("0.40")
    if any(finding.severity is FindingSeverity.REVIEW for finding in audit.findings):
        return DeliveryState.REVIEW_REQUIRED, "REVIEW REQUIRED\n\n" + markdown.strip(), Decimal("0.40")
    if quality.utility_score < UTILITY_EDITABLE_THRESHOLD:
        return DeliveryState.REVIEW_REQUIRED, "REVIEW REQUIRED\n\n" + markdown.strip(), UTILITY_REVIEW_CAP
    return DeliveryState.EDITABLE_DRAFT, markdown.strip(), None
