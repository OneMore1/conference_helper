#!/usr/bin/env python3
"""Maintainer helper: hash staged files and require identical working-tree bytes."""
from __future__ import annotations
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    try:
        top = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=ROOT, text=True).strip()
        if Path(top).resolve() != ROOT:
            raise ValueError('This helper requires the source repository Git checkout, not an enclosing repository.')
        names = subprocess.check_output(['git', 'ls-files', '--cached', '-z'], cwd=ROOT).decode('utf-8').split('\0')
        entries = []
        for name in sorted(set(names) - {'', 'PACKAGE-MANIFEST.json'}):
            path = ROOT / name
            if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
                raise ValueError(f'Refusing file outside source repository: {name}')
            data = subprocess.check_output(['git', 'show', ':' + name], cwd=ROOT)
            if path.read_bytes() != data:
                raise ValueError(f'Working-tree bytes differ from the staged file: {name}. '
                                 'Stage intended edits and use LF line endings before packaging.')
            entries.append({'path': name, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
        payload = {'version': (ROOT / 'VERSION').read_text(encoding='utf-8').strip(),
                   'files': entries, 'manifest_excludes_itself': True}
        (ROOT / 'PACKAGE-MANIFEST.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        print(f'Manifest updated: {len(entries)} tracked files. Review and stage PACKAGE-MANIFEST.json next.')
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
