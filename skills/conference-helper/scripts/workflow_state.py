#!/usr/bin/env python3
"""Offline state routing. Reads recorded assessments, not scientific content.

No network, experiment launch, manuscript upload or conference submission.
"""
from __future__ import annotations
import argparse
import copy
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
if os.name == 'nt':
    _script_dir = os.path.abspath(os.path.dirname(__file__))
    if not _script_dir.startswith('\\\\?\\'):
        _script_dir = ('\\\\?\\UNC\\' + _script_dir[2:] if _script_dir.startswith('\\\\')
                       else '\\\\?\\' + _script_dir)
    sys.path.insert(0, _script_dir)
from path_utils import io_path
from local_files import check_local_file, file_hash as digest, valid_sha256, workspace_file_path

STAGES = {'intake', 'topic', 'ideation', 'design', 'execution', 'analysis',
          'supplement', 'writing', 'review', 'submission', 'rebuttal'}
STATUSES = {'unknown', 'not_started', 'in_progress', 'complete', 'blocked',
            'needs_refresh', 'not_applicable'}
FIELDS = ['research_question', 'literature_grounding', 'concept', 'experiment_plan',
          'experiments', 'result_analysis', 'evidence_gaps', 'manuscript',
          'internal_review', 'venue_compliance', 'submission_receipt']
OBSERVED = [('submission_receipt', 'submission'), ('venue_compliance', 'submission'),
            ('internal_review', 'review'), ('manuscript', 'writing'),
            ('evidence_gaps', 'supplement'), ('result_analysis', 'analysis'),
            ('experiments', 'execution'), ('experiment_plan', 'design'),
            ('concept', 'ideation'), ('research_question', 'topic')]
DEPENDENTS = {
    'research_question': ['literature_grounding', 'concept'],
    'literature_grounding': [],
    'concept': ['literature_grounding', 'experiment_plan'],
    'experiment_plan': ['experiments'],
    'experiments': ['result_analysis'],
    'result_analysis': ['evidence_gaps'],
    'evidence_gaps': ['manuscript'],
    'manuscript': ['internal_review'],
    'internal_review': ['venue_compliance'],
    'venue_compliance': [],
    'submission_receipt': [],
}


def load_json(path: Path) -> dict[str, Any]:
    path = io_path(path)
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError(f'{path.name}: JSON root must be an object')
    return value


def nonblank(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def inside(root: Path, value: str) -> Path:
    return workspace_file_path(root, value)


def ledger_sources(root: Path, referenced_ids: set[str] | None = None) -> dict[str, dict[str, Any]]:
    ledger = load_json(inside(root, 'evidence_ledger.json'))
    entries = ledger.get('sources', [])
    if not isinstance(entries, list):
        raise ValueError('ledger.sources must be an array')
    sources: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or not nonblank(entry.get('source_id')):
            if referenced_ids is not None:
                continue
            raise ValueError(f'ledger.sources[{index}]: source_id required')
        source_id = entry['source_id']
        if referenced_ids is not None and source_id not in referenced_ids:
            continue
        if source_id in sources:
            raise ValueError(f'duplicate source_id: {source_id}')
        sources[source_id] = entry
    return sources


def validate_state(state: dict[str, Any], root: Path,
                   source_workstream: str | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(state, dict):
        return ['state: JSON root must be an object']
    if state.get('schema_version') != '0.2':
        errors.append('schema_version must be 0.2')
    rev = state.get('revision')
    if type(rev) is not int or rev < 0:
        errors.append('revision must be a nonnegative integer')
    if not nonblank(state.get('project_id')):
        errors.append('project_id required')
    if state.get('updated_at') is not None and not isinstance(state['updated_at'], str):
        errors.append('updated_at: expected text or null')
    streams = state.get('workstreams')
    if not isinstance(streams, dict) or not streams:
        return errors + ['workstreams must be a nonempty object']
    if not nonblank(state.get('active_workstream')) or state['active_workstream'] not in streams:
        errors.append('active_workstream must identify an existing workstream')
    for sid, stream in streams.items():
        if not isinstance(stream, dict):
            errors.append(f'{sid}: workstream must be object'); continue
        requested = stream.get('requested_stage', 'auto')
        if not isinstance(requested, str) or requested not in STAGES | {'auto'}:
            errors.append(f'{sid}: invalid requested_stage')
        if 'latest_request' in stream and not isinstance(stream['latest_request'], str):
            errors.append(f'{sid}/latest_request: expected text')
        assessments = stream.get('assessments')
        if not isinstance(assessments, dict):
            errors.append(f'{sid}: assessments must be object'); continue
        artifacts = stream.get('artifacts', [])
        if not isinstance(artifacts, list):
            errors.append(f'{sid}: artifacts must be array'); artifacts = []
        ids: set[str] = set()
        for a in artifacts:
            if not isinstance(a, dict) or not nonblank(a.get('id')) or not nonblank(a.get('path')):
                errors.append(f'{sid}: artifact id and relative path required'); continue
            if a['id'] in ids:
                errors.append(f'{sid}: duplicate artifact id {a["id"]}')
            ids.add(a['id'])
            try:
                inside(root, a['path'])
            except (OSError, ValueError, RuntimeError) as exc:
                errors.append(str(exc))
            sha = a.get('sha256')
            if sha is not None and not valid_sha256(sha):
                errors.append(f'{sid}/{a["id"]}: malformed SHA-256')
        for field in FIELDS:
            a = assessments.get(field)
            if not isinstance(a, dict):
                errors.append(f'{sid}/{field}: assessment object required'); continue
            status = a.get('status')
            if not isinstance(status, str) or status not in STATUSES:
                errors.append(f'{sid}/{field}: invalid status')
                continue
            refs = a.get('evidence')
            if not isinstance(refs, list):
                errors.append(f'{sid}/{field}: evidence must be array'); refs = []
            if status in {'complete', 'in_progress'} and not refs:
                errors.append(f'{sid}/{field}: completion/progress requires evidence locator')
            for key in ('note', 'assessed_by'):
                if key in a and not isinstance(a[key], str):
                    errors.append(f'{sid}/{field}/{key}: expected text')
            if status not in {'unknown', 'not_started'} and not nonblank(a.get('note')):
                errors.append(f'{sid}/{field}: note/reason required')
            for ref in refs:
                if not isinstance(ref, str) or ':' not in ref:
                    errors.append(f'{sid}/{field}: use artifact:, source:, or author: locator'); continue
                kind, locator = ref.split(':', 1)
                if kind not in {'artifact', 'source', 'author'} or not locator.strip():
                    errors.append(f'{sid}/{field}: invalid evidence locator {ref}')
                if kind == 'artifact' and locator not in ids:
                    errors.append(f'{sid}/{field}: unknown artifact {locator}')
            if not isinstance(a.get('confidence', 'low'), str) or a.get('confidence', 'low') not in {'low', 'medium', 'high'}:
                errors.append(f'{sid}/{field}: invalid confidence')
        for field in ('manuscript', 'internal_review'):
            entry = assessments.get(field)
            if not isinstance(entry, dict):
                continue
            scope = entry.get('scope', 'full_paper')
            if not isinstance(scope, str) or scope not in {'full_paper', 'section'}:
                errors.append(f'{sid}/{field}: scope must be full_paper or section')
        for key in ('gaps', 'invalidations'):
            if not isinstance(stream.get(key, []), list):
                errors.append(f'{sid}/{key}: must be array')
        for g in stream.get('gaps', []) if isinstance(stream.get('gaps', []), list) else []:
            if not isinstance(g, dict):
                errors.append(f'{sid}: gap must be object'); continue
            if not nonblank(g.get('id')) or not nonblank(g.get('reason')):
                errors.append(f'{sid}: gap id/reason required')
            if not isinstance(g.get('priority'), str) or g['priority'] not in {'blocking', 'supportive', 'optional'}:
                errors.append(f'{sid}: invalid gap priority')
            if not isinstance(g.get('status'), str) or g['status'] not in {'open', 'resolved', 'deferred'}:
                errors.append(f'{sid}: invalid gap status')
        for inv in stream.get('invalidations', []) if isinstance(stream.get('invalidations', []), list) else []:
            if not isinstance(inv, dict) or not nonblank(inv.get('reason')):
                errors.append(f'{sid}: invalidation requires reason'); continue
            affected = inv.get('affected_fields')
            if not isinstance(affected, list) or not affected or any(not isinstance(x, str) or x not in FIELDS for x in affected):
                errors.append(f'{sid}: invalid affected_fields')
            if not isinstance(inv.get('status'), str) or inv['status'] not in {'open', 'resolved'}:
                errors.append(f'{sid}: invalid invalidation status')
            if 'source' in inv and not isinstance(inv['source'], str):
                errors.append(f'{sid}: invalidation source must be text')
    # Resolve declared source IDs when state records rely on the evidence ledger.
    source_refs = []
    for sid, stream in streams.items():
        if source_workstream is not None and sid != source_workstream:
            continue
        if not isinstance(stream, dict) or not isinstance(stream.get('assessments'), dict):
            continue
        for field, entry in stream['assessments'].items():
            if not isinstance(entry, dict) or not isinstance(entry.get('evidence'), list):
                continue
            source_refs.extend((sid, field, ref.split(':', 1)[1]) for ref in entry['evidence']
                               if isinstance(ref, str) and ref.startswith('source:'))
    if source_refs:
        try:
            referenced = {source_id for _, _, source_id in source_refs}
            source_ids = ledger_sources(root, referenced if source_workstream is not None else None)
            for sid, field, source_id in source_refs:
                if source_id not in source_ids:
                    errors.append(f'{sid}/{field}: unknown ledger source {source_id}')
        except (OSError, ValueError) as exc:
            errors.append(f'Cannot resolve source locators: {exc}')
    return errors


def closure(fields: set[str]) -> set[str]:
    result = set(fields)
    pending = list(fields)
    while pending:
        for field in DEPENDENTS.get(pending.pop(), []):
            if field not in result:
                result.add(field); pending.append(field)
    return result


def diagnose(root: Path, requested: str | None = None,
             workstream: str | None = None) -> dict[str, Any]:
    root = io_path(root)
    state = load_json(inside(root, 'project_state.json'))
    sid = state.get('active_workstream') if workstream is None else workstream
    errors = validate_state(state, root, sid if isinstance(sid, str) else None)
    if errors:
        return {'status': 'invalid_state', 'errors': errors, 'external_actions_performed': False}
    if not isinstance(sid, str) or sid not in state['workstreams']:
        raise ValueError(f'Unknown workstream: {sid}')
    stream = state['workstreams'][sid]
    requested = stream.get('requested_stage', 'auto') if requested is None else requested
    if not isinstance(requested, str) or requested not in STAGES | {'auto'}:
        raise ValueError(f'Unsupported requested stage: {requested}')
    a = stream['assessments']
    status = {k: a[k]['status'] for k in FIELDS}
    warnings: list[str] = []
    stale: set[str] = {k for k in FIELDS if status[k] == 'needs_refresh'}
    for inv in stream.get('invalidations', []):
        if inv['status'] == 'open':
            stale.update(inv['affected_fields']); warnings.append(inv['reason'])
    for artifact in stream.get('artifacts', []):
        issues = check_local_file(root, artifact['path'], artifact.get('sha256'))
        if issues:
            warnings.append(f'{artifact["id"]}: {"; ".join(issues)}; re-read before relying on it')
            stale.update(k for k in FIELDS if f'artifact:{artifact["id"]}' in a[k]['evidence'])
    # Only sources used by this workstream can invalidate its assessments.
    used_sources: dict[str, set[str]] = {}
    for field in FIELDS:
        for ref in a[field]['evidence']:
            if ref.startswith('source:'):
                used_sources.setdefault(ref.split(':', 1)[1], set()).add(field)
    if used_sources:
        try:
            sources = ledger_sources(root, set(used_sources))
        except (OSError, ValueError) as exc:
            return {'status': 'invalid_state', 'errors': [f'Cannot resolve source locators: {exc}'],
                    'external_actions_performed': False}
        for source_id, fields in used_sources.items():
            source = sources.get(source_id)
            if source is None:
                return {'status': 'invalid_state', 'errors': [f'{sid}: unknown ledger source {source_id}'],
                        'external_actions_performed': False}
            if source.get('kind') != 'local_result':
                continue
            issues = check_local_file(root, source.get('locator'), source.get('sha256'))
            if issues:
                warnings.append(f'source:{source_id}: {"; ".join(issues)}; re-read before relying on it')
                stale.update(fields)
    stale = closure(stale)
    for field in stale:
        # A filed submission remains a historical event, even when later files change.
        if status[field] != 'not_applicable':
            status[field] = 'needs_refresh'
    done = lambda field: status[field] in {'complete', 'not_applicable'}
    started = lambda field: status[field] in {'complete', 'in_progress'}
    blockers = [g for g in stream.get('gaps', []) if g['priority'] == 'blocking' and g['status'] != 'resolved']
    observed = next((stage for field, stage in OBSERVED
                     if a[field]['status'] in {'complete', 'in_progress'}), 'intake')

    # Prioritize the active evidence bottleneck; do not force an advanced project to restart.
    if blockers:
        recommended, reason = 'supplement', 'Core claim has an unresolved evidence gap; diagnose the smallest repair.'
    elif started('experiments') and not done('result_analysis'):
        recommended, reason = 'analysis', 'Preliminary or completed results exist; analyze them before strengthening claims.'
    elif done('result_analysis') and not done('evidence_gaps'):
        recommended, reason = 'supplement', 'Audit remaining evidence gaps; this does not automatically require new experiments.'
    elif status['manuscript'] == 'complete' and a['manuscript'].get('scope', 'full_paper') == 'full_paper':
        if not done('internal_review') or a['internal_review'].get('scope', 'full_paper') != 'full_paper':
            recommended, reason = 'review', 'A manuscript is recorded; review scientific and cross-section consistency.'
        else:
            recommended, reason = 'submission', 'Scientific review is recorded; prepare/check the venue-specific package.'
    elif status['manuscript'] in {'in_progress', 'complete'}:
        recommended, reason = 'writing', 'Continue the existing manuscript while tracking evidence limitations separately.'
    elif done('result_analysis') and done('evidence_gaps'):
        recommended, reason = 'writing', 'Analysis and claim-gap assessment support writing within the recorded scope.'
    elif done('experiment_plan'):
        recommended, reason = 'execution', 'A plan is recorded; prepare or verify execution, subject to permissions.'
    elif done('concept'):
        recommended, reason = 'design', 'The idea is specific; determine the distinguishing experiment.'
    elif done('research_question'):
        recommended, reason = 'ideation', 'The question is specific; develop and check a concrete mechanism or explanation.'
    elif status['research_question'] == 'in_progress':
        recommended, reason = 'topic', 'Narrow and select the research question using the available context.'
    else:
        recommended, reason = 'intake', 'Read available materials and ask only decision-changing missing questions.'
    # Explicitly invalidated upstream outputs take precedence over dependent ready-looking files.
    for field, stage in [('research_question', 'topic'), ('literature_grounding', 'topic'),
                         ('concept', 'ideation'), ('experiment_plan', 'design'),
                         ('experiments', 'execution'), ('result_analysis', 'analysis'),
                         ('evidence_gaps', 'supplement'), ('manuscript', 'writing'),
                         ('internal_review', 'review'), ('venue_compliance', 'submission')]:
        if field in stale:
            recommended, reason = stage, f'{field} or its evidence changed; refresh affected work only.'
            break
    if a['submission_receipt']['status'] == 'complete':
        warnings.append('A historical submission receipt is recorded; do not resubmit automatically.')
    active = recommended if requested == 'auto' else requested
    if requested != 'auto' and requested != recommended:
        warnings.append('Explicit task retained; unfinished dependencies remain visible and do not authorize broader work.')
    if status['literature_grounding'] not in {'complete', 'not_applicable'}:
        warnings.append('Literature grounding is not recorded complete; do not claim that novelty has been established.')
    observed_basis = {k: {'status': a[k]['status'], 'evidence': a[k]['evidence'], 'note': a[k].get('note', '')}
                      for k in FIELDS if a[k]['status'] != 'unknown'}
    return {'status': 'routed', 'project_id': state['project_id'], 'revision': state['revision'],
            'workstream': sid, 'observed_stage': observed, 'requested_stage': requested,
            'recommended_stage': recommended, 'active_stage': active, 'reason': reason,
            'effective_status': status, 'assessment_basis': observed_basis, 'blockers': blockers,
            'stale_fields': sorted(stale), 'warnings': warnings,
            'assessment_truth_verified_by_script': False, 'external_actions_performed': False,
            'submission_action': 'none; preparation is not submission'}


def init_state(root: Path) -> dict[str, Any]:
    root = io_path(root)
    inside(root, 'project_state.json')
    project = load_json(inside(root, 'project.json'))
    state = load_json(io_path(__file__).parents[1] / 'assets/project-state.template.json')
    state['project_id'] = project['project_id']
    with inside(root, 'project_state.json').open('x', encoding='utf-8') as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2); handle.write('\n')
    return {'created': str(root / 'project_state.json'), 'all_assessments': 'unknown'}


def commit(root: Path, draft: dict[str, Any], expected_revision: int) -> dict[str, Any]:
    root = io_path(root)
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError('expected_revision must be a nonnegative integer')
    errors = validate_state(draft, root)
    if errors:
        raise ValueError('; '.join(errors))
    # Resolve every transaction target before creating even the lock. Parent
    # junctions/symlinks may redirect an apparently local history directory.
    history_name = f'artifacts/state_history/revision-{expected_revision:06d}-{uuid.uuid4().hex}.json'
    temp_name = f'.project_state-{uuid.uuid4().hex}.tmp'
    inside(root, 'project_state.json')
    lock = inside(root, '.workflow-state.lock')
    inside(root, 'artifacts/state_history')
    inside(root, history_name)
    inside(root, temp_name)
    # Lock is used only for this short local transaction. A leftover lock requires inspection.
    with lock.open('x', encoding='utf-8') as handle:
        handle.write(str(os.getpid()))
    temp: Path | None = None
    try:
        before = load_json(inside(root, 'project_state.json'))
        if before.get('revision') != expected_revision:
            raise ValueError('Revision conflict: read the latest state before applying your changes.')
        if draft.get('revision') != expected_revision:
            raise ValueError('Draft revision does not match expected_revision.')
        if draft.get('project_id') != before.get('project_id'):
            raise ValueError('project_id cannot change in a state update.')
        if not isinstance(before.get('workstreams'), dict):
            raise ValueError('Current state workstreams must be an object; restore the state before updating.')
        if not set(before['workstreams']).issubset(draft['workstreams']):
            raise ValueError('State update cannot silently remove workstreams; archive them explicitly instead.')
        after = copy.deepcopy(draft)
        after['revision'] = expected_revision + 1
        after['updated_at'] = datetime.now(timezone.utc).isoformat()
        inside(root, 'artifacts/state_history').mkdir(parents=True, exist_ok=True)
        with inside(root, history_name).open('x', encoding='utf-8') as handle:
            json.dump(before, handle, ensure_ascii=False, indent=2); handle.write('\n')
        candidate = inside(root, temp_name)
        with candidate.open('x', encoding='utf-8') as handle:
            temp = candidate
            json.dump(after, handle, ensure_ascii=False, indent=2); handle.write('\n')
            handle.flush(); os.fsync(handle.fileno())
        os.replace(inside(root, temp_name), inside(root, 'project_state.json'))
        return {'status': 'state_updated', 'revision': after['revision'], 'external_actions_performed': False}
    finally:
        if temp is not None:
            inside(root, temp_name).unlink(missing_ok=True)
        inside(root, '.workflow-state.lock').unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    p = subs.add_parser('init'); p.add_argument('workspace', type=Path)
    p = subs.add_parser('diagnose'); p.add_argument('workspace', type=Path)
    p.add_argument('--requested', choices=sorted(STAGES | {'auto'})); p.add_argument('--workstream')
    p = subs.add_parser('commit'); p.add_argument('workspace', type=Path)
    p.add_argument('--input', type=Path, required=True); p.add_argument('--expected-revision', type=int, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            result = init_state(args.workspace)
        elif args.command == 'diagnose':
            result = diagnose(args.workspace, args.requested, args.workstream)
        else:
            result = commit(args.workspace, load_json(args.input), args.expected_revision)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'error', 'message': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 2 if result.get('status') == 'invalid_state' else 0


if __name__ == '__main__':
    raise SystemExit(main())
