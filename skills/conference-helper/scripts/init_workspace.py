#!/usr/bin/env python3
"""Initialize an offline paper workspace without overwriting core records."""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from pathlib import Path
if os.name == 'nt':
    _script_dir = os.path.abspath(os.path.dirname(__file__))
    if not _script_dir.startswith('\\\\?\\'):
        _script_dir = ('\\\\?\\UNC\\' + _script_dir[2:] if _script_dir.startswith('\\\\')
                       else '\\\\?\\' + _script_dir)
    sys.path.insert(0, _script_dir)
from path_utils import io_path
from local_files import workspace_file_path

CORE = {
    "project_state.json": "project-state.template.json",
    "project.json": "project.template.json",
    "evidence_ledger.json": "evidence-ledger.template.json",
    "venue_profile.json": "venue-profile.template.json",
}

def initialize(directory: Path, project_id: str) -> list[str]:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}", project_id):
        raise ValueError("project-id must contain 1–80 ASCII letters, digits, hyphens or underscores.")
    directory = io_path(directory)
    if directory.exists() and not directory.is_dir():
        raise ValueError("Workspace path exists but is not a directory.")
    # Check all core paths and created directories before any persistent write.
    paths = {name: workspace_file_path(directory, name) for name in CORE}
    folders = [workspace_file_path(directory, name) for name in ('evidence', 'results', 'manuscript', 'artifacts')]
    collisions = [name for name, path in paths.items() if path.exists()]
    if collisions:
        raise FileExistsError("Refusing to overwrite: " + ", ".join(collisions))
    assets = io_path(__file__).parents[1] / "assets"
    payloads = {name: json.loads((assets / template).read_text(encoding="utf-8"))
                for name, template in CORE.items()}
    payloads["project.json"]["project_id"] = project_id
    payloads["project_state.json"]["project_id"] = project_id
    directory.mkdir(parents=True, exist_ok=True)
    for folder in folders:
        folder.mkdir(exist_ok=True)
    written: list[Path] = []
    try:
        for name, data in payloads.items():
            path = workspace_file_path(directory, name)
            with path.open("x", encoding="utf-8") as handle:
                written.append(path)
                json.dump(data, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
    except Exception:
        # Only remove records created in this invocation, never pre-existing files.
        for path in written:
            path.unlink(missing_ok=True)
        raise
    return [str(p) for p in written]

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--project-id", required=True)
    args = parser.parse_args()
    try:
        paths = initialize(args.workspace, args.project_id)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"created": paths, "status": "templates_need_completion"}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
