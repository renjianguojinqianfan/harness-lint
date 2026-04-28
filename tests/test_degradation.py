"""Tests for the degradation cost visibility module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from harness_lint.degradation import (
    format_degradation_notice,
    is_harness_lint_enabled,
    record_run_state,
)
from harness_lint.rules.base import Rule, Violation


@pytest.fixture
def temp_harness_dir(monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary .harness directory and patch paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        harness_dir = tmp_path / ".harness"
        harness_dir.mkdir()

        # Patch module-level paths
        monkeypatch.setattr(
            "harness_lint.degradation._STATE_FILE",
            harness_dir / "harness-lint-state.json",
        )
        monkeypatch.setattr(
            "harness_lint.degradation._ENABLED_FLAG",
            harness_dir / "harness-lint-enabled",
        )

        yield harness_dir


def _make_rule(
    rule_id: str = "HL201",
    name: str = "假异常处理",
    agente_ref: str = "AGENTS.md §4.1",
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


def _make_violation(rule_id: str = "HL201") -> Violation:
    """Create a minimal violation for testing."""
    return Violation(
        file="test.py",
        line=1,
        column=0,
        rule_id=rule_id,
        severity="Warning",
        phenomenon="test phenomenon",
        attribution="test attribution",
        agente_ref="AGENTS.md §4.1",
    )


class TestRecordRunState:
    """Tests for record_run_state."""

    def test_writes_valid_json(self, temp_harness_dir: Path) -> None:
        """record_run_state should write a valid JSON file."""
        rules = [_make_rule()]
        violations = [_make_violation()]
        record_run_state(rules, violations)

        state_file = temp_harness_dir / "harness-lint-state.json"
        assert state_file.exists()
        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert "rules" in data
        assert "violation_count" in data
        assert "agente_refs" in data

    def test_records_rule_metadata(self, temp_harness_dir: Path) -> None:
        """Should record rule IDs, names, and agente_refs."""
        rules = [
            _make_rule(rule_id="HL201", name="函数过长", agente_ref="AGENTS.md §4.1"),
            _make_rule(rule_id="HL202", name="假异常处理", agente_ref="AGENTS.md §4.2"),
        ]
        record_run_state(rules, [])

        state_file = temp_harness_dir / "harness-lint-state.json"
        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert len(data["rules"]) == 2
        assert data["rules"][0]["rule_id"] == "HL201"
        assert data["rules"][0]["name"] == "函数过长"
        assert data["rules"][0]["agente_ref"] == "AGENTS.md §4.1"

    def test_records_violation_count(self, temp_harness_dir: Path) -> None:
        """Should record the total number of violations."""
        violations = [_make_violation(), _make_violation(rule_id="HL202")]
        record_run_state([], violations)

        state_file = temp_harness_dir / "harness-lint-state.json"
        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert data["violation_count"] == 2

    def test_records_unique_agente_refs(self, temp_harness_dir: Path) -> None:
        """Should collect unique AGENTS.md references from rules."""
        rules = [
            _make_rule(rule_id="HL201", agente_ref="AGENTS.md §4.1"),
            _make_rule(rule_id="HL202", agente_ref="AGENTS.md §4.2"),
            _make_rule(rule_id="HL203", agente_ref="AGENTS.md §4.1"),  # duplicate
        ]
        record_run_state(rules, [])

        state_file = temp_harness_dir / "harness-lint-state.json"
        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert sorted(data["agente_refs"]) == ["AGENTS.md §4.1", "AGENTS.md §4.2"]


class TestIsHarnessLintEnabled:
    """Tests for is_harness_lint_enabled."""

    def test_returns_true_when_flag_exists(self, temp_harness_dir: Path) -> None:
        """Should return True when the enabled flag file exists."""
        flag = temp_harness_dir / "harness-lint-enabled"
        flag.write_text("1", encoding="utf-8")
        assert is_harness_lint_enabled() is True

    def test_returns_false_when_flag_missing(self, temp_harness_dir: Path) -> None:
        """Should return False when the enabled flag file does not exist."""
        assert is_harness_lint_enabled() is False


class TestFormatDegradationNotice:
    """Tests for format_degradation_notice."""

    def test_returns_none_when_enabled(self, temp_harness_dir: Path) -> None:
        """Should return None when Harness-Lint is enabled."""
        flag = temp_harness_dir / "harness-lint-enabled"
        flag.write_text("1", encoding="utf-8")
        assert format_degradation_notice() is None

    def test_returns_none_when_no_state_file(self, temp_harness_dir: Path) -> None:
        """Should return None when disabled but no state file exists."""
        assert format_degradation_notice() is None

    def test_shows_disabled_message(self, temp_harness_dir: Path) -> None:
        """Should include the disabled notice message."""
        rules = [_make_rule()]
        record_run_state(rules, [])
        result = format_degradation_notice()
        assert result is not None
        assert "当前未启用 Harness-Lint" in result

    def test_shows_rule_count(self, temp_harness_dir: Path) -> None:
        """Should show the total number of rules that were active."""
        rules = [_make_rule(), _make_rule(rule_id="HL202")]
        record_run_state(rules, [])
        result = format_degradation_notice()
        assert result is not None
        assert "2" in result

    def test_shows_last_violation_count(self, temp_harness_dir: Path) -> None:
        """Should show the last reported violation count."""
        violations = [_make_violation(), _make_violation()]
        record_run_state([], violations)
        result = format_degradation_notice()
        assert result is not None
        assert "2" in result

    def test_shows_agente_refs_list(self, temp_harness_dir: Path) -> None:
        """Should list AGENTS.md clauses no longer being verified."""
        rules = [
            _make_rule(rule_id="HL201", agente_ref="AGENTS.md §4.1"),
            _make_rule(rule_id="HL202", agente_ref="AGENTS.md §4.2"),
        ]
        record_run_state(rules, [])
        result = format_degradation_notice()
        assert result is not None
        assert "AGENTS.md §4.1" in result
        assert "AGENTS.md §4.2" in result

    def test_single_rule_single_violation(self, temp_harness_dir: Path) -> None:
        """End-to-end with single rule and single violation."""
        rules = [_make_rule(rule_id="HL201", name="函数过长", agente_ref="AGENTS.md §5.3")]
        violations = [_make_violation(rule_id="HL201")]
        record_run_state(rules, violations)
        result = format_degradation_notice()
        assert result is not None
        assert "当前未启用 Harness-Lint" in result
        assert "1" in result  # at least one 1 for rule count or violation count
        assert "AGENTS.md §5.3" in result
