"""HL301: Public functions without docstring.

This rule detects public functions (including async functions and methods)
that lack a docstring.  Private functions (names starting with ``_``) and
dunder methods are excluded.
"""

from __future__ import annotations

import ast

from harness_lint.rules.base import Rule, Violation


class HL301NoDocstringRule(Rule):
    """Detect public functions that are missing a docstring."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="HL301",
            name="公共函数无 docstring",
            severity="Info",
            message_template="公共函数 {name} 缺少 docstring",
            phases=["evaluate"],
            agente_ref="AGENTS.md §4 Working Guidelines",
            attribution="AI 倾向写完功能就收工，公共函数应有文档字符串",
        )

    def check(self, file_path: str, file_content: str, ast_tree: ast.AST) -> list[Violation] | None:
        """Check a file for public functions missing docstrings.

        Args:
            file_path: Path to the file being checked.
            file_content: Raw text content of the file.
            ast_tree: Parsed AST of the file content.

        Returns:
            A list of :class:`Violation` objects for each public function
            without a docstring, or ``None`` if no violations are detected.
        """
        violations: list[Violation] = []
        for node in ast.walk(ast_tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_"):
                continue
            body = node.body
            if not body:
                has_docstring = False
            else:
                first = body[0]
                has_docstring = (
                    isinstance(first, ast.Expr)
                    and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)
                )
            if not has_docstring:
                violations.append(
                    self._create_violation(
                        file=file_path,
                        line=node.lineno,
                        column=node.col_offset,
                        phenomenon=self.message_template.format(name=node.name),
                    )
                )
        return violations if violations else None
