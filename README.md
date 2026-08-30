# Kairosys — Agentic Financial Research System

> I built Kairosys solo—an agentic financial-research system that coordinates evidence and specialist analysis into traceable drafts for human analysts.

Kairosys itself is the agentic system; this curated public case makes its admission-and-audit slice runnable, while the broader agent coordination is mapped in the [architecture](docs/architecture.md).

Since April 2025, I have rebuilt its architecture around one increasingly demanding goal: **can every important claim survive an audit?**

**15 seconds.** Kairosys is a research operating system, not a single report generator. It decomposes a research question across several analytical lenses, preserves the evidence and decisions behind the work, and admits only an appropriately labeled draft to a human analyst.

**What it coordinates:**

- **Fundamentals and financial modeling** — company performance, accounting meaning, and forecast structure.
- **Industry, peers, and supply chain** — competitive position and the operating context around the issuer.
- **Market context and supporting technical signals** — market behavior used as supporting evidence, not as a substitute for a thesis.
- **Valuation and scenarios** — methods and assumptions selected only when the available financial state permits them.
- **Catalysts, falsifiers, and analyst next steps** — what could change the thesis, disprove it, or require follow-up.
- **Persistent research context and decision traces** — prior evidence and reasoning remain inspectable across the research process.

**60 seconds.** Its differentiator is a two-layer admission model. An integrity gate first asks whether the draft is allowed to travel at all. A separate utility score asks whether the research is broad and useful enough. A polished, wide report cannot average away a fatal evidence or arithmetic error; a correct but shallow report still cannot present itself as analyst-ready.

## Evidence

### Six fixed scenarios

| Scenario | What it pressures | Delivery meaning |
| --- | --- | --- |
| `ready_report` | Coherent evidence, state, and report math | Editable analyst draft |
| `spoofed_provenance` | A model tries to promote its own source claim | Review-capped draft |
| `incomplete_financials` | A missing quarter blocks a target | Context-only draft |
| `contradictory_financials` | Financial facts conflict | Withheld |
| `rendered_math_conflict` | Final prose contradicts its displayed math | Review-capped retained draft; final use blocked pending correction |
| `shallow_but_sound` | Supported facts, but only two research dimensions are complete | Review-required draft for insufficient utility |

### Inspect the chain of custody

- [Open the offline browser dossier](web/index.html) for all six outcomes, their evidence rail, and the two-layer admission strip.
- [Read the public architecture](docs/architecture.md) and [the engineering evolution](docs/evolution.md).
- [Read the flagship case: the report is the attack surface](docs/report-is-the-attack-surface.md).
- [Inspect the two-layer governance mechanism](docs/two-layer-governance.md).
- [Inspect the content contract](tests/test_content_contract.py) and [switch to Traditional Chinese](README.zh-TW.md).

### Run the demonstration

```bash
python3 -m demo.kairosys_case.cli --scenario ready_report
python3 -m unittest
python3 scripts/check_links.py .
CANDIDATE="$(mktemp -d)/public-candidate"
python3 scripts/assemble_public.py --source . --destination "$CANDIDATE" --manifest PUBLIC-MANIFEST.txt
python3 scripts/check_public_boundary.py "$CANDIDATE"
```

The last two commands rebuild the public candidate from `PUBLIC-MANIFEST.txt` into a fresh directory and run the default-deny boundary scanner against that copy. The scanner intentionally flags Git metadata and runtime caches, so it passes on the assembled candidate rather than on a working clone.

## 5 minutes: the design judgment

The question is not whether a draft looks polished. It is whether source authority, financial meaning, research completeness, and final rendered wording remain consistent after the model has done its work. The architecture note maps the broader research system; the two engineering cases make its admission controls inspectable.

## 30 minutes: lineage and boundaries

Kairosys evolved through a persistent-assistant beginning, a finance-domain pivot, an executable layered runtime, a greenfield rewrite, and a trust-first research criterion. The evolution document records that progression without pretending it was one uninterrupted runtime.

This is a clean-room, synthetic vertical slice: it demonstrates the public behavior contract rather than a full system. It contains no private data and is not production software; a human analyst remains responsible for research judgment and delivery.
