"""HL401: Repeated violation pattern detection.

This rule detects files containing multiple instances of the same
anti-pattern (e.g., three or more bare ``except`` clauses).  Such
repetition indicates a systematic deviation rather than an isolated
mistake, warranting a pattern-level report.
"""

from __future__ import annotations

import ast

from harness_lint.rules.base import Rule, Violation

# Minimum occurrences of the same anti-pattern within a single file
# before it is flagged as a repeated-pattern violation.
_PATTERN_THRESHOLD = 3


class HL401RepeatedPatternRule(Rule):
    """Detect repeated violation patterns within a single file."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="HL401",
            name="重复违规模式检测",
            severity="Warning",
            message_template="检测到重复违规模式：{description}（出现 {count} 次）",
            phases=["execute", "evaluate"],
            agente_ref="AGENTS.md §5 Critical Rules",
            attribution="同一违规模式反复出现表明是系统性偏差，而非孤立错误",
        )

    def _count_bare_excepts(self, tree: ast.AST) -> list[tuple[int, int]]:
        """Return (line, col) for every bare ``except:`` handler."""
        positions: list[tuple[int, int]] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
            for handler in node.handlers:
                if handler.type is None:
                    positions.append((handler.lineno, handler.col_offset))
        return positions

    def _count_overly_broad_excepts(self, tree: ast.AST) -> list[tuple[int, int]]:
        """Return (line, col) for every ``except Exception`` handler."""
        positions: list[tuple[int, int]] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
            for handler in node.handlers:
                if (
                    handler.type is not None
                    and isinstance(handler.type, ast.Name)
                    and handler.type.id == "Exception"
                ):
                    positions.append((handler.lineno, handler.col_offset))
        return positions

    def _count_specific_pass_bodies(self, tree: ast.AST) -> list[tuple[int, int]]:
        """Return (line, col) for every ``except SpecificError: pass`` block.

        Only counts handlers with a *specific* exception type (not bare
        ``except:`` and not overly broad ``except Exception:``) whose
        body is just ``pass``.  This avoids overlap with the "bare
        except" and "overly broad except Exception" patterns.
        """
        positions: list[tuple[int, int]] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
            for handler in node.handlers:
                if len(handler.body) != 1 or not isinstance(handler.body[0], ast.Pass):
                    continue
                # Skip bare except (handler.type is None)
                if handler.type is None:
                    continue
                # Skip overly broad `except Exception`
                if isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
                    continue
                positions.append((handler.lineno, handler.col_offset))
        return positions

    def check(
        self, file_path: str, file_content: str, ast_tree: ast.AST
    ) -> list[Violation] | None:
        """Check a file for repeated anti-pattern occurrences.

        Args:
            file_path: Path to the file being checked.
            file_content: Raw text content of the file.
            ast_tree: Parsed AST of the file content.

        Returns:
            A list of :class:`Violation` objects for each repeated
            pattern found, or ``None`` if no repeated patterns are
            detected.
        """
        pattern_checks: list[tuple[str, list[tuple[int, int]]]] = [
            ("bare except", self._count_bare_excepts(ast_tree)),
            ("overly broad except Exception", self._count_overly_broad_excepts(ast_tree)),
            ("specific except with pass body", self._count_specific_pass_bodies(ast_tree)),
        ]

        violations: list[Violation] = []
        for description, positions in pattern_checks:
            if len(positions) < _PATTERN_THRESHOLD:
                continue
            # Report at the first occurrence of the repeated pattern
            first_line, first_col = positions[0]
            violations.append(
                self._create_violation(
                    file=file_path,
                    line=first_line,
                    column=first_col,
                    phenomenon=self.message_template.format(
                        description=description, count=len(positions)
                    ),
                )
            )

        return violations if violations else None
