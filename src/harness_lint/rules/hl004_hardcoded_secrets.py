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

    def _is_env_call(self, node: ast.expr) -> bool:
        """Check if node is an os.environ.get() or os.getenv() call."""
        if not isinstance(node, ast.Call):
            return False
        func = node.func
        # os.environ.get(...)
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "get"
            and isinstance(func.value, ast.Attribute)
            and func.value.attr == "environ"
            and isinstance(func.value.value, ast.Name)
            and func.value.value.id == "os"
        ):
            return True
        # os.getenv(...)
        return (
            isinstance(func, ast.Attribute)
            and func.attr == "getenv"
            and isinstance(func.value, ast.Name)
            and func.value.id == "os"
        )

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
            if not isinstance(node, ast.Assign):
                continue
            # Check if value is a string literal
            if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, str):
                # Also skip os.environ.get / os.getenv calls
                if self._is_env_call(node.value):
                    continue
                continue
            value = node.value.value
            if value in _PLACEHOLDER_VALUES:
                continue
            # Check each target
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
        return violations if violations else None
