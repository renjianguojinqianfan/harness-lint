"""CLI entry point for Harness-Lint."""

from __future__ import annotations

import typer

from harness_lint.checker import check, collect_files
from harness_lint.degradation import format_degradation_notice, is_harness_lint_enabled
from harness_lint.pbh_adapter import get_context
from harness_lint.reporter import format_json, format_summary, format_terminal
from harness_lint.rules import HL001EvalRule, HL201FunctionLengthRule
from harness_lint.rules.base import Rule, Violation

app = typer.Typer()


def _get_default_rules() -> list[Rule]:
    """Return the built-in rule instances."""
    return [HL001EvalRule(), HL201FunctionLengthRule()]


def _has_errors(violations: list[Violation]) -> bool:
    """Check if any violation has Error severity."""
    return any(v.severity == "Error" for v in violations)


def _has_warnings(violations: list[Violation]) -> bool:
    """Check if any violation has Warning severity."""
    return any(v.severity == "Warning" for v in violations)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo("harness-lint 0.1.0")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit.",
        is_eager=True,
        callback=version_callback,
    ),
) -> None:
    """Harness-Lint CLI."""


@app.command()
def run(
    path: str = typer.Argument(".", help="Target directory to lint."),
    fmt: str = typer.Option(
        "terminal",
        "--format",
        help="Output format: terminal, json, summary.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Treat warnings as errors for exit code.",
    ),
) -> None:
    """Run Harness-Lint against the given path."""
    # Degradation check
    if not is_harness_lint_enabled():
        notice = format_degradation_notice()
        if notice:
            typer.echo(notice)
        else:
            typer.echo("当前未启用 Harness-Lint")
        raise typer.Exit(code=0)

    # Build context and rules
    context = get_context(path)
    rules = _get_default_rules()

    # Collect files and run checker
    files = collect_files(path)
    files_checked = len(files)

    violations, pattern_warnings = check(path, context, rules)

    # Format output
    if fmt == "json":
        output = format_json(
            violations, files_checked, pattern_warnings, phase=context.phase
        )
    elif fmt == "summary":
        output = format_summary(
            violations, files_checked, pattern_warnings, phase=context.phase
        )
    else:
        output = format_terminal(
            violations, files_checked, pattern_warnings, phase=context.phase
        )

    typer.echo(output)

    # Exit code
    if _has_errors(violations):
        raise typer.Exit(code=1)
    if strict and _has_warnings(violations):
        raise typer.Exit(code=1)
    raise typer.Exit(code=0)


def cli() -> None:
    """Entry point for setuptools console script."""
    app()
