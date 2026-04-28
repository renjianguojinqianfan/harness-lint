"""Tests for harness_lint.rules.base."""

import ast
from dataclasses import FrozenInstanceError

import pytest

from harness_lint.rules.base import Rule, Violation


class DummyRule(Rule):
    """Concrete rule for testing purposes."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="HL999",
            name="Dummy",
            severity="Warning",
            message_template="Found {thing}",
            agente_ref="AGENTS.md §1",
            attribution="Test attribution",
        )

    def check(self, file_path: str, file_content: str, ast_tree: ast.AST) -> list[Violation] | None:  # noqa: ARG002
        return None


def test_violation_creation() -> None:
    """A Violation can be created with all required fields."""
    v = Violation(
        file="src/example.py",
        line=10,
        column=4,
        rule_id="HL001",
        severity="Error",
        phenomenon="禁止使用 eval()",
        attribution="AI 可能用 eval 实现灵活执行，导致代码注入",
        agente_ref="AGENTS.md §5 Critical Rules",
    )
    assert v.file == "src/example.py"
    assert v.line == 10
    assert v.column == 4
    assert v.rule_id == "HL001"
    assert v.severity == "Error"
    assert v.phenomenon == "禁止使用 eval()"
    assert v.attribution == "AI 可能用 eval 实现灵活执行，导致代码注入"
    assert v.agente_ref == "AGENTS.md §5 Critical Rules"


def test_violation_is_frozen() -> None:
    """Violation instances must be immutable."""
    v = Violation(
        file="src/example.py",
        line=1,
        column=0,
        rule_id="HL001",
        severity="Error",
        phenomenon="x",
        attribution="y",
        agente_ref="z",
    )
    with pytest.raises(FrozenInstanceError):
        v.line = 99


def test_rule_is_abstract() -> None:
    """Rule cannot be instantiated directly because check() is abstract."""
    with pytest.raises(TypeError, match="abstract"):
        Rule(
            rule_id="HL999",
            name="Dummy",
            severity="Error",
            message_template="{thing} is bad",
            phases=["execute", "evaluate"],
            agente_ref="AGENTS.md §1",
            attribution="Test attribution",
        )


def test_rule_concrete_subclass() -> None:
    """A concrete subclass can be instantiated and used."""
    rule = DummyRule()
    assert rule.rule_id == "HL999"
    assert rule.name == "Dummy"
    assert rule.severity == "Warning"
    assert rule.message_template == "Found {thing}"
    assert rule.phases == ["execute", "evaluate"]
    assert rule.agente_ref == "AGENTS.md §1"
    assert rule.attribution == "Test attribution"

    tree = ast.parse("x = 1\n")
    result = rule.check("dummy.py", "x = 1\n", tree)
    assert result is None


def test_rule_default_phases() -> None:
    """Default phases include both execute and evaluate."""
    rule = DummyRule()
    assert rule.phases == ["execute", "evaluate"]


def test_rule_post_init_rejects_empty_agente_ref() -> None:
    """Rule must reject empty agente_ref during instantiation."""

    class BadRule(Rule):
        def check(
            self, file_path: str, file_content: str, ast_tree: ast.AST,
        ) -> list[Violation] | None:  # noqa: ARG002
            return None

    with pytest.raises(ValueError, match="agente_ref must not be empty"):
        BadRule(
            rule_id="HL999",
            name="Bad",
            severity="Error",
            message_template="msg",
            agente_ref="",
            attribution="Some attribution",
        )


def test_rule_post_init_rejects_empty_attribution() -> None:
    """Rule must reject empty attribution during instantiation."""

    class BadRule(Rule):
        def check(
            self, file_path: str, file_content: str, ast_tree: ast.AST,
        ) -> list[Violation] | None:  # noqa: ARG002
            return None

    with pytest.raises(ValueError, match="attribution must not be empty"):
        BadRule(
            rule_id="HL999",
            name="Bad",
            severity="Error",
            message_template="msg",
            agente_ref="AGENTS.md §1",
            attribution="",
        )


def test_rule_post_init_accepts_valid_attribution() -> None:
    """Rule accepts valid agente_ref and attribution."""

    class GoodRule(Rule):
        def check(
            self, file_path: str, file_content: str, ast_tree: ast.AST,
        ) -> list[Violation] | None:  # noqa: ARG002
            return None

    rule = GoodRule(
        rule_id="HL001",
        name="Good",
        severity="Warning",
        message_template="ok",
        agente_ref="AGENTS.md §2",
        attribution="Valid attribution",
    )
    assert rule.agente_ref == "AGENTS.md §2"
    assert rule.attribution == "Valid attribution"


def test_create_violation_prefills_metadata() -> None:
    """_create_violation should pre-fill rule metadata."""
    rule = DummyRule()
    v = rule._create_violation(
        file="src/test.py",
        line=10,
        column=4,
        phenomenon="Something happened",
    )
    assert v.file == "src/test.py"
    assert v.line == 10
    assert v.column == 4
    assert v.rule_id == "HL999"
    assert v.severity == "Warning"
    assert v.phenomenon == "Something happened"
    assert v.attribution == "Test attribution"
    assert v.agente_ref == "AGENTS.md §1"
