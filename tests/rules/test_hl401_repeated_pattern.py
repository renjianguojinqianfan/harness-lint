"""Tests for HL401: Repeated violation pattern detection."""

from __future__ import annotations

import ast

from harness_lint.attribution import validate_violation
from harness_lint.rules.hl401_repeated_pattern import HL401RepeatedPatternRule


class TestHL401RepeatedPatternRule:
    """Tests for the HL401 repeated pattern detection rule."""

    def test_three_bare_excepts_detected(self) -> None:
        """Three bare except clauses should trigger the rule."""
        code = """\
try:
    pass
except:
    pass
try:
    pass
except:
    pass
try:
    pass
except:
    pass
"""
        tree = ast.parse(code)
        rule = HL401RepeatedPatternRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.rule_id == "HL401"
        assert v.severity == "Warning"
        assert "bare except" in v.phenomenon
        assert "3" in v.phenomenon

    def test_two_bare_excepts_not_detected(self) -> None:
        """Only two bare except clauses should NOT trigger."""
        code = """\
try:
    pass
except:
    pass
try:
    pass
except:
    pass
"""
        tree = ast.parse(code)
        rule = HL401RepeatedPatternRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_no_try_except_returns_none(self) -> None:
        """Code with no try/except should return None."""
        code = "x = 1\ny = 2\n"
        tree = ast.parse(code)
        rule = HL401RepeatedPatternRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_three_overly_broad_excepts_detected(self) -> None:
        """Three ``except Exception`` handlers should trigger."""
        code = """\
try:
    pass
except Exception:
    pass
try:
    pass
except Exception:
    pass
try:
    pass
except Exception:
    pass
"""
        tree = ast.parse(code)
        rule = HL401RepeatedPatternRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "overly broad except Exception" in v.phenomenon

    def test_three_except_pass_blocks_detected(self) -> None:
        """Three ``except SpecificError: pass`` blocks should trigger."""
        code = """\
try:
    pass
except ValueError:
    pass
try:
    pass
except TypeError:
    pass
try:
    pass
except KeyError:
    pass
"""
        tree = ast.parse(code)
        rule = HL401RepeatedPatternRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "specific except with pass body" in v.phenomenon

    def test_specific_except_with_body_not_counted_as_pass(self) -> None:
        """An except clause with a real body should NOT count as 'pass'."""
        code = """\
try:
    pass
except ValueError:
    print("caught")
try:
    pass
except TypeError:
    pass
try:
    pass
except KeyError:
    pass
"""
        tree = ast.parse(code)
        rule = HL401RepeatedPatternRule()
        result = rule.check("test.py", code, tree)

        # Only 2 except:pass, below threshold
        assert result is None or result == []

    def test_multiple_patterns_detected_independently(self) -> None:
        """Multiple distinct patterns each exceeding threshold generate separate violations."""
        code = """\
try:
    pass
except:
    pass
try:
    pass
except:
    pass
try:
    pass
except:
    pass
try:
    pass
except Exception:
    pass
try:
    pass
except Exception:
    pass
try:
    pass
except Exception:
    pass
"""
        tree = ast.parse(code)
        rule = HL401RepeatedPatternRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 2
        phenomena = {v.phenomenon for v in result}
        assert any("bare except" in p for p in phenomena)
        assert any("overly broad except Exception" in p for p in phenomena)

    def test_violation_at_first_occurrence(self) -> None:
        """The violation should be reported at the first occurrence line."""
        code = """\
x = 0
try:
    pass
except:
    pass
y = 1
try:
    pass
except:
    pass
z = 2
try:
    pass
except:
    pass
"""
        tree = ast.parse(code)
        rule = HL401RepeatedPatternRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        # First bare except is at line 4 (except keyword is on line 4)
        assert result[0].line == 4

    def test_full_attribution_chain(self) -> None:
        """Each violation must carry the full attribution chain."""
        code = """\
try:
    pass
except:
    pass
try:
    pass
except:
    pass
try:
    pass
except:
    pass
"""
        tree = ast.parse(code)
        rule = HL401RepeatedPatternRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.attribution == "同一违规模式反复出现表明是系统性偏差，而非孤立错误"
        assert v.agente_ref == "AGENTS.md §5 Critical Rules"
        assert validate_violation(v) == []

    def test_mixed_handler_types_count_bare_separately(self) -> None:
        """Bare except and specific except should be counted separately."""
        code = """\
try:
    pass
except:
    pass
try:
    pass
except ValueError:
    pass
try:
    pass
except:
    pass
"""
        tree = ast.parse(code)
        rule = HL401RepeatedPatternRule()
        result = rule.check("test.py", code, tree)

        # 2 bare excepts (below threshold), 1 specific except with pass (below threshold)
        assert result is None or result == []

    def test_nested_try_except_in_function(self) -> None:
        """Nested try/except inside a function should be counted."""
        code = """\
def func():
    try:
        pass
    except:
        pass
    try:
        pass
    except:
        pass
    try:
        pass
    except:
        pass
"""
        tree = ast.parse(code)
        rule = HL401RepeatedPatternRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) >= 1

    def test_multiple_handlers_in_single_try_counted(self) -> None:
        """Multiple handlers in a single try block should each be counted."""
        code = """\
try:
    pass
except:
    pass
except:
    pass
except:
    pass
"""
        tree = ast.parse(code)
        rule = HL401RepeatedPatternRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        assert "bare except" in result[0].phenomenon
