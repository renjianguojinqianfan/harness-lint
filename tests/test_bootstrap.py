"""Bootstrap test: harness-lint checks itself.

Runs the full harness-lint engine against the project's own source code,
verifying that:
1. No violations are found in self (after fixing)
2. All rule outputs contain the full attribution chain
"""

from harness_lint.checker import check
from harness_lint.pbh_adapter import get_context
from harness_lint.rules import (
    HL001EvalRule,
    HL002ExecRule,
    HL003OsSystemRule,
    HL004HardcodedSecretsRule,
    HL201FunctionLengthRule,
    HL202FakeExceptionRule,
    HL301NoDocstringRule,
)


def test_self_check_passes() -> None:
    """harness-lint should find no violations in its own code."""
    rules = [
        HL001EvalRule(),
        HL002ExecRule(),
        HL003OsSystemRule(),
        HL004HardcodedSecretsRule(),
        HL201FunctionLengthRule(),
        HL202FakeExceptionRule(),
        HL301NoDocstringRule(),
    ]
    context = get_context(".")
    violations, pattern_warnings = check(".", context, rules)

    assert len(violations) == 0, f"Self-check found violations: {violations}"
    assert len(pattern_warnings) == 0


def test_attribution_chain_completeness() -> None:
    """Every rule must produce violations with full attribution chain.

    We verify this by checking the rules' metadata directly.
    """
    rules = [
        HL001EvalRule(),
        HL002ExecRule(),
        HL003OsSystemRule(),
        HL004HardcodedSecretsRule(),
        HL201FunctionLengthRule(),
        HL202FakeExceptionRule(),
        HL301NoDocstringRule(),
    ]

    for rule in rules:
        assert rule.agente_ref, f"{rule.rule_id} missing agente_ref"
        assert rule.attribution, f"{rule.rule_id} missing attribution"
        assert rule.agente_ref.startswith("AGENTS.md"), (
            f"{rule.rule_id} agente_ref must reference AGENTS.md"
        )
