"""HL402: Protocol consistency check.

This rule detects AI behaviour patterns that conflict with AGENTS.md
clauses.  Specifically, it flags public functions that are missing type
annotations on their parameters or return type, which violates the
"All public APIs need type hints and docstrings" guideline in
AGENTS.md §4.
"""

from __future__ import annotations

import ast

from harness_lint.rules.base import Rule, Violation

# Parameters whose annotations are not required (conventional
# self/cls in method signatures).
_SELF_CLS = {"self", "cls"}


class HL402ProtocolConsistencyRule(Rule):
    """Detect public APIs missing type annotations."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="HL402",
            name="协议一致性检查",
            severity="Warning",
            message_template="公共函数 {name} 缺少类型标注（{details}）",
            phases=["execute", "evaluate"],
            agente_ref="AGENTS.md §4 Working Guidelines",
            attribution="AI 生成的公共 API 常省略类型标注，违反 AGENTS.md 的类型提示要求",
        )

    @staticmethod
    def _is_dunder(name: str) -> bool:
        """Check if a name is a double-underscore special method."""
        return name.startswith("__") and name.endswith("__")

    @staticmethod
    def _collect_missing_annotations(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> list[str]:
        """Return a list of human-readable descriptions of missing annotations."""
        missing: list[str] = []

        # Check parameters (skip self/cls)
        args = node.args
        all_args = args.args + args.posonlyargs + args.kwonlyargs
        if args.vararg and args.vararg.annotation is None:
            missing.append("*" + args.vararg.arg)
        if args.kwarg and args.kwarg.annotation is None:
            missing.append("**" + args.kwarg.arg)
        for arg in all_args:
            if arg.arg in _SELF_CLS:
                continue
            if arg.annotation is None:
                missing.append(arg.arg)

        # Check return type
        if node.returns is None:
            missing.append("返回值")

        return missing

    def check(self, file_path: str, file_content: str, ast_tree: ast.AST) -> list[Violation] | None:
        """Check a file for public functions missing type annotations.

        Args:
            file_path: Path to the file being checked.
            file_content: Raw text content of the file.
            ast_tree: Parsed AST of the file content.

        Returns:
            A list of :class:`Violation` objects for each public
            function missing type annotations, or ``None`` if all
            public APIs are properly annotated.
        """
        violations: list[Violation] = []

        for node in ast.walk(ast_tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            # Skip private and dunder functions
            if node.name.startswith("_"):
                continue

            missing = self._collect_missing_annotations(node)
            if not missing:
                continue

            details = ", ".join(missing)
            violations.append(
                self._create_violation(
                    file=file_path,
                    line=node.lineno,
                    column=node.col_offset,
                    phenomenon=self.message_template.format(name=node.name, details=details),
                )
            )

        return violations if violations else None
