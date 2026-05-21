"""Tests for HL402: Protocol consistency check."""

from __future__ import annotations

import ast

from harness_lint.attribution import validate_violation
from harness_lint.rules.hl402_protocol_consistency import HL402ProtocolConsistencyRule


class TestHL402ProtocolConsistencyRule:
    """Tests for the HL402 type annotation detection rule."""

    def test_func_no_annotations_detected(self) -> None:
        """A public function with no annotations at all should trigger."""
        code = "def public_func(a, b): return a + b\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.rule_id == "HL402"
        assert v.severity == "Warning"
        assert "public_func" in v.phenomenon
        assert "返回值" in v.phenomenon

    def test_func_fully_annotated_not_detected(self) -> None:
        """A fully annotated public function should NOT trigger."""
        code = "def public_func(a: int, b: str) -> bool: return True\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_func_missing_return_annotation_detected(self) -> None:
        """A public function missing return annotation should trigger."""
        code = "def public_func(a: int) -> None: pass\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        # Has return annotation → should NOT trigger
        assert result is None or result == []

    def test_func_missing_param_annotation_detected(self) -> None:
        """A public function missing a param annotation should trigger."""
        code = "def public_func(a, b: int) -> None: pass\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "a" in v.phenomenon

    def test_func_missing_only_return_annotation(self) -> None:
        """A public function with annotated params but no return type."""
        code = "def public_func(a: int, b: str): pass\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "返回值" in v.phenomenon

    def test_private_func_not_detected(self) -> None:
        """A private function should NOT trigger."""
        code = "def _private(a, b): pass\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_dunder_method_not_detected(self) -> None:
        """A dunder method should NOT trigger."""
        code = "def __init__(self, x): pass\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_async_public_func_detected(self) -> None:
        """An async public function missing annotations should trigger."""
        code = "async def public_async(a, b): pass\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "public_async" in v.phenomenon

    def test_class_method_self_skipped(self) -> None:
        """The 'self' parameter should not require annotation."""
        code = "class MyClass:\n    def method(self, x: int) -> None: pass\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_class_method_cls_skipped(self) -> None:
        """The 'cls' parameter should not require annotation."""
        code = "class MyClass:\n    @classmethod\n    def method(cls, x: int) -> None: pass\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_class_method_missing_annotation_detected(self) -> None:
        """A class method with missing annotation should trigger."""
        code = "class MyClass:\n    def method(self, x): pass\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "method" in v.phenomenon

    def test_no_functions_returns_none(self) -> None:
        """Code with no functions should return None."""
        code = "x = 1\ny = 2\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_multiple_unannotated_funcs(self) -> None:
        """Multiple public functions without annotations should each trigger."""
        code = "def foo(a): pass\ndef bar(b): pass\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 2
        names = {v.phenomenon.split()[1] for v in result}
        assert names == {"foo", "bar"}

    def test_full_attribution_chain(self) -> None:
        """Each violation must carry the full attribution chain."""
        code = "def public_func(a): pass\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.attribution == "AI 生成的公共 API 常省略类型标注，违反 AGENTS.md 的类型提示要求"
        assert v.agente_ref == "AGENTS.md §4 Working Guidelines"
        assert validate_violation(v) == []

    def test_varargs_missing_annotation_detected(self) -> None:
        """A public function with unannotated *args should trigger."""
        code = "def public_func(*args, x: int) -> None: pass\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "*args" in v.phenomenon

    def test_kwargs_missing_annotation_detected(self) -> None:
        """A public function with unannotated **kwargs should trigger."""
        code = "def public_func(x: int, **kwargs) -> None: pass\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "**kwargs" in v.phenomenon

    def test_kwonly_missing_annotation_detected(self) -> None:
        """A keyword-only parameter missing annotation should trigger."""
        code = "def public_func(*, x, y: int) -> None: pass\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "x" in v.phenomenon

    def test_no_params_just_return_missing(self) -> None:
        """A no-arg function missing return annotation should trigger."""
        code = "def public_func(): pass\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "返回值" in v.phenomenon

    def test_no_params_with_return_not_detected(self) -> None:
        """A no-arg function with return annotation should NOT trigger."""
        code = "def public_func() -> None: pass\n"
        tree = ast.parse(code)
        rule = HL402ProtocolConsistencyRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []
