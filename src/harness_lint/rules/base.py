"""Base classes for Harness-Lint rules."""

from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Violation:
    """A single rule violation found in a source file.

    Each violation carries the full attribution chain required by the
    Harness-Lint output protocol: phenomenon (what), attribution (why),
    and agente_ref (where in AGENTS.md).
    """

    file: str
    line: int
    column: int
    rule_id: str
    severity: str
    phenomenon: str
    attribution: str
    agente_ref: str


@dataclass
class Rule(ABC):
    """Abstract base class for all Harness-Lint rules.

    Subclasses must implement :meth:`check` and provide the rule metadata.
    The ``agente_ref`` field anchors the rule to a specific AGENTS.md
    clause, fulfilling the attribution-chain requirement.
    """

    rule_id: str
    name: str
    severity: str
    message_template: str
    phases: list[str] = field(default_factory=lambda: ["execute", "evaluate"])
    agente_ref: str = ""
    attribution: str = ""

    def __post_init__(self) -> None:
        """Validate attribution fields after instantiation."""
        if not self.agente_ref:
            raise ValueError(
                f"{self.__class__.__name__}: agente_ref must not be empty"
            )
        if not self.attribution:
            raise ValueError(
                f"{self.__class__.__name__}: attribution must not be empty"
            )

    def _create_violation(
        self, file: str, line: int, column: int, phenomenon: str
    ) -> Violation:
        """Create a Violation with rule metadata pre-filled.

        Args:
            file: Path to the file where the violation occurred.
            line: Line number (1-based).
            column: Column offset (0-based).
            phenomenon: Human-readable description of what was detected.

        Returns:
            A :class:`Violation` instance with ``rule_id``, ``severity``,
            ``attribution``, and ``agente_ref`` copied from this rule.
        """
        return Violation(
            file=file,
            line=line,
            column=column,
            rule_id=self.rule_id,
            severity=self.severity,
            phenomenon=phenomenon,
            attribution=self.attribution,
            agente_ref=self.agente_ref,
        )

    @abstractmethod
    def check(
        self, file_path: str, file_content: str, ast_tree: ast.AST
    ) -> list[Violation] | None:
        """Check a file for violations of this rule.

        Args:
            file_path: Path to the file being checked.
            file_content: Raw text content of the file.
            ast_tree: Parsed AST of the file content.

        Returns:
            A list of :class:`Violation` objects, or ``None`` if no
            violations are found.
        """
        ...
