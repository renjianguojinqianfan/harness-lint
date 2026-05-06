"""HL003: Prohibit os.system() calls.

This rule detects direct calls to os.system(), which is an unsafe
system call. AI-generated code may use os.system() instead of the
safer subprocess.run() alternative.
"""

from __future__ import annotations

import ast

from harness_lint.rules.base import Rule, Violation


class HL003OsSystemRule(Rule):
    """Detect direct calls to os.system()."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="HL003",
            name="禁止使用 os.system()",
            severity="Error",
            message_template="禁止使用 os.system()，请使用 subprocess.run() 替代",
            phases=["execute", "evaluate"],
            agente_ref="AGENTS.md §5 Critical Rules",
            attribution="使用了不安全的系统调用，应使用 subprocess.run() 替代",
        )

    def check(self, file_path: str, file_content: str, ast_tree: ast.AST) -> list[Violation] | None:
        """Check a file for os.system() calls.

        Args:
            file_path: Path to the file being checked.
            file_content: Raw text content of the file.
            ast_tree: Parsed AST of the file content.

        Returns:
            A list of :class:`Violation` objects for each os.system()
            call found, or ``None`` if no violations are detected.
        """
        violations = []
        for node in ast.walk(ast_tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "system"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "os"
            ):
                violations.append(
                    self._create_violation(
                        file=file_path,
                        line=node.lineno,
                        column=node.col_offset,
                        phenomenon=self.message_template,
                    )
                )
        return violations if violations else None
