"""Tests for the deviation cost accumulation mechanism."""

from __future__ import annotations

from harness_lint.accumulator import apply_accumulation
from harness_lint.rules.base import Rule, Violation


def _make_violation(
    rule_id: str = "HL201",
    severity: str = "Warning",
    agente_ref: str = "AGENTS.md §1",
) -> Violation:
    """Create a minimal violation for testing."""
    return Violation(
        file="test.py",
        line=1,
        column=0,
        rule_id=rule_id,
        severity=severity,
        phenomenon="original phenomenon",
        attribution="test attribution",
        agente_ref=agente_ref,
    )


def _make_rule(
    rule_id: str = "HL201",
    name: str = "假异常处理",
    agente_ref: str = "AGENTS.md §1",
) -> Rule:
    """Create a minimal concrete rule for testing."""

    class _TestRule(Rule):
        def check(self, file_path, file_content, ast_tree):
            return []

    return _TestRule(
        rule_id=rule_id,
        name=name,
        severity="Warning",
        message_template="test message",
        agente_ref=agente_ref,
        attribution="test attribution",
    )


class TestBelowThreshold:
    """When violation count is below threshold, no escalation should occur."""

    def test_count_equal_to_threshold_minus_one_no_escalation(self) -> None:
        """2 violations with default threshold 3 → no change."""
        violations = [_make_violation(), _make_violation()]
        rules = [_make_rule()]
        result_v, result_pw = apply_accumulation(violations, phase=None, rules=rules)

        assert len(result_v) == 2
        assert all(v.severity == "Warning" for v in result_v)
        assert all(v.phenomenon == "original phenomenon" for v in result_v)
        assert result_pw == []

    def test_single_violation_no_escalation(self) -> None:
        """1 violation with default threshold 3 → no change."""
        violations = [_make_violation()]
        rules = [_make_rule()]
        result_v, result_pw = apply_accumulation(violations, phase=None, rules=rules)

        assert len(result_v) == 1
        assert result_v[0].severity == "Warning"
        assert result_v[0].phenomenon == "original phenomenon"
        assert result_pw == []

    def test_different_rules_below_threshold_independently(self) -> None:
        """Each rule_id is counted independently."""
        violations = [
            _make_violation(rule_id="HL201"),
            _make_violation(rule_id="HL201"),
            _make_violation(rule_id="HL202"),
            _make_violation(rule_id="HL202"),
        ]
        rules = [_make_rule(rule_id="HL201"), _make_rule(rule_id="HL202", name="函数过长")]
        result_v, result_pw = apply_accumulation(violations, phase=None, rules=rules)

        assert all(v.severity == "Warning" for v in result_v)
        assert all(v.phenomenon == "original phenomenon" for v in result_v)
        assert result_pw == []


class TestAtThreshold:
    """When violation count equals threshold, escalation should occur."""

    def test_exact_threshold_generates_pattern_warning(self) -> None:
        """3 violations with default threshold 3 → escalation."""
        violations = [_make_violation(), _make_violation(), _make_violation()]
        rules = [_make_rule(name="假异常处理")]
        result_v, result_pw = apply_accumulation(violations, phase=None, rules=rules)

        assert len(result_pw) == 1
        assert result_pw[0].rule_id == "HL201"
        assert result_pw[0].count == 3
        assert result_pw[0].description == "假异常处理"

    def test_exact_threshold_phenomenon_changed(self) -> None:
        """Phenomenon should be updated for escalated violations."""
        violations = [_make_violation(), _make_violation(), _make_violation()]
        rules = [_make_rule()]
        result_v, _ = apply_accumulation(violations, phase=None, rules=rules)

        expected = "该冲突已持续出现 3 次，尚未解决"
        assert all(v.phenomenon == expected for v in result_v)


class TestAboveThreshold:
    """When violation count exceeds threshold, escalation should occur."""

    def test_above_threshold_generates_pattern_warning(self) -> None:
        """5 violations with default threshold 3 → escalation."""
        violations = [_make_violation() for _ in range(5)]
        rules = [_make_rule()]
        result_v, result_pw = apply_accumulation(violations, phase=None, rules=rules)

        assert len(result_pw) == 1
        assert result_pw[0].count == 5

    def test_above_threshold_phenomenon_changed(self) -> None:
        """Phenomenon should reflect actual count."""
        violations = [_make_violation() for _ in range(5)]
        rules = [_make_rule()]
        result_v, _ = apply_accumulation(violations, phase=None, rules=rules)

        expected = "该冲突已持续出现 5 次，尚未解决"
        assert all(v.phenomenon == expected for v in result_v)


class TestPhaseBehavior:
    """Severity upgrade behavior depends on phase."""

    def test_phase_none_keeps_warning_severity(self) -> None:
        """phase=None → severity stays Warning, phenomenon changes."""
        violations = [_make_violation() for _ in range(3)]
        rules = [_make_rule()]
        result_v, result_pw = apply_accumulation(violations, phase=None, rules=rules)

        assert all(v.severity == "Warning" for v in result_v)
        assert len(result_pw) == 1

    def test_phase_execute_keeps_warning_severity(self) -> None:
        """phase='execute' → severity stays Warning, phenomenon changes."""
        violations = [_make_violation() for _ in range(3)]
        rules = [_make_rule()]
        result_v, result_pw = apply_accumulation(violations, phase="execute", rules=rules)

        assert all(v.severity == "Warning" for v in result_v)
        assert len(result_pw) == 1

    def test_phase_evaluate_upgrades_to_error(self) -> None:
        """phase='evaluate' → severity upgraded to Error."""
        violations = [_make_violation() for _ in range(3)]
        rules = [_make_rule()]
        result_v, result_pw = apply_accumulation(violations, phase="evaluate", rules=rules)

        assert all(v.severity == "Error" for v in result_v)
        assert len(result_pw) == 1


class TestMultipleRules:
    """Multiple rules exceeding threshold should each generate PatternWarning."""

    def test_two_rules_over_threshold(self) -> None:
        """Both HL201 and HL202 exceed threshold → two PatternWarnings."""
        violations = [
            _make_violation(rule_id="HL201", agente_ref="AGENTS.md §5") for _ in range(3)
        ]
        violations += [
            _make_violation(rule_id="HL202", agente_ref="AGENTS.md §4") for _ in range(4)
        ]
        rules = [
            _make_rule(rule_id="HL201", name="假异常处理"),
            _make_rule(rule_id="HL202", name="函数过长"),
        ]
        result_v, result_pw = apply_accumulation(violations, phase=None, rules=rules)

        assert len(result_pw) == 2
        rule_ids = {pw.rule_id for pw in result_pw}
        assert rule_ids == {"HL201", "HL202"}

        hl201_pw = next(pw for pw in result_pw if pw.rule_id == "HL201")
        hl202_pw = next(pw for pw in result_pw if pw.rule_id == "HL202")
        assert hl201_pw.count == 3
        assert hl201_pw.description == "假异常处理"
        assert hl202_pw.count == 4
        assert hl202_pw.description == "函数过长"


class TestEmptyViolations:
    """Edge case: empty input."""

    def test_empty_violations_returns_empty_lists(self) -> None:
        """Empty violations → empty lists."""
        result_v, result_pw = apply_accumulation([], phase=None, rules=[])
        assert result_v == []
        assert result_pw == []


class TestPatternWarningSuggestion:
    """PatternWarning suggestion should reference agente_ref."""

    def test_suggestion_uses_first_violation_agente_ref(self) -> None:
        """Suggestion should cite the first violation's agente_ref."""
        violations = [
            _make_violation(agente_ref="AGENTS.md §5 Critical Rules")
            for _ in range(3)
        ]
        rules = [_make_rule(agente_ref="AGENTS.md §5 Critical Rules")]
        _, result_pw = apply_accumulation(violations, phase=None, rules=rules)

        assert len(result_pw) == 1
        assert result_pw[0].suggestion == "建议在 AGENTS.md §5 Critical Rules 中明确相关规范"

    def test_suggestion_per_rule(self) -> None:
        """Each rule uses its own agente_ref for suggestion."""
        violations = [
            _make_violation(rule_id="HL201", agente_ref="AGENTS.md §5") for _ in range(3)
        ]
        violations += [
            _make_violation(rule_id="HL202", agente_ref="AGENTS.md §4") for _ in range(3)
        ]
        rules = [
            _make_rule(rule_id="HL201", agente_ref="AGENTS.md §5"),
            _make_rule(rule_id="HL202", agente_ref="AGENTS.md §4"),
        ]
        _, result_pw = apply_accumulation(violations, phase=None, rules=rules)

        hl201_pw = next(pw for pw in result_pw if pw.rule_id == "HL201")
        hl202_pw = next(pw for pw in result_pw if pw.rule_id == "HL202")
        assert hl201_pw.suggestion == "建议在 AGENTS.md §5 中明确相关规范"
        assert hl202_pw.suggestion == "建议在 AGENTS.md §4 中明确相关规范"


class TestCustomThreshold:
    """Threshold parameter should be configurable."""

    def test_custom_threshold_of_two(self) -> None:
        """threshold=2 → 2 violations triggers escalation."""
        violations = [_make_violation(), _make_violation()]
        rules = [_make_rule()]
        result_v, result_pw = apply_accumulation(
            violations, phase=None, rules=rules, threshold=2
        )

        assert len(result_pw) == 1
        assert all(v.phenomenon == "该冲突已持续出现 2 次，尚未解决" for v in result_v)

    def test_custom_threshold_of_five(self) -> None:
        """threshold=5 → 4 violations does not trigger."""
        violations = [_make_violation() for _ in range(4)]
        rules = [_make_rule()]
        result_v, result_pw = apply_accumulation(
            violations, phase=None, rules=rules, threshold=5
        )

        assert result_pw == []
        assert all(v.phenomenon == "original phenomenon" for v in result_v)


class TestUnchangedViolations:
    """Violations that are not escalated should remain completely unchanged."""

    def test_non_escalated_violations_unchanged(self) -> None:
        """Mix of escalated and non-escalated rules."""
        violations = [
            _make_violation(rule_id="HL201"),
            _make_violation(rule_id="HL201"),
            _make_violation(rule_id="HL202"),
            _make_violation(rule_id="HL202"),
            _make_violation(rule_id="HL202"),
            _make_violation(rule_id="HL202"),
        ]
        rules = [
            _make_rule(rule_id="HL201"),
            _make_rule(rule_id="HL202"),
        ]
        result_v, result_pw = apply_accumulation(violations, phase=None, rules=rules)

        # HL201 should be unchanged (2 < threshold 3)
        hl201_violations = [v for v in result_v if v.rule_id == "HL201"]
        assert all(v.phenomenon == "original phenomenon" for v in hl201_violations)
        assert all(v.severity == "Warning" for v in hl201_violations)

        # HL202 should be escalated (4 >= threshold 3)
        hl202_violations = [v for v in result_v if v.rule_id == "HL202"]
        assert all(v.phenomenon == "该冲突已持续出现 4 次，尚未解决" for v in hl202_violations)

        assert len(result_pw) == 1
        assert result_pw[0].rule_id == "HL202"


class TestPatternWarningDescription:
    """PatternWarning description should come from rule name."""

    def test_description_from_rule_name(self) -> None:
        """description should be the rule's name."""
        violations = [_make_violation() for _ in range(3)]
        rules = [_make_rule(name="假异常处理")]
        _, result_pw = apply_accumulation(violations, phase=None, rules=rules)

        assert len(result_pw) == 1
        assert result_pw[0].description == "假异常处理"

    def test_description_missing_rule_defaults_to_rule_id(self) -> None:
        """If rule not found in rules list, description defaults to rule_id."""
        violations = [_make_violation(rule_id="HL999") for _ in range(3)]
        rules = [_make_rule(rule_id="HL201")]
        _, result_pw = apply_accumulation(violations, phase=None, rules=rules)

        assert len(result_pw) == 1
        assert result_pw[0].description == "HL999"

    def test_description_for_multiple_rules(self) -> None:
        """Each PatternWarning gets description from its corresponding rule."""
        violations = [
            _make_violation(rule_id="HL201") for _ in range(3)
        ]
        violations += [
            _make_violation(rule_id="HL202") for _ in range(3)
        ]
        rules = [
            _make_rule(rule_id="HL201", name="假异常处理"),
            _make_rule(rule_id="HL202", name="函数过长"),
        ]
        _, result_pw = apply_accumulation(violations, phase=None, rules=rules)

        assert len(result_pw) == 2
        descriptions = {pw.rule_id: pw.description for pw in result_pw}
        assert descriptions["HL201"] == "假异常处理"
        assert descriptions["HL202"] == "函数过长"
