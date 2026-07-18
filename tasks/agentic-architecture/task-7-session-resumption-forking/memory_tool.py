"""Client-side handler for Anthropic's built-in memory tool (memory_20250818),
backing the `restart` mode's "start fresh, recover context from a curated
memory file" path (Domain 1.7) — see
https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool

The memory tool is model-driven and file-based: Claude decides when to
view/create/edit files under a `/memories` prefix, and this handler is the
client-side code that actually executes those requests. It has no concept
of a conversation transcript at all — unlike `common/session_store.py`
(which resumes/forks the exact prior messages), a `restart` run here starts
with a genuinely empty conversation and recovers context purely from
whatever an earlier run wrote to a memory file, which is why it's the right
tool for "the raw session's tool results would be stale, but I still want a
reliable, up-to-date summary" rather than for `resume`/`fork` themselves.

Files live under this task's own memory/ directory on disk; every path is
validated to stay within the /memories prefix before touching the
filesystem (see the doc's Path traversal protection guidance).
"""

import shutil
from pathlib import Path

MEMORY_ROOT_PREFIX = "/memories"


def _memory_dir() -> Path:
    """The real, on-disk directory /memories maps onto for this task."""
    path = Path(__file__).parent / "memory"
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def reset_memory() -> None:
    """Clear every file under the memory directory.

    Called from `new` mode only — a fresh baseline investigation should
    start with a clean slate, otherwise a leftover file from a previous run
    makes the coordinator's `create` call fail with "File already exists"
    and mixes old findings into a new investigation. Never called from
    `restart`, whose entire point is recovering whatever is already there.
    """
    root = _memory_dir()
    for child in root.iterdir():
        shutil.rmtree(child) if child.is_dir() else child.unlink()


def _resolve(path: str) -> Path:
    """Map a client-facing /memories/... path onto the on-disk memory directory,
    rejecting anything that would resolve outside it (path traversal protection)."""
    if not path.startswith(MEMORY_ROOT_PREFIX):
        raise ValueError(f"Path must start with {MEMORY_ROOT_PREFIX}: {path}")
    relative = path[len(MEMORY_ROOT_PREFIX):].lstrip("/")
    root = _memory_dir()
    resolved = (root / relative).resolve() if relative else root
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"Path escapes the memory directory: {path}")
    return resolved


def _human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "K", "M"):
        if size < 1024 or unit == "M":
            return f"{int(size)}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}M"


def memory_tool(
    command: str,
    path: str = MEMORY_ROOT_PREFIX,
    file_text: str = None,
    old_str: str = None,
    new_str: str = None,
    view_range: list = None,
    insert_line: int = None,
    insert_text: str = None,
    old_path: str = None,
    new_path: str = None,
) -> str:
    """Dispatch one memory command against the on-disk /memories directory,
    returning the exact reference response text the Anthropic docs specify
    for each command — Claude reads this content directly, so wording matters."""
    try:
        target = _resolve(path)
    except ValueError as exc:
        return f"Error: {exc}"

    if command == "view":
        if target.is_dir():
            files = sorted(target.rglob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            lines = [
                f"{_human_size(f.stat().st_size if f.is_file() else 0)}\t"
                f"{MEMORY_ROOT_PREFIX}/{f.relative_to(_memory_dir())}"
                for f in files
            ]
            header = (
                f"Here're the files and directories up to 2 levels deep in {path}, "
                "excluding hidden items and node_modules:"
            )
            return "\n".join([header, f"{_human_size(total_size)}\t{path}", *lines])
        if not target.exists():
            return f"The path {path} does not exist. Please provide a valid path."
        file_lines = target.read_text().splitlines()
        start, end = view_range or [1, len(file_lines)]
        end = len(file_lines) if end == -1 else end
        numbered = "\n".join(f"{i:>6}\t{line}" for i, line in enumerate(file_lines[start - 1 : end], start=start))
        return f"Here's the content of {path} with line numbers:\n{numbered}"

    if command == "create":
        if target.exists():
            return f"Error: File {path} already exists"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(file_text or "")
        return f"File created successfully at: {path}"

    if command == "str_replace":
        if not target.exists():
            return f"Error: The path {path} does not exist. Please provide a valid path."
        text = target.read_text()
        count = text.count(old_str)
        if count == 0:
            return f"No replacement was performed, old_str `{old_str}` did not appear verbatim in {path}."
        if count > 1:
            return (
                f"No replacement was performed. Multiple occurrences of old_str `{old_str}` "
                f"in {path}. Please ensure it is unique"
            )
        target.write_text(text.replace(old_str, new_str or "", 1))
        return "The memory file has been edited."

    if command == "insert":
        if not target.exists():
            return f"Error: The path {path} does not exist"
        lines = target.read_text().split("\n")
        if insert_line < 0 or insert_line > len(lines):
            return (
                f"Error: Invalid `insert_line` parameter: {insert_line}. It should be within "
                f"the range of lines of the file: [0, {len(lines)}]"
            )
        lines.insert(insert_line, (insert_text or "").rstrip("\n"))
        target.write_text("\n".join(lines))
        return f"The file {path} has been edited."

    if command == "delete":
        if not target.exists():
            return f"Error: The path {path} does not exist"
        if target == _memory_dir():
            return "Error: cannot delete the /memories root directory"
        shutil.rmtree(target) if target.is_dir() else target.unlink()
        return f"Successfully deleted {path}"

    if command == "rename":
        try:
            source = _resolve(old_path)
            dest = _resolve(new_path)
        except ValueError as exc:
            return f"Error: {exc}"
        if not source.exists():
            return f"Error: The path {old_path} does not exist"
        if dest.exists():
            return f"Error: The destination {new_path} already exists"
        source.rename(dest)
        return f"Successfully renamed {old_path} to {new_path}"

    return f"Error: unknown command {command}"
