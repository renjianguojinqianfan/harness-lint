"""Attribution validation for Harness-Lint rules and violations.

Provides utilities to verify that every rule and every violation carries
a complete attribution chain pointing back to AGENTS.md.
"""

from __future__ import annotations

from harness_lint.rules.base import Rule, Violation


def validate_rule_attribution(rule: Rule) -> list[str]:
    """Validate a rule's attribution chain.

    Args:
        rule: The rule to validate.

    Returns:
        A list of error messages. An empty list means the rule passes
        validation.
    """
    errors: list[str] = []
    if not rule.agente_ref:
        errors.append(f"{rule.rule_id}: agente_ref is empty")
    if not rule.attribution:
        errors.append(f"{rule.rule_id}: attribution is empty")
    if rule.agente_ref and not rule.agente_ref.startswith("AGENTS.md"):
        errors.append(f"{rule.rule_id}: agente_ref must start with 'AGENTS.md'")
    return errors


def validate_violation(violation: Violation) -> list[str]:
    """Validate a violation's full attribution chain.

    Args:
        violation: The violation to validate.

    Returns:
        A list of error messages. An empty list means the violation passes
        validation.
    """
    errors: list[str] = []
    if not violation.phenomenon:
        errors.append("phenomenon is empty")
    if not violation.attribution:
        errors.append("attribution is empty")
    if not violation.agente_ref:
        errors.append("agente_ref is empty")
    if violation.agente_ref and not violation.agente_ref.startswith("AGENTS.md"):
        errors.append("agente_ref must start with 'AGENTS.md'")
    return errors


def validate_ruleset(rules: list[Rule]) -> list[str]:
    """Validate all rules in a ruleset.

    Args:
        rules: List of rules to validate.

    Returns:
        Aggregated error messages from all rules.
    """
    all_errors: list[str] = []
    for rule in rules:
        all_errors.extend(validate_rule_attribution(rule))
    return all_errors
