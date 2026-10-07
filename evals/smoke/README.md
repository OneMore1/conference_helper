# Synthetic task checks

Release 0.1.0 · 2026-10-07.

Three independent subagents invoked the current Skill with the minimal inputs listed in [scenarios.json](scenarios.json). They were not given expected answers. The coordinating agent reviewed the actual outputs for task scope and evidence handling; this was not blinded scoring and had no baseline group.

| Case | Observed behavior |
|---|---|
| [Direction](direction-output.md) | Declined to turn curated pattern frequencies into personal acceptance probabilities, then proposed a concrete conditional research question and minimal validation. |
| [Ablations](ablation-output.md) | Applied the structural-prior tip to a capacity-matched alternative and a mismatched-prior control, retaining the two-condition budget and failure criteria. |
| [Writing](writing-output.md) | Used the evidence to define an article argument, preserved the held-out negative result, and drafted text without inventing uncertainty or adding experiments. |

Inputs are synthetic: [model](inputs/model.md), [results](inputs/results.csv), [context](inputs/context.md). Result differences independently checked: 0.03, 0.01 and −0.01.

Output prose is preserved. Machine-specific source links are normalized to repository-relative links. These few calls do not establish scientific quality, stability across models, or improved acceptance outcomes.
