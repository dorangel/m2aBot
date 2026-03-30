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
        """Return the complete test file as a string.

        Parameters
        ----------
        codebase:
            ``{relative_path: content}`` dict produced by the codebase reader.
        existing_tests:
            The test file from the previous iteration (``None`` on the first run).
        adversarial_gaps:
            Structured gap list returned by the Adversarial Agent.
        iteration:
            Current loop counter (used only for the prompt header).
        """
        user_prompt = build_testing_prompt(
            codebase=codebase,
            existing_tests=existing_tests,
            adversarial_gaps=adversarial_gaps,
            iteration=iteration,
        )

        # Stream the response — test files can be large and streaming prevents
        # HTTP timeouts while also letting the model think longer with adaptive
        # thinking enabled.
        with self.client.messages.stream(
            model=self.config.model,
            max_tokens=16_000,
            thinking={"type": "adaptive"},
            system=TESTING_AGENT_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            message = stream.get_final_message()

        return self._extract_text(message)

    @staticmethod
    def _extract_text(message: anthropic.types.Message) -> str:
        """Return only the text blocks from a response that may also contain
        thinking blocks."""
        return "\n".join(
            block.text
            for block in message.content
            if block.type == "text"
        ).strip()
