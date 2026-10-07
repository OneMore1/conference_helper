#!/usr/bin/env python3
"""One offline CLI for initialization, routing, state recording and checks."""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
# Python may strip the extended prefix from sys.path[0] even when it successfully
# opened a long script filename. Restore a usable sibling-import directory first.
if os.name == 'nt':
    _script_dir = os.path.abspath(os.path.dirname(__file__))
    if not _script_dir.startswith('\\\\?\\'):
        _script_dir = ('\\\\?\\UNC\\' + _script_dir[2:] if _script_dir.startswith('\\\\')
                       else '\\\\?\\' + _script_dir)
    sys.path.insert(0, _script_dir)
from init_workspace import initialize
from workflow_state import STAGES, commit, diagnose, load_json
from validate_workspace import validate

LABELS = {'intake':'阶段诊断', 'topic':'选题', 'ideation':'构思', 'design':'实验设计',
          'execution':'执行准备/核查', 'analysis':'结果分析', 'supplement':'证据补充',
          'writing':'写作', 'review':'科学审阅', 'submission':'投稿准备', 'rebuttal':'审稿回复'}

def render_card(report: dict) -> str:
    if report.get('status') != 'routed':
        return '状态记录需要修正：\n' + '\n'.join(report.get('errors', []))
    def label(key):
        value = report[key]
        return f'{LABELS.get(value, value)} ({value})'
    gaps = '；'.join(g.get('reason', '') for g in report['blockers']) or '未登记阻断性缺口；不等于科学验证通过'
    stale = ', '.join(report['stale_fields']) or '无已登记的版本失效'
    warnings = report.get('warnings', [])
    notice = '；'.join(' '.join(str(item).split()) for item in warnings)
    if not notice:
        notice = '仅依据已登记材料状态；未执行科研作业或论文提交。'
    return '\n'.join([
        f'已有进度：{label("observed_stage")}',
        f'建议推进：{label("recommended_stage")}',
        f'本轮执行：{label("active_stage")}；分支 {report["workstream"]}',
        f'关键缺口：{gaps}',
        f'版本检查：{stale}',
        f'注意：{notice}',
    ])

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('init', help='Create empty project records without overwrite')
    p.add_argument('workspace', type=Path); p.add_argument('--project-id', required=True)
    p = sub.add_parser('status', help='Route recorded assessments; does not read scientific content')
    p.add_argument('workspace', type=Path); p.add_argument('--requested', choices=sorted(STAGES | {'auto'}))
    p.add_argument('--workstream'); p.add_argument('--format', choices=['card','json'], default='card')
    p = sub.add_parser('record', help='Commit a reviewed state draft with optimistic locking')
    p.add_argument('workspace', type=Path); p.add_argument('--input', type=Path, required=True)
    p.add_argument('--expected-revision', type=int, required=True)
    p = sub.add_parser('check', help='Run structural checks; not independent scientific verification')
    p.add_argument('workspace', type=Path); p.add_argument('--stage', choices=sorted(STAGES | {'auto'}), default='auto')
    p.add_argument('--as-of', type=date.fromisoformat); p.add_argument('--baseline', type=Path)
    args = parser.parse_args(argv)
    try:
        code = 0
        if args.command == 'init':
            result = {'created': initialize(args.workspace, args.project_id), 'status':'templates_need_completion'}
        elif args.command == 'status':
            result = diagnose(args.workspace, args.requested, args.workstream)
            code = 2 if result.get('status') != 'routed' else 0
            if args.format == 'card':
                print(render_card(result)); return code
        elif args.command == 'record':
            result = commit(args.workspace, load_json(args.input), args.expected_revision)
        else:
            stage = args.stage
            if stage == 'auto':
                routed = diagnose(args.workspace)
                if routed.get('status') != 'routed':
                    print(json.dumps(routed, ensure_ascii=False, indent=2)); return 2
                stage = routed['active_stage']
            result = validate(args.workspace, stage, args.baseline, args.as_of)
            code = 0 if result['structural_status'] == 'pass' else 1
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status':'error', 'message':str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
