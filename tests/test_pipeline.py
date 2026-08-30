from __future__ import annotations

import ast
import builtins
from contextlib import redirect_stderr
from dataclasses import fields
from decimal import Decimal
from io import StringIO
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from demo.kairosys_case import cli
from demo.kairosys_case.model import (
    AuditResult,
    DeliveryState,
    IntegrityGateState,
)
from demo.kairosys_case.pipeline import evaluate_case, run_scenario
from demo.kairosys_case.scenarios import SCENARIO_NAMES, load_scenario
from demo.kairosys_case.serialization import to_stable_json


EXPECTED = {
    "ready_report": "editable_draft",
    "spoofed_provenance": "review_required",
    "incomplete_financials": "context_only",
    "contradictory_financials": "withheld",
    "rendered_math_conflict": "review_required",
    "shallow_but_sound": "review_required",
}

_MODULES = (
    "model.py",
    "provenance.py",
    "valuation.py",
    "report_audit.py",
    "quality_governance.py",
    "pipeline.py",
    "scenarios.py",
)
_ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "dataclasses",
    "decimal",
    "demo",
    "enum",
    "re",
    "types",
    "typing",
}
_FORBIDDEN_CALLS = {"open", "eval", "exec", "compile", "__import__"}


class PipelineScenarioTests(unittest.TestCase):
    def test_each_approved_scenario_has_its_exact_delivery_outcome(self) -> None:
        self.assertEqual(
            {name: run_scenario(name).delivery.value for name in SCENARIO_NAMES},
            EXPECTED,
        )

    def test_spoofed_provenance_discards_the_model_claim_without_trusting_market_share(self) -> None:
        result = run_scenario("spoofed_provenance")

        self.assertEqual(result.provenance.discarded_model_claims, 1)
        self.assertNotIn("market_share", {entry.metric_id for entry in result.provenance.entries})

    def test_incomplete_financials_delivers_context_without_a_synthetic_target(self) -> None:
        result = run_scenario("incomplete_financials")

        self.assertEqual(result.delivery, DeliveryState.CONTEXT_ONLY)
        self.assertNotIn("Synthetic target", result.rendered_report)

    def test_contradictory_financials_withholds_an_empty_report_with_its_exact_reason(self) -> None:
        result = run_scenario("contradictory_financials")

        self.assertEqual(result.valuation.reason, "revenue_eps_conflict")
        self.assertEqual(result.rendered_report, "")
        self.assertEqual(result.delivery, DeliveryState.WITHHELD)

    def test_math_conflict_keeps_labeled_draft_and_copies_the_delivery_confidence_cap(self) -> None:
        result = run_scenario("rendered_math_conflict")

        self.assertEqual(result.delivery, DeliveryState.REVIEW_REQUIRED)
        self.assertTrue(result.rendered_report.startswith("REVIEW REQUIRED\n\n"))
        self.assertEqual(result.audit.confidence_cap, Decimal("0.40"))
        self.assertEqual(to_stable_json(result), to_stable_json(result))

    def test_high_utility_math_conflict_cannot_average_away_integrity_failure(self) -> None:
        result = run_scenario("rendered_math_conflict")

        self.assertEqual(result.quality.integrity_gate, IntegrityGateState.FAIL)
        self.assertEqual(result.quality.utility_score, Decimal("1.00"))
        self.assertEqual(result.quality.effective_score, Decimal("0.40"))

    def test_shallow_but_sound_is_reviewed_for_utility_alone(self) -> None:
        result = run_scenario("shallow_but_sound")

        self.assertEqual(result.quality.integrity_gate, IntegrityGateState.PASS)
        self.assertEqual(result.quality.gate_reasons, ())
        self.assertEqual(result.quality.utility_score, Decimal("0.35"))
        self.assertEqual(result.quality.effective_score, Decimal("0.35"))
        self.assertEqual(result.audit.findings, ())
        self.assertEqual(result.audit.confidence_cap, Decimal("0.60"))
        self.assertEqual(result.delivery, DeliveryState.REVIEW_REQUIRED)

    def test_identical_scenario_evaluation_produces_identical_json_bytes(self) -> None:
        for name in SCENARIO_NAMES:
            with self.subTest(name=name):
                self.assertEqual(
                    to_stable_json(run_scenario(name)).encode("ascii"),
                    to_stable_json(run_scenario(name)).encode("ascii"),
                )

    def test_evaluate_case_leaves_the_input_and_prior_audit_immutable(self) -> None:
        case = load_scenario("rendered_math_conflict")
        prior_audit = AuditResult(findings=(), confidence_cap=None)

        result = evaluate_case(case)

        self.assertEqual(tuple(field.name for field in fields(case)), (
            "scenario", "issuer", "symbol", "tool_results", "model_claimed_provenance",
            "quarters", "completed_dimensions", "draft_markdown",
        ))
        self.assertEqual(prior_audit.confidence_cap, None)
        self.assertEqual(result.audit.confidence_cap, Decimal("0.40"))


class OfflineCallSurfaceTests(unittest.TestCase):
    def test_pipeline_modules_allow_only_the_declared_import_roots_and_no_forbidden_calls(self) -> None:
        package_dir = Path(__file__).resolve().parents[1] / "demo" / "kairosys_case"

        for module_name in _MODULES:
            with self.subTest(module=module_name):
                tree = ast.parse((package_dir / module_name).read_text(encoding="utf-8"))
                roots = {
                    alias.name.split(".", 1)[0]
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Import)
                    for alias in node.names
                }
                roots.update(
                    node.module.split(".", 1)[0]
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None
                )
                calls = {
                    node.func.id
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                }
                calls.update(
                    node.func.attr
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "builtins"
                )

                self.assertTrue(roots <= _ALLOWED_IMPORT_ROOTS, roots - _ALLOWED_IMPORT_ROOTS)
                self.assertFalse(calls & _FORBIDDEN_CALLS, calls & _FORBIDDEN_CALLS)

    def test_ready_evaluation_never_opens_a_file(self) -> None:
        with patch.object(builtins, "open", side_effect=AssertionError("file access is forbidden")):
            result = run_scenario("ready_report")

        self.assertEqual(result.delivery, DeliveryState.EDITABLE_DRAFT)


class CliTests(unittest.TestCase):
    def test_each_cli_scenario_prints_one_stable_json_object(self) -> None:
        for name in SCENARIO_NAMES:
            with self.subTest(name=name):
                command = (sys.executable, "-m", "demo.kairosys_case.cli", "--scenario", name)
                first = subprocess.run(command, check=True, capture_output=True, text=True)
                second = subprocess.run(command, check=True, capture_output=True, text=True)

                self.assertEqual(first.stderr, "")
                self.assertEqual(first.stdout, second.stdout)
                self.assertEqual(first.stdout.count("\n"), 1)
                self.assertTrue(first.stdout.rstrip().startswith("{"))
                self.assertTrue(first.stdout.rstrip().endswith("}"))

    def test_unknown_cli_scenario_is_rejected_before_evaluation(self) -> None:
        standard_error = StringIO()
        with patch.object(cli, "run_scenario") as evaluate, redirect_stderr(standard_error):
            with self.assertRaises(SystemExit) as error:
                cli.main(("--scenario", "unapproved_case"))

        self.assertEqual(error.exception.code, 2)
        self.assertIn("invalid choice", standard_error.getvalue())
        evaluate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
