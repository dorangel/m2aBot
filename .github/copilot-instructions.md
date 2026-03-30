---
name: m2aBot Workspace Instructions
description: "Workspace-scoped guidance for developing features and working with the m2aBot codebase."
---

# m2aBot Workspace Instructions

## Quick Start

This is the **m2aBot** repository — an automated test generation system using adversarial Claude agents.

For help with:
- **Planning or implementing features** → Use `/feature-developer` agent
- **Understanding code patterns** → Search `.github/agents/feature-developer.agent.md` for architecture context
- **Running tests** → See README.md or run `uv run pytest`
- **Testing the system** → See vimeo_example/CLAUDE.md

## Project Layout

```
m2abot/                 # Main package
  agents/               # Testing & Adversarial agents + Orchestrator
  core/                 # Codebase reader + prompt builders
  cli.py                # CLI entry point
  config.py             # Configuration

vimeo_example/          # Example/reference implementation
  tests/                # API and UI test suites
  pages/                # Playwright page objects
  api/                  # API clients
```

## Common Tasks

### Add a new feature
1. **Use the feature-developer agent**: Type `/feature-developer` in chat and describe what you want to build
2. **Explore patterns**: The agent will help you find similar implementations

### Run tests
```bash
uv run pytest vimeo_example/tests/
uv run pytest vimeo_example/tests/ui/ --headed
```

### Generate tests for a project
```bash
export ANTHROPIC_API_KEY=sk-ant-...
m2abot run --target ./src --output ./tests/test_generated.py
```

### Install from GitHub
```bash
uv add git+https://github.com/dorangel/m2aBot.git
```

## Key Concepts

- **Adversarial Loop** — Testing Agent writes tests; Adversarial Agent finds gaps; Orchestrator loops
- **Token Budgeting** — Large codebases are auto-trimmed to fit context (~50K tokens)
- **Adaptive Thinking** — Agents use Claude's thinking mode for reasoning-heavy tasks
- **JSON Parsing** — Adversarial Agent output has fallback parsing for robustness (direct → strip fences → regex)

## Conventions

- Type hints: Use them throughout (Python 3.10+)
- Docstrings: Explain agent prompts and key logic
- Testing: All features tested in `vimeo_example/tests/` or new feature test directories
- Prompts: Centralized in `m2abot/core/prompts.py`

---

**Tip:** For detailed feature development guidance, invoke the `/feature-developer` agent.
