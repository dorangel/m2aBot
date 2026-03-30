from pathlib import Path
from ..config import Config


def read_codebase(config: Config) -> dict[str, str]:
    """Walk *config.target* and return ``{relative_path: content}``.

    Files are filtered by extension, excluded directories, and max size.
    Content is truncated at *config.max_codebase_chars* total to stay within
    the model's context window.
    """
    files: dict[str, str] = {}
    target = Path(config.target).resolve()
    exclude = set(config.exclude_dirs)

    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        # Skip excluded directories
        if any(part in exclude for part in path.parts):
            continue
        # Filter by extension
        if path.suffix not in config.extensions:
            continue
        # Skip oversized files
        if path.stat().st_size > config.max_file_size_kb * 1024:
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        rel = str(path.relative_to(target))
        files[rel] = content

    return _trim_to_budget(files, config.max_codebase_chars)


def _trim_to_budget(
    files: dict[str, str], max_chars: int
) -> dict[str, str]:
    """Drop files (largest first) until the total character count fits within
    *max_chars*.  Small files are always preferred over large ones."""
    total = sum(len(v) for v in files.values())
    if total <= max_chars:
        return files

    # Sort by size descending so we drop the biggest files first
    by_size = sorted(files.items(), key=lambda kv: len(kv[1]), reverse=True)
    result: dict[str, str] = {}
    used = 0
    dropped: list[str] = []

    for path, content in reversed(by_size):  # smallest first
        if used + len(content) <= max_chars:
            result[path] = content
            used += len(content)
        else:
            dropped.append(path)

    if dropped:
        note = (
            f"\n\n# [m2abot] NOTE: {len(dropped)} file(s) were omitted because "
            f"the codebase exceeded the context budget:\n"
            + "\n".join(f"#   {p}" for p in dropped)
        )
        # Prepend the note as a pseudo-file
        result = {"__budget_note__.txt": note, **result}

    return result


def format_for_prompt(codebase: dict[str, str]) -> str:
    """Render the codebase dict as a human-readable string for inclusion in
    a prompt."""
    parts: list[str] = []
    for path, content in sorted(codebase.items()):
        parts.append(f"### FILE: {path}\n\n{content}")
    return "\n\n---\n\n".join(parts)
