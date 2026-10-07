#!/usr/bin/env python3
"""Copy the synthetic TinyShapes case outside this repository and recompute its table."""
from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / 'examples/tiny-shapes'
CONDITIONS = ('clean', 'noise', 'shift')
MODELS = ('Baseline', 'Augmented')
COLUMNS = ('synthetic', 'split_id', 'condition', 'model', 'seed', 'accuracy_pct')


def summarize_csv(path: Path) -> list[dict]:
    """Validate this teaching fixture and summarize paired entries; no inference tests."""
    groups: dict[tuple[str, str], dict[int, float]] = {}
    splits: set[str] = set()
    with path.open(encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(COLUMNS):
            raise ValueError('Unexpected columns in the synthetic results file.')
        for line, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f'Row {line}: incomplete or extra columns.')
            if row['synthetic'] != 'true':
                raise ValueError(f'Row {line}: this demo accepts only synthetic=true.')
            condition, model = row['condition'], row['model']
            if condition not in CONDITIONS or model not in MODELS:
                raise ValueError(f'Row {line}: unknown demo condition or model.')
            seed = int(row['seed'])
            accuracy = float(row['accuracy_pct'])
            if seed not in {1, 2, 3} or not math.isfinite(accuracy) or not 0 <= accuracy <= 100:
                raise ValueError(f'Row {line}: invalid seed or accuracy.')
            if not row['split_id'].strip():
                raise ValueError(f'Row {line}: split_id is required.')
            splits.add(row['split_id'])
            group = groups.setdefault((condition, model), {})
            if seed in group:
                raise ValueError(f'Row {line}: duplicate condition/model/seed.')
            group[seed] = accuracy
    if len(splits) != 1:
        raise ValueError('The demo requires one shared split_id.')
    summary = []
    for condition in CONDITIONS:
        baseline = groups.get((condition, 'Baseline'), {})
        augmented = groups.get((condition, 'Augmented'), {})
        if set(baseline) != {1, 2, 3} or set(augmented) != set(baseline):
            raise ValueError(f'{condition}: require three complete paired seeds.')
        seeds = sorted(baseline)
        differences = [augmented[seed] - baseline[seed] for seed in seeds]
        summary.append({
            'condition': condition,
            'n_paired_seeds': len(seeds),
            'baseline_mean_pct': statistics.mean(baseline.values()),
            'baseline_sd_pct': statistics.stdev(baseline.values()),
            'augmented_mean_pct': statistics.mean(augmented.values()),
            'augmented_sd_pct': statistics.stdev(augmented.values()),
            'difference_mean_pp': statistics.mean(differences),
            'difference_sd_pp': statistics.stdev(differences),
        })
    return summary


def build_demo(destination: Path) -> dict:
    destination = destination.expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Output already exists. Choose a new directory; no files were overwritten.')
    destination = destination.resolve()
    if destination.is_relative_to(ROOT) or ROOT.is_relative_to(destination):
        raise ValueError('Choose an output directory outside the source repository.')
    summary = summarize_csv(CASE / 'materials/results.csv')
    destination.mkdir(parents=True, exist_ok=False)
    for folder in ('materials', 'reference'):
        shutil.copytree(CASE / folder, destination / folder)
    shutil.copy2(CASE / 'prompts.md', destination / 'prompts.md')
    outputs = destination / 'outputs'
    outputs.mkdir()
    with (outputs / 'metric-summary.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]), lineterminator='\n')
        writer.writeheader()
        for row in summary:
            writer.writerow({key: f'{value:.2f}' if isinstance(value, float) else value
                             for key, value in row.items()})
    table = [
        '# Synthetic TinyShapes: descriptive summary', '',
        'All inputs are manually constructed teaching data, not experimental measurements.',
        'Source: materials/results.csv. Three paired seeds per condition; sample SD uses n-1.',
        'Difference = Augmented - Baseline, in percentage points. No p-values are computed.', '',
        '| Condition | Baseline mean ± SD (%) | Augmented mean ± SD (%) | Difference mean ± SD (pp) |',
        '|---|---:|---:|---:|',
    ]
    for row in summary:
        table.append(
            f"| {row['condition']} | {row['baseline_mean_pct']:.2f} ± {row['baseline_sd_pct']:.2f}"
            f" | {row['augmented_mean_pct']:.2f} ± {row['augmented_sd_pct']:.2f}"
            f" | {row['difference_mean_pp']:+.2f} ± {row['difference_sd_pp']:.2f} |")
    (outputs / 'metric-summary.md').write_text('\n'.join(table) + '\n', encoding='utf-8')
    (destination / 'START_HERE.md').write_text(
        '# Synthetic workflow exercise\n\n'
        'Install conference-helper into this project using the source repository installer.\n'
        'Then open this folder in your agent and follow [the three prompts](prompts.md).\n'
        'Start with materials/ only; compare reference/ and outputs/ after completing each turn.\n\n'
        'reference/ contains authored example responses, not actual agent transcripts.\n'
        'outputs/ contains only deterministic numeric summaries computed by the demo script.\n'
        'No research experiments, model calls, state initialization, or network actions were performed.\n',
        encoding='utf-8')
    return {'status': 'created', 'path': str(destination), 'synthetic': True,
            'conditions': len(summary), 'agent_run_performed': False,
            'network_actions': False, 'research_experiments_performed': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build_demo(args.output), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({'status': 'error', 'message': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
