"""HL002: Fake exception handling detection.

This rule detects ineffective exception handlers such as 'except: pass'
and 'except Exception as e: print(e)', which AI-generated code often
uses to silently swallow errors.
"""

from __future__ import annotations

import ast

from harness_lint.rules.base import Rule, Violation


class HL202FakeExceptionRule(Rule):
    """Detect fake exception handling patterns."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="HL202",
            name="假异常处理",
            severity="Warning",
            message_template="检测到无效异常处理：{pattern}",
            phases=["execute", "evaluate"],
            agente_ref="AGENTS.md §5 Critical Rules",
            attribution="AI 倾向于用 except: pass 掩盖错误，应正确处理或记录异常",
        )

    def _is_print_call(self, node: ast.stmt) -> bool:
        """Check if a statement is a print() call."""
        return (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "print"
        )

    def check(self, file_path: str, file_content: str, ast_tree: ast.AST) -> list[Violation] | None:
        """Check a file for fake exception handling.

        Args:
            file_path: Path to the file being checked.
            file_content: Raw text content of the file.
            ast_tree: Parsed AST of the file content.

        Returns:
            A list of :class:`Violation` objects for each fake exception
            handler found, or ``None`` if no violations are detected.
        """
        violations = []
        for node in ast.walk(ast_tree):
            if not isinstance(node, ast.Try):
                continue
            for handler in node.handlers:
                if len(handler.body) != 1:
                    continue
                stmt = handler.body[0]
                if isinstance(stmt, ast.Pass):
                    violations.append(
                        self._create_violation(
                            file=file_path,
                            line=handler.lineno,
                            column=handler.col_offset,
                            phenomenon=self.message_template.format(pattern="except: pass"),
                        )
                    )
                elif self._is_print_call(stmt):
                    violations.append(
                        self._create_violation(
                            file=file_path,
                            line=handler.lineno,
                            column=handler.col_offset,
                            phenomenon=self.message_template.format(pattern="except: print(e)"),
                        )
                    )
        return violations if violations else None
