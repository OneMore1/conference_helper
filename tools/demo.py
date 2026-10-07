#!/usr/bin/env python3
"""Exercise three routing cases using temporary synthetic state, never user data."""
from __future__ import annotations
import copy
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/conference-helper'
sys.path.insert(0, str(SKILL / 'scripts'))
from init_workspace import initialize
from workflow_state import diagnose
from workflow import render_card

def main() -> int:
    with tempfile.TemporaryDirectory(prefix='conference-synthetic-') as folder:
        root = Path(folder)
        initialize(root, 'synthetic-example-not-user-results')
        state = json.loads((SKILL / 'examples/partial-results-with-draft.state.json').read_text(encoding='utf-8'))
        (root/'project_state.json').write_text(json.dumps(state),encoding='utf-8')
        auto = diagnose(root)
        explicit = diagnose(root, 'writing')
        if auto['active_stage'] != 'analysis' or explicit['active_stage'] != 'writing':
            raise RuntimeError('Synthetic routing expectation failed.')
        print('示例一：已有初稿，但结果未分析（全部为合成状态）')
        print(render_card(auto))
        print('\n示例二：用户只要求写作，不改题')
        print(render_card(explicit))
        section = copy.deepcopy(state)
        a = section['workstreams']['main']['assessments']
        for field in ['result_analysis','evidence_gaps']:
            a[field].update(status='complete', evidence=['author:synthetic fixture'], note='Synthetic only')
        a['manuscript']['scope'] = 'section'
        (root/'project_state.json').write_text(json.dumps(section),encoding='utf-8')
        report = diagnose(root)
        if report['active_stage'] != 'writing':
            raise RuntimeError('A completed section must not imply a complete manuscript.')
        print('\n示例三：Methods 完成，不等于整篇定稿')
        print(render_card(report))
        print('\nPASS: 3 synthetic routing demonstrations. No network or research experiment was run.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
