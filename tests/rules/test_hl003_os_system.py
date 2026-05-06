"""Tests for HL003: Prohibit os.system() calls."""

from __future__ import annotations

import ast

from harness_lint.attribution import validate_violation
from harness_lint.rules.hl003_os_system import HL003OsSystemRule


class TestHL003OsSystemRule:
    """Tests for the HL003 os.system detection rule."""

    def test_simple_os_system_call_detected(self) -> None:
        """Simple os.system('ls') should be detected with correct line/column."""
        code = 'os.system("ls")\n'
        tree = ast.parse(code)
        rule = HL003OsSystemRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.line == 1
        assert v.column == 0
        assert v.rule_id == "HL003"
        assert v.severity == "Error"

    def test_no_os_system_returns_none(self) -> None:
        """Code without os.system calls should return None."""
        code = "x = 1 + 1\n"
        tree = ast.parse(code)
        rule = HL003OsSystemRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_os_path_join_not_detected(self) -> None:
        """os.path.join() should NOT be detected."""
        code = 'os.path.join("a", "b")\n'
        tree = ast.parse(code)
        rule = HL003OsSystemRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_bare_system_not_detected(self) -> None:
        """system() without os prefix should NOT be detected."""
        code = 'system("ls")\n'
        tree = ast.parse(code)
        rule = HL003OsSystemRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_os_system_inside_function_detected(self) -> None:
        """os.system nested inside a function should be detected."""
        code = """def foo():
    os.system("ls")
"""
        tree = ast.parse(code)
        rule = HL003OsSystemRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.line == 2
        assert v.column == 4

    def test_multiple_os_system_calls_return_multiple_violations(self) -> None:
        """Multiple os.system calls should return multiple violations."""
        code = """os.system("ls")
os.system("pwd")
"""
        tree = ast.parse(code)
        rule = HL003OsSystemRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 2
        lines = [v.line for v in result]
        assert sorted(lines) == [1, 2]

    def test_violation_contains_full_attribution_chain(self) -> None:
        """Each violation must contain the full attribution chain."""
        code = 'os.system("ls")\n'
        tree = ast.parse(code)
        rule = HL003OsSystemRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "os.system()" in v.phenomenon
        assert "subprocess.run()" in v.phenomenon
        assert v.attribution == "使用了不安全的系统调用，应使用 subprocess.run() 替代"
        assert v.agente_ref == "AGENTS.md §5 Critical Rules"
        assert validate_violation(v) == []

    def test_subprocess_run_not_detected(self) -> None:
        """subprocess.run() should NOT be detected (it's the recommended alternative)."""
        code = 'subprocess.run(["ls"])\n'
        tree = ast.parse(code)
        rule = HL003OsSystemRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_os_system_in_class_method_detected(self) -> None:
        """os.system in a class method should be detected."""
        code = """class MyClass:
    def method(self):
        os.system("ls")
"""
        tree = ast.parse(code)
        rule = HL003OsSystemRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.line == 3
        assert v.column == 8

    def test_other_os_functions_not_detected(self) -> None:
        """Other os module functions should NOT be detected."""
        code = """os.listdir(".")
os.getcwd()
os.environ.get("HOME")
"""
        tree = ast.parse(code)
        rule = HL003OsSystemRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []
