from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import unittest

from demo.kairosys_case.pipeline import run_scenario
from demo.kairosys_case.scenarios import SCENARIO_NAMES
from demo.kairosys_case.serialization import to_public_dict
from scripts.build_web_data import build_payload, render_javascript


ROOT = Path(__file__).resolve().parents[1]


def css_block(source: str, header: str) -> str:
    """Return a balanced CSS block body for a unique rule or at-rule header."""
    match = re.search(r"(?m)^\s*" + re.escape(header) + r"\s*\{", source)
    if match is None:
        raise AssertionError(f"missing CSS header: {header}")
    opening = match.end() - 1
    depth = 1
    for index in range(opening + 1, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1 : index]
    raise AssertionError(f"unterminated CSS block: {header}")


def css_declarations(source: str, selector: str) -> dict[str, str]:
    body = css_block(source, selector)
    declarations: dict[str, str] = {}
    for declaration in body.split(";"):
        if not declaration.strip():
            continue
        name, separator, value = declaration.partition(":")
        if not separator:
            raise AssertionError(f"malformed declaration for {selector}: {declaration!r}")
        declarations[name.strip()] = value.strip()
    return declarations


class WebDataContractTests(unittest.TestCase):
    def test_payload_contains_each_approved_scenario_with_stable_pipeline_keys(self) -> None:
        payload = build_payload()

        self.assertEqual(tuple(payload), SCENARIO_NAMES)
        for name in SCENARIO_NAMES:
            with self.subTest(name=name):
                self.assertEqual(payload[name], to_public_dict(run_scenario(name)))

    def test_javascript_is_compact_sorted_and_has_no_generated_metadata(self) -> None:
        rendered = render_javascript(build_payload())

        self.assertTrue(rendered.startswith("window.KAIROSYS_CASE_DATA="))
        self.assertTrue(rendered.endswith(";\n"))
        self.assertNotIn("timestamp", rendered.lower())
        self.assertNotIn(str(ROOT), rendered)
        decoded = json.loads(rendered.removeprefix("window.KAIROSYS_CASE_DATA=").removesuffix(";\n"))
        self.assertEqual(set(decoded), set(SCENARIO_NAMES))
        self.assertEqual(rendered, render_javascript(build_payload()))

    def test_generated_data_file_exactly_matches_current_payload(self) -> None:
        self.assertEqual(
            (ROOT / "web" / "data.js").read_text(encoding="utf-8"),
            render_javascript(build_payload()),
        )


class WebShellContractTests(unittest.TestCase):
    def test_hero_separates_product_descriptor_thesis_and_ownership_in_both_languages(self) -> None:
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")

        ordered_ids = (
            'id="hero-descriptor"',
            'id="hero-title"',
            'id="hero-thesis"',
            'id="hero-ownership"',
        )
        for identifier in ordered_ids:
            self.assertIn(identifier, html)
        positions = tuple(html.index(identifier) for identifier in ordered_ids)
        self.assertEqual(positions, tuple(sorted(positions)))
        self.assertEqual(app.count('hero: "Kairosys"'), 2)
        self.assertIn('descriptor: "AGENTIC FINANCIAL RESEARCH SYSTEM"', app)
        self.assertIn('thesis: "Every important claim should survive an audit."', app)
        self.assertIn('ownership: "Designed and built solo by Titus Lai."', app)
        self.assertIn('descriptor: "Agentic 金融研究系統"', app)
        self.assertIn('thesis: "每一項重要主張，都應經得起稽核。"', app)
        self.assertIn('ownership: "由 Titus Lai 獨立設計與打造。"', app)
        self.assertIn('setText("hero-ownership", copy.ownership)', app)
        self.assertNotIn("I built Kairosys solo.", app)
        self.assertNotIn("我獨立打造 Kairosys。", app)

    def test_system_overview_and_quality_governance_have_ordered_semantic_surfaces(self) -> None:
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")

        ordered_ids = (
            'id="system-overview"',
            'id="system-overview-title"',
            'id="capability-flow"',
            'id="quality-governance"',
            'id="quality-integrity-state"',
            'id="quality-utility-score"',
            'id="quality-effective-score"',
            'id="quality-delivery"',
            'id="report-title"',
        )
        for identifier in ordered_ids:
            self.assertIn(identifier, html)
        positions = tuple(html.index(identifier) for identifier in ordered_ids)
        self.assertEqual(positions, tuple(sorted(positions)))
        self.assertIn('<ol class="capability-flow" id="capability-flow"></ol>', html)
        self.assertIn('aria-live="polite"', html)
        self.assertEqual(app.count("capabilities: ["), 2)
        for phrase in (
            "Fundamentals & financial modeling",
            "Industry, peers & supply chain",
            "Market context & supporting technical signals",
            "Valuation & scenarios",
            "Catalysts, falsifiers & analyst next steps",
            "Persistent context & decision traces",
            "基本面與財務建模",
            "產業、同業與供應鏈",
            "市場脈絡與輔助技術訊號",
            "估值與情境分析",
            "催化劑、反證與分析師下一步",
            "持續研究脈絡與決策軌跡",
        ):
            self.assertIn(phrase, app)

    def test_tablet_contract_stacks_evidence_without_erasing_desktop_or_compact_modes(self) -> None:
        css = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")

        self.assertEqual(
            css_declarations(css, ".evidence-rail")["grid-template-columns"],
            "repeat(5, minmax(0, 1fr))",
        )
        tablet = css_block(css, "@media (max-width: 900px)")
        self.assertEqual(
            css_declarations(tablet, ".evidence-rail")["grid-template-columns"],
            "1fr",
        )
        tablet_cards = css_declarations(tablet, ".rail-card, .rail-card:last-child")
        self.assertEqual(tablet_cards["min-height"], "0")
        self.assertEqual(tablet_cards["border-right"], "0")
        self.assertIn("solid var(--quiet-line)", tablet_cards["border-bottom"])
        compact = css_block(css, "@media (max-width: 390px)")
        self.assertEqual(css_declarations(compact, ".evidence-rail")["display"], "block")
        self.assertEqual(
            css_declarations(compact, ".rail-card")["grid-template-columns"],
            "30px 1fr",
        )

    def test_language_and_scenario_controls_have_minimum_pointer_targets(self) -> None:
        css = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")

        shared_controls = css_declarations(css, ".language-button, .scenario-button")
        language = css_declarations(css, ".language-button")
        self.assertGreaterEqual(float(shared_controls["min-height"].removesuffix("px")), 44)
        self.assertGreaterEqual(float(language["min-width"].removesuffix("px")), 44)

    def test_node_dom_stub_executes_evidence_rail_for_every_scenario_and_locale(self) -> None:
        data_source = (ROOT / "web" / "data.js").read_text(encoding="utf-8")
        app_source = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        runtime = f"""
const vm = require("node:vm");
class ClassList {{
  constructor() {{ this.values = new Set(); }}
  add(value) {{ this.values.add(value); }}
  remove(value) {{ this.values.delete(value); }}
  toggle(value, force) {{
    if (force) this.add(value); else this.remove(value);
    return Boolean(force);
  }}
}}
class Element {{
  constructor() {{
    this.children = [];
    this.className = "";
    this.dataset = {{}};
    this.attributes = {{}};
    this.listeners = {{}};
    this.classList = new ClassList();
    this.textContent = "";
  }}
  append(...nodes) {{ this.children.push(...nodes); }}
  replaceChildren(...nodes) {{ this.children = nodes; }}
  setAttribute(name, value) {{ this.attributes[name] = String(value); }}
  addEventListener(name, listener) {{ (this.listeners[name] ||= []).push(listener); }}
  click() {{ (this.listeners.click || []).forEach((listener) => listener()); }}
}}
const ids = Object.fromEntries([
  "folio-mark", "language-controls", "scenario-tabs", "hero-eyebrow", "hero-title",
  "hero-value", "hero-descriptor", "hero-thesis", "hero-ownership",
  "case-selector-title", "case-selector-note", "evidence-title",
  "evidence-note", "report-kicker", "report-title", "finding-title",
  "technical-label", "technical-copy", "boundary-label", "boundary-copy",
  "system-overview-title", "system-overview-note", "capability-flow",
  "quality-title", "quality-note", "quality-governance", "quality-integrity-label",
  "quality-integrity-state", "quality-integrity-reasons", "quality-utility-label",
  "quality-raw-label", "quality-utility-score", "quality-effective-label", "quality-effective-score",
  "quality-completion", "quality-delivery-label", "quality-delivery",
  "evidence-rail", "report-sheet", "finding-list"
].map((id) => [id, new Element()]));
const languageButtons = ["en", "zh-TW"].map((locale) => {{
  const button = new Element();
  button.dataset.locale = locale;
  return button;
}});
const document = {{
  body: new Element(),
  documentElement: new Element(),
  title: "",
  createElement: () => new Element(),
  getElementById: (id) => ids[id],
  querySelectorAll: (selector) => selector === ".language-button" ? languageButtons : []
}};
const window = {{ setTimeout: (callback) => callback() }};
const context = {{ window, document, console }};
vm.runInNewContext({json.dumps(data_source)}, context);
vm.runInNewContext({json.dumps(app_source)}, context);
const payload = window.KAIROSYS_CASE_DATA;
const scenarioTabs = ids["scenario-tabs"];
const toolData = () => ids["evidence-rail"].children[0].children[3].textContent;
const modelCard = () => ids["evidence-rail"].children[1];
const modelData = () => modelCard().children[3].textContent;
const qualitySnapshot = () => ({{
  gate: ids["quality-integrity-state"].textContent,
  utility: ids["quality-utility-score"].textContent,
  effective: ids["quality-effective-score"].textContent,
  delivery: ids["quality-delivery"].textContent
}});
const clickScenario = (name) => {{
  const button = scenarioTabs.children.find((candidate) => candidate.dataset.scenario === name);
  if (!button) throw new Error(`missing scenario button: ${{name}}`);
  button.click();
}};
const expectedToolData = (entries, locale) => entries.length === 0
  ? (locale === "en" ? "No trusted tool evidence was returned." : "沒有回傳可信的工具證據。")
  : `${{locale === "en" ? "Trusted tool records:" : "可信工具紀錄："}} ${{entries.length}}\\n${{entries.map((entry) => `${{entry.source_tool}} · ${{entry.metric_id}}=${{entry.value}} ${{entry.unit}} · ${{entry.period}}`).join("\\n")}}`;
const observed = {{}};
for (const [name, result] of Object.entries(payload)) {{
  clickScenario(name);
  const discarded = result.provenance.discarded_model_claims;
  if (toolData() !== expectedToolData(result.provenance.entries, "en")) throw new Error(`tool facts mismatch: ${{name}}`);
  if (modelCard().className.includes("discarded-claim") !== (discarded > 0)) throw new Error(`model class mismatch: ${{name}}`);
  const expectedModel = discarded > 0
    ? `Model-originated source claims discarded: ${{discarded}}`
    : "No model-originated source claim was supplied.";
  if (modelData() !== expectedModel) throw new Error(`model message mismatch: ${{name}}`);
  const quality = qualitySnapshot();
  const expectedQuality = {{
    gate: result.quality.integrity_gate.toUpperCase(),
    utility: result.quality.utility_score,
    effective: result.quality.effective_score,
    delivery: result.delivery
  }};
  if (JSON.stringify(quality) !== JSON.stringify(expectedQuality)) throw new Error(`quality mismatch: ${{name}}`);
  observed[name] = {{ tool: toolData(), model: modelData(), struck: modelCard().className.includes("discarded-claim"), quality }};
}}
languageButtons.find((button) => button.dataset.locale === "zh-TW").click();
clickScenario("ready_report");
if (modelData() !== "未提供模型來源主張。" || modelCard().className.includes("discarded-claim")) throw new Error("zh zero-state mismatch");
clickScenario("spoofed_provenance");
if (modelData() !== "已捨棄的模型來源主張： 1" || !modelCard().className.includes("discarded-claim")) throw new Error("zh positive-state mismatch");
clickScenario("shallow_but_sound");
if (JSON.stringify(qualitySnapshot()) !== JSON.stringify({{ gate: "PASS", utility: "0.35", effective: "0.35", delivery: "review_required" }})) throw new Error("zh shallow quality mismatch");
process.stdout.write(JSON.stringify(observed));
"""

        result = subprocess.run(
            ("node", "-e", runtime),
            check=True,
            capture_output=True,
            text=True,
        )
        observed = json.loads(result.stdout)

        self.assertEqual(set(observed), set(SCENARIO_NAMES))
        self.assertTrue(observed["spoofed_provenance"]["struck"])
        self.assertFalse(observed["ready_report"]["struck"])
        self.assertEqual(
            observed["rendered_math_conflict"]["quality"],
            {"gate": "FAIL", "utility": "1.00", "effective": "0.40", "delivery": "review_required"},
        )
        self.assertEqual(
            observed["shallow_but_sound"]["quality"],
            {"gate": "PASS", "utility": "0.35", "effective": "0.35", "delivery": "review_required"},
        )

    def test_evidence_rail_uses_raw_payload_facts_and_real_discard_counts(self) -> None:
        payload = build_payload()
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertEqual(
            {name: payload[name]["provenance"]["discarded_model_claims"] for name in SCENARIO_NAMES},
            {
                "ready_report": 0,
                "spoofed_provenance": 1,
                "incomplete_financials": 0,
                "contradictory_financials": 0,
                "rendered_math_conflict": 0,
                "shallow_but_sound": 0,
            },
        )
        self.assertIn("result.provenance.entries", app)
        self.assertIn("entry.source_tool", app)
        self.assertIn("entry.metric_id", app)
        self.assertIn("entry.value", app)
        self.assertIn("entry.period", app)
        self.assertIn("entry.unit", app)
        self.assertIn("entries.length", app)
        self.assertNotIn('railCard("01", copy.steps[0], copy.rail[0], result.scenario', app)

    def test_quality_strip_reads_supplied_result_without_recomputing_policy(self) -> None:
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("function renderQuality(copy, result)", app)
        self.assertIn("const quality = result.quality", app)
        self.assertIn("quality.integrity_gate", app)
        self.assertIn("quality.gate_reasons", app)
        self.assertIn("quality.utility_score", app)
        self.assertIn("quality.effective_score", app)
        self.assertIn("quality.completed_dimensions", app)
        self.assertIn("quality.missing_dimensions", app)
        self.assertIn("result.delivery", app)

    def test_model_claim_strike_is_conditional_on_the_raw_discard_count(self) -> None:
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("result.provenance.discarded_model_claims", app)
        self.assertIn('discardedCount > 0 ? "discarded-claim" : ""', app)
        self.assertIn("copy.modelDiscarded", app)
        self.assertIn("copy.modelEmpty", app)
        self.assertNotIn("copy.modelAttempt", app)

    def test_semantic_shell_and_rendering_boundary_are_present(self) -> None:
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        css = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")

        self.assertEqual(html.count("<main"), 1)
        self.assertEqual(html.count("<h1"), 1)
        self.assertIn('<h1 id="hero-title"></h1>', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn('src="data.js"', html)
        self.assertIn('src="app.js"', html)
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)
        self.assertIn("const COPY =", app)
        self.assertIn('hero: "Kairosys"', app)
        self.assertIn('ownership: "Designed and built solo by Titus Lai."', app)
        self.assertIn("zh-TW", app)
        self.assertIn("evidence-rail", html)
        self.assertIn("system-overview", html)
        self.assertIn("quality-governance", html)
        self.assertIn("discarded-claim", app)
        self.assertIn("text-decoration", css)
        self.assertIn("@media (max-width: 390px)", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn(":focus-visible", css)

    def test_browser_renderer_does_not_recompute_pipeline_policy(self) -> None:
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        forbidden = ("Math.", "authorized_methods", "confidence_cap", "allows_target", "reduce(", "filter(", "fetch(", "XMLHttpRequest", "0.75", "0.40")

        self.assertFalse(set(forbidden) & {token for token in forbidden if token in app})


if __name__ == "__main__":
    unittest.main()
