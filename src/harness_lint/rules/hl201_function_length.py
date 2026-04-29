"""HL201: Function body length limit.

This rule detects functions (including async functions and methods)
whose total line count exceeds a configurable threshold.
"""

from __future__ import annotations

import ast

from harness_lint.rules.base import Rule, Violation


class HL201FunctionLengthRule(Rule):
    """Detect functions that exceed the maximum allowed length."""

    def __init__(self, threshold: int = 50) -> None:
        super().__init__(
            rule_id="HL201",
            name="函数体长度超限",
            severity="Warning",
            message_template="函数 {name} 长度 {length} 行（阈值 {threshold} 行）",
            phases=["execute", "evaluate"],
            agente_ref="AGENTS.md §5 Critical Rules",
            attribution="AGENTS.md 未明确定义函数长度上限",
        )
        self.threshold = threshold

    def check(self, file_path: str, file_content: str, ast_tree: ast.AST) -> list[Violation] | None:
        """Check a file for functions exceeding the length threshold.

        Args:
            file_path: Path to the file being checked.
            file_content: Raw text content of the file.
            ast_tree: Parsed AST of the file content.

        Returns:
            A list of :class:`Violation` objects for each function that
            exceeds the threshold, or ``None`` if no violations are detected.
        """
        violations = []
        for node in ast.walk(ast_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = node.end_lineno - node.lineno + 1
                if length > self.threshold:
                    violations.append(
                        self._create_violation(
                            file=file_path,
                            line=node.lineno,
                            column=node.col_offset,
                            phenomenon=self.message_template.format(
                                name=node.name,
                                length=length,
                                threshold=self.threshold,
                            ),
                        )
                    )
        return violations if violations else None
