"""Shared offline checks for files declared inside a project workspace."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
from path_utils import io_path


def valid_sha256(value: Any) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(c in '0123456789abcdefABCDEF' for c in value))


def workspace_file_path(root: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError('relative file path required')
    raw = Path(value)
    try:
        resolved_root = io_path(root)
        result = io_path(resolved_root / raw)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f'cannot resolve workspace path {value}: {exc}') from exc
    if raw.is_absolute() or not result.is_relative_to(resolved_root):
        raise ValueError(f'path must stay inside the workspace: {value}')
    return result


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with io_path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def check_local_file(root: Path, value: Any, sha256: Any = None,
                     require_hash: bool = False) -> list[str]:
    """Check a locator and its recorded bytes; never assess scientific support."""
    try:
        path = workspace_file_path(root, value)
    except (OSError, ValueError, RuntimeError) as exc:
        return [str(exc)]
    errors: list[str] = []
    try:
        if not path.is_file():
            return [f'file not found: {value}']
        if require_hash and (not isinstance(sha256, str) or not sha256.strip()):
            errors.append('SHA-256 required at final preflight')
        if sha256 is not None:
            if not valid_sha256(sha256):
                errors.append('invalid SHA-256')
            elif file_hash(path).lower() != sha256.lower():
                errors.append('SHA-256 mismatch; recheck changed evidence')
    except (OSError, ValueError) as exc:
        errors.append(f'cannot read file: {exc}')
    return errors
