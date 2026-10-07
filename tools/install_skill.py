#!/usr/bin/env python3
"""Install the canonical skill locally. Offline, no credentials, no silent overwrite."""
from __future__ import annotations
import argparse
import json
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

NAME = 'conference-helper'
# Python may start a deep script successfully while normalizing sys.path[0]
# back to a Windows path its module finder cannot open. Bootstrap before imports.
_scripts = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       '..', 'skills', NAME, 'scripts'))
if os.name == 'nt' and not _scripts.startswith('\\\\?\\'):
    _scripts = ('\\\\?\\UNC\\' + _scripts[2:] if _scripts.startswith('\\\\')
                else '\\\\?\\' + _scripts)
sys.path.insert(0, _scripts)
from path_utils import io_path, display_path

SOURCE = io_path(Path(__file__).parent.parent / 'skills' / NAME)

def install(destination: Path, backup_existing: bool = False, source: Path = SOURCE) -> dict:
    source = io_path(source)
    if not (source / 'SKILL.md').is_file():
        raise ValueError('Source does not contain SKILL.md.')
    if any(p.is_symlink() for p in source.rglob('*')):
        raise ValueError('Source contains symlinks; inspect before installing.')
    destination = io_path(destination, resolve=False)
    if destination.name != NAME:
        raise ValueError(f'Destination folder must be named {NAME}.')
    if destination.is_symlink():
        raise ValueError('Destination is a symlink; refusing to replace it.')
    destination = io_path(destination)
    if destination == source or destination.is_relative_to(source) or source.is_relative_to(destination):
        raise ValueError('Source and destination must not overlap.')
    if destination.exists() and not backup_existing:
        raise FileExistsError('Skill already exists. Inspect it or use --backup-existing for an explicit upgrade.')
    if destination.exists() and not destination.is_dir():
        raise ValueError('Destination exists and is not a directory.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    lock = destination.parent / f'.{NAME}.install.lock'
    with lock.open('x', encoding='utf-8') as handle:
        handle.write(str(os.getpid()))
    stage = destination.parent / f'.cpw-{uuid.uuid4().hex[:16]}.tmp'
    backup = None
    try:
        # Recheck after acquiring the lock.
        if destination.exists() and not backup_existing:
            raise FileExistsError('Destination appeared during installation; refusing to overwrite.')
        shutil.copytree(source, stage, ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
        if destination.exists():
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            backup_root = destination.parent.with_name(destination.parent.name + '-backups')
            backup_root.mkdir(parents=True, exist_ok=True)
            backup = backup_root / f'{NAME}-{stamp}-{uuid.uuid4().hex[:8]}'
            destination.rename(backup)
        stage.rename(destination)
    except Exception:
        if stage.exists():
            if not io_path(stage).is_relative_to(io_path(destination.parent)):
                raise ValueError('Installation stage escaped its parent; refusing cleanup.')
            shutil.rmtree(stage)
        if backup is not None and backup.exists() and not destination.exists():
            backup.rename(destination)
        raise
    finally:
        lock.unlink(missing_ok=True)
    return {'status':'installed', 'path':str(destination), 'display_path':display_path(destination),
            'backup':str(backup) if backup else None,
            'display_backup':display_path(backup) if backup else None,
            'network_actions':False, 'research_workspace_created':False}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--project', type=Path, help='Install in PROJECT/.agents/skills')
    group.add_argument('--user', action='store_true', help='Install in ~/.agents/skills')
    group.add_argument('--destination', type=Path, help=f'Exact skill folder, ending in /{NAME}')
    parser.add_argument('--backup-existing', action='store_true')
    args = parser.parse_args(argv)
    destination = args.destination
    if args.project is not None:
        destination = args.project / '.agents/skills' / NAME
    elif args.user:
        destination = Path.home() / '.agents/skills' / NAME
    try:
        print(json.dumps(install(destination, args.backup_existing),ensure_ascii=False,indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({'status':'error','message':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
