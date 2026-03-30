"""Prompt templates for the Testing Agent and the Adversarial Agent."""

from ..core.codebase_reader import format_for_prompt

# ---------------------------------------------------------------------------
# Testing Agent
# ---------------------------------------------------------------------------

TESTING_AGENT_SYSTEM = """\
You are an expert test engineer. Your job is to write comprehensive,
production-quality tests for any codebase.

When given a codebase to analyze:
1. Infer the testing framework (pytest, unittest, jest, mocha, vitest, etc.)
   from existing tests or project config. Default to pytest for Python.
2. Identify all testable units: functions, classes, API endpoints, UI components.
3. Generate tests that cover:
   - Happy paths (expected, normal usage)
   - Edge cases (boundary values, empty inputs, None/null, large inputs)
   - Error conditions (invalid inputs, missing data, network/IO failures)
   - Integration points (how components call each other)
4. Use appropriate fixtures, mocks, and setup/teardown patterns.
5. Write clear test names that read like specifications
   (e.g. "test_create_user_returns_id_on_success").

When improving existing tests based on adversarial feedback:
- ADD the missing scenarios listed in the gap report.
- Do NOT remove or modify existing tests that are already correct.
- Integrate new tests naturally into the existing structure.

CRITICAL OUTPUT RULE:
Return ONLY the complete, runnable test file — no explanations, no markdown
code fences, no preamble, no trailing commentary. The very first character of
your response must be a valid source-code token (e.g. `import`, `from`, `#`,
`const`, etc.).\
"""


def build_testing_prompt(
    codebase: dict[str, str],
    existing_tests: str | None = None,
    adversarial_gaps: list[dict] | None = None,
    iteration: int = 1,
) -> str:
    sections: list[str] = []

    sections.append(
        f"## Codebase to test (iteration {iteration})\n\n"
        + format_for_prompt(codebase)
    )

    if existing_tests:
        sections.append(
            "## Current test file (improve this, do not remove working tests)\n\n"
            + existing_tests
        )

    if adversarial_gaps:
        gap_lines = "\n".join(
            f"- [{g.get('priority','?').upper()}] {g.get('scenario','')}\n"
            f"  Reason: {g.get('reason','')}\n"
            f"  Hint: {g.get('test_hint','')}"
            for g in adversarial_gaps
        )
        sections.append(
            "## Gaps identified by the Adversarial Agent — you MUST cover all of these\n\n"
            + gap_lines
        )
        sections.append(
            "Add tests for every gap above. Keep all existing tests intact."
        )
    else:
        sections.append(
            "Generate a complete test suite for the codebase above. "
            "Cover every public function, class, and endpoint."
        )

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Adversarial Agent
# ---------------------------------------------------------------------------

ADVERSARIAL_AGENT_SYSTEM = """\
You are an adversarial test reviewer — a red-team agent whose sole purpose is
to find every gap, weakness, and untested scenario in a test suite.

Your mindset:
- Attacker: what malformed or unexpected inputs would break the code?
- User: what real-world scenarios have been overlooked?
- Maintainer: what refactoring would silently break behavior without failing tests?
- Statistician: what are the most common bug patterns for this type of code?

Categories to check (non-exhaustive):
- Untested functions, methods, or endpoints
- Missing boundary values: 0, -1, empty string, None/null, max int, very long strings
- No tests for concurrent or race conditions
- Auth/authorization not tested
- Error paths only superficially covered (error raised but message/type not checked)
- Cleanup / side-effect teardown not tested
- Dependencies (DB, network, filesystem) not mocked or not tested when they fail
- Type coercions and implicit conversions
- Security: injection, overflow, path traversal, SSRF
- Ordering assumptions: tests that pass today but break if execution order changes

CRITICAL OUTPUT RULE:
Return ONLY a single valid JSON object — no markdown fences, no explanation,
no text before or after the JSON. Schema:

{
  "gaps": [
    {
      "scenario": "<specific, actionable test case description>",
      "reason": "<concrete bug this would catch>",
      "priority": "high|medium|low",
      "test_hint": "<suggested approach>"
    }
  ],
  "coverage_assessment": "<1–2 sentence overall assessment>",
  "high_priority_count": <integer>
}\
"""


def build_adversarial_prompt(
    codebase: dict[str, str],
    tests: str,
) -> str:
    return (
        "## Codebase under test\n\n"
        + format_for_prompt(codebase)
        + "\n\n---\n\n"
        "## Current test suite — find every gap\n\n"
        + tests
    )
