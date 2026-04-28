"""Tests for HL201: Function body length limit."""

from __future__ import annotations

import ast

from harness_lint.attribution import validate_violation
from harness_lint.rules.hl201_function_length import HL201FunctionLengthRule


class TestHL201FunctionLengthRule:
    """Tests for the HL201 function length detection rule."""

    def _make_function(self, name: str, length: int) -> str:
        """Generate a function with exactly `length` total lines."""
        # Total lines = 1 (def) + (length - 1) body lines
        body_lines = length - 1
        lines = [f"def {name}():"]
        for i in range(body_lines - 1):
            lines.append(f"    x{i} = {i}")
        lines.append("    pass")
        return "\n".join(lines) + "\n"

    def test_exact_threshold_no_trigger(self) -> None:
        """A function of exactly 50 lines should NOT trigger."""
        code = self._make_function("foo", 50)
        tree = ast.parse(code)
        rule = HL201FunctionLengthRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_one_over_threshold_triggers(self) -> None:
        """A function of 51 lines should trigger."""
        code = self._make_function("foo", 51)
        tree = ast.parse(code)
        rule = HL201FunctionLengthRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1

    def test_correct_line_and_name_reported(self) -> None:
        """Violation should report correct starting line and function name."""
        # Add leading lines so the function doesn't start at line 1
        prefix = "# comment\n# another\n"
        code = prefix + self._make_function("long_func", 51)
        tree = ast.parse(code)
        rule = HL201FunctionLengthRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.line == 3
        assert v.column == 0
        assert "long_func" in v.phenomenon

    def test_no_functions_returns_none(self) -> None:
        """Code with no function definitions should return None."""
        code = "x = 1\ny = 2\n"
        tree = ast.parse(code)
        rule = HL201FunctionLengthRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_below_threshold_no_trigger(self) -> None:
        """A short function should NOT trigger."""
        code = "def foo():\n    pass\n"
        tree = ast.parse(code)
        rule = HL201FunctionLengthRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_async_function_over_threshold(self) -> None:
        """An async function over the threshold should trigger."""
        prefix = "async def bar():\n"
        body = "\n".join([f"    x{i} = {i}" for i in range(50)])
        code = prefix + body + "\n"
        tree = ast.parse(code)
        rule = HL201FunctionLengthRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "bar" in v.phenomenon

    def test_nested_functions_detected_independently(self) -> None:
        """Nested functions should each be checked independently."""
        # Outer function is 55 lines (over threshold)
        # Inner function is 5 lines (under threshold)
        lines = ["def outer():"]
        for i in range(49):
            lines.append(f"    x{i} = {i}")
        lines.append("    def inner():")
        lines.append("        pass")
        lines.append("    pass")
        code = "\n".join(lines) + "\n"
        tree = ast.parse(code)
        rule = HL201FunctionLengthRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "outer" in v.phenomenon
        assert "inner" not in v.phenomenon

    def test_class_method_over_threshold(self) -> None:
        """A class method over the threshold should trigger."""
        lines = ["class MyClass:", "    def method(self):"]
        for i in range(50):
            lines.append(f"        x{i} = {i}")
        code = "\n".join(lines) + "\n"
        tree = ast.parse(code)
        rule = HL201FunctionLengthRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "method" in v.phenomenon

    def test_multiple_functions_over_threshold(self) -> None:
        """Multiple functions over threshold should return multiple violations."""
        code = self._make_function("foo", 51) + self._make_function("bar", 52)
        tree = ast.parse(code)
        rule = HL201FunctionLengthRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 2
        names = []
        for v in result:
            if "foo" in v.phenomenon:
                names.append("foo")
            elif "bar" in v.phenomenon:
                names.append("bar")
        assert sorted(names) == ["bar", "foo"]

    def test_custom_threshold(self) -> None:
        """A custom threshold should be respected."""
        code = self._make_function("foo", 11)
        tree = ast.parse(code)
        rule = HL201FunctionLengthRule(threshold=10)
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        assert "阈值 10 行" in result[0].phenomenon

    def test_custom_threshold_no_trigger(self) -> None:
        """A function below custom threshold should NOT trigger."""
        code = self._make_function("foo", 10)
        tree = ast.parse(code)
        rule = HL201FunctionLengthRule(threshold=10)
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_full_attribution_chain(self) -> None:
        """Each violation must contain the full attribution chain."""
        code = self._make_function("foo", 51)
        tree = ast.parse(code)
        rule = HL201FunctionLengthRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.rule_id == "HL201"
        assert v.severity == "Warning"
        assert "foo" in v.phenomenon
        assert "51" in v.phenomenon
        assert "50" in v.phenomenon
        assert v.attribution == "AGENTS.md 未明确定义函数长度上限"
        assert v.agente_ref == "AGENTS.md §5 Critical Rules"
        assert validate_violation(v) == []

    def test_phenomenon_format(self) -> None:
        """Phenomenon should follow the exact template."""
        code = self._make_function("my_func", 55)
        tree = ast.parse(code)
        rule = HL201FunctionLengthRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        expected = "函数 my_func 长度 55 行（阈值 50 行）"
        assert v.phenomenon == expected

    def test_nested_function_over_threshold(self) -> None:
        """A nested function itself over threshold should trigger."""
        lines = ["def outer():", "    pass", "    def inner():"]
        for i in range(50):
            lines.append(f"        x{i} = {i}")
        code = "\n".join(lines) + "\n"
        tree = ast.parse(code)
        rule = HL201FunctionLengthRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        # Both outer and inner exceed threshold because outer's end_lineno
        # encompasses the entire nested function body.
        assert len(result) == 2
        names = {v.phenomenon.split()[1] for v in result}
        assert names == {"outer", "inner"}
