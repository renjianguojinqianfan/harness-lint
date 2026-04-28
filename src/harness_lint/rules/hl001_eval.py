"""HL001: Prohibit eval() calls.

This rule detects direct calls to the unsafe eval() builtin,
which can lead to code injection vulnerabilities when used by AI-generated code.
"""

from __future__ import annotations

import ast

from harness_lint.rules.base import Rule, Violation


class HL001EvalRule(Rule):
    """Detect direct calls to the unsafe eval() builtin."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="HL001",
            name="禁止使用 eval()",
            severity="Error",
            message_template="禁止使用 eval()",
            phases=["execute", "evaluate"],
            agente_ref="AGENTS.md §5 Critical Rules",
            attribution="AI 可能用 eval 实现灵活执行，导致代码注入",
        )

    def check(
        self, file_path: str, file_content: str, ast_tree: ast.AST
    ) -> list[Violation] | None:
        """Check a file for direct eval() calls.

        Args:
            file_path: Path to the file being checked.
            file_content: Raw text content of the file.
            ast_tree: Parsed AST of the file content.

        Returns:
            A list of :class:`Violation` objects for each direct eval()
            call found, or ``None`` if no violations are detected.
        """
        def _is_eval_call(func: ast.expr) -> bool:
            return (
                isinstance(func, ast.Name) and func.id == "eval"
            ) or (
                isinstance(func, ast.Attribute)
                and func.attr == "eval"
                and isinstance(func.value, ast.Name)
                and func.value.id in ("builtins", "__builtins__")
            )

        violations = []
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Call) and _is_eval_call(node.func):
                violations.append(
                    self._create_violation(
                        file=file_path,
                        line=node.lineno,
                        column=node.col_offset,
                        phenomenon=self.message_template,
                    )
                )
        return violations if violations else None
