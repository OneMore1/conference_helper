#!/usr/bin/env python3
"""Build verified source and standalone-skill ZIPs from the package allowlist."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SKILL_PREFIX = 'skills/conference-helper/'
RUNTIME_FILES = ('workflow.py', 'workflow_state.py', 'validate_workspace.py',
                 'init_workspace.py', 'local_files.py', 'path_utils.py')
INIT_TEMPLATES = ('project-state.template.json', 'project.template.json',
                  'evidence-ledger.template.json', 'venue-profile.template.json')


def verified_files(root: Path) -> tuple[str, dict[str, bytes]]:
    root = root.resolve()
    raw = (root / 'PACKAGE-MANIFEST.json').read_bytes()
    manifest = json.loads(raw)
    version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    if not isinstance(manifest, dict) or manifest.get('version') != version:
        raise ValueError('Package manifest and VERSION must agree.')
    if not version or any(c not in '0123456789.-abcdefghijklmnopqrstuvwxyz' for c in version):
        raise ValueError('Invalid release version.')
    entries = manifest.get('files')
    if not isinstance(entries, list) or not entries:
        raise ValueError('Package manifest must list files.')
    files: dict[str, bytes] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get('path'), str):
            raise ValueError('Manifest entries require a relative path.')
        name = entry['path']
        rel = PurePosixPath(name)
        if (not name or rel.is_absolute() or '..' in rel.parts or ':' in name
                or '\\' in name or name != rel.as_posix() or name in files
                or name == 'PACKAGE-MANIFEST.json'):
            raise ValueError(f'Unsafe or duplicate manifest path: {name}')
        path = root / name
        if not path.resolve().is_relative_to(root) or path.is_symlink():
            raise ValueError(f'File leaves the source tree: {name}')
        data = path.read_bytes()
        if len(data) != entry.get('bytes') or hashlib.sha256(data).hexdigest() != entry.get('sha256'):
            raise ValueError(f'Package manifest is stale or content changed: {name}')
        files[name] = data
    required = {'LICENSE', 'README.md', 'tools/install_skill.py',
                SKILL_PREFIX + 'SKILL.md', SKILL_PREFIX + 'LICENSE',
                SKILL_PREFIX + 'LICENSE-SCOPE.md', SKILL_PREFIX + 'THIRD_PARTY_NOTICES.md',
                SKILL_PREFIX + 'licenses/ResearchStudio-MIT.txt',
                SKILL_PREFIX + 'licenses/Paper-X-Ray-MIT.txt',
                SKILL_PREFIX + 'licenses/PAPER-CC-BY-4.0-NOTICE.md'}
    required.update(SKILL_PREFIX + 'scripts/' + name for name in RUNTIME_FILES)
    required.update(SKILL_PREFIX + 'assets/' + name for name in INIT_TEMPLATES)
    # Also catch future helper modules or templates omitted from a stale allowlist.
    for folder, pattern in (('scripts', '*.py'), ('assets', '*.json')):
        required.update(path.relative_to(root).as_posix()
                        for path in (root / SKILL_PREFIX / folder).rglob(pattern))
    if required - files.keys():
        raise ValueError('Manifest omits required installation or license files: '
                         + ', '.join(sorted(required - files.keys())))
    files['PACKAGE-MANIFEST.json'] = raw
    return version, files


def archive(path: Path, files: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, data)


def build_release(output: Path, root: Path = ROOT) -> dict:
    root = root.resolve()
    output = output.expanduser().absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError('Output already exists; choose a new directory.')
    output = output.resolve()
    if output.is_relative_to(root) or root.is_relative_to(output):
        raise ValueError('Release output must be outside the source repository.')
    # Verify every byte before creating an output directory.
    version, files = verified_files(root)
    output.mkdir(parents=True, exist_ok=False)
    source_name = f'conference_helper-v{version}-source.zip'
    skill_name = f'conference-helper-v{version}.zip'
    archive(output / source_name, {'conference_helper/' + name: data for name, data in files.items()})
    skill_files = {'conference-helper/' + name[len(SKILL_PREFIX):]: data
                   for name, data in files.items() if name.startswith(SKILL_PREFIX)}
    archive(output / skill_name, skill_files)
    hashes = {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
              for name in (source_name, skill_name)}
    with (output / 'SHA256SUMS.txt').open('x', encoding='utf-8', newline='\n') as handle:
        handle.write(''.join(f'{sha}  {name}\n' for name, sha in hashes.items()))
    return {'version': version, 'output': str(output), 'source_files': len(files),
            'skill_files': len(skill_files), 'sha256': hashes}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build_release(args.output), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({'status': 'error', 'message': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
