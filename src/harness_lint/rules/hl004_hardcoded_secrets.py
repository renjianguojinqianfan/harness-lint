"""HL004: Hardcoded secrets detection.

This rule detects hardcoded secrets such as passwords, API keys, and tokens
in source code, which pose a security risk when committed to repositories.
"""

from __future__ import annotations

import ast
import re

from harness_lint.rules.base import Rule, Violation

# Sensitive variable name patterns (case-insensitive)
_SENSITIVE_PATTERNS = re.compile(
    r"(password|passwd|secret|api_key|apikey|token|access_key|private_key|"
    r"auth_token|client_secret|db_password|database_url)",
    re.IGNORECASE,
)

# Placeholder values that should not be flagged
_PLACEHOLDER_VALUES = {
    "",
    "xxx",
    "your_key_here",
    "changeme",
    "placeholder",
    "test",
    "example",
    "dummy",
    "fake",
    "sample",
    "TODO",
    "FIXME",
}


class HL004HardcodedSecretsRule(Rule):
    """Detect hardcoded secrets in variable assignments."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="HL004",
            name="硬编码密钥检测",
            severity="Error",
            message_template="检测到硬编码密钥：{var_name}",
            phases=["execute", "evaluate"],
            agente_ref="AGENTS.md §5 Critical Rules",
            attribution="硬编码密钥存在泄露风险，应使用环境变量或 .env 文件",
        )

    def _check_assign(self, node: ast.Assign, file_path: str) -> list[Violation]:
        """Check an ast.Assign node for hardcoded secrets."""
        violations: list[Violation] = []
        # Only string literal values are subject to detection; non-Constant
        # values (including os.environ.get / os.getenv calls) are skipped.
        if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, str):
            return violations
        value = node.value.value
        if value in _PLACEHOLDER_VALUES:
            return violations
        for target in node.targets:
            if isinstance(target, ast.Name) and _SENSITIVE_PATTERNS.search(target.id):
                violations.append(
                    self._create_violation(
                        file=file_path,
                        line=node.lineno,
                        column=node.col_offset,
                        phenomenon=self.message_template.format(var_name=target.id),
                    )
                )
        return violations

    def _check_ann_assign(self, node: ast.AnnAssign, file_path: str) -> list[Violation]:
        """Check an ast.AnnAssign node for hardcoded secrets."""
        violations: list[Violation] = []
        if node.value is None:
            return violations
        # Only string literal values are subject to detection; non-Constant
        # values (including os.environ.get / os.getenv calls) are skipped.
        if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, str):
            return violations
        value = node.value.value
        if value in _PLACEHOLDER_VALUES:
            return violations
        if isinstance(node.target, ast.Name) and _SENSITIVE_PATTERNS.search(node.target.id):
            violations.append(
                self._create_violation(
                    file=file_path,
                    line=node.lineno,
                    column=node.col_offset,
                    phenomenon=self.message_template.format(var_name=node.target.id),
                )
            )
        return violations

    def check(self, file_path: str, file_content: str, ast_tree: ast.AST) -> list[Violation] | None:
        """Check a file for hardcoded secrets.

        Args:
            file_path: Path to the file being checked.
            file_content: Raw text content of the file.
            ast_tree: Parsed AST of the file content.

        Returns:
            A list of :class:`Violation` objects for each hardcoded secret
            found, or ``None`` if no violations are detected.
        """
        violations = []
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Assign):
                violations.extend(self._check_assign(node, file_path))
            elif isinstance(node, ast.AnnAssign):
                violations.extend(self._check_ann_assign(node, file_path))
        return violations if violations else None
