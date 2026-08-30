"""Public case-study contract for the bilingual Kairosys dossier."""

from __future__ import annotations

from pathlib import Path
import re
import tempfile
import unittest
from xml.etree import ElementTree as ET

from scripts.check_links import check


ROOT = Path(__file__).resolve().parents[1]
ENGLISH = ROOT / "README.md"
CHINESE = ROOT / "README.zh-TW.md"
FIRST_EVIDENCE = "## Evidence"
SCENARIOS = (
    "ready_report",
    "spoofed_provenance",
    "incomplete_financials",
    "contradictory_financials",
    "rendered_math_conflict",
    "shallow_but_sound",
)
_MARKDOWN_TARGET = re.compile(r"(?<!\\)!?\[[^\]]*\]\(([^)]+)\)")
_APPROVED_MATH_DELIVERY = {
    ENGLISH: "Review-capped retained draft; final use blocked pending correction",
    CHINESE: "保留且需複核的草稿；在修正完成前，最終使用仍受阻擋。",
}
_OPENING_SCOPE_SENTENCE = {
    ENGLISH: (
        "Kairosys itself is the agentic system; this curated public case makes its "
        "admission-and-audit slice runnable, while the broader agent coordination is mapped "
        "in the [architecture](docs/architecture.md)."
    ),
    CHINESE: (
        "Kairosys 本體是 agentic 系統；這份精選公開案例將其中的准入與稽核切片做成可執行示範，"
        "更完整的 agent 協調則呈現在[架構說明](docs/architecture.zh-TW.md)中。"
    ),
}


def _delivery_category(value: str, markers: dict[str, tuple[str, ...]]) -> str:
    return next(
        (
            category
            for category, required in sorted(markers.items(), key=lambda item: len(item[1]), reverse=True)
            if all(marker in value for marker in required)
        ),
        "invalid",
    )


def _scenario_delivery_cell(markdown: str, scenario: str) -> str:
    match = re.search(
        rf"^\| `{re.escape(scenario)}` \| .*? \| (.*?) \|$",
        markdown,
        flags=re.MULTILINE,
    )
    if match is None:
        raise AssertionError(f"missing scenario row: {scenario}")
    return match.group(1)


def _markdown_h2_headings(markdown: str) -> list[str]:
    """Return CommonMark H2 headings while avoiding table delimiter rows."""
    headings = []
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        atx = re.match(r"^ {0,3}##(?!#)[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$", lines[index])
        if atx:
            headings.append(atx.group(1).strip())
            index += 1
            continue
        has_setext_underline = index + 1 < len(lines) and re.match(r"^ {0,3}-{3,}[ \t]*$", lines[index + 1])
        if has_setext_underline and lines[index].strip() and "|" not in lines[index]:
            headings.append(lines[index].strip())
            index += 2
            continue
        index += 1
    return headings


class ContentContractTests(unittest.TestCase):
    def read(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def test_readme_openings_and_evidence_order_are_recruiter_first(self) -> None:
        for path, required in (
            (ENGLISH, ("I built Kairosys solo", "financial-research system")),
            (CHINESE, ("我獨立打造 Kairosys", "金融研究")),
        ):
            text = self.read(path)
            self.assertTrue(all(phrase in "\n".join(text.splitlines()[:40]) for phrase in required))
            evidence_at = text.index(FIRST_EVIDENCE)
            for caveat in ("clean" + "-room", "synthe" + "tic", "pri" + "vate", "not " + "production"):
                self.assertNotIn(caveat, text[:evidence_at].lower())

    def test_readme_openings_distinguish_the_agentic_system_from_the_runnable_slice(self) -> None:
        for path, required_sentence in _OPENING_SCOPE_SENTENCE.items():
            text = self.read(path)
            opening = "\n".join(text.splitlines()[:12])
            self.assertIn(required_sentence, opening, path.name)
            self.assertLess(text.index(required_sentence), text.index("Since" if path == ENGLISH else "自 2025"))
            self.assertLess(text.index(required_sentence), text.index(FIRST_EVIDENCE))

    def test_readme_openings_establish_the_six_research_dimensions_before_evidence(self) -> None:
        required = {
            ENGLISH: (
                "Fundamentals and financial modeling",
                "Industry, peers, and supply chain",
                "Market context and supporting technical signals",
                "Valuation and scenarios",
                "Catalysts, falsifiers, and analyst next steps",
                "Persistent research context and decision traces",
            ),
            CHINESE: (
                "基本面與財務建模",
                "產業、同業與供應鏈",
                "市場脈絡與輔助技術訊號",
                "估值與情境分析",
                "催化劑、反證與分析師下一步",
                "持續研究脈絡與決策軌跡",
            ),
        }
        for path, phrases in required.items():
            opening = "\n".join(self.read(path).splitlines()[:60])
            self.assertTrue(all(phrase in opening for phrase in phrases), path.name)

    def test_readmes_have_exact_parallel_navigation_and_commands(self) -> None:
        expected = {
            ENGLISH: {
                "web/index.html",
                "docs/architecture.md",
                "docs/evolution.md",
                "docs/report-is-the-attack-surface.md",
                "docs/two-layer-governance.md",
                "tests/test_content_contract.py",
                "README.zh-TW.md",
            },
            CHINESE: {
                "web/index.html",
                "docs/architecture.zh-TW.md",
                "docs/evolution.zh-TW.md",
                "docs/report-is-the-attack-surface.zh-TW.md",
                "docs/two-layer-governance.zh-TW.md",
                "tests/test_content_contract.py",
                "README.md",
            },
        }
        command_blocks = []
        for path, required in expected.items():
            text = self.read(path)
            targets = {match.group(1).strip() for match in _MARKDOWN_TARGET.finditer(text)}
            self.assertEqual(targets, required)
            blocks = re.findall(r"```bash\n(.*?)\n```", text, flags=re.DOTALL)
            self.assertEqual(len(blocks), 1)
            command_blocks.append(blocks[0])
        self.assertEqual(command_blocks[0], command_blocks[1])

    def test_readmes_have_equal_scenarios_and_exact_delivery_meanings(self) -> None:
        expected = {
            "ready_report": "editable",
            "spoofed_provenance": "review",
            "incomplete_financials": "context",
            "contradictory_financials": "withheld",
            "rendered_math_conflict": "review_retained",
            "shallow_but_sound": "review",
        }
        markers = {
            ENGLISH: {
                "editable": ("editable",),
                "review": ("review",),
                "context": ("context",),
                "withheld": ("withheld",),
                "review_retained": ("review", "retained"),
            },
            CHINESE: {
                "editable": ("可編輯",),
                "review": ("複核",),
                "context": ("脈絡",),
                "withheld": ("不交付",),
                "review_retained": ("複核", "保留"),
            },
        }
        for path in (ENGLISH, CHINESE):
            rows = {
                match.group(1): match.group(2).lower()
                for match in re.finditer(r"^\| `([^`]+)` \| .*? \| (.*?) \|$", self.read(path), re.MULTILINE)
            }
            self.assertEqual(tuple(rows), SCENARIOS)
            observed = {
                name: _delivery_category(rows[name], markers[path])
                for name in SCENARIOS
            }
            self.assertEqual(observed, expected)

    def test_governance_articles_explain_the_three_distinct_admission_cases(self) -> None:
        required = {
            ROOT / "docs/two-layer-governance.md": (
                "Complete + clean",
                "Complete + blocked",
                "Shallow + clean",
                "integrity gate",
                "utility score",
                "effective score",
                "0.75",
                "0.40",
                "quality_governance.py",
                "test_quality_governance.py",
            ),
            ROOT / "docs/two-layer-governance.zh-TW.md": (
                "完整且乾淨",
                "完整但被阻擋",
                "淺但乾淨",
                "完整性門檻",
                "效用分數",
                "有效分數",
                "0.75",
                "0.40",
                "quality_governance.py",
                "test_quality_governance.py",
            ),
        }
        for path, phrases in required.items():
            text = self.read(path)
            self.assertTrue(all(phrase in text for phrase in phrases), path.name)

    def test_architecture_documents_show_research_breadth_before_admission_controls(self) -> None:
        required = {
            ROOT / "docs/architecture.md": (
                "Research question",
                "Agentic coordination",
                "Fundamentals",
                "Industry and supply chain",
                "Market context",
                "Valuation and scenarios",
                "Persistent context and decision trace",
                "Integrity gate",
                "Utility score",
            ),
            ROOT / "docs/architecture.zh-TW.md": (
                "研究問題",
                "Agentic 協調",
                "基本面",
                "產業與供應鏈",
                "市場脈絡",
                "估值與情境",
                "持續研究脈絡與決策軌跡",
                "完整性門檻",
                "效用分數",
            ),
        }
        for path, phrases in required.items():
            text = self.read(path)
            self.assertTrue(all(phrase in text for phrase in phrases), path.name)

    def test_flagship_articles_explain_authority_and_retained_drafts(self) -> None:
        for path in (
            ROOT / "docs/report-is-the-attack-surface.md",
            ROOT / "docs/report-is-the-attack-surface.zh-TW.md",
        ):
            text = self.read(path).lower()
            for phrase in ("evidence", "valuation", "rendered report", "retained draft", "analyst", "audit"):
                self.assertIn(phrase, text, f"{path.name} lacks {phrase}")

    def test_flagship_articles_have_six_ordered_failure_and_boundary_sections(self) -> None:
        expected = {
            ROOT / "docs/report-is-the-attack-surface.md": [
                "1. The polished report is the dangerous surface",
                "2. Failure 1: the model promotes its own source claim",
                "3. Failure 2: complete-looking numbers do not authorize a valuation",
                "4. Failure 3: final prose introduces a new contradiction",
                "5. Why a failed audit can retain a labeled draft",
                "6. What the clean-room demo proves—and does not",
            ],
            ROOT / "docs/report-is-the-attack-surface.zh-TW.md": [
                "1. Polished report 是危險表面",
                "2. 失敗一：模型抬升自己的來源主張",
                "3. 失敗二：數字完整，不代表有 valuation authorization",
                "4. 失敗三：最終文字引入新的矛盾",
                "5. 失敗 audit 仍可能保留標示清楚的草稿",
                "6. clean-room demo 證明什麼，又沒有證明什麼",
            ],
        }
        for path, required in expected.items():
            headings = _markdown_h2_headings(self.read(path))
            self.assertEqual(headings, required, path.name)

    def test_flagship_h2_contract_rejects_setext_bypass_without_treating_table_rules_as_h2(self) -> None:
        adversarial = """## 1. Required title
| Scenario | Delivery |
| --- | --- |
Unexpected extra heading
---
"""
        self.assertEqual(
            _markdown_h2_headings(adversarial),
            ["1. Required title", "Unexpected extra heading"],
        )

    def test_rendered_math_conflict_retains_review_draft_but_blocks_final_use(self) -> None:
        rows = {}
        for path in (ENGLISH, CHINESE):
            rows[path] = _scenario_delivery_cell(self.read(path), "rendered_math_conflict")

        self.assertEqual(rows, _APPROVED_MATH_DELIVERY)

    def test_math_conflict_semantics_reject_negated_table_cell_bypass(self) -> None:
        variants = (
            "not retained; no review required; final use not blocked pending correction",
            "never retained; no review required; final use never blocked pending correction",
        )
        for variant in variants:
            adversarial = f"""| Scenario | What it pressures | Delivery meaning |
| --- | --- | --- |
| `rendered_math_conflict` | conflict | {variant} |
"""
            self.assertNotEqual(
                _scenario_delivery_cell(adversarial, "rendered_math_conflict"),
                _APPROVED_MATH_DELIVERY[ENGLISH],
            )

    def test_evolution_documents_the_lineage_and_trust_first_criterion(self) -> None:
        required = (
            "april 2025",
            "domain pivot",
            "greenfield rewrite",
            "can every important claim survive an independent audit?",
        )
        for path in (ROOT / "docs/evolution.md", ROOT / "docs/evolution.zh-TW.md"):
            text = self.read(path).lower()
            for phrase in required:
                self.assertIn(phrase, text, f"{path.name} lacks {phrase}")

    def test_public_copy_avoids_prohibited_capability_overclaims(self) -> None:
        paths = (ENGLISH, CHINESE, *sorted((ROOT / "docs").glob("*.md")))
        forbidden = (
            r"\bcustomers?\b",
            r"\balpha\b",
            r"automated\s+trading",
            r"current(?:ly)?[-\s]+live",
            r"mature\s+technical\s+analysis",
            r"report[-\s]+quality\s+acceptance",
            r"self[-\s]+evolving",
            r"fully\s+autonomous\s+research",
            r"proven\s+memory\s+uplift",
        )
        for path in paths:
            text = self.read(path)
            for pattern in forbidden:
                self.assertIsNone(re.search(pattern, text, flags=re.IGNORECASE), f"{path}: {pattern}")

    def test_diagrams_are_accessible_and_present(self) -> None:
        for name in ("architecture.svg", "evolution.svg"):
            text = self.read(ROOT / "assets" / name)
            self.assertIn('role="img"', text)
            self.assertIn("<title", text)
            self.assertIn("<desc", text)
            self.assertIn("viewBox=", text)
            self.assertIn("<tspan", text)
            root = ET.fromstring(text)
            view_box = root.attrib["viewBox"].split()
            width = float(view_box[2])
            text_nodes = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "text"]
            self.assertTrue(text_nodes)
            for node in text_nodes:
                self.assertIn("font-size", node.attrib)
                self.assertGreaterEqual(float(node.attrib["font-size"]) * 390 / width, 16, name)

    def test_architecture_diagram_shows_breadth_trace_and_two_layer_delivery(self) -> None:
        text = self.read(ROOT / "assets" / "architecture.svg")

        for phrase in (
            "RESEARCH QUESTION",
            "AGENTIC COORDINATION",
            "FUNDAMENTALS",
            "INDUSTRY + SUPPLY CHAIN",
            "MARKET CONTEXT",
            "VALUATION + SCENARIOS",
            "TYPED EVIDENCE + PROVENANCE",
            "PERSISTENT CONTEXT + DECISION TRACE",
            "LAYER 1 / INTEGRITY",
            "LAYER 2 / UTILITY",
            "DELIVERY",
        ):
            self.assertIn(phrase, text)

    def test_svg_link_checker_rejects_decoded_xlink_and_escape_variants(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "candidate"
            root.mkdir()
            outside = Path(temp_dir) / "outside.svg"
            outside.write_text("<svg/>", encoding="utf-8")
            (root / "escape.svg").symlink_to(outside)
            absolute = "/" + "Users/example/absolute.svg"
            (root / "probe.svg").write_text(
                f"""<svg xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\">
  <image href=\"{absolute}\"/>
  <image href=\"%2FUsers/example/encoded.svg\"/>
  <image href=\"../outside.svg\"/>
  <image href=\"escape.svg\"/>
  <use xlink:href=\"&#x2F;Users/example/numeric-entity.svg\"/>
</svg>""",
                encoding="utf-8",
            )
            total, findings = check(root)
        self.assertEqual(total, 5)
        self.assertEqual(findings, tuple(sorted(findings)))
        probe_findings = [finding for finding in findings if finding.path == "probe.svg"]
        self.assertEqual(
            {(finding.target, finding.reason) for finding in probe_findings},
            {
                ("/" + "Users/example/absolute.svg", "absolute_or_external_target"),
                ("%2FUsers/example/encoded.svg", "absolute_or_external_target"),
                ("/" + "Users/example/numeric-entity.svg", "absolute_or_external_target"),
                ("../outside.svg", "target_escapes_candidate"),
                ("escape.svg", "symlink_target"),
            },
        )

    def test_svg_link_checker_fails_closed_on_doctype(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "probe.svg").write_text(
                "<!DOCTYPE svg [<!ENTITY safe \"nothing\">]><svg xmlns=\"http://www.w3.org/2000/svg\"/>",
                encoding="utf-8",
            )
            total, findings = check(root)
        self.assertEqual(total, 0)
        self.assertEqual([(finding.path, finding.reason) for finding in findings], [("probe.svg", "doctype_not_allowed")])


if __name__ == "__main__":
    unittest.main()
