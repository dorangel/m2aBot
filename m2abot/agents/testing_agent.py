import re
import anthropic
from ..config import Config
from ..core.prompts import TESTING_AGENT_SYSTEM, build_testing_prompt


class TestingAgent:
    """Generates a runnable test suite from a codebase.

    Uses Claude Opus 4.6 with adaptive thinking and streaming so that large
    test files are produced without hitting HTTP timeouts.
    """

    def __init__(self, client: anthropic.Anthropic, config: Config) -> None:
        self.client = client
        self.config = config

    def generate_tests(
        self,
        codebase: dict[str, str],
        existing_tests: str | None = None,
        adversarial_gaps: list[dict] | None = None,
        iteration: int = 1,
    ) -> str:
        """Return the complete test file as a string."""
        # Inject max_tests into the system prompt at call time
        system = TESTING_AGENT_SYSTEM.format(max_tests=self.config.max_tests)

        user_prompt = build_testing_prompt(
            codebase=codebase,
            existing_tests=existing_tests,
            adversarial_gaps=adversarial_gaps,
            iteration=iteration,
            max_tests=self.config.max_tests,
        )

        with self.client.messages.stream(
            model=self.config.model,
            max_tokens=16_000,
            thinking={"type": "adaptive"},
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            message = stream.get_final_message()

        return self._extract_text(message)

    @staticmethod
    def extract_test_names(tests: str) -> list[str]:
        """Parse test function / method names from the generated file.

        Handles pytest-style ``def test_foo``, jest-style ``it('...')`` and
        ``test('...')``, and vitest/mocha ``it("...")``.
        """
        names: list[str] = []
        # Python / Java / Go: def test_foo or func TestFoo
        names += re.findall(r"(?:def|func)\s+(test\w+|Test\w+)", tests, re.IGNORECASE)
        # JS/TS: it('description') or test('description')
        names += re.findall(r"""(?:it|test)\s*\(\s*['"]([^'"]{3,60})['"]""", tests)
        return names

    @staticmethod
    def _extract_text(message: anthropic.types.Message) -> str:
        return "\n".join(
            block.text for block in message.content if block.type == "text"
        ).strip()
