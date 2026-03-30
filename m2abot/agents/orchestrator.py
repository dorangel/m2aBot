import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import anthropic

from ..config import Config
from ..core.codebase_reader import read_codebase
from .testing_agent import TestingAgent
from .adversarial_agent import AdversarialAgent

# How long to wait (seconds) between rate-limit retries when the API doesn't
# send a Retry-After header.
_DEFAULT_RETRY_WAIT = 60
_MAX_RATE_LIMIT_RETRIES = 3


@dataclass
class IterationResult:
    iteration: int
    test_names: list[str]
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

    Resilience
    ----------
    After every agent call the current state is written to a checkpoint file
    (``<output_dir>/.m2abot_checkpoint.json``).  If the run is interrupted by a
    rate-limit or any other transient error, the checkpoint preserves the work
    done so far and the final partial test file is kept on disk.

    Rate limits are retried up to ``_MAX_RATE_LIMIT_RETRIES`` times with the
    wait time taken from the ``Retry-After`` response header (defaulting to
    ``_DEFAULT_RETRY_WAIT`` seconds).
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.api_key)
        self.testing_agent = TestingAgent(self.client, config)
        self.adversarial_agent = AdversarialAgent(self.client, config)
        self._output_path: Path | None = None  # resolved lazily

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> OrchestratorResult:
        self._log(f"Reading codebase from {self.config.target} ...")
        codebase = read_codebase(self.config)
        self._log(f"Found {len(codebase)} file(s)")

        output_path = self._resolve_output_path()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path = output_path
        self._log(f"Output → {output_path}")

        tests: str | None = None
        iteration_results: list[IterationResult] = []

        for i in range(1, self.config.iterations + 1):
            self._log(f"\n=== Iteration {i}/{self.config.iterations} ===")

            # -- Testing Agent --
            self._log("Testing Agent: generating tests ...")
            prev_gaps = iteration_results[-1].gaps if iteration_results else None
            tests = self._call_with_rate_limit_retry(
                "Testing Agent",
                self.testing_agent.generate_tests,
                codebase=codebase,
                existing_tests=tests,
                adversarial_gaps=prev_gaps,
                iteration=i,
            )

            # Save immediately so work is not lost if Adversarial Agent fails
            output_path.write_text(tests, encoding="utf-8")

            test_names = TestingAgent.extract_test_names(tests)
            self._log(f"Testing Agent: wrote {len(test_names)} test(s)")
            for name in test_names:
                self._log(f"  → {name}")

            self._save_checkpoint(
                iteration=i,
                tests=tests,
                gaps=prev_gaps or [],
                output_path=output_path,
            )

            # -- Adversarial Agent --
            self._log("Adversarial Agent: reviewing tests ...")
            gaps = self._call_with_rate_limit_retry(
                "Adversarial Agent",
                self.adversarial_agent.find_gaps,
                codebase=codebase,
                tests=tests,
            )
            high = sum(1 for g in gaps if g.get("priority") == "high")
            self._log(
                f"Adversarial Agent: found {len(gaps)} gap(s) — {high} high priority"
            )
            for g in gaps:
                pri = g.get("priority", "?").upper()
                self._log(f"  [{pri}] {g.get('scenario', '')}")

            self._save_checkpoint(
                iteration=i,
                tests=tests,
                gaps=gaps,
                output_path=output_path,
            )

            iteration_results.append(
                IterationResult(
                    iteration=i,
                    test_names=test_names,
                    gaps=gaps,
                    high_priority_gaps=high,
                )
            )

            if high == 0:
                self._log("No high-priority gaps remaining. Stopping early.")
                break

        assert tests is not None, "No tests were generated"
        # Final write (already done after last Testing Agent call, but be explicit)
        output_path.write_text(tests, encoding="utf-8")
        self._log(f"\nTests written to {output_path}")

        return OrchestratorResult(
            tests=tests,
            iterations_run=len(iteration_results),
            output_path=output_path,
            iteration_results=iteration_results,
        )

    # ------------------------------------------------------------------
    # Rate-limit retry wrapper
    # ------------------------------------------------------------------

    def _call_with_rate_limit_retry(self, agent_name: str, fn, **kwargs):
        """Call *fn* with keyword args, retrying on ``RateLimitError``.

        On each rate-limit hit the current checkpoint is saved so work is not
        lost, then we wait for the period specified in the ``Retry-After``
        header before retrying.
        """
        for attempt in range(1, _MAX_RATE_LIMIT_RETRIES + 1):
            try:
                return fn(**kwargs)
            except anthropic.RateLimitError as exc:
                if attempt == _MAX_RATE_LIMIT_RETRIES:
                    self._log(
                        f"{agent_name}: rate limit exceeded after "
                        f"{_MAX_RATE_LIMIT_RETRIES} retries. "
                        f"Partial work is saved in the checkpoint. "
                        f"Re-run to resume."
                    )
                    raise

                wait = _DEFAULT_RETRY_WAIT
                try:
                    wait = int(exc.response.headers.get("retry-after", wait))
                except Exception:
                    pass

                self._log(
                    f"{agent_name}: rate limit hit (attempt {attempt}/"
                    f"{_MAX_RATE_LIMIT_RETRIES}). "
                    f"Checkpoint saved. Retrying in {wait}s ..."
                )
                time.sleep(wait)

    # ------------------------------------------------------------------
    # Output path resolution
    # ------------------------------------------------------------------

    def _resolve_output_path(self) -> Path:
        """Return the concrete .py file path for the generated tests.

        If *config.output* already ends in ``.py`` it is used as-is.
        Otherwise it is treated as a directory and a timestamped filename is
        generated inside it:  ``test_<target_name>_YYYYMMDD_HHMMSS.py``
        """
        out = Path(self.config.output)
        if out.suffix == ".py":
            return out

        target_name = Path(self.config.target).resolve().name.replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return out / f"test_{target_name}_{timestamp}.py"

    # ------------------------------------------------------------------
    # Checkpointing
    # ------------------------------------------------------------------

    def _save_checkpoint(
        self,
        iteration: int,
        tests: str,
        gaps: list[dict],
        output_path: Path,
    ) -> None:
        """Persist current state to ``<output_dir>/.m2abot_checkpoint.json``."""
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "target": str(self.config.target),
            "iteration": iteration,
            "output_path": str(output_path),
            "gaps": gaps,
            # Store only the test names, not the full file, to keep the JSON small
            "test_names": TestingAgent.extract_test_names(tests),
        }
        checkpoint_path = output_path.parent / ".m2abot_checkpoint.json"
        checkpoint_path.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    @staticmethod
    def _log(message: str) -> None:
        print(f"[m2abot] {message}", flush=True)
