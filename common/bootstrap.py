"""Locate the repository root.

`common` is installed editable into the root uv project's venv (see
pyproject.toml's [tool.hatch.build.targets.wheel]), so it's importable from
any exercise script regardless of nesting depth — no sys.path hacks needed.
This just locates the root itself, e.g. to load the root .env file.
"""

from pathlib import Path


def find_repo_root(start_file: str) -> Path:
    """Walk upward from start_file until a directory containing pyproject.toml is found."""
    path = Path(start_file).resolve()
    for parent in path.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise RuntimeError(f"Could not locate repository root (pyproject.toml) above {path}")
