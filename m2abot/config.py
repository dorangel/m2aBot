from dataclasses import dataclass, field
from pathlib import Path

# Directories that are never useful to scan
DEFAULT_EXCLUDE_DIRS: list[str] = [
    ".venv", "venv", ".env",
    "node_modules",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".git", ".hg", ".svn",
    "dist", "build", "target",
    ".idea", ".vscode",
]

DEFAULT_EXTENSIONS: list[str] = [".py", ".js", ".ts", ".jsx", ".tsx"]


@dataclass
class Config:
    target: Path
    output: Path
    iterations: int = 2
    model: str = "claude-opus-4-6"
    extensions: list[str] = field(default_factory=lambda: list(DEFAULT_EXTENSIONS))
    exclude_dirs: list[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDE_DIRS))
    api_key: str | None = None
    # Hard cap on the number of test functions the Testing Agent may generate
    max_tests: int = 20
    # Files larger than this (KB) are skipped to keep prompts manageable
    max_file_size_kb: int = 150
    # Approximate upper bound on codebase content sent to the model
    max_codebase_chars: int = 200_000
