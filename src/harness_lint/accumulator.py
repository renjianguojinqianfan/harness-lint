"""Deviation cost accumulation mechanism for Harness-Lint.

Provides pattern-based cost escalation: repeated violations of the same
rule trigger elevated warnings and, in the evaluate phase, severity
upgrades to Error.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from harness_lint.rules.base import Rule, Violation


@dataclass(frozen=True)
class PatternWarning:
    """A pattern-level warning for repeated rule violations.

    Attributes:
        rule_id: The identifier of the rule that was repeatedly violated.
        count: Total number of occurrences for this rule.
        suggestion: Human-readable guidance referencing AGENTS.md.
        description: Human-readable rule name (from Rule.name).
    """

    rule_id: str
    count: int
    suggestion: str
    description: str = ""


def apply_accumulation(
    violations: list[Violation],
    phase: str | None,
    rules: list[Rule] | None = None,
    threshold: int = 3,
) -> tuple[list[Violation], list[PatternWarning]]:
    """Apply cost accumulation to violations.

    Counts violations per *rule_id*. For rules whose count meets or
    exceeds *threshold*:

    - *phase* == ``"evaluate"``: upgrade severity to ``"Error"``
    - Otherwise: keep severity but update phenomenon
    - In both cases: generate a :class:`PatternWarning`

    Args:
        violations: Raw violations collected by the checker.
        phase: Current PBH phase (``"execute"``, ``"evaluate"``, or None).
        rules: Optional list of rules to look up rule names for descriptions.
        threshold: Minimum count before escalation (default 3).

    Returns:
        Tuple of (processed_violations, pattern_warnings).
    """
    if not violations:
        return [], []

    # Build rule lookup map
    rule_map: dict[str, Rule] = {}
    if rules:
        for r in rules:
            rule_map[r.rule_id] = r

    # Count per rule_id
    counts: dict[str, int] = defaultdict(int)
    for v in violations:
        counts[v.rule_id] += 1

    # Determine which rule_ids exceed threshold
    elevated_rule_ids = {rid for rid, cnt in counts.items() if cnt >= threshold}

    # Collect first agente_ref per elevated rule for suggestion
    first_refs: dict[str, str] = {}
    for v in violations:
        if v.rule_id in elevated_rule_ids and v.rule_id not in first_refs:
            first_refs[v.rule_id] = v.agente_ref

    # Build pattern warnings
    pattern_warnings = [
        PatternWarning(
            rule_id=rid,
            count=counts[rid],
            suggestion=f"建议在 {first_refs[rid]} 中明确相关规范",
            description=rule_map[rid].name if rid in rule_map else rid,
        )
        for rid in sorted(elevated_rule_ids)
    ]

    # Process violations: update severity/phenomenon for elevated rules
    processed: list[Violation] = []
    for v in violations:
        if v.rule_id in elevated_rule_ids:
            new_severity = "Error" if phase == "evaluate" else v.severity
            new_phenomenon = f"该冲突已持续出现 {counts[v.rule_id]} 次，尚未解决"
            processed.append(
                Violation(
                    file=v.file,
                    line=v.line,
                    column=v.column,
                    rule_id=v.rule_id,
                    severity=new_severity,
                    phenomenon=new_phenomenon,
                    attribution=v.attribution,
                    agente_ref=v.agente_ref,
                )
            )
        else:
            processed.append(v)

    return processed, pattern_warnings
