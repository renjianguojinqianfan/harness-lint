"""Tests for harness_lint.attribution."""

from __future__ import annotations

import ast

from harness_lint.attribution import (
    validate_rule_attribution,
    validate_ruleset,
    validate_violation,
)
from harness_lint.rules.base import Rule, Violation


class ValidRule(Rule):
    """A rule with full attribution for testing."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="HL001",
            name="Valid",
            severity="Error",
            message_template="msg",
            agente_ref="AGENTS.md §1",
            attribution="Valid attribution",
        )

    def check(self, file_path: str, file_content: str, ast_tree: ast.AST) -> list[Violation] | None:  # noqa: ARG002
        """No-op check for testing."""
        return None


class MissingAgenteRefRule(Rule):
    """A rule missing agente_ref for testing."""

    def check(self, file_path: str, file_content: str, ast_tree: ast.AST) -> list[Violation] | None:  # noqa: ARG002
        """No-op check for testing."""
        return None


class MissingAttributionRule(Rule):
    """A rule missing attribution for testing."""

    def check(self, file_path: str, file_content: str, ast_tree: ast.AST) -> list[Violation] | None:  # noqa: ARG002
        """No-op check for testing."""
        return None


class InvalidAgenteRefRule(Rule):
    """A rule with invalid agente_ref format for testing."""

    def check(self, file_path: str, file_content: str, ast_tree: ast.AST) -> list[Violation] | None:  # noqa: ARG002
        """No-op check for testing."""
        return None


def test_validate_rule_with_full_attribution_passes() -> None:
    """A rule with complete attribution passes validation."""
    rule = ValidRule()
    errors = validate_rule_attribution(rule)
    assert errors == []


def test_validate_rule_missing_agente_ref_fails() -> None:
    """Validation fails when agente_ref is empty."""
    rule = ValidRule()
    object.__setattr__(rule, "agente_ref", "")
    errors = validate_rule_attribution(rule)
    assert any("agente_ref is empty" in e for e in errors)


def test_validate_rule_missing_attribution_fails() -> None:
    """Validation fails when attribution is empty."""
    rule = ValidRule()
    object.__setattr__(rule, "attribution", "")
    errors = validate_rule_attribution(rule)
    assert any("attribution is empty" in e for e in errors)


def test_validate_rule_invalid_agente_ref_format_fails() -> None:
    """Validation fails when agente_ref does not start with 'AGENTS.md'."""
    rule = InvalidAgenteRefRule(
        rule_id="HL004",
        name="InvalidRef",
        severity="Warning",
        message_template="msg",
        agente_ref="README.md §1",
        attribution="Some attribution",
    )
    errors = validate_rule_attribution(rule)
    assert any("must start with 'AGENTS.md'" in e for e in errors)


def test_validate_violation_full_chain_passes() -> None:
    """A violation with full attribution chain passes validation."""
    v = Violation(
        file="test.py",
        line=1,
        column=0,
        rule_id="HL001",
        severity="Error",
        phenomenon="eval used",
        attribution="AI may use eval",
        agente_ref="AGENTS.md §5",
    )
    errors = validate_violation(v)
    assert errors == []


def test_validate_violation_missing_phenomenon_fails() -> None:
    """Validation fails when phenomenon is empty."""
    v = Violation(
        file="test.py",
        line=1,
        column=0,
        rule_id="HL001",
        severity="Error",
        phenomenon="",
        attribution="AI may use eval",
        agente_ref="AGENTS.md §5",
    )
    errors = validate_violation(v)
    assert any("phenomenon is empty" in e for e in errors)


def test_validate_violation_missing_attribution_fails() -> None:
    """Validation fails when attribution is empty."""
    v = Violation(
        file="test.py",
        line=1,
        column=0,
        rule_id="HL001",
        severity="Error",
        phenomenon="eval used",
        attribution="",
        agente_ref="AGENTS.md §5",
    )
    errors = validate_violation(v)
    assert any("attribution is empty" in e for e in errors)


def test_validate_violation_missing_agente_ref_fails() -> None:
    """Validation fails when agente_ref is empty."""
    v = Violation(
        file="test.py",
        line=1,
        column=0,
        rule_id="HL001",
        severity="Error",
        phenomenon="eval used",
        attribution="AI may use eval",
        agente_ref="",
    )
    errors = validate_violation(v)
    assert any("agente_ref is empty" in e for e in errors)


def test_validate_violation_invalid_agente_ref_format_fails() -> None:
    """Validation fails when agente_ref does not start with 'AGENTS.md'."""
    v = Violation(
        file="test.py",
        line=1,
        column=0,
        rule_id="HL001",
        severity="Error",
        phenomenon="eval used",
        attribution="AI may use eval",
        agente_ref="README.md §5",
    )
    errors = validate_violation(v)
    assert any("must start with 'AGENTS.md'" in e for e in errors)


def test_validate_ruleset_multiple_rules() -> None:
    """Validation aggregates errors across multiple rules."""
    bad_ref_rule = ValidRule()
    object.__setattr__(bad_ref_rule, "agente_ref", "")
    bad_attr_rule = ValidRule()
    object.__setattr__(bad_attr_rule, "attribution", "")
    rules = [ValidRule(), bad_ref_rule, bad_attr_rule]
    errors = validate_ruleset(rules)
    assert any("agente_ref is empty" in e for e in errors)
    assert any("attribution is empty" in e for e in errors)


def test_validate_ruleset_empty_rules_passes() -> None:
    """An empty ruleset passes validation."""
    errors = validate_ruleset([])
    assert errors == []
