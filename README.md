# m2aBot — AI-Powered Test Generation Harness

m2aBot is a drop-in test generation harness powered by Claude.
Point it at any codebase, and two adversarial AI agents collaborate to produce a
thorough, iteratively-improved test suite.

---

## How it works

```
┌─────────────────────────────────────────────────────────────┐
│                        Orchestrator                         │
│                                                             │
│  1. Read target codebase                                    │
│                                                             │
│  ┌──────────────┐   tests    ┌───────────────────────┐     │
│  │              │ ─────────► │                       │     │
│  │   Testing    │            │   Adversarial Agent   │     │
│  │   Agent      │ ◄───────── │                       │     │
│  │              │    gaps    │  Finds what's missing │     │
│  └──────────────┘            └───────────────────────┘     │
│        │  ▲                                                 │
│        │  └──── repeat up to N iterations ─────────────┐   │
│        │                                                │   │
│        ▼  (no high-priority gaps, or iterations done)  │   │
│  Write final tests to disk  ◄──────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### The Testing Agent
Reads the codebase and generates a complete, runnable test suite.
Uses **Claude Opus 4.6 with adaptive thinking** — it reasons about the code before
writing tests, covering happy paths, edge cases, and error conditions.
In later iterations it receives the Adversarial Agent's gap report and adds the
missing scenarios to the existing tests.

### The Adversarial Agent
Reviews the current test suite and hunts for everything the Testing Agent missed:
untested functions, missing boundary values, unsimulated failures, security edge
cases, implicit assumptions, race conditions, and more.
Returns a structured JSON report — each gap has a scenario, a reason it matters,
a priority (`high / medium / low`), and a test hint.

### The Orchestrator
Runs the Testing → Adversarial loop up to `--iterations` times.
Stops early when the Adversarial Agent finds no high-priority gaps.
Prints progress at every step and writes the final tests to the output path.

---

## Quickstart

### Requirements
- Python 3.12+
- An [Anthropic API key](https://console.anthropic.com/)

### 1 — Add m2aBot to your project

**Option A — pip (recommended)**
```bash
pip install git+https://github.com/dorangel/m2aBot.git
```

**Option B — uv**
```bash
uv add git+https://github.com/dorangel/m2aBot.git
```

**Option C — clone and install locally**
```bash
git clone https://github.com/dorangel/m2aBot.git
pip install -e ./m2aBot
```

**Option D — add to your `pyproject.toml` so every team member gets it**
```toml
# pyproject.toml in your project
[project]
dependencies = [
    "m2abot @ git+https://github.com/dorangel/m2aBot.git",
]
```
Then `pip install -e .` or `uv sync`.

### 2 — Set your API key
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### 3 — Run
```bash
# Generate tests for the current directory (output defaults to ./m2atests/)
m2abot run --target .

# Write to a specific file instead of the default output folder
m2abot run --target . --output ./tests/test_generated.py

# Three improvement iterations
m2abot run --target . --output ./tests/test_generated.py --iterations 3

# Only scan Python files
m2abot run --target . --output ./tests/test_generated.py --extensions .py

# Custom model
m2abot run --target . --output ./tests/test_generated.py --model claude-sonnet-4-6
```

---

## CLI reference

```
m2abot run [OPTIONS]

Options:
  -t, --target TEXT       Path to the codebase to analyze  [required]
  -o, --output TEXT       Output directory or .py file  [default: ./m2atests]
  -n, --iterations INT    Number of Testing↔Adversarial cycles  [default: 2]
      --model TEXT        Claude model ID  [default: claude-opus-4-6]
      --extensions TEXT   Comma-separated file extensions to scan
                          [default: .py,.js,.ts,.jsx,.tsx]
  --help                  Show this message and exit.
```

---

## What gets generated

m2aBot writes a single test file to `--output`.
It infers the testing framework from your codebase (pytest, unittest, jest, mocha, etc.)
and matches your existing test conventions.

After each run, stdout shows:
```
[m2abot] Reading codebase from ./src...
[m2abot] Found 12 files

[m2abot] === Iteration 1/2 ===
[m2abot] Testing Agent: generating tests...
[m2abot] Testing Agent: generated 18 test functions
[m2abot] Adversarial Agent: reviewing tests...
[m2abot] Adversarial Agent: found 7 gaps (3 high priority)

[m2abot] === Iteration 2/2 ===
[m2abot] Testing Agent: generating tests...
[m2abot] Testing Agent: generated 24 test functions
[m2abot] Adversarial Agent: reviewing tests...
[m2abot] Adversarial Agent: found 2 gaps (0 high priority)
[m2abot] No high-priority gaps. Stopping early.

[m2abot] Tests written to ./tests/test_generated.py
Done! Generated 24 tests in 2 iterations.
```

---

## Project layout

```
m2abot/
├── agents/
│   ├── testing_agent.py      # Generates tests via Claude
│   ├── adversarial_agent.py  # Finds gaps in the test suite
│   └── orchestrator.py       # Runs the iterative loop
├── core/
│   ├── codebase_reader.py    # Walks & reads the target directory
│   └── prompts.py            # All prompt templates
├── cli.py                    # `m2abot run` entry point
└── config.py                 # Dataclass-based configuration

vimeo_example/                # Example tests generated by m2aBot
                              # (API + UI tests for Restful Booker)
```

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |

---

## Limitations & notes

- The generated test file is a **starting point**, not a finished product. Review it, remove tests that don't apply, and add domain-specific fixtures.
- Large codebases are truncated to stay within the model's context window. Point `--target` at the specific sub-directory you care about for best results.
- Each run makes 2–6 Claude API calls (depending on `--iterations`). With Opus 4.6 this costs approximately $0.10–$0.50 per run for a typical small codebase.
- Generated tests use the conventions inferred from your codebase. If no existing tests are found, pytest is assumed for Python projects.
