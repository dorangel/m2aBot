from dataclasses import dataclass, field
from pathlib import Path

import anthropic

from ..config import Config
from ..core.codebase_reader import read_codebase
from .testing_agent import TestingAgent
from .adversarial_agent import AdversarialAgent


@dataclass
class IterationResult:
    iteration: int
    test_count: int
    gaps: list[dict]
    high_priority_gaps: int


@dataclass
class OrchestratorResult:
    tests: str
    iterations_run: int
    output_path: Path
    iteration_results: list[IterationResult] = field(default_factory=list)


class Orchestrator:
    """Drives the Testing ↔ Adversarial improvement loop.

    Flow
    ----
    1. Read the target codebase.
    2. Testing Agent → initial test suite.
    3. For each remaining iteration:
       a. Adversarial Agent reviews the tests → gap report.
       b. If no high-priority gaps remain → stop early.
       c. Testing Agent improves tests using the gap report.
    4. Write the final test file to *config.output*.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.api_key)
        self.testing_agent = TestingAgent(self.client, config)
        self.adversarial_agent = AdversarialAgent(self.client, config)

    def run(self) -> OrchestratorResult:
        self._log(f"Reading codebase from {self.config.target} ...")
        codebase = read_codebase(self.config)
        self._log(f"Found {len(codebase)} file(s)")

        tests: str | None = None
        iteration_results: list[IterationResult] = []

        for i in range(1, self.config.iterations + 1):
            self._log(f"\n=== Iteration {i}/{self.config.iterations} ===")

            # -- Testing Agent --
            self._log("Testing Agent: generating tests ...")
            prev_gaps = iteration_results[-1].gaps if iteration_results else None
            tests = self.testing_agent.generate_tests(
                codebase=codebase,
                existing_tests=tests,
                adversarial_gaps=prev_gaps,
                iteration=i,
            )
            test_count = tests.count("def test_") + tests.count("it(") + tests.count("test(")
            self._log(f"Testing Agent: generated ~{test_count} test function(s)")

            # -- Adversarial Agent --
            self._log("Adversarial Agent: reviewing tests ...")
            gaps = self.adversarial_agent.find_gaps(codebase=codebase, tests=tests)
            high = sum(1 for g in gaps if g.get("priority") == "high")
            self._log(
                f"Adversarial Agent: found {len(gaps)} gap(s) — {high} high priority"
            )

            iteration_results.append(
                IterationResult(
                    iteration=i,
                    test_count=test_count,
                    gaps=gaps,
                    high_priority_gaps=high,
                )
            )

            if high == 0:
                self._log("No high-priority gaps remaining. Stopping early.")
                break

        # Write output
        assert tests is not None, "No tests were generated"
        output_path = Path(self.config.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(tests, encoding="utf-8")
        self._log(f"\nTests written to {output_path}")

        return OrchestratorResult(
            tests=tests,
            iterations_run=len(iteration_results),
            output_path=output_path,
            iteration_results=iteration_results,
        )

    @staticmethod
    def _log(message: str) -> None:
        print(f"[m2abot] {message}", flush=True)
