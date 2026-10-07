# Conference Helper

**Turn a research direction into a question, a model design into evidence, and existing results into an article.**

Evidence-grounded assistance for ideation, experiments, writing and conference preparation. One Skill follows the task you need now.

**v0.1.0 · First open-source release** · **Python 3.10+** · **MIT / CC BY 4.0 for paper-derived summaries** · [中文](README.md)

## Three ways to start

| Your request | Deliverable |
|---|---|
| I want to work on an fMRI foundation model | Concrete questions, tradeoffs, a recommendation and minimal validation |
| My model is designed; which ablations should I add? | Claims, evidence gaps, matched controls, interpretations and priorities |
| How can we organize our results into an article? | Main argument, claim-to-figure map, section plan and evidence-grounded sample text |

[Complete teaching cases (Chinese)](skills/conference-helper/examples/research-workflow-cases.md). All model components and numbers in these cases are synthetic teaching inputs, not real research findings.

A direction in one sentence is enough to begin. Provide designs or results when available; no JSON form or manual stage choice is required.

## Get started

From an extracted or cloned source directory, with Python 3.10+:

~~~bash
python tools/install_skill.py --project /path/to/your-paper-project
~~~

On Windows, keep the source directory short. Add --backup-existing when upgrading. [Installation guide](docs/USER_GUIDE.zh-CN.md)

Open the target project in Codex, then choose one of these requests.

### Only a rough direction

~~~text
Use $conference-helper.
I want to work on an fMRI foundation model, but the question is not fixed yet.
Compare possible angles, recommend one question, and explain the rationale, unknowns and minimal validation.
Keep the first response concise. Do not launch experiments.
~~~

### A model needs ablations

~~~text
Use $conference-helper.
My model design is complete. Which ablations should I add?
Design: [description or path]. Existing experiments: [if available].
Map claims to evidence gaps and controls. Explain what changes, what stays matched,
how different outcomes affect the claim, and which experiment should come first.
Do not launch experiments.
~~~

### Results need an article

~~~text
Use $conference-helper.
We have methods, results tables and figures: [materials].
Recommend an article argument, map claims to figures, arrange the sections,
and draft a sample paragraph using the available results.
Preserve negative results and put evidence gaps in a separate memo.
~~~

## How the workflow reasons

Specific problem → design rationale and assumptions → evidence and competing explanations → the smallest next action or the requested writing.

Enter at any point. Existing designs stay in scope; supported parts of an article can be written while other evidence is incomplete. Literature checks serve the current research task. Delivery defaults to the conversation; request a saved document or visualization when useful.

[Research cases](skills/conference-helper/examples/research-workflow-cases.md) · [Ablation template](skills/conference-helper/assets/ablation-plan.md) · [Runnable results demo](examples/tiny-shapes/README.md) · [Evidence to writing](skills/conference-helper/examples/evidence-to-writing.md)

## Research tips from conference outcomes

[ResearchStudio-Idea](https://arxiv.org/abs/2607.04439v1) analyzes 1,947 ML papers, including Oral, high-citation and rejected samples. Conference Helper maps its observations and design advice into practical decisions:

- State what the contribution constructs, measures or proves.
- Give each component a reason to exist; test interaction when claiming it.
- Make a structural prior's effect identifiable with matched alternatives.
- Compare substantive differences with the closest prior work.
- Check that the metric measures the claimed ability.
- State a falsification outcome and stopping condition before evaluation.
- Keep conclusions within the evidence, including negative results.

The [tip cards](skills/conference-helper/references/review-tips.md) separate source observations, source design recommendations and our workflow extensions. They guide concrete choices in ideation, ablations and writing.

These are not acceptance predictions. The source's curated Oral/Reject composition is not a general submission acceptance rate.

## Sources and attribution

Research patterns and empirical inspiration come from [ResearchStudio-Idea](https://arxiv.org/abs/2607.04439v1). Problem-led reasoning through mechanisms, controls and limits also draws on [Paper X-Ray](https://github.com/Wang-auspicious/paper-xray).

Original rules, code and examples are MIT-licensed. Upstream MIT notices and CC BY 4.0 attribution for paper-derived summaries are retained. See [third-party notices](skills/conference-helper/THIRD_PARTY_NOTICES.md) and [license scope](skills/conference-helper/LICENSE-SCOPE.md). This independent project does not inherit upstream evaluation results or endorsements.

## Validation and documentation

[Validation](docs/TEST_REPORT.md) · [CI](https://github.com/OneMore1/conference_helper/actions) · [User guide](docs/USER_GUIDE.zh-CN.md) · [Advanced commands](docs/QUICKSTART.zh-CN.md) · [Maintenance](docs/PUBLISHING.zh-CN.md)

Software and synthetic checks do not establish improvements in real research outcomes or acceptance rates. Scientific judgments and final manuscripts need evidence review; venue rules must be checked for the relevant year.

[MIT License](LICENSE) · [BibTeX](CITATION.bib) · [Skill entry](skills/conference-helper/SKILL.md)
