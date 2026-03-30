# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

m2aBot is an installable Python harness that generates tests for any codebase using two
adversarial Claude agents: a **Testing Agent** that writes tests and an **Adversarial Agent**
that finds gaps. An **Orchestrator** runs them in a loop until no high-priority gaps remain.

## Setup & Commands

```bash
# Install the package and its dependencies
uv sync

# Run the CLI against a codebase
m2abot run --target ./path/to/src --output ./tests/test_generated.py

# Or via uv
uv run m2abot run --target ./path/to/src --output ./tests/test_generated.py

# Run the vimeo_example tests (API + UI)
uv run pytest vimeo_example/tests/api/
uv run pytest vimeo_example/tests/ui/ --headed
```

Requires `ANTHROPIC_API_KEY` to be set in the environment.

## Package Layout

```
m2abot/                         # Installable Python package
  agents/
    testing_agent.py            # Calls Claude → generates test file
    adversarial_agent.py        # Calls Claude → returns JSON gap list
    orchestrator.py             # Runs Testing↔Adversarial loop, writes output
  core/
    codebase_reader.py          # Walks target dir, trims to context budget
    prompts.py                  # All system prompts and user prompt builders
  cli.py                        # `m2abot run` click entry point
  config.py                     # Config dataclass (target, output, model, etc.)

vimeo_example/                  # Example usage: tests for a real site
  api/booking_client.py         # ObjectsClient for restful-api.dev
  api/user_client.py            # UserApiClient for practicesoftwaretesting.com
  pages/                        # Playwright page objects
  tests/                        # pytest test suites
```

## Architecture Notes

- Both agents use `claude-opus-4-6` with `thinking: {"type": "adaptive"}` + streaming.
  Adaptive thinking lets Claude reason before writing; streaming prevents HTTP timeouts
  on long outputs.
- The Adversarial Agent outputs structured JSON. `adversarial_agent._parse_gaps()` has
  three fallback levels (direct JSON parse → strip fences → regex extract) to handle
  models that wrap output in markdown.
- The Orchestrator stops early when `high_priority_count == 0` rather than always
  running all `--iterations`. This saves API cost on codebases that are already
  well-tested.
- `codebase_reader._trim_to_budget()` drops the largest files first when the codebase
  exceeds `max_codebase_chars` (200K chars ≈ ~50K tokens). A note is injected into the
  prompt listing which files were omitted.
- The `[tool.pytest.ini_options] testpaths` points at `vimeo_example/tests` so
  `uv run pytest` only runs the example tests, not the `m2abot` package itself.

## Adding m2aBot to another project (via GitHub)

```bash
pip install git+https://github.com/dorangel/m2aBot.git
# or
uv add git+https://github.com/dorangel/m2aBot.git
```

Then:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
m2abot run --target ./src --output ./tests/test_generated.py
```
