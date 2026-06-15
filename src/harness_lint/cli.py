"""CLI entry point for Harness-Lint."""

from __future__ import annotations

import typer

from harness_lint.accumulator import PatternWarning
from harness_lint.checker import check, collect_files
from harness_lint.degradation import format_degradation_notice, is_harness_lint_enabled
from harness_lint.pbh_adapter import get_context
from harness_lint.reporter import format_json, format_summary, format_terminal
from harness_lint.rules import (
    HL001EvalRule,
    HL002ExecRule,
    HL003OsSystemRule,
    HL004HardcodedSecretsRule,
    HL201FunctionLengthRule,
    HL202FakeExceptionRule,
    HL301NoDocstringRule,
    HL401RepeatedPatternRule,
    HL402ProtocolConsistencyRule,
)
from harness_lint.rules.base import Rule, Violation

app = typer.Typer()


def _get_default_rules() -> list[Rule]:
    """Return the built-in rule instances."""
    return [
        HL001EvalRule(),
        HL002ExecRule(),
        HL003OsSystemRule(),
        HL004HardcodedSecretsRule(),
        HL201FunctionLengthRule(),
        HL202FakeExceptionRule(),
        HL301NoDocstringRule(),
        HL401RepeatedPatternRule(),
        HL402ProtocolConsistencyRule(),
    ]


def _has_errors(violations: list[Violation]) -> bool:
    """Check if any violation has Error severity."""
    return any(v.severity == "Error" for v in violations)


def _has_warnings(violations: list[Violation]) -> bool:
    """Check if any violation has Warning severity."""
    return any(v.severity == "Warning" for v in violations)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo("harness-lint 0.2.0")
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


def _handle_degradation() -> None:
    """Check if harness-lint is enabled and exit early if not."""
    if is_harness_lint_enabled():
        return
    notice = format_degradation_notice()
    if notice:
        typer.echo(notice)
    else:
        typer.echo("当前未启用 Harness-Lint")
    raise typer.Exit(code=0)


def _format_output(
    violations: list[Violation],
    files_checked: int,
    pattern_warnings: list[PatternWarning],
    fmt: str,
    phase: str | None,
) -> str:
    """Format violations according to the requested output format."""
    if fmt == "json":
        return format_json(violations, files_checked, pattern_warnings, phase=phase)
    if fmt == "summary":
        return format_summary(violations, files_checked, pattern_warnings, phase=phase)
    return format_terminal(violations, files_checked, pattern_warnings, phase=phase)


def _determine_exit_code(violations: list[Violation], strict: bool) -> int:
    """Return the exit code based on violations and strict mode."""
    if _has_errors(violations):
        return 1
    if strict and _has_warnings(violations):
        return 1
    return 0


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
    _handle_degradation()

    context = get_context(path)
    rules = _get_default_rules()
    files = collect_files(path)
    files_checked = len(files)

    violations, pattern_warnings = check(path, context, rules)

    output = _format_output(violations, files_checked, pattern_warnings, fmt, context.phase)
    typer.echo(output)

    raise typer.Exit(code=_determine_exit_code(violations, strict))


def cli() -> None:
    """Entry point for setuptools console script."""
    app()
