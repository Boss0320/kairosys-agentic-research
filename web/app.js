"use strict";

const COPY = {
  en: {
    documentTitle: "Kairosys research dossier",
    languageLabel: "Language",
    languageNames: { en: "EN", "zh-TW": "中文" },
    scenarioTabsLabel: "Synthetic case files",
    mark: "KAIROSYS / RESEARCH DOSSIER",
    descriptor: "AGENTIC FINANCIAL RESEARCH SYSTEM",
    hero: "Kairosys",
    thesis: "Every important claim should survive an audit.",
    ownership: "Designed and built solo by Titus Lai.",
    overviewTitle: "One system, several research lenses",
    overviewNote: "Coordinates evidence and specialist analysis into a traceable draft for human judgment.",
    capabilities: [
      "Fundamentals & financial modeling",
      "Industry, peers & supply chain",
      "Market context & supporting technical signals",
      "Valuation & scenarios",
      "Catalysts, falsifiers & analyst next steps",
      "Persistent context & decision traces"
    ],
    selectorTitle: "Select a synthetic case file",
    selectorNote: "Six fixed outcomes, rendered offline.",
    evidenceTitle: "Chain of custody",
    evidenceNote: "A claim is an attempt. The audit decides what can travel.",
    qualityTitle: "Two-layer admission",
    qualityNote: "Correctness is mandatory. Usefulness is scored separately.",
    integrityLabel: "LAYER 1 / INTEGRITY GATE",
    utilityLabel: "LAYER 2 / RESEARCH UTILITY",
    rawScoreLabel: "raw coverage",
    effectiveScoreLabel: "effective score",
    deliveryLabel: "DELIVERY",
    noGateReasons: "No blocking reason.",
    gateReasons: "Blocking reasons:",
    completedLabel: "Completed:",
    missingLabel: "Missing:",
    reportKicker: "RENDERED ARTIFACT / FINAL CHECK",
    reportTitle: "Annotated report",
    findingTitle: "Finding ledger",
    technicalLabel: "TECHNICAL EVIDENCE",
    technicalCopy: "Deterministic scenario outputs · provenance reconstruction · valuation authorization · rendered-report audit",
    boundaryLabel: "SYNTHETIC BOUNDARY",
    boundaryCopy: "This browser demonstration contains fixed clean-room data only. It makes no live requests.",
    steps: ["Tool output", "Attempted model claim", "Trusted evidence", "Valuation authorization", "Rendered-report verdict"],
    rail: ["Recorded upstream output.", "Untrusted until the evidence path supports it.", "Rebuilt from deterministic tool records.", "The supplied result records the allowed report context.", "The supplied result is the final delivery verdict."],
    toolCount: "Trusted tool records:",
    toolEmpty: "No trusted tool evidence was returned.",
    modelDiscarded: "Model-originated source claims discarded:",
    modelEmpty: "No model-originated source claim was supplied.",
    scenario: {
      ready_report: "Ready report",
      spoofed_provenance: "Spoofed provenance",
      incomplete_financials: "Incomplete financials",
      contradictory_financials: "Contradictory financials",
      rendered_math_conflict: "Rendered math conflict",
      shallow_but_sound: "Sound but shallow"
    },
    labels: { scenario: "case", delivery: "delivery", evidence: "evidence", state: "state", reason: "reason", findings: "findings", reportUnavailable: "No report may be rendered for this case." }
  },
  "zh-TW": {
    documentTitle: "Kairosys 研究卷宗",
    languageLabel: "語言",
    languageNames: { en: "EN", "zh-TW": "中文" },
    scenarioTabsLabel: "合成案例檔案",
    mark: "KAIROSYS / 研究卷宗",
    descriptor: "Agentic 金融研究系統",
    hero: "Kairosys",
    thesis: "每一項重要主張，都應經得起稽核。",
    ownership: "由 Titus Lai 獨立設計與打造。",
    overviewTitle: "一套系統，多個研究視角",
    overviewNote: "協調證據與專業分析，產出可追溯、由人負責判斷的研究草稿。",
    capabilities: [
      "基本面與財務建模",
      "產業、同業與供應鏈",
      "市場脈絡與輔助技術訊號",
      "估值與情境分析",
      "催化劑、反證與分析師下一步",
      "持續研究脈絡與決策軌跡"
    ],
    selectorTitle: "選擇合成案例檔案",
    selectorNote: "六種固定結果，離線呈現。",
    evidenceTitle: "證據保管鏈",
    evidenceNote: "主張只是嘗試；稽核決定它能否交付。",
    qualityTitle: "兩層准入治理",
    qualityNote: "正確性是硬門檻；研究效用另外評分。",
    integrityLabel: "第一層 / 完整性門檻",
    utilityLabel: "第二層 / 研究效用",
    rawScoreLabel: "原始覆蓋分數",
    effectiveScoreLabel: "有效分數",
    deliveryLabel: "交付狀態",
    noGateReasons: "沒有阻擋原因。",
    gateReasons: "阻擋原因：",
    completedLabel: "已完成：",
    missingLabel: "缺少：",
    reportKicker: "渲染產物 / 最終檢查",
    reportTitle: "標註報告",
    findingTitle: "發現紀錄",
    technicalLabel: "技術證據",
    technicalCopy: "確定性情境輸出 · 來源重建 · 估值授權 · 渲染報告稽核",
    boundaryLabel: "合成邊界",
    boundaryCopy: "此瀏覽器展示僅含固定的 clean-room 資料，不會發出即時請求。",
    steps: ["工具輸出", "模型嘗試主張", "可信證據", "估值授權", "渲染報告判定"],
    rail: ["記錄的上游輸出。", "在證據鏈支持前不可信。", "由確定性的工具紀錄重建。", "提供的結果記錄可使用的報告情境。", "提供的結果即為最終交付判定。"],
    toolCount: "可信工具紀錄：",
    toolEmpty: "沒有回傳可信的工具證據。",
    modelDiscarded: "已捨棄的模型來源主張：",
    modelEmpty: "未提供模型來源主張。",
    scenario: {
      ready_report: "可編輯報告",
      spoofed_provenance: "偽造來源",
      incomplete_financials: "財務資料不完整",
      contradictory_financials: "財務資料矛盾",
      rendered_math_conflict: "渲染算式衝突",
      shallow_but_sound: "正確但不夠深入"
    },
    labels: { scenario: "案例", delivery: "交付", evidence: "證據", state: "狀態", reason: "原因", findings: "發現", reportUnavailable: "此案例不得渲染報告。" }
  }
};

const DATA = window.KAIROSYS_CASE_DATA;
let locale = "en";
let selectedScenario = "ready_report";

function element(id) { return document.getElementById(id); }

function setText(id, value) { element(id).textContent = value; }

function textBlock(tag, className, value) {
  const node = document.createElement(tag);
  node.className = className;
  node.textContent = value;
  return node;
}

function renderTabs(copy) {
  const tabs = element("scenario-tabs");
  tabs.replaceChildren();
  Object.keys(DATA).forEach((name) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "scenario-button";
    button.role = "tab";
    button.dataset.scenario = name;
    button.setAttribute("aria-selected", String(name === selectedScenario));
    button.textContent = copy.scenario[name];
    button.addEventListener("click", () => selectScenario(name));
    tabs.append(button);
  });
}

function renderCapabilities(copy) {
  const flow = element("capability-flow");
  flow.replaceChildren();
  copy.capabilities.forEach((capability, index) => {
    const item = document.createElement("li");
    item.append(textBlock("span", "capability-index", String(index + 1).padStart(2, "0")));
    item.append(textBlock("span", "capability-copy", capability));
    flow.append(item);
  });
}

function railCard(step, title, copy, data, className) {
  const card = document.createElement("article");
  card.className = `rail-card ${className}`;
  card.append(textBlock("p", "rail-step", step));
  card.append(textBlock("h3", "rail-title", title));
  card.append(textBlock("p", "rail-copy", copy));
  card.append(textBlock("p", "rail-data", data));
  return card;
}

function formatToolEvidence(copy, entries) {
  if (entries.length === 0) {
    return copy.toolEmpty;
  }
  const facts = entries.map((entry) => (
    `${entry.source_tool} · ${entry.metric_id}=${entry.value} ${entry.unit} · ${entry.period}`
  ));
  return `${copy.toolCount} ${entries.length}\n${facts.join("\n")}`;
}

function renderEvidence(copy, result) {
  const rail = element("evidence-rail");
  rail.replaceChildren();
  const entries = result.provenance.entries;
  const discardedCount = result.provenance.discarded_model_claims;
  const modelMessage = discardedCount > 0
    ? `${copy.modelDiscarded} ${discardedCount}`
    : copy.modelEmpty;
  const cards = [
    railCard("01", copy.steps[0], copy.rail[0], formatToolEvidence(copy, entries), ""),
    railCard("02", copy.steps[1], copy.rail[1], modelMessage, discardedCount > 0 ? "discarded-claim" : ""),
    railCard("03", copy.steps[2], copy.rail[2], JSON.stringify(result.provenance), "trusted-evidence"),
    railCard("04", copy.steps[3], copy.rail[3], JSON.stringify(result.valuation), "review-authority"),
    railCard("05", copy.steps[4], copy.rail[4], result.delivery, "verdict-card")
  ];
  const stamp = textBlock("span", "verdict-stamp", result.delivery);
  cards[4].append(stamp);
  rail.append(...cards);
}

function renderQuality(copy, result) {
  const quality = result.quality;
  const governance = element("quality-governance");
  governance.className = `quality-governance gate-${quality.integrity_gate}`;
  setText("quality-integrity-state", quality.integrity_gate.toUpperCase());
  setText(
    "quality-integrity-reasons",
    quality.gate_reasons.length
      ? `${copy.gateReasons} ${quality.gate_reasons.join(", ")}`
      : copy.noGateReasons
  );
  setText("quality-utility-score", quality.utility_score);
  setText("quality-effective-score", quality.effective_score);
  setText(
    "quality-completion",
    `${copy.completedLabel} ${quality.completed_dimensions.join(", ")}\n${copy.missingLabel} ${quality.missing_dimensions.join(", ") || "—"}`
  );
  setText("quality-delivery", result.delivery);
}

function renderReport(copy, result) {
  const sheet = element("report-sheet");
  sheet.replaceChildren();
  sheet.append(textBlock("p", result.rendered_report ? "report-content" : "report-empty", result.rendered_report || copy.labels.reportUnavailable));
  const ledger = element("finding-list");
  ledger.replaceChildren();
  const rows = [
    [copy.labels.scenario, result.scenario],
    [copy.labels.delivery, result.delivery],
    [copy.labels.state, result.valuation.state],
    [copy.labels.reason, result.valuation.reason],
    [copy.labels.findings, JSON.stringify(result.audit.findings)]
  ];
  rows.forEach(([label, value]) => {
    ledger.append(textBlock("dt", "", label));
    ledger.append(textBlock("dd", "", value));
  });
}

function render() {
  const copy = COPY[locale];
  const result = DATA[selectedScenario];
  document.documentElement.lang = locale;
  document.title = copy.documentTitle;
  element("language-controls").setAttribute("aria-label", copy.languageLabel);
  element("scenario-tabs").setAttribute("aria-label", copy.scenarioTabsLabel);
  setText("folio-mark", copy.mark);
  setText("hero-descriptor", copy.descriptor);
  setText("hero-title", copy.hero);
  setText("hero-thesis", copy.thesis);
  setText("hero-ownership", copy.ownership);
  setText("system-overview-title", copy.overviewTitle);
  setText("system-overview-note", copy.overviewNote);
  setText("case-selector-title", copy.selectorTitle);
  setText("case-selector-note", copy.selectorNote);
  setText("evidence-title", copy.evidenceTitle);
  setText("evidence-note", copy.evidenceNote);
  setText("quality-title", copy.qualityTitle);
  setText("quality-note", copy.qualityNote);
  setText("quality-integrity-label", copy.integrityLabel);
  setText("quality-utility-label", copy.utilityLabel);
  setText("quality-raw-label", copy.rawScoreLabel);
  setText("quality-effective-label", copy.effectiveScoreLabel);
  setText("quality-delivery-label", copy.deliveryLabel);
  setText("report-kicker", copy.reportKicker);
  setText("report-title", copy.reportTitle);
  setText("finding-title", copy.findingTitle);
  setText("technical-label", copy.technicalLabel);
  setText("technical-copy", copy.technicalCopy);
  setText("boundary-label", copy.boundaryLabel);
  setText("boundary-copy", copy.boundaryCopy);
  renderCapabilities(copy);
  renderTabs(copy);
  renderEvidence(copy, result);
  renderQuality(copy, result);
  renderReport(copy, result);
  document.querySelectorAll(".language-button").forEach((button) => {
    button.textContent = copy.languageNames[button.dataset.locale];
    button.classList.toggle("is-current", button.dataset.locale === locale);
    button.setAttribute("aria-pressed", String(button.dataset.locale === locale));
  });
}

function selectScenario(name) {
  selectedScenario = name;
  document.body.classList.add("is-settling");
  render();
  window.setTimeout(() => document.body.classList.remove("is-settling"), 180);
}

document.querySelectorAll(".language-button").forEach((button) => {
  button.addEventListener("click", () => {
    locale = button.dataset.locale;
    render();
  });
});

render();
