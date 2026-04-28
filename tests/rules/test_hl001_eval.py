"""Tests for HL001: Prohibit eval() calls."""

from __future__ import annotations

import ast

from harness_lint.attribution import validate_violation
from harness_lint.rules.hl001_eval import HL001EvalRule


class TestHL001EvalRule:
    """Tests for the HL001 eval detection rule."""

    def test_simple_eval_call_detected(self) -> None:
        """Simple eval('1+1') should be detected with correct line/column."""
        code = 'x = eval("1+1")\n'
        tree = ast.parse(code)
        rule = HL001EvalRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.line == 1
        assert v.column == 4
        assert v.rule_id == "HL001"
        assert v.severity == "Error"

    def test_no_eval_returns_none(self) -> None:
        """Code without eval calls should return None or empty list."""
        code = "x = 1 + 1\n"
        tree = ast.parse(code)
        rule = HL001EvalRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_eval_reference_not_detected(self) -> None:
        """Assigning eval to a variable without calling it should not trigger."""
        code = "x = eval\n"
        tree = ast.parse(code)
        rule = HL001EvalRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_eval_inside_function_detected(self) -> None:
        """eval nested inside a function definition should be detected."""
        code = """def foo():
    return eval("1+1")
"""
        tree = ast.parse(code)
        rule = HL001EvalRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.line == 2
        assert v.column == 11

    def test_eval_inside_class_detected(self) -> None:
        """eval nested inside a class method should be detected."""
        code = """class MyClass:
    def method(self):
        result = eval("self")
"""
        tree = ast.parse(code)
        rule = HL001EvalRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.line == 3
        assert v.column == 17

    def test_multiple_eval_calls_return_multiple_violations(self) -> None:
        """Multiple eval calls in the same file should return multiple violations."""
        code = """a = eval("1")
b = eval("2")
"""
        tree = ast.parse(code)
        rule = HL001EvalRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 2
        lines = [v.line for v in result]
        assert sorted(lines) == [1, 2]

    def test_violation_contains_full_attribution_chain(self) -> None:
        """Each violation must contain the full attribution chain."""
        code = 'eval("bad")\n'
        tree = ast.parse(code)
        rule = HL001EvalRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.phenomenon == "禁止使用 eval()"
        assert v.attribution == "AI 可能用 eval 实现灵活执行，导致代码注入"
        assert v.agente_ref == "AGENTS.md §5 Critical Rules"
        assert validate_violation(v) == []

    def test_eval_in_expression_context_detected(self) -> None:
        """eval used in an expression context should be detected."""
        code = "print(eval('1+1'))\n"
        tree = ast.parse(code)
        rule = HL001EvalRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.line == 1
        assert v.column == 6

    def test_indirect_eval_not_detected(self) -> None:
        """Indirect eval via getattr should not be detected."""
        code = 'getattr(__builtins__, "eval")("1+1")\n'
        tree = ast.parse(code)
        rule = HL001EvalRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_builtins_eval_detected(self) -> None:
        """builtins.eval('1+1') should be detected."""
        code = 'builtins.eval("1+1")\n'
        tree = ast.parse(code)
        rule = HL001EvalRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.rule_id == "HL001"
        assert v.severity == "Error"

    def test_builtins_dunder_eval_detected(self) -> None:
        """__builtins__.eval('1+1') should be detected."""
        code = '__builtins__.eval("1+1")\n'
        tree = ast.parse(code)
        rule = HL001EvalRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.rule_id == "HL001"
        assert v.severity == "Error"

    def test_obj_eval_not_detected(self) -> None:
        """obj.eval('1+1') should NOT be detected (not builtin eval)."""
        code = 'obj.eval("1+1")\n'
        tree = ast.parse(code)
        rule = HL001EvalRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []
