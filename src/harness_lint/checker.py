"""Checker engine: file traversal, AST parsing, and rule execution."""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import TYPE_CHECKING

from harness_lint.accumulator import apply_accumulation

if TYPE_CHECKING:
    from harness_lint.accumulator import PatternWarning
    from harness_lint.rules.base import Rule, Violation

_DEFAULT_IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
}


class Context:
    """Simplified context object for phase-aware rule activation."""

    def __init__(
        self,
        phase: str | None = None,
        harness_version: str | None = None,
        hint: str = "",
    ) -> None:
        """Initialize context with optional phase.

        Args:
            phase: The current PBH phase ("plan", "execute", "evaluate", "done", or None).
            harness_version: The harness version from progress.json, if present.
            hint: Human-readable hint based on the current phase.
        """
        self.phase = phase
        self.harness_version = harness_version
        self.hint = hint


def collect_files(path: str) -> list[str]:
    """Recursively collect Python files, applying default ignore patterns.

    Args:
        path: Root directory to scan.

    Returns:
        Sorted list of absolute file paths for all ``.py`` files found
        under *path*, excluding files inside default ignored directories.
    """
    result: list[str] = []
    root = Path(path)

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d not in _DEFAULT_IGNORE_DIRS
        ]
        for filename in filenames:
            if filename.endswith(".py"):
                result.append(str(Path(dirpath) / filename))

    return sorted(result)


def _is_rule_active(rule: Rule, phase: str | None) -> bool:
    """Determine whether a rule is active for the given phase.

    Args:
        rule: The rule to evaluate.
        phase: Current phase ("execute", "evaluate", or None).

    Returns:
        True if the rule should be executed for the given phase.
    """
    if phase is None:
        return True
    return phase in rule.phases


def check(
    path: str, context: Context, rules: list[Rule]
) -> tuple[list[Violation], list[PatternWarning]]:
    """Check all Python files in *path* against activated rules.

    Args:
        path: Root directory to scan.
        context: Phase-aware context controlling rule activation.
        rules: List of rules to (potentially) apply.

    Returns:
        Tuple of (sorted violations, pattern warnings). Violations are
        sorted by file path. Pattern warnings are generated for rules
        whose violation count meets or exceeds the escalation threshold.
        Invalid Python syntax is silently skipped rather than raising.
    """
    files = collect_files(path)
    active_rules = [r for r in rules if _is_rule_active(r, context.phase)]
    all_violations: list[Violation] = []

    for file_path in files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue

        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue

        for rule in active_rules:
            violations = rule.check(file_path, content, tree)
            if violations:
                all_violations.extend(violations)

    sorted_violations = sorted(all_violations, key=lambda v: v.file)
    processed_violations, pattern_warnings = apply_accumulation(
        sorted_violations, phase=context.phase, rules=active_rules
    )
    return processed_violations, pattern_warnings
