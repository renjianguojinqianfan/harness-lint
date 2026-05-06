"""Tests for HL002: Prohibit exec() calls."""

from __future__ import annotations

import ast

from harness_lint.attribution import validate_violation
from harness_lint.rules.hl002_exec import HL002ExecRule


class TestHL002ExecRule:
    """Tests for the HL002 exec detection rule."""

    def test_simple_exec_call_detected(self) -> None:
        """Simple exec('code') should be detected with correct line/column."""
        code = 'exec("print(1)")\n'
        tree = ast.parse(code)
        rule = HL002ExecRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.line == 1
        assert v.column == 0
        assert v.rule_id == "HL002"
        assert v.severity == "Error"

    def test_no_exec_returns_none(self) -> None:
        """Code without exec calls should return None."""
        code = "x = 1 + 1\n"
        tree = ast.parse(code)
        rule = HL002ExecRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_exec_reference_not_detected(self) -> None:
        """Assigning exec to a variable without calling it should not trigger."""
        code = "x = exec\n"
        tree = ast.parse(code)
        rule = HL002ExecRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_exec_inside_function_detected(self) -> None:
        """exec nested inside a function definition should be detected."""
        code = """def foo():
    exec("x = 1")
"""
        tree = ast.parse(code)
        rule = HL002ExecRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.line == 2
        assert v.column == 4

    def test_exec_inside_class_detected(self) -> None:
        """exec nested inside a class method should be detected."""
        code = """class MyClass:
    def method(self):
        exec("x = 1")
"""
        tree = ast.parse(code)
        rule = HL002ExecRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.line == 3
        assert v.column == 8

    def test_multiple_exec_calls_return_multiple_violations(self) -> None:
        """Multiple exec calls in the same file should return multiple violations."""
        code = """exec("a = 1")
exec("b = 2")
"""
        tree = ast.parse(code)
        rule = HL002ExecRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 2
        lines = [v.line for v in result]
        assert sorted(lines) == [1, 2]

    def test_violation_contains_full_attribution_chain(self) -> None:
        """Each violation must contain the full attribution chain."""
        code = 'exec("bad")\n'
        tree = ast.parse(code)
        rule = HL002ExecRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.phenomenon == "禁止使用 exec()"
        assert v.attribution == "AI 可能用 exec 实现动态执行，导致代码注入"
        assert v.agente_ref == "AGENTS.md §5 Critical Rules"
        assert validate_violation(v) == []

    def test_exec_in_expression_context_detected(self) -> None:
        """exec used in an expression context should be detected."""
        code = "print(exec('x = 1'))\n"
        tree = ast.parse(code)
        rule = HL002ExecRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.line == 1
        assert v.column == 6

    def test_builtins_exec_detected(self) -> None:
        """builtins.exec('code') should be detected."""
        code = 'builtins.exec("x = 1")\n'
        tree = ast.parse(code)
        rule = HL002ExecRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.rule_id == "HL002"
        assert v.severity == "Error"

    def test_builtins_dunder_exec_detected(self) -> None:
        """__builtins__.exec('code') should be detected."""
        code = '__builtins__.exec("x = 1")\n'
        tree = ast.parse(code)
        rule = HL002ExecRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.rule_id == "HL002"
        assert v.severity == "Error"

    def test_obj_exec_not_detected(self) -> None:
        """obj.exec('code') should NOT be detected (not builtin exec)."""
        code = 'obj.exec("x = 1")\n'
        tree = ast.parse(code)
        rule = HL002ExecRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []
