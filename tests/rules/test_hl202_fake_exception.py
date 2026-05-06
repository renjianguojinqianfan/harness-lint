"""Tests for HL202: Fake exception handling."""

from __future__ import annotations

import ast

from harness_lint.attribution import validate_violation
from harness_lint.rules.hl202_fake_exception import HL202FakeExceptionRule


class TestHL202FakeExceptionRule:
    """Tests for the HL202 fake exception handling detection rule."""

    def test_except_pass_detected(self) -> None:
        """except: pass should be detected."""
        code = """try:
    x = 1
except:
    pass
"""
        tree = ast.parse(code)
        rule = HL202FakeExceptionRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.rule_id == "HL202"
        assert v.severity == "Warning"
        assert "pass" in v.phenomenon

    def test_except_exception_pass_detected(self) -> None:
        """except Exception: pass should be detected."""
        code = """try:
    x = 1
except Exception:
    pass
"""
        tree = ast.parse(code)
        rule = HL202FakeExceptionRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1

    def test_except_as_pass_detected(self) -> None:
        """except Exception as e: pass should be detected."""
        code = """try:
    x = 1
except Exception as e:
    pass
"""
        tree = ast.parse(code)
        rule = HL202FakeExceptionRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1

    def test_except_print_e_detected(self) -> None:
        """except Exception as e: print(e) should be detected."""
        code = """try:
    x = 1
except Exception as e:
    print(e)
"""
        tree = ast.parse(code)
        rule = HL202FakeExceptionRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "print" in v.phenomenon

    def test_except_logging_not_detected(self) -> None:
        """except Exception as e: logging.error(e) should NOT be detected."""
        code = """try:
    x = 1
except Exception as e:
    logging.error(e)
"""
        tree = ast.parse(code)
        rule = HL202FakeExceptionRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_except_raise_not_detected(self) -> None:
        """except Exception as e: raise should NOT be detected."""
        code = """try:
    x = 1
except Exception as e:
    raise
"""
        tree = ast.parse(code)
        rule = HL202FakeExceptionRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_no_try_except_returns_none(self) -> None:
        """Code without try/except should return None."""
        code = "x = 1 + 1\n"
        tree = ast.parse(code)
        rule = HL202FakeExceptionRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_violation_contains_full_attribution_chain(self) -> None:
        """Each violation must contain the full attribution chain."""
        code = """try:
    x = 1
except:
    pass
"""
        tree = ast.parse(code)
        rule = HL202FakeExceptionRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.attribution == "AI 倾向于用 except: pass 掩盖错误，应正确处理或记录异常"
        assert v.agente_ref == "AGENTS.md §5 Critical Rules"
        assert validate_violation(v) == []

    def test_multiple_fake_handlers_multiple_violations(self) -> None:
        """Multiple fake exception handlers should return multiple violations."""
        code = """try:
    x = 1
except ValueError:
    pass
try:
    y = 2
except TypeError:
    pass
"""
        tree = ast.parse(code)
        rule = HL202FakeExceptionRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 2

    def test_except_multi_line_handler_not_detected(self) -> None:
        """A multi-line handler should NOT be detected."""
        code = """try:
    x = 1
except Exception as e:
    logging.error(e)
    raise
"""
        tree = ast.parse(code)
        rule = HL202FakeExceptionRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_except_print_fstring_detected(self) -> None:
        """except Exception as e: print(f'Error: {e}') should be detected."""
        code = """try:
    x = 1
except Exception as e:
    print(f"Error: {e}")
"""
        tree = ast.parse(code)
        rule = HL202FakeExceptionRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
