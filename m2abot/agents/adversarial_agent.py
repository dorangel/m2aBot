import json
import re
import anthropic
from ..config import Config
from ..core.prompts import ADVERSARIAL_AGENT_SYSTEM, build_adversarial_prompt


class AdversarialAgent:
    """Reviews a test suite and returns a structured list of gaps.

    Uses Claude Opus 4.6 with adaptive thinking so the model can reason
    carefully before deciding what is and isn't covered.
    """

    def __init__(self, client: anthropic.Anthropic, config: Config) -> None:
        self.client = client
        self.config = config

    def find_gaps(
        self,
        codebase: dict[str, str],
        tests: str,
    ) -> list[dict]:
        """Return a list of gap dicts, each with keys:
        ``scenario``, ``reason``, ``priority``, ``test_hint``.

        Returns an empty list if parsing fails or no gaps are found.
        """
        user_prompt = build_adversarial_prompt(codebase=codebase, tests=tests)

        with self.client.messages.stream(
            model=self.config.model,
            max_tokens=8_000,
            thinking={"type": "adaptive"},
            system=ADVERSARIAL_AGENT_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            message = stream.get_final_message()

        raw = "\n".join(
            block.text for block in message.content if block.type == "text"
        ).strip()

        return self._parse_gaps(raw)

    @staticmethod
    def _parse_gaps(raw: str) -> list[dict]:
        """Parse the JSON response.  Falls back to regex extraction if the
        model wraps the JSON in markdown fences."""
        # Try direct parse first
        try:
            data = json.loads(raw)
            return data.get("gaps", [])
        except json.JSONDecodeError:
            pass

        # Strip markdown code fences and retry
        stripped = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        stripped = re.sub(r"\s*```$", "", stripped, flags=re.MULTILINE).strip()
        try:
            data = json.loads(stripped)
            return data.get("gaps", [])
        except json.JSONDecodeError:
            pass

        # Last resort: extract the first {...} block
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                return data.get("gaps", [])
            except json.JSONDecodeError:
                pass

        return []
