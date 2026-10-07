# Evaluation scope

Runtime tests check routing, evidence references, version conflicts, path boundaries and safe installation. Run the complete repository suite with `python tools/run_checks.py`; current results are in `docs/TEST_REPORT.md` in the source package.

Behavioral checks should use realistic requests and only the raw materials needed for the task. Preserve actual inputs and outputs. Do not provide expected answers to the executing agent or describe an authored teaching example as an agent run.

Useful cases include a broad direction, a fixed model needing controls, mixed positive/negative results, a local writing request and changed source evidence. Assess task completion, factual preservation, meaningful controls, source support and user scope. Reviewer-facing tips should improve concrete decisions without inventing acceptance probabilities.

Small synthetic checks do not establish improvements in real research outcomes. Any comparison between configurations should use matched tasks, isolated contexts, source-blinded review and retained failures; a same-context second pass is not an independent review.
