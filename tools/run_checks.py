#!/usr/bin/env python3
"""Run both suites with an isolated temporary workspace outside the repository."""
from __future__ import annotations
import argparse
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TempRootError(RuntimeError):
    """No safe, writable temporary root was available."""


def check_temp_root(candidate: Path) -> None:
    """Probe permissions without tempfile's Windows permission-error retries."""
    probe_directory = candidate / f'conference-workflow-probe-{uuid.uuid4().hex}'
    # On restricted Windows hosts os.access() can report writable even when
    # mkdir is denied. tempfile treats that denial as a name collision and may
    # retry hundreds of thousands of times; this direct mkdir fails promptly.
    probe_directory.mkdir()
    probe_file = probe_directory / '.write-probe'
    try:
        probe_file.write_bytes(b'')
    finally:
        if probe_file.exists():
            probe_file.unlink()
        probe_directory.rmdir()


def default_temp_roots(repo_root: Path) -> list[Path]:
    """Consider normal temp locations, then the repository's writable parent.

    Do not call gettempdir(): its last-resort probe can write into the cwd.
    Every candidate is checked below before creating any temporary files.
    """
    candidates = [Path(os.environ[key]) for key in ('TMPDIR', 'TEMP', 'TMP')
                  if os.environ.get(key)]
    if os.name == 'nt':
        for key, suffix in [('LOCALAPPDATA', 'Temp'),
                            ('USERPROFILE', 'AppData/Local/Temp'),
                            ('SYSTEMROOT', 'Temp')]:
            if os.environ.get(key):
                candidates.append(Path(os.environ[key]) / suffix)
    else:
        candidates.extend(Path(path) for path in ('/tmp', '/var/tmp', '/usr/tmp'))
    candidates.append(repo_root.parent)
    return candidates


def create_run_workspace(repo_root: Path, temp_root: str | Path | None = None
                         ) -> tempfile.TemporaryDirectory:
    """Create only an owned temporary child of an existing external directory."""
    repo_root = repo_root.resolve()
    candidates = ([Path(temp_root)] if temp_root is not None
                  else default_temp_roots(repo_root))
    failures = []
    seen = set()
    for candidate in candidates:
        temporary = None
        try:
            candidate = candidate.expanduser().resolve()
            if candidate in seen:
                continue
            seen.add(candidate)
            if candidate == repo_root or repo_root in candidate.parents:
                raise ValueError('must be outside the source repository')
            if not candidate.is_dir():
                raise ValueError('must be an existing directory')
            check_temp_root(candidate)
            temporary = tempfile.TemporaryDirectory(
                prefix='conference-workflow-checks-', dir=candidate)
            # Directory creation alone does not prove file-write permission.
            probe = Path(temporary.name) / '.write-probe'
            probe.write_bytes(b'')
            probe.unlink()
            return temporary
        except (OSError, ValueError, RuntimeError) as exc:
            failures.append(f'{candidate}: {exc}')
            if temporary is not None:
                temporary.cleanup()
    details = '\n  '.join(failures) or 'no candidates were available'
    choice = 'Requested --temp-root is unusable' if temp_root is not None else 'No usable temporary root'
    raise TempRootError(
        f'{choice}.\n  {details}\n'
        'Use --temp-root EXISTING_WRITABLE_DIRECTORY outside the source repository.')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--temp-root', metavar='DIRECTORY',
                        help='existing writable directory outside this repository; '
                             'only the temporary child created for this run is removed')
    args = parser.parse_args(argv)
    try:
        with create_run_workspace(ROOT, args.temp_root) as workspace:
            env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1',
                       TMP=workspace, TEMP=workspace, TMPDIR=workspace)
            print(f'Temporary workspace: {workspace}', flush=True)
            failed = False
            for folder in ['skills/conference-helper/evals', 'tests']:
                print(f'\n=== {folder} ===', flush=True)
                result = subprocess.run(
                    [sys.executable, '-m', 'unittest', 'discover', '-s', folder,
                     '-p', 'test_*.py', '-v'], cwd=ROOT, env=env, check=False)
                failed = failed or result.returncode != 0
            return 1 if failed else 0
    except (TempRootError, OSError) as exc:
        print(f'ERROR: checks could not run safely: {exc}', file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
