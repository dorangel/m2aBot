import os
import sys
from pathlib import Path

import click

from .config import Config
from .agents.orchestrator import Orchestrator


@click.group()
def cli() -> None:
    """m2abot — AI-powered test generation harness.\n
    Uses two adversarial Claude agents to generate and iteratively improve
    tests for any codebase.
    """


@cli.command()
@click.option(
    "--target", "-t",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to the codebase directory to analyze.",
)
@click.option(
    "--output", "-o",
    required=True,
    type=click.Path(file_okay=True, dir_okay=False),
    help="Output path for the generated test file (e.g. tests/test_generated.py).",
)
@click.option(
    "--iterations", "-n",
    default=2,
    show_default=True,
    type=int,
    help="Number of Testing↔Adversarial improvement cycles.",
)
@click.option(
    "--model",
    default="claude-opus-4-6",
    show_default=True,
    help="Claude model ID to use.",
)
@click.option(
    "--extensions",
    default=".py,.js,.ts,.jsx,.tsx",
    show_default=True,
    help="Comma-separated list of file extensions to include.",
)
def run(
    target: str,
    output: str,
    iterations: int,
    model: str,
    extensions: str,
) -> None:
    """Generate and iteratively improve tests for a codebase."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        click.echo(
            "Error: ANTHROPIC_API_KEY environment variable is not set.\n"
            "Export it before running: export ANTHROPIC_API_KEY=sk-ant-...",
            err=True,
        )
        sys.exit(1)

    config = Config(
        target=Path(target),
        output=Path(output),
        iterations=iterations,
        model=model,
        extensions=[e.strip() for e in extensions.split(",") if e.strip()],
        api_key=api_key,
    )

    orchestrator = Orchestrator(config)
    result = orchestrator.run()

    final_tests = result.iteration_results[-1].test_count if result.iteration_results else 0
    click.echo(
        f"\nDone! Generated ~{final_tests} test(s) in "
        f"{result.iterations_run} iteration(s)."
    )


def main() -> None:
    cli()
