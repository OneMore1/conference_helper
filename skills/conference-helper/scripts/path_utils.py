"""Normalize filesystem paths without requiring global Windows long-path settings."""
from __future__ import annotations

import os
import re
from pathlib import Path


def display_path(value: str | os.PathLike[str]) -> str:
    """Remove the Windows I/O prefix for display only, never for filesystem use."""
    text = os.fspath(value)
    if text[:8].lower() == '\\\\?\\unc\\':
        return '\\\\' + text[8:]
    if text.startswith('\\\\?\\'):
        return text[4:]
    return text


def _windows_absolute(value: str | os.PathLike[str]) -> Path:
    # Normalize dot components before adding the extended prefix, whose native
    # Windows semantics do not otherwise collapse them. This also makes ordinary
    # and already-prefixed spellings identical for containment comparisons.
    text = os.fspath(value).replace('/', '\\')
    if text.startswith('\\\\.\\'):
        raise ValueError('Windows device namespaces are not supported; use a drive or UNC filesystem path.')
    if text.startswith('\\\\?\\'):
        suffix = text[4:]
        if suffix[:4].lower() != 'unc\\' and not re.match(r'^[A-Za-z]:\\', suffix):
            raise ValueError('Only extended drive and UNC filesystem paths are supported.')
    absolute = os.path.abspath(os.path.expanduser(display_path(text)))
    if absolute.startswith('\\\\'):
        parts = absolute[2:].split('\\')
        if len(parts) < 2 or not parts[0] or not parts[1] or parts[0] in {'.', '?'}:
            raise ValueError('UNC filesystem paths require a server and share.')
        return Path('\\\\?\\UNC\\' + absolute[2:])
    return Path('\\\\?\\' + absolute)


def io_path(value: str | os.PathLike[str], resolve: bool = True) -> Path:
    """Return an absolute I/O path; resolve links unless explicitly disabled.

    Windows paths always use an extended drive or UNC prefix. Every operand in
    a containment comparison should be normalized with this function. Resolving
    follows junctions and symlinks, so existing workspace boundary checks remain
    effective. ``resolve=False`` preserves links for pre-replacement checks.
    """
    if os.name != 'nt':
        path = Path(value).expanduser()
        return path.resolve() if resolve else path.absolute()
    path = _windows_absolute(value)
    return _windows_absolute(path.resolve()) if resolve else path
