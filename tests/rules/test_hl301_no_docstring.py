"""Tests for HL301: Public functions without docstring."""

from __future__ import annotations

import ast

from harness_lint.attribution import validate_violation
from harness_lint.rules.hl301_no_docstring import HL301NoDocstringRule


class TestHL301NoDocstringRule:
    """Tests for the HL301 public function docstring detection rule."""

    def test_public_func_no_docstring_detected(self) -> None:
        """A public function without docstring should trigger."""
        code = "def public_func(): pass\n"
        tree = ast.parse(code)
        rule = HL301NoDocstringRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.severity == "Info"
        assert v.rule_id == "HL301"
        assert "public_func" in v.phenomenon

    def test_public_func_with_docstring_not_detected(self) -> None:
        """A public function with docstring should NOT trigger."""
        code = 'def public_func():\n    """Has docstring."""\n    pass\n'
        tree = ast.parse(code)
        rule = HL301NoDocstringRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_private_func_not_detected(self) -> None:
        """A private function (underscore prefix) should NOT trigger."""
        code = "def _private(): pass\n"
        tree = ast.parse(code)
        rule = HL301NoDocstringRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_async_public_func_detected(self) -> None:
        """An async public function without docstring should trigger."""
        code = "async def public_async(): pass\n"
        tree = ast.parse(code)
        rule = HL301NoDocstringRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.severity == "Info"
        assert "public_async" in v.phenomenon

    def test_class_public_method_detected(self) -> None:
        """A public class method without docstring should trigger."""
        code = "class MyClass:\n    def method(self): pass\n"
        tree = ast.parse(code)
        rule = HL301NoDocstringRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "method" in v.phenomenon

    def test_class_private_method_not_detected(self) -> None:
        """A private class method should NOT trigger."""
        code = "class MyClass:\n    def _method(self): pass\n"
        tree = ast.parse(code)
        rule = HL301NoDocstringRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_no_functions_returns_none(self) -> None:
        """Code with no function definitions should return None."""
        code = "x = 1\ny = 2\n"
        tree = ast.parse(code)
        rule = HL301NoDocstringRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_multiple_no_docstring_funcs(self) -> None:
        """Multiple public functions without docstrings should return multiple violations."""
        code = "def foo(): pass\ndef bar(): pass\n"
        tree = ast.parse(code)
        rule = HL301NoDocstringRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 2
        names = {v.phenomenon.split()[1] for v in result}
        assert names == {"foo", "bar"}

    def test_dunder_method_not_detected(self) -> None:
        """A double-underscore method should NOT trigger."""
        code = "def __init__(self): pass\n"
        tree = ast.parse(code)
        rule = HL301NoDocstringRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_full_attribution_chain(self) -> None:
        """Each violation must contain the full attribution chain."""
        code = "def public_func(): pass\n"
        tree = ast.parse(code)
        rule = HL301NoDocstringRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.rule_id == "HL301"
        assert v.severity == "Info"
        assert "public_func" in v.phenomenon
        assert v.attribution == "AI 倾向写完功能就收工，公共函数应有文档字符串"
        assert v.agente_ref == "AGENTS.md §4 Working Guidelines"
        assert validate_violation(v) == []
